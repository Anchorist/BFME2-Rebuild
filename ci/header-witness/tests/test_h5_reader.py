"""Tests for ci/header-witness/h5_reader.py with a stand-in for the declaration reader's issuer and artifact checks."""
import json
import os
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest
import unittest.mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import h5_reader as reader  # noqa: E402

BINDING = {"number": 9, "base": "b" * 40, "head": "c" * 40, "tree": "d" * 40}
RUN = {"id": "77", "attempt": "2"}
ISSUER = {"run": "77", "attempt": "2"}


def receipt(**changes):
    doc = {"version": 1, "binding": {"repo": 5, **BINDING, "issuer": dict(ISSUER)}, "headers": {}, "held": []}
    doc.update(changes)
    return doc


def fake_h2(doc, decision=None, moved_after=False, issuers=None):
    state = {"reads": 0, "issuer_calls": 0}
    files = {"decision.json": dict(BINDING, kind="compile", repo=5, plan="e" * 64) if decision is None else decision,
             "header-h5.json": doc}

    class Actions:
        def __init__(self, head, base):
            self.run = None

        def anchor(self):
            return 0

        def extract(self, artifact, names, limit, scratch):
            (name,) = names
            Path(scratch, name).write_text(json.dumps(files[name]))

    def current(api, binding):
        state["reads"] += 1
        return not (moved_after and state["reads"] > 1)

    def published_issuer(api, binding):
        state["issuer_calls"] += 1
        return (issuers or [RUN, RUN])[min(state["issuer_calls"], 2) - 1]

    return SimpleNamespace(HEX40=re.compile(r"[0-9a-f]{40}\Z"), REPO_ID=5, Actions=Actions, current=current,
                           published_issuer=published_issuer, named_artifact=lambda api, run, name, *a: name,
                           own_decision=lambda decision: decision,
                           read=lambda path, limit: json.loads(Path(path).read_text()))


def read(h2):
    with unittest.mock.patch.object(reader, "_h2", return_value=h2), \
            unittest.mock.patch.dict(os.environ, {"GITHUB_SHA": BINDING["base"]}):
        return reader.read_published(dict(BINDING))


class Reader(unittest.TestCase):
    def test_the_bound_receipt_of_the_current_attempt_is_returned(self):
        self.assertEqual(read(fake_h2(receipt()))["version"], 1)

    def test_a_receipt_for_another_head_attempt_or_shape_is_refused(self):
        for doc in (receipt(binding={"repo": 5, **BINDING, "head": "f" * 40, "issuer": dict(ISSUER)}),
                    receipt(binding={"repo": 5, **BINDING, "issuer": {"run": "77", "attempt": "1"}}),
                    receipt(version=2), receipt(headers=[])):
            with self.assertRaises(ValueError):
                read(fake_h2(doc))

    def test_a_decision_for_another_pull_request_is_refused(self):
        with self.assertRaises(ValueError):
            read(fake_h2(receipt(), decision=dict(BINDING, number=10, kind="compile", repo=5, plan="e" * 64)))

    def test_a_move_or_a_newer_attempt_during_the_read_is_refused(self):
        with self.assertRaises(ValueError):
            read(fake_h2(receipt(), moved_after=True))
        with self.assertRaises(ValueError):
            read(fake_h2(receipt(), issuers=[RUN, {"id": "78", "attempt": "1"}]))

    def test_a_binding_for_another_main_is_refused_before_any_read(self):
        with unittest.mock.patch.object(reader, "_h2", return_value=fake_h2(receipt())), \
                unittest.mock.patch.dict(os.environ, {"GITHUB_SHA": "a" * 40}):
            with self.assertRaises(ValueError):
                reader.read_published(dict(BINDING))


if __name__ == "__main__":
    unittest.main()
