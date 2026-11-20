"""Read Git objects without checking out a candidate tree."""

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
import subprocess


class ObjectError(Exception):
    """An input or Git operation could not be completed."""


@dataclass(frozen=True, slots=True)
class Entry:
    mode: str
    oid: str

    @property
    def regular(self):
        return self.mode == '100644'


@dataclass(frozen=True, slots=True)
class Delta:
    path: str
    old: Entry | None
    new: Entry | None


def pathname(raw):
    return raw.decode('utf-8', 'surrogateescape')


class Git:
    def __init__(self, root):
        self.command = [
            'git', '-c', f'core.hooksPath={os.devnull}', '-c', 'core.quotePath=true',
            '-c', f'diff.orderFile={os.devnull}', '-c', 'protocol.allow=never',
            '-c', 'protocol.ext.allow=never', '--no-replace-objects',
            '-C', str(Path(root).resolve()),
        ]
        self.env = {key: os.environ[key] for key in (
            'HOME', 'PATH', 'SYSTEMROOT', 'TMP', 'TEMP', 'TMPDIR',
        ) if key in os.environ}
        self.env.update(LC_ALL='C', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_NO_LAZY_FETCH='1')
        self.reader = None
        self.sizer = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        for proc in (self.reader, self.sizer):
            if proc is not None:
                proc.stdin.close()
                proc.stdout.close()
                proc.wait()

    def run(self, *args):
        result = subprocess.run(self.command + list(args), env=self.env,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if result.returncode:
            raise ObjectError(f'Git {args[0]} could not read the requested objects.')
        return result.stdout

    def tree_oid(self, rev):
        return self.run('rev-parse', '--verify', '--end-of-options',
                        rev + '^{tree}').decode('ascii').strip()

    def tree(self, rev, *paths):
        raw = self.run('ls-tree', '-r', '-z', rev, '--', *paths)
        for item in raw.split(b'\0')[:-1]:
            details, path = item.split(b'\t', 1)
            mode, _, oid = details.decode('ascii').split()
            yield pathname(path), Entry(mode, oid)

    def diff(self, base, head):
        raw = self.run('diff-tree', '-r', '--raw', '-z', '--no-commit-id',
                       '--no-renames', '--no-ext-diff', '--no-textconv',
                       '--ignore-submodules=none', '--no-abbrev', base, head, '--')
        fields = raw.split(b'\0')[:-1]
        for meta, path in zip(fields[::2], fields[1::2], strict=True):
            oldmode, newmode, old, new, _ = meta[1:].decode('ascii').split()
            yield Delta(pathname(path),
                        Entry(oldmode, old) if oldmode != '000000' else None,
                        Entry(newmode, new) if newmode != '000000' else None)

    def object_process(self, mode):
        return subprocess.Popen(
            self.command + ['cat-file', mode], env=self.env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )

    @staticmethod
    def blob_info(proc, oid):
        proc.stdin.write(oid.encode('ascii') + b'\n')
        proc.stdin.flush()
        info = proc.stdout.readline().split()
        if len(info) != 3 or info[0].decode('ascii') != oid or info[1] != b'blob':
            raise ObjectError('A tracked Git blob could not be read.')
        return int(info[2])

    @lru_cache(maxsize=8192)
    def blob(self, oid, limit):
        return self.read_blob(oid, limit)

    def read_blob(self, oid, limit):
        if self.sizer is None:
            self.sizer = self.object_process('--batch-check')
        size = self.blob_info(self.sizer, oid)
        if size > limit:
            return size, None
        if self.reader is None:
            self.reader = self.object_process('--batch')
        if self.blob_info(self.reader, oid) != size:
            raise ObjectError('Git returned conflicting blob sizes.')
        data = self.reader.stdout.read(size)
        if len(data) != size:
            raise ObjectError('A tracked Git blob was truncated.')
        if self.reader.stdout.read(1) != b'\n':
            raise ObjectError('Git returned an invalid blob record.')
        return size, data

    def ledger_oid(self, tree, path='config/map.json', *, optional=False):
        record = dict(self.tree(tree, path)).get(path)
        if record is None and optional:
            return None
        if record is None or not record.regular:
            raise ObjectError(f'The base ledger {path} is missing or not a regular file.')
        return record.oid

