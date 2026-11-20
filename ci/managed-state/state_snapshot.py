"""Assemble a complete exact-main snapshot from trusted comparison shards.

Only booleans, owned row addresses and numeric comparison results are published.
The comparison processes and all raw compiler output are outside this module.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


OID = re.compile(r"[0-9a-f]{40}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
RVA = re.compile(r"0x[0-9a-fA-F]{1,8}\Z")
PATH = re.compile(r"src/[A-Za-z0-9_.+/-]{1,260}\.(?:cpp|cc|cxx|c)\Z")
VERDICTS = {"MATCH", "PARTIAL", "MISSING", "MISNAMED", "WRONG_REFERENCE",
            "COMPILE_ERROR", "UNKNOWN_RVA"}
MAX_PLAN_BYTES = 2 * 1024**2
MAX_SHARD_BYTES = 8 * 1024**2
MAX_TUS, MAX_SHARDS = 12000, 128


def safe_tu(path):
    return (isinstance(path, str) and PATH.fullmatch(path)
            and all(p not in {".", "..", ""} for p in path.split("/")))


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("ascii")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def unique_record(items):
    value = {}
    for name, item in items:
        if name in value:
            raise ValueError("A measurement record repeats a key.")
        value[name] = item
    return value


def load(path, limit):
    if not path.is_file() or path.is_symlink():
        raise ValueError("A measurement input must be a regular file.")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("A measurement input exceeds its size limit.")
    return json.loads(data, object_pairs_hook=unique_record)


def git(directory, *args):
    return subprocess.check_output(["git", "-C", str(directory), *args], timeout=120,
                                   stderr=subprocess.PIPE)


def authoritative_units(repository, main):
    if not OID.fullmatch(main):
        raise ValueError("Supply the full protected main commit.")
    actual = git(repository, "rev-parse", "--verify", main + "^{commit}").decode().strip()
    if actual != main:
        raise ValueError("Main ref did not resolve to the requested commit.")
    entries = git(repository, "ls-tree", "-rz", main, "--", "expected/", "src/").split(b"\0")
    units, sources = set(), set()
    for entry in filter(None, entries):
        record, name = entry.decode().split("\t", 1)
        mode, kind, _ = record.split()
        if mode != "100644" or kind != "blob":
            continue
        if name.startswith("expected/") and name.endswith(".json"):
            source = "src/" + name[len("expected/") : -len(".json")]
            if safe_tu(source):
                units.add(source)
        elif safe_tu(name):
            sources.add(name)
    if units - sources:
        raise ValueError("An expected object has no regular source file on this commit.")
    if not units or len(units) > MAX_TUS:
        raise ValueError("The trusted commit must describe a bounded nonempty set of expected objects.")
    return sorted(units)


def make_plan(repository, main, checker, per_batch):
    if not SHA.fullmatch(checker) or not 8 <= per_batch <= 128:
        raise ValueError("Supply the checked validator digest and a batch size from 8 to 128.")
    units = authoritative_units(repository, main)
    groups = [units[start:start + per_batch] for start in range(0, len(units), per_batch)]
    if len(groups) > MAX_SHARDS:
        raise ValueError("Increase batch size to fit the managed workflow matrix.")
    return {"schema": 1, "main": main, "checker": checker, "batches": groups}


def validate_plan(plan):
    if (not isinstance(plan, dict) or set(plan) != {"schema", "main", "checker", "batches"}
            or plan["schema"] != 1 or not OID.fullmatch(plan["main"])
            or not SHA.fullmatch(plan["checker"])):
        raise ValueError("The state plan does not name an exact main and checker.")
    batches = plan["batches"]
    if not isinstance(batches, list) or not 1 <= len(batches) <= MAX_SHARDS:
        raise ValueError("The state plan must enumerate all expected batches.")
    if not all(isinstance(b, list) and 1 <= len(b) <= 128 for b in batches):
        raise ValueError("A state plan batch exceeds its size limit.")
    flat = [p for record in batches for p in record]
    if (len(flat) > MAX_TUS or any(not safe_tu(p) for p in flat) or sorted(set(flat)) != flat):
        raise ValueError("The state plan contains an invalid, repeated or unsorted TU.")


def unit_status(record):
    if (not isinstance(record, dict) or set(record) != {"rows", "proven", "verified", "error", "gate_sha256"}
            or type(record["error"]) is not bool or type(record["verified"]) is not bool
            or not isinstance(record["rows"], dict) or not isinstance(record["proven"], list)):
        raise ValueError("The trusted comparator returned malformed unit state.")
    gates = record["gate_sha256"]
    if (not isinstance(gates, list) or len(gates) > 512
            or not all(isinstance(g, str) and SHA.fullmatch(g) for g in gates)
            or sorted(set(gates)) != gates):
        raise ValueError("The trusted comparator returned invalid gate fingerprints.")
    normalized = {}
    for rva, verdict in record["rows"].items():
        if (not RVA.fullmatch(rva) or not isinstance(verdict, list) or len(verdict) != 2
                or verdict[0] not in VERDICTS or type(verdict[1]) not in {int, float}
                or not math.isfinite(verdict[1]) or not 0 <= verdict[1] <= 100):
            raise ValueError("The trusted comparator returned malformed row state.")
        key = f"0x{int(rva, 16):08X}"
        if key in normalized:
            raise ValueError("The trusted comparator returned a duplicate row address.")
        normalized[key] = verdict
    if any(not isinstance(rva, str) or not RVA.fullmatch(rva) for rva in record["proven"]):
        raise ValueError("The trusted comparator returned malformed proof state.")
    proven = {f"0x{int(rva, 16):08X}" for rva in record["proven"]}
    if len(proven) != len(record["proven"]) or any(normalized.get(k, [""])[0] != "MATCH" for k in proven):
        raise ValueError("Proof requires a unique credited MATCH in the same unit.")
    if record["error"] and (record["verified"] or proven or any(x[0] == "MATCH" for x in normalized.values())):
        raise ValueError("A failed compilation cannot report credited rows or a verified object.")
    return {"rows": normalized, "proven": sorted(proven), "verified": record["verified"],
            "error": record["error"], "gate_sha256": gates}


def assemble(plan, shards, repository, *, required=None):
    validate_plan(plan)
    if required is None:
        required = authoritative_units(repository, plan["main"])
    if [p for batch in plan["batches"] for p in batch] != required:
        raise ValueError("The shard plan does not cover the protected commit's full ledger surface.")
    batches = plan["batches"]
    pin = digest(plan)
    used = set()
    units = {}
    for shard in shards:
        if (not isinstance(shard, dict)
                or set(shard) != {"schema", "main", "checker", "plan", "batch", "units"}
                or shard["schema"] != 1 or shard["main"] != plan["main"]
                or shard["checker"] != plan["checker"] or shard["plan"] != pin):
            raise ValueError("A measurement shard refers to a different commit, checker or plan.")
        batch = shard["batch"]
        if type(batch) is not int or not 0 <= batch < len(batches) or batch in used:
            raise ValueError("The state refresh repeats an invalid or completed batch.")
        data = shard["units"]
        if not isinstance(data, dict) or set(data) != set(batches[batch]):
            raise ValueError("A measurement shard is missing planned translation units.")
        used.add(batch)
        units.update((tu, unit_status(value)) for tu, value in data.items())
    if len(used) != len(batches):
        raise ValueError("State refresh is incomplete. Leave the existing published state unchanged.")
    return {"schema": 1, "sha": plan["main"], "checker": plan["checker"], "tus": units}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("repository", type=Path)
    commands = p.add_subparsers(dest="operation", required=True)
    plan_cmd = commands.add_parser("plan")
    plan_cmd.add_argument("main")
    plan_cmd.add_argument("checker")
    plan_cmd.add_argument("--per-batch", type=int, default=32)
    merge_cmd = commands.add_parser("assemble")
    merge_cmd.add_argument("plan", type=Path)
    merge_cmd.add_argument("shard", type=Path, nargs="+")
    a = p.parse_args()
    if a.operation == "plan":
        data = make_plan(a.repository, a.main, a.checker, a.per_batch)
    else:
        if len(a.shard) > MAX_SHARDS:
            raise ValueError("State refresh exceeds the allowed batch count.")
        data = assemble(load(a.plan, MAX_PLAN_BYTES),
                        (load(file, MAX_SHARD_BYTES) for file in a.shard), a.repository)
    sys.stdout.buffer.write(canonical(data))


if __name__ == "__main__":
    main()

