import unittest

from header_inline import classify_changed, shape
from header_inline_scan import changed_discovery, scan


PATH = "include/Host.h"
OLD = """#pragma once
namespace Game {
class Owner : public Base {
public:
    int get() const { return field; }
    void change(int input) { this->field = input; }
    void extra(int input) { Base::extra(input); }
    int other() { return use(field); }
private:
    int field;
};
}
"""


class InlineDiscovery(unittest.TestCase):
    def test_qualified_explicit_methods_and_bindings(self):
        found = scan(PATH, OLD)
        self.assertFalse(found.unresolved)
        actual = {item.qualified: shape(item) for item in found.bodies}
        self.assertEqual(actual, {
            "Game::Owner::get": "member-read",
            "Game::Owner::change": "member-write",
            "Game::Owner::extra": "base-forward",
            "Game::Owner::other": None,
        })

    def test_constructor_initializers_and_local_bodies(self):
        source = """class Name : public Base {
public:
    Name(int v) : Base(v) {}
    int read() { if (other()) { return data; } return 0; }
    int data;
};
"""
        found = scan(PATH, source)
        self.assertFalse(found.unresolved)
        self.assertEqual([x.qualified for x in found.bodies], ["Name::Name", "Name::read"])
        self.assertTrue(found.bodies[0].initializers)
        self.assertTrue(all(shape(x) is None for x in found.bodies))

    def test_changed_opaque_declarator_is_named(self):
        old = "struct Type { unsigned value; };\n"
        after = old.replace("unsigned value;", "int operator()(int x) { return x; }")
        _, _, ambiguous = changed_discovery(PATH, old, after)
        self.assertTrue(ambiguous)

    def test_only_changed_body_needs_behavior(self):
        after = OLD.replace("return field;", "return field + 1;")
        before, current, ambiguous = changed_discovery(PATH, OLD, after)
        self.assertFalse(ambiguous)
        simple, needed = classify_changed(before, current, complete=True)
        self.assertEqual(simple, [])
        self.assertEqual([item.qualified for item in needed], ["Game::Owner::get"])

    def test_comments_or_line_moves_do_not_change_an_inline_body(self):
        before, after, ambiguous = changed_discovery(PATH, OLD, OLD.replace("return field;", "return /* field */ field;"))
        self.assertFalse(ambiguous)
        self.assertEqual(classify_changed(before, after, complete=True), ([], []))


if __name__ == "__main__":
    unittest.main()
