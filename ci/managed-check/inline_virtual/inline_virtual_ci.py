"""Portable CLI. Run trusted base tools against separately authenticated compile artifacts."""
import argparse
import json
from pathlib import Path

from inline_virtual_receipt import encoded, make_receipt, write_private_receipt
from inline_virtual_report import render
import inline_virtual_shadow as gate
from portable_binary import COFF, PE


def evaluate_spec(spec):
    repo = Path(spec["repo"]).resolve(strict=True)
    if not isinstance(spec["scope_complete"], bool):
        raise ValueError("scope proof must come from the exact trusted planner")
    owners = spec["owners"]
    if owners is not None and (not isinstance(owners, list) or len(set(owners)) != len(owners)):
        raise ValueError("duplicate or invalid owner in the planned inline-virtual scope")
    native = PE(Path(spec["reference"]).resolve(strict=True))
    catalogue = json.loads(Path(spec["catalogue"]).read_bytes())
    if gate.sha256(Path(spec["catalogue"]).read_bytes()) != spec["catalogue_sha256"]:
        raise ValueError("virtual slot catalogue digest differs from trusted policy")
    roots = tuple(str(Path(root).resolve(strict=True)).rstrip("/") + "/" for root in spec["external_roots"])
    reports = []
    for side in ("candidate", "parent"):
        contract = spec[side]
        files = contract["tus"]
        if sorted(files) != sorted(set(files)) or set(contract["contracts"]) != set(files):
            raise ValueError("duplicate or unpinned compiler inputs")
        inputs, holes = gate.inputs(repo, contract["manifest"], files, contract["contracts"], roots)
        result = gate.scan(native, catalogue, inputs, owners, COFF, keep_comparable=True)
        result.update(pin=contract["manifest"]["pin"], required_tus=len(files),
                      authenticated_tus=len(inputs), requested_owners=owners)
        result["coverage_holes"] += holes
        reports.append(result)
    return make_receipt(repo, spec["binding"], spec["candidate"]["manifest"]["pin"],
                        spec["policy_sha256"], *reports, scope_complete=spec["scope_complete"])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("draft", type=Path, help="source and compiler proof assembled by the trusted planner")
    p.add_argument("--receipt-dir", type=Path)
    p.add_argument("--evidence", type=Path)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    receipt, evidence = evaluate_spec(json.loads(args.draft.read_bytes()))
    if args.evidence:
        args.evidence.write_bytes(encoded(evidence))
    if args.report:
        args.report.write_bytes(render(evidence).encode("utf-8"))
    if args.receipt_dir:
        write_private_receipt(args.receipt_dir, receipt)
    print(encoded(receipt).decode("ascii"), end="")
    return {"pass": 0, "fail": 1, "pending": 2}[receipt["state"]]


if __name__ == "__main__":
    raise SystemExit(main())
