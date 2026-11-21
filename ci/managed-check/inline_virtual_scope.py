"""Prove when an existing source packet has no material owner changes."""

import re

from cpp import SPLICE, Source

LIMIT = 1024**2
DIRECTIVE_COMMENT = re.compile(r'^//[ \t]*(?:cl(?:-arch)?[ \t]*:|FUNCTION[ \t]*:|(?:dxsdk|psdk|platformsdk|stlport|stlport46|msvcstl)\b|bfmealloc_\w+)', re.I)


def normalized(data):
    # Retain the preprocessor's physical line boundaries and the exact
    # spelling of all literals, directives and non-comment tokens.
    text = data.decode("utf-8-sig").replace("\r\n", "\n")
    if "\r" in text:
        return None
    source = Source(text, raw_strings=False)
    splices = tuple(match[0] for match in SPLICE.finditer(text))
    translated = tuple(re.findall(r"\?\?[=/'()!<>-]", text))
    text = source.logical
    pieces = []
    position = 0
    for item in source.comments:
        if item.kind == "block" and not item.value.endswith("*/"):
            return None
        pieces.append(text[position:item.offset])
        pieces.append(item.value if DIRECTIVE_COMMENT.match(item.value) else " " + "\n" * item.value.count("\n"))
        position = item.stop
    pieces.append(text[position:])
    code = "\n".join(line.rstrip(" \t") for line in "".join(pieces).split("\n")).rstrip("\n")
    lines = tuple((token.line, token.end_line) for token in source.tokens)
    return code, lines, splices, translated


def scope_inputs(git, plan, candidate):
    equivalent, material = [], []
    for path in plan["changed_paths"]:
        blobs = [git.run("cat-file", "blob", f"{revision}:{path}", check=False) for revision in (plan["base"], candidate)]
        if any(blob.returncode or len(blob.stdout) > LIMIT for blob in blobs):
            material.append(path)
            continue
        try:
            before, after = [normalized(blob.stdout) for blob in blobs]
        except (ValueError, UnicodeError):
            material.append(path)
            continue
        (equivalent if before is not None and before == after else material).append(path)
    return {"equivalent": equivalent, "material": material, "complete": not material}
