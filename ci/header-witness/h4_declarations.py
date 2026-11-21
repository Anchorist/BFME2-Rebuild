"""H4 declaration inventory from the compiler's own preprocessing.

The protected compiler preprocesses a probe that includes one changed header (`cl -E`, the same include paths and
defines as the probe compiles). Its output keeps `#line N "file"` markers, expands macros and drops inactive
conditional branches. `own_text()` rebuilds the header's own lines from that output, line for line, so every
declaration keeps its original line number. The lexical inventory of tools/gates (header_lexical_inventory) then
reads that text: a declaration made by a macro is seen, one in a dead branch is not.

`read()` returns the declarations and what stayed unreadable. A layout assertion of the form the raw reader accepts
(`typedef char X[(offsetof(...) == N) ? 1 : -1]`) is read from the raw line, since expansion turns `offsetof` into
an expression the lexical reader does not take. The inventory is complete only when nothing else stayed unreadable;
otherwise H4 holds by name.
"""
import re

LINE = re.compile(r'^\s*#\s*line\s+(\d+)\s+"((?:[^"\\]|\\.)*)"\s*$')
MAX_LINES = 400000


class Held(Exception):
    pass


def _same_file(marker, relative):
    """Does a #line path name this header? Compared by its include-relative suffix, case-insensitively, with
    either separator (the compiler prints the path it opened)."""
    path = marker.replace("\\\\", "/").replace("\\", "/").lower()
    suffix = relative.replace("\\", "/").lower()
    return path.endswith("/" + suffix) or path == suffix


def own_text(preprocessed, header, relative):
    """The header's own lines, rebuilt from preprocessed output."""
    lines = preprocessed.split("\n")
    if len(lines) > MAX_LINES:
        raise Held("The preprocessed output is too large.")
    own, current, number, seen = {}, False, 0, False
    for line in lines:
        match = LINE.match(line)
        if match:
            number, current = int(match.group(1)), _same_file(match.group(2), relative)
            seen = seen or current
            continue
        if current and line.strip():
            own[number] = (own[number] + " " + line.strip()) if own.get(number, "").strip() else line
        number += 1
    if not seen:
        raise Held(f"The preprocessed output never entered {header}.")
    if not own:
        return ""
    return "\n".join(own.get(index, "") for index in range(1, max(own) + 1)) + "\n"


def read(preprocessed, header, relative, raw, lexical):
    """(declarations, unreadable) for one side. `lexical` is tools/gates header_lexical_inventory; `raw` is the
    header's own bytes on that side, used only for layout assertions."""
    expanded = lexical.inventory(header, own_text(preprocessed, header, relative))
    raw_lines = raw.split("\n")
    raw_reading = lexical.inventory(header, raw)
    raw_opaque = {item.line for item in raw_reading.unknown}
    unreadable = []
    for item in expanded.unknown:
        text = raw_lines[item.line - 1] if 0 < item.line <= len(raw_lines) else ""
        is_assertion = (tuple(item.tokens[:2]) == ("typedef", "char") and re.search(r"\b(?:offsetof|sizeof)\s*\(", text)
                        and item.line not in raw_opaque)
        if not is_assertion:
            unreadable.append(item)
    return expanded.declarations, tuple(unreadable)


def compare(before, after, lexical):
    """before/after: (preprocessed, header, relative, raw) or None for a side where the header does not exist.
    Returns (before_declarations, after_declarations, complete, unreadable)."""
    results = []
    for side in (before, after):
        results.append(((), ()) if side is None else read(*side, lexical))
    (old, old_unknown), (new, new_unknown) = results
    unreadable = tuple(old_unknown) + tuple(new_unknown)
    return tuple(old), tuple(new), not unreadable, unreadable
