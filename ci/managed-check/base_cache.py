"""Trusted base-side COFF object cache with full dependency verification."""
import gzip
import json
import os
from pathlib import Path
import time
import zlib

from common import HEX64, digest, encoded
from measure import CONFIG, data_entry, file_hash
from pool_compare import projection
from pool_protocol import MAX_OBJECT, check_object, decode, encode

SCHEMA = 1
MAX_CACHE_BYTES = 256 * 1024 * 1024
MAX_ENTRY_BYTES = 8 * 1024 * 1024


def path_set_digest(hashes):
    """Digest of the exact sorted set of source/header paths in the base projection.

    Invalidates cached objects whenever any file path is added, renamed, or removed
    on base so a newly introduced header can never shadow an earlier include search hit.
    """
    return digest(encoded(sorted(hashes)))


def entry_key(row, plan):
    return digest(encoded([
        "bfme-base-obj-v1",
        row["tu"],
        row["source"],
        row["contract"],
        plan["profile_sha256"],
        plan["image_sha256"],
    ]))


def _entry_path(cache_dir, key):
    return Path(cache_dir) / key[:2] / f"{key}.json.gz"


def _read_gzip_bounded(path, limit=MAX_ENTRY_BYTES):
    with gzip.open(path, "rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Cached object entry exceeded its size limit.")
    return json.loads(data.decode("ascii"))


def _verify_sealed_dep(tools, role, rel_path, expected_sha):
    if role not in tools or not isinstance(rel_path, str) or not rel_path or Path(rel_path).is_absolute():
        return None
    root = Path(tools[role]).resolve(strict=True)
    target = (root / rel_path).resolve(strict=True)
    if not target.is_relative_to(root) or not target.is_file():
        return None
    if file_hash(target) != expected_sha:
        return None
    return target


def verify_hit(cache_dir, row, plan, sources, hashes, tools):
    """Verify one cached base TU without mutating `job`. Returns hit dict or None."""
    key = entry_key(row, plan)
    path = _entry_path(cache_dir, key)
    if not path.is_file():
        return None
    try:
        entry = _read_gzip_bounded(path)
        if (not isinstance(entry, dict) or entry.get("version") != SCHEMA
                or entry.get("key") != key or entry.get("tu") != row["tu"]
                or entry.get("source") != row["source"] or entry.get("contract") != row["contract"]
                or entry.get("profile") != plan["profile_sha256"]
                or entry.get("image") != plan["image_sha256"]
                or entry.get("path_set_sha") != path_set_digest(hashes)):
            return None
        obj_sha = entry.get("object_sha256")
        if not isinstance(obj_sha, str) or not HEX64.fullmatch(obj_sha):
            return None
        source_deps = entry.get("source_deps")
        sealed_deps = entry.get("sealed_deps")
        if not isinstance(source_deps, list) or not isinstance(sealed_deps, list):
            return None
        verified_source = []
        for item in source_deps:
            if not (isinstance(item, list) and len(item) == 2 and all(isinstance(x, str) for x in item)):
                return None
            rel_path, dep_sha = item
            if hashes.get(rel_path) != dep_sha or rel_path not in sources:
                return None
            verified_source.append((rel_path, dep_sha))
        verified_sealed = []
        for item in sealed_deps:
            if not (isinstance(item, list) and len(item) == 3 and all(isinstance(x, str) for x in item)):
                return None
            role, rel_path, dep_sha = item
            target = _verify_sealed_dep(tools, role, rel_path, dep_sha)
            if target is None:
                return None
            verified_sealed.append((target, dep_sha))
        obj_bytes = decode(entry.get("object_b64"), MAX_OBJECT)
        if check_object(obj_bytes) != obj_sha:
            return None
    except (OSError, ValueError, TypeError, KeyError, EOFError, zlib.error):
        return None
    return {
        "cache_path": path,
        "row": row,
        "object_sha256": obj_sha,
        "object_bytes": obj_bytes,
        "verified_source": verified_source,
        "verified_sealed": verified_sealed,
    }


def materialize_hit(hit, sources, job):
    """Write a verified hit into `job` matching `measure.measure()` layout."""
    try:
        os.utime(hit["cache_path"], None)
    except OSError:
        pass
    row = hit["row"]
    tu = row["tu"]
    needed = {tu} | {rel_path for rel_path, _ in hit["verified_source"]}
    for filename in needed:
        target = job / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(decode(sources[filename], 1024**2))
    obj_dir = job / "obj"
    obj_dir.mkdir(parents=True, exist_ok=True)
    obj = obj_dir / (tu.replace("/", "_") + ".obj")
    obj.write_bytes(hit["object_bytes"])
    headers_map = {str(job / rel_path): dep_sha for rel_path, dep_sha in hit["verified_source"]}
    for target, dep_sha in hit["verified_sealed"]:
        headers_map[str(target)] = dep_sha
    obj.with_suffix(".obj.includes.json").write_text(json.dumps(sorted(headers_map)))
    obj.with_suffix(".obj.compile.json").write_text(json.dumps({
        "source_sha256": row["source"],
        "object_sha256": hit["object_sha256"],
        "headers": dict(sorted(headers_map.items())),
        "compiler_contract": row["contract"],
    }))
    return obj


def prune(cache_dir, max_bytes=MAX_CACHE_BYTES):
    root = Path(cache_dir)
    if not root.is_dir():
        return
    entries, total = [], 0
    for item in root.rglob("*.json.gz"):
        try:
            st = item.stat()
        except OSError:
            continue
        entries.append((st.st_mtime, st.st_size, item))
        total += st.st_size
    if total <= max_bytes:
        return
    entries.sort()
    for _, size, item in entries:
        try:
            item.unlink()
            total -= size
        except OSError:
            pass
        if total <= max_bytes:
            break


def store(cache_dir, row, plan, job, tools, hashes):
    """Store one freshly compiled base TU into `cache_dir`. Returns True if stored."""
    tu = row["tu"]
    obj = job / "obj" / (tu.replace("/", "_") + ".obj")
    meta_path = obj.with_suffix(".obj.compile.json")
    if not (obj.is_file() and meta_path.is_file()):
        return False
    try:
        meta = json.loads(meta_path.read_text())
        if (meta.get("source_sha256") != row["source"]
                or meta.get("compiler_contract") != row["contract"]
                or not HEX64.fullmatch(meta.get("object_sha256", ""))):
            return False
        obj_bytes = obj.read_bytes()
        if check_object(obj_bytes) != meta["object_sha256"]:
            return False
        resolved_job = job.resolve(strict=True)
        resolved_tools = {role: Path(root).resolve(strict=True) for role, root in tools.items()}
        source_deps, sealed_deps = [], []
        for raw_path, dep_sha in sorted((meta.get("headers") or {}).items()):
            if not isinstance(dep_sha, str) or not HEX64.fullmatch(dep_sha):
                return False
            candidate = Path(raw_path).resolve(strict=True)
            if candidate.is_relative_to(resolved_job):
                source_deps.append([candidate.relative_to(resolved_job).as_posix(), dep_sha])
                continue
            matched_role = None
            for role, root in resolved_tools.items():
                if candidate.is_relative_to(root):
                    sealed_deps.append([role, candidate.relative_to(root).as_posix(), dep_sha])
                    matched_role = role
                    break
            if matched_role is None:
                return False
        key = entry_key(row, plan)
        payload = {
            "version": SCHEMA,
            "key": key,
            "tu": tu,
            "source": row["source"],
            "contract": row["contract"],
            "profile": plan["profile_sha256"],
            "image": plan["image_sha256"],
            "path_set_sha": path_set_digest(hashes),
            "object_sha256": meta["object_sha256"],
            "source_deps": source_deps,
            "sealed_deps": sealed_deps,
            "object_b64": encode(obj_bytes),
        }
        dest = _entry_path(cache_dir, key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(f".tmp.{os.getpid()}")
        with gzip.open(tmp, "wb", compresslevel=4) as stream:
            stream.write(encoded(payload))
        os.replace(tmp, dest)
        return True
    except (OSError, ValueError, TypeError, KeyError):
        return False


def measure_base_with_cache(git, judge, plan, tools, job, cache_dir, *, measure_fn, timing=None):
    """Serve verified base TUs from `cache_dir` and compile only cache misses."""
    cache_root = Path(cache_dir)
    cache_root.mkdir(parents=True, exist_ok=True)
    base = plan["historical_base"]
    sources, hashes = projection(git, base)
    rows = plan["compile"]["base"]
    hit_payloads, missed_rows = {}, []
    for row in rows:
        hit = verify_hit(cache_root, row, plan, sources, hashes, tools)
        if hit is not None:
            hit_payloads[row["tu"]] = hit
        else:
            missed_rows.append(row)

    results = {}
    compile_s, compare_s = 0.0, 0.0
    if missed_rows:
        miss_plan = dict(
            plan,
            request_paths=[row["tu"] for row in missed_rows],
            compile=dict(plan["compile"], base=missed_rows),
        )
        miss_timing = {} if timing is not None else None
        miss_results = measure_fn(git, judge, "base", miss_plan, tools, job, timing=miss_timing)
        if miss_timing:
            compile_s += miss_timing.get("compile", 0.0)
            compare_s += miss_timing.get("compare", 0.0)
        results.update(miss_results)
        stored_any = False
        for row in missed_rows:
            tu = row["tu"]
            if not (miss_results.get(tu) or {}).get("error"):
                if store(cache_root, row, plan, job, tools, hashes):
                    stored_any = True
        if stored_any:
            prune(cache_root)
            try:
                (cache_root / ".updated").write_text(f"{int(time.time())}\n")
            except OSError:
                pass

    if hit_payloads:
        hit_objs = {tu: materialize_hit(hit, sources, job) for tu, hit in hit_payloads.items()}
        for file in CONFIG:
            if not (job / "config" / file).is_file():
                data_entry(git, base, "config/" + file, job)
        for tu in hit_objs:
            if not (job / "expected" / (tu[4:] + ".json")).is_file():
                data_entry(git, base, "expected/" + tu[4:] + ".json", job)

        def precompiled_hit(work, name):
            raw = (work / name).read_text(encoding="utf-8-sig", errors="replace")
            return hit_objs[name], "", judge.effective_source(name, raw)

        judge.compile_tu = precompiled_hit
        started = time.monotonic()
        try:
            ledger = judge.ledger(job)
            for tu in plan["request_paths"]:
                if tu in hit_objs:
                    results[tu] = judge.judge_tu(job, tu, ledger)
        finally:
            compare_s += time.monotonic() - started

    if timing is not None:
        timing["compile"] = compile_s
        timing["compare"] = compare_s
    print(f"Base compile cache: {len(hit_payloads)}/{len(rows)} hits, {len(missed_rows)} compiled.", flush=True)
    return {tu: results[tu] for tu in plan["request_paths"]}
