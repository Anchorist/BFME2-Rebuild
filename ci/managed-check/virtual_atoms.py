"""Join authenticated candidate-derived vftable effects without uploading raw COFF."""

from collections import defaultdict
from hashlib import sha256
import re
import json
from pathlib import Path
import struct

from managed_inline import BASELINE, CATALOGUE, INLINE, report_text
from compact_matrix import assignment_table
from gitrepo import Git
from managed_matrix import SIDES
from pool_protocol import check_object
from wide_plan import identity, key
from common import REPO_ID

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
            witnesses = []
            tables, bodies = gate.collect_one(COFF(path), witnesses=witnesses)
        except (IndexError, KeyError, OSError, TypeError, ValueError, struct.error):
            records.append(entry | {"unavailable": "compiler object could not be decoded"})
            continue
        records.append(entry | {"tables": tables, "bodies": [[name,effect_wire(effect)] for name,effect in bodies],
                                "body_witnesses": [list(witness) for witness in sorted(set(witnesses))]})
    return {"shard": compiler["shard"], "compiler_plan": compiler["plan_sha256"], "records": records}


def protected_targets(repo, revision, catalogue, material_paths):
    by_address = defaultdict(set)
    for table, info in catalogue["tables"].items():
        for rva in info["slots"]:
            by_address[rva].add(table)
    owner_map = json.loads(Git(repo).run("show", f"{revision}:config/map.json").stdout)
    modified = set(material_paths)
    owners = {item["object_id"] for item in owner_map["objects"] if item.get("tu") in modified}
    contracts, by_symbol, required = defaultdict(set), defaultdict(set), set()
    for row in owner_map["rows"]:
        address = int(row["rva"], 16)
        if address not in by_address:
            continue
        if row.get("object") in owners:
            required.update(by_address[address])
        names = (row["name"], *row["accepted_names"])
        for name in names:
            by_symbol[name].update(by_address[address])
            if contract := gate.return_contract(name):
                contracts[address].add(contract)
    types = {rva: next(iter(known)) for rva, known in contracts.items() if len(known) == 1}
    return types, by_symbol, required


def witness_chain(symbol, bodies, witnesses, seen=()):
    """Retain exact defined owner, body and relocations, following bounded measured tails."""
    if symbol in gate.PURE_NAMES:
        return (("pure", symbol),)
    if symbol in seen or len(seen) >= 4:
        return None
    seen = (*seen, symbol)
    options = witnesses.get(symbol, {})
    effects = bodies.get(symbol, {})
    if len(options) != 1 or len(effects) != 1:
        return None
    [(body_sha, owners)] = options.items()
    [(effect, providers)] = effects.items()
    # Equal bytes and relocation names do not bind the providers reached by
    # an undecoded body. A decoded tail can still prove its target below.
    if effect is None or owners != providers:
        return None
    proof = ((symbol, body_sha, tuple(sorted(owners))),)
    if isinstance(effect, gate.Tail):
        tail = witness_chain(effect.name, bodies, witnesses, seen)
        if tail is None:
            return None
        proof += tail
    return proof


def table_scope(catalog, mappings, witnesses, explicitly_required=(), *, native_owners=None):
    """Identify concrete table changes and slots with complete retained body identity."""
    before, after = (mappings[side] for side in ("parent", "candidate"))
    required, retained = set(explicitly_required), set()
    old_defs, new_defs = witnesses["parent"], witnesses["candidate"]
    old_effects, new_effects = before[1], after[1]
    changed = {name for name in old_defs.keys() | new_defs.keys() | old_effects.keys() | new_effects.keys()
               if old_defs.get(name) != new_defs.get(name) or old_effects.get(name) != new_effects.get(name)}
    # An undecoded terminal keeps both witness chains absent even if its
    # emitted body changed. Its observed callers still select their tables.
    callers = {}
    for bodies in (old_effects, new_effects):
        for name, effects in bodies.items():
            for effect in effects:
                if isinstance(effect, gate.Tail):
                    callers.setdefault(effect.name, set()).add(name)
    pending = list(changed)
    while pending:
        for caller in callers.get(pending.pop(), ()):
            if caller not in changed:
                changed.add(caller)
                pending.append(caller)
    for symbol in changed:
        required.update((native_owners or {}).get(symbol, ()))
    for table in before[0].keys() | after[0].keys():
        old, new = before[0].get(table, {}), after[0].get(table, {})
        if old != new:
            required.add(table)
        if len(old) != 1 or len(new) != 1:
            continue
        old_slots, new_slots = next(iter(old)), next(iter(new))
        targets = catalog["tables"].get(table, {}).get("slots", [])
        for ordinal, (old_symbol, symbol) in enumerate(zip(old_slots, new_slots)):
            if symbol is None or old_symbol != symbol:
                continue
            a = witness_chain(symbol, before[1], witnesses["parent"])
            b = witness_chain(symbol, after[1], witnesses["candidate"])
            # Compare the emitted provider identity even when neither
            # side can decode a complete retained body.
            if symbol in changed or a != b:
                required.add(table)
            elif a is not None and ordinal < len(targets):
                retained.add((table, ordinal, targets[ordinal]))
    return required, retained


def evaluate(document, atoms, *, expected, repo, candidate, baseline, scope_complete, required_tables=(),
             source_scope=None):
    if identity(document) != expected:
        raise ValueError("Virtual portions carry the wrong managed plan.")
    baseline = Path(baseline)
    catalogue = INLINE / "catalogue-audited.json"
    if sha256(baseline.read_bytes()).hexdigest() != BASELINE or sha256(catalogue.read_bytes()).hexdigest() != CATALOGUE:
        raise ValueError("Managed virtual reference or catalogue differs from the protected policy.")
    pe, catalog = PE(baseline), json.loads(catalogue.read_bytes())
    mappings = {side: gate.collections() for side in SIDES.values()}
    covered = {side: set() for side in SIDES.values()}
    witnesses = {side: defaultdict(lambda: defaultdict(set)) for side in SIDES.values()}
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
            for name, checksum in item.get("body_witnesses", ()):
                if (not isinstance(name, str) or not 0 < len(name) < 8192
                        or not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-f]{64}", checksum)):
                    raise ValueError("Managed virtual body witness is malformed.")
                witnesses[side][name][checksum].add(tu)
            covered[side].add(tu)
        if requested:
            raise ValueError("Managed virtual shard omitted compile outcomes.")
    binding = document["partition"]["binding"]
    reports, parent_slots = {}, {}
    source_scope = source_scope or {"equivalent": [], "material": [],
                                    "complete": False}
    return_types, native_owners, path_tables = protected_targets(
        repo, binding["base"], catalog, source_scope["material"])
    selected, retained = table_scope(catalog, mappings, witnesses, set(required_tables) | path_tables,
                                     native_owners=native_owners)
    selection = {
        "repository": REPO_ID, **binding, "matrix": expected,
        "compiler_profile": document["pins"]["profile_sha256"], "intake": document["scope_sha256"],
        "tables": sorted(selected), "source_scope": source_scope,
    }
    for side,pin in (("parent", binding["base"]), ("candidate", candidate)):
        requested = document["instructions"][side]
        reported = gate.scan_collected(
            pe, catalog, *mappings[side], None, holes[side], keep_comparable=True, return_types=return_types,
            parent_slots=parent_slots if side == "candidate" else None,
            scanned_slots=parent_slots if side == "parent" else None,
            required_tables=selected, retained_slots=retained,
        )
        contextual = [
            hole for hole in reported["coverage_holes"]
            if gate.TABLE.fullmatch(hole[0]) and hole[0] not in selected
            and (hole[1] in {"no independently bound native table", "multiple emitted vftable topologies"}
                 or hole[1].startswith("emitted length "))
        ]
        reported["coverage_holes"][:] = [hole for hole in reported["coverage_holes"] if hole not in contextual]
        reports[side] = reported | {"context_table_holes": contextual,
                                    "typed_scope": selection,
                                    "pin": pin, "required_tus": len(requested),
                                    "authenticated_tus": len(covered[side]), "requested_owners": None}
    receipt, evidence = make_receipt(repo,binding,candidate,document["pins"]["policy_sha256"],
                                    reports["candidate"],reports["parent"],
                                    scope_complete=(scope_complete and source_scope["complete"]
                                                    and received == expected_shards),
                                    direct_parent=True)
    return receipt, evidence, report_text(receipt, evidence)
