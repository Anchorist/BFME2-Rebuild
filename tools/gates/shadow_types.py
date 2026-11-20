"""Report explicit type swaps without affecting the source verdict."""

from collections import defaultdict
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from functools import lru_cache
import json
from pathlib import PurePosixPath
import re
import subprocess
import sys

from cpp import Source, decode
from git_objects import Git, ObjectError

MAX_BYTES = 1 << 20
SUFFIXES = {"src": {".c", ".cpp"}, "include": {".h", ".hh", ".hpp", ".inl"}}
IDENT = re.compile(r"[A-Za-z_]\w*", re.ASCII)
QUALIFIED = re.compile(r"(?:[A-Za-z_]\w* :: )*[A-Za-z_]\w*", re.ASCII)
INTEGER = {"char", "unsigned", "signed", "short", "int", "long", "wchar_t",
           "__int8", "__int16", "__int32", "__int64"}
CV = {"const", "volatile"}
MODIFIERS = CV | {"static", "mutable", "extern", "register", "inline", "constexpr",
                  "constinit", "thread_local"}
NONDECL = {"return", "delete", "new", "throw", "goto", "union", "typedef", "using", "case",
           "else", "sizeof", "alignof", "do", "break", "continue", "friend", "auto", "bool"}
CLASS_DECL = re.compile(r"\b(?:class|struct) ([A-Za-z_]\w*) (?:final )?(?=[{:;])")


@dataclass(frozen=True)
class Declaration:
    name: str
    spelling: tuple
    first: int
    last: int
    scope: tuple
    init: tuple = ()


@dataclass(frozen=True)
class Fact:
    path: str
    line: int
    name: str
    old_type: str
    new_type: str
    before_line: int


def plain_integer(words):
    return bool(words) and set(words) <= INTEGER


def eligible(path):
    root, _, rest = path.partition("/")
    return bool(rest) and PurePosixPath(rest).suffix.lower() in SUFFIXES.get(root, ())


def scoped_statements(source):
    """Recognize only ordinary semicolon declarators outside nested parentheses."""
    hidden = {i for first, stop in source.directives() for i in range(first, stop)}
    statement, scopes = [], []
    paren = brackets = 0
    for i, token in enumerate(source.tokens):
        if i in hidden:
            continue
        word = token.value
        if word == "(":
            paren += 1
        elif word == ")":
            paren = max(paren - 1, 0)
        elif word == "[":
            brackets += 1
        elif word == "]":
            brackets = max(brackets - 1, 0)
        elif not paren and not brackets:
            if word == "{":
                head = tuple(t.value for t in statement)
                scopes.append(head if len(head) <= 96 else ("@",))
                statement = []
                continue
            if word == "}":
                if scopes:
                    scopes.pop()
                statement = []
                continue
            if word == ":" and [t.value for t in statement] in (["private"], ["protected"], ["public"]):
                statement = []
                continue
            if word == ";":
                if statement:
                    yield statement, tuple(scopes), token.line
                statement = []
                continue
        statement.append(token)


def declaration(tokens, scope, last):
    words = tuple(t.value for t in tokens)
    main, _, init = " ".join(words).partition(" = ")
    words = tuple(main.split())
    if len(words) < 2:
        return None
    name, spelling = words[-1], words[:-1]
    core = tuple(w for w in spelling if w not in MODIFIERS)
    if not core or not IDENT.fullmatch(name) or name in INTEGER | MODIFIERS | NONDECL or core[0] in NONDECL:
        return None
    return Declaration(name, spelling, tokens[0].line, last, scope, tuple(init.split()))


def aliases(words):
    if len(words) > 2 and words[0] == "typedef" and IDENT.fullmatch(words[-1]):
        return words[-1], words[1:-1]
    if len(words) > 3 and words[0] == "using" and words[2] == "=" and IDENT.fullmatch(words[1]):
        return words[1], words[3:]
    return None


@lru_cache(maxsize=512)
def parse(text):
    source = Source(text)
    declarations, statements = [], []
    alias_candidates = defaultdict(set)
    for tokens, scope, last in scoped_statements(source):
        words = tuple(t.value for t in tokens)
        statements.append((words, scope, tokens[0].line, last))
        parsed = declaration(tokens, scope, last)
        if parsed:
            declarations.append(parsed)
        alias = aliases(words)
        if alias:
            alias_candidates[alias[0]].add((alias[1], scope))
    return declarations, statements, alias_candidates


def resolve(words, alias_candidates, scope, enabled):
    words = tuple(w for w in words if w not in MODIFIERS)
    seen = set()
    while enabled and len(words) == 1 and words[0] not in seen:
        name = words[0]
        options = {(value, owner) for value, owner in alias_candidates.get(name, ())
                   if scope[:len(owner)] == owner}
        if len(options) != 1:
            break
        seen.add(name)
        words, _ = options.pop()
        words = tuple(w for w in words if w not in MODIFIERS)
    return words


def classified(words, known_class):
    if plain_integer(words):
        return "integer"
    pointer = False
    while words and words[-1] == "*":
        pointer = True
        words = words[:-1]
    tagged = words[:1] in (("class",), ("struct",))
    if tagged:
        words = words[1:]
    name = " ".join(words)
    if pointer and (QUALIFIED.fullmatch(name) or plain_integer(words)):
        return "pointer"
    if QUALIFIED.fullmatch(name) and (tagged or known_class(name)):
        return "class"
    return None


def spots(items, first, stop):
    found = defaultdict(list)
    for decl in items:
        if decl.first <= stop and first < decl.last:
            found[decl.scope, decl.name].append(decl)
    return found


def compare(text0, text1, path, known_class, *, multiline=False, use_aliases=False):
    old, _, old_aliases = parse(text0)
    new, _, new_aliases = parse(text1)
    paired = set()
    edits = SequenceMatcher(None, text0.splitlines(), text1.splitlines(), autojunk=False)
    for op, a, b, c, d in edits.get_opcodes():
        if op != "replace":
            continue
        before, after = spots(old, a, b), spots(new, c, d)
        for key in sorted(before.keys() & after.keys()):
            if len(before[key]) != 1 or len(after[key]) != 1:
                continue
            left, right = before[key][0], after[key][0]
            if not multiline and (left.first != left.last or right.first != right.last):
                continue
            words1 = resolve(right.spelling, new_aliases, right.scope, use_aliases)
            if not plain_integer(words1):
                continue
            words0 = resolve(left.spelling, old_aliases, left.scope, use_aliases)
            if classified(words0, known_class) in {"pointer", "class"}:
                paired.add(Fact(path, right.first, right.name,
                                " ".join(left.spelling), " ".join(right.spelling), left.first))
    return sorted(paired, key=lambda x: (x.path, x.line, x.name, x.before_line))


def reader(git, tree):
    @lru_cache(maxsize=256)
    def known(spelling):
        if " :: " in spelling:
            return False
        if not IDENT.fullmatch(spelling):
            return False
        # Search candidate spellings only, then use the lexer to verify each
        # declaration. Inactive preprocessor branches remain lexical evidence.
        pattern = f"(class|struct)[[:space:]]+{spelling}([[:space:]:;{{]|$)"
        result = subprocess.run(
            git.command + ["grep", "-I", "-l", "-z", "-E", "-e", pattern, tree, "--", "include", "src"],
            env=git.env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        if result.returncode == 1:
            return False
        if result.returncode:
            raise ObjectError("The protected class name search failed.")
        for hit in result.stdout.split(b"\0"):
            if not hit:
                continue
            path = hit.split(b":", 1)[1].decode("utf-8", "surrogateescape")
            if not eligible(path):
                continue
            raw = git.run("cat-file", "blob", f"{tree}:{path}")
            if len(raw) > MAX_BYTES:
                continue
            try:
                atoms = [t.value if t.kind != "literal" else "$literal" for t in Source(decode(raw)).tokens]
            except UnicodeError:
                continue
            if spelling in CLASS_DECL.findall(" ".join(atoms)):
                return True
        return False
    return known


def pairs(git, base, head):
    for diff in git.diff(base, head):
        if not eligible(diff.path) or not diff.old or not diff.new or not diff.old.regular or not diff.new.regular:
            continue
        _, old = git.blob(diff.old.oid, MAX_BYTES)
        _, new = git.blob(diff.new.oid, MAX_BYTES)
        if old is None or new is None:
            continue
        try:
            yield diff.path, decode(old), decode(new)
        except UnicodeError:
            continue


def measure(git, base, head):
    known = reader(git, base)
    return [asdict(f) for path, old, new in pairs(git, base, head)
            for f in compare(old, new, path, known)]


if __name__ == "__main__":
    repository, base, head = sys.argv[1:]
    with Git(repository) as repo:
        print(json.dumps(measure(repo, repo.tree_oid(base), repo.tree_oid(head)),
                         ensure_ascii=True, sort_keys=True))
