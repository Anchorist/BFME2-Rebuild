"""Lexical helpers for the source gate. This module never preprocesses C++."""

from bisect import bisect_right
from dataclasses import dataclass
import re


TOKEN = re.compile(
    r'(?P<line>//[^\n]*)|(?P<block>/\*[\s\S]*?(?:\*/|\Z))'
    r'|(?P<raw>(?:u8|[LuU])?R"(?P<delimiter>[^ ()\\\t\n]{0,16})\()'
    r'|(?P<literal>(?:u8|[LuU])?(?:"(?:\\.|[^"\\\n])*(?:"|(?=\n|\Z))'
    r"|'(?:\\.|[^'\\\n])*(?:'|(?=\n|\Z))))"
    r'|(?P<word>[^\W\d]\w*)|(?P<number>(?:\d|\.\d)(?:[\w.]|\x27(?=\w)|(?<=[eEpP])[+-])*)'
    r'|(?P<operator>::|->\*|->|\.\*|\.\.\.|<<=|>>=|<<|>>|<=|>=|==|!=|'
    r'\+=|-=|\*=|/=|%=|&=|\|=|\^=|\+\+|--|&&|\|\||##|%:%:|%:|<:|:>|<%|%>|[^\s])'
)
SPLICE = re.compile(r'\\[ \t]*\n')
BLANK = re.compile(r'[^\n]')
DIGRAPH = {'%:': '#', '%:%:': '##', '<:': '[', ':>': ']', '<%': '{', '%>': '}'}
TRIGRAPH = {'=': '#', '/': '\\', "'": '^', '(': '[', ')': ']',
            '!': '|', '<': '{', '>': '}', '-': '~'}


@dataclass(frozen=True, slots=True)
class Token:
    value: str
    kind: str
    line: int
    end_line: int
    offset: int
    stop: int


class Source:
    def __init__(self, text):
        self.text = text
        self.lines = text.split('\n')
        # Translation phases 1 and 2. Keep a map to physical Git line numbers.
        # Raw string body contents are opaque; only the closing marker is read.
        text = re.sub(r'\?\?([=/\'()!<>-])', lambda m: TRIGRAPH[m[1]], text)
        text, self.breaks = splice(text)
        self.tokens = []
        self.comments = []
        pieces = []
        pos = 0
        while match := TOKEN.search(text, pos):
            kind = match.lastgroup
            start, end = match.span()
            if kind == 'raw':
                delimiter = ')' + match['delimiter'] + '"'
                closing = text.find(delimiter, end)
                end = len(text) if closing == -1 else closing + len(delimiter)
                kind = 'literal'
            value = text[start:end]
            line, end_line = self.line(start), self.line(max(start, end - 1))
            token = Token(DIGRAPH.get(value, value), kind, line, end_line, start, end)
            if kind in ('line', 'block'):
                self.comments.append(token)
            else:
                self.tokens.append(token)
            if kind in ('line', 'block', 'literal'):
                pieces.extend((text[pos:start], BLANK.sub(' ', value)))
            else:
                pieces.append(text[pos:end])
            pos = end
        pieces.append(text[pos:])
        self.code = ''.join(pieces)
        self.ordered = tuple(t.value for t in self.tokens)

    def line(self, offset):
        return bisect_right(self.breaks, offset) + 1

    def directives(self):
        """Yield [start,end) token intervals for logical preprocessor directives."""
        start = 0
        for end, token in enumerate(self.tokens):
            if (
                end and '\n' in self.code[
                    self.tokens[end-1].stop:token.offset]
            ):
                if self.tokens[start].value == '#':
                    yield start, end
                start = end
        if self.tokens and self.tokens[start].value == '#':
            yield start, len(self.tokens)


def splice(text):
    """Remove line splices and return their physical line boundaries."""
    pieces, breaks = [], []
    pos = logical = 0
    for match in SPLICE.finditer(text):
        fragment = text[pos:match.start()]
        pieces.append(fragment)
        breaks.extend(logical + m.end() for m in re.finditer('\n', fragment))
        logical += len(fragment)
        breaks.append(logical)
        pos = match.end()
    fragment = text[pos:]
    pieces.append(fragment)
    breaks.extend(logical + m.end() for m in re.finditer('\n', fragment))
    return ''.join(pieces), breaks


def decode(raw):
    # A file can contain any mixture of LF and CRLF. A bare CR is rejected
    # by G1. Drop a UTF-8 BOM only at the start of each blob.
    return raw.decode('utf-8-sig').replace('\r\n', '\n')


def matching(values, start):
    """Return index of a matching delimiter, or None for an incomplete group."""
    pairs = {'(': ')', '[': ']', '{': '}'}
    stack = [pairs[values[start]]]
    for i in range(start + 1, len(values)):
        value = values[i]
        if value == stack[-1]:
            stack.pop()
            if not stack:
                return i
        elif value in pairs:
            stack.append(pairs[value])
        elif value in (')', ']', '}'):
            return None
    return None


def include_sites(source):
    """Literal include directives as (physical line, spelling, quoted)."""
    for start, end in source.directives():
        t = source.tokens[start:end]
        if len(t) < 3 or t[1].value != 'include':
            continue
        if len(t) == 3 and t[2].kind == 'literal' and t[2].value.startswith('"') and t[2].value.endswith('"'):
            yield (t[0].line, t[2].value[1:-1], True)
        elif t[2].value == '<' and t[-1].value == '>' and not any(x.value == '>' for x in t[3:-1]):
            yield (t[0].line, ''.join(x.value for x in t[3:-1]), False)

