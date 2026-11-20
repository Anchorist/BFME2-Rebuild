"""Offline tests for the landing job, driven by captured read-only GitHub API payloads.

fixtures/live-pr2-pr3.json holds the open pull requests 2 to 7 as GitHub returned them
on 2026-11-20 (trimmed to the fields the lander reads) while main was 89db7cafe448,
plus the three receipts pull request 2's checks produced on main 879a5be4f21d.
Run from the repository root:  python3 -m unittest discover -s ci/landing/tests -v
"""
import copy
import io
import json
import os
from contextlib import redirect_stdout
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ci/landing"))
import lander  # noqa: E402
from api import Api, ReadOnly  # noqa: E402

FIXTURE = json.loads((Path(__file__).parent / "fixtures/live-pr2-pr3.json").read_text())
LIVE_MAIN = FIXTURE["main"]                              # main when captured; PR 2 is stale on it
MEASURED = "879a5be4f21dfdcabe5fef6e73d2b6a01fd77f94"    # main PR 2 and PR 3 were measured on
PR2 = "7eb1cdbb67eb375af71626adfc89f05b72c9b393"
PR3 = "e0cd7fef8dd4"
TREE = "44fa7dfb9e1d25379e7c64aa22069d5e03770223"
NEW = "ab" * 20
CONFIG = {"approvers": set(), "exceptions": {(2, PR2)}, "remeasure": "repository_dispatch"}


class FakeApi(Api):
    def __init__(self, live, main=LIVE_MAIN, edit=None):
        self._token, self.live, self.writes = "x" * 20, live, []
        self.fx = copy.deepcopy(FIXTURE["api"])
        self.fx["git/ref/heads/main"] = {"object": {"sha": main}}
        self.responses = {}
        self.after_write = {}
        self.after_read = []
        if edit:
            edit(self.fx)

    def _send(self, method, path, body):
        if method == "GET":
            if self.after_read:
                self.after_read.pop(0)(self.fx)
            if path in self.fx:
                return 200, copy.deepcopy(self.fx[path])
            if path.startswith("git/commits/"):
                return 200, {"sha": path[12:], "message": "An ordinary commit\n", "parents": [], "tree": {"sha": "0" * 40}}
            if path.startswith("commits/") and "/statuses" in path:
                return 200, []
            return 404, {"message": "Not Found"}
        key = (method, path.split("/")[0] if method == "POST" else path)
        code, payload = self.responses.get(key, ({"POST": 201, "PUT": 200}[method], {}))
        if path == "dispatches":
            code = 204
        hook = self.after_write.get(key)
        if hook:
            hook(self.fx)
        return code, payload


def env(main=MEASURED, mode="dry-run", pr="", run="1"):
    return {"GITHUB_REPOSITORY": "Open-BFME/BFME2-Rebuild", "GITHUB_REPOSITORY_ID": "1464323350",
            "GITHUB_REF": "refs/heads/main", "GITHUB_SHA": main, "BFME_LANDING_MODE": mode,
            "BFME_LANDING_PR": pr, "GITHUB_RUN_ID": run}


def put_receipts(directory, drop_inline=False):
    for name, record in FIXTURE["receipts"].items():
        if drop_inline and name.startswith("inline/"):
            continue
        path = Path(directory, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record))


def receipts_match_checkout():
    """The real receipts carry the policy digests of ci/managed-check and tools/gates at 879a5be4."""
    inline = FIXTURE["receipts"]["inline/inline-status.json"]["policy_sha256"]
    return lander.lr.policy() == inline


def quiet(fn, *args, **kwargs):
    with redirect_stdout(io.StringIO()) as out:
        result = fn(*args, **kwargs)
    return result, out.getvalue()


class Select(unittest.TestCase):
    def test_dry_run_over_all_open_pull_requests_on_the_captured_main(self):
        api = FakeApi(live=False)
        with tempfile.TemporaryDirectory() as tmp:
            code, out = quiet(lander.run, ["select", tmp + "/w"], env(main=LIVE_MAIN), api=api, config=CONFIG)
        self.assertEqual(code, 0)
        self.assertEqual(api.writes, [])
        self.assertIn("Would send repository_dispatch bfme-remeasure for #2 head 7eb1cdbb67eb on main 89db7cafe448", out)
        for number in (3, 4, 5, 6, 7):
            self.assertRegex(out, rf"\| #{number} \|.*Held: refused-branch")

    def test_pull_request_2_measured_on_current_main_is_the_candidate(self):
        api = FakeApi(live=False, main=MEASURED)
        decision = lander.evaluate(api, 2, MEASURED, CONFIG)
        self.assertEqual((decision["stage"], decision["reasons"], decision["inline"]), ("land", [], "success"))

    def test_pull_request_3_is_held_with_named_reasons(self):
        api = FakeApi(live=False, main=MEASURED)
        decision = lander.evaluate(api, 3, MEASURED, CONFIG)
        codes = [item.code for item in decision["reasons"]]
        self.assertEqual(decision["stage"], "hold")
        self.assertEqual(codes[0], "refused-branch")
        self.assertIn("check-failure", codes)
        self.assertEqual(decision["checks"][lander.BOAT], "fresh-failure")
        self.assertEqual(decision["checks"][lander.INLINE], "pending")

    def test_rehearsal_branch_is_refused_without_its_exact_exception(self):
        api = FakeApi(live=False, main=MEASURED)
        decision = lander.evaluate(api, 2, MEASURED, CONFIG | {"exceptions": set()})
        self.assertEqual(decision["reasons"][0].code, "refused-branch")
        decision = lander.evaluate(api, 2, MEASURED, CONFIG | {"exceptions": {(2, "0" * 40)}})
        self.assertEqual(decision["reasons"][0].code, "refused-branch")

    def test_superseded_run_does_nothing(self):
        api = FakeApi(live=True, main=LIVE_MAIN)
        with tempfile.TemporaryDirectory() as tmp:
            code, out = quiet(lander.run, ["select", tmp + "/w"], env(main=MEASURED, mode="live"), api=api, config=CONFIG)
        self.assertEqual((code, api.writes), (0, []))
        self.assertIn("Superseded", out)

    def test_header_change_needs_a_listed_approver(self):
        def header(fx):
            fx["pulls/2/files?per_page=100&page=1"].append({"filename": "include/GameLogic/Object.h", "status": "modified"})
        api = FakeApi(live=False, main=MEASURED, edit=header)
        decision = lander.evaluate(api, 2, MEASURED, CONFIG)
        self.assertEqual(decision["reasons"][0].code, "header-approvers-empty")
        decision = lander.evaluate(api, 2, MEASURED, CONFIG | {"approvers": {99}})
        self.assertEqual(decision["reasons"][0].code, "header-approval")
        api.fx["pulls/2/reviews?per_page=100&page=1"] = [
            {"id": 5, "user": {"id": 99}, "state": "APPROVED", "commit_id": "0" * 40},
            {"id": 6, "user": {"id": 99}, "state": "APPROVED", "commit_id": PR2}]
        decision = lander.evaluate(api, 2, MEASURED, CONFIG | {"approvers": {99}})
        self.assertEqual((decision["stage"], decision["reasons"]), ("land", []))
        author = api.fx["pulls/2"]["user"]["id"]
        api.fx["pulls/2/reviews?per_page=100&page=1"] = [
            {"id": 7, "user": {"id": author}, "state": "APPROVED", "commit_id": PR2}]
        decision = lander.evaluate(api, 2, MEASURED, CONFIG | {"approvers": {author}})
        self.assertEqual(decision["reasons"][0].code, "header-approval")

    def test_workflow_change_is_refused(self):
        def wf(fx):
            fx["pulls/2/files?per_page=100&page=1"].append({"filename": ".github/workflows/x.yml", "status": "added"})
        decision = lander.evaluate(FakeApi(live=False, main=MEASURED, edit=wf), 2, MEASURED, CONFIG)
        self.assertEqual(decision["reasons"][0].code, "workflow-change")

    def test_failed_landing_on_main_stops_everything(self):
        def failed(fx):
            fx[f"commits/{MEASURED}/statuses?per_page=100&page=1"] = [
                {"id": 1, "context": lander.LANDING_CONTEXT, "state": "failure", "description": "x",
                 "creator": {"id": lander.lr.BOT_ID}}]
        api = FakeApi(live=True, main=MEASURED, edit=failed)
        with self.assertRaises(lander.Failed) as caught, tempfile.TemporaryDirectory() as tmp:
            lander.run(["select", tmp + "/w"], env(mode="live"), api=api, config=CONFIG)
        self.assertEqual(caught.exception.code, "main-unverified")

    def test_inline_virtual_policy(self):
        def pending(fx):
            for item in fx[f"commits/{PR2}/statuses?per_page=100&page=1"]:
                if item["context"] == lander.INLINE:
                    item["state"], item["description"] = "pending", "Waiting for admitted inline-virtual evidence"
        api = FakeApi(live=False, main=MEASURED, edit=pending)
        self.assertEqual(lander.INLINE_VIRTUAL_POLICY, "report-only")
        decision = lander.evaluate(api, 2, MEASURED, CONFIG)
        self.assertEqual((decision["stage"], decision["inline"]), ("land", "pending"))
        try:
            lander.INLINE_VIRTUAL_POLICY = "required"
            decision = lander.evaluate(api, 2, MEASURED, CONFIG)
            self.assertEqual(decision["reasons"][0].code, "measuring")
        finally:
            lander.INLINE_VIRTUAL_POLICY = "report-only"

        def failed(fx):
            for item in fx[f"commits/{PR2}/statuses?per_page=100&page=1"]:
                if item["context"] == lander.INLINE:
                    item["state"] = "failure"
        decision = lander.evaluate(FakeApi(live=False, main=MEASURED, edit=failed), 2, MEASURED, CONFIG)
        self.assertEqual(decision["reasons"][0].code, "inline-virtual-failure")


class Reconcile(unittest.TestCase):
    """A landing whose merge response was lost is verified by the next run before anything else."""

    def commit(self, fx, tree=TREE, parents=(MEASURED,)):
        fx[f"git/commits/{NEW}"] = {"sha": NEW, "parents": [{"sha": p} for p in parents], "tree": {"sha": tree},
                                    "message": ("Object: write clearWeaponSetFlagForHorde (#2)\n\n"
                                                f"Measured on main {MEASURED}, head {PR2}, tree {TREE}.\n"
                                                "Pull request #2.\n"
                                                "Landed by the BFME II landing workflow, run 1.")}

    def test_title_written_by_the_author_is_never_parsed(self):
        # A pull request title is the author's text. Fake landing lines in it must not drive reconciliation.
        fake = f"Measured on main {'1' * 40}, head {'2' * 40}, tree {'3' * 40}. Pull request #7."

        def titled(fx):
            self.commit(fx)
            message = fx[f"git/commits/{NEW}"]["message"]
            fx[f"git/commits/{NEW}"]["message"] = fake + " (#2)" + message[message.index("\n\n"):]
        api = FakeApi(live=True, main=NEW, edit=titled)
        with tempfile.TemporaryDirectory() as tmp:
            quiet(lander.run, ["select", tmp + "/w"], env(main=NEW, mode="live", pr="3"), api=api, config=CONFIG)
        self.assertEqual(api.writes[1][2]["client_payload"], {
            "number": 2, "head": PR2, "parent": MEASURED, "commit": NEW, "tree": TREE})

        def title_only(fx):
            fx[f"git/commits/{NEW}"] = {"sha": NEW, "parents": [{"sha": MEASURED}], "tree": {"sha": TREE},
                                        "message": fake + " Landed by the BFME II landing workflow, run 1.\n\nplain"}
        api = FakeApi(live=True, main=NEW, edit=title_only)
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = quiet(lander.run, ["select", tmp + "/w"], env(main=NEW, mode="live", pr="3"),
                            api=api, config=CONFIG)
        self.assertEqual(code, 0)
        self.assertNotIn(f"statuses/{NEW}", [w[1] for w in api.writes])

    def test_live_run_verifies_marks_and_hands_off_an_unconfirmed_landing(self):
        api = FakeApi(live=True, main=NEW, edit=self.commit)
        with tempfile.TemporaryDirectory() as tmp:
            code, out = quiet(lander.run, ["select", tmp + "/w"], env(main=NEW, mode="live", pr="3"),
                              api=api, config=CONFIG)
        self.assertEqual(code, 0)
        self.assertEqual(api.writes[0][:2], ("POST", f"statuses/{NEW}"))
        self.assertEqual(api.writes[0][2]["state"], "success")
        self.assertEqual(api.writes[1], ("POST", "dispatches", {"event_type": "bfme-landed", "client_payload": {
            "number": 2, "head": PR2, "parent": MEASURED, "commit": NEW, "tree": TREE}}))
        self.assertIn("Reconciled the earlier landing of #2", out)

    def test_wrong_tree_found_later_stops_landing(self):
        api = FakeApi(live=True, main=NEW, edit=lambda fx: self.commit(fx, tree="ee" * 20))
        with self.assertRaises(lander.Failed) as caught, tempfile.TemporaryDirectory() as tmp:
            quiet(lander.run, ["select", tmp + "/w"], env(main=NEW, mode="live"), api=api, config=CONFIG)
        self.assertEqual(caught.exception.code, "post-merge")
        self.assertEqual(api.writes[0][2]["state"], "failure")
        self.assertNotIn("dispatches", [w[1] for w in api.writes])

    def test_dry_run_reports_and_writes_nothing(self):
        api = FakeApi(live=False, main=NEW, edit=self.commit)
        with self.assertRaises(lander.Held) as caught, tempfile.TemporaryDirectory() as tmp:
            quiet(lander.run, ["select", tmp + "/w"], env(main=NEW), api=api, config=CONFIG)
        self.assertEqual((caught.exception.code, api.writes), ("unreconciled-landing", []))

    def test_already_marked_landing_is_left_alone(self):
        def marked(fx):
            self.commit(fx)
            fx[f"commits/{NEW}/statuses?per_page=100&page=1"] = [
                {"id": 1, "context": lander.LANDING_CONTEXT, "state": "success", "description": "Verified",
                 "creator": {"id": lander.lr.BOT_ID}}]
        api = FakeApi(live=True, main=NEW, edit=marked)
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = quiet(lander.run, ["select", tmp + "/w"], env(main=NEW, mode="live", pr="3"),
                            api=api, config=CONFIG)
        self.assertEqual(code, 0)
        self.assertNotIn(f"statuses/{NEW}", [w[1] for w in api.writes])


class Remeasure(unittest.TestCase):
    def test_live_remeasure_sends_exact_dispatch_and_stops_when_main_moves(self):
        api = FakeApi(live=True, main=LIVE_MAIN)
        ticks = iter(range(0, 100000, 20))
        reads = {"n": 0}

        def move(fx):
            reads["n"] += 1
            if reads["n"] > 30:
                fx["git/ref/heads/main"] = {"object": {"sha": "cd" * 20}}
        api.after_read = [move] * 1000
        with tempfile.TemporaryDirectory() as tmp:
            code, out = quiet(lander.run, ["select", tmp + "/w"], env(main=LIVE_MAIN, mode="live", pr="2"),
                              api=api, config=CONFIG, clock=lambda: next(ticks), sleep=lambda s: None)
        self.assertEqual(code, 0)
        self.assertEqual(api.writes[0], ("POST", "dispatches", {"event_type": "bfme-remeasure", "client_payload": {
            "number": 2, "base": LIVE_MAIN, "head": PR2}}))
        self.assertNotIn("PUT", [w[0] for w in api.writes])
        self.assertIn("main-moved", out)

    def test_remeasure_times_out_with_a_named_reason(self):
        api = FakeApi(live=True, main=LIVE_MAIN)
        ticks = iter(range(0, 10**7, 600))
        with tempfile.TemporaryDirectory() as tmp:
            code, out = quiet(lander.run, ["select", tmp + "/w"], env(main=LIVE_MAIN, mode="live", pr="2"),
                              api=api, config=CONFIG, clock=lambda: next(ticks), sleep=lambda s: None)
        self.assertEqual(code, 0)
        self.assertIn("measurement-timeout", out)
        posted = [w for w in api.writes if w[1] == f"statuses/{PR2}"][-1][2]["description"]
        self.assertIn(f"(main {LIVE_MAIN[:12]})", posted)
        # The next run does not wait on the same pull request again for the same main.
        api.fx[f"commits/{PR2}/statuses?per_page=100&page=1"].insert(0, {
            "id": 10**12, "context": lander.LANDING_CONTEXT, "state": "pending", "description": posted,
            "creator": {"id": lander.lr.BOT_ID}})
        api.writes.clear()
        with tempfile.TemporaryDirectory() as tmp:
            code, out = quiet(lander.run, ["select", tmp + "/w"], env(main=LIVE_MAIN, mode="live", pr="2"),
                              api=api, config=CONFIG, clock=lambda: next(ticks), sleep=lambda s: None)
        self.assertEqual((code, [w for w in api.writes if w[1] == "dispatches"]), (0, []))
        self.assertIn("Nothing to land.", out)

    def test_remeasure_off_names_the_manual_route(self):
        api = FakeApi(live=True, main=LIVE_MAIN)
        with tempfile.TemporaryDirectory() as tmp:
            code, out = quiet(lander.run, ["select", tmp + "/w"], env(main=LIVE_MAIN, mode="live", pr="2"),
                              api=api, config=CONFIG | {"remeasure": "off"})
        self.assertEqual([w for w in api.writes if w[1] == "dispatches"], [])
        self.assertIn("automatic re-measurement is off", out)


@unittest.skipUnless(receipts_match_checkout(), "the captured receipts were produced by ci/managed-check at 879a5be4; "
                     "run these tests in a checkout of that commit plus ci/landing")
class Land(unittest.TestCase):
    def prepare(self, tmp, api, drop_inline=False):
        code, _ = quiet(lander.run, ["select", tmp + "/w"], env(pr="2", mode="live" if api.live else "dry-run"),
                        api=api, config=CONFIG)
        self.assertEqual(code, 0)
        self.assertTrue(Path(tmp, "w/binding.json").is_file())
        put_receipts(tmp + "/w", drop_inline)

    def merged(self, fx):
        fx["git/ref/heads/main"] = {"object": {"sha": NEW}}
        fx[f"git/commits/{NEW}"] = {"sha": NEW, "parents": [{"sha": MEASURED}], "tree": {"sha": TREE}}

    def test_dry_run_verifies_real_receipts_and_merges_nothing(self):
        api = FakeApi(live=False, main=MEASURED)
        with tempfile.TemporaryDirectory() as tmp:
            self.prepare(tmp, api)
            binding = json.loads(Path(tmp, "w/binding.json").read_text())
            self.assertEqual(binding["runs"], {"match": ["44770182794", "1"], "rules": ["44770182973", "1"], "inline": "success"})
            code, out = quiet(lander.run, ["land", tmp + "/w"], env(), api=api, config=CONFIG)
        self.assertEqual((code, api.writes), (0, []))
        self.assertIn("Would merge #2 (squash) with expected head 7eb1cdbb67eb onto main 879a5be4f21d, "
                      "expecting one parent 879a5be4f21d and tree 44fa7dfb9e1d.", out)

    def test_waits_for_a_fresh_status_whose_run_has_not_completed(self):
        # Live trial 2026-11-20 run 44777584236: Boat posted success at 16:55:06, its run completed at 16:55:46.
        api = FakeApi(live=True, main=MEASURED)
        api.fx["actions/runs/44770182794"]["status"] = "in_progress"
        api.fx["actions/runs/44770182794"]["conclusion"] = None
        reads = {"n": 0}

        def complete(fx):
            reads["n"] += 1
            if reads["n"] == 40:
                fx["actions/runs/44770182794"]["status"] = "completed"
                fx["actions/runs/44770182794"]["conclusion"] = "success"
        api.after_read = [complete] * 10000
        ticks = iter(range(0, 10**6, 20))
        with tempfile.TemporaryDirectory() as tmp:
            code, out = quiet(lander.run, ["select", tmp + "/w"], env(pr="2", mode="live"), api=api, config=CONFIG,
                              clock=lambda: next(ticks), sleep=lambda s: None)
            self.assertTrue(Path(tmp, "w/binding.json").is_file())
        self.assertEqual(code, 0)
        self.assertIn("waiting for their runs to complete", out)
        self.assertIn("collecting its receipts", out)

    def test_dry_run_does_not_wait_on_an_incomplete_run(self):
        api = FakeApi(live=False, main=MEASURED)
        api.fx["actions/runs/44770182794"]["status"] = "in_progress"
        with tempfile.TemporaryDirectory() as tmp:
            code, out = quiet(lander.run, ["select", tmp + "/w"], env(pr="2"), api=api, config=CONFIG,
                              clock=lambda: 0, sleep=lambda s: self.fail("dry run slept"))
        self.assertEqual((code, api.writes), (0, []))
        self.assertIn("held while waiting for its results. run-binding", out)

    def test_dry_run_api_refuses_every_write(self):
        with self.assertRaises(ReadOnly):
            FakeApi(live=False).write("PUT", "pulls/2/merge", {})

    def test_live_landing_merges_with_expected_head_and_verifies_parent_and_tree(self):
        api = FakeApi(live=True, main=MEASURED)
        api.responses[("PUT", "pulls/2/merge")] = (200, {"sha": NEW, "merged": True})
        api.after_write[("PUT", "pulls/2/merge")] = self.merged
        with tempfile.TemporaryDirectory() as tmp:
            self.prepare(tmp, api)
            api.writes.clear()
            code, out = quiet(lander.run, ["land", tmp + "/w"], {**env(mode="live"), "BFME_LANDING_CHAIN": "1"},
                              api=api, config=CONFIG, sleep=lambda s: None)
        self.assertEqual(code, 0)
        # The clearance the ruleset requires comes first, for this exact head only.
        self.assertEqual(api.writes[0][:2], ("POST", f"statuses/{PR2}"))
        self.assertEqual((api.writes[0][2]["state"], api.writes[0][2]["description"]),
                         ("success", f"Cleared to land on main {MEASURED[:12]}"))
        method, path, body = api.writes[1]
        self.assertEqual((method, path, body["sha"], body["merge_method"]), ("PUT", "pulls/2/merge", PR2, "squash"))
        self.assertTrue(body["commit_title"].endswith("(#2)"))
        kinds = [(w[0], w[1]) for w in api.writes[2:]]
        self.assertEqual(kinds, [("POST", f"statuses/{NEW}"), ("POST", f"statuses/{PR2}"), ("POST", "issues/2/comments"),
                                 ("POST", "dispatches"), ("POST", "dispatches")])
        self.assertEqual(api.writes[5][2], {"event_type": "bfme-landed", "client_payload": {
            "number": 2, "head": PR2, "parent": MEASURED, "commit": NEW, "tree": TREE}})
        self.assertEqual(list(api.writes[5][2]["client_payload"]), ["number", "head", "parent", "commit", "tree"])
        # The body this workflow writes is exactly what a later run parses to reconcile this landing.
        lines = body["commit_message"].splitlines()
        self.assertEqual(lander.MEASURED_LINE.fullmatch(lines[0]).groups(), (MEASURED, PR2, TREE))
        self.assertEqual(lander.NUMBER_LINE.fullmatch(lines[1])[1], "2")
        self.assertTrue(lander.TRAILER_LINE.fullmatch(lines[2]))
        self.assertEqual(api.writes[6][2]["event_type"], "bfme-land-next")
        self.assertIn(f"Landed #2 as {NEW[:12]}", out)
        self.assertIn(f"::notice title=BFME II landing::Landed #2 as {NEW[:12]} on main", out)

    def test_main_moving_before_the_merge_stops_without_merging(self):
        api = FakeApi(live=True, main=MEASURED)
        with tempfile.TemporaryDirectory() as tmp:
            self.prepare(tmp, api)
            api.writes.clear()
            # Main moves after selection; the receipts still verify, and the read just before the merge sees it.
            api.fx["git/ref/heads/main"] = {"object": {"sha": "cd" * 20}}
            with self.assertRaises(lander.Held) as caught:
                quiet(lander.run, ["land", tmp + "/w"], env(mode="live"), api=api, config=CONFIG)
            out = caught.exception.line()
        self.assertEqual([w for w in api.writes if w[0] == "PUT"], [])
        self.assertIn("main-moved", out)
        # The clearance is withdrawn at once: the last Landing status on the head names the hold.
        last = [w for w in api.writes if w[1] == f"statuses/{PR2}"][-1][2]
        self.assertEqual(last["state"], "pending")
        self.assertTrue(last["description"].startswith("Held: main-moved."))

    def test_wrong_tree_after_merge_fails_and_marks_main(self):
        api = FakeApi(live=True, main=MEASURED)
        api.responses[("PUT", "pulls/2/merge")] = (200, {"sha": NEW, "merged": True})

        def bad(fx):
            self.merged(fx)
            fx[f"git/commits/{NEW}"]["tree"]["sha"] = "ee" * 20
        api.after_write[("PUT", "pulls/2/merge")] = bad
        with tempfile.TemporaryDirectory() as tmp:
            self.prepare(tmp, api)
            api.writes.clear()
            with self.assertRaises(lander.Failed) as caught:
                quiet(lander.run, ["land", tmp + "/w"], env(mode="live"), api=api, config=CONFIG, sleep=lambda s: None)
        self.assertEqual(caught.exception.code, "post-merge")
        self.assertEqual(api.writes[2], ("POST", f"statuses/{NEW}", {
            "state": "failure", "context": lander.LANDING_CONTEXT, "target_url":
            "https://github.com/Open-BFME/BFME2-Rebuild/actions/runs/1",
            "description": f"Landing verification failed: expected tree {TREE[:12]}"}))

    def test_merge_conflict_is_held_and_explained(self):
        api = FakeApi(live=True, main=MEASURED)
        api.responses[("PUT", "pulls/2/merge")] = (405, {"message": "Pull Request is not mergeable"})
        with tempfile.TemporaryDirectory() as tmp:
            self.prepare(tmp, api)
            api.writes.clear()
            with self.assertRaises(lander.Held) as caught:
                quiet(lander.run, ["land", tmp + "/w"], env(mode="live"), api=api, config=CONFIG)
        self.assertEqual(caught.exception.code, "merge-refused")
        self.assertIn(("POST", "issues/2/comments"), [(w[0], w[1]) for w in api.writes])
        last = [w for w in api.writes if w[1] == f"statuses/{PR2}"][-1][2]
        self.assertEqual((last["state"], last["description"][:22]), ("failure", "Held: merge-refused. E"))

    def test_report_only_inline_pending(self):
        def pending(fx):
            for item in fx[f"commits/{PR2}/statuses?per_page=100&page=1"]:
                if item["context"] == lander.INLINE:
                    item["state"], item["description"] = "pending", "Waiting for admitted inline-virtual evidence"
        api = FakeApi(live=False, main=MEASURED, edit=pending)
        with tempfile.TemporaryDirectory() as tmp:
            if not lander.optional_inline_supported():
                code, out = quiet(lander.run, ["select", tmp + "/w"], env(pr="2"), api=api, config=CONFIG)
                self.assertEqual((code, api.writes), (0, []))
                self.assertIn("inline-virtual-pending", out)
                return
            self.prepare(tmp, api, drop_inline=True)
            self.assertEqual(json.loads(Path(tmp, "w/binding.json").read_text())["runs"]["inline"], "pending")
            code, out = quiet(lander.run, ["land", tmp + "/w"], env(), api=api, config=CONFIG)
        self.assertEqual((code, api.writes), (0, []))
        self.assertIn("Would merge #2 (squash)", out)

    def test_changed_receipt_is_refused(self):
        api = FakeApi(live=False, main=MEASURED)
        with tempfile.TemporaryDirectory() as tmp:
            self.prepare(tmp, api)
            path = Path(tmp, "w/rules/receipt.json")
            record = json.loads(path.read_text())
            record["tree"] = "ee" * 20
            path.write_text(json.dumps(record))
            with self.assertRaises(lander.Held) as caught:
                quiet(lander.run, ["land", tmp + "/w"], env(), api=api, config=CONFIG)
        self.assertEqual(caught.exception.code, "receipt")


if __name__ == "__main__":
    unittest.main()
