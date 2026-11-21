"""Explicit qualified declarations from a conservative header grammar."""
from dataclasses import dataclass
import json
import re

from cpp import Source, matching
from definitions import CLASS_HEAD, IDENT, LINKAGE, NAMESPACE
from header_removal import Declaration, NAME


ACCESS = {"public", "protected", "private"}
TYPE_HEAD = {"class", "struct", "union", "enum"}
OPAQUE_HEAD = {"typedef", "friend", "using", "template", "namespace", *TYPE_HEAD}
SPECIFIERS = {"const", "volatile", "void", "bool", "char", "char16_t", "wchar_t", "short",
              "int", "long", "float", "double", "signed", "unsigned", "__int8", "__int16",
              "__int32", "__int64"}
TOKENS_IN_TYPE = {"::", "<", ">", ">>", ",", "*", "&", "&&"}
TEMPLATES = {"<": 1, ">": -1, ">>": -2}
CALL_SUFFIX = {"const", "volatile", "&", "&&", "noexcept", "override", "final"}
NUMERAL = re.compile(r"(?:0[xX][0-9a-fA-F]+|[0-9]+)[uUlL]{0,3}\Z")
CONST_EXPRESSION = {"+", "-", "~", "!", "*", "/", "%", "(", ")", "<<", ">>", "&", "|", "^", "::"}
QUALIFIED = r"(?:::)?[A-Za-z_]\w*(?:::[A-Za-z_]\w*)*"
OFFSET_CHECK = rf"(?:sizeof\({QUALIFIED}\)|offsetof\({QUALIFIED},[A-Za-z_]\w*\))"
LAYOUT_EXPRESSION = rf"{OFFSET_CHECK}(?:[+-]{OFFSET_CHECK})*"
LAYOUT_ASSERT = re.compile(rf"typedefchar[A-Za-z_]\w*\[(?:\({LAYOUT_EXPRESSION}==(?:0[xX][0-9a-fA-F]+|[0-9]+)\)|"
                           rf"{LAYOUT_EXPRESSION}==(?:0[xX][0-9a-fA-F]+|[0-9]+))\?1:-1\]\Z", re.ASCII)
CALL_CONVENTIONS = {"__cdecl", "__stdcall", "__fastcall", "__thiscall"}
PUNCTUATION = {"(": ")", "[": "]", "{": "}"}


@dataclass(frozen=True, order=True)
class Unknown:
    path: str
    owner: tuple[str, ...]
    tokens: tuple[str, ...]
    line: int


@dataclass(frozen=True)
class LexicalInventory:
    declarations: tuple[Declaration, ...]
    unknown: tuple[Unknown, ...]


def join_name(owner, name):
    prefix = "::".join(owner)
    full = name[2:] if name.startswith("::") else name
    return full if not prefix or full.startswith(prefix + "::") or name.startswith("::") else f"{prefix}::{full}"


def plain_type(values):
    return (
        bool(values)
        and all(IDENT.fullmatch(value) or value in TOKENS_IN_TYPE for value in values)
        and all(value not in OPAQUE_HEAD for value in values)
        and any(IDENT.fullmatch(value) for value in values)
    )


def groups(values):
    """Split ordinary arguments, balancing template argument commas."""
    if not values:
        return []
    start = depth = 0
    arguments = []
    for index, value in enumerate(values):
        depth += TEMPLATES.get(value, 0)
        if depth < 0:
            return None
        if depth == 0 and value == ",":
            if start == index:
                return None
            arguments.append(values[start:index])
            start = index + 1
    if depth or start == len(values):
        return None
    arguments.append(values[start:])
    return arguments


def parameter_type(values):
    if plain_type(values):
        last = values[-1]
        if (len(values) > 1 and IDENT.fullmatch(last) and last not in SPECIFIERS
                and values[-2] != "::" and any(t not in {"const", "volatile"} for t in values[:-1])):
            return values[:-1]
        return values
    return None


def callable_declaration(head, owner):
    if not head or "(" not in head or head[0] in OPAQUE_HEAD:
        return None
    left = head.index("(")
    right = matching(head, left)
    if left == 0 or right is None or not IDENT.fullmatch(head[left - 1]):
        return None
    start = left - 1
    if head[start - 1:start] == ("~",):
        start -= 1
    while start >= 2 and head[start - 1] == "::" and IDENT.fullmatch(head[start - 2]):
        start -= 2
    name = "".join(head[start:left])
    prefix = tuple(word for word in head[:start] if word not in {"inline", "virtual", "explicit"})
    leaf = name.rsplit("::", 1)[-1].lstrip("~")
    constructor = bool(owner) and (leaf == owner[-1].rsplit("::", 1)[-1] or name.endswith(f"{leaf}::{leaf}"))
    if not (plain_type(prefix) or (constructor and not prefix)) or "operator" in prefix:
        return None
    suffix = head[right + 1:]
    if suffix[-2:] == ("=", "0"):
        suffix = suffix[:-2]
    if ":" in suffix:
        split = suffix.index(":")
        if not constructor or not constructor_initializers(suffix[split + 1:]):
            return None
        suffix = suffix[:split]
    if any(token not in CALL_SUFFIX for token in suffix):
        return None
    args = groups(head[left + 1:right])
    if args is None:
        return None
    parameters = tuple(parameter_type(arg) for arg in args)
    if any(value is None for value in parameters):
        return None
    if parameters == (("void",),):
        parameters = ()
    suffix = tuple(token for token in suffix if token not in {"override", "final"})
    return join_name(owner, name), ("function", prefix, parameters, suffix)


def constructor_initializers(values):
    if not values:
        return False
    cursor = 0
    while cursor < len(values):
        if "(" not in values[cursor:]:
            return False
        opening = values.index("(", cursor)
        type_name = values[cursor:opening]
        if "<" in type_name and type_name[-1:] == (">",):
            template = type_name.index("<")
            if not plain_type(type_name[template + 1:-1]) or groups(type_name[template + 1:-1]) is None:
                return False
            type_name = type_name[:template]
        if not re.fullmatch(QUALIFIED, "".join(type_name), re.ASCII):
            return False
        closing = matching(values, opening)
        if closing is None:
            return False
        cursor = closing + 1
        if cursor == len(values):
            return True
        if values[cursor] != ",":
            return False
        cursor += 1
    return False


def simple_constant(values):
    return all(IDENT.fullmatch(value) or NUMERAL.fullmatch(value) or value in CONST_EXPRESSION
               for value in values)


def array_suffix(head, start):
    """Preserve balanced integral constant expressions, without evaluating them."""
    cursor = start
    while cursor < len(head):
        if head[cursor] != "[":
            return None
        close = matching(head, cursor)
        if close is None or not simple_constant(head[cursor + 1:close]):
            return None
        cursor = close + 1
    return head[start:]


def typedef_declaration(head, owner):
    if "(" not in head:
        result = field_declaration(head[1:], owner)
        if result:
            return result[0], ("alias", result[1][1:])
        return None
    opening = head.index("(")
    close = matching(head, opening)
    if close is None or head[close + 1:close + 2] != ("(",) or head[-1] != ")":
        return None
    pointer = head[opening + 1:close]
    result_type = head[1:opening]
    if (len(pointer) < 2 or pointer[-2] != "*" or not IDENT.fullmatch(pointer[-1])
            or any(item not in CALL_CONVENTIONS for item in pointer[:-2]) or not plain_type(result_type)):
        return None
    parts = groups(head[close + 2:-1])
    if parts is None:
        return None
    args = tuple(parameter_type(arg) for arg in parts)
    if any(arg is None for arg in args):
        return None
    return join_name(owner, pointer[-1]), ("function-pointer-alias", result_type, pointer[:-1], args)


def friend_declaration(head, owner, namespace):
    if len(head) >= 3 and head[1] in {"class", "struct", "union"}:
        name = "".join(head[2:])
        if re.fullmatch(QUALIFIED, name, re.ASCII):
            qualified = join_name(namespace, name)
            return qualified, ("friend-type", owner)
    return None


def field_declaration(head, owner):
    if not head or head[0] in OPAQUE_HEAD:
        return None
    if "[" in head:
        bound = head.index("[")
        suffix = array_suffix(head, bound)
        if suffix is None:
            return None
        head = head[:bound]
    else:
        suffix = ()
    if len(head) < 2 or not IDENT.fullmatch(head[-1]) or head[-1] in SPECIFIERS:
        return None
    prefix = tuple(token for token in head[:-1] if token != "extern")
    if not plain_type(prefix) or prefix[-1] == "::":
        return None
    return join_name(owner, head[-1]), ("data", prefix, suffix)


def ordinary_header_guard(source, directives, skipped):
    meaningful = [(a, b) for a, b in directives
                  if source.ordered[a + 1:b] not in (("pragma", "once"), ())
                  and source.ordered[a + 1:a + 2] != ("include",)]
    if len(meaningful) < 3:
        return set()
    first, define, *_, last = meaningful
    guard = source.ordered[first[0]:first[1]]
    if (len(guard) != 3 or guard[:2] != ("#", "ifndef") or not IDENT.fullmatch(guard[2])
            or source.ordered[define[0]:define[1]] != ("#", "define", guard[2])
            or source.ordered[last[0]:last[1]] != ("#", "endif")
            or any(index not in skipped for index in range(define[1]))
            or any(index not in skipped for index in range(last[1], len(source.tokens)))):
        return set()
    depth = 0
    for start, _ in meaningful:
        directive = source.ordered[start + 1]
        if directive in {"if", "ifdef", "ifndef"}:
            depth += 1
        elif directive == "endif":
            depth -= 1
            if depth == 0 and start != last[0]:
                return set()
        elif depth == 1 and directive in {"elif", "elifdef", "elifndef", "else"}:
            return set()
    return {first, define, last} if depth == 0 else set()


def conditional_contexts(path, source, directives, skipped):
    ignored = ordinary_header_guard(source, directives, skipped)
    stack, guards, unknown = [], [], []
    seen = dict(directives)
    cursor = 0
    while cursor < len(source.tokens):
        if cursor in seen:
            end = seen[cursor]
            statement = source.ordered[cursor + 1:end]
            if statement and (cursor, end) not in ignored:
                name = statement[0]
                if name in {"if", "ifdef", "ifndef"}:
                    stack.append((statement, []))
                elif name in {"elif", "elifdef", "elifndef", "else", "endif"}:
                    if not stack or stack[-1][1]:
                        return None
                    previous, _ = stack.pop()
                    if name != "endif":
                        stack.append(((*previous, "#", *statement), []))
                elif name not in {"include", "include_next"} and statement != ("pragma", "once"):
                    tokens = source.tokens[cursor + 1:end]
                    # Macro whitespace can change function-like definition or stringification.
                    material = tuple((token.value, i > 0 and tokens[i - 1].stop != token.offset)
                                     for i, token in enumerate(tokens))
                    guard = tuple(repr(item[0]) for item in stack)
                    unknown.append(Unknown(path, guard, (repr(material),), source.tokens[cursor].line))
            cursor = end
            continue
        token = source.tokens[cursor].value
        if stack:
            delimiters = stack[-1][1]
            if token in PUNCTUATION:
                delimiters.append(PUNCTUATION[token])
            elif token in PUNCTUATION.values() and (not delimiters or delimiters.pop() != token):
                return None
        guards.append(tuple(item[0] for item in stack))
        cursor += 1
    return (guards, unknown) if not stack else None


def constant_value(tokens):
    sign = -1 if tokens[:1] == ("-",) else 1
    if tokens[:1] in (("-",), ("+",)):
        tokens = tokens[1:]
    if len(tokens) != 1 or len(tokens[0]) > 16 or not NUMERAL.fullmatch(tokens[0]):
        return None
    text = tokens[0].rstrip("uUlL")
    base = 16 if text.lower().startswith("0x") else 8 if text.startswith("0") else 10
    try:
        return sign * int(text, base)
    except ValueError:
        return None


def enum_members(values, start, end, guards, context):
    """Capture explicit integral values and implicit successors within one arm."""
    entries = []
    previous, offset = -1, 0
    cursor = start
    while cursor < end:
        if not IDENT.fullmatch(values[cursor]) or guards[cursor] != context:
            return None
        symbol = values[cursor]
        following = cursor + 1
        while following < end and values[following] != ",":
            if guards[following] != context:
                return None
            if values[following] == "(" and (closing := matching(values, following)) is not None:
                following = closing
            following += 1
        expression = values[cursor + 1:following]
        if expression:
            if expression[0] != "=" or len(expression) == 1 or not simple_constant(expression[1:]):
                return None
            explicit = constant_value(expression[1:])
            previous = explicit if explicit is not None else expression[1:]
            offset = 0
        else:
            offset += 1
        value = previous + offset if type(previous) is int else (previous, offset)
        entries.append((symbol, value, cursor))
        cursor = following + 1
    return entries


def inventory(path, text):
    source = Source(text)
    directives = tuple(source.directives())
    omitted = {i for start, end in directives for i in range(start, end)}
    tokens = tuple(token for index, token in enumerate(source.tokens) if index not in omitted)
    values = tuple(token.value for token in tokens)
    contexts = conditional_contexts(path, source, directives, omitted)
    if contexts is None:
        return LexicalInventory((), (Unknown(path, (), source.ordered, 1),))
    guards, unknown = contexts
    declarations = []

    def record(result, offset):
        qualified, identity = result
        if not NAME.fullmatch(qualified):
            return False
        declarations.append(Declaration(path, tokens[offset].line, qualified,
                                        json.dumps((identity, guards[offset]), ensure_ascii=True,
                                                   separators=(",", ":"))))
        return True

    def opaque(owner, start, stop):
        guard = tuple(repr(item) for item in guards[start])
        unknown.append(Unknown(path, (*owner, *guard), values[start:stop], tokens[start].line))

    def statement(owner, namespace, start, stop):
        head = values[start:stop]
        if not head:
            return
        if head[:2] == ("typedef", "char") and LAYOUT_ASSERT.fullmatch("".join(head)):
            return
        if len(head) == 2 and head[0] in TYPE_HEAD and IDENT.fullmatch(head[1]):
            result = join_name(owner, head[1]), ("type",)
        elif head[0] == "typedef":
            result = typedef_declaration(head, owner)
        elif head[0] == "friend":
            result = friend_declaration(head, owner, namespace)
        else:
            result = callable_declaration(head, owner) or field_declaration(head, owner)
        if not result or not record(result, start):
            opaque(owner, start, stop)

    def walk(owner, start, stop, is_class=False, namespace=()):
        cursor = start
        while cursor < stop:
            token = values[cursor]
            if cursor == start and is_class and token in ACCESS and values[cursor + 1:cursor + 2] == (":",):
                cursor = start = cursor + 2
                continue
            if token in {"(", "[", "{"}:
                close = matching(values, cursor)
                if close is None or close >= stop:
                    opaque(owner, start, stop)
                    return
                if token == "{":
                    head = values[start:cursor]
                    spelling = " ".join(head)
                    named_namespace = NAMESPACE.fullmatch(spelling)
                    record_type = CLASS_HEAD.fullmatch(spelling)
                    after_close = close + 1
                    if named_namespace and named_namespace[1]:
                        nested = "".join(named_namespace[1].split())
                        qualified_namespace = (join_name(owner, nested),)
                        walk(qualified_namespace, cursor + 1, close, namespace=qualified_namespace)
                    elif LINKAGE.fullmatch(spelling):
                        walk(owner, cursor + 1, close, is_class, namespace)
                    elif (record_type and not record_type["args"]
                          and values[after_close:after_close + 1] == (";",)):
                        qualified = join_name(owner, "".join(record_type["name"].split()))
                        template = ()
                        if head[:2] == ("template", "<"):
                            close_template = head.index(">")
                            template = head[:close_template + 1]
                        if record_type["kind"] == "enum":
                            members = enum_members(values, cursor + 1, close, guards, guards[start])
                            if members is None:
                                opaque(owner, start, after_close)
                            elif record((qualified, ("type",)), start):
                                scoped = head[:2] in (("enum", "class"), ("enum", "struct"))
                                within = (qualified,) if scoped else owner
                                for name, value, offset in members:
                                    record((join_name(within, name), ("enumerator", qualified, value)), offset)
                        elif record((qualified, ("type", *template)), start):
                            walk((qualified,), cursor + 1, close, True, namespace)
                    elif (result := callable_declaration(head, owner)) and record(result, start):
                        pass
                    else:
                        if record_type or head and head[0] == "typedef":
                            # A trailing declarator can be part of this type.
                            while after_close < stop and values[after_close] != ";":
                                after_close += 1
                            after_close = min(after_close + 1, stop)
                        opaque(owner, start, after_close)
                    cursor = start = after_close
                    continue
                cursor = close
            elif token == ";":
                statement(owner, namespace, start, cursor)
                start = cursor + 1
            cursor += 1
        if start < stop:
            opaque(owner, start, stop)

    walk((), 0, len(values))
    return LexicalInventory(tuple(sorted(declarations)), tuple(sorted(unknown)))


def compare_inventories(files):
    """Return exact represented declarations and unmatched opaque scopes."""
    before, after = [], []
    old_unknown, new_unknown = {}, {}
    for file in files:
        path = file.identity.path
        left, right = inventory(path, file.before), inventory(path, file.after)
        before.extend(left.declarations)
        after.extend(right.declarations)
        for found, target in ((left.unknown, old_unknown), (right.unknown, new_unknown)):
            for item in found:
                target.setdefault((item.path, item.owner, item.tokens), []).append(item)
    unobserved = []
    for key in sorted(old_unknown.keys() | new_unknown.keys()):
        old, new = old_unknown.get(key, ()), new_unknown.get(key, ())
        paired = min(len(old), len(new))
        unobserved.extend(old[paired:])
        unobserved.extend(new[paired:])
    return tuple(before), tuple(after), tuple(sorted(unobserved))
