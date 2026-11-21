from dataclasses import replace
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from git_objects import Git
from header_inline import InlineBody, classify_changed
from header_inline_context import VirtualSlot, body_key
from header_inventory import (Binding, BodyContext, VerifiedInlineContext, VerifiedInlineEvidence, VerifiedInventory,
                              changed_headers, check_h4, check_h6, evaluate_inventories)
from header_removal import Declaration

HEADER = "include/A.h"
OTHER = "include/B.h"
SOURCE = "namespace P { class A { public:\nvirtual int get(int v) const;\nint f;\n}; }\n"
CHANGE = SOURCE.replace("get(int v)", "get(unsigned v)")
REMOVED = Declaration(HEADER, 2, "P::A::get", "?get@A@P@@UBEHH@Z")
NEW = replace(REMOVED, identity="?get@A@P@@UBEHI@Z")
INLINE = InlineBody(HEADER, 2, "P::A::get", NEW.identity, "{ return f; }", ("f",), ("v",))
POLICY = SimpleNamespace(limits={"bytes_per_file": 4096})
ENV = os.environ | {"GIT_AUTHOR_NAME": "Header control", "GIT_COMMITTER_NAME": "Header control",
                    "GIT_AUTHOR_EMAIL": "fixture@example.invalid", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}


class InventoryTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "include").mkdir()
        self.git("init", "-q")

    def git(self, *args):
        return subprocess.check_output(
            ["git", "-c", f"core.hooksPath={os.devnull}", "-C", str(self.root), *args],
            env=ENV, stderr=subprocess.DEVNULL,
        ).decode().strip()

    def commit(self, changes, message="Fixture"):
        for path, text in changes.items():
            target = self.root / path
            if text is None:
                target.unlink()
            else:
                target.write_text(text, encoding="utf-8", newline="\n")
        self.git("add", "-A", "--", "include")
        self.git("commit", "-qm", message, "--allow-empty")
        return self.git("rev-parse", "HEAD")

    def compare(self, base, head):
        with Git(self.root) as repo:
            binding = Binding("owner/project", base, head, repo.tree_oid(head),
                              "f" * 64, "e" * 64, 21, 1)
            return binding, changed_headers(repo, binding, POLICY)

    def inventory(self, binding, rule, files, before, after):
        return VerifiedInventory(binding, rule, tuple(item.identity for item in files), before, after, 1, True)

    def test_comment_and_whitespace_only_do_not_require_an_inventory(self):
        base = self.commit({HEADER: SOURCE})
        head = self.commit({HEADER: SOURCE.replace("int f;", "int  f; // note")})
        binding, files = self.compare(base, head)
        self.assertEqual(files, ())
        with Git(self.root) as repo:
            self.assertEqual(check_h4(repo, binding, files).state, "pass")
        self.assertEqual(check_h6(binding, files).state, "pass")

    def test_line_number_sensitive_context_cannot_use_comment_fast_path(self):
        base = self.commit({HEADER: SOURCE})
        head = self.commit({HEADER: "// explain on its own line\n" + SOURCE})
        binding, files = self.compare(base, head)
        self.assertEqual([item.identity.path for item in files], [HEADER])
        with Git(self.root) as repo:
            h4, h6 = evaluate_inventories(repo, binding, POLICY)
        self.assertEqual((h4.state, h6.state), ("held", "held"))

    def test_macro_definition_whitespace_may_change_meaning(self):
        base = self.commit({HEADER: "#define X(a) 0\n" + SOURCE})
        head = self.commit({HEADER: "#define X (a) 0\n" + SOURCE})
        _, files = self.compare(base, head)
        self.assertEqual([item.identity.path for item in files], [HEADER])

    def test_same_qualified_name_with_changed_decoration_needs_exact_trailer(self):
        base = self.commit({HEADER: SOURCE})
        heads = [
            self.commit({HEADER: CHANGE}, "Change\n\nRemoved declaration: P::A::get"),
            self.commit({}, "Change\n\nRemoved-Declaration: Other::A::get"),
            self.commit({}, "Change\n\nRemoved-Declaration: P::A::get"),
        ]
        outcomes = []
        with Git(self.root) as repo:
            for head in heads:
                binding, files = self.compare(base, head)
                receipt = self.inventory(binding, "H4", files, (REMOVED,), (NEW,))
                outcomes.append(check_h4(repo, binding, files, receipt))
        self.assertEqual([item.state for item in outcomes], ["fail", "fail", "pass"])
        self.assertEqual(outcomes[0].findings[0].line, 2)

    def test_moved_exact_qualified_declaration_is_retained(self):
        base = self.commit({HEADER: SOURCE})
        head = self.commit({HEADER: None, OTHER: SOURCE})
        binding, files = self.compare(base, head)
        receipt = self.inventory(binding, "H4", files, (REMOVED,), (replace(REMOVED, path=OTHER),))
        with Git(self.root) as repo:
            self.assertEqual(check_h4(repo, binding, files, receipt).state, "pass")

    def test_incomplete_or_wrong_binding_stays_held(self):
        base = self.commit({HEADER: SOURCE})
        head = self.commit({HEADER: CHANGE})
        binding, files = self.compare(base, head)
        receipt = self.inventory(binding, "H4", files, (REMOVED,), (NEW,))
        cases = (None, replace(receipt, files=()), replace(receipt, complete=False),
                 replace(receipt, binding=replace(binding, attempt=2)),
                 replace(receipt, before=(replace(REMOVED, line=100),)),
                 replace(receipt, before=(REMOVED, REMOVED)),
                 replace(receipt, before=(replace(REMOVED, path=OTHER),)))
        with Git(self.root) as repo:
            for invalid in cases:
                with self.subTest(receipt=invalid):
                    result = check_h4(repo, binding, files, invalid)
                    self.assertEqual(result.state, "held")
                    self.assertEqual(result.findings[0].rule, "H4")

    def test_trivial_shape_and_required_exact_body(self):
        base = self.commit({HEADER: SOURCE})
        head = self.commit({HEADER: CHANGE.replace(") const;", ") const { return f; }")})
        binding, files = self.compare(base, head)
        trivial = self.inventory(binding, "H6", files, (), (INLINE,))
        self.assertEqual(check_h6(binding, files).state, "held")
        self.assertEqual(check_h6(binding, files, trivial).state, "pass")
        nontrivial_body = replace(INLINE, body="{ return f + 1; }")
        nontrivial = replace(trivial, after=(nontrivial_body,))
        self.assertEqual(check_h6(binding, files, nontrivial).state, "held")
        _, needed = classify_changed([], [nontrivial_body], complete=True)
        proof = VerifiedInlineEvidence(binding, tuple(needed), True)
        self.assertEqual(check_h6(binding, files, nontrivial, proof).state, "pass")
        red = replace(proof, covered=(), refused=tuple(needed))
        self.assertEqual(check_h6(binding, files, nontrivial, red).state, "fail")
        self.assertEqual(check_h6(binding, files, nontrivial, replace(red, covered=tuple(needed))).state, "held")
        self.assertEqual(check_h6(binding, files, nontrivial, replace(proof, complete=False)).state, "held")
        self.assertEqual(check_h6(binding, files, nontrivial,
                                 replace(proof, binding=replace(binding, tree="a" * 40))).state, "held")

    def test_virtual_base_forward_waits_for_the_exact_complete_slot_proof(self):
        base = self.commit({HEADER: SOURCE})
        new_code = SOURCE.replace(") const;", ") const { return Base::get(v); }")
        head = self.commit({HEADER: new_code})
        binding, files = self.compare(base, head)
        body = replace(INLINE, body="{ return Base::get(v); }", direct_bases=("Base",))
        required = body_key(body)
        inventory = self.inventory(binding, "H6", files, (), (body,))
        behavior_alone = VerifiedInlineEvidence(binding, (required,), True)
        held = check_h6(binding, files, inventory, behavior_alone)
        self.assertEqual(held.state, "held")
        self.assertIn("retail table slot", held.findings[0].message)
        slot = VirtualSlot(required, "P::A", 0x400000, 1, "Base", 0x401234,
                           0x401234, 0, 0x403411, True)
        verified = VerifiedInlineContext(binding, (BodyContext(required, True),), (slot,), (required,))
        self.assertEqual(check_h6(binding, files, inventory, context=verified).state, "pass")
        for invalid in (replace(verified, complete_slots=()),
                        replace(verified, slots=(slot, slot)),
                        replace(verified, slots=(slot, replace(slot, index=2, emitted_target_rva=0x401987))),
                        replace(verified, binding=replace(binding, attempt=2))):
            self.assertEqual(check_h6(binding, files, inventory, context=invalid).state, "held")

    def test_nonvirtual_direct_base_and_transitive_case_keep_distinct_requirements(self):
        base = self.commit({HEADER: SOURCE})
        head = self.commit({HEADER: CHANGE})
        binding, files = self.compare(base, head)
        direct = replace(INLINE, body="{ return Base::get(v); }", direct_bases=("Base",))
        wrong = replace(direct, body="{ return GrandParent::get(v); }")
        valid = VerifiedInlineContext(binding, (BodyContext(body_key(direct), False),), ())
        direct_inv = self.inventory(binding, "H6", files, (), (direct,))
        self.assertEqual(check_h6(binding, files, direct_inv, context=valid).state, "pass")
        transitive = replace(direct_inv, after=(wrong,))
        unverifiable = check_h6(binding, files, transitive)
        self.assertEqual(unverifiable.state, "held")
        self.assertIn("retail table slot", unverifiable.findings[0].message)


if __name__ == "__main__":
    unittest.main()
