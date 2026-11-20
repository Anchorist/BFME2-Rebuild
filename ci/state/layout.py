"""Split a complete main state into one small file per source file, and join it back.

The input is the numeric snapshot written by the main state workflow
(`.github/workflows/state.yml`, `ci/managed-state/state_workflow.py`):

    {"schema": 1, "sha": <main commit>, "checker": <sha256>, "tus": {<src path>: <unit>}}

where each unit is the record `ci/managed-state/state_snapshot.unit_status` accepts.

The `state` branch holds:

    index.json              the main commit, its tree, the checker, totals, and the
                            SHA-256 of every per-file record
    files/<src path>.json   one record per source file:
                            {"schema": 1, "tu": path, "verified": bool, "error": bool,
                             "gate_sha256": [...],
                             "functions": {"0x00ABCDEF": [verdict, percent, proven]}}
    README.md               this format, for readers

A per-file record never names the main commit, so a file whose verdicts did not
change keeps the same bytes and Git stores nothing new for it.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

sys.path.insert(1, str(Path(__file__).resolve().parent.parent / "managed-state"))
from state_snapshot import OID, SHA, safe_tu, unit_status  # noqa: E402

SCHEMA = 1
PREFIX = "files/"
MAX_FILE = 1024**2          # one per-file record; real ones are a few KiB
MAX_INDEX = 4 * 1024**2     # about 110 bytes per source file


class Refused(ValueError):
    """A step that must not continue. The message says what was expected and what was found."""


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("ascii")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def record(tu, unit):
    unit = unit_status(unit)
    proven = set(unit["proven"])
    functions = {rva: [verdict, pct, rva in proven] for rva, (verdict, pct) in unit["rows"].items()}
    return {"schema": SCHEMA, "tu": tu, "verified": unit["verified"], "error": unit["error"],
            "gate_sha256": unit["gate_sha256"], "functions": functions}


def unit_from(record_doc):
    rows = {rva: [value[0], value[1]] for rva, value in record_doc["functions"].items()}
    proven = sorted(rva for rva, value in record_doc["functions"].items() if value[2] is True)
    return unit_status({"rows": rows, "proven": proven, "verified": record_doc["verified"],
                        "error": record_doc["error"], "gate_sha256": record_doc["gate_sha256"]})


def totals(units):
    count = {"files": len(units), "functions": 0, "match": 0, "proven": 0,
             "verified_files": 0, "error_files": 0}
    for unit in units.values():
        count["functions"] += len(unit["rows"])
        count["match"] += sum(v[0] == "MATCH" for v in unit["rows"].values())
        count["proven"] += len(unit["proven"])
        count["verified_files"] += int(unit["verified"])
        count["error_files"] += int(unit["error"])
    return count


def check_snapshot(snapshot, sha, units_expected):
    """Validate a numeric snapshot against the exact commit's list of source files."""
    if not isinstance(snapshot, dict) or set(snapshot) != {"schema", "sha", "checker", "tus"}:
        found = sorted(snapshot) if isinstance(snapshot, dict) else type(snapshot).__name__
        raise Refused(f"state input: expected keys ['checker', 'schema', 'sha', 'tus'], found {found}")
    if snapshot["schema"] != 1:
        raise Refused(f"state input: expected schema 1, found {snapshot['schema']!r}")
    if snapshot["sha"] != sha:
        raise Refused(f"state input: expected main commit {sha}, found {snapshot['sha']!r}")
    if not isinstance(snapshot["checker"], str) or not SHA.fullmatch(snapshot["checker"]):
        raise Refused(f"state input: expected a 64-hex checker digest, found {snapshot['checker']!r}")
    have = sorted(snapshot["tus"]) if isinstance(snapshot["tus"], dict) else []
    if have != units_expected:
        missing = sorted(set(units_expected) - set(have))
        extra = sorted(set(have) - set(units_expected))
        raise Refused(f"state input: expected {len(units_expected)} source files with an expected/ record, "
                      f"found {len(have)} (missing {len(missing)}, first {missing[:3]}; "
                      f"extra {len(extra)}, first {extra[:3]})")
    for tu in have:
        if not safe_tu(tu):
            raise Refused(f"state input: expected a src/ C or C++ path, found {tu!r}")
        try:
            unit_status(snapshot["tus"][tu])
        except ValueError as error:
            raise Refused(f"state input: expected a valid record for {tu}, found: {error}") from None


def split(snapshot, tree):
    """Return {path on the state branch: bytes} for one validated snapshot."""
    if not OID.fullmatch(snapshot["sha"]) or not OID.fullmatch(tree):
        raise Refused(f"state split: expected 40-hex commit and tree, found {snapshot['sha']!r} {tree!r}")
    files, digests, units = {}, {}, {}
    for tu in sorted(snapshot["tus"]):
        doc = record(tu, snapshot["tus"][tu])
        data = canonical(doc)
        if len(data) > MAX_FILE:
            raise Refused(f"state split: expected at most {MAX_FILE} bytes for {tu}, found {len(data)}")
        files[PREFIX + tu + ".json"] = data
        digests[tu] = sha256(data)
        units[tu] = unit_status(snapshot["tus"][tu])
    index = {"schema": SCHEMA, "main": snapshot["sha"], "tree": tree, "checker": snapshot["checker"],
             "totals": totals(units), "files": digests}
    data = canonical(index)
    if len(data) > MAX_INDEX:
        raise Refused(f"state split: expected an index of at most {MAX_INDEX} bytes, found {len(data)}")
    files["index.json"] = data
    files["README.md"] = (Path(__file__).with_name("STATE-BRANCH.md")).read_bytes()
    return files


def join(read):
    """Rebuild {"schema","sha","checker","tus"} from a state branch. `read(path)` returns bytes."""
    index = json.loads(read("index.json"))
    if index.get("schema") != SCHEMA:
        raise Refused(f"state join: expected index schema {SCHEMA}, found {index.get('schema')!r}")
    tus = {}
    for tu, digest in sorted(index["files"].items()):
        data = read(PREFIX + tu + ".json")
        if sha256(data) != digest:
            raise Refused(f"state join: expected {tu} to hash to {digest}, found {sha256(data)}")
        doc = json.loads(data)
        if doc.get("tu") != tu or doc.get("schema") != SCHEMA:
            raise Refused(f"state join: expected record for {tu}, found {doc.get('tu')!r}")
        tus[tu] = unit_from(doc)
    if totals(tus) != index["totals"]:
        raise Refused(f"state join: expected totals {index['totals']}, found {totals(tus)}")
    return {"schema": 1, "sha": index["main"], "checker": index["checker"], "tus": tus}


def normalized(snapshot):
    """The snapshot with every unit in the canonical form unit_status returns."""
    return {"schema": snapshot["schema"], "sha": snapshot["sha"], "checker": snapshot["checker"],
            "tus": {tu: unit_status(unit) for tu, unit in sorted(snapshot["tus"].items())}}


def differences(expected, found, limit=20):
    """Lines naming what differs between two snapshots, at most `limit` file lines."""
    lines = []
    for key in ("sha", "checker"):
        if expected[key] != found[key]:
            lines.append(f"{key}: expected {expected[key]}, found {found[key]}")
    a, b = expected["tus"], found["tus"]
    for tu in sorted(set(a) | set(b)):
        if a.get(tu) == b.get(tu):
            continue
        if tu not in b:
            lines.append(f"{tu}: expected present, found absent")
        elif tu not in a:
            lines.append(f"{tu}: expected absent, found present")
        else:
            rows = sorted(r for r in set(a[tu]["rows"]) | set(b[tu]["rows"])
                          if a[tu]["rows"].get(r) != b[tu]["rows"].get(r))
            detail = "; ".join(f"{r} expected {a[tu]['rows'].get(r)} found {b[tu]['rows'].get(r)}"
                               for r in rows[:3])
            other = [k for k in ("proven", "verified", "error", "gate_sha256") if a[tu][k] != b[tu][k]]
            lines.append(f"{tu}: {detail or 'rows equal'}" + (f"; also differs in {other}" if other else ""))
        if len(lines) >= limit:
            lines.append("(more differences not listed)")
            break
    return lines


def tu_path(path):
    """The source file a state branch path describes, or None."""
    if not path.startswith(PREFIX) or not path.endswith(".json"):
        return None
    tu = path[len(PREFIX):-len(".json")]
    return tu if safe_tu(tu) and PurePosixPath(tu).as_posix() == tu else None
