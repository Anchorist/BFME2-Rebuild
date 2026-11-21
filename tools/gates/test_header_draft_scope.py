from dataclasses import replace
from types import SimpleNamespace
import unittest

from git_objects import Delta, Entry
from header_draft_scope import Dependency, VerifiedDraftScope, check_draft_scope
from header_inventory import Binding


DRAFT = "include/Draft/Game/A.h"
SCRIPT = "src/Game/A.cpp"
INCLUDER = "include/Manager.h"
BIND = Binding("owner/repo", "1" * 40, "2" * 40, "3" * 40, "a" * 64, "b" * 64, 51, 1)
POLICY = SimpleNamespace(kind=lambda path: "header" if path.endswith(".h") else "source",
                         limits={"bytes_per_file": 100_000})


class Repo:
    def __init__(self, line):
        self.line = line

    def diff(self, base, tree):
        return iter([Delta(DRAFT, Entry("100644", "d" * 40), None)])

    def tree(self, revision, *paths):
        if revision == BIND.base:
            yield DRAFT, Entry("100644", "d" * 40)
        yield INCLUDER, Entry("100644", "e" * 40)

    def blob(self, oid, limit):
        text = self.line if oid == "e" * 40 else b"class A {};\n"
        return len(text), text


class DraftDependencyProof(unittest.TestCase):
    def setUp(self):
        self.repo = Repo(b'// note\n#include RETIRED_DRAFT\n')
        self.proof = VerifiedDraftScope(BIND, (SCRIPT,), (), True)

    def check(self, proof=None, required=(SCRIPT,)):
        return check_draft_scope(self.repo, POLICY, BIND, required_units=required, proof=proof)

    def test_unresolved_macros_hold_without_complete_compiler_scope(self):
        self.assertEqual(self.check().state, "held")
        self.assertEqual(self.check(self.proof).state, "pass")
        empty = replace(self.proof, translation_units=())
        self.assertEqual(self.check(empty, ()).state, "pass")
        self.assertEqual(self.check(empty).state, "held")
        self.assertEqual(self.check(self.proof, None).state, "held")
        self.assertEqual(self.check(replace(self.proof, complete=False)).state, "held")

    def test_a_reachable_computed_include_names_actual_file_and_line(self):
        edge = Dependency(SCRIPT, INCLUDER, 2, DRAFT)
        result = self.check(replace(self.proof, dependencies=(edge,)))
        self.assertEqual(result.state, "fail")
        self.assertEqual([(f.path, f.line, f.rule) for f in result.findings], [(INCLUDER, 2, "H7")])
        self.assertIn(DRAFT, result.findings[0].message)

    def test_wrong_binding_or_unit_cannot_clear_the_draft(self):
        for invalid in (
            replace(self.proof, binding=replace(BIND, tree="8" * 40)),
            replace(self.proof, translation_units=("src/Other.cpp",)),
            replace(self.proof, dependencies=(Dependency("src/Different.cpp", INCLUDER, 2, DRAFT),)),
        ):
            with self.subTest(invalid=invalid):
                self.assertEqual(self.check(invalid).state, "held")

    def test_literal_failure_is_immediate_without_graph(self):
        self.repo = Repo(b'#include "Draft/Game/A.h"\n')
        result = self.check()
        self.assertEqual(result.state, "fail")
        self.assertEqual(result.findings[0].line, 1)


if __name__ == "__main__":
    unittest.main()
