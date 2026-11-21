"""Collect the header rules for one pull request and write "BFME II / Header rules".

Run by .github/workflows/header-rules.yml on a GitHub-hosted runner, in two steps:

  collect.py preview NUMBER HEAD BASE OUT   no token: anonymous fetch of the exact base and pull request head as Git
                                            objects (nothing is checked out or run) and the header source checks
                                            H3 H4 H6 H7 H8 from this main's tools/gates; writes OUT (JSON)
  collect.py publish PREVIEW                with the job token: re-read the pull request and main, take H1 from the
                                            wide check's verdict on this main, compose, write the status if changed

Rules whose producer is not on main yet (H2 declarations, H5 layout, and H3-H8 until their checks are installed)
are reported as "not built": the decision is held, never passed.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compose  # noqa: E402

REPO = "Open-BFME/BFME2-Rebuild"
REPO_ID = 1464323350
BOT_ID = 41898282
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
SOURCE_RULES = ("H3", "H4", "H6", "H7", "H8")


class Stop(Exception):
    pass


def git(repo, *args):
    done = subprocess.run(["git", "--git-dir", str(repo), *args], capture_output=True, timeout=600,
                          env={"PATH": "/usr/bin:/bin", "GIT_TERMINAL_PROMPT": "0", "LANG": "C", "HOME": "/nonexistent"})
    if done.returncode:
        raise Stop(f"Expected git {args[0]} to succeed. Found exit {done.returncode}.")
    return done.stdout.decode().strip()


def fetch(repo, number):
    """Anonymous public fetch of main and the pull request head. No credential exists in this step."""
    if not repo.exists():
        git(repo, "init", "--bare", "-q")
    git(repo, "-c", "gc.auto=0", "fetch", "-q", "--no-tags", "--no-recurse-submodules",
        f"https://github.com/{REPO}.git", "+refs/heads/main:refs/protected/main",
        f"+refs/pull/{number}/head:refs/pull/head")


def source_checks(repo, base, head, tree):
    """H3 H4 H6 H7 H8 from this main's tools/gates; None when those checks are not installed yet."""
    tools = HERE.parents[1] / "tools" / "gates"
    sys.path.insert(0, str(tools))
    try:
        from gate import policy_at, policy_digest
        from git_objects import Git
        from header_inventory import Binding
        from header_source_preview import source_preview
    except ImportError:
        return None
    config = tools / "config.json"
    with Git(repo) as objects:
        binding = Binding(REPO, base, head, tree, policy_digest(config), "0" * 64, 1, 1)
        return source_preview(objects, policy_at(config), binding)


def tools_commit(root=HERE.parents[1]):
    """The commit these tools were checked out at (the workflow's own main commit)."""
    done = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, timeout=60,
                          env={"PATH": "/usr/bin:/bin", "LANG": "C", "HOME": "/nonexistent"})
    found = done.stdout.decode().strip()
    if done.returncode or not HEX40.fullmatch(found):
        raise Stop("Expected the header tools to be a Git checkout. Found none.")
    return found


def header_paths(repo, base, tree):
    """Every path under include/ that the merge changes, at either end: renames are split into their old and new
    paths (--no-renames), so a header moved out of include/ is still reported. NUL-delimited, so no name is mangled."""
    names = git(repo, "diff", "--no-renames", "--name-only", "-z", base, tree).split("\0")
    return sorted({name for name in names if name.startswith("include/")})


def preview(number, head, base, out):
    if not (HEX40.fullmatch(head) and HEX40.fullmatch(base)) or not re.fullmatch(r"[1-9][0-9]{0,8}", number):
        raise Stop("Expected a pull request number and two 40-character commits.")
    tools = tools_commit()
    if tools != base:
        raise Stop(f"Expected the checked-out header tools to be main {base[:12]}. Found {tools[:12]}; a newer run decides.")
    repo = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "bfme-header.git"
    fetch(repo, number)
    if git(repo, "rev-parse", "refs/protected/main") != base or git(repo, "rev-parse", "refs/pull/head") != head:
        raise Stop("Expected main and the pull request head to be the commits named. Found them moved.")
    tree = git(repo, "merge-tree", "--write-tree", base, head).splitlines()[0]
    paths = header_paths(repo, base, tree)
    record = {"number": int(number), "head": head, "base": base, "tree": tree, "tools": tools, "header_paths": paths}
    if paths:
        checks = source_checks(repo, base, head, tree)
        record["checks"] = checks          # None: the header source checks are not installed on this main yet
    Path(out).write_text(json.dumps(record, sort_keys=True) + "\n")
    print(f"Header preview of #{number}: {len(paths)} header file(s) changed.")


def components_for(record, boat):
    base = record["base"]
    if record.get("checks") is None:
        rows = {rule: {"state": "missing"} for rule in SOURCE_RULES}
    else:
        rows = compose.from_preview(record["checks"])
        for rule in SOURCE_RULES:
            rows.setdefault(rule, {"state": "missing"})
    rows["H1"] = compose.from_wide_status(boat, base)
    rows.setdefault("H2", {"state": "missing"})     # declaration producer: not on main yet
    rows.setdefault("H5", {"state": "missing"})     # layout producer: not on main yet
    return rows


class Api:
    def __init__(self, token):
        if not token or not re.fullmatch(r"[A-Za-z0-9_.-]{15,2048}", token):
            raise Stop("Expected the job token in BFME_HEADER_TOKEN. Found none.")
        self.token = token

    def send(self, method, path, body=None):
        request = urllib.request.Request(f"https://api.github.com/repos/{REPO}/{path}", method=method,
                                         data=json.dumps(body).encode() if body is not None else None,
                                         headers={"Authorization": "Bearer " + self.token,
                                                  "Accept": "application/vnd.github+json"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.loads(response.read(4 * 1024**2) or b"null")
        except urllib.error.HTTPError as exc:
            return exc.code, None


def current(pr, ref, record):
    """The pull request is still open, ready, aimed at this repository's main, at the head judged, on the main judged."""
    base = pr.get("base") or {}
    return (pr.get("state") == "open" and pr.get("draft") is False
            and base.get("ref") == "main" and (base.get("repo") or {}).get("id") == REPO_ID
            and (pr.get("head") or {}).get("sha") == record["head"]
            and (ref.get("object") or {}).get("sha") == record["base"])


def latest_bot_status(statuses, context):
    found = [item for item in statuses or [] if item.get("context") == context
             and (item.get("creator") or {}).get("id") == BOT_ID]
    return max(found, key=lambda item: item["id"]) if found else None


def still_current(api, record):
    """The last read before writing: the pull request and main are still exactly what was judged."""
    code, pr = api.send("GET", f"pulls/{record['number']}")
    code_main, ref = api.send("GET", "git/ref/heads/main")
    return code == 200 and code_main == 200 and current(pr, ref, record)


def publish(path, api=None, out=print):
    record = json.loads(Path(path).read_text())
    if not record.get("header_paths"):
        out(f"#{record['number']}: no header change; nothing to write.")
        return 0
    api = api or Api(os.environ.pop("BFME_HEADER_TOKEN", None))
    code, pr = api.send("GET", f"pulls/{record['number']}")
    code_main, ref = api.send("GET", "git/ref/heads/main")
    if code != 200 or code_main != 200:
        raise Stop(f"Expected the pull request and main to be readable. Found HTTP {code} and {code_main}.")
    workflow_sha = os.environ.get("GITHUB_SHA", "")
    if record.get("tools") != record["base"] or workflow_sha != record["base"]:
        out(f"#{record['number']}: the tools that judged it ({str(record.get('tools'))[:12]}, workflow "
            f"{workflow_sha[:12]}) are not main {record['base'][:12]}; a newer run decides. Nothing written.")
        return 0
    if not current(pr, ref, record):
        out(f"#{record['number']}: the head or main moved, or it is a draft or retargeted, since the preview; "
            "a newer run decides. Nothing written.")
        return 0
    code, statuses = api.send("GET", f"commits/{record['head']}/statuses?per_page=100")
    if code != 200:
        raise Stop(f"Expected the status list. Found HTTP {code}.")
    rows = components_for(record, latest_bot_status(statuses, "BFME II / Boat"))
    state, text, report = compose.compose(record["base"], rows)
    prior = latest_bot_status(statuses, compose.CONTEXT) or {}
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as stream:
            stream.write("\n".join([f"### #{record['number']}: {state}, {text}", ""] + report) + "\n")
    if prior.get("state") == state and prior.get("description") == text:
        out(f"#{record['number']}: {state}, {text} (unchanged)")
        return 0
    if not still_current(api, record):
        out(f"#{record['number']}: the head or main moved while the rules were read; a newer run decides. "
            "Nothing written.")
        return 0
    body = {"state": state, "context": compose.CONTEXT, "description": text}
    run = os.environ.get("GITHUB_RUN_ID", "")
    if run.isdigit():
        body["target_url"] = f"https://github.com/{REPO}/actions/runs/{run}"
    code, _ = api.send("POST", f"statuses/{record['head']}", body)
    if code != 201:
        raise Stop(f"Expected HTTP 201 for the {compose.CONTEXT} status. Found HTTP {code}.")
    out(f"::notice title=BFME II header rules::#{record['number']}: {state}, {text}")
    return 0


FILE_PAGES = 30          # GitHub lists at most 3000 files of a pull request


def touches_include(api, number, pr):
    """Whether any changed file is under include/, at either end of a rename. Every page is read; a list that is
    unreadable or shorter than the pull request's changed_files counts as touching include/ (the preview decides)."""
    seen = 0
    for page in range(1, FILE_PAGES + 1):
        code, files = api.send("GET", f"pulls/{number}/files?per_page=100&page={page}")
        if code != 200 or not isinstance(files, list):
            return True
        for item in files:
            if any((item.get(key) or "").startswith("include/") for key in ("filename", "previous_filename")):
                return True
        seen += len(files)
        if len(files) < 100:
            break
    return seen < int(pr.get("changed_files") or 0) or seen >= FILE_PAGES * 100


def emit(rows, env):
    target = env.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a") as stream:
            stream.write(f"pulls={json.dumps(rows, sort_keys=True)}\n")


def plan(api=None, env=os.environ):
    """Which pull requests to judge: the one named by a bfme-header-rules dispatch, or every open ready one that
    changes include/. Writes a GitHub Actions matrix to GITHUB_OUTPUT as `pulls`."""
    api = api or Api(env.get("BFME_HEADER_TOKEN"))
    code, ref = api.send("GET", "git/ref/heads/main")
    if code != 200:
        raise Stop(f"Expected main to be readable. Found HTTP {code}.")
    base = ref["object"]["sha"]
    if env.get("GITHUB_REPOSITORY_ID") != str(REPO_ID):
        raise Stop(f"Expected repository id {REPO_ID}. Found {env.get('GITHUB_REPOSITORY_ID')!r}.")
    if env.get("GITHUB_SHA") != base:
        emit([], env)
        print(f"Main is {base[:12]} but this run's tools are {str(env.get('GITHUB_SHA'))[:12]}; "
              "the run started by the newer main decides. Nothing judged.")
        return []
    numbers = []
    if env.get("GITHUB_EVENT_NAME") == "repository_dispatch":
        payload = json.loads(Path(env["GITHUB_EVENT_PATH"]).read_text()).get("client_payload") or {}
        if type(payload.get("number")) is not int or not 0 < payload["number"] < 10**9:
            raise Stop("Expected a bfme-header-rules payload with a pull request number.")
        numbers = [payload["number"]]
    elif env.get("BFME_HEADER_PR", "").isdigit():
        numbers = [int(env["BFME_HEADER_PR"])]
    else:
        for page in range(1, 11):
            code, pulls = api.send("GET", f"pulls?state=open&base=main&per_page=100&page={page}")
            if code != 200 or not isinstance(pulls, list):
                raise Stop(f"Expected the open pull requests. Found HTTP {code}.")
            numbers += [item["number"] for item in pulls if item.get("draft") is False]
            if len(pulls) < 100:
                break
    rows = []
    for number in numbers:
        code, pr = api.send("GET", f"pulls/{number}")
        if code != 200 or not current(pr, ref, {"head": (pr.get("head") or {}).get("sha"), "base": base}):
            continue
        if touches_include(api, number, pr):
            rows.append({"number": str(number), "head": pr["head"]["sha"], "base": base})
    emit(rows, env)
    print(f"Header rules plan on main {base[:12]}: " + (", ".join(f"#{row['number']}" for row in rows) or "nothing"))
    return rows


def main():
    try:
        mode, *args = sys.argv[1:]
        if mode == "plan":
            plan()
            return 0
        if mode == "preview":
            preview(*args)
            return 0
        if mode == "publish":
            return publish(*args)
        raise Stop("Expected preview or publish.")
    except (Stop, ValueError, KeyError, OSError, subprocess.SubprocessError) as exc:
        print(f"Header rules stopped. {str(exc)[:300]}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
