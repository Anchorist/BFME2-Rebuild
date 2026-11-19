"""Bind a protected PR scope, portable compiler plans and matrix result receipts."""

import json
import re
from pathlib import Path

from wide_plan import encoded, identity, join, plan

SIDES = {"base": "parent", "head": "candidate"}
SHA = re.compile(r"[a-f0-9]{64}\Z")
STATUS = re.compile(r"[A-Z][A-Z_]{0,31}\Z")
RVA = re.compile(r"0x[0-9a-fA-F]{1,8}\Z")


def digest_pins(scope):
    names = ("image_sha256", "profile_sha256", "checker", "policy_sha256")
    pins = {name: scope["policy" if name == "policy_sha256" and "policy" in scope else name] for name in names}
    if not all(isinstance(value, str) and SHA.fullmatch(value) for value in pins.values()):
        raise ValueError("The managed plan requires exact image, compiler profile, checker and policy pins.")
    return pins


def make(scope, commands, *, limit, weights=None, batch_size=1, batch_cost=0):
    """Commands are portable native compiler instructions from the protected planner."""
    if scope.get("version", scope.get("schema")) != 1 or set(commands) != set(SIDES):
        raise ValueError("Unknown managed plan format.")
    paths = scope["request_paths"]
    if not isinstance(paths, list) or not paths or paths != sorted(set(paths)):
        raise ValueError("The managed native scope must identify each requested TU once.")
    weights = weights or {}
    input_rows, instructions = [], {}
    for input_side, side in SIDES.items():
        rows = commands[input_side]
        if [row["tu"] for row in rows] != paths:
            raise ValueError("Native compile instructions do not cover the complete planned scope.")
        instructions[side] = {row["tu"]: row for row in rows}
        for row in rows:
            if (set(row) != {"tu", "source", "flags", "env", "contract"}
                    or not isinstance(row["flags"], list) or not isinstance(row["env"], dict)):
                raise ValueError("A managed compile instruction is malformed.")
            path = row["tu"]
            input_rows.append({"side": side, "tu": path, "source": row["source"], "contract": row["contract"],
                               "weight": weights.get(path, 1)})
    pins = digest_pins(scope)
    binding = {name: scope[name] for name in ("base", "head", "tree")}
    partition = plan(binding, input_rows, image_sha256=pins["image_sha256"],
                     policy_sha256=pins["policy_sha256"], limit=limit,
                     batch_size=batch_size, batch_cost=batch_cost)
    return {"schema": 1, "scope_sha256": identity(scope), "pins": pins,
            "partition": partition, "instructions": instructions}


def assignment(document, index, *, expected):
    if type(index) is not int or index < 0 or index >= len(document["partition"]["shards"]):
        raise ValueError("Unknown managed matrix shard.")
    if identity(document) != expected:
        raise ValueError("The managed matrix plan has changed.")
    shard = document["partition"]["shards"][index]
    if shard["index"] != index:
        raise ValueError("The matrix assignment has an unexpected index.")
    instructions = {}
    for side in SIDES.values():
        instructions[side] = []
    for row in shard["compile"]:
        side, tu = row["side"], row["tu"]
        command = document["instructions"][side][tu]
        if any(command[field] != row[field] for field in ("source", "contract")):
            raise ValueError("A matrix instruction differs from its assignment.")
        instructions[side].append(command)
    return instructions


def compiler_receipt(document, index, rows):
    return {"schema": 1, "plan_sha256": identity(document["partition"]),
            "image_sha256": document["pins"]["image_sha256"], "shard": index, "results": rows}


def check_row(row):
    return (isinstance(row, dict) and RVA.fullmatch(row.get("rva", ""))
            and STATUS.fullmatch(row.get("status", "")) and type(row.get("credited", False)) is bool
            and row.get("proof") in (None, "proven", "unproven")
            and (not row.get("credited") or row["status"] == "MATCH"))


def check_native(outcome):
    if (not isinstance(outcome, dict) or type(outcome.get("object_verified", False)) is not bool
            or not isinstance(outcome.get("rows"), list) or not all(map(check_row, outcome["rows"]))
            or not isinstance(outcome.get("gates"), list)
            or any(not isinstance(gate, str) for gate in outcome["gates"])):
        raise ValueError("The native comparison has a malformed verdict.")
    addresses = [int(row["rva"], 16) for row in outcome["rows"]]
    if len(addresses) != len(set(addresses)):
        raise ValueError("The native comparison repeated a row.")


def join_native(document, artifacts, *, expected, read_object, validate_dependencies):
    """Aggregate only the trusted comparison jobs for this exact Actions run."""
    if identity(document) != expected:
        raise ValueError("The managed matrix plan has changed.")
    by_side = {side: {} for side in SIDES}
    from_side = {value: key for key, value in SIDES.items()}
    compiler = []
    for artifact in artifacts:
        if (set(artifact) != {"schema", "managed_plan_sha256", "compiler_receipt", "native"}
                or artifact["schema"] != 1 or artifact["managed_plan_sha256"] != expected):
            raise ValueError("A comparison is not bound to the active managed matrix.")
        receipt = artifact["compiler_receipt"]
        compiler.append(receipt)
        permitted = {(row["side"], row["tu"]): row["status"] for row in receipt["results"]}
        for row in artifact["native"]:
            if set(row) != {"side", "tu", "outcome"}:
                raise ValueError("A matrix comparison has unexpected fields.")
            side, tu, outcome = row["side"], row["tu"], row["outcome"]
            if (side, tu) not in permitted or tu in by_side[from_side[side]]:
                raise ValueError("Unexpected or duplicate managed comparison.")
            compile_status = permitted.pop((side, tu))
            check_native(outcome)
            if compile_status == "error" and not outcome.get("error"):
                raise ValueError("A failed compile has a successful comparison.")
            by_side[from_side[side]][tu] = outcome
        if permitted:
            raise ValueError("A matrix comparison omitted requested compile outcomes.")
    join(document["partition"], compiler, read_object=read_object, validate_dependencies=validate_dependencies)
    for input_side, side in SIDES.items():
        if set(by_side[input_side]) != set(document["instructions"][side]):
            raise ValueError("A managed comparison is incomplete.")
    return by_side


def read_document(path):
    return json.loads(Path(path).read_bytes())


def write_document(path, document):
    Path(path).write_bytes(encoded(document))
