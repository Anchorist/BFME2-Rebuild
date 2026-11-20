"""Linking figure: how many of the names the rebuilt program needs are provided.

  python3 -B ci/nightly/link_census.py SHARD_ROOT --names ci/nightly/link-names/library-names.txt --out OUT.json
      [--map config/map.json] [--missing-out MISSING.tsv]

Reads the symbol tables of every compiled object (`*.obj`) in the given directories and resolves them the way the
linker would, against each other and against the names the standard libraries and import libraries define (listed
in the names file). Writes OUT.json:

  needed    distinct names that some rebuilt object refers to (an undefined, weak or forced reference) and that it
            does not define itself; the linker's own built-in names are left out
  missing   the needed names that no rebuilt object and no listed library defines
  provided  needed - missing
  pair      [provided, needed], the form the progress card reads

The same objects and the same names file always give the same numbers.
"""
import argparse
import collections
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "planner"))
import coffsym  # noqa: E402
import resolve  # noqa: E402

LINKER_KNOWN = {"___ImageBase"}


def kind(name):
    if name.startswith("__imp_"):
        return "import"
    if name.startswith("??_7") or name.startswith("??_R"):
        return "vtable-or-type-info"
    if name.startswith("?"):
        return "c++"
    return "c"


def census(object_paths, library_names):
    order = sorted(object_paths, key=lambda p: Path(p).name)
    idx = {p: coffsym.obj_symbols(p) for p in order}
    idx["<libraries>"] = {"lib": True, "defs": {n: [False, "lib", 0, "", 0] for n in library_names},
                          "undefs": [], "weak": {}}
    r = resolve.resolve(order + ["<libraries>"], idx)
    missing = {n for n in r["unresolved"] if n not in LINKER_KNOWN}
    needed = set()
    for p in order:
        s = idx[p]
        own = set(s.get("defs", {}))
        refs = set(s.get("undefs", [])) | set(s.get("weak", {})) | set(s.get("include", []))
        needed |= {n for n in refs - own if n not in LINKER_KNOWN}
    needed |= missing
    by_kind = collections.Counter(kind(n) for n in missing)
    referrers = {n: sorted(Path(p).name for p in r["unresolved"][n]) for n in missing}
    defined = set()
    for p in order:
        defined |= set(idx[p].get("defs", {}))
    return {"objects": len(order), "needed": len(needed), "missing": len(missing),
            "provided": len(needed) - len(missing), "pair": [len(needed) - len(missing), len(needed)],
            "missing_by_kind": dict(sorted(by_kind.items())), "duplicates": len(r["duplicates"]),
            "duplicate_names": sorted(r["duplicates"]),
            "_referrers": referrers, "_defined": defined}


def program_functions(map_json, defined):
    """Of every distinct function address the ledger says the original program owns, how many our files define
    under one of its accepted names: [provided, total]."""
    names = collections.defaultdict(set)
    for row in map_json["rows"]:
        if row.get("role") == "owned":
            names[row["rva"]].update([row["name"]] + list(row.get("accepted_names") or []))
    provided = sum(1 for ns in names.values() if ns & defined)
    return [provided, len(names)]


def source_of(root):
    """{object file name: source path} from the shards' judge.jsonl."""
    out = {}
    for jl in Path(root).rglob("judge.jsonl"):
        for line in jl.read_text().splitlines():
            if line.strip():
                tu = json.loads(line)["tu"]
                out[tu.replace("/", "_") + ".obj"] = tu
    return out


def missing_table(referrers, source, sha, date, objects):
    """The missing names, most referred first: one row per name with the number of rebuilt objects referring to it
    and the source path of the first such object in sorted order."""
    rows = sorted(referrers.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    out = [f"# link census of {sha} on {date} objects={objects} missing={len(rows)}",
           "symbol\treferrers\tfirst_referrer"]
    out += [f"{n}\t{len(rs)}\t{source.get(rs[0], rs[0]) if rs else ''}" for n, rs in rows]
    return "\n".join(out) + "\n"


def object_set(root):
    """The exact objects the compile shards under `root` say they produced, checked against their receipts.

    Each shard directory holds judge.jsonl (one judged source file per line) and obj/<file>.obj with its
    <file>.obj.compile.json receipt. Returns the sorted object paths; raises ValueError naming the first defect:
    an object for a file no shard judged, a file judged twice, an object found twice, a judged and compiled file
    without its object, or an object whose SHA-256 differs from its receipt."""
    import hashlib
    expected, judged = set(), set()
    for jl in sorted(Path(root).rglob("judge.jsonl")):
        for line in jl.read_text().splitlines():
            if not line.strip():
                continue
            tu = json.loads(line)["tu"]
            if tu in judged:
                raise ValueError(f"expected each source file judged once; found {tu} twice")
            judged.add(tu)
            if not json.loads(line).get("error"):
                expected.add(tu.replace("/", "_") + ".obj")
    found = collections.defaultdict(list)
    for p in Path(root).rglob("*.obj"):
        found[p.name].append(p)
    twice = sorted(n for n, ps in found.items() if len(ps) > 1)
    if twice:
        raise ValueError(f"expected each object once; found {twice[0]} {len(found[twice[0]])} times")
    extra = sorted(set(found) - expected)
    missing = sorted(expected - set(found))
    if extra or missing:
        raise ValueError(f"expected exactly the {len(expected)} objects the shards record; found {len(found)} "
                         f"({len(extra)} unrecorded, first {extra[:1]}; {len(missing)} absent, first {missing[:1]})")
    for name, (p,) in sorted(found.items()):
        receipt = p.with_name(name + ".compile.json")
        want = json.loads(receipt.read_text()).get("object_sha256") if receipt.is_file() else None
        if want != hashlib.sha256(p.read_bytes()).hexdigest():
            raise ValueError(f"expected {name} to match its compile receipt; found {'a different object' if want else 'no receipt'}")
    return sorted(str(ps[0]) for ps in found.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", help="directory holding the compile shards (judge.jsonl, obj/)")
    ap.add_argument("--names", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--map", help="config/map.json of the measured commit: adds the whole-program function figure")
    ap.add_argument("--missing-out", help="write the missing names with their referrer counts as TSV")
    a = ap.parse_args()
    try:
        objs = object_set(a.root)
    except (ValueError, OSError, KeyError) as e:
        raise SystemExit(f"link census: {e}")
    if not objs:
        raise SystemExit(f"link census: expected compiled objects in {a.root}; found none")
    names = [l.strip() for l in Path(a.names).read_text().splitlines() if l.strip() and not l.startswith("#")]
    res = census(objs, names)
    referrers, defined = res.pop("_referrers"), res.pop("_defined")
    if a.map:
        res["program_functions"] = program_functions(json.loads(Path(a.map).read_text()), defined)
    if a.missing_out:
        import datetime
        sha = os.environ.get("NIGHTLY_SHA") or os.environ.get("GITHUB_SHA", "")
        day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        Path(a.missing_out).write_text(missing_table(referrers, source_of(a.root), sha, day, res["objects"]))
    Path(a.out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(f"link census: {res['objects']} objects; {res['provided']} of {res['needed']} needed names provided, "
          f"{res['missing']} missing, {res['duplicates']} defined twice"
          + (f"; {res['program_functions'][0]} of {res['program_functions'][1]} functions of the original program "
             "defined" if a.map else ""))


if __name__ == "__main__":
    main()
