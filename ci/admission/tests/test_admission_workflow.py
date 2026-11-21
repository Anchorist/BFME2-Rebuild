"""The admission workflow: which events start which mode, and what the retry run may touch.

A person's push to main starts the same retry as the hourly schedule, in one concurrency group that never cancels a
running retry. The push run reads no pull request content and uses main's own tools.
"""
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch

from test_admit import CONFIG, CLOCK, HEAD, MAIN, LedgerApi, admit, dispatches, env, fork_pr

WORKFLOW = (Path(__file__).resolve().parents[3] / ".github/workflows/admission.yml").read_text()


def step(name):
    start = WORKFLOW.index(f"- name: {name}")
    end = WORKFLOW.find("- name:", start + 8)
    return WORKFLOW[start:end if end != -1 else len(WORKFLOW)]


class Triggers(unittest.TestCase):
    def test_a_push_to_main_only_starts_the_retry(self):
        on = WORKFLOW.split("\npermissions:")[0]
        self.assertIn("  push:\n    branches: [main]\n", on)
        self.assertNotIn("tags:", on)
        retry = step("Retry held and undecided fork pull requests, oldest first")
        self.assertIn("github.event_name == 'push'", retry)
        self.assertIn("admit.py retry", retry)
        for other in ("Decide admission for this pull request", "Decide for the pull request the landing workflow named"):
            self.assertNotIn("push", step(other))

    def test_retries_share_one_group_that_never_cancels_a_running_retry(self):
        job = WORKFLOW.split("  admit:")[1]
        self.assertIn("concurrency:", job)
        self.assertIn("'bfme-admission-retry'", job)
        self.assertIn("github.event_name == 'push' || github.event_name == 'schedule' || "
                      "github.event_name == 'workflow_dispatch'", " ".join(job.split()))
        self.assertIn("cancel-in-progress: false", job)

    def test_the_push_run_reads_main_tools_and_no_pull_request_content(self):
        checkout = step("Read the admission tools from main, never from the pull request")
        self.assertIn("ref: '${{ github.sha }}'", checkout)
        self.assertIn("persist-credentials: false", checkout)
        self.assertNotIn("github.event.head_commit", WORKFLOW)
        self.assertNotIn("github.event.commits", WORKFLOW)
        permissions = WORKFLOW.split("  admit:")[1].split("permissions:")[1].split("# Live only")[0]
        self.assertEqual(sorted(line.strip() for line in permissions.strip().splitlines()),
                         ["actions: read", "contents: write", "pull-requests: read", "statuses: write"])


class PushRun(unittest.TestCase):
    def run_push(self, api):
        with patch.object(admit, "check_source", lambda *_: None), redirect_stdout(io.StringIO()) as out:
            admit.run(["retry"], env(event="push", sha=MAIN), api=api, config=CONFIG, clock=CLOCK)
        return out.getvalue()

    def test_a_push_run_admits_like_the_hourly_run(self):
        api = LedgerApi(True, [fork_pr()], {21: ["src/a.cpp"]})
        self.assertIn("admitted by rule", self.run_push(api))
        self.assertEqual([item["event_type"] for item in dispatches(api)], ["bfme-remeasure"])

    def test_several_pushes_reserve_once(self):
        api = LedgerApi(True, [fork_pr()], {21: ["src/a.cpp"]})
        for _ in range(3):
            self.run_push(api)
        text = "".join(content for content, _ in api.store.values())
        self.assertEqual(text.count(HEAD), 1)                         # one reservation for this commit on this main
        self.assertIsNotNone(admit.ledger.find(api, 21, HEAD, MAIN))
        # each unclaimed re-issue may dispatch again; the compiler check's single-use claim lets only one measure
        admit.ledger.claim(api, 21, HEAD, MAIN, "900", "1", CLOCK, tree="a1" * 20)
        before = len(dispatches(api))
        self.assertIn("already used", self.run_push(api))
        self.assertEqual(len(dispatches(api)), before)

    def test_a_push_run_on_a_moved_main_does_nothing(self):
        api = LedgerApi(True, [fork_pr()], {21: ["src/a.cpp"]})
        with patch.object(admit, "check_source", lambda *_: None), redirect_stdout(io.StringIO()) as out:
            admit.run(["retry"], env(event="push", sha="9" * 40), api=api, config=CONFIG, clock=CLOCK)
        self.assertIn("Superseded", out.getvalue())
        self.assertEqual(api.writes, [])


if __name__ == "__main__":
    unittest.main()
