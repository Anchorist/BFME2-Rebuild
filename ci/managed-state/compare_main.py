"""Measure one complete exact-main state shard with the sealed managed compiler."""
import os
from pathlib import Path
import sys
import tempfile

CHECK = Path(__file__).resolve().parent.parent / "managed-check"
sys.path.insert(0, str(CHECK))

from common import PIN, HEX40
from compare import native_commands, protected_judge
from gitrepo import Git
from state_compact import compact
from state_evidence import header, make_entry, native_record
from measure import audit, data_entry, measure, pin
from state_snapshot import MAX_PLAN_BYTES, MAX_SHARD_BYTES, canonical, digest, load, validate_plan


def measured(repository, main, units, *, capture=False):
    if not HEX40.fullmatch(main):
        raise ValueError("Use the full exact protected main revision.")
    required = Git(repository / ".git")
    if required.rev("HEAD") != main:
        raise ValueError("The protected state runner checked out a different commit.")
    reference = repository / "baseline/game.dat"
    pin(reference, PIN["baseline_sha256"])
    tools = audit(PIN)
    all_results, evidence = [], {}
    with tempfile.TemporaryDirectory(prefix="bfme-state-native-") as folder:
        work = Path(folder)
        git = Git(work / "main.git", initialize=True)
        (git.path / "objects/info/alternates").write_text(str((required.path / "objects").resolve()) + "\n")
        git.run("update-ref", "refs/heads/main", main)
        judge = protected_judge(work / "home", tools, reference)
        judge.BARE = git.path
        allowance = "config/asm_allowlist.json"
        has_allowance = git.run("cat-file", "-e", f"{main}:{allowance}", check=False).returncode == 0
        for first in range(0, len(units), 8):
            batch = units[first:first + 8]
            plan = {**PIN, "historical_base": main, "request_paths": batch, "compile": {
                "base": native_commands(git, judge, main, batch, tools)}}
            batch_dir = work / f"batch-{first}"
            outcomes = measure(git, judge, "base", plan, tools, batch_dir)
            if list(outcomes) != batch:
                raise ValueError("The trusted state comparator omitted a planned translation unit.")
            if capture:
                for command in plan["compile"]["base"]:
                    tu = command["tu"]
                    evidence[tu] = make_entry(judge, command, outcomes[tu], batch_dir)
            if has_allowance:
                # The narrow route omits this file. Reuse the authenticated COFF
                # with the same approved allowance the paired wide route applies.
                data_entry(git, main, allowance, batch_dir)
                ledger = judge.ledger(batch_dir)
                outcomes = {tu: judge.judge_tu(batch_dir, tu, ledger) for tu in batch}
                if capture:
                    for tu, outcome in outcomes.items():
                        wide = native_record(outcome)
                        if wide != evidence[tu]["native"]:
                            evidence[tu]["wide_native"] = wide
            all_results.extend(outcomes.values())
    return (all_results, evidence) if capture else all_results


def shard(root, plan, batch, output, engine=None, *, evidence_output=None):
    validate_plan(plan)
    if plan["main"] != os.environ["GITHUB_SHA"] or plan["checker"] != PIN["checker"]:
        raise ValueError("The state plan does not match the workflow checkout and checker.")
    if not 0 <= batch < len(plan["batches"]):
        raise ValueError("Use an assigned state shard.")
    units = plan["batches"][batch]
    if evidence_output:
        results, evidence = (engine or measured)(root, plan["main"], units, capture=True)
        tree = Git(root / ".git").value("rev-parse", plan["main"] + "^{tree}")
        cache = header(plan["main"], tree) | {"plan": digest(plan), "batch": batch, "evidence": evidence}
        bits = canonical(cache)
        if len(bits) > MAX_SHARD_BYTES:
            raise ValueError("The state evidence shard exceeds its artifact cap.")
        with evidence_output.open("xb") as stream:
            stream.write(bits)
    else:
        results = (engine or measured)(root, plan["main"], units)
    raw = {"binding": {}, "results": results}
    status = compact(raw, units)
    record = {"schema": 1, "main": plan["main"], "checker": plan["checker"], "plan": digest(plan),
              "batch": batch, "units": status}
    contents = canonical(record)
    if len(contents) > MAX_SHARD_BYTES:
        raise ValueError("The state shard exceeds its artifact cap.")
    with output.open("xb") as stream:
        stream.write(contents)


if __name__ == "__main__":
    os.umask(0o077)
    plan_file, batch_number, outfile, *cache = sys.argv[1:]
    shard(Path.cwd(), load(Path(plan_file), MAX_PLAN_BYTES), int(batch_number), Path(outfile),
          evidence_output=Path(cache[0]) if cache else None)

