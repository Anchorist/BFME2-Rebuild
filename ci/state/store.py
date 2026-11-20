"""Read and write the `state` branch with plain Git, one deterministic commit per main commit.

The token reaches Git only through an environment-supplied HTTP header (never argv,
never a file in the checkout). Commits carry fixed identity and the main commit's
own timestamp, so the same parent and the same main give the same commit bytes.
"""
import base64
import os
from pathlib import Path
import subprocess
import tempfile

from layout import Refused

BRANCH = "refs/heads/state"
IDENTITY = {"GIT_AUTHOR_NAME": "github-actions[bot]",
            "GIT_AUTHOR_EMAIL": "41898282+github-actions[bot]@users.noreply.github.com",
            "GIT_COMMITTER_NAME": "github-actions[bot]",
            "GIT_COMMITTER_EMAIL": "41898282+github-actions[bot]@users.noreply.github.com"}
SUBJECT = "State for main "


class Git:
    def __init__(self, path, remote, token=None):
        self.path = Path(path)
        self.remote = remote
        self.env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C", "LC_ALL": "C",
                    "HOME": str(self.path), "GIT_TERMINAL_PROMPT": "0",
                    "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
        if token:
            header = base64.b64encode(b"x-access-token:" + token.encode()).decode()
            self.env.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
                            GIT_CONFIG_VALUE_0="AUTHORIZATION: basic " + header)
        if not (self.path / "HEAD").exists():
            self.run("init", "-q", "--bare", str(self.path), cwd=None)

    def run(self, *args, data=None, env=None, check=True, cwd="repo"):
        command = ["git"] + (["--git-dir", str(self.path)] if cwd else []) + list(args)
        done = subprocess.run(command, input=data, capture_output=True, timeout=300,
                              env=self.env | (env or {}), check=False)
        if check and done.returncode:
            text = done.stderr.decode("utf-8", "replace").strip().splitlines()
            raise Refused(f"git {args[0]}: expected exit 0, found {done.returncode}: "
                          f"{text[-1] if text else 'no message'}")
        return done

    def value(self, *args, **kw):
        return self.run(*args, **kw).stdout.decode().strip()


def remote_tip(git):
    done = git.run("ls-remote", "--", git.remote, BRANCH, check=False)
    if done.returncode:
        raise Refused(f"read {BRANCH}: expected ls-remote exit 0, found {done.returncode}")
    line = done.stdout.decode().strip()
    return line.split("\t")[0] if line else ""


def fetch(git, tip):
    if tip:
        git.run("fetch", "-q", "--no-tags", "--", git.remote, f"+{BRANCH}:{BRANCH}")
        found = git.value("rev-parse", BRANCH)
        if found != tip:
            raise Refused(f"fetch {BRANCH}: expected {tip}, found {found}")


def reader(git, commit):
    def read(path):
        done = git.run("cat-file", "blob", f"{commit}:{path}", check=False)
        if done.returncode:
            raise Refused(f"read state: expected {path} in state commit {commit}, found nothing")
        return done.stdout
    return read


def published_main(git, commit):
    """The main commit a state commit describes, from its subject line."""
    subject = git.value("log", "-1", "--format=%s", commit)
    return subject[len(SUBJECT):] if subject.startswith(SUBJECT) else ""


def find_state(git, main):
    """The state commit for one main commit, searching the whole state history."""
    if not git.run("rev-parse", "-q", "--verify", BRANCH, check=False).stdout:
        return ""
    found = git.value("log", "--format=%H", "--fixed-strings", "--grep", SUBJECT + main, BRANCH)
    hits = [c for c in found.splitlines() if published_main(git, c) == main]
    return hits[0] if hits else ""


def write_commit(git, files, parent, main, date, changed):
    with tempfile.TemporaryDirectory() as folder:
        index_env = {"GIT_INDEX_FILE": str(Path(folder) / "index")}
        entries = []
        for path, data in sorted(files.items()):
            oid = git.value("hash-object", "-w", "--stdin", data=data)
            entries.append(f"100644 {oid}\t{path}\0".encode())
        git.run("read-tree", "--empty", env=index_env)
        git.run("update-index", "-z", "--index-info", data=b"".join(entries), env=index_env)
        tree = git.value("write-tree", env=index_env)
    message = f"{SUBJECT}{main}\n\nFiles whose verdicts changed: {changed}\n".encode()
    dates = {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
    args = ["commit-tree", tree] + (["-p", parent] if parent else [])
    return git.value(*args, data=message, env=IDENTITY | dates)


def push(git, commit, old):
    # A plain push: GitHub refuses it unless it fast-forwards from what we read.
    done = git.run("push", "-q", "--", git.remote, f"{commit}:{BRANCH}", check=False)
    if done.returncode:
        text = done.stderr.decode("utf-8", "replace").strip().splitlines()
        raise Refused(f"push {BRANCH}: expected a fast-forward from {old or 'nothing'}, "
                      f"found refusal: {text[-1] if text else 'no message'}")
