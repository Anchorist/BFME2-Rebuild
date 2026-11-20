"""Vendored link planner module; see ci/nightly/PROVENANCE.md."""
import collections


def def_names(path):
    need = []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line or line.upper().startswith(("EXPORTS", "LIBRARY", ";", "NAME")):
            continue
        tok = line.split()[0]
        need.append(tok.split("=", 1)[1] if "=" in tok else tok)
    return need


def resolve(order, objects, extra_needed=()):
    strong = collections.defaultdict(list)
    comdat = collections.defaultdict(list)
    libdefs = {}
    for p in order:
        s = objects.get(p)
        if s is None:
            continue
        if s.get("lib"):
            for n in s["defs"]:
                libdefs.setdefault(n, p)
            continue
        secs = s.get("secs", {})
        for n, d in s["defs"].items():
            nodup = d[0] and len(d) > 4 and (secs.get(d[4]) or [0, 0])[1] == 1
            (comdat if d[0] and not nodup else strong)[n].append(p)
    winner = {n: ps[0] for n, ps in comdat.items()}
    winner.update({n: ps[0] for n, ps in strong.items()})
    defined = set(strong) | set(comdat) | set(libdefs)
    alt = collections.defaultdict(list)
    for p in order:
        s = objects.get(p)
        if s and not s.get("lib"):
            for a, b in s.get("alt", []):
                alt[a].append(b)

    def is_def(n, depth=0):
        if n in defined:
            return True
        return depth < 8 and any(is_def(b, depth + 1) for b in alt.get(n, ()))

    def live(p, s, sec, depth=0):
        info = s.get("secs", {}).get(sec)
        if not info:
            return True
        _, sel, assoc, leader = info
        if sel == 5 and assoc and depth < 4:
            return live(p, s, assoc, depth + 1)
        if leader is None or leader not in winner:
            return True
        return winner[leader] == p

    dups = {}
    for n, ps in strong.items():
        if len(ps) > 1:
            dups[n] = ps
        elif n in comdat:
            dups[n] = ps + comdat[n]
    unresolved = collections.defaultdict(list)
    for p in order:
        s = objects.get(p)
        if s is None or s.get("lib"):
            continue
        refs = s.get("refs", {})
        for n in s["undefs"]:
            if is_def(n):
                continue


            unresolved[n].append(p)
        for w, a in s.get("weak", {}).items():
            if not is_def(w) and a and not is_def(a):
                unresolved[w].append(p)
        for n in s.get("include", []):
            if not is_def(n):
                unresolved[n].append(p)
    for n in extra_needed:
        if not is_def(n):
            unresolved[n].append("<exports>")
    return {"unresolved": dict(unresolved), "duplicates": dups, "winner": winner, "libdefs": libdefs,
            "strong": strong, "comdat": comdat}
