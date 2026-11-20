"""Assemble nightly.json, the job summary and the alarm decisions from the stage outputs.

  python3 -B ci/nightly/result.py SHARDS_DIR STAGE2_DIR OUT_DIR --compile-job RESULT --game-job RESULT --game-live true|false|external [--jobs JOBS.json]

SHARDS_DIR holds the compile shards' shard.json files, STAGE2_DIR the link-and-play stage2.json (absent when that
stage did not run). RESULT is the GitHub job result (success, failure, cancelled, skipped). JOBS.json is the run's job
list from the GitHub API, used for wall time and machine minutes. Writes OUT_DIR/nightly.json, OUT_DIR/summary.md and
OUT_DIR/alarms.json ({kind: {"failed": true|false, "detail": text}}; a kind that was not measured is left out).
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

SCHEMA = "bfme2-nightly/1"
TEST_ORDER = ("udun", "control", "fords", "long", "save")
TEST_TITLES = {"udun": "Udun, seed 1, to frame 1000", "control": "Udun with a deliberate change at frame 500",
               "fords": "Fords of Isen II, seed 2, to frame 1000", "long": "Udun, seed 1, to frame 5000",
               "save": "Save at frame 600, load, play on"}


def compile_summary(shards_dir, sha, expected):
    """Join the shard summaries of this run. Returns the totals with "problem": None, or with the first defect found
    (a missing, foreign, duplicated or extra shard) as an expected/found sentence."""
    infos = [json.loads(p.read_text()) for p in sorted(Path(shards_dir).glob("*/shard.json"))]
    s = {k: sum(int(i.get(k) or 0) for i in infos) for k in ("files", "compiled", "compile_errors", "fully_matching")}
    s.update(shards=len(infos), expected_shards=expected,
             slowest_shard_s=max((i.get("seconds") or 0 for i in infos), default=None),
             fastest_shard_s=min((i.get("seconds") or 0 for i in infos), default=None), problem=None,
             per_shard=[{"shard": i.get("shard"), "files": i.get("files"), "seconds": i.get("seconds"),
                         "batch_median_s": i.get("batch_median_s"), **(i.get("host") or {})}
                        for i in sorted(infos, key=lambda x: (str(type(x.get("shard"))), x.get("shard") or 0))])
    indices = sorted(i.get("shard") for i in infos if isinstance(i.get("shard"), int))
    foreign = sorted({i.get("sha") for i in infos} - {sha}, key=str)
    if not infos:
        s["problem"] = f"expected {expected} compile shard summaries from this run; found none"
    elif foreign:
        s["problem"] = f"expected compile shards of main {sha}; found shards of {foreign[0]}"
    elif any(i.get("shards") != expected for i in infos):
        plans = sorted({str(i.get("shards")) for i in infos})
        s["problem"] = f"expected every shard to belong to a {expected}-shard plan; found plans of {plans}"
    elif indices != list(range(expected)):
        s["problem"] = f"expected shard indices 0 to {expected - 1} once each; found {indices}"
    return s


STAMP = "%Y-%m-%dT%H:%M:%SZ"


def _ts(value):
    return datetime.strptime(value, STAMP) if value else None


def machine_time(jobs):
    """Wall time of the run and runner minutes per runner label, from the GitHub API job list."""
    if not jobs:
        return None
    starts = [_ts(j.get("started_at")) for j in jobs if j.get("started_at")]
    ends = [_ts(j.get("completed_at")) for j in jobs if j.get("completed_at")]
    per_stage = {}
    for j in jobs:
        a, b = _ts(j.get("started_at")), _ts(j.get("completed_at"))
        if a and b and b >= a and j.get("status", "completed") == "completed":
            name = j.get("name") or ""
            stage = ("compile" if name.startswith("Compile") else "link_and_play" if name.startswith("Link")
                     else "publish" if name.startswith("Publish") else "other")
            per_stage[stage] = round(per_stage.get(stage, 0) + (b - a).total_seconds() / 60, 1)
    return {"wall_minutes": round((max(ends) - min(starts)).total_seconds() / 60, 1) if starts and ends else None,
            "runner_minutes": per_stage, "jobs": len(jobs)}


def read_link(path):
    """The link census of this run, or None when it is absent or not in the expected form."""
    try:
        d = json.loads(Path(path).read_text()) if path else None
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict):
        return None
    keep = {k: d.get(k) for k in ("objects", "needed", "missing", "provided", "duplicates")}
    if not all(type(v) is int and v >= 0 for v in keep.values()) or keep["needed"] <= 0 \
            or keep["provided"] + keep["missing"] != keep["needed"]:
        return None
    by_kind = d.get("missing_by_kind")
    keep["missing_by_kind"] = {str(k): v for k, v in by_kind.items() if type(v) is int} if isinstance(by_kind, dict) else {}
    dup = d.get("duplicate_names")
    keep["duplicate_names"] = [str(x) for x in dup][:50] if isinstance(dup, list) else []
    prog = d.get("program_functions")
    if isinstance(prog, list) and len(prog) == 2 and all(type(v) is int and v >= 0 for v in prog) \
            and prog[1] > 0 and prog[0] <= prog[1]:
        keep["program_functions"] = prog
    return keep


def carried_link(previous, sha):
    """The link census the compile run published for the same commit, when this run measured none."""
    if not isinstance(previous, dict) or previous.get("sha") != sha:
        return None
    lc = previous.get("link_census")
    if not isinstance(lc, dict):
        return None
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({k: v for k, v in lc.items() if k != "refused"}, f)
    try:
        return read_link(f.name)
    finally:
        os.unlink(f.name)


GAME_FIELDS = ("files_substituted", "functions", "starts", "menu", "skirmish", "simulation_equal", "equal_frames",
               "save_load", "control_caught", "result", "headline", "image_sha256")


def game_record(n):
    """game/latest.json: the last game run's numbers and identities, written only by a run that played."""
    if n["stages"]["link_and_play"] in ("not live", "runs separately") or n.get("games_skipped") or not n["tests"]:
        return None
    rec = {k: n.get(k) for k in GAME_FIELDS}
    rec.update(schema="bfme2-nightly-game/1", sha=n["sha"], date=n.get("date"), public_run_id=n.get("run_id"),
               run_url=n.get("run_url"), tests={k: {f: v.get(f) for f in ("status", "frames_compared", "frames_equal",
                                                                         "first_divergent_frame")}
                                               for k, v in n["tests"].items()})
    return rec


def link_pair(link, headline="referenced"):
    """The card's Linking pair: names our written code refers to ("referenced"), or the original program's
    functions ("program"); None when not measured or refused."""
    if not link or link.get("refused"):
        return None
    if headline == "program":
        return link.get("program_functions")
    return [link["provided"], link["needed"]]


def check_link(link, compile_info):
    """A census over any other object count than one per source file would miscount what is needed: refuse it."""
    if not link:
        return link
    files = (compile_info or {}).get("files")
    compiled = (compile_info or {}).get("compiled")
    if type(files) is not int or files <= 0 or link["objects"] != files or compiled != files:
        return dict(link, refused=f"expected one object for each of {files} source files; found {link['objects']}")
    return link


def check_rows(tests):
    def st(name):
        return (tests.get(name) or {}).get("status")
    udun = tests.get("udun") or {}
    reached = bool(udun.get("frames_compared"))
    rows = {}
    if not tests:
        return {k: "not run" for k in ("starts", "menu", "maps", "save_load", "control")}
    rows["starts"] = "pass" if reached else "fail"
    rows["menu"] = "pass" if reached else "fail"
    maps = [st(n) for n in ("udun", "fords", "long")]
    rows["maps"] = "pass" if all(m == "pass" for m in maps) else ("not run" if all(m is None for m in maps) else "fail")
    rows["save_load"] = {None: "not run", "pass": "pass"}.get(st("save"), "fail")
    rows["control"] = {None: "not run", "pass": "pass"}.get(st("control"), "fail")
    return rows


def build(compile_info, stage2, meta):
    compile_ok = meta["compile_job"] == "success" and compile_info is not None and compile_info.get("problem") is None
    s2 = stage2 or {}
    tests = s2.get("tests") or {}
    frames_compared = sum((t.get("frames_compared") or 0) for n, t in tests.items() if n != "control")
    frames_equal = sum((t.get("frames_equal") or 0) for n, t in tests.items() if n != "control")
    first = {n: t.get("first_divergent_frame") for n, t in tests.items()
             if n != "control" and t.get("first_divergent_frame") is not None}
    statuses = [t.get("status") for t in tests.values()]
    linked = bool((s2.get("link") or {}).get("image"))
    size_ok = (s2.get("size_check") or {}).get("blocking") == 0 if s2.get("size_check") else False
    live = bool(meta.get("game_live"))
    if not compile_ok:
        result = "fail"
    elif not live:
        result = "partial"
    elif stage2 is None or s2.get("stopped") or meta["game_job"] != "success":
        result = "fail"
    elif s2.get("games_skipped") and linked and size_ok:
        result = "partial"
    elif all(s == "pass" for s in statuses) and len(tests) == len(TEST_ORDER) and linked and size_ok:
        result = "pass"
    else:
        result = "fail"
    rows = check_rows(tests)
    flag = {"pass": True, "fail": False}
    record_tests = [tests[n].get("status") for n in ("udun", "fords", "long", "save") if n in tests]
    if not record_tests:
        sim_equal = None
    elif any(s == "differs" for s in record_tests):
        sim_equal = False
    else:
        sim_equal = True if all(s == "pass" for s in record_tests) and len(record_tests) == 4 else None
    ctl = (tests.get("control") or {}).get("status")
    ci = compile_info or {}
    link = check_link(meta.get("link"), compile_info)
    compiled = f"{ci.get('compiled', 0)} of {ci.get('files', 0)} files compile, {ci.get('fully_matching', 0)} match completely"
    if result == "partial" and live:
        headline = (f"links and checks: {(s2.get('plan') or {}).get('files')} rebuilt files, 0 unresolved, "
                    f"0 blocking size findings; games not played this run")
    elif result == "partial":
        headline = (f"compiles ({compiled}); game run follows separately" if meta.get("game_external")
                    else f"compiles ({compiled}); game run not live yet")
    elif result == "pass":
        headline = (f"plays identically: {(s2.get('plan') or {}).get('files')} rebuilt files, "
                    f"{frames_equal} of {frames_compared} checksum frames equal, control caught")
    elif not compile_ok:
        headline = "compile stage failed: " + (ci.get("problem") or f"the compile jobs ended with {meta['compile_job']}")
    else:
        bad = [f"{t['name']} {t.get('status')}" for t in tests.values() if t.get("status") != "pass"]
        headline = "game run failed: " + (s2.get("stopped") or ", ".join(bad) or f"stage ended with {meta['game_job']}")
    return {
        "headline": headline,
        "schema": SCHEMA, "sha": meta["sha"], "date": meta.get("date"),
        "starts": flag.get(rows["starts"]), "menu": flag.get(rows["menu"]), "skirmish": flag.get(rows["maps"]),
        "save_load": flag.get(rows["save_load"]), "simulation_equal": sim_equal, "equal_frames": frames_equal if tests else None,
        "control_caught": None if ctl is None else ctl == "pass",
        "provided_required_symbols": link_pair(link, meta.get("linking_headline", "referenced")), "link_census": link,
        "linking_headline": meta.get("linking_headline", "referenced"),
        "linking_unit": "functions" if meta.get("linking_headline") == "program" else "names",
        "commit": meta["sha"], "run_id": meta.get("run_id"), "run_url": meta.get("run_url"),
        "event": meta.get("event"), "result": result, "compile_ok": compile_ok,
        "games_skipped": bool(s2.get("games_skipped")),
        "stages": {"compile": meta["compile_job"], "link_and_play": meta["game_job"] if live else
                   ("runs separately" if meta.get("game_external") else "not live")},
        "compile": compile_info,
        "files_substituted": (s2.get("plan") or {}).get("files"),
        "functions": (s2.get("plan") or {}).get("functions"),
        "plan": s2.get("plan"), "link": s2.get("link"), "size_check": s2.get("size_check"),
        "image_sha256": s2.get("image_sha256"), "image_manifest_sha256": s2.get("image_manifest_sha256"),
        "checks": rows,
        "tests": {n: tests[n] for n in TEST_ORDER if n in tests},
        "frames": {"compared": frames_compared, "equal": frames_equal, "first_divergent": first},
        "stopped": s2.get("stopped"),
        "timings": {"link_and_play": s2.get("timings"), "compile_slowest_shard_s": (compile_info or {}).get("slowest_shard_s"),
                    "run": meta.get("machine")},
    }


def alarms(n):
    """{kind: {failed, detail}} for every kind this night measured."""
    out = {}
    s2_ran = n["stages"]["link_and_play"] not in ("not live", "runs separately")
    build_failed = not n["compile_ok"] or (s2_ran and (n["link"] is None or not n["link"].get("image")
                                                       or (n["size_check"] or {}).get("blocking", 1) != 0))
    problem = (n["compile"] or {}).get("problem")
    if n["stages"]["compile"] != "success":
        detail = "expected the compile stage to succeed; found " + n["stages"]["compile"]
    elif problem:
        detail = problem
    else:
        detail = n.get("stopped") or ""
    if build_failed and not detail and s2_ran and n["stages"]["link_and_play"] != "success":
        detail = "the link-and-play stage ended with " + n["stages"]["link_and_play"]
    if build_failed or n["stages"]["link_and_play"] != "runs separately":
        out["nightly-build"] = {"failed": build_failed, "detail": detail or "built and checked"}
    if s2_ran and not build_failed and not n.get("games_skipped"):
        tests = n["tests"]
        crash = [t for t in tests.values() if t.get("status") == "crash"]
        differs = [t for t in tests.values() if t.get("status") == "differs"]
        out["nightly-crash"] = {"failed": bool(crash) or len(tests) == 0,
                                "detail": "; ".join(f"{t['name']}: {t['detail']}" for t in crash) or
                                          ("expected game tests; found none" if not tests else "no crash")}
        out["nightly-differs"] = {"failed": bool(differs),
                                  "detail": "; ".join(f"{t['name']}: {t['detail']}" for t in differs) or "all frames equal"}
        ctl = tests.get("control")
        if ctl is not None:
            out["nightly-control"] = {"failed": ctl.get("status") != "pass", "detail": ctl.get("detail", "")}
    return out


def summary(n):
    L = [f"# Nightly build of main {n['commit'][:10]}: **{n['result'].upper()}**", ""]
    L.append("The nightly job compiles every source file, substitutes each file whose functions all match the "
             "original into the original program's link, links that image, plays it and compares the game state "
             "with the original program's recording, frame by frame.")
    L.append("")
    c = n["compile"] or {}
    L.append("| Stage | Result |")
    L.append("| --- | --- |")
    L.append(f"| Compile | {n['stages']['compile']}: {c.get('compiled', '?')} of {c.get('files', '?')} files compiled, "
             f"{c.get('fully_matching', '?')} match completely |")
    lc = n.get("link_census") or {}
    if lc and not lc.get("refused"):
        prog = lc.get("program_functions")
        L.append(f"| Linking | {lc['provided']:,} of {lc['needed']:,} names our written code refers to are provided "
                 f"({100 * lc['provided'] / lc['needed']:.1f}%); {lc['missing']:,} missing, {lc['duplicates']:,} defined twice |")
        if prog:
            L.append(f"| Whole program | {prog[0]:,} of {prog[1]:,} functions of the original program are defined "
                     f"({100 * prog[0] / prog[1]:.1f}%) |")
    else:
        why = lc.get("refused")
        L.append(f"| Linking | not measured this run{': ' + why if why else ''} |")
    if n["stages"]["link_and_play"] == "not live":
        L.append("| Link and play | not live yet: the private game image for this stage is not configured |")
    elif n["stages"]["link_and_play"] == "runs separately":
        L.append("| Link and play | runs later in the private game run, which replaces this result |")
    else:
        lk = n["link"] or {}
        L.append(f"| Plan | {n['files_substituted']} files and {n['functions']} functions substituted |")
        L.append(f"| Link | {'image written' if lk.get('image') else 'no image'}, {lk.get('unresolved', '?')} unresolved, "
                 f"{lk.get('duplicates', '?')} duplicate names |")
        sc = n["size_check"] or {}
        L.append(f"| Size check | {sc.get('blocking', 'not run')} blocking findings |")
        for name in TEST_ORDER:
            t = n["tests"].get(name)
            L.append(f"| {TEST_TITLES[name]} | {t['status'] + ': ' + t['detail'] if t else 'not run'} |")
    L.append("")
    if n.get("stopped"):
        L += [f"Stopped: {n['stopped']}", ""]
    if c.get("per_shard"):
        L.append(f"Compile shards took {round((c.get('fastest_shard_s') or 0) / 60, 1)} to "
                 f"{round((c.get('slowest_shard_s') or 0) / 60, 1)} min; median batch of 8 files "
                 f"{min(s.get('batch_median_s') or 0 for s in c['per_shard'])} to "
                 f"{max(s.get('batch_median_s') or 0 for s in c['per_shard'])} s across machines.")
    run = (n["timings"] or {}).get("run") or {}
    if run:
        L.append(f"Wall time {run.get('wall_minutes')} min; runner minutes by stage {json.dumps(run.get('runner_minutes'))}.")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shards")
    ap.add_argument("stage2")
    ap.add_argument("out")
    ap.add_argument("--compile-job", required=True)
    ap.add_argument("--game-job", required=True)
    ap.add_argument("--jobs")
    ap.add_argument("--shards-expected", type=int, required=True)
    ap.add_argument("--link", help="link_census.py output; absent or unreadable means linking was not measured")
    ap.add_argument("--game-live", choices=["true", "false", "external"], required=True)
    ap.add_argument("--previous", help="the nightly branch's current latest.json (its link census is reused for the same commit)")
    ap.add_argument("--linking-headline", choices=["referenced", "program"], default="referenced",
                    help="which pair the card's Linking field carries")
    a = ap.parse_args()
    s2p = Path(a.stage2) / "stage2.json"
    stage2 = json.loads(s2p.read_text()) if s2p.is_file() else None
    jobs = json.loads(Path(a.jobs).read_text()).get("jobs") if a.jobs and Path(a.jobs).is_file() else None
    server = os.environ.get("GITHUB_SERVER_URL", "")
    repo = os.environ.get("NIGHTLY_REPOSITORY") or os.environ.get("GITHUB_REPOSITORY", "")
    run = os.environ.get("NIGHTLY_RUN_ID") or os.environ.get("GITHUB_RUN_ID", "")
    meta = {"sha": os.environ.get("NIGHTLY_SHA") or os.environ.get("GITHUB_SHA", ""), "run_id": run, "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "event": os.environ.get("GITHUB_EVENT_NAME"),
            "run_url": f"{server}/{repo}/actions/runs/{run}" if run else None,
            "compile_job": a.compile_job, "game_job": a.game_job, "game_live": a.game_live == "true", "game_external": a.game_live == "external",
            "machine": machine_time(jobs), "link": read_link(a.link), "linking_headline": a.linking_headline}
    if meta["link"] is None and a.previous and Path(a.previous).is_file():
        try:
            meta["link"] = carried_link(json.loads(Path(a.previous).read_text()), meta["sha"])
        except ValueError:
            meta["link"] = None
    n = build(compile_summary(a.shards, meta["sha"], a.shards_expected), stage2, meta)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "nightly.json").write_text(json.dumps(n, indent=1, sort_keys=True) + "\n")
    game = game_record(n)
    if game:
        (out / "game.json").write_text(json.dumps(game, indent=1, sort_keys=True) + "\n")
    (out / "summary.md").write_text(summary(n))
    (out / "alarms.json").write_text(json.dumps(alarms(n), indent=1, sort_keys=True) + "\n")
    print(summary(n))


if __name__ == "__main__":
    main()
