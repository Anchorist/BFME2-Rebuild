"""Tests for ci/header-witness/h5_witness.py. The objects in fixtures/witness-vc71.json were compiled by VC7.1 from the
synthetic header and source stored beside them: the unmodified head and, per atom, both header variants."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import h5_witness as witness  # noqa: E402

FIXTURE = json.loads((Path(__file__).parent / "fixtures/witness-vc71.json").read_text())
HEADER = FIXTURE["header"].encode()
HEAD = bytes.fromhex(FIXTURE["head"])
NAMES = FIXTURE["functions"]


def row(**changes):
    base = {"rva": 0x1234, "path": "src/t.cpp", "head_object": hashlib.sha256(HEAD).hexdigest(),
            "before": {"credited": False}, "after": {"credited": True, "proof": True, "status": "MATCH"}}
    base.update(changes)
    return base


def atom(key, offset=None):
    kind, identity = key.split(":")
    data = FIXTURE["atoms"][key]
    return {"header": "include/Foo.h", "qualified_class": "Foo", "kind": kind, "identity": identity,
            "after": {"offset": data["offset"] if offset is None else offset, "width": data["width"], "type": "int"}}


def objects(key):
    data = FIXTURE["atoms"][key]
    return bytes.fromhex(data["control"]), bytes.fromhex(data["moved"])


def judge(key, label, **kwargs):
    control, moved = objects(key)
    return witness.evaluate(kwargs.get("atom") or atom(key), kwargs.get("row") or row(), kwargs.get("head", HEAD),
                            kwargs.get("control", control), kwargs.get("moved", moved), NAMES[label])


def witnessed(key):
    found = set()
    for label in NAMES:
        try:
            judge(key, label)
            found.add(label)
        except witness.Held:
            pass
    return found


class RealCompiler(unittest.TestCase):
    def test_each_atom_is_witnessed_exactly_by_the_functions_whose_code_uses_it(self):
        for key, data in FIXTURE["atoms"].items():
            with self.subTest(atom=key):
                self.assertEqual(witnessed(key), set(data["expected"]))

    def test_uses_through_a_getter_a_macro_this_and_a_derived_class_count(self):
        self.assertIn("useA", witnessed("member:a"))         # inline getter
        self.assertIn("raw", witnessed("member:a"))          # unqualified, in a derived class's member function
        self.assertIn("sum", witnessed("member:b"))          # FIRST_B(this) macro plus this->b[1]
        self.assertIn("viaDerived", witnessed("member:pub"))  # through a pointer to a derived struct

    def test_a_call_to_an_out_of_line_function_is_a_named_hold(self):
        with self.assertRaisesRegex(witness.Held, "no use of it was observed"):
            judge("member:a", "viaCall")

    def test_code_that_depends_on_the_class_size_is_held_not_witnessed(self):
        for label in ("sizeCond", "sizeOnly"):
            with self.assertRaisesRegex(witness.Held, "depends on the class size"):
                judge("member:pub", label)

    def test_a_virtual_slot_is_witnessed_only_by_its_callers(self):
        self.assertEqual(witnessed("slot:g"), {"callG"})

    def test_the_record_is_what_layout_check_reads(self):
        record = judge("member:a", "useA")
        for key in ("header", "qualified_class", "kind", "identity", "receiver_type", "observed", "operation",
                    "rva", "path", "head_object"):
            self.assertIn(key, record)
        self.assertEqual((record["receiver_type"], record["operation"]), ("Foo", "access"))
        self.assertEqual(record["witness"]["form"], "W1-swapped-slot-2")
        self.assertGreater(record["witness"]["offset_shift"], 0)
        self.assertEqual((record["witness"]["size"], record["witness"]["align"]), (24, 4))


class Adverse(unittest.TestCase):
    def test_a_row_not_newly_credited_witnesses_nothing(self):
        for changed in (row(before={"credited": True}), row(after={"credited": True, "proof": False, "status": "MATCH"}),
                        row(after={"credited": True, "proof": True, "status": "NONMATCH"})):
            with self.assertRaisesRegex(witness.Held, "not newly credited"):
                judge("member:a", "useA", row=changed)

    def test_an_unauthenticated_head_object_is_held(self):
        with self.assertRaisesRegex(witness.Held, "not the authenticated object"):
            judge("member:a", "useA", row=row(head_object="0" * 64))

    def test_a_layout_atom_with_the_wrong_offset_is_held(self):
        with self.assertRaisesRegex(witness.Held, "no operand addresses"):
            judge("member:a", "useA", atom=atom("member:a", offset=40))

    def test_swapped_variants_are_held(self):
        control, moved = objects("member:a")
        with self.assertRaises(witness.Held):
            judge("member:a", "useA", control=moved, moved=control)

    def test_variants_from_another_atom_are_held(self):
        control, moved = objects("member:b")
        with self.assertRaisesRegex(witness.Held, "layout constant"):
            judge("member:a", "useA", control=control, moved=moved)

    def test_the_same_object_twice_is_no_witness(self):
        control, _ = objects("member:a")
        with self.assertRaises(witness.Held):
            judge("member:a", "useA", moved=control)

    def test_a_function_missing_from_the_object_holds(self):
        control, moved = objects("member:a")
        with self.assertRaises(witness.Held):
            witness.evaluate(atom("member:a"), row(), HEAD, control, moved, "?absent@@YAXXZ")


def coff(overflow):
    """A minimal i386 COFF: one COMDAT code section holding ?f@@YAXXZ with one relocation to _target. With
    overflow, the relocation table starts with the count entry (counting itself) as the compiler writes it."""
    import struct
    body = b"\xe8\x00\x00\x00\x00\xc3"
    relocs = (struct.pack("<IIH", 2, 0, 0) if overflow else b"") + struct.pack("<IIH", 1, 2, 0x14)
    flags = 0x60000020 | witness.COMDAT | (witness.RELOC_OVERFLOW if overflow else 0)
    raw_at = 20 + 40
    rel_at = raw_at + len(body)
    symtab = rel_at + len(relocs)
    section = struct.pack("<8sIIIIIIHHI", b".text", 0, 0, len(body), raw_at, rel_at, 0,
                          0xFFFF if overflow else 1, 0, flags)
    def symbol(name, value, number, kind, klass):
        return struct.pack("<8sIhHBB", name.ljust(8, b"\0"), value, number, kind, klass, 0)
    names = b"?f@@YAXXZ\0"
    long_name = struct.pack("<II", 0, 4)
    symbols = (symbol(b".text", 0, 1, 0, 3) + long_name + struct.pack("<IhHBB", 0, 1, 0x20, 2, 0)
               + symbol(b"_target", 0, 0, 0x20, 2))
    strings = struct.pack("<I", 4 + len(names)) + names
    header = struct.pack("<HHIIIHH", 0x14C, 1, 0, symtab, 3, 0, 0)
    return header + section + body + relocs + symbols + strings


class Coff(unittest.TestCase):
    def test_overflowed_relocations_are_read_past_the_count_entry(self):
        plain, overflowed = witness.function(coff(False), "?f@@YAXXZ"), witness.function(coff(True), "?f@@YAXXZ")
        self.assertEqual(plain, overflowed)
        self.assertEqual(plain[1], ((1, 0x14, "_target"),))


class Plan(unittest.TestCase):
    def test_the_two_variants_differ_only_in_names(self):
        control, moved = witness.plan(HEADER, "Foo", "member", "a", "include/Foo.h")
        probe = ("__bfme_w_" + witness.tag("include/Foo.h", "Foo", "a")).encode()
        self.assertNotEqual(control, moved)
        self.assertEqual(control.replace(probe + b";", b"#;").replace(b"int a;", b"int @;"),
                         moved.replace(probe + b";", b"@;").replace(b"int a;", b"int #;"))

    def test_both_variants_emit_the_size_and_alignment_constants(self):
        for variant in witness.plan(HEADER, "Foo", "member", "a", "include/Foo.h"):
            self.assertIn(b'_size = sizeof(Foo);', variant)
            self.assertIn(b'_align = __alignof(Foo);', variant)

    def test_the_appended_member_keeps_its_access(self):
        control, _ = witness.plan(HEADER, "Foo", "member", "a", "include/Foo.h")
        self.assertIn(b"\nprotected:\n    int __bfme_w_", control)
        control, _ = witness.plan(b"struct S\n{\n    int x;\n};\n", "S", "member", "x")
        self.assertIn(b"\npublic:\n", control)

    def test_comments_strings_and_directives_do_not_confuse_it(self):
        text = (b"#define BRACE {\n// class Foo { int a; };\nstruct Foo\n{\n    const char *s; /* a; } */\n"
                b"    const char *t; // \"}\" a;\n    int a;\n};\n")
        control, moved = witness.plan(text, "Foo", "member", "a")
        self.assertNotEqual(control, moved)

    def test_a_conditional_second_declaration_is_held(self):
        text = b"struct Foo\n{\n#if 0\n    int a;\n#else\n    long a;\n#endif\n};\n"
        with self.assertRaises(witness.Held):
            witness.plan(text, "Foo", "member", "a")

    def test_forms_it_cannot_read_are_held(self):
        cases = [
            (b"struct Foo { int a : 3; };", "member", "a"),            # bit-field
            (b"struct Foo { int a, b; };", "member", "a"),             # two declarators
            (b"struct Foo { DECLARE(a); };", "member", "a"),           # made by a macro
            (b"struct Foo { int a; }; struct Foo { int a; };", "member", "a"),
            (b"struct Foo { int a; } theFoo;", "member", "a"),         # declared with a variable
            (b"struct Bar { int a; };", "member", "a"),                # no such class
            (b"struct Foo { int a; };", "size", "Foo"),
            (b"struct Foo { int a; };", "base", "Base"),
            (b"struct Foo { virtual void g() {} };", "slot", "g"),     # inline virtual body
            (b"struct Foo { int a; };", "member", "a b"),
        ]
        for text, kind, identity in cases:
            with self.subTest(text=text, kind=kind):
                with self.assertRaises(witness.Held):
                    witness.plan(text, "Foo", kind, identity)

    def test_nested_and_template_classes_are_held(self):
        for name in ("Outer::Foo", "Foo<int>"):
            with self.assertRaises(witness.Held):
                witness.plan(b"struct Foo { int a; };", name, "member", "a")


if __name__ == "__main__":
    unittest.main()
