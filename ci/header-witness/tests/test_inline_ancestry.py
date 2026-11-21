"""Tests for ci/header-witness/inline_ancestry.py. The end-to-end test runs the real consumer chain: the compiled
table binder (compiled_table_owners), the source binding (tools/gates/inline_scope_binding.authenticate) and the
owner-scope selector (inline_owner_scope.select_owner_scope), all looked up in ci/managed-check and tools/gates."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for extra in (ROOT / "ci" / "managed-check", ROOT / "tools" / "gates"):
    sys.path.append(str(extra))
import inline_ancestry as A  # noqa: E402

BASE = b"""#ifndef SHAPES_H
#define SHAPES_H
namespace Game {
class Shape
{
public:
    virtual ~Shape();
    virtual float area() const = 0;   // a comment that mentions class Fake { }
};
class Circle : public Shape
{
public:
    float area() const;
    float m_radius;
    struct Cache { int hits; };
};
}
template <class T> class Holder { T value; };
class Plain { int x; };
class UsesTemplate : public Holder<int> { };
enum class Color { Red, Green };
#endif
"""


def owners(data, path="include/Shapes.h"):
    return {item["owner"]: item for item in A.scan(path, data)["classes"]}


def digest(data, owner, path="include/Shapes.h"):
    return A.records({path: data})[0][owner]["digest"]


class Scan(unittest.TestCase):
    def test_qualified_owners_bases_and_virtuals(self):
        found = owners(BASE)
        self.assertEqual(sorted(found), ["Game::Circle", "Game::Circle::Cache", "Game::Shape", "Holder", "Plain",
                                         "UsesTemplate"])
        self.assertEqual(found["Game::Circle"]["bases_raw"], ["Shape"])
        self.assertTrue(found["Game::Shape"]["virtual"])
        self.assertFalse(found["Game::Circle"]["virtual"])        # its own body declares none
        self.assertTrue(found["Holder"]["template"])
        self.assertNotIn("T", found)                              # template <class T> is not a class

    def test_comments_and_spacing_do_not_change_a_digest_but_text_does(self):
        same = BASE.replace(b"// a comment that mentions", b"// another remark about").replace(b"float m_radius;",
                                                                                            b"float  m_radius;")
        self.assertEqual(digest(same, "Game::Circle"), digest(BASE, "Game::Circle"))
        moved = BASE.replace(b"float m_radius;", b"double m_radius;")
        self.assertNotEqual(digest(moved, "Game::Circle"), digest(BASE, "Game::Circle"))

    def test_bases_resolve_through_the_namespace_and_polymorphism_is_inherited(self):
        table, _, bad, _ = A.records({"include/Shapes.h": BASE})
        self.assertEqual(table["Game::Circle"]["bases"], ["Game::Shape"])
        self.assertTrue(table["Game::Circle"]["polymorphic"])
        self.assertFalse(table["Plain"]["polymorphic"])
        self.assertEqual(table["UsesTemplate"]["unresolved"], ["Holder<int>"])
        self.assertEqual(bad, {})


def judge(before, after, changed):
    _, candidate, report = A.sides(before, dict(before, **after), changed, "1" * 40, "2" * 40)
    return candidate["complete"], report


class Bypasses(unittest.TestCase):
    """Changes that must either select the class they touch or hold; never pass silently."""

    def test_a_duplicate_class_name_holds_when_any_copy_changes(self):
        files = {"include/A.h": b"class Dup { int a; };\n", "include/B.h": b"class Dup { int a; };\n"}
        complete, report = judge(files, {"include/B.h": b"class Dup { int a; virtual void evil(); };\n"},
                                 ["include/B.h"])
        self.assertFalse(complete)
        self.assertIn("Dup", report["changed"])

    def test_an_out_of_line_inline_member_body_selects_its_class(self):
        poly = b"class Poly { public: virtual int f(); };\ninline int Poly::f() { return 1; }\n"
        complete, report = judge({"include/Poly.h": poly}, {"include/Poly.h": poly.replace(b"return 1", b"return 2")},
                                 ["include/Poly.h"])
        self.assertTrue(complete)
        self.assertEqual(report["changed"], ["Poly"])

    def test_a_macro_or_typedef_change_outside_class_bodies_holds(self):
        files = {"include/Macros.h": b"#define EXTRA_METHODS\n",
                 "include/Poly.h": b'#include "Macros.h"\nclass Poly { public: EXTRA_METHODS virtual int f(); };\n'}
        complete, report = judge(files, {"include/Macros.h": b"#define EXTRA_METHODS virtual void injected();\n"},
                                 ["include/Macros.h"])
        self.assertFalse(complete)
        self.assertTrue(any("outside the class bodies" in issue for issue in report["issues"]))
        typedef = files["include/Poly.h"].replace(b"class Poly", b"typedef int I;\nclass Poly")
        complete, _ = judge(files, {"include/Poly.h": typedef}, ["include/Poly.h"])
        self.assertFalse(complete)

    def test_an_out_of_line_nested_class_is_its_own_owner(self):
        nested = (b"class Base { virtual ~Base(); };\nclass Outer { class Inner; };\n"
                  b"class Outer::Inner : public Base { int x; };\n")
        complete, report = judge({"include/N.h": nested},
                                 {"include/N.h": nested.replace(b"int x;", b"int x; int y;")}, ["include/N.h"])
        self.assertTrue(complete)
        self.assertEqual(report["changed"], ["Outer::Inner"])
        self.assertEqual(A.records({"include/N.h": nested})[0]["Outer::Inner"]["bases"], ["Base"])

    def test_a_declspec_class_head_is_read(self):
        aligned = b"class __declspec(novtable) Aligned { virtual void f(); };\n"
        complete, report = judge({"include/D.h": aligned},
                                 {"include/D.h": aligned.replace(b"void f();", b"void f(); int z;")}, ["include/D.h"])
        self.assertTrue(complete)
        self.assertEqual(report["changed"], ["Aligned"])

    def test_nested_bodies_are_cut_by_position_not_by_text(self):
        found = owners(b"class P { struct E {}; void g() {} virtual void h(); };\n", "include/P.h")
        self.assertIn("g() {}", json.loads(found["P"]["text"])[0])
        self.assertTrue(found["P"]["virtual"])

    def test_an_unqualified_base_resolves_only_through_enclosing_scopes(self):
        text = b"namespace A { class Base { }; }\nnamespace B { class D : public Base { }; }\n"
        self.assertEqual(A.records({"include/S.h": text})[0]["B::D"]["unresolved"], ["Base"])


class Bypasses2(unittest.TestCase):
    """The second round of review cases: each must select the class or hold."""

    def test_a_changed_file_this_reader_does_not_read_holds(self):
        files = {"include/Poly.h": b'class Poly { public:\n#include "Fields.inc"\n virtual int f(); };\n'}
        _, candidate, report = A.sides(files, files, ["include/Fields.inc"], "1" * 40, "2" * 40)
        self.assertFalse(candidate["complete"])
        self.assertTrue(any("does not read" in issue for issue in report["issues"]))

    def test_a_macro_before_the_class_name_holds(self):
        files = {"include/E.h": b"class W3D_API Foo : public Base { int a; };\nclass Base { virtual ~Base(); };\n"
                                b"class Derived : public Foo { };\n"}
        complete, report = judge(files, {"include/E.h": files["include/E.h"].replace(b"int a;", b"int a; int b;")},
                                 ["include/E.h"])
        self.assertFalse(complete)
        self.assertNotIn("W3D_API", report["changed"])

    def test_inline_bodies_and_unparsed_classes_in_source_files(self):
        files = {"include/Poly.h": b"class Poly { public: virtual int f(); };\n",
                 "src/Poly.cpp": b'#include "Poly.h"\ninline int Poly::f() { return 1; }\nint other() { return 0; }\n'}
        complete, report = judge(files, {"src/Poly.cpp": files["src/Poly.cpp"].replace(b"return 1", b"return 2")},
                                 ["src/Poly.cpp"])
        self.assertTrue(complete)
        self.assertEqual(report["changed"], ["Poly"])
        complete, report = judge(files, {"src/Poly.cpp": files["src/Poly.cpp"].replace(b"return 0", b"return 3")},
                                 ["src/Poly.cpp"])
        self.assertTrue(complete)                             # a non-inline body is the native comparison's
        self.assertEqual(report["changed"], [])
        local = {"include/B.h": b"class Base { virtual ~Base(); };\n",
                 "src/Unit.cpp": b'#include "B.h"\nclass MY_ATTR(16) Local : public Base { int a; };\n'}
        complete, _ = judge(local, {"src/Unit.cpp": local["src/Unit.cpp"].replace(b"int a;", b"int a; int b;")},
                            ["src/Unit.cpp"])
        self.assertFalse(complete)

    def test_a_duplicated_class_takes_the_bases_of_every_copy(self):
        files = {"include/A.h": b"class Base1 { virtual ~Base1(); };\nclass Dup : public Base1 { };\n",
                 "include/B.h": b"class Base2 { virtual ~Base2(); };\nclass Dup : public Base2 { };\n"}
        complete, report = judge(files, {"include/B.h": files["include/B.h"].replace(b"~Base2();", b"~Base2(); int x;")},
                                 ["include/B.h"])
        self.assertIn("Dup", report["selected"])
        self.assertFalse(complete)                            # Dup is defined twice

    def test_aliases_and_using_namespace_resolve_or_hold(self):
        files = {"include/Base.h": b"namespace NS { class Base { virtual ~Base(); }; }\n",
                 "include/D.h": b'#include "Base.h"\nusing namespace NS;\nclass Derived : public Base { };\n',
                 "include/T.h": b'#include "Base.h"\ntypedef NS::Base BaseAlias;\nclass Other : public BaseAlias { };\n'}
        complete, report = judge(files, {"include/Base.h": files["include/Base.h"].replace(b"~Base();", b"~Base(); int x;")},
                                 ["include/Base.h"])
        self.assertTrue(complete)
        self.assertEqual(report["selected"], ["Derived", "NS::Base", "Other"])
        hidden = dict(files, **{"include/H.h": b"class Hidden : public Base { };\n"})
        complete, report = judge(hidden, {"include/Base.h": files["include/Base.h"].replace(b"~Base();", b"~Base(); int x;")},
                                 ["include/Base.h"])
        self.assertFalse(complete)
        self.assertTrue(any("Hidden" in issue for issue in report["issues"]))


class Bypasses3(unittest.TestCase):
    """The third round: an unreadable class head in an unchanged file."""

    def test_an_unreadable_head_in_an_unchanged_file_holds_when_it_names_a_selected_class(self):
        files = {"include/Base.h": b"struct Base { virtual int f() { return 1; } };\n",
                 "include/Mid.h": b'#include "Base.h"\nclass W3D_API Mid : public Base {};\nclass Leaf : public Mid {};\n'}
        complete, report = judge(files, {"include/Base.h": files["include/Base.h"].replace(b"return 1", b"return 2")},
                                 ["include/Base.h"])
        self.assertFalse(complete)
        self.assertTrue(any("unreadable class head names Base" in issue for issue in report["issues"]))
        for head in (b"class ALIGN(16) Mid : public Base {};\n", b"class GAME_EXPORT Mid : public Base {};\n"):
            other = dict(files, **{"include/Mid.h": head})
            complete, _ = judge(other, {"include/Base.h": files["include/Base.h"].replace(b"return 1", b"return 2")},
                                ["include/Base.h"])
            self.assertFalse(complete, head)

    def test_an_unreadable_head_naming_other_classes_does_not_hold(self):
        files = {"include/Base.h": b"struct Base { virtual int f() { return 1; } };\n",
                 "include/Other.h": b"struct Unrelated { };\nclass W3D_API Far : public Unrelated {};\n"}
        complete, report = judge(files, {"include/Base.h": files["include/Base.h"].replace(b"return 1", b"return 2")},
                                 ["include/Base.h"])
        self.assertTrue(complete, report["issues"])


class Bypasses4(unittest.TestCase):
    """Bases spelled through macros, and classes declared by a macro call."""

    def test_a_base_spelled_by_a_macro_selects_or_holds(self):
        base = b"class Base { virtual ~Base(); int a; };\n"
        files = {"include/Base.h": base,
                 "include/D.h": b'#include "Base.h"\n#define PARENT Base\nclass Derived : public PARENT { };\n',
                 "include/E.h": b'#include "Base.h"\n#define PARENT2 ::Base /* the root */\nclass Other : public PARENT2 { };\n'}
        complete, report = judge(files, {"include/Base.h": base.replace(b"int a;", b"int a; int b;")}, ["include/Base.h"])
        self.assertIn("Derived", report["selected"])                  # a one-name macro is an alias
        self.assertFalse(complete)                                    # PARENT2 is not a plain alias: hold
        self.assertTrue(any("Other" in issue for issue in report["issues"]))

    def test_a_class_declared_by_a_macro_call_holds_when_it_names_a_selected_class(self):
        base = b"class Base { virtual ~Base(); int a; };\n"
        files = {"include/Base.h": base, "include/M.h": b'#include "Base.h"\nDECLARE_CLASS(Foo, Base);\n'}
        complete, report = judge(files, {"include/Base.h": base.replace(b"int a;", b"int a; int b;")}, ["include/Base.h"])
        self.assertFalse(complete)
        self.assertTrue(any("names Base" in issue for issue in report["issues"]))


class Bypasses5(unittest.TestCase):
    """Bases reached through a template: an argument, a default argument, or an alias of a template-id."""
    BASE = b"class Base { virtual ~Base(); int a; };\n"

    def hold(self, text):
        files = {"include/Base.h": self.BASE, "include/Leaf.h": b'#include "Base.h"\n' + text}
        complete, report = judge(files, {"include/Base.h": self.BASE.replace(b"int a;", b"int a; int b;")},
                                 ["include/Base.h"])
        self.assertFalse(complete)
        self.assertTrue(any("Leaf" in issue and "Base" in issue for issue in report["issues"]), report["issues"])

    def test_a_template_argument_base_holds(self):
        self.hold(b"template <class T> class Wrap : public T { };\nclass Leaf : public Wrap<Base> { virtual void f(); };\n")

    def test_a_default_template_argument_base_holds(self):
        self.hold(b"template <class T = Base> class W : public T { };\nclass Leaf : public W<> { };\n")

    def test_an_alias_of_a_template_id_holds(self):
        self.hold(b"template <class T> class Wrap : public T { };\ntypedef Wrap<Base> WB;\nclass Leaf : public WB { };\n")
        self.hold(b"template <class T> class Wrap : public T { };\nusing WB = Wrap<Base>;\nclass Leaf : public WB { };\n")

    def test_an_unrelated_template_base_still_completes(self):
        files = {"include/Base.h": self.BASE,
                 "include/Leaf.h": b"template <class T> class Box { T t; };\nclass Leaf : public Box<int> { };\n"}
        complete, report = judge(files, {"include/Base.h": self.BASE.replace(b"int a;", b"int a; int b;")},
                                 ["include/Base.h"])
        self.assertTrue(complete, report["issues"])


class Bypasses6(unittest.TestCase):
    """Function-like macros in a base clause, and class-making macros called inside namespaces and class bodies."""
    BASE = b"struct Base { virtual int f() { return 1; } };\n"

    def judged(self, text, extra=None):
        files = {"include/B.h": self.BASE, "include/D.h": b'#include "B.h"\n' + text}
        files.update(extra or {})
        return judge(files, {"include/B.h": self.BASE.replace(b"return 1;", b"return 2;")}, ["include/B.h"])

    def assert_holds(self, text, extra=None):
        complete, report = self.judged(text, extra)
        self.assertFalse(complete, report)
        self.assertTrue(any("Base" in issue for issue in report["issues"]), report["issues"])

    def test_a_function_like_macro_base_holds(self):
        self.assert_holds(b"#define BASE_OF(x) Base\nstruct Der : public BASE_OF(0) {};\n")

    def test_a_class_making_macro_in_a_namespace_holds(self):
        self.assert_holds(b"namespace N {\n#define INHERIT_BASE(X) class X : public Base {}\nINHERIT_BASE(Hidden);\n}\n")

    def test_a_class_making_macro_in_a_class_body_holds(self):
        self.assert_holds(b"#define NESTED_DER(X) struct X : public Base {}\nstruct Outer { NESTED_DER(Inner); };\n")

    def test_a_class_making_macro_given_the_base_as_an_argument_holds(self):
        self.assert_holds(b"struct Outer { MAKE_DERIVED(Inner, Base); };\n",
                          {"include/M.h": b"#define MAKE_DERIVED(X, B) \\\n  struct X : public B {}\n"})

    def test_an_unrelated_function_like_macro_still_completes(self):
        complete, report = self.judged(b"#define SQUARE(x) ((x) * (x))\nstruct Plain { int v[SQUARE(2)]; };\n")
        self.assertTrue(complete, report["issues"])


class Bypasses7(unittest.TestCase):
    """Class makers reached through other macros, and calls the statement-start pattern did not see."""
    BASE = b"struct Base { virtual int f() { return 1; } };\n"

    def assert_holds(self, text):
        files = {"include/B.h": self.BASE, "include/D.h": b'#include "B.h"\n' + text}
        complete, report = judge(files, {"include/B.h": self.BASE.replace(b"return 1;", b"return 2;")}, ["include/B.h"])
        self.assertFalse(complete, report)
        self.assertTrue(any("Base" in issue for issue in report["issues"]), report["issues"])

    def test_a_wrapper_around_a_class_maker_holds(self):
        inner = b"#define MK_CLS_INNER(N, B) class N : public B {}\n#define MK_CLS(N, B) MK_CLS_INNER(N, B)\n"
        self.assert_holds(inner + b"struct Outer { MK_CLS(Der, Base); };\n")
        self.assert_holds(inner + b"namespace N { MK_CLS(Der, Base); }\n")

    def test_a_class_keyword_spelled_by_a_macro_holds(self):
        self.assert_holds(b"#define KW_STRUCT struct\n#define MK_DER(N) KW_STRUCT N : public Base {}\n"
                          b"struct Outer { MK_DER(Der); };\n")

    def test_a_nested_call_in_a_maker_argument_holds(self):
        self.assert_holds(b"#define BASE_OF(x) Base\n#define MAKE_DER(N, B) struct N : public B {}\n"
                          b"struct Outer { MAKE_DER(Der, BASE_OF(0)); };\n")

    def test_a_maker_called_right_after_an_access_label_holds(self):
        self.assert_holds(b"#define MAKE_DER_SEMI(N, B) struct N : public B {};\n"
                          b"struct Outer { public: MAKE_DER_SEMI(Der, Base) };\n")


def git(repo, *args, data=None):
    env = {"PATH": os.environ["PATH"], "HOME": str(repo), "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t"}
    return subprocess.run(["git", "-C", str(repo), *args], input=data, capture_output=True, check=True,
                          env=env).stdout.decode().strip()


def commit(repo, files, message):
    for path, data in files.items():
        Path(repo, path).parent.mkdir(parents=True, exist_ok=True)
        Path(repo, path).write_bytes(data)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", message)
    return git(repo, "rev-parse", "HEAD")


SOURCE = {"include/Shapes.h": BASE, "src/Circle.cpp": b'#include "Shapes.h"\nfloat Game::Circle::area() const { return 0; }\n',
          "src/Square.cpp": b'#include "Shapes.h"\nclass Square : public Game::Shape { float area() const; };\n'}


class Sides(unittest.TestCase):
    def build(self, change):
        tmp = tempfile.mkdtemp()
        git(tmp, "init", "-q")
        base = commit(tmp, SOURCE, "base")
        head = commit(tmp, change, "head")
        tree = git(tmp, "rev-parse", "HEAD^{tree}")
        git_dir = Path(tmp, ".git")
        parent = A.tree_files(git_dir, base)
        candidate = A.tree_files(git_dir, tree)
        before, after = A.changed_blobs(git_dir, base, tree)
        return tmp, base, head, tree, parent, candidate, before, after

    def test_a_changed_base_selects_its_descendants_in_any_file_and_lists_their_ancestors(self):
        change = {"include/Shapes.h": BASE.replace(b"virtual float area() const = 0;",
                                                   b"virtual float area() const = 0;\n    virtual int sides() const;")}
        _, _, _, tree, parent, candidate, before, _ = self.build(change)
        p, c, report = A.sides(parent, candidate, sorted(before), "1" * 40, tree)
        self.assertEqual(report["changed"], ["Game::Shape"])
        self.assertEqual(report["selected"], ["Game::Circle", "Game::Shape", "Square"])
        self.assertTrue(c["complete"])
        self.assertEqual({row["owner"] for row in c["classes"]}, {"Game::Circle", "Game::Shape", "Square"})
        self.assertEqual(c["paths"], ["include/Shapes.h"])

    def test_a_change_reaching_a_template_base_is_incomplete(self):
        change = {"include/Shapes.h": BASE.replace(b"class UsesTemplate : public Holder<int> { };",
                                                   b"class UsesTemplate : public Holder<int> { int more; };")}
        _, _, _, tree, parent, candidate, before, _ = self.build(change)
        p, c, report = A.sides(parent, candidate, sorted(before), "1" * 40, tree)
        self.assertFalse(c["complete"])
        self.assertTrue(any("Holder<int>" in issue for issue in report["issues"]))

    def test_end_to_end_through_the_binder_the_source_binding_and_the_selector(self):
        try:
            import compiled_table_owners as builder
            from inline_owner_scope import select_owner_scope
            from inline_scope_binding import authenticate
            from git_objects import Git
        except ImportError as exc:
            self.skipTest(f"consumer chain not installed here: {exc}")
        change = {"include/Shapes.h": BASE.replace(b"virtual float area() const = 0;",
                                                   b"virtual float area() const = 0;\n    virtual int sides() const;")}
        tmp, base, head, tree, parent, candidate, before, after = self.build(change)
        binding = {"repository": 7, "base": base, "head": head, "tree": tree, "matrix": "a" * 64,
                   "compiler_profile": "b" * 64, "intake": "c" * 64, "policy": "d" * 64}
        issuer = {"repository": 7, "workflow": 3, "run": 11, "attempt": 1}
        p, c, _ = A.sides(parent, candidate, sorted(before), git(tmp, "rev-parse", f"{base}^{{tree}}"), tree)
        catalogue = ["??_7Shape@Game@@6B@", "??_7Circle@Game@@6B@", "??_7Square@@6B@"]
        def tables(extra_slot):
            owners = {"Game::Shape": "??_7Shape@Game@@6B@", "Game::Circle": "??_7Circle@Game@@6B@",
                      "Square": "??_7Square@@6B@"}
            return {"complete": True, "holes": [], "conflicts": [], "template_tables": {},
                    "owners": {o: {"tables": [t], "protected_tables": [t], "unprotected_tables": []}
                               for o, t in owners.items()},
                    "tables": {t: {"slots": ["a", "b"] + (["c"] if extra_slot else [])} for t in owners.values()}}
        data, attestation, _ = A.packet_and_attestation(
            binding=binding, issuer=issuer, parent_side=p, candidate_side=c, parent_tables=tables(False),
            candidate_tables=tables(True), protected_tables=catalogue, parent_blobs=before, candidate_blobs=after,
            builder=builder)
        with Git(Path(tmp, ".git")) as objects:
            bound = authenticate(objects, data, attestation, expected=binding, issuer=issuer, max_paths=60)
        scope = select_owner_scope(bound.packet, expected=binding, base_tree=bound.base_tree,
                                   changed_paths=bound.changed_paths, protected_tables=catalogue)
        self.assertEqual(scope["owners"], ["Game::Circle", "Game::Shape", "Square"])
        self.assertEqual(scope["tables"], sorted(catalogue))
        tampered = json.loads(data)
        tampered["candidate"]["classes"] = tampered["candidate"]["classes"][:1]
        with Git(Path(tmp, ".git")) as objects:
            with self.assertRaises(ValueError):
                authenticate(objects, A.canonical(tampered), attestation, expected=binding, issuer=issuer,
                             max_paths=60)


class InJob(unittest.TestCase):
    """The producer as the inline job runs it: tables from same-run shard atoms, declarations from Git objects."""

    def test_atoms_and_git_objects_give_a_packet_the_selector_accepts(self):
        try:
            import compiled_table_owners as builder
            from inline_owner_scope import select_owner_scope
        except ImportError as exc:
            self.skipTest(f"consumer chain not installed here: {exc}")
        sides_test = Sides()
        change = {"include/Shapes.h": BASE.replace(b"virtual float area() const = 0;",
                                                   b"virtual float area() const = 0;\n    virtual int sides() const;")}
        tmp, base, head, tree, *_ = sides_test.build(change)
        tables = {"??_7Shape@Game@@6B@": ["a", "b"], "??_7Circle@Game@@6B@": ["a", "b"], "??_7Square@@6B@": ["a", "b"]}
        def records(side, extra):
            return [{"side": side, "tu": "src/Circle.cpp", "bodies": [],
                     "tables": [[name, slots + extra] for name, slots in tables.items()]}]
        atoms = [{"shard": 0, "compiler_plan": "p", "records": records("parent", []) + records("candidate", ["c"])}]
        class FakeGit:
            path = Path(tmp, ".git")
            def value(self, *args):
                return git(tmp, *args)
        plan = {"base": base, "tree": tree, "changed_paths": ["include/Shapes.h"]}
        expected = {"repository": 7, "base": base, "head": head, "tree": tree, "matrix": "a" * 64,
                    "compiler_profile": "b" * 64, "intake": "c" * 64, "policy": "d" * 64}
        produce = A.in_job_owner_scope(atoms, builder, list(tables))
        packet = produce(FakeGit(), plan, head, expected)
        scope = select_owner_scope(packet, expected=expected, base_tree=git(tmp, "rev-parse", f"{base}^{{tree}}"),
                                   changed_paths=plan["changed_paths"], protected_tables=list(tables))
        self.assertEqual(scope["owners"], ["Game::Circle", "Game::Shape", "Square"])
        self.assertEqual(scope["tables"], sorted(tables))

    def test_a_missing_shard_record_makes_the_selector_hold(self):
        try:
            import compiled_table_owners as builder
            from inline_owner_scope import select_owner_scope
        except ImportError as exc:
            self.skipTest(f"consumer chain not installed here: {exc}")
        change = {"include/Shapes.h": BASE.replace(b"virtual float area() const = 0;",
                                                   b"virtual float area() const = 0;\n    virtual int sides() const;")}
        tmp, base, head, tree, *_ = Sides().build(change)
        atoms = [{"records": [{"side": "parent", "tu": "src/Circle.cpp", "unavailable": "no object"},
                              {"side": "candidate", "tu": "src/Circle.cpp", "unavailable": "no object"}]}]
        class FakeGit:
            path = Path(tmp, ".git")
            def value(self, *args):
                return git(tmp, *args)
        plan = {"base": base, "tree": tree, "changed_paths": ["include/Shapes.h"]}
        expected = {"repository": 7, "base": base, "head": head, "tree": tree, "matrix": "a" * 64,
                    "compiler_profile": "b" * 64, "intake": "c" * 64, "policy": "d" * 64}
        packet = A.in_job_owner_scope(atoms, builder, ["??_7Shape@Game@@6B@"])(FakeGit(), plan, head, expected)
        self.assertFalse(packet["candidate"]["complete"])
        with self.assertRaises(ValueError):
            select_owner_scope(packet, expected=expected, base_tree=git(tmp, "rev-parse", f"{base}^{{tree}}"),
                               changed_paths=plan["changed_paths"], protected_tables=["??_7Shape@Game@@6B@"])


if __name__ == "__main__":
    unittest.main()
