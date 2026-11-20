"""Nightly stage 1: compile every source file of the checked-out main commit with the sealed compiler.

  python3 -B ci/nightly/compile_main.py SHARD SHARDS OUT_DIR

Runs on the compiler image. Reuses the pull request check's own sealed-compiler audit, native compile commands and
per-file judge (ci/managed-check, ci/managed-nt2) by import, so a nightly verdict is the same verdict a pull request
gets. This shard takes the files whose position in the size-balanced assignment equals SHARD.

The source projection (every file under src/ and include/, packed for the compiler) is the same for every batch of a
run, so it is built once per runner and reused, not rebuilt for each batch of 8 files. Each batch logs its compiler
and comparison seconds separately. The sealed compiler takes one request at a time on this image.

Writes OUT_DIR/judge.jsonl (one judge result per file: functions, matches, rows, errors), OUT_DIR/obj/ (the
compiled objects with their compile receipts) and OUT_DIR/shard.json. All come from public source only.
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


def cpu_times():
    """(busy, steal, total) jiffies from /proc/stat, or None where it does not exist."""
    try:
        f = [int(x) for x in Path("/proc/stat").read_text().splitlines()[0].split()[1:]]
    except (OSError, ValueError, IndexError):
        return None
    steal = f[7] if len(f) > 7 else 0
    idle = f[3] + (f[4] if len(f) > 4 else 0)
    return sum(f) - idle - steal, steal, sum(f)


def host_facts(before, after):
    """CPU count, model and the share of CPU time the hypervisor took (steal) while this shard ran."""
    model = ""
    try:
        model = next((line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
                      if line.startswith("model name")), "")
    except OSError:
        pass
    out = {"cpus": os.cpu_count(), "cpu_model": model[:80]}
    if before and after and after[2] > before[2]:
        total = after[2] - before[2]
        out.update(busy_pct=round(100 * (after[0] - before[0]) / total, 1),
                   steal_pct=round(100 * (after[1] - before[1]) / total, 1))
    return out


def fail(expected, found):
    print(f"nightly compile: expected {expected}; found {found}", file=sys.stderr, flush=True)
    raise SystemExit(1)


def memoize_projection(measure_mod, compare_mod):
    """Build the source projection and its packed form once per process (same commit for every batch)."""
    built, packed = {}, {}
    original_projection, original_pack = measure_mod.projection, measure_mod.pack_sources

    def projection(git, revision):
        key = (str(git.path), revision)
        if key not in built:
            built[key] = original_projection(git, revision)
        return built[key]

    def pack_sources(files):
        key = id(files)
        if key not in packed or packed[key][0] is not files:
            packed[key] = (files, original_pack(files))
        return packed[key][1]

    measure_mod.projection = compare_mod.projection = projection
    measure_mod.pack_sources = pack_sources
    return built


def compile_files(files, out, label):
    """Compile and judge `files` (sorted TU paths) into out/; returns counts and batch seconds."""
    sha = os.environ.get("GITHUB_SHA", "")
    from common import PIN
    import compare as compare_mod
    from compare import native_commands, protected_judge
    from gitrepo import Git
    import measure as measure_mod
    from measure import audit, pin
    from wide import measure_batch

    built = memoize_projection(measure_mod, compare_mod)
    checkout = Git(Path.cwd() / ".git")
    head = checkout.rev("HEAD")
    if head != sha:
        fail(f"the checkout at the workflow commit {sha}", f"HEAD {head}")
    baseline = (Path.cwd() / "baseline/game.dat").resolve(strict=True)
    try:
        pin(baseline, PIN["baseline_sha256"])
    except ValueError:
        fail(f"baseline/game.dat with SHA-256 {PIN['baseline_sha256']}", "a different file")
    tools = audit(PIN)
    out.mkdir(parents=True, exist_ok=True)
    (out / "obj").mkdir(exist_ok=True)
    counts = {"files": len(files), "compiled": 0, "compile_errors": 0, "fully_matching": 0}
    batch_seconds = []
    split = {"compile": 0.0, "compare": 0.0}
    with tempfile.TemporaryDirectory(prefix="bfme-nightly-") as name, open(out / "judge.jsonl", "w") as log:
        work = Path(name)
        git = Git(work / "source.git", initialize=True)
        (git.path / "objects/info/alternates").write_text(str((checkout.path / "objects").resolve(strict=True)) + "\n")
        git.run("update-ref", "refs/heads/main", sha)
        judge = protected_judge(work / "home", tools, baseline)
        judge.BARE = git.path
        commands = native_commands(git, judge, sha, files, tools)
        for begin in range(0, len(commands), BATCH):
            batch = commands[begin:begin + BATCH]
            names = [c["tu"] for c in batch]
            plan = dict(PIN, historical_base=sha, historical_head=sha, request_paths=names,
                        compile={"head": batch}, changed_paths=[])
            job = work / f"batch-{begin}"
            t0 = monotonic()
            spans = {}
            results = measure_batch(git, judge, "head", plan, tools, job, timing=spans)
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
            batch_seconds.append(round(monotonic() - t0, 1))
            for stage in ("compile", "compare"):
                split[stage] += spans.get(stage, 0.0)
            print(f"Nightly {label}: batch {begin // BATCH + 1}, {len(names)} files, {batch_seconds[-1]:.1f} s "
                  f"(compiler {spans.get('compile', 0.0):.1f} s, comparison {spans.get('compare', 0.0):.1f} s).", flush=True)
    counts["projections_built"] = len(built)
    counts["compiler_s"] = round(split["compile"], 1)
    counts["comparison_s"] = round(split["compare"], 1)
    return counts, batch_seconds


def main(shard, shards, out):
    shard, shards, out = int(shard), int(shards), Path(out)
    sha = os.environ.get("GITHUB_SHA", "")
    started = monotonic()
    cpu0 = cpu_times()
    from gitrepo import Git
    sizes = source_files(Git(Path.cwd() / ".git"), sha)
    mine = assign(sizes, shards)[shard]
    print(f"Nightly shard {shard + 1} of {shards}: {len(mine)} of {len(sizes)} source files.", flush=True)
    counts, batch_seconds = compile_files(mine, out, f"shard {shard + 1}")
    counts["seconds"] = round(monotonic() - started, 1)
    ordered = sorted(batch_seconds)
    counts["batch_median_s"] = ordered[len(ordered) // 2] if ordered else None
    counts["host"] = host_facts(cpu0, cpu_times())
    (out / "shard.json").write_text(json.dumps(dict(counts, shard=shard, shards=shards, sha=sha), sort_keys=True) + "\n")
    print("Nightly shard summary: " + json.dumps(counts, sort_keys=True), flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        fail("arguments SHARD SHARDS OUT_DIR", " ".join(sys.argv[1:]) or "none")
    main(*sys.argv[1:])
