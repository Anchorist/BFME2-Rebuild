"""Find internal working text that must not appear in the public repository.

  python3 -B ci/public-text/check.py [PATH ...]     (default: every tracked file)

Prints one line per finding, `path:line: category` (never the matched text, so a log cannot repeat it), and exits 1
when there is any. Categories:
  host-path     home directories and internal host or service paths
  host-name     internal machine and service names
  config-key    internal environment keys and configuration names
  board-file    internal coordination files
  attribution   a lane tag next to an arrow, a date or a clock time (all files)
  lane-tag      a bare lane tag (documentation, scripts, data and workflows only)
  role          internal role words (documentation, scripts, data and workflows only)
  clock-time    a time of day in UTC (an `HH:MMZ` stamp), the shape of an internal log entry
  email         an e-mail address other than a GitHub no-reply address
The patterns use character classes, so this file does not contain the words it looks for. In C and C++ sources
words such as the role words have ordinary game meanings, so there only the contextual forms count.
Skipped: binary files and third-party or generated trees listed in SKIP.
"""
import re
import subprocess
import sys
from pathlib import Path

SKIP = ("reference/", "include/upstream/", "expected/", "baseline/", "src/stlport-4.6/", "src/gamespy-sdk/")
TAG = (r"(?:[L][01]\d|b[t]\d|g[e]n\d{1,2}[a-z]?|d[d]\d|x1\d|m1\d|k1\d|f[01]\d|h[01]\d|c[i]\d|p[c]1|n[b]1|l[d]1"
       r"|g[t]1|p[u]b\d|c[m]1|c[r]1)")
PATTERNS = {
    "host-path": re.compile(r"/h[o]me/\w|(?:~|HOME)[/\\]p[i]lot\b|\bp[i]lot/(?:link|gen|farm|auto|docs)\b"
                            r"|bfme2-[o]ps|bfme2-[r]unner|n[e]xt2\.git"),
    "host-name": re.compile(r"(?<![\w-])s[r]v\d+(?![\w-])|\bc[l]aude\b", re.I),
    "config-key": re.compile(r"\b(?:P[I]LOT_[A-Z0-9_]+|p[i]lot_sha|p[i]lot_import\.json)\b"),
    "board-file": re.compile(r"\b(?:PROGRE[S]S\.md|team_finding[s]\.md|decl_queu[e]|rowclai[m])\b"),
    "attribution": re.compile(r"\b" + TAG + r"\s*(?:->|20\d\d-\d\d-\d\d|\d{1,2}:\d\dZ)"
                              r"|\bc[o]ordinator\s+20\d\d-\d\d-\d\d", re.I),
    "lane-tag": re.compile(r"(?<![?@])\b(?:" + TAG + r"|[l][01]\d/)\b"),
    "role": re.compile(r"\bc[o]ordinator\b|\bthe f[l]eet\b|\bs[e]at\b", re.I),
    "clock-time": re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:Z|\s?U[T]C)\b"),
    "email": re.compile(r"[\w.+-]+@(?!users\.noreply\.github\.com\b)[\w-]+(?:\.[\w-]+)*\.[a-z]{2,}\b"),
}
SOURCE = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".inl", ".inc", ".asm"}
PROSE_ONLY = {"lane-tag", "role"}
# ISO timestamps inside data or test fixtures are dates, not log entries: `YYYY-MM-DDThh:mm:ssZ`
ISO = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?Z")
CONFIG_NAME = "p" + "ilot_import.json"


def tracked(root):
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True).stdout
    return [p for p in out.decode().split("\0") if p]


def scan(root, paths):
    found = []
    for rel in paths:
        if rel.startswith(SKIP):
            continue
        if Path(rel).name.lower() == CONFIG_NAME:
            found.append(f"{rel}:0: config-key")
        p = Path(root) / rel
        try:
            data = p.read_bytes()
        except OSError:
            continue
        if b"\0" in data[:8192]:
            continue
        source = Path(rel).suffix.lower() in SOURCE
        for n, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
            for cat, rx in PATTERNS.items():
                if source and cat in PROSE_ONLY:
                    continue
                text = ISO.sub("", line) if cat == "clock-time" else line
                if rx.search(text):
                    found.append(f"{rel}:{n}: {cat}")
    return found


def main(argv):
    root = Path.cwd().resolve()
    if argv:
        paths = []
        for a in argv:
            p = Path(a)
            for q in ([p] if p.is_file() else sorted(x for x in p.rglob("*") if x.is_file())):
                q = q.resolve()
                paths.append(str(q.relative_to(root)) if q.is_relative_to(root) else str(q))
        paths = [q.replace("\\", "/") for q in paths if "__pycache__" not in q]
    else:
        paths = tracked(root)
    found = scan(root, paths)
    for f in found:
        print(f)
    print(f"public text check: expected no internal working text in {len(paths)} files; found {len(found)}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
