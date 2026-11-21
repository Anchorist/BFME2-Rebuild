"""Bind protected header inventories to the same Git objects that were judged."""
from collections import Counter
from dataclasses import dataclass
import re

from cpp import Source, decode
from git_objects import ObjectError
from header_inline import BehaviorEvidence, InlineBody, classify_changed, missing_behavior
from header_inline_context import ArrayMember, VirtualSlot, body_key, contextual_shape, needs_slot
from header_removal import Declaration, acknowledgments, check_removals
from rules import Finding

OID = re.compile(r"[0-9a-f]{40}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
HEADER = re.compile(r"include/[A-Za-z0-9_./+-]+\Z")
ACCESS = re.compile(r"[^A-Za-z0-9_:~<> *&^,()[\]/%!=+-]")


@dataclass(frozen=True)
class Binding:
    repository: str
    base: str
    head: str
    tree: str
    source_policy_sha256: str
    checker_sha256: str
    run_id: int
    attempt: int


@dataclass(frozen=True, order=True)
class FileIdentity:
    path: str
    before_blob: str | None
    after_blob: str | None


@dataclass(frozen=True)
class FileText:
    identity: FileIdentity
    before: str
    after: str


@dataclass(frozen=True)
class VerifiedInventory:
    """Protected receipt after the hosted collector has validated its origin.

    The collector validates the issuer and job, expected artifact format,
    Git projection identity, and the complete plan and result blob digest.
    Passing an author-supplied object of this type would defeat that contract.
    """
    binding: Binding
    rule: str
    files: tuple[FileIdentity, ...]
    before: tuple[Declaration | InlineBody, ...]
    after: tuple[Declaration | InlineBody, ...]
    format_revision: int
    complete: bool


@dataclass(frozen=True)
class VerifiedInlineEvidence:
    """Exact behavior observations from the protected checker."""
    binding: Binding
    covered: tuple[BehaviorEvidence, ...]
    complete: bool
    refused: tuple[BehaviorEvidence, ...] = ()


@dataclass(frozen=True)
class BodyContext:
    body: BehaviorEvidence
    is_virtual: bool | None
    arrays: tuple[ArrayMember, ...] = ()


@dataclass(frozen=True)
class VerifiedInlineContext:
    """Protected member binding, virtuality and table/target receipts."""
    binding: Binding
    known: tuple[BodyContext, ...]
    slots: tuple[VirtualSlot, ...]
    complete_slots: tuple[BehaviorEvidence, ...] = ()


@dataclass(frozen=True)
class Result:
    rule: str
    state: str
    findings: tuple[Finding, ...] = ()


def valid_binding(binding):
    return (
        isinstance(binding, Binding) and binding.repository
        and all(OID.fullmatch(oid) for oid in (binding.base, binding.head, binding.tree))
        and all(HASH.fullmatch(digest) for digest in (binding.source_policy_sha256, binding.checker_sha256))
        and type(binding.run_id) is int and binding.run_id > 0
        and type(binding.attempt) is int and binding.attempt > 0
    )


def preprocessor_identity(source):
    result = []
    for start, end in source.directives():
        tokens = source.tokens[start:end]
        values = tuple(token.value for token in tokens)
        # Whitespace in a macro definition may affect replacement or
        # stringization. Normalization must not hide it.
        spaces = tuple(left.stop != right.offset for left, right in zip(tokens, tokens[1:]))
        result.append((start, end, values, spaces))
    return tuple(result)


def code_and_directives(text):
    source = Source(text)
    token_lines = tuple((token.line, token.end_line) for token in source.tokens)
    return source.ordered, token_lines, preprocessor_identity(source)


def file_text(repo, entry, path, max_bytes):
    if entry is None:
        return ""
    if not entry.regular:
        raise ObjectError(f"Header inventory requires regular text at {path}.")
    _, raw = repo.blob(entry.oid, max_bytes)
    if raw is None:
        raise ObjectError(f"Header inventory exceeded the text bound at {path}.")
    try:
        return decode(raw)
    except UnicodeDecodeError as exc:
        raise ObjectError(f"Header inventory needs UTF-8 at {path}.") from exc


def changed_headers(repo, binding, policy):
    """Identify required files independently of either producer's coverage claim."""
    if not valid_binding(binding) or repo.tree_oid(binding.tree) != binding.tree:
        raise ObjectError("The protected header check could not identify the bound trees.")
    if repo.tree_oid(binding.base) == binding.tree:
        return ()
    controls = []
    for delta in sorted(repo.diff(binding.base, binding.tree), key=lambda item: item.path):
        if not delta.path.startswith("include/"):
            continue
        if not HEADER.fullmatch(delta.path):
            raise ObjectError("A changed header path could not be identified.")
        old = file_text(repo, delta.old, delta.path, policy.limits["bytes_per_file"])
        new = file_text(repo, delta.new, delta.path, policy.limits["bytes_per_file"])
        if delta.old is not None and delta.new is not None and code_and_directives(old) == code_and_directives(new):
            continue
        identity = FileIdentity(delta.path, delta.old.oid if delta.old else None, delta.new.oid if delta.new else None)
        controls.append(FileText(identity, old, new))
    return tuple(controls)


def normalized_spelling(text):
    return bool(text) and isinstance(text, str) and not ACCESS.search(text)


def coverage(inventory, rule, binding, files):
    return (
        isinstance(inventory, VerifiedInventory) and inventory.binding == binding and inventory.rule == rule
        and inventory.complete is True and type(inventory.format_revision) is int and inventory.format_revision == 1
        and inventory.files == tuple(file.identity for file in files)
    )


def in_relevant_blobs(items, kind, texts):
    existing = Counter()
    for item in items:
        if not isinstance(item, kind):
            return False
        if (item.path not in texts or type(item.line) is not int or item.line < 1
                or item.line > len(texts[item.path].split("\n"))
                or not normalized_spelling(item.qualified)):
            return False
        signature = item.identity if kind is Declaration else item.signature
        if not isinstance(signature, str) or not signature:
            return False
        existing[item.path, item.line, item.qualified, signature] += 1
    return all(count == 1 for count in existing.values())


def valid_inventory(inventory, rule, binding, files, kind):
    return (
        coverage(inventory, rule, binding, files)
        and in_relevant_blobs(inventory.before, kind, {
            item.identity.path: item.before for item in files if item.identity.before_blob is not None
        })
        and in_relevant_blobs(inventory.after, kind, {
            item.identity.path: item.after for item in files if item.identity.after_blob is not None
        })
    )


def first_change(files):
    record = files[0]
    old, new = record.before.split("\n"), record.after.split("\n")
    line = next((i for i, (before, after) in enumerate(zip(old, new), 1) if before != after),
                min(len(old), len(new)))
    return record.identity.path, line


def incomplete(rule, files, description, remedy):
    path, line = first_change(files)
    return Result(rule, "held", (Finding(path, line, rule, description, remedy),))


def check_h4(repo, binding, files, inventory=None):
    if not files:
        return Result("H4", "pass")
    if not valid_inventory(inventory, "H4", binding, files, Declaration):
        return incomplete("H4", files, "This header change needs a complete declaration comparison.",
                          "Wait for the declaration check to finish on this revision.")
    findings = tuple(check_removals(inventory.before, inventory.after,
                                    acknowledgments(repo, binding.head), complete=True))
    return Result("H4", "fail" if findings else "pass", findings)


def check_h6(binding, files, inventory=None, evidence=None, context=None):
    if not files:
        return Result("H6", "pass")
    if not valid_inventory(inventory, "H6", binding, files, InlineBody):
        return incomplete("H6", files, "This header change needs a complete inline-function comparison.",
                          "Wait for the inline check to finish on this revision.")
    helpers, slots = {}, {}
    if isinstance(context, VerifiedInlineContext) and context.binding == binding:
        helpers = {item.body: item for item in context.known}
        scope = {body_key(item) for item in inventory.after}
        if (len(helpers) != len(context.known) or not set(helpers) <= scope
                or not set(context.complete_slots) <= scope
                or len(context.complete_slots) != len(set(context.complete_slots))
                or any(item.body not in context.complete_slots for item in context.slots)
                or len(context.slots) != len({(item.body, item.table_rva, item.index, item.offset_to_subobject)
                                              for item in context.slots})):
            helpers = {}
        else:
            for item in context.slots:
                slots.setdefault(item.body, []).append(item)

    slot_holds = []

    def classify(record):
        key = body_key(record)
        learned = helpers.get(key)
        virtual = learned.is_virtual if learned else None
        arrays = learned.arrays if learned else ()
        kind, reason = contextual_shape(record, arrays=arrays, is_virtual=virtual, slot_proofs=slots.get(key, ()))
        if kind is None and needs_slot(record, virtual):
            slot_holds.append(Finding(record.path, record.line, "H6", reason,
                                      "Use the direct base selected by retail and wait for the slot comparison."))
            return "pending-slot"
        return kind

    _, required = classify_changed(inventory.before, inventory.after, complete=True, classify=classify)
    valid = (
        isinstance(evidence, VerifiedInlineEvidence) and evidence.binding == binding and evidence.complete is True
        and len(evidence.covered + evidence.refused) == len(set(evidence.covered + evidence.refused))
        and set(evidence.covered + evidence.refused) <= set(required)
    )
    if valid and evidence.refused:
        findings = tuple(Finding(item.path, item.line, "H6",
                                 f"The changed inline function {item.qualified} changes verified behavior.",
                                 "Restore the behavior or use a direct member operation with the same result.")
                         for item in sorted(evidence.refused))
        return Result("H6", "fail", findings)
    findings = tuple(sorted(slot_holds + missing_behavior(required, evidence.covered if valid else ())))
    return Result("H6", "held" if findings else "pass", findings)


def evaluate_inventories(repo, binding, policy, *, declarations=None, bodies=None, inline=None, context=None):
    """Hosted entry point. Compute coverage from Git before using any receipt."""
    files = changed_headers(repo, binding, policy)
    return check_h4(repo, binding, files, declarations), check_h6(binding, files, bodies, inline, context)
