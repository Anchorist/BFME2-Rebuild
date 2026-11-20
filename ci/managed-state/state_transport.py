"""Download the current plan and its immutable shards with bounded retries."""

from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import re
import sys
from time import sleep
from zipfile import BadZipFile

from state_fetch import GitHub, download, retry
from state_snapshot import MAX_PLAN_BYTES, MAX_SHARD_BYTES, load, validate_plan
from state_evidence import LIMIT


def artifact_rows(api, run):
    max_pages = 4
    for page in range(1, max_pages + 1):
        result = retry(lambda: api.call(f"actions/runs/{run}/artifacts?per_page=100&page={page}"))
        rows = result["artifacts"]
        if not isinstance(rows, list) or len(rows) > 100:
            raise ValueError("Invalid artifact inventory.")
        yield from rows
        if len(rows) < 100:
            return
    raise ValueError("This run exceeds the assembly artifact inventory allowance.")


def chosen(rows, plan_attempt, attempt):
    matcher = re.compile(rf"bfme-state-{plan_attempt}-shard-(0|[1-9][0-9]{{0,2}})-try-([1-9][0-9]{{0,19}})")
    plan_name, found, newest = f"bfme-state-plan-{plan_attempt}", [], {}
    for row in rows:
        if row["expired"]:
            continue
        name = row["name"]
        if name == plan_name:
            found.append(row)
        elif match := matcher.fullmatch(name):
            index, generation = map(int, match.groups())
            if not plan_attempt <= generation <= attempt or index >= 128:
                raise ValueError("The run lists an unexpected shard attempt.")
            if index in newest and newest[index][0] == generation:
                raise ValueError("The run lists a duplicate shard attempt.")
            if index not in newest or newest[index][0] < generation:
                newest[index] = (generation, row)
    if len(found) != 1:
        raise ValueError("Expected one immutable state plan from this run.")
    return found[0], {index: row for index, (_, row) in newest.items()}


def transfer(api, row, location, specs):
    artifact_id, size = row["id"], row["size_in_bytes"]
    expected = row.get("digest") or ""
    if (type(artifact_id) is not int or artifact_id <= 0 or type(size) is not int or not 0 < size <= LIMIT
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", expected)):
        raise ValueError("The state transfer lacks a valid immutable artifact identity.")

    def attempt():
        for name in specs:
            (location / name).unlink(missing_ok=True)
        download(api, artifact_id, size, expected[7:], location, members=specs)

    location.mkdir(mode=0o700)
    retry(attempt)


def restore_plan(api, run, plan_attempt, inputs):
    name = f"bfme-state-plan-{plan_attempt}"
    for pause in (0, 2, 5):
        if pause:
            sleep(pause)
        response = retry(lambda: api.call(f"actions/runs/{run}/artifacts?name={name}&per_page=5"))
        rows = [row for row in response["artifacts"] if row["name"] == name and not row["expired"]]
        if len(rows) > 1:
            raise ValueError("Expected one immutable state plan from this run.")
        if rows:
            transfer(api, rows[0], inputs, {"state-plan.json": MAX_PLAN_BYTES, "carry.json": LIMIT})
            validate_plan(load(inputs / "state-plan.json", MAX_PLAN_BYTES))
            return
    raise ValueError("The exact plan artifact is unavailable.")


def restore(api, run, plan_attempt, attempt, inputs, shards):
    def lookup():
        return chosen(artifact_rows(api, run), plan_attempt, attempt)

    plan_row, results = lookup()
    transfer(api, plan_row, inputs, {"state-plan.json": MAX_PLAN_BYTES, "carry.json": LIMIT})
    plan = load(inputs / "state-plan.json", MAX_PLAN_BYTES)
    validate_plan(plan)
    indices = set(range(len(plan["batches"])))
    if set(results) != indices:
        # A just-completed shard can be briefly absent from the run listing.
        for delay in (2, 5):
            sleep(delay)
            _, results = lookup()
            if set(results) == indices:
                break
    if set(results) != indices:
        raise ValueError("Expected all exact planned state shards.")

    def download_shard(item):
        index, row = item
        transfer(api, row, shards / row["name"], {
            f"state-shard-{index}.json": MAX_SHARD_BYTES,
            f"base-shard-{index}.json": MAX_SHARD_BYTES,
        })

    shards.mkdir(mode=0o700)
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(download_shard, results.items()))
    print(f"Restored one immutable plan and {len(results)} exact state shards.")


def main(inputs, shards=None):
    args = [os.environ[key] for key in ("GITHUB_RUN_ID", "BFME_STATE_PLAN_ATTEMPT", "GITHUB_RUN_ATTEMPT")]
    if not all(re.fullmatch(r"[1-9][0-9]{0,19}", item) for item in args):
        raise ValueError("Expected exact Actions run and attempt numbers.")
    run, plan_attempt, attempt = map(int, args)
    if plan_attempt > attempt:
        raise ValueError("An assembly cannot read a future attempt.")
    api = GitHub()
    if shards is None:
        restore_plan(api, run, plan_attempt, Path(inputs))
    else:
        restore(api, run, plan_attempt, attempt, Path(inputs), Path(shards))


if __name__ == "__main__":
    os.umask(0o077)
    try:
        main(*sys.argv[1:])
    except (BadZipFile, KeyError, OSError, TypeError, ValueError):
        # Object storage exceptions may include signed URLs.
        raise SystemExit("Protected state artifact restoration failed after bounded retries.") from None

