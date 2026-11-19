"""Create advisory payloads while the protected comparison's local COFF is available."""

import os
from pathlib import Path

from common import read, write
from compact_matrix import make_compact
from managed_matrix import SIDES, compiler_receipt, make
from wide_plan import identity
from virtual_atoms import collect


def narrow(plan, native, tables, work, root):
    """Use both already authenticated narrow comparison sides, with no second compile."""
    from wide import sanitize_outcome

    root, work = Path(root), Path(work)
    doc = make(plan, native["compile"], limit=1)
    pin = identity(doc)
    objects, rows = {}, []
    summaries = {"base": {}, "head": {}}
    changed = set(plan["changed_paths"])
    for input_side, side in SIDES.items():
        for item in native["compile"][input_side]:
            tu = item["tu"]
            data = tables[input_side][tu]
            output = work / input_side / "obj" / (tu.replace("/", "_") + ".obj")
            row = {key: item[key] for key in ("tu", "source", "contract")} | {"side": side}
            if output.is_file():
                witness = read(output.with_suffix(".obj.compile.json"), 4 * 1024**2)
                if witness["source_sha256"] != item["source"] or witness["compiler_contract"] != item["contract"]:
                    raise ValueError("Narrow virtual witness differs from its verified source.")
                row.update(status="compiled", object_sha256=witness["object_sha256"],
                           dependencies=sorted(witness["headers"].values()))
                objects[(side,tu)] = output
            elif data.get("error"):
                row["status"] = "error"
            else:
                raise ValueError("Narrow virtual input tool did not return a verified object or compile error.")
            rows.append(row)
            summaries[input_side][tu] = sanitize_outcome(data, tu, changed)
    compiler = compiler_receipt(doc, 0, rows)
    atoms = collect(compiler, find_object=lambda side,tu: objects[(side,tu)])
    receipt = make_compact(doc, expected=pin, run=os.environ["GITHUB_RUN_ID"],
                           attempt=os.environ["GITHUB_RUN_ATTEMPT"], compiler=compiler,
                           native=summaries, inline=atoms)
    shard = root / "shard-0"
    shard.mkdir(mode=0o700, parents=True)
    write(root / "matrix.json",doc)
    write(shard / "shard.json",receipt)
    if (shard / "shard.json").stat().st_size > 8 * 1024**2:
        raise ValueError("Narrow virtual receipt exceeds its budget.")
    return pin
