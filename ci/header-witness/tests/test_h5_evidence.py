"""Tests for ci/header-witness/h5_evidence.py. fixtures/evidence-vc71.json holds the VC7.1 objects of every compile the
three cases make (the TU with a layout probe appended, and the TU, each keyed by the SHA-256 of header bytes, "|",
source)."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import h5_evidence as evidence  # noqa: E402
import h5_witness as witness  # noqa: E402

FIXTURE = json.loads((Path(__file__).parent / "fixtures/evidence-vc71.json").read_text())
H = "include/Foo.h"
BASE, SOURCE = FIXTURE["base"].encode(), FIXTURE["source"].encode()


def compiled(header, source):
    key = hashlib.sha256(header + b"|" + source).hexdigest()
    if key not in FIXTURE["objects"]:
        raise witness.Held("not recorded")
    return bytes.fromhex(FIXTURE["objects"][key])


def symbol_of(obj, name):
    _, symbols, _ = witness._coff(obj)
    return next(item[1] for item in symbols if item[1].startswith(f"?{name}@@") and item[3] > 0)


def run(case):
    head = FIXTURE["cases"][case]["head"].encode()
    head_obj = compiled(head, SOURCE)
    rows = [{"rva": 0x1000 + i, "path": "src/t.cpp", "symbol": symbol_of(head_obj, name),
             "head_object": hashlib.sha256(head_obj).hexdigest(),
             "before": {"credited": False}, "after": {"credited": True, "proof": True, "status": "MATCH"}}
            for i, name in enumerate(FIXTURE["cases"][case]["credited"])]
    return evidence.evidence(H, BASE, head, rows, {"src/t.cpp": head_obj},
                             probe_compile=lambda side, header, probe: compiled(header, SOURCE + b"\n" + probe),
                             tu_compile=lambda header, paths: {p: compiled(header, SOURCE) for p in paths})


class RealCompiler(unittest.TestCase):
    def test_a_split_of_storage_is_compatible_shape_with_no_witness_needed(self):
        result = run("split (compatible)")
        self.assertEqual(result["layout"], {"complete": True, "compatible_shape": True, "atoms": []})
        self.assertEqual(result["access"]["reads"], [])

    def test_a_swap_used_by_both_new_functions_has_a_witness_for_each_member(self):
        result = run("swap a/b, both used")
        self.assertEqual(sorted(a["identity"] for a in result["layout"]["atoms"]), ["a", "b"])
        self.assertEqual(sorted((r["identity"], r["rva"]) for r in result["access"]["reads"]),
                         [("a", 0x1000), ("b", 0x1001)])
        self.assertFalse(result["layout"]["compatible_shape"])

    def test_a_swap_with_one_member_unused_leaves_that_member_unwitnessed(self):
        result = run("swap a/b, only a used")
        self.assertEqual([r["identity"] for r in result["access"]["reads"]], ["a"])

    def test_records_carry_the_layout_atom_offsets(self):
        reads = {r["identity"]: r for r in run("swap a/b, both used")["access"]["reads"]}
        atoms = {a["identity"]: a for a in run("swap a/b, both used")["layout"]["atoms"]}
        self.assertEqual(reads["a"]["observed"], atoms["a"]["after"])


class Selection(unittest.TestCase):
    def test_only_classes_whose_text_changed_are_measured(self):
        other = b"struct Other { int z; };\n"
        self.assertEqual(evidence.changed_classes(BASE + other, BASE.replace(b"int a;", b"int a; ") + other), [])
        self.assertEqual(evidence.changed_classes(BASE, BASE.replace(b"int b;", b"short b;")), ["Foo"])

    def test_too_many_changed_classes_hold(self):
        many = b"".join(b"struct C%d { int x; };\n" % i for i in range(6))
        changed = many.replace(b"int x;", b"long x;")
        result = evidence.evidence(H, many, changed, [], {}, lambda *a: None, lambda *a: {})
        self.assertFalse(result["layout"]["complete"])
        self.assertTrue(result["held"])

    def test_a_new_or_removed_class_holds(self):
        result = evidence.evidence(H, None, BASE, [], {}, lambda *a: None, lambda *a: {})
        self.assertFalse(result["layout"]["complete"])


if __name__ == "__main__":
    unittest.main()
