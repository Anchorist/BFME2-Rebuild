"""Compare a protected base and validated source-only candidate on the sealed Boat image."""
import hashlib
import os
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace

from common import PIN, digest, encoded, read, validate_binding, write
from intake import reconstruct
from gitrepo import Git
from pool_compare import TrustedPaths, projection
from pool_protocol import decode
from measure import audit, measure, pin, setup_home
from edited_functions import edited
from diff_scope import diff_lines
from finished_index import Owners, RealHeaders
from gateway import projection as public_projection
from progress_delta import drafts_in_use, progress
from reporting import GATES, from_landing


def native_commands(git, judge, revision, paths, tools):
    sources, hashes = projection(git, revision)
    portable = TrustedPaths(tools, hashes)
    result = []
    for path in paths:
        command = portable.plan(judge, path, decode(sources[path], 1024**2), hashes[path])
        command["contract"] = digest(encoded({"compiler": "vc71-sealed-v1", "policy": PIN, **{
            key: command[key] for key in ("flags", "env")}}))
        result.append(command)
    return result


def protected_judge(work, roots, baseline):
    os.environ.update(LANG="C", LC_ALL="C")
    judge = setup_home(work, roots, baseline)
    # The sealed compiler supplies SDK headers only. Reuse the native
    # inventory verifier against that header-only view.
    judge.build.DXSDK_DIR = work / "bfme2-runner/repo/vendor/dxsdk-aug2005"
    judge.build.DXSDK_MANIFEST = Path(__file__).with_name("dxsdk-includes.manifest")
    import stlport_overlay
    judge.stlport46_overlay = lambda: Path(roots["overlay"])
    stlport_overlay.TREE = Path(roots["stlport46"])
    original = judge.build.compiler_environment

    def compiler_environment(root, source=None):
        env = original(root, source)
        env["WINEPATH"] = ";".join(judge.build.wine_path(path) for path in
                                   (root / "Vc7/bin", root / "Common7/IDE", Path(roots["vcruntime"])))
        return env

    judge.build.compiler_environment = compiler_environment
    if judge.checker_hash() != PIN["checker"]:
        raise ValueError("The protected native engine identity differs from the approved engine.")
    return judge


def index(table):
    return {path: {"verified": item.get("object_verified", False),
                   "error": bool(item.get("error")),
                   "gates": set(item["gates"]),
                   "proven": {row["rva"] for row in item["rows"]
                              if row.get("credited", row["status"] == "MATCH") and row.get("proof") == "proven"},
                   "rows": {row["rva"]: (row["status"], row.get("pct", 100.0 if row["status"] == "MATCH" else 0.0))
                            for row in item["rows"]}}
            for path, item in table.items()}


def reduction(old, new):
    counts = dict.fromkeys(("gained", "lost_credit", "lost_proof", "lost_verified",
                            "new_compiler_errors", "new_source_gates"), 0)
    rules, hint = set(), []
    for path in old:
        prior, current = old[path], new[path]
        before = {address for address, row in prior["rows"].items() if row[0] == "MATCH"}
        after = {address for address, row in current["rows"].items() if row[0] == "MATCH"}
        counts["gained"] += len(after - before)
        counts["lost_credit"] += len(before - after)
        counts["lost_proof"] += len(prior["proven"] - current["proven"])
        counts["lost_verified"] += int(prior["verified"] and not current["verified"])
        counts["new_compiler_errors"] += int(not prior["error"] and current["error"])
        added = current["gates"] - prior["gates"]
        counts["new_source_gates"] += len(added)
        if prior["rows"].keys() - current["rows"].keys():
            rules.add("regression")
        for problem in sorted(added):
            reason = next((phrase for phrase in GATES if phrase in problem), None)
            if "annotations" in problem:
                rules.add("annotation")
            elif "assembly" in problem or " asm " in problem:
                rules.add("assembly")
            else:
                rules.add("native-source")
            if reason:
                hint.append(GATES[reason])
    for key, rule in (("lost_credit", "regression"), ("lost_proof", "reference-proof"),
                      ("lost_verified", "verified"), ("new_compiler_errors", "compile")):
        if counts[key]:
            rules.add(rule)
    return counts, rules, hint


def nearby(judge, body, first):
    lines = []
    for line in judge.disasm(body, 0):
        address, separator, text = line.strip().partition(":")
        if separator and re.fullmatch("[0-9a-f]+", address):
            lines.append({"offset": int(address, 16), "text": " ".join(text.split())})
    position = next((i - 1 for i, row in enumerate(lines) if row["offset"] > first), len(lines) - 1)
    start = max(0, min(position - 3, len(lines) - 8))
    return lines[start:start + 8]


def difference(judge, obj, row, allow_listing):
    symbol, size = row.get("symbol"), row.get("size")
    if not symbol or type(size) is not int or not 0 < size < 1024**2:
        return None
    try:
        compiled, relocs = judge.read_body(obj, symbol)
        if len(compiled) > size and all(byte == 0xCC for byte in compiled[size:]):
            compiled = compiled[:size]
        old = judge.build.read_target_bytes(int(row["rva"], 16), size)
        left = judge.masked(compiled, relocs, max(len(compiled), size))[:len(compiled)]
        right = judge.mask_like(old, left, relocs, size)
        first = next((i for i, pair in enumerate(zip(left, right)) if pair[0] != pair[1]),
                     min(len(left), len(right)) if len(left) != len(right) else None)
        result = {"first": first, "compiled_size": len(compiled), "retail_size": size}
        if allow_listing and first is not None:
            result.update(compiled_listing=nearby(judge, compiled, first),
                          reference_listing=nearby(judge, old, first))
        return result
    except (OSError, KeyError, TypeError, ValueError):
        return None


def make_report(git, judge, plan, tip, old, new, find_object, *, lookup_difference=None):
    from header_definitions import global_class_defs

    base = plan["base"]
    indexed_old, indexed_new = index(old), index(new)
    counts, rules, hints = reduction(indexed_old, indexed_new)
    owners = Owners(git, base)
    adapter = SimpleNamespace(ANNOT=judge.ANNOT, land_gate9=SimpleNamespace(diff_lines=diff_lines))
    scope = edited(git, adapter, base, tip, owners)
    for entry in scope:
        address = entry["address"]
        if entry["after_body"] and address is not None:
            row = f"0x{address:08X}"
            before = indexed_old.get(entry["owner"], {}).get("rows", {}).get(row)
            after = indexed_new.get(entry["owner"], {}).get("rows", {}).get(row)
            if after and after[0] == "PARTIAL" and (before is None or before[0] == "MISSING"):
                rules.add("partial-body")
    state = {"new": indexed_new, "gains": counts["gained"], "jt": plan["request_paths"],
             "kind": "regression" if rules else "ok"}
    changed = set(plan["changed_paths"])
    prior = {"base_results": indexed_old, "results": new}
    def first_difference(path, row, _raw, own):
        if lookup_difference:
            return lookup_difference(path, row, own)
        obj = find_object(path)
        return difference(judge, obj, row, own) if obj else None

    report = from_landing(state, prior, changed, first_difference, owners, edited=scope)
    old_headers = RealHeaders(git, base, global_class_defs)
    new_headers = RealHeaders(git, tip, global_class_defs)

    def finished(address, after):
        tree = new_headers if after else old_headers
        source, name, _ = owners.functions[address]
        return tree.ready(source, name)

    report["progress"] = progress(indexed_old, indexed_new, owners.path, finished,
                                  drafts_in_use(git, base), drafts_in_use(git, tip))
    report["progress"]["lost"] = max(report["lost_count"], report["progress"]["lost"])
    report["codes"] = sorted(rules)
    clean = public_projection(report, changed)
    clean["messages"] = list(dict.fromkeys(hints))[:8]
    functions = [{"path": row["path"], "line": row["line"], "function": row["function"],
                  "rva": row["rva"], "before": row["old"], "after": row["new"]}
                 for row in clean["edited"]]
    return clean, counts, functions


def main(admission, out):
    admission, out = Path(admission), Path(out)
    plan_path = admission / "plan.json"
    plan, decision = validate_binding(read(plan_path, 18 * 1024**2)), read(admission / "decision.json", 4096)
    with plan_path.open("rb") as raw_plan:
        plan_hash = hashlib.file_digest(raw_plan, "sha256").hexdigest()
    if decision.get("plan") != plan_hash or any(decision.get(key) != plan[key] for key in ("repo", "base", "head", "tree", "number")):
        raise ValueError("The protected intake receipt and its plan differ.")
    if plan["base"] != os.environ["GITHUB_SHA"] or len(plan["request_paths"]) > 8:
        raise ValueError("This workflow requires the admitted protected revision and at most eight translation units.")
    if not plan["request_paths"] or sorted(set(plan["request_paths"])) != plan["request_paths"]:
        raise ValueError("The admitted translation-unit list is invalid.")
    baseline = (Path.cwd() / "baseline/game.dat").resolve(strict=True)
    pin(baseline, PIN["baseline_sha256"])
    roots = audit(PIN)
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix="bfme-managed-check-") as name:
        work = Path(name)
        git = Git(work / "source.git", initialize=True)
        alternate = (Path.cwd() / ".git/objects").resolve(strict=True)
        (git.path / "objects/info/alternates").write_text(str(alternate) + "\n")
        if Git(Path.cwd() / ".git").rev("HEAD") != plan["base"]:
            raise ValueError("The trusted comparator did not receive the admitted main commit.")
        git.run("update-ref", "refs/heads/main", plan["base"])
        tip = reconstruct(git, plan)
        judge = protected_judge(work / "home", roots, baseline)
        judge.BARE = git.path
        native = dict(plan, historical_base=plan["base"], historical_head=tip,
                      compile={side: native_commands(git, judge, rev, plan["request_paths"], roots)
                               for side, rev in (("base", plan["base"]), ("head", tip))})
        old = measure(git, judge, "base", native, roots, work / "base")
        new = measure(git, judge, "head", native, roots, work / "head")
        report, counts, functions = make_report(git, judge, plan, tip, old, new,
            lambda path: work / "head/obj" / (path.replace("/", "_") + ".obj"))
        if advisory_root := os.environ.get("BFME_INLINE_EXPORT"):
            try:
                from inline_payload import narrow
                matrix_sha = narrow(plan, native, {"base": old, "head": new}, work, advisory_root)
                with Path(os.environ["GITHUB_OUTPUT"]).open("a") as stream:
                    stream.write("inline_matrix_sha=" + matrix_sha + "\n")
            except Exception:
                print("Inline virtual advisory evidence is unavailable for this run.", file=sys.stderr)
    out.mkdir(mode=0o700)
    write(out / "verdict.json", {key: plan[key] for key in ("version", "repo", "number", "base", "head", "tree")}
          | {"plan": plan_hash, "report": report, "counts": counts, "functions": functions})


if __name__ == "__main__":
    main(*sys.argv[1:])

