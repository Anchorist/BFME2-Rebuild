#!/usr/bin/env python3
"""Audit 1.5 compiled table-owner reader.

Derives primary and secondary MSVC vftable bindings and slot topologies per
qualified class owner directly from authenticated COFF objects (or from
virtual_atoms.collect records produced inside the isolated compiler shard).

Never reads headers to guess vftable names and never accepts unauthenticated
objects. Feeds directly into inline_owner_scope.select_owner_scope().
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import re
import struct
from typing import Iterable

TABLE_RE = re.compile(r"^\?\?_7(.+)@@6([BE])(.*)@$")
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\Z")
IMAGE_SCN_LNK_NRELOC_OVFL = 0x01000000
IMAGE_REL_I386_DIR32 = 0x0006


def decode_vftable_symbol(symbol: str) -> dict | None:
    """Parse an MSVC vftable decorated name into owner and primary/secondary kind.

    Returns None if SYMBOL is not a vftable symbol.
    Returns dict(table, raw_owner, owner, owner_status, kind, subobject).
    owner_status is one of:
      - 'qualified': plain or nested/namespaced C++ owner (e.g. 'AI', 'HLodClass::ModelArrayClass')
      - 'template':  MSVC template specialization owner (contains '?$'); owner is None (requires explicit binding)
      - 'undecodable': local/anonymous/backref/unexpected mangling; fails closed when bound
    """
    m = TABLE_RE.fullmatch(symbol)
    if not m:
        return None
    raw_owner, tag, sub = m.group(1), m.group(2), m.group(3)
    kind = "primary" if sub == "" else "secondary"
    subobject = None
    if sub:
        # Secondary vftable suffix is reversed '@'-separated base path ending with '@'
        sub_parts = [p for p in sub.rstrip("@").split("@") if p]
        subobject = "::".join(reversed(sub_parts)) if sub_parts else sub
    if "?$" in raw_owner:
        return {
            "table": symbol,
            "raw_owner": raw_owner,
            "owner": None,
            "owner_status": "template",
            "kind": kind,
            "subobject": subobject,
            "tag": tag,
        }
    parts = raw_owner.split("@")
    if all(IDENT_RE.fullmatch(p) for p in parts):
        owner = "::".join(reversed(parts))
        status = "qualified"
    else:
        owner = None
        status = "undecodable"
    return {
        "table": symbol,
        "raw_owner": raw_owner,
        "owner": owner,
        "owner_status": status,
        "kind": kind,
        "subobject": subobject,
        "tag": tag,
    }


def _read_coff_vftables(data: bytes) -> list[dict]:
    """Parse COFF vftable definitions and their DIR32 slot targets, handling extended relocations."""
    if len(data) < 20:
        raise ValueError("COFF object is truncated before header.")
    machine, nsec, _ts, sym_off, nsym, opt_size, _chars = struct.unpack_from("<HHIIIHH", data, 0)
    if machine != 0x014C or opt_size != 0:
        raise ValueError(f"Unsupported COFF header (machine=0x{machine:04x}, opt={opt_size}).")
    sec_off = 20
    if sec_off + nsec * 40 > len(data):
        raise ValueError("COFF section table exceeds object length.")
    str_off = sym_off + nsym * 18
    if sym_off == 0 or str_off + 4 > len(data):
        raise ValueError("COFF symbol/string table missing or truncated.")
    str_size = struct.unpack_from("<I", data, str_off)[0]
    if str_off + str_size > len(data):
        raise ValueError("COFF string table exceeds object length.")

    def sym_name(off: int) -> str:
        raw = data[off:off + 8]
        z, ptr = struct.unpack_from("<II", raw, 0)
        if z == 0:
            end = data.find(b"\x00", str_off + ptr, str_off + str_size)
            if end < 0:
                raise ValueError("Unterminated COFF string table entry.")
            return data[str_off + ptr:end].decode("latin1")
        return raw.split(b"\x00", 1)[0].decode("latin1")

    sections = []
    for i in range(nsec):
        o = sec_off + i * 40
        _nm, _vs, _va, raw_sz, raw_ptr, rel_ptr, _ln, nrel, _nln, flags = struct.unpack_from("<8sIIIIIIHHI", data, o)
        sections.append({
            "index": i + 1,
            "raw_size": raw_sz,
            "raw_ptr": raw_ptr,
            "rel_ptr": rel_ptr,
            "nrel": nrel,
            "flags": flags,
        })

    symbols: dict[int, dict] = {}
    i = 0
    while i < nsym:
        o = sym_off + i * 18
        name = sym_name(o)
        value, sec_num, _typ, storage, naux = struct.unpack_from("<IhHBB", data, o + 8)
        symbols[i] = {"name": name, "value": value, "section": sec_num, "storage": storage}
        i += 1 + naux

    def section_relocs(sec: dict) -> list[tuple[int, str, int]]:
        if sec["rel_ptr"] == 0 and sec["nrel"] == 0:
            return []
        count = sec["nrel"]
        first = 0
        if sec["flags"] & IMAGE_SCN_LNK_NRELOC_OVFL:
            if sec["rel_ptr"] + 10 > len(data):
                raise ValueError("COFF overflow relocation entry truncated.")
            count = struct.unpack_from("<I", data, sec["rel_ptr"])[0]
            first = 1
        if sec["rel_ptr"] + count * 10 > len(data):
            raise ValueError("COFF relocation table exceeds object length.")
        out = []
        for k in range(first, count):
            roff, sym_idx, rtype = struct.unpack_from("<IIH", data, sec["rel_ptr"] + k * 10)
            if sym_idx not in symbols:
                raise ValueError(f"COFF relocation references missing symbol index {sym_idx}.")
            out.append((roff, symbols[sym_idx]["name"], rtype))
        return out

    # Group defined symbols by section to bound each vftable's extent when multiple sit in one section
    defined_in_sec: dict[int, list[int]] = defaultdict(list)
    for sym in symbols.values():
        if sym["section"] > 0 and sym["storage"] in (2, 3):
            defined_in_sec[sym["section"]].append(sym["value"])
    for vals in defined_in_sec.values():
        vals.sort()

    results = []
    reloc_cache: dict[int, list[tuple[int, str, int]]] = {}
    for sym in symbols.values():
        if sym["section"] <= 0 or sym["storage"] not in (2, 3):
            continue
        parsed = decode_vftable_symbol(sym["name"])
        if parsed is None:
            continue
        sec = sections[sym["section"] - 1]
        start = sym["value"]
        later = [v for v in defined_in_sec[sym["section"]] if v > start]
        end = later[0] if later else sec["raw_size"]
        if sec["index"] not in reloc_cache:
            reloc_cache[sec["index"]] = section_relocs(sec)
        slot_relocs = []
        for roff, target, rtype in reloc_cache[sec["index"]]:
            if start <= roff < end:
                if rtype != IMAGE_REL_I386_DIR32 or (roff - start) % 4 != 0:
                    raise ValueError(f"Unexpected vftable relocation in {sym['name']} at +{roff - start} (type {rtype}).")
                slot_relocs.append(((roff - start) // 4, target))
        slot_relocs.sort()
        # Require contiguous slots 0..N-1 (no gap, no duplicate slot index)
        slots = []
        for idx, (slot_i, target) in enumerate(slot_relocs):
            if slot_i != idx:
                raise ValueError(f"Non-contiguous vftable slots in {sym['name']}: expected slot {idx}, found {slot_i}.")
            slots.append(target)
        results.append({
            **parsed,
            "slots": tuple(slots),
            "slot_count": len(slots),
        })
    return results


def extract_from_coff(
    coff_bytes: bytes,
    *,
    tu: str,
    expected_sha256: str,
    verifier=None,
) -> dict:
    """Extract vftable records from one authenticated COFF object.

    VERIFY: sha256 (or pool_protocol.check_object if supplied via verifier) must equal expected_sha256.
    """
    actual = verifier(coff_bytes) if verifier is not None else hashlib.sha256(coff_bytes).hexdigest()
    if actual != expected_sha256:
        raise ValueError(f"COFF digest mismatch for {tu}: expected {expected_sha256}, got {actual}.")
    tables = _read_coff_vftables(coff_bytes)
    return {
        "tu": tu,
        "object_sha256": actual,
        "tables": tables,
    }


def extract_from_virtual_atoms(records: Iterable[dict]) -> list[dict]:
    """Convert virtual_atoms.collect records (from isolated compiler shards) into table observations."""
    out = []
    for rec in records:
        tu = rec["tu"]
        if "unavailable" in rec:
            out.append({"tu": tu, "unavailable": rec["unavailable"], "tables": []})
            continue
        parsed_tables = []
        for name, slots in rec.get("tables", []):
            parsed = decode_vftable_symbol(name)
            if parsed is None:
                continue
            slot_tuple = tuple(slots)
            parsed_tables.append({
                **parsed,
                "slots": slot_tuple,
                "slot_count": len(slot_tuple),
            })
        out.append({"tu": tu, "tables": parsed_tables})
    return out


def build_side_tables(observations: Iterable[dict], *, protected_tables: Iterable[str]) -> dict:
    """Aggregate compiled vftables across all TUs on one side (parent or candidate).

    Any unavailable TU, undecodable vftable owner, or cross-TU vftable topology conflict
    marks complete=False so the downstream selector fails closed (holds).
    """
    catalogue = set(protected_tables)
    holes: list[dict] = []
    conflicts: list[dict] = []
    by_table: dict[str, dict] = {}
    by_owner: dict[str, set[str]] = defaultdict(set)
    template_tables: dict[str, set[str]] = defaultdict(set)

    for obs in observations:
        tu = obs["tu"]
        if "unavailable" in obs:
            holes.append({"tu": tu, "reason": str(obs["unavailable"])})
            continue
        for t in obs.get("tables", []):
            name = t["table"]
            slots = tuple(t["slots"])
            if t["owner_status"] == "undecodable":
                holes.append({"tu": tu, "table": name, "reason": "undecodable vftable owner mangling"})
                continue
            rec = by_table.get(name)
            if rec is None:
                by_table[name] = {
                    "table": name,
                    "raw_owner": t["raw_owner"],
                    "owner": t["owner"],
                    "owner_status": t["owner_status"],
                    "kind": t["kind"],
                    "subobject": t["subobject"],
                    "slots": list(slots),
                    "slot_count": len(slots),
                    "protected": name in catalogue,
                    "tus": [tu],
                }
            else:
                if tuple(rec["slots"]) != slots:
                    conflicts.append({
                        "table": name,
                        "tus": sorted(set(rec["tus"] + [tu])),
                        "reason": "conflicting vftable topologies across TUs",
                        "slot_counts": [rec["slot_count"], len(slots)],
                    })
                if tu not in rec["tus"]:
                    rec["tus"].append(tu)
                    rec["tus"].sort()
            if t["owner_status"] == "qualified":
                by_owner[t["owner"]].add(name)
            elif t["owner_status"] == "template":
                template_tables[t["raw_owner"]].add(name)

    owners_out = {}
    for owner, tnames in sorted(by_owner.items()):
        prot = sorted(t for t in tnames if t in catalogue)
        unprot = sorted(t for t in tnames if t not in catalogue)
        owners_out[owner] = {
            "tables": sorted(tnames),
            "protected_tables": prot,
            "unprotected_tables": unprot,
        }

    return {
        "complete": not holes and not conflicts,
        "owners": owners_out,
        "template_tables": {k: sorted(v) for k, v in sorted(template_tables.items())},
        "tables": by_table,
        "holes": holes,
        "conflicts": conflicts,
    }


def bind_inventory_side(
    declaration_side: dict,
    side_tables: dict,
    *,
    protected_tables: Iterable[str],
    require_all_compiled_owners: bool = False,
) -> tuple[dict, dict]:
    """Attach compiled primary + secondary protected vftables to a declaration inventory side.

    Returns (bound_side_for_selector, audit_report).
    Raises ValueError if a declaration lies (polymorphic=False when COFF emits a vftable for it).
    Sets complete=False (forcing select_owner_scope to hold) when:
      - declaration_side['complete'] is not True, or
      - side_tables['complete'] is not True (unavailable TU, undecodable owner, or topology conflict), or
      - require_all_compiled_owners is True and a compiled qualified protected owner is absent from classes.
    """
    catalogue = set(protected_tables)
    compiled_owners = side_tables["owners"]
    declared_names = set()
    bound_classes = []
    unprotected_on_declared: dict[str, list[str]] = {}

    for row in declaration_side["classes"]:
        owner = row["owner"]
        declared_names.add(owner)
        comp = compiled_owners.get(owner)
        emitted_all = comp["tables"] if comp else []
        emitted_prot = [t for t in (comp["protected_tables"] if comp else []) if t in catalogue]
        emitted_unprot = comp["unprotected_tables"] if comp else []
        if emitted_all and row["polymorphic"] is False:
            raise ValueError(
                f"Declaration inventory marks {owner} non-polymorphic, but compiled COFF emits {emitted_all}."
            )
        if emitted_unprot:
            unprotected_on_declared[owner] = list(emitted_unprot)
        bound_classes.append({
            "owner": owner,
            "declarations": row["declarations"],
            "bases": list(row["bases"]),
            "polymorphic": row["polymorphic"],
            "tables": sorted(emitted_prot),
        })

    omitted_protected_owners = sorted(
        owner for owner, info in compiled_owners.items()
        if info["protected_tables"] and owner not in declared_names
    )
    complete = (
        declaration_side.get("complete") is True
        and side_tables["complete"] is True
        and (not require_all_compiled_owners or not omitted_protected_owners)
    )
    bound_side = {
        "tree": declaration_side["tree"],
        "complete": complete,
        "paths": list(declaration_side["paths"]),
        "classes": bound_classes,
    }
    report = {
        "complete": complete,
        "holes": list(side_tables["holes"]),
        "conflicts": list(side_tables["conflicts"]),
        "omitted_protected_owners": omitted_protected_owners,
        "unprotected_on_declared": unprotected_on_declared,
    }
    return bound_side, report


def build_scope_packet(
    *,
    binding: dict,
    parent_decl: dict,
    candidate_decl: dict,
    parent_tables: dict,
    candidate_tables: dict,
    protected_tables: Iterable[str],
) -> tuple[dict, dict]:
    """Assemble the full version=1 packet for inline_owner_scope.select_owner_scope.

    Additionally checks whether any compiled protected owner NOT in the declaration inventory
    changed its emitted vftables or slot topologies between parent and candidate; if so,
    forces complete=False on candidate so select_owner_scope holds instead of missing a changed class.
    """
    parent_side, parent_rep = bind_inventory_side(parent_decl, parent_tables, protected_tables=protected_tables)
    cand_side, cand_rep = bind_inventory_side(candidate_decl, candidate_tables, protected_tables=protected_tables)

    # Catch any omitted polymorphic owner whose compiled vftable set or slots changed across the PR
    declared_either = {r["owner"] for r in parent_decl["classes"]} | {r["owner"] for r in candidate_decl["classes"]}
    compiled_either = set(parent_tables["owners"]) | set(candidate_tables["owners"])
    omitted_changed = []
    for owner in sorted(compiled_either - declared_either):
        p_info = parent_tables["owners"].get(owner)
        c_info = candidate_tables["owners"].get(owner)
        p_sig = {t: parent_tables["tables"][t]["slots"] for t in (p_info["protected_tables"] if p_info else [])}
        c_sig = {t: candidate_tables["tables"][t]["slots"] for t in (c_info["protected_tables"] if c_info else [])}
        if p_sig != c_sig:
            omitted_changed.append(owner)

    if omitted_changed:
        cand_side["complete"] = False

    packet = {
        "version": 1,
        "binding": dict(binding),
        "parent": parent_side,
        "candidate": cand_side,
    }
    report = {
        "parent": parent_rep,
        "candidate": cand_rep,
        "omitted_changed_compiled_owners": omitted_changed,
    }
    return packet, report
