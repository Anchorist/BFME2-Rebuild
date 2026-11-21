"""Qualified identity checks for the protected header admission path."""
from collections import Counter, defaultdict
import json
from pathlib import PurePosixPath
import re

from cpp import Source, decode, matching
from definitions import CLASS_HEAD, LINKAGE, NAMESPACE, Definition, definitions
from git_objects import ObjectError
from rules import Finding

RULE = "H3"
PLACEHOLDER = re.compile(r"Rva[0-9A-Fa-f]{6}\w*\Z", re.ASCII)
COMPONENT = re.compile(r"[A-Za-z_]\w*\Z", re.ASCII)
TYPE_ENCODING = re.compile(r"(?:[VUT]|W4)(Rva[0-9A-Fa-f]{6}\w*(?:@[A-Za-z_]\w*)*)@@", re.ASCII)
SPECIAL_OWNER = re.compile(r"^\?\?(?:0|1|_7|_8)(.+)$", re.ASCII)
POSSIBLE_SPLICE = re.compile(rb"(?:\\|\?\?/)[ \t]*\r?\n")
ACCESS = {"public", "protected", "private"}


def normalized_part(value):
    return re.sub(r"\s+", "", value)


def qualified_types(source):
    """Read named namespace and class scopes while skipping function and initializer bodies."""
    omitted = {i for start, end in source.directives() for i in range(start, end)}
    tokens = [token for i, token in enumerate(source.tokens) if i not in omitted]
    values = [token.value for token in tokens]

    def walk(start, end, scope, inside_class=False, internal=False):
        cursor = start
        while cursor < end:
            token = values[cursor]
            if cursor == start and inside_class and token in ACCESS and values[cursor + 1:cursor + 2] == [":"]:
                cursor += 2
                start = cursor
                continue
            if token in {"(", "[", "{"}:
                close = matching(values, cursor)
                if close is None or close >= end:
                    return
                if token == "{":
                    head = " ".join(values[start:cursor])
                    namespace = NAMESPACE.fullmatch(head)
                    record = CLASS_HEAD.fullmatch(head)
                    if namespace:
                        nested = normalized_part(namespace[1]) if namespace[1] else "@anonymous"
                        yield from walk(cursor + 1, close, (*scope, nested), internal=internal or nested == "@anonymous")
                    elif LINKAGE.fullmatch(head):
                        yield from walk(cursor + 1, close, scope, inside_class, internal)
                    elif record:
                        name = normalized_part(record["name"]) + normalized_part(record["args"] or "")
                        prefix = "::".join(scope)
                        qualified = name if prefix and name.startswith(prefix + "::") else "::".join((*scope, name))
                        yield Definition("type", qualified, tokens[start].line, internal)
                        if record["kind"] != "enum":
                            yield from walk(cursor + 1, close, (qualified,), inside_class=True, internal=internal)
                    start = close + 1
                cursor = close
            elif token in {";", "}"}:
                start = cursor + 1
            cursor += 1

    return walk(0, len(values), ())


def ledger_types(symbol):
    """Extract explicitly encoded placeholder types in supported MSVC key forms."""
    head, marker, tail = symbol.partition("@@")
    if not marker:
        return
    special = SPECIAL_OWNER.fullmatch(head)
    if special:
        owner = special[1].split("@")
    elif head.startswith("?") and not head.startswith("??") and tail[:1] in set("ABCDEFGHIJKLMNOPQRSTUVWX012"):
        owner = head[1:].split("@")[1:]
    else:
        owner = []
    if owner and PLACEHOLDER.fullmatch(owner[0]) and all(COMPONENT.fullmatch(part) for part in owner):
        yield "::".join(reversed(owner))
    for mention in TYPE_ENCODING.finditer(tail):
        yield "::".join(reversed(mention[1].split("@")))


def file_definitions(source, path):
    """Reuse the global object scanner and add qualified nested type records."""
    globals_found = (entry for entry in definitions(source, is_c=path.endswith(".c")) if entry.kind == "global")
    yield from globals_found
    yield from qualified_types(source)


def leaf(name):
    """Find the last qualified component outside template arguments."""
    depth = start = 0
    for index, token in enumerate(name):
        if token == "<":
            depth += 1
        elif token == ">":
            depth -= 1
        elif not depth and token == ":" and name[index - 1:index] == ":":
            start = index + 1
    return name[start:].split("<", 1)[0]


def key(site):
    return site.kind, site.name, site.internal


def check_identities(repo, policy, base, head):
    wanted = {}
    loaded = {}

    def load(oid, path, needles=()):
        cache_key = (oid, path.endswith(".c"))
        if cache_key not in loaded:
            _, raw = repo.blob(oid, policy.limits["bytes_per_file"])
            if raw is None:
                raise ObjectError(f"Cannot inspect qualified definitions in {path}.")
            if needles and not any(needle in raw for needle in needles) and not POSSIBLE_SPLICE.search(raw):
                return ()
            try:
                loaded[cache_key] = tuple(file_definitions(Source(decode(raw)), path))
            except UnicodeDecodeError as exc:
                raise ObjectError(f"Cannot read definitions in {path} as UTF-8.") from exc
        return loaded[cache_key]

    for delta in sorted(repo.diff(base, head), key=lambda item: item.path):
        if not delta.new or not delta.new.regular or policy.kind(delta.path) is None:
            continue
        old = Counter(key(item) for item in load(delta.old.oid, delta.path)) if delta.old and delta.old.regular else Counter()
        for entry in load(delta.new.oid, delta.path):
            identity = key(entry)
            if old[identity]:
                old[identity] -= 1
            else:
                wanted.setdefault(identity, set()).add((delta.path, entry.line))
    if not wanted:
        return []

    names = defaultdict(list)
    external = [identity for identity in wanted if not identity[2]]
    needles = tuple(sorted({leaf(identity[1]).encode("utf-8")
                            for identity in external}))
    interesting_paths = {path for positions in wanted.values() for path, _ in positions}
    for path, entry in sorted(repo.tree(head, "include", "src")):
        if not entry.regular or policy.kind(path) is None or (not external and path not in interesting_paths):
            continue
        choices = () if path in interesting_paths else needles
        for definition in load(entry.oid, path, choices):
            identity = key(definition)
            if identity in wanted:
                names[identity].append((path, definition.line))

    findings = []
    unresolved = [identity for identity in wanted if identity[0] == "type" and
                  PLACEHOLDER.fullmatch(leaf(identity[1]))]
    known = set()
    if unresolved:
        _, raw = repo.read_blob(repo.ledger_oid(base), 1 << 30)
        try:
            rows = json.loads(raw)["rows"]
            for row in rows:
                for spelling in (row["name"], *row["accepted_names"]):
                    known.update(ledger_types(spelling))
        except (KeyError, TypeError, ValueError) as exc:
            raise ObjectError("The protected ledger cannot establish the placeholder type names.") from exc

    for identity, positions in sorted(wanted.items()):
        kind, name, internal = identity
        matches = names[identity]
        for path, line in sorted(positions):
            other = next(((p, n) for p, n in matches if (p, n) != (path, line) and (p == path or not internal)), None)
            if other:
                findings.append(Finding(
                    path, line, RULE, f"The qualified {kind} {name} also has a definition at {other[0]}:{other[1]}.",
                    "Keep the existing definition and refer to it from this change.",
                ))
            elif matches.count((path, line)) > 1:
                findings.append(Finding(path, line, RULE, f"The qualified {kind} {name} is defined twice here.",
                                        "Keep one definition at this location."))
            if identity in unresolved and name not in known:
                findings.append(Finding(
                    path, line, RULE, f"The protected ledger does not identify the placeholder type {name}.",
                    "Use a type already identified by the ledger or submit a ledger request for this type.",
                ))
    return sorted(set(findings))
