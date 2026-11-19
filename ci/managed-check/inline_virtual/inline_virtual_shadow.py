#!/usr/bin/env python3
"""Read-only shadow audit of constant and trivial virtuals in authenticated COFF.

The caller supplies decorated class owners and the landing's complete staged TU
closure. This program never runs a compiler, changes Git state, or fails a landing
on a finding. Unresolved evidence is explicit in the JSON report.
"""
from bisect import bisect_right
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from functools import lru_cache
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

TABLE = re.compile(r"^\?\?_7(.+)@@6[BE].*$")
PURE_NAMES = {"_purecall", "__purecall", "___purecall"}
HASH = re.compile(r"[0-9a-f]{64}")
PIN = re.compile(r"[0-9a-f]{40}")
MAX_BODY = 32


@dataclass(frozen=True)
class Effect:
    kind: str
    value: int | tuple | None
    pop: int
    write: tuple | None = None


@dataclass(frozen=True)
class Tail:
    name: str
    receiver_delta: int


def integer(data):
    return int.from_bytes(data, "little")


def decode(data, exact=True):
    """Small complete x86 leaves. Holds caller-visible writes and stack pop."""
    write = None
    if len(data) >= 6 and data[:2] in (b"\xc7\x01", b"\xc7\x41", b"\xc7\x81"):
        width = {1: 0, 0x41: 1, 0x81: 4}[data[1]]
        stop = 2 + width + 4
        if len(data) < stop:
            return None
        write = (int.from_bytes(data[2:2 + width], "little", signed=True), integer(data[2 + width:stop]))
        data = data[stop:]
    elif len(data) >= 3 and data[0] == 0x83 and data[1] in (0x21, 0x61, 0xa1):
        # MSVC also clears a receiver dword with and [ecx + displacement], 0.
        width = {0x21: 0, 0x61: 1, 0xa1: 4}[data[1]]
        immediate = 2 + width
        if len(data) <= immediate or data[immediate] != 0:
            return None
        write = (int.from_bytes(data[2:immediate], "little", signed=True), 0)
        data = data[immediate + 1:]
    kind, value, i = "void", None, 0
    if data[:2] in (b"\x32\xc0", b"\x30\xc0", b"\x2a\xc0", b"\x28\xc0"):
        kind, value, i = "al", 0, 2
    elif len(data) >= 2 and data[0] == 0xb0:
        kind, value, i = "al", data[1], 2
    elif data[:2] in (b"\x31\xc0", b"\x33\xc0", b"\x29\xc0", b"\x2b\xc0"):
        kind, value, i = "eax", 0, 2
        if data[2:3] == b"\x40":
            value, i = 1, 3
    elif len(data) >= 5 and data[0] == 0xb8:
        kind, value, i = "eax", integer(data[1:5]), 5
    elif data[:3] == b"\x83\xc8\xff":
        kind, value, i = "eax", 0xffffffff, 3
    elif len(data) >= 3 and data[0] == 0x6a and data[2] == 0x58:
        kind, value, i = "eax", int.from_bytes(data[1:2], "little", signed=True) & 0xffffffff, 3
    elif data[:2] in (b"\xd9\xee", b"\xd9\xe8"):
        kind, value, i = "x87", int(data[1] == 0xe8), 2
    elif data[:2] in (b"\x8b\xc1", b"\x89\xc8"):
        kind, value, i = "this", 0, 2
    elif data[:2] in (b"\x8d\x41", b"\x8d\x81"):
        size = 1 if data[1] == 0x41 else 4
        if len(data) < 2 + size:
            return None
        kind, value, i = "this", int.from_bytes(data[2:2 + size], "little", signed=True), 2 + size
    elif data[:2] in (b"\x8b\x01", b"\x8b\x41", b"\x8b\x81",
                       b"\x8a\x01", b"\x8a\x41", b"\x8a\x81"):
        size = {0x01: 0, 0x41: 1, 0x81: 4}[data[1]]
        if len(data) < 2 + size:
            return None
        width = 8 if data[0] == 0x8a else 32
        kind, value, i = "read", (width, int.from_bytes(data[2:2 + size], "little", signed=True)), 2 + size
    if data[i:i + 1] == b"\xc3":
        pop, end = 0, i + 1
    elif data[i:i + 1] == b"\xc2" and len(data) >= i + 3:
        pop, end = integer(data[i + 1:i + 3]), i + 3
    else:
        return None
    if exact and end != len(data):
        return None
    return Effect(kind, value, pop, write)


def return_width(name):
    # Public/protected/private ordinary virtual thiscall signatures only.
    # Adjustment thunks have different decoration; leave that inference open.
    match = re.search(r"@@[EMU][A-D]E([_A-Z])", name)
    if not match:
        return None
    code = match[1]
    if code == "_" and name[match.end():match.end() + 1] == "N":
        return 8
    if code == "W":
        return {"0": 8, "1": 8, "2": 16, "3": 16, "4": 32, "5": 32}.get(
            name[match.end():match.end() + 1])
    return {"X": 0, "C": 8, "D": 8, "E": 8, "F": 16, "G": 16,
            "H": 32, "I": 32, "J": 32, "K": 32,
            "P": 32, "Q": 32, "R": 32, "S": 32}.get(code)


def compare(ours, native, symbol):
    if ours is None or native is None:
        return "review"
    if ours.kind == "pure" or native.kind == "pure":
        return "same" if ours.kind == native.kind else "mismatch"
    if ours.pop != native.pop or ours.write != native.write:
        return "mismatch"
    width = return_width(symbol)
    if width == 0:
        # Integer register clobber is immaterial to a void virtual, but x87
        # pushes a value onto the caller's floating-point stack.
        return "mismatch" if (ours.kind == "x87") != (native.kind == "x87") else "same"
    if ours.kind == native.kind:
        if ours.kind == "eax" and width in (8, 16):
            mask = (1 << width) - 1
            return "same" if ours.value & mask == native.value & mask else "mismatch"
        return "same" if ours.value == native.value else "mismatch"
    if {ours.kind, native.kind} <= {"al", "eax"}:
        if ours.value & 0xff != native.value & 0xff:
            return "mismatch"
        return "same" if width == 8 else "review"
    if {ours.kind, native.kind} == {"this", "eax"} and width == 32:
        return "mismatch"
    if "read" in (ours.kind, native.kind):
        other = native if ours.kind == "read" else ours
        if other.kind in ("al", "eax") and width in (8, 16, 32):
            return "mismatch"
    return "review"


def tail_prefix(data):
    if data[:2] in (b"\x83\xc1", b"\x83\xe9") and len(data) >= 3:
        step = int.from_bytes(data[2:3], "little", signed=True)
        return 3, -step if data[1] == 0xe9 else step
    if data[:2] in (b"\x81\xc1", b"\x81\xe9") and len(data) >= 6:
        step = int.from_bytes(data[2:6], "little", signed=True)
        return 6, -step if data[1] == 0xe9 else step
    return 0, 0


def adjusted(effect, delta):
    if effect is None or not delta:
        return effect
    value = effect.value
    if effect.kind == "this":
        value += delta
    if effect.kind == "read":
        value = value[0], value[1] + delta
    write = effect.write
    if write:
        write = write[0] + delta, write[1]
    return replace(effect, value=value, write=write)


@lru_cache(maxsize=16384)
def read_image_effect(pe, target, pure_targets):
    seen, total_delta = set(), 0
    for _ in range(4):
        if target in pure_targets:
            return Effect("pure", None, 0)
        if target in seen:
            break
        seen.add(target)
        try:
            extent = pe.section(target, 1)
            if not extent["flags"] & 0x20:
                return None
            end = extent["rva"] + extent["raw_size"]
            if end <= target:
                return None
            raw = pe.read(target, min(MAX_BODY, end - target))
        except ValueError:
            return None
        off, delta = tail_prefix(raw)
        branch = raw[off:]
        if len(branch) >= 5 and branch[0] == 0xe9:
            target += off + 5 + int.from_bytes(branch[1:5], "little", signed=True)
        elif len(branch) >= 2 and branch[0] == 0xeb:
            target += off + 2 + int.from_bytes(branch[1:2], "little", signed=True)
        else:
            return adjusted(decode(raw, exact=False), total_delta)
        total_delta += delta
    return None


def sha256(data):
    return hashlib.sha256(data).hexdigest()


class Commit:
    """Immutable tracked inputs, batched through Git by blob hash."""
    def __init__(self, repo, pin):
        self.repo, self.pin = Path(repo), pin
        if not PIN.fullmatch(pin):
            raise ValueError("scope must name a full commit pin")
        actual = self.git("rev-parse", "--verify", pin + "^{commit}").decode().strip()
        if actual != pin:
            raise ValueError("invalid pinned commit")
        self.paths = {}
        for record in self.git("ls-tree", "-r", "-z", pin).split(b"\0"):
            if not record:
                continue
            meta, path = record.split(b"\t", 1)
            mode, kind, oid = meta.decode().split()
            if kind == "blob" and mode in ("100644", "100755"):
                self.paths[path.decode("utf-8")] = oid

    def git(self, *args, input=None):
        return subprocess.check_output(["git", "--git-dir", str(self.repo), *args], input=input)

    def digests(self, paths):
        wanted = {self.paths[path] for path in paths if path in self.paths}
        if not wanted:
            return {}
        cmd = b"".join(oid.encode() + b"\n" for oid in sorted(wanted))
        output = self.git("cat-file", "--batch", input=cmd)
        pos, result = 0, {}
        while pos < len(output):
            end = output.index(b"\n", pos)
            oid, kind, size = output[pos:end].decode().split()
            if kind != "blob" or oid not in wanted or oid in result:
                raise ValueError("unexpected Git blob while validating receipt")
            end += 1
            pos = end + int(size)
            result[oid] = sha256(output[end:pos])
            if output[pos:pos + 1] != b"\n":
                raise ValueError("invalid Git blob extent")
            pos += 1
        if set(result) != wanted:
            raise ValueError("incomplete Git blob read")
        return {path: result[self.paths[path]] for path in paths if path in self.paths}


@lru_cache(maxsize=8192)
def external_digest(path):
    return sha256(Path(path).read_bytes())


def inputs(repo, manifest, required, contracts, external_roots):
    """Index only source/object certificates belonging to this exact staged pin."""
    pin = manifest["pin"]
    tree = Commit(repo, pin)
    default_root = manifest.get("compile_root")
    if not isinstance(default_root, str) or not default_root:
        raise ValueError("the trusted manifest requires a compile root")
    source_roots = manifest.get("compile_roots", {})
    paths = set(required)
    records, holes = {}, []
    for tu in required:
        artifact = manifest["objects"].get(tu)
        if artifact is None:
            holes.append((tu, "no authenticated candidate object"))
            continue
        obj = Path(artifact)
        try:
            root = Path(source_roots.get(tu, default_root))
            if not root.is_absolute() or ".." in root.parts or len(root.parts) < 4:
                raise ValueError("invalid trusted compile job root")
            prefix = str(root).rstrip("/") + "/"
            receipt = json.loads(obj.with_suffix(".obj.compile.json").read_text())
            accepted_contracts = contracts.get(tu, ()) if isinstance(contracts, dict) else contracts
            if isinstance(accepted_contracts, str):
                accepted_contracts = (accepted_contracts,)
            if receipt["compiler_contract"] not in accepted_contracts or receipt["include_capture"] != "msvc-showIncludes-v1":
                raise ValueError("compiler or include-capture contract differs")
            if receipt["object_sha256"] != sha256(obj.read_bytes()):
                raise ValueError("object digest differs from receipt")
            dependencies = {}
            for absolute, digest in receipt["headers"].items():
                if absolute.startswith(prefix):
                    relative = absolute[len(prefix):]
                    dependencies[relative] = digest
                    paths.add(relative)
                elif any(absolute.startswith(root) for root in external_roots):
                    if not HASH.fullmatch(digest) or external_digest(absolute) != digest:
                        raise ValueError("external compiler header digest differs")
                else:
                    raise ValueError("dependency is outside the pinned candidate tree and compiler roots")
            records[tu] = obj, receipt["source_sha256"], dependencies
        except (OSError, TypeError, KeyError, ValueError) as failure:
            holes.append((tu, str(failure)))
    current = tree.digests(paths)
    accepted = {}
    for tu, (obj, source_digest, dependencies) in records.items():
        if current.get(tu) != source_digest or any(current.get(p) != d for p, d in dependencies.items()):
            holes.append((tu, "tracked source or include does not match pinned commit"))
        else:
            accepted[tu] = obj
    return accepted, holes


def table_cells(coff, index):
    loc = coff.loc(index)
    size = coff.extent(index)
    if not 0 < size <= 16384 or size % 4:
        raise ValueError("invalid emitted table extent")
    data = coff.bytes(loc, size)
    fixups = {}
    for off, kind, target in coff.relocs(loc, size):
        if off in fixups or off % 4:
            raise ValueError("duplicate or misaligned table pointer")
        fixups[off] = kind, target
    slots = []
    for off in range(0, size, 4):
        fixup = fixups.get(off)
        if fixup is None or fixup[0] != 6 or integer(data[off:off + 4]) != 0:
            slots.append(None)
            continue
        name = coff.symbols[fixup[1]].get("name")
        slots.append(name or None)
    return tuple(slots)


def small_bodies(coff):
    """Read complete bounded x86 bodies and unambiguous tail relocations."""
    starts = defaultdict(set)
    functions = []
    for index, symbol in enumerate(coff.symbols):
        section = symbol.get("section", 0)
        if (section <= 0 or not (symbol.get("type", 0) & 32)
                or not coff.sections[section - 1]["characteristics"] & 0x20):
            continue
        name = symbol.get("name", "")
        if name:
            starts[section].add(symbol["value"])
        if (symbol.get("storage") in (2, 3) and name.startswith("?")
                and not name.startswith(("??_E", "??_G", "??_R"))):
            functions.append((index, section, symbol["value"], name))
    sorted_starts = {sec: sorted(offsets) for sec, offsets in starts.items()}
    for index, section, offset, name in functions:
        points = sorted_starts[section]
        at = bisect_right(points, offset)
        end = points[at] if at < len(points) else coff.sections[section - 1]["raw_size"]
        size = end - offset
        if not 0 < size <= MAX_BODY:
            yield name, None
            continue
        loc = coff.loc(index)
        code = coff.bytes(loc, size)
        relocs = coff.relocs(loc, size)
        if not relocs:
            yield name, decode(code)
            continue
        lead, delta = tail_prefix(code)
        branch = code[lead:]
        if (branch == b"\xe9\0\0\0\0" and len(relocs) == 1
                and relocs[0][:2] == (lead + 1, 20)):
            target = coff.symbols[relocs[0][2]].get("name")
            yield name, Tail(target, delta) if target else None
        else:
            yield name, None


def resolve_effect(bodies, symbol, path=()):
    if symbol in PURE_NAMES:
        return {Effect("pure", None, 0): set()}
    if symbol in path or len(path) == 4:
        return {None: set()}
    effects = defaultdict(set)
    for option, witnesses in bodies.get(symbol, {}).items():
        if isinstance(option, Tail):
            resolved = resolve_effect(bodies, option.name, (*path, symbol))
            if not resolved:
                effects[None].update(witnesses)
            for effect, targets in resolved.items():
                effects[adjusted(effect, option.receiver_delta)].update(witnesses | targets)
        else:
            effects[option].update(witnesses)
    return effects


def collect_one(coff, selected=None):
    tables = []
    for index, symbol in enumerate(coff.symbols):
        name = symbol.get("name", "")
        match = TABLE.fullmatch(name)
        if match and symbol.get("section", 0) > 0 and (selected is None or match[1] in selected):
            tables.append((name, table_cells(coff, index)))
    return tables, list(small_bodies(coff))


def collections():
    return (defaultdict(lambda: defaultdict(set)), defaultdict(lambda: defaultdict(set)))


def collect_into(tables, bodies, tu, units, effects):
    for name, slots in units:
        tables[name][slots].add(tu)
    for name, effect in effects:
        bodies[name][effect].add(tu)


def scan(pe, catalog, objects, owners, coff_reader, known=(), keep_comparable=False):
    selected = set(owners) if owners is not None else None
    tables, bodies = collections()
    holes = []
    for tu, path in sorted(objects.items()):
        try:
            collect_into(tables, bodies, tu, *collect_one(coff_reader(path), selected))
        except (IndexError, KeyError, OSError, TypeError, ValueError, struct.error) as problem:
            holes.append((tu, str(problem)))
    return scan_collected(pe, catalog, tables, bodies, selected, holes, known, keep_comparable)


def scan_collected(pe, catalog, tables, bodies, selected, holes, known=(), keep_comparable=False):
    if catalog.get("format", 1) != 1 or catalog["retail_sha256"] != pe.sha256:
        raise ValueError("retail image fingerprint differs from anchor catalogue")
    known = set(known)
    pure = frozenset(catalog.get("pure_targets", []))
    findings, stats, comparable = [], Counter(), []
    observed = {TABLE.fullmatch(table)[1] for table in tables}
    for owner in sorted((selected or set()) - observed):
        holes.append((owner, "no vftable emitted in supplied closure"))
    for table, variants in sorted(tables.items()):
        anchor = catalog["tables"].get(table)
        if len(variants) != 1:
            holes.append((table, "multiple emitted vftable topologies"))
            continue
        if anchor is None:
            holes.append((table, "no independently bound native table"))
            continue
        slots, source_tus = next(iter(variants.items()))
        address, targets = anchor["rva"], anchor["slots"]
        try:
            raw = pe.read(address, len(targets) * 4)
        except ValueError:
            holes.append((table, "native table extent outside image"))
            continue
        if tuple(value - pe.base for (value,) in struct.iter_unpack("<I", raw)) != tuple(targets):
            holes.append((table, "native table contents differ from anchor"))
            continue
        if len(slots) != len(targets):
            holes.append((table, f"emitted length {len(slots)} differs from native {len(targets)}"))
            continue
        stats["bound_tables"] += 1
        stats["cells_in_bound_tables"] += len(targets)
        for ordinal, (symbol, target) in enumerate(zip(slots, targets)):
            if symbol is None:
                stats["unresolved_cells"] += 1
                continue
            opts = resolve_effect(bodies, symbol)
            if len(opts) != 1 or None in opts:
                stats["body_variants" if len(opts) > 1 else "unprofiled_source_cells"] += 1
                continue
            ours, providers = next(iter(opts.items()))
            native = read_image_effect(pe, target, pure)
            status = compare(ours, native, symbol)
            if status == "review":
                stats["unsupported_native_or_abi"] += 1
                continue
            stats["compared_trivial_cells"] += 1
            if keep_comparable:
                comparable.append((table, address, ordinal, target))
            if status == "same":
                continue
            discrepancy = {
                "table": table, "owner": TABLE.fullmatch(table)[1],
                "table_rva": address, "slot": ordinal, "retail_target": target,
                "symbol": symbol, "ours": asdict(ours), "reference": asdict(native),
                "emitters": sorted(source_tus), "providers": sorted(providers),
                "anchor_evidence": anchor["evidence"],
            }
            signature = fingerprint(discrepancy)
            discrepancy["fingerprint"] = signature
            discrepancy["status"] = "known-open" if signature in known else "alert"
            stats[discrepancy["status"]] += 1
            findings.append(discrepancy)
    report = {"owners": sorted(observed), "observations": dict(stats),
              "findings": findings, "coverage_holes": holes}
    if keep_comparable:
        report["comparable"] = comparable
    return report


def mark_parent(candidate, prior):
    """Prior positive witnesses survive incomplete coverage; absence needs comparable proof."""
    previous = {finding["fingerprint"] for finding in prior["findings"]}
    comparable = {tuple(cell) for cell in prior.get("comparable", ())}
    coverage_complete = (isinstance(prior.get("required_tus"), int)
                         and prior["required_tus"] == prior.get("authenticated_tus")
                         and not any(len(hole) >= 1 and str(hole[0]).startswith("src/")
                                     for hole in prior["coverage_holes"]))
    counts = Counter()
    for finding in candidate["findings"]:
        identity = tuple(finding[field] for field in ("table", "table_rva", "slot", "retail_target"))
        if finding["fingerprint"] in previous:
            status = "retained-from-parent"
        elif coverage_complete and identity in comparable:
            status = "changed-from-comparable-parent"
        else:
            status = "prior-unresolved"
        finding["comparison_to_parent"] = status
        counts[status] += 1
    candidate["parent_pin"] = prior.get("pin")
    candidate["parent_observations"] = dict(counts)



def fingerprint(finding):
    fields = ("table", "table_rva", "slot", "retail_target", "symbol", "ours", "reference")
    return sha256(json.dumps({field: finding[field] for field in fields},
                             sort_keys=True, separators=(",", ":")).encode())


def tsv_owners(path):
    return [line.strip() for line in Path(path).read_text().splitlines()
            if line.strip() and not line.startswith("#")]


def shell_main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--retail", required=True)
    parser.add_argument("--owners", required=True, help="one decorated class owner per line")
    parser.add_argument("--tus", required=True, help="complete candidate TU closure, one path per line")
    contracts = parser.add_mutually_exclusive_group(required=True)
    contracts.add_argument("--contract", action="append")
    contracts.add_argument("--contracts-file", help="trusted TU-to-compiler-contract JSON")
    parser.add_argument("--external-root", default=[], action="append")
    parser.add_argument("--known", help="pinned exact-behavior open findings")
    parser.add_argument("--base-manifest")
    parser.add_argument("--base-tus")
    parser.add_argument("--base-contracts-file", help="trusted TU-to-compiler-contract JSON for base")
    args = parser.parse_args()
    from binary_model import COFF, PE
    import build
    manifest = json.loads(Path(args.manifest).read_text())
    catalog = json.loads(Path(args.catalog).read_text())
    selected = tsv_owners(args.owners)
    required = tsv_owners(args.tus)
    if len(selected) != len(set(selected)) or len(required) != len(set(required)):
        raise ValueError("duplicate owner or required TU")
    known = json.loads(Path(args.known).read_text())["fingerprints"] if args.known else []
    expected = json.loads(Path(args.contracts_file).read_text()) if args.contracts_file else set(args.contract)
    pe = PE(args.retail)
    roots = tuple(root.rstrip("/") + "/" for root in args.external_root)

    def inspect(compiled, tus, contract, keep_comparable=False):
        paths, missing = inputs(args.repo, compiled, tus, contract, roots)
        verdict = scan(pe, catalog, paths, selected, lambda path: COFF(path, build), known,
                       keep_comparable=keep_comparable)
        verdict["coverage_holes"] += missing
        verdict["pin"] = compiled["pin"]
        verdict["required_tus"] = len(tus)
        verdict["authenticated_tus"] = len(paths)
        return verdict

    report = inspect(manifest, required, expected)
    report["requested_owners"] = selected
    if args.base_manifest:
        if not args.base_tus or (args.contracts_file and not args.base_contracts_file):
            parser.error("--base-manifest needs --base-tus and, with --contracts-file, --base-contracts-file")
        base = json.loads(Path(args.base_manifest).read_text())
        baseline_paths = tsv_owners(args.base_tus)
        if len(baseline_paths) != len(set(baseline_paths)):
            parser.error("duplicate base TU")
        if not PIN.fullmatch(base["pin"]):
            parser.error("invalid full base pin")
        subprocess.run(["git", "--git-dir", args.repo, "merge-base", "--is-ancestor",
                        base["pin"], manifest["pin"]], check=True)
        baseline_contract = (json.loads(Path(args.base_contracts_file).read_text())
                             if args.base_contracts_file else expected)
        mark_parent(report, inspect(base, baseline_paths, baseline_contract, keep_comparable=True))
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    shell_main()

