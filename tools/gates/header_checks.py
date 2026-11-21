"""Preview header source checks from exact Git objects and protected observations."""
import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
import sys

from gate import encode, policy_at, policy_digest
from git_objects import Git, ObjectError
from header_draft_scope import VerifiedDraftScope, check_draft_scope
from header_force_evidence import NativeProof, changes_in, decide, donor_from_repo, owner_key
from header_inventory import (Binding, Result, VerifiedInlineContext, VerifiedInlineEvidence, VerifiedInventory,
                              changed_headers, check_h4, check_h6, file_text)
from header_macro_policy import MacroProof, change_in, verify_change
from header_noinline import check_noinline
from header_qualified import check_identities
from rules import Finding
from shadow_types import measure as type_swaps


@dataclass(frozen=True)
class TrustedObservations:
    """Supplied only after the protected collector has authenticated all receipt producers."""
    binding: Binding
    declarations: VerifiedInventory | None = None
    bodies: VerifiedInventory | None = None
    inline: VerifiedInlineEvidence | None = None
    inline_context: VerifiedInlineContext | None = None
    draft_required_units: tuple[str, ...] | None = None
    draft_scope: VerifiedDraftScope | None = None
    force: tuple[NativeProof, ...] = ()
    macros: tuple[MacroProof, ...] = ()


def result(rule, findings):
    return Result(rule, "fail" if findings else "pass", tuple(findings))


def header_type_swap_findings(repo, policy, base, tree):
    if not any(policy.kind(edit.path) == "header" for edit in repo.diff(base, tree)):
        return ()
    return tuple(
        Finding(fact["path"], fact["line"], "H8",
                f'The declaration of {fact["name"]} changed from {fact["old_type"]} to {fact["new_type"]}.',
                "Keep the typed declaration or file a ledger request citing the parser, "
                "save/load transfer, or initializer that proves it stores an integer.")
        for fact in type_swaps(repo, repo.tree_oid(base), tree)
        if policy.kind(fact["path"]) == "header"
    )


def check_h8(repo, policy, binding, trusted):
    binding_tuple = binding.base, binding.head, binding.tree
    rows = sorted(repo.diff(binding.base, binding.tree), key=lambda item: item.path)
    header_blobs = None
    donor = None
    failures = list(header_type_swap_findings(repo, policy, binding.base, binding.tree))
    held = []
    macro_proofs = {} if trusted is None else {item.change: item for item in trusted.macros}
    if trusted and len(macro_proofs) != len(trusted.macros):
        raise ObjectError("The shared-header comparisons include a duplicate receipt.")
    for delta in rows:
        path = delta.path
        if policy.kind(path) is None or not delta.new:
            continue
        before = file_text(repo, delta.old, path, policy.limits["bytes_per_file"])
        after = file_text(repo, delta.new, path, policy.limits["bytes_per_file"])
        failures.extend(check_noinline(path, before, after))
        old_sites = Counter(map(owner_key, changes_in(path, before)))
        new_sites = Counter(map(owner_key, changes_in(path, after)))
        if new_sites - old_sites:
            if donor is None:
                donor = donor_from_repo(repo, binding.base)
            findings, incomplete, _ = decide(path, before, after, donor, binding_tuple,
                                              published_native=trusted.force if trusted else ())
            failures.extend(findings)
            held.extend(Finding(path, site.line, "H8", message,
                                "Wait for the compiler evidence or remove this control.")
                        for site, message in incomplete)
        change = change_in(path, before, after)
        if change is None:
            continue
        proof = macro_proofs.get(change)
        if proof is not None and header_blobs is None:
            header_blobs = {name: entry.oid for name, entry in repo.tree(binding.tree, "include")
                            if entry.regular and policy.kind(name) == "header"}
        findings, incomplete = verify_change(change, binding_tuple, header_blobs or {}, proof)
        failures.extend(findings)
        held.extend(Finding(path, site.line, "H8", message,
                            "Wait for the shared-header comparison or remove the local override.")
                    for site, message in incomplete)
    if failures:
        return result("H8", sorted(set(failures)))
    return Result("H8", "held" if held else "pass", tuple(sorted(set(held))))


def check_header_source(repo, policy, binding, trusted=None):
    """Entry point for the protected adapter after the ordinary rules pass.

    H1, H2, H5, H9 and H10 remain with their separate owners. The preview
    performs no build, reservation, workflow, status, or repository write.
    """
    files = changed_headers(repo, binding, policy)
    if trusted is not None and trusted.binding != binding:
        trusted = None
    return (
        result("H3", check_identities(repo, policy, binding.base, binding.tree)),
        check_h4(repo, binding, files, trusted.declarations if trusted else None),
        check_h6(binding, files, trusted.bodies if trusted else None, trusted.inline if trusted else None,
                 trusted.inline_context if trusted else None),
        check_draft_scope(repo, policy, binding,
                          required_units=trusted.draft_required_units if trusted else None,
                          proof=trusted.draft_scope if trusted else None),
        check_h8(repo, policy, binding, trusted),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="Git object store")
    parser.add_argument("base", help="Exact protected base commit")
    parser.add_argument("head", help="Exact submitted head commit")
    parser.add_argument("tree", help="Exact composed candidate tree")
    args = parser.parse_args(argv)
    config = Path(__file__).with_name("config.json")
    try:
        with Git(args.repository) as repo:
            binding = Binding("Open-BFME/BFME2-Rebuild", args.base, args.head, args.tree,
                              policy_digest(config), "0" * 64, 1, 1)
            rules = check_header_source(repo, policy_at(config), binding)
            print(encode({"base": args.base, "head": args.head, "tree": args.tree,
                          "rules": [asdict(rule) for rule in rules], "preview": True}), end="")
    except (ObjectError, ValueError, OSError) as exc:
        print(encode({"state": "error", "message": str(exc), "preview": True}), end="")
        return 2
    return int(any(rule.state != "pass" for rule in rules))


if __name__ == "__main__":
    sys.exit(main())
