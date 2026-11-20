"""Fixtures for the advisory result and its independent presentation."""

from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from git_objects import Git
import workflow
from shadow_types import compare, measure

PATH = "include/Example.h"
TABLE = "| Rule | Result |\n| --- | --- |\n| G4 Stand-in types | Pass |\n"


def known(name):
    return name == "File"


class TypeSwapTests(unittest.TestCase):
    def compare(self, old, new, **flags):
        return compare(old, new, PATH, known, **flags)

    def test_b027_direct(self):
        before = "struct Holder {\n File *m_file;\n};\n"
        after = before.replace("File *", "unsigned int ")
        source, = self.compare(before, after)
        self.assertEqual((source.name, source.line, source.old_type, source.new_type),
                         ("m_file", 2, "File *", "unsigned int"))

    def test_direct_class_spelling(self):
        self.assertEqual(1, len(self.compare("File file;\n", "unsigned int file;\n")))
        self.assertEqual(1, len(self.compare("struct File file;\n", "int file;\n")))
        self.assertEqual([], self.compare("Other item;\n", "int item;\n"))

    def test_different_name_and_scope(self):
        self.assertEqual([], self.compare("File *a;\n", "int b;\n"))
        before = "struct Old {\n File *a;\n};\n"
        self.assertEqual([], self.compare(before, "struct New {\n int a;\n};\n"))

    def test_unrelated_declarations_and_comments(self):
        self.assertEqual([], self.compare("int a;\n", "long a;\n"))
        self.assertEqual([], self.compare("// File *a;\n", "// int a;\n"))
        self.assertEqual([], self.compare("#define T File *a;\n", "#define T int a;\n"))
        self.assertEqual([], self.compare('char const *s = "File *a;";\n',
                                          'char const *s = "int a;";\n'))
        self.assertEqual([], self.compare("File *get();\n", "int get();\n"))

    def test_duplicate_declaration_identity_is_ambiguous(self):
        self.assertEqual([], self.compare("File *a;\nFile *a;\n", "int a;\nunsigned int a;\n"))

    def test_multiline_is_research_only(self):
        before = "struct A {\n  File *\n    m_file;\n};\n"
        after = before.replace("File *", "unsigned int")
        self.assertEqual([], self.compare(before, after))
        self.assertEqual(1, len(self.compare(before, after, multiline=True)))

    def test_local_typedefs_are_research_only(self):
        common = "typedef File *Handle;\nusing Small = unsigned int;\n"
        old, new = common + "Handle h;\n", common + "Small h;\n"
        self.assertEqual([], self.compare(old, new))
        self.assertEqual(1, len(self.compare(old, new, use_aliases=True)))

    def test_ambiguous_alias_is_unavailable(self):
        common = "#if ONE\nusing Handle = File *;\n#else\nusing Handle = int;\n#endif\n"
        self.assertEqual([], self.compare(common + "Handle h;\n", common + "int h;\n", use_aliases=True))

    def test_signed_builtin_and_cv_pointer(self):
        hits = self.compare("const File * const p;\n", "unsigned __int64 p;\n")
        self.assertEqual(len(hits), 1)
        self.assertEqual([], self.compare("File *a;\n", "bool a;\n"))

    def test_pointer_to_class_is_outside_the_advisory(self):
        self.assertEqual([], self.compare("File *a;\n", "File a;\n"))

    def test_real_git_separate_header_class(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            def run(*args):
                return subprocess.check_output(["git", "-C", folder, *args], stderr=subprocess.PIPE).decode().strip()
            run("init", "-q", "--template=")
            for field, value in (("name", "Fixture"), ("email", "fixture@example.test")):
                run("config", "user." + field, value)
            (repo / "include").mkdir()
            (repo / "include/Shared.h").write_text("class Widget {};\n")
            source = repo / PATH
            source.write_text("Widget member;\n")
            run("add", PATH, "include/Shared.h")
            run("commit", "-qm", "Typed")
            before = run("rev-parse", "HEAD^{tree}")
            source.write_text("unsigned int member;\n")
            run("add", PATH)
            after = run("write-tree")
            with Git(repo) as objects:
                row, = measure(objects, before, after)
            self.assertEqual((row["path"], row["line"]), (PATH, 1))

    def test_report_advisory_unavailable_keeps_enforced_row(self):
        with patch.object(workflow.subprocess, "run", side_effect=subprocess.TimeoutExpired("shadow", 12)):
            report = workflow.append_advisory(TABLE, workflow.Git(Path(".")), "base", "tree", Path("."))
        self.assertIn("| G4 Stand-in types | Pass |\n", report)
        self.assertIn("| G4b Type swaps | Unavailable (advisory) |\n", report)

    def test_report_escapes_advisory_fields(self):
        result = subprocess.CompletedProcess(["shadow"], 0, stdout=(
            b'[{"path":"<unsafe>.h","name":"a","old_type":"File *","new_type":"int","line":10}]'
        ))
        with patch.object(workflow.subprocess, "run", return_value=result):
            report = workflow.append_advisory(TABLE, workflow.Git(Path(".")), "base", "tree", Path("."))
        self.assertIn("| G4b Type swaps | Review 1 (advisory) |\n", report)
        self.assertIn("<code>&lt;unsafe&gt;.h:10</code>", report)
        self.assertNotIn("<unsafe>", report)


if __name__ == "__main__":
    unittest.main()
