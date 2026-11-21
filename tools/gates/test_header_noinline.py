import unittest

from header_noinline import check_noinline


PATH = "include/Example.h"


class NoInline(unittest.TestCase):
    def test_explicit_control_in_supported_attribute_spellings(self):
        for declaration in (
            "__declspec(noinline) void example();",
            "__attribute__((noinline)) void example();",
            "__attribute__((__noinline__, cold)) void example();",
            "[[msvc::noinline]] void example();",
            "__noinline void example();",
            "#define EXAMPLE_DECL __declspec(noinline)",
        ):
            with self.subTest(declaration=declaration):
                finding, = check_noinline(PATH, "", declaration)
                self.assertEqual((finding.path, finding.line, finding.rule), (PATH, 1, "H8"))

    def test_comments_literals_and_same_spelled_variable_do_not_match(self):
        for declaration in (
            "// __declspec(noinline) void test();",
            "/* [[msvc::noinline]] */ int named;",
            'const char *named = "__declspec(noinline)";',
            'const char *named = R"raw([[msvc::noinline]])raw";',
            '[[example::attribute(noinline)]] void ordinary();',
            "int noinline = 0;",
        ):
            with self.subTest(declaration=declaration):
                self.assertEqual(check_noinline(PATH, "", declaration), [])

    def test_existing_attribute_survives_formatting_and_body_changes(self):
        before = "class A { __declspec(noinline) void run() { hit(); } };"
        after = '''
#include "Example.h"
class A {
    // Ordinary explanation.
    __declspec( noinline ) void run() { miss(); }
};
'''
        self.assertEqual(check_noinline(PATH, before, after), [])

    def test_new_member_does_not_inherit_old_member_exception(self):
        before = "class A { __declspec(noinline) void run(); };"
        after = "class A { __declspec(noinline) void stop(); };"
        self.assertEqual(len(check_noinline(PATH, before, after)), 1)

    def test_moving_control_to_a_different_owner_requires_new_decision(self):
        before = "class A { __declspec(noinline) void run(); };"
        after = before + "\nclass B { __declspec(noinline) void run(); };"
        finding, = check_noinline(PATH, before, after)
        self.assertEqual(finding.line, 2)

    def test_lexical_line_splice_reports_physical_attribute_line(self):
        before = ""
        after = "#define CONTROL __declspec(\\\n noinline)\n"
        finding, = check_noinline(PATH, before, after)
        self.assertEqual(finding.line, 2)


if __name__ == "__main__":
    unittest.main()
