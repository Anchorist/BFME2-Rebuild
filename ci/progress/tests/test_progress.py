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

ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@users.noreply.invalid",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@users.noreply.invalid",
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

    def build(self, nightly=None, history=()):
        return card.build(self.root, self.state.__getitem__, nightly, list(history))


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
        text = files["PROGRESS.md"].decode()
        self.assertIn("66.7% (100 of 150 bytes)", text)
        self.assertIn("- Starts: not run yet", text)
        self.assertIn("Linking**: `░░░░░░░░░░░░░░░░░░░░` not measured yet", text)
        for key, label, meaning in card.BARS:
            self.assertIn(meaning, text)
        self.assertNotRegex(text.lower(), r"\bgate\b")

    def test_same_inputs_same_bytes(self):
        self.assertEqual(self.build()[0], self.build()[0])

    def test_nightly_and_linking(self):
        nightly = {"sha": "c" * 40, "date": "2026-11-21", "starts": True, "menu": True, "skirmish": False,
                   "simulation_equal": True, "equal_frames": 9000, "save_load": None, "control_caught": True,
                   "provided_required_symbols": [900, 1000]}
        files, _ = self.build(nightly)
        text = files["PROGRESS.md"].decode()
        self.assertIn("- Starts: passed", text)
        self.assertIn("- Plays a skirmish: failed", text)
        self.assertIn("- Equals the original game for 9,000 frames: passed", text)
        self.assertIn("- Saves and loads: not run yet", text)
        self.assertIn("90.0% (900 of 1,000 names)", text)

    def test_drop_is_reported(self):
        before = {"main": "b" * 40, "date": "2000-01-01T00:00:00Z", "matched": [120, 150], "proven": [100, 150],
                  "linking": None, "finished": [1, 2]}
        files, down = self.build(history=[before])
        self.assertEqual(len(down), 1)
        self.assertRegex(down[0], r"^Code matched: expected at least 120 .* found 100 ")
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
            "# measured_utc=2026-11-19T15:51:11Z revision=5c48db972b body_checked_against=0a6b4f7e08 left_out_written=54\n"
            "referrers\tstate\trva\tfile\tsymbol\tfirst_referrer\tbody_check\n"
            "59\tplaceholder-owned:MISSING\t0x00401100\t" + TU + "\t?g@Foo@@QAEXXZ\tsrc/x.cpp\tnone-found\n")
        (wl / "unwritten_with_zero_hour_counterpart.tsv").write_text(
            "# measured_utc=2026-11-19T17:52:36Z revision=89dbb655bd body_checked_against=0a6b4f7e08 left_out_written=373\n"
            "rva\tfunction\towner_file\tsize_bytes\tzero_hour_file\tzero_hour_line\tzero_hour_function\treference_kind\tlink_referrers\tready_at_snapshot\tbody_check\n"
            "0x00401100\tFoo::g\t" + TU + "\t50\t" + worklists.DONOR + "Foo.cpp\t12\tFoo::g\tdef\t3\tyes\tnone-found\n")
        out = Path(self.tmp.name) / "in"
        out.mkdir()
        worklists.inputs(self.root, self.main, self.state.__getitem__, out)
        ranked = (out / "ranked.tsv").read_text().splitlines()
        self.assertEqual(ranked[0], "# generated=2026-11-19T15:51:11Z standalone=5c48db972b")
        self.assertEqual(ranked[2].split("\t")[:3], ["59", "placeholder-owned:MISSING", "0x00401100"])
        unwritten = (out / "unwritten.tsv").read_text().splitlines()
        self.assertEqual(unwritten[0], "# generated 2026-11-19T17:52:36Z main=89dbb655bd")
        self.assertEqual(unwritten[2].split("\t")[4], "Foo.cpp:12,def")
        verdicts = json.loads((out / "verdicts.json").read_text())
        self.assertEqual(verdicts["tus"][TU]["rows"]["0x401100"], ["PARTIAL", 40.0])
        with self.assertRaisesRegex(Refused, r"expected the state of main"):
            worklists.inputs(self.root, "f" * 40, self.state.__getitem__, out)


class BranchTests(Tiny):
    def test_write_is_deterministic_and_idempotent(self):
        out = Path(self.tmp.name) / "out"
        out.mkdir()
        (out / "PROGRESS.md").write_text("x\n")
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
        self.assertNotIn("workflow_run", text)
        caller = (ROOT / ".github/workflows/state-publish.yml").read_text()
        self.assertIn("uses: ./.github/workflows/progress.yml", caller)
        self.assertIn("needs.publish.outputs.new == 'true'", caller)
        self.assertIn("github.event.workflow_run.conclusion != 'cancelled'", caller)
        WriteJobs.assert_main_only(self, text, "progress.yml")
        self.assertIn("name: Publish main state", (ROOT / ".github/workflows/state-publish.yml").read_text())


if __name__ == "__main__":
    unittest.main()
