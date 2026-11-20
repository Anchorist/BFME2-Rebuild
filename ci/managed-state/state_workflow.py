"""Plan and verify exact-main state workflow inputs without publication credentials."""
import os
from pathlib import Path
import re
import sys

from state_snapshot import MAX_PLAN_BYTES, MAX_SHARD_BYTES, assemble, authoritative_units, canonical, digest, load, make_plan, validate_plan
from state_compact import compact

sys.path.append(str(Path(__file__).resolve().parent.parent / "managed-check"))
from common import HEX40, PIN, REPO, REPO_ID, read
from gitrepo import Git
from state_evidence import LIMIT, cached_pairs, header
from state_delta import inherited, merge


def make_checked_plan(root, main, budget, *, measured=None):
    if not re.fullmatch(r"[1-9][0-9]{0,2}", budget) or int(budget) > 128:
        raise ValueError("Set BFME_STATE_BUDGET_JOBS to the approved runner cap, between 1 and 128.")
    plan = make_plan(root, main, PIN["checker"], per_batch=32)
    if measured is not None:
        plan["batches"] = [measured[i:i+32] for i in range(0, len(measured), 32)]
        validate_plan(plan)
    count = len(plan["batches"])
    if count > int(budget):
        raise ValueError(f"This full refresh requires {count} runners, above the {budget}-runner cap.")
    return plan


def assembled(root, plan, directory, attempt, *, required=None):
    if not re.fullmatch(r"[1-9][0-9]{0,19}", attempt):
        raise ValueError("Use the exact Actions attempt.")
    prefix = f"bfme-state-{attempt}-shard-"
    expected = {prefix + str(index): index for index in range(len(plan["batches"]))}
    if set(expected) != {path.name for path in directory.iterdir()}:
        raise ValueError("Missing or foreign state shard artifacts. Keep the prior state.")
    shards = []
    for name, index in expected.items():
        root_dir = directory / name
        if root_dir.is_symlink() or not root_dir.is_dir():
            raise ValueError("An unexpected state shard directory was returned.")
        path = root_dir / f"state-shard-{index}.json"
        doc = load(path, MAX_SHARD_BYTES)
        if doc.get("batch") != index:
            raise ValueError("A state shard's batch does not match its artifact.")
        shards.append(doc)
    return assemble(plan, shards, root, required=required)

 
def assemble_evidence(root, plan, directory, attempt):
    main = plan["main"]
    tree = Git(root / ".git").value("rev-parse", main + "^{tree}")
    identity = header(main, tree)
    evidence = {}
    for index, paths in enumerate(plan["batches"]):
        row = load(directory / f"bfme-state-{attempt}-shard-{index}" / f"base-shard-{index}.json",
                   MAX_SHARD_BYTES)
        if (row.pop("plan", None) != digest(plan) or row.pop("batch", None) != index
                or set(row["evidence"]) != set(paths)):
            raise ValueError("Exact base evidence has incomplete or foreign translation units.")
        commands = [{"tu": tu, **{key: row["evidence"][tu]["compiler"][key] for key in ("source", "contract")}}
                    for tu in paths]
        evidence.update(cached_pairs(row, identity, commands))
    return identity | {"evidence": evidence}


def main(mode, *args):
    root = Path.cwd()
    main = os.environ["GITHUB_SHA"]
    if (os.environ.get("GITHUB_REPOSITORY") != REPO or os.environ.get("GITHUB_REPOSITORY_ID") != str(REPO_ID)
            or os.environ.get("GITHUB_REF") != "refs/heads/main" or not HEX40.fullmatch(main)):
        raise ValueError("Use the configured protected repository and main revision.")
    if mode == "plan":
        if os.environ.get("GITHUB_EVENT_NAME") == "repository_dispatch":
            event = read(os.environ["GITHUB_EVENT_PATH"], 128 * 1024)
            record = event.get("client_payload")
            if (event.get("action") != "bfme-landed" or not isinstance(record, dict)
                    or set(record) != {"number", "head", "parent", "commit", "tree"}
                    or type(record["number"]) is not int or not 0 < record["number"] < 10**9
                    or not all(isinstance(record[key], str) and HEX40.fullmatch(record[key])
                               for key in ("head","parent","commit","tree"))
                    or record["commit"] != main):
                raise ValueError("Expected the exact protected landing receipt. Found an invalid or stale dispatch.")
            checkout = Git(root / ".git")
            if (checkout.rev(main + "^") != record["parent"]
                    or checkout.value("rev-parse", main + "^{tree}") != record["tree"]):
                raise ValueError("Expected the landed parent and tree from the repository. Found different Git objects.")
        units = authoritative_units(root, main)
        carried = inherited(root, main, Path(args[2])) if len(args) == 3 else {}
        measured = sorted(set(units) - set(carried))
        if not measured:
            measured.append(units[0])
            del carried[units[0]]
        result = make_checked_plan(root, main, os.environ.get("STATE_BUDGET", ""), measured=measured)
        print(f"Measuring {len(measured)} units. Reusing {len(carried)} unaffected units from the exact predecessor.")
        if len(args) == 3:
            tree = Git(root / ".git").value("rev-parse", main + "^{tree}")
            stored = canonical(header(main, tree) | {"plan": digest(result), "evidence": carried})
            if len(stored) > LIMIT:
                raise ValueError("Inherited state exceeds its artifact allowance.")
            with Path(args[1]).open("xb") as file:
                file.write(stored)
        batches = ",".join(str(index) for index in range(len(result["batches"])))
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as file:
            file.write(f"batches=[{batches}]\n")
        out = Path(args[0])
    elif mode == "assemble":
        plan, shards, out, *cache = map(Path, args)
        plan = load(plan, MAX_PLAN_BYTES)
        if plan["main"] != main or plan["checker"] != PIN["checker"]:
            raise ValueError("The state plan names a different revision or protected checker.")
        attempt = os.environ["GITHUB_RUN_ATTEMPT"]
        required = authoritative_units(root, main)
        tree = Git(root / ".git").value("rev-parse", main + "^{tree}")
        identity = header(main, tree)
        carry = {}
        if len(cache) == 2:
            saved = load(cache[1], LIMIT)
            if saved.pop("plan", None) != digest(plan):
                raise ValueError("Inherited evidence belongs to a different refresh plan.")
            carry = saved["evidence"]
            commands = [{"tu": tu, **{key: entry["compiler"][key] for key in ("source", "contract")}}
                        for tu, entry in carry.items()]
            cached_pairs(saved, identity, commands)
        dirty = [tu for batch in plan["batches"] for tu in batch]
        result = assembled(root, plan, shards, attempt, required=dirty)
        carried_numeric = compact({"binding": {}, "results": [entry.get("wide_native", entry["native"]) | {"tu": tu}
                                                                for tu, entry in carry.items()]},
                                  carry, prehashed=True)
        result["tus"] = merge(required, result["tus"], carried_numeric)
        if cache:
            assembled_cache = assemble_evidence(root, plan, shards, attempt)
            assembled_cache["evidence"] = merge(required, assembled_cache["evidence"], carry)
            content = canonical(assembled_cache)
            if len(content) > LIMIT:
                raise ValueError("Exact parent evidence exceeds its publication budget.")
            with cache[0].open("xb") as file:
                file.write(content)
    else:
        raise ValueError("Unknown protected state workflow operation.")
    with out.open("xb") as file:
        file.write(canonical(result))


if __name__ == "__main__":
    os.umask(0o077)
    main(*sys.argv[1:])
