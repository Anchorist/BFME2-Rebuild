
"""Vendored link planner module; see ci/nightly/PROVENANCE.md."""
import argparse, collections, csv, json, re, struct, sys, time
from pathlib import Path

import os; HOME = Path.home(); L = Path(os.environ["NIGHTLY_WORK"])
sys.path.insert(0, str(L))

SCN_CODE, SCN_IDATA, SCN_UDATA, SCN_COMDAT, SCN_OVFL = 0x20, 0x40, 0x80, 0x1000, 0x01000000


def parse(path):
    b = Path(path).read_bytes()
    if len(b) < 20:
        return None
    machine, nsec, _, symptr, nsym, optsz, _ = struct.unpack_from("<HHIIIHH", b, 0)
    if machine != 0x14C:
        return None
    secs, off = [], 20 + optsz
    for i in range(nsec):
        nm = b[off:off + 8].rstrip(b"\0").decode("latin-1")
        size, raw, rel = struct.unpack_from("<III", b, off + 16)
        nrel = struct.unpack_from("<H", b, off + 32)[0]
        ch = struct.unpack_from("<I", b, off + 36)[0]
        secs.append([nm, size, raw, rel, nrel, ch])
        off += 40
    strtab = symptr + nsym * 18
    syms, i = {}, 0
    while i < nsym:
        e = symptr + i * 18
        n = b[e:e + 8]
        if n[:4] == b"\0\0\0\0":
            o = struct.unpack_from("<I", n, 4)[0]
            name = b[strtab + o:b.index(b"\0", strtab + o)].decode("latin-1")
        else:
            name = n.rstrip(b"\0").decode("latin-1")
        val, sec, typ, cls, naux = struct.unpack_from("<IhHBB", b, e + 8)
        syms[i] = (name, val, sec, cls, naux, typ)
        i += 1 + naux
    return b, secs, syms


def is_data_sec(ch):
    return not ch & SCN_CODE and ch & (SCN_IDATA | SCN_UDATA)


TYPE_RE = re.compile(r"@@3([UV][A-Za-z0-9_]+@@)A$")


def source_sizes(objdir, rva_of):
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    by_rva, by_type = {}, {}
    for o in sorted(Path(objdir).glob("*.obj")):
        try:
            p = parse(o)
        except Exception:
            continue
        if not p:
            continue
        _b, secs, syms = p
        persec = collections.defaultdict(list)
        for name, val, sec, cls, naux, typ in syms.values():
            if 0 < sec <= len(secs) and is_data_sec(secs[sec - 1][5]) and cls in (2, 3) and typ >> 4 != 2 \
                    and not (cls == 3 and naux == 1 and val == 0 and name == secs[sec - 1][0]):
                persec[sec].append((val, name, cls))
        for sec, lst in persec.items():
            lst.sort()
            for i, (val, name, cls) in enumerate(lst):
                if cls != 2:
                    continue
                nxt = next((v for v, _n, _c in lst[i + 1:] if v > val), secs[sec - 1][1])
                room = nxt - val
                ra = rva_of.get(name)
                if ra is not None:
                    by_rva[ra] = max(by_rva.get(ra, (0, ""))[0], room), f"{o.name}:{name}"
                m = TYPE_RE.search(name)
                if m and room > by_type.get(m.group(1), (0, ""))[0]:
                    by_type[m.group(1)] = (room, f"{o.name}:{name}")
    return by_rva, by_type


def analyse(objs, rva_of, ledger, src=None):
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    defs = {}
    layout = {}
    reach = collections.defaultdict(list)
    deficit = {}
    contrib, secname_of = collections.defaultdict(list), {}
    t0 = time.time()
    for n_, (label, path) in enumerate(objs):
        try:
            p = parse(path)
        except Exception as e:
            print("parse failed", path, e, file=sys.stderr)
            continue
        if not p:
            continue
        b, secs, syms = p
        persec = collections.defaultdict(list)
        for idx_, (name, val, sec, cls, naux, typ) in syms.items():
            if sec <= 0 or sec > len(secs):
                if cls == 2 and sec == 0 and val > 0:
                    defs.setdefault(name, (label, val, 0, None))
                continue
            ch = secs[sec - 1][5]
            if not is_data_sec(ch):
                continue
            if cls == 3 and naux == 1 and val == 0 and name == secs[sec - 1][0]:
                continue
            if cls in (2, 3) and typ >> 4 != 2:
                persec[sec].append((val, name))
                if cls == 2:
                    defs.setdefault(name, (label, secs[sec - 1][1], val, (label, sec)))
        for sec, lst in persec.items():
            layout[(label, sec)] = sorted(lst)
        for sn, (nm, size, raw, rel, nrel, ch) in enumerate(secs, 1):
            if is_data_sec(ch) and size:
                g = nm.split("$")[0]
                secname_of[(label, sn)] = g
                bn = Path(label).name
                if contrib[g] and contrib[g][-1][0] == bn:
                    contrib[g][-1][1] += size
                else:
                    contrib[g].append([bn, size])
        for sn, (nm, size, raw, rel, nrel, ch) in enumerate(secs, 1):
            if not nrel or not rel or ch & SCN_UDATA and not raw:
                continue
            if ch & SCN_OVFL:
                nrel = struct.unpack_from("<I", b, rel)[0]
                rel += 10
                nrel -= 1
            for va, si, ty in struct.iter_unpack("<IIH", b[rel:rel + 10 * nrel]):
                if ty not in (6, 0x14) or si not in syms:
                    continue
                tname, tval, tsec, tcls, _, ttyp = syms[si]
                if ttyp >> 4 == 2 or not raw:
                    continue
                k = struct.unpack_from("<i", b, raw + va)[0]
                if tcls == 3 and tsec > 0:
                    continue
                if k > 0:
                    reach[tname].append((k, label))
        if n_ % 3000 == 0:
            print(f"  {n_}/{len(objs)} objects, {time.time() - t0:.0f} s", file=sys.stderr, flush=True)
    findings = {}
    for name, (label, secsize, val, key) in defs.items():
        ra = rva_of.get(name)
        if ra is None or key is None or name.startswith("??_C@"):
            continue
        lst = layout.get(key, [])
        led = ledger.get(name)

        room = secsize - val
        for v2, n2 in lst:
            if v2 <= val or n2 == name:
                continue
            r2 = rva_of.get(n2)
            if r2 is not None and r2 > ra and r2 - ra == v2 - val:
                continue
            room = v2 - val
            break
        if led and room < led:
            deficit[(name, "SHORT")] = led - room
            findings[(name, "SHORT")] = (ra, name, label, room, led, "SHORT", f"room {room:#x} < ledger {led:#x}")
        if src:
            s_rva, s_type = src
            sr = s_rva.get(ra)
            if sr and room < sr[0] and secsize - val < sr[0] and (room + 3) & ~3 < sr[0]:
                kd = "SHORT-VTABLE" if name.startswith("??_7") else "SHORT-SRC"
                deficit[(name, kd)] = sr[0] - room
                findings[(name, kd)] = (ra, name, label, room, led, kd,
                                                 f"room {room:#x} (section left {secsize - val:#x}) < source {sr[0]:#x} {sr[1]}")
            m = TYPE_RE.search(name)
            st = s_type.get(m.group(1)) if m else None
            if st and secsize - val < st[0] and room < st[0]:
                deficit[(name, "SHORT-TYPE")] = st[0] - room
                findings[(name, "SHORT-TYPE")] = (ra, name, label, room, led, "SHORT-TYPE",
                                                  f"room {room:#x} < sizeof per source {st[0]:#x} {st[1]}")
        ks = reach.get(name)
        if ks:
            kmax, who = max(ks)
            if val + kmax == secsize:
                findings[(name, "END")] = (ra, name, label, room, led, "END",
                                           f"reach +{kmax:#x} from {who} = one past the end (bound pointer or overrun)")
            elif val + kmax > secsize:
                deficit[(name, "OUTSIDE")] = val + kmax + 4 - secsize
                findings[(name, "OUTSIDE")] = (ra, name, label, room, led, "OUTSIDE",
                                               f"reach +{kmax:#x} from {who} past section end (+{secsize - val:#x})")
            else:
                bad = None
                for k, who in sorted(set(ks)):
                    pos = val + k
                    if pos >= secsize:
                        continue
                    cover = [(v2, n2) for v2, n2 in lst if v2 <= pos]
                    if not cover:
                        continue
                    v2, n2 = cover[-1]
                    r2 = rva_of.get(n2)
                    if n2 != name and r2 is not None and r2 + (pos - v2) != ra + k:
                        bad = (k, who, n2, r2)
                        break
                if bad:
                    findings[(name, "MISPLACED")] = (ra, name, label, room, led, "MISPLACED",
                                                     f"+{bad[0]:#x} from {bad[1]} lands on {bad[2]} (retail {bad[3]:#x})")
    pos = {}
    for g, lst in contrib.items():
        for i, (bn, _sz) in enumerate(lst):
            pos.setdefault((bn, g), i)
    for k, f in list(findings.items()):
        key = defs[k[0]][3]
        g = secname_of.get(key, "?")
        i = pos.get((Path(f[2]).name, g))
        need = max(4, deficit.get(k, 4))
        win, acc = [], 0
        if i is not None:
            for bn, sz in contrib[g][i + 1:]:
                win.append(f"{bn}:{sz:#x}")
                acc += sz
                if acc >= need:
                    break
        findings[k] = f + (g, " ".join(win) or None)
    return defs, findings


def rsp_objects(tier, base):
    out = []
    for line in (tier / "hybrid.rsp").read_text().splitlines():
        if not line.startswith('"'):
            continue
        p = line.strip('"')
        if p.startswith("Z:"):
            p = p[2:].replace("\\", "/")
        else:
            p = str(base / p)
        if p.endswith(".obj"):
            lab = p.split(str(L) + "/", 1)[-1]
            if "/base/" in lab:
                lab = lab.split("/", 2)[-1]
            out.append((Path(p).name if "/rebuilt/" in p else lab, p))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tier"); ap.add_argument("sha")
    ap.add_argument("--base", default="56174094dd"); ap.add_argument("--out"); ap.add_argument("--json")
    ap.add_argument("--no-baseline", action="store_true")
    ap.add_argument("--src-objs", help="compiled objects of all TUs (default work/<sha>/tree/obj)")
    a = ap.parse_args()
    import hybrid
    tier, base = Path(a.tier).resolve(), L / "base" / a.base
    hybrid.BASE = base
    main_ = hybrid.Main(base)
    rb = hybrid.Rebuild(hybrid.git("rev-parse", a.sha))
    rva_of, ledger = {}, {}
    for n, rs in main_.name_rva.items():
        if len(rs) == 1:
            rva_of[n] = next(iter(rs))
    for n, r in rb.sym_rva.items():
        rva_of.setdefault(n, r)
    for src in (base / "reverse/data_rows.csv", rb.tree / "reverse/data_rows.csv"):
        if src.exists():
            with open(src, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    try:
                        ledger[r["name"]] = int(r["size"])
                        a_ = int(r["address"], 16) - (0x400000 if r["address_kind"] == "va" else 0)
                        rva_of[r["name"]] = a_
                    except (ValueError, KeyError):
                        pass
    objs = rsp_objects(tier, base)
    src = source_sizes(a.src_objs or rb.tree / "obj", rva_of)
    print(f"plan: {len(objs)} objects; source sizes for {len(src[0])} addresses, {len(src[1])} class types",
          file=sys.stderr)
    _d, plan_f = analyse(objs, rva_of, ledger, src)
    base_f = {}
    if not a.no_baseline:
        bobjs = [(p_, str(base / p_)) for p_ in main_.order if p_.endswith(".obj")]
        print(f"base alone: {len(bobjs)} objects", file=sys.stderr)
        _b, base_f = analyse(bobjs, rva_of, ledger, src)
    rows = []


    BLOCK = {"OUTSIDE", "SHORT", "SHORT-SRC", "SHORT-TYPE"}
    for key, f in sorted(plan_f.items(), key=lambda kv: kv[1][0]):
        ra, name, label, room, led, kind, det, g, nxt = f
        bf = base_f.get(key)
        state = "inherited" if bf else "new"
        moved = bf is not None and bf[8] != nxt
        blocking = (state == "new" and kind != "END") or (kind in BLOCK and moved)
        rows.append([f"{ra + 0x400000:#010x}", name, label, f"{room:#x}", f"{led:#x}" if led else "",
                     kind, det, state, f"{g} tail={nxt}" + (f" (base tail: {bf[8]})" if moved else ""),
                     "BLOCKING" if blocking else ""])
    fixed = [list(f[:2]) + [f[5]] for k, f in base_f.items() if k not in plan_f]
    hdr = ["retail_va", "name", "owner_object", "size_in_object", "retail_extent_ledger", "finding", "detail", "plan_vs_base",
           "section_neighbour", "verdict"]
    out = Path(a.out) if a.out else tier / "extents.tsv"
    with open(out, "w") as f:
        f.write(f"# extents check {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} plan {tier} commit {a.sha}"
                f" base {a.base}; {len(objs)} objects; findings {len(rows)} "
                f"({collections.Counter(r[5] for r in rows)}); new {sum(r[7] == 'new' for r in rows)}; "
                f"base-only findings the plan removes {len(fixed)}; BLOCKING {sum(r[9] == 'BLOCKING' for r in rows)}\n")
        f.write("\t".join(hdr) + "\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    summ = {"objects": len(objs), "findings": len(rows), "by_kind": dict(collections.Counter(r[5] for r in rows)),
            "new": sum(r[7] == "new" for r in rows), "blocking": sum(r[9] == "BLOCKING" for r in rows),
            "blocking_rows": [r[:2] + [r[5], r[8]] for r in rows if r[9] == "BLOCKING"][:60],
            "new_by_kind": dict(collections.Counter(r[5] for r in rows if r[7] == "new")),
            "base_findings": len(base_f), "removed_by_plan": fixed[:50]}
    if a.json:
        Path(a.json).write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ)[:2000])


if __name__ == "__main__":
    main()
