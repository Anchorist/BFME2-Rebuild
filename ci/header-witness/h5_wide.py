"""Header layout evidence (H5) on the wide route, run in the wide-join job after the declaration probe.

Usage: h5_wide.py ADMITTED_PLAN_DIR OUTPUT_DIR

The wide route compiles in shards, so the head objects of newly matched functions are not here: this step measures
layout only. A header change whose classes keep their shape passes; a moved member holds (it needs a witness, which
the narrow route gives). Probes are compiled inside a planned translation unit with that unit's own native compile
row, through the same sealed compiler request; a unit counts only if the compiler's include list shows it read the
header. Writes OUTPUT_DIR/header-h5.json, bound to this run attempt exactly as the narrow route binds it.
"""
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for extra in (HERE.parent / "managed-check", HERE.parent / "managed-nt2"):
    sys.path.insert(0, str(extra))
sys.path.insert(0, str(HERE))


def main(admitted, output):
    from types import SimpleNamespace

    from common import PIN
    from compare import native_commands
    import measure
    import pool_protocol
    from pool_compare import projection
    from wide import admission, comparison_inputs
    import h5_bridge

    plan, _ = admission(Path(admitted), kinds=("wide", "compile"))
    if not any(path.startswith("include/") for path in plan["changed_paths"]):
        return False
    with comparison_inputs(plan) as (work, git, tip, judge, tools):
        paths = plan["request_paths"][:6]
        native = {"profile_sha256": plan.get("profile_sha256") or PIN["profile_sha256"],
                  "compile": {side: native_commands(git, judge, revision, paths, tools)
                              for side, revision in (("base", plan["base"]), ("head", tip))}}
        worker = SimpleNamespace(projection=projection, encode=pool_protocol.encode, decode=pool_protocol.decode,
                                 pack_sources=pool_protocol.pack_sources, MAX_OBJECT=pool_protocol.MAX_OBJECT,
                                 MAX_SOURCE=pool_protocol.MAX_FILE, profile=PIN["profile_sha256"], roots=tools)
        binding = {"repo": plan["repo"], **{key: plan[key] for key in ("number", "base", "head", "tree")},
                   "issuer": {"run": os.environ["GITHUB_RUN_ID"], "attempt": os.environ["GITHUB_RUN_ATTEMPT"]}}
        h5_bridge.narrow(dict(plan, request_paths=paths), native, {}, {}, work, git, tip, measure.request, worker,
                         output, binding)
    receipt = Path(output) / "header-h5.json"
    if receipt.stat().st_size > h5_bridge.MAX_RECEIPT:
        receipt.unlink()
        return False
    return True


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: h5_wide.py ADMITTED_PLAN_DIR OUTPUT_DIR")
    sys.exit(0 if main(sys.argv[1], sys.argv[2]) else 3)
