"""Carry an exact main-line ancestor across fully tracked input changes."""

from hashlib import sha256
from subprocess import CalledProcessError

from state_snapshot import OID, authoritative_units, git, load, safe_tu
from state_evidence import LIMIT, cached_pairs, header

# These are orchestration and publication paths. The comparison inputs and
# implementation retain full-refresh semantics. state.yml can be carried only
# across the reviewed producer-v2 to resume transport revision.
REPORT_DIRS = ("docs/", "worklist/", "ci/state/", "ci/progress/", "ci/alarms/",
               "ci/nightly/", "ci/landing/", "ci/public-text/", ".github/workflows/")
STATE_FLOW = ".github/workflows/state.yml"
TRANSPORT = {"ci/managed-state/state_delta.py", "ci/managed-state/state_fetch.py",
             "ci/managed-state/state_workflow.py",
             "ci/managed-state/recovery-artifacts.json", "ci/managed-state/state_recover.py",
             "ci/managed-state/state_transport.py", "ci/managed-state/state_origin.py",
             "ci/managed-state/bundle.sha256",
             "ci/README.md"}
RESUME_MIGRATION = ("5df8abc2a97aef390b5a0256a15e163ae4a312566c0ea893187da4a254aea8fc", "14286c7910816519777d5a46c720605d142dff009f5751843d4e4c5263e2111f")
# The one-shot PR orchestration change leaves every comparison input intact.
COMPACT_GRAPH = {
    "ci/managed-check/landing_read.py": (
        "fcbc657e031cff9f496470c5ad3fa7d01080357d3f277381584c48d35a3ce89f",
        "c156b8a77e440fa8f87d017389d8aea9e164e236704eba2baf26d190821b1cc1",
    ),
    "ci/managed-check/github_io.py": (
        "3a5c9373f5bb105a71b4f00a730a5361ac7b238372ccf7e7baadb51e17c6b744",
        "af57df171f74d66f557535dfe2b702c194bd51219828060b60dca6ff210c5f77",
    ),
    "ci/managed-check/bundle.sha256": (
        "8e8f38f80f0327372967ae319b28261bca972d0435dd21465875b03806fd9f12",
        "21c6f500a947b2b957366fa346de2864cb3d017901e0e528bfd50220589abf82",
    ),
}
COMPACT_SCOPE = {"ci/managed-state/state_delta.py", "ci/managed-state/state_origin.py",
                 "ci/managed-state/bundle.sha256"}
MAX_DIFF_BYTES = 4 * 1024**2
ANCESTOR_LIMIT = 16


def predecessors(root, main):
    return git(root, "rev-list", "--first-parent", "--skip=1", "--max-count",
               str(ANCESTOR_LIMIT), main).decode("ascii").splitlines()


def compact_graph_change(root, parent, main):
    try:
        for path, expected in COMPACT_GRAPH.items():
            observed = []
            for revision in (parent, main):
                tree = git(root, "ls-tree", revision, "--", path)
                if not tree.startswith(b"100644 blob "):
                    return False
                observed.append(sha256(git(root, "show", f"{revision}:{path}")).hexdigest())
            if tuple(observed) != expected:
                return False
    except (OSError, CalledProcessError):
        return False
    return True


def publication_path(root, parent, main, file):
    if file in COMPACT_GRAPH:
        return compact_graph_change(root, parent, main)
    if file == STATE_FLOW:
        fingerprints = tuple(sha256(git(root, "show", f"{rev}:{file}")).hexdigest()
                             for rev in (parent, main))
        return fingerprints == RESUME_MIGRATION
    return (file in TRANSPORT or file.startswith(REPORT_DIRS)
            or ("/" not in file and file.endswith(".md")))


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
        info = meta.split()
        if (len(info) == 5 and info[0] in {b":100644", b":000000"}
                and info[1] in {b"100644", b"000000"} and info[4] in {b"A", b"D", b"M"}
                and publication_path(root, parent, main, file)):
            continue
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
        old = load(snapshot, LIMIT)
        parent = old.get("sha", "")
        if not isinstance(parent, str) or not OID.fullmatch(parent) or parent not in predecessors(root, main):
            return {}
        if (changed := source_changes(root, parent, main)) is None:
            return {}
        tree = git(root, "rev-parse", parent + "^{tree}").decode().strip()
        units = authoritative_units(root, main)
        if set(old["evidence"]) != set(units):
            return {}
        keys = ("source", "contract")
        requests = [{"tu": name, **{key: old["evidence"][name]["compiler"][key] for key in keys}}
                    for name in units]
        if not all(safe_tu(item["tu"]) for item in requests):
            return {}
        identity = header(parent, tree)
        prior_policy, graph_policy = COMPACT_GRAPH["ci/managed-check/bundle.sha256"]
        if identity["policy"] == graph_policy and compact_graph_change(root, parent, main):
            identity["policy"] = prior_policy
        return unaffected(cached_pairs(old, identity, requests), changed)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, CalledProcessError):
        warn("Previous exact state cannot be reused. A full initial refresh is required.")
        return {}


def merge(required, measured, carried):
    if set(measured) & set(carried) or set(required) != set(measured) | set(carried):
        raise ValueError("The new protected state does not cover each translation unit exactly once.")
    return measured | carried

