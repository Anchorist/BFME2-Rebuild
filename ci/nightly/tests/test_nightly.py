"""Offline tests of the nightly package: python3 -B -m unittest discover -s ci/nightly/tests"""
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
        jobs = [{"started_at": "2026-11-20T03:17:00Z", "completed_at": "2026-11-20T03:37:00Z", "labels": ["boat-small/from=x"]},
                {"started_at": "2026-11-20T03:38:00Z", "completed_at": "2026-11-20T04:38:00Z", "labels": ["boat/from=y"]}]
        m = result.machine_time(jobs)
        self.assertEqual(m["wall_minutes"], 81.0)
        self.assertEqual(m["runner_minutes"], {"boat-small/from=x": 20.0, "boat/from=y": 60.0})

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
    FORBIDDEN = re.compile(r"(?i:pilot/|srv1|/home/|claude|bfme2-ops|bfme2-runner|next2|coordinator|\bseat\b|"
                           r"[\w.+-]+@(?!users\.noreply\.github\.com)[\w-]+\.[a-z]{2,}|\bgate\b)|"
                           r"\b(?:L0\d|L1\d|l0\d|l1\d|bt\d|gen\d+[a-z]?|dd\d|x12|m10|k1\d|f\d\d|h\d\d|ci1|pc1|nb1|ld1|gt1|pub\d)\b")

    def files(self):
        out = [p for p in NIGHTLY.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
        wf = REPO / ".github/workflows/nightly.yml"
        return out + ([wf] if wf.exists() else [])

    def test_no_private_strings(self):
        bad = []
        for p in self.files():
            if p.name in ("test_nightly.py",):
                continue
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                m = self.FORBIDDEN.search(line)
                if m:
                    bad.append(f"{p.name}:{i}: {m.group(0)}")
        self.assertEqual(bad, [])

    def test_workflow_rules(self):
        wf = (REPO / ".github/workflows/nightly.yml")
        if not wf.exists():
            self.skipTest("workflow not beside the package")
        text = wf.read_text()
        self.assertIn("\npermissions: {}\n", text)
        for line in text.splitlines():
            if "uses:" in line:
                self.assertRegex(line, r"uses: [\w-]+/[\w-]+@[0-9a-f]{40}$")
        play = text.split("  link-and-play:")[1].split("\n  publish:")[0]
        self.assertNotIn("github.token", play)
        self.assertNotIn("contents: write", play)
        self.assertIn("persist-credentials: false", play)

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


if __name__ == "__main__":
    unittest.main()
