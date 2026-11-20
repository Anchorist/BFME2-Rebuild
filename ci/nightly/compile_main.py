"""Nightly stage 1: compile every source file of the checked-out main commit with the sealed compiler.

  python3 -B ci/nightly/compile_main.py SHARD SHARDS OUT_DIR

Runs on the compiler image. Reuses the pull request check's own sealed-compiler audit, native compile commands and
per-file judge (ci/managed-check, ci/managed-nt2) by import, so a nightly verdict is the same verdict a pull request
gets. This shard takes the files whose position in the size-balanced assignment equals SHARD.

Writes OUT_DIR/judge.jsonl (one judge result per file: functions, matches, rows, errors) and OUT_DIR/obj/ (the
compiled objects with their compile receipts). Both come from public source only.
"""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from time import monotonic

ROOT = Path(__file__).resolve().parent
CHECK = ROOT.parent / "managed-check"
sys.path.insert(0, str(CHECK))

from plan_shards import assign, source_files  # noqa: E402

BATCH = 8


def fail(expected, found):
    print(f"nightly compile: expected {expected}; found {found}", file=sys.stderr, flush=True)
    raise SystemExit(1)


def main(shard, shards, out):
    shard, shards, out = int(shard), int(shards), Path(out)
    sha = os.environ.get("GITHUB_SHA", "")
    from common import PIN
    from compare import native_commands, protected_judge
    from gitrepo import Git
    from measure import audit, pin
    from wide import measure_batch

    checkout = Git(Path.cwd() / ".git")
    head = checkout.rev("HEAD")
    if head != sha:
        fail(f"the checkout at the workflow commit {sha}", f"HEAD {head}")
    baseline = (Path.cwd() / "baseline/game.dat").resolve(strict=True)
    try:
        pin(baseline, PIN["baseline_sha256"])
    except ValueError:
        fail(f"baseline/game.dat with SHA-256 {PIN['baseline_sha256']}", "a different file")
    started = monotonic()
    tools = audit(PIN)
    out.mkdir(parents=True, exist_ok=True)
    (out / "obj").mkdir(exist_ok=True)
    sizes = source_files(checkout, sha)
    mine = assign(sizes, shards)[shard]
    print(f"Nightly shard {shard + 1} of {shards}: {len(mine)} of {len(sizes)} source files.", flush=True)
    counts = {"files": len(mine), "compiled": 0, "compile_errors": 0, "fully_matching": 0}
    with tempfile.TemporaryDirectory(prefix="bfme-nightly-") as name, open(out / "judge.jsonl", "w") as log:
        work = Path(name)
        git = Git(work / "source.git", initialize=True)
        (git.path / "objects/info/alternates").write_text(str((checkout.path / "objects").resolve(strict=True)) + "\n")
        git.run("update-ref", "refs/heads/main", sha)
        judge = protected_judge(work / "home", tools, baseline)
        judge.BARE = git.path
        commands = native_commands(git, judge, sha, mine, tools)
        for begin in range(0, len(commands), BATCH):
            batch = commands[begin:begin + BATCH]
            names = [c["tu"] for c in batch]
            plan = dict(PIN, historical_base=sha, historical_head=sha, request_paths=names,
                        compile={"head": batch}, changed_paths=[])
            job = work / f"batch-{begin}"
            t0 = monotonic()
            results = measure_batch(git, judge, "head", plan, tools, job)
            if list(results) != names:
                fail(f"a judge result for each of {len(names)} files", f"{len(results)} results")
            for tu in names:
                res = dict(results[tu], tu=tu)
                obj = job / "obj" / (tu.replace("/", "_") + ".obj")
                if obj.is_file():
                    counts["compiled"] += 1
                    for suffix in (".obj", ".obj.compile.json"):
                        shutil.copyfile(obj.with_suffix(suffix), out / "obj" / obj.with_suffix(suffix).name)
                else:
                    counts["compile_errors"] += 1
                if res.get("functions") and res.get("function_match") == res.get("functions"):
                    counts["fully_matching"] += 1
                keep = {k: res.get(k) for k in ("tu", "functions", "function_match", "object_verified", "gates", "error")}
                keep["rows"] = [{"rva": r.get("rva"), "status": r.get("status")} for r in res.get("rows", [])]
                log.write(json.dumps(keep, sort_keys=True) + "\n")
            shutil.rmtree(job, ignore_errors=True)
            print(f"Nightly shard {shard + 1}: batch {begin // BATCH + 1}, {len(names)} files, "
                  f"{monotonic() - t0:.1f} s.", flush=True)
    counts["seconds"] = round(monotonic() - started, 1)
    (out / "shard.json").write_text(json.dumps(dict(counts, shard=shard, shards=shards, sha=sha), sort_keys=True) + "\n")
    print("Nightly shard summary: " + json.dumps(counts, sort_keys=True), flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        fail("arguments SHARD SHARDS OUT_DIR", " ".join(sys.argv[1:]) or "none")
    main(*sys.argv[1:])
