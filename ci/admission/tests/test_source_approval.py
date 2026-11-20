"""Check the real protected pre-reservation gate and the controller/receiver seam."""
import copy
import json
import unittest

from test_admit import BUDGET, CLOCK, CONFIG, HEAD, MAIN, TREE, LedgerApi, admit, dispatches, fork_pr
from source_approval import CONTEXTS, Unavailable, require_source

POLICY = "d" * 64
RUN = "314159"
FILE = "src/example.cpp"


class ProtectedProof(LedgerApi):
    def __init__(self, pr=None, files=None):
        super().__init__(True, [pr or fork_pr()], {21: files if files is not None else [FILE]})
        target = f"https://github.com/{admit.REPO}/actions/runs/{RUN}"
        self.statuses[HEAD] = [
            {"context": context, "state": "success", "creator": {"id": 41898282}, "target_url": target,
             "description": f"Pass (main {MAIN[:12]})", "id": i}
            for i, context in enumerate(CONTEXTS, start=100)
        ]
        self.run = {"id": int(RUN), "run_attempt": 1, "path": ".github/workflows/managed-pr.yml",
                    "repository": {"id": admit.REPO_ID}, "head_sha": HEAD, "event": "pull_request_target",
                    "status": "completed", "conclusion": "success"}
        self.artifact = {"id": 8, "name": "bfme-source-receipt-1", "expired": False, "size_in_bytes": 211}
        self.receipt = {"repo": admit.REPO_ID, "number": 21, "base": MAIN, "head": HEAD, "tree": TREE,
                        "tools_commit": MAIN, "policy_sha256": POLICY, "run": RUN, "attempt": "1", "state": "pass"}

    def call(self, path):
        if path == f"actions/runs/{RUN}":
            return copy.deepcopy(self.run)
        if path == f"actions/runs/{RUN}/artifacts?per_page=100":
            return {"artifacts": [copy.deepcopy(self.artifact)]}
        return super().call(path)

    def proof(self, api, number, head, base, tree):
        return require_source(api, number, head, base, tree, POLICY, self.receive)

    def receive(self, artifact):
        if artifact != self.artifact["id"]:
            raise AssertionError("wrong artifact")
        return copy.deepcopy(self.receipt)


def handle(api, *, proof=None, **kwargs):
    return admit.handle(api, 21, CONFIG, MAIN, BUDGET, CLOCK,
                        source_proof=proof if proof is not None else api.proof, **kwargs)


class PriorSourceGate(unittest.TestCase):
    def test_exact_receipt_reserves_once(self):
        api = ProtectedProof()
        self.assertIn("admitted by rule", handle(api))
        reservation = admit.ledger.find(api, 21, HEAD, MAIN)
        self.assertEqual((reservation["kind"], reservation["tree"]), ("narrow", TREE))
        self.assertEqual(len(dispatches(api)), 1)

    def test_different_tree_policy_or_attempt_never_debits(self):
        for key, wrong in (("tree","b"*40), ("policy_sha256","a"*64), ("attempt","2")):
            with self.subTest(key=key):
                api = ProtectedProof()
                api.receipt[key] = wrong
                self.assertIn("nothing reserved", handle(api))
                self.assertEqual((api.store, dispatches(api)), ({},[]))

    def test_named_red_does_not_spin_and_never_debits(self):
        api = ProtectedProof()
        api.statuses[HEAD][4]["state"] = "failure"
        delays = []
        self.assertIn("source rules refused", handle(api, source_attempts=5, sleep=delays.append))
        self.assertEqual((api.store, dispatches(api), delays), ({},[],[]))

    def test_wrong_writer_or_different_run_is_held(self):
        api = ProtectedProof()
        api.statuses[HEAD][1]["creator"]["id"] = 1234
        self.assertIn("nothing reserved", handle(api))
        api.statuses[HEAD][1]["creator"]["id"] = 41898282
        api.statuses[HEAD][1]["target_url"] += "1"
        self.assertIn("nothing reserved", handle(api))
        self.assertEqual((api.store, dispatches(api)), ({},[]))

    def test_superseded_event_never_reserves_current_head(self):
        api = ProtectedProof()
        self.assertIn("a newer head", handle(api, expected_head="e"*40))
        self.assertEqual((api.store, dispatches(api)), ({},[]))

    def test_main_moves_between_source_receipt_and_reserve(self):
        api = ProtectedProof()

        def moved(*args):
            receipt = api.proof(*args)
            api.main = "e"*40
            return receipt

        self.assertIn("main, head or admission type moved", handle(api, proof=moved))
        self.assertEqual((api.store, dispatches(api)), ({},[]))

    def test_artifact_is_only_from_protected_expected_current_run(self):
        for field, different in (("path",".github/workflows/unrelated.yml"),("head_sha","a"*40),
                                 ("conclusion","failure"),("run_attempt",2)):
            with self.subTest(field=field):
                api = ProtectedProof()
                api.run[field] = different
                self.assertIn("nothing reserved", handle(api))
                self.assertEqual((api.store, dispatches(api)), ({},[]))

    def test_missing_receipt_can_arrive_later_without_recharge(self):
        api = ProtectedProof()
        delays = []
        require = api.proof

        def delayed(*args):
            if not delays:
                raise Unavailable("source report is running")
            return require(*args)

        self.assertIn("admitted by rule", handle(api, proof=delayed, source_attempts=2, sleep=delays.append))
        self.assertEqual(delays, [5])
        self.assertEqual(len(dispatches(api)), 1)

    def test_nonowner_trusted_narrow_spends_no_quota(self):
        for origin in ("member","same-repo"):
            with self.subTest(origin=origin):
                pr = fork_pr()
                if origin == "member":
                    pr["author_association"] = "MEMBER"
                else:
                    pr["head"]["repo"]["id"] = admit.REPO_ID
                api = ProtectedProof(pr)
                book = admit.ledger
                self.assertIn("admitted by rule", admit.handle(api, 21, CONFIG, MAIN, None, CLOCK,
                                                       source_proof=api.proof))
                ledger = json.loads(api.store["ledger.json"][0])
                self.assertEqual(ledger["days"], {})
                item = book.find(api, 21, HEAD, MAIN)
                self.assertEqual(item["kind"], "trusted-narrow")
                self.assertEqual(book.claim(api, 21, HEAD, MAIN, "900", "1", CLOCK, tree=TREE,
                                            kind="narrow", admitted_by=item["admitted_by"]), "kind-mismatch")
                self.assertEqual(book.claim(api, 21, HEAD, MAIN, "900", "1", CLOCK, tree=TREE,
                                            kind="trusted-narrow", admitted_by=item["admitted_by"]), "claimed")
                self.assertEqual(len(dispatches(api)), 1)

    def test_owner_origin_trusted_stays_direct(self):
        pr = fork_pr()
        pr["author_association"] = "OWNER"
        api = ProtectedProof(pr)
        self.assertIn("protected direct", handle(api, owner_origin=True))
        self.assertEqual((api.store, dispatches(api)), ({},[]))

    def test_nine_source_paths_and_protected_workflow_cannot_debit(self):
        pr = fork_pr(labels=("boat-ok",))
        pr["author_association"] = "MEMBER"
        for files in ([f"src/{i}.cpp" for i in range(9)], [FILE,".github/workflows/rules.yml"]):
            with self.subTest(files=files):
                api = ProtectedProof(pr, files)
                handle(api, owner_origin=True)
                self.assertEqual((api.store, dispatches(api)), ({},[]))

    def test_stale_issuer_remains_ineligible_after_refresh(self):
        api = ProtectedProof()
        handle(api)
        ledger = admit.ledger
        before = ledger.find(api, 21, HEAD, MAIN)
        self.assertEqual(ledger.refresh_issuer(api, 21, HEAD, MAIN, "72", "1"), "refreshed")
        same = dict(tree=TREE, kind="narrow")
        self.assertEqual(ledger.claim(api, 21, HEAD, MAIN, "900", "1", CLOCK, **same,
                                      admitted_by=before["admitted_by"]), "issuer-mismatch")
        current = ledger.find(api, 21, HEAD, MAIN)
        self.assertIsNone(current["claimed_by"])
        self.assertEqual(ledger.claim(api, 21, HEAD, MAIN, "900", "1", CLOCK, **same,
                                      admitted_by=current["admitted_by"]), "claimed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
