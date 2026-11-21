"""Bind new forced inlining and related pragmas to donor or protected native evidence."""
from collections import Counter, defaultdict
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import PurePosixPath
import re

from cpp import Source, matching
from definitions import CLASS_HEAD, IDENT, LINKAGE, NAMESPACE
from git_objects import ObjectError
from header_noinline import segments
from rules import Finding

FORCE = {"__forceinline", "WWINLINE"}
PRAGMAS = {"intrinsic", "function", "inline_depth", "inline_recursion", "auto_inline"}
HASH = re.compile(r"[0-9a-f]{64}\Z")
RVA = re.compile(r"\b0x([0-9a-fA-F]{4,8})\b")
NOTE = re.compile(r"^\s*//\s*evidence\s*:", re.IGNORECASE)
ARG_TYPE_WORDS = {"const", "volatile", "unsigned", "signed", "int", "long", "short",
                  "void", "char", "bool", "float", "double", "wchar_t", "__int8", "__int16", "__int32", "__int64"}
DONOR_ROOT = "reference/CnC_Generals_Zero_Hour/GeneralsMD/Code"
DONOR_EXTENSIONS = {".h", ".hpp", ".inl", ".cpp", ".c"}
DONOR_LIMIT = 4 * 1024 * 1024


@dataclass(frozen=True, order=True)
class Site:
    path: str
    line: int
    kind: str
    subject: str
    owner: str
    signature: str
    rvas: tuple[int, ...]


@dataclass(frozen=True)
class NativeProof:
    """Record from an independently authenticated producer, never a PR attachment."""
    base: str
    head: str
    tree: str
    site: Site
    source_sha256: str
    proved_rvas: tuple[int, ...]
    caller_sites: tuple[int, ...]
    expanded_sites: tuple[int, ...]
    complete_callers: bool
    ordinary_form: str
    measurement_sha256: str


def digest(values):
    raw = json.dumps(values, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return sha256(raw).hexdigest()


def scopes_at(scopes):
    names = []
    for values in scopes:
        text = " ".join(values)
        ns, record = NAMESPACE.fullmatch(text), CLASS_HEAD.fullmatch(text)
        if ns and ns[1]:
            names.append(re.sub(r"\s+", "", ns[1]))
        elif record and not record["args"]:
            names.append(re.sub(r"\s+", "", record["name"]))
        elif not LINKAGE.fullmatch(text):
            return None
    return "::".join(names)


def arguments(values):
    """Canonicalize ordinary parameter names, with no guessed alias equivalence."""
    current, groups = [], []
    for value in values:
        if value == ",":
            if not current:
                return None
            groups.append(current)
            current = []
        elif value in {"(", ")", "<", ">", ">>", "[", "]", "="}:
            return None
        else:
            current.append(value)
    if current:
        groups.append(current)
    elif groups:
        return None
    normalized = []
    for group in groups:
        last = group[-1]
        if (len(group) > 1 and IDENT.fullmatch(last) and last not in ARG_TYPE_WORDS
                and group[-2] not in {"::", "enum", "class", "struct"}
                and any(word not in {"const", "volatile"} for word in group[:-1])):
            group = group[:-1]
        normalized.append(group)
    return normalized


def callable_at(values, scopes):
    scope = scopes_at(scopes)
    if scope is None or "(" not in values or values[:1] == ("#",):
        return "", "", ""
    left = values.index("(")
    right = matching(values, left)
    if not left or right is None or not IDENT.fullmatch(values[left - 1]):
        return "", "", ""
    start = left - 1
    if values[start - 1:start] == ("~",):
        start -= 1
    while start >= 2 and values[start - 1] == "::" and IDENT.fullmatch(values[start - 2]):
        start -= 2
    name = "".join(values[start:left])
    owner = "::".join(filter(None, (scope, name.rpartition("::")[0])))
    subject = "::".join(filter(None, (scope, name)))
    args = arguments(values[left + 1:right])
    suffix = values[right + 1:]
    if args is None or any(token not in {"const", "volatile", "override", "final"} for token in suffix):
        return "", "", ""
    prefix = tuple(token for token in values[:start] if token not in {"inline", "virtual"})
    qualifiers = tuple(token for token in suffix if token not in {"override", "final"})
    return subject, owner, digest((prefix, args, qualifiers))


def nominated_rvas(source, line, declaration_line):
    for index in range(min(line, declaration_line) - 2, -1, -1):
        text = source.lines[index]
        if text.strip():
            comment = next((item for item in source.comments if item.kind == "line"
                            and item.line == item.end_line == index + 1), None)
            if comment and NOTE.match(text):
                return tuple(sorted({int(match, 16) for match in RVA.findall(comment.value)}))
            return ()
    return ()


def changes_in(path, text):
    source = Source(text)
    for scopes, tokens in segments(source):
        values = tuple(token.value for token in tokens)
        if values[:2] == ("#", "pragma") and len(values) > 2 and values[2] in PRAGMAS:
            line = tokens[0].line
            yield Site(path, line, "pragma", values[2], "", digest(values[2:]), nominated_rvas(source, line, line))
        for index, value in enumerate(values):
            if value not in FORCE:
                continue
            line = tokens[index].line
            clean = tuple(token for token in values if token not in FORCE)
            subject, owner, signature = callable_at(clean, scopes)
            if not signature:
                signature = digest((scopes, clean, index))
            yield Site(path, line, "forceinline", subject, owner, signature,
                       nominated_rvas(source, line, tokens[0].line))


def owner_key(site):
    return site.kind, site.subject, site.owner, site.signature


class DonorCatalog:
    """Read lexical donor sites from the pinned protected Zero Hour source."""
    def __init__(self, files):
        self.subjects = defaultdict(list)
        for path, text in files:
            for site in changes_in(path, text):
                if site.subject:
                    self.subjects[site.kind, site.subject].append(site)

    def candidates(self, site):
        target = PurePosixPath(site.path)
        for found in sorted(self.subjects.get((site.kind, site.subject), ())):
            source = PurePosixPath(found.path)
            if site.kind == "pragma":
                allowed = source.name.casefold() == target.name.casefold()
            else:
                allowed = (source.stem.casefold() == target.stem.casefold()
                           or bool(site.owner and site.owner == found.owner))
            if allowed:
                yield found

    def counterpart(self, site):
        return next((item for item in self.candidates(site) if owner_key(item) == owner_key(site)), None)


def donor_from_repo(repo, protected_base):
    """Load only regular donor blobs from the protected base, never from head."""
    def files():
        entries = sorted(repo.tree(protected_base, DONOR_ROOT))
        if not entries:
            raise ObjectError("H8 needs the protected Zero Hour source.")
        for path, entry in entries:
            if PurePosixPath(path).suffix.casefold() not in DONOR_EXTENSIONS:
                continue
            if not entry.regular:
                raise ObjectError("H8 cannot read a protected donor source file.")
            _, raw = repo.blob(entry.oid, DONOR_LIMIT)
            if raw is None:
                raise ObjectError("H8 cannot read a protected donor source file within the size bound.")
            text = raw.decode("latin-1").replace("\r\n", "\n")
            if any(marker in text for marker in ("__forceinline", "WWINLINE", "pragma", "\\\n", "??/")):
                yield path, text

    return DonorCatalog(files())


def native_match(site, proof, binding, source_sha256):
    """Match content and exact source identities after the adapter validates origin."""
    return (
        (proof.base, proof.head, proof.tree) == binding
        and proof.site == site and proof.source_sha256 == source_sha256
        and bool(site.rvas) and proof.proved_rvas == site.rvas
        and proof.complete_callers is True and bool(proof.caller_sites)
        and tuple(sorted(set(proof.caller_sites))) == proof.caller_sites == proof.expanded_sites
        and all(type(address) is int and 0 < address <= 0xFFFFFFFF for address in proof.caller_sites)
        and proof.ordinary_form == "verified-different"
        and HASH.fullmatch(proof.measurement_sha256) is not None
    )


def decide(path, before, after, donor, binding, *, published_native=()):
    """Return named refusals, unresolved proof requests and passing witnesses."""
    source_sha256 = sha256(after.encode("utf-8")).hexdigest()
    old = Counter(map(owner_key, changes_in(path, before)))
    findings, held, accepted = [], [], []
    for site in sorted(changes_in(path, after)):
        key = owner_key(site)
        if old[key]:
            old[key] -= 1
            continue
        counterpart = donor.counterpart(site) if donor is not None else None
        if counterpart:
            accepted.append((site, counterpart.path, counterpart.line))
            continue
        where = site.subject or "this declaration"
        ambiguous = donor is None or not site.subject or any(donor.candidates(site))
        if site.kind == "forceinline" and path.startswith("src/"):
            if ambiguous:
                held.append((site, "The exact Zero Hour declaration has not been established."))
            else:
                findings.append(Finding(path, site.line, "H8",
                    f"{where} adds forced inlining without a corresponding Zero Hour declaration.",
                    "Remove forced inlining or use the corresponding shared declaration."))
            continue
        if site.rvas and any(native_match(site, proof, binding, source_sha256) for proof in published_native):
            accepted.append((site, "retail caller evidence", 0))
        elif site.rvas or ambiguous:
            held.append((site, "This compiler control needs an exact donor match or verified retail caller evidence."))
        else:
            findings.append(Finding(path, site.line, "H8",
                f"{where} adds a compiler control without matching donor or retail caller evidence.",
                "Remove the control or cite the retail addresses in an evidence comment and submit the verified comparison."))
    return findings, held, accepted
