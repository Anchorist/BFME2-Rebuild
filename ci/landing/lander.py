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
from concurrent.futures import ThreadPoolExecutor
import datetime
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parent / "managed-check"))

import landing_read as lr  # noqa: E402
from common import CONTEXT as BOAT, HEX40, REPO, REPO_ID, read  # noqa: E402
from inline_status import CONTEXT as INLINE  # noqa: E402
from github_status import admitted  # noqa: E402  (the compiler check's own admission rule)
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
ADMIT_REQUEST_EVENT = "bfme-admit-request"  # admission.yml reserves and starts a measurement of a fork
MEASURE_WAIT_SECONDS = 1800         # wide changes measured 744 to 978 s
LAND_SETTLE_SECONDS = 180           # bounded wait for just-completed runs on stage == land
MAX_PARALLEL_REMEASURES = 5         # fan out stale-ready PRs without holding the global lock
POLL_SECONDS = 20
MAX_OPEN_PULLS = 300
TRAILER = "Landed by the BFME II landing workflow"
# Reconciliation reads only the body this workflow writes (after the title, which a pull request author chooses).
MEASURED_LINE = re.compile(r"Measured on main ([0-9a-f]{40}), head ([0-9a-f]{40}), tree ([0-9a-f]{40})\.")
NUMBER_LINE = re.compile(r"Pull request #([1-9][0-9]{0,8})\.")
TRAILER_LINE = re.compile(re.escape(TRAILER) + r", run [0-9]{1,20}\.")


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


def read_statuses_all(api, head):
    """Read all commit statuses once, returning (latest_any, latest_bot) maps by context."""
    latest, latest_bot = {}, {}
    for page in range(1, 11):
        entries = api.call(f"commits/{head}/statuses?per_page=100&page={page}")
        if not isinstance(entries, list):
            raise Failed("status-list", "GitHub's status list", "a different response")
        for item in entries:
            if isinstance(item, dict) and isinstance(item.get("context"), str) and isinstance(item.get("id"), int):
                context = item["context"]
                if context not in latest or item["id"] > latest[context]["id"]:
                    latest[context] = item
                if (item.get("creator") or {}).get("id") == lr.BOT_ID:
                    if context not in latest_bot or item["id"] > latest_bot[context]["id"]:
                        latest_bot[context] = item
        if len(entries) < 100:
            break
    return latest, latest_bot


def read_statuses(api, head):
    latest, _ = read_statuses_all(api, head)
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
    kind = "success" if state == "success" else ("error" if state == "error" else "failure")
    return ("fresh-" if bound else "stale-") + kind


ADMISSION_CONTEXT = "BFME II / Admission"
ADMITTED_BY_RULE = "Admitted by rule:"
HEADER_RULES_CONTEXT = "BFME II / Header rules"   # H1-H8, written by the header route on the exact head
LEDGER_REQUEST_LABEL = "ledger-request"
PROTECTED_PATHS = ("ci/", "tools/", "config/", "expected/", "baseline/")


def latest_bot_status(api, head, context):
    entries = api.call(f"commits/{head}/statuses?per_page=100&page=1")
    found = [item for item in entries if isinstance(item, dict) and item.get("context") == context
             and (item.get("creator") or {}).get("id") == lr.BOT_ID]
    return max(found, key=lambda item: item["id"]) if found else None


def admission_status(api, head):
    """The latest BFME II / Admission status on this exact commit written by GitHub Actions, or None."""
    entries = api.call(f"commits/{head}/statuses?per_page=100&page=1")
    found = [item for item in entries if isinstance(item, dict) and item.get("context") == ADMISSION_CONTEXT
             and (item.get("creator") or {}).get("id") == lr.BOT_ID]
    return max(found, key=lambda item: item["id"]) if found else None


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
                "author": (pr.get("user") or {}).get("login"), "node_id": pr.get("node_id"),
                "stage": "hold", "reasons": [], "checks": {}}
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
    head_repo = (pr.get("head") or {}).get("repo") or {}
    decision["fork"] = head_repo.get("id") != REPO_ID
    # Trusted: a branch of this repository, or an author who is an owner, member or collaborator.
    decision["trusted"] = not decision["fork"] or pr.get("author_association") in {"OWNER", "MEMBER", "COLLABORATOR"}
    head_ref = (pr.get("head") or {}).get("ref", "")
    # Rehearsal and corpus branches are ours. A fork's branch name is chosen by its author and decides nothing.
    if (not decision["fork"] and head_ref.startswith(REFUSED_BRANCH_PREFIXES)
            and (number, head) not in config["exceptions"]):
        hold("refused-branch", "an ordinary contributor branch",
             f"branch {printable(head_ref, 80)}, a rehearsal or corpus branch that never lands", True)
    if pr.get("draft") is not False:
        hold("draft", "a pull request marked ready for review",
             "a draft; choose Ready for review when you want it to land")
    decision["has_ledger_label"] = any(label.get("name") == LEDGER_REQUEST_LABEL for label in pr.get("labels") or ())
    if any(label.get("name") == HOLD_LABEL for label in pr.get("labels") or ()):
        hold("hold-label", f"no {HOLD_LABEL} label", f"the {HOLD_LABEL} label, set by a maintainer")
    statuses, bot_statuses = read_statuses_all(api, head)
    adm_status = bot_statuses.get(ADMISSION_CONTEXT) or {}
    if not head_repo:
        hold("head-repository-missing", "the pull request's source repository",
             "a deleted repository; open a new pull request from an existing fork", True)
    elif admitted(pr):
        decision["rule_admitted"] = False
    elif (adm_status.get("state") == "success"
          and (adm_status.get("description") or "").startswith(ADMITTED_BY_RULE)):
        # Admitted by rule: each compiler measurement of it is reserved by .github/workflows/admission.yml.
        decision["rule_admitted"] = True
    elif (adm_status.get("description") or "").startswith("Held: daily limit"):
        hold("daily-limit", "room in today's limit for automatic admissions",
             "the limit is reached; retried automatically, you do not need to do anything")
    else:
        hold("awaiting-admission", "an admission of this commit to the compiler check",
             "none yet. Changes to source files only are admitted automatically within a daily limit; other "
             "changes wait for a maintainer (label boat-ok); you do not need to do anything")
    files = changed_files(api, number)
    if any(name.startswith(".github/") for name in files):
        hold("workflow-change", "no change under .github/", "a workflow change; a maintainer merges those by hand", True)
    protected = sorted({name.split("/", 1)[0] + "/" for name in files if name.startswith(PROTECTED_PATHS)})
    if protected:
        # The checks refuse these paths too; the landing workflow never relies on that alone.
        hold("protected-path", "changes only outside " + ", ".join(PROTECTED_PATHS),
             f"a change under {', '.join(protected)}; a maintainer merges those by hand", True)
    header_change = any(name.startswith("include/") for name in files)
    if header_change and config.get("auto_headers"):
        rules = bot_statuses.get(HEADER_RULES_CONTEXT) or {}
        text = rules.get("description") or ""
        if rules.get("state") == "success" and marker(main) in text:
            pass                                    # H1-H8 passed on this head and this main
        elif rules.get("state") in ("failure", "error"):
            hold("header-rules", f"{HEADER_RULES_CONTEXT} success", f"{printable(text, 100)}", True)
        else:
            approved_by_maintainer = False
            if config["approvers"]:
                try:
                    approved_by_maintainer = lr.maintainer_review(
                        api, pr, {"number": number, "head": head}, config["approvers"]
                    )
                except lr.Waiting:
                    approved_by_maintainer = False
            if approved_by_maintainer:
                pass                                # listed maintainer approved this exact head
            elif rules.get("state") == "success":
                decision["header_stale"] = True     # measured on another main: re-measured like the checks
            elif rules.get("state") == "pending" and text.startswith("Held: ledger request"):
                decision["ledger_request"] = True
                hold("ledger-request", "a decision on the ledger change this pull request asks for",
                     f"{printable(text, 90)}; it waits and never fails, you do not need to do anything")
            elif rules.get("state") == "pending" and text.startswith("Held: rule not built"):
                hold("header-rule-not-built", "every header rule to be in place", printable(text, 90))
            elif rules.get("state") == "pending" and text.startswith("Held:"):
                hold("header-rules", f"{HEADER_RULES_CONTEXT} success or listed header approval",
                     f"{printable(text, 90)}; a listed maintainer approval can clear this hold")
            else:
                hold("header-rules", f"{HEADER_RULES_CONTEXT} on head {head[:12]}", "no result yet")
    elif header_change:
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
                         "none yet. A maintainer listed in ci/landing/landing.json reviews every change under "
                         "include/; a new push needs a new approval")
    # GitHub does not recompute "mergeable" when main moves. A compiler check that passed on this exact main composed
    # this head onto it (unique ancestor, three-way merge), so an older "false" does not hold it; the merge itself is
    # still GitHub's and refuses a real conflict.
    if pr.get("mergeable") is False and classify(statuses.get(BOAT), main) != "fresh-success":
        hold("merge-conflict", "a pull request that merges cleanly into main",
             "a conflict; merge or rebase main into the branch", True)
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
        elif kind == "fresh-error":
            hold("infrastructure-error", f"{context} to complete on main {main[:12]}",
                 "an infrastructure error; retried automatically, you do not need to push")
        elif kind == "stale-error":
            hold("infrastructure-error", f"{context} to complete",
                 "an infrastructure error on an older main; retried automatically, you do not need to push")
        elif kind == "fresh-failure":
            hold("check-failure", f"{context} success on main {main[:12]}",
                 "failure; open that check's Details for the reason, then push a fix", True)
        elif kind == "stale-failure":
            hold("check-failure", f"{context} success",
                 "failure on an older main; open that check's Details, then push a fix to start a new check", True)
        elif kind == "pending":
            hold("measuring", f"{context} finished", "pending")
        elif (context == BOAT and kind == "missing" and decision["fork"]
              and pr.get("author_association") not in {"OWNER", "MEMBER", "COLLABORATOR"}):
            # The compiler check runs a contributor's commit only when a maintainer starts it; boat-ok on an
            # earlier commit does not start it for a new push.
            hold("awaiting-readmission", f"a maintainer to admit commit {head[:12]} (remove and add the boat-ok label)",
                 "no compiler check for this commit yet. A maintainer reads each new commit from a contributor "
                 "before the compiler runs it; you do not need to do anything")
        else:
            hold("no-status", f"{context} from GitHub Actions on head {head[:12]}", kind)
    if not reasons:
        decision["stage"] = "remeasure" if stale or decision.get("header_stale") else "land"
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


CLEARED = "Cleared to land on main"


def report_hold(api, decision, main=None):
    """Live only: keep one current BFME II / Landing status on the pull request head.

    That status is also a required check of main's ruleset. "Cleared to land" exists only while this job merges
    that exact head, so a clearance left behind by an interrupted run is withdrawn here.
    """
    if not api.live:
        return
    prior = decision.get("landing_status") or {}
    if not decision["reasons"]:
        if prior.get("state") == "success" and (prior.get("description") or "").startswith(CLEARED):
            status(api, decision["head"], "pending", "Eligible; waiting for the landing job")
        return
    first = decision["reasons"][0]
    if (first.code == "measuring" and main
            and prior.get("state") == "pending"
            and prior.get("description") == f"Measuring on main {main[:12]} before landing"):
        return
    state = "failure" if first.final else "pending"
    text = printable(f"Held: {first.code}. Expected {first.expected}.", 140)
    if prior.get("state") == state and prior.get("description") == text:
        return
    status(api, decision["head"], state, text)


def label_ledger_request(api, decision):
    """H9: a pull request waiting for a ledger decision carries the ledger-request label (live only, once)."""
    if not api.live or not decision.get("ledger_request") or decision.get("has_ledger_label"):
        return
    code, _ = api.write("POST", f"issues/{decision['number']}/labels", {"labels": [LEDGER_REQUEST_LABEL]})
    if code not in (200, 201):
        print(f"label: Expected HTTP 200 adding {LEDGER_REQUEST_LABEL} to #{decision['number']}. Found HTTP {code}.",
              file=sys.stderr)


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


def headline(text):
    """One line for someone reading the Actions page: an annotation on the run plus the top of the summary."""
    text = printable(text, 200).replace("::", ": ")
    print(f"::notice title=BFME II landing::{text}")
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with Path(path).open("a") as stream:
            stream.write(f"### {text}\n\n")


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


def wait_for_measurement(api, config, binding, clock, sleep, check_first=False, max_wait=MEASURE_WAIT_SECONDS):
    """Poll until fresh results on this main exist AND their producing runs have completed and bind.

    A check posts its status a few seconds before its workflow run is marked completed, so a fresh status alone
    is not enough: the protected run check in landing_read requires a completed run.
    """
    deadline = clock() + (max_wait if api.live else 0)
    first = True
    while True:
        if not (first and check_first):
            sleep(POLL_SECONDS)
        first = False
        main = current_main(api)
        if main != binding["base"]:
            raise Held("main-moved", f"main {binding['base'][:12]} while measuring", f"main {main[:12]}")
        decision = evaluate(api, binding["number"], main, config)
        if decision["head"] != binding["head"]:
            raise Held("head-changed", f"head {binding['head'][:12]}", f"head {decision['head'][:12]}")
        if decision["stage"] == "land":
            try:
                return decision, runs_for(api, binding, decision["inline"])
            except Held as exc:
                if exc.code != "run-binding":
                    raise
                print(f"Fresh results seen; waiting for their runs to complete ({exc.found[:120]}).")
                if clock() >= deadline:
                    raise
                continue
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


def measuring_state(decision, main, wall_clock=None):
    """Return 'active', 'expired', or None for an in-flight non-blocking remeasurement on this main."""
    prior = decision.get("landing_status") or {}
    expected = f"Measuring on main {main[:12]} before landing"
    if prior.get("state") != "pending" or prior.get("description") != expected:
        return None
    created = prior.get("created_at") or ""
    if not created:
        return "active"
    try:
        started = datetime.datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return "active"
    now = wall_clock() if wall_clock else datetime.datetime.now(datetime.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=datetime.timezone.utc)
    return "expired" if (now - started).total_seconds() >= MEASURE_WAIT_SECONDS else "active"


ENQUEUE = ("mutation($pr: ID!, $head: GitObjectID!) { enqueuePullRequest(input: "
           "{pullRequestId: $pr, expectedHeadOid: $head}) { mergeQueueEntry { position } } }")
QUEUED = "Cleared for the merge queue at head"
GROUP_REF = re.compile(r"refs/heads/gh-readonly-queue/main/pr-([1-9][0-9]{0,8})-([0-9a-f]{40})\Z")


def group(api, env):
    """merge_group: vouch for a queue commit only when this workflow queued that exact pull request head.

    main's ruleset requires BFME II / Landing on the queue commit as well, so a pull request queued any other way
    (a writer's "merge when ready") is drained from the queue with a named reason. Nothing from the queue commit is
    run: the workflow checks these tools out from the group's base, which is main.
    """
    event = read(env["GITHUB_EVENT_PATH"], 2 * 1024**2).get("merge_group") or {}
    sha, ref = event.get("head_sha") or "", event.get("head_ref") or ""
    if not HEX40.fullmatch(sha):
        raise Failed("merge-group", "a merge group with a 40-character head commit", "missing or malformed metadata")
    found = GROUP_REF.fullmatch(ref)
    if not found:
        held = Held("merge-group-ref", "a queue ref refs/heads/gh-readonly-queue/main/pr-<number>-<head>",
                    printable(ref, 100) or "no ref")
    else:
        number, head = int(found[1]), found[2]
        pr = api.call(f"pulls/{number}")
        landing = read_statuses(api, head).get(LANDING_CONTEXT) or {}
        held = None
        if pr.get("state") != "open" or (pr.get("head") or {}).get("sha") != head:
            held = Held("head-changed", f"#{number} open at head {head[:12]}", "a different head or a closed pull request")
        elif (landing.get("state") != "success" or landing.get("description") != f"{QUEUED} {head[:12]}"
              or (landing.get("creator") or {}).get("id") != lr.BOT_ID):
            held = Held("not-queued-by-landing", f"#{number} queued by the landing workflow at head {head[:12]}",
                        "a pull request added to the queue another way")
    if held:
        status(api, sha, "failure", f"Held: {held.code}. Expected {held.expected}.")
        headline(f"Merge group {sha[:12]} refused: {held.code}.")
        summary([f"Refused merge group {sha[:12]}. {held.line()}"])
        return 0
    status(api, sha, "success", f"Cleared in the merge queue: #{number} head {head[:12]}")
    headline(f"Merge group {sha[:12]} cleared for #{number} at head {head[:12]}.")
    return 0


def merge_queue_active(api):
    """True when an active ruleset requires the merge queue on main.

    The private Free repository answers 403 (rules unavailable); then the job merges directly. That is safe in both
    directions: once a queue is required, GitHub refuses a direct merge (HTTP 405) and the job only holds.
    """
    try:
        rules = api.call("rules/branches/main")
    except ApiError:
        return False
    return isinstance(rules, list) and any(isinstance(rule, dict) and rule.get("type") == "merge_queue"
                                           for rule in rules)


def enqueue(api, decisions, main, lines):
    """Merge-queue mode: add every eligible pull request to GitHub's queue with its expected head.

    The queue measures main plus the pull request again (merge_group) and merges exactly what it measured, so this
    job neither re-measures nor merges. The hold rules above (admission, header approval, refusals) still decide
    what may enter the queue.
    """
    ready = [item for item in decisions if item["stage"] in {"land", "remeasure"}]
    done, failed = [], []
    for item in ready:
        prior = (item.get("landing_status") or {}).get("description") or ""
        if prior == f"{QUEUED} {item['head'][:12]}":
            continue
        if not api.live:
            done.append(f"#{item['number']} (dry run: would queue)")
            continue
        # The ruleset requires this status on the pull request and on its queue commit (see group()).
        status(api, item["head"], "success", f"{QUEUED} {item['head'][:12]}")
        try:
            api.mutate(ENQUEUE, {"pr": item["node_id"], "head": item["head"]})
        except ApiError as exc:
            held = Held("enqueue-refused", "GitHub to accept the pull request into the merge queue", str(exc)[:160])
            report_hold(api, {"head": item["head"], "reasons": [held], "landing_status": None})
            failed.append(f"#{item['number']}")
            continue
        done.append(f"#{item['number']}")
    headline(f"Merge queue mode on main {main[:12]}: queued {', '.join(done) or 'nothing new'}"
             + (f"; refused {', '.join(failed)}" if failed else "") + ".")
    summary(lines)
    output("action", "none")
    return 0


def select(api, env, config, directory, clock=time.monotonic, sleep=time.sleep):
    main = current_main(api)
    if env.get("GITHUB_SHA") != main:
        headline(f"Superseded: main moved to {main[:12]} after this run started; a newer run takes over.")
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
    if len(numbers) > 1 and getattr(api, "thread_safe_reads", False):
        with ThreadPoolExecutor(max_workers=min(6, len(numbers))) as pool:
            decisions = list(pool.map(lambda n: evaluate(api, n, main, config), numbers))
    else:
        decisions = [evaluate(api, number, main, config) for number in numbers]
    for item in decisions:
        report_hold(api, item, main=main)
        label_ledger_request(api, item)
    lines = table(decisions, main, api.live)
    if merge_queue_active(api):
        return enqueue(api, decisions, main, lines)
    pick = next((item for item in decisions if item["stage"] == "land"), None)
    if pick is None:
        stale_items = [item for item in decisions if item["stage"] == "remeasure" and not timed_out(item, main)]
        if not stale_items:
            held = [f"#{item['number']} {item['reasons'][0].code}" for item in decisions if item["reasons"]]
            headline(f"Nothing to land on main {main[:12]}: {len(decisions)} open pull request(s)"
                     + (f"; held {', '.join(held[:6])}" if held else "") + ".")
            summary(lines + ["", "Nothing to land."])
            output("action", "none")
            return 0
        if config["remeasure"] == "off":
            first = stale_items[0]
            headline(f"#{first['number']} waits: measured on an older main and automatic re-measurement is off.")
            summary(lines + ["", f"#{first['number']} needs a fresh measurement on main {main[:12]}; "
                             "automatic re-measurement is off. Push a commit or reopen the pull request."])
            output("action", "none")
            return 0
        if not api.live:
            first = stale_items[0]
            headline(f"Dry run: would re-measure #{first['number']} on main {main[:12]}, then land it.")
            summary(lines + ["", f"Would send repository_dispatch {REMEASURE_EVENT} for #{first['number']} "
                             f"head {first['head'][:12]} on main {main[:12]} and land once fresh results arrive."])
            output("action", "none")
            return 0
        dispatched, active, expired, held_notes, pending_dispatch = [], [], [], [], []
        for item in stale_items:
            mstate = measuring_state(item, main)
            if mstate == "active":
                active.append(f"#{item['number']}")
            elif mstate == "expired":
                exc = Held("measurement-timeout", f"fresh results {marker(main)} within {MEASURE_WAIT_SECONDS} s",
                           "checks still pending or not started; are the check workflows listening for "
                           f"repository_dispatch {REMEASURE_EVENT}?")
                report_hold(api, {"head": item["head"], "reasons": [exc], "landing_status": None})
                expired.append(f"#{item['number']}")
            else:
                pending_dispatch.append(item)
        in_flight_measuring = sum(
            1 for item in decisions
            if item["reasons"] and any(r.code == "measuring" for r in item["reasons"])
            and measuring_state(item, main) != "expired"
        )
        for item in pending_dispatch:
            if len(active) + in_flight_measuring + len(dispatched) >= MAX_PARALLEL_REMEASURES:
                break
            item_binding = {"number": item["number"], "base": main, "head": item["head"]}
            if config.get("auto_admission"):
                dispatch(api, ADMIT_REQUEST_EVENT, {"number": item["number"]})
            elif not item.get("trusted"):
                held = Held("awaiting-readmission", f"a maintainer to admit commit {item['head'][:12]} on main "
                            f"{main[:12]} (remove and add the boat-ok label)",
                            "a measurement on an older main only; you do not need to do anything")
                report_hold(api, {"head": item["head"], "reasons": [held], "landing_status": None})
                held_notes.append(f"#{item['number']} held. {held.line()}")
                continue
            else:
                dispatch(api, REMEASURE_EVENT, item_binding)
            status(api, item["head"], "pending", f"Measuring on main {main[:12]} before landing")
            print(f"Requested a fresh measurement of #{item['number']} on main {main[:12]}.")
            dispatched.append(f"#{item['number']}")
        notes = []
        if dispatched:
            notes.append(f"Requested fresh measurements on main {main[:12]} for {', '.join(dispatched)}; "
                         "landing resumes automatically when results arrive.")
        if active:
            notes.append(f"Already measuring on main {main[:12]}: {', '.join(active)}.")
        if expired:
            notes.append(f"Held (measurement-timeout) on main {main[:12]}: {', '.join(expired)}.")
        notes.extend(held_notes)
        if dispatched:
            headline(f"Requested non-blocking re-measurement on main {main[:12]} for {', '.join(dispatched)}.")
        elif expired:
            headline(f"Held {', '.join(expired)}: measurement-timeout.")
        elif held_notes:
            headline(f"Held: awaiting-readmission ({len(held_notes)} pull request(s)).")
        else:
            waiting_desc = ", ".join(active) if active else f"{in_flight_measuring} measuring pull request(s)"
            headline(f"Waiting for in-flight measurements on main {main[:12]}: {waiting_desc}.")
        summary(lines + [""] + (notes or ["Nothing to land."]))
        output("action", "none")
        return 0
    binding = {"number": pick["number"], "base": main, "head": pick["head"]}
    try:
        pick, runs = wait_for_measurement(api, config, binding, clock, sleep,
                                          check_first=True, max_wait=LAND_SETTLE_SECONDS)
    except Held as exc:
        report_hold(api, {"head": binding["head"], "reasons": [exc], "landing_status": None})
        headline(f"Held #{binding['number']}: {exc.code}. Expected {exc.expected}.")
        summary(lines + ["", f"#{binding['number']} held while waiting for its results. {exc.line()}"])
        output("action", "none")
        return 0
    Path(directory).mkdir(mode=0o700, parents=True)
    Path(directory, "binding.json").write_text(json.dumps(binding | {"runs": runs}, sort_keys=True) + "\n")
    for key, value in (("action", "land"), ("number", binding["number"]), ("match_run", runs["match"][0]),
                       ("match_attempt", runs["match"][1]), ("rules_run", runs["rules"][0]),
                       ("rules_attempt", runs["rules"][1]), ("inline", runs["inline"])):
        output(key, value)
    headline(f"#{binding['number']} is measured on current main {main[:12]}; checking its receipts and merging next.")
    summary(lines + ["", f"Candidate #{binding['number']} head {binding['head'][:12]} on main {main[:12]}; "
                     "collecting its receipts."])
    return 0


def land(api, env, config, directory, sleep=time.sleep):
    """Merge the selected pull request. Any hold replaces its Landing status, so "Measuring" never stays behind."""
    directory = Path(directory)
    prior = read(directory / "binding.json", 4096)
    try:
        return land_bound(api, env, config, directory, prior, sleep)
    except Failed:
        raise
    except Held as exc:
        report_hold(api, {"head": prior["head"], "reasons": [exc], "landing_status": None})
        raise
    except (ApiError, OSError, ValueError, KeyError, TypeError):
        if api.live:
            try:
                report_hold(api, {"head": prior["head"], "landing_status": None, "reasons": [Held(
                    "interrupted", "a confirmed merge result", "an interrupted landing run; the next run checks main")]})
            except (Held, ApiError, OSError):
                pass
        raise


def land_bound(api, env, config, directory, prior, sleep):
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

    if not api.live:
        main = current_main(api)
        if main != binding["base"]:
            raise Held("main-moved", f"main {binding['base'][:12]}, the commit the checks measured", f"main {main[:12]}")
        headline(f"Dry run: would merge #{binding['number']} onto main {main[:12]}.")
        summary([f"Would merge #{binding['number']} ({MERGE_METHOD}) with expected head {binding['head'][:12]} "
                 f"onto main {main[:12]}, expecting one parent {main[:12]} and tree {tree[:12]}."])
        return 0
    # The ruleset requires this status from GitHub Actions, so only this job can make the head mergeable.
    status(api, binding["head"], "success", f"{CLEARED} {binding['base'][:12]}")
    # Immediately before the merge: main must still be the measured commit.
    main = current_main(api)
    if main != binding["base"]:
        raise Held("main-moved", f"main {binding['base'][:12]}, the commit the checks measured", f"main {main[:12]}")
    body = {"merge_method": MERGE_METHOD, "sha": binding["head"],
            "commit_title": printable(f"{decision['title']} (#{binding['number']})", 250),
            "commit_message": (f"Measured on main {binding['base']}, head {binding['head']}, tree {tree}.\n"
                               f"Pull request #{binding['number']}.\n"
                               f"{TRAILER}, run {env.get('GITHUB_RUN_ID', '0') or '0'}.")}
    code, payload = api.write("PUT", f"pulls/{binding['number']}/merge", body)
    message = printable((payload or {}).get("message", ""), 160)
    if code == 409:
        raise Held("head-changed", f"head {binding['head'][:12]} at merge",
                   f"a newer head; GitHub refused the merge ({message}). The new head is measured from scratch")
    if code == 405:
        comment(api, binding["number"], f"Held: GitHub would not merge this pull request ({message}). "
                "If it conflicts with main, merge or rebase main into your branch and push.")
        raise Held("merge-refused", "GitHub to merge the pull request", f"HTTP 405: {message}", True)
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
    headline(f"Landed #{binding['number']} as {commit[:12]} on main (parent {binding['base'][:12]}, tree verified).")
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
    # Only the body is ours; the title is the pull request author's and is never parsed.
    lines = (record.get("message") or "").partition("\n\n")[2].splitlines()
    if not any(TRAILER_LINE.fullmatch(line) for line in lines) or LANDING_CONTEXT in read_statuses(api, main):
        return
    measured = next(filter(None, map(MEASURED_LINE.fullmatch, lines)), None)
    number = next(filter(None, map(NUMBER_LINE.fullmatch, lines)), None)
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
    if env.get("GITHUB_REPOSITORY") != REPO or env.get("GITHUB_REPOSITORY_ID") != str(REPO_ID):
        raise Failed("repository", "this repository", "another repository")
    if mode == "group":
        # GitHub starts this for the merge queue; it only ever writes one status, so it always runs live.
        if (env.get("GITHUB_EVENT_NAME") != "merge_group"
                or not (env.get("GITHUB_REF") or "").startswith("refs/heads/gh-readonly-queue/main/")):
            raise Failed("event", "a merge_group event for main's queue", "another event or ref")
        if api is None:
            api = Api(REPO, env.pop("BFME_LANDING_TOKEN", None), True)
        api.run_id = env.get("GITHUB_RUN_ID", "")
        return group(api, env)
    if env.get("GITHUB_REF") != "refs/heads/main":
        raise Failed("repository", "this repository's main branch", "another ref")
    live = env.get("BFME_LANDING_MODE") == "live"
    if api is None:
        api = Api(REPO, env.pop("BFME_LANDING_TOKEN", None), live)
    api.run_id = env.get("GITHUB_RUN_ID", "")
    api.run_attempt = env.get("GITHUB_RUN_ATTEMPT", "")
    config = dict(config or load_config())
    config.setdefault("auto_headers", env.get("BFME_AUTO_HEADERS") == "yes")
    config.setdefault("auto_admission", env.get("BFME_AUTO_ADMISSION") == "yes")
    if mode == "select":
        return select(api, env, config, directory, **kwargs)
    if mode == "land":
        return land(api, env, config, directory, **kwargs)
    raise Failed("mode", "select, land or group", printable(mode, 20))


def main():
    try:
        return run(sys.argv[1:], os.environ)
    except Failed as exc:
        print(f"Landing stopped. {exc.line()}", file=sys.stderr)
        headline(f"Stopped: {exc.code}. Expected {exc.expected}.")
        summary([f"Stopped. {exc.line()}"])
        return 1
    except Held as exc:
        print(f"Landing held. {exc.line()}", file=sys.stderr)
        headline(f"Held: {exc.code}. Expected {exc.expected}.")
        summary([f"Held. {exc.line()}"])
        return 0
    except (lr.Waiting, ApiError, ReadOnly) as exc:
        print(f"Landing stopped. {printable(exc, 300)}", file=sys.stderr)
        headline(f"Stopped: {printable(exc, 160)}")
        summary([f"Stopped. {printable(exc, 300)}"])
        return 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        detail = f"Expected readable landing inputs. Found a {type(exc).__name__} while reading them."
        print(f"Landing stopped. {detail}", file=sys.stderr)
        headline(f"Stopped: {detail}")
        summary([f"Stopped. {detail}"])
        return 1


if __name__ == "__main__":
    sys.exit(main())
