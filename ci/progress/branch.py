"""Read the inputs of the progress card and write its outputs to the `progress` branch.

    python3 -B ci/progress/branch.py read  --dir IN    (exports state, nightly and progress tips; prints main=...)
    python3 -B ci/progress/branch.py write --dir OUT --main SHA

`read` writes IN/state/ (the newest state); from branch nightly, when present, IN/nightly.json,
IN/link-missing.tsv and IN/game.json; IN/history.json (the previous card's history, if any);
and GITHUB_OUTPUT main=<sha>.
`write` makes one commit on `progress` holding exactly OUT's files, dated with the main
commit's date, and pushes it as a fast-forward. Tokens: READ_TOKEN / WRITE_TOKEN.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "state"))
from layout import Refused  # noqa: E402
import store  # noqa: E402

PROGRESS = "refs/heads/progress"
NIGHTLY = "refs/heads/nightly"


def tip(git, ref):
    done = git.run("ls-remote", "--", git.remote, ref, check=False)
    if done.returncode:
        raise Refused(f"read {ref}: expected ls-remote exit 0, found {done.returncode}")
    line = done.stdout.decode().strip()
    return line.split("\t")[0] if line else ""


def fetch(git, ref):
    sha = tip(git, ref)
    if sha:
        git.run("fetch", "-q", "--no-tags", "--", git.remote, f"+{ref}:{ref}")
    return sha


def export(git, commit, target):
    target.mkdir(parents=True, exist_ok=True)
    archive = git.run("archive", "--format=tar", commit).stdout
    subprocess.run(["tar", "-x", "-C", str(target)], input=archive, check=True)


def valid_pair(pair):
    return (isinstance(pair, list) and len(pair) == 2 and all(type(n) is int for n in pair)
            and 0 <= pair[0] <= pair[1] and pair[1] > 0)


def latest_has_pair(path):
    try:
        record = json.loads(Path(path).read_bytes())
    except (OSError, ValueError):
        return False
    return isinstance(record, dict) and valid_pair(record.get("provided_required_symbols"))


def last_linking(git, commit, limit=400):
    """The newest record under history/ on branch nightly (highest public run id) that carries a valid
    Linking pair, as bytes; None when there is none."""
    names = git.run("ls-tree", "--name-only", f"{commit}:history", check=False)
    if names.returncode:
        return None
    best, best_run = None, -1
    for name in sorted(names.stdout.decode().split())[-limit:]:
        if not name.endswith(".json"):
            continue
        blob = git.run("cat-file", "blob", f"{commit}:history/{name}", check=False)
        if blob.returncode or len(blob.stdout) > 1024 * 1024:
            continue
        try:
            record = json.loads(blob.stdout)
        except ValueError:
            continue
        if not isinstance(record, dict):
            continue  # any other JSON value is not a nightly record
        try:
            run = int(str(record.get("run_id")))
        except ValueError:
            continue
        if valid_pair(record.get("provided_required_symbols")) and run > best_run:
            best, best_run = blob.stdout, run
    return best


def read(directory, remote, token, out=print):
    directory = Path(directory)
    with tempfile.TemporaryDirectory() as folder:
        git = store.Git(Path(folder) / "b.git", remote, token)
        state = fetch(git, store.BRANCH)
        if not state:
            raise Refused("progress: expected a state branch to read, found none (publish the state first)")
        export(git, state, directory / "state")
        main = store.published_main(git, state)
        nightly = fetch(git, NIGHTLY)
        if nightly:
            # latest.json: the daily build; link-missing.tsv: names the daily link census found missing,
            # with how many rebuilt objects wait on each; game/latest.json: the last game run folded in.
            for source, target in (("latest.json", "nightly.json"), ("link-missing.tsv", "link-missing.tsv"),
                                   ("game/latest.json", "game.json")):
                found = git.run("cat-file", "blob", f"{nightly}:{source}", check=False)
                if found.returncode == 0:
                    (directory / target).write_bytes(found.stdout)
            # A failed night writes latest.json without a Linking pair; then keep the last measured one.
            if not latest_has_pair(directory / "nightly.json"):
                last = last_linking(git, nightly)
                if last is not None:
                    (directory / "linking.json").write_bytes(last)
        progress = fetch(git, PROGRESS)
        if progress:
            found = git.run("cat-file", "blob", f"{progress}:history.json", check=False)
            if found.returncode == 0:
                (directory / "history.json").write_bytes(found.stdout)
        out(f"Inputs: state {state[:12]} (main {main}), nightly {nightly[:12] or 'not published yet'}, "
            f"previous card {progress[:12] or 'none'}.")
        return main


def write(directory, main, checkout, remote, token, out=print):
    directory = Path(directory)
    files = {p.relative_to(directory).as_posix(): p.read_bytes()
             for p in sorted(directory.rglob("*")) if p.is_file()}
    date = subprocess.check_output(["git", "-C", str(checkout), "show", "-s", "--format=%ct +0000", main],
                                   text=True).strip()
    with tempfile.TemporaryDirectory() as folder:
        git = store.Git(Path(folder) / "b.git", remote, token)
        for attempt in range(3):
            old = fetch(git, PROGRESS)
            with tempfile.TemporaryDirectory() as index_dir:
                env = {"GIT_INDEX_FILE": str(Path(index_dir) / "index")}
                entries = b"".join(f"100644 {git.value('hash-object', '-w', '--stdin', data=data)}\t{path}\0".encode()
                                   for path, data in files.items())
                git.run("read-tree", "--empty", env=env)
                git.run("update-index", "-z", "--index-info", data=entries, env=env)
                tree = git.value("write-tree", env=env)
            if old and git.value("rev-parse", old + "^{tree}") == tree:
                out(f"Unchanged: progress {old[:12]} already holds these files.")
                return old
            message = f"Progress for main {main}\n".encode()
            commit = git.value("commit-tree", tree, *(["-p", old] if old else []), data=message,
                               env=store.IDENTITY | {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})
            done = git.run("push", "-q", "--", git.remote, f"{commit}:{PROGRESS}", check=False)
            if done.returncode == 0:
                out(f"Published progress {commit} for main {main} ({len(files)} files).")
                return commit
            out(f"Retrying after a refused push ({attempt + 1}/3).")
        raise Refused(f"push {PROGRESS}: expected a fast-forward, found three refusals")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["read", "write"])
    parser.add_argument("--dir", required=True)
    parser.add_argument("--main", default="")
    parser.add_argument("--checkout", default=".")
    parser.add_argument("--remote", default="")
    args = parser.parse_args()
    remote = args.remote or f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', '')}.git"
    try:
        if args.mode == "read":
            sha = read(args.dir, remote, os.environ.pop("READ_TOKEN", ""))
            with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a") as stream:
                stream.write(f"main={sha}\n")
        else:
            write(args.dir, args.main, args.checkout, remote, os.environ.pop("WRITE_TOKEN", ""))
    except (Refused, OSError, subprocess.CalledProcessError) as error:
        print(f"::error::{error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
