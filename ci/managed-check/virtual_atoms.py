"""Join authenticated candidate-derived vftable effects without uploading raw COFF."""

from hashlib import sha256
import json
from pathlib import Path
import struct

from managed_inline import BASELINE, CATALOGUE, INLINE, report_text
from compact_matrix import assignment_table
from managed_matrix import SIDES
from pool_protocol import check_object
from wide_plan import identity, key

import inline_virtual_shadow as gate
from inline_virtual_receipt import make_receipt
from portable_binary import COFF, PE


def effect_wire(effect):
    if effect is None:
        return None
    if isinstance(effect, gate.Tail):
        return ["tail", effect.name, effect.receiver_delta]
    return ["effect", effect.kind, effect.value, effect.pop, effect.write]


def fixed(value):
    if isinstance(value, list):
        return tuple(map(fixed, value))
    return value


def effect_value(item):
    if item is None:
        return None
    if item[0] == "tail" and len(item) == 3:
        return gate.Tail(*item[1:])
    if item[0] == "effect" and len(item) == 5:
        return gate.Effect(*map(fixed, item[1:]))
    raise ValueError("Unknown managed virtual effect record.")


def collect(compiler, object_dir=None, *, find_object=None):
    """Called in the isolated compile shard after exact source, dependency and object authentication."""
    if (object_dir is None) == (find_object is None):
        raise ValueError("Select exactly one private object lookup.")
    records = []
    for row in compiler["results"]:
        side, tu = key(row)
        entry = {"side": side, "tu": tu}
        if row["status"] == "error":
            records.append(entry | {"unavailable": "compiler reported an error"})
            continue
        digest = row["object_sha256"]
        path = Path(find_object(side, tu)) if find_object else Path(object_dir) / (digest + ".obj")
        if path.is_symlink() or check_object(path.read_bytes()) != digest:
            raise ValueError("Virtual shard COFF differs from the private compiler receipt.")
        try:
            tables, bodies = gate.collect_one(COFF(path))
        except (IndexError, KeyError, OSError, TypeError, ValueError, struct.error):
            records.append(entry | {"unavailable": "compiler object could not be decoded"})
            continue
        records.append(entry | {"tables": tables, "bodies": [[name,effect_wire(effect)] for name,effect in bodies]})
    return {"shard": compiler["shard"], "compiler_plan": compiler["plan_sha256"], "records": records}


def evaluate(document, atoms, *, expected, repo, candidate, baseline, scope_complete=True):
    if identity(document) != expected:
        raise ValueError("Virtual portions carry the wrong managed plan.")
    baseline = Path(baseline)
    catalogue = INLINE / "catalogue-audited.json"
    if sha256(baseline.read_bytes()).hexdigest() != BASELINE or sha256(catalogue.read_bytes()).hexdigest() != CATALOGUE:
        raise ValueError("Managed virtual reference or catalogue differs from the protected policy.")
    pe, catalog = PE(baseline), json.loads(catalogue.read_bytes())
    mappings = {side: gate.collections() for side in SIDES.values()}
    covered = {side: set() for side in SIDES.values()}
    holes = {side: [] for side in SIDES.values()}
    received = set()
    expected_shards = {s["index"] for s in document["partition"]["shards"]}
    partition = identity(document["partition"])
    for shard in atoms:
        idx = shard["shard"]
        if idx in received or idx not in expected_shards or shard["compiler_plan"] != partition:
            raise ValueError("Duplicate or foreign managed virtual shard.")
        received.add(idx)
        requested = assignment_table(document, idx)
        for item in shard["records"]:
            side, tu = key(item)
            if (side, tu) not in requested:
                raise ValueError("Unexpected managed virtual atoms.")
            requested.pop((side,tu))
            if "unavailable" in item:
                holes[side].append((tu, item["unavailable"]))
                continue
            tables = [(name, tuple(slots)) for name, slots in item["tables"]]
            bodies = [(name, effect_value(effect)) for name, effect in item["bodies"]]
            gate.collect_into(*mappings[side], tu, tables, bodies)
            covered[side].add(tu)
        if requested:
            raise ValueError("Managed virtual shard omitted compile outcomes.")
    binding = document["partition"]["binding"]
    reports = {}
    for side,pin in (("parent", binding["base"]), ("candidate", candidate)):
        requested = document["instructions"][side]
        reported = gate.scan_collected(pe, catalog, *mappings[side], None, holes[side], keep_comparable=True)
        reports[side] = reported | {"pin": pin, "required_tus": len(requested),
                                    "authenticated_tus": len(covered[side]), "requested_owners": None}
    receipt, evidence = make_receipt(repo,binding,candidate,document["pins"]["policy_sha256"],
                                    reports["candidate"],reports["parent"],
                                    scope_complete=scope_complete and received==expected_shards,
                                    direct_parent=True)
    return receipt, evidence, report_text(receipt, evidence)
