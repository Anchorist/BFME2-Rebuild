import unittest

from header_inventory import FileIdentity, FileText
from header_lexical_inventory import inventory, compare_inventories
from header_removal import check_removals


HEADER = "include/Foo.h"
OLD = """#pragma once
#ifndef PROJECT_FOO_H
#define PROJECT_FOO_H
#include "Other.h"
namespace G {
class Foo : public Parent {
protected:
    long member;
public:
    int read(int first) const;
    int read(unsigned second) const;
    const _STL::vector<Item *> & list();
    struct Slot { int item; };
    template<class T> void complex(T (*func)(int));
};
}
#endif
"""


def view(before=OLD, after=OLD):
    return compare_inventories((FileText(FileIdentity(HEADER, "1" * 40, "2" * 40), before, after),))


class ExplicitDeclarations(unittest.TestCase):
    def verdict(self, base, candidate, trailers=()):
        before, after, unresolved = view(base, candidate)
        self.assertEqual(unresolved, ())
        return check_removals(before, after, set(trailers), complete=True)

    def test_qualified_members_overloads_and_nested_types(self):
        names = [item.qualified for item in inventory(HEADER, OLD).declarations]
        self.assertEqual(names.count("G::Foo::read"), 2)
        for name in ("G::Foo", "G::Foo::Slot", "G::Foo::Slot::item", "G::Foo::member", "G::Foo::list"):
            self.assertIn(name, names)
        self.assertNotIn("G::Foo::complex", names)

    def test_nested_class_and_method_removal_do_not_match_unrelated_name(self):
        after = OLD.replace("    struct Slot { int item; };", "")
        after += "namespace Other { struct Slot { int item; }; }\n"
        _, _, unresolved = view(OLD, after)
        self.assertTrue(unresolved)
        after = OLD.replace("    struct Slot { int item; };", "")
        findings = self.verdict(OLD, after, ("Other::Slot", "Other::Slot::item"))
        self.assertEqual([finding.line for finding in findings], [13, 13])

    def test_remove_only_one_overload_and_read_its_exact_trailer(self):
        after = OLD.replace("int read(int first) const;", "")
        finding, = self.verdict(OLD, after, ("Foo::read",))
        self.assertEqual(finding.line, 10)
        self.assertEqual(self.verdict(OLD, after, ("G::Foo::read",)), [])

    def test_change_only_spelling_of_parameter_comment_and_access(self):
        after = OLD.replace("int first", "int renamed /* named after its purpose */")
        after = after.replace("public:\n    int read", "protected:\n    int read")
        self.assertEqual(self.verdict(OLD, after), [])

    def test_pointer_and_template_parameter_identity(self):
        a = "namespace G { void use(Vector<Pair<int, X>> const *value); }\n"
        b = a.replace("value", "item")
        self.assertEqual(self.verdict(a, b), [])
        finding, = self.verdict(a, a.replace("int, X", "float, X"))
        self.assertEqual((finding.line, finding.rule), (1, "H4"))

    def test_opaque_edit_is_visible_and_existing_opaque_text_is_stable(self):
        after = OLD.replace("(*func)(int)", "(*func)(int, int)")
        _, _, uncertain = view(OLD, after)
        self.assertEqual({item.line for item in uncertain}, {14})
        self.assertEqual(view()[2], ())

    def test_balanced_preprocessor_arms_do_not_hide_a_removed_declaration(self):
        before = "#pragma once\n#if ONE\nint a();\n#else\nint b();\n#endif\n"
        after = before.replace("int b();", "int c();")
        finding, = self.verdict(before, after)
        self.assertEqual(finding.line, 5)
        self.assertEqual(self.verdict(before, before.replace("ONE", "TWO"), ("a", "b")), [])

    def test_conditional_crossing_a_declaration_stays_opaque(self):
        before = "class Base { int f; };\n"
        after = "#if CONTEXT\nclass Base {\n#endif\nint f; };\n"
        self.assertTrue(view(before, after)[2])

    def test_structure_assertions_are_h5_inputs_not_h4_declarations(self):
        before = "struct Slot { int value; };\n"
        after = before + ("typedef char SlotSize[(sizeof(Slot) == 0x4) ? 1 : -1];\n"
                          "typedef char SlotOffset[offsetof(Slot, value)==0x0?1:-1];\n"
                          "typedef char SlotSum[(sizeof(Slot)+sizeof(Int)==8)?1:-1];\n")
        self.assertEqual(self.verdict(before, after), [])
        self.assertEqual(self.verdict(after, before), [])
        alias = "typedef char NamedArray[4];\n"
        self.assertEqual(len(self.verdict(alias, "")), 1)

    def test_friends_have_a_separate_qualified_relationship(self):
        before = "namespace Game { class Host {}; class Buddy; }\n"
        after = before.replace("Host {};", "Host { friend class Buddy; };")
        self.assertEqual(self.verdict(before, after), [])
        finding, = self.verdict(after, before)
        self.assertIn("Game::Buddy", finding.message)

    def test_enum_literals_and_implicit_successors(self):
        before = "namespace Game { enum Command { Stop = 2, Pause, Start = 0x11 }; }\n"
        self.assertEqual(self.verdict(before, before.replace("0x11", "17")), [])
        findings = self.verdict(before, before.replace("Stop = 2", "Stop = 4"))
        self.assertEqual(len(findings), 2)
        self.assertTrue(any("Game::Pause" in finding.message for finding in findings))

    def test_templates_collect_nested_members(self):
        before = "template<class T> class List { struct Node { T value; }; T *find(); };\n"
        after = before.replace("T *find();", "T *scan();")
        finding, = self.verdict(before, after)
        self.assertIn("List::find", finding.message)
        names = {item.qualified for item in inventory(HEADER, before).declarations}
        self.assertIn("List::Node::value", names)

    def test_constructor_initializers_and_expression_sized_members(self):
        before = "class Name { Name(); unsigned char gap[0x120 - 0x04]; };\n"
        after = before.replace("Name();", "Name() : Base<unsigned short>(value()), state(0) {}")
        self.assertEqual(self.verdict(before, after), [])
        finding, = self.verdict(after, after.replace("gap[", "bytes["))
        self.assertIn("Name::gap", finding.message)

    def test_function_pointer_typedef_is_a_named_alias(self):
        before = "namespace G { typedef void (__cdecl *Handler)(int count); }\n"
        after = before.replace("count", "value")
        self.assertEqual(self.verdict(before, after), [])
        finding, = self.verdict(before, before.replace("*Handler", "*Callback"))
        self.assertIn("G::Handler", finding.message)

    def test_function_body_edit_does_not_remove_declaration(self):
        before = "class Host { int act() { return 1; } };\n"
        self.assertEqual(self.verdict(before, before.replace("1;", "2;")), [])
        self.assertEqual(self.verdict(before, "class Host { int act(); };\n"), [])

    def test_stable_opaque_lines_do_not_hide_a_field_rename(self):
        after = OLD.replace("long member;", "long preciseMember;")
        finding, = self.verdict(OLD, after)
        self.assertEqual((finding.line, finding.rule), (8, "H4"))


if __name__ == "__main__":
    unittest.main()
