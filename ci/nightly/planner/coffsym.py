"""Vendored link planner module; see ci/nightly/PROVENANCE.md."""
import re
import struct
from pathlib import Path

SCN_CODE = 0x20
SCN_INIT = 0x40
SCN_UNINIT = 0x80
SCN_COMDAT = 0x1000


def obj_symbols(path):
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    b = Path(path).read_bytes()
    out = {"defs": {}, "undefs": [], "weak": {}, "refs": {}, "secs": {}, "alt": [], "include": []}
    if len(b) < 20:
        return out
    machine, nsec = struct.unpack_from("<HH", b, 0)
    if machine == 0 and nsec == 0xFFFF:
        return out
    _, _, _, symptr, nsym, optsz, _ = struct.unpack_from("<HHIIIHH", b, 0)
    secs = []
    off = 20 + optsz
    strtab = symptr + nsym * 18
    drectve = ""
    for _ in range(nsec):
        name = b[off:off + 8].rstrip(b"\0")
        if name.startswith(b"/"):
            try:
                o = int(name[1:])
                name = b[strtab + o:b.index(b"\0", strtab + o)]
            except ValueError:
                pass
        vsize, va, rawsz, rawptr, relptr, lnptr, nrel, nln, chars = struct.unpack_from("<IIIIIIHHI", b, off + 8)
        secs.append((name.decode("latin-1"), rawsz, chars, relptr, nrel))
        if name == b".drectve" and rawptr:
            drectve += b[rawptr:rawptr + rawsz].decode("latin-1", "replace") + " "
        off += 40
    syms = []
    i = 0
    while i < nsym:
        e = symptr + i * 18
        n = b[e:e + 8]
        if n[:4] == b"\0\0\0\0":
            o = struct.unpack_from("<I", n, 4)[0]
            name = b[strtab + o:b.index(b"\0", strtab + o)]
        else:
            name = n.rstrip(b"\0")
        value, secnum, typ, cls, naux = struct.unpack_from("<IhHBB", b, e + 8)
        name = name.decode("latin-1")
        syms.append((name, secnum, cls))
        for _ in range(naux):
            syms.append(None)
        if cls == 3 and naux and secnum > 0 and value == 0:
            ln, nr, nl, ck, number, sel = struct.unpack_from("<IHHIHB", b, e + 18)
            chars = secs[secnum - 1][2]
            if chars & SCN_COMDAT:
                out["secs"][secnum] = [True, sel, number if sel == 5 else 0, None]
        elif cls == 2:
            if secnum > 0:
                sname, rawsz, chars, _, _ = secs[secnum - 1]
                kind = "code" if chars & SCN_CODE else ("bss" if chars & SCN_UNINIT else "data")
                out["defs"][name] = [bool(chars & SCN_COMDAT), kind, rawsz, sname, secnum]
                s = out["secs"].get(secnum)
                if s and s[3] is None:
                    s[3] = name
            elif secnum == 0 and value > 0:
                out["defs"].setdefault(name, [True, "common", value, "", 0])
            elif secnum == 0:
                out["undefs"].append(name)
            elif secnum == -1:
                out["defs"][name] = [False, "abs", 0, "", 0]
        elif cls == 3 and secnum > 0 and naux == 0:
            s = out["secs"].get(secnum)
            if s and s[3] is None:
                s[3] = name
        elif cls == 105 and naux:
            tag = struct.unpack_from("<I", b, e + 18)[0]
            out["weak"][name] = tag
        i += 1 + naux
    for w, tag in list(out["weak"].items()):
        out["weak"][w] = syms[tag][0] if tag < len(syms) and syms[tag] else ""
    undef = set(out["undefs"]) - set(out["defs"])
    out["undefs"] = sorted(undef)
    refs = {}
    for idx, (sname, rawsz, chars, relptr, nrel) in enumerate(secs, 1):
        for k in range(nrel):
            va, si, ty = struct.unpack_from("<IIH", b, relptr + k * 10)
            if si < len(syms) and syms[si]:
                nm = syms[si][0]
                if nm in undef or nm in out["weak"]:
                    refs.setdefault(nm, set()).add(idx)
    out["refs"] = {k: sorted(v) for k, v in refs.items()}
    out["alt"] = re.findall(r'/alternatename:"?([^\s="]+)=([^\s"]+)', drectve, re.I)
    out["include"] = re.findall(r'/include:"?([^\s"]+)', drectve, re.I)
    return out


def archive_symbols(path):
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    b = Path(path).read_bytes()
    if not b.startswith(b"!<arch>\n"):
        return set()
    off = 8
    hdr = b[off:off + 60]
    size = int(hdr[48:58].decode().strip())
    body = b[off + 60:off + 60 + size]
    n = struct.unpack_from(">I", body, 0)[0]
    strings = body[4 + 4 * n:]
    return {s.decode("latin-1") for s in strings.split(b"\0")[:n]}
