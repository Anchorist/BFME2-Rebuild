"""Use authenticated compiler dependency coverage to finish Draft deletion checks."""
from dataclasses import dataclass

from header_draft import check_drafts
from header_inventory import Binding, Result
from rules import DRAFT, Finding

RULE = "H7"


@dataclass(frozen=True, order=True)
class Dependency:
    translation_unit: str
    includer: str
    line: int
    retired_draft: str


@dataclass(frozen=True)
class VerifiedDraftScope:
    """Protected per-TU dependency result with a complete candidate observation.

    The graph producer authenticates directive origins and any unresolved Draft
    target, including computed includes. A failed or partial dependency walk
    cannot issue complete evidence. An unresolved retired edge is valid when
    the producer can identify its target before reporting the missing include.
    """
    binding: Binding
    translation_units: tuple[str, ...]
    dependencies: tuple[Dependency, ...]
    complete: bool


def deleted_drafts(repo, policy, base, tree):
    return tuple(sorted(delta.path for delta in repo.diff(base, tree)
                        if delta.path.startswith(DRAFT) and policy.kind(delta.path) == "header"
                        and delta.old and not delta.new))


def complete_scope(proof, binding, required_units, removed):
    """The required units come from protected, complete base dependency data."""
    return (
        isinstance(proof, VerifiedDraftScope) and proof.binding == binding and proof.complete is True
        and required_units is not None and required_units == tuple(sorted(set(required_units)))
        and proof.translation_units == required_units
        and proof.dependencies == tuple(sorted(set(proof.dependencies)))
        and all(edge.translation_unit in required_units
                and edge.includer.startswith(("include/", "src/"))
                and type(edge.line) is int and edge.line > 0
                and edge.retired_draft in removed for edge in proof.dependencies)
    )


def check_draft_scope(repo, policy, binding, *, required_units=None, proof=None):
    issues = check_drafts(repo, policy, binding.base, binding.tree)
    if issues:
        return Result(RULE, "fail", tuple(issues))
    removed = deleted_drafts(repo, policy, binding.base, binding.tree)
    if not removed:
        return Result(RULE, "pass")
    if not complete_scope(proof, binding, required_units, removed):
        findings = tuple(Finding(path, 1, RULE,
                                 "This Draft deletion needs a complete check of its former includers.",
                                 "Wait for the dependency check to finish on this revision.")
                         for path in removed)
        return Result(RULE, "held", findings)
    findings = tuple(sorted({Finding(
        item.includer, item.line, RULE, f"This include still depends on the deleted Draft {item.retired_draft}.",
        "Point this include at the permanent header or remove the include if it is unused.",
    ) for item in proof.dependencies}))
    return Result(RULE, "fail" if findings else "pass", findings)
