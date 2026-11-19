"""Recompile and judge both sides of the exact private nt2 canary in a Boat job."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace

from diff_scope import diff_lines
from edited_functions import edited
from finished_index import Owners

from gitrepo import Git
from pool_compare import projection, TrustedPaths
from pool_protocol import MAX_OBJECT, check_object, contributed_source_problem, decode, digest, pack_sources

ROOT = Path(__file__).resolve().parent
SEALED = Path("/opt/boat-compiler")
ENTRY = Path("/usr/local/libexec/bfme2-compiler/run")
ENTRY_SHA = "3c5253ceace321aa6855d5f313a951f2db79ab00cbb06bcd78c0c80d08fa7630"
PROBE_SHA = "88888c03f6f12eedd455273f0cd131ef7637dba66f83503bf29ed89544b208ab"
COMPILER = "2ecf86a3edfd3deae498e08298e210e984537ce9e11759930561e43f40bd2515"
MAX_REPLY = 96 * 1024**2
CONFIG = ("map.json", "symbols.json", "header_manifest.json")


def file_hash(path):
    with Path(path).open("rb") as data:
        return hashlib.file_digest(data, "sha256").hexdigest()


def pin(path, expected):
    if not path.is_file() or file_hash(path) != expected:
        raise ValueError("A protected compiler or comparison input differs from its approved digest.")


def request(operation, payload=b"", limit=MAX_REPLY):
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        ran = subprocess.run(["/usr/bin/prlimit", f"--fsize={limit}:{limit}", "--",
                              "/usr/bin/sudo", "-n", "--", str(ENTRY), operation], input=payload,
                             stdout=output, stderr=errors, close_fds=True, timeout=480,
                             env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"}, check=False)
        output.seek(0)
        raw = output.read(limit + 1)
        if ran.returncode or not 0 < len(raw) <= limit:
            raise RuntimeError("The sealed compiler job was unavailable.")
    return json.loads(raw)


def audit(plan):
    pin(ENTRY, ENTRY_SHA)
    pin(ENTRY.with_name("managed_probe.py"), PROBE_SHA)
    pin(SEALED / "worker.json", plan["profile_sha256"])
    pin(SEALED / "image-inventory.json", plan["image_sha256"])
    proof = request("probe", limit=65536)
    fields = ("private_paths_absent", "private_mounts_absent", "credential_environment_absent",
              "network_sockets_denied", "network_namespace_private", "unprivileged_compiler",
              "no_inherited_network_descriptors", "no_new_privileges")
    if (proof["profile"] != plan["profile_sha256"] or proof["compiler_sha256"] != COMPILER
            or proof["image_inventory_verified"] is not True
            or any(proof["checks"].get(key) is not True for key in fields)):
        raise ValueError("The compiler process did not prove the required isolation.")
    return json.loads((SEALED / "worker.json").read_bytes())["roots"]


def setup_home(home, tools, baseline):
    runner = home / "bfme2-runner/repo"
    runner.mkdir(parents=True)
    (runner / "tools").symlink_to(ROOT / "engine/reference")
    install = runner / "baselines/bfme2/workshop-vanilla-1.06/files"
    install.mkdir(parents=True)
    (install / "game.dat").symlink_to(baseline)
    gen = home / "pilot/gen"
    (gen / "wine/dosdevices").mkdir(parents=True)
    (gen / "wine/dosdevices/z:").symlink_to("/")
    links = {"stlport45": runner / "vendor/stlport", "stlport46": runner / "vendor/stlport-4.6",
             "dx": runner / "vendor/dxsdk-aug2005/Include",
             "allocator": runner / "reference/shims/bfmealloc_alloconly",
             "overlay": gen / "build/stlport46"}
    for label, path in links.items():
        if label in tools:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(tools[label])
    os.environ.update(HOME=str(home), VC71_ROOT=str(tools["vc"]), PILOT_REMOTE="0")
    sys.path.insert(0, str(ROOT / "engine/gen/bin"))
    import judge
    judge.build.EXE = baseline
    judge.record_replay = lambda *_args, **_kwargs: None
    return judge


def data_entry(git, rev, name, root, *, max_size=128 * 1024**2):
    oid = f"{rev}:{name}"
    if int(git.value("cat-file", "-s", oid)) > max_size:
        raise ValueError("A protected ledger blob exceeds its cap.")
    data = git.run("cat-file", "blob", oid).stdout
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def measure(git, judge, side, plan, tools, job):
    base = plan["historical_base"]
    sha = plan["historical_" + side]
    sources, hashes = projection(git, sha)
    rows = plan["compile"][side]
    if [row["tu"] for row in rows] != plan["request_paths"] or len(rows) > 8:
        raise ValueError("The exact paired compiler plan changed.")
    if any(row["source"] != hashes.get(row["tu"]) for row in rows):
        raise ValueError("The TU source differs from the exact recorded native plan.")
    if side == "head":
        changes = git.changes(base, sha)
        if sorted(change.path for change in changes) != plan["changed_paths"]:
            raise ValueError("The canary's changed paths drifted.")
        for change in changes:
            if change.mode != "000000" and contributed_source_problem(decode(sources[change.path], 1024**2)):
                raise ValueError("The canary violated compiler source-input policy.")
    wire = json.dumps({"version": 1, "profile": plan["profile_sha256"],
                       "source": pack_sources(sources), "plan": rows},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    if len(wire) > 92 * 1024**2:
        raise ValueError("The compiler input is too large.")
    reply = request("compile", wire)
    if (reply["version"] != 1 or reply["request"] != digest(wire)
            or reply["profile"] != plan["profile_sha256"] or len(reply["results"]) != len(rows)):
        raise ValueError("The compiler response is incompatible with the exact source plan.")
    receipts = {}
    paths = TrustedPaths(tools, hashes)
    (job / "obj").mkdir(parents=True)
    for file in CONFIG:
        data_entry(git, base, "config/" + file, job)
    for want, value in zip(rows, reply["results"], strict=True):
        tu = want["tu"]
        if any(want[key] != value[key] for key in ("tu", "source", "contract")):
            raise ValueError("A compiler result changed its input identity.")
        data_entry(git, base, "expected/" + tu[4:] + ".json", job)
        needed = {tu}
        obj = job / "obj" / (tu.replace("/", "_") + ".obj")
        if value["status"] == "compiled":
            object_data = decode(value["artifact"], MAX_OBJECT)
            if check_object(object_data) != value["sha256"]:
                raise ValueError("The COFF does not match its compiler receipt.")
            found = [paths.dependency(row) for row in value["includes"]]
            if len(set(found)) != len(found):
                raise ValueError("The compiler receipt repeated a dependency.")
            needed.update(path for kind, path in found if kind == "source")
            headers = {(job if kind == "source" else Path(tools[kind])) / file for kind, file in found}
            for filename in needed:
                target = job / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(decode(sources[filename], 1024**2))
            obj.write_bytes(object_data)
            obj.with_suffix(".obj.includes.json").write_text(json.dumps(sorted(map(str, headers))))
            obj.with_suffix(".obj.compile.json").write_text(json.dumps(
                {"source_sha256": value["source"], "object_sha256": value["sha256"],
                 "headers": {str(path): file_hash(path) for path in sorted(headers)},
                 "compiler_contract": value["contract"]}))
            receipts[tu] = obj, ""
        elif value["status"] == "error" and isinstance(value["diagnostics"], str) and 0 < len(value["diagnostics"]) <= 2048:
            data_entry(git, sha, tu, job, max_size=1024**2)
            receipts[tu] = None, value["diagnostics"]
        else:
            raise ValueError("The compiler returned an unsupported outcome.")

    def precompiled(work, name):
        obj, error = receipts[name]
        raw = (work / name).read_text(encoding="utf-8-sig", errors="replace")
        return obj, error, judge.effective_source(name, raw)

    judge.compile_tu = precompiled
    ledger = judge.ledger(job)
    return {tu: judge.judge_tu(job, tu, ledger) for tu in plan["request_paths"]}


def reduced(before, after):
    counts = {"gained": 0, "lost_credit": 0, "lost_proof": 0, "lost_verified": 0,
              "new_compiler_errors": 0, "new_source_gates": 0}
    for path in sorted(before):
        old, new = before[path], after[path]
        current = {row["rva"]: row for row in new["rows"]}
        prior = {row["rva"]: row for row in old["rows"]}
        counts["gained"] += sum(r["credited"] and not prior.get(r["rva"], {}).get("credited") for r in current.values())
        counts["lost_credit"] += sum(r["credited"] and not current.get(r["rva"], {}).get("credited") for r in prior.values())
        counts["lost_proof"] += sum(r.get("proof") == "proven" and current.get(r["rva"], {}).get("proof") != "proven"
                                    for r in prior.values())
        counts["lost_verified"] += int(old["object_verified"] and not new["object_verified"])
        counts["new_compiler_errors"] += int(not old.get("error") and bool(new.get("error")))
        counts["new_source_gates"] += len(set(new["gates"]) - set(old["gates"]))
    return counts


def public_rows(git, judge, plan, old, new):
    base, head = plan["historical_base"], plan["historical_head"]
    adapter = SimpleNamespace(ANNOT=judge.ANNOT, land_gate9=SimpleNamespace(diff_lines=diff_lines))
    scope = edited(git, adapter, base, head, Owners(git, base))

    def verdict(table, path, address):
        row = next((row for row in table.get(path, {}).get("rows", [])
                    if int(row["rva"], 16) == address), None)
        if row is None:
            return "UNMEASURED"
        status = row["status"]
        return status + " / " + row.get("proof", "unproven") if status == "MATCH" else status

    output = []
    for item in scope:
        address = item["address"]
        if address is None:
            raise ValueError("A contributor-edited canary function lacks an exact owned row.")
        output.append({name: item[name] for name in ("path", "function", "line")} |
                      {"rva": f"0x{address:08X}", "before": verdict(old, item["owner"], address),
                       "after": verdict(new, item["owner"], address)})
    return output


def main():
    os.umask(0o077)
    started = time.monotonic()
    input_path = Path(sys.argv[1]).resolve(strict=True)
    plan = json.loads((ROOT / "nt2-plan.json").read_bytes())
    git = Git(input_path / "inputs.git")
    expected = json.loads((ROOT / "nt2-expected.json").read_bytes())
    admission = json.loads((input_path / "admission.json").read_bytes())
    for side, ref in (("base", "refs/heads/main"), ("head", "refs/ci/candidate")):
        if git.rev(ref) != plan["historical_" + side] or admission[side] != git.rev(ref):
            raise ValueError("The private PR input moved after authorization.")
    if (git.value("rev-parse", "refs/ci/candidate^{tree}") != plan["candidate_tree"]
            or git.rev("refs/ci/candidate^") != plan["historical_base"]):
        raise ValueError("The canary no longer has the exact recorded parent and tree.")
    baseline = (Path.cwd() / "baseline/game.dat").resolve(strict=True)
    pin(baseline, plan["baseline_sha256"])
    tools = audit(plan)
    with tempfile.TemporaryDirectory(prefix="bfme-nt2-match-") as folder:
        work = Path(folder)
        judge = setup_home(work / "home", tools, baseline)
        if judge.checker_hash() != plan["checker"]:
            raise ValueError("The standalone native checker digest differs from the approved comparator.")
        judge.BARE = git.path
        old = measure(git, judge, "base", plan, tools, work / "base")
        new = measure(git, judge, "head", plan, tools, work / "head")
        counts = reduced(old, new)
        rows = public_rows(git, judge, plan, old, new)
    elapsed = time.monotonic() - started
    acceptable = expected["expected"] == "pass" and counts == expected["counts"] and rows == expected["functions"]
    message = "Pass" if acceptable else "Fail"
    note = [f"## BFME II managed match canary · {message}", "",
            f"Private PR #{admission['number']}, head {admission['head']}, base {admission['base']}.", "",
            f"Protected workflow and reference commit {admission['workflow_sha']}.", "",
            f"Three translation units compiled on both sides in {elapsed:.3f}s of job time.",
            f"Native checker {plan['checker']}.", "", "| Measurement | Count |", "| --- | ---: |"]
    note.extend(f"| {name.replace('_', ' ')} | {value} |" for name, value in counts.items())
    note += ["", "| Changed function | Edited source | Address | Before | After |",
             "| --- | --- | --- | --- | --- |"]
    for item in rows:
        note.append(f"| {item['function']} | {item['path']}:{item['line']} | {item['rva']} | {item['before']} | {item['after']} |")
    if not acceptable:
        note += ["", "The managed result differs from the exact archived srv1 result."]
    note += ["", "This private canary checks the compiler and the native function, proof and object comparisons."]
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a") as report:
        report.write("\n".join(note) + "\n")
    return 0 if acceptable else 1


if __name__ == "__main__":
    raise SystemExit(main())

