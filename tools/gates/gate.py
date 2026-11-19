#!/usr/bin/env python3
"""Decide source policy from a trusted configuration and two Git trees."""

import argparse
from dataclasses import asdict
from html import escape
from hashlib import sha256
import json
from pathlib import Path
import sys

from git_objects import Git, ObjectError
from rules import Comparison, Finding, GATES, Index, Policy


POLICY_FILES = ('cpp.py', 'definitions.py', 'gate.py', 'git_objects.py',
                'ratchets.py', 'rules.py', 'config.json')

LABELS = (
    'Paths', 'Generated annotations', 'Forbidden constructs', 'Stand-in types',
    'Comments', 'One item', 'One definition', 'Address names',
)


def encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2) + '\n'


def write(path, data):
    Path(path).write_text(data, encoding='utf-8', newline='\n')


def policy_digest(config_path):
    """Digest actual runtime modules and the trusted configuration."""
    here = Path(__file__).resolve().parent
    digests = {}
    for name in POLICY_FILES:
        path = config_path if name == 'config.json' else here / name
        digests[name] = sha256(path.read_bytes()).hexdigest()
    entries = json.dumps(digests, sort_keys=True, separators=(',', ':')).encode('ascii')
    return sha256(entries).hexdigest()


def policy_at(path):
    return Policy(json.loads(Path(path).read_text(encoding='utf-8')))


def verdict(repo, policy, index, base_tree, head_tree):
    ctx = Comparison(repo, policy, index, base_tree, head_tree)
    gates = []
    for gate, label in zip(GATES, LABELS, strict=True):
        findings = sorted(set(gate(ctx)))
        status = 'fail' if findings else 'blocked' if ctx.uninspectable and gate != GATES[0] else 'pass'
        gates.append({'id': gate.__name__.upper(), 'label': label, 'status': status,
                      'findings': [asdict(f) for f in findings]})
    return {'status': 'pass' if all(g['status'] == 'pass' for g in gates) else 'fail',
            'gates': gates, 'base_tree': base_tree, 'head_tree': head_tree}


def error_result(message):
    return {
        'status': 'error',
        'gates': [{'id': gate.__name__.upper(), 'label': label, 'status': 'error', 'findings': []}
                  for gate, label in zip(GATES, LABELS, strict=True)],
        'error': asdict(Finding('tools/gates/gate.py', 1, 'INTERNAL', message,
                                'Contact a maintainer to rerun the source checks.')),
    }


def safe(text):
    """Escaped text with no controls, markdown delimiters or embedded links."""
    text = json.dumps(text, ensure_ascii=True)[1:-1]
    return escape(text).translate(str.maketrans({c: f'&#{ord(c)};' for c in '[]()*_`|\\@#'}))


def report(result):
    labels = {'blocked': 'Fail (blocked by G1)'}
    lines = [
        '| Gate | Result |',
        '| --- | --- |',
        *[f'| {gate["id"]} {gate["label"]} | {labels.get(gate["status"], gate["status"].title())} |' for gate in result['gates']],
    ]
    failures = [f for gate in result['gates'] for f in gate['findings']]
    if result['status'] == 'error':
        failures.append(result['error'])
    if failures:
        lines.append('')
    for f in failures:
        lines.append(f'- <code>{safe(f["path"])}:{f["line"]}</code> **{f["rule"]}** '
                     f'<span>{safe(f["message"])} {safe(f["remedy"])}</span>')
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository', help='Local Git repository, bare or working')
    parser.add_argument('base', help='Base revision')
    parser.add_argument('head', help='Head revision')
    parser.add_argument('--config', type=Path, default=Path(__file__).with_name('config.json'))
    parser.add_argument('--json', type=Path, required=True, help='Write machine result to this path')
    parser.add_argument('--report', type=Path, help='Write Markdown to this path instead of stdout')
    args = parser.parse_args(argv)
    try:
        policy = policy_at(args.config)
        digest = policy_digest(args.config)
        with Git(args.repository) as repo:
            result = verdict(repo, policy, Index(repo, policy),
                             repo.tree_oid(args.base), repo.tree_oid(args.head))
        result['policy_sha256'] = digest
    except ObjectError as exc:
        result = error_result(str(exc))
    except Exception as exc:
        result = error_result(f'The gate could not complete ({type(exc).__name__}).')
    try:
        write(args.json, encode(result))
        if args.report is None:
            sys.stdout.buffer.write(report(result).encode('utf-8'))
        else:
            write(args.report, report(result))
    except OSError:
        print('The gate could not write its results.', file=sys.stderr)
        return 2
    return {'pass': 0, 'fail': 1, 'error': 2}[result['status']]


if __name__ == '__main__':
    sys.exit(main())

