"""Check Draft promotions from protected base and candidate Git objects."""
from collections import defaultdict
import argparse
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path, PurePosixPath
import re
import sys

from cpp import Source, decode, include_sites
from header_qualified import qualified_types
from gate import encode, policy_at
from git_objects import Git, ObjectError
from rules import DRAFT, Finding, include_targets

RULE = "H7"
PROJECT_SOURCE = ("src", "include")
POSSIBLE_SPLICE = re.compile(rb"(?:\\|\?\?/)[ \t]*\r?\n")


def lookup(entries, policy):
    """Index the first-party paths used by the Windows compiler."""
    paths = {}
    for path, entry in sorted(entries.items()):
        if not entry.regular or policy.kind(path) is None:
            continue
        folded = path.casefold()
        if folded in paths:
            raise ObjectError(f"Two source paths differ only in case: {paths[folded]} and {path}.")
        paths[folded] = path
    return paths


def resolve(targets, known):
    return next((known[target] for target in targets if target in known), None)


def check_drafts(repo, policy, base, head):
    """Return actionable H7 findings. Both inputs are exact trusted binding trees."""
    deltas = tuple(repo.diff(base, head))
    removes = {change.path for change in deltas if change.path.startswith(DRAFT)
               and policy.kind(change.path) == "header" and change.old and not change.new}
    permanent = [change for change in deltas if policy.kind(change.path) == "header"
                 and not change.path.startswith(DRAFT) and change.new and change.new.regular]
    if not removes and not permanent:
        return []

    def read(oid):
        _, raw = repo.blob(oid, policy.limits["bytes_per_file"])
        if raw is None:
            raise ObjectError("A source file exceeds the size supported for the Draft check.")
        return raw

    @lru_cache(maxsize=5000)
    def parse(oid):
        try:
            return Source(decode(read(oid)))
        except UnicodeDecodeError as exc:
            raise ObjectError("A source file is not UTF-8 during the Draft check.") from exc

    def named_types(entry):
        if not entry or not entry.regular:
            return {}
        return {item.name: item.line for item in qualified_types(parse(entry.oid))
                if item.kind == "type" and not item.internal}

    promotions = defaultdict(list)
    for change in permanent:
        old_types, new_types = named_types(change.old), named_types(change.new)
        for name, line in new_types.items():
            if name not in old_types:
                promotions[name].append((change.path, line))

    findings = []
    if promotions:
        for draft_path, entry in sorted(repo.tree(head, "include/Draft")):
            if policy.kind(draft_path) != "header":
                continue
            for name in sorted(promotions.keys() & named_types(entry).keys()):
                for path, line in promotions[name]:
                    findings.append(Finding(
                        path, line, RULE, f"The permanent definition of {name} leaves {draft_path} in place.",
                        f"Delete {draft_path} in this pull request and update every file that includes it.",
                    ))

    if removes:
        before = dict(repo.tree(base, *PROJECT_SOURCE))
        after = dict(repo.tree(head, *PROJECT_SOURCE))
        old_names, new_names = lookup(before, policy), lookup(after, policy)
        removed_names = {path.casefold(): path for path in removes}
        leaves = tuple(sorted({PurePosixPath(path).name.lower().encode("ascii") for path in removes}))
        for path in sorted(new_names.values()):
            oid = after[path].oid
            raw = read(oid).lower()
            # A literal resolving to a removed header contains its filename.
            # Leave all spliced spellings to the lexer.
            if not any(leaf in raw for leaf in leaves) and not POSSIBLE_SPLICE.search(raw):
                continue
            for line, spelling, quoted in include_sites(parse(oid)):
                targets = tuple(target.casefold() for target in include_targets(path, spelling, quoted))
                removed = resolve(targets, removed_names)
                if removed is None:
                    continue
                old_target = resolve(targets, old_names)
                if old_target is not None and old_target not in removes:
                    continue
                new_target = resolve(targets, new_names)
                if new_target is not None and not new_target.startswith(DRAFT):
                    continue
                draft = old_target or removed
                findings.append(Finding(
                    path, line, RULE, f"This include still depends on the deleted Draft {draft}.",
                    "Point this include at the permanent header or remove the include if it is now unused.",
                ))
    return sorted(set(findings))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo")
    parser.add_argument("base")
    parser.add_argument("head")
    options = parser.parse_args(argv)
    config = Path(__file__).with_name("config.json")
    try:
        with Git(options.repo) as repo:
            base, head = repo.tree_oid(options.base), repo.tree_oid(options.head)
            findings = check_drafts(repo, policy_at(config), base, head)
    except (ObjectError, OSError, ValueError) as exc:
        print(encode({"rule": RULE, "status": "error", "message": str(exc)}), end="")
        return 2
    print(encode({"rule": RULE, "status": "fail" if findings else "pass",
                  "base_tree": base, "head_tree": head,
                  "findings": [asdict(item) for item in findings]}), end="")
    return int(bool(findings))


if __name__ == "__main__":
    sys.exit(main())
