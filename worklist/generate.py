#!/usr/bin/env python3
"""Write the public worklists from two dated report inputs and a source checkout.

Every function row is checked against the checkout before it is written: a row
whose function already has a body (in its owning file, in a header that file
includes, or elsewhere under src/ or include/) is left out, and the remaining
rows say what the check found in `body_check`:

  none-found          no body under src/ or include/
  unclear             the qualified name opens something the scanner could not
                      parse as a body; look before you start
  owner-file-missing  the owning file named by the report is no longer in the
                      checkout; find the current owner first

The file view (files.tsv) lists every source file that still has owned
functions to finish: how many it owns, how many are not yet credited MATCH
(from the dated verdict input), their bytes, how many link referrers wait on
them, and whether the file's class already has a real header. Finishing a
file is the preferred unit of work.

The stand-in list (stand_in_types.tsv) names declarations in ordinary
headers (not Draft, not upstream libraries) whose return or parameter type is
`void *`. Many are a known type erased at a module boundary; some are
legitimate (buffers, allocators, callbacks with user data). Check the callers
before replacing one.

Draft headers are split in two: the ones some file includes (to retire by
promoting them) and the unused ones (layout leads for whoever writes that
class). An unused Draft whose class or file name already exists outside
include/Draft/ is left out: it is a dead copy, not a lead.
"""
import argparse
import bisect
from collections import Counter, defaultdict, namedtuple
import csv
import json
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess

DONOR = "reference/CnC_Generals_Zero_Hour/GeneralsMD/Code"
INCLUDE = re.compile(rb'(?m)^[ \t]*#[ \t]*include[ \t]*[<"]([^"\r\n>]+)[">]')
UNWRITTEN_META = re.compile(r"generated (\S+)\s+main=([0-9a-f]{7,40})")
LINK_META = re.compile(r"generated=(\S+) standalone=([0-9a-f]{7,40})")
SRC_EXT = (".h", ".hpp", ".inl", ".cpp", ".c", ".cc", ".cxx")
HDR_EXT = (".h", ".hpp", ".inl")
STRIP = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'', re.S)
BRACE = re.compile(r"[{};]")
CLS = re.compile(r'.*\b(?:class|struct)\s+(?:__declspec\s*\([^)]*\)\s*)?([A-Za-z_]\w*)[^;{}()]*$', re.S)
FUNC = re.compile(
    r"((?:[A-Za-z_]\w*\s*::\s*)*)(~?[A-Za-z_]\w*)\s*\(([^;{}]*)\)\s*(?:const\s*)?(?:volatile\s*)?"
    r"(?:throw\s*\([^)]*\)\s*)?(?::[^;{}]*)?$")
Def = namedtuple("Def", "path cls line")


class Index:
    """Includes, class names and function bodies of every source file and header in the checkout."""

    def __init__(self, root, files):
        self.files = set(files)
        self.includes, self.stripped, self.classes = {}, {}, {}
        self.defs = defaultdict(list)
        for path in files:
            if not path.lower().endswith(SRC_EXT):
                continue
            text = (root / path).read_bytes().decode("latin-1")
            self.includes[path] = [m.decode("latin-1") for m in INCLUDE.findall(text.encode("latin-1"))]
            stripped, defs, classes, newlines = scan(text)
            self.stripped[path] = stripped
            self.classes[path] = classes
            for cls_q, fn, enclosing, pos in defs:
                self.defs[fn].append(Def(path, cls_q or enclosing, bisect.bisect_right(newlines, pos) + 1))

    def resolve(self, owner, target):
        target = target.replace("\\", "/")
        for candidate in (target, "include/" + target, posixpath.join(posixpath.dirname(owner), target)):
            candidate = posixpath.normpath(candidate)
            if candidate in self.files:
                return candidate
        return None

    def header_closure(self, owner):
        seen, stack = set(), [owner]
        while stack:
            current = stack.pop()
            for target in self.includes.get(current, []):
                found = self.resolve(current, target)
                if found and found.lower().endswith(HDR_EXT) and found not in seen:
                    seen.add(found)
                    stack.append(found)
        return seen

    def body_check(self, owner, cls, fn):
        """Return 'written', 'none-found', 'unclear' or 'owner-file-missing'."""
        if fn is None:
            return "unclear"
        bodies = [d for d in self.defs.get(fn, []) if d.cls == cls]
        if bodies:
            return "written"
        if owner not in self.files:
            return "owner-file-missing"
        if cls:
            opening = re.compile(r"\b" + re.escape(cls) + r"\s*::\s*" + re.escape(fn) + r"\s*\([^;]*$", re.M)
            if any(opening.search(self.stripped.get(p, "")) for p in [owner, *self.header_closure(owner)]):
                return "unclear"
        return "none-found"


def scan(text):
    """Strip comments and literals, then walk braces to find function bodies and class bodies."""
    s = STRIP.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)
    newlines = [m.start() for m in re.finditer("\n", text)]
    defs, classes, stack, last = [], [], [], 0
    for m in BRACE.finditer(s):
        p, c = m.start(), s[m.start()]
        if c in ";}":
            if c == "}" and stack:
                stack.pop()
            last = p + 1
            continue
        chunk, last = s[last:p], p + 1
        kind, name = "other", None
        cm = CLS.match(chunk)
        if cm and not re.search(r"\benum\b", chunk):
            kind, name = "class", cm.group(1)
            classes.append(name)
        else:
            fm = FUNC.search(chunk)
            if fm:
                quals = re.findall(r"[A-Za-z_]\w*", fm.group(1))
                enclosing = next((n for k, n in reversed(stack) if k == "class"), None)
                defs.append((quals[-1] if quals else None, fm.group(2), enclosing, p))
                kind, name = "func", fm.group(2)
        stack.append((kind, name))
    return s, defs, classes, newlines


def split_name(name):
    name = re.sub(r"<[^<>]*>", "", name).strip()
    if "::" in name:
        parts = name.split("::")
        return parts[-2].strip(), parts[-1].strip()
    return None, name


def demangle(symbol):
    """MSVC-decorated name to (class or None, function); None when the form is not handled."""
    def scopes(s):
        out = []
        for piece in s.split("@"):
            if piece == "":
                break
            out.append(piece)
        return out
    if symbol.startswith(("__imp_", "?$", "??$")):
        return None
    if symbol.startswith(("??0", "??1")):
        parts = scopes(symbol[3:])
        if not parts:
            return None
        return (parts[0], parts[0]) if symbol[2] == "0" else (parts[0], "~" + parts[0])
    if symbol.startswith("??"):
        return None
    if symbol.startswith("?"):
        parts = scopes(symbol[1:])
        if not parts:
            return None
        return (parts[1] if len(parts) > 1 else None, parts[0])
    name = symbol[1:] if symbol.startswith("_") else symbol
    return None, name.split("@")[0]


def snapshot(path, pattern):
    lines = path.read_text(encoding="utf-8").splitlines()
    meta = next((m for line in lines if (m := pattern.search(line))), None)
    if meta is None:
        raise ValueError(f"Input lacks measurement date and revision: {path.name}")
    rows = csv.DictReader((line for line in lines if line and not line.startswith("#")), delimiter="\t")
    return meta.groups(), list(rows)


def write(path, meta, columns, rows, note=""):
    with path.open("w", newline="", encoding="utf-8") as stream:
        stream.write(f"# measured_utc={meta[0]} revision={meta[1]}{note}\n")
        csv_writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        csv_writer.writerow(columns)
        csv_writer.writerows(rows)


def checked_line(lines, line, qualified_name, kind):
    # The report may have been generated from a different checkout of the
    # released source. Keep the file and name and re-anchor the line.
    qualified = r"\s*::\s*".join(re.escape(part) for part in qualified_name.split("::"))
    token = qualified if kind == "def" else re.escape(qualified_name.rsplit("::", 1)[-1])
    pattern = re.compile(r"(?<![\w])" + token + r"\s*\(")
    locations = [
        index for index, source in enumerate(lines, 1)
        if not source.lstrip().startswith(("//", "/*", "*")) and pattern.search(source)
    ]
    if line in locations:
        return line
    nearest = sorted(locations, key=lambda item: (abs(item-line), item))
    if nearest and (len(nearest)==1 or abs(nearest[0]-line)<abs(nearest[1]-line)):
        return nearest[0]
    return ""


def unwritten(args, index, checked):
    meta, rows = snapshot(args.unwritten, UNWRITTEN_META)
    donor_root = args.root / DONOR
    names = {}
    for file in sorted(donor_root.rglob("*")):
        if file.is_file():
            name = file.relative_to(donor_root).as_posix()
            names.setdefault(name.casefold(), []).append(name)
    public_rows, dropped = [], 0
    lines_by_file = {}
    for row in rows:
        cls, fn = split_name(row["class::method"])
        status = index.body_check(row["file"], cls, fn)
        if status == "written":
            dropped += 1
            continue
        target, kind = row["zh_file:line,kind"].rsplit(",", 1)
        file, line = target.rsplit(":", 1)
        if not line.isdecimal():
            raise ValueError(f"Invalid reference line: {target}")
        donor_paths = names.get(file.casefold(), [])
        if file in donor_paths:
            actual = file
        elif len(donor_paths) == 1:
            actual = donor_paths[0]
        else:
            raise ValueError(f"Missing or ambiguous checked-in reference path: {file}")
        if actual not in lines_by_file:
            lines_by_file[actual] = (donor_root / actual).read_bytes().decode("latin-1").splitlines()
        anchor = checked_line(lines_by_file[actual], int(line), row["class::method"], kind)
        public_rows.append((row["rva"], row["class::method"], row["file"], int(row["size"]),
                            f"{DONOR}/{actual}", anchor, row["class::method"], kind,
                            int(row["referrers"] or 0), row["writable"], status))
    write(args.output / "unwritten_with_zero_hour_counterpart.tsv", meta,
          ["rva", "function", "owner_file", "size_bytes", "zero_hour_file", "zero_hour_line",
           "zero_hour_function", "reference_kind", "link_referrers", "ready_at_snapshot", "body_check"],
          public_rows, f" body_checked_against={checked} left_out_written={dropped}")


def link_ranked(args, index, checked):
    meta, rows = snapshot(args.ranked, LINK_META)
    columns = ["referrers", "state", "rva", "file", "symbol", "first_referrer"]
    rows.sort(key=lambda row: (-int(row["referrers"]), row["rva"], row["symbol"]))
    kept, dropped = [], 0
    for row in rows:
        parsed = demangle(row["symbol"])
        status = "unclear" if parsed is None else index.body_check(row["file"], *parsed)
        if status == "written":
            dropped += 1
            continue
        kept.append([row[key] for key in columns] + [status])
    write(args.output / "link_ranked.tsv", meta, columns + ["body_check"], kept,
          f" body_checked_against={checked} left_out_written={dropped}")


def draft_headers(args, index, files, meta):
    drafts = {f for f in files if f.startswith("include/Draft/") and PurePosixPath(f).suffix.lower() in HDR_EXT}
    counts = Counter()
    for file in files:
        if not file.lower().endswith(SRC_EXT):
            continue
        used = set()
        for target in index.includes.get(file, []):
            target = target.replace("\\", "/")
            for path in (target, "include/" + target, (PurePosixPath(file).parent / target).as_posix()):
                if path in drafts:
                    used.add(path)
                    break
        counts.update(used)
    outside_stem, outside_class = defaultdict(list), defaultdict(list)
    for file in files:
        if file.lower().endswith(HDR_EXT) and not file.startswith("include/Draft/"):
            outside_stem[PurePosixPath(file).stem].append(file)
            for name in index.classes.get(file, []):
                outside_class[name].append(file)
    in_use = sorted((d for d in drafts if counts[d]), key=lambda name: (-counts[name], name))
    leads, dead = [], 0
    for draft in sorted(d for d in drafts if not counts[d]):
        classes = index.classes.get(draft, [])
        if outside_stem.get(PurePosixPath(draft).stem) or any(outside_class.get(c) for c in classes):
            dead += 1
            continue
        leads.append((draft, ",".join(sorted(set(classes))) or "none-parsed"))
    write(args.output / "draft_headers_in_use.tsv", meta, ["header", "direct_including_files"],
          ((name, counts[name]) for name in in_use))
    write(args.output / "draft_headers_unused.tsv", meta, ["header", "classes_defined"], leads,
          f" left_out_duplicates={dead}")


def per_file(args, index, files):
    ledger = json.loads((args.root / "config/map.json").read_text(encoding="utf-8"))
    objects = {o["object_id"]: o for o in ledger["objects"]}
    present = set(files)
    verdicts, revision = {}, "none"
    if args.verdicts:
        state = json.loads(args.verdicts.read_text(encoding="utf-8"))
        verdicts, revision = state.get("tus", {}), state.get("sha", "unknown")
    waiting = Counter()
    if args.ranked:
        for row in snapshot(args.ranked, LINK_META)[1]:
            waiting[int(row["rva"], 16)] += int(row["referrers"] or 0)
    owned, todo, todo_bytes, todo_wait = Counter(), Counter(), Counter(), Counter()
    for row in ledger["rows"]:
        if row.get("role") != "owned":
            continue
        tu = (objects.get(row.get("object")) or {}).get("tu")
        if tu not in present:
            continue
        rva = int(row["rva"], 16)
        owned[tu] += 1
        verdict = verdicts.get(tu, {}).get("rows", {}).get(hex(rva), ["MISSING"])[0]
        if verdict != "MATCH":
            todo[tu] += 1
            todo_bytes[tu] += int(row.get("size") or 0)
            todo_wait[tu] += waiting.get(rva, 0)
    real = defaultdict(bool)
    draft = defaultdict(bool)
    for file in files:
        if not file.lower().endswith(HDR_EXT):
            continue
        names = {PurePosixPath(file).stem.lower(), *(c.lower() for c in index.classes.get(file, []))}
        for name in names:
            if file.startswith("include/Draft/"):
                draft[name] = True
            else:
                real[name] = True
    rows = []
    for tu, count in todo.items():
        stem = PurePosixPath(tu).stem.lower()
        if tu.startswith("src/unk/"):
            header = "address-named"
        else:
            header = "real" if real[stem] else "draft" if draft[stem] else "none"
        rows.append((tu, owned[tu], count, todo_bytes[tu], todo_wait[tu], header))
    rows.sort(key=lambda r: (r[5] == "address-named", r[2], -r[4], r[0]))
    finished = sum(1 for tu in owned if not todo[tu])
    try:
        date = subprocess.check_output(["git", "-C", str(args.root), "show", "-s", "--format=%cI", revision],
                                       stderr=subprocess.DEVNULL).decode().strip()
        date = datetime.fromisoformat(date).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except (subprocess.CalledProcessError, ValueError):
        date = "unknown"
    write(args.output / "files.tsv", (date, revision[:10]),
          ["file", "owned_functions", "not_yet_matched", "bytes_not_yet_matched", "link_referrers_waiting",
           "class_header"], rows, f" finished_files={finished}")


SKIP = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'|^[ \t]*#[^\n]*(?:\\\n[^\n]*)*', re.M)
DECL = re.compile(r'(?<![\w.])(?P<type>[A-Za-z_~][\w:\s*&<>,]*?)\s*(?<=[\s*&])(?P<name>[A-Za-z_~]\w*)\s*\((?P<params>[^;{}]*?)\)\s*(?:const\s*)?(?:=\s*0\s*)?(?=[;{])')
VOIDP = re.compile(r'\bvoid\s*(?:(?:const|volatile)\s*)?\*')
NOT_A_STAND_IN = re.compile(r'alloc|free|copy|mem|buffer|data|raw|lock|operator|new|delete|read|write|callback|user|param|handle|ptr|pointer|address', re.I)
BLOCKED = {'if', 'else', 'for', 'while', 'return', 'switch', 'case', 'catch', 'sizeof', 'typedef', 'using', 'delete', 'new'}


def stand_ins(args, files, meta):
    rows = []
    for file in files:
        if not file.startswith("include/") or file.startswith(("include/Draft/", "include/upstream/")):
            continue
        if not file.lower().endswith(HDR_EXT):
            continue
        raw = (args.root / file).read_bytes().decode("latin-1")
        text = SKIP.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), raw)
        for m in DECL.finditer(text):
            name = m.group("name")
            if name in BLOCKED or NOT_A_STAND_IN.search(name):
                continue
            where = [w for w, part in (("return", m.group("type")), ("parameter", m.group("params"))) if VOIDP.search(part)]
            if not where:
                continue
            rows.append((file, text.count("\n", 0, m.start("name")) + 1, name, "+".join(where)))
    rows.sort()
    write(args.output / "stand_in_types.tsv", meta, ["header", "line", "function", "void_pointer_in"], rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="checked-out source and reference tree")
    parser.add_argument("--revision", default="HEAD", help="source revision checked out under --root")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--unwritten", type=Path, help="dated correspondence report, including the header row")
    parser.add_argument("--ranked", type=Path, help="dated standalone link report")
    parser.add_argument("--verdicts", type=Path, help="dated checker state (per-file row verdicts)")
    args = parser.parse_args()
    args.output = args.output or args.root / "worklist"
    args.output.mkdir(parents=True, exist_ok=True)
    for path in ("src", "include"):
        subprocess.run(["git", "-C", str(args.root), "diff", "--quiet", args.revision, "--", path], check=True)
    git = ["git", "-C", str(args.root)]
    date, revision = subprocess.check_output([*git, "show", "-s", "--format=%cI %H", args.revision]).decode().split()
    date = datetime.fromisoformat(date).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    files = subprocess.check_output([*git, "ls-tree", "-r", "-z", "--name-only", args.revision, "--", "src", "include"]
                                    ).decode("utf-8", "surrogateescape").strip("\0").split("\0")
    index = Index(args.root, files)
    checked = revision[:10]
    old = args.output / "draft_headers.tsv"
    if old.exists():
        old.unlink()
    draft_headers(args, index, files, (date, revision))
    stand_ins(args, files, (date, revision))
    if args.unwritten:
        unwritten(args, index, checked)
    if args.ranked:
        link_ranked(args, index, checked)
    if args.verdicts:
        per_file(args, index, files)

if __name__ == "__main__":
    main()
