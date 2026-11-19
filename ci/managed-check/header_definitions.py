"""Protected global class census used by the contributor report."""
import re

DUPCLASS_DEF = re.compile(r'^(?:template\s*<[^>]*>\s*)?(?:class|struct)\s+(?:__declspec\([^)]*\)\s*)?([A-Za-z_]\w*)(?!\s*::)\s*(?:final\s*)?(?::(?!:)[^;{]*)?(?:\{.*)?$')
DUPCLASS_DEF_M = re.compile(DUPCLASS_DEF.pattern, re.M)


_DUP_BLANK = re.compile(r'"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'|/\*.*?\*/|//[^\n]*', re.S)


def _dup_blank(text):
    """TEXT with comments and string/char literals blanked (same length, newlines kept)."""
    return _DUP_BLANK.sub(lambda m: re.sub(r'[^\n]', ' ', m.group(0)), text)


def global_class_defs(text):
    """gen8 dup2: names of classes/structs DEFINED at global scope in TEXT (inside extern "C" counts as global; inside a
    namespace, another class or a function does not). `class A::B {` defines no A."""
    code = _dup_blank(text)
    defs = sorted((m.start(), m.group(1)) for m in DUPCLASS_DEF_M.finditer(code))
    out, stack, last, k = set(), [], 0, 0
    for i, ch in enumerate(code):
        while k < len(defs) and defs[k][0] <= i:
            if all(kind == 'extern' for kind in stack):
                out.add(defs[k][1])
            k += 1
        if k >= len(defs):
            break
        if ch == '{':
            head = code[last:i]
            if re.search(r'\bnamespace\b[^;{}]*$', head):
                kind = 'ns'
            elif re.search(r'\bextern\s*$', head):
                kind = 'extern'
            elif re.search(r'\b(class|struct|union|enum)\b[^;{}()]*$', head):
                kind = 'type'
            else:
                kind = 'code'
            stack.append(kind); last = i + 1
        elif ch == '}':
            if stack:
                stack.pop()
            last = i + 1
        elif ch == ';':
            last = i + 1
    return out


