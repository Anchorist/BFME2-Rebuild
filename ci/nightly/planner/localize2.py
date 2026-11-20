"""Vendored link planner module; see ci/nightly/PROVENANCE.md."""
import struct
from pathlib import Path

SCN_CODE = 0x20
SCN_COMDAT = 0x1000


def localize(src, dst, names, extern=()):
    b = bytearray(Path(src).read_bytes())
    names, extern = set(names), set(extern)
    machine, nsec, _, symptr, nsym, optsz, _ = struct.unpack_from("<HHIIIHH", b, 0)
    if machine == 0 and nsec == 0xFFFF:
        raise ValueError(f"{src}: bigobj/anon object not supported")
    chars = []
    off = 20 + optsz
    for _ in range(nsec):
        chars.append(struct.unpack_from("<I", b, off + 36)[0])
        off += 40
    strtab = symptr + nsym * 18
    code, data = [], []
    i = 0
    while i < nsym:
        e = symptr + i * 18
        n = bytes(b[e:e + 8])
        if n[:4] == b"\0\0\0\0":
            o = struct.unpack_from("<I", n, 4)[0]
            name = bytes(b[strtab + o:b.index(b"\0", strtab + o)])
        else:
            name = n.rstrip(b"\0")
        value, secnum, _typ, cls, naux = struct.unpack_from("<IhHBB", b, e + 8)
        nm = name.decode("latin-1")
        if cls == 2 and secnum > 0 and nm in names and chars[secnum - 1] & SCN_CODE:
            b[e + 16] = 3
            code.append(nm)
        elif cls == 2 and nm in extern and naux == 0 and (
                (secnum > 0 and not chars[secnum - 1] & (SCN_CODE | SCN_COMDAT)) or (secnum == 0 and value > 0)):
            struct.pack_into("<Ih", b, e + 8, 0, 0)
            data.append(nm)
        i += 1 + naux
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_bytes(bytes(b))
    return sorted(code), sorted(data)
