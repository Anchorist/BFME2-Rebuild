
"""Vendored link planner module; see ci/nightly/PROVENANCE.md."""
import argparse, collections, csv, hashlib, json, os, pickle, re, shutil, subprocess, sys, time
import concurrent.futures
from pathlib import Path

HOME = Path.home()
L = Path(os.environ["NIGHTLY_WORK"])
BARE = Path(os.environ["NIGHTLY_GIT_DIR"])
GENBIN = L / "judge-unavailable"
BASE = L / "base/a4df5d39b2"
RETAIL = Path(os.environ["NIGHTLY_BASELINE"])
VC = Path(os.environ["NIGHTLY_VC_ROOT"])
sys.path.insert(0, str(L))
import coffsym, resolve

LINKER_KNOWN = {"___ImageBase"}
IMPORT_ROOTS = ["__imp__GetVersion@0", "__imp__GetVersionExA@4", "__imp__SHGetSpecialFolderPathW@16"]
PLACEHOLDER = re.compile(r"[Rr]va[0-9A-Fa-f]{6,8}|Bfme|^\$L\d+$|^uw_|Gen_t_|_0x[0-9A-Fa-f]{6}")


def log(*a):
    msg = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(msg, flush=True)


def git(*a):
    return subprocess.run(["git", "--git-dir", str(BARE), *a], capture_output=True, text=True, check=True).stdout.strip()


def obj_path_main(source, member=None):
    stem = "_".join(Path(source).with_suffix("").parts)
    if member:
        stem += "_" + re.split(r"[\\/]", member)[-1].removesuffix(".obj")
    return "build/match/" + "".join(("^" + c.lower()) if c.isupper() else c for c in stem) + ".obj"


class Main:
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    def __init__(self, base=None):
        base = base or BASE
        self.rva_objs = collections.defaultdict(set)
        self.obj_rvas = collections.defaultdict(set)
        self.obj_rows = collections.defaultdict(list)
        self.name_rva = collections.defaultdict(set)
        self.rva_names = collections.defaultdict(set)
        with open(base / "reverse/functions.csv", newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                src = r["source"]
                if not src or not r["target_rva"]:
                    continue
                member = None
                if src.lower().endswith(".lib"):
                    m = re.search(r"(?:^|;)member=([^;]+)", r.get("notes") or "")
                    member = m.group(1) if m else None
                o = obj_path_main(src, member)
                rva = int(r["target_rva"], 16)
                self.rva_objs[rva].add(o)
                self.obj_rvas[o].add(rva)
                self.obj_rows[o].append((rva, r["name"], r["status"]))
                self.name_rva[r["name"]].add(rva)
                self.rva_names[rva].add(r["name"])
        self.obj_data = collections.defaultdict(list)
        with open(base / "reverse/data_rows.csv", newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if not r["source"]:
                    continue
                a = int(r["address"], 16)
                if r["address_kind"] == "va":
                    a -= 0x400000
                self.obj_data[obj_path_main(r["source"])].append((a, r["name"], r["section"]))
                self.name_rva[r["name"]].add(a)
                self.rva_names[a].add(r["name"])
        idx = pickle.loads((base / "index.pkl").read_bytes())
        idx["objects"].pop("build/exit_link/retail.def", None)
        self.order = [p for p in idx["order"] if p != "build/exit_link/retail.def"]
        self.objects = idx["objects"]
        self.needed = resolve.def_names(base / "build/exit_link/retail.def") + IMPORT_ROOTS


class Rebuild:
    def __init__(self, sha):
        self.sha = sha
        self.work = L / "work" / sha[:12]
        self.work.mkdir(parents=True, exist_ok=True)
        self.tree = self.work / "tree"
        if not (self.tree / "config/map.json").exists():
            tmp = self.work / ".tree"
            shutil.rmtree(tmp, ignore_errors=True)
            tmp.mkdir()
            a = subprocess.Popen(["git", "--git-dir", str(BARE), "archive", sha], stdout=subprocess.PIPE)
            subprocess.run(["tar", "-x", "-C", str(tmp)], stdin=a.stdout, check=True)
            a.wait()
            tmp.rename(self.tree)
        m = json.loads((self.tree / "config/map.json").read_text())
        self.objects = {o["object_id"]: o for o in m["objects"]}
        self.tu_rows = collections.defaultdict(list)
        self.name_rows = collections.defaultdict(list)
        self.rva_rows = collections.defaultdict(list)
        for r in m["rows"]:
            o = self.objects.get(r["object"])
            tu = (o or {}).get("tu")
            r["_tu"] = tu
            r["_rva"] = int(r["rva"], 16)
            if tu:
                self.tu_rows[tu].append(r)
            self.rva_rows[r["_rva"]].append(r)
            for n in set([r["name"]] + list(r.get("accepted_names") or [])):
                self.name_rows[n].append(r)
        s = json.loads((self.tree / "config/symbols.json").read_text())
        self.sym_rva = {}
        for n, v in s["symbols"].items():
            c = v.get("candidates") or []
            if c:
                self.sym_rva[n] = int(c[0]["rva"], 16)
        for n, v in s["vtables"].items():
            if v:
                self.sym_rva.setdefault(n, int(v[0]["rva"], 16))
        self.data_items = s["data_items"]

    def files(self):
        out = subprocess.run(["git", "--git-dir", str(BARE), "ls-tree", "-r", "--name-only", self.sha, "src"],
                             capture_output=True, text=True, check=True).stdout.split()
        return [p for p in out if p.endswith((".cpp", ".c"))]


def judge_all(sha, work):
    out = work / "judge_all.json"
    if (not out.exists() or out.stat().st_size == 0) and os.environ.get("NIGHTLY_JUDGE") != "local":

        files = subprocess.run(["git", "--git-dir", str(BARE), "ls-tree", "-r", "--name-only", sha, "src"],
                               capture_output=True, text=True, check=True).stdout.split()
        files = [p for p in files if p.endswith((".cpp", ".c"))]
        jobs = work / "batch_jobs.jsonl"
        jobs.write_text(json.dumps({"id": "nightly-" + sha[:10], "commit": sha, "files": files}) + "\n")
        for attempt in range(4):
            log("farm batch judge", sha[:12], "attempt", attempt + 1)
            rc = subprocess.run(["nice", "-n", "15", sys.executable, str(L / "farm-unavailable/farm.py"), "batch", str(jobs),
                                 "--out", str(work / "batch"), "--max-files", "8"],
                                stdout=open(work / "batch.log", "a"), stderr=subprocess.STDOUT).returncode
            if rc == 0:
                break
        res = [json.loads(l) for l in (work / "batch/results.jsonl").read_text().splitlines() if l.strip()] \
            if (work / "batch/results.jsonl").exists() else []
        if len(res) == len(files) and all("tu" in r for r in res):
            out.write_text(json.dumps({"summary": {"sha": sha, "via": "farm batch"}, "results": res}))
    if not out.exists() or out.stat().st_size == 0:
        log("judge --all", sha[:12])
        with open(out.with_suffix(".tmp"), "w") as f, open(work / "judge_all.err", "w") as e:
            subprocess.run(["nice", "-n", "15", sys.executable, str(GENBIN / "judge.py"), sha, "--all", "--json"],
                           stdout=f, stderr=e, check=False)
        out.with_suffix(".tmp").rename(out)
    return json.loads(out.read_text())


def tiers(sha, work):
    p = work / "tiers.json"
    if p.exists():
        return json.loads(p.read_text())
    j = judge_all(sha, work)
    res = j["results"] if isinstance(j, dict) else j
    t = {"verified": [], "matching": [], "compiles": [], "compile_error": [], "per_file": {}}
    for r in res:
        tu = r["tu"]
        st = {"functions": r.get("functions", 0), "function_match": r.get("function_match", 0),
              "object_verified": bool(r.get("object_verified")), "statuses": {}}
        for row in r.get("rows", []):
            st["statuses"][row["rva"]] = row.get("status")
        t["per_file"][tu] = st
        if r.get("compile_error") or any(g for g in r.get("gates", []) if "COMPILE" in str(g).upper()):
            t["compile_error"].append(tu)
        else:
            t["compiles"].append(tu)
        if st["object_verified"]:
            t["verified"].append(tu)
        if st["functions"] and st["function_match"] == st["functions"]:
            t["matching"].append(tu)
    p.write_text(json.dumps(t))
    return t


def _compile_one(args):
    job, tu = args
    sys.path.insert(0, str(GENBIN))
    sys.path.insert(0, str(GENBIN.parent))
    os.chdir(job)
    import judge
    try:
        obj, err, _ = judge.compile_tu(Path(job), tu)
    except Exception as e:
        return tu, None, repr(e)
    return tu, (str(obj) if obj else None), err


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _reuse(tree, prev_trees, tu, obj):
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    name = tu.replace("/", "_") + ".obj"
    for prev in prev_trees:
        po = prev / "obj" / name
        rec = po.with_suffix(".obj.compile.json")
        if not (po.exists() and rec.exists()):
            continue
        try:
            r = json.loads(rec.read_text())
            if not (tree / tu).exists() or _sha(tree / tu) != r["source_sha256"]:
                continue
            ok = True
            for h, digest in r["headers"].items():
                if h.startswith(str(prev) + "/"):
                    mine = tree / h[len(str(prev)) + 1:]
                    if not mine.exists() or _sha(mine) != digest:
                        ok = False
                        break
            if not ok:
                continue

            obj.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(po, obj)
            shutil.copyfile(rec, obj.with_suffix(".obj.compile.json"))
            return True
        except (OSError, ValueError, KeyError):
            continue
    return False


def compile_files(rb, files, workers=2):
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    todo, done = [], {}
    prev_trees = [p for p in sorted((L / "work").glob("*/tree"), key=lambda p: p.stat().st_mtime, reverse=True)
                  if p != rb.tree][:2] if os.environ.get("NIGHTLY_REUSE") == "1" else []
    reused = 0
    for tu in files:
        o = rb.tree / "obj" / (tu.replace("/", "_") + ".obj")
        if o.exists() and (o.with_suffix(".obj.compile.json")).exists():
            done[tu] = (str(o), "")
        elif _reuse(rb.tree, prev_trees, tu, o):
            done[tu] = (str(o), "")
            reused += 1
        else:
            todo.append(tu)
    log(f"compile: {len(done) - reused} cached, {reused} reused from an earlier commit (source and every header "
        f"equal), {len(todo)} to compile on the farm")
    errors = {}
    if todo:
        sys.path.insert(0, str(L / "farm-unavailable"))
        import farm_compile
        objs, errors = farm_compile.compile_files(rb.sha, todo, dest=rb.tree / "obj", log=log)
        for tu, obj in objs.items():
            done[tu] = (str(obj), "")
        log(f"  farm compiled {len(objs)}/{len(todo)}, {len(errors)} errors")
    return {tu: o for tu, (o, _) in done.items()}, errors


def kind_of(name):
    if name.startswith("??_7") or name.startswith("??_8"):
        return "vtable"
    if name.startswith("??_R"):
        return "rtti"
    if name.startswith("__imp_"):
        return "import"
    if name.startswith("?"):
        m = re.search(r"@@[23456]", name)
        if m and not re.search(r"@@[QUAIEMSYCKG]", name.split("@@")[1] if "@@" in name else ""):
            return "data"
        if re.search(r"@@3|@@2", name) and not name.startswith("??"):
            return "data"
        return "function"
    return "c-name"


def name_rvas(main, rb, n):
    out = set(main.name_rva.get(n, ()))
    for r_ in rb.name_rows.get(n, []):
        out.add(r_["_rva"])
    if n in rb.sym_rva:
        out.add(rb.sym_rva[n])
    return out


def plan(main, rb, tus, objs, base_unres, base_dups, rounds=14):
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    sub_objs = {tu: "rebuilt/" + Path(objs[tu]).name for tu in tus if tu in objs}
    idx = dict(main.objects)
    for tu, rel in sub_objs.items():
        idx[rel] = coffsym.obj_symbols(objs[tu])
    rvas = {tu: {r_["_rva"] for r_ in rb.tu_rows.get(tu, [])} for tu in sub_objs}
    U = set().union(*rvas.values()) if rvas else set()
    in_rsp = {p_: i for i, p_ in enumerate(main.order)}
    cands, straddle = {}, {}
    for tu in sub_objs:
        c = set()
        for a in rvas[tu]:
            c |= main.rva_objs.get(a, set())
        cands[tu] = sorted(x for x in c if x in in_rsp)
        for o in cands[tu]:
            left = main.obj_rvas[o] - U
            if left:
                straddle.setdefault(tu, []).append((o, len(left), sorted(left)[:5]))
    owner = {}
    for tu, cs in cands.items():
        for o in cs:
            owner.setdefault(o, tu)
    kept_back = {}
    for tu, items in straddle.items():
        for o, n, _ in items:
            kept_back[o] = "straddle"
    bridges = {}
    localized = collections.defaultdict(set)
    externed = collections.defaultdict(set)
    qbridges, qn_defs = {}, None
    alt_of = None
    r = None


    tw_path = L / "inputs/data_twins.json"
    rb_defined = set()
    for rel in sub_objs.values():
        rb_defined |= {n for n, d_ in idx[rel]["defs"].items() if d_[1] in ("data", "bss", "common")}
    twins_used = {}
    if tw_path.exists() and os.environ.get("NIGHTLY_TWINS", "1") == "1":
        for mname, t_ in json.loads(tw_path.read_text()).items():
            if t_.get("off") or t_["rebuilt"] not in rb_defined or t_["main_obj"] not in in_rsp:
                continue
            if mname not in main.objects.get(t_["main_obj"], {}).get("defs", {}):
                continue
            externed[t_["main_obj"]].add(mname)
            bridges[mname] = t_["rebuilt"]
            twins_used[mname] = t_["rebuilt"]


    pads_used, pads_skipped, rb_extern = {}, {}, collections.defaultdict(set)
    rb_pads = {}
    pd_path = L / "inputs/pads.json"
    if pd_path.exists() and os.environ.get("NIGHTLY_PADS", "1") == "1":
        for po, spec in json.loads(pd_path.read_text()).items():
            d_a = main.objects.get(po, {}).get("defs", {}).get(spec["anchor"])
            rb_anchor = [(rel, n_) for rel in sub_objs.values() for n_, d_ in idx[rel]["defs"].items()
                         if d_[1] in ("data", "bss") and not d_[0]
                         and any(n_.startswith(x) for x in spec.get("rebuilt_anchor_prefixes", []))]
            if len(rb_anchor) > 1:
                pads_skipped[po] = f"several rebuilt definitions of the object: {rb_anchor}"
            elif rb_anchor:
                rel_, an_ = rb_anchor[0]
                rb_pads[rel_] = {"anchor": an_, "define_rel": spec["define_rel"], "min_room": spec["retail_extent"],
                                 "base_object": po}
                if po in in_rsp and d_a:
                    externed[po].add(spec["anchor"])
                    bridges[spec["anchor"]] = an_
                    twins_used[spec["anchor"]] = an_
            elif po not in in_rsp:
                pads_skipped[po] = "not in the base link"
            elif po in owner and po not in kept_back:
                pads_skipped[po] = "replaced by rebuilt " + str(owner[po]) + " (its size is the extents check's)"
            elif not d_a or d_a[1] != "bss" or d_a[3] != spec["section"] or d_a[2] != spec["old_size"]:
                pads_skipped[po] = f"anchor/section changed: {d_a}"
            else:
                pads_used[po] = spec
        tails = [(po, None, list(spec["define"])) for po, spec in pads_used.items()] + \
                [(None, rel_, list(rp["define_rel"])) for rel_, rp in rb_pads.items()]
        for po, rel_, names in tails:
            for nm in names:
                for o_, s_ in main.objects.items():
                    d_ = s_.get("defs", {}).get(nm)
                    if o_ != po and o_ in in_rsp and d_ and d_[1] in ("data", "bss", "common"):
                        externed[o_].add(nm)
                for rel in sub_objs.values():
                    if rel != rel_ and nm in idx[rel]["defs"]:
                        rb_extern[rel].add(nm)
        for rel, ns in rb_extern.items():
            idx[rel] = dict(idx[rel], defs={k: v for k, v in idx[rel]["defs"].items() if k not in ns},
                            undefs=sorted(set(idx[rel]["undefs"]) | ns))
        for rel_, rp in rb_pads.items():
            secn = idx[rel_]["defs"][rp["anchor"]]
            idx[rel_] = dict(idx[rel_], defs={**idx[rel_]["defs"], **{nm: list(secn) for nm in rp["define_rel"]}},
                             undefs=[u for u in idx[rel_]["undefs"] if u not in rp["define_rel"]])

    rebinds_used, rebinds_skipped = {}, {}

    rbf_ = os.environ.get("NIGHTLY_REBINDS_FILE", str(L / "inputs/rebinds.json"))
    if rbf_ and Path(rbf_).exists():
        for n_, sp_ in json.loads(Path(rbf_).read_text()).items():
            tgt = sp_["to"]
            defs_ = [o_ for o_ in in_rsp if (main.objects.get(o_, {}).get("defs", {}).get(n_) or [0, ""])[1] == "code"]
            has_t = [o_ for o_ in in_rsp if tgt in main.objects.get(o_, {}).get("defs", {})]
            if not defs_ or not has_t:
                rebinds_skipped[n_] = f"base definers {len(defs_)}, target definers {len(has_t)}"
                continue
            for o_ in defs_:
                localized[o_].add(n_)
            bridges[n_] = tgt
            rebinds_used[n_] = {"to": tgt, "localized_in": defs_}


    sys.path.insert(0, str(L / "planner"))
    import libguard
    lg_local, lg_extern, lg_exclude, lg_report = libguard.compute(
        main, rb, sub_objs, idx, in_rsp, set(owner) - set(kept_back), objs, sorted(bridges.items()), base=BASE)
    for rel_, ns_ in lg_local.items():
        idx[rel_] = dict(idx[rel_], defs={k: v for k, v in idx[rel_]["defs"].items() if k not in set(ns_)})
    for rel_, ns_ in lg_extern.items():
        idx[rel_] = dict(idx[rel_], defs={k: v for k, v in idx[rel_]["defs"].items() if k not in set(ns_)},
                         undefs=sorted(set(idx[rel_]["undefs"]) | set(ns_)))
    for it in range(rounds):
        for o_ in set(localized) | set(externed):
            b_ = main.objects[o_]
            gone = localized[o_] | externed[o_]
            idx[o_] = dict(b_, defs={k: v for k, v in b_["defs"].items() if k not in gone},
                           undefs=sorted(set(b_["undefs"]) | externed[o_]))
        for po, spec in pads_used.items():
            cur = idx[po] if (po in localized or po in externed) else main.objects[po]
            secn = cur["defs"][spec["anchor"]][4]
            idx[po] = dict(cur, defs={**cur["defs"], **{nm: [False, "bss", spec["new_size"], spec["section"], secn]
                                                       for nm in spec["define"]}})
        dropped = set(owner) - set(kept_back)
        pos = {tu: min((in_rsp[c] for c in cands[tu]), default=None) for tu in sub_objs}
        ins, tail, order = collections.defaultdict(list), [], []
        for tu, p_ in pos.items():
            (ins[p_] if p_ is not None else tail).append(sub_objs[tu])
        for i, p_ in enumerate(main.order):
            order.extend(ins.get(i, []))
            if p_ in dropped:
                continue
            if p_ == "build/exit_link/retail_initializers_after_objects.obj":
                order.extend(tail)
            order.append(p_)
        idx["<bridges>"] = {"secs": {}, "defs": {}, "undefs": [], "weak": {}, "refs": {}, "include": [],
                            "alt": sorted(bridges.items())}
        r = resolve.resolve(order + ["<bridges>"], idx, extra_needed=main.needed)
        unres = {n: v for n, v in r["unresolved"].items() if n not in base_unres and n not in LINKER_KNOWN}
        dups = {n: v for n, v in r["duplicates"].items() if n not in base_dups}
        defined = set(r["winner"]) | set(r["libdefs"])
        changed = False


        if alt_of is None:
            alt_of = collections.defaultdict(set)
            for o_, s_ in main.objects.items():
                for a_, b_ in s_.get("alt", []):
                    alt_of[a_].add(b_)
        targets = []
        for n in list(unres):
            stack, seen = [n], set()
            while stack:
                x = stack.pop()
                for b_ in alt_of.get(x, ()):
                    if b_ not in seen and b_ not in defined:
                        seen.add(b_)
                        targets.append(b_)
                        stack.append(b_)
        unres_t = list(unres) + [t_ for t_ in targets if t_ not in unres]
        for n in unres_t:
            if n in bridges:
                continue
            for a in sorted(name_rvas(main, rb, n)):
                alts = [m for m in (main.rva_names.get(a, set()) | {x["name"] for x in rb.rva_rows.get(a, [])})
                        if m != n and m in defined]
                if alts:
                    bridges[n] = sorted(alts)[0]
                    changed = True
                    break


        if qn_defs is None:
            qn_defs = collections.defaultdict(set)
            for o_, s_ in main.objects.items():
                if s_.get("lib"):
                    continue
                for d_ in s_.get("defs", {}):
                    if d_.startswith("?") and "@@" in d_ and not d_.startswith(("??_", "?$")):
                        qn_defs[d_.split("@@")[0]].add(d_)
        for n in unres:
            if n in bridges or not n.startswith("?") or n.startswith(("??_", "?$")) or "@@" not in n:
                continue
            if name_rvas(main, rb, n):
                continue
            c_ = [m for m in qn_defs.get(n.split("@@")[0], ()) if m != n and m in defined]
            if len(c_) == 1 and len(qn_defs[n.split("@@")[0]]) == 1:
                bridges[n] = c_[0]
                qbridges[n] = c_[0]
                changed = True
        dropped_defs = {}
        for o in dropped:
            for n in main.objects.get(o, {}).get("defs", {}):
                dropped_defs.setdefault(n, o)
            for n, _b in main.objects.get(o, {}).get("alt", []):
                dropped_defs.setdefault(n, o)
        for n in unres_t:
            if n not in bridges and n in dropped_defs and dropped_defs[n] not in kept_back:
                kept_back[dropped_defs[n]] = "defines " + n
                changed = True


        for n, ps in dups.items():
            rb_ps = [x for x in ps if x.startswith("rebuilt/")]
            others = [x for x in ps if not x.startswith("rebuilt/")]
            rb_strong = [x for x in rb_ps if not (idx[x]["defs"].get(n) or [False])[0]]
            if not rb_ps or not others or len(rb_strong) > 1:
                continue
            if any(x not in main.objects or main.objects[x].get("lib") for x in others):
                continue
            kinds = {x: (main.objects[x]["defs"].get(n) or [False, ""]) for x in others}
            if all(d_[1] == "code" for d_ in kinds.values()):
                tgt = localized
            elif all(d_[1] in ("data", "bss", "common") and (d_[1] == "common" or not d_[0]) for d_ in kinds.values())                     and rb_strong:
                tgt = externed
            else:
                continue
            for x in others:
                if n not in tgt[x]:
                    tgt[x].add(n)
                    changed = True

        for n, ps in dups.items():
            if any(x.startswith("rebuilt/") for x in ps):
                for x in ps:
                    if x in owner and x in kept_back and kept_back[x] == "straddle":
                        kept_back[x] = "straddle-dup:" + n
        if not changed:
            break
    shadow = []
    for tu, rel in sub_objs.items():
        own = {r_["name"] for r_ in rb.tu_rows.get(tu, [])}
        for n, d in idx[rel]["defs"].items():
            if d[0] and n in own and r["winner"].get(n) not in (rel, None):
                shadow.append((tu, n, r["winner"].get(n)))
    idx.pop("<bridges>", None)
    return {"order": order, "index": idx, "sub_objs": sub_objs, "drops": cands, "straddle": straddle,
            "unresolved": unres, "duplicates": dups, "shadow": shadow, "rebuilt": set(sub_objs.values()),
            "resolved": r, "dropped": dropped, "kept_back": kept_back, "bridges": bridges,
            "localized": {o_: sorted(ns_) for o_, ns_ in localized.items() if ns_},
            "externed": {o_: sorted(ns_) for o_, ns_ in externed.items() if ns_}, "qbridges": qbridges,
            "twins": twins_used, "pads": {po: sp for po, sp in pads_used.items() if po in order},
            "pads_skipped": dict(pads_skipped, **{po: "dropped from the order" for po in pads_used if po not in order}),
            "rb_extern": {rel: sorted(ns) for rel, ns in rb_extern.items()}, "rb_pads": rb_pads, "rebinds": rebinds_used,
            "rebinds_skipped": rebinds_skipped,
            "lg_local": lg_local, "lg_extern": lg_extern, "lg_exclude": lg_exclude, "libguard": lg_report}


def attribute(main, rb, p):
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    rebuilt_tu = {v: k for k, v in p["sub_objs"].items()}
    owner = {}
    for tu, cs in p["drops"].items():
        for o in cs:
            owner.setdefault(o, tu)
    by_file = collections.defaultdict(list)
    for n, refs in p["unresolved"].items():
        rb_refs = [rebuilt_tu[x] for x in refs if x in rebuilt_tu]
        rows = rb.name_rows.get(n, [])
        for tu in (rb_refs or [None]):
            by_file[tu].append({"cause": "references-name-nothing-defines", "symbol": n, "kind": kind_of(n),
                                "map_rows": [(r_["rva"], r_["_tu"]) for r_ in rows[:2]],
                                "retail_rva": sorted(hex(a) for a in name_rvas(main, rb, n))[:2],
                                "referenced_by": refs[:3]})
    for n, ps in p["duplicates"].items():
        rows = rb.name_rows.get(n, [])
        owners = sorted({r_["_tu"] for r_ in rows if r_["_tu"]})
        for tu in [rebuilt_tu[x] for x in ps if x in rebuilt_tu] or [None]:
            if not rows:
                cause = "duplicate-definition:no-map-row"
            elif tu in owners:
                cause = "duplicate-definition:hybrid-artifact"
            else:
                cause = "duplicate-definition:defines-another-files-row"
            by_file[tu].append({"cause": cause, "symbol": n, "kind": kind_of(n), "definers": ps,
                                "map_row_files": owners[:3]})
    for o, why in p["kept_back"].items():
        tu = owner.get(o)
        if why.startswith("defines "):
            n = why[8:]
            by_file[tu].append({"cause": "retail-object-defines-what-file-does-not", "symbol": n,
                                "kind": kind_of(n), "main_object": o,
                                "retail_rva": sorted(hex(a) for a in name_rvas(main, rb, n))[:2]})
    for n, m in p["bridges"].items():
        by_file["<bridges>"].append({"cause": "name-bridge", "symbol": n, "bridged_to": m, "kind": kind_of(n),
                                     "retail_rva": sorted(hex(a) for a in name_rvas(main, rb, n))[:2]})
    return by_file


def linkable(main, rb, tus, objs, base_unres, base_dups):
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    keep = [t for t in tus if t in objs]
    excluded = {}

    exf_ = os.environ.get("NIGHTLY_EXCLUDE_FILE", str(L / "inputs/exclude.json"))
    if exf_ and Path(exf_).exists():
        for tu_, why_ in json.loads(Path(exf_).read_text()).items():
            if tu_ in keep:
                keep.remove(tu_)
                excluded[tu_] = "plan input " + Path(exf_).name + ": " + why_
    lg_ex = {}
    p = None
    for _ in range(12):
        p = plan(main, rb, keep, objs, base_unres, base_dups)
        rebuilt_tu = {v: k for k, v in p["sub_objs"].items()}
        bad = set()
        for n, refs in p["unresolved"].items():
            bad |= {rebuilt_tu[x] for x in refs if x in rebuilt_tu}
        for n, ps in p["duplicates"].items():
            bad |= {rebuilt_tu[x] for x in ps if x in rebuilt_tu}
        for tu_, why_ in (p.get("lg_exclude") or {}).items():
            bad.add(tu_)
            excluded[tu_] = why_
            lg_ex[tu_] = ((p.get("libguard") or {}).get("units") or {}).get(tu_)
        if not bad:
            if lg_ex and p.get("libguard"):
                p["libguard"]["excluded_units"] = lg_ex
            return keep, excluded, p
        for tu in bad:
            excluded.setdefault(tu, "introduces-unresolved-or-duplicate")
        keep = [t for t in keep if t not in bad]
    return keep, excluded, plan(main, rb, keep, objs, base_unres, base_dups)


def wpath(p):
    return "Z:" + str(Path(p).resolve()).replace("/", "\\")


def real_link(main, p, outdir):
    """Vendored link planner module; see ci/nightly/PROVENANCE.md."""
    outdir.mkdir(parents=True, exist_ok=True)
    rb_dir = outdir / "rebuilt"
    rb_dir.mkdir(exist_ok=True)
    lines = []
    loc = p.get("localized") or {}
    ext = p.get("externed") or {}
    pads = p.get("pads") or {}
    rbx = p.get("rb_extern") or {}
    rbp = p.get("rb_pads") or {}
    if loc or ext or pads or rbx or rbp:
        sys.path.insert(0, str(L / "planner"))
        import localize2
    if pads or rbp:
        sys.path.insert(0, str(L / "planner"))
        import padobj
    for x in p["order"]:
        if x in pads:
            sp_ = pads[x]
            src_ = BASE / x
            if x in loc or x in ext:
                src_ = outdir / "localized" / (Path(x).name + ".prepad")
                gc, gd = localize2.localize(BASE / x, src_, loc.get(x, ()), ext.get(x, ()))
                if set(gc) != set(loc.get(x, ())) or set(gd) != set(ext.get(x, ())):
                    raise SystemExit(f"localize {x}: wanted {loc.get(x)} / {ext.get(x)}, patched {gc} / {gd}")
            dst = outdir / "padded" / Path(x).name
            padobj.pad(src_, dst, sp_["section"], sp_["old_size"], sp_["new_size"], sp_["anchor"], sp_["anchor_offset"],
                       sp_["define"])
            lines.append(f'"{wpath(dst)}"')
        elif x in loc or x in ext:
            dst = outdir / "localized" / Path(x).name
            gc, gd = localize2.localize(BASE / x, dst, loc.get(x, ()), ext.get(x, ()))
            if set(gc) != set(loc.get(x, ())) or set(gd) != set(ext.get(x, ())):
                raise SystemExit(f"localize {x}: wanted {loc.get(x)} / {ext.get(x)}, patched {gc} / {gd}")
            lines.append(f'"{wpath(dst)}"')
        elif x.startswith("rebuilt/"):
            lines.append(f'"{wpath(rb_dir / Path(x).name)}"')
        else:
            lines.append(f'"{x}"')
    for tu, rel in p["sub_objs"].items():
        shutil.copyfile(p["_obj_paths"][tu], rb_dir / Path(rel).name)
        lgl_, lge_ = (p.get("lg_local") or {}).get(rel, []), (p.get("lg_extern") or {}).get(rel, [])
        if lgl_ or lge_:
            sys.path.insert(0, str(L / "planner")); sys.path.insert(0, str(L / "planner"))
            import libguard, localize2
            f_ = rb_dir / Path(rel).name
            got_l = libguard.static_any(f_, f_, lgl_) if lgl_ else []
            got_e = localize2.localize(f_, f_, (), lge_)[1] if lge_ else []
            if set(got_l) != set(lgl_) or set(got_e) != set(lge_):
                raise SystemExit(f"library guard {rel}: wanted {len(lgl_)}/{len(lge_)}, patched {len(got_l)}/{len(got_e)}")
        if rel in rbx:
            _gc, gd = localize2.localize(rb_dir / Path(rel).name, rb_dir / Path(rel).name, (), rbx[rel])
            if set(gd) != set(rbx[rel]):
                raise SystemExit(f"extern {rel}: wanted {rbx[rel]}, patched {gd}")
        if rel in rbp:
            padobj.define_at(rb_dir / Path(rel).name, rb_dir / Path(rel).name, rbp[rel]["anchor"],
                             rbp[rel]["define_rel"], rbp[rel]["min_room"])
    for a, b in sorted(p["bridges"].items()):
        lines.append(f"/ALTERNATENAME:{a}={b}")
    repairs = BASE / "build/exit_link/base_repairs.rsp"
    if repairs.exists():
        lines += [l for l in repairs.read_text().splitlines() if l.strip()]
    if p.get("_stubs"):
        stub = "build/exit_link/diagnostic_stubs_main.obj"
        if not (BASE / stub).exists():
            stub = "build/exit_link/diagnostic_stubs.obj"
        lines.append(f'"{stub}"')
    lines.append('/DEF:"build/exit_link/retail.def"')
    lines.append('"build/exit_link/retail_resources.obj"')
    lines += [f"/INCLUDE:{n}" for n in IMPORT_ROOTS]
    rsp = outdir / "hybrid.rsp"
    rsp.write_text("\n".join(lines) + "\n")
    image = outdir / "exit.exe"
    cmd = ["nice", "-n", "15", "wine", str(VC / "Vc7/bin/link.exe"), "/NOLOGO", "/NODEFAULTLIB", "/INCREMENTAL:NO",
           "/MACHINE:X86", "/SUBSYSTEM:WINDOWS", "/ENTRY:WinMainCRTStartup", "/BASE:0x2000000",
           f"/OUT:{wpath(image)}", f"/MAP:{wpath(outdir / 'exit.map')}", "/FIXED:NO", "/OPT:NOREF", "/OPT:NOICF",
           f"@{wpath(rsp)}"]
    sys.path.insert(0, os.environ["NIGHTLY_BUILD_TOOLS"])
    import build
    env = dict(build.compiler_environment(build.vc71_root(), None))
    env.update(WINEPREFIX=str(L / "wine"), WINEDEBUG="-all")
    t0 = time.time()
    try:
        r = None
        if os.environ.get("NIGHTLY_REMOTE_LINK", "1") == "1":
            sys.path.insert(0, str(L / "farm-unavailable"))
            import farm_link
            try:
                r = farm_link.run(cmd, cwd=BASE, env=env, files_root=outdir,
                                  outputs=[outdir / "exit.map", outdir / "link.log", outdir / "exit.exe",
                                           outdir / "exit.exp", outdir / "exit.lib"],
                                  mirrors=[BASE], timeout=7200, who="nightly")
                (outdir / "farm.json").write_text(json.dumps(getattr(r, "farm", {}) or {}, default=str))
            except farm_link.FarmUnavailable as e:
                (outdir / "farm.json").write_text(json.dumps({"fallback": str(e)}))
                r = None
        if r is None and os.environ.get("NIGHTLY_NO_LOCAL_LINK") == "1":
            r = subprocess.CompletedProcess(cmd, -8, "", "remote link unavailable and NIGHTLY_NO_LOCAL_LINK=1: not linked locally")
        if r is None:
            r = subprocess.run(cmd, cwd=BASE, env=env, capture_output=True, text=True, errors="replace", timeout=7200)
    except subprocess.TimeoutExpired as e:
        r = subprocess.CompletedProcess(cmd, -9, (e.stdout or b"").decode("latin-1", "replace") if isinstance(e.stdout, bytes) else (e.stdout or ""), "link.exe timed out after 7200 s")
    (outdir / "link.log").write_text(r.stdout + r.stderr)
    unres = sorted({m.group(1) or m.group(2) for m in re.finditer(
        r'error LNK20(?:01|19): unresolved external symbol (?:"[^"]*" \(([^)\s]+)\)|(\S+))', r.stdout)})
    dups = sorted({m.group(1) or m.group(2) for m in re.finditer(r"LNK2005: (?:\"[^\"]*\" \(([^)]+)\)|(\S+)) already defined", r.stdout)})
    return {"rc": r.returncode, "seconds": round(time.time() - t0), "image": image.exists() and r.returncode == 0,
            "unresolved": unres, "duplicates": dups,
            "errors": [l for l in r.stdout.splitlines() if " error LNK" in l or "fatal error" in l][:200]}


def run(sha, tier_names, do_link, outroot, stubs=False, base=None):
    global BASE
    if base:
        BASE = L / "base" / base
    main = Main()
    rb = Rebuild(sha)
    t = tiers(sha, rb.work)
    base_r = resolve.resolve(main.order, main.objects, extra_needed=main.needed)
    base_unres, base_dups = set(base_r["unresolved"]), set(base_r["duplicates"])
    results = {}
    for name in tier_names:
        tus = t[name]
        objs, errs = compile_files(rb, tus)
        if os.environ.get("NIGHTLY_DROP"):
            drop = {x.strip() for x in open(os.environ["NIGHTLY_DROP"]) if x.strip()}
            objs = {tu: o for tu, o in objs.items() if tu not in drop and Path(o).name not in drop
                    and (tu.replace("/", "_") + ".obj") not in drop}
            log("NIGHTLY_DROP: left out", len(drop), "names;", len(objs), "objects remain")
        p0 = plan(main, rb, list(objs), objs, base_unres, base_dups)
        attr = attribute(main, rb, p0)
        keep, excluded, p = linkable(main, rb, list(objs), objs, base_unres, base_dups)
        p["_obj_paths"] = objs
        p["_stubs"] = stubs
        res = {"tier": name, "files": len(tus), "compiled": len(objs), "compile_errors": errs,
               "strict": {"unresolved": len(p0["unresolved"]), "duplicates": len(p0["duplicates"]),
                          "straddle_files": len(p0["straddle"]), "shadowed": len(p0["shadow"]),
                          "dropped_main_objects": len(p0["dropped"]), "kept_back": len(p0["kept_back"]),
                          "bridges": len(p0["bridges"]), "localized_names": sum(map(len, p0["localized"].values()))},
               "linkable": {"files": len(keep), "excluded": excluded, "dropped_main_objects": len(p["dropped"]),
                            "functions": sum(len(rb.tu_rows.get(tu, [])) for tu in keep),
                            "predicted_unresolved": len(p["unresolved"]), "predicted_duplicates": len(p["duplicates"]),
                            "kept_back": len(p["kept_back"]), "bridges": len(p["bridges"]), "shadowed": len(p["shadow"]),
                            "localized_objects": len(p["localized"]), "localized_names": sum(map(len, p["localized"].values())),
                            "externed_names": sum(map(len, p["externed"].values())), "qname_bridges": len(p["qbridges"]),
                            "data_twins": len(p.get("twins") or {}),
                            "pads": sorted(p.get("pads") or {}), "pads_skipped": p.get("pads_skipped") or {},
                            "pad_rebuilt_externs": p.get("rb_extern") or {},
                            "rebuilt_pads": p.get("rb_pads") or {},
                            "rebinds": p.get("rebinds") or {}, "rebinds_skipped": p.get("rebinds_skipped") or {},
                            "libguard": p.get("libguard")},
               "base_unresolved": sorted(base_unres - LINKER_KNOWN), "base_duplicates": sorted(base_dups)}
        detail = {"attribution": {str(k): v for k, v in attr.items()}, "straddle": p0["straddle"],
                  "kept_back": p0["kept_back"], "bridges": p0["bridges"], "linkable_kept_back": p["kept_back"],
                  "linkable_bridges": p["bridges"], "localized": p0["localized"], "linkable_localized": p["localized"],
                  "externed": p0["externed"], "linkable_externed": p["externed"], "linkable_qbridges": p["qbridges"],
                  "shadow": p0["shadow"], "drops": p0["drops"], "unresolved": p0["unresolved"],
                  "duplicates": p0["duplicates"], "linkable_files": keep}
        d = outroot / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "detail.json").write_text(json.dumps(detail, indent=1, default=list))
        if do_link:
            res["link"] = real_link(main, p, d)
        (d / "result.json").write_text(json.dumps(res, indent=1))
        results[name] = res
        log(name, json.dumps({k: v for k, v in res.items() if k not in ("compile_errors", "base_unresolved")})[:1500])
    return results


def main_cli():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("tiers"); s.add_argument("rev")
    s = sub.add_parser("run"); s.add_argument("rev"); s.add_argument("--tier", action="append")
    s.add_argument("--link", action="store_true"); s.add_argument("--out")
    s.add_argument("--base", help="a directory under the work base/ directory")
    s.add_argument("--stubs", action="store_true", help="trap the BASE's own inherited unresolved names with the main repo's diagnostic stub object")
    a = ap.parse_args()
    sha = git("rev-parse", a.rev)
    if a.cmd == "tiers":
        rb = Rebuild(sha)
        t = tiers(sha, rb.work)
        print({k: len(v) for k, v in t.items()})
    elif a.cmd == "run":
        out = Path(a.out) if a.out else L / "runs" / (time.strftime("%Y%m%dT%H%M%S") + "-" + sha[:10])
        run(sha, a.tier or ["verified", "matching"], a.link, out, stubs=a.stubs, base=a.base)
        print(out)


if __name__ == "__main__":
    main_cli()
