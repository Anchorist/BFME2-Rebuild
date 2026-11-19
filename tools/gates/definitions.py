"""Definition discovery adapted from land_gate9.py's duplicate-class check.

Scope filtering follows global_class_defs: inspect declarations at file scope
and under linkage specifications, but skip bodies. Extend the same approach
to named namespace scopes, unions, enums and explicit object declarators.
"""

from dataclasses import dataclass, replace
import re

from cpp import matching


# land_gate9.DUPCLASS_DEF's declaration-head grammar. The caller supplies a
# complete lexed head, and confirms a following open brace.
CLASS_HEAD = re.compile(
    r'^(?:template\s*<.*?>\s*)?(?:(?:friend|export|typedef)\s+)?'
    r'(?P<kind>class|struct|union|enum)\s+'
    r'(?:(?:class|struct)\s+)?(?:__declspec\s*\([^)]*\)\s*)*'
    r'(?P<name>[^\W\d]\w*(?:\s*::\s*[^\W\d]\w*)*)'
    r'(?P<args>\s*<.*>)?\s*(?:final\s*)?'
    r'(?::(?!:)[^;{}]*)?$'
)
NAMESPACE = re.compile(r'^(?:inline\s+)?namespace(?:\s+([^\W\d]\w*(?:\s*::\s*[^\W\d]\w*)*))?$')
LINKAGE = re.compile(r'^extern\s+"C(?:\+\+)?"$')
IDENT = re.compile(r'^[^\W\d]\w*$')
NON_OBJECT = {'using', 'typedef', 'static_assert', 'template', 'class', 'struct',
              'union', 'enum', 'concept', 'namespace', 'asm', '__asm', '_asm',
              'module', 'import', 'return', 'friend'}
NOT_NAMES = NON_OBJECT | {'void', 'extern', 'const', 'volatile', 'signed', 'unsigned',
                          'char', 'short', 'int', 'long', 'float', 'double', 'bool',
                          'static', 'inline', 'register', 'mutable', '__int8', '__int16',
                          '__int32', '__int64', 'wchar_t', 'constexpr', 'thread_local'}


@dataclass(frozen=True, slots=True)
class Definition:
    kind: str
    name: str
    line: int
    internal: bool = False


def defined_objects(tokens, namespace, is_c):
    """Yield explicit namespace-scope variable names, including C tentative definitions."""
    values = [t.value for t in tokens]
    if not values or values[0] in NON_OBJECT:
        return
    if len(values) >= 2 and values[0] == 'extern' and values[1] in ('"C"', '"C++"'):
        tokens, values = tokens[2:], values[2:]
    boundaries = [0]
    first = 0
    in_initializer = False
    template_depth = 0
    initializer = []
    while first < len(values):
        value = values[first]
        if value == ',' and not template_depth:
            boundaries.append(first + 1)
            initializer.append(in_initializer)
            in_initializer = False
        elif value in ('=', '{') and not template_depth:
            in_initializer = True
        elif value == '<' and not in_initializer:
            template_depth += 1
        elif value in ('>', '>>') and template_depth:
            template_depth = max(0, template_depth - len(value))
        if value in ('(', '[', '{'):
            close = matching(values, first)
            if close is None:
                return
            first = close
        first += 1
    boundaries.append(len(values) + 1)
    initializer.append(in_initializer)

    for index, (start, stop) in enumerate(zip(boundaries, boundaries[1:])):
        part = values[start:stop-1]
        part_tokens = tokens[start:stop-1]
        if not part or ('extern' in values[:boundaries[1]-1] and not initializer[index]):
            continue
        declaration = []
        pos = depth = 0
        while pos < len(part):
            value = part[pos]
            if value in ('=', '{', '[') and not depth:
                break
            if value == '(':
                if part[pos-1:pos] and part[pos-1] in ('__declspec', 'alignas', '__attribute__'):
                    declaration.pop()
                    end = matching(part, pos)
                    if end is None:
                        break
                    pos = end + 1
                    continue
                # A pointer-to-function declaration has the object name
                # inside (*name), unlike a function declaration or call.
                end = matching(part, pos)
                inner = part[pos+1:end] if end is not None else []
                if inner and inner[0] in ('*', '&'):
                    declaration.extend(range(pos+1, end))
                    break
                # Parenthesized direct initialization with a manifest expression.
                # All other T f(...) forms are left to the compiler.
                if end is not None and inner and (
                    part_tokens[pos+1].kind in ('literal', 'number')
                    or inner[0] in ('true', 'false', 'nullptr', '&')
                ):
                    break
                declaration = []
                break
            if value == '<':
                depth += 1
            elif value in ('>', '>>') and depth:
                depth = max(0, depth - len(value))
            elif not depth:
                declaration.append(pos)
            pos += 1

        if not declaration:
            continue
        last = declaration[-1]
        name = part[last]
        if not IDENT.fullmatch(name) or name in NOT_NAMES:
            continue
        name_start = last
        while (name_start >= 2 and part[name_start-1] == '::'
               and IDENT.fullmatch(part[name_start-2])):
            name_start -= 2
        if index == 0 and name_start == 0:
            continue
        spelling = ''.join(part[name_start:last+1])
        prefix = part[:name_start]
        is_internal = (
            'static' in values[:boundaries[1]-1] and '::' not in spelling
            or '@anonymous' in namespace
        )
        pointer = max((i for i, word in enumerate(prefix) if word in ('*', '&')), default=-1)
        if not is_c and 'const' in prefix[pointer+1:] and 'extern' not in prefix and '::' not in spelling:
            is_internal = True
        yield Definition('global', '::'.join((*namespace, spelling)), part_tokens[last].line, is_internal)


def walk_definitions(source, is_c=False, include_functions=False, include_internal=False):
    """Find explicit definitions by scope, without expanding macros or includes."""
    skip = {i for start, end in source.directives() for i in range(start, end)}
    tokens = [t for i, t in enumerate(source.tokens) if i not in skip]
    values = [t.value for t in tokens]
    namespace, scopes = (), []
    start = i = 0
    while i < len(values):
        value = values[i]
        if value in ('(', '['):
            close = matching(values, i)
            if close is not None:
                i = close
        elif value == '{':
            head = ' '.join(values[start:i])
            ns = NAMESPACE.fullmatch(head)
            cls = CLASS_HEAD.fullmatch(head)
            if ns or LINKAGE.fullmatch(head):
                scopes.append(namespace)
                if ns:
                    name = re.sub(r'\s+', '', ns[1]) if ns[1] else '@anonymous'
                    namespace = (*namespace, name)
                start = i + 1
            elif cls:
                name = re.sub(r'\s+', '', cls['name'])
                args = re.sub(r'\s+', '', cls['args'] or '')
                if not include_functions:
                    yield Definition('type', '::'.join((*namespace, name + args)),
                                     tokens[start].line, '@anonymous' in namespace)
                end = matching(values, i)
                if end is None:
                    return
                i = end
                # Handle a tagged type with a namespace-scope object declarator.
                if (values[start] != 'typedef' and i+1 < len(values)
                    and (IDENT.fullmatch(values[i+1]) or values[i+1] in ('*', '&'))):
                    start = i
                    tokens[start] = replace(tokens[start], value="int", kind="word")
                    values[start] = 'int'
                else:
                    start = i + 1
            else:
                close = matching(values, i)
                if close is None:
                    return
                # Initializer braces belong to the object declaration. A
                # function body is skipped and resets the statement boundary.
                locator = function_locator(values, start, i, namespace)
                if locator is not None:
                    if include_functions and (
                        include_internal or ('static' not in values[start:i] and '@anonymous' not in namespace)
                    ):
                        yield (locator, tuple(values[start:close+1])), tokens[start].line
                    start = close + 1
                i = close
        elif value == ';':
            if not include_functions:
                yield from defined_objects(tokens[start:i], namespace, is_c)
            start = i + 1
        elif value == '}':
            if scopes:
                namespace = scopes.pop()
            start = i + 1
        i += 1



def function_locator(values, start, end, namespace):
    """Locate explicit top-level function declarators, chiefly engine methods."""
    for opening in range(start, end):
        value = values[opening]
        if value == '=':
            return None
        if value != '(':
            continue
        if opening <= start:
            return None
        name_end = opening-1
        name = values[name_end]
        if name in ('__declspec', '__attribute__', 'alignas', '__attribute'):
            return None
        if not IDENT.fullmatch(name) or name in NOT_NAMES:
            return None
        name_start = name_end
        if name_start > start and values[name_start-1] == '~':
            name_start -= 1
        while (name_start >= start + 2 and values[name_start-1] == '::'
               and IDENT.fullmatch(values[name_start-2])):
            name_start -= 2
        if name_start == start and not ('::' in values[name_start:opening]):
            return None
        return '::'.join((*namespace, ''.join(values[name_start:opening])))
    return None


def functions(source, *, include_internal=False):
    """Yield (identity, lexical body), line for direct function definitions."""
    yield from walk_definitions(source, include_functions=True, include_internal=include_internal)


def definitions(source, *, is_c=False):
    """Yield named types and global objects."""
    yield from walk_definitions(source, is_c=is_c)


TYPE_KEYWORDS = {'class', 'struct', 'union'}
ATTRIBUTE_START = {'__declspec', '__attribute__', '__attribute', 'alignas'}


def type_sites(source):
    """Find class/struct/union definitions at any lexical scope in a source."""
    hidden = {i for start, end in source.directives() for i in range(start, end)}
    tokens = [t for i, t in enumerate(source.tokens) if i not in hidden]
    values = [t.value for t in tokens]
    for index, category in enumerate(values):
        if category not in TYPE_KEYWORDS or (index and values[index-1] == 'enum'):
            continue
        cursor = index+1
        cursor = after_attributes(values, cursor)
        if values[cursor:cursor+1] == ['{']:
            yield tokens[index].line, (category, '')
            continue
        if cursor >= len(tokens) or tokens[cursor].kind != 'word':
            continue
        start = cursor
        cursor += 1
        while (values[cursor:cursor+1] == ['::'] and cursor+1 < len(tokens)
               and tokens[cursor+1].kind == 'word'):
            cursor += 2
        if values[cursor:cursor+1] == ['<']:
            depth = 0
            while cursor < len(values):
                word = values[cursor]
                if word in (';', '{', '}'):
                    break
                if word == '<':
                    depth += 1
                elif word in ('>', '>>'):
                    depth -= len(word)
                cursor += 1
                if not depth:
                    break
        name = ''.join(values[start:cursor])
        cursor = after_attributes(values, cursor)
        if values[cursor:cursor+1] == ['final']:
            cursor += 1
        if values[cursor:cursor+1] == [':']:
            cursor += 1
            if values[cursor:cursor+1] not in (['private'], ['protected'], ['public'], ['virtual']):
                # A named base may follow immediately. A numeric bitfield
                # after an elaborated enum declaration cannot be a base.
                if cursor >= len(tokens) or tokens[cursor].kind != 'word':
                    continue
            while cursor < len(values) and values[cursor] not in ('{', ';', '}'):
                cursor += 1
        if values[cursor:cursor+1] == ['{']:
            yield tokens[index].line, (category, name)


def after_attributes(values, cursor):
    while cursor < len(values):
        start = cursor
        if values[cursor] in ATTRIBUTE_START and values[cursor+1:cursor+2] == ['(']:
            start = cursor+1
        elif values[cursor:cursor+2] != ['[', '[']:
            break
        close = matching(values, start)
        if close is None:
            return len(values)
        cursor = close+1
    return cursor
