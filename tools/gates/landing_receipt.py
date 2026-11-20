"""Retain only the validated, bounded source-rule fields used by landing."""
import json
import os
from pathlib import Path
import re
import sys

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
    if env.get("GITHUB_EVENT_NAME") != "pull_request_target" or env.get("GITHUB_REF") != "refs/heads/main":
        raise ValueError("Use only the protected source-rules publication job.")
    raw = env["SOURCE_RULE_RECEIPT"]
    if not 0 < len(raw) <= 4096:
        raise ValueError("The trusted source rules receipt exceeded its size allowance.")
    record = keep(json.loads(raw), env["GITHUB_SHA"], env["GITHUB_REPOSITORY_ID"],
                  env["PR_NUMBER"], env["GITHUB_RUN_ID"], env["GITHUB_RUN_ATTEMPT"])
    path.mkdir(mode=0o700)
    (path / "receipt.json").write_text(json.dumps(record, sort_keys=True, separators=(",", ":"))+"\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
