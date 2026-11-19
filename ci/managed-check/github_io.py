"""Fetch exact source objects and publish the managed check report."""
import base64
import os
from pathlib import Path
import re
import sys

from common import REPO, REPO_ID, read, write
from github_status import GitHub, Superseded, admitted, event
from gitrepo import Git, GitFailure


def fetch(work):
    binding = event()
    api = GitHub()
    pr = api.current(binding)
    binding["approved"] = admitted(pr, binding["event_association"])
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
        for line in masked_git_errors(result.stderr, environment.get("BFME_GIT_TOKEN")):
            print("Protected Git fetch stderr | " + line, file=sys.stderr)
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


def masked_git_errors(stderr, token):
    text = stderr.decode("utf-8", "replace")
    if token:
        basic = base64.b64encode(("x-access-token:" + token).encode()).decode("ascii")
        text = text.replace(token, "***").replace(basic, "***")
    text = re.sub(r"(?i)(?<=://)[^@/\\s]+@", "***@", text)
    text = re.sub(r"(?i)\\b(?:gh[oprsu]_|github_pat_)[a-z0-9_]{12,}\\b", "***", text)
    lines = ("".join(ch if ch.isprintable() else " " for ch in line) for line in text[:4096].splitlines())
    return [line for line in lines if line.strip()][:24]


def publish(phase, admission=None, result=None):
    from quality_format import quality_report
    binding = event()
    api = GitHub()
    api.current(binding)
    if phase == "start":
        api.status(binding, "pending", "Waiting for protected intake and Boat comparison")
        from inline_status import CONTEXT as INLINE_CONTEXT
        api.status(binding, "pending", "Waiting for admitted inline-virtual evidence", context=INLINE_CONTEXT)
        return
    decision_path = admission / "decision.json"
    final_path = result / "verdict.json"
    out = Path(os.environ["MANAGED_PUBLIC_REPORT"])
    out.mkdir(mode=0o700, exist_ok=True)
    record = {"kind": "infrastructure", "messages": [
        "Protected source intake did not produce a verified receipt. Re-run all jobs."]}
    decision = read(decision_path, 4096) if decision_path.is_file() else None
    if decision:
        identity = {"version": 1, "repo": REPO_ID} | {k: binding[k] for k in ("base", "head", "number")}
        if any(decision.get(key) != value for key, value in identity.items()):
            raise ValueError("The admission receipt came from a different pull request.")
        if decision["kind"] == "gate":
            record = {"kind": "gate", "rules": decision["rules"]}
        elif decision["kind"] == "awaiting-approval":
            record = {"kind": "pending", "messages": ["A maintainer can approve Boat comparison by adding the boat-ok label."]}
        elif decision["kind"] in {"compile", "wide"}:
            record = {"kind": "infrastructure", "messages": [
                "Boat compiler or native comparison did not produce a verified receipt. Re-run all jobs."]}
        if decision["kind"] in {"compile", "wide"} and final_path.is_file():
            verdict = read(final_path, 256 * 1024)
            identity |= {k: decision[k] for k in ("tree", "plan")}
            if any(verdict.get(key) != value for key, value in identity.items()):
                raise ValueError("The compiler receipt did not match the admission.")
            record = verdict["report"]
            metadata = {"counts": verdict["counts"], "functions": verdict["functions"], "kind": record["kind"]}
            if decision["kind"] == "wide":
                matrix = verdict["matrix"]
                if (set(matrix) != {"runners", "paired_results"} or type(matrix["runners"]) is not int
                        or not 1 <= matrix["runners"] <= 16 or matrix["paired_results"] != 2 * record["judged"]):
                    raise ValueError("The wide verdict lacks complete paired measurements.")
                record["messages"].append(f"{matrix['runners']} Boat runners checked {matrix['paired_results']} paired TU results.")
                metadata["matrix"] = matrix
            write(out / "verdict.json", identity | metadata)
    report = quality_report(binding["base"], binding["head"], record) + "\n"
    (out / "summary.md").write_text(report)
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a") as stream:
        stream.write(report)
    states = {"ok": "success", "pending": "pending", "gate": "failure", "regression": "failure",
              "infrastructure": "error"}
    status = states[record["kind"]]
    message = {"success": "BFME II comparison passed", "failure": "BFME II check refused this patch",
               "pending": "Waiting for required approval",
               "error": ("Boat comparison unavailable. Re-run all jobs." if decision else
                         "Protected Git intake unavailable. Re-run all jobs.")}[status]
    # Keep the status pending if the event was superseded while preparing the report.
    latest = api.current(binding)
    if status == "success" and not admitted(latest, binding.get("event_association")):
        raise Superseded()
    api.status(binding, status, f"{message} (main {binding['base'][:12]})")
    if status in {"failure", "error"}:
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

