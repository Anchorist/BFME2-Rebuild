"""Offline tests for the progress card, the worklist inputs and the progress branch.

Run from the repository root:  python3 -B -m unittest discover -s ci/progress/tests -v
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))

import branch  # noqa: E402
import card  # noqa: E402
import worklists  # noqa: E402
sys.path.insert(0, str(ROOT / "ci/state/tests"))
from test_state import WriteJobs  # noqa: E402
from layout import Refused, split  # noqa: E402

ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@users.noreply.github.com",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@users.noreply.github.com",
       "GIT_AUTHOR_DATE": "1763600000 +0000", "GIT_COMMITTER_DATE": "1763600000 +0000",
       "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
TU = "src/Code/GameEngine/Source/Common/Foo.cpp"


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                          env=os.environ | ENV, check=True).stdout.strip()


class Tiny(unittest.TestCase):
    """One source file owning two functions of class Foo, declared in a real header."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "main"
        files = {
            "config/map.json": json.dumps({"objects": [{"object_id": "O1", "tu": TU}], "rows": [
                {"rva": "0x00401000", "size": 100, "role": "owned", "object": "O1", "name": "?f@Foo@@QAEXXZ"},
                {"rva": "0x00401100", "size": 50, "role": "owned", "object": "O1", "name": "?g@Foo@@QAEXXZ"}]}),
            "include/Foo.h": "class Foo {\npublic:\n  void f();\n  void g();\n};\n",
            TU: '#include "Foo.h"\nvoid Foo::f() {}\n',
            "expected/Code/GameEngine/Source/Common/Foo.cpp.json": "{}\n",
        }
        for rel, text in files.items():
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_text(text)
        git(self.root.parent, "init", "-q", "-b", "main", str(self.root))
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "tiny")
        self.main = git(self.root, "rev-parse", "HEAD")
        tree = git(self.root, "rev-parse", "HEAD^{tree}")
        snap = {"schema": 1, "sha": self.main, "checker": "a" * 64, "tus": {TU: {
            "rows": {"0x00401000": ["MATCH", 100], "0x00401100": ["PARTIAL", 40.0]},
            "proven": ["0x00401000"], "verified": False, "error": False, "gate_sha256": []}}}
        self.state = split(snap, tree)

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, nightly=None, history=(), game=None):
        return card.build(self.root, self.state.__getitem__, nightly, list(history), game)


class CardTests(Tiny):
    def test_figures_follow_the_definitions(self):
        files, down = self.build()
        point = json.loads(files["card.json"])
        self.assertEqual(point["matched"], [100, 150])
        self.assertEqual(point["proven"], [100, 150])
        self.assertEqual(point["finished"], [1, 2])
        self.assertIsNone(point["linking"])
        self.assertEqual(point["subsystems"], {"GameEngine / Common": [100, 150]})
        self.assertEqual(down, [])
        text = files["README.md"].decode()
        self.assertIn("66.7% (100 of 150 bytes)", text)
        self.assertIn("- Starts: not run yet", text)
        self.assertIn("Linking**: `░░░░░░░░░░░░░░░░░░░░` not measured yet", text)
        for key, label, meaning in card.BARS:
            self.assertIn(meaning, text)
        self.assertNotRegex(text.lower(), r"\bgate\b")

    def test_same_inputs_same_bytes(self):
        self.assertEqual(self.build()[0], self.build()[0])

    def test_nightly_and_linking(self):
        nightly = {"sha": "c" * 40, "date": "2001-01-04", "starts": True, "menu": True, "skirmish": False,
                   "simulation_equal": True, "equal_frames": 9000, "save_load": None, "control_caught": True,
                   "provided_required_symbols": [900, 1000]}
        files, _ = self.build(nightly)
        text = files["README.md"].decode()
        self.assertIn("- Starts: passed", text)
        self.assertIn("- Plays a skirmish: failed", text)
        self.assertIn("- Equals the original game for 9,000 frames: passed", text)
        self.assertIn("- Saves and loads: not run yet", text)
        self.assertIn("90.0% (900 of 1,000 names)", text)

    def test_partial_night_reads_plainly(self):
        """A night whose game run is not live yet, in the shape the nightly workflow writes."""
        nightly = {"schema": "bfme2-nightly/1", "sha": "d" * 40, "date": "2001-01-04", "result": "partial",
                   "compile": {"compiled": 3253, "files": 3253, "fully_matching": 407},
                   "stages": {"compile": "success", "link_and_play": "not live"},
                   "starts": None, "menu": None, "skirmish": None, "simulation_equal": None, "save_load": None,
                   "control_caught": None, "equal_frames": None, "provided_required_symbols": None}
        text = self.build(nightly)[0]["README.md"].decode()
        self.assertIn("(4 January 2001): Compiles; the game run is not live yet (3,253 of 3,253 source files "
                      "compile, 407 of them match the original completely).", text)
        self.assertIn("- Starts: not run yet", text)
        self.assertNotIn("Warning", text)

    def test_reader_facing_text(self):
        text = self.build()[0]["README.md"].decode()
        self.assertTrue(text.startswith("# Battle for Middle-earth II rebuild: progress\n"))
        self.assertRegex(text, r"Measured \*\*\d{1,2} [A-Z][a-z]+ \d{4}\*\*\. The code figures describe commit ")
        self.assertIn(f"[`{self.main[:12]}`](https://github.com/Open-BFME/BFME2-Rebuild/commit/{self.main})", text)
        self.assertIn("Counted in functions, not bytes", text)
        self.assertNotRegex(text, r"\b(checker|unk|Unplaced|PROGRESS)\b")
        self.assertEqual(card.PART_NAMES["unk"], "Not yet placed in a named file")
        self.assertEqual(card.human_date("2001-02-03"), "3 February 2001")
        self.assertIn("| Game engine: Common | 66.7% (100 of 150 bytes) |", text)

    def test_headline_order_date_and_picture(self):
        files = self.build({"sha": "e" * 40, "date": "2030-01-09", "result": "partial",
                            "provided_required_symbols": [7, 10]})[0]
        text = files["README.md"].decode()
        self.assertLess(text.index("**Byte match**"), text.index("**Linking**"))
        self.assertLess(text.index("**Linking**"), text.index("**Code proven**"))
        self.assertIn("Measured **9 January 2030**.", text)  # the nightly is newer than the commit
        self.assertIn("70.0% (7 of 10 names)", text)
        svg = files["detail.svg"].decode()
        self.assertIn("Measured 9 January 2030", svg)
        self.assertLess(svg.index(">Byte match<"), svg.index(">Linking<"))
        self.assertIn('font-size="24" font-weight="600">Byte match<', svg)
        self.assertIn('font-size="19" font-weight="600">Code proven<', svg)
        self.assertIn("prefers-color-scheme: dark", svg)
        self.assertIn('<rect class="bg"', svg)
        plain = self.build()[0]
        self.assertIn("Not measured yet: the daily build will report this figure.\n", plain["README.md"].decode())
        self.assertNotIn("links the game", plain["README.md"].decode())
        # The nightly measured another commit: its Linking value is attributed to that build.
        self.assertIn(f"Measured by the daily build of commit [`{'e' * 12}`]", text)
        self.assertIn("(9 January 2030), which can be newer or older", text)
        self.assertIn("| 70.00% (build `eeeeeee`) |", text)
        self.assertIn("7 of 10 names · daily build of 9 January 2030", svg)
        point = json.loads(files["card.json"])
        self.assertEqual(point["linking_main"], "e" * 40)
        # Same commit: no build label in the history table.
        same = self.build({"sha": self.main, "date": "2030-01-09", "result": "partial",
                           "provided_required_symbols": [7, 10]})[0]["README.md"].decode()
        self.assertNotIn("(build `", same)
        self.assertIn(">not measured yet<", plain["detail.svg"].decode())

    def test_front_picture_is_the_approved_design(self):
        """Same numbers, same bytes as the approved README design."""
        made = card.design.card(25.7, (5137, 8267), (10054, 41565), 366, "20 Nov 2026")
        self.assertEqual(made, (HERE / "design-reference.svg").read_text(encoding="utf-8"))

    def test_front_picture_from_measurements(self):
        files = self.build()[0]
        svg = files["progress.svg"].decode()
        self.assertIn(">BYTE MATCH<", svg)
        self.assertIn(">66.7%<", svg)
        self.assertIn("not measured yet; the daily build will report it", svg)
        self.assertIn("inside the original game (not run yet)", svg)
        self.assertIn(">1<", svg)  # functions finished
        self.assertIn("· measured by machine, daily at noon ET", svg)
        self.assertIn("prefers-color-scheme: light", svg)
        self.assertIn("Byte match", files["detail.svg"].decode())
        # No nightly: the state's file count is never shown as files compiled.
        self.assertIn('x="592" y="286" font-size="24" font-weight="700">—</text>', svg)
        self.assertIn("compared with the game every day (not run yet)", svg)
        night = {"sha": "f" * 40, "date": "2030-01-09", "result": "pass", "simulation_equal": True,
                 "files_substituted": 366, "compile": {"compiled": 3253, "files": 3253, "fully_matching": 407},
                 "provided_required_symbols": [5137, 8267]}
        # The nightly's own game fields are not the source of the identical-files figure any more.
        svg = self.build(night)[0]["progress.svg"].decode()
        self.assertIn(">62.1%<", svg)
        self.assertIn("of the names a full game needs: 5,137 of 8,267", svg)
        self.assertIn("inside the original game (not run yet)", svg)
        self.assertIn('font-weight="700">3,253</text>', svg)
        self.assertIn("9 Jan 2030 · measured by machine", svg)
        game = self.game(date="2030-01-08")
        svg = self.build(night, game=game)[0]["progress.svg"].decode()
        self.assertIn('font-weight="700">366</text>', svg)
        self.assertIn("in the game, run privately 8 Jan 2030", svg)

    def game(self, **change):
        # The shape the nightly's result.py game_record() writes (schema bfme2-nightly-game/1).
        record = {"schema": "bfme2-nightly-game/1", "sha": self.main, "date": "2030-01-08", "public_run_id": 123,
                  "run_url": "https://github.com/Open-BFME/BFME2-Rebuild/actions/runs/123",
                  "files_substituted": 366, "functions": 6187, "starts": True, "menu": True, "skirmish": True,
                  "simulation_equal": True, "equal_frames": 9000, "save_load": True, "control_caught": True,
                  "result": "pass", "headline": "plays", "image_sha256": "0" * 64,
                  "tests": {"skirmish": {"status": "pass", "frames_compared": 9000, "frames_equal": 9000,
                                         "first_divergent_frame": None}}}
        record.update(change)
        return record

    def test_linking_unit_follows_the_daily_build(self):
        night = {"sha": "f" * 40, "date": "2030-01-09", "result": "partial", "linking_unit": "functions",
                 "provided_required_symbols": [14358, 41565]}
        files = self.build(night)[0]
        self.assertIn("of the functions a full game needs: 14,358 of 41,565", files["progress.svg"].decode())
        self.assertIn("34.5% (14,358 of 41,565 functions)", files["README.md"].decode())
        self.assertIn("functions our compiled source already supplies", files["README.md"].decode())
        night["linking_unit"] = "anything else"
        self.assertIn("of the names a full game needs", self.build(night)[0]["progress.svg"].decode())

    def test_failed_night_keeps_the_last_measured_linking(self):
        failed = {"sha": "d" * 40, "date": "2030-01-10", "result": "fail", "run_id": 9,
                  "provided_required_symbols": None}
        older = {"sha": "e" * 40, "date": "2030-01-09", "result": "partial", "run_id": 8,
                 "provided_required_symbols": [5181, 8317]}
        files = card.build(self.root, self.state.__getitem__, failed, [], None, older)[0]
        svg = files["progress.svg"].decode()
        self.assertIn("of the names a full game needs: 5,181 of 8,317", svg)
        text = files["README.md"].decode()
        self.assertIn(f"Measured by the daily build of commit [`{'e' * 12}`]", text)
        self.assertIn("(9 January 2030)", text)
        self.assertIn("The nightly build failed", text)  # the failed night is still reported as failed
        # A newer valid pair wins over the older record.
        fresh = dict(failed, result="partial", provided_required_symbols=[5200, 8317])
        self.assertIn("5,200 of 8,317", card.build(self.root, self.state.__getitem__, fresh, [], None,
                                                    older)[0]["progress.svg"].decode())
        # No pair anywhere: the honest dash.
        self.assertIn("not measured yet", card.build(self.root, self.state.__getitem__, failed, [], None,
                                                      None)[0]["progress.svg"].decode())

    def test_carried_linking_is_credited_to_its_own_build(self):
        """Nightly r10 shape: a run that measured no pair carries the last good one with linking_measured."""
        carried = {"sha": "d" * 40, "date": "2030-01-10", "result": "fail", "run_id": 9,
                   "provided_required_symbols": [5181, 8317], "linking_unit": "names",
                   "linking_measured": {"this_run": False, "reason": "this run measured no linking figure",
                                        "sha": "e" * 40, "date": "2030-01-09",
                                        "run_url": "https://github.com/Open-BFME/BFME2-Rebuild/actions/runs/8"}}
        files = self.build(carried)[0]
        text = files["README.md"].decode()
        self.assertIn(f"Measured by the daily build of commit [`{'e' * 12}`]", text)
        self.assertIn("(9 January 2030)", text)
        self.assertNotIn(f"Measured by the daily build of commit [`{'d' * 12}`]", text)
        self.assertIn("5,181 of 8,317", files["progress.svg"].decode())
        self.assertEqual(json.loads(files["card.json"])["linking_main"], "e" * 40)
        # Measured this run: credited to this run.
        fresh = dict(carried, linking_measured={"this_run": True, "sha": "d" * 40, "date": "2030-01-10"})
        self.assertIn(f"commit [`{'d' * 12}`]", self.build(fresh)[0]["README.md"].decode().split("Measured by the daily build of ")[1][:30])
        # Carried without its own identity: not shown.
        bare = dict(carried, linking_measured={"this_run": False, "reason": "x"})
        self.assertIn("not measured yet", self.build(bare)[0]["progress.svg"].decode())

    def test_game_record_rule(self):
        night = {"sha": "f" * 40, "date": "2030-01-10", "result": "partial",
                 "stages": {"compile": "success", "link_and_play": "runs separately"}}
        files = self.build(night, game=self.game())[0]
        text = files["README.md"].decode()
        self.assertIn("Game run on a private machine (the game's files cannot be published) on 8 January 2030, "
                      f"with the objects built from commit [`{self.main[:12]}`]", text)
        self.assertIn("by [the public nightly run](https://github.com/Open-BFME/BFME2-Rebuild/actions/runs/123)", text)
        self.assertIn(": 366 rebuilt files (6,187 functions) play identically inside the original game.", text)
        self.assertIn("- Starts: passed", text)
        self.assertIn("- Equals the original game for 9,000 frames: passed", text)
        self.assertIn("Compiles; the game is run separately.", text)
        point = json.loads(files["card.json"])
        self.assertTrue(point["game"]["shown"])
        cases = [({"simulation_equal": False}, "differs from the original"),
                 ({"simulation_equal": None}, "not run yet"),
                 ({"control_caught": False}, "control run not caught"),
                 ({"sha": "a" * 40}, "commit not on main"),
                 ({"date": "2030-01-01"}, "last run 9 days ago")]
        for change, reason in cases:
            files = self.build(night, game=self.game(**change))[0]
            svg = files["progress.svg"].decode()
            self.assertIn(f"inside the original game ({reason})", svg, reason)
            self.assertIn(f"the identical-files figure is not shown ({reason})", files["README.md"].decode())
            self.assertNotIn('font-weight="700">366</text>', svg)
        self.assertIsNone(json.loads(self.build(night, game={"sha": "x"})[0]["card.json"])["game"])
        # Only run_url, or a foreign URL: the link follows run_url only when it is this repository's run.
        only_url = self.game()
        del only_url["public_run_id"]
        self.assertIn("by [the public nightly run](https://github.com/Open-BFME/BFME2-Rebuild/actions/runs/123)",
                      self.build(night, game=only_url)[0]["README.md"].decode())
        only_url["run_url"] = "https://example.invalid/actions/runs/123"
        self.assertNotIn("by [the public nightly run]", self.build(night, game=only_url)[0]["README.md"].decode())

    def test_drop_is_reported(self):
        before = {"main": "b" * 40, "date": "2000-01-01T00:00:00Z", "matched": [120, 150], "proven": [100, 150],
                  "linking": None, "finished": [1, 2]}
        files, down = self.build(history=[before])
        self.assertEqual(len(down), 1)
        self.assertRegex(down[0], r"^Byte match: expected at least 120 .* found 100 ")
        self.assertEqual(len(json.loads(files["history.json"])), 2)

    def test_corrupt_state_is_refused(self):
        path = "files/" + TU + ".json"
        self.state[path] = self.state[path] + b" "
        with self.assertRaisesRegex(Refused, r"expected .* to hash to"):
            self.build()


class WorklistInputTests(Tiny):
    def test_inputs_round_trip(self):
        wl = self.root / "worklist"
        wl.mkdir()
        (wl / "link_ranked.tsv").write_text(
            "# measured_utc=2001-01-02T15:51:11Z revision=5c48db972b body_checked_against=0a6b4f7e08 left_out_written=54\n"
            "referrers\tstate\trva\tfile\tsymbol\tfirst_referrer\tbody_check\n"
            "59\tplaceholder-owned:MISSING\t0x00401100\t" + TU + "\t?g@Foo@@QAEXXZ\tsrc/x.cpp\tnone-found\n")
        (wl / "unwritten_with_zero_hour_counterpart.tsv").write_text(
            "# measured_utc=2001-01-02T17:52:36Z revision=89dbb655bd body_checked_against=0a6b4f7e08 left_out_written=373\n"
            "rva\tfunction\towner_file\tsize_bytes\tzero_hour_file\tzero_hour_line\tzero_hour_function\treference_kind\tlink_referrers\tready_at_snapshot\tbody_check\n"
            "0x00401100\tFoo::g\t" + TU + "\t50\t" + worklists.DONOR + "Foo.cpp\t12\tFoo::g\tdef\t3\tyes\tnone-found\n")
        out = Path(self.tmp.name) / "in"
        out.mkdir()
        worklists.inputs(self.root, self.main, self.state.__getitem__, out)
        ranked = (out / "ranked.tsv").read_text().splitlines()
        self.assertEqual(ranked[0], "# generated=2001-01-02T15:51:11Z standalone=5c48db972b")
        self.assertEqual(ranked[2].split("\t")[:3], ["59", "placeholder-owned:MISSING", "0x00401100"])
        unwritten = (out / "unwritten.tsv").read_text().splitlines()
        self.assertEqual(unwritten[0], "# generated 2001-01-02T17:52:36Z main=89dbb655bd")
        self.assertEqual(unwritten[2].split("\t")[4], "Foo.cpp:12,def")
        verdicts = json.loads((out / "verdicts.json").read_text())
        self.assertEqual(verdicts["tus"][TU]["rows"]["0x401100"], ["PARTIAL", 40.0])
        with self.assertRaisesRegex(Refused, r"expected the state of main"):
            worklists.inputs(self.root, "f" * 40, self.state.__getitem__, out)


class LastLinkingTests(unittest.TestCase):
    def test_newest_record_with_a_pair(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "n"
        (root / "history").mkdir(parents=True)
        records = {"2030-01-08-aaaaaaaaaaaa.json": {"run_id": 7, "provided_required_symbols": [1, 2]},
                   "2030-01-09-bbbbbbbbbbbb.json": {"run_id": 8, "provided_required_symbols": [3, 4]},
                   "2030-01-10-cccccccccccc.json": {"run_id": 9, "provided_required_symbols": None},
                   "2030-01-10-dddddddddddd.json": {"run_id": "x", "provided_required_symbols": [5, 6]},
                   "2030-01-11-eeeeeeeeeeee.json": [],
                   "2030-01-11-ffffffffffff.json": "not a record",
                   "2030-01-12-000000000000.json": {"run_id": {"nested": 1}, "provided_required_symbols": [7, 8]}}
        for name, record in records.items():
            (root / "history" / name).write_text(json.dumps(record))
        git(root.parent, "init", "-q", "-b", "nightly", str(root))
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "n")
        repo = branch.store.Git(root / ".git", str(root))
        (root / "history" / "2030-01-11-gggggggggggg.json").write_text("{not json")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "broken")
        found = json.loads(branch.last_linking(repo, "HEAD"))  # malformed records are skipped, never fatal
        self.assertEqual(found["run_id"], 8)
        latest = Path(tmp.name) / "latest.json"
        latest.write_text(json.dumps({"provided_required_symbols": [1, 2]}))
        self.assertTrue(branch.latest_has_pair(latest))
        for bad in ("[]", "{}", "{not json", json.dumps({"provided_required_symbols": None})):
            latest.write_text(bad)
            self.assertFalse(branch.latest_has_pair(latest), bad)
        self.assertFalse(branch.latest_has_pair(Path(tmp.name) / "absent.json"))
        # A nightly commit with no history/ at all gives nothing.
        (root / "history" / "2030-01-08-aaaaaaaaaaaa.json").unlink()
        git(root, "rm", "-q", "-r", "history")
        git(root, "commit", "-q", "-m", "empty")
        self.assertIsNone(branch.last_linking(repo, "HEAD"))


class CensusInputTests(Tiny):
    def test_census_rows_map_to_owner_and_verdict(self):
        census = Path(self.tmp.name) / "link-missing.tsv"
        census.write_text("# link census of " + "c" * 40 + " on 2030-01-09 objects=1 missing=3\n"
                          "symbol\treferrers\tfirst_referrer\n"
                          "?g@Foo@@QAEXXZ\t5\tsrc/x.cpp\n"
                          "?h@Bar@@QAEXXZ\t2\tsrc/y.cpp\n"
                          "_plain\t1\tsrc/z.c\n")
        first, rows, counts = worklists.ranked_from_census(census, self.root, card.join(self.state.__getitem__))
        self.assertEqual(first, "# generated=2030-01-09 standalone=" + "c" * 40)
        self.assertEqual(rows, [["5", "owned:PARTIAL", "0x00401100", TU, "?g@Foo@@QAEXXZ", "src/x.cpp"]])
        self.assertEqual(counts, {"names": 3, "mapped": 1, "no_owner": 2, "two_owners": 0})
        census.write_text("# something else\nsymbol\treferrers\tfirst_referrer\n")
        with self.assertRaisesRegex(Refused, r"expected a first line '# link census of"):
            worklists.ranked_from_census(census, self.root, card.join(self.state.__getitem__))


class BranchTests(Tiny):
    def test_write_is_deterministic_and_idempotent(self):
        out = Path(self.tmp.name) / "out"
        out.mkdir()
        (out / "README.md").write_text("x\n")
        commits = []
        for name in ("r1.git", "r2.git"):
            remote = Path(self.tmp.name) / name
            git(self.tmp.name, "init", "-q", "--bare", str(remote))
            commits.append(branch.write(out, self.main, self.root, str(remote), "", out=lambda *_: None))
        self.assertEqual(commits[0], commits[1])
        lines = []
        again = branch.write(out, self.main, self.root, str(Path(self.tmp.name) / "r1.git"), "", out=lines.append)
        self.assertEqual(again, commits[0])
        self.assertIn("Unchanged", lines[0])


class WorkflowRules(unittest.TestCase):
    def test_rules(self):
        text = (ROOT / ".github/workflows/progress.yml").read_text()
        self.assertRegex(text, r"(?m)^permissions: \{\}$")
        for line in re.findall(r"uses: (\S+)", text):
            self.assertRegex(line, r"@[0-9a-f]{40}$")
        self.assertNotIn("secrets.", text)
        self.assertNotIn("pull_request", text)
        self.assertNotRegex(text.lower(), r"\bgate\b")
        self.assertEqual(set(re.findall(r"persist-credentials: (\S+)", text)), {"false"})
        self.assertIn("  workflow_call:\n", text)
        self.assertIn('workflow_run:\n    workflows: ["Nightly build and compare"]\n'
                      '    types: [completed]\n    branches: [main]\n', text)
        self.assertIn("    - cron: '37 17 * * *'\n", text)
        caller = (ROOT / ".github/workflows/state-publish.yml").read_text()
        self.assertIn("uses: ./.github/workflows/progress.yml", caller)
        self.assertIn("needs.publish.outputs.new == 'true'", caller)
        self.assertIn("github.event.workflow_run.conclusion != 'cancelled'", caller)
        WriteJobs.assert_main_only(self, text, "progress.yml")
        self.assertIn("name: Publish main state", (ROOT / ".github/workflows/state-publish.yml").read_text())


if __name__ == "__main__":
    unittest.main()
