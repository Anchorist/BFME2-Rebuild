"""Qualified class scopes, selected from the project layout reader."""

import re


NON_CODE = re.compile(r'//[^\n]*|/\*.*?(?:\*/|\Z)|"(?:\\.|[^"\\\n])*"?|\'(?:\\.|[^\'\\\n])*\'?', re.S)


LINKAGE = re.compile(r'\bextern\s+"C(?:\+\+)?"\s*\{')


IDENT = r"[A-Za-z_]\w*"


CLASS_KEY = re.compile(r"\b(?P<key>class|struct)\b")


DECLSPEC = re.compile(r"__declspec\s*\(")


NAMESPACE_HEAD = re.compile(r"\bnamespace\s*(?P<name>" + IDENT + r"(?:\s*::\s*" + IDENT + r")*)?\s*\{")


TEMPLATE_MEMBER = re.compile(r"\btemplate\s*<")


ACCESS = re.compile(r"^(?:\s*(?:public|protected|private)\s*:)+")


OTHER_SCOPE = re.compile(r"^(?:typedef\s+)?(?:enum|union)\b[^;{}()]*$")


FUNCTION_HEAD = re.compile(r"\)\s*(?:const\b\s*)?(?:volatile\b\s*)?(?:throw\s*\([^;{}]*\)\s*)?(?::[^;{}]*)?$")


KNOWN_SCOPE = "scope"


class Ambiguous(Exception):
    """The reader cannot prove what a brace or head is."""


def _masked(text):
    """`text` with comments and literals blanked, offsets kept."""
    return NON_CODE.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), text)


def _ambiguous(text, code):
    """Constructs that can manufacture or hide scope: the refusals moved_bodies uses."""
    return bool(re.search(r'(?:u8|u|U|L)?R"|<%|%>|<:|:>|\\\r?\n', text)
                or re.search(r"\?\?[=/'()!<>-]", text)
                or re.search(r"^[ \t\f\v]*(?:#|%:)(?![ \t]*(?:include|pragma)\b)", code, re.M))


def _without_includes(code):
    """`code` with #include and #pragma lines blanked: neither can open or close a scope."""
    return re.sub(r"^[ \t]*#[ \t]*(?:include|pragma)\b[^\n]*", lambda m: " " * len(m.group()), code, flags=re.M)


def _skip_space(code, pos):
    while pos < len(code) and code[pos].isspace():
        pos += 1
    return pos


def _angle_end(code, pos):
    """Index just after the `>` closing the `<` at code[pos]; parentheses hide `<`/`>`; None if
    a `;`, `{` or `}` comes first."""
    angle = paren = 0
    for i in range(pos, len(code)):
        char = code[i]
        if char == "(":
            paren += 1
        elif char == ")":
            paren -= 1
            if paren < 0:
                return None
        elif paren:
            continue
        elif char == "<":
            angle += 1
        elif char == ">":
            angle -= 1
            if angle == 0:
                return i + 1
        elif char in ";{}":
            return None
    return None


def _brace_end(code, pos):
    """Index just after the `}` closing the `{` at code[pos], or None."""
    depth = 0
    for i in range(pos, len(code)):
        if code[i] == "{":
            depth += 1
        elif code[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return None


def _paren_end(code, pos):
    depth = 0
    for i in range(pos, len(code)):
        if code[i] == "(":
            depth += 1
        elif code[i] == ")":
            depth -= 1
            if depth == 0:
                return i + 1
    return None


def _template_prefix(code, pos):
    """True when the class key at `pos` follows `template <...>` (parameters may hold parenthesised
    comparisons, defaults with nested templates, and template template parameters)."""
    i = pos - 1
    while i >= 0 and code[i].isspace():
        i -= 1
    if i < 0 or code[i] != ">":
        return False
    angle = paren = 0
    while i >= 0:
        char = code[i]
        if char == ")":
            paren += 1
        elif char == "(":
            paren -= 1
        elif paren:
            pass
        elif char == ">":
            angle += 1
        elif char == "<":
            angle -= 1
            if angle == 0:
                break
        elif char in ";{}":
            return False
        i -= 1
    if i < 0:
        return False
    return re.search(r"\btemplate\s*$", code[:i]) is not None


def _qualified_name(code, pos):
    """(spelling, args, end) of `A::B<args>::C<args>` at pos: the spelling keeps inner argument
    lists, `args` is the last component's list (None when it has none), whitespace collapsed."""
    parts, args = [], None
    while True:
        name = re.compile(IDENT).match(code, pos)
        if not name:
            return None
        pos = _skip_space(code, name.end())
        piece, args = name.group(), None
        if pos < len(code) and code[pos] == "<":
            end = _angle_end(code, pos)
            if end is None:
                raise Ambiguous("unbalanced template argument list")
            args = re.sub(r"\s*([<>,])\s*", r"\1", " ".join(code[pos + 1:end - 1].split()))
            piece += "<" + args + ">"
            pos = _skip_space(code, end)
        parts.append(piece)
        if code[pos:pos + 2] == "::":
            pos = _skip_space(code, pos + 2)
            continue
        if args is not None:
            parts[-1] = name.group()             # the last component's list is `args`, not spelling
        return "::".join(parts), args, pos


def _class_head(code, match):
    """(name, args, brace) when this class key opens a class body; (None, None, brace) for an
    anonymous one; None when it opens no body (a declaration, friend or elaborated type)."""
    pos = _skip_space(code, match.end())
    while True:
        declspec = DECLSPEC.match(code, pos)
        if not declspec:
            break
        end = _paren_end(code, declspec.end() - 1)
        if end is None:
            raise Ambiguous("unbalanced __declspec")
        pos = _skip_space(code, end)
    if pos < len(code) and code[pos] == "{":
        return None, None, pos
    head = _qualified_name(code, pos)
    if head is None:
        return None
    name, args, pos = head
    if pos < len(code) and code[pos] == ":" and code[pos:pos + 2] != "::":
        paren = 0
        for i in range(pos + 1, len(code)):
            char = code[i]
            if char == "(":
                paren += 1
            elif char == ")":
                paren -= 1
            elif char in ";}" and not paren:
                return None
            elif char == "{" and not paren:
                pos = i
                break
        else:
            return None
    if pos >= len(code) or code[pos] != "{":
        return None
    return re.sub(r"\s+", "", name), args, pos


def _typedef_name(code, start, close):
    """The declarator of `typedef struct { ... } NAME;`; None for an anonymous non-typedef body."""
    if not re.search(r"\btypedef\s*$", code[:start]):
        return None
    after = re.compile(r"\s*(" + IDENT + r")\s*[;,\[]").match(code, close)
    if not after:
        raise Ambiguous("typedef of an anonymous class without a plain declarator")
    return after.group(1)


def _proven_brace(statement, owner=None):
    """A `{` that opens no class or namespace: an initializer, an enum/union body or a function
    body with a type, a qualified name or an operator before its parameter list (in a class,
    also `owner`'s own constructor or destructor)."""
    statement = ACCESS.sub("", statement).strip()
    if statement.endswith("=") or statement.endswith(","):
        return "initializer"
    # A template prefix is no evidence of a return type: strip and validate every
    # `template <...>` first, so `template <class T> MACRO(X) {` stays unproven.
    while True:
        prefix = re.match(r"template\s*<", statement)
        if not prefix:
            break
        end = _angle_end(statement, prefix.end() - 1)
        if end is None:
            return None
        statement = statement[end:].strip()
    if OTHER_SCOPE.match(statement):
        return "other"
    tail = FUNCTION_HEAD.search(statement)
    if not tail:
        return None
    # The text before the parameter list: find the `(` that opens it.
    depth, open_at = 0, None
    for i in range(tail.start(), -1, -1):
        if statement[i] == ")":
            depth += 1
        elif statement[i] == "(":
            depth -= 1
            if depth == 0:
                open_at = i
                break
    if open_at is None:
        return None
    before = statement[:open_at].strip()
    if re.search(r"(?:::|\boperator\b)", before):
        return "function"
    if owner and re.fullmatch(r"(?:(?:inline|explicit|virtual|__forceinline)\s+)*~?\s*" + re.escape(owner), before):
        return "function"
    tokens = re.findall(r"[A-Za-z_]\w*|[*&]", before)
    return "function" if len(tokens) >= 2 else None


def class_identities(text):
    """[(qualified, name, args, is_template, start, end, key)] for every class body outside a
    function body, in source order; None when the text cannot be read with certainty.

    Opt-in and scope-tracked: namespaces and enclosing classes are part of `qualified`
    (`(anonymous)` for an unnamed namespace), so a member template Outer::X is not FX::X.
    `args` is a specialization's argument list (None for a primary). Every brace at namespace or
    class scope must be a class, namespace, linkage, enum or union body, an initializer, or a
    function body with a provable head; anything else (a macro-generated scope) gives None.
    Declarations, explicit instantiations and uses define no body and are absent.
    """
    code = _masked(text)
    if _ambiguous(text, code):
        return None
    code = _without_includes(code)
    try:
        heads = {}
        for match in CLASS_KEY.finditer(code):
            head = _class_head(code, match)
            if head:
                name, args, brace = head
                heads[brace] = (name, args, _template_prefix(code, match.start()), match.start(),
                                match.group("key"))
        namespaces = {m.end() - 1: m for m in NAMESPACE_HEAD.finditer(code)}
        linkage = {m.end() - 1 for m in LINKAGE.finditer(text) if code[m.start():m.start() + 6] == "extern"}
        stack, found, boundary = [], [], 0
        for token in re.finditer(r"[{};]", code):
            pos, char = token.start(), token.group()
            known = all(frame[0] is not None for frame in stack)
            if char == "{":
                head, namespace = heads.get(pos), namespaces.get(pos)
                if namespace:
                    path = tuple(re.sub(r"\s+", "", namespace.group("name") or "(anonymous)").split("::"))
                elif head and head[0] is not None:
                    path = tuple(head[0].split("::"))
                elif head:
                    path = ("(anonymous class)",)
                elif pos in linkage:
                    path = ()
                elif not known:
                    path = None                  # nested in a function or initializer: not ours
                else:
                    owner = next((frame[1][0].split("::")[-1].split("<")[0] for frame in reversed(stack)
                                  if frame[1] and frame[1][0]), None)
                    kind = _proven_brace(code[boundary:pos], owner)
                    if kind is None:
                        return None              # a brace this reader cannot name
                    path = None if kind in ("function", "initializer") else (KNOWN_SCOPE,)
                scope = tuple(part for frame in stack for part in (frame[0] or ()) if part != KNOWN_SCOPE)
                stack.append((path, head if known else None, scope))
            elif char == "}":
                if not stack:
                    return None
                _path, head, scope = stack.pop()
                if head:
                    name, args, is_template, start, key = head
                    if name is None:
                        name = _typedef_name(code, start, pos + 1)
                    if name is not None:
                        qualified = "::".join(scope + tuple(name.split("::")))
                        found.append((qualified, name, args, is_template, start, pos + 1, key))
            boundary = token.end()
    except Ambiguous:
        return None
    if stack:
        return None
    return sorted(found, key=lambda item: item[4])
