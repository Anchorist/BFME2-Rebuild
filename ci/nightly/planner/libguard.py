"""Vendored link planner module; see ci/nightly/PROVENANCE.md."""
import collections, json, os, struct
from pathlib import Path

L = Path(os.environ["NIGHTLY_WORK"])
DEFAULT = L / "inputs/libguard.json"
SCN_CODE, SCN_COMDAT, SCN_WRITE = 0x20, 0x1000, 0x80000000


def config():
    f = os.environ.get("NIGHTLY_LIBGUARD_FILE", str(DEFAULT))
    if not f or not Path(f).exists():
        return None, f
    return json.loads(Path(f).read_text()), f


def sec_chars(path):
    b = Path(path).read_bytes()
    _m, nsec, _, _sp, _ns, optsz, _ = struct.unpack_from("<HHIIIHH", b, 0)
    off, out = 20 + optsz, {}
    for i in range(nsec):
        out[i + 1] = struct.unpack_from("<I", b, off + 36)[0]
        off += 40
    return out


def compute(main, rb, sub_objs, idx, in_rsp, replaced, obj_paths, extra_alt=(), base=None):
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    cfg, path = config()
    if cfg is None:
        return {}, {}, {}, {"plan_input": path or "(off)", "active": False}
    prefixes = tuple(cfg.get("prefixes") or [])
    shown = cfg.get("contract_shown") or {}
    lib = {tu: rel for tu, rel in sub_objs.items() if tu.startswith(prefixes)}
    ref_objs = [o for o in in_rsp if o not in replaced and o in main.objects]
    definers = collections.defaultdict(list)
    undef_by = collections.defaultdict(int)
    alt_to = collections.defaultdict(set)
    for o in ref_objs:
        s = main.objects[o]
        for n in s.get("defs", {}):
            definers[n].append(o)
        for n in s.get("undefs", []):
            undef_by[n] += 1
        for a_, b_ in s.get("alt", []):
            alt_to[b_].add(a_)
    for a_, b_ in extra_alt:
        alt_to[b_].add(a_)
    for tu, rel in sub_objs.items():
        if tu not in lib:
            for n in idx[rel].get("defs", {}):
                definers[n].append(rel)
    rb_local, rb_extern, exclude = {}, {}, {}
    rep = {"plan_input": path, "active": True, "prefixes": list(prefixes), "units": {}, "counts": collections.Counter()}
    for tu, rel in sorted(lib.items()):
        own = set()
        for r_ in rb.tu_rows.get(tu, []):
            own.add(r_["name"])
            own.update(r_.get("accepted_names") or [])
        chars = sec_chars(obj_paths[tu])
        loc, ext, wc, caught, sole = [], [], [], [], []
        for n, d in idx[rel].get("defs", {}).items():
            if n in own or n in shown:
                continue
            reach = "alt" if alt_to.get(n) else ("direct" if undef_by.get(n) else "none")
            others = definers.get(n, [])
            ch = chars.get(d[4], 0)
            if not others:
                if reach == "alt":
                    sole.append(n)
                continue
            if ch & SCN_CODE or not ch & SCN_WRITE:
                how = "local"
            elif not d[0]:
                how = "extern"
            else:
                how = "writable-comdat"
            caught.append({"name": n, "how": how, "reach": reach, "kind": d[1], "comdat": bool(d[0]),
                           "other_definers": len(others), "other_sample": others[0]})
            rep["counts"][f"{how}:{reach}"] += 1
            (loc if how == "local" else ext if how == "extern" else wc).append(n)
        for n in sole:
            rep["counts"]["sole-provider:alt"] += 1
        why = []
        if sole:
            why.append(f"sole provider of {len(sole)} name(s) reference code reaches by alternate name")
        if wc:
            why.append(f"{len(wc)} writable COMDAT data also defined elsewhere")
        if why:
            exclude[tu] = "library-guard: " + "; ".join(why)
        if loc:
            rb_local[rel] = sorted(loc)
        if ext:
            rb_extern[rel] = sorted(ext)
        rep["units"][tu] = {"local": len(loc), "extern": len(ext), "excluded": exclude.get(tu),
                            "sole_alt": sorted(sole), "writable_comdat": sorted(wc), "caught": caught}


    rep["address_guard"] = []
    if cfg.get("address_guard"):
        ref_code = collections.defaultdict(list)
        for o in ref_objs:
            for n, d in main.objects[o].get("defs", {}).items():
                if d[1] == "code":
                    ref_code[n].append(o)
        for tu, rel in sorted(sub_objs.items()):
            if tu in lib:
                continue
            own = {r_["name"] for r_ in rb.tu_rows.get(tu, [])}
            own |= {n for r_ in rb.tu_rows.get(tu, []) for n in (r_.get("accepted_names") or [])}
            add = []
            for n, d in idx[rel].get("defs", {}).items():
                if not d[0] or d[1] != "code" or n in own or n not in ref_code:
                    continue
                rbr = sorted({x["_rva"] for x in rb.name_rows.get(n, [])})
                bsr = sorted(main.name_rva.get(n, set()))
                if rbr and bsr and rbr != bsr:
                    add.append(n)
                    rep["address_guard"].append({"tu": tu, "name": n, "rebuild_rva": [hex(x) for x in rbr],
                                                 "reference_rva": [hex(x) for x in bsr], "reference_definer": ref_code[n][0]})
            if add:
                rb_local[rel] = sorted(set(rb_local.get(rel, [])) | set(add))
        rep["counts"]["address-guard:local"] = len(rep["address_guard"])


    rep["content_guard"] = []
    if cfg.get("content_guard") and base is not None:
        first_ref = {}
        for o in ref_objs:
            for n, d in main.objects[o].get("defs", {}).items():
                if d[1] == "code":
                    first_ref.setdefault(n, o)
        cache = {}
        for tu, rel in sorted(sub_objs.items()):
            if tu in lib:
                continue
            own = {r_["name"] for r_ in rb.tu_rows.get(tu, [])}
            own |= {n for r_ in rb.tu_rows.get(tu, []) for n in (r_.get("accepted_names") or [])}
            cand = [n for n, d in idx[rel].get("defs", {}).items()
                    if d[0] and d[1] == "code" and n not in own and n in first_ref and n not in set(rb_local.get(rel, []))]
            if not cand:
                continue
            mine = code_sections(obj_paths[tu])
            add = []
            for n in cand:
                bo = first_ref[n]
                if bo not in cache:
                    cache[bo] = code_sections(Path(base) / bo)
                if n not in mine or n not in cache[bo]:
                    continue
                (x, mx), (y, my) = mine[n], cache[bo][n]
                if len(x) != len(y):
                    why = f"size {len(x)} vs reference {len(y)}"
                else:
                    dk = next((k for k in range(len(x)) if x[k] != y[k] and k not in mx and k not in my), None)
                    if dk is None:
                        continue
                    why = f"bytes differ at +{dk:#x}"
                add.append(n)
                rep["content_guard"].append({"tu": tu, "name": n, "why": why, "reference_definer": bo})
            if add:
                rb_local[rel] = sorted(set(rb_local.get(rel, [])) | set(add))
        rep["counts"]["content-guard:local"] = len(rep["content_guard"])
    rep["counts"] = dict(rep["counts"])
    return rb_local, rb_extern, exclude, rep


def code_sections(path):
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    b = Path(path).read_bytes()
    _m, nsec, _, symptr, nsym, optsz, _ = struct.unpack_from("<HHIIIHH", b, 0)
    secs, off = [], 20 + optsz
    for _ in range(nsec):
        _vs, _va, rawsz, rawptr, relptr, _lp, nrel, _nl, ch = struct.unpack_from("<IIIIIIHHI", b, off + 8)
        mask = set()
        for k in range(nrel):
            ro = struct.unpack_from("<I", b, relptr + 10 * k)[0]
            mask.update(range(ro, ro + 4))
        secs.append((b[rawptr:rawptr + rawsz] if rawptr else b"", mask, ch))
        off += 40
    strtab = symptr + nsym * 18
    out, i = {}, 0
    while i < nsym:
        e = symptr + 18 * i
        n = b[e:e + 8]
        if n[:4] == b"\0\0\0\0":
            o = struct.unpack_from("<I", n, 4)[0]
            name = b[strtab + o:b.index(b"\0", strtab + o)]
        else:
            name = n.rstrip(b"\0")
        val, sn, _t, cls, naux = struct.unpack_from("<IhHBB", b, e + 8)
        if cls == 2 and sn > 0 and val == 0 and secs[sn - 1][2] & SCN_CODE:
            out[name.decode("latin-1")] = secs[sn - 1][:2]
        i += 1 + naux
    return out


def static_any(src, dst, names):
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    b = bytearray(Path(src).read_bytes())
    names = set(names)
    _m, nsec, _, symptr, nsym, optsz, _ = struct.unpack_from("<HHIIIHH", b, 0)
    strtab = symptr + nsym * 18
    done, i = [], 0
    while i < nsym:
        e = symptr + i * 18
        n = bytes(b[e:e + 8])
        if n[:4] == b"\0\0\0\0":
            o = struct.unpack_from("<I", n, 4)[0]
            name = bytes(b[strtab + o:b.index(b"\0", strtab + o)])
        else:
            name = n.rstrip(b"\0")
        _v, secnum, _t, cls, naux = struct.unpack_from("<IhHBB", b, e + 8)
        nm = name.decode("latin-1")
        if cls == 2 and secnum > 0 and nm in names:
            b[e + 16] = 3
            done.append(nm)
        i += 1 + naux
    Path(dst).write_bytes(bytes(b))
    return sorted(done)
