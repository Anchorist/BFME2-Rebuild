"""Use an exact parent snapshot only for fully tracked source modifications."""

from subprocess import CalledProcessError

from state_snapshot import authoritative_units, git, load, safe_tu
from state_evidence import LIMIT, cached_pairs, header

# This generated file is outside the compiler and checker inputs.
READ_ONLY_REPORTS = {"docs/progress-card.md"}
MAX_DIFF_BYTES = 4 * 1024**2


def source_changes(root, parent, main):
    """Return the dirty source paths, or None if the transition needs a full rebuild."""
    data = git(root, "diff-tree", "-r", "--raw", "-z", "--no-commit-id", "--no-renames",
               "--no-ext-diff", parent, main, "--")
    if len(data) > MAX_DIFF_BYTES:
        return None
    parts = data.split(b"\0")
    if parts.pop() != b"" or len(parts) % 2:
        return None
    changed = set()
    for meta, name in zip(parts[::2], parts[1::2], strict=True):
        file = name.decode("utf-8", "strict")
        if file in READ_ONLY_REPORTS:
            continue
        info = meta.split()
        # New/deleted paths, configuration, ledgers, and name or mode changes
        # may alter symbolic lookup or introduce an earlier include candidate.
        if (not file.startswith(("src/", "include/")) or len(info) != 5
                or info[:2] != [b":100644", b"100644"] or info[4] != b"M"):
            return None
        changed.add(file.casefold())
    return changed


def unaffected(evidence, changed):
    clean = {}
    for tu, entry in evidence.items():
        row = entry["compiler"]
        if tu.casefold() in changed or (changed and row["status"] != "compiled"):
            continue
        # Only installed and authenticated receipts can supply these dependencies.
        if any(path.casefold() in changed for path, _ in row.get("dependencies", ())):
            continue
        clean[tu] = entry
    return clean


def inherited(root, main, snapshot, *, warn=print):
    if not snapshot or not snapshot.is_file():
        return {}
    try:
        parent = git(root, "rev-parse", "--verify", main + "^").decode().strip()
        if (changed := source_changes(root, parent, main)) is None:
            return {}
        tree = git(root, "rev-parse", parent + "^{tree}").decode().strip()
        old = load(snapshot, LIMIT)
        units = authoritative_units(root, main)
        if set(old["evidence"]) != set(units):
            return {}
        keys = ("source", "contract")
        requests = [{"tu": name, **{key: old["evidence"][name]["compiler"][key] for key in keys}}
                    for name in units]
        if not all(safe_tu(item["tu"]) for item in requests):
            return {}
        return unaffected(cached_pairs(old, header(parent, tree), requests), changed)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, CalledProcessError):
        warn("Previous exact state cannot be reused. A full initial refresh is required.")
        return {}


def merge(required, measured, carried):
    if set(measured) & set(carried) or set(required) != set(measured) | set(carried):
        raise ValueError("The new protected state does not cover each translation unit exactly once.")
    return measured | carried

