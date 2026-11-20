"""Rejoin the protected bootstrap receipts after its artifact service reset."""

from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import re
import sys
from zipfile import BadZipFile

from state_fetch import GitHub, REPO, REPO_ID, WORKFLOW, retry
from state_snapshot import MAX_PLAN_BYTES, MAX_SHARD_BYTES, canonical, digest, git, load, make_plan
from state_workflow import PIN, assembled, assemble_evidence
from state_transport import transfer
from state_evidence import LIMIT, header

SOURCE = "cd88e80ac175ec64a3b48bfaacb07d680d66a599"
# These protected intervening commits changed only state transport, progress reporting, landing
# orchestration, and source-rule delivery. Compiler and comparison inputs are
# byte-identical at the two pins and verified below.
INSTALL_BASE = "afc5c0fa60758e444d2bc1694019d1d35ab90873"
RUN = 44781520465
COUNT = 102
PLAN = "bfme-state-plan-1"
TRANSPORT = {
    ".github/workflows/state.yml",
    ".github/workflows/state-seed-refresh.yml",
    "ci/managed-state/bundle.sha256",
    "ci/managed-state/recovery-artifacts.json",
    "ci/managed-state/state_delta.py",
    "ci/managed-state/state_fetch.py",
    "ci/managed-state/state_origin.py",
    "ci/managed-state/state_recover.py",
    "ci/managed-state/state_workflow.py",
    "ci/managed-state/state_transport.py",
}


def transport_child(root, current):
    if not re.fullmatch("[0-9a-f]{40}", current):
        raise ValueError("Expected the exact protected revision.")
    hashes = git(root, "rev-list", "--parents", "-n", "1", current).decode().split()
    if hashes != [current, INSTALL_BASE]:
        raise ValueError("Recovery requires a direct child of the reviewed install base.")
    surface = ("src", "include", "config", "baseline", "expected", "ci/managed-check",
               "ci/managed-nt2", "ci/managed-state/compare_main.py")
    if git(root, "diff", "--name-only", "-z", SOURCE, INSTALL_BASE, "--", *surface):
        raise ValueError("The intervening protected revisions changed a comparison input.")
    diff = git(root, "diff", "--name-only", "--no-renames", "-z", INSTALL_BASE, current, "--")
    paths = {part.decode("utf-8", "strict") for part in diff.split(b"\0") if part}
    if not paths or not paths <= TRANSPORT:
        raise ValueError("Recovery may only change state transport files.")


def inventory(api, expected):
    run = retry(lambda: api.call(f"actions/runs/{RUN}/attempts/1"))
    if (run.get("id") != RUN or run.get("head_sha") != SOURCE
            or run.get("head_branch") != "main" or run.get("path") != WORKFLOW
            or (run.get("repository") or {}).get("id") != REPO_ID
            or run.get("event") != "repository_dispatch" or run.get("run_attempt") != 1
            or run.get("status") != "completed" or run.get("conclusion") != "failure"):
        raise ValueError("The original protected run no longer matches its bound receipt.")
    pages = [retry(lambda: api.call(f"actions/runs/{RUN}/artifacts?per_page=100&page={page}"))
             for page in (1, 2)]
    if any(item.get("total_count") != COUNT + 1 for item in pages):
        raise ValueError("The original artifact count changed.")
    actual = [{key: obj[key] for key in ("name", "id", "digest", "size_in_bytes")}
              for item in pages for obj in item["artifacts"] if not obj["expired"]]
    if sorted(actual, key=lambda row: row["name"]) != sorted(expected, key=lambda row: row["name"]):
        raise ValueError("Expected the pinned plan and all 102 original artifact digests.")
    return actual


def required_artifacts():
    specs = {PLAN: {"state-plan.json": MAX_PLAN_BYTES, "carry.json": LIMIT}}
    for index in range(COUNT):
        specs[f"bfme-state-1-shard-{index}"] = {
            f"state-shard-{index}.json": MAX_SHARD_BYTES,
            f"base-shard-{index}.json": MAX_SHARD_BYTES,
        }
    return specs


def fetch(api, directory, listing):
    specs = required_artifacts()
    if len(listing) != len(specs) or set(specs) != {row["name"] for row in listing}:
        raise ValueError("Recovery received missing or foreign artifact names.")

    def fetch_one(row):
        transfer(api, row, directory / row["name"], specs[row["name"]])

    with ThreadPoolExecutor(max_workers=4) as workers:
        list(workers.map(fetch_one, listing))


def recover(root, current, receipts, output):
    transport_child(root, current)
    plan = load(receipts / PLAN / "state-plan.json", MAX_PLAN_BYTES)
    tree = git(root, "rev-parse", SOURCE + "^{tree}").decode().strip()
    empty_carry = header(SOURCE, tree) | {"plan": digest(plan), "evidence": {}}
    if (plan != make_plan(root, SOURCE, PIN["checker"], per_batch=32)
            or len(plan["batches"]) != COUNT
            or load(receipts / PLAN / "carry.json", LIMIT) != empty_carry):
        raise ValueError("Recovery requires the original complete plan without inherited results.")
    dirs = [receipts / f"bfme-state-1-shard-{index}" for index in range(COUNT)]
    # Select once against the exact set of proper shard directories.
    if (set(receipts.iterdir()) != {receipts / PLAN, *dirs}
            or any(path.is_symlink() or not path.is_dir() for path in dirs)):
        raise ValueError("Expected the plan and every exact shard directory.")
    numeric = assembled(root, plan, dirs)
    evidence = assemble_evidence(root, plan, dirs)
    current_tree = git(root, "rev-parse", current + "^{tree}").decode().strip()
    numeric["sha"] = current
    evidence = header(current, current_tree) | {"evidence": evidence["evidence"]}
    articles = {"state.json": (numeric, 64 * 1024**2), "base-state.json": (evidence, LIMIT)}
    for filename, (value, limit) in articles.items():
        data = canonical(value)
        if len(data) > limit:
            raise ValueError("An assembled receipt exceeds its publication budget.")
        with (output / filename).open("xb") as target:
            target.write(data)
    print(f"Rejoined {COUNT} protected bootstrap receipts covering {len(numeric['tus'])} translation units.")


def main(receipts, output):
    if (os.environ.get("GITHUB_REPOSITORY") != REPO
            or os.environ.get("GITHUB_REPOSITORY_ID") != str(REPO_ID)
            or os.environ.get("GITHUB_REF") != "refs/heads/main"
            or os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch"):
        raise ValueError("Recovery only runs on a protected manual main invocation.")
    root, current = Path.cwd(), os.environ["GITHUB_SHA"]
    transport_child(root, current)
    receipts, output = Path(receipts), Path(output)
    receipts.mkdir(mode=0o700)
    output.mkdir(mode=0o700)
    api = GitHub()
    pinned = load(Path(__file__).with_name("recovery-artifacts.json"), 128 * 1024)
    fetch(api, receipts, inventory(api, pinned))
    recover(root, current, receipts, output)


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main(*sys.argv[1:])
    except (BadZipFile, KeyError, OSError, TypeError, ValueError):
        # Storage exceptions can contain signed URLs. The output is only written
        # after provenance checks and a complete successful join.
        raise SystemExit("Protected bootstrap recovery failed. Keep the prior published state.") from None

