"""Audit 1.5: the declaration and ancestry side of the inline owner-scope packet.

For each tree (parent = main, candidate = the composed pull request tree) this reads every class definition in the
project's own source text (include/ and src/) and produces the side the owner-scope selector consumes:

    {"tree", "complete", "paths", "classes": [{"owner", "declarations", "bases", "polymorphic"}]}

- owner        the qualified class name (enclosing namespaces and classes joined with ::)
- declarations SHA-256 of every definition of the class (its own body text, comments and spacing normalised, and
               its base list) together with every out-of-line member definition in a header (Owner::f() { ... }),
               so a change to the class or to an inline member body defined outside it changes the digest
- bases        the resolved qualified names of its direct bases (exact name or through enclosing scopes only)
- polymorphic  the class or one of its bases declares a virtual function

Only the classes the selector can reach are listed: those whose record differs between the two trees, their
descendants anywhere in the tree, and every ancestor of those. A side is complete only when nothing it depends on
escaped this reader:
- no listed class has an unresolved or template base, is a template or union, or is defined more than once;
- no changed header differs outside the class bodies and bound member definitions it parsed (preprocessor lines,
  macros, typedefs, free functions, a class head this reader cannot parse all count);
- no changed source file differs in its preprocessor lines or top-level typedef/using statements;
- no changed file has a class it could not delimit or a class head it cannot read (an export macro before the
  name, a macro call in the head);
- every changed path is a file this reader reads;
- no class anywhere has an unresolved base whose name, after typedef and using aliases, is a selected class's name.
Bases resolve through enclosing scopes, the file's using-directives and typedef/using aliases. Inline member bodies
bind to their class in source files too; a duplicated class takes the bases of every copy.
Anything else sets complete to false, which makes the selector hold. Tables are attached afterwards from the compiled
objects (compiled_table_owners.bind_inventory_side).
"""
from collections import defaultdict
import hashlib
import json
import re
import subprocess

from h5_witness import _mask

SOURCE = re.compile(r"(?:include|src)/.+\.(?:h|hpp|inl|cpp)\Z", re.I)
HEADER_FILE = re.compile(r".+\.(?:h|hpp|inl)\Z", re.I)
QUALIFIED = r"[A-Za-z_]\w*(?:\s*::\s*[A-Za-z_]\w*)*"
DECLSPEC = r"(?:\s*__declspec\s*\((?:[^()]|\([^()]*\))*\))*"
HEAD = re.compile(r"\b(class|struct|union|namespace)\b" + DECLSPEC + r"\s*(" + QUALIFIED + r")?")
MEMBER_DEF = re.compile(r"(" + QUALIFIED + r")\s*::\s*(~?\s*[A-Za-z_]\w*|operator\s*[^\s(]+)\s*\(")
DIRECTIVE = re.compile(r"^[ \t]*#.*(?:\\\n.*)*", re.M)
MAX_FILES = 40_000
_SCANNED = {}


class Unreadable(Exception):
    pass


def _matching(text, open_, opening="{", closing="}"):
    depth = 0
    for index in range(open_, len(text)):
        if text[index] == opening:
            depth += 1
        elif text[index] == closing:
            depth -= 1
            if depth == 0:
                return index
    return None


def _split_bases(clause):
    parts, depth, current = [], 0, ""
    for char in clause:
        depth += char == "<"
        depth -= char == ">"
        if char == "," and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current)
    out = []
    for part in parts:
        name = re.sub(r"\b(?:public|protected|private|virtual)\b", " ", part)
        out.append("".join(name.split()))
    return out


def _normal(text):
    return " ".join(text.split())


def _cut(text, spans):
    """text with the given (start, end_inclusive) spans removed, outermost first."""
    out, cursor = [], 0
    for start, end in sorted(spans):
        if start < cursor:
            continue
        out.append(text[cursor:start])
        cursor = end + 1
    out.append(text[cursor:])
    return " ".join(out)


def scan(path, data):
    """One file: {"classes": [...], "defs": [(scope, qualifier, text)], "residual": str, "problems": [...]}."""
    text = data.decode("latin-1")
    masked = _mask(text)
    spans, classes, problems = [], [], []
    hidden = set()          # identifiers in class heads this reader could not read: possible hidden derivations
    for match in HEAD.finditer(masked):
        kind, name = match.group(1), _normal(match.group(2) or "").replace(" ", "")
        cursor = match.end()
        while cursor < len(masked) and masked[cursor] not in "{;()=":
            cursor += 1
        tail = re.split(r"[;{}]", masked[max(0, match.start() - 400):match.start()])[-1]
        if re.search(r"\benum\s*$", tail):
            continue
        if "template" in tail and tail.count("<") > tail.count(">"):
            continue                                        # a template parameter: template <class T>
        if cursor < len(masked) and masked[cursor] == "(" and kind != "namespace":
            brace, semicolon = masked.find("{", cursor), masked.find(";", cursor)
            if brace >= 0 and (semicolon < 0 or brace < semicolon):
                problems.append(f"unparsed class head {name or kind}")   # class MACRO(16) Name {, or a function
                hidden.update(re.findall(r"[A-Za-z_]\w*", masked[match.end():brace]))
            continue
        if cursor >= len(masked) or masked[cursor] != "{":
            continue                                        # declaration, parameter, cast or variable
        close = _matching(masked, cursor)
        if close is None:
            problems.append(name or kind)
            continue
        head = masked[match.end():cursor].replace("::", "\0")
        before_clause = head.split(":", 1)[0] if ":" in head else head
        if kind != "namespace" and before_clause.strip() not in ("", "final"):
            problems.append(f"unparsed class head {name} {before_clause.strip()[:40]}")   # class EXPORT_MACRO Name
            hidden.update(re.findall(r"[A-Za-z_]\w*", head.replace("\0", "::")))
            continue
        spans.append({"start": match.start(), "open": cursor, "close": close, "kind": kind, "name": name})
        if kind != "namespace" and name:
            clause = head.split(":", 1)[1].replace("\0", "::") if ":" in head else ""
            classes.append({"name": name, "kind": kind, "open": cursor, "close": close, "start": match.start(),
                            "bases_raw": _split_bases(clause) if clause.strip() else [],
                            "template": bool(re.search(r"\btemplate\s*<[^;{}]*$", tail)) or "<" in name,
                            "head_ids": re.findall(r"[A-Za-z_]\w*", (re.search(r"\btemplate\s*<[^;{}]*$", tail)
                                                                       or re.match("", "")).group(0))})
    spans.sort(key=lambda span: span["open"])

    def scope_of(position, exclude_open=None):
        return [span["name"] for span in spans if span["open"] < position <= span["close"] and span["name"]
                and span["open"] != exclude_open]

    for item in classes:
        scope = scope_of(item["open"], exclude_open=item["open"])
        item["scope"] = scope
        item["owner"] = "::".join(scope + [item["name"]])
        children = [(s["start"], s["close"]) for s in spans
                    if s["kind"] != "namespace" and item["open"] < s["start"] and s["close"] < item["close"]]
        body = _normal(_cut(masked[item["open"]:item["close"] + 1],
                            [(a - item["open"], b - item["open"]) for a, b in children]))
        item["virtual"] = bool(re.search(r"\bvirtual\b", body))
        item["text"] = json.dumps([body, item["bases_raw"]])
    class_spans = [(item["start"], item["close"]) for item in classes]
    # Out-of-line member definitions outside every class body: Owner::f(...) [const] [: init] { ... }
    defs, def_spans = [], []
    for match in MEMBER_DEF.finditer(masked):
        if any(start <= match.start() <= end for start, end in class_spans):
            continue
        params_end = _matching(masked, match.end() - 1, "(", ")")
        if params_end is None:
            continue
        cursor = params_end + 1
        while cursor < len(masked) and masked[cursor] not in "{;":
            cursor += 1
        if cursor >= len(masked) or masked[cursor] != ";" and masked[cursor] != "{":
            continue
        if masked[cursor] == ";":
            continue                                        # a declaration, not a definition
        close = _matching(masked, cursor)
        if close is None:
            problems.append(match.group(1))
            continue
        qualifier = match.group(1).replace(" ", "")
        lead = re.split(r"[;{}]", masked[max(0, match.start() - 200):match.start()])[-1]
        inline = bool(re.search(r"\b(?:inline|__inline|__forceinline)\b", lead))
        defs.append((scope_of(match.start()), qualifier, _normal(masked[match.start():close + 1]), inline))
        def_spans.append((match.start(), close))
    outside = _normal(_cut(masked, class_spans + def_spans))
    directives = "\n".join(_normal(line) for line in DIRECTIVE.findall(text))
    typedefs = " ".join(re.findall(r"\b(?:typedef|using)\b[^;{}]*;", outside))
    residual = (outside if HEADER_FILE.fullmatch(path) else typedefs) + "\n#\n" + directives
    aliases = {}
    for target, name in re.findall(r"\btypedef\s+(?:(?:class|struct|union|typename)\s+)?([A-Za-z_][\w:]*(?:\s*<[^;{}]*>)?)"
                                   r"\s+([A-Za-z_]\w*)\s*;",
                                   masked):
        aliases[name] = target
    for name, target in re.findall(r"\busing\s+([A-Za-z_]\w*)\s*=\s*(?:(?:class|struct|union|typename)\s+)?"
                                   r"([A-Za-z_][\w:]*(?:\s*<[^;{}]*>)?)\s*;",
                                   masked):
        aliases[name] = target
    namespaces = re.findall(r"\busing\s+namespace\s+([A-Za-z_][\w:]*)\s*;", masked)
    # Object-like macros: a one-identifier body is an alias; any other body may still name a class, so its
    # identifiers count as names a base spelled with that macro could mean.
    macros, makers = {}, set()
    spliced = re.sub(r"\\\r?\n", " ", text)
    for name, params, body in re.findall(r"^[ \t]*#[ \t]*define[ \t]+([A-Za-z_]\w*)(\([^)\n]*\))?[ \t]*(.*)$",
                                         spliced, re.M):
        idents = re.findall(r"[A-Za-z_]\w*(?:::[A-Za-z_]\w*)*", body)
        if not params and len(idents) == 1 and body.strip() == idents[0]:
            aliases.setdefault(name, idents[0])
        elif idents:
            macros[name] = [ident.split("::")[-1] for ident in idents]
        if re.search(r"\b(?:class|struct|union)\b", body):
            # A macro that declares a class: anything its body names may be that class's base.
            makers.add(name)
            hidden.update(ident.split("::")[-1] for ident in idents)
    # Statement-position calls anywhere (top level, namespaces, class bodies): their arguments count when the
    # callee turns out to be a class-making macro (records() decides, since the definition may be in another file).
    calls = defaultdict(set)
    for call in re.finditer(r"\b([A-Za-z_]\w*)\s*\(", masked):
        close = _matching(masked, call.end() - 1, "(", ")")
        args = masked[call.end():close] if close is not None else masked[call.end():call.end() + 4096]
        calls[call.group(1)].update(re.findall(r"[A-Za-z_]\w*", args))
    # A class declared by a macro call outside any class body (DECLARE_CLASS(Foo, Base)) is invisible to this
    # reader: the names in such calls count as possible bases.
    for args in re.findall(r"(?:^|[;{}])\s*[A-Z_][A-Z0-9_]*\s*\(([^;{}()]*)\)", outside):
        hidden.update(re.findall(r"[A-Za-z_]\w*", args))
    return {"classes": classes, "defs": defs, "residual": residual, "problems": problems, "aliases": aliases,
            "using": namespaces, "hidden": sorted(hidden), "macros": macros, "makers": sorted(makers),
            "calls": {callee: sorted(names) for callee, names in calls.items()}}


def tree_files(git_dir, tree):
    """{path: bytes} of every project source file in a Git tree, read as objects (nothing is checked out)."""
    listing = subprocess.run(["git", "--git-dir", str(git_dir), "ls-tree", "-r", "-z", tree],
                             capture_output=True, check=True).stdout.split(b"\0")
    wanted = []
    for row in listing:
        if not row:
            continue
        meta, path = row.split(b"\t", 1)
        mode, kind, oid = meta.split()
        name = path.decode("utf-8", "replace")
        if kind == b"blob" and mode in (b"100644", b"100755") and SOURCE.fullmatch(name):
            wanted.append((name, oid.decode()))
    if len(wanted) > MAX_FILES:
        raise Unreadable("Too many source files.")
    batch = subprocess.run(["git", "--git-dir", str(git_dir), "cat-file", "--batch"],
                           input=b"".join(oid.encode() + b"\n" for _, oid in wanted),
                           capture_output=True, check=True).stdout
    files, offset = {}, 0
    for name, oid in wanted:
        header_end = batch.index(b"\n", offset)
        _, _, size = batch[offset:header_end].split()
        start = header_end + 1
        files[name] = batch[start:start + int(size)]
        offset = start + int(size) + 1
    return files


def _resolve(target, scope, owners):
    """A name as C++ looks it up from a scope: innermost enclosing scope first, then the global name. No guessing."""
    target = target.lstrip(":")
    for depth in range(len(scope), -1, -1):
        name = "::".join(scope[:depth] + [target])
        if name in owners:
            return name
    return None


def records(files):
    """Every class on one tree, plus per-file residuals and undelimited definitions."""
    occurrences, defs, residuals, problems = defaultdict(list), [], {}, {}
    aliases, using, hidden_bases, macros = {}, {}, set(), {}
    makers, calls = set(), defaultdict(set)
    for path in sorted(files):
        key = (path, hashlib.sha256(files[path]).digest())
        found = _SCANNED.get(key)
        if found is None:
            found = _SCANNED[key] = scan(path, files[path])        # both trees share all unchanged files
        residuals[path] = found["residual"]
        using[path] = found["using"]
        aliases.update(found["aliases"])
        macros.update(found["macros"])
        makers.update(found.get("makers", ()))
        for callee, names in found.get("calls", {}).items():
            calls[callee].update(names)
        hidden_bases.update(found["hidden"])
        if found["problems"]:
            problems[path] = found["problems"]
        for item in found["classes"]:
            occurrences[item["owner"]].append(dict(item, path=path))
        header = HEADER_FILE.fullmatch(path)
        # Member bodies bind to their class in headers, and in source files when declared inline: those are the
        # bodies an inline virtual check compares. Other source-file bodies are the native comparison's.
        defs.extend((path, scope, qualifier, body) for scope, qualifier, body, inline in found["defs"]
                    if header or inline)
    bound = defaultdict(list)
    for path, scope, qualifier, body in defs:
        owner = _resolve(qualifier, scope, occurrences)
        if owner is None:
            residuals[path] += "\nunbound " + body                 # an inline body this reader cannot bind
        else:
            bound[owner].append(body)

    def lookup(raw, scope, path):
        """Through enclosing scopes, the file's using-directives and typedef/using aliases (bounded)."""
        target = raw
        for _ in range(4):
            name = _resolve(target, scope, occurrences)
            for space in using.get(path, ()):
                name = name or _resolve(space + "::" + target.lstrip(":"), [], occurrences)
            if name:
                return name
            bare = target.split("::")[-1]
            if bare not in aliases:
                return None
            target = aliases[bare]
        return None
    # Identifiers a class template can pass on as a base: its template head (parameters and their defaults) and
    # its own base clause. A class deriving from Wrap<...> may derive from any of them.
    template_ids = defaultdict(set)
    for owner, items in occurrences.items():
        for item in items:
            if item["template"]:
                key = owner.split("<")[0].split("::")[-1]
                template_ids[key].update(item.get("head_ids", ()))
                for raw in item["bases_raw"]:
                    template_ids[key].update(re.findall(r"[A-Za-z_]\w*", raw))

    def reachable(raw):
        """Every identifier a base text can stand for: its own (template arguments included), alias bodies,
        multi-token macro bodies and class-template heads and bases, to a fixed point."""
        seen, todo = set(), re.findall(r"[A-Za-z_]\w*", raw)
        while todo:
            ident = todo.pop()
            if ident in seen:
                continue
            seen.add(ident)
            todo.extend(re.findall(r"[A-Za-z_]\w*", aliases.get(ident, "")))
            todo.extend(macros.get(ident, ()))
            todo.extend(template_ids.get(ident, ()))
        return seen
    resolved = {}
    for owner, items in occurrences.items():
        first = items[0]
        bases, unresolved = [], []
        for item in items:                                      # every copy of a duplicated class
            for raw in item["bases_raw"]:
                name = None if "<" in raw else lookup(raw, item["scope"], item["path"])
                if name and name not in bases:
                    bases.append(name)
                elif not name and raw not in unresolved:
                    unresolved.append(raw)
        unresolved_bare = []
        for raw in unresolved:
            bare = raw.split("<")[0].split("::")[-1]
            for _ in range(4):
                if bare not in aliases:
                    break
                bare = aliases[bare].split("<")[0].split("::")[-1]
            unresolved_bare.append(bare)
            unresolved_bare.extend(macros.get(bare, ()))      # a base spelled with a multi-token macro
            unresolved_bare.extend(sorted(reachable(raw) - set(unresolved_bare)))   # through templates
        digest = hashlib.sha256(json.dumps([sorted(item["text"] for item in items),
                                            sorted(bound.get(owner, ()))]).encode("latin-1")).hexdigest()
        resolved[owner] = {"owner": owner, "digest": digest, "bases": bases, "unresolved": unresolved,
                           "unresolved_bare": unresolved_bare,
                           "virtual": any(item["virtual"] for item in items), "duplicate": len(items) > 1,
                           "template": any(item["template"] for item in items),
                           "union": any(item["kind"] == "union" for item in items)}
    memo = {}

    def poly(owner, trail=()):
        if owner in memo:
            return memo[owner]
        if owner in trail:
            return False
        item = resolved[owner]
        memo[owner] = item["virtual"] or any(poly(base, trail + (owner,)) for base in item["bases"])
        return memo[owner]
    for owner in resolved:
        resolved[owner]["polymorphic"] = poly(owner)
    # A macro is a class maker when its body names a class keyword or another class maker (a wrapper around a
    # maker, or a keyword spelled through a macro): to a fixed point.
    bodies = {name: set(idents) for name, idents in macros.items()}
    for name, target in aliases.items():
        bodies.setdefault(name, set()).update(re.findall(r"[A-Za-z_]\w*", target))
    growing = True
    while growing:
        growing = False
        for name, idents in bodies.items():
            if name not in makers and idents & (makers | {"class", "struct", "union"}):
                makers.add(name)
                growing = True
    for callee in makers:
        hidden_bases.update(bodies.get(callee, ()))          # whatever a maker's body names
        hidden_bases.update(calls.get(callee, ()))           # MAKE_CLASS(Foo, Base) wherever it is called
    hidden_bases = reachable(" ".join(sorted(hidden_bases)))  # through macros, aliases and class templates
    return resolved, residuals, problems, hidden_bases


def _row(item):
    return {"owner": item["owner"], "declarations": item["digest"], "bases": sorted(item["bases"]),
            "polymorphic": item["polymorphic"]}


def sides(parent_files, candidate_files, changed_paths, parent_tree, candidate_tree):
    """(parent_side, candidate_side, report) for the owner-scope packet."""
    old, old_residual, old_bad, old_hidden = records(parent_files)
    new, new_residual, new_bad, new_hidden = records(candidate_files)
    changed = {owner for owner in old.keys() | new.keys()
               if (owner in old) != (owner in new) or _row(old[owner]) != _row(new[owner])}
    children = defaultdict(set)
    for table in (old, new):
        for owner, item in table.items():
            for base in item["bases"]:
                children[base].add(owner)
    selected, pending = set(changed), list(changed)
    while pending:
        for child in children[pending.pop()] - selected:
            selected.add(child)
            pending.append(child)
    listed, pending = set(selected), list(selected)
    while pending:
        owner = pending.pop()
        for table in (old, new):
            for base in (table.get(owner) or {}).get("bases", ()):
                if base not in listed:
                    listed.add(base)
                    pending.append(base)
    issues = []
    # A class whose base this reader could not resolve may still derive from a selected class (through a typedef,
    # a using-declaration or a namespace it cannot see): if the base's bare name, after aliases, is a selected
    # class's bare name, the scope may be missing a descendant.
    selected_bare = {owner.split("::")[-1] for owner in selected}
    for table in (old, new):
        for owner, item in table.items():
            hidden = [name for name in item["unresolved_bare"] if name in selected_bare]
            if hidden and owner not in selected:
                issues.append(f"{owner}: unresolved base {hidden[0]} may be a selected class")
    # A class head this reader could not read (an export or alignment macro), in ANY file, may name a selected
    # class as its base: hold when any identifier in such a head is a selected class's name.
    for name in sorted((old_hidden | new_hidden) & selected_bare):
        issues.append(f"an unreadable class head names {name}, a selected class")
    for path in changed_paths:
        if path not in parent_files and path not in candidate_files:
            issues.append(f"{path}: a changed file this reader does not read")
    for owner in sorted(listed):
        for table in (old, new):
            item = table.get(owner)
            if not item:
                continue
            if item["duplicate"]:
                issues.append(f"{owner}: defined more than once")
            if item["unresolved"]:
                issues.append(f"{owner}: base {item['unresolved'][0]} not resolved to one project class")
            if item["template"] or item["union"]:
                issues.append(f"{owner}: template or union class")
    for path in changed_paths:
        if old_bad.get(path) or new_bad.get(path):
            issues.append(f"{path}: a definition could not be delimited")
        if old_residual.get(path, "") != new_residual.get(path, ""):
            issues.append(f"{path}: changes outside the class bodies this reader binds")
    complete = not issues
    paths = sorted(changed_paths)

    def side(table, tree):
        return {"tree": tree, "complete": complete, "paths": paths,
                "classes": [_row(table[owner]) for owner in sorted(listed) if owner in table]}
    report = {"changed": sorted(changed), "selected": sorted(selected), "listed": len(listed),
              "issues": sorted(set(issues))[:50]}
    return side(old, parent_tree), side(new, candidate_tree), report


def changed_blobs(git_dir, base, tree):
    """(parent_blobs, candidate_blobs): {path: blob id or None} for every changed path under src/ and include/,
    read the same way the consumer's source projection reads them (no rename detection)."""
    raw = subprocess.run(["git", "--git-dir", str(git_dir), "diff-tree", "-r", "-z", "--no-renames", base, tree,
                          "--", "src", "include"], capture_output=True, check=True).stdout.split(b"\0")
    before, after, index = {}, {}, 0
    while index + 1 < len(raw) and raw[index]:
        meta, path = raw[index].decode(), raw[index + 1].decode("utf-8")
        _, _, old, new, _ = meta.lstrip(":").split()
        before[path] = None if set(old) == {"0"} else old
        after[path] = None if set(new) == {"0"} else new
        index += 2
    return before, after


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def packet_and_attestation(*, binding, issuer, parent_side, candidate_side, parent_tables, candidate_tables,
                           protected_tables, parent_blobs, candidate_blobs, builder):
    """The two files of bfme-inline-owner-scope-<attempt>: (inline-owner-scope.json bytes, attestation dict, report).
    builder is compiled_table_owners (it binds the compiled tables onto each side)."""
    packet, report = builder.build_scope_packet(binding=binding, parent_decl=parent_side, candidate_decl=candidate_side,
                                                parent_tables=parent_tables, candidate_tables=candidate_tables,
                                                protected_tables=protected_tables)
    data = canonical(packet)
    attestation = {
        "version": 1, "kind": "compiled-inline-declarations", "issuer": dict(issuer), "binding": dict(binding),
        "scope_sha256": hashlib.sha256(data).hexdigest(),
        "parent": {"tree": packet["parent"]["tree"], "blobs": dict(parent_blobs),
                   "inventory_sha256": hashlib.sha256(canonical(packet["parent"])).hexdigest()},
        "candidate": {"tree": packet["candidate"]["tree"], "blobs": dict(candidate_blobs),
                      "inventory_sha256": hashlib.sha256(canonical(packet["candidate"])).hexdigest()},
    }
    return data, attestation, report


def in_job_owner_scope(atoms, builder, protected_tables):
    """The owner-scope producer for the inline job itself (managed_inline_action.run, behind
    BFME_INLINE_OWNER_SCOPE=yes). Returns the callable bound_owner_scope takes as protected_inventory.

    Both inputs come from this protected job: the tables from this run's own shard atoms (join_compact's inline
    records, read by compiled_table_owners.extract_from_virtual_atoms), the declarations from the job's own Git
    objects of main and the composed tree. No artifact or author file supplies either. The selector then holds
    unless both sides are complete."""
    records = [row for doc in atoms or () for row in (doc or {}).get("records", ())]
    catalogue = sorted(set(protected_tables))

    def produce(git, plan, candidate, expected):
        tables = {}
        for side in ("parent", "candidate"):
            observed = builder.extract_from_virtual_atoms([row for row in records if row.get("side") == side])
            tables[side] = builder.build_side_tables(observed, protected_tables=catalogue)
        base_tree = git.value("rev-parse", plan["base"] + "^{tree}")
        parent_files, candidate_files = tree_files(git.path, plan["base"]), tree_files(git.path, plan["tree"])
        parent, candidate_side, _ = sides(parent_files, candidate_files, plan["changed_paths"], base_tree,
                                          plan["tree"])
        packet, _ = builder.build_scope_packet(binding=expected, parent_decl=parent, candidate_decl=candidate_side,
                                               parent_tables=tables["parent"], candidate_tables=tables["candidate"],
                                               protected_tables=catalogue)
        return packet
    return produce
