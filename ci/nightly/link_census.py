"""Linking figure: how many of the names the rebuilt program needs are provided.

  python3 -B ci/nightly/link_census.py OBJECT_DIR [OBJECT_DIR ...] --names ci/nightly/link-names/library-names.txt --out OUT.json

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
    defined_here = collections.defaultdict(set)
    needed = set()
    for p in order:
        s = idx[p]
        own = set(s.get("defs", {}))
        refs = set(s.get("undefs", [])) | set(s.get("weak", {})) | set(s.get("include", []))
        needed |= {n for n in refs - own if n not in LINKER_KNOWN}
    needed |= missing
    by_kind = collections.Counter(kind(n) for n in missing)
    return {"objects": len(order), "needed": len(needed), "missing": len(missing),
            "provided": len(needed) - len(missing), "pair": [len(needed) - len(missing), len(needed)],
            "missing_by_kind": dict(sorted(by_kind.items())), "duplicates": len(r["duplicates"])}


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
    a = ap.parse_args()
    try:
        objs = object_set(a.root)
    except (ValueError, OSError, KeyError) as e:
        raise SystemExit(f"link census: {e}")
    if not objs:
        raise SystemExit(f"link census: expected compiled objects in {a.root}; found none")
    names = [l.strip() for l in Path(a.names).read_text().splitlines() if l.strip() and not l.startswith("#")]
    res = census(objs, names)
    Path(a.out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(f"link census: {res['objects']} objects; {res['provided']} of {res['needed']} needed names provided, "
          f"{res['missing']} missing")


if __name__ == "__main__":
    main()
