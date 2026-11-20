"""Vendored link planner module; see ci/nightly/PROVENANCE.md."""
import struct
from pathlib import Path


def _symname(b, e, strtab):
    n = bytes(b[e:e + 8])
    if n[:4] == b"\0\0\0\0":
        o = struct.unpack_from("<I", n, 4)[0]
        return bytes(b[strtab + o:b.index(b"\0", strtab + o)]).decode("latin-1")
    return n.rstrip(b"\0").decode("latin-1")


def pad(src, dst, section, old_size, new_size, anchor, anchor_offset, define):
    b = bytearray(Path(src).read_bytes())
    machine, nsec, _, symptr, nsym, optsz, _ = struct.unpack_from("<HHIIIHH", b, 0)
    if machine == 0 and nsec == 0xFFFF:
        raise ValueError(f"{src}: bigobj/anon object not supported")
    off, hit = 20 + optsz, []
    for i in range(nsec):
        if bytes(b[off:off + 8]).rstrip(b"\0").decode("latin-1") == section:
            hit.append((i + 1, off))
        off += 40
    if len(hit) != 1:
        raise ValueError(f"{src}: {len(hit)} sections named {section}")
    secnum, hdr = hit[0]
    size, rawptr = struct.unpack_from("<II", b, hdr + 16)
    if rawptr != 0 and new_size != old_size:
        raise ValueError(f"{src}: {section} has raw data (only uninitialised sections are grown)")
    if size != old_size:
        raise ValueError(f"{src}: {section} is {size:#x} bytes, expected {old_size:#x}")
    if not all(0 <= v < new_size for v in define.values()):
        raise ValueError(f"{src}: a defined offset lies outside the new size {new_size:#x}")
    struct.pack_into("<I", b, hdr + 16, new_size)
    strtab = symptr + nsym * 18
    have, aux_done, anchor_ok = set(), 0, False
    i = 0
    while i < nsym:
        e = symptr + i * 18
        val, sec, _typ, cls, naux = struct.unpack_from("<IhHBB", b, e + 8)
        nm = _symname(b, e, strtab)
        if sec == secnum and cls == 3 and naux == 1 and nm == section:
            if struct.unpack_from("<I", b, e + 18)[0] != old_size:
                raise ValueError(f"{src}: {section} section symbol length differs from the header")
            struct.pack_into("<I", b, e + 18, new_size)
            aux_done += 1
        if cls == 2 and sec > 0:
            have.add(nm)
            if nm == anchor and sec == secnum and val == anchor_offset:
                anchor_ok = True
        i += 1 + naux
    if aux_done != 1:
        raise ValueError(f"{src}: {aux_done} section symbols for {section}")
    if not anchor_ok:
        raise ValueError(f"{src}: anchor {anchor} is not at {section}+{anchor_offset:#x}")
    clash = sorted(set(define) & have)
    if clash:
        raise ValueError(f"{src}: already defines {clash}")
    strsize = struct.unpack_from("<I", b, strtab)[0]
    if strtab + strsize != len(b):
        raise ValueError(f"{src}: data after the string table")
    strings = bytearray(b[strtab + 4:strtab + strsize])
    recs = bytearray()
    for nm, v in sorted(define.items(), key=lambda kv: kv[1]):
        raw = nm.encode("latin-1")
        if len(raw) <= 8:
            name = raw.ljust(8, b"\0")
        else:
            name = struct.pack("<II", 0, 4 + len(strings))
            strings += raw + b"\0"
        recs += name + struct.pack("<IhHBB", v, secnum, 0, 2, 0)
    out = b[:strtab] + recs + struct.pack("<I", 4 + len(strings)) + strings
    struct.pack_into("<I", out, 12, nsym + len(define))
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_bytes(bytes(out))
    return sorted(define)


def define_at(src, dst, anchor, define_rel, min_room):
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    secs, syms = check(src)
    if anchor not in syms or syms[anchor][0] <= 0:
        raise ValueError(f"{src}: anchor {anchor} not defined")
    secn, val = syms[anchor]
    sname, ssize = secs[secn]
    if ssize - val < min_room:
        raise ValueError(f"{src}: {anchor} has {ssize - val:#x} bytes in {sname}, retail's object is {min_room:#x}")
    b = Path(src).read_bytes()
    _m, nsec, _, _sp, _ns, optsz, _ = struct.unpack_from("<HHIIIHH", b, 0)
    same = [i for i in range(1, nsec + 1) if secs[i][0] == sname]
    if len(same) != 1:
        raise ValueError(f"{src}: {len(same)} sections named {sname}")
    return pad(src, dst, sname, ssize, ssize, anchor, val, {n: val + o for n, o in define_rel.items()})


def check(path):
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    b = Path(path).read_bytes()
    _m, nsec, _, symptr, nsym, optsz, _ = struct.unpack_from("<HHIIIHH", b, 0)
    secs, off = {}, 20 + optsz
    for i in range(nsec):
        secs[i + 1] = (bytes(b[off:off + 8]).rstrip(b"\0").decode("latin-1"), struct.unpack_from("<I", b, off + 16)[0])
        off += 40
    strtab = symptr + nsym * 18
    syms, i = {}, 0
    while i < nsym:
        e = symptr + i * 18
        val, sec, _t, cls, naux = struct.unpack_from("<IhHBB", b, e + 8)
        if cls == 2:
            syms[_symname(b, e, strtab)] = (sec, val)
        i += 1 + naux
    return secs, syms
