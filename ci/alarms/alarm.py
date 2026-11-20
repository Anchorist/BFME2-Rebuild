"""Keep exactly one GitHub issue per kind of failure: open or update it on failure, close it when clear.

    python3 -B ci/alarms/alarm.py raise KIND --detail "expected X, found Y" [--run-url URL]
    python3 -B ci/alarms/alarm.py clear KIND [--run-url URL]
    python3 -B ci/alarms/alarm.py set KIND --failed true|false --detail ... [--run-url URL]

The token is read from ALARM_TOKEN (it needs `issues: write` and nothing else).
Issues carry the label `alarm` and a hidden marker naming the kind, so a renamed
title still finds its issue. Raising an open alarm edits its body (no new
notification); raising a closed one reopens it with a comment; clearing an open
one comments and closes it; clearing a closed one does nothing.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

KINDS = {
    "state-measure": ("Main state measurement failed",
                      "The job that measures every source file on main did not finish."),
    "state-publish": ("Main state could not be published",
                      "A measurement exists but the state branch was not updated from it."),
    "state-stale": ("Main has no measured state",
                    "No measurement of the newest main commit arrived in the expected time."),
    "state-parity": ("Incremental state differs from a full recompute",
                     "The state kept up to date commit by commit disagrees with measuring everything again."),
    "progress-failed": ("Progress card could not be generated",
                        "The job that writes the progress card and its pictures failed."),
    "progress-down": ("A progress figure went down",
                      "A headline figure is lower than in the previous published card."),
    "nightly-build": ("Nightly build did not produce a checked image",
                      "The nightly compile, link or size check stopped before the game ran."),
    "nightly-crash": ("Nightly game run crashed or stopped early",
                      "The rebuilt game did not reach the end of the nightly run."),
    "nightly-differs": ("Nightly game state differs from the original",
                        "The rebuilt game's state differs from the original program's over the compared frames."),
    "nightly-control": ("Nightly comparison missed a deliberate change",
                        "The perturbed control run was not caught, so a clean night cannot be trusted."),
    "worklist-failed": ("Worklists could not be generated",
                        "The job that regenerates worklist/*.tsv failed or its output differs from a second run."),
}
LABEL = "alarm"
MARK = "<!-- alarm-kind: {} -->"


class GitHub:
    def __init__(self, repository, token):
        self.base = f"https://api.github.com/repos/{repository}/"
        self.token = token

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.base + path, data=data, method=method, headers={
            "Authorization": "Bearer " + self.token, "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(4 * 1024**2)
        return json.loads(raw) if raw else None


def find(api, kind):
    mark = MARK.format(kind)
    for page in range(1, 11):
        query = urllib.parse.urlencode({"labels": LABEL, "state": "all", "per_page": 100, "page": page,
                                        "sort": "created", "direction": "asc"})
        items = api.call("GET", "issues?" + query)
        for item in items:
            if "pull_request" not in item and mark in (item.get("body") or ""):
                return item
        if len(items) < 100:
            return None
    return None


def body(kind, detail, run_url):
    title, meaning = KINDS[kind]
    lines = [MARK.format(kind), "", meaning, "", "**Latest failure**", "", "```", detail.strip() or "(no detail)", "```"]
    if run_url:
        lines += ["", f"Run: {run_url}"]
    lines += ["", "This issue is opened, updated and closed by the repository's workflows. "
              "It closes by itself when the next run of the same job succeeds."]
    return "\n".join(lines) + "\n"


def ensure_label(api):
    try:
        api.call("GET", "labels/" + LABEL)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        api.call("POST", "labels", {"name": LABEL, "color": "b60205",
                                    "description": "Opened and closed by the repository's workflows"})


def raise_alarm(api, kind, detail, run_url, out=print):
    title = "Alarm: " + KINDS[kind][0]
    issue = find(api, kind)
    text = body(kind, detail, run_url)
    if issue is None:
        ensure_label(api)
        made = api.call("POST", "issues", {"title": title, "body": text, "labels": [LABEL]})
        out(f"Alarm {kind}: opened issue #{made['number']}.")
        return "opened"
    number = issue["number"]
    if issue["state"] == "open":
        api.call("PATCH", f"issues/{number}", {"body": text, "title": title})
        out(f"Alarm {kind}: issue #{number} was already open; updated its details.")
        return "updated"
    api.call("PATCH", f"issues/{number}", {"state": "open", "body": text, "title": title})
    api.call("POST", f"issues/{number}/comments", {"body": "Failing again." + (f" Run: {run_url}" if run_url else "")})
    out(f"Alarm {kind}: reopened issue #{number}.")
    return "reopened"


def clear_alarm(api, kind, run_url, out=print):
    issue = find(api, kind)
    if issue is None or issue["state"] != "open":
        out(f"Alarm {kind}: clear, nothing open.")
        return "none"
    number = issue["number"]
    api.call("POST", f"issues/{number}/comments", {"body": "Cleared: the job succeeded." + (f" Run: {run_url}" if run_url else "")})
    api.call("PATCH", f"issues/{number}", {"state": "closed", "state_reason": "completed"})
    out(f"Alarm {kind}: closed issue #{number}.")
    return "closed"


def main(argv=None, api=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["raise", "clear", "set"])
    parser.add_argument("kind", choices=sorted(KINDS))
    parser.add_argument("--detail", default="")
    parser.add_argument("--detail-file", default="")
    parser.add_argument("--failed", choices=["true", "false"], default="")
    parser.add_argument("--run-url", default="")
    args = parser.parse_args(argv)
    detail = args.detail
    if args.detail_file and os.path.isfile(args.detail_file):
        with open(args.detail_file, encoding="utf-8", errors="replace") as stream:
            detail = (detail + "\n" + stream.read(16384)).strip()
    if api is None:
        token = os.environ.pop("ALARM_TOKEN", "")
        if not token:
            print("::error::alarm: expected ALARM_TOKEN with issues: write, found none")
            return 1
        api = GitHub(os.environ["GITHUB_REPOSITORY"], token)
    mode = args.mode
    if mode == "set":
        if not args.failed:
            print("::error::alarm set: expected --failed true or false, found nothing")
            return 1
        mode = "raise" if args.failed == "true" else "clear"
    if mode == "raise":
        raise_alarm(api, args.kind, detail, args.run_url)
    else:
        clear_alarm(api, args.kind, args.run_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
