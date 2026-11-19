"""Trusted transport client and native-judge input adapter for compiler-only Boat jobs."""
import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path

from gitrepo import Git
from pool_protocol import (MAX_DIAGNOSTICS, MAX_FILE, MAX_FILES, MAX_OBJECT, MAX_SOURCE, ProtocolError,
                           VERSION, check_object, decode, digest, encode, pack_sources, relative, safe_diagnostics, source_path)
from pool_worker import (MAX_HEADERS, MAX_PLAN, MAX_REQUEST, PATH_ENV, PLAIN_ENV, json_bytes,
                         read_regular)

MAX_REPLY = (MAX_OBJECT * 4 // 3 + 400_000) * MAX_PLAN + 4096
WIN = re.compile(r"^Z:[\\/](.+)$", re.I)


def projection(git, commit):
    """Build a compiler-only payload from exact Git blobs. Read archives as data."""
    raw = git.run("archive", "--format=tar", commit, "--", "src", "include").stdout
    if len(raw) > MAX_SOURCE + 12 * 1024**2:
        raise ProtocolError("Source projection exceeds its archive size limit.")
    encoded, hashes, names, object_names, total = {}, {}, set(), set(), 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        for entry in archive:
            path = entry.name
            if not source_path(path):
                continue
            if not entry.isfile() or path.casefold() in names or not 0 <= entry.size <= MAX_FILE:
                raise ProtocolError("Source projection has an unsupported entry.")
            total += entry.size
            if total > MAX_SOURCE or len(encoded) >= MAX_FILES:
                raise ProtocolError("Source projection exceeds its size limit.")
            names.add(path.casefold())
            if path.startswith("src/") and Path(path).suffix.lower() in {".c", ".cpp"}:
                object_name = path.replace("/", "_").casefold()
                if object_name in object_names:
                    raise ProtocolError("Two translation units share a native judge artifact name.")
                object_names.add(object_name)
            with archive.extractfile(entry) as stream:
                data = stream.read(MAX_FILE + 1)
            if len(data) != entry.size:
                raise ProtocolError("Incomplete source blob in Git archive.")
            encoded[path] = encode(data)
            hashes[path] = digest(data)
    return encoded, hashes


class TrustedPaths:
    def __init__(self, roots, git_blobs):
        self.roots = {alias: Path(path).resolve(strict=True) for alias, path in roots.items()}
        self.order = sorted(self.roots, key=lambda a: -len(self.roots[a].parts))
        self.git_blobs = git_blobs
        self.hashes = {}

    def portable(self, flag_path):
        match = WIN.fullmatch(flag_path)
        if not match:
            raise ProtocolError("Compiler path is outside the approved toolchain.")
        actual = Path("/" + match[1].replace("\\", "/")).resolve(strict=True)
        for alias in self.order:
            root = self.roots[alias]
            if actual == root:
                return alias
            if actual.is_relative_to(root):
                value = actual.relative_to(root).as_posix()
                if relative(value):
                    return alias + "/" + value
        raise ProtocolError("Compiler path is outside the approved toolchain.")

    def plan(self, judge, tu, raw, dl):
        text = judge.effective_source(tu, raw.decode("utf-8-sig", "replace"))
        flags, env, _roots = judge.compile_settings(text)
        base = judge.compiler_base(text)
        plan_flags = [f"-I@{self.portable(arg[2:])}" if arg.startswith("-I") and WIN.fullmatch(arg[2:])
                      else arg for arg in flags]
        portable_env = {}
        for name in PATH_ENV:
            if env.get(name):
                portable_env[name] = [self.portable(path) for path in env[name].split(";") if path]
        for name in PLAIN_ENV:
            if env.get(name):
                portable_env[name] = env[name]
        return {"tu": tu, "source": dl, "flags": base + ["-showIncludes", *plan_flags, "-Iinclude"],
                "env": portable_env, "contract": judge.compilation_contract(flags, env, base)}

    def dependency(self, record):
        if (not isinstance(record, list) or len(record) != 3 or not relative(record[1])):
            raise ProtocolError("Invalid compiler dependency record.")
        alias, rel, expected = record
        if alias == "source":
            if self.git_blobs.get(rel) != expected or rel not in self.git_blobs:
                raise ProtocolError("Compiler dependency differs from the reviewed source projection.")
            return alias, rel
        if alias not in self.roots:
            raise ProtocolError("Compiler dependency is outside the approved toolchain.")
        root = self.roots[alias]
        path = (root / rel).resolve(strict=True)
        if not path.is_relative_to(root):
            raise ProtocolError("Compiler dependency is outside the approved toolchain.")
        info = path.stat()
        key = (path, info.st_mtime_ns, info.st_size)
        if key not in self.hashes:
            self.hashes[key] = digest(read_regular(path, MAX_FILE))
        if self.hashes[key] != expected:
            raise ProtocolError("Compiler dependency differs from the approved toolchain.")
        return alias, rel


class CompilerPool:
    """The transport executable is installed by the operator and uses the dedicated worker lane."""
    def __init__(self, release, paths, source):
        self.release = release
        self.profile = release["worker_profile_sha256"]
        self.transport = Path(release["compiler_transport"])
        if not self.transport.is_absolute() or digest(read_regular(self.transport, MAX_FILE)) != release["transport_sha256"]:
            raise ProtocolError("Dedicated compiler transport differs from the approved release.")
        if release["priority"] != 2:
            raise ProtocolError("Unapproved compiler priority.")
        self.source = pack_sources(source)
        self.paths = paths

    def batch(self, plan):
        raw = json_bytes({"version": VERSION, "profile": self.profile, "source": self.source, "plan": plan})
        if len(raw) > MAX_REQUEST:
            raise ProtocolError("Compiler request exceeds its size limit.")
        with tempfile.TemporaryFile() as output:
            try:
                # The transport handles only public source data and uses its own restricted control channel.
                completed = subprocess.run(["prlimit", f"--fsize={MAX_REPLY}:{MAX_REPLY}", "--",
                                            str(self.transport), "compile", "--priority=2"],
                                           input=raw, stdout=output, stderr=subprocess.DEVNULL,
                                           env={"PATH": "/usr/bin:/bin", "LANG": "C"}, timeout=3600)
            except subprocess.TimeoutExpired as error:
                raise ProtocolError("Dedicated compiler transport timed out.") from error
            if completed.returncode:
                raise ProtocolError("Dedicated compiler transport is unavailable.")
            output.seek(0)
            wire = output.read(MAX_REPLY + 1)
        return self.results(plan, raw, wire)

    def results(self, plan, raw, wire):
        if len(wire) > MAX_REPLY:
            raise ProtocolError("Compiler reply exceeds its size limit.")
        envelope = json.loads(wire)
        worker = envelope.get("worker")
        permitted = self.release["verified_workers"].get(worker)
        if (not permitted or permitted["expires"] <= time.time()
                or permitted["probe"] != envelope.get("probe")
                or permitted["image"] != envelope.get("image")):
            raise ProtocolError("Compiler worker lacks a current isolation receipt.")
        response = envelope["result"]
        if (response["version"] != VERSION or response["request"] != digest(raw)
                or response["profile"] != self.profile or len(response["results"]) != len(plan)):
            raise ProtocolError("Compiler reply does not match the request.")
        out = {}
        for expected, row in zip(plan, response["results"], strict=True):
            if any(row.get(key) != expected[key] for key in ("tu", "source", "contract")):
                raise ProtocolError("Compiler reply does not match the TU and its inputs.")
            tu = expected["tu"]
            expected_keys = {"tu", "source", "contract", "status"}
            if row["status"] == "error" and set(row) == expected_keys | {"diagnostics"}:
                text = row["diagnostics"]
                if not isinstance(text, str) or not 0 < len(text) <= MAX_DIAGNOSTICS:
                    raise ProtocolError("Invalid bounded compiler diagnostics.")
                text = safe_diagnostics(tu, text, self.paths.git_blobs)
                if not text:
                    raise ProtocolError("Compiler diagnostic did not occur in the requested TU.")
                out[tu] = None, text, ()
                continue
            if row["status"] != "compiled" or set(row) != expected_keys | {"artifact", "sha256", "includes"}:
                raise ProtocolError("Unexpected compiler result fields.")
            data = decode(row["artifact"], MAX_OBJECT)
            if check_object(data) != row["sha256"]:
                raise ProtocolError("Compiler object digest differs from its receipt.")
            records = row["includes"]
            if (not isinstance(records, list) or len(records) > MAX_HEADERS):
                raise ProtocolError("Too many compiler dependencies.")
            dependencies = [self.paths.dependency(d) for d in records]
            if len(set(dependencies)) != len(dependencies):
                raise ProtocolError("Repeated compiler dependency.")
            out[tu] = data, "", tuple(dependencies)
        self.last_receipt = {"worker": worker, "image": permitted["image"], "probe": permitted["probe"],
                             "profile": self.profile, "request": digest(raw), "tu_count": len(out),
                             "compiled": sum(bool(row[0]) for row in out.values())}
        return out


class JudgeAdapter:
    def __init__(self, judge, release):
        self.judge = judge
        self.release = release
        if judge.tool_digest(judge.CL) != release["compiler_sha256"]:
            raise ProtocolError("The installed comparator expects a different compiler.")
        self.stock_prepare = judge.prepare_job
        self.results = {}
        self.paths = None

    def prepare(self, commit, job, needs_ledger):
        result = self.stock_prepare(commit, job, needs_ledger)
        if not needs_ledger:
            return result
        source, hashes = projection(Git(self.judge.BARE), commit)
        self.paths = TrustedPaths(self.release["compare_roots"], hashes)
        client = CompilerPool(self.release, self.paths, source)
        plan = []
        for tu in self.tus:
            raw = (job / tu).read_bytes()
            if digest(raw) != hashes.get(tu):
                raise ProtocolError("Trusted judge source and compiler projection disagree.")
            try:
                plan.append(self.paths.plan(self.judge, tu, raw, hashes[tu]))
            except ProtocolError:
                raise
            except ValueError:
                self.results[tu] = ("", (None, "Source requested an unsupported compiler option.", ()))
        for start in range(0, len(plan), MAX_PLAN):
            batch = plan[start:start + MAX_PLAN]
            artifacts = client.batch(batch)
            if self.release.get("cache"):
                trace = Path(self.release["cache"]) / "compiler-receipts.jsonl"
                with trace.open("a") as receipt:
                    receipt.write(json.dumps(client.last_receipt, separators=(",", ":")) + "\n")
            self.results.update((row["tu"], (row["contract"], artifacts[row["tu"]])) for row in batch)
        return result

    def compile_tu(self, job, tu):
        if tu not in self.results:
            raise ProtocolError("Trusted judge requested a TU outside the supplied compile plan.")
        contract, (data, failure, dependencies) = self.results[tu]
        source = job / tu
        raw = source.read_bytes()
        text = self.judge.effective_source(tu, raw.decode("utf-8-sig", "replace").replace("\r\n", "\n")
                                           .replace("\r", "\n"))
        if data is None:
            return None, failure, text

        obj = job / "obj" / (tu.replace("/", "_") + ".obj")
        obj.parent.mkdir(exist_ok=True)
        obj.write_bytes(data)
        headers = {}
        for role, label in dependencies:
            dependency = (job if role == "source" else self.paths.roots[role]) / label
            with dependency.open("rb") as stream:
                headers[str(dependency)] = hashlib.file_digest(stream, "sha256").hexdigest()
        obj.with_suffix(".obj.includes.json").write_text(json.dumps(list(headers)))
        receipt = {"compiler_contract": contract, "include_capture": "msvc-showIncludes-v1",
                   "source_sha256": digest(raw), "object_sha256": digest(data), "headers": headers}
        obj.with_suffix(".obj.compile.json").write_text(json.dumps(receipt))
        return obj, "", text

    def run(self, argv):
        files = [x for x in argv[1:] if not x.startswith("--")]
        options = [x for x in argv[1:] if x.startswith("--")]
        if (not argv or not files or "--json" not in options or set(options) - {"--json", "--cache-only"}
                or any(not source_path(tu) or not tu.startswith("src/") for tu in files)):
            raise ProtocolError("Trusted judge received unexpected arguments.")

        def misses_only(_args, misses, *_unused):
            self.tus = tuple(misses)
            return None

        self.judge.remote_judge = misses_only
        self.judge.prepare_job = self.prepare
        self.judge.compile_tu = self.compile_tu
        original = self.judge._judge_file

        def retain(tu):
            result = original(tu)
            if not result.get("cache_key") and not result.get("volatile_object"):
                self.judge.keep_volatile_object(self.judge._WORK_JOB, tu, result)
            return result

        self.judge._judge_file = retain
        return self.judge.main(argv)
