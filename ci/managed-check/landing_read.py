"""Read-only landing rehearsal using three authenticated, exact Actions receipts."""
import os
from pathlib import Path
import re
import sys

from common import CONTEXT, HEX40, HEX64, REPO, REPO_ID, policy, read, write
from github_io import GitHub, Superseded
from inline_status import CONTEXT as INLINE
from quality_format import quoted

TOOLS = Path(__file__).resolve().parents[2] / "tools/gates"
sys.path.append(str(TOOLS))

RULES = "BFME II / source rules"
BUILDS = (CONTEXT, INLINE)
FLOW = {CONTEXT: ".github/workflows/managed-pr.yml", INLINE: ".github/workflows/managed-pr.yml",
        RULES: ".github/workflows/rules.yml"}
NUMBER = re.compile(r"[1-9][0-9]{0,19}\Z")
URL = re.compile(rf"https://github\.com/{re.escape(REPO)}/actions/runs/([1-9][0-9]{{0,19}})\Z")
BOT_ID = 41898282  # GitHub Actions bot account

class Waiting(ValueError):
    pass


def pull(api, number, base):
    pr = api.call(f"pulls/{number}")
    if pr.get("base", {}).get("ref", "").startswith("corpus/base-") or pr.get("head", {}).get("ref", "").startswith("corpus/case-"):
        raise Waiting("Expected an ordinary pull request targeting main. Found a historical corpus fixture with no landing path.")
    observed = api.call("git/ref/heads/main")["object"]["sha"]
    if observed != base:
        raise Waiting(f"Expected main {base[:12]}. Found a different main. Request fresh checks.")
    if (pr.get("number") != number or pr["base"]["repo"]["id"] != REPO_ID
            or pr["base"]["ref"] != "main" or pr["state"] != "open" or pr.get("draft") is not False):
        raise Waiting("Expected an open, review-ready pull request targeting this main. Found an ineligible pull request.")
    head = pr["head"]["sha"]
    if not HEX40.fullmatch(head):
        raise Waiting("Expected the exact pull-request head SHA. Found missing or malformed metadata.")
    return pr, {"number": number, "base": base, "head": head}


def latest_statuses(items):
    results = {}
    for item in items:
        context = item.get("context")
        if context in FLOW and (context not in results or item["id"] > results[context]["id"]):
            results[context] = item
    return results


def start_runs(api, binding, *, inline_required=True):
    # Commit status entries can be written by other actors. They select a
    # candidate run only. The protected run and its artifacts prove the result.
    head = binding["head"]
    required = tuple(FLOW) if inline_required else (CONTEXT, RULES)
    latest = {}
    for page in range(1, 5):
        entries = api.call(f"commits/{head}/statuses?per_page=100&page={page}")
        if not isinstance(entries, list):
            raise Waiting("Expected GitHub's status list with writer identities. Found a different response.")
        latest.update({context: status for context, status in latest_statuses(entries).items()
                       if context not in latest})
        if all(context in latest for context in required) or len(entries) < 100:
            break
    runs = {}
    for context in required:
        status = latest.get(context, {})
        state = status.get("state")
        if state != "success":
            found = state if state in {"pending", "failure", "error"} else "no current status"
            raise Waiting(f"Expected {context} success on the exact head. Found {found}.")
        if (status.get("creator") or {}).get("id") != BOT_ID:
            raise Waiting(f"Expected {context} from GitHub Actions. Found a different or missing writer.")
        target = URL.fullmatch(status.get("target_url") or "")
        base_marker = f"(main {binding['base'][:12]})"
        if not target or base_marker not in (status.get("description") or ""):
            raise Waiting(f"Expected {context} to link its protected run on {binding['base'][:12]}. Found a stale or missing binding.")
        runs[context] = target[1]
    if inline_required and runs[CONTEXT] != runs[INLINE]:
        raise Waiting("Expected match and inline virtual from the same run. Found different runs.")
    result = {}
    for context in (CONTEXT, RULES):
        run = api.call("actions/runs/" + runs[context])
        event = run.get("event")
        run_sha = {"pull_request_target": binding["head"], "repository_dispatch": binding["base"]}.get(event)
        if (str(run.get("id")) != runs[context] or run.get("path") != FLOW[context]
                or run_sha is None or run.get("head_sha") != run_sha
                or (run.get("repository") or {}).get("id") != REPO_ID
                or run.get("status") != "completed" or run.get("conclusion") != "success"
                or not NUMBER.fullmatch(str(run.get("run_attempt", "")))):
            raise Waiting(f"Expected a completed, successful protected {context} run for the PR head. Found incompatible run metadata.")
        linked = (run.get("pull_requests") or []) if event == "pull_request_target" else []
        if linked and not any(item.get("number") == binding["number"]
                              and (item.get("head") or {}).get("sha") == binding["head"]
                              and (item.get("base") or {}).get("sha") == binding["base"]
                              and (item.get("base") or {}).get("ref") == "main" for item in linked):
            raise Waiting(f"Expected {context} to bind this PR and main. Found another associated pair.")
        result[context] = (runs[context], str(run["run_attempt"]))
    return result


def maintainer_review(api, pr, binding, allow):
    if not allow:
        raise Waiting("Set BFME_MAINTAINER_IDS to approved reviewer account IDs.")
    latest = {}
    for page in range(1, 21):
        records = api.call(f"pulls/{binding['number']}/reviews?per_page=100&page={page}")
        for item in records:
            actor = (item.get("user") or {}).get("id")
            if actor not in allow or actor == pr["user"]["id"]:
                continue
            if item.get("state") in {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}:
                number = item["id"]
                if actor not in latest or number > latest[actor][0]:
                    latest[actor] = (number, item["state"] == "APPROVED" and item.get("commit_id") == binding["head"])
        if len(records) < 100:
            return any(approved for _, approved in latest.values())
    raise Waiting("Too many review records to verify the latest maintainer approval.")


def compare_receipts(match, inline, rules, binding, match_attempt, match_run, rules_attempt, rules_run, rules_policy,
                     *, inline_required=True):
    base, head, number = (binding[key] for key in ("base", "head", "number"))
    if (match.get("repo") != REPO_ID or match.get("version") != 1 or match.get("number") != number
            or match.get("base") != base or match.get("head") != head or match.get("kind") != "ok"
            or not HEX40.fullmatch(match.get("tree", "")) or not HEX64.fullmatch(match.get("plan", ""))):
        raise Waiting("The match receipt does not prove this exact main and pull request.")
    positions = {key: match[key] for key in ("base", "head", "tree")}
    if inline_required and (not isinstance(inline, dict) or inline.get("binding") != positions or inline.get("plan") != match["plan"]
            or inline.get("number") != number or inline.get("repo") != REPO_ID
            or inline.get("run") != match_run or inline.get("attempt") != match_attempt
            or inline.get("policy_sha256") != policy() or inline.get("state") != "pass"
            or inline.get("verdict") != "pass" or not HEX64.fullmatch(inline.get("evidence_sha256", ""))):
        raise Waiting("The inline receipt did not pass on the same exact admitted tree.")
    if (any(rules.get(key) != value for key, value in positions.items())
            or rules.get("number") != number or rules.get("tools_commit") != base
            or rules.get("repo") != REPO_ID or rules.get("run") != rules_run or rules.get("attempt") != rules_attempt
            or rules.get("state") != "pass" or rules.get("policy_sha256") != rules_policy):
        raise Waiting("The source rules receipt did not pass on the same exact admitted tree.")
    return positions


def output(name, value):
    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as file:
        file.write(f"{name}={value}\n")


def summary(message):
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a") as file:
        file.write(f"**BFME II landing rehearsal**\n\n{message}\n")


def main(mode, directory):
    if (os.environ.get("GITHUB_REPOSITORY") != REPO
            or os.environ.get("GITHUB_REPOSITORY_ID") != str(REPO_ID)
            or os.environ.get("GITHUB_REF") != "refs/heads/main"
            or os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch"):
        raise RuntimeError("Run this from the protected repository main.")
    base = os.environ["GITHUB_SHA"]
    number = os.environ["BFME_PR"]
    if not NUMBER.fullmatch(number) or not HEX40.fullmatch(base):
        raise ValueError("Use a valid pull request number and protected main revision.")
    repo = GitHub()
    pr, binding = pull(repo, int(number), base)
    directory = Path(directory)
    if mode == "discover":
        runs = start_runs(repo, binding)
        directory.mkdir(mode=0o700)
        match_run, match_attempt = runs[CONTEXT]
        rules_run, rules_attempt = runs[RULES]
        for key, value in (("match_run", match_run), ("rules_run", rules_run), ("match_attempt", match_attempt),
                           ("rules_attempt", rules_attempt)):
            output(key, value)
        write(directory / "binding.json", binding | {"runs": runs})
    elif mode == "verify":
        prior = read(directory / "binding.json", 4096)
        runs = start_runs(repo, binding)
        if prior != binding | {"runs": {name: list(run) for name, run in runs.items()}}:
            raise Waiting("The pair or check attempts changed while collecting evidence.")
        match = read(directory / "match/verdict.json", 256 * 1024)
        inline = read(directory / "inline/inline-status.json", 4096)
        rules = read(directory / "rules/receipt.json", 4096)
        from gate import policy_digest
        rules_policy = policy_digest(TOOLS / "config.json")
        match_run, match_attempt = runs[CONTEXT]
        rules_run, rules_attempt = runs[RULES]
        positions = compare_receipts(match, inline, rules, binding, match_attempt, match_run,
                                     rules_attempt, rules_run, rules_policy)
        allow = {int(value) for value in os.environ.get("BFME_MAINTAINER_IDS", "").split(",") if NUMBER.fullmatch(value)}
        if allow and not maintainer_review(repo, pr, binding, allow):
            raise Waiting("Waiting for a listed maintainer to approve this exact head.")
        repo.current(binding)
        if runs != start_runs(repo, binding):
            raise Waiting("An exact-head status or its producing attempt changed after verification.")
        summary(f"Eligible on exact main {quoted(base[:12])}, head {quoted(binding['head'][:12])}, "
                f"and candidate tree {quoted(positions['tree'][:12])}. "
                "All three protected receipts match. Merge held: this private Free repository cannot enforce the measured base at the merge operation.")
    else:
        raise RuntimeError("Unknown landing rehearsal operation.")


if __name__ == "__main__":
    try:
        main(*sys.argv[1:])
    except (Waiting, Superseded, FileNotFoundError) as exc:
        detail = str(exc) if isinstance(exc, Waiting) else "Expected the exact current pair and receipts. Found changed or missing inputs."
        print(f"Landing rehearsal held. {detail}", file=sys.stderr)
        summary(f"Held. {detail}")
        raise SystemExit(1) from None
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as exc:
        # Other exception text can include a path, token-related data, or a redirect.
        detail = f"Expected verified landing inputs. Found a {type(exc).__name__} while checking them."
        print(f"Landing rehearsal held. {detail}", file=sys.stderr)
        summary(detail)
        raise SystemExit(1) from None

