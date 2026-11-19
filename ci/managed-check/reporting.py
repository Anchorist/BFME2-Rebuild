"""Public output allowlist. Worker logs and raw comparison records stay private."""
import re

from gitrepo import safe_path
from pool_protocol import DIAGNOSTIC, diagnostic_message
from quality_format import quality_report

ROW = re.compile(r"0x[0-9A-Fa-f]{1,8}\Z")
SYMBOL = re.compile(r"[A-Za-z0-9_?$~:@.,<>() *&+\-/]{1,160}\Z")
INSN = re.compile(r"[A-Za-z0-9_ .%+<>:\[\](),*-]{1,100}\Z")
STATES = {"MATCH", "PARTIAL", "MISSING", "MISNAMED", "WRONG_REFERENCE", "COMPILE_ERROR", "UNKNOWN_RVA", "NONE"}
ERROR = re.compile(r"^(?P<path>[^()\r\n]+)\((?P<line>[1-9]\d{0,6})(?:,(?P<col>[1-9]\d{0,4}))?\)"
                   r"\s*:\s*(?:fatal )?error (?P<code>C\d{4})(?:\s*:|$)", re.I)
MSVC = {
    "C1001": "internal compiler error", "C1026": "parser stack overflow", "C1033": "compiler output error",
    "C1083": "cannot open an include or source file", "C1189": "preprocessor error directive",
    "C1903": "compiler could not recover from earlier errors", "C2001": "newline in a constant",
    "C2011": "type redefinition", "C2027": "use of an undefined type",
    "C2039": "name is not a member of the type", "C2059": "syntax error",
    "C2061": "syntax error near an identifier", "C2065": "undeclared identifier",
    "C2079": "object uses an undefined type", "C2084": "function already has a body",
    "C2129": "static function declared but not defined", "C2143": "expected a token before another token",
    "C2228": "member access requires a class or struct",
    "C2270": "modifiers are disallowed on this nonmember function", "C2440": "type conversion failed",
    "C2504": "base class is undefined", "C2511": "member function declaration does not match",
    "C2555": "override return type differs", "C2660": "wrong number of function arguments",
    "C2664": "cannot convert a function argument", "C2733": "C-linkage function declared more than once",
    "C3861": "identifier not found",
}
GATES = {
    "duplicate class:": "A global class has duplicate definitions. Keep one definition and update its includers.",
    "Draft header re-added:": "This patch re-adds a Draft class with a canonical header. Use the canonical header.",
    "removes the declaration": "A protected declaration was removed. Name it with Removed-Declaration in the tip commit message and explain why.",
    "FUNCTION annotations changed": "FUNCTION annotations changed. Restore the ledger-owned annotations.",
    "wrong reference": "The compiler emitted a different reference. Check operand and type identities.",
    "inline assembly": "Inline assembly requires an approved allowlist entry.",
    "shortcut": "The checker found a banned code-shaping construct.",
    "generator-owned": "The patch touches checker-owned metadata.",
    "new header named like": "Use the real class name for the new header.",
    "duplicate definitions": "The checker found duplicate definitions.",
    "lost proven reference": "A previously proven reference is no longer proven.",
    "lost MATCH (WRONG_REFERENCE)": "An equal-byte body now uses a wrong reference.",
    "adds a body judged PARTIAL": "A newly authored body falls short of an exact match.",
    "defines the placeholder type": "A new type uses a reserved placeholder name.",
    "class/struct with a body defined in a .cpp": "A class definition belongs in a header.",
    "banned construct": "A source construct is outside compiler policy.",
    "removed map-owned row": "The checker no longer sees a ledger-owned body.",
}
RESULTS = {"ok", "regression", "gate", "conflict", "nothing", "pending"}


def status(row, proven):
    if not row or row[0] not in STATES:
        return "NONE"
    return row[0] + (" / proven" if row[0] == "MATCH" and proven else
                     " / unproven" if row[0] == "MATCH" else "")


def numeric(value, limit):
    return value if type(value) is int and 0 <= value <= limit else None


def safe_listing(records):
    return [{"offset": x["offset"], "text": x["text"]} for x in records[:8]
            if numeric(x.get("offset"), 2**31) is not None
            and isinstance(x.get("text"), str) and INSN.fullmatch(x["text"])]

def row_report(path, address, old, new, metadata, was_proven, is_proven, comparison):
    size = numeric(metadata.get("size"), 2**31)
    name = metadata.get("name")
    if not isinstance(name, str) or not SYMBOL.fullmatch(name):
        name = None
    pct = (new or ("NONE", None))[1]
    if type(pct) not in {int, float} or not 0 <= pct <= 100:
        pct = None
    comparison = comparison or {}
    # The trusted judge's MATCH predicate requires equal body lengths.
    matched = bool(new and new[0] == "MATCH")
    if matched:
        pct = 100.0
        if size is not None:
            comparison = {"compiled_size": size, "retail_size": size}
    return {"path": path, "rva": f"0x{int(address, 16):08X}", "name": name, "size": size,
            "old": status(old, was_proven), "new": status(new, is_proven),
            "pct": pct if matched or new and new[0] == "PARTIAL" else None,
            "first": numeric(comparison.get("first"), 2**31) if new and new[0] == "PARTIAL" else None,
            "compiled_size": numeric(comparison.get("compiled_size"), 2**31),
            "retail_size": numeric(comparison.get("retail_size"), 2**31),
            "compiled_listing": safe_listing(comparison.get("compiled_listing", [])),
            "reference_listing": safe_listing(comparison.get("reference_listing", []))}


def diagnostics(raw_results, changed_paths):
    allowed = {path.casefold(): path for path in changed_paths}
    found = {}
    for _tu, result in sorted(raw_results.items()):
        error = result.get("error")
        if not isinstance(error, str):
            continue
        for line in error[:40000].splitlines():
            match = DIAGNOSTIC.fullmatch(line.strip())
            if not match:
                continue
            path, line_no, level, code, message = match.groups()
            path = allowed.get(path.replace(chr(92), "/").removeprefix("./").casefold())
            message = diagnostic_message(message)
            if path and message and 0 < int(line_no) < 10**7 and "error" in level.lower():
                found[(path, int(line_no), code.upper(), message)] = None
    return [{"path": path, "line": number, "code": code, "message": message}
            for path, number, code, message in sorted(found)[:20]]


def measured_rows(rows):
    return {int(key, 16): value for key, value in rows.items() if ROW.fullmatch(key)}


def changed_definitions(edited, state, prior, raw, lookup, first_diff, errors):
    before = prior.get("base_results") or {}
    after = state.get("new") or {}
    reported = []
    for item in edited[:40]:
        address = item["address"]
        path = item["owner"]
        old_obj, new_obj = before.get(path) or {}, after.get(path) or {}
        old = measured_rows(old_obj.get("rows", {})).get(address)
        new = measured_rows(new_obj.get("rows", {})).get(address)
        old_proven = {int(x, 16) for x in old_obj.get("proven", []) if ROW.fullmatch(x)}
        new_proven = {int(x, 16) for x in new_obj.get("proven", []) if ROW.fullmatch(x)}
        data = raw.get(path) or {}
        rows = {int(row["rva"], 16): row for row in data.get("rows", []) if ROW.fullmatch(row.get("rva", ""))}
        record = rows.get(address, {})
        diff = first_diff(path, record, data, True) if new and new[0] == "PARTIAL" and record else None
        if address is None:
            item_row = {"path": item["path"], "rva": None, "name": None, "size": None,
                        "old": "UNMEASURED" if item["before_body"] else "NONE",
                        "new": "UNKNOWN_RVA", "pct": None, "first": None,
                        "compiled_listing": [], "reference_listing": []}
        else:
            key = f"0x{address:08X}"
            item_row = row_report(item["path"], key, old, new, lookup(key), address in old_proven,
                                  address in new_proven, diff)
            if not new:
                item_row["new"] = "UNMEASURED"
        if item_row["new"] in {"UNKNOWN_RVA", "UNMEASURED", "MISSING"} and any(
                row["path"] in {item["path"], path} for row in errors):
            item_row["new"] = "COMPILE_ERROR"
        if not item["after_body"]:
            item_row["new"] = "NONE"
        reason = {
            "UNKNOWN_RVA": "The source definition has no unique owned ledger row in this comparison.",
            "UNMEASURED": "The exact body was absent from the checker output for this translation unit.",
            "MISSING": "The compiler output did not contain a body usable for this ledger row.",
            "COMPILE_ERROR": "The source file did not compile.",
            "PARTIAL": "The emitted body differs from the reference.",
        }.get(item_row["new"], "")
        item_row.update(function=item["function"], line=item["line"], owner=path, explanation=reason)
        reported.append(item_row)
    return reported


def from_landing(st, prior, changed_paths, first_diff, lookup, listing_rows=frozenset(), *, edited=()):
    """Project a real landing verdict to contributor-visible fields."""
    raw_results = prior.get("results") or {}
    base_results = prior.get("base_results") or {}
    gained, lost, near, objects = [], [], [], []
    for path, current in sorted(st.get("new", {}).items()):
        if not safe_path(path):
            continue
        before = base_results.get(path) or {}
        detail = {r["rva"]: r for r in (raw_results.get(path) or {}).get("rows", [])}
        old_rows, new_rows = before.get("rows", {}), current.get("rows", {})
        old_proven, new_proven = set(before.get("proven", [])), set(current.get("proven", []))
        if before.get("verified") and not current.get("verified"):
            objects.append(path)
        for address in sorted(set(old_rows) | set(new_rows)):
            if not ROW.fullmatch(address):
                continue
            old, new = old_rows.get(address), new_rows.get(address)
            was_proven, is_proven = address in old_proven, address in new_proven
            lost_credit = bool(old and old[0] == "MATCH" and (not new or new[0] != "MATCH"))
            lost_proof = was_proven and not is_proven
            added = bool(new and new[0] == "MATCH" and (not old or old[0] != "MATCH"))
            partial = bool(new and new[0] == "PARTIAL" and (not old or old != new))
            if lost_credit or lost_proof or added or partial:
                fields = detail.get(address, {})
                comparison = (first_diff(path, fields, raw_results.get(path) or {}, (path, int(address, 16)) in listing_rows)
                              if partial and len(near) < 20 else None)
                row = row_report(path, address, old, new, lookup(address), was_proven, is_proven, comparison)
                if lost_credit or lost_proof:
                    lost.append(row)
                if added:
                    gained.append(row)
                if partial:
                    near.append(row)
    messages = []
    for problem in st.get("problems", []):
        for phrase, guidance in GATES.items():
            if phrase in problem:
                messages.append(guidance)
        if "no longer compiles" in problem:
            messages.append("A translation unit that compiled on main failed to compile with this patch.")
    errors = diagnostics(raw_results, changed_paths)
    return {"edited": changed_definitions(edited, st, prior, raw_results, lookup, first_diff, errors), "kind": st["kind"], "gains": st.get("gains", len(gained)), "judged": len(st.get("jt", [])),
            "lost_count": len(lost), "verified_count": len(objects), "gained": gained[:20], "lost": lost[:20],
            "near": near[:20], "objects": objects[:20], "diagnostics": errors,
            "messages": list(dict.fromkeys(messages))[:10]}


def code(value):
    return chr(96) + str(value) + chr(96)


def format_result(base, head, lane, result):
    return quality_report(base, head, result)
