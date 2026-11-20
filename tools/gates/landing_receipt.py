"""Retain only the validated, bounded source-rule fields used by landing."""
import json
import os
from pathlib import Path
import re
import sys

# The runner uses isolated Python. Add only this protected checkout directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workflow import CheckUnavailable, REASONS, event

OID = re.compile(r"[0-9a-f]{40}")
HASH = re.compile(r"[0-9a-f]{64}")
ID = re.compile(r"[1-9][0-9]{0,19}")


def keep(document, base, repository_id, number, run, attempt):
    if not all(ID.fullmatch(value) for value in (repository_id, number, run, attempt)):
        raise ValueError("Use the exact repository, PR, run and attempt.")
    if (document.get("base") != base or document.get("tools_commit") != base
            or document.get("state") != "pass" or document.get("overall") != "success"
            or not HASH.fullmatch(document.get("policy_sha256", ""))
            or not all(OID.fullmatch(document.get(key, "")) for key in ("base", "head", "tree"))):
        raise ValueError("Only the exact successful source-rules decision is retained.")
    keys = ("base", "head", "tree", "tools_commit", "policy_sha256", "state")
    return {key: document[key] for key in keys} | {
        "repo": int(repository_id), "number": int(number), "run": run, "attempt": attempt}


def main(path):
    os.umask(0o077)
    env = os.environ
    if env.get("GITHUB_EVENT_NAME") not in {"pull_request_target", "repository_dispatch"}:
        raise ValueError("found a historical or unsupported event")
    binding = event(env)
    raw = env["SOURCE_RULE_RECEIPT"]
    if not 0 < len(raw) <= 4096:
        raise ValueError("The trusted source rules receipt exceeded its size allowance.")
    decision = json.loads(raw)
    if decision.get("head") != binding.head or decision.get("fixture_case"):
        raise ValueError("found a result for another author head or for a historical fixture")
    record = keep(decision, binding.base, str(binding.repo_id),
                  str(binding.number), env["GITHUB_RUN_ID"], env["GITHUB_RUN_ATTEMPT"])
    path.mkdir(mode=0o700)
    (path / "receipt.json").write_text(json.dumps(record, sort_keys=True, separators=(",", ":"))+"\n")


if __name__ == "__main__":
    try:
        main(Path(sys.argv[1]))
    except CheckUnavailable as exc:
        print(f"Expected a current source result for landing. Found: {REASONS[exc.reason]}", file=sys.stderr)
        sys.exit(1)
    except (AttributeError, IndexError, KeyError, OSError, TypeError, ValueError):
        print("Expected an exact successful source result for landing. Found a missing or inconsistent result.", file=sys.stderr)
        sys.exit(1)
