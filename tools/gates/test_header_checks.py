from dataclasses import replace
from pathlib import Path
import unittest

import gate
from git_objects import Git
from header_checks import TrustedObservations, check_header_source
from header_inventory import VerifiedInventory
import test_header_inventory as fixtures

POLICY = gate.policy_at(Path(gate.__file__).with_name("config.json"))
HEADER = "include/Foo.h"


class HeaderIntegration(unittest.TestCase):
    def git_fixture(self):
        fixture = fixtures.InventoryTests(methodName="test_comment_and_whitespace_only_do_not_require_an_inventory")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        return fixture

    def evaluate(self, fixture, binding, trusted=None):
        with Git(fixture.root) as repo:
            return {item.rule: item for item in check_header_source(repo, POLICY, binding, trusted)}

    def test_comment_only_header_clears_text_rules_without_inventory(self):
        fixture = self.git_fixture()
        base = fixture.commit({HEADER: "class Foo { int value; }; // previous note\n"})
        head = fixture.commit({HEADER: "class Foo { int value; }; // a clearer note\n"})
        binding, _ = fixture.compare(base, head)
        self.assertEqual({item.state for item in self.evaluate(fixture, binding).values()}, {"pass"})

    def test_local_noinline_is_named_even_without_other_receipts(self):
        fixture = self.git_fixture()
        base = fixture.commit({HEADER: "class Foo { int value; };\n"})
        head = fixture.commit({HEADER: "class Foo { __declspec(noinline) int get(); int value; };\n"})
        binding, _ = fixture.compare(base, head)
        rules = self.evaluate(fixture, binding)
        self.assertEqual(rules["H4"].state, "held")
        self.assertEqual(rules["H6"].state, "held")
        self.assertEqual(rules["H8"].state, "fail")
        finding, = rules["H8"].findings
        self.assertEqual((finding.path, finding.line), (HEADER, 1))

    def test_same_header_declaration_cannot_replace_a_pointer_with_an_integer(self):
        fixture = self.git_fixture()
        base = fixture.commit({HEADER: "class File;\nclass Foo { File *m_theFile; };\n"})
        head = fixture.commit({HEADER: "class File;\nclass Foo { unsigned int m_theFile; };\n"})
        binding, _ = fixture.compare(base, head)
        rule = self.evaluate(fixture, binding)["H8"]
        self.assertEqual(rule.state, "fail")
        finding, = rule.findings
        self.assertEqual((finding.path, finding.line), (HEADER, 2))
        self.assertIn("m_theFile", finding.message)
        self.assertIn("ledger request", finding.remedy)
        self.assertIn("proves it stores an integer", finding.remedy)

    def test_header_type_swap_ignores_ordinary_retypes_and_new_independent_members(self):
        fixture = self.git_fixture()
        base = fixture.commit({HEADER: "class File;\nclass Foo { File *m_theFile; short code; };\n"})
        head = fixture.commit({HEADER: "class File;\nclass Foo { File *m_theFile; int code; int index; };\n"})
        binding, _ = fixture.compare(base, head)
        self.assertEqual(self.evaluate(fixture, binding)["H8"].state, "pass")

    def test_source_only_type_swap_remains_advisory_even_in_header_preview(self):
        fixture = self.git_fixture()
        (fixture.root / "src").mkdir(exist_ok=True)
        base = fixture.commit({"src/Foo.cpp": "void f() { File *value; }\n"})
        head = fixture.commit({"src/Foo.cpp": "void f() { unsigned int value; }\n"})
        binding, _ = fixture.compare(base, head)
        self.assertEqual(self.evaluate(fixture, binding)["H8"].state, "pass")

    def test_changed_header_waits_for_exact_producer_binding(self):
        fixture = self.git_fixture()
        base = fixture.commit({HEADER: "class Foo { int value; };\n"})
        head = fixture.commit({HEADER: "class Foo { int value; int get(); };\n"})
        binding, files = fixture.compare(base, head)
        h4 = VerifiedInventory(binding, "H4", tuple(item.identity for item in files), (), (), 1, True)
        trusted = TrustedObservations(binding, declarations=h4)
        self.assertEqual(self.evaluate(fixture, binding, trusted)["H4"].state, "pass")
        wrong_attempt = replace(trusted, binding=replace(binding, attempt=2))
        self.assertEqual(self.evaluate(fixture, binding, wrong_attempt)["H4"].state, "held")
