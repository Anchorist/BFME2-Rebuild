"""Protected matrix preparation, per-runner native comparison and receipt join."""
from contextlib import contextmanager
import os
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace

from common import HEX64, PIN, digest, read, validate_binding, write
from compare import difference, make_report, native_commands, protected_judge
from compact_matrix import make_compact, join_compact
from diff_scope import diff_lines
from edited_functions import edited
from finished_index import Owners
from gitrepo import Git
from intake import reconstruct
from managed_matrix import SIDES, assignment, check_native, compiler_receipt, make
import measure as canary_measure
from measure import audit, pin
from pool_protocol import safe_diagnostics
from reporting import GATES, STATES, numeric, safe_listing
from wide_plan import identity

RUNNERS = 16
BATCH = 8
MAX_RECEIPT = 4 * 1024**2


def admission(path):
    path = Path(path)
    saved = path / "plan.json"
    plan = validate_binding(read(saved))
    decision = read(path / "decision.json", 4096)
    plan_hash = digest(saved.read_bytes())
    if (decision["kind"] != "wide" or decision["plan"] != plan_hash
            or any(decision[key] != plan[key] for key in ("number", "repo", "base", "head", "tree"))
            or plan["base"] != os.environ["GITHUB_SHA"]):
        raise ValueError("The wide input differs from protected admission.")
    return plan, plan_hash


@contextmanager
def comparison_inputs(plan):
    baseline = (Path.cwd() / "baseline/game.dat").resolve(strict=True)
    pin(baseline, PIN["baseline_sha256"])
    tools = audit(PIN)
    with tempfile.TemporaryDirectory(prefix="bfme-managed-wide-") as name:
        work = Path(name)
        git = Git(work / "source.git", initialize=True)
        checkout = Git(Path.cwd() / ".git")
        if checkout.rev("HEAD") != plan["base"]:
            raise ValueError("The wide comparison has an unexpected base checkout.")
        alternates = git.path / "objects/info/alternates"
        alternates.write_text(str((checkout.path / "objects").resolve(strict=True)) + "\n")
        git.run("update-ref", "refs/heads/main", plan["base"])
        tip = reconstruct(git, plan)
        judge = protected_judge(work / "home", tools, baseline)
        judge.BARE = git.path
        yield work, git, tip, judge, tools


def plan_matrix(source, out):
    plan, _ = admission(source)
    with comparison_inputs(plan) as (_, git, tip, judge, tools):
        commands = {side: native_commands(git, judge, rev, plan["request_paths"], tools)
                    for side, rev in (("base", plan["base"]), ("head", tip))}
    document = make(plan, commands, limit=RUNNERS)
    out.mkdir(mode=0o700)
    write(out / "matrix.json", document)
    indexes = list(range(len(document["partition"]["shards"])))
    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as stream:
        stream.write("shards=[" + ",".join(map(str, indexes)) + "]\n")
        stream.write("matrix_sha=" + identity(document) + "\n")


def load_matrix(path, expected, plan):
    doc = read(Path(path) / "matrix.json", 3 * 1024**2)
    if (not HEX64.fullmatch(expected) or identity(doc) != expected
            or doc["scope_sha256"] != identity(plan)
            or doc["partition"]["binding"] != {key: plan[key] for key in ("base", "head", "tree")}
            or doc["partition"]["compile_rows"] != 2 * len(plan["request_paths"])):
        raise ValueError("The sealed compile matrix differs from the protected plan.")
    return doc


def sanitize_outcome(raw, path, changed):
    def gate_key(value):
        if "annotation" in value:
            label = "annotations"
        elif "assembly" in value or " asm " in value:
            label = "assembly"
        else:
            label = next((phrase for phrase in GATES if phrase in value), "native")
        return label + " " + digest(value.encode())

    verdict = {"rows": [{key: row[key] for key in ("rva", "status", "credited", "proof", "pct") if key in row}
                        for row in raw["rows"]],
               "object_verified": bool(raw.get("object_verified")),
               "gates": sorted({gate_key(value) for value in raw["gates"]})}
    if raw.get("error"):
        located = safe_diagnostics(path, raw["error"], tuple(sorted(changed)))
        diagnostics = "\n".join(line for line in located.splitlines() if line.split("(", 1)[0] in changed)
        verdict["error"] = diagnostics or "Compilation failed in an affected translation unit."
    check_native(verdict)
    return verdict


def clean_difference(value, listing):
    return {key: field for key, field in {
        "first": numeric(value.get("first"), 2**31),
        "compiled_size": numeric(value.get("compiled_size"), 2**31),
        "retail_size": numeric(value.get("retail_size"), 2**31),
        "compiled_listing": safe_listing(value.get("compiled_listing", [])) if listing else [],
        "reference_listing": safe_listing(value.get("reference_listing", [])) if listing else [],
    }.items() if field is not None}


def measure_batch(git, judge, side, plan, tools, job):
    """Preserve the optional assembly allowances from the protected base."""
    previous = canary_measure.CONFIG
    base = plan["historical_base"]
    asm = "asm_allowlist.json"
    if git.run("cat-file", "-e", f"{base}:config/{asm}", check=False).returncode == 0:
        canary_measure.CONFIG = (*previous, asm)
    try:
        return canary_measure.measure(git, judge, side, plan, tools, job)
    finally:
        canary_measure.CONFIG = previous


def compile_shard(source, matrix, expected, index, out):
    plan, _ = admission(source)
    doc = load_matrix(matrix, expected, plan)
    commands_by_side = assignment(doc, index, expected=expected)
    records, reports, details = [], {side: {} for side in SIDES}, {}
    with comparison_inputs(plan) as (work, git, tip, judge, tools):
        owners = Owners(git, plan["base"])
        adapter = SimpleNamespace(ANNOT=judge.ANNOT, land_gate9=SimpleNamespace(diff_lines=diff_lines))
        edited_keys = {(item["owner"], item["address"]) for item in edited(git, adapter, plan["base"], tip, owners)}
        changed = set(plan["changed_paths"])
        for side in SIDES:
            commands = commands_by_side[SIDES[side]]
            paths = [row["tu"] for row in commands]
            rev = plan["base"] if side == "base" else tip
            if native_commands(git, judge, rev, paths, tools) != commands:
                raise ValueError("A shard command differs from the protected native compiler settings.")
            for begin in range(0, len(paths), BATCH):
                batch = commands[begin:begin + BATCH]
                names = [command["tu"] for command in batch]
                native = dict(plan, historical_base=plan["base"], historical_head=tip,
                              request_paths=names, compile={side: batch})
                job = work / f"{side}-{begin}"
                results = measure_batch(git, judge, side, native, tools, job)
                if list(results) != names:
                    raise ValueError("The trusted comparator omitted a planned TU.")
                for command in batch:
                    path = command["tu"]
                    raw = results[path]
                    obj = job / "obj" / (path.replace("/", "_") + ".obj")
                    value = {key: command[key] for key in ("tu", "source", "contract")} | {"side": SIDES[side]}
                    reports[side][path] = sanitize_outcome(raw, path, changed)
                    if obj.is_file():
                        local = read(obj.with_suffix(".obj.compile.json"), 4 * 1024**2)
                        if (local["source_sha256"] != command["source"] or local["compiler_contract"] != command["contract"]
                                or not HEX64.fullmatch(local["object_sha256"])):
                            raise ValueError("The local comparison changed a verified compiler receipt.")
                        dependencies = sorted((str(Path(label).relative_to(job)) if Path(label).is_relative_to(job)
                                               else "sealed/" + Path(label).name, checksum)
                                              for label, checksum in local["headers"].items())
                        value.update(status="compiled", object_sha256=local["object_sha256"], dependencies=dependencies)
                    elif raw.get("error"):
                        value["status"] = "error"
                    else:
                        raise ValueError("The local comparison omitted the compiler outcome.")
                    records.append(value)
                    if side == "head" and obj.is_file():
                        for row in raw["rows"]:
                            if row["status"] != "PARTIAL":
                                continue
                            listing = (path, int(row["rva"], 16)) in edited_keys
                            record = difference(judge, obj, row, listing)
                            if record:
                                details[path + "@" + row["rva"]] = clean_difference(record, listing)
    receipt = make_compact(doc, expected=expected, run=os.environ["GITHUB_RUN_ID"],
                           attempt=os.environ["GITHUB_RUN_ATTEMPT"],
                           compiler=compiler_receipt(doc, index, records), native=reports, details=details)
    out.mkdir(mode=0o700)
    target = out / "shard.json"
    write(target, receipt)
    if target.stat().st_size > MAX_RECEIPT:
        raise ValueError("The protected shard verdict exceeded its size allowance.")


def join_receipts(doc, artifacts, expected, run, attempt):
    expected_dirs = {f"shard-{index}" for index in range(len(doc["partition"]["shards"]))}
    if {item.name for item in artifacts.iterdir()} != expected_dirs:
        raise ValueError("The wide comparison is missing a shard or has an unexpected one.")
    receipts = [read(artifacts / folder / "shard.json", MAX_RECEIPT) for folder in sorted(expected_dirs)]
    tables, details, _inline = join_compact(doc, receipts, expected=expected, run=run, attempt=attempt)
    partial = {path + "@" + row["rva"] for path, outcome in tables["head"].items()
               for row in outcome["rows"] if row["status"] == "PARTIAL"}
    if details.keys() - partial:
        raise ValueError("A shard supplied near-miss details outside its partial results.")
    return tables, details


def combine(source, matrix, expected, staging, out):
    plan, plan_sha = admission(source)
    doc = load_matrix(matrix, expected, plan)
    # Same-run downloads keep the artifact directory, including its attempt-prefix name.
    prefix = "bfme-wide-" + os.environ["GITHUB_RUN_ATTEMPT"] + "-"
    normalized = staging.parent / "shards-for-join"
    normalized.mkdir(mode=0o700)
    for path in staging.iterdir():
        index = path.name.removeprefix(prefix)
        if not path.name.startswith(prefix) or not re.fullmatch(r"(?:0|[1-9][0-9]?)", index) or not path.is_dir():
            raise ValueError("The wide download contains an unexpected artifact.")
        (normalized / ("shard-" + index)).symlink_to(path.resolve(strict=True))
    tables, offsets = join_receipts(doc, normalized, expected, os.environ["GITHUB_RUN_ID"],
                                    os.environ["GITHUB_RUN_ATTEMPT"])

    def lookup(path, row, own):
        result = offsets.get(path + "@" + row["rva"])
        return clean_difference(result, own) if result else None
    with comparison_inputs(plan) as (_, git, tip, judge, _tools):
        report, counts, functions = make_report(git, judge, plan, tip, tables["base"], tables["head"],
            lambda _path: None, lookup_difference=lookup)
    out.mkdir(mode=0o700)
    write(out / "verdict.json", {key: plan[key] for key in ("version", "repo", "number", "base", "head", "tree")}
          | {"plan": plan_sha, "report": report, "counts": counts, "functions": functions,
             "matrix": {"runners": len(doc["partition"]["shards"]), "paired_results": 2 * len(tables["base"])}})


def main(mode, *args):
    os.umask(0o077)
    if mode == "plan":
        plan_matrix(*map(Path, args))
    elif mode == "compile":
        source, matrix, expected, index, out = args
        compile_shard(Path(source), Path(matrix), expected, int(index), Path(out))
    elif mode == "join":
        source, matrix, expected, staging, out = args
        combine(Path(source), Path(matrix), expected, Path(staging), Path(out))
    else:
        raise ValueError("Unknown protected matrix operation.")


if __name__ == "__main__":
    main(*sys.argv[1:])

