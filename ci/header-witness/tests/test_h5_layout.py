"""Tests for ci/header-witness/h5_layout.py. fixtures/layout-vc71.json holds VC7.1 probe objects compiled from the
base header and each changed header stored beside them."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import h5_layout as layout  # noqa: E402

FIXTURE = json.loads((Path(__file__).parent / "fixtures/layout-vc71.json").read_text())
H = "include/Foo.h"


def side(text, obj_hex):
    inv = layout.inventory(text.encode(), "Foo")
    return inv, layout.measure(bytes.fromhex(obj_hex), H, "Foo", inv)


def judge(case):
    data = FIXTURE["cases"][case]
    before_inv, before = side(FIXTURE["base"], FIXTURE["base_object"])
    after_inv, after = side(data["head"], data["head_object"])
    return layout.atoms(H, "Foo", before_inv, before, after_inv, after)


class RealCompiler(unittest.TestCase):
    def test_the_base_layout_is_measured_from_constants(self):
        _, measured = side(FIXTURE["base"], FIXTURE["base_object"])
        self.assertEqual((measured["size"], measured["align"]), (24, 4))
        self.assertEqual({name: (m["offset"], m["width"]) for name, m in measured["members"].items()},
                         {"pub": (4, 4), "a": (8, 4), "b": (12, 2), "c": (14, 2), "m_unk0x10": (16, 8)})
        self.assertEqual(measured["members"]["m_unk0x10"]["type"], "char[8]")

    def test_every_case_gives_the_expected_atoms(self):
        for case, data in FIXTURE["cases"].items():
            if data["expected"] == "held":
                continue
            with self.subTest(case=case):
                record = judge(case)
                if data["expected"] == "compatible":
                    self.assertEqual(record, {"complete": True, "compatible_shape": True, "atoms": []})
                else:
                    got = sorted([a["kind"], a["identity"]] for a in record["atoms"])
                    self.assertEqual(got, sorted(data["expected"]))
                    self.assertFalse(record["compatible_shape"])

    def test_renamed_and_split_storage_is_compatible_shape(self):
        for case in ("rename", "split", "comment-only"):
            self.assertTrue(judge(case)["compatible_shape"], case)

    def test_a_member_atom_carries_before_and_after_offsets(self):
        swap = {a["identity"]: a for a in judge("swap")["atoms"]}
        self.assertEqual((swap["a"]["before"]["offset"], swap["a"]["after"]["offset"]), (8, 12))
        self.assertEqual(swap["a"]["after"]["width"], 4)

    def test_an_unreadable_changed_statement_holds(self):
        with self.assertRaisesRegex(layout.Held, "cannot read may change layout"):
            before_inv = layout.inventory(FIXTURE["base"].encode(), "Foo")
            after_inv = layout.inventory(FIXTURE["cases"]["macro"]["head"].encode(), "Foo")
            fake = {"size": 24, "align": 4, "members": {}}
            layout.atoms(H, "Foo", before_inv, fake, after_inv, fake)

    def test_a_probe_object_of_another_class_is_held(self):
        inv = layout.inventory(FIXTURE["base"].encode(), "Foo")
        with self.assertRaises(layout.Held):
            layout.measure(bytes.fromhex(FIXTURE["base_object"]), "include/Other.h", "Foo", inv)


class Probe(unittest.TestCase):
    def test_the_probe_befriends_the_class_and_measures_every_member(self):
        header, source, inv = layout.probe(FIXTURE["base"].encode(), H, "Foo")
        self.assertEqual(header.count(b"friend struct __bfme_layout_"), 1)
        self.assertEqual(header.replace(header[header.index(b" friend"):header.index(b";", header.index(b" friend")) + 1],
                                        b""), FIXTURE["base"].encode())
        for name, _ in inv["members"]:
            self.assertIn(f"offsetof(Foo, {name})".encode(), source)
        self.assertTrue(source.startswith(b'#include "Foo.h"'))

    def test_methods_typedefs_and_constructors_are_not_layout_risks(self):
        for statement in ("void f(int x);", "int getA() const { return a; }", "typedef int T;", "Foo();",
                          "~Foo();", "static int count;", "friend class Bar;", "class Fwd;", "enum E { A, B };"):
            self.assertFalse(layout._layout_risk(statement, "Foo"), statement)
        for statement in ("DECLARE_STORAGE(x);", "int a : 3;", "int a, b;", "void (*fn)(int);"):
            self.assertTrue(layout._layout_risk(statement, "Foo"), statement)

    def test_classes_it_cannot_read_are_held(self):
        for text, name in ((b"struct Foo { int a; int a; };", "Foo"), (b"struct Bar { int a; };", "Foo"),
                           (b"struct Foo { int a; };", "Outer::Foo")):
            with self.assertRaises(layout.Held):
                layout.inventory(text, name)


if __name__ == "__main__":
    unittest.main()
