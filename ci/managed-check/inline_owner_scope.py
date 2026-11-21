"""Select both sides of a protected changed-declaration and descendant inventory."""

from collections import defaultdict, deque
from graphlib import CycleError, TopologicalSorter
import re


PIN = re.compile(r"[0-9a-f]{40}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
KEYS = {"repository", "base", "head", "tree", "matrix", "compiler_profile", "intake", "policy"}


def names(items):
    return (
        type(items) is list
        and all(isinstance(value, str) and 0 < len(value) <= 512 for value in items)
        and len(items) == len(set(items))
    )


def read_side(side, expected_tree, changed_paths, protected_tables):
    if (not isinstance(side, dict) or set(side) != {"tree", "complete", "paths", "classes"}
            or side["tree"] != expected_tree or side["complete"] is not True
            or not names(side["paths"]) or set(side["paths"]) != changed_paths
            or type(side["classes"]) is not list or len(side["classes"]) > 50_000):
        raise ValueError("Incomplete protected declaration inventory.")
    records = {}
    children = defaultdict(set)
    for row in side["classes"]:
        if not isinstance(row, dict) or set(row) != {"owner", "declarations", "bases", "polymorphic", "tables"}:
            raise ValueError("Unexpected declaration inventory fields.")
        owner, bases, tables = row["owner"], row["bases"], row["tables"]
        if (not names([owner]) or owner in records or not isinstance(row["declarations"], str)
                or not HASH.fullmatch(row["declarations"]) or not names(bases) or not names(tables)
                or type(row["polymorphic"]) is not bool or (tables and not row["polymorphic"])
                or not set(tables) <= protected_tables):
            raise ValueError("Ambiguous protected class or native table identity.")
        records[owner] = (row["declarations"], tuple(bases), frozenset(tables), row["polymorphic"])
        for parent in bases:
            children[parent].add(owner)
    if not children.keys() <= records.keys():
        raise ValueError("Protected class has a missing direct base.")
    try:
        list(TopologicalSorter({owner: shape[1] for owner, shape in records.items()}).static_order())
    except CycleError as exc:
        raise ValueError("Protected class inheritance is cyclic.") from exc
    return records, children


def select_owner_scope(packet, *, expected, base_tree, changed_paths, protected_tables):
    """Require caller-authenticated ancestry and derive the same table set for both trees."""
    if (set(expected) != KEYS or set(packet) != {"version", "binding", "parent", "candidate"}
            or type(packet["version"]) is not int or packet["version"] != 1
            or packet["binding"] != expected or not PIN.fullmatch(base_tree)
            or any(not PIN.fullmatch(expected[key]) for key in ("base", "head", "tree"))
            or any(not HASH.fullmatch(expected[key]) for key in ("matrix", "compiler_profile", "intake", "policy"))):
        raise ValueError("Protected owner scope belongs to a different plan.")
    paths = set(changed_paths)
    catalogue = set(protected_tables)
    before, old_children = read_side(packet["parent"], base_tree, paths, catalogue)
    after, new_children = read_side(packet["candidate"], expected["tree"], paths, catalogue)
    changed = {name for name in before.keys() | after.keys() if before.get(name) != after.get(name)}
    selected = set(changed)
    pending = deque(changed)
    while pending:
        owner = pending.popleft()
        descendants = (old_children[owner] | new_children[owner]) - selected
        selected.update(descendants)
        pending.extend(descendants)
    required = set()
    for side in (before, after):
        for name in selected & side.keys():
            _digest, _bases, tables, polymorphic = side[name]
            if polymorphic and not tables:
                raise ValueError(f"Protected native table binding is missing for {name}.")
            required.update(tables)
    return {"binding": expected, "owners": sorted(selected), "tables": sorted(required)}
