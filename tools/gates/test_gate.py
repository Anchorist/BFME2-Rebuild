"""Git-level fixtures for the eight source gates."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from cpp import Source
from gate import report, verdict
from git_objects import Git
from rules import Index, Policy, forbidden
import ratchets


HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / 'config.json').read_text())
SEED = 'src/subject.cpp'


class Fixture(unittest.TestCase):
    def setUp(self):
        scratch = TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.git('init', '-q', '--template=')
        self.git('config', 'user.name', 'Source gate fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'core.autocrlf', 'false')
        self.git('config', 'core.safecrlf', 'false')
        self.git('config', 'core.hooksPath', '/dev/null')

    def git(self, *args, data=None):
        return subprocess.check_output(['git', '-C', str(self.root), *args], input=data,
                                       stderr=subprocess.PIPE)

    def snapshot(self, additions):
        for name, content in additions.items():
            path = self.root / name
            if content is None:
                path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content if isinstance(content, bytes) else content.encode())
        self.git('add', '-A')
        return self.git('write-tree').decode().strip()

    def compare(self, old, new, config=None):
        base = self.snapshot({'config/map.json': json.dumps({
            'rows': [
                {'name': '?rva00123456@Class@@QAEHXZ', 'accepted_names': ['sub_00123457']},
                {'name': '??0Rva00123458Class@@QAE@XZ', 'accepted_names': []},
            ],
        }), **old})
        head = self.snapshot(new)
        policy = Policy(config or CONFIG)
        with Git(self.root) as git:
            return verdict(git, policy, Index(git, policy), git.tree_oid(base), git.tree_oid(head))

    def assert_gate(self, label, expected, result):
        gate = next(gate for gate in result['gates'] if gate['id'] == label)
        self.assertEqual(expected, gate['status'], report(result))
        for finding in gate['findings']:
            self.assertGreaterEqual(finding['line'], 1)
            self.assertTrue(finding['path'])
            self.assertTrue(finding['remedy'])
        return gate['findings']

    def test_g1_existing_source_and_promoted_header_paths(self):
        result = self.compare({SEED: 'int x;\n', 'include/Draft/A.h': 'struct A {};\n'},
                              {SEED: 'int y;\n', 'include/Draft/A.h': None,
                               'include/A.h': 'struct A {};\n'})
        self.assert_gate('G1', 'pass', result)

    def test_g1_source_rename_disguised_as_delete_and_add_and_config_edit(self):
        result = self.compare({SEED: 'int x;\n', 'tools/gates/config.json': '{}'},
                              {SEED: None, 'src/renamed.cpp': 'int x;\n',
                               'tools/gates/config.json': '{"limits":{}}'})
        findings = self.assert_gate('G1', 'fail', result)
        self.assertEqual({SEED, 'src/renamed.cpp', 'tools/gates/config.json'}, {f['path'] for f in findings})

    def test_g1_draft_addition_and_permanent_deletion(self):
        result = self.compare({'include/A.h': 'int x;\n'},
                              {'include/A.h': None, 'include/Draft/A.h': 'int x;\n'})
        self.assertEqual(2, len(self.assert_gate('G1', 'fail', result)))

    def test_g1_crlf_and_mixed_endings(self):
        result = self.compare({SEED: b'// FUNCTION: A\r\nint x;\r\n// ordinary\r\n'},
                              {SEED: b'// FUNCTION: A\nint y;\r\n// ordinary\n'})
        self.assert_gate('G1', 'pass', result)
        self.assert_gate('G2', 'pass', result)

    def test_g1_rejects_invalid_utf8_and_bare_cr(self):
        result = self.compare({SEED: 'int x;\n', 'include/A.h': ''},
                              {SEED: b'int y;\rint z;\n', 'include/A.h': b'\xff'})
        self.assertEqual(2, len(self.assert_gate('G1', 'fail', result)))
        self.assert_gate('G4', 'blocked', result)

    def test_g1_limits(self):
        cfg = deepcopy(CONFIG)
        cfg['limits'].update(changed_paths=1, bytes_per_file=10, changed_source_bytes=18)
        result = self.compare({SEED: 'int x;\n', 'include/A.h': ''},
                              {SEED: 'int yy;\n', 'include/A.h': 'int elephant;\n'}, cfg)
        findings = self.assert_gate('G1', 'fail', result)
        self.assertTrue(any('paths' in f['message'] for f in findings))
        self.assertTrue(any('Changed source exceeds' in f['message'] for f in findings))

    def test_g2_duplicates_and_raw_string_decoy(self):
        result = self.compare({SEED: '// FUNCTION: A\n// FUNCTION: A\n// GLOBAL: B\n'},
                              {SEED: '// FUNCTION: A\n// FUNCTION: A\n// GLOBAL: B\n'
                                     'const char *s = R"(hello\n// FUNCTION: C\n)";\n'})
        self.assert_gate('G2', 'pass', result)

    def test_g2_removed_duplicate_and_upstream_marker(self):
        result = self.compare({SEED: '// FUNCTION: A\n// FUNCTION: A\n// UPSTREAM: original\n'},
                              {SEED: '// FUNCTION: A\n// UPSTREAM: modified\n'})
        self.assertEqual(3, len(self.assert_gate('G2', 'fail', result)))

    def test_g3_comment_and_string_keywords_are_opaque(self):
        result = self.compare({SEED: 'int x;\n'},
                              {SEED: '/* asm __emit __declspec(naked) */\n'
                                     'const char *s = "asm // __emit";\n'
                                     'const char *t = R"tag(" // _asm\n'
                                     '#pragma comment(linker, "fake")\n)tag";\n'})
        self.assert_gate('G3', 'pass', result)

    def test_g3_multiline_asm_alias_and_pragmas(self):
        result = self.compare({SEED: ''},
                              {SEED: '#pragma \\\ncomment(linker,"alias")\n'
                                     '__declspec(\nnaked) void f() {\n'
                                     '    __as\\\nm { nop }\n    __emit 0x90;\n}\n'
                                     'int x __attribute__((alias("target")));\n'
                                     '__pragma(optimize("", off))\n'})
        hits = self.assert_gate('G3', 'fail', result)
        self.assertEqual(6, len(hits))

    def test_g3_allowlist_is_exact_and_does_not_allow_a_second_copy(self):
        old = '__asm nop\n'
        cfg = deepcopy(CONFIG)
        key = next(forbidden(Source(old), Policy(cfg), SEED))[-1]
        cfg['approved_forbidden'][SEED] = {key: 1}
        result = self.compare({SEED: old},
                              {SEED: '\t__asm nop\n__asm nop\n'}, cfg)
        self.assertEqual(1, len(self.assert_gate('G3', 'fail', result)))

    def test_g4_comments_strings_and_offset_free_code(self):
        result = self.compare({SEED: ''},
                              {SEED: '// void * stand-in in a comment\n'
                                     'const char *s = "reinterpret_cast<int*>(this + 4)";\n'
                                     'int C::f() { return this->x + 4; }\n'})
        self.assert_gate('G4', 'pass', result)

    def test_g4_separate_metrics_and_indirect_this(self):
        result = self.compare({SEED: ''},
                              {SEED: 'void *create();\n'
                                     'int C::f() {\n'
                                     '  char *p = reinterpret_cast<char *>(this);\n'
                                     '  p += 4;\n'
                                     '  return *((int*)p) + static_cast<int>(get());\n'
                                     '}\n'})
        hits = self.assert_gate('G4', 'fail', result)
        self.assertEqual(5, len(hits), hits)

    def test_g4_replacement_ratchet_includes_deleted_draft(self):
        result = self.compare({'include/Draft/A.h': 'void *lookup();\n', SEED: ''},
                              {'include/Draft/A.h': None, SEED: 'void *lookup();\n'})
        self.assert_gate('G4', 'pass', result)

    def test_g5_only_new_comment_text_and_vendor_exemption(self):
        result = self.compare({SEED: 'int x; // gen99: 1999-12-31\n', 'src/zlib-1.1.4/a.c': ''},
                              {SEED: 'int y; // gen99: 1999-12-31\n'
                                     '// Mask comes from 0x00ABCDEF.\n'
                                     '// Matches the selected field.\n'
                                     'const char *s = "Author: Fixture Author";\n',
                               'src/zlib-1.1.4/a.c': '// Author: Fixture Author, 1999-12-31\n'})
        self.assert_gate('G5', 'pass', result)

    def test_g5_adds_private_attempt_log(self):
        result = self.compare({SEED: ''},
                              {SEED: '/* 2026-11-19\n'
                                     ' * Author: gen99\n'
                                     ' * @author Somebody\n'
                                     ' * a/gen99/trial on srv' '88 in ~/fictional/build\n'
                                     ' * byte-exact; matches retail bytes; 98% vs retail\n'
                                     ' */\n'})
        self.assertGreaterEqual(len(self.assert_gate('G5', 'fail', result)), 5)

    def sources(self, text):
        return {f'src/a{i}.cpp': text for i in range(4)}

    def test_g6_comment_only_changes_do_not_count(self):
        result = self.compare(self.sources('int f();\n'), self.sources('// Evidence.\nint f();\n'))
        self.assert_gate('G6', 'pass', result)

    def test_g6_literal_edit_is_real_change(self):
        result = self.compare(self.sources('static const char *s = "a";\n'),
                              self.sources('static const char *s = "b";\n'))
        self.assert_gate('G6', 'fail', result)

    def test_g6_valid_promotion_with_four_includers(self):
        result = self.compare({
            **self.sources('#include "Draft/A.h"\nA *get();\n'),
            'include/Draft/A.h': 'struct A {};\n',
        }, {
            **self.sources('#include "A.h"\nA *get();\n'),
            'include/Draft/A.h': None, 'include/A.h': 'struct A {};\n',
        })
        self.assert_gate('G6', 'pass', result)
        self.assert_gate('G7', 'pass', result)

    def test_g6_promotion_fails_for_stale_includer(self):
        result = self.compare({SEED: '#include "Draft/A.h"\n', 'include/Draft/A.h': 'struct A {};\n'},
                              {'include/Draft/A.h': None, 'include/A.h': 'struct A {};\n'})
        findings = self.assert_gate('G6', 'fail', result)
        self.assertEqual(SEED, findings[0]['path'])

    def test_g6_promotion_cannot_exempt_unrelated_changes(self):
        result = self.compare({
            **self.sources('#include "Draft/A.h"\nint f();\n'),
            'include/Draft/A.h': 'struct A {};\n',
        }, {
            **self.sources('#include "A.h"\nint g();\n'),
            'include/Draft/A.h': None, 'include/A.h': 'struct A {};\n',
        })
        self.assert_gate('G6', 'fail', result)

    def test_g7_real_duplicates_with_scope_and_linkage(self):
        result = self.compare({'include/A.h': 'namespace N { union A {}; enum E { one }; }\n'
                                               'extern "C" { int global = 0; }\n',
                               SEED: ''},
                              {'include/B.h': 'namespace N {\n union A\n { int first; };\n'
                                     ' enum E { two };\n}\nint global;\n'})
        self.assertEqual(3, len(self.assert_gate('G7', 'fail', result)))

    def test_g7_forward_declarations_local_and_internal_linkage(self):
        result = self.compare({'include/A.h': 'struct A {};\nextern int global;\n'
                                               'namespace N { struct B {}; }\n'
                                               'static int hidden;\n',
                               SEED: ''},
                              {SEED: 'struct A;\nint global;\nstatic int hidden;\n'
                                     'int f() { enum A { A1 }; int global; return 0; }\n',
                               'include/Other.h': 'namespace Other { struct B {}; }\n'})
        self.assert_gate('G7', 'pass', result)

    def test_g7_duplicate_global_twice_in_one_file(self):
        result = self.compare({SEED: 'int global;\n'}, {SEED: 'int global;\nint global = 1;\n'})
        self.assert_gate('G7', 'fail', result)

    def test_g7_checks_same_identity_across_upstream_and_project_paths(self):
        upstream = 'include/upstream/Example/Shared.h'
        project = 'include/Shared.h'
        result = self.compare({upstream: 'struct Shared {};\n', project: ''},
                              {project: 'struct Shared { int payload; };\n'})
        findings = self.assert_gate('G7', 'fail', result)
        self.assertEqual(project, findings[0]['path'])
        self.assertIn(upstream, findings[0]['message'])
        result = self.compare({upstream: 'struct Shared {};\n', project: ''},
                              {upstream: 'struct Shared {};\nint Global;\nint Global = 1;\n'})
        self.assert_gate('G7', 'fail', result)

    def test_g8_accepted_mangled_exact_and_existing_names(self):
        result = self.compare({'include/A.h': 'int g_111111;\n', SEED: ''},
                              {SEED: 'int rva00123456();\nint sub_00123457();\n'
                                     'Rva00123458Class *get();\nint f() { return g_111111; }\n'})
        self.assert_gate('G8', 'pass', result)

    def test_g8_unsupported_spellings_and_candidate_ledger_edit(self):
        result = self.compare({SEED: ''},
                              {SEED: 'int sub_00123457_extra();\nint g_00FEDCBA;\n',
                               'config/map.json': '{"rows":[{"name":"g_00FEDCBA","accepted_names":[]}]}'})
        findings = self.assert_gate('G8', 'fail', result)
        self.assertEqual(2, len(findings))

    def test_g4_deref_operand_is_not_pointer_arithmetic(self):
        source = Source("""
int C::f() {
    char *p = (char *)this;
    int bytes = sizeof(*this) + 4 + *((int*)p);
    { char *p; bytes += p + 4 - p; }
    char *q = getBuffer(this);
    return bytes + (*(q + 4));
}
""")
        self.assertEqual([], ratchets.counts(source)['this_arithmetic'])

    def test_g4_real_arithmetic_and_nested_alias(self):
        source = Source("""
int C::f() {
    unsigned char *p = (unsigned char *)(this);
    auto *q = p;
    q += 4;
    return (4 + q)[1] + ((char*)this)[0] + (this + 1)->x;
}
""")
        self.assertEqual([5, 6, 6, 6], ratchets.counts(source)['this_arithmetic'])

    def test_g4_cast_target_void_is_not_a_void_declaration(self):
        source = Source("""
static_cast<void *>(p);
sizeof(void *);
(void *)p;
void *factory();
void x(void*const);
""")
        counts = ratchets.counts(source)
        self.assertEqual([5, 6], counts['void_pointer'])
        self.assertEqual([4], counts['c_pointer_cast'])

    def test_g4_cast_call_results_and_call_chain(self):
        source = Source("""
int f() {
    return int(first()) + static_cast<int>(object.get().call())
        + (int)(other()) + static_cast<int>(sum() + 1)
        + (int)other().field + (int)(callee()()[1]);
}
""")
        self.assertEqual([3, 3, 4], ratchets.counts(source)['cast_call_result'])

    def test_g4_c_style_function_pointer_cast(self):
        source = Source('Handler h = (void (__cdecl *)(int))getCallback();')
        self.assertEqual([1], ratchets.counts(source)['c_pointer_cast'])
        self.assertEqual([1], ratchets.counts(source)['cast_call_result'])

    def test_g6_distinguishes_function_like_macro(self):
        result = self.compare(self.sources('#define A(x) (x)\n'),
                              self.sources('#define A (x) (x)\n'))
        self.assert_gate('G6', 'fail', result)

    def test_g6_rename_of_a_promoted_type(self):
        result = self.compare({
            **self.sources('#include "Draft/Temporary.h"\nTemporary *get();\n'),
            'include/Draft/Temporary.h': 'struct Temporary {};\n',
        }, {
            **self.sources('#include "EngineThing.h"\nEngineThing *get();\n'),
            'include/Draft/Temporary.h': None, 'include/EngineThing.h': 'struct EngineThing {};\n',
        })
        self.assert_gate('G6', 'pass', result)

    def test_g7_const_has_external_linkage_in_c(self):
        result = self.compare({'src/a.c': 'const int global = 0;\n', 'src/b.c': ''},
                              {'src/b.c': 'const int global = 1;\n'})
        self.assert_gate('G7', 'fail', result)

    def test_g1_cross_file_move_without_moving_annotation(self):
        definition = 'void Engine::setFlag(int f) { flag = f; }\n'
        result = self.compare({SEED: '// FUNCTION: A\n' + definition, 'src/other.cpp': ''},
                              {SEED: '// FUNCTION: A\n', 'src/other.cpp': definition})
        findings = self.assert_gate('G1', 'fail', result)
        self.assertEqual('src/other.cpp', findings[0]['path'])
        self.assert_gate('G2', 'pass', result)

    def test_g8_address_shaped_member(self):
        result = self.compare({SEED: 'struct Some { int m_unk08; };\n'},
                              {SEED: 'struct Some { int m_00A123CD; int m_unk0x40; };\n'})
        findings = self.assert_gate('G8', 'fail', result)
        self.assertEqual(1, len(findings))

    def test_g5_bare_row_tag_and_address_evidence(self):
        result = self.compare({SEED: ''}, {SEED: '// RVA 0x00123456\n'
                                                   '// Mask recovered from the table at 0x00223344.\n'})
        findings = self.assert_gate('G5', 'fail', result)
        self.assertEqual([1], [f['line'] for f in findings])

    def test_g2_annotation_order_is_part_of_the_contract(self):
        result = self.compare({SEED: '// FUNCTION: first\n// FUNCTION: second\n'},
                              {SEED: '// FUNCTION: second\n// FUNCTION: first\n'})
        self.assert_gate('G2', 'fail', result)

    def test_g2_same_sequence_marker_moved_below_its_body(self):
        definition = 'void Engine::setFlag(int f) { flag = f; }\n'
        result = self.compare({SEED: '// FUNCTION: A\n' + definition + '// FUNCTION: B\n'},
                              {SEED: definition + '// FUNCTION: A\n// FUNCTION: B\n'})
        self.assert_gate('G2', 'fail', result)

    def test_g2_adding_and_editing_a_body_below_its_marker(self):
        old = '// FUNCTION: A\n// FUNCTION: B\nint foo() { return 1; }\n'
        new = ('// FUNCTION: A\nint added() { return 3; }\n'
               '// FUNCTION: B\nint foo() { return 2; }\n')
        self.assert_gate('G2', 'pass', self.compare({SEED: old}, {SEED: new}))

    def test_g3_default_denies_and_does_not_allow_source_pack(self):
        result = self.compare({SEED: ''}, {SEED: '#pragma message("inert")\n'
                                                '#pragma pack(push, 8)\n'
                                                '_Pragma("log")\n'})
        self.assertEqual(3, len(self.assert_gate('G3', 'fail', result)))

    def test_g3_allowlisted_pragma_scopes_and_source_warning(self):
        result = self.compare(
            {SEED: '', 'include/A.h': ''},
            {SEED: '#pragma warning(push)\n__pragma(warning(pop))\n',
             'include/A.h': '#pragma once\n#pragma pack(push, 4)\n_Pragma("pack(pop)")\n'},
        )
        self.assert_gate('G3', 'pass', result)

    def test_g7_new_local_and_anonymous_source_types(self):
        result = self.compare({SEED: ''}, {SEED: 'int f() { struct Point { int x; }; '
                                              'union { int i; char a[4]; } u; return u.i; }\n'})
        hits = self.assert_gate('G7', 'fail', result)
        self.assertEqual(2, len(hits))

    def test_g7_source_forward_declaration_enum_and_existing_debt(self):
        result = self.compare({SEED: 'struct Existing {};\n'},
                              {SEED: 'struct Existing { int count; };\n'
                                     'class Declared;\nenum class Mode { A };\n'
                                     'struct Existing *p = 0;\n'})
        self.assert_gate('G7', 'pass', result)

    def test_g2_can_restore_binding_to_unique_exact_mangled_name(self):
        real = '// FUNCTION: BFME2 name=?parse@Engine@@QAEXXZ\n'
        orphan = '// FUNCTION: BFME2 name=??0Other@@QAE@XZ\n'
        body = 'void Engine::parse() { close(); }\n'
        result = self.compare({SEED: real + orphan + body}, {SEED: real + body + orphan})
        self.assert_gate('G2', 'pass', result)

    def test_g3_approved_assembly_cannot_change_instruction_boundaries(self):
        old = '__asm {\n mov eax, 1\n nop\n}\n'
        cfg = deepcopy(CONFIG)
        key = next(forbidden(Source(old), Policy(cfg), SEED))[-1]
        cfg['approved_forbidden'][SEED] = {key: 1}
        result = self.compare({SEED: old}, {SEED: '__asm {\n mov eax, 1 nop\n}\n'}, cfg)
        self.assert_gate('G3', 'fail', result)

    def test_g5_trailing_rva_on_a_real_declaration_is_evidence(self):
        result = self.compare({SEED: ''}, {SEED: 'extern int value; // RVA 0x00123456\n'})
        self.assert_gate('G5', 'pass', result)

    def test_g6_promotion_of_a_header_without_a_named_type(self):
        result = self.compare({
            **self.sources('#include "Draft/Constants.h"\n'),
            'include/Draft/Constants.h': 'enum { Limit = 2 };\n',
        }, {
            **self.sources('#include "Constants.h"\n'),
            'include/Draft/Constants.h': None,
            'include/Constants.h': 'enum { Limit = 2 };\n',
        })
        self.assert_gate('G6', 'pass', result)

    def test_g6_promotion_renames_primary_type_in_a_multi_type_header(self):
        result = self.compare({
            **self.sources('#include "Draft/Temporary.h"\nTemporary *get();\n'),
            'include/Draft/Temporary.h': 'struct Temporary {};\nstruct Context {};\n',
        }, {
            **self.sources('#include "EngineThing.h"\nEngineThing *get();\n'),
            'include/Draft/Temporary.h': None,
            'include/EngineThing.h': 'struct EngineThing {};\nstruct Context {};\n',
        })
        self.assert_gate('G6', 'pass', result)

    def test_internal_error_from_missing_revision(self):
        tree = self.snapshot({SEED: ''})
        command = [sys.executable, '-B', str(HERE / 'gate.py'), str(self.root), 'missing-ref', tree,
                   '--json', str(self.root / 'result.json')]
        result = subprocess.run(command, encoding='utf-8', capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads((self.root / 'result.json').read_text())['status'], 'error')
        self.assertIn('**INTERNAL**', result.stdout)


if __name__ == '__main__':
    unittest.main()

