"""Detect new explicit inlining suppression in source and header changes."""
from collections import Counter
from dataclasses import dataclass

from cpp import Source, matching
from rules import Finding

ALIASES = {"__noinline", "__noinline__"}
ATTRIBUTES = {"__declspec", "__attribute__", "__attribute"}
NAMES = {"noinline", "__noinline", "__noinline__"}


@dataclass(frozen=True)
class Site:
    line: int
    declaration: tuple[str, ...]
    marker: int
    scopes: tuple[tuple[str, ...], ...]


def segments(source):
    """Yield lexical declaration heads and whole preprocessor directives."""
    tokens = source.tokens
    ranges = dict(source.directives())
    values = source.ordered
    scopes = []
    start = cursor = 0
    while cursor < len(values):
        if cursor in ranges:
            if start < cursor:
                yield tuple(scopes), tokens[start:cursor]
            stop = ranges[cursor]
            yield tuple(scopes), tokens[cursor:stop]
            start = cursor = stop
            continue
        value = values[cursor]
        if value in ("(", "["):
            close = matching(values, cursor)
            if close is not None:
                cursor = close + 1
                continue
        if value in (";", "{", "}"):
            if start < cursor:
                yield tuple(scopes), tokens[start:cursor]
            if value == "{":
                scopes.append(values[start:cursor])
            if value == "}" and scopes:
                scopes.pop()
            start = cursor + 1
        cursor += 1
    if start < len(values):
        yield tuple(scopes), tokens[start:]


def direct_attributes(values, start, stop):
    cursor = start
    while cursor < stop:
        value = values[cursor]
        if value in ("(", "[", "{"):
            close = matching(values, cursor)
            if close is None or close >= stop:
                return
            cursor = close + 1
            continue
        if value in NAMES:
            yield cursor
        cursor += 1


def markers(values):
    cursor = 0
    while cursor < len(values):
        value = values[cursor]
        if value in ATTRIBUTES and values[cursor + 1:cursor + 2] == ("(",):
            opening = cursor + 1
            close = matching(values, opening)
            if close is not None:
                start, stop = opening + 1, close
                if value != "__declspec" and values[start:start + 1] == ("(",) and matching(values, start) == close - 1:
                    start, stop = start + 1, close - 1
                yield from direct_attributes(values, start, stop)
                cursor = close + 1
                continue
        if values[cursor:cursor + 2] == ("[", "["):
            close = matching(values, cursor)
            if close is not None and values[close - 1:close + 1] == ("]", "]"):
                yield from direct_attributes(values, cursor + 2, close - 1)
                cursor = close + 1
                continue
        if value in ALIASES:
            yield cursor
        cursor += 1


def sites(text):
    for scopes, tokens in segments(Source(text)):
        values = tuple(token.value for token in tokens)
        for index in markers(values):
            yield Site(tokens[index].line, values, index, scopes)


def check_noinline(path, before, after):
    """Refuse newly introduced noinline controls, including controls in macros."""
    old = Counter((site.scopes, site.declaration, site.marker) for site in sites(before))
    result = []
    for site in sites(after):
        identity = site.scopes, site.declaration, site.marker
        if old[identity]:
            old[identity] -= 1
        else:
            result.append(Finding(
                path, site.line, "H8", "This change adds an explicit noinline control.",
                "Remove the attribute or macro and give the function its ordinary declaration.",
            ))
    return sorted(set(result))
