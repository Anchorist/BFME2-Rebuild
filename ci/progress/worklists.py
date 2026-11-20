"""Regenerate worklist/*.tsv for one main commit with worklist/generate.py, then run it again and compare.

    python3 -B ci/progress/worklists.py --checkout . --main SHA --state-dir STATE --out OUT [--link-missing TSV]

The checkout must be at SHA. Inputs:
  - the source tree at SHA (Draft headers in use and unused, stand-in types);
  - the `state` branch for SHA (per-file verdicts for files.tsv);
  - the link input: with --link-missing (link-missing.tsv from branch nightly, written by the daily
    link census), one row per name the link still misses, with how many rebuilt objects refer to
    it; each name is mapped to the function that owns it in config/map.json at SHA and to that
    function's verdict on the state branch. Without it, the dated table in worklist/ at SHA.
  - the dated unwritten-functions table in worklist/ at SHA, turned back into generate.py's input
    form. Every row is re-checked against the bodies on SHA and rows now written drop out; its
    measurement date and revision stay what they were.
generate.py runs twice, in separate output folders and with different hash seeds; the two
outputs must be byte-identical, else the step fails and says which file differs.
"""
import argparse
import csv
import filecmp
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(1, str(HERE.parent / "state"))
from layout import Refused, join  # noqa: E402

DONOR = "reference/CnC_Generals_Zero_Hour/GeneralsMD/Code/"
META = re.compile(r"^# measured_utc=(\S+) revision=([0-9a-f]{7,40})")
CENSUS = re.compile(r"^# link census of ([0-9a-f]{40}) on (\d{4}-\d\d-\d\d)\b")
RANKED_COLUMNS = ["referrers", "state", "rva", "file", "symbol", "first_referrer"]
OUTPUTS = ("draft_headers_in_use.tsv", "draft_headers_unused.tsv", "stand_in_types.tsv",
           "files.tsv", "unwritten_with_zero_hour_counterpart.tsv", "link_ranked.tsv")


def read_table(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    meta = META.match(lines[0]) if lines else None
    if not meta:
        raise Refused(f"worklist input {path.name}: expected a first line '# measured_utc=... revision=...', "
                      f"found {lines[0][:80] if lines else 'an empty file'!r}")
    return meta.groups(), list(csv.DictReader(lines[1:], delimiter="\t"))


def write_tsv(path, first, columns, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        stream.write(first + "\n")
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)


def owners(checkout):
    """Decorated name -> (rva, owning source file) for every owned function of config/map.json.
    A name two owned functions claim is left out (returned separately), never guessed."""
    ledger = json.loads((Path(checkout) / "config/map.json").read_text(encoding="utf-8"))
    files = {obj["object_id"]: obj.get("tu") for obj in ledger["objects"]}
    seen, ambiguous = {}, set()
    for row in ledger["rows"]:
        rva = row.get("rva", "")
        if row.get("role") != "owned" or not re.fullmatch(r"0x[0-9a-fA-F]{1,8}", rva):
            continue
        tu = files.get(row.get("object"))
        if not tu:
            continue
        target = (int(rva, 16), tu)
        names = {row.get("name") or ""} | set(row.get("accepted_names") or [])
        for name in filter(None, names):  # the ledger stores the linker's own spellings (_WinMain@16, ?f@X@@...)
            if seen.get(name, target) != target:
                ambiguous.add(name)
            seen.setdefault(name, target)
    for name in ambiguous:
        seen.pop(name, None)
    return seen, ambiguous


def ranked_from_census(path, checkout, state):
    """generate.py's ranked input from link-missing.tsv: (first line, rows, counts)."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    meta = CENSUS.match(lines[0]) if lines else None
    if not meta:
        raise Refused(f"link-missing.tsv: expected a first line '# link census of <40-hex commit> on <YYYY-MM-DD>', "
                      f"found {lines[0][:80] if lines else 'an empty file'!r}")
    sha, day = meta.groups()
    table = list(csv.DictReader(lines[1:], delimiter="\t"))
    if table and not {"symbol", "referrers", "first_referrer"} <= set(table[0]):
        raise Refused(f"link-missing.tsv: expected columns symbol, referrers, first_referrer, found {sorted(table[0])}")
    index, ambiguous = owners(checkout)
    rows, unmapped, unclear = [], 0, 0
    for row in table:
        symbol, count = row["symbol"], row["referrers"]
        if not count.isdecimal():
            raise Refused(f"link-missing.tsv: expected a whole number of referrers for {symbol}, found {count!r}")
        if symbol in ambiguous:
            unclear += 1
            continue
        if symbol not in index:
            unmapped += 1
            continue
        rva, tu = index[symbol]
        key = f"0x{rva:08X}"
        verdict = (state["tus"].get(tu, {}).get("rows", {}).get(key) or ["UNMEASURED"])[0]
        rows.append([count, "owned:" + verdict, key, tu, symbol, row["first_referrer"]])
    first = f"# generated={day} standalone={sha}"
    return first, rows, {"names": len(table), "mapped": len(rows), "no_owner": unmapped, "two_owners": unclear}


def inputs(checkout, main, state_read, folder, link_missing=None):
    folder = Path(folder)
    state = join(state_read)
    if state["sha"] != main:
        raise Refused(f"worklists: expected the state of main {main}, found the state of {state['sha']}")
    verdicts = {"sha": main, "tus": {tu: {"rows": {hex(int(rva, 16)): value for rva, value in unit["rows"].items()}}
                                     for tu, unit in state["tus"].items()}}
    (folder / "verdicts.json").write_text(json.dumps(verdicts, sort_keys=True))
    worklist = Path(checkout) / "worklist"
    counts = None
    if link_missing and Path(link_missing).is_file():
        first, rows, counts = ranked_from_census(link_missing, checkout, state)
        write_tsv(folder / "ranked.tsv", first, RANKED_COLUMNS, rows)
    else:
        (date, revision), rows = read_table(worklist / "link_ranked.tsv")
        write_tsv(folder / "ranked.tsv", f"# generated={date} standalone={revision}", RANKED_COLUMNS,
                  [[r[k] for k in RANKED_COLUMNS] for r in rows])
    (date, revision), rows = read_table(worklist / "unwritten_with_zero_hour_counterpart.tsv")
    converted = []
    for r in rows:
        if not r["zero_hour_file"].startswith(DONOR) or not r["zero_hour_line"].isdecimal():
            raise Refused(f"worklist input: expected a reference path under {DONOR} with a line number, "
                          f"found {r['zero_hour_file']!r} line {r['zero_hour_line']!r} for {r['rva']}")
        converted.append([r["rva"], r["function"], r["owner_file"], r["size_bytes"],
                          f"{r['zero_hour_file'][len(DONOR):]}:{r['zero_hour_line']},{r['reference_kind']}",
                          r["link_referrers"], r["ready_at_snapshot"]])
    write_tsv(folder / "unwritten.tsv", f"# generated {date} main={revision}",
              ["rva", "class::method", "file", "size", "zh_file:line,kind", "referrers", "writable"], converted)
    return counts


def run_generate(checkout, main, folder, out, seed):
    command = [sys.executable, "-B", str(Path(checkout) / "worklist/generate.py"), "--root", str(checkout),
               "--revision", main, "--output", str(out), "--unwritten", str(folder / "unwritten.tsv"),
               "--ranked", str(folder / "ranked.tsv"), "--verdicts", str(folder / "verdicts.json")]
    done = subprocess.run(command, capture_output=True, text=True, env=os.environ | {"PYTHONHASHSEED": seed})
    if done.returncode:
        tail = (done.stderr.strip().splitlines() or ["no message"])[-1]
        raise Refused(f"worklist/generate.py: expected exit 0, found {done.returncode}: {tail}")
    return " ".join(command[3:]).replace(str(folder), "worklist/inputs").replace(str(out), "OUT")


def regenerate(checkout, main, state_read, out, link_missing=None, report=print):
    out = Path(out)
    with tempfile.TemporaryDirectory(prefix="bfme-worklist-") as folder:
        folder = Path(folder)
        counts = inputs(checkout, main, state_read, folder, link_missing)
        if counts:
            report(f"Link input from the daily census: {counts['names']} missing names, {counts['mapped']} mapped to "
                   f"their owner function, {counts['no_owner']} with no owned function in the ledger, "
                   f"{counts['two_owners']} claimed by two owned functions (left out).")
        else:
            report("Link input: no daily census export yet; using the dated table in worklist/.")
        first, second = folder / "first", folder / "second"
        command = run_generate(checkout, main, folder, first, "0")
        run_generate(checkout, main, folder, second, "12345")
        made = sorted(p.name for p in first.iterdir())
        if made != sorted(OUTPUTS):
            raise Refused(f"worklists: expected {sorted(OUTPUTS)}, found {made}")
        for name in made:
            if not filecmp.cmp(first / name, second / name, shallow=False):
                raise Refused(f"worklists: expected two runs of generate.py to write identical {name}, found a difference")
        out.mkdir(parents=True, exist_ok=True)
        for name in made:
            (out / name).write_bytes((first / name).read_bytes())
        (out / "inputs").mkdir(exist_ok=True)
        for name in ("verdicts.json", "ranked.tsv", "unwritten.tsv"):
            (out / "inputs" / name).write_bytes((folder / name).read_bytes())
    return command


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", default=".")
    parser.add_argument("--main", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--link-missing", default="")
    args = parser.parse_args()
    root = Path(args.state_dir)
    try:
        command = regenerate(Path(args.checkout).resolve(), args.main, lambda p: (root / p).read_bytes(), args.out,
                             args.link_missing or None)
    except (Refused, OSError, ValueError) as error:
        print(f"::error::{error}")
        return 1
    print(f"Worklists regenerated for main {args.main}; two runs identical. Same as a local run of:")
    print("  python3 worklist/generate.py " + command)
    return 0


if __name__ == "__main__":
    sys.exit(main())
