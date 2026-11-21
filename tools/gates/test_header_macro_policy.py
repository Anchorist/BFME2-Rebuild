from dataclasses import replace
import unittest

from header_macro_policy import MacroProof, SharedView, change_in, verify_change


PATH = "src/Unit.cpp"
HEADER = "include/Shared.h"
BIND = ("1" * 40, "2" * 40, "3" * 40)
OID = "a" * 40
VIEWS = (SharedView(HEADER, OID, "Unit.cpp:2/Shared.h:9", "a" * 64, "a" * 64),)
OLD = '#define SHAPE 1\n#include "Shared.h"\n'
NEW = OLD.replace("SHAPE 1", "SHAPE 2")


class MacroPolicyTests(unittest.TestCase):
    def changes(self, old=OLD, new=NEW):
        return change_in(PATH, old, new)

    def proof(self, change=None, views=VIEWS):
        return MacroProof(*BIND, change or self.changes(), "c" * 64, True,
                          tuple((v.path, v.git_blob, v.site) for v in views), views)

    def verify(self, proof):
        return verify_change(self.changes(), BIND, {HEADER: OID}, proof)

    def test_no_macro_or_timing_delta(self):
        self.assertIsNone(self.changes(OLD, "\n// comment\n" + OLD))
        self.assertIsNone(self.changes('#include "Shared.h"\n', '#include "Other.h"\n'))
        self.assertIsNone(self.changes(OLD, OLD + "#define ENGINETOKEN 1\n"))
        self.assertIsNone(self.changes("", '// "#define SHAPE 1"\n"push_macro(SHAPE)";\n'))
        self.assertIsNone(self.changes("", '#define FOR_LOCAL_CODE 1\nint i = FOR_LOCAL_CODE;\n'))

    def test_regular_header_guard_does_not_make_a_literal_include_a_macro_override(self):
        protected = ("#pragma once\n#ifndef STANDARD_HEADER_H\n#define STANDARD_HEADER_H\n"
                     "struct Record {};\n#endif\n")
        current = protected.replace("struct Record", '#include "Vector.h"\nstruct Record')
        self.assertIsNone(change_in(HEADER, protected, current))
        self.assertIsNone(change_in(HEADER, "", current))
        self.assertIsNotNone(change_in(PATH, protected, current))

    def test_unchanged_outer_guard_does_not_hide_a_real_local_override(self):
        before = ("#ifndef STANDARD_HEADER_H\n#define STANDARD_HEADER_H\n"
                  '#define SHAPE 1\n#include "Shared.h"\n#endif\n')
        after = before.replace("SHAPE 1", "SHAPE 2")
        self.assertEqual(change_in(HEADER, before, after).line, 3)
        extra_include = before.replace('#include "Shared.h"', '#include "Vector.h"\n#include "Shared.h"')
        self.assertEqual(change_in(HEADER, before, extra_include).line, 4)

    def test_differently_spelled_guards_and_non_guards_stay_visible(self):
        before = '#ifndef FIRST_H\n#define FIRST_H\n#include "Shared.h"\n#endif\n'
        self.assertIsNotNone(change_in(HEADER, before, before.replace("FIRST_H", "SECOND_H")))
        partial_guard = before.replace("#endif", '#else\n#include "Fallback.h"\n#endif')
        self.assertIsNotNone(change_in(HEADER, partial_guard, partial_guard.replace("Shared.h", "Parts.h")))
        with_outside_include = '#include "Before.h"\n' + before
        self.assertIsNotNone(change_in(HEADER, with_outside_include, with_outside_include.replace("Before.h", "Parts.h")))

    def test_macros_before_literal_and_computed_includes(self):
        self.assertEqual(self.changes().line, 1)
        self.assertEqual(self.changes("", '#define HEADER "Shared.h"\n#include HEADER\n').line, 1)
        self.assertEqual(self.changes(OLD, '#include "Shared.h"\n#define SHAPE 1\n').line, 1)

    def test_digraph_splices_and_conditional_clock(self):
        source = '%:if 1\n??=de\\\nfine SHAPE 1\n#endif\n#include "Shared.h"\n'
        self.assertIsNone(self.changes(source, source.replace('%:', '#').replace('??=de\\\nfine', '#define')))
        self.assertIsNotNone(self.changes(source, source.replace('%:if 1', '%:if 0')))
        source = '#if A\nint x;\n#elif B\nint y;\n#else\n#define SHAPE 1\n#endif\n#include "Shared.h"\n'
        self.assertIsNotNone(self.changes(source, source.replace('#elif B', '#elif C')))

    def test_function_macro_token_adjacency_follows_cpp(self):
        self.assertIsNotNone(self.changes(OLD, OLD.replace("SHAPE 1", "SHAPE(x) 1")))
        a = OLD.replace("SHAPE 1", "SHAPE(x) x")
        self.assertIsNotNone(self.changes(a, a.replace("SHAPE(x)", "SHAPE (x)")))

    def test_flag_macros_undef_and_forced_include(self):
        before = '// cl: -DSHAPE=1 /I safe\n#include "Shared.h"\n'
        self.assertIsNotNone(self.changes(before, before.replace("-DSHAPE=1", "/USHAPE")))
        self.assertIsNone(self.changes(before, before.replace("-DSHAPE=1", "/DSHAPE=1")))
        self.assertIsNotNone(self.changes("", '// cl: -DSHAPE=1 /FI Shared.h\n'))
        self.assertIsNone(self.changes("", '// cl: /O2\n#include "Shared.h"\n'))

    def test_macro_stack_control(self):
        for prefix in ('#pragma push_macro("SHAPE")', '__pragma(pop_macro("SHAPE"))',
                       '_Pragma("push_macro(\\"SHAPE\\")")'):
            with self.subTest(prefix=prefix):
                self.assertIsNotNone(self.changes(OLD, prefix + "\n" + OLD))

    def test_complete_bound_proof_can_clear_candidate(self):
        self.assertEqual(self.verify(self.proof()), ([], []))
        self.assertEqual(self.verify(self.proof()), verify_change(self.changes(), BIND, {HEADER: OID}, self.proof()))
        _, holds = self.verify(None)
        self.assertEqual(holds[0][0].line, 1)

    def test_differently_expanded_shared_declarations_refuse_at_macro_input(self):
        proof = self.proof(views=(replace(VIEWS[0], after_declarations_sha256="b" * 64),))
        failures, holds = self.verify(proof)
        self.assertEqual(holds, [])
        self.assertEqual([(f.path, f.line, f.rule) for f in failures], [(PATH, 1, "H8")])
        self.assertIn(HEADER, failures[0].message)

    def test_partial_stale_and_duplicate_receipts_hold(self):
        proof = self.proof()
        for invalid in (
            replace(proof, complete=False), replace(proof, tree="4" * 40),
            replace(proof, views=()), replace(proof, views=VIEWS + VIEWS),
            replace(proof, record_sha256="bad"),
            self.proof(views=(replace(VIEWS[0], git_blob="b" * 40),)),
        ):
            with self.subTest(proof=invalid):
                self.assertTrue(self.verify(invalid)[1])



class HeaderOwnDeclarations(unittest.TestCase):
    """A macro in a header that rewrites the header's own declarations, with no include after it."""

    def test_a_keyword_macro_before_the_class_is_flagged(self):
        before = "class A { int x; };\n"
        self.assertIsNotNone(change_in("include/K13Control.h", before, "#define int short\n" + before))
        for spelled in ("#define class struct\n", "#define unsigned signed\n"):
            self.assertIsNotNone(change_in(HEADER, before, spelled + before))

    def test_a_macro_capturing_an_identifier_the_header_used_is_flagged(self):
        before = "#include \"Types.h\"\nstruct A { Bool b; };\n"
        self.assertIsNotNone(change_in(HEADER, before, before + "#define Bool char\n"))
        self.assertIsNotNone(change_in(HEADER, before.replace("Bool b", "Real r"),
                                       before.replace("Bool b", "Real r") + "#undef Real\n"))
        changed = '#include "Types.h"\n#define Bool int\nstruct A { Bool b; };\n'
        self.assertIsNotNone(change_in(HEADER, changed, changed.replace("Bool int", "Bool char")))

    def test_an_added_ordinary_include_guard_is_not_flagged(self):
        before = "class A { int x; };\n"
        guarded = "#ifndef A_H\n#define A_H\n" + before + "#endif\n"
        self.assertIsNone(change_in(HEADER, before, guarded))
        self.assertIsNone(change_in(HEADER, "", guarded))

    def test_an_identical_macro_on_both_sides_is_not_flagged(self):
        text = "#define int short\nclass A { int x; };\n"
        self.assertIsNone(change_in(HEADER, text, text + "// a comment\n"))

    def test_a_new_constant_after_the_last_include_is_not_flagged(self):
        before = '#include "Types.h"\nstruct A { int x; };\n'
        after = before + "#define MAX_ARMIES 16\nstruct B { int armies[MAX_ARMIES]; };\n"
        self.assertIsNone(change_in(HEADER, before, after))

    def test_a_source_file_keeps_its_local_macros(self):
        before = '#include "Shared.h"\nint f() { return 1; }\n'
        self.assertIsNone(change_in(PATH, before, before + "#define int short\n"))


if __name__ == "__main__":
    unittest.main()
