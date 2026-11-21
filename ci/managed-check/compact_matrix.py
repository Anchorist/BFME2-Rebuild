"""Verify complete matrix coverage using protected shard-local attestations."""

import re

from managed_matrix import check_native
from emitted_data import valid_witness
from pool_protocol import diagnostic_message
from wide_plan import identity, key

SHA = re.compile(r"[a-f0-9]{64}\Z")
RUN = re.compile(r"[1-9][0-9]{0,19}\Z")
ROWS = ("rva", "status", "pct", "proof", "credited", "size", "symbol")
NATIVE = ("object_verified", "error", "gates", "rows", "optimization_hint", "emitted_data", "blockers")


def compact_native(outcome):
    check_native(outcome)
    if "blockers" not in outcome:
        raise ValueError("The native comparison omitted its verification facts.")
    if "emitted_data" in outcome and not valid_witness(outcome["emitted_data"]):
        raise ValueError("The emitted-data witness is malformed.")
    row_fields = [{name: row[name] for name in ROWS if name in row} for row in outcome["rows"]]
    result = {key: outcome[key] for key in NATIVE if key in outcome}
    result["rows"] = row_fields
    if result.get("error"):
        result["error"] = "\n".join(diagnostic_message(line) for line in result["error"].splitlines()[:8])
    result["gates"] = [diagnostic_message(gate) for gate in result["gates"]]
    return result


def run_id(run, attempt):
    if not isinstance(run, str) or not RUN.fullmatch(run) or not isinstance(attempt, str) or not RUN.fullmatch(attempt):
        raise ValueError("Managed artifacts require an exact Actions run and attempt.")
    return {"id": run, "attempt": attempt}


def assignment_table(document, index):
    shards = document["partition"]["shards"]
    if type(index) is not int or not 0 <= index < len(shards) or shards[index]["index"] != index:
        raise ValueError("Foreign managed shard index.")
    return {(row["side"], row["tu"]): row for row in shards[index]["compile"]}


def make_compact(document, *, expected, run, attempt, compiler, native, details=None, inline=None):
    """Call only after the worker has validated actual COFF and include digests in private scratch."""
    if identity(document) != expected or compiler["plan_sha256"] != identity(document["partition"]):
        raise ValueError("Managed compiler fixture is not bound to its trusted assignment.")
    if compiler["image_sha256"] != document["pins"]["image_sha256"]:
        raise ValueError("Managed compiler identity drift.")
    index = compiler["shard"]
    assigned = assignment_table(document, index)
    records = {}
    for row in compiler["results"]:
        k = key(row)
        if k in records or assigned.get(k, {}).get("source") != row.get("source") or assigned[k]["contract"] != row["contract"]:
            raise ValueError("A managed shard returned a foreign or duplicate compile outcome.")
        entry = {name: row[name] for name in ("side", "tu", "source", "contract", "status")}
        if row["status"] == "compiled":
            entry.update(artifact_sha256=row["object_sha256"],
                         dependencies_sha256=identity(row["dependencies"]))
        elif row["status"] != "error":
            raise ValueError("Unsupported managed compiler outcome.")
        records[k] = entry
    if set(records) != set(assigned) or set(native) != {"base", "head"}:
        raise ValueError("The managed shard comparison is incomplete.")
    for side, outputs in (("parent", native["base"]), ("candidate", native["head"])):
        for tu, outcome in outputs.items():
            records[(side, tu)]["native"] = compact_native(outcome)
    if any("native" not in row for row in records.values()):
        raise ValueError("The managed shard omitted a native verdict.")
    return {"schema": 1, "run": run_id(run, attempt), "managed_plan_sha256": expected,
            "shard": index, "records": [records[k] for k in sorted(records)],
            "details": details or {}, "inline": inline}


def join_compact(document, receipts, *, expected, run, attempt):
    """Use outputs of the expected protected jobs in this attempt, without importing their raw objects."""
    if identity(document) != expected:
        raise ValueError("The managed matrix plan changed.")
    owner = run_id(run, attempt)
    native = {"base": {}, "head": {}}
    details, inline, received = {}, [], set()
    for receipt in receipts:
        if (set(receipt) != {"schema", "run", "managed_plan_sha256", "shard", "records", "details", "inline"}
                or receipt["schema"] != 1 or receipt["run"] != owner or receipt["managed_plan_sha256"] != expected):
            raise ValueError("A managed shard receipt is stale or foreign.")
        index = receipt["shard"]
        remaining = assignment_table(document, index)
        if index in received:
            raise ValueError("Duplicate managed shard receipt.")
        received.add(index)
        for row in receipt["records"]:
            k = key(row)
            assigned = remaining.pop(k, None)
            if not assigned or any(row.get(name) != assigned[name] for name in ("source", "contract")):
                raise ValueError("A compact result differs from its trusted assignment.")
            fields = {"side", "tu", "source", "contract", "status", "native"}
            if row["status"] == "compiled":
                checks = {"artifact_sha256", "dependencies_sha256"}
                if set(row) != fields | checks or any(not SHA.fullmatch(row[name]) for name in checks):
                    raise ValueError("A compact result lacks its private compile proof digest.")
            elif row["status"] != "error" or set(row) != fields or not row["native"].get("error"):
                raise ValueError("A compact result has an invalid failure witness.")
            outcome = row["native"]
            check_native(outcome)
            if "blockers" not in outcome:
                raise ValueError("A native receipt omitted its verification facts.")
            if set(outcome) - set(NATIVE) or any(set(r) - set(ROWS) for r in outcome["rows"]):
                raise ValueError("A compact result includes private native fields.")
            native["base" if k[0] == "parent" else "head"][k[1]] = outcome
        statuses = {key(row): row["status"] for row in receipt["records"]}
        for row in receipt["records"]:
            witness = row["native"].get("emitted_data")
            if "emitted_data" in row["native"]:
                if (row["side"] != "candidate" or row["status"] != "compiled"
                        or statuses.get(("parent", row["tu"])) != "compiled"
                        or not valid_witness(witness)):
                    raise ValueError("The emitted-data witness lacks an authenticated compiled pair.")
        if remaining:
            raise ValueError("A compact shard omitted its required assignments.")
        if not isinstance(receipt["details"], dict) or details.keys() & receipt["details"].keys():
            raise ValueError("Duplicate or invalid sanitized comparison details.")
        details.update(receipt["details"])
        if receipt["inline"] is not None:
            inline.append(receipt["inline"])
    if received != set(range(len(document["partition"]["shards"]))):
        raise ValueError("The compact matrix is incomplete.")
    return native, details, inline
