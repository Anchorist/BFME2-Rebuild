"""Offline tests of the nightly package: python3 -B -m unittest discover -s ci/nightly/tests"""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
NIGHTLY = HERE.parent
REPO = NIGHTLY.parent.parent
sys.path.insert(0, str(NIGHTLY))

import alarms  # noqa: E402
import checks  # noqa: E402
import plan_shards  # noqa: E402
import result  # noqa: E402

SHA = "a" * 40


def record(frames, bad=()):
    return {"crcs": {str(f): (f * 7 + (1 if f in bad else 0)) for f in frames}}


class Shards(unittest.TestCase):
    def test_assignment_is_complete_disjoint_and_deterministic(self):
        sizes = {f"src/f{i}.cpp": (i * 37) % 101 + 1 for i in range(300)}
        a = plan_shards.assign(sizes, 8)
        self.assertEqual(a, plan_shards.assign(dict(reversed(list(sizes.items()))), 8))
        flat = [p for g in a for p in g]
        self.assertEqual(sorted(flat), sorted(sizes))
        self.assertEqual(len(flat), len(set(flat)))
        loads = [sum(sizes[p] for p in g) for g in a]
        self.assertLessEqual(max(loads) - min(loads), max(sizes.values()))

    def test_source_files_reads_ls_tree(self):
        class G:
            def value(self, *a):
                return ("100644 blob 1111 120\tsrc/a.cpp\n100644 blob 2222 30\tsrc/b.c\n"
                        "100644 blob 3333 9\tsrc/c.h\n100644 blob 4444 9\tsrc/d.CPP")
        self.assertEqual(plan_shards.source_files(G(), SHA), {"src/a.cpp": 120, "src/b.c": 30})

    def test_zero_shards_refused(self):
        with self.assertRaises(ValueError):
            plan_shards.assign({"src/a.cpp": 1}, 0)


class Compare(unittest.TestCase):
    frames = range(25, 1001, 25)

    def test_equal_run_passes(self):
        f = checks.crc_compare(record(self.frames), record(self.frames), 1000)
        self.assertEqual((f["frames_compared"], f["frames_equal"], f["first_divergent_frame"]), (40, 40, None))
        v = checks.judge_test(checks.TESTS[0], f, 0)
        self.assertEqual(v["status"], "pass")

    def test_differing_frame_is_reported(self):
        f = checks.crc_compare(record(self.frames), record(self.frames, bad={300, 400}), 1000)
        v = checks.judge_test(checks.TESTS[0], f, 0)
        self.assertEqual((v["status"], v["first_divergent_frame"]), ("differs", 300))
        self.assertIn("first differing frame 300", v["detail"])

    def test_short_run_is_a_crash(self):
        f = checks.crc_compare(record(self.frames), record(range(25, 501, 25)), 1000)
        v = checks.judge_test(checks.TESTS[0], f, 1)
        self.assertEqual(v["status"], "crash")
        self.assertIn("expected 40 compared frames; found 20", v["detail"])

    def test_no_record_is_a_crash(self):
        self.assertEqual(checks.judge_test(checks.TESTS[0], {}, 1)["status"], "crash")

    def test_control_caught_at_its_frame_passes(self):
        ctl = next(t for t in checks.TESTS if t["name"] == "control")
        f = checks.crc_compare(record(self.frames), record(self.frames, bad=set(range(500, 1001, 25))), 1000)
        self.assertEqual(checks.judge_test(ctl, f, 0)["status"], "pass")

    def test_control_not_caught_fails(self):
        ctl = next(t for t in checks.TESTS if t["name"] == "control")
        f = checks.crc_compare(record(self.frames), record(self.frames), 1000)
        self.assertEqual(checks.judge_test(ctl, f, 0)["status"], "control-blind")
        f = checks.crc_compare(record(self.frames), record(self.frames, bad={250}), 1000)
        self.assertEqual(checks.judge_test(ctl, f, 0)["status"], "control-blind")

    def test_until_limits_the_control(self):
        f = checks.crc_compare(record(range(25, 5001, 25)), record(range(25, 1001, 25)), 1000)
        self.assertEqual((f["frames_compared"], f["control_frames"]), (40, 40))

    def test_list_form_records(self):
        f = checks.crc_compare({"crcs": [[25, 1], [50, 2]]}, {"crcs": [["25", 1], ["50", 3]]})
        self.assertEqual(f["first_divergent_frame"], 50)

    def test_reload(self):
        save = next(t for t in checks.TESTS if t["name"] == "save")
        ctl = {"crcs": {"625": 1, "650": 2}, "crcs_before_load": {"25": 5}}
        ok = checks.reload_compare(ctl, dict(ctl, outcome="pass"))
        self.assertEqual(checks.judge_test(save, ok, 0)["status"], "pass")
        bad = checks.reload_compare(ctl, {"outcome": "pass", "crcs": {"625": 1, "650": 9}, "crcs_before_load": {"25": 5}})
        self.assertEqual(checks.judge_test(save, bad, 0)["status"], "differs")
        crash = checks.reload_compare(ctl, {"outcome": "crash", "crcs_before_load": {"25": 5}})
        self.assertEqual(checks.judge_test(save, crash, 0)["status"], "crash")
        self.assertEqual(checks.judge_test(save, {}, 0)["status"], "crash")


def write_shard(root, i, n, files, sha=SHA, matching=()):
    d = Path(root) / f"nightly-shard-{i}"
    d.mkdir(parents=True)
    with open(d / "judge.jsonl", "w") as f:
        for tu in files:
            f.write(json.dumps({"tu": tu, "functions": 2, "function_match": 2 if tu in matching else 1}) + "\n")
    (d / "shard.json").write_text(json.dumps({"sha": sha, "shard": i, "shards": n, "files": len(files), "compiled": len(files),
                                              "compile_errors": 0, "fully_matching": len(set(files) & set(matching)),
                                              "seconds": 10.0 + i}))


class Merge(unittest.TestCase):
    def test_complete_set_merges(self):
        with tempfile.TemporaryDirectory() as d:
            write_shard(d, 0, 2, ["src/a.cpp"], matching=["src/a.cpp"])
            write_shard(d, 1, 2, ["src/b.cpp"])
            res, info = checks.merge_shards(d, SHA, ["src/a.cpp", "src/b.cpp"])
            self.assertEqual([r["tu"] for r in res], ["src/a.cpp", "src/b.cpp"])
            self.assertEqual((info["files"], info["fully_matching"], info["slowest_shard_s"]), (2, 1, 11.0))

    def test_missing_shard_refused(self):
        with tempfile.TemporaryDirectory() as d:
            write_shard(d, 0, 2, ["src/a.cpp"])
            with self.assertRaisesRegex(ValueError, "every compile shard"):
                checks.merge_shards(d, SHA, ["src/a.cpp"])

    def test_foreign_commit_refused(self):
        with tempfile.TemporaryDirectory() as d:
            write_shard(d, 0, 1, ["src/a.cpp"], sha="b" * 40)
            with self.assertRaisesRegex(ValueError, "compile shards of"):
                checks.merge_shards(d, SHA, ["src/a.cpp"])

    def test_missing_file_refused(self):
        with tempfile.TemporaryDirectory() as d:
            write_shard(d, 0, 1, ["src/a.cpp"])
            with self.assertRaisesRegex(ValueError, "missing 1"):
                checks.merge_shards(d, SHA, ["src/a.cpp", "src/b.cpp"])

    def test_duplicate_refused(self):
        with tempfile.TemporaryDirectory() as d:
            write_shard(d, 0, 2, ["src/a.cpp"])
            write_shard(d, 1, 2, ["src/a.cpp"])
            with self.assertRaisesRegex(ValueError, "twice"):
                checks.merge_shards(d, SHA, ["src/a.cpp"])


def stage2(statuses=None, stopped=None, image=True, blocking=0):
    statuses = statuses or {}
    tests = {}
    for t in checks.TESTS:
        st = statuses.get(t["name"], "pass")
        tests[t["name"]] = {"name": t["name"], "status": st, "detail": f"{t['name']} {st}",
                            "frames_compared": 40, "frames_equal": 40 if st == "pass" else 10,
                            "first_divergent_frame": 300 if st == "differs" else None}
    return {"sha": SHA, "stopped": stopped, "tests": tests, "timings": {"stage_s": 1},
            "plan": {"files": 323, "functions": 5600}, "link": {"image": image, "unresolved": 0, "duplicates": 0},
            "size_check": {"blocking": blocking}, "image_sha256": "c" * 64}


def meta(compile_job="success", game_job="success", live=True):
    return {"sha": SHA, "compile_job": compile_job, "game_job": game_job, "game_live": live, "machine": None}


CINFO = {"files": 2, "compiled": 2, "compile_errors": 0, "fully_matching": 1, "shards": 8, "expected_shards": 8,
         "slowest_shard_s": 3, "problem": None}


class Result(unittest.TestCase):
    def test_clean_night(self):
        n = result.build(CINFO, stage2(), meta())
        self.assertEqual(n["result"], "pass")
        self.assertEqual((n["files_substituted"], n["functions"]), (323, 5600))
        self.assertEqual(n["checks"], {"starts": "pass", "menu": "pass", "maps": "pass", "save_load": "pass", "control": "pass"})
        a = result.alarms(n)
        self.assertEqual({k: v["failed"] for k, v in a.items()},
                         {"nightly-build": False, "nightly-crash": False, "nightly-differs": False, "nightly-control": False})
        self.assertIn("**PASS**", result.summary(n))
        self.assertEqual({k: n[k] for k in ("starts", "menu", "skirmish", "save_load", "simulation_equal", "control_caught")},
                         dict.fromkeys(("starts", "menu", "skirmish", "save_load", "simulation_equal", "control_caught"), True))
        self.assertEqual(n["equal_frames"], 160)

    def test_game_stage_not_live_is_partial_and_touches_only_build_alarm(self):
        n = result.build(CINFO, None, meta(game_job="skipped", live=False))
        self.assertEqual((n["result"], n["stages"]["link_and_play"]), ("partial", "not live"))
        self.assertEqual(set(result.alarms(n)), {"nightly-build"})
        self.assertIn("not live yet", result.summary(n))
        self.assertEqual((n["starts"], n["simulation_equal"], n["control_caught"], n["equal_frames"]), (None, None, None, None))

    def test_compile_failure(self):
        n = result.build(CINFO, None, meta(compile_job="failure", game_job="skipped"))
        self.assertEqual(n["result"], "fail")
        a = result.alarms(n)
        self.assertTrue(a["nightly-build"]["failed"])
        self.assertIn("expected the compile stage to succeed; found failure", a["nightly-build"]["detail"])

    def test_link_failure(self):
        n = result.build(CINFO, dict(stage2(), tests={}, stopped="expected a linked image; found none", image=False,
                                     link={"image": False}), meta(game_job="failure"))
        a = result.alarms(n)
        self.assertEqual(n["result"], "fail")
        self.assertTrue(a["nightly-build"]["failed"])
        self.assertNotIn("nightly-crash", a)

    def test_game_job_lost_without_result(self):
        n = result.build(CINFO, None, meta(game_job="failure"))
        self.assertEqual(n["result"], "fail")
        self.assertTrue(result.alarms(n)["nightly-build"]["failed"])

    def test_differs_and_crash(self):
        n = result.build(CINFO, stage2({"fords": "differs", "save": "crash"}), meta())
        a = result.alarms(n)
        self.assertEqual(n["result"], "fail")
        self.assertTrue(a["nightly-differs"]["failed"] and a["nightly-crash"]["failed"])
        self.assertFalse(a["nightly-control"]["failed"])
        self.assertEqual(n["frames"]["first_divergent"], {"fords": 300})
        self.assertEqual(n["checks"]["maps"], "fail")
        self.assertEqual((n["simulation_equal"], n["skirmish"], n["save_load"]), (False, False, False))

    def test_blind_control(self):
        n = result.build(CINFO, stage2({"control": "control-blind"}), meta())
        self.assertEqual(n["result"], "fail")
        self.assertTrue(result.alarms(n)["nightly-control"]["failed"])

    def test_size_check_blocks(self):
        n = result.build(CINFO, stage2(blocking=2), meta())
        self.assertEqual(n["result"], "fail")
        self.assertTrue(result.alarms(n)["nightly-build"]["failed"])

    def test_machine_time(self):
        def at(minutes):
            return (datetime(2026, 1, 1) + timedelta(minutes=minutes)).strftime(result.STAMP)
        jobs = [{"name": "Compile shard 0", "started_at": at(0), "completed_at": at(20), "labels": ["private-label"]},
                {"name": "Compile shard 1", "started_at": at(1), "completed_at": at(11), "labels": ["private-label"]},
                {"name": "Link, check and play the image", "started_at": at(21), "completed_at": at(81),
                 "labels": ["private-label"]}]
        m = result.machine_time(jobs)
        self.assertEqual(m["wall_minutes"], 81.0)
        self.assertEqual(m["runner_minutes"], {"compile": 30.0, "link_and_play": 60.0})
        self.assertNotIn("private-label", json.dumps(m))

    def test_output_is_deterministic(self):
        a = json.dumps(result.build(CINFO, stage2(), meta()), sort_keys=True)
        b = json.dumps(result.build(CINFO, stage2(), meta()), sort_keys=True)
        self.assertEqual(a, b)


class Summaries(unittest.TestCase):
    def make(self, d, specs):
        for k, (sha, idx, n) in enumerate(specs):
            p = Path(d) / f"nightly-shard-summary-{k}-a1"
            p.mkdir()
            (p / "shard.json").write_text(json.dumps({"sha": sha, "shard": idx, "shards": n, "files": 1, "compiled": 1,
                                                      "compile_errors": 0, "fully_matching": 0, "seconds": 2.0}))

    def night(self, d, compile_job="success"):
        info = result.compile_summary(d, SHA, 2)
        n = result.build(info, None, meta(compile_job=compile_job, game_job="skipped", live=False))
        return info, n, result.alarms(n)

    def test_complete(self):
        with tempfile.TemporaryDirectory() as d:
            self.make(d, [(SHA, 0, 2), (SHA, 1, 2)])
            info, n, a = self.night(d)
            self.assertIsNone(info["problem"])
            self.assertEqual((n["result"], a["nightly-build"]["failed"]), ("partial", False))

    def test_wrong_sha_opens_build_alarm_even_when_jobs_succeed(self):
        with tempfile.TemporaryDirectory() as d:
            self.make(d, [(SHA, 0, 2), ("b" * 40, 1, 2)])
            info, n, a = self.night(d)
            self.assertIn("expected compile shards of main", info["problem"])
            self.assertEqual(n["result"], "fail")
            self.assertTrue(a["nightly-build"]["failed"])
            self.assertEqual(a["nightly-build"]["detail"], info["problem"])

    def test_duplicate_index(self):
        with tempfile.TemporaryDirectory() as d:
            self.make(d, [(SHA, 0, 2), (SHA, 0, 2)])
            info, n, a = self.night(d)
            self.assertEqual(info["problem"], "expected shard indices 0 to 1 once each; found [0, 0]")
            self.assertTrue(a["nightly-build"]["failed"])

    def test_foreign_plan(self):
        with tempfile.TemporaryDirectory() as d:
            self.make(d, [(SHA, 0, 3), (SHA, 1, 3), (SHA, 2, 3)])
            info, _, a = self.night(d)
            self.assertIn("2-shard plan", info["problem"])
            self.assertTrue(a["nightly-build"]["failed"])

    def test_missing_artifacts_open_build_alarm(self):
        with tempfile.TemporaryDirectory() as d:
            self.make(d, [(SHA, 0, 2)])
            info, n, a = self.night(d)
            self.assertEqual(info["problem"], "expected shard indices 0 to 1 once each; found [0]")
            self.assertTrue(a["nightly-build"]["failed"])
        with tempfile.TemporaryDirectory() as d:
            info, n, a = self.night(d)
            self.assertIn("found none", info["problem"])
            self.assertTrue(a["nightly-build"]["failed"])


class Alarms(unittest.TestCase):
    def test_commands(self):
        with tempfile.TemporaryDirectory() as d:
            cmds = alarms.commands({"nightly-build": {"failed": True, "detail": "x"},
                                    "nightly-differs": {"failed": False, "detail": "y"}}, "https://run", d)
            self.assertEqual([(c[4], c[6]) for c in cmds], [("nightly-build", "true"), ("nightly-differs", "false")])
            self.assertEqual(Path(cmds[0][8]).read_text(), "x\n")

    def test_unknown_kind_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.json"
            p.write_text(json.dumps({"nightly-other": {"failed": True, "detail": ""}}))
            self.assertEqual(alarms.main(str(p), ""), 1)


class Publish(unittest.TestCase):
    def test_publish_to_a_local_branch(self):
        sys.path.insert(0, str(NIGHTLY))
        import publish_branch
        with tempfile.TemporaryDirectory() as d:
            remote = Path(d) / "remote.git"
            subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
            res = Path(d) / "res"
            res.mkdir()
            n = result.build(CINFO, stage2(), meta())
            (res / "nightly.json").write_text(json.dumps(n))
            (res / "summary.md").write_text(result.summary(n))
            env = dict(os.environ, NIGHTLY_PUSH_TOKEN="t", GITHUB_REPOSITORY="o/r", NIGHTLY_PUSH_URL=str(remote))
            for _ in range(2):
                subprocess.run([sys.executable, "-B", str(NIGHTLY / "publish_branch.py"), str(res)], env=env, check=True,
                               capture_output=True)
            log = subprocess.run(["git", "--git-dir", str(remote), "log", "--format=%s", "nightly"],
                                 capture_output=True, text=True, check=True).stdout.split("\n")
            self.assertEqual(log[0], f"Nightly pass for main {SHA}")
            self.assertEqual(len([x for x in log if x]), 2)
            files = subprocess.run(["git", "--git-dir", str(remote), "ls-tree", "-r", "--name-only", "nightly"],
                                   capture_output=True, text=True, check=True).stdout.split()
            self.assertIn("latest.json", files)
            self.assertTrue(any(f.startswith("history/") for f in files))


class Package(unittest.TestCase):
    CHECK = REPO / "ci/public-text/check.py"

    def test_no_internal_text(self):
        if not self.CHECK.exists():
            self.skipTest("ci/public-text/check.py not beside the package")
        paths = [str(NIGHTLY)] + [str(p) for p in (REPO / ".github/workflows/nightly.yml", self.CHECK) if p.exists()]
        r = subprocess.run([sys.executable, "-B", str(self.CHECK), *paths], cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_check_finds_planted_text(self):
        if not self.CHECK.exists():
            self.skipTest("ci/public-text/check.py not beside the package")
        planted = ["see ~/" + "pi" + "lot/link", "ask n" + "b1 at 16:" + "06Z", "mail " + "someone" + "@" + "example.org",
                   "the co" + "ordinator said", "run on s" + "rv1"]
        with tempfile.TemporaryDirectory() as d:
            for i, text in enumerate(planted):
                Path(d, f"f{i}.md").write_text(text + "\n")
            stamp = datetime(2026, 1, 1, 3, 17).strftime(result.STAMP)
            Path(d, "ok.md").write_text(f"stamp {stamp} and noreply 1+x@users.noreply.github.com\n")
            r = subprocess.run([sys.executable, "-B", str(self.CHECK), d], cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        named = sorted(set(re.findall(r"(f\d+\.md|ok\.md):\d+: ", r.stdout)))
        self.assertEqual(named, [f"f{i}.md" for i in range(len(planted))])

    def test_workflow_rules(self):
        wf = (REPO / ".github/workflows/nightly.yml")
        if not wf.exists():
            self.skipTest("workflow not beside the package")
        text = wf.read_text()
        self.assertIn("\npermissions: {}\n", text)
        for line in text.splitlines():
            if "uses:" in line:
                self.assertRegex(line, r"uses: [\w-]+/[\w-]+@[0-9a-f]{40}$")
        # the public workflow names no machine image that holds game files, and no variable can supply one
        for line in text.splitlines():
            if "runs-on:" in line:
                self.assertEqual(line.strip(), "runs-on: boat-small/from=bfme2-compiler-v1")
        self.assertNotIn("bfme2-nightly", text)
        self.assertNotIn("bfme2-game", text)
        compile_job = text.split("\n  compile:")[1].split("\n  publish:")[0]
        self.assertNotIn("github.token", compile_job)
        self.assertNotIn("contents: write", compile_job)
        self.assertIn("timeout-minutes: 40", compile_job)
        shards = re.search(r"shard: \[([\d, ]+)\]", compile_job).group(1)
        self.assertEqual([int(x) for x in shards.split(",")], list(range(int(re.search(r"SHARDS: '(\d+)'", text).group(1)))))

    def test_manifest_matches(self):
        m = NIGHTLY / "files.sha256"
        if not m.exists():
            self.skipTest("manifest written at packaging")
        r = subprocess.run(["sha256sum", "-c", "--quiet", "files.sha256"], cwd=NIGHTLY, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_vendored_planner_imports(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, NIGHTLY_WORK=d, NIGHTLY_GIT_DIR=d, NIGHTLY_BASELINE=d, NIGHTLY_VC_ROOT=d)
            code = ("import sys; sys.path.insert(0, sys.argv[1]); import hybrid, resolve, coffsym, localize2, padobj, "
                    "libguard; print(hybrid.kind_of('??_7Foo@@6B@'), hybrid.kind_of('?f@X@@QAEHXZ'))")
            r = subprocess.run([sys.executable, "-B", "-c", code, str(NIGHTLY / "planner")], env=env,
                               capture_output=True, text=True)
            self.assertEqual(r.stdout.strip(), "vtable function", r.stderr)

    def test_provenance_lists_every_vendored_file(self):
        prov = json.loads((NIGHTLY / "planner/PROVENANCE.json").read_text())
        names = sorted(p.name for p in (NIGHTLY / "planner").glob("*.py"))
        self.assertEqual(sorted(prov), names)
        import hashlib
        for name, v in prov.items():
            self.assertEqual(hashlib.sha256((NIGHTLY / "planner" / name).read_bytes()).hexdigest(), v["output_sha256"])


class Scrub(unittest.TestCase):
    def test_paths_and_flagged_text(self):
        import scrub
        out = scrub.scrub({"stopped": "expected X; found OSError: /opt/bfme2-nightly/ref/index.pkl missing",
                           "files": ["src/Code/GameEngine/A.cpp"], "n": 3,
                           "detail": "see " + "~/" + "pi" + "lot/link/x and ask " + "n" + "b1"})
        self.assertEqual(out["n"], 3)
        self.assertEqual(out["files"], ["src/Code/GameEngine/A.cpp"])
        self.assertIn("index.pkl missing", out["stopped"])
        self.assertNotIn("/opt/", out["stopped"])
        self.assertNotIn("pi" + "lot", out["detail"])
        self.assertIn("[removed]", out["detail"])


class External(unittest.TestCase):
    def test_compile_night_when_game_runs_elsewhere(self):
        m = dict(meta(game_job="skipped", live=False), game_external=True)
        n = result.build(CINFO, None, m)
        self.assertEqual((n["result"], n["stages"]["link_and_play"]), ("partial", "runs separately"))
        self.assertTrue(n["headline"].endswith("game run follows separately"))
        self.assertEqual(result.alarms(n), {})
        self.assertIn("runs later in the private game run", result.summary(n))

    def test_compile_failure_still_raises(self):
        m = dict(meta(compile_job="failure", game_job="skipped", live=False), game_external=True)
        a = result.alarms(result.build(CINFO, None, m))
        self.assertTrue(a["nightly-build"]["failed"])

    def test_headlines(self):
        self.assertTrue(result.build(CINFO, None, meta(game_job="skipped", live=False))["headline"]
                        .endswith("game run not live yet"))
        self.assertTrue(result.build(CINFO, stage2(), meta())["headline"].startswith("plays identically"))
        self.assertTrue(result.build(CINFO, stage2({"fords": "differs"}), meta())["headline"]
                        .startswith("game run failed: fords differs"))


class Machines(unittest.TestCase):
    def test_per_shard_facts(self):
        with tempfile.TemporaryDirectory() as d:
            for i, (sec, steal) in enumerate(((600.0, 0.5), (1500.0, 48.0))):
                p = Path(d) / f"nightly-shard-summary-{i}-a1"
                p.mkdir()
                (p / "shard.json").write_text(json.dumps({"sha": SHA, "shard": i, "shards": 2, "files": 1, "compiled": 1,
                                                          "compile_errors": 0, "fully_matching": 0, "seconds": sec,
                                                          "batch_median_s": sec / 25,
                                                          "host": {"cpus": 2, "steal_pct": steal}}))
            info = result.compile_summary(d, SHA, 2)
        self.assertEqual((info["fastest_shard_s"], info["slowest_shard_s"]), (600.0, 1500.0))
        self.assertEqual([s["steal_pct"] for s in info["per_shard"]], [0.5, 48.0])
        n = result.build(info, None, meta(game_job="skipped", live=False))
        self.assertIn("Compile shards took 10.0 to 25.0 min", result.summary(n))

    def test_cpu_times_shape(self):
        import compile_main
        t = compile_main.cpu_times()
        if t is None:
            self.skipTest("no /proc/stat here")
        facts = compile_main.host_facts(t, (t[0] + 50, t[1] + 50, t[2] + 200))
        self.assertEqual((facts["busy_pct"], facts["steal_pct"]), (25.0, 25.0))


class LinkOnly(unittest.TestCase):
    def test_skip_game_is_partial_and_leaves_game_alarms(self):
        s2 = dict(stage2(), tests={}, games_skipped=True)
        n = result.build(CINFO, s2, meta())
        self.assertEqual(n["result"], "partial")
        self.assertTrue(n["headline"].startswith("links and checks: 323 rebuilt files"))
        self.assertEqual(result.alarms(n), {"nightly-build": {"failed": False, "detail": "built and checked"}})


class FoldIn(unittest.TestCase):
    def setUp(self):
        import fold_in
        from datetime import timezone as tz
        self.f = fold_in
        self.now = datetime(2026, 1, 2, 7, 17).replace(tzinfo=tz.utc)
        self.meta = {"sha": SHA, "public_run_id": 44, "public_run_attempt": 1, "game_job": "success",
                     "workflow": ".github/workflows/nightly.yml",
                     "finished_at": datetime(2026, 1, 2, 6, 30).strftime(result.STAMP)}
        self.values = {"sha": SHA, "run_id": 44, "attempt": 1, "game_job": "success"}
        self.run = {"path": ".github/workflows/nightly.yml", "head_sha": SHA, "head_branch": "main",
                    "run_attempt": 1, "conclusion": "success"}
        self.jobs = [{"name": f"Compile shard {i}", "conclusion": "success"} for i in range(3)]

    def test_fresh(self):
        ok, why, out = self.f.decide(self.meta, {"sha": SHA}, self.now)
        self.assertTrue(ok, why)
        self.assertEqual(out, self.values)

    def test_refused_results(self):
        old = dict(self.meta, finished_at=datetime(2026, 1, 1, 6, 30).strftime(result.STAMP))
        for meta, stage2 in ((old, None), (self.meta, {"sha": "b" * 40}), (self.meta, {"tests": {}}),
                             (dict(self.meta, sha="zz"), None), (dict(self.meta, workflow=".github/workflows/x.yml"), None),
                             ({k: v for k, v in self.meta.items() if k != "public_run_id"}, None)):
            self.assertFalse(self.f.decide(meta, stage2, self.now)[0], (meta, stage2))

    def test_unknown_job_outcome_counts_as_failure(self):
        self.assertEqual(self.f.decide(dict(self.meta, game_job="weird"), None, self.now)[2]["game_job"], "failure")

    def test_bind(self):
        self.assertTrue(self.f.bind(self.values, self.run, self.jobs, 3)[0])
        for run in (dict(self.run, path=".github/workflows/other.yml"), dict(self.run, head_sha="b" * 40),
                    dict(self.run, run_attempt=2), dict(self.run, conclusion="failure"), dict(self.run, head_branch="x")):
            self.assertFalse(self.f.bind(self.values, run, self.jobs, 3)[0], run)
        self.assertFalse(self.f.bind(self.values, self.run, self.jobs[:2], 3)[0])
        self.assertFalse(self.f.bind(self.values, self.run, [dict(self.jobs[0], conclusion="failure")] + self.jobs[1:], 3)[0])

    def test_both_files_read_at_one_commit_while_the_branch_moves(self):
        commits = iter(["c" * 40, "d" * 40])
        seen = []

        def fake_get(api, path, token, raw=False):
            seen.append(path)
            if path.endswith("git/ref/heads/results"):
                return {"object": {"sha": next(commits)}}
            if "contents/meta.json" in path:
                return dict(self.meta, finished_at=datetime.now(timezone.utc).strftime(result.STAMP))
            if "contents/stage2.json" in path:
                return {"sha": SHA, "tests": {}}
            if path.endswith("/jobs?per_page=100"):
                return {"jobs": [{"name": f"Compile shard {i}", "conclusion": "success"} for i in range(16)]}
            return self.run
        saved = self.f.get
        self.f.get = fake_get
        env = {"GAME_REPO": "o/game", "GAME_TOKEN": "t", "GH_TOKEN": "u", "GITHUB_REPOSITORY": "o/pub", "SHARDS": "16"}
        old = {k: os.environ.get(k) for k in env}
        os.environ.update(env)
        try:
            with tempfile.TemporaryDirectory() as d:
                out = self.f.main(d)
        finally:
            self.f.get = saved
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.assertIn("fresh=true", out)
        contents = [p for p in seen if "/contents/" in p]
        self.assertEqual(contents, [f"repos/o/game/contents/meta.json?ref={'c' * 40}",
                                    f"repos/o/game/contents/stage2.json?ref={'c' * 40}"])
        self.assertEqual(sum(p.endswith("git/ref/heads/results") for p in seen), 1)

    def test_without_tokens_nothing_is_folded(self):
        env = {k: v for k, v in os.environ.items() if k not in ("GAME_REPO", "GAME_TOKEN", "GH_TOKEN", "GITHUB_OUTPUT")}
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, "-B", str(NIGHTLY / "fold_in.py"), d], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("fresh=false", r.stdout)

    def test_game_failure_without_stage2_fails_the_night(self):
        n = result.build(CINFO, None, meta(game_job="failure"))
        self.assertEqual(n["result"], "fail")
        self.assertTrue(result.alarms(n)["nightly-build"]["failed"])


if __name__ == "__main__":
    unittest.main()
