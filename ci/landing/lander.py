"""Land pull requests on main one at a time.

A pull request lands only when its required checks passed on its exact head
AND were measured against the main commit that is current when it merges.
.github/workflows/landing.yml runs this file in one job for the whole
repository, so nothing else moves main while it works.

  lander.py select DIR   choose one pull request, refresh a stale measurement,
                         record the exact runs whose receipts must be downloaded
  lander.py land DIR     verify the receipts, re-read main, merge with the
                         expected head, verify the new main commit, report

Receipt and run checks are the protected ones in ci/managed-check/landing_read.py,
imported, not copied.
"""
import inspect
import json
import os
from pathlib import Path
import re
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parent / "managed-check"))

import landing_read as lr  # noqa: E402
from common import CONTEXT as BOAT, HEX40, REPO, REPO_ID, read  # noqa: E402
from inline_status import CONTEXT as INLINE  # noqa: E402
from api import Api, ApiError, ReadOnly, printable  # noqa: E402

RULES = lr.RULES

# --- Policy -----------------------------------------------------------------
# "report-only": Inline virtual must not be failure on current main; pending or
# missing is allowed. "required": it must be success like the other two.
INLINE_VIRTUAL_POLICY = "report-only"
REQUIRED = (BOAT, RULES)
REFUSED_BRANCH_PREFIXES = ("canary/", "ci-corpus/", "corpus/")
MERGE_METHOD = "squash"            # one commit per pull request, credited to its author
LANDING_CONTEXT = "BFME II / Landing"
HOLD_LABEL = "landing-hold"
REMEASURE_EVENT = "bfme-remeasure"  # both check workflows measure the PR on current main
LANDED_EVENT = "bfme-landed"        # state and progress workflows run after a landing
NEXT_EVENT = "bfme-land-next"       # this workflow takes the next pull request
MEASURE_WAIT_SECONDS = 1800         # wide changes measured 744 to 978 s
POLL_SECONDS = 20
MAX_OPEN_PULLS = 300
TRAILER = "Landed by the BFME II landing workflow"
MEASURED_LINE = re.compile(r"Measured on main ([0-9a-f]{40}), head ([0-9a-f]{40}), tree ([0-9a-f]{40})\.")
TITLE_NUMBER = re.compile(r"\(#([1-9][0-9]{0,8})\)\Z")


class Held(Exception):
    """A named reason this run does not merge. final=True means the author or a maintainer must act."""

    def __init__(self, code, expected, found, final=False):
        super().__init__(code)
        self.code, self.expected, self.found, self.final = code, expected, found, final

    def line(self):
        return f"{self.code}: Expected {self.expected}. Found {self.found}."


class Failed(Held):
    """Something went wrong after main moved, or the inputs are unusable. The job fails."""


def load_config(path=HERE / "landing.json"):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    approvers = data.get("header_approvers")
    if not isinstance(approvers, list) or any(type(item) is not int or item <= 0 for item in approvers):
        raise Failed("config", "header_approvers as a list of numeric GitHub account ids", "something else")
    exceptions = set()
    for item in data.get("rehearsal_exceptions", []):
        if type(item.get("number")) is not int or not HEX40.fullmatch(item.get("head", "")):
            raise Failed("config", "rehearsal_exceptions entries with a number and a 40-character head", "something else")
        exceptions.add((item["number"], item["head"]))
    if data.get("remeasure") not in {"repository_dispatch", "off"}:
        raise Failed("config", 'remeasure "repository_dispatch" or "off"', repr(data.get("remeasure")))
    return {"approvers": set(approvers), "exceptions": exceptions, "remeasure": data["remeasure"]}


def marker(main):
    return f"(main {main[:12]})"


def current_main(api):
    sha = (api.call("git/ref/heads/main").get("object") or {}).get("sha", "")
    if not HEX40.fullmatch(sha):
        raise Failed("main-unreadable", "the main branch commit", "missing or malformed metadata")
    return sha


def read_statuses(api, head):
    latest = {}
    for page in range(1, 11):
        entries = api.call(f"commits/{head}/statuses?per_page=100&page={page}")
        if not isinstance(entries, list):
            raise Failed("status-list", "GitHub's status list", "a different response")
        for item in entries:
            context = item.get("context")
            if context in (BOAT, RULES, INLINE, LANDING_CONTEXT):
                if context not in latest or item["id"] > latest[context]["id"]:
                    latest[context] = item
        if len(entries) < 100:
            break
    return latest


def classify(status, main):
    """fresh-* = measured on this main; stale-* = measured on another main."""
    if not status:
        return "missing"
    state = status.get("state")
    bound = marker(main) in (status.get("description") or "")
    if (status.get("creator") or {}).get("id") != lr.BOT_ID:
        return "untrusted"
    if state == "pending":
        return "pending"
    if state not in {"success", "failure", "error"}:
        return "missing"
    kind = "success" if state == "success" else "failure"
    return ("fresh-" if bound else "stale-") + kind


def changed_files(api, number):
    names = []
    for page in range(1, 31):
        entries = api.call(f"pulls/{number}/files?per_page=100&page={page}")
        if not isinstance(entries, list):
            raise Failed("file-list", "the pull request's changed file list", "a different response")
        for item in entries:
            names.append(item.get("filename", ""))
            if item.get("previous_filename"):
                names.append(item["previous_filename"])
        if len(entries) < 100:
            return names
    raise Held("too-many-files", "at most 3000 changed files", "more", final=True)


def evaluate(api, number, main, config):
    """Return a decision dict: stage land | remeasure | hold, with every named reason found."""
    pr = api.call(f"pulls/{number}")
    head = (pr.get("head") or {}).get("sha", "")
    decision = {"number": number, "head": head, "title": printable(pr.get("title", ""), 120),
                "author": (pr.get("user") or {}).get("login"), "stage": "hold", "reasons": [], "checks": {}}
    reasons = decision["reasons"]

    def hold(code, expected, found, final=False):
        reasons.append(Held(code, expected, found, final))

    if pr.get("state") != "open" or pr.get("number") != number or not HEX40.fullmatch(head):
        hold("not-open", "an open pull request with an exact head", "a closed or malformed pull request", True)
        return decision
    base = pr.get("base") or {}
    if base.get("ref") != "main" or (base.get("repo") or {}).get("id") != REPO_ID:
        hold("not-main", "a pull request into this repository's main", f"base {printable(base.get('ref'), 60)}", True)
        return decision
    head_ref = (pr.get("head") or {}).get("ref", "")
    if head_ref.startswith(REFUSED_BRANCH_PREFIXES) and (number, head) not in config["exceptions"]:
        hold("refused-branch", "an ordinary contributor branch",
             f"branch {printable(head_ref, 80)}, a rehearsal or corpus branch that never lands", True)
    if pr.get("draft") is not False:
        hold("draft", "a pull request marked ready for review", "a draft")
    if any(label.get("name") == HOLD_LABEL for label in pr.get("labels") or ()):
        hold("hold-label", f"no {HOLD_LABEL} label", f"the {HOLD_LABEL} label")
    if not (pr.get("head") or {}).get("repo"):
        hold("head-repository-missing", "the pull request's source repository", "a deleted repository", True)
    files = changed_files(api, number)
    if any(name.startswith(".github/") for name in files):
        hold("workflow-change", "no change under .github/", "a workflow change; a maintainer merges those by hand", True)
    if any(name.startswith("include/") for name in files):
        if not config["approvers"]:
            hold("header-approvers-empty", "a listed header approver in ci/landing/landing.json",
                 "an empty list, so no header change can land automatically", True)
        else:
            try:
                approved = lr.maintainer_review(api, pr, {"number": number, "head": head}, config["approvers"])
            except lr.Waiting as exc:
                hold("header-approval", "a readable review history", str(exc))
            else:
                if not approved:
                    hold("header-approval", f"an approval of head {head[:12]} by a listed header approver",
                         "no such approval")
    if pr.get("mergeable") is False:
        hold("merge-conflict", "a pull request that merges cleanly into main",
             "a conflict; merge or rebase main into the branch", True)

    statuses = read_statuses(api, head)
    decision["landing_status"] = statuses.get(LANDING_CONTEXT)
    stale = False
    required = REQUIRED + ((INLINE,) if INLINE_VIRTUAL_POLICY == "required" else ())
    for context in (BOAT, RULES, INLINE):
        kind = classify(statuses.get(context), main)
        decision["checks"][context] = kind
        if context == INLINE and context not in required:
            if kind == "fresh-failure":
                hold("inline-virtual-failure", f"{INLINE} not failure on main {main[:12]}", "failure", True)
            elif kind == "stale-failure":
                stale = True
            continue
        if kind == "fresh-success":
            continue
        if kind == "stale-success":
            stale = True
        elif kind == "fresh-failure":
            hold("check-failure", f"{context} success on main {main[:12]}", "failure or error", True)
        elif kind == "stale-failure":
            hold("check-failure", f"{context} success", "failure on an older main; push a fix to start a new check", True)
        elif kind == "pending":
            hold("measuring", f"{context} finished", "pending")
        else:
            hold("no-status", f"{context} from GitHub Actions on head {head[:12]}", kind)
    if not reasons:
        decision["stage"] = "remeasure" if stale else "land"
        decision["inline"] = statuses.get(INLINE, {}).get("state") if decision["checks"][INLINE] == "fresh-success" else "pending"
    return decision


def open_pulls(api):
    numbers = []
    for page in range(1, MAX_OPEN_PULLS // 100 + 1):
        entries = api.call(f"pulls?state=open&base=main&sort=created&direction=asc&per_page=100&page={page}")
        numbers += [item["number"] for item in entries]
        if len(entries) < 100:
            break
    return numbers


def main_failed_landing(api, main):
    status = read_statuses(api, main).get(LANDING_CONTEXT)
    return status and status.get("state") == "failure" and (status.get("creator") or {}).get("id") == lr.BOT_ID


def report_hold(api, decision):
    """Live only: keep one current BFME II / Landing status on the pull request head."""
    if not api.live or not decision["reasons"]:
        return
    first = decision["reasons"][0]
    state = "failure" if first.final else "pending"
    text = printable(f"Held: {first.code}. Expected {first.expected}.", 140)
    prior = decision.get("landing_status") or {}
    if prior.get("state") == state and prior.get("description") == text:
        return
    status(api, decision["head"], state, text)


def status(api, sha, state, text):
    run = getattr(api, "run_id", "") or ""
    body = {"state": state, "context": LANDING_CONTEXT, "description": printable(text, 140)}
    if run.isdigit():
        body["target_url"] = f"https://github.com/{REPO}/actions/runs/{run}"
    code, _ = api.write("POST", f"statuses/{sha}", body)
    if code != 201:
        raise Failed("status-write", f"HTTP 201 for the {LANDING_CONTEXT} status", f"HTTP {code}")


def comment(api, number, text):
    code, _ = api.write("POST", f"issues/{number}/comments", {"body": text})
    if code != 201:
        print(f"comment: Expected HTTP 201 for a comment on #{number}. Found HTTP {code}.", file=sys.stderr)


def dispatch(api, event, payload):
    code, _ = api.write("POST", "dispatches", {"event_type": event, "client_payload": payload})
    if code != 204:
        raise Failed("dispatch", f"HTTP 204 for repository_dispatch {event}", f"HTTP {code}")


def optional_inline_supported():
    """ci/managed-check/landing_read.py accepts inline_required=False from its remeasure release on."""
    return "inline_required" in inspect.signature(lr.start_runs).parameters


def inline_options(inline):
    if inline == "success":
        return {}
    if INLINE_VIRTUAL_POLICY == "required":
        raise Held("inline-virtual", f"{INLINE} success", inline)
    if not optional_inline_supported():
        raise Held("inline-virtual-pending", "a receipt reader that accepts a report-only Inline virtual result",
                   "the installed ci/managed-check/landing_read.py, which requires Inline virtual success")
    return {"inline_required": False}


def runs_for(api, binding, inline):
    """Exact producing runs, read by the protected landing_read.start_runs."""
    options = inline_options(inline)
    try:
        runs = lr.start_runs(api, binding, **options)
    except lr.Waiting as exc:
        raise Held("run-binding", "protected runs bound to this head and main", str(exc)) from None
    return {"match": list(runs[BOAT]), "rules": list(runs[RULES]), "inline": "success" if not options else "pending"}


def output(name, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with Path(path).open("a") as stream:
            stream.write(f"{name}={value}\n")


def summary(lines):
    text = "\n".join(lines) + "\n"
    print(text)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with Path(path).open("a") as stream:
            stream.write(text)


def table(decisions, main, live):
    lines = [f"**BFME II landing** ({'live' if live else 'dry run'}) on main `{main[:12]}`", "",
             "| PR | Head | Boat | Source rules | Inline virtual | Decision |", "|---|---|---|---|---|---|"]
    for item in decisions:
        if item["reasons"]:
            first = item["reasons"][0]
            more = f" (+{len(item['reasons']) - 1} more)" if len(item["reasons"]) > 1 else ""
            verdict = f"Held: {first.line()}{more}"
        else:
            verdict = {"land": "Eligible: measured on current main", "remeasure": "Eligible after a fresh measurement on current main"}[item["stage"]]
        checks = item["checks"]
        lines.append(f"| #{item['number']} | `{item['head'][:12]}` | {checks.get(BOAT, '-')} | {checks.get(RULES, '-')} "
                     f"| {checks.get(INLINE, '-')} | {verdict} |")
    return lines


def wait_for_measurement(api, config, binding, clock, sleep):
    deadline = clock() + MEASURE_WAIT_SECONDS
    while True:
        sleep(POLL_SECONDS)
        main = current_main(api)
        if main != binding["base"]:
            raise Held("main-moved", f"main {binding['base'][:12]} while measuring", f"main {main[:12]}")
        decision = evaluate(api, binding["number"], main, config)
        if decision["head"] != binding["head"]:
            raise Held("head-changed", f"head {binding['head'][:12]}", f"head {decision['head'][:12]}")
        if decision["stage"] == "land":
            return decision
        hard = [item for item in decision["reasons"] if item.code != "measuring"]
        if hard:
            raise hard[0]
        if clock() >= deadline:
            raise Held("measurement-timeout", f"fresh results {marker(main)} within {MEASURE_WAIT_SECONDS} s",
                       "checks still pending or not started; are the check workflows listening for "
                       f"repository_dispatch {REMEASURE_EVENT}?")


def timed_out(decision, main):
    """A re-measurement that already timed out on this main is not retried until main or the head changes."""
    text = (decision.get("landing_status") or {}).get("description") or ""
    return text.startswith("Held: measurement-timeout") and marker(main) in text


def select(api, env, config, directory, clock=time.monotonic, sleep=time.sleep):
    main = current_main(api)
    if env.get("GITHUB_SHA") != main:
        summary([f"Superseded: this run started on main {env.get('GITHUB_SHA', '')[:12]}; main is now {main[:12]}. "
                 "A newer run takes over."])
        output("action", "none")
        return 0
    reconcile(api, main)
    if main_failed_landing(api, main):
        raise Failed("main-unverified", f"main {main[:12]} without a failed {LANDING_CONTEXT} status",
                     "a failed post-landing verification; a maintainer must repair main first")
    only = env.get("BFME_LANDING_PR", "").strip()
    if only and not lr.NUMBER.fullmatch(only):
        raise Failed("input", "a pull request number or nothing", printable(only, 40))
    numbers = [int(only)] if only else open_pulls(api)
    decisions = [evaluate(api, number, main, config) for number in numbers]
    for item in decisions:
        report_hold(api, item)
    lines = table(decisions, main, api.live)
    pick = (next((item for item in decisions if item["stage"] == "land"), None)
            or next((item for item in decisions if item["stage"] == "remeasure" and not timed_out(item, main)), None))
    if pick is None:
        summary(lines + ["", "Nothing to land."])
        output("action", "none")
        return 0
    binding = {"number": pick["number"], "base": main, "head": pick["head"]}
    if pick["stage"] == "remeasure":
        if config["remeasure"] == "off":
            summary(lines + ["", f"#{pick['number']} needs a fresh measurement on main {main[:12]}; "
                             "automatic re-measurement is off. Push a commit or reopen the pull request."])
            output("action", "none")
            return 0
        if not api.live:
            summary(lines + ["", f"Would send repository_dispatch {REMEASURE_EVENT} for #{pick['number']} "
                             f"head {pick['head'][:12]} on main {main[:12]} and wait for fresh results."])
            output("action", "none")
            return 0
        dispatch(api, REMEASURE_EVENT, binding)
        status(api, pick["head"], "pending", f"Measuring on main {main[:12]} before landing")
        print(f"Requested a fresh measurement of #{pick['number']} on main {main[:12]}.")
        try:
            pick = wait_for_measurement(api, config, binding, clock, sleep)
        except Held as exc:
            report_hold(api, {"head": binding["head"], "reasons": [exc], "landing_status": None})
            summary(lines + ["", f"#{binding['number']} held after re-measurement. {exc.line()}"])
            output("action", "none")
            return 0
    runs = runs_for(api, binding, pick["inline"])
    Path(directory).mkdir(mode=0o700, parents=True)
    Path(directory, "binding.json").write_text(json.dumps(binding | {"runs": runs}, sort_keys=True) + "\n")
    for key, value in (("action", "land"), ("number", binding["number"]), ("match_run", runs["match"][0]),
                       ("match_attempt", runs["match"][1]), ("rules_run", runs["rules"][0]),
                       ("rules_attempt", runs["rules"][1]), ("inline", runs["inline"])):
        output(key, value)
    summary(lines + ["", f"Candidate #{binding['number']} head {binding['head'][:12]} on main {main[:12]}; "
                     "collecting its receipts."])
    return 0


def land(api, env, config, directory, sleep=time.sleep):
    directory = Path(directory)
    prior = read(directory / "binding.json", 4096)
    binding = {key: prior[key] for key in ("number", "base", "head")}
    if env.get("GITHUB_SHA") != binding["base"]:
        raise Failed("binding", f"a candidate measured on this run's main {env.get('GITHUB_SHA', '')[:12]}",
                     f"main {binding['base'][:12]}")
    decision = evaluate(api, binding["number"], binding["base"], config)
    if decision["head"] != binding["head"]:
        raise Held("head-changed", f"head {binding['head'][:12]}", f"head {decision['head'][:12]}")
    if decision["stage"] != "land":
        raise decision["reasons"][0] if decision["reasons"] else Held(
            "stale", f"results measured on main {binding['base'][:12]}", "results for another main")
    runs = runs_for(api, binding, decision["inline"])
    if runs != prior["runs"]:
        raise Held("attempt-changed", "the same producing runs as when the receipts were downloaded", "different runs")
    match = read(directory / "match/verdict.json", 256 * 1024)
    rules = read(directory / "rules/receipt.json", 4096)
    from gate import policy_digest
    rules_policy = policy_digest(lr.TOOLS / "config.json")
    options = inline_options(runs["inline"])
    inline = read(directory / "inline/inline-status.json", 4096) if not options else None
    try:
        positions = lr.compare_receipts(match, inline, rules, binding, runs["match"][1], runs["match"][0],
                                        runs["rules"][1], runs["rules"][0], rules_policy, **options)
    except lr.Waiting as exc:
        raise Held("receipt", "receipts for the same main, head and tree", str(exc)) from None
    tree = positions["tree"]

    # Immediately before the merge: main must still be the measured commit.
    main = current_main(api)
    if main != binding["base"]:
        raise Held("main-moved", f"main {binding['base'][:12]}, the commit the checks measured", f"main {main[:12]}")
    if not api.live:
        summary([f"Would merge #{binding['number']} ({MERGE_METHOD}) with expected head {binding['head'][:12]} "
                 f"onto main {main[:12]}, expecting one parent {main[:12]} and tree {tree[:12]}."])
        return 0
    pr_title = decision["title"]
    body = {"merge_method": MERGE_METHOD, "sha": binding["head"],
            "commit_title": printable(f"{pr_title} (#{binding['number']})", 250),
            "commit_message": (f"Measured on main {binding['base']}, head {binding['head']}, tree {tree}.\n"
                               f"Landed by the BFME II landing workflow, run {env.get('GITHUB_RUN_ID', '')}.")}
    code, payload = api.write("PUT", f"pulls/{binding['number']}/merge", body)
    message = printable((payload or {}).get("message", ""), 160)
    if code == 409:
        raise Held("head-changed", f"head {binding['head'][:12]} at merge", f"GitHub refused: {message}")
    if code == 405:
        held = Held("merge-refused", "GitHub to merge the pull request", f"HTTP 405: {message}", True)
        report_hold(api, {"head": binding["head"], "reasons": [held], "landing_status": None})
        comment(api, binding["number"], f"Held: GitHub would not merge this pull request ({message}). "
                "If it conflicts with main, merge or rebase main into your branch and push.")
        raise held
    if code != 200 or not (payload or {}).get("merged") or not HEX40.fullmatch((payload or {}).get("sha", "")):
        raise Failed("merge", "HTTP 200 and a merged commit", f"HTTP {code}: {message}")
    commit = payload["sha"]
    verify(api, binding, tree, commit, sleep)
    status(api, commit, "success", f"Verified landing of #{binding['number']}: parent {binding['base'][:12]}, tree {tree[:12]}")
    status(api, binding["head"], "success", f"Landed as {commit[:12]}")
    comment(api, binding["number"], f"Landed as {commit} on main. Measured on main {binding['base'][:12]}, "
            f"candidate tree {tree[:12]}; the new main commit has exactly that parent and tree.")
    notified = []
    events = [(LANDED_EVENT, landed_payload(binding["number"], binding["head"], binding["base"], commit, tree))]
    if env.get("BFME_LANDING_CHAIN") == "1":
        events.append((NEXT_EVENT, {"after": commit}))
    for event, payload in events:
        try:
            dispatch(api, event, payload)
            notified.append(event)
        except Held as exc:
            print(exc.line(), file=sys.stderr)
    summary([f"Landed #{binding['number']} as {commit[:12]} (parent {binding['base'][:12]}, tree {tree[:12]}). "
             f"Sent: {', '.join(notified) or 'nothing'}."])
    return 0


def landed_payload(number, head, parent, commit, tree):
    """The exact bfme-landed hand-off the state workflow accepts: these five keys and no others."""
    return {"number": number, "head": head, "parent": parent, "commit": commit, "tree": tree}


def reconcile(api, main):
    """Finish a landing whose merge outcome was never confirmed (lost response, timeout, stopped job).

    A commit made by this workflow names, in its message, the main, head and tree it was measured on. If main's
    newest commit is one of those and has no BFME II / Landing status yet, verify it now, before anything else.
    """
    record = api.call(f"git/commits/{main}")
    message = record.get("message") or ""
    if TRAILER not in message or LANDING_CONTEXT in read_statuses(api, main):
        return
    measured = MEASURED_LINE.search(message)
    number = TITLE_NUMBER.search(message.split("\n", 1)[0].rstrip())
    if not measured or not number:
        raise Failed("unreconciled-landing", f"main {main[:12]} to name its measured main, head, tree and pull request",
                     "a landing commit without them; a maintainer must check main")
    parent, head, tree = measured.groups()
    if not api.live:
        raise Held("unreconciled-landing", f"a {LANDING_CONTEXT} status on main {main[:12]}",
                   "a landing commit not yet verified; the next live run verifies it first")
    parents = [item.get("sha") for item in record.get("parents") or ()]
    found_tree = (record.get("tree") or {}).get("sha")
    binding = {"number": int(number[1]), "head": head, "base": parent}
    if parents != [parent]:
        fail_after(api, binding, main, f"exactly one parent {parent[:12]}",
                   "parents " + (", ".join(p[:12] for p in parents) or "none"))
    if found_tree != tree:
        fail_after(api, binding, main, f"tree {tree[:12]}", f"tree {str(found_tree)[:12]}")
    status(api, main, "success", f"Verified landing of #{binding['number']}: parent {parent[:12]}, tree {tree[:12]}")
    dispatch(api, LANDED_EVENT, landed_payload(binding["number"], head, parent, main, tree))
    print(f"Reconciled the earlier landing of #{binding['number']} as {main[:12]}.")


def verify(api, binding, tree, commit, sleep):
    for attempt in range(5):
        main = current_main(api)
        if main == commit:
            break
        sleep(2)
    else:
        fail_after(api, binding, commit, f"main at the merged commit {commit[:12]}", f"main {main[:12]}")
    record = api.call(f"git/commits/{commit}")
    parents = [item.get("sha") for item in record.get("parents") or ()]
    found_tree = (record.get("tree") or {}).get("sha")
    if parents != [binding["base"]]:
        fail_after(api, binding, commit, f"exactly one parent {binding['base'][:12]}",
                   "parents " + (", ".join(p[:12] for p in parents) or "none"))
    if found_tree != tree:
        fail_after(api, binding, commit, f"tree {tree[:12]}", f"tree {str(found_tree)[:12]}")


def fail_after(api, binding, commit, expected, found):
    try:
        status(api, commit, "failure", f"Landing verification failed: expected {expected}")
        comment(api, binding["number"], f"Merged as {commit}, but main failed verification: expected {expected}, "
                f"found {found}. Automatic landing is stopped until a maintainer repairs main.")
    finally:
        raise Failed("post-merge", expected, found)


def run(argv, env, api=None, config=None, **kwargs):
    mode, directory = argv
    if (env.get("GITHUB_REPOSITORY") != REPO or env.get("GITHUB_REPOSITORY_ID") != str(REPO_ID)
            or env.get("GITHUB_REF") != "refs/heads/main"):
        raise Failed("repository", "this repository's main branch", "another repository or ref")
    live = env.get("BFME_LANDING_MODE") == "live"
    if api is None:
        api = Api(REPO, env.pop("BFME_LANDING_TOKEN", None), live)
    api.run_id = env.get("GITHUB_RUN_ID", "")
    config = config or load_config()
    if mode == "select":
        return select(api, env, config, directory, **kwargs)
    if mode == "land":
        return land(api, env, config, directory, **kwargs)
    raise Failed("mode", "select or land", printable(mode, 20))


def main():
    try:
        return run(sys.argv[1:], os.environ)
    except Failed as exc:
        print(f"Landing stopped. {exc.line()}", file=sys.stderr)
        summary([f"Stopped. {exc.line()}"])
        return 1
    except Held as exc:
        print(f"Landing held. {exc.line()}", file=sys.stderr)
        summary([f"Held. {exc.line()}"])
        return 0
    except (lr.Waiting, ApiError, ReadOnly) as exc:
        print(f"Landing stopped. {printable(exc, 300)}", file=sys.stderr)
        summary([f"Stopped. {printable(exc, 300)}"])
        return 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        detail = f"Expected readable landing inputs. Found a {type(exc).__name__} while reading them."
        print(f"Landing stopped. {detail}", file=sys.stderr)
        summary([f"Stopped. {detail}"])
        return 1


if __name__ == "__main__":
    sys.exit(main())
