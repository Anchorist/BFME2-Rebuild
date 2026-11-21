import unittest

from git_objects import Git
from header_source_preview import source_preview
from test_header_checks import HEADER, POLICY
import test_header_inventory as fixtures


class SourcePreviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.InventoryTests(methodName="test_comment_and_whitespace_only_do_not_require_an_inventory")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def evaluate(self, base, head):
        binding, _ = self.fixture.compare(base, head)
        with Git(self.fixture.root) as repo:
            data = source_preview(repo, POLICY, binding)
        return data, {item["rule"]: item for item in data["preview"]}

    def test_source_declaration_reformulation_stays_pending(self):
        base = self.fixture.commit({HEADER: "struct Foo { int value; };\n"})
        head = self.fixture.commit({HEADER:
            "#define DECLARE_FIELD(type, name) type name\n"
            "struct Foo { DECLARE_FIELD(int, value); };\n"})
        data, rules = self.evaluate(base, head)
        self.assertEqual(rules["H4"]["state"], "held")
        self.assertEqual(data["declaration_review"]["candidates"],
                         [{"path": HEADER, "line": 1, "declaration": "Foo::value"}])
        self.assertTrue(data["declaration_review"]["unclassified"])
        self.assertNotIn("explicit_removed", data)

    def test_even_an_explicit_apparent_removal_awaits_protected_inventory(self):
        base = self.fixture.commit({HEADER: "struct Foo { int value; };\n"})
        head = self.fixture.commit({HEADER: "struct Foo {};\n"})
        data, rules = self.evaluate(base, head)
        self.assertEqual(rules["H4"]["state"], "held")
        self.assertEqual(len(data["declaration_review"]["candidates"]), 1)
        self.assertEqual(data["declaration_review"]["unclassified"], [])
        head = self.fixture.commit({}, "Change\n\nRemoved-Declaration: Foo::value")
        data, rules = self.evaluate(base, head)
        self.assertEqual(rules["H4"]["state"], "held")
        self.assertEqual(data["declaration_review"]["candidates"], [])

    def test_recognized_hard_refusals_remain_terminal(self):
        base = self.fixture.commit({HEADER: "struct Foo { int value; };\n"})
        head = self.fixture.commit({HEADER: "struct Foo { __declspec(noinline) int get(); };\n"})
        data, rules = self.evaluate(base, head)
        self.assertEqual(rules["H4"]["state"], "held")
        self.assertEqual(rules["H8"]["state"], "fail")
        self.assertEqual(rules["H8"]["findings"][0]["line"], 1)
        self.assertTrue(data["declaration_review"]["candidates"])

    def test_no_changed_headers_passes_all_source_components(self):
        base = self.fixture.commit({HEADER: "struct Foo { int value; };\n"})
        data, rules = self.evaluate(base, base)
        self.assertEqual({item["state"] for item in rules.values()}, {"pass"})
        self.assertEqual(data["declaration_review"], {"candidates": [], "unclassified": []})
