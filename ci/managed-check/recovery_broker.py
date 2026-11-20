"""Stage exact-attempt recovery checkpoints with a read-only GitHub credential."""

import os
from pathlib import Path
import sys
from time import sleep, time

from common import read, write
from recovery_artifacts import Actions
from wide import admission, load_matrix
from wide_plan import identity
from wide_recovery import (
    GROUP_LIMIT, RESERVE_SECONDS, checked_lease, freeze, groups, label,
)

PRIMARY_SECONDS = 520
LEASE_LIMIT = 64 * 1024
POLL = 10


def output(values):
    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as target:
        for key, value in values.items():
            target.write(f"{key}={value}\n")


def anchor(source):
    plan, _ = admission(Path(source))
    start = Actions(plan["head"]).anchor()
    cutoff = start + PRIMARY_SECONDS
    output({"started": start, "primary_cutoff": cutoff, "reserve_cutoff": cutoff + RESERVE_SECONDS})


def recovery_inputs(source, matrix, checksum, started, cutoff):
    plan, _ = admission(Path(source))
    doc = load_matrix(Path(matrix), checksum, plan)
    start, cutoff = int(started), int(cutoff)
    if cutoff - start != PRIMARY_SECONDS or start > time() or start + 900 < time():
        raise ValueError("A recovery job has an unavailable attempt window.")
    api = Actions(plan["head"])
    if api.anchor() != start:
        raise ValueError("The recovery clock is not the service's attempt clock.")
    return doc, api, start, cutoff


def freeze_for_reserves(source, matrix, checksum, directory, target, started, cutoff):
    doc, api, start, cutoff = recovery_inputs(source, matrix, checksum, started, cutoff)
    prefix = "bfme-recovery-primary-" + api.run["attempt"] + "-"
    names = {prefix + label(pair): "primary-" + label(pair) for pair in groups(doc)}
    root = Path(directory)
    root.mkdir(mode=0o700)
    seen = {}
    while True:
        observed = api.inventory(names, earliest=start, cutoff=cutoff)
        if any(observed.get(name, observed_id) != observed_id for name, observed_id in seen.items()):
            raise ValueError("A primary checkpoint changed after its service timestamp was verified.")
        todo = {name: value for name, value in observed.items() if name not in seen}
        if todo:
            api.primary(todo, names, root)
            seen.update(todo)
        if set(seen) == set(names) or time() >= cutoff:
            break
        sleep(max(0, min(POLL, cutoff - time())))
    lease = freeze(doc, checksum, root, cutoff)
    write(target, lease)
    output({"lease_sha": identity(lease), "reserve_needed": str(bool(lease["reserve"])).lower()})
    print(f"Frozen {len(lease['primary'])} paired groups; leased {len(lease['reserve'])} groups.")


def wait_for_lease(source, matrix, checksum, target, started, cutoff):
    doc, api, start, cutoff = recovery_inputs(source, matrix, checksum, started, cutoff)
    end = cutoff + RESERVE_SECONDS
    name = "bfme-recovery-lease-" + api.run["attempt"]
    while time() < end:
        records = api.inventory({name}, earliest=start, cutoff=end)
        if records:
            dest = Path(target)
            dest.mkdir(mode=0o700)
            api.extract(records[name], {"lease.json"}, LEASE_LIMIT, dest)
            lease = read(dest / "lease.json", LEASE_LIMIT)
            digest = identity(lease)
            checked_lease(doc, checksum, lease, digest)
            if lease["primary_cutoff"] != cutoff:
                raise ValueError("The reserve lease changed the protected cutoff.")
            output({"lease_sha": digest, "reserve_needed": str(bool(lease["reserve"])).lower()})
            return
        # Poll infrequently before the recovery window. Four reserves can
        # wait concurrently without making one request per second each.
        sleep(max(0, min(POLL if time() >= cutoff else 20, end - time())))
    raise ValueError("The protected recovery lease missed its deadline.")


def gather_reserves(source, matrix, checksum, lease_path, lease_sha, directory, started, cutoff):
    doc, api, _start, cutoff = recovery_inputs(source, matrix, checksum, started, cutoff)
    lease = read(lease_path, LEASE_LIMIT)
    checked_lease(doc, checksum, lease, lease_sha)
    if lease["primary_cutoff"] != cutoff:
        raise ValueError("The recovery lease changed the protected cutoff.")
    allowed = {}
    for name, slot in lease["reserve"].items():
        artifact = f"bfme-recovery-reserve-{api.run['attempt']}-{slot}"
        allowed.setdefault(artifact, set()).add("reserve-" + name + "/group.json")
    if not allowed:
        return
    end = lease["reserve_cutoff"]
    seen = set()
    while True:
        current = api.inventory(allowed, earliest=cutoff, cutoff=end)
        for name, artifact in current.items():
            if name in seen:
                continue
            api.extract(artifact, allowed[name], GROUP_LIMIT, Path(directory))
            seen.add(name)
        if seen == allowed.keys():
            return
        if time() >= end:
            raise ValueError("A leased paired group missed the reserve deadline.")
        sleep(max(0, min(POLL, end - time())))


def main(mode, *args):
    os.umask(0o077)
    if mode == "clock":
        anchor(*args)
    elif mode == "freeze":
        freeze_for_reserves(*args)
    elif mode == "lease":
        wait_for_lease(*args)
    elif mode == "gather":
        gather_reserves(*args)
    else:
        raise ValueError("Unknown managed recovery step.")


if __name__ == "__main__":
    main(*sys.argv[1:])
