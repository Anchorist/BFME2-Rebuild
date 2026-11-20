"""Deterministically partition an exact paired compile plan and join shard proofs."""
from collections import defaultdict
from hashlib import sha256
import json
import re

from pool_protocol import MAX_OBJECT, check_object, source_path

OID = re.compile(r"[0-9a-f]{40}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
SIDES = {"parent", "candidate"}


def encoded(record):
    return (json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")


def identity(record):
    return sha256(encoded(record)).hexdigest()


def key(row):
    return row["side"], row["tu"]


def plan(binding, rows, *, image_sha256, policy_sha256, limit=16):
    if set(binding) != {"head", "base", "tree"} or not all(
        isinstance(value, str) and OID.fullmatch(value) for value in binding.values()
    ):
        raise ValueError("wide plan requires exact head, base and tree")
    if not all(isinstance(digest, str) and HASH.fullmatch(digest) for digest in (image_sha256, policy_sha256)):
        raise ValueError("wide plan requires image and policy digests")
    if type(limit) is not int or not 1 <= limit <= 32:
        raise ValueError("wide plan requests an unavailable number of runners")
    grouped, keys = defaultdict(list), set()
    for row in rows:
        if (set(row) != {"side", "tu", "source", "contract", "weight"} or row["side"] not in SIDES
                or not source_path(row["tu"]) or not row["tu"].startswith("src/")
                or not row["tu"].lower().endswith((".c", ".cpp"))
                or type(row["weight"]) is not int or row["weight"] < 1
                or not all(isinstance(row[k], str) and HASH.fullmatch(row[k]) for k in ("source", "contract"))):
            raise ValueError("wide plan has an invalid trusted compile row")
        k = key(row)
        if k in keys:
            raise ValueError("duplicate translation unit on the same side")
        keys.add(k)
        grouped[row["tu"]].append(dict(row))
    if not grouped:
        raise ValueError("no compiler work in the wide plan")
    work = [(sum(r["weight"] for r in group), tu, sorted(group, key=key)) for tu, group in grouped.items()]
    shards = [{"index": i, "weight": 0, "compile": []} for i in range(min(limit, len(work)))]
    for weight, _, group in sorted(work, key=lambda item: (-item[0], item[1])):
        worker = min(shards, key=lambda shard: (shard["weight"], shard["index"]))
        worker["weight"] += weight
        worker["compile"].extend(group)
    for shard in shards:
        shard["compile"].sort(key=key)
    return {"schema": 1, "binding": dict(binding), "image_sha256": image_sha256,
            "policy_sha256": policy_sha256, "shards": shards, "compile_rows": len(keys)}


def join(plan_doc, artifacts, *, read_object, validate_dependencies):
    """Use receipts from the expected trusted Actions jobs after producer provenance is checked."""
    expected_id = identity(plan_doc)
    by_shard = {s["index"]: s for s in plan_doc["shards"]}
    completed, results = set(), []
    for receipt in artifacts:
        if (set(receipt) != {"schema", "plan_sha256", "image_sha256", "shard", "results"}
                or receipt["schema"] != 1 or receipt["plan_sha256"] != expected_id
                or receipt["image_sha256"] != plan_doc["image_sha256"]
                or type(receipt["shard"]) is not int or receipt["shard"] in completed
                or receipt["shard"] not in by_shard):
            raise ValueError("stale, duplicate or foreign wide shard")
        index = receipt["shard"]
        completed.add(index)
        required = {key(row): row for row in by_shard[index]["compile"]}
        for row in receipt["results"]:
            k = key(row)
            if k not in required:
                raise ValueError("foreign or duplicate translation unit in wide shard")
            contract = required.pop(k)
            if any(row[field] != contract[field] for field in ("source", "contract")):
                raise ValueError("wide artifact compile instructions or source changed")
            fields = {"side", "tu", "source", "contract", "status"}
            if row["status"] == "compiled" and set(row) == fields | {"object_sha256", "dependencies"}:
                digest = row["object_sha256"]
                if not isinstance(digest, str) or not HASH.fullmatch(digest):
                    raise ValueError("invalid wide object digest")
                body = read_object(index, digest)
                if not isinstance(body, bytes) or len(body) > MAX_OBJECT or check_object(body) != digest:
                    raise ValueError("wide object contents differ from the compile proof")
                validate_dependencies(row["side"], row["tu"], row["dependencies"])
            elif (row["status"] != "error" or set(row) != fields | {"diagnostics"}
                  or not isinstance(row["diagnostics"], str)
                  or not 0 < len(row["diagnostics"].encode("utf-8")) <= 2048):
                raise ValueError("invalid wide diagnostic outcome")
            results.append(dict(row))
        if required:
            raise ValueError("wide shard omitted required translation units")
    if completed != set(by_shard) or len(results) != plan_doc["compile_rows"]:
        raise ValueError("wide matrix is incomplete")
    return sorted(results, key=key)
