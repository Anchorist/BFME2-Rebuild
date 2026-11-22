"""Admit pull requests from forks to the compiler check by rule, one exact commit at a time.

Run by .github/workflows/admission.yml from main's code on a GitHub-hosted runner. It reads pull request
metadata through the API and never checks out or runs pull request content.

For a fork pull request whose author is not an organisation member (members are measured already):
  - any change under .github/        -> never admitted here; a maintainer merges it by hand
  - anything outside src/, or under a maintainer path, or too many files
                                     -> waits for a maintainer (label boat-ok), as before
  - source files only                -> one reservation in the daily ledger (ledger.py), then
                                        "BFME II / Admission" success on that exact commit, then the existing
                                        bfme-remeasure dispatch; the compiler check claims the reservation once
Every new push is judged again for its new commit. Over the daily limit, or when the ledger cannot be used, the
commit is held ("daily limit, retried automatically") and an hourly run retries the oldest first.
When the compiler check that used a reservation finished without measuring anything (a machine fault, not a
verdict), the hourly run frees that reservation for another check, at most twice for one commit on one main.
After main moves, GitHub keeps the pull request's merge preview on the old main. The hourly run and a landing
request then take the merged tree from the protected source-rules receipt for exactly this commit on the current
main; when there is none yet, they ask the source rules workflow for one (bfme-source-refresh, at most once an hour
for one commit on one main), and that workflow asks admission to decide again as soon as it has published.

  admit.py event     decide for the pull request in this pull_request_target event
  admit.py retry     decide again for open fork pull requests that are held or undecided (hourly)
  admit.py request   decide for one pull request named by a bfme-admit-request dispatch (the landing workflow
                     sends it before re-measuring a pull request admitted by rule on an older main)

Switched on by the repository variable BFME_AUTO_ADMISSION=yes; otherwise it reports what it would do and writes
nothing. Limits come from BFME_ADMISSION_DAILY_TOTAL and BFME_ADMISSION_DAILY_PER_AUTHOR; when they are missing or
invalid, nothing is admitted (held, retried automatically).
"""
import datetime
import re
import json
import os
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parent / "landing"))
sys.path.insert(2, str(HERE.parent / "managed-check"))

from api import Api, ApiError, ReadOnly, printable  # noqa: E402
from common import HEX40, REPO, REPO_ID, read  # noqa: E402
import ledger  # noqa: E402
import source_approval  # noqa: E402
import subprocess
import zipfile

CONTEXT = "BFME II / Admission"
BOT_ID = 41898282                       # github-actions[bot], the only writer of an admission
ADMITTED = "Admitted by rule: source files only"
ADMITTED_TRUSTED = "Admitted by rule: trusted source files only"
ADMITTED_WIDE = "Admitted by rule: header change, wide check"
DAILY_LIMIT = "Held: daily limit, retried automatically"
SOURCE_HOLD = "Held: current source rules have not passed, retried automatically"
UNMEASURED = "Held: the compiler check failed to run three times; a maintainer will look"
COMPILER_WORKFLOW = ".github/workflows/managed-pr.yml"
RUN_NUMBER = re.compile(r"[1-9][0-9]{0,19}")
SETTLE_SECONDS = 120                    # a finished run's last status is visible well within this
STATUS_PAGES = 10                       # more statuses than this on one commit: treat it as measured
UNMEASURED_ENDINGS = {"failure", "cancelled", "timed_out", "startup_failure"}
REMEASURE_EVENT = "bfme-remeasure"
REFRESH_EVENT = "bfme-source-refresh"     # .github/workflows/rules.yml: source rules only, no compiler machine
REFRESH_SECONDS = 3600                    # at most one source refresh for one commit on one main per hour
SOURCE_CONTEXT = "BFME II / source rules"
# Written by tools/gates/workflow.py on the source rules status when only the author can fix this commit on that main.
SOURCE_CONFLICT = "Conflicts with main: merge or rebase main into your branch and push"
SOURCE_HISTORY = "No shared history with main: rebase your branch on main and push"
NEVER_PATHS = (".github/",)
MAINTAINER_PATHS = ("include/", "ci/", "tools/", "config/", "expected/", "baseline/")
MEMBER_ROLES = {"OWNER", "MEMBER", "COLLABORATOR"}


class Stop(Exception):
    def __init__(self, expected, found):
        super().__init__(expected)
        self.expected, self.found = expected, found

    def line(self):
        return f"Expected {self.expected}. Found {self.found}."


def load_config(path=HERE / "admission.json"):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if type(data.get("max_paths")) is not int or data["max_paths"] < 1 or data.get("source_prefix") != "src/":
        raise Stop("admission.json with max_paths and source_prefix src/", "something else")
    return data


def limits(env, kind="narrow"):
    """The daily limits from repository variables, validated like the compiler check's own reader; None if invalid.

    narrow: BFME_ADMISSION_DAILY_TOTAL / _PER_AUTHOR; wide: BFME_ADMISSION_WIDE_DAILY_TOTAL / _PER_AUTHOR.
    """
    prefix = "BFME_ADMISSION_DAILY_" if kind == "narrow" else "BFME_ADMISSION_WIDE_DAILY_"
    values = [env.get(prefix + key, "") for key in ("TOTAL", "PER_AUTHOR")]
    if not all(re.fullmatch(r"[1-9][0-9]{0,4}", value) for value in values):
        return None
    total, per_author = int(values[0]), int(values[1])
    if not 0 < per_author <= total <= 5040:
        return None
    return {"daily_total": total, "daily_per_author": per_author}


def admitted_text(base, kind="narrow"):
    texts = {"narrow": ADMITTED, "trusted-narrow": ADMITTED_TRUSTED, "wide": ADMITTED_WIDE}
    return f"{texts[kind]} (main {base[:12]})"


def changed_files(api, number):
    names = []
    for page in range(1, 31):
        entries = api.call(f"pulls/{number}/files?per_page=100&page={page}")
        for item in entries:
            names.append(item.get("filename", ""))
            if item.get("previous_filename"):
                names.append(item["previous_filename"])
        if len(entries) < 100:
            return names
    return names + ["(more than 3000 files)"]


BOAT_CONTEXT = "BFME II / Boat"
REFUSED_MAIN_RE = re.compile(r"^BFME II check refused this patch \(main ([0-9a-f]{12})\)\Z")
RELEVANT_MAIN_PREFIXES = ("include/", "config/", "expected/", "baseline/", "ci/managed-check/", "ci/managed-nt2/")


def prior_code_refusal(api, head, base):
    """The 12-char main SHA of a prior measured Boat code refusal for this exact head, or None."""
    latest = None
    for page in range(1, STATUS_PAGES + 1):
        entries = api.call(f"commits/{head}/statuses?per_page=100&page={page}")
        if not isinstance(entries, list):
            return None
        for item in entries:
            if (isinstance(item, dict) and item.get("context") == BOAT_CONTEXT
                    and (item.get("creator") or {}).get("id") == BOT_ID):
                if latest is None or item.get("id", 0) > latest.get("id", 0):
                    latest = item
        if len(entries) < 100:
            break
    if not latest or latest.get("state") != "failure":
        return None
    match = REFUSED_MAIN_RE.fullmatch(latest.get("description") or "")
    if not match or match.group(1) == base[:12]:
        return None
    return match.group(1)


def dormant_refusal(api, head, base, pr_files):
    """Return the prior main prefix when a refused head cannot be fixed by unrelated main moves, else None."""
    try:
        old12 = prior_code_refusal(api, head, base)
        if not old12:
            return None
        comp = api.call(f"compare/{old12}...{base}")
    except (ApiError, ValueError, TypeError, KeyError, AttributeError):
        return None
    comp_status = comp.get("status") if isinstance(comp, dict) else None
    if not isinstance(comp_status, str) or comp_status not in {"ahead", "identical"}:
        return None
    changed = comp.get("files")
    if not isinstance(changed, list) or len(changed) >= 300:
        return None
    watched = set(pr_files)
    prefixes = RELEVANT_MAIN_PREFIXES + (("src/",) if any(p.startswith("include/") for p in pr_files) else ())
    for item in changed:
        if not isinstance(item, dict):
            return None
        fname = item.get("filename")
        if not isinstance(fname, str) or not fname:
            return None
        prev = item.get("previous_filename")
        if prev is not None and (not isinstance(prev, str) or not prev):
            return None
        for name in (fname, prev):
            if name and (name in watched or name.startswith(prefixes)):
                return None
    return old12


def measured_on(api, head, base):
    """True when the latest BFME II / Boat status on this head, written by GitHub Actions, is final for this main."""
    entries = api.call(f"commits/{head}/statuses?per_page=100&page=1")
    found = [item for item in entries if item.get("context") == BOAT_CONTEXT
             and (item.get("creator") or {}).get("id") == BOT_ID]
    if not found:
        return False
    latest = max(found, key=lambda item: item["id"])
    # Only an explicitly measured outcome counts; an infrastructure error or a bare status is not a measurement.
    text = latest.get("description") or ""
    measured = {"success": "BFME II comparison passed", "failure": "BFME II check refused this patch"}
    prefix = measured.get(latest.get("state"))
    return prefix is not None and text.startswith(prefix) and text.endswith(f"(main {base[:12]})")


def verdict_recorded(api, head, base):
    """True unless it is certain that no compiler verdict for this main was ever written on this head.

    Reads every status page, not the newest entries only: a later pending or error status, or a flood of other
    statuses, must not hide an earlier verdict. Any measured status by the Actions bot for this main counts. If the
    pages cannot all be read, the answer is True (treat as measured).
    """
    measured = {"success": "BFME II comparison passed", "failure": "BFME II check refused this patch"}
    suffix = f"(main {base[:12]})"
    for page in range(1, STATUS_PAGES + 1):
        entries = api.call(f"commits/{head}/statuses?per_page=100&page={page}")
        if not isinstance(entries, list):
            return True
        for item in entries:
            if not isinstance(item, dict) or item.get("context") != BOAT_CONTEXT \
                    or (item.get("creator") or {}).get("id") != BOT_ID:
                continue
            prefix = measured.get(item.get("state"))
            text = item.get("description") or ""
            if prefix is not None and text.startswith(prefix) and text.endswith(suffix):
                return True
        if len(entries) < 100:
            return False
    return True


def unmeasured_claim(api, number, head, base, clock=None):
    """The claim on this reservation when the run that made it is finished and measured nothing; else None.

    A reservation is used once. If the compiler check that used it stopped on a machine fault, no verdict was
    written and nothing else would ever measure this commit on this main. This reads the ledger, the claiming run
    and every status page; any doubt (something unreadable, not this repository's compiler check started by the
    admission dispatch on this main, another attempt, still running, not a failed ending, finished moments ago, a
    verdict present) returns None and the reservation stays used.
    """
    try:
        item = ledger.find(api, number, head, base)
        claimed = (item or {}).get("claimed_by")
        if not isinstance(claimed, dict) or set(claimed) != {"run", "attempt"}:
            return None
        run_id, attempt = claimed["run"], claimed["attempt"]
        if not (isinstance(run_id, str) and RUN_NUMBER.fullmatch(run_id)
                and isinstance(attempt, str) and RUN_NUMBER.fullmatch(attempt)):
            return None
        run = api.call(f"actions/runs/{run_id}")
        if not isinstance(run, dict) or str(run.get("id")) != run_id or str(run.get("run_attempt")) != attempt \
                or run.get("path") != COMPILER_WORKFLOW or (run.get("repository") or {}).get("id") != REPO_ID \
                or run.get("event") != "repository_dispatch" or run.get("head_sha") != base \
                or run.get("status") != "completed" or run.get("conclusion") not in UNMEASURED_ENDINGS:
            return None
        finished = datetime.datetime.strptime(run.get("updated_at") or "", "%Y-%m-%dT%H:%M:%SZ")
        now = clock() if clock else datetime.datetime.now(datetime.timezone.utc)
        if now.tzinfo is not None:
            now = now.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        if (now - finished).total_seconds() < SETTLE_SECONDS:
            return None
        # The run's last status is written before the run completes, so read the verdict only now.
        if verdict_recorded(api, head, base):
            return None
    except (ApiError, ledger.LedgerError, ValueError, TypeError, AttributeError):
        return None
    return claimed


def latest_status(api, sha):
    entries = api.call(f"commits/{sha}/statuses?per_page=100&page=1")
    found = [item for item in entries if item.get("context") == CONTEXT
             and (item.get("creator") or {}).get("id") == BOT_ID]
    return max(found, key=lambda item: item["id"]) if found else None


def trusted_source(pr):
    repo = (pr.get("head") or {}).get("repo") or {}
    return repo.get("id") == REPO_ID or pr.get("author_association") in MEMBER_ROLES


def decide(pr, files, config, auto_headers=False):
    """Return (verdict, state, description). verdict: skip | never | wait | draft | admit | admit-wide.

    With auto_headers (BFME_AUTO_HEADERS=yes), changes under include/ (with or without src/) are admitted to the
    wide check under the wide budget; the header rules (H1-H8) then decide whether it may land.
    """
    head_repo = (pr.get("head") or {}).get("repo") or {}
    if pr.get("state") != "open" or (pr.get("base") or {}).get("ref") != "main" \
            or ((pr.get("base") or {}).get("repo") or {}).get("id") != REPO_ID:
        return "skip", None, None
    if type(head_repo.get("id")) is not int or head_repo["id"] <= 0:
        return "never", "failure", "The source repository was deleted; open a new pull request from a fork"
    if any(name.startswith(NEVER_PATHS) for name in files):
        return "never", "failure", "Changes under .github/ are merged by a maintainer by hand"
    allowed = (config["source_prefix"], "include/") if auto_headers else (config["source_prefix"],)
    waiting = tuple(path for path in MAINTAINER_PATHS if not (auto_headers and path == "include/"))
    outside = sorted({name.split("/", 1)[0] + "/" for name in files
                      if not name.startswith(allowed) or name.startswith(waiting)})
    if outside:
        return "wait", "pending", f"Waiting for a maintainer: this changes {', '.join(outside)[:60]}"
    if len(files) > config["max_paths"]:
        return "wait", "pending", f"Waiting for a maintainer: more than {config['max_paths']} files"
    if pr.get("draft") is not False:
        return "draft", "pending", "Waiting: the pull request is a draft"
    if any(name.startswith("include/") for name in files):
        if trusted_source(pr):
            return "wait", "pending", "Held: trusted header admission still requires the header rules"
        return "admit-wide", "success", ADMITTED_WIDE
    if not files:
        return "wait", "pending", "Waiting: no source changes to compare"
    if len(set(files)) > 8:
        return "wait", "pending", "Held: source-only admission covers at most eight paths"
    if trusted_source(pr):
        return "admit-trusted", "success", ADMITTED_TRUSTED
    return "admit", "success", ADMITTED


PREVIEW_WAIT = "Held: waiting for GitHub's merge preview on main, retried automatically"
CONFLICT = "This conflicts with main: merge or rebase main into your branch and push"
HISTORY = "This branch shares no history with main: rebase it on main and push"
STALE = "stale"


def refresh_text(base):
    return f"Held: checking the source rules on main {base[:12]}, retried automatically"


def merge_preview(api, number, head, base, sleep=time.sleep, tries=6):
    """The tree of GitHub's merge of exactly `head` onto exactly `base`, 'conflict', 'stale', or None if not ready.

    Reading the pull request asks GitHub to (re)compute its merge preview commit; its parents must be exactly
    [base, head]. 'stale' is a preview of this head on another main: GitHub does not recompute it when main moves,
    so waiting for it would never end. Nothing from the pull request is checked out or run.
    """
    for attempt in range(tries):
        pr = api.call(f"pulls/{number}")
        if (pr.get("head") or {}).get("sha") != head:
            return None
        if pr.get("mergeable") is False:
            return "conflict"
        sha = pr.get("merge_commit_sha") or ""
        if HEX40.fullmatch(sha):
            commit = api.call(f"git/commits/{sha}")
            parents = [item.get("sha") for item in commit.get("parents") or ()]
            tree = (commit.get("tree") or {}).get("sha") or ""
            if parents == [base, head] and HEX40.fullmatch(tree):
                return tree
            if len(parents) == 2 and parents[1] == head and parents[0] != base and HEX40.fullmatch(parents[0] or ""):
                return STALE
        if attempt + 1 < tries:
            sleep(5)
    return None


def source_tree(api, number, head, base):
    """The merged tree from the protected source-rules receipt for exactly this pull request, head, main and
    current policy. The source rules composed it themselves (unique ancestor, three-way merge); the compiler check
    composes it again and refuses a different tree before any machine starts."""
    sys.path.append(str(source_approval.TOOLS))
    from gate import policy_digest
    policy = policy_digest(source_approval.TOOLS / "config.json")
    value = source_approval.receipt_for(api, number, head, base, policy,
                                        lambda artifact: source_approval.download(artifact, api._token))
    return value["tree"]


def source_conflict(api, head, base):
    """'conflict' or 'history' when the protected source rules wrote, for this main, that only the author can fix
    this commit (it conflicts with main, or shares no history with it); else None."""
    named = {f"{SOURCE_CONFLICT} (main {base[:12]})": "conflict", f"{SOURCE_HISTORY} (main {base[:12]})": "history"}
    for page in range(1, 5):
        entries = api.call(f"commits/{head}/statuses?per_page=100&page={page}")
        found = [item for item in entries if isinstance(item, dict) and item.get("context") == SOURCE_CONTEXT
                 and (item.get("creator") or {}).get("id") == BOT_ID]
        if found:
            latest = max(found, key=lambda item: item["id"])
            return named.get(latest.get("description")) if latest.get("state") == "error" else None
        if len(entries) < 100:
            return None
    return None


def refresh_recent(api, head, base, clock=None):
    """True when this commit already has a refresh marker for this main from the Actions bot written within the hour,
    on any status page, whatever came after it (an event's status, other writers, more than 100 newer statuses).
    True also when the pages cannot all be read: no second request on doubt."""
    marker = refresh_text(base)
    for page in range(1, STATUS_PAGES + 1):
        entries = api.call(f"commits/{head}/statuses?per_page=100&page={page}")
        if not isinstance(entries, list):
            return True
        for item in entries:
            if (isinstance(item, dict) and item.get("context") == CONTEXT
                    and (item.get("creator") or {}).get("id") == BOT_ID and item.get("state") == "pending"
                    and item.get("description") == marker and recent(item, clock)):
                return True
        if len(entries) < 100:
            return False
    return True


def recent(status, clock=None, seconds=REFRESH_SECONDS):
    """True unless the status is certainly older than `seconds` (an unreadable time counts as recent)."""
    try:
        written = datetime.datetime.strptime(status.get("created_at") or "", "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return True
    now = clock() if clock else datetime.datetime.now(datetime.timezone.utc)
    if now.tzinfo is not None:
        now = now.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return (now - written).total_seconds() < seconds


def post(api, head, state, description):
    if not api.live:
        print(f"Would set {CONTEXT} on {head[:12]}: {state}, {description}")
        return
    body = {"state": state, "context": CONTEXT, "description": printable(description, 140)}
    run = getattr(api, "run_id", "")
    if run.isdigit():
        body["target_url"] = f"https://github.com/{REPO}/actions/runs/{run}"
    code, _ = api.write("POST", f"statuses/{head}", body)
    if code != 201:
        raise Stop(f"HTTP 201 for the {CONTEXT} status", f"HTTP {code}")


def check_source(api, number, head, base, tree):
    sys.path.append(str(source_approval.TOOLS))
    from gate import policy_digest
    policy = policy_digest(source_approval.TOOLS / "config.json")
    return source_approval.require_source(api, number, head, base, tree, policy,
                                         lambda artifact: source_approval.download(artifact, api._token))


def still_current(api, number, pr, head, base):
    """The final freshness predicate: same open, ready pull request at the same head, same admission type, same main."""
    latest = api.call(f"pulls/{number}")
    return not ((latest.get("head") or {}).get("sha") != head or latest.get("state") != "open"
                or (latest.get("base") or {}).get("ref") != "main" or latest.get("draft") is not False
                or ((latest.get("base") or {}).get("repo") or {}).get("id") != REPO_ID
                or trusted_source(latest) != trusted_source(pr)
                or api.call("git/ref/heads/main")["object"]["sha"] != base)


def on_moved_main(api, number, pr, head, base, prior, clock, find_tree, attempts=1, sleep=time.sleep):
    """A stale preview: the tree from the exact source receipt, 'conflict', or a line saying why nothing was reserved.

    With no receipt for this main yet, ask the source rules workflow for one, at most once an hour for this commit
    on this main (the Admission status written here records when). That workflow publishes the source statuses and
    the receipt with no compiler machine, then asks admission to decide again for this pull request.
    """
    for attempt in range(attempts):
        named = source_conflict(api, head, base)
        if named == "conflict":
            return "conflict"
        if named == "history":
            if not (prior and prior.get("state") == "pending" and prior.get("description") == HISTORY):
                post(api, head, "pending", HISTORY)
            return f"#{number}: shares no history with main; nothing reserved"
        try:
            return find_tree(api, number, head, base)
        except source_approval.Refused:
            return f"#{number}: protected source rules refused this head; nothing reserved"
        except (ApiError, OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError,
                zipfile.BadZipFile):
            if attempt + 1 < attempts:
                sleep(5)
    text = refresh_text(base)
    try:
        waiting = refresh_recent(api, head, base, clock)
    except (ApiError, ValueError, TypeError, AttributeError):
        waiting = True
    if waiting:
        return f"#{number}: waiting for the source rules on main {base[:12]}; nothing reserved, retried hourly"
    if not still_current(api, number, pr, head, base):
        return f"#{number}: protected main, head or admission type moved; nothing reserved"
    post(api, head, "pending", text)
    code, _ = api.write("POST", "dispatches", {"event_type": REFRESH_EVENT,
                                               "client_payload": {"number": number, "head": head, "base": base}})
    if code != 204:
        return f"#{number}: the source rules could not be requested (HTTP {code}); retried hourly"
    return f"#{number}: source rules requested on main {base[:12]}; admission decides again when they publish"


def handle(api, number, config, base, budget, clock=None, sleep=time.sleep,
           auto_headers=False, wide_budget=None, *, source_proof=None,
           source_attempts=1, owner_origin=False, expected_head=None, refresh=False, find_tree=None,
           refresh_attempts=1):
    """Decide for one pull request against main commit `base`. The ledger reservation is the authority.

    refresh: when GitHub's preview is of another main, use the protected source receipt (and request one) instead
    of waiting for a preview GitHub never recomputes. The hourly run and the landing request use it."""
    pr = api.call(f"pulls/{number}")
    head = (pr.get("head") or {}).get("sha", "")
    if not HEX40.fullmatch(head):
        raise Stop("an exact pull request head", "missing metadata")
    if expected_head is not None and head != expected_head:
        return f"#{number}: a newer head has its own event; nothing reserved"
    files = changed_files(api, number)
    verdict, state, description = decide(pr, files, config, auto_headers)
    if verdict == "skip":
        return f"#{number}: no eligible pull request targeting main"
    prior = latest_status(api, head)
    kind = {"admit-wide": "wide", "admit-trusted": "trusted-narrow"}.get(verdict, "narrow")
    if kind == "wide":
        budget = wide_budget
    if verdict not in ("admit", "admit-wide", "admit-trusted"):
        if not (prior and prior.get("state") == state and prior.get("description") == description):
            post(api, head, state, description)
        return f"#{number}: {description}"
    if owner_origin and trusted_source(pr):
        return f"#{number}: owner-started protected direct comparison"
    if kind == "trusted-narrow" and measured_on(api, head, base):
        # A direct run (the owner's) already gave this exact head a final compiler verdict on this main, so a
        # trusted pull request needs no second compare. A pending verdict is not enough: a direct run whose
        # compiler jobs were refused leaves pending behind, and that head must still be admitted.
        return f"#{number}: commit {head[:12]} already has a compiler verdict on main {base[:12]}"
    if refresh:
        prior_main = dormant_refusal(api, head, base, files)
        if prior_main:
            return (f"#{number}: commit {head[:12]} was refused on main {prior_main} and no relevant files "
                    f"changed on main {base[:12]}; waiting for author push")
    if not api.live:
        return f"#{number}: would check source receipts and reserve {kind} commit {head[:12]} on main {base[:12]}"
    if kind != "trusted-narrow" and budget is None:
        post(api, head, "pending", DAILY_LIMIT)
        return f"#{number}: held, the daily limits are not configured"
    tree = merge_preview(api, number, head, base, sleep)
    if tree in (STALE, "conflict", None) and refresh:
        tree = on_moved_main(api, number, pr, head, base, prior, clock, find_tree or source_tree,
                             attempts=refresh_attempts, sleep=sleep)
        if not (tree == "conflict" or HEX40.fullmatch(tree)):
            return tree
    elif tree == STALE:
        tree = None
    if tree == "conflict":
        if not (prior and prior.get("description") == CONFLICT):
            post(api, head, "pending", CONFLICT)
        return f"#{number}: conflicts with main; nothing reserved"
    if tree is None:
        post(api, head, "pending", PREVIEW_WAIT)
        return f"#{number}: GitHub's merge preview on main {base[:12]} is not ready; nothing reserved, retried hourly"
    moved = f"#{number}: protected main, head or admission type moved; nothing reserved"
    for wait in range(source_attempts):
        try:
            (check_source if source_proof is None else source_proof)(api, number, head, base, tree)
            break
        except source_approval.Refused:
            return f"#{number}: protected source rules refused this head; nothing reserved"
        except (ApiError, OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError,
                zipfile.BadZipFile):
            # Stop waiting at once when the pull request or main moved: a newer event or run decides then.
            if not still_current(api, number, pr, head, base):
                return moved
            if wait + 1 < source_attempts:
                sleep(5)
    else:
        # Only a still-current commit may be marked held, and only if its latest status says something else.
        if not still_current(api, number, pr, head, base):
            return moved
        proven = False
        if refresh:
            # No receipt for GitHub's tree on this main. The hourly run and the landing request never just wait:
            # the source rules' own receipt (with their tree) is used, or requested once an hour, exactly as for a
            # stale preview. The pull request event keeps waiting for its own source run.
            routed = on_moved_main(api, number, pr, head, base, prior, clock, find_tree or source_tree,
                                   attempts=refresh_attempts, sleep=sleep)
            if routed == "conflict":
                if not (prior and prior.get("description") == CONFLICT):
                    post(api, head, "pending", CONFLICT)
                return f"#{number}: conflicts with main; nothing reserved"
            if not HEX40.fullmatch(routed):
                return routed
            try:
                (check_source if source_proof is None else source_proof)(api, number, head, base, routed)
                tree, proven = routed, True
            except source_approval.Refused:
                return f"#{number}: protected source rules refused this head; nothing reserved"
            except (ApiError, OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError,
                    zipfile.BadZipFile):
                pass
        if not proven:
            latest_admission = latest_status(api, head)
            if not (latest_admission and latest_admission.get("state") == "pending"
                    and latest_admission.get("description") == SOURCE_HOLD):
                post(api, head, "pending", SOURCE_HOLD)
            return f"#{number}: {SOURCE_HOLD}; nothing reserved"
    if not still_current(api, number, pr, head, base):
        return moved
    try:
        result = ledger.reserve(api, budget, (pr.get("user") or {}).get("id"), number, head, base,
                                getattr(api, "run_id", ""), getattr(api, "run_attempt", ""), clock, tree, kind)
    except (ledger.LedgerError, ApiError) as exc:
        post(api, head, "pending", DAILY_LIMIT)
        return f"#{number}: held, the daily ledger could not be used ({printable(exc, 120)})"
    if result == "over-budget":
        post(api, head, "pending", DAILY_LIMIT)
        return f"#{number}: held, daily limit reached"
    if result == "binding-mismatch":
        return f"#{number}: prior reservation has another tree, kind or author; nothing dispatched"
    text = admitted_text(base, kind)
    if result == "already":
        # The ledger, not the status, decides: a claimed reservation was measured; an unclaimed one was reserved
        # by a run that may have stopped before its dispatch, so it is re-issued to this run and dispatched again
        # (the compiler check's single-use claim fences any duplicate delivery).
        try:
            issued = ledger.refresh_issuer(api, number, head, base, getattr(api, "run_id", ""),
                                           getattr(api, "run_attempt", ""))
        except (ledger.LedgerError, ApiError) as exc:
            post(api, head, "pending", DAILY_LIMIT)
            return f"#{number}: held, the daily ledger could not be used ({printable(exc, 120)})"
        if issued == "claimed":
            claimed = unmeasured_claim(api, number, head, base, clock)
            if claimed is None:
                if not (prior and prior.get("state") == "success" and prior.get("description") == text):
                    post(api, head, "success", text)
                return f"#{number}: exact reservation was already used on main {base[:12]}"
            try:
                again = ledger.reissue_unmeasured(api, budget, number, head, base, claimed, getattr(api, "run_id", ""),
                                                  getattr(api, "run_attempt", ""), clock)
            except (ledger.LedgerError, ApiError) as exc:
                post(api, head, "pending", DAILY_LIMIT)
                return f"#{number}: held, the daily ledger could not be used ({printable(exc, 120)})"
            if again == "over-budget":
                post(api, head, "pending", DAILY_LIMIT)
                return f"#{number}: held, daily limit reached (retry after an unmeasured run)"
            if again == "exhausted":
                if not (prior and prior.get("state") == "pending" and prior.get("description") == UNMEASURED):
                    post(api, head, "pending", UNMEASURED)
                return f"#{number}: the compiler check ended unmeasured three times; nothing more is dispatched"
            if again != "reissued":
                return f"#{number}: the reservation changed while it was read; retried automatically"
            issued = "refreshed"
        if issued != "refreshed":
            return f"#{number}: prior reservation no longer exists; retried automatically"
    # The reservation is committed before the status and the dispatch, so the compiler check can always find it;
    # a repeated dispatch for the same reservation is refused there (single-use claim).
    post(api, head, "success", text)
    code, _ = api.write("POST", "dispatches", {"event_type": REMEASURE_EVENT,
                                               "client_payload": {"number": number, "head": head, "base": base}})
    if code != 204:
        post(api, head, "pending", "Held: the compiler check could not be started, retried automatically")
        return f"#{number}: admitted, but the dispatch got HTTP {code}; retried hourly"
    return f"#{number}: commit {head[:12]} admitted by rule; compiler check requested on main {base[:12]}"


def retry_candidates(api):
    numbers = []
    for page in range(1, 4):
        entries = api.call(f"pulls?state=open&base=main&sort=created&direction=asc&per_page=100&page={page}")
        for pr in entries:
            if pr.get("draft") is False:
                numbers.append(pr["number"])
        if len(entries) < 100:
            break
    return numbers


def run(argv, env, api=None, config=None, clock=None):
    mode = argv[0] if argv else ""
    if env.get("GITHUB_REPOSITORY") != REPO or env.get("GITHUB_REPOSITORY_ID") != str(REPO_ID) \
            or env.get("GITHUB_REF") != "refs/heads/main":
        raise Stop("this repository's main branch", "another repository or ref")
    live = env.get("BFME_AUTO_ADMISSION") == "yes"
    if api is None:
        api = Api(REPO, env.pop("BFME_ADMISSION_TOKEN", None), live)
    api.run_id = env.get("GITHUB_RUN_ID", "")
    api.run_attempt = env.get("GITHUB_RUN_ATTEMPT", "")
    config = config or load_config()
    budget = limits(env)
    main = api.call("git/ref/heads/main")["object"]["sha"]
    if main != env.get("GITHUB_SHA"):
        print(f"::notice title=BFME II admission::Superseded: main moved to {main[:12]}; a newer run decides.")
        return 0
    expected_head = None
    if mode == "event":
        if env.get("GITHUB_EVENT_NAME") != "pull_request_target":
            raise Stop("a pull_request_target event", printable(env.get("GITHUB_EVENT_NAME"), 40))
        event_pr = read(env["GITHUB_EVENT_PATH"], 2 * 1024**2)["pull_request"]
        expected_head = event_pr["head"]["sha"]
        if not HEX40.fullmatch(expected_head):
            raise Stop("a protected event with the exact PR head", "an invalid SHA")
        numbers = [event_pr["number"]]
    elif mode in {"retry", "request"}:
        if mode == "request":
            payload = read(env["GITHUB_EVENT_PATH"], 2 * 1024**2).get("client_payload") or {}
            if set(payload) != {"number"} or type(payload["number"]) is not int or not 0 < payload["number"] < 10**9:
                raise Stop("a bfme-admit-request payload with one pull request number", "something else")
            numbers = [payload["number"]]
        else:
            numbers = retry_candidates(api)
    else:
        raise Stop("event, retry or request", printable(mode, 20))
    auto_headers = env.get("BFME_AUTO_HEADERS") == "yes"
    wide_budget = limits(env, "wide")
    owner_origin = mode == "event" and env.get("GITHUB_ACTOR_ID") == "1760627" \
        and env.get("GITHUB_TRIGGERING_ACTOR") == "Ancalgonn"
    lines = [handle(api, number, config, main, budget, clock, auto_headers=auto_headers,
                    wide_budget=wide_budget, source_attempts=25 if mode == "event" else 1,
                    owner_origin=owner_origin, expected_head=expected_head, refresh=mode != "event",
                    refresh_attempts=12 if mode == "request" else 1)
             for number in numbers]
    text = f"Admission ({'live' if live else 'dry run'}): " + ("; ".join(lines) if lines else "no fork pull requests")
    print(f"::notice title=BFME II admission::{printable(text, 200).replace('::', ': ')}")
    path = env.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a") as stream:
            stream.write("\n".join(["### BFME II admission", ""] + [f"- {line}" for line in lines]) + "\n")
    return 0


def main():
    try:
        return run(sys.argv[1:], os.environ)
    except Stop as exc:
        print(f"Admission stopped. {exc.line()}", file=sys.stderr)
        return 1
    except (ApiError, ReadOnly, ledger.LedgerError) as exc:
        print(f"Admission stopped. {printable(exc, 300)}", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Admission stopped. Expected readable inputs. Found a {type(exc).__name__}.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
