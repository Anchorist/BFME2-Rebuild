"""Focused source-tree controls for the Draft admission check."""
import unittest

from git_objects import Delta, Entry
from header_draft import check_drafts


class Policy:
    limits = {"bytes_per_file": 1024**2}

    def kind(self, path):
        if path.startswith("include/") and path.endswith((".h", ".hpp")):
            return "header"
        if path.startswith("src/") and path.endswith(".cpp"):
            return "source"
        return None


class Trees:
    def __init__(self, before, after):
        self.data = {}
        self.entries = {"before": self.make(before), "after": self.make(after)}

    def make(self, data):
        rows = {}
        for path, source in sorted(data.items()):
            oid = len(self.data)
            self.data[oid] = source.encode()
            rows[path] = Entry("100644", oid)
        return rows

    def blob(self, oid, limit):
        data = self.data[oid]
        return len(data), data if len(data) <= limit else None

    def tree(self, revision, *paths):
        return ((path, item) for path, item in self.entries[revision].items()
                if any(path == root or path.startswith(root + "/") for root in paths))

    def diff(self, before, after):
        old, new = self.entries[before], self.entries[after]
        for path in sorted(old.keys() | new.keys()):
            o, n = old.get(path), new.get(path)
            if o is None or n is None or self.data[o.oid] != self.data[n.oid]:
                yield Delta(path, o, n)


def run(before, after):
    return check_drafts(Trees(before, after), Policy(), "before", "after")


class DraftMoves(unittest.TestCase):
    old = "include/Draft/Thing.h"
    new = "include/Common/Thing.h"
    src = "src/Thing.cpp"
    definition = "namespace Game { class Thing {}; }\n"

    def test_permanent_type_with_retained_draft(self):
        before = {self.old: self.definition}
        after = before | {self.new: self.definition}
        finding, = run(before, after)
        self.assertEqual((finding.path, finding.line), (self.new, 1))
        self.assertIn(self.old, finding.message)
        self.assertIn("Game::Thing", finding.message)

    def test_existing_permanent_header_adds_type(self):
        before = {self.old: self.definition, self.new: "class Other {};\n"}
        after = before | {self.new: before[self.new] + "\n" + self.definition}
        finding, = run(before, after)
        self.assertEqual((finding.path, finding.line), (self.new, 3))

    def test_identical_leaf_in_other_namespace(self):
        prior = {self.old: self.definition}
        self.assertEqual(run(prior, prior | {self.new: self.definition.replace("Game", "Other")}), [])

    def test_comments_do_not_define(self):
        before = {self.old: self.definition}
        self.assertEqual(run(before, before | {self.new: "// " + self.definition}), [])

    def test_promotion_moves_actual_includes(self):
        old_text = '#include "Draft/Thing.h"\n'
        new_text = '#include "Common/Thing.h"\n'
        self.assertEqual(run({self.old: self.definition, self.src: old_text},
                             {self.new: self.definition, self.src: new_text}), [])

    def test_promotion_leaves_unchanged_includer(self):
        text = '// include next\n#include "Draft/Thing.h"\n'
        finding, = run({self.old: self.definition, self.src: text},
                       {self.new: self.definition, self.src: text})
        self.assertEqual((finding.path, finding.line), (self.src, 2))
        self.assertIn(self.old, finding.message)

    def test_literal_relative_include(self):
        path = "include/Consumer.h"
        text = '#include "./Draft/Thing.h"\n'
        finding, = run({self.old: self.definition, path: text}, {path: text})
        self.assertEqual((finding.path, finding.line), (path, 1))

    def test_case_with_identical_local_header(self):
        path = "include/Local/Consumer.h"
        local = "include/Local/Draft/Thing.h"
        draft = self.old
        # A local header wins over the include-root candidate.
        text = '#include "Draft/Thing.h"\n'
        before = {path: text, local: self.definition, draft: self.definition}
        self.assertEqual(run(before, {path: text, local: self.definition}), [])

    def test_comment_and_string_include_ignored(self):
        text = '// #include "Draft/Thing.h"\nconst char *x = "#include Draft/Thing.h";\n'
        self.assertEqual(run({self.old: self.definition, self.src: text}, {self.src: text}), [])

    def test_spliced_spelling_passes_byte_prefilter(self):
        text = '#include "Draft/Th' + "\\" + "\n" + 'ing.h"\n'
        finding, = run({self.old: self.definition, self.src: text}, {self.src: text})
        self.assertEqual((finding.path, finding.line), (self.src, 1))

    def test_removing_unused_draft_is_allowed(self):
        self.assertEqual(run({self.old: self.definition}, {}), [])

    def test_accepted_same_spelling_when_new_path_resolves(self):
        consumer = "include/Draft/Other.h"
        permanent = "include/Thing.h"
        text = '#include "Thing.h"\n'
        before = {self.old: self.definition, consumer: text}
        after = {permanent: self.definition, consumer: text}
        self.assertEqual(run(before, after), [])


if __name__ == "__main__":
    unittest.main()
