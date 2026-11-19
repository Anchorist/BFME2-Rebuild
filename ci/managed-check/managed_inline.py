"""Stage the trusted per-side compiler receipts and create a report-only virtual comparison."""

from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import tempfile

from managed_matrix import SIDES
from pool_compare import TrustedPaths
from wide_plan import identity, join

INLINE = Path(__file__).resolve().parent / "inline_virtual"
sys.path.insert(0, str(INLINE))
from inline_virtual_ci import evaluate_spec
from inline_virtual_report import render

CATALOGUE = "984b900a17483866061d6fdb3f5e24280c51a91d7fcc30ec01a1aa1e03a05b7b"
BASELINE = "f008b587570bad693981dc7218588c81d192a1e064b0f7f861539c51156a7640"


def artifact_paths(index, digest, roots):
    root = Path(roots[index]).resolve(strict=True)
    data = root / (digest + ".obj")
    if data.is_symlink() or not data.is_file() or data.resolve() != data:
        raise ValueError("An inline-virtual shard object is outside the admitted artifacts.")
    return data.read_bytes()


def materialize(root, pin, planned, rows, tools, read_object, ownership):
    result = {"tus": sorted(planned), "contracts": {tu: row["contract"] for tu, row in planned.items()},
              "manifest": {"pin": pin, "compile_root": str(root), "objects": {}}}
    relative_root = root / "obj"
    relative_root.mkdir(parents=True)
    for index, row in rows:
        if row["status"] == "error":
            continue
        digest = row["object_sha256"]
        obj = relative_root / (sha256(row["tu"].encode()).hexdigest() + ".obj")
        source = read_object(index, digest)
        if sha256(source).hexdigest() != digest:
            raise ValueError("An inline-virtual COFF changed after joining its compile proof.")
        obj.write_bytes(source)
        headers = {}
        for dependency in row["dependencies"]:
            alias, path = ownership.dependency(dependency)
            name = root / path if alias == "source" else (Path(tools[alias]) / path).resolve(strict=True)
            existing = headers.setdefault(str(name), dependency[2])
            if existing != dependency[2]:
                raise ValueError("A virtual compiler certificate conflicts on a repeated include.")
        meta = {"source_sha256": row["source"], "object_sha256": digest, "headers": headers,
                "compiler_contract": row["contract"], "include_capture": "msvc-showIncludes-v1"}
        obj.with_suffix(".obj.compile.json").write_text(json.dumps(meta, sort_keys=True) + "\n")
        result["manifest"]["objects"][row["tu"]] = str(obj)
    return result


def evaluate(*, document, expected, repo, pin, reference, compiler, object_roots, source_hashes, tools,
             scope_complete, owners=None):
    """Return a compact verdict and deterministic text without affecting the main match result."""
    if identity(document) != expected or set(source_hashes) != set(SIDES):
        raise ValueError("Inline-virtual work is not pinned to the trusted matrix and source sets.")
    if sha256(Path(reference).read_bytes()).hexdigest() != BASELINE:
        raise ValueError("The inline-virtual reference image differs from the protected baseline.")
    authority = {SIDES[name]: TrustedPaths(tools, hashes) for name, hashes in source_hashes.items()}
    def deps(side, tu, dependencies):
        if len(dependencies) != len({tuple(item) for item in dependencies}):
            raise ValueError("A virtual proof repeated a dependency.")
        for dependency in dependencies:
            authority[side].dependency(dependency)
    def read_object(index, digest):
        return artifact_paths(index, digest, object_roots)
    join(document["partition"], compiler, read_object=read_object, validate_dependencies=deps)
    binding = document["partition"]["binding"]
    specs = {"repo": str(repo), "binding": binding, "scope_complete": scope_complete,
             "reference": str(reference), "owners": owners,
             "policy_sha256": document["pins"]["policy_sha256"],
             "catalogue": str(INLINE / "catalogue-audited.json"), "catalogue_sha256": CATALOGUE,
             "external_roots": sorted({str(Path(root).resolve(strict=True)) for root in tools.values()})}
    with tempfile.TemporaryDirectory(prefix="bfme-inline-virtual-") as work:
        for name, commit in (("candidate", pin), ("parent", binding["base"])):
            selected = [(receipt["shard"], row) for receipt in compiler for row in receipt["results"]
                        if row["side"] == name]
            specs[name] = materialize(Path(work) / "compare" / name, commit, document["instructions"][name],
                                      selected, tools, read_object, authority[name])
        receipt, evidence = evaluate_spec(specs)
    return receipt, evidence, report_text(receipt, evidence)


def report_text(receipt, evidence):
    report = render(evidence).splitlines(keepends=True)
    report[0] = {"pass": "Inline virtual report found no new comparable mismatch.\n",
                 "fail": "Inline virtual report found a new comparable mismatch.\n",
                 "pending": "Inline virtual report needs more compiler evidence.\n"}[receipt["state"]]
    return "".join(report)


def write_step_summary(report, summary=None):
    path = summary or os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        detail = "\n".join("    " + line for line in report.splitlines())
        with Path(path).open("a", encoding="utf-8") as stream:
            stream.write("\n## Inline virtual behaviour · report only\n\n" + detail + "\n")
