"""Attribute changed source lines to actual function definitions and trusted row IDs."""
from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
import re

LITERALS = re.compile(r'/\*[\s\S]*?\*/|//[^\n]*|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'')
DIRECTIVES = re.compile(r'^[ \t]*#[^\n]*', re.M)
BODY = re.compile(
    r'(?<![\w:])(?P<name>(?:[A-Za-z_]\w*\s*::\s*)*~?[A-Za-z_]\w*)\s*'
    r'\([^;{}]*\)\s*(?:const\s*)?(?:volatile\s*)?(?:throw\s*\([^{}]*\)\s*)?'
    r'(?::[^;{}:]*)?$')
CLASS = re.compile(r'\b(?:class|struct)\s+(?:__declspec\s*\([^)]*\)\s*)?([A-Za-z_]\w*)[^;{}()]*$')
NAMESPACE = re.compile(r'\bnamespace(?:\s+([A-Za-z_]\w*))?\s*$')
KEYWORDS = {"if", "while", "for", "switch", "catch", "sizeof", "return", "else"}
RVA = re.compile(r"0x[0-9a-fA-F]{1,8}\Z")
SIMPLE = re.compile(r"[A-Za-z_]\w*\Z")


@dataclass(frozen=True)
class Function:
    name: str
    begin: int
    end: int
    rva: int | None


def blank(match):
    return re.sub(r"[^\n]", " ", match[0])


def names(symbol):
    if symbol.startswith(("??0", "??1")) and "?$" not in symbol:
        scopes = symbol[3:].split("@@", 1)[0].split("@")
        if scopes and all(SIMPLE.fullmatch(x) for x in scopes):
            return "::".join([*reversed(scopes), ("~" if symbol[2] == "1" else "") + scopes[0]])
    if symbol.startswith("?") and not symbol.startswith("??") and "?$" not in symbol:
        scopes = symbol[1:].split("@@", 1)[0].split("@")
        if all(SIMPLE.fullmatch(x) for x in scopes):
            return "::".join(reversed(scopes))
    common = symbol.removeprefix("_").split("@", 1)[0]
    if SIMPLE.fullmatch(common):
        return common
    return None


def spans(text, annotation):
    code = DIRECTIVES.sub(blank, LITERALS.sub(blank, text))
    newlines = [m.start() for m in re.finditer("\n", code)]
    original = text.splitlines()
    stack = []
    start = 0
    functions = []
    for token in re.finditer(r"[{};]", code):
        pos, char = token.start(), token[0]
        if char == "}":
            if stack:
                kind, value = stack.pop()
                if kind == "function":
                    name, begin, rva = value
                    functions.append(Function(name, begin, bisect_right(newlines, pos) + 1, rva))
        elif char == "{":
            raw = code[start:pos].rstrip()
            family = CLASS.search(raw)
            space = NAMESPACE.search(raw)
            method = BODY.search(raw) if not any(k in {"function", "block"} for k, _ in stack) else None
            if family:
                stack.append(("class", family[1]))
            elif space:
                stack.append(("namespace", space[1]))
            elif method and (word := re.sub(r"\s+", "", method["name"])).split("::")[-1] not in KEYWORDS:
                scope = [s for k, s in stack if k in {"class", "namespace"} and s]
                qualified = "::".join([*scope, word]) if "::" not in word else "::".join([
                    *[s for k, s in stack if k == "namespace" and s], word])
                line = bisect_right(newlines, start + method.start("name")) + 1
                rva = nearest_annotation(original, line, annotation)
                stack.append(("function", (qualified, line, rva)))
            elif re.search(r'\bextern\s*$', raw):
                stack.append(("extern", None))
            else:
                stack.append(("block", None))
        start = pos + 1
    return functions


def nearest_annotation(lines, begin, annotation):
    for line in reversed(lines[max(0, begin - 7):begin - 1]):
        mark = annotation.search(line)
        if mark:
            return int(mark[1], 16)
        if line.strip() and not line.lstrip().startswith("//"):
            break
    return None


def indexed_rows(owner_map):
    by_name = defaultdict(list)
    by_path = defaultdict(list)
    for rva, (path, symbol, _size) in owner_map.functions.items():
        if label := names(symbol):
            by_name[label].append((rva, path))
            by_path[(path, label)].append((rva, path))
    return by_name, by_path


def edited(git, land, base, tip, owner_map):
    raw = git.run("diff", "-U0", "--no-color", "--no-ext-diff", "--no-renames", base, tip, "--", "src", "include").stdout
    changes = land.land_gate9.diff_lines(raw.decode("utf-8", "replace"))
    by_name, by_path = indexed_rows(owner_map)
    found = {}
    for path, lines in sorted(changes.items()):
        path_spans = []
        for rev in (base, tip):
            text = git.run("show", f"{rev}:{path}", check=False).stdout.decode("utf-8", "replace")
            path_spans.append(spans(text, land.ANNOT))
        defined = [{f.name: f for f in functions} for functions in path_spans]
        for side, functions, altered in zip((0, 1), path_spans, lines, strict=True):
            touched = {number for number, text in altered
                       if text.strip() and not text.lstrip().startswith(("//", "/*", "*"))}
            if not touched:
                continue
            for function in functions:
                if touched.isdisjoint(range(function.begin, function.end + 1)):
                    continue
                targets = by_path[(path, function.name)] if path.startswith("src/") else by_name[function.name]
                identity = None
                if function.rva in owner_map.functions and (path.startswith("include/") or
                                                             owner_map.path(function.rva) == path):
                    identity = function.rva, owner_map.path(function.rva)
                elif len(targets) == 1:
                    identity = targets[0]
                old = defined[0].get(function.name)
                new = defined[1].get(function.name)
                source = (identity[1] or path) if identity else path
                found[(path, function.name, identity)] = {
                    "path": path, "function": function.name, "address": identity[0] if identity else None,
                    "owner": source, "before_body": old is not None, "after_body": new is not None,
                    "line": (new or old or function).begin,
                }
    return sorted(found.values(), key=lambda row: (row["path"], row["line"], row["function"]))
