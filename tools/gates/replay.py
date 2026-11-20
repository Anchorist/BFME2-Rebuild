#!/usr/bin/env python3
"""Replay the gate or compute the informational baseline over Git objects."""

import argparse
from collections import Counter
from hashlib import sha256
from pathlib import Path
import random
import sys

from cpp import Source, decode
from gate import encode, policy_at, policy_digest, report, verdict, write
from git_objects import Git
from rules import Index, forbidden, stand_in_counts
import ratchets


def landings(git, tip, count):
    # A fleet landing is an actual first-parent commit with the land.py
    # trailer. Intervening map or export maintenance stays in its parent tree.
    raw = git.run('log', '--first-parent', '--format=%H%x00%P%x00%(trailers:key=Landed-branch,valueonly,separator=%x20)',
                  tip, '--').decode('ascii', 'surrogateescape')
    selected = []
    for row in raw.splitlines():
        commit, parents, trailer = row.split('\0')
        if trailer.strip() and parents:
            selected.append((parents.split()[0], commit))
        if len(selected) == count:
            return selected[::-1]
    raise ValueError(f'Found {len(selected)} trailer-marked landings, expected {count}.')


def replay(git, policy, tip, count):
    pairs = landings(git, tip, count)
    index = Index(git, policy)
    items = []
    for i, (base, head) in enumerate(pairs, 1):
        result = verdict(git, policy, index, git.tree_oid(base), git.tree_oid(head))
        items.append({'base': base, 'head': head,
                      'report_sha256': sha256(report(result).encode('utf-8')).hexdigest(), **result})
        if i % 25 == 0:
            print(f'Replayed {i}/{count}', file=sys.stderr, flush=True)
    return {'main_tip': tip, 'landings': items}


def inventory(git, policy, tip):
    totals = Counter({name: 0 for name in ratchets.RULES})
    forbidden_allowlist = {}
    address_prefix = Counter()
    unscannable = []
    files = 0
    tree = git.tree_oid(tip)
    index = Index(git, policy)
    for path, entry in git.tree(tree, 'src', 'include'):
        if not policy.kind(path):
            continue
        files += 1
        if not entry.regular:
            unscannable.append(path)
            continue
        try:
            _, raw = git.blob(entry.oid, policy.limits['bytes_per_file'])
            source = Source(decode(raw))
        except (UnicodeDecodeError, AttributeError):
            unscannable.append(path)
            continue
        totals.update({key: len(lines) for key, lines in stand_in_counts(source, path, index, tree).items()})
        hits = Counter(key for _, _, _, key in forbidden(source, policy, path))
        if hits:
            forbidden_allowlist[path] = dict(hits)
        for token in source.tokens:
            if token.kind == 'word' and policy.address.fullmatch(token.value):
                first = next((i for i, c in enumerate(token.value) if c.isdigit()), len(token.value))
                address_prefix[token.value[:first]] += 1
    return {
        'baseline': {'tree': tree, 'files': files, 'unscannable': sorted(unscannable), 'totals': dict(totals)},
        'forbidden_inventory': forbidden_allowlist,
        'address_prefix_counts': dict(address_prefix),
    }


def shuffle(entries, seed):
    result = list(entries)
    random.Random(seed).shuffle(result)
    return iter(result)


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('mode', choices=('replay', 'inventory'))
    args.add_argument('repo')
    args.add_argument('tip')
    args.add_argument('output')
    args.add_argument('--count', type=int, default=500)
    args.add_argument('--shuffle', type=int)
    run = args.parse_args()
    config = Path(__file__).with_name('config.json')
    policy = policy_at(config)
    digest = policy_digest(config)
    with Git(run.repo) as git:
        tip = git.run('rev-parse', '--verify', '--end-of-options',
                      run.tip + '^{commit}').decode('ascii').strip()
        if run.shuffle is not None:
            tree, diff = git.tree, git.diff
            git.tree = lambda *params: shuffle(tree(*params), run.shuffle)
            git.diff = lambda *params: shuffle(diff(*params), run.shuffle)
        if run.mode == 'replay':
            result = replay(git, policy, tip, run.count)
        else:
            result = inventory(git, policy, tip)
    if policy_digest(config) != digest:
        raise ValueError('The trusted policy bundle changed during the measurement.')
    result['policy_sha256'] = digest
    write(run.output, encode(result))


if __name__ == '__main__':
    main()

