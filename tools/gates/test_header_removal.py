"""Focused controls for exact declaration removal acknowledgment."""

from pathlib import Path
import os
import subprocess
import tempfile
import unittest

from git_objects import Git, ObjectError
from header_removal import Declaration, acknowledgments, check_removals

OLD = Declaration("include/Foo.h", 14, "Game::Foo::Read", "?Read@Foo@Game@@QAEHH@Z")
SECOND = Declaration("include/Foo.h", 17, "Game::Foo::Read", "?Read@Foo@Game@@QAEH_N@Z")
NEW = Declaration("include/Foo.h", 13, "Game::Foo::Read", "?Read@Foo@Game@@QAEHI@Z")


class Removals(unittest.TestCase):
    def test_old_line_and_qualified_remedy(self):
        finding, = check_removals([OLD], [NEW], set(), complete=True)
        self.assertEqual((finding.path, finding.line, finding.rule), ("include/Foo.h", 14, "H4"))
        self.assertIn("Removed-Declaration: Game::Foo::Read", finding.remedy)

    def test_explicit_trailer_acknowledges_the_intent(self):
        self.assertEqual(check_removals([OLD], [NEW], {"Game::Foo::Read"}, complete=True), [])

    def test_bare_and_wrong_scope_do_not_acknowledge_member(self):
        result = check_removals([OLD], [], {"Read", "Other::Foo::Read"}, complete=True)
        self.assertEqual(len(result), 1)

    def test_moved_declaration_keeps_identity(self):
        moved = Declaration("include/Other/Foo.h", 45, OLD.qualified, OLD.identity)
        self.assertEqual(check_removals([OLD], [moved], set(), complete=True), [])

    def test_retained_overload_does_not_cover_removed_overload(self):
        finding, = check_removals([OLD, SECOND], [SECOND], set(), complete=True)
        self.assertEqual(finding.line, OLD.line)

    def test_incomplete_inventory_cannot_pass(self):
        with self.assertRaisesRegex(ObjectError, "complete"):
            check_removals([], [], set(), complete=False)

    def test_unsupported_inventory_has_named_h4_error(self):
        with self.assertRaisesRegex(ObjectError, "H4"):
            check_removals([Declaration("include/Foo.h", 2, "(!)", "identity")], [], {}, complete=True)

    def test_git_trailer_block_exactly(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name)
            git = ["git", "-C", name, "-c", f"core.hooksPath={os.devnull}"]
            env = os.environ | {"GIT_AUTHOR_NAME": "Header control", "GIT_COMMITTER_NAME": "Header control",
                                "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                                "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}
            subprocess.run(git + ["init", "-q"], check=True, env=env)
            tree = subprocess.check_output(git + ["write-tree"], env=env).strip().decode()
            msg = ("Header cleanup\n\nRemoved-Declaration: Game::WillNotPass::Read\n\n"
                   "That earlier paragraph is ordinary text.\n\n"
                   "Removed-Declaration: Game::Foo::Read\n"
                   "Removed-Declaration: Game::Foo::operator==\n"
                   "Removed-Declaration: Game::Bar::~Bar\n"
                   "Removed-Declaration: Game::Foo::Read()\n")
            head = subprocess.check_output(git + ["commit-tree", tree], input=msg.encode(), env=env).strip().decode()
            with Git(path) as repo:
                self.assertEqual(acknowledgments(repo, head),
                                 {"Game::Foo::Read", "Game::Foo::operator==", "Game::Bar::~Bar"})


if __name__ == "__main__":
    unittest.main()
