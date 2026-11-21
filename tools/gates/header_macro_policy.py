"""Identify local preprocessor input changes and check shared-header evidence."""
from dataclasses import dataclass
from hashlib import sha256
import json
import re

from cpp import Source, matching
from header_lexical_inventory import ordinary_header_guard
from rules import Finding

RULE = "H8"
MACROS = {"define", "undef", "push_macro", "pop_macro"}
INCLUDES = {"include", "include_next", "import", "using"}
OPEN = {"if", "ifdef", "ifndef"}
ARMS = {"elif", "elifdef", "elifndef", "else"}
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
# A macro named like one of these rewrites declarations wherever it is defined.
KEYWORDS = frozenset("""
    alignof asm auto bool break case catch char class const const_cast continue default delete do double
    dynamic_cast else enum explicit export extern false float for friend goto if inline int long mutable namespace
    new operator private protected public register reinterpret_cast return short signed sizeof static static_cast
    struct switch template this throw true try typedef typeid typename union unsigned using virtual void volatile
    wchar_t while __int8 __int16 __int32 __int64 __declspec __stdcall __cdecl __fastcall __thiscall
""".split())
MOVE = re.compile(r"[-/](?:[DU](?:[A-Za-z_]\S*)?|FI\S*)\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
OID = re.compile(r"[0-9a-f]{40}\Z")


@dataclass(frozen=True)
class Event:
    kind: str
    line: int
    values: tuple[str, ...]
    guards: tuple[tuple[str, ...], ...]


@dataclass(frozen=True, order=True)
class MacroChange:
    path: str
    line: int
    input_sha256: str


@dataclass(frozen=True, order=True)
class SharedView:
    path: str
    git_blob: str
    site: str
    before_declarations_sha256: str
    after_declarations_sha256: str


@dataclass(frozen=True)
class MacroProof:
    """Trusted paired scan of the same shared header blobs under old/new local inputs.

    The protected adapter checks provenance, the planned full translation-unit
    closure, per-header actual read identity and the exact include-instance list.
    """
    base: str
    head: str
    tree: str
    change: MacroChange
    record_sha256: str
    complete: bool
    instances: tuple[tuple[str, str, str], ...]
    views: tuple[SharedView, ...]


def source_flags(source):
    for line, value in enumerate(source.lines, 1):
        if value.startswith("// cl:"):
            options = value[len("// cl:"):].split()
            # The accepted compiler syntax keeps -D/-U operands in one bare
            # token. Forced includes also matter since they precede the file.
            values = []
            index = 0
            while index < len(options):
                option = options[index]
                if MOVE.fullmatch(option):
                    values.append("-" + option[1:])
                    if option[1:] == "FI" and index + 1 < len(options):
                        index += 1
                        values.append(options[index])
                elif option in ("-I", "/I"):
                    index += 1
                index += 1
            if values:
                return Event("flags", line, tuple(values), ())
            return None
    return None


def spell(tokens):
    """Preserve token adjacency since it can affect definitions and stringization."""
    values = []
    for position, token in enumerate(tokens):
        if position and tokens[position - 1].stop != token.offset:
            values.append(" ")
        values.append(token.value)
    return tuple(values)


def guard_definition(source):
    """Find the structural outer guard, rather than a local macro input."""
    directives = tuple(source.directives())
    omitted = {index for start, end in directives for index in range(start, end)}
    guard = ordinary_header_guard(source, directives, omitted)
    if not guard:
        return None
    opening, definition, closing = sorted(guard)
    outside = ((start, end) for start, end in directives if start < opening[0] or end > closing[1])
    if any(source.ordered[start + 1:end] != ("pragma", "once") for start, end in outside):
        return None
    return source.ordered[opening[0] + 2], definition[0]


def events(source, ignored_definition=None, whole_file=False):
    flags = source_flags(source)
    all_events = [flags] if flags else []
    guards = []
    tokens = source.tokens
    offset = 0
    directive_ranges = dict(source.directives())
    while offset < len(tokens):
        current = tokens[offset]
        if offset in directive_ranges:
            end = directive_ranges[offset]
            parts = tokens[offset + 1:end]
            ignored = offset == ignored_definition
            offset = end
            if not parts or ignored:
                continue
            name = parts[0].value
            if name in OPEN:
                guards.append(spell(parts))
            elif name in ARMS:
                if guards:
                    # The current arm also depends on all previous arms
                    # being false.
                    guards[-1] += ("#", *spell(parts))
            elif name == "endif":
                if guards:
                    guards.pop()
            elif name in MACROS | INCLUDES:
                all_events.append(Event(name, current.line, spell(parts[1:]), tuple(guards)))
            elif name == "pragma" and len(parts) > 1 and parts[1].value in MACROS:
                all_events.append(Event(parts[1].value, current.line, spell(parts[2:]), tuple(guards)))
            continue
        if (current.value in ("__pragma", "_Pragma") and offset + 1 < len(tokens)
                and tokens[offset + 1].value == "("):
            stop = matching(source.ordered, offset + 1)
            if stop is not None:
                inner = tokens[offset + 2:stop]
                if current.value == "_Pragma":
                    keyword = inner[0].value.strip('"').split("(", 1)[0].strip() if inner else ""
                else:
                    keyword = inner[0].value if inner else ""
                if keyword in {"push_macro", "pop_macro"}:
                    all_events.append(Event(keyword, current.line, spell(inner), tuple(guards)))
                offset = stop + 1
                continue
        offset += 1
    if whole_file:
        return tuple(all_events)
    last_include = max((i for i, item in enumerate(all_events) if item.kind in INCLUDES), default=-1)
    if last_include < 0:
        return (flags,) if flags and any(value.startswith("-FI") for value in flags.values) else ()
    return tuple(all_events[:last_include + 1])


def own_identifiers(source):
    """Identifiers in the file's own text, outside preprocessor directives."""
    inside = {index for start, end in source.directives() for index in range(start, end)}
    return {token.value for index, token in enumerate(source.tokens)
            if index not in inside and IDENTIFIER.fullmatch(token.value)}


def macro_name(event):
    if event.kind in ("define", "undef"):
        return event.values[0] if event.values else ""
    for value in event.values:                       # push_macro("NAME") / pop_macro("NAME")
        if value.startswith('"'):
            return value.strip('"')
    return ""


def capturing(source, ignored_definition, names):
    """Macro directives anywhere in a header whose name is a keyword or one of the header's own identifiers: they
    rewrite the header's own declarations whether or not an include follows them."""
    return tuple(event for event in events(source, ignored_definition, whole_file=True)
                 if event.kind in MACROS and (macro_name(event) in KEYWORDS or macro_name(event) in names))


def shape_key(record):
    return record.kind, record.values, record.guards


def change_in(path, before, after):
    """Isolate local macro changes or changes in where they precede a shared include."""
    prior, candidate = Source(before), Source(after)
    old_guard, new_guard = (
        (guard_definition(prior), guard_definition(candidate))
        if path.startswith("include/") else (None, None)
    )
    prior_ignored = candidate_ignored = None
    if old_guard and new_guard and old_guard[0] == new_guard[0]:
        prior_ignored, candidate_ignored = old_guard[1], new_guard[1]
    elif new_guard and not prior.tokens:
        candidate_ignored = new_guard[1]
    own = False
    old, new = events(prior, prior_ignored), events(candidate, candidate_ignored)
    old_key, new_key = tuple(map(shape_key, old)), tuple(map(shape_key, new))
    if old_key == new_key or not any(e.kind in MACROS | {"flags"} for e in old + new):
        if not path.startswith("include/"):
            return None
        # A header's own declarations: a macro named like a keyword, or like an identifier the header already
        # used, changes them even after the last include. A new macro name (a new constant) does not.
        names = own_identifiers(prior)
        old = capturing(prior, prior_ignored, names)
        new = capturing(candidate, candidate_ignored, names)
        old_key, new_key = tuple(map(shape_key, old)), tuple(map(shape_key, new))
        if old_key == new_key:
            return None
        own = True
    # Locate the first changed preprocessor input or include boundary. Lines
    # are for presentation and stay out of the canonical input identity.
    limit = min(len(old_key), len(new_key))
    first = next((i for i in range(limit) if old_key[i] != new_key[i]), limit)
    physical = new[first] if first < len(new) else old[first]
    shape = ("own", old_key, new_key) if own else (old_key, new_key)
    material = json.dumps(shape, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return MacroChange(path, physical.line, sha256(material).hexdigest())


def valid_proof(change, proof, binding, pinned_shared_blobs):
    if ((proof.base, proof.head, proof.tree) != binding or proof.change != change
            or proof.complete is not True or not HASH.fullmatch(proof.record_sha256)):
        return False
    expected = tuple(sorted(set(proof.instances)))
    actual = tuple(sorted((view.path, view.git_blob, view.site) for view in proof.views))
    if expected != proof.instances or expected != actual:
        return False
    return all(
        view.path.startswith("include/") and view.git_blob == pinned_shared_blobs.get(view.path)
        and OID.fullmatch(view.git_blob) and view.site
        and HASH.fullmatch(view.before_declarations_sha256) and HASH.fullmatch(view.after_declarations_sha256)
        for view in proof.views
    )


def verify_change(change, binding, pinned_shared_blobs, trusted=None):
    """Return named refusals and holds for authenticated paired evidence."""
    if change is None:
        return [], []
    if trusted is None or not valid_proof(change, trusted, binding, pinned_shared_blobs):
        return [], [(change, "This file's preprocessor change needs a complete shared-header comparison.")]
    findings = [
        Finding(change.path, change.line, RULE,
                f"This file's preprocessor change reshapes declarations in {path}.",
                "Remove the local macro override and put the shared declaration in its header.")
        for path in sorted({item.path for item in trusted.views
                            if item.before_declarations_sha256 != item.after_declarations_sha256})
    ]
    return findings, []
