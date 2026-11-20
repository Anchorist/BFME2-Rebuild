"""Prove that the state kept commit by commit equals a fresh measurement.

    python3 -B ci/state/parity.py target
        -> GITHUB_OUTPUT sha=<main commit the state branch describes>
    python3 -B ci/state/parity.py sample-plan --checkout DIR --main SHA --day YYYY-MM-DD --out plan.json
        -> a one-batch measurement plan holding the night's sample of source files
    python3 -B ci/state/parity.py compare --snapshot full.json --main SHA --tree TREE
    python3 -B ci/state/parity.py compare-sample --shard state-shard-0.json --main SHA
        -> GITHUB_OUTPUT result=equal|differs|inconclusive

Nightly sample: the source files of SHA, sorted, are dealt into SAMPLE_GROUPS groups by
position (file i goes to group i mod SAMPLE_GROUPS); the night's group is the day number
modulo SAMPLE_GROUPS, so every file is measured afresh once in SAMPLE_GROUPS nights and each
night's sample spreads over the whole tree. One compiler job measures it (one runner start);
each file's fresh result must equal its record on the state branch.
The full check measures every file with nothing carried over (about 104 runner starts) and is
started by hand. Both use the same tools as every push (`ci/managed-state/`).
The token (READ_TOKEN, contents: read) is removed from the environment at once.
"""
import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout import PREFIX, Refused, differences, join, normalized, split, unit_from  # noqa: E402
from state_snapshot import OID, authoritative_units, unit_status  # noqa: E402
import store  # noqa: E402

SAMPLE_GROUPS = 102  # 3,253 files -> 31 or 32 a night, one compiler job of at most 32


def open_state(folder, remote, token):
    git = store.Git(Path(folder) / "state.git", remote, token)
    tip = store.remote_tip(git)
    store.fetch(git, tip)
    return git, tip


def target(remote, token):
    with tempfile.TemporaryDirectory() as folder:
        git, tip = open_state(folder, remote, token)
        if not tip:
            raise Refused("parity target: expected a state branch, found none; publish one state first")
        return store.published_main(git, tip)


def sample(units, day):
    group = date.fromisoformat(day).toordinal() % SAMPLE_GROUPS
    return units[group::SAMPLE_GROUPS]


def sample_plan(checkout, main, day, checker):
    if not OID.fullmatch(main):
        raise Refused(f"sample plan: expected a 40-hex main commit, found {main!r}")
    units = authoritative_units(Path(checkout), main)
    picked = sample(units, day)
    if not picked:
        raise Refused(f"sample plan: expected source files on {main}, found none")
    return {"schema": 1, "main": main, "checker": checker, "batches": [picked]}


def compare(snapshot_path, main, tree, remote, token, out=print):
    full = normalized(json.loads(Path(snapshot_path).read_bytes()))
    if full["sha"] != main:
        raise Refused(f"parity: expected a full measurement of {main}, found one of {full['sha']}")
    with tempfile.TemporaryDirectory() as folder:
        git, _ = open_state(folder, remote, token)
        commit = store.find_state(git, main)
        if not commit:
            out(f"Inconclusive: the state branch has no state for main {main} to compare with.")
            return "inconclusive", []
        incremental = normalized(join(store.reader(git, commit)))
        lines = differences(full, incremental)
        # Byte check of the published files themselves, not only the parsed values.
        expected_files = split(full, tree)
        read = store.reader(git, commit)
        for path in ("index.json",) + tuple(sorted(p for p in expected_files if p.startswith("files/"))):
            if read(path) != expected_files[path]:
                lines.append(f"{path}: expected the full-recompute bytes, found different bytes on state {commit}")
                if len(lines) > 25:
                    break
        if lines:
            out(f"DIFFERS: full recompute of {main} vs state {commit}:")
            for line in lines:
                out("  " + line)
            return "differs", lines
        out(f"Equal: full recompute of {main} equals state {commit} byte for byte "
            f"({len(full['tus'])} files).")
        return "equal", []


def compare_sample(shard_path, main, remote, token, out=print):
    shard = json.loads(Path(shard_path).read_bytes())
    if shard.get("main") != main or not isinstance(shard.get("units"), dict) or not shard["units"]:
        raise Refused(f"sample: expected a measurement of {main} with source files, "
                      f"found main {shard.get('main')!r} with {len(shard.get('units') or {})} files")
    fresh = {tu: unit_status(unit) for tu, unit in shard["units"].items()}
    with tempfile.TemporaryDirectory() as folder:
        git, _ = open_state(folder, remote, token)
        commit = store.find_state(git, main)
        if not commit:
            out(f"Inconclusive: the state branch has no state for main {main} to compare with.")
            return "inconclusive", []
        read = store.reader(git, commit)
        index = json.loads(read("index.json"))
        if index.get("checker") != shard.get("checker"):
            out(f"Inconclusive: the state of {main} was measured with checker {index.get('checker')}, "
                f"this sample with {shard.get('checker')}.")
            return "inconclusive", []
        kept = {}
        for tu in fresh:
            if tu not in index["files"]:
                kept[tu] = None
                continue
            kept[tu] = unit_from(json.loads(read(PREFIX + tu + ".json")))
        wanted = {"schema": 1, "sha": main, "checker": shard["checker"], "tus": fresh}
        found = {"schema": 1, "sha": main, "checker": shard["checker"],
                 "tus": {tu: unit for tu, unit in kept.items() if unit is not None}}
        lines = differences(wanted, found)
        if lines:
            out(f"DIFFERS: fresh measurement of {len(fresh)} sampled files of {main} vs state {commit}:")
            for line in lines:
                out("  " + line)
            return "differs", lines
        out(f"Equal: {len(fresh)} sampled files of {main} measured afresh equal their records on state {commit}.")
        return "equal", []


def pin_checker(checkout):
    sys.path.insert(0, str(Path(checkout).resolve() / "ci/managed-check"))
    from common import PIN  # noqa: E402  (the checked-out commit's own comparison tools)
    return PIN["checker"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["target", "sample-plan", "compare", "compare-sample"])
    parser.add_argument("--snapshot")
    parser.add_argument("--shard")
    parser.add_argument("--main")
    parser.add_argument("--tree")
    parser.add_argument("--checkout", default=".")
    parser.add_argument("--day")
    parser.add_argument("--out")
    parser.add_argument("--remote")
    parser.add_argument("--report", default="")
    args = parser.parse_args()
    token = os.environ.pop("READ_TOKEN", "")
    remote = args.remote or f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', '')}.git"
    output = os.environ.get("GITHUB_OUTPUT", os.devnull)
    try:
        if args.mode == "target":
            sha = target(remote, token)
            print(f"Parity target: main {sha}, the commit the state branch describes now.")
            with open(output, "a") as stream:
                stream.write(f"sha={sha}\n")
            return 0
        if args.mode == "sample-plan":
            plan = sample_plan(args.checkout, args.main, args.day, pin_checker(args.checkout))
            Path(args.out).write_text(json.dumps(plan, sort_keys=True, separators=(",", ":")) + "\n")
            print(f"Sample for {args.day}: {len(plan['batches'][0])} source files of {args.main}, "
                  f"group {date.fromisoformat(args.day).toordinal() % SAMPLE_GROUPS} of {SAMPLE_GROUPS}.")
            return 0
        if args.mode == "compare":
            result, lines = compare(args.snapshot, args.main, args.tree, remote, token)
        else:
            result, lines = compare_sample(args.shard, args.main, remote, token)
    except (Refused, ValueError) as error:
        print(f"::error::{error}")
        return 1
    with open(output, "a") as stream:
        stream.write(f"result={result}\n")
    if args.report:
        Path(args.report).write_text("\n".join(lines) + "\n")
    return 1 if result == "differs" else 0


if __name__ == "__main__":
    sys.exit(main())
