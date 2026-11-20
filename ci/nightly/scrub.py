"""Make text from the private game machine safe to publish.

Every string the game stage reports passes through `scrub`: absolute paths keep only their last part, and anything
the repository's public-text check would flag is replaced by `[removed]`. Numbers, hashes and booleans pass unchanged.
"""
import importlib.util
from pathlib import Path
import re

_spec = importlib.util.spec_from_file_location("public_text_check", Path(__file__).resolve().parents[1] / "public-text/check.py")
_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_check)

PATH = re.compile(r"(?<![\w.])(?:[A-Za-z]:)?(?:[\\/][\w.~$@+-]+){2,}[\\/]?")
LIMIT = 400


def scrub_text(text):
    text = PATH.sub(lambda m: "…/" + re.split(r"[\\/]", m.group(0).rstrip("\\/"))[-1], text)
    for rx in _check.PATTERNS.values():
        text = rx.sub("[removed]", text)
    return text[:LIMIT]


def scrub(value):
    if isinstance(value, str):
        return scrub_text(value)
    if isinstance(value, list):
        return [scrub(v) for v in value]
    if isinstance(value, dict):
        return {scrub_text(k) if isinstance(k, str) else k: scrub(v) for k, v in value.items()}
    return value
