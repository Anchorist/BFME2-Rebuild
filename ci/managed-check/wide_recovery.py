"""Checkpoint paired work, lease unfinished groups and reconstruct checked shards."""

from collections import defaultdict
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from time import time

from common import HEX64, encoded, read, write
from compact_matrix import join_compact, run_id
from wide import BATCH, MAX_RECEIPT, admission, compile_assigned, load_matrix
from wide_plan import identity, key

RESERVES = 4
RESERVE_SECONDS = 270
MATRIX_LIMIT = 3 * 1024**2
GROUP_LIMIT = MAX_RECEIPT + 4096
NAME = re.compile(r"(primary|reserve)-([0-9]|[12][0-9]|3[01])-([0-3])\Z")


def active_run():
    return run_id(os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_RUN_ATTEMPT"])


def get_matrix(path, expected):
    doc = read(Path(path) / "matrix.json", MATRIX_LIMIT)
    if not HEX64.fullmatch(expected) or identity(doc) != expected:
        raise ValueError("Recovery matrix differs from the protected plan.")
    return doc


def groups(doc):
    result = {}
    for index, shard in enumerate(doc["partition"]["shards"]):
        rows = shard["compile"]
        if index != shard["index"] or not rows or index >= 32:
            raise ValueError("Invalid protected shard.")
        paired = defaultdict(list)
        for row in rows:
            paired[row["tu"]].append(row)
        paths = sorted(paired)
        if any(sorted(row["side"] for row in pair) != ["candidate", "parent"]
               for pair in paired.values()):
            raise ValueError("Recovery requires complete TU pairs.")
        for offset in range(0, len(paths), BATCH):
            part = offset // BATCH
            if part > 3:
                raise ValueError("A shard exceeds four recoverable groups.")
            result[index, part] = sorted(
                (row for path in paths[offset:offset+BATCH] for row in paired[path]), key=key)
    return result


def group_document(doc, rows):
    instructions = {"parent": {}, "candidate": {}}
    for row in rows:
        side, tu = key(row)
        instructions[side][tu] = doc["instructions"][side][tu]
    return doc | {
        "partition": doc["partition"] | {
            "shards": [{"index": 0, "weight": sum(row["weight"] for row in rows), "compile": rows}],
            "compile_rows": len(rows),
        },
        "instructions": instructions,
    }


def label(pair):
    return f"{pair[0]}-{pair[1]}"


def envelope(expected, pair, slot):
    return {"schema": 1, "run": active_run(), "matrix": expected,
            "shard": pair[0], "part": pair[1], "reserve": slot}


def verify_group(doc, expected, planned, pair, slot, record):
    rest = envelope(expected, pair, slot)
    if set(record) != rest.keys() | {"receipt"} or any(record[k] != v for k, v in rest.items()):
        raise ValueError("Recovery group belongs to a foreign assignment or attempt.")
    child = group_document(doc, planned[pair])
    receipt = record["receipt"]
    current = active_run()
    join_compact(child, [receipt], expected=identity(child), run=current["id"], attempt=current["attempt"])
    inline = receipt["inline"]
    if inline is not None and (
        inline["shard"] != 0 or inline["compiler_plan"] != identity(child["partition"])
        or sorted(map(key, inline["records"])) != sorted(map(key, planned[pair]))
    ):
        raise ValueError("Recovery advisory evidence does not cover its exact assignment.")
    return receipt


def produce(plan, doc, expected, planned, pair, slot, out):
    child = group_document(doc, planned[pair])
    name = f"{label(pair)}" if slot is None else f"{label(pair)} reserve {slot}"
    with tempfile.TemporaryDirectory(prefix="bfme-paired-group-") as tmp:
        folder = Path(tmp) / "receipt"
        compile_assigned(plan, child, identity(child), 0, folder, label=name)
        record = envelope(expected, pair, slot) | {"receipt": read(folder / "shard.json", MAX_RECEIPT)}
        verify_group(doc, expected, planned, pair, slot, record)
        out.mkdir(mode=0o700)
        # A consumer receives this checkpoint only after the whole file is written.
        scratch = out / ".group.json"
        write(scratch, record)
        scratch.rename(out / "group.json")


def find_receipts(directory, planned):
    result = {}
    for item in Path(directory).iterdir():
        match = NAME.fullmatch(item.name)
        if not match or not item.is_dir() or item.is_symlink():
            raise ValueError("Unexpected recovery artifact directory.")
        source, shard, part = match.groups()
        pair = int(shard), int(part)
        if pair not in planned:
            raise ValueError("Foreign recovery group.")
        path = item / "group.json"
        if not path.is_file() or path.is_symlink():
            raise ValueError("The recovery group is missing its ordinary receipt file.")
        result[source, pair] = path
    return result


def assignments(planned, ready):
    loads = [0] * RESERVES
    result = {}
    missing = planned.keys() - ready.keys()
    cost = {pair: sum(row["weight"] for row in planned[pair]) for pair in missing}
    for pair in sorted(missing, key=lambda pair: (-cost[pair], pair)):
        slot = min(range(RESERVES), key=lambda slot: (loads[slot], slot))
        loads[slot] += cost[pair]
        result[label(pair)] = slot
    return result


def freeze(doc, expected, primary_dir, cutoff, *, now=None):
    now = int(time()) if now is None else now
    planned = groups(doc)
    available = find_receipts(primary_dir, planned)
    ready = {}
    for (origin, pair), path in available.items():
        if origin != "primary":
            raise ValueError("Reserve output cannot create a lease.")
        record = read(path, GROUP_LIMIT)
        verify_group(doc, expected, planned, pair, None, record)
        ready[pair] = identity(record)
    if len(ready) != len(planned) and not cutoff <= now < cutoff + RESERVE_SECONDS:
        raise ValueError("A partial assignment can be frozen only in the reserve window.")
    return {"schema": 1, "run": active_run(), "matrix": expected,
            "primary_cutoff": cutoff, "reserve_cutoff": cutoff + RESERVE_SECONDS,
            "primary": {label(pair): checksum for pair, checksum in ready.items()},
            "reserve": assignments(planned, ready)}


def checked_lease(doc, expected, lease, digest):
    if not HEX64.fullmatch(digest) or identity(lease) != digest:
        raise ValueError("Recovery lease differs from its protected digest.")
    expected_keys = {"schema", "run", "matrix", "primary_cutoff", "reserve_cutoff", "primary", "reserve"}
    if (set(lease) != expected_keys or lease["schema"] != 1
            or lease["run"] != active_run() or lease["matrix"] != expected
            or type(lease["primary_cutoff"]) is not int
            or lease["reserve_cutoff"] != lease["primary_cutoff"] + RESERVE_SECONDS):
        raise ValueError("Foreign recovery lease.")
    planned = groups(doc)
    labels = {label(pair): pair for pair in planned}
    ready = {}
    for name, checksum in lease["primary"].items():
        if name not in labels or not isinstance(checksum, str) or not HEX64.fullmatch(checksum):
            raise ValueError("Invalid primary selection in recovery lease.")
        ready[labels[name]] = checksum
    if (any(type(slot) is not int for slot in lease["reserve"].values())
            or lease["reserve"] != assignments(planned, ready)):
        raise ValueError("Noncanonical reserve assignments.")
    return planned, ready


def reconstruct(doc, expected, lease, digest, directory):
    planned, ready = checked_lease(doc, expected, lease, digest)
    available = find_receipts(directory, planned)
    chosen = defaultdict(list)
    for pair in planned:
        origin = "primary" if pair in ready else "reserve"
        selected = available.get((origin, pair))
        if selected is None:
            raise ValueError(f"Recovery group {label(pair)} is incomplete.")
        record = read(selected, GROUP_LIMIT)
        if origin == "primary" and identity(record) != ready[pair]:
            raise ValueError("A primary checkpoint changed after lease creation.")
        slot = None if origin == "primary" else lease["reserve"][label(pair)]
        chosen[pair[0]].append(verify_group(doc, expected, planned, pair, slot, record))
    # Stale/late primary files for replaced groups are irrelevant. A reserve
    # outside its selected assignment is a workflow error.
    if any(origin == "reserve" and pair in ready for origin, pair in available):
        raise ValueError("Recovery output has an unleased reserve group.")
    result = []
    for shard, receipts in sorted(chosen.items()):
        records, details, inline = [], {}, []
        for receipt in receipts:
            if details.keys() & receipt["details"].keys():
                raise ValueError("Duplicate recovery comparison details.")
            records.extend(receipt["records"])
            details.update(receipt["details"])
            if receipt["inline"] is not None:
                inline.extend(receipt["inline"]["records"])
        atoms = None
        if all(item["inline"] is not None for item in receipts):
            atoms = {"shard": shard, "compiler_plan": identity(doc["partition"]), "records": inline}
        result.append({"schema": 1, "run": active_run(), "managed_plan_sha256": expected,
                       "shard": shard, "records": sorted(records, key=key), "details": details, "inline": atoms})
    current = active_run()
    join_compact(doc, result, expected=expected, run=current["id"], attempt=current["attempt"])
    return result


def main(mode, *args):
    os.umask(0o077)
    if mode == "compile":
        source, matrix, expected, shard, part, out = args
        plan, _ = admission(Path(source))
        doc = load_matrix(Path(matrix), expected, plan)
        produce(plan, doc, expected, groups(doc), (int(shard), int(part)), None, Path(out))
    elif mode == "freeze":
        matrix, expected, directory, target, cutoff = args
        lease = freeze(get_matrix(matrix, expected), expected, directory, int(cutoff))
        write(target, lease)
        print(identity(lease))
    elif mode in {"reserve", "reserve-group"}:
        source, matrix, expected, lease_path, lease_sha, slot_arg, directory, *group = args
        slot = int(slot_arg)
        if not 0 <= slot < RESERVES:
            raise ValueError("Unknown reserve runner slot.")
        plan, _ = admission(Path(source))
        doc = load_matrix(Path(matrix), expected, plan)
        lease = read(lease_path, 64 * 1024)
        planned, _ = checked_lease(doc, expected, lease, lease_sha)
        assigned = {label(pair): pair for pair in planned if lease["reserve"].get(label(pair)) == slot}
        out = Path(directory)
        if mode == "reserve":
            if group:
                raise ValueError("A reserve slot does not take a group.")
            out.mkdir(mode=0o700)
            for key in assigned:
                # A judge import binds its scratch home and process-wide tempfile
                # settings. Give the next group a clean interpreter.
                subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()),
                                "reserve-group", *args, key], check=True)
        else:
            if len(group) != 1 or group[0] not in assigned:
                raise ValueError("The reserve group is not assigned to this slot.")
            if not lease["primary_cutoff"] <= time() < lease["reserve_cutoff"]:
                raise ValueError("Reserve lease is not in its execution window.")
            key = group[0]
            produce(plan, doc, expected, planned, assigned[key], slot, out / ("reserve-" + key))
    elif mode == "join":
        matrix, expected, lease_path, lease_sha, directory, out = args
        records = reconstruct(get_matrix(matrix, expected), expected, read(lease_path, 64 * 1024),
                              lease_sha, directory)
        out = Path(out)
        out.mkdir(mode=0o700)
        for record in records:
            if len(encoded(record)) > MAX_RECEIPT:
                record["inline"] = None
                print(f"Wide shard {record['shard']}: advisory evidence exceeded the shard limit.", file=sys.stderr)
            if len(encoded(record)) > MAX_RECEIPT:
                raise ValueError(f"Expected capped native receipt; shard {record['shard']} exceeded its limit.")
            sub = out / f"shard-{record['shard']}"
            sub.mkdir(mode=0o700)
            write(sub / "shard.json", record)
    else:
        raise ValueError("Unknown paired recovery operation.")


if __name__ == "__main__":
    main(*sys.argv[1:])
