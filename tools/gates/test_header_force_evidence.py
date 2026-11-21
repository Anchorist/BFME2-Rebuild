import hashlib
from dataclasses import replace
import unittest

from header_force_evidence import DonorCatalog, NativeProof, changes_in, decide


BINDING = ("1" * 40, "2" * 40, "3" * 40)
DONOR = DonorCatalog([
    ("zero/Position.hpp", "namespace g { class Position {\n"
     "WWINLINE int value(const int *index) const;\n}; }\n"
     "#pragma intrinsic(abs)\n"),
    ("zero/Source.cpp", "__forceinline int helper(const int *index) { return 1; }\n"),
    ("zero/Pragma.h", "#pragma intrinsic(abs)\n"),
])
BODY = "namespace g { class Position {\n__forceinline int value(const int * p) const;\n}; }\n"
NEW = "// evidence: 0x401234 and 0x401982\n__forceinline int helper(int index) { return 1; }\n"


class ForceEvidenceTests(unittest.TestCase):
    def evaluate(self, after, path="include/Position.h", before="", proofs=(), donor=DONOR):
        return decide(path, before, after, donor, BINDING, published_native=proofs)

    def proof(self, source=NEW, path="include/Position.h"):
        site, = changes_in(path, source)
        return NativeProof(*BINDING, site, hashlib.sha256(source.encode()).hexdigest(),
                           site.rvas, (0x401234, 0x401982), (0x401234, 0x401982),
                           True, "verified-different", "b" * 64)

    def test_exact_qualified_donor_matches_suffix_and_ignores_parameter_names(self):
        failures, holds, witnesses = self.evaluate(BODY)
        self.assertEqual((failures, holds), ([], []))
        self.assertEqual(witnesses[0][1:], ("zero/Position.hpp", 2))

    def test_other_owner_does_not_borrow_donor(self):
        failures, holds, witnesses = self.evaluate(BODY.replace("namespace g", "namespace d"))
        self.assertEqual((len(failures), holds, witnesses), (1, [], []))
        self.assertEqual(failures[0].line, 2)

    def test_other_overload_requires_evidence(self):
        found, hold, ok = self.evaluate(BODY.replace("const int * p", "const float * p"))
        self.assertEqual((found, len(hold), ok), ([], 1, []))

    def test_exact_pragma_requires_same_basename(self):
        pragma = "#pragma intrinsic ( abs )\n"
        self.assertEqual(len(self.evaluate(pragma, "include/Pragma.h")[2]), 1)
        self.assertEqual(len(self.evaluate(pragma, "include/Other.h")[0]), 1)
        self.assertEqual(len(self.evaluate(pragma.replace("abs", "foo"), "include/Pragma.h")[1]), 1)

    def test_header_native_evidence_requires_exact_bound_whole_caller_proof(self):
        proof = self.proof()
        self.assertEqual(len(self.evaluate(NEW, proofs=(proof,))[2]), 1)
        for fields in (
            {"tree": "4" * 40}, {"complete_callers": False}, {"expanded_sites": (0x401234,)},
            {"source_sha256": "1" * 64}, {"proved_rvas": (0x401234,)},
            {"ordinary_form": "untested"}, {"measurement_sha256": "owner says okay"},
        ):
            with self.subTest(fields=fields):
                verdict = self.evaluate(NEW, proofs=(replace(proof, **fields),))
                self.assertEqual((verdict[0], len(verdict[1]), verdict[2]), ([], 1, []))

    def test_new_source_private_force_cannot_use_native_exception(self):
        path = "src/Other.cpp"
        self.assertEqual(len(self.evaluate(NEW, path, proofs=(self.proof(path=path),))[0]), 1)
        source = "__forceinline int helper(const int *value) { return 2; }\n"
        self.assertEqual(len(self.evaluate(source, "src/Source.cpp")[2]), 1)

    def test_forged_or_detached_note_does_not_nominate_rvas(self):
        for before in ('/*\n// evidence: 0x401234\n*/\n', '// evidence: 0x401234\n// other\n',
                       '#define X R"(text\n// evidence: 0x401234\n)"\n'):
            with self.subTest(before=before):
                site, = changes_in("include/Position.h", before + NEW.split("\n", 1)[1])
                self.assertEqual(site.rvas, ())

    def test_comments_literals_splices_and_existing_site(self):
        after = '// __forceinline\nconst char *p = "__forceinline";\n'
        self.assertEqual(self.evaluate(after), ([], [], []))
        after += 'int __forcein\\\nline function(int x);\n'
        self.assertEqual(len(self.evaluate(after)[0]), 1)
        self.assertEqual(self.evaluate("\n" + BODY, before=BODY), ([], [], []))

    def test_missing_donor_holds(self):
        self.assertEqual(len(self.evaluate(BODY, donor=None)[1]), 1)


if __name__ == "__main__":
    unittest.main()
