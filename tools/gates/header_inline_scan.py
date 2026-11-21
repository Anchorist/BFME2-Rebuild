"""Discover explicit header inline bodies and state when source coverage is incomplete."""
from collections import Counter
from dataclasses import dataclass
import json
import re

from cpp import Source, matching
from definitions import CLASS_HEAD, LINKAGE, NAMESPACE
from header_force_evidence import scopes_at
from header_inline import InlineBody
from header_lexical_inventory import ACCESS, callable_declaration, groups, inventory, parameter_type
from header_noinline import segments


BASE = re.compile(r"(?:[A-Za-z_]\w*::)*[A-Za-z_]\w*\Z", re.ASCII)
BASE_SPECIFIERS = {"public", "protected", "private", "virtual"}


@dataclass(frozen=True)
class Observation:
    bodies: tuple[InlineBody, ...]
    unresolved: tuple[tuple[int, tuple[str, ...], tuple[str, ...]], ...]


def parameter_names(head, opening, closing):
    arguments = groups(head[opening + 1:closing])
    if arguments == [("void",)]:
        return ()
    return tuple(arg[-1] if len(parameter_type(arg)) < len(arg) else "" for arg in arguments)


def bases_of(scopes):
    if not scopes or not CLASS_HEAD.fullmatch(" ".join(scopes[-1])) or ":" not in scopes[-1]:
        return ()
    definition = scopes[-1]
    start = definition.index(":")
    names = groups(definition[start + 1:])
    if names is None:
        return ()
    spellings = ("".join(token for token in name if token not in BASE_SPECIFIERS) for name in names)
    return tuple(name for name in spellings if BASE.fullmatch(name))


def scope_opening(head):
    spelling = " ".join(head)
    return CLASS_HEAD.fullmatch(spelling) or NAMESPACE.fullmatch(spelling) or LINKAGE.fullmatch(spelling)


def preceding_tokens(scopes, values):
    if scopes and values[0:1] and values[0] in ACCESS and values[1:2] == (":",):
        return values[2:]
    return values


def scan(path, text):
    source = Source(text)
    slots = {token.offset: index for index, token in enumerate(source.tokens)}
    observed_declarations = inventory(path, text)
    members = {}
    shapes, unknown = [], []
    for declaration in observed_declarations.declarations:
        signature, guards = json.loads(declaration.identity)
        if not guards and signature[0] == "data" and "::" in declaration.qualified:
            owner, _, name = declaration.qualified.rpartition("::")
            members.setdefault(owner, set()).add(name)
    directives = dict(source.directives())
    for scopes, tokens in segments(source):
        if not tokens:
            continue
        last = slots[tokens[-1].offset] + 1
        values = preceding_tokens(scopes, tuple(token.value for token in tokens))
        if source.ordered[last:last + 1] != ("{",) or not values or scope_opening(values):
            continue
        context = tuple(" ".join(scope) for scope in scopes)
        owner = scopes_at(scopes)
        if owner is None:
            if any("(" in scope and not scope_opening(scope) for scope in scopes):
                continue  # The owning recorded body already contains these tokens.
            unknown.append((tokens[0].line, context, values))
            continue
        declaration = callable_declaration(values, (owner,) if owner else ())
        if not declaration:
            unknown.append((tokens[0].line, context, values))
            continue
        qualified, signature = declaration
        if slots[tokens[0].offset] in directives or not signature:
            unknown.append((tokens[0].line, context, values))
            continue
        closing = matching(source.ordered, last)
        if closing is None:
            unknown.append((tokens[0].line, context, values))
            continue
        left = values.index("(")
        right = matching(values, left)
        suffix = values[right + 1:]
        initializer = () if ":" not in suffix else suffix[suffix.index(":") + 1:]
        method_owner = qualified.rpartition("::")[0]
        shapes.append(InlineBody(
            path, source.tokens[last].line, qualified,
            json.dumps(signature, ensure_ascii=True, separators=(",", ":")),
            source.logical[source.tokens[last].offset:source.tokens[closing].stop],
            tuple(sorted(members.get(method_owner, ()))),
            parameter_names(values, left, right), bases_of(scopes), " ".join(initializer),
        ))
    unknown.extend((item.line, item.owner, item.tokens) for item in observed_declarations.unknown)
    return Observation(tuple(sorted(shapes, key=lambda item: (item.line, item.qualified, item.signature))),
                       tuple(sorted(set(unknown))))


def changed_discovery(path, before, after):
    """Keep stable opaque scopes and name new/removed ambiguity for the hosted consumer."""
    prior, current = scan(path, before), scan(path, after)
    before_keys = Counter((scope, tokens) for _, scope, tokens in prior.unresolved)
    after_keys = Counter((scope, tokens) for _, scope, tokens in current.unresolved)
    return prior.bodies, current.bodies, before_keys != after_keys
