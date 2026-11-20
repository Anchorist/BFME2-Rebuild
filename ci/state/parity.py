"""Prove that the state kept commit by commit equals measuring everything again.

    python3 -B ci/state/parity.py target              -> GITHUB_OUTPUT sha=<main the state branch describes>
    python3 -B ci/state/parity.py compare --snapshot full.json --main <sha>
                                                      -> GITHUB_OUTPUT result=equal|differs|inconclusive

The full snapshot comes from the same tools as every push (`ci/managed-state/`),
run with no carried results. The comparison is of the canonical per-file
records, so equal means byte-for-byte equal on the state branch.
The token (READ_TOKEN, contents: read) is removed from the environment at once.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout import Refused, differences, join, normalized, split  # noqa: E402
import store  # noqa: E402


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["target", "compare"])
    parser.add_argument("--snapshot")
    parser.add_argument("--main")
    parser.add_argument("--tree")
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
        result, lines = compare(args.snapshot, args.main, args.tree, remote, token)
    except Refused as error:
        print(f"::error::{error}")
        return 1
    with open(output, "a") as stream:
        stream.write(f"result={result}\n")
    if args.report:
        Path(args.report).write_text("\n".join(lines) + "\n")
    return 1 if result == "differs" else 0


if __name__ == "__main__":
    sys.exit(main())
