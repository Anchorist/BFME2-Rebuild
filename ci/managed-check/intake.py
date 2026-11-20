"""Build a source-only delta against the protected revision or an actionable refusal."""
from collections import defaultdict, deque
import os
from pathlib import Path, PurePosixPath
import re
import sys

from common import PIN, REPO_ID, digest, policy, read, validate_binding, write
from gitrepo import Change, Git, Refusal, safe_path
from fork_admission import narrow
from pool_compare import projection
from pool_protocol import compiler_source_problem, decode, encode

INCLUDE = re.compile(rb'^[ \t]*#[ \t]*include[ \t]*[<"]([^>"\r\n]+)[>"]', re.M)
MAX_AFFECTED = 512


class Refused(Exception):
    def __init__(self, rule, location=None):
        super().__init__(rule)
        self.rule = rule
        self.location = location


def blob(git, rev, path):
    return git.run("cat-file", "blob", f"{rev}:{path}").stdout


def tu(path):
    return path.startswith("src/") and PurePosixPath(path).suffix.lower() in {".c", ".cpp"}


def affected(files, headers):
    """A conservative reverse graph. Include suffixes cover different search paths and case."""
    aliases = defaultdict(set)
    includers = defaultdict(set)
    for path in files:
        parts = path.casefold().split("/")
        for start in range(len(parts)):
            aliases["/".join(parts[start:])].add(path)
    for path, content in files.items():
        for item in INCLUDE.findall(decode(content, 1024**2)):
            pieces = item.decode("utf-8", "replace").replace("\\", "/").casefold().split("/")
            label = "/".join(part for part in pieces if part not in {"", ".", ".."})
            for target in aliases[label] | aliases[pieces[-1]]:
                includers[target].add(path)
    seen, todo = set(headers), deque(headers)
    while todo:
        for includer in includers[todo.popleft()] - seen:
            seen.add(includer)
            todo.append(includer)
    return {path for path in seen if tu(path)}


def refusal_rule(reason):
    if reason.startswith("Protected path:"):
        return "protected-path"
    if "conflict" in reason.lower():
        return "conflict"
    if "no measurable source changes" in reason or "no remaining source change" in reason:
        return "empty"
    for fragment, rule in (
        ("60 changed paths", "source-file-count"),
        ("1 MiB per file", "source-byte-count"),
        ("source naming rules", "source-name"),
        ("regular C/C++", "source-file-type"),
        ("UTF-8", "source-encoding"),
        ("collides", "source-case"),
        ("identity", "source-attribution"),
        ("one merge base", "conflict"),
        ("additional paths", "conflict"),
    ):
        if fragment in reason:
            return rule
    return "source-intake"


def candidate(git, event):
    base, head = (event[key] for key in ("base", "head"))
    try:
        prepared = git.prepare(base, head, event["number"], event["login"], event["uid"])
    except Refusal as rejected:
        raise Refused(refusal_rule(str(rejected))) from None
    changes = []
    for change in prepared.changes:
        path, mode, oid = change.path, change.mode, change.oid
        if tu(path):
            expected = "expected/" + path[4:] + ".json"
            if git.run("cat-file", "-e", f"{base}:{expected}", check=False).returncode:
                raise Refused("new_tu")
            if mode == "000000":
                raise Refused("deletion")
        data = blob(git, prepared.commit, path) if mode != "000000" else None
        if data is not None:
            issue = compiler_source_problem(data)
            if issue:
                rule, line = issue
                raise Refused(rule, f"{path}:{line}")
        changes.append({"path": path, "mode": mode, "oid": oid,
                        "blob": encode(data) if data is not None else None})
    changed = sorted(row["path"] for row in changes)
    headers = {path for path in changed if path.startswith("include/")}
    paths = {path for path in changed if tu(path)}
    if headers:
        old_files, _ = projection(git, base)
        new_files, _ = projection(git, prepared.commit)
        paths |= affected(old_files, headers) | affected(new_files, headers)
    if not paths:
        raise Refused("no-includers")
    if len(paths) > MAX_AFFECTED:
        raise Refused("wide-cap")
    for path in paths:
        for rev, name in ((base, "expected/" + path[4:] + ".json"), (base, path), (prepared.commit, path)):
            if git.run("cat-file", "-e", f"{rev}:{name}", check=False).returncode:
                raise Refused("new_tu")
    return {"version": 1, "repo": REPO_ID, "number": event["number"], "base": base, "head": head,
            "tree": prepared.tree, **PIN, "policy": policy(),
            "changed_paths": changed, "request_paths": sorted(paths),
            "changes": changes}


def reconstruct(git, plan):
    validate_binding(plan)
    changes, total = [], 0
    for row in plan["changes"]:
        path, mode, oid = (row[k] for k in ("path", "mode", "oid"))
        if not safe_path(path) or mode not in {"000000", "100644"}:
            raise ValueError("The compiler payload contains an unsupported source path.")
        if mode == "000000":
            if oid != "0" * 40 or row["blob"] is not None:
                raise ValueError("The compiler payload contains an invalid deleted path.")
        else:
            data = decode(row["blob"], 1024**2)
            total += len(data)
            if (len(data) > 1024**2 or total > 8 * 1024**2 or compiler_source_problem(data)
                    or git.value("hash-object", "-w", "--stdin", data=data) != oid):
                raise ValueError("The compiler payload failed its source validation.")
        changes.append(Change(path, mode, oid))
    changed = sorted({change.path for change in changes})
    if len(changed) != len(changes) or not 0 < len(changed) <= 60 or changed != plan["changed_paths"]:
        raise ValueError("The compiler payload has an inconsistent path list.")
    tree = git.tree_with(plan["base"], changes)
    if tree != plan["tree"]:
        raise ValueError("The rebuilt tree differs from the admitted tree.")
    git.case_check(tree, changes)
    # This synthetic commit exists only in this job. Only its validated tree is measured.
    return git.commit(tree, plan["base"], "Apply admitted source tree\n", "bfme-boat", 1)


def main(work, out):
    work, out = Path(work), Path(out)
    out.mkdir(mode=0o700, exist_ok=True)
    event = read(work / "event.json", 4096)
    try:
        plan = candidate(Git(work / "source.git"), event)
    except Refused as rejected:
        write(out / "decision.json", {key: event[key] for key in ("number", "head", "base")}
              | {"version": 1, "repo": REPO_ID, "kind": "gate", "rules": [rejected.rule]}
              | ({"location": rejected.location} if rejected.location else {}))
        return
    automatic = event.get("automatic_author") if narrow(plan) else None
    if not event["approved"] and automatic is None:
        kind = "awaiting-automatic" if narrow(plan) and event.get("automatic_pending") else "awaiting-approval"
        write(out / "decision.json", {key: event[key] for key in ("number", "head", "base")}
              | {"version": 1, "repo": REPO_ID, "kind": kind})
        return
    route = "compile" if len(plan["request_paths"]) <= 8 else "wide"
    write(out / "plan.json", plan)
    write(out / "decision.json", {key: plan[key] for key in ("number", "head", "base", "tree")}
          | {"version": 1, "repo": REPO_ID, "kind": route, "plan": digest((out / "plan.json").read_bytes())}
          | ({"automatic_author": automatic} if automatic is not None else {}))
    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
        output.write("route=" + ("automatic" if automatic is not None else route) + "\n")



if __name__ == "__main__":
    main(*sys.argv[1:])

