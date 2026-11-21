"""Advisory Actions job for trusted, same-run inline-virtual shard atoms."""

import os
from pathlib import Path
import sys
import tempfile

from common import PIN, digest, read, validate_binding, write
from compact_matrix import join_compact
from gitrepo import Git
from intake import reconstruct
from managed_inline import CATALOGUE, INLINE, write_step_summary
from measure import pin as verify_file
from virtual_atoms import evaluate
from inline_virtual_scope import scope_inputs
from inline_owner_scope import select_owner_scope
from wide_plan import identity


def bound_owner_scope(git, plan, candidate, native, *, protected_inventory=None):
    scope = scope_inputs(git, plan, candidate)
    parent, head = (native["instructions"][side] for side in ("parent", "candidate"))
    settings = ("contract", "flags", "env")
    compiler_paths = sorted(path for path in parent.keys() | head.keys()
                            if path not in parent or path not in head
                            or any(parent[path][key] != head[path][key] for key in settings))
    if compiler_paths:
        return scope | {"complete": False, "compiler_changes": compiler_paths}, ()
    if scope["complete"] or protected_inventory is None:
        return scope, ()
    expected = {
        "repository": plan["repo"],
        **{key: plan[key] for key in ("base", "head", "tree")},
        "matrix": identity(native),
        "compiler_profile": native["pins"]["profile_sha256"],
        "intake": identity(plan),
        "policy": plan["policy"],
    }
    try:
        # The only caller that may supply this input is a protected
        # same-run producer with exact Git and native table bindings.
        # No CLI argument, environment or author artifact supplies it.
        catalogue = INLINE / "catalogue-audited.json"
        verify_file(catalogue, CATALOGUE)
        base_tree = git.value("rev-parse", plan["base"] + "^{tree}")
        packet = protected_inventory(git, plan, candidate, expected)
        proof = select_owner_scope(packet, expected=expected, base_tree=base_tree,
                                  changed_paths=plan["changed_paths"],
                                  protected_tables=read(catalogue, 8 * 1024**2)["tables"])
    except (OSError, ValueError, TypeError, KeyError):
        return scope, ()
    return scope | {"complete": True, "owner_count": len(proof["owners"]),
                    "inventory_sha256": identity(packet)}, proof["tables"]


def run(admission_path, matrix_path, shard_tree, expected_matrix, output, *, protected_inventory=None):
    os.umask(0o077)
    admission_path, matrix_path, shard_tree, output = map(
        Path, (admission_path, matrix_path, shard_tree, output))
    plan = validate_binding(read(admission_path, 18 * 1024**2))
    if plan["base"] != os.environ["GITHUB_SHA"]:
        raise ValueError("Inline report checkout differs from its protected base.")
    native = read(matrix_path, 12 * 1024**2)
    if (identity(native) != expected_matrix
            or native["scope_sha256"] != identity(plan)
            or native["partition"]["binding"] != {k: plan[k] for k in ("base", "head", "tree")}):
        raise ValueError("Inline report received a foreign managed matrix.")
    expected_indices = {shard["index"] for shard in native["partition"]["shards"]}
    names = {path.name for path in shard_tree.iterdir() if path.name != "matrix.json"}
    names_local = {f"shard-{index}" for index in expected_indices}
    prefix_managed = "bfme-wide-" + os.environ["GITHUB_RUN_ATTEMPT"] + "-"
    names_uploaded = {prefix_managed + str(index) for index in expected_indices}
    prefix = {frozenset(names_local): "shard-", frozenset(names_uploaded): prefix_managed}.get(frozenset(names))
    if prefix is None:
        raise ValueError("Inline report requires every trusted shard artifact.")
    receipts = []
    for index in sorted(expected_indices):
        root = shard_tree / (prefix + str(index))
        path = root / "shard.json"
        if root.resolve() != root.absolute() or path.is_symlink() or not path.is_file():
            raise ValueError("Inline report shard artifact is outside its output root.")
        receipt = read(path, 20 * 1024**2)
        if receipt["shard"] != index:
            raise ValueError("Inline report shard receipt has the wrong index.")
        receipts.append(receipt)
    _, _, atoms = join_compact(native, receipts, expected=expected_matrix,
                               run=os.environ["GITHUB_RUN_ID"], attempt=os.environ["GITHUB_RUN_ATTEMPT"])
    if protected_inventory is None and os.environ.get("BFME_INLINE_OWNER_SCOPE") == "yes":
        # Audit 1.5: the owner scope is produced here, from this run's own shard atoms and Git objects.
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "header-witness"))
            import compiled_table_owners
            from inline_ancestry import in_job_owner_scope
            catalogue = INLINE / "catalogue-audited.json"
            verify_file(catalogue, CATALOGUE)
            protected_inventory = in_job_owner_scope(atoms, compiled_table_owners,
                                                     read(catalogue, 8 * 1024**2)["tables"])
        except (ImportError, OSError, ValueError, KeyError, TypeError):
            protected_inventory = None
    reference = (Path.cwd() / "baseline/game.dat").resolve(strict=True)
    verify_file(reference, PIN["baseline_sha256"])
    with tempfile.TemporaryDirectory(prefix="bfme-inline-action-") as folder:
        git = Git(Path(folder) / "repo.git", initialize=True)
        protected_objects = (Path.cwd() / ".git/objects").resolve(strict=True)
        (git.path / "objects/info/alternates").write_text(str(protected_objects) + "\n")
        candidate = reconstruct(git, plan)
        source_scope, selected_tables = bound_owner_scope(
            git, plan, candidate, native, protected_inventory=protected_inventory)
        receipt, _private, report = evaluate(native, atoms, expected=expected_matrix, repo=git.path,
                                             candidate=candidate, baseline=reference,
                                             scope_complete=source_scope["complete"],
                                             required_tables=selected_tables, source_scope=source_scope)
    output.mkdir(mode=0o700)
    write(output / "inline-status.json", receipt | {
        "version": 1, "repo": plan["repo"], "number": plan["number"],
        "run": os.environ["GITHUB_RUN_ID"], "attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "plan": digest(admission_path.read_bytes()),
    })
    (output / "inline-report.txt").write_text(report, encoding="utf-8")
    write_step_summary(report)


if __name__ == "__main__":
    run(*sys.argv[1:])
