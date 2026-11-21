"""Check exact acknowledgments for removed declarations from a protected inventory."""
from collections import Counter
from dataclasses import dataclass
import re

from git_objects import ObjectError
from rules import Finding

RULE = "H4"
OID = re.compile(r"[0-9a-f]{40}\Z")
PREFIX = r"(?:[A-Za-z_]\w*::)*"
IDENTIFIER = r"~?[A-Za-z_]\w*"
OPERATOR = r"operator(?:\[\]|\(\)|[-+*%/^!=<>&|~]+|[ ][A-Za-z_]\w*(?:[ ][A-Za-z_]\w*)*[ *&]*)"
NAME = re.compile(PREFIX + "(?:" + IDENTIFIER + "|" + OPERATOR + r")\Z", re.ASCII)
TRAILERS = "--format=%(trailers:key=Removed-Declaration,valueonly,separator=%x00,unfold)"


@dataclass(frozen=True, order=True)
class Declaration:
    path: str
    line: int
    qualified: str
    identity: str


def acknowledgments(repo, author_head):
    """Read only the true Git trailer block of the exact submitted tip."""
    if not isinstance(author_head, str) or not OID.fullmatch(author_head):
        raise ObjectError("H4 needs the exact submitted commit to read removal trailers.")
    raw = repo.run("show", "-s", "--no-show-signature", TRAILERS, author_head, "--")
    values = raw.decode("utf-8", "replace").strip().split("\0")
    return frozenset(value.strip() for value in values if NAME.fullmatch(value.strip()))


def check_removals(before, after, approved, *, complete):
    """Compare qualified identities supplied by a complete protected declaration inventory.

    A signature change removes its old identity. A move or formatting edit
    retains identity, and is not a removal. A true trailer is intent only.
    The paired compiler comparison still checks dependent files.
    """
    if complete is not True:
        raise ObjectError("H4 needs a complete before-and-after declaration inventory.")
    before, after = tuple(before), tuple(after)
    for item in before + after:
        if (not isinstance(item, Declaration) or not item.path.startswith("include/") or not item.identity
                or not NAME.fullmatch(item.qualified) or type(item.line) is not int or item.line < 1):
            raise ObjectError("H4 cannot identify a declaration in the protected inventory.")

    remaining = Counter((record.qualified, record.identity) for record in after)
    findings = []
    for old in sorted(before):
        key = old.qualified, old.identity
        if remaining[key]:
            remaining[key] -= 1
        elif old.qualified not in approved:
            findings.append(Finding(
                old.path, old.line, RULE, f"This change removes or renames {old.qualified}.",
                f"Restore it or add Removed-Declaration: {old.qualified} to the last commit.",
            ))
    return sorted(set(findings))
