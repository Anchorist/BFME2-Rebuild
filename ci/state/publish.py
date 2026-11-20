"""Publish one measured main state to the `state` branch, one small file per source file.

    python3 -B ci/state/publish.py --snapshot state.json --main <sha> --checkout . [--drill]

The token is read from STATE_TOKEN and removed from the environment at once.
`--remote` (default: this repository on GitHub) exists for the offline tests.
`--drill` deliberately removes one source file from the input before checking it:
the check must refuse it and the alarm must open. It is for the alarm test only.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout import Refused, check_snapshot, differences, join, normalized, split  # noqa: E402
from state_snapshot import OID, authoritative_units  # noqa: E402
import store  # noqa: E402

MAX_SNAPSHOT = 64 * 1024**2


def local(checkout, *args):
    done = subprocess.run(["git", "-C", str(checkout), *args], capture_output=True, timeout=120)
    return done.returncode, done.stdout.decode().strip()


def publish(snapshot_path, main, checkout, remote, token, *, drill=False, attempts=3, out=print):
    if not OID.fullmatch(main):
        raise Refused(f"main commit: expected 40 hex digits, found {main!r}")
    code, tree = local(checkout, "rev-parse", "--verify", main + "^{tree}")
    if code:
        raise Refused(f"main commit: expected {main} in the checkout, found it missing")
    _, date = local(checkout, "show", "-s", "--format=%ct +0000", main)
    raw = Path(snapshot_path).read_bytes()
    if len(raw) > MAX_SNAPSHOT:
        raise Refused(f"state input: expected at most {MAX_SNAPSHOT} bytes, found {len(raw)}")
    snapshot = json.loads(raw)
    if drill:
        victim = sorted(snapshot.get("tus", {}))[:1]
        for tu in victim:
            del snapshot["tus"][tu]
        out(f"DRILL: removed {victim} from the input on purpose; the next check must refuse it.")
    check_snapshot(snapshot, main, authoritative_units(Path(checkout), main))
    files = split(snapshot, tree)
    wanted = normalized(snapshot)
    with tempfile.TemporaryDirectory(prefix="bfme-state-") as folder:
        git = store.Git(Path(folder) / "state.git", remote, token)
        for attempt in range(1, attempts + 1):
            tip = store.remote_tip(git)
            store.fetch(git, tip)
            old_index = {}
            if tip:
                previous = store.published_main(git, tip)
                if previous == main:
                    found = normalized(join(store.reader(git, tip)))
                    if found != wanted:
                        raise Refused("state branch: expected the published state of " + main
                                      + " to equal this measurement, found differences: "
                                      + " | ".join(differences(wanted, found, 5)))
                    out(f"Already published: state {tip} describes main {main} with the same verdicts.")
                    return tip, 0
                if previous and local(checkout, "merge-base", "--is-ancestor", main, previous)[0] == 0:
                    out(f"Skipped: the state branch already describes {previous}, which is newer than {main}.")
                    return "", 0
                old_index = json.loads(store.reader(git, tip)("index.json"))["files"]
            new_index = json.loads(files["index.json"])["files"]
            changed = sum(old_index.get(tu) != digest for tu, digest in new_index.items()) + \
                len(set(old_index) - set(new_index))
            commit = store.write_commit(git, files, tip, main, date, changed)
            try:
                store.push(git, commit, tip)
            except Refused as error:
                if attempt == attempts:
                    raise
                out(f"Retrying ({attempt}/{attempts}): {error}")
                continue
            out(f"Published state {commit} for main {main}: {len(new_index)} files, {changed} changed.")
            return commit, changed
    raise Refused("unreachable")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--main", required=True)
    parser.add_argument("--checkout", default=".")
    parser.add_argument("--remote", default=None)
    parser.add_argument("--drill", action="store_true")
    args = parser.parse_args()
    token = os.environ.pop("STATE_TOKEN", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    remote = args.remote or f"https://github.com/{repository}.git"
    try:
        commit, changed = publish(args.snapshot, args.main, args.checkout, remote, token, drill=args.drill)
    except Refused as error:
        print(f"::error::{error}")
        print(str(error), file=sys.stderr)
        return 1
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a") as stream:
            stream.write(f"state_commit={commit}\nchanged={changed}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
