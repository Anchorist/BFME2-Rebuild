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

  admit.py event     decide for the pull request in this pull_request_target event
  admit.py retry     decide again for open fork pull requests that are held or undecided (hourly)
  admit.py request   decide for one pull request named by a bfme-admit-request dispatch (the landing workflow
                     sends it before re-measuring a pull request admitted by rule on an older main)

Switched on by the repository variable BFME_AUTO_ADMISSION=yes; otherwise it reports what it would do and writes
nothing. Limits come from BFME_ADMISSION_DAILY_TOTAL and BFME_ADMISSION_DAILY_PER_AUTHOR; when they are missing or
invalid, nothing is admitted (held, retried automatically).
"""
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
REMEASURE_EVENT = "bfme-remeasure"
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


def latest_status(api, sha):
    entries = api.call(f"commits/{sha}/statuses?per_page=100&page=1")
    found = [item for item in entries if item.get("context") == CONTEXT]
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


def merge_preview(api, number, head, base, sleep=time.sleep, tries=6):
    """The tree of GitHub's merge of exactly `head` onto exactly `base`, or 'conflict', or None if not ready.

    Reading the pull request asks GitHub to (re)compute its merge preview commit; its parents must be exactly
    [base, head]. Nothing from the pull request is checked out or run.
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
        if attempt + 1 < tries:
            sleep(5)
    return None


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


def handle(api, number, config, base, budget, clock=None, sleep=time.sleep,
           auto_headers=False, wide_budget=None, *, source_proof=None,
           source_attempts=1, owner_origin=False, expected_head=None):
    """Decide for one pull request against main commit `base`. The ledger reservation is the authority."""
    pr = api.call(f"pulls/{number}")
    head = (pr.get("head") or {}).get("sha", "")
    if not HEX40.fullmatch(head):
        raise Stop("an exact pull request head", "missing metadata")
    if expected_head is not None and head != expected_head:
        return f"#{number}: a newer head has its own event; nothing reserved"
    verdict, state, description = decide(pr, changed_files(api, number), config, auto_headers)
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
    if not api.live:
        return f"#{number}: would check source receipts and reserve {kind} commit {head[:12]} on main {base[:12]}"
    if kind != "trusted-narrow" and budget is None:
        post(api, head, "pending", DAILY_LIMIT)
        return f"#{number}: held, the daily limits are not configured"
    tree = merge_preview(api, number, head, base, sleep)
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
            if not (prior and prior.get("state") == "success" and prior.get("description") == text):
                post(api, head, "success", text)
            return f"#{number}: exact reservation was already used on main {base[:12]}"
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
                    owner_origin=owner_origin, expected_head=expected_head)
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
