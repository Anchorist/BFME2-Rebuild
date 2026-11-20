"""Recognize exact x86 decorated signatures for explicit void-pointer types."""
from bisect import bisect_left
from collections import Counter
import re

from cpp import matching
from definitions import CLASS_HEAD, NAMESPACE


MARKER = re.compile(r"^//[ \t]*FUNCTION:[ \t]+BFME2[ \t]+0x([0-9a-fA-F]{8})[ \t]+.*?\bname=(\S+)")
DECORATED = re.compile(r"^\?([A-Za-z_]\w*(?:@[A-Za-z_]\w*)*)@@"
                       r"(Y[AEGI]|[CKS][AGI]|[AEIMQU][ABCD]E)(\S+)$", re.ASCII)
ID = re.compile(r"[A-Za-z_]\w*\Z", re.ASCII)
CONVENTIONS = {"__cdecl": "A", "__stdcall": "G", "__fastcall": "I", "__thiscall": "E"}
MODIFIERS = {"inline", "__inline", "static", "virtual", "extern"} | CONVENTIONS.keys()
PLAIN_TYPES = {
    ("void",): "X", ("signed", "char"): "C", ("char",): "D", ("unsigned", "char"): "E",
    ("short",): "F", ("short", "int"): "F", ("unsigned", "short"): "G",
    ("unsigned", "short", "int"): "G", ("int",): "H", ("signed", "int"): "H",
    ("unsigned",): "I", ("unsigned", "int"): "I", ("long",): "J", ("long", "int"): "J",
    ("unsigned", "long"): "K", ("unsigned", "long", "int"): "K", ("float",): "M",
    ("double",): "N", ("long", "double"): "O", ("bool",): "_N", ("__int64",): "_J",
    ("unsigned", "__int64"): "_K",
}


def encode_type(tokens):
    values = tuple(token.value for token in tokens)
    if values in PLAIN_TYPES:
        return PLAIN_TYPES[values], None
    if values[-1:] != ("*",) or values.count("*") != 1:
        return None
    target = values[:-1]
    qualifier = "B" if "const" in target else "A"
    if target.count("const") > 1:
        return None
    builtin = tuple(word for word in target if word != "const")
    code = PLAIN_TYPES.get(builtin)
    if code is None:
        return None
    offset = tokens[values.index("void")].offset if code == "X" else None
    return "P" + qualifier + code, offset


def parameter_types(tokens):
    if not tokens or tuple(token.value for token in tokens) == ("void",):
        return "XZ", ()
    pieces, start = [], 0
    for i, token in enumerate(tokens):
        if token.value == ",":
            pieces.append(tokens[start:i])
            start = i + 1
    pieces.append(tokens[start:])
    codes, offsets = [], []
    for part in pieces:
        encoded = encode_type(part)
        if encoded is None and len(part) > 1 and ID.fullmatch(part[-1].value):
            encoded = encode_type(part[:-1])
        if encoded is None or encoded[0] == "X":
            return None
        code, offset = encoded
        codes.append(code)
        if offset is not None:
            offsets.append(offset)
    return "".join(codes) + "@Z", tuple(offsets)


def declaration(source, start, decorated):
    """Prove recognized signature slots from the entire directly annotated head."""
    values, tokens = source.ordered, source.tokens
    name = "::".join(reversed(decorated[1].split("@")))
    call, encoded = decorated.group(2, 3)
    left = start
    while left < len(values) and values[left] not in {"(", "#", ";", "{", "}"}:
        left += 1
    if left <= start or values[left:left + 1] != ("(",) or not ID.fullmatch(values[left - 1]):
        return ()
    name_start = left - 1
    while name_start >= start + 2 and values[name_start - 1] == "::" and ID.fullmatch(values[name_start - 2]):
        name_start -= 2
    if "".join(values[name_start:left]) != name:
        return ()
    prefixes = tokens[start:name_start]
    spelled_calls = [CONVENTIONS[token.value] for token in prefixes if token.value in CONVENTIONS]
    if spelled_calls and spelled_calls != [call[-1]]:
        return ()
    returns = encode_type(tuple(token for token in prefixes if token.value not in MODIFIERS))
    closing = matching(values, left)
    if returns is None or closing is None:
        return ()
    param = parameter_types(tokens[left + 1:closing])
    if param is None or returns[0] + param[0] != encoded:
        return ()
    end = closing + 1
    while end < len(values) and values[end] in {"const", "volatile"}:
        end += 1
    suffix = values[closing + 1:end]
    if len(call) == 3:
        qualification = ("D" if "const" in suffix and "volatile" in suffix else
                         "B" if "const" in suffix else "C" if "volatile" in suffix else "A")
        if call[1] != qualification:
            return ()
    elif suffix:
        return ()
    if values[end:end + 1] != ("{",):
        return ()
    return param[1] if returns[1] is None else (returns[1], *param[1])


def candidates(source):
    """Return row binding and exact void-token offsets for supported declarations."""
    if "void" not in source.ordered or not any(key in source.text for key in ("PAX", "PBX")):
        return ()
    offsets = [token.offset for token in source.tokens]
    entries = []
    for comment in source.comments:
        if comment.kind != "line" or comment.line != comment.end_line:
            continue
        annotation = MARKER.match(comment.value)
        if annotation is None or not any(key in annotation[2] for key in ("PAX", "PBX")):
            continue
        decorated = DECORATED.fullmatch(annotation[2])
        if decorated is None:
            continue
        start = bisect_left(offsets, comment.stop)
        locations = declaration(source, start, decorated)
        if locations:
            entries.append(((int(annotation[1], 16), annotation[2]), locations))
    return tuple(entries)

ACCESS = {"private": "A", "protected": "I", "public": "Q"}
QUALIFIERS = {frozenset(): "A", frozenset({"const"}): "B",
              frozenset({"volatile"}): "C", frozenset({"const", "volatile"}): "D"}


def header_tokens(source):
    """Accept direct declarations in unbranched headers, optionally guarded once."""
    directives = tuple(source.directives())
    if not directives:
        return source.tokens
    values = source.ordered
    body = [values[start + 1:end] for start, end in directives]
    if body[0] == ("pragma", "once"):
        checked, start = body[1:], 1
    else:
        checked, start = body, 0
    if len(checked) >= 3 and checked[0][:1] == ("ifndef",):
        guard = checked[0][1:]
        if (len(guard) != 1 or not ID.fullmatch(guard[0])
                or checked[1] != ("define", *guard) or checked[-1] != ("endif",)
                or directives[start][0] != (directives[start - 1][1] if start else 0)
                or directives[start][1] != directives[start + 1][0]
                or directives[-1][1] != len(values)):
            return ()
        checked = checked[2:-1]
    if any(line[:1] != ("include",) and line != ("pragma", "once") for line in checked):
        return ()
    hidden = {i for start, end in directives for i in range(start, end)}
    return tuple(token for i, token in enumerate(source.tokens) if i not in hidden)


def member_declaration(tokens, values, start, end, owner, access):
    """Encode a complete explicit x86 member prototype and recover its void slots."""
    head = values[start:end]
    if "void" not in head or "*" not in head or "(" not in head:
        return None
    left = start + head.index("(")
    right = matching(values, left)
    if left <= start or right is None or right >= end or not ID.fullmatch(values[left - 1]):
        return None
    prefixes = tokens[start:left - 1]
    words = [token.value for token in prefixes]
    convention = [word for word in words if word in CONVENTIONS]
    suffix = values[right + 1:end]
    if any(value not in {"const", "volatile"} for value in suffix) or len(suffix) != len(set(suffix)):
        return None
    storage = ("static" in words, "virtual" in words)
    if storage == (True, True) or "extern" in words:
        return None
    access_code = ACCESS[access]
    if storage[0]:
        if suffix or len(convention) > 1 or convention == ["__thiscall"]:
            return None
        call = chr(ord(access_code) + 2) + CONVENTIONS[convention[0] if convention else "__cdecl"]
    else:
        if convention not in ([], ["__thiscall"]):
            return None
        if storage[1]:
            access_code = chr(ord(access_code) + 4)
        call = access_code + QUALIFIERS[frozenset(suffix)] + "E"
    returns = encode_type(tuple(token for token in prefixes if token.value not in MODIFIERS))
    argtypes = parameter_types(tokens[left + 1:right])
    if returns is None or argtypes is None:
        return None
    offsets = argtypes[1] if returns[1] is None else (returns[1], *argtypes[1])
    if not offsets:
        return None
    spelling = "?" + "@".join((values[left - 1], *reversed(owner))) + "@@" + call + returns[0] + argtypes[0]
    return (spelling, offsets) if DECORATED.fullmatch(spelling) else None


def header_candidates(source):
    """Identify declaration slots by lexical scope and access, never by comments."""
    if "void" not in source.ordered or "*" not in source.ordered:
        return ()
    tokens = header_tokens(source)
    values = tuple(token.value for token in tokens)
    candidates = []

    def walk(start, end, owner=(), access=None, depth=0):
        if depth >= 32:
            return
        i = start
        while i < end:
            value = values[i]
            if access is not None and i == start and value in ACCESS and values[i + 1:i + 2] == (":",):
                access, start, i = value, i + 2, i + 2
                continue
            if value == "{":
                head_end = i
                close = matching(values, i)
                if close is None or close >= end:
                    return
                head = " ".join(values[start:i])
                namespace = NAMESPACE.fullmatch(head) if access is None else None
                record = CLASS_HEAD.fullmatch(head) if values[start:i][:1] in (
                    ("class",), ("struct",), ("union",)
                ) else None
                if namespace and namespace[1]:
                    parts = tuple("".join(namespace[1].split()).split("::"))
                    walk(i + 1, close, (*owner, *parts), depth=depth + 1)
                elif (record and ID.fullmatch(record["name"]) and not record["args"]
                      and values[close + 1:close + 2] == (";",)):
                    default = "private" if record["kind"] == "class" else "public"
                    walk(i + 1, close, (*owner, record["name"]), default, depth + 1)
                i = close + 1
                if namespace or record or "(" in values[start:head_end]:
                    start = i
                else:
                    # An initializer can extend after its closing brace.
                    continue
                continue
            if value in ("(", "["):
                close = matching(values, i)
                if close is None or close >= end:
                    return
                i = close
            elif value == ";":
                if access is not None:
                    candidate = member_declaration(tokens, values, start, i, owner, access)
                    if candidate is not None:
                        candidates.append(candidate)
                start = i + 1
            i += 1

    walk(0, len(values))
    if not candidates:
        return ()
    counts = Counter(spelling for spelling, _ in candidates)
    return tuple(pair for pair in candidates if counts[pair[0]] == 1)
