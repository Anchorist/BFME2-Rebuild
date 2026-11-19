"""Fixed-origin GitHub input and status endpoints for the protected workflow."""
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

from common import CONTEXT, HEX40, REPO, REPO_ID, encoded, read, write
from gitrepo import Git, GitFailure


class Superseded(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def event():
    if (os.environ.get("GITHUB_REPOSITORY") != REPO
            or os.environ.get("GITHUB_REPOSITORY_ID") != str(REPO_ID)
            or os.environ.get("GITHUB_REF") != "refs/heads/main"
            or os.environ.get("GITHUB_EVENT_NAME") != "pull_request_target"):
        raise ValueError("This workflow requires the approved protected repository and main.")
    payload = read(os.environ["GITHUB_EVENT_PATH"], 2 * 1024**2)
    pr = payload["pull_request"]
    base, head, number = os.environ["GITHUB_SHA"], pr["head"]["sha"], pr["number"]
    validate_pr(pr, number, head)
    if not HEX40.fullmatch(base):
        raise ValueError("The workflow revision is invalid.")
    return {"number": number, "base": base, "head": head, "login": "bfme-boat", "uid": 1}


def validate_pr(pr, number, head):
    if (pr["state"] != "open" or type(number) is not int or not 0 < number < 10**9
            or pr["number"] != number or pr["base"]["repo"]["id"] != REPO_ID
            or pr["base"]["ref"] != "main" or not HEX40.fullmatch(head)):
        raise ValueError("The pull request metadata is outside the managed check scope.")


class GitHub:
    def __init__(self):
        self.token = os.environ.pop("BFME_STATUS_TOKEN", None) or os.environ.pop("BFME_READ_TOKEN", None)
        if not self.token or not re.fullmatch(r"[A-Za-zA-Z0-9_.-]{15,2048}", self.token):
            raise ValueError("This protected step requires its repository token.")
        self.api = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def call(self, path, value=None):
        import json
        request = urllib.request.Request("https://api.github.com/repos/" + REPO + "/" + path,
                                         data=encoded(value) if value is not None else None,
                                         headers={"Authorization": "Bearer " + self.token,
                                                  "Accept": "application/vnd.github+json",
                                                  "Content-Type": "application/json"})
        try:
            with self.api.open(request, timeout=25) as response:
                raw = response.read(2 * 1024**2 + 1)
        except urllib.error.HTTPError as exc:
            raise ValueError(f"The GitHub API returned HTTP {exc.code}.") from None
        if len(raw) > 2 * 1024**2:
            raise ValueError("The GitHub API response exceeded the configured limit.")
        return json.loads(raw)

    def current(self, binding):
        number, head, base = (binding[key] for key in ("number", "head", "base"))
        pr = self.call(f"pulls/{number}")
        if pr["state"] != "open" or pr["base"]["ref"] != "main":
            raise Superseded()
        validate_pr(pr, number, head)
        if (pr["head"]["sha"] != head or self.call("git/ref/heads/main")["object"]["sha"] != base):
            raise Superseded()
        return pr

    def status(self, binding, state, text):
        run = os.environ["GITHUB_RUN_ID"]
        if not re.fullmatch(r"[1-9][0-9]{0,20}", run):
            raise ValueError("The Actions run ID is invalid.")
        result = self.call("statuses/" + binding["head"], {"state": state, "context": CONTEXT,
                           "description": text, "target_url": f"https://github.com/{REPO}/actions/runs/{run}"})
        if result.get("state") != state or result.get("context") != CONTEXT:
            raise ValueError("GitHub did not acknowledge the expected commit status.")


def admitted(pr):
    return (pr.get("author_association") in {"OWNER", "MEMBER", "COLLABORATOR"}
            or any(label.get("name") == "boat-ok" for label in pr.get("labels", ())))


def fetch(work):
    binding = event()
    api = GitHub()
    pr = api.current(binding)
    binding["approved"] = admitted(pr)
    work.mkdir(mode=0o700)
    git = Git(work / "source.git", initialize=True)
    base = Git(Path.cwd() / ".git")
    if base.rev("HEAD") != binding["base"]:
        raise ValueError("The trusted checkout differs from the protected workflow revision.")
    ask = work / "askpass"
    ask.write_text('#!/bin/sh\ncase "$1" in *Username*) printf "%s\\n" x-access-token ;;\n'
                   '*Password*) printf "%s\\n" "$BFME_GIT_TOKEN" ;; *) exit 1 ;; esac\n')
    ask.chmod(0o700)
    try:
        receive_refs(git, f"https://github.com/{REPO}.git", binding,
                     {"GIT_ASKPASS": str(ask), "BFME_GIT_TOKEN": api.token})
    finally:
        ask.unlink()
    write(work / "event.json", binding)


def receive_refs(git, remote, binding, environment):
    # Fetch into an empty bare repo. A depth-one checkout's alternate store
    # does not carry the checkout's shallow boundary into the receiving repo.
    number = binding["number"]
    result = git.run("fetch", "-q", "--no-tags", "--no-write-fetch-head", "--depth=128", "--", remote,
                     "+refs/heads/main:refs/ci/actual-main", f"+refs/pull/{number}/head:refs/ci/head",
                     env=environment, timeout=120, check=False)
    if result.returncode:
        code = result.stderr.lower()
        reasons = (
            (b"remote ref", "one exact repository ref is unavailable"),
            (b"authenti", "GitHub denied the read credential"),
            (b"permission denied", "GitHub denied repository read access"),
            (b"object", "the received Git object pack could not be verified"),
            (b"size limit", "the transfer exceeded the private Git input allowance"),
            (b"unable to access", "the GitHub transfer could not connect"),
        )
        reason = next((reason for fragment, reason in reasons if fragment in code),
                      "the authenticated Git transfer did not complete")
        raise GitFailure(f"Protected Git intake failed ({result.returncode}): {reason}.")
    if git.rev("refs/ci/head") != binding["head"] or git.rev("refs/ci/actual-main") != binding["base"]:
        raise Superseded()


def publish(phase, admission=None, result=None):
    from quality_format import quality_report
    binding = event()
    api = GitHub()
    api.current(binding)
    if phase == "start":
        api.status(binding, "pending", "Waiting for protected intake and Boat comparison")
        return
    decision_path = admission / "decision.json"
    final_path = result / "verdict.json"
    out = Path(os.environ["MANAGED_PUBLIC_REPORT"])
    out.mkdir(mode=0o700, exist_ok=True)
    record = {"kind": "pending", "messages": ["The managed compiler or comparison did not return a complete receipt. Re-run this check."]}
    decision = read(decision_path, 4096) if decision_path.is_file() else None
    if decision:
        identity = {"version": 1, "repo": REPO_ID} | {k: binding[k] for k in ("base", "head", "number")}
        if any(decision.get(key) != value for key, value in identity.items()):
            raise ValueError("The admission receipt came from a different pull request.")
        if decision["kind"] == "gate":
            record = {"kind": "gate", "rules": decision["rules"]}
        elif decision["kind"] == "awaiting-approval":
            record = {"kind": "pending", "messages": ["A maintainer can approve Boat comparison by adding the boat-ok label."]}
        elif decision["kind"] == "awaiting-wide":
            record = {"kind": "pending", "messages": ["This patch requires the wide Boat comparison. The managed wide comparison has not been enabled."]}
        elif decision["kind"] == "compile" and final_path.is_file():
            verdict = read(final_path, 256 * 1024)
            identity |= {k: decision[k] for k in ("tree", "plan")}
            if any(verdict.get(key) != value for key, value in identity.items()):
                raise ValueError("The compiler receipt did not match the admission.")
            record = verdict["report"]
            write(out / "verdict.json", identity | {"counts": verdict["counts"], "functions": verdict["functions"],
                                                   "kind": record["kind"]})
    report = quality_report(binding["base"], binding["head"], record) + "\n"
    (out / "summary.md").write_text(report)
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a") as stream:
        stream.write(report)
    states = {"ok": "success", "pending": "pending", "gate": "failure", "regression": "failure"}
    status = states[record["kind"]]
    message = {"success": "BFME II comparison passed", "failure": "BFME II check refused this patch",
               "pending": "Boat comparison incomplete. Re-run the check."}[status]
    # Keep the status pending if the event was superseded while preparing the report.
    latest = api.current(binding)
    if status == "success" and not admitted(latest):
        raise Superseded()
    api.status(binding, status, f"{message} (main {binding['base'][:12]})")
    if record["kind"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    os.umask(0o077)
    mode, *args = sys.argv[1:]
    try:
        if mode == "fetch":
            fetch(Path(args[0]))
        elif mode == "start":
            publish(mode)
        elif mode == "finish":
            publish(mode, *map(Path, args))
        else:
            raise ValueError("Unknown protected GitHub operation.")
    except Superseded:
        print("This event was superseded by a change to the pull request or main.")
        raise SystemExit(2) from None

