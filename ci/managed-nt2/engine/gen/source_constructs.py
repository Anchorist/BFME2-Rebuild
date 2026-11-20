"""Match source rules against C++ tokens, keeping semantic pragma operands."""
from functools import lru_cache
from cpp import Source


@lru_cache(maxsize=32)
def source_forms(text):
    # VC7.1 predates raw string literals. Parse its ordinary string grammar.
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    source = Source(normalized, raw_strings=False)
    alias = False
    if "alternatename" in normalized.casefold():
        for start, end in source.directives():
            tokens = source.tokens[start:end]
            if (len(tokens) >= 3 and tokens[1].value == "pragma" and tokens[2].value == "comment"
                    and any(tok.kind == "literal" and "alternatename" in tok.value.casefold()
                            for tok in tokens[3:])):
                alias = True
                break
    # Retain only the compact view, never the token arrays or comments.
    return source.code, alias


def code_only(text):
    return source_forms(text)[0]


def banned(text, pattern):
    code, alias = source_forms(text)
    return alias or bool(pattern.search(code))
