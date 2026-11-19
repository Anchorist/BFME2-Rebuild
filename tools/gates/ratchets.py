"""Count explicit stand-in constructs on lexed source."""

import re


RULES = (
    'void_pointer', 'reinterpret_cast', 'c_pointer_cast', 'this_arithmetic',
    'cast_call_result',
)
FIXES = {
    'void_pointer': 'Declare the pointee type shown by the function and its callers.',
    'reinterpret_cast': 'Use the declared object or pointee type directly.',
    'c_pointer_cast': 'Use the declared pointer type directly and correct the signature where needed.',
    'this_arithmetic': 'Access the typed member or base directly through this.',
    'cast_call_result': 'Declare the callee return type so its caller can use it without a cast.',
}

WORD = r'[^\W\d]\w*'
QUALIFIED = rf'{WORD}(?:\s*::\s*{WORD})*'
TYPE = rf'(?:::)?\s*{QUALIFIED}(?:\s*<[^;{{}}()]*?>)?(?:\s+{QUALIFIED})*'
C_TARGET = re.compile(
    rf'(?P<type>{TYPE})(?P<tail>(?:\s*[*&](?:\s*(?:const|volatile)\b)*)*)\s*$'
)
QUALIFIER = r'(?:const|volatile|__restrict|__restrict__)'
VOID_DECL = re.compile(
    rf'\bvoid\s*(?:{QUALIFIER}\b\s*)*\*\s*(?:{QUALIFIER}\b\s*)*'
    rf'(?:[*&]\s*(?:{QUALIFIER}\b\s*)*)*(?={WORD}\b|[,)>]|\[|\(\s*\*)'
)
FUNDAMENTAL_CAST = {
    'char', 'wchar_t', 'char8_t', 'char16_t', 'char32_t', 'int', 'signed',
    'unsigned', 'short', 'long', 'bool', 'float', 'double', '__int8', '__int16',
    '__int32', '__int64',
}
NAMED_CAST = {'reinterpret_cast', 'static_cast', 'const_cast', 'dynamic_cast'}
NOT_CALL = {'sizeof', '__alignof', 'alignof', 'alignas', 'decltype', 'typeid', 'noexcept',
            'return', 'if', 'while', 'switch', 'case', 'for', 'static_assert',
            'delete', 'new', 'throw', 'catch'}
BYTE_TYPES = {'char', 'int8_t', 'uint8_t', 'BYTE', 'Byte', '__int8', 'byte'}
ARITHMETIC = {'+', '-', '++', '--', '+=', '-=', '['}
WORD_LEFT = {'return', 'throw', 'case', 'co_return', 'co_yield'}
NO_OPERAND = {')', ']', '[', '}', '{', ';', ',', ':', '=', 'const', 'volatile', 'noexcept'}
UNARY_CONTEXT = {'(', '[', '=', ',', ';', '{', '}', '?', ':', '!', '~',
                 '*', '+', '-'} | WORD_LEFT
BARE_DECL = re.compile(r'(?:(?:const|volatile|static)\s+)*'
                       rf'{QUALIFIED}(?:\s+{QUALIFIED})*\s*[*&]*\s*({WORD})$')


def group_ends(values):
    """Match balanced parentheses once for all the recognizers."""
    stack, ends = [], {}
    for i, value in enumerate(values):
        if value == '(':
            stack.append(i)
        elif value == ')' and stack:
            ends[stack.pop()] = i
    return ends


def named_target_end(values, index):
    if values[index+1:index+2] != ('<',):
        return None
    depth = 0
    for i in range(index+1, len(values)):
        value = values[i]
        if value == '<':
            depth += 1
        elif value in ('>', '>>'):
            depth -= len(value)
            if depth == 0:
                return i
            if depth < 0:
                break
        elif value in (';', '{', '}'):
            break
    return None


def c_target(source, index, close):
    values = source.ordered
    before = values[index-1] if index else ''
    if (before.isidentifier() and before not in WORD_LEFT
        or before in ('::', '.', '->', ')', ']')
        or close+1 == len(values) or values[close+1] in NO_OPERAND):
        return None
    if close - index > 100:
        return None
    start, end = source.tokens[index].offset+1, source.tokens[close].offset
    target = source.code[start:end].strip()
    simple = C_TARGET.fullmatch(target)
    if simple:
        return '*' in simple['tail']
    # C++ declarator forms such as (void (__cdecl *)(int))handler.
    function = re.fullmatch(
        rf'{TYPE}\s*\(\s*(?:(?:__cdecl|__stdcall|__fastcall|__thiscall)\s*)?'
        r'\*+\s*\)\s*(?:\([^;{}]*\)|\[[^;{}]*\])', target
    )
    return True if function else None


def call_end(source, starts, start, limit):
    """Recognize a direct call operand. Parenthesized compound values are excluded."""
    values = source.ordered
    wrappers = []
    while start < limit and values[start] == '(':
        close = starts.get(start)
        if close is None or close >= limit:
            return None
        wrappers.append(close)
        limit = close
        start += 1
    if values[start:start+1] == ('::',):
        start += 1
    has_name = False
    while start < limit:
        token = source.tokens[start]
        if token.kind != 'word' or token.value in NOT_CALL:
            return None
        has_name = True
        start += 1
        if values[start:start+1] == ('<',):
            close = named_target_end(values, start-1)
            if close is None or close >= limit:
                return None
            start = close + 1
        if values[start:start+1] not in (('::',), ('.',), ('->',)):
            break
        start += 1
    if not has_name or start >= limit or values[start] != '(':
        return None
    end = starts.get(start)
    if end is None or end >= limit:
        return None
    # A postfix chain can include calls that return callable values or
    # receivers for another member call. Only a call at its end qualifies.
    is_call = True
    while end+1 < limit:
        op = values[end+1]
        if op == '(' and end+1 in starts:
            end = starts[end+1]
            is_call = True
        elif op in ('.', '->') and end+2 < limit and source.tokens[end+2].kind == 'word':
            end += 2
            is_call = False
        elif op in ('[', '++', '--'):
            return None
        else:
            break
    if not is_call or end >= limit:
        return None
    for close in reversed(wrappers):
        if close != end + 1:
            return None
        end = close
    return end


def casts(source, groups, positions):
    values = source.ordered
    c_casts, named_casts, type_targets = {}, {}, []
    for index, word in enumerate(values):
        line = source.tokens[index].line
        if word in NAMED_CAST:
            if word == 'reinterpret_cast':
                positions['reinterpret_cast'].append(line)
            end = named_target_end(values, index)
            if end is None or values[end+1:end+2] != ('(',):
                continue
            close = groups.get(end+1)
            if close is not None:
                named_casts[end+1] = index
                type_targets.append((source.tokens[index+1].stop, source.tokens[end].stop))
                if call_end(source, groups, end+2, close) == close-1:
                    positions['cast_call_result'].append(line)
        elif word == '(' and index in groups:
            close = groups[index]
            target = c_target(source, index, close)
            if target is None:
                continue
            c_casts[close] = index
            if target:
                positions['c_pointer_cast'].append(line)
            type_targets.append((source.tokens[index].stop, source.tokens[close].stop))
            if call_end(source, groups, close+1, len(values)) is not None:
                positions['cast_call_result'].append(line)
        elif (word in FUNDAMENTAL_CAST and values[index+1:index+2] == ('(',)
              and values[max(0,index-1):index] not in (('operator',), ('::',), ('.',), ('->',))):
            close = groups.get(index+1)
            if close is not None and call_end(source, groups, index+2, close) == close-1:
                positions['cast_call_result'].append(line)
    return c_casts, named_casts, sorted(type_targets)


def around_pointer(values, groups, c_casts, named_casts, index):
    """Return the extent of a this/alias expression, including enclosing casts."""
    start = end = index
    while start:
        left = start - 1
        if left in c_casts:
            start = c_casts[left]
            continue
        if values[left] != '(' or groups.get(left) != end + 1:
            break
        if left not in named_casts and left and left-1 not in c_casts and (
            values[left-1].isidentifier() and values[left-1] not in WORD_LEFT
            or values[left-1] in (')', ']', '>', '>>')
        ):
            break
        start = named_casts.get(left, left)
        end += 1
    return start, end


def is_unary(values, i):
    if i == 0:
        return True
    return values[i-1] in UNARY_CONTEXT


def this_offsets(source, groups, c_casts, named_casts):
    """Recognize direct arithmetic and simple local byte-pointer aliases."""
    values = source.ordered
    aliases = [{}]
    emit = set()
    statement = 0
    for i, value in enumerate(values):
        if value == '{':
            aliases.append({})
            statement = i + 1
        elif value == '}' and len(aliases) > 1:
            aliases.pop()
            statement = i + 1
        elif value == ';':
            if any(aliases) and i - statement <= 50 and statement < i:
                first, last = source.tokens[statement], source.tokens[i]
                match = BARE_DECL.fullmatch(source.code[first.offset:last.offset].strip())
                if match and match[1] in values[statement:i] and visible_alias(aliases, match[1]):
                    if values[statement] not in WORD_LEFT:
                        aliases[-1][match[1]] = False
            statement = i + 1
        elif value == '=' and i and values[i-1].isidentifier():
            end = i + 1
            while end < len(values) and values[end] not in (';', '{', '}'):
                end += 1
            rhs = values[i+1:end]
            start = i - 1
            while start and values[start-1] not in (';', '{', '}', '('):
                start -= 1
            lhs = values[start:i]
            name = values[i-1]
            byte_pointer = bool(
                '*' in lhs and BYTE_TYPES.intersection(lhs)
                or '*' in rhs and BYTE_TYPES.intersection(rhs)
                or 'auto' in lhs and any(visible_alias(aliases, a) for a in rhs)
                or len(lhs) == 1 and visible_alias(aliases, name)
            )
            if byte_pointer and lhs and not any(x in lhs for x in ('.', '->')):
                derived = derived_rhs(values, groups, c_casts, named_casts, aliases, i+1, end)
                if len(lhs) > 1:
                    aliases[-1][name] = derived
                else:
                    scope = next((scope for scope in reversed(aliases) if name in scope), aliases[-1])
                    scope[name] = derived
            elif len(lhs) > 1:
                aliases[-1][name] = False
        elif value == 'this' or visible_alias(aliases, value):
            if i and values[i-1] in ('.', '->', '::'):
                continue
            start, end = around_pointer(values, groups, c_casts, named_casts, i)
            left, right = start - 1, end + 1
            if left >= 0 and values[left] in ('*', '&') and is_unary(values, left):
                continue
            if right < len(values) and values[right] in ARITHMETIC:
                emit.add(right)
            if left >= 0 and values[left] in ('++', '--'):
                emit.add(left)
            if (left >= 0 and values[left] == '+' and not is_unary(values, left)
                and values[right:right+1] not in (('[',), ('.',), ('->',), ('(',))):
                emit.add(left)
    return sorted(emit)


def visible_alias(scopes, name):
    return next((scope[name] for scope in reversed(scopes) if name in scope), False)


def derived_rhs(values, groups, c_casts, named_casts, aliases, begin, end):
    for i in range(begin, end):
        if values[i] != 'this' and not visible_alias(aliases, values[i]):
            continue
        left, right = around_pointer(values, groups, c_casts, named_casts, i)
        if left == begin and (right+1 == end or values[right+1] in ('+', '-')):
            return True
    return False


def counts(source):
    positions = {key: [] for key in RULES}
    groups = group_ends(source.ordered)
    c_casts, named_casts, type_targets = casts(source, groups, positions)
    target_index = 0
    for item in VOID_DECL.finditer(source.code):
        left = source.code[max(0, item.start()-160):item.start()]
        if re.search(r'\b(?:sizeof|alignof|__alignof)\s*\(?\s*$', left):
            continue
        while target_index < len(type_targets) and type_targets[target_index][1] <= item.start():
            target_index += 1
        if target_index < len(type_targets) and type_targets[target_index][0] <= item.start():
            continue
        positions['void_pointer'].append(source.line(item.start()))
    positions['this_arithmetic'] = [source.tokens[i].line
                                    for i in this_offsets(source, groups, c_casts, named_casts)]
    return positions

