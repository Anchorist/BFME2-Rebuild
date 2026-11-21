"""Tests for ci/header-witness/h4_declarations.py. fixtures/declarations-vc71.json holds real VC7.1 `-E` output for
the synthetic header stored beside it, before and after one change. Needs tools/gates on the path."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "tools" / "gates"))
import h4_declarations as declarations  # noqa: E402
import header_lexical_inventory as lexical  # noqa: E402

FIXTURE = json.loads((Path(__file__).parent / "fixtures/declarations-vc71.json").read_text())
HEADER, RELATIVE = "include/Game/Unit.h", "Game/Unit.h"


def side(name):
    case = FIXTURE["cases"][name]
    return case["preprocessed"], HEADER, RELATIVE, case["header"]


def names(items):
    return {item.qualified for item in items}


class RealPreprocessor(unittest.TestCase):
    def test_own_lines_keep_their_numbers(self):
        text = declarations.own_text(FIXTURE["cases"]["before"]["preprocessed"], HEADER, RELATIVE)
        lines = text.split("\n")
        self.assertEqual(lines[9].strip(), "Int getCount() const { return m_Count; }")   # line 10 of the header
        self.assertNotIn("typedef int Int", text)                                         # Types.h stays out

    def test_macro_made_members_are_seen_and_a_dead_branch_is_not(self):
        found, unreadable = declarations.read(*side("before"), lexical)
        self.assertTrue({"Unit::getCount", "Unit::m_Count", "Unit::shown", "Unit::removedLater"} <= names(found))
        self.assertNotIn("Unit::hidden", names(found))
        self.assertEqual(unreadable, ())

    def test_a_layout_assertion_is_read_from_the_raw_line(self):
        _, unreadable = declarations.read(*side("before"), lexical)
        self.assertEqual(unreadable, ())
        expanded = lexical.inventory(HEADER, declarations.own_text(*side("before")[:3]))
        self.assertTrue(any(item.tokens[:2] == ("typedef", "char") for item in expanded.unknown))

    def test_the_comparison_shows_the_added_and_the_removed_declaration(self):
        before, after, complete, _ = declarations.compare(side("before"), side("after"), lexical)
        self.assertTrue(complete)
        self.assertEqual(names(after) - names(before), {"Unit::getHealth"})
        self.assertEqual(names(before) - names(after), {"Unit::removedLater"})

    def test_raw_reading_misses_what_the_compiler_expands(self):
        raw = lexical.inventory(HEADER, FIXTURE["cases"]["before"]["header"])
        self.assertNotIn("Unit::getCount", names(raw.declarations))


class Shape(unittest.TestCase):
    def test_output_that_never_enters_the_header_holds(self):
        with self.assertRaises(declarations.Held):
            declarations.own_text('#line 1 "C:\\\\probe\\\\p.cpp"\nint x;\n', HEADER, RELATIVE)

    def test_paths_match_by_suffix_case_and_separator(self):
        self.assertTrue(declarations._same_file("C:\\\\probe\\\\game\\\\unit.h", "Game/Unit.h"))
        self.assertTrue(declarations._same_file("z:/probe/Game/Unit.h", "Game/Unit.h"))
        self.assertFalse(declarations._same_file("C:\\\\probe\\\\OtherGame\\\\Unit.h", "Game/Unit.h"))

    def test_an_unreadable_statement_makes_the_side_incomplete(self):
        text = '#line 1 "C:\\\\probe\\\\Game\\\\Unit.h"\nclass Unit { int a : 3; };\n'
        _, _, complete, unreadable = declarations.compare((text, HEADER, RELATIVE, "class Unit { int a : 3; };\n"),
                                                          None, lexical)
        self.assertFalse(complete)
        self.assertTrue(unreadable)


if __name__ == "__main__":
    unittest.main()
