"""Check exact declaration keys from protected VC7.1 compiler probes."""

import hashlib
import re
import struct
from collections import defaultdict
from pathlib import PurePosixPath


RVA = re.compile(r"0x[0-9a-fA-F]{1,8}")
SHA256 = re.compile(r"[0-9a-f]{64}")
GIT_ID = re.compile(r"[0-9a-f]{40}")
PLAIN_NAME = re.compile(r"(?:[A-Za-z_]\w*::)*~?[A-Za-z_]\w*", re.ASCII)
WORD = re.compile(r"[A-Za-z_]\w*", re.ASCII)
MANGLED = re.compile(r"\?[\x21-\x7e]+", re.ASCII)
PRIMITIVE_TEMPLATE_CTOR = re.compile(r"\?\?0\?\$([A-Za-z_]\w*)@([DG])@@", re.ASCII)
PRIMITIVE = {"D": "char", "G": "unsigned short"}
PRIMITIVE_TEMPLATE_FAMILY = re.compile(r"([A-Za-z_]\w*)<(?:char|unsigned short)>::\1", re.ASCII)


class Unobserved(ValueError):
    """The probe cannot establish a requested identity."""


def rva(value):
    if not isinstance(value, str) or not RVA.fullmatch(value) or int(value, 16) == 0:
        raise ValueError(f"invalid RVA {value!r}")
    return f"0x{int(value, 16):08X}"


def sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def canonical_header(value):
    if not isinstance(value, str):
        raise ValueError("header path is missing")
    path = PurePosixPath(value)
    if (str(path) != value or len(path.parts) < 2 or path.parts[0] != "include"
            or any(not re.fullmatch(r"[A-Za-z0-9_.+-]+", p) or p == ".." for p in path.parts)):
        raise ValueError(f"unsupported header path {value!r}")
    return value


def plain_family(symbol):
    """Qualified family for ordinary VC7 symbols.

    Also admit a global one-parameter char or unsigned-short constructor
    specialization. Other template members, operators and local classes hold.
    """
    specialization = PRIMITIVE_TEMPLATE_CTOR.match(symbol)
    if specialization:
        owner, primitive = specialization.groups()
        return f"{owner}<{PRIMITIVE[primitive]}>::{owner}"
    scope, marker, _ = symbol.partition("@@")
    if not marker or not scope.startswith("?"):
        return None
    names = scope[1:].split("@")
    if names[0].startswith(("?0", "?1")):
        short = names[0][2:]
        names[0] = short
        member = short if scope.startswith("??0") else "~" + short
    else:
        member = names.pop(0)
    if not all(WORD.fullmatch(part) for part in names):
        return None
    qualified = "::".join([*reversed(names), member])
    return qualified if PLAIN_NAME.fullmatch(qualified) else None


def verify_object(receipt, pin, header, obj):
    """Bind observed bytes to a protected compile request and input inventory."""
    canonical_header(header)
    keys = ("tree", "compiler_sha256", "profile_sha256", "probe_sha256")
    for key in (*keys, "header_sha256"):
        pattern = GIT_ID if key == "tree" else SHA256
        if not pattern.fullmatch(pin.get(key, "")):
            raise ValueError(f"{header}: invalid protected {key} pin")
    for key in keys:
        if receipt.get(key) != pin[key]:
            raise Unobserved(f"{header}: compile receipt has a different {key}")
    if type(receipt.get("exit")) is not int or receipt["exit"] != 0:
        raise Unobserved(f"{header}: probe did not compile")
    files = receipt.get("input_sha256")
    if not isinstance(files, dict) or files.get(header) != pin["header_sha256"]:
        raise Unobserved(f"{header}: compile did not bind the expected header bytes")
    if not obj or receipt.get("object_sha256") != sha256(obj):
        raise Unobserved(f"{header}: compile object does not match the receipt")


def defined_external_symbols(obj):
    """Yield external definitions in ordinary i386 COFF, with bounded reads."""
    if len(obj) < 20:
        raise Unobserved("COFF file is truncated")
    machine, sections, _, table, count, opt_size, _ = struct.unpack_from("<HHIIIHH", obj)
    if machine != 0x14C or not sections or opt_size:
        raise Unobserved("probe object is not i386 COFF")
    end = table + 18 * count
    if table < 20 + 40 * sections or end + 4 > len(obj):
        raise Unobserved("COFF symbol table is truncated")
    str_end = end + struct.unpack_from("<I", obj, end)[0]
    if not end + 4 <= str_end <= len(obj):
        raise Unobserved("COFF string table is truncated")
    index = 0
    while index < count:
        entry = table + 18 * index
        aux = obj[entry + 17]
        if index + aux >= count:
            raise Unobserved("COFF auxiliary record is truncated")
        section, storage = struct.unpack_from("<h2xB", obj, entry + 12)
        if storage == 2 and 0 < section <= sections:
            name = obj[entry:entry + 8]
            if name[:4] == b"\0" * 4:
                start = end + struct.unpack_from("<I", name, 4)[0]
                if not end + 4 <= start < str_end:
                    raise Unobserved("COFF symbol string offset is invalid")
                stop = obj.find(b"\0", start, str_end)
                if stop < 0:
                    raise Unobserved("COFF symbol string is unterminated")
                name = obj[start:stop]
            else:
                name = name.rstrip(b"\0")
            yield name.decode("latin-1")
        index += 1 + aux


def observed_symbol(qualified, plain, probe):
    """Select one new definition for an independently inventoried declaration."""
    if not (PLAIN_NAME.fullmatch(qualified) or PRIMITIVE_TEMPLATE_FAMILY.fullmatch(qualified)):
        raise Unobserved(f"{qualified}: no compiler locator for this declaration class")
    before = set(defined_external_symbols(plain))
    after = set(defined_external_symbols(probe))
    keys = sorted(key for key in after - before if plain_family(key) == qualified)
    if len(keys) != 1:
        raise Unobserved(f"{qualified}: expected one new COFF definition, found {len(keys)}")
    return keys[0]


def _placeholder(row):
    if row.get("name_evidence") == "?:placeholder":
        return True
    name = row.get("name", "")
    marker = r"(?:[Rr]va[0-9A-Fa-f]{6,}|sub_[0-9A-Fa-f]+)"
    if re.match(r"^\??" + marker, name):
        return True
    # A placeholder class can be part of a decorated constructor or member
    # identity. Restrict the check to the name, before argument type encodings.
    family = plain_family(name)
    return family is not None and any(re.fullmatch(marker, part)
                                      for part in family.split("::"))


def index_ledger(map_doc, symbols_doc):
    """Index code keys and independently proved data keys in the pinned sidecar."""
    if symbols_doc.get("map_snapshot") != map_doc.get("snapshot") or not map_doc.get("snapshot"):
        raise ValueError("code map and symbol sidecar snapshot differ")
    entries, by_key, by_family = {}, defaultdict(set), defaultdict(set)

    def record(addr, names, placeholder=False):
        addr = rva(addr)
        entry = entries.setdefault(addr, {"keys": set(), "unproved_keys": set(), "placeholder": placeholder})
        if entry["placeholder"] != placeholder:
            raise ValueError(f"{addr}: conflicting row identity")
        for name in names:
            if MANGLED.fullmatch(name):
                entry["keys"].add(name)
                by_key[name].add(addr)
                family = plain_family(name)
                if family:
                    by_family[family].add(addr)

    for row in map_doc["rows"]:
        record(row["rva"], {row["name"], *row.get("accepted_names", ())}, _placeholder(row))
    for item in symbols_doc["data_items"]:
        entries.setdefault(rva(item["rva"]), {"keys": set(), "unproved_keys": set(), "placeholder": True})
    for key, group in symbols_doc["symbols"].items():
        for candidate in group.get("candidates", ()):
            if candidate.get("kind") != "named-data":
                continue
            addr = rva(candidate["rva"])
            if candidate.get("proven") is True:
                current = entries.get(addr)
                if current and not current["keys"]:
                    current["placeholder"] = False
                record(addr, (key,))
            elif MANGLED.fullmatch(key):
                item = entries.setdefault(addr, {"keys": set(), "unproved_keys": set(), "placeholder": True})
                item["unproved_keys"].add(key)
                family = plain_family(key)
                if family:
                    by_family[family].add(addr)
    return entries, by_key, by_family


def check_declaration(qualified, key, ledger, *, cited=None, prior=None):
    """Decide a compiler-emitted key. A prior address requires protected evidence."""
    if ((not PLAIN_NAME.fullmatch(qualified) and not PRIMITIVE_TEMPLATE_FAMILY.fullmatch(qualified))
            or plain_family(key) != qualified):
        raise Unobserved(f"{qualified}: COFF key is not bound to this declaration")
    entries, by_key, by_family = ledger
    explicit = rva(cited) if cited is not None else None
    expected = rva(prior) if prior is not None else None
    exact = by_key.get(key, set())
    fact = {"declaration": qualified, "key": key, "rva": explicit or expected,
            "candidate_rvas": sorted(exact)}

    def result(status, reason):
        return dict(fact, status=status, reason=reason)

    if expected and explicit and expected != explicit:
        return result("refuse", "Declares contradicts the verified before-side row")
    address = explicit or expected
    if address:
        if address not in entries:
            return result("refuse", "Declares cites an address outside the protected ledger")
        if exact and address not in exact:
            return result("refuse", "key is assigned to a different protected address")
        if entries[address]["placeholder"]:
            if entries[address]["unproved_keys"]:
                return result("ledger_request", "the data sidecar lacks a proved binding for this address")
            return result("ledger_request", "protected row has a placeholder identity")
        if address not in exact:
            return result("refuse", "decorated key differs from the cited protected row")
        return result("pass", "exact compiled key at the cited protected address")
    if len(exact) == 1:
        fact["rva"] = next(iter(exact))
        if entries[fact["rva"]]["placeholder"]:
            return result("ledger_request", "protected row has a placeholder identity")
        return result("pass", "unique protected address for the exact compiled key")
    if exact:
        return result("held", "compiled key maps to several addresses; a Declares address is required")
    family = by_family.get(qualified, ())
    fact["candidate_rvas"] = sorted(family)
    unproved = [address for address in family if key in entries[address]["unproved_keys"]]
    if len(unproved) == 1:
        fact["rva"] = unproved[0]
        return result("ledger_request", "the exact key appears only in the unproved data sidecar")
    return result("held", "no exact protected key; a Declares address or ledger request is required")


def measure_declaration(header, qualified, plain, definition):
    """Verify both protected probe inputs, then select their unique new key.

    The protected planner supplies each expected pin independently of the
    compiler receipt. Both invocations must share one tree and profile.
    """
    for field in ("tree", "compiler_sha256", "profile_sha256", "header_sha256"):
        if plain["pin"].get(field) != definition["pin"].get(field):
            raise Unobserved(f"{qualified}: plain and definition input differ in {field}")
    for item in (plain, definition):
        verify_object(item["receipt"], item["pin"], header, item["object"])
    if plain["pin"]["probe_sha256"] == definition["pin"]["probe_sha256"]:
        raise Unobserved(f"{qualified}: the definition probe has no source change")
    return observed_symbol(qualified, plain["object"], definition["object"])


def evaluate_declaration(header, qualified, ledger, candidate, *, base=None, cited=None):
    """Run H2 over trusted probe records. Report an unobservable row by name."""
    try:
        key = measure_declaration(header, qualified, *candidate)
        prior = None
        if base is not None:
            before = measure_declaration(header, qualified, *base)
            prior_report = check_declaration(qualified, before, ledger)
            if prior_report["status"] == "held" and cited is not None:
                prior_report = check_declaration(qualified, before, ledger, cited=cited)
            if prior_report["status"] == "pass":
                prior = prior_report["rva"]
            elif before != key:
                return {"declaration": qualified, "status": "held", "key": key, "base_key": before,
                        "reason": "changed declaration has no verified before-side address"}
        return check_declaration(qualified, key, ledger, cited=cited, prior=prior)
    except Unobserved as exc:
        return {"declaration": qualified, "status": "held", "reason": str(exc)}
