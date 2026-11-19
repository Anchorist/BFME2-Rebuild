"""Parse the trusted zero-context Git diff line coordinates."""
import re

def diff_lines(diff):
    """{path: ([(old line, text) removed], [(new line, text) added])} from `git diff -U0` output."""
    out, path, old, new = {}, None, 0, 0
    for raw in diff.splitlines():
        if raw.startswith('--- '):
            continue
        if raw.startswith('+++ '):
            name = raw[4:]; path = name[2:] if name.startswith('b/') else None
            if path: out.setdefault(path, ([], []))
            continue
        if raw.startswith('@@'):
            m = re.match(r'@@ -(\d+)(?:,\d+)? \+(\d+)', raw); old, new = int(m.group(1)), int(m.group(2)); continue
        if path is None: continue
        if raw.startswith('-'): out[path][0].append((old, raw[1:])); old += 1
        elif raw.startswith('+'): out[path][1].append((new, raw[1:])); new += 1
    return out
