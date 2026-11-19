"""Git plumbing for CI. GitHub objects enter the judge only through a validated tree."""
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

OID = re.compile(r"[0-9a-f]{40}\Z")
LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})\Z")
PART = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.+-]{0,95}\Z")
DEVICE = re.compile(r"(?:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\.|$)", re.I)
SOURCE_EXT = {"src": {".c", ".cpp"},
              "include": {".h", ".hpp", ".hh", ".inl"}}
DECLARATION = re.compile(r"^Removed-Declaration: ((?:[A-Za-z_]\w*::)*~?[A-Za-z_]\w*)[ \t]*$", re.M | re.ASCII)


class Refusal(Exception):
    """An actionable input problem. Text consists of bot-owned diagnostics."""


class GitFailure(Exception):
    pass


@dataclass(frozen=True)
class Change:
    path: str
    mode: str
    oid: str


@dataclass(frozen=True)
class Candidate:
    head: str
    base: str
    commit: str
    tree: str
    changes: tuple[Change, ...]


def safe_path(path):
    if not isinstance(path, str) or len(path) > 220:
        return False
    parts = path.split("/")
    return (len(parts) >= 2 and parts[0] in SOURCE_EXT
            and Path(parts[-1]).suffix.lower() in SOURCE_EXT[parts[0]]
            and all(PART.fullmatch(p) and not p.endswith(".") and not DEVICE.match(p) for p in parts))


def git_environment(overrides=None):
    env = {key: os.environ[key] for key in ("HOME", "PATH", "TMPDIR", "SSL_CERT_FILE", "SSL_CERT_DIR")
           if key in os.environ}
    env.update(GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1", GIT_NO_REPLACE_OBJECTS="1",
               GIT_TERMINAL_PROMPT="0", LC_ALL="C")
    env.update(overrides or {})
    return env


class Git:
    def __init__(self, path, *, initialize=False, hooks=None):
        self.path = Path(path).absolute()
        self.hooks = str(hooks or "/dev/null")
        if initialize and not (self.path / "HEAD").exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "-c", "init.templateDir=", "init", "--bare", "-q", str(self.path)],
                           env=git_environment(), check=True, capture_output=True, timeout=15)

    def run(self, *args, data=None, env=None, check=True, timeout=180):
        quota = (["prlimit", "--fsize=268435456:268435456", "--as=1610612736:1610612736", "--"]
                 if args[0] == "fetch" and any(a.startswith("https://github.com/") for a in args) else [])
        p = subprocess.run(quota + ["git", "-c", "core.hooksPath=" + self.hooks,
                            "-c", "protocol.ext.allow=never", "-c", "credential.helper=",
                            "-c", "http.followRedirects=false", "-c", "fetch.fsckObjects=true",
                            "-c", "fetch.unpackLimit=1", "-c", "gc.auto=0",
                            "--git-dir", str(self.path), *args],
                           input=data, env=git_environment(env), capture_output=True, timeout=timeout)
        if check and p.returncode:
            raise GitFailure(f"git {args[0]} failed ({p.returncode})")
        return p

    def value(self, *args, **kwargs):
        return self.run(*args, **kwargs).stdout.decode("ascii").strip()

    def rev(self, ref):
        return self.value("rev-parse", "--verify", ref + "^{commit}")

    def fetch_main(self, remote, branch="main"):
        if branch not in {"main", "ci-replay"}:
            raise GitFailure("Unknown authoritative branch")
        self.run("fetch", "-q", "--no-tags", "--no-write-fetch-head", "--", remote,
                 f"+refs/heads/{branch}:refs/ci/main")
        return self.rev("refs/ci/main")

    def fetch_head(self, remote, number, expected):
        assert type(number) is int and number > 0 and OID.fullmatch(expected)
        ref = f"refs/ci/pull/{number}"
        self.run("fetch", "-q", "--no-tags", "--no-write-fetch-head", "--", remote,
                 f"+refs/pull/{number}/head:{ref}")
        if self.rev(ref) != expected:
            raise GitFailure("Pull request head moved during fetch")

    def changes(self, base, head, *, validate=True):
        raw = self.run("diff", "--raw", "-z", "--abbrev=40", "--no-renames", "--no-ext-diff", base, head, "--").stdout
        records = raw.rstrip(b"\0").split(b"\0") if raw else []
        changes = []
        if len(records) > 2 * 60:
            raise Refusal("This pull request exceeds 60 changed paths. Split it into smaller pull requests.")
        total = 0
        for meta, name in zip(records[::2], records[1::2], strict=True):
            try:
                path = name.decode("ascii")
            except UnicodeDecodeError:
                raise Refusal("This pull request contains a path outside the supported source naming rules.") from None
            old_mode, mode, _base_oid, oid, _status = meta[1:].decode("ascii").split()
            if validate:
                if path.casefold().startswith(("ci/", "tools/", "config/", "expected/", ".github/", "baseline/")):
                    raise Refusal("Protected path: remove checker, workflow, ledger, configuration or baseline edits from this source pull request.")
                if not safe_path(path) or {old_mode, mode} - {"000000", "100644"}:
                    raise Refusal("Only regular C/C++ source and header files under src/ and include/ can be measured.")
                if mode != "000000":
                    size = int(self.value("cat-file", "-s", oid))
                    total += size
                    if size > 1024 * 1024 or total > 8 * 1024 * 1024:
                        raise Refusal("This pull request exceeds the 1 MiB per file or 8 MiB combined source limit.")
                    content = self.run("cat-file", "blob", oid).stdout
                    try:
                        if b"\0" in content:
                            raise UnicodeError()
                        content.decode("utf-8")
                    except UnicodeError:
                        raise Refusal("Changed source must be UTF-8 text.") from None
            changes.append(Change(path, mode, oid))
        return tuple(changes)

    def tree_with(self, base, changes):
        with tempfile.TemporaryDirectory(dir=self.path.parent) as tmp:
            env = {"GIT_INDEX_FILE": str(Path(tmp) / "index")}
            self.run("read-tree", base, env=env)
            entries = sorted(changes, key=lambda c: c.mode != "000000")
            data = b"".join(f"{c.mode} {c.oid}\t{c.path}\0".encode("ascii") for c in entries)
            self.run("update-index", "-z", "--index-info", data=data, env=env)
            return self.value("write-tree", env=env)

    def case_check(self, tree, changes):
        touched = set()
        for c in changes:
            if c.mode != "000000":
                parts = c.path.split("/")
                touched.update("/".join(parts[:n]).lower() for n in range(1, len(parts) + 1))
        paths = self.run("ls-tree", "-r", "-t", "-z", "--name-only", tree, "--", "src/", "include/").stdout
        seen = {}
        for name in paths.decode("utf-8", "surrogateescape").split("\0"):
            key = name.casefold()
            if key in touched and seen.setdefault(key, name) != name:
                raise Refusal("A changed path collides with an existing path when case is ignored.")

    def commit(self, tree, base, message, login, user_id):
        if not LOGIN.fullmatch(login) or type(user_id) is not int or not 0 < user_id < 10**15:
            raise Refusal("Could not validate the pull request author's GitHub identity.")
        env = {"GIT_AUTHOR_NAME": login, "GIT_AUTHOR_EMAIL": f"{user_id}+{login}@users.noreply.github.com",
               "GIT_COMMITTER_NAME": "BFME II Boat", "GIT_COMMITTER_EMAIL": "bfme-boat@users.noreply.github.com"}
        return self.value("commit-tree", tree, "-p", base, data=message.encode("ascii"), env=env)

    def prepare(self, base, head, number, login, user_id):
        merge = self.run("merge-base", "--all", base, head, check=False)
        ancestors = merge.stdout.decode("ascii").splitlines()
        if merge.returncode not in {0, 1}:
            raise GitFailure("Could not determine merge base")
        if len(ancestors) != 1:
            raise Refusal("Rebase the pull request on main so it has one merge base.")
        ancestor, = ancestors
        changes = self.changes(ancestor, head)
        if not changes:
            raise Refusal("The pull request contains no measurable source changes.")
        topic_tree = self.tree_with(ancestor, changes)
        head_message = self.run("show", "-s", "--no-show-signature", "--format=%B", head, "--").stdout[:65000]
        ack = list(dict.fromkeys(DECLARATION.findall(head_message.decode("utf-8", "replace"))))[:50]
        ack = [name for name in ack if len(name) <= 120]
        message = f"Apply BFME II pull request #{number}\n\n"
        message += "".join(f"Removed-Declaration: {name}\n" for name in ack)
        message += f"\nGitHub-PR: {number}\nGitHub-Head: {head}\n"
        if ancestor == base:
            tree = topic_tree
        else:
            topic = self.commit(topic_tree, ancestor, message, login, user_id)
            merge = self.run("merge-tree", "--write-tree", "--no-messages", base, topic, check=False)
            if merge.returncode == 1:
                raise Refusal("This pull request conflicts with main. Resolve the conflict and push the updated branch.")
            if merge.returncode:
                raise GitFailure("Could not merge validated source")
            tree = merge.stdout.decode("ascii").splitlines()[0]
        commit = self.commit(tree, base, message, login, user_id)
        merged = self.changes(base, commit)
        if not merged:
            raise Refusal("There is no remaining source change after applying this pull request to main.")
        if {x.path for x in merged} - {x.path for x in changes}:
            raise Refusal("Rebasing changes additional paths. Rebase the pull request explicitly and try again.")
        self.case_check(tree, merged)
        return Candidate(head, base, commit, tree, merged)

    def push_main(self, remote, commit, expected, env=None):
        if self.value("rev-parse", commit + "^") != expected:
            raise GitFailure("Landing commit has the wrong parent")
        self.run("push", "-q", f"--force-with-lease=refs/heads/main:{expected}", "--", remote,
                 f"{commit}:refs/heads/main", env=env, timeout=75)

    def publish_claims(self, remote, value, env):
        ref = "refs/heads/claims"
        check = self.run("ls-remote", "--exit-code", "--", remote, ref, check=False, timeout=20)
        if check.returncode not in {0, 2}:
            raise GitFailure("Could not read the claims branch")
        old = None
        payload = (json.dumps(value, indent=2) + "\n").encode()
        if check.returncode == 0:
            self.run("fetch", "-q", "--no-tags", "--", remote, f"+{ref}:refs/ci/claims", timeout=30)
            old = self.rev("refs/ci/claims")
            existing = self.run("show", f"{old}:worklist/claims.json", check=False)
            if existing.returncode == 0 and existing.stdout == payload:
                return
        oid = self.value("hash-object", "-w", "--stdin", data=payload)
        with tempfile.TemporaryDirectory(dir=self.path.parent) as tmp:
            index_env = {"GIT_INDEX_FILE": str(Path(tmp) / "index")}
            self.run("read-tree", "--empty", env=index_env)
            self.run("update-index", "-z", "--index-info",
                     data=f"100644 {oid}\tworklist/claims.json\0".encode(), env=index_env)
            tree = self.value("write-tree", env=index_env)
        identity = {"GIT_AUTHOR_NAME": "BFME II Boat", "GIT_AUTHOR_EMAIL": "bfme-boat@users.noreply.github.com",
                    "GIT_COMMITTER_NAME": "BFME II Boat",
                    "GIT_COMMITTER_EMAIL": "bfme-boat@users.noreply.github.com"}
        parent = ["-p", old] if old else []
        tip = self.value("commit-tree", tree, *parent, env=identity, data=b"Update advisory claims\n")
        self.run("push", "-q", f"--force-with-lease={ref}:{old or ''}", "--", remote, f"{tip}:{ref}",
                 env=env, timeout=25)
