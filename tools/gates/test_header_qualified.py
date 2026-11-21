"""Qualified header identity controls."""
import json
import unittest

from cpp import Source
from header_qualified import check_identities, ledger_types, qualified_types
from test_header_draft import Policy, Trees


class LedgerTrees(Trees):
    def __init__(self, before, after, names):
        super().__init__(before, after)
        self.ledger = json.dumps({"rows": [{"name": name, "accepted_names": []} for name in names]}).encode()

    def ledger_oid(self, base):
        return "test-ledger"

    def read_blob(self, oid, limit):
        return len(self.ledger), self.ledger


def check(before, after, names=()):
    return check_identities(LedgerTrees(before, after, names), Policy(), "before", "after")


class Qualified(unittest.TestCase):
    def test_namespace_and_nested_identity(self):
        text = "namespace Game { class Outer { public: struct Inner {}; }; class Other { struct Inner {}; }; }"
        self.assertEqual([row.name for row in qualified_types(Source(text))],
                         ["Game::Outer", "Game::Outer::Inner", "Game::Other", "Game::Other::Inner"])

    def test_internal_namespace_propagates_into_nested_class(self):
        found = list(qualified_types(Source("namespace { struct Outer { struct Inner {}; }; }")))
        self.assertTrue(all(row.internal for row in found), found)

    def test_function_local_types_not_global(self):
        self.assertEqual(list(qualified_types(Source("void Run() { struct Local {}; }"))), [])

    def test_qualified_duplicate_names_both_paths(self):
        before = {"include/A.h": "namespace Game { struct Outer { struct Inner; }; }"}
        after = before | {"include/B.h": "namespace Game { struct Outer::Inner {}; }",
                          "include/C.h": "namespace Game { struct Outer::Inner {}; }"}
        result = check(before, after)
        self.assertEqual({x.path for x in result}, {"include/B.h", "include/C.h"})
        self.assertTrue(all("Game::Outer::Inner" in x.message for x in result))

    def test_nested_definition_conflicts_with_out_of_class_definition(self):
        before = {"include/A.h": "struct Outer { struct Inner {}; };"}
        after = before | {"include/B.h": "struct Outer::Inner {};"}
        finding, = check(before, after)
        self.assertIn("include/A.h", finding.message)

    def test_identical_leaf_in_different_namespace_passes(self):
        prior = {"include/A.h": "namespace Game { class Impl {}; }"}
        self.assertEqual(check(prior, prior | {"include/B.h": "namespace Menu { class Impl {}; }"}), [])

    def test_existing_duplicate_without_growth_passes(self):
        prior = {"include/A.h": "struct Type {};", "include/B.h": "class Type {};"}
        self.assertEqual(check(prior, prior | {"include/B.h": "// Same type\n" + prior["include/B.h"]}), [])

    def test_existing_same_namespace_global_is_named(self):
        prior = {"include/A.h": "namespace Game { int Value = 1; }"}
        finding, = check(prior, prior | {"src/T.cpp": "namespace Game { int Value = 2; }"})
        self.assertIn("Game::Value", finding.message)

    def test_internal_global_does_not_conflict_across_files(self):
        prior = {"src/A.cpp": "static int Token = 1;"}
        self.assertEqual(check(prior, prior | {"src/B.cpp": "static int Token = 2;"}), [])

    def test_member_mangled_name_identifies_exact_qualified_type(self):
        code = {"include/A.h": "namespace Game { class Rva00A123Type {}; }"}
        self.assertEqual(check({}, code, ("?run@Rva00A123Type@Game@@QAEXXZ",)), [])
        finding, = check({}, code, ("?run@Rva00A123Type@Menu@@QAEXXZ",))
        self.assertIn("Game::Rva00A123Type", finding.message)

    def test_mangled_function_or_namespace_does_not_claim_a_type(self):
        code = {"include/A.h": "class Rva00A123Type {};"}
        finding, = check({}, code, ("?Rva00A123Type@@YAXXZ", "?run@Rva00A123Type@@YAXXZ"))
        self.assertIn("placeholder type", finding.message)

    def test_encoded_ctor_vftable_and_parameter(self):
        for key in ("??0Rva00A123Type@Game@@QAE@XZ", "??_7Rva00A123Type@Game@@6B@",
                    "?test@@YAXPAVRva00A123Type@Game@@@Z"):
            self.assertEqual(list(ledger_types(key)), ["Game::Rva00A123Type"])


if __name__ == "__main__":
    unittest.main()
