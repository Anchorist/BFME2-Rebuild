"""Fetch the one owner-approved private canary PR as Git objects."""
import argparse
import json
import os
import re
from pathlib import Path
import urllib.request

from gitrepo import Git

ROOT = Path(__file__).resolve().parent
GITHUB_NAME = "Open-BFME/BFME2-Rebuild"
GITHUB_ID = 1464323350


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    if (os.environ.get("GITHUB_REPOSITORY") != GITHUB_NAME
            or os.environ.get("GITHUB_REPOSITORY_ID") != str(GITHUB_ID)
            or os.environ.get("GITHUB_REF") != "refs/heads/main"
            or os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch"):
        raise ValueError("This one-off canary only runs on protected main in the approved private repository.")
    number = os.environ["BFME_CANARY_PR"]
    if not re.fullmatch(r"[1-9][0-9]{0,8}", number):
        raise ValueError("Supply the canonical private pull request number.")
    token = os.environ.pop("BFME_CANARY_READ_TOKEN")
    if not re.fullmatch(r"[A-Za-zA-Z0-9_.-]{15,2048}", token):
        raise ValueError("The protected job needs a read-only GitHub token.")
    plan = json.loads((ROOT / "nt2-plan.json").read_bytes())
    url = f"https://api.github.com/repos/{GITHUB_NAME}/pulls/{number}"

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    request = urllib.request.Request(url, headers={"Authorization": "Bearer " + token,
                                                      "Accept": "application/vnd.github+json"})
    api = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with api.open(request, timeout=30) as response:
        raw = response.read(2 * 1024**2 + 1)
    if len(raw) > 2 * 1024**2:
        raise ValueError("The private PR metadata exceeded its size cap.")
    record = json.loads(raw)
    base = record["base"]
    if (record["state"] != "open" or record["number"] != int(number)
            or base["ref"] != "canary/nt2-base" or base["repo"]["id"] != GITHUB_ID
            or base["sha"] != plan["historical_base"]
            or record["head"]["sha"] != plan["historical_head"]):
        raise ValueError("This PR is not the exact recorded nt2 pair and dedicated base branch.")
    args.target.mkdir(mode=0o700)
    git = Git(args.target / "inputs.git", initialize=True)
    ask = args.target / "read-askpass.sh"
    with ask.open("x") as script:
        script.write('#!/bin/sh\ncase "$1" in *Username*) printf "%s\\n" x-access-token ;;\n'
                     '*Password*) printf "%s\\n" "$BFME_GIT_TOKEN" ;; *) exit 1 ;; esac\n')
    ask.chmod(0o700)
    try:
        remote = f"https://github.com/{GITHUB_NAME}.git"
        env = {"GIT_ASKPASS": str(ask), "BFME_GIT_TOKEN": token}
        git.run("fetch", "-q", "--no-tags", "--no-write-fetch-head", "--depth=2", "--", remote,
                "+refs/heads/canary/nt2-base:refs/heads/main",
                f"+refs/pull/{number}/head:refs/ci/candidate", env=env, timeout=120)
    finally:
        ask.unlink()
    if git.rev("refs/heads/main") != plan["historical_base"] or git.rev("refs/ci/candidate") != plan["historical_head"]:
        raise ValueError("GitHub moved the exact canary refs.")
    (args.target / "admission.json").write_text(json.dumps(
        {"number": int(number), "workflow_sha": os.environ["GITHUB_SHA"],
         "base": plan["historical_base"], "head": plan["historical_head"]}, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()

