"""Assemble nightly.json, the job summary and the alarm decisions from the stage outputs.

  python3 -B ci/nightly/result.py SHARDS_DIR STAGE2_DIR OUT_DIR --compile-job RESULT --game-job RESULT --game-live true|false [--jobs JOBS.json]

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
             slowest_shard_s=max((i.get("seconds") or 0 for i in infos), default=None), problem=None)
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


def _ts(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ") if value else None


def machine_time(jobs):
    """Wall time of the run and runner minutes per runner label, from the GitHub API job list."""
    if not jobs:
        return None
    starts = [_ts(j.get("started_at")) for j in jobs if j.get("started_at")]
    ends = [_ts(j.get("completed_at")) for j in jobs if j.get("completed_at")]
    per_label = {}
    for j in jobs:
        a, b = _ts(j.get("started_at")), _ts(j.get("completed_at"))
        if a and b:
            label = ",".join(j.get("labels") or ["unknown"])
            per_label[label] = round(per_label.get(label, 0) + (b - a).total_seconds() / 60, 1)
    return {"wall_minutes": round((max(ends) - min(starts)).total_seconds() / 60, 1) if starts and ends else None,
            "runner_minutes": per_label, "jobs": len(jobs)}


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
    return {
        "schema": SCHEMA, "sha": meta["sha"], "date": meta.get("date"),
        "starts": flag.get(rows["starts"]), "menu": flag.get(rows["menu"]), "skirmish": flag.get(rows["maps"]),
        "save_load": flag.get(rows["save_load"]), "simulation_equal": sim_equal, "equal_frames": frames_equal if tests else None,
        "control_caught": None if ctl is None else ctl == "pass", "provided_required_symbols": None,
        "commit": meta["sha"], "run_id": meta.get("run_id"), "run_url": meta.get("run_url"),
        "event": meta.get("event"), "result": result, "compile_ok": compile_ok,
        "stages": {"compile": meta["compile_job"], "link_and_play": meta["game_job"] if live else "not live"},
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
    s2_ran = n["stages"]["link_and_play"] != "not live"
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
    out["nightly-build"] = {"failed": build_failed, "detail": detail or "built and checked"}
    if s2_ran and not build_failed:
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
    if n["stages"]["link_and_play"] == "not live":
        L.append("| Link and play | not live yet: the private game image for this stage is not configured |")
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
    run = (n["timings"] or {}).get("run") or {}
    if run:
        L.append(f"Wall time {run.get('wall_minutes')} min; runner minutes {json.dumps(run.get('runner_minutes'))}.")
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
    ap.add_argument("--game-live", choices=["true", "false"], required=True)
    a = ap.parse_args()
    s2p = Path(a.stage2) / "stage2.json"
    stage2 = json.loads(s2p.read_text()) if s2p.is_file() else None
    jobs = json.loads(Path(a.jobs).read_text()).get("jobs") if a.jobs and Path(a.jobs).is_file() else None
    server, repo, run = os.environ.get("GITHUB_SERVER_URL", ""), os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_RUN_ID", "")
    meta = {"sha": os.environ.get("GITHUB_SHA", ""), "run_id": run, "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "event": os.environ.get("GITHUB_EVENT_NAME"),
            "run_url": f"{server}/{repo}/actions/runs/{run}" if run else None,
            "compile_job": a.compile_job, "game_job": a.game_job, "game_live": a.game_live == "true",
            "machine": machine_time(jobs)}
    n = build(compile_summary(a.shards, meta["sha"], a.shards_expected), stage2, meta)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "nightly.json").write_text(json.dumps(n, indent=1, sort_keys=True) + "\n")
    (out / "summary.md").write_text(summary(n))
    (out / "alarms.json").write_text(json.dumps(alarms(n), indent=1, sort_keys=True) + "\n")
    print(summary(n))


if __name__ == "__main__":
    main()
