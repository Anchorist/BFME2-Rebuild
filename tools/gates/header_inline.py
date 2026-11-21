"""Classify changed inline function bodies before requiring behavior evidence."""
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
import re

from cpp import Source
from git_objects import ObjectError
from rules import Finding

RULE = "H6"
IDENTIFIER = re.compile(r"[A-Za-z_]\w*\Z", re.ASCII)


@dataclass(frozen=True)
class InlineBody:
    path: str
    line: int
    qualified: str
    signature: str
    body: str
    fields: tuple[str, ...]
    parameters: tuple[str, ...]
    direct_bases: tuple[str, ...] = ()
    initializers: str = ""


@dataclass(frozen=True, order=True)
class BehaviorEvidence:
    path: str
    line: int
    qualified: str
    signature: str
    body_sha256: str


def body_values(record):
    source = Source(record.body)
    values = source.ordered
    return source, values


def field_reference(value, fields, parameters):
    return (len(value) == 1 and value[0] in fields and value[0] not in parameters
            or len(value) == 3 and value[:2] == ("this", "->") and value[2] in fields)


def base_prefix(spelling):
    parts = spelling.split("::")
    if all(IDENTIFIER.fullmatch(part) for part in parts):
        return tuple(token for part in parts for token in (part, "::"))
    return ()


def shape(record):
    """Accept only a direct member read/store or unchanged arguments to a base."""
    if record.initializers.strip():
        return None
    source, values = body_values(record)
    if list(source.directives()) or len(values) < 4 or values[0] != "{" or values[-2:] != (";", "}"):
        return None
    expression = values[1:-2]
    if expression[0] == "return" and field_reference(expression[1:], record.fields, record.parameters):
        return "member-read"
    if len(expression) >= 3 and expression[-2] == "=" and expression[-1] in record.parameters:
        if field_reference(expression[:-2], record.fields, record.parameters):
            return "member-write"
    invocation = expression[1:] if expression[0] == "return" else expression
    subject = record.qualified.rsplit("::", 1)[-1]
    if not IDENTIFIER.fullmatch(subject):
        return None
    arguments = tuple(token for index, argument in enumerate(record.parameters)
                      for token in ((argument,) if not index else (",", argument)))
    for spelling in record.direct_bases:
        prefix = base_prefix(spelling)
        if prefix and invocation == (*prefix, subject, "(", *arguments, ")"):
            return "base-forward"
    return None


def fingerprint(record):
    source, values = body_values(record)
    directive_spans = tuple(source.directives())
    data = json.dumps([values, directive_spans, Source(record.initializers).ordered],
                      ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return sha256(data).hexdigest()


def identity(record):
    return (record.path, record.qualified, record.signature, tuple(sorted(record.fields)),
            record.parameters, tuple(sorted(record.direct_bases)), fingerprint(record))


def classify_changed(before, after, *, complete, classify=shape):
    """Return lexically simple changes and exact inline evidence requirements."""
    if complete is not True:
        raise ObjectError("H6 needs complete inline-body discovery on both bound trees.")
    before, after = tuple(before), tuple(after)
    for record in before + after:
        if (not isinstance(record, InlineBody) or not record.path.startswith("include/")
                or type(record.line) is not int or record.line < 1 or not record.qualified
                or not record.signature):
            raise ObjectError("H6 cannot identify an inline body in the protected inventory.")

    existing = Counter(map(identity, before))
    simple, required = [], []
    for record in sorted(after, key=lambda item: (item.path, item.line, item.qualified, item.signature)):
        signature = identity(record)
        if existing[signature]:
            existing[signature] -= 1
            continue
        kind = classify(record)
        if kind is None:
            required.append(BehaviorEvidence(record.path, record.line, record.qualified,
                                             record.signature, signature[-1]))
        else:
            simple.append((record.path, record.line, record.qualified, kind))
    return simple, required


def missing_behavior(required, covered):
    """Name the uncovered bodies after the caller validates its run binding."""
    covered = set(covered)
    return [Finding(item.path, item.line, RULE,
                    f"The changed inline function {item.qualified} needs verified behavior.",
                    "Keep the body to a direct member read, store, or base forward, or rerun the inline check.")
            for item in sorted(required) if item not in covered]
