"""Reduce exact trusted measurements into one stable progress table."""
from pathlib import PurePosixPath
import re

DRAFT = "include/Draft/"
HEADERS = (".h", ".hpp", ".inl")
SOURCES = HEADERS + (".cpp", ".c", ".cc", ".cxx")
INCLUDE = re.compile(rb'^[ \t]*#[ \t]*include[ \t]*[<"]([^"\r\n>]+)[">]')
METRICS = ("matched", "proven", "finished", "lost", "drafts_before", "drafts_after")
ADDRESS = re.compile(r"0x[0-9a-fA-F]{1,8}\Z")


def drafts_in_use(git, pin):
    raw = git.run("ls-tree", "-r", "--name-only", "-z", pin, "--", "include").stdout
    paths = raw.decode("utf-8", "surrogateescape").split("\0")
    drafts = {p for p in paths if p.startswith(DRAFT) and p.lower().endswith(HEADERS)}
    hits = git.run("grep", "--null", "-I", "--no-line-number", "-E",
                   r'^[[:blank:]]*#[[:blank:]]*include[[:blank:]]*[<"]',
                   pin, "--", "src", "include", check=False)
    if hits.returncode not in (0, 1):
        raise ValueError("The Draft include census did not complete.")
    used = set()
    for line in hits.stdout.splitlines():
        tag, separator, directive = line.partition(b"\0")
        if not separator:
            continue
        owner = tag.split(b":", 1)[1].decode("utf-8", "surrogateescape")
        match = INCLUDE.match(directive) if owner.lower().endswith(SOURCES) else None
        if match:
            target = match[1].decode("utf-8", "surrogateescape")
            for path in (target, "include/" + target, str(PurePosixPath(owner).parent / target)):
                if path in drafts:
                    used.add(path)
                    break
    return len(used)


def states(results, owner):
    """Use the exact base-map owner to deduplicate address-keyed object rows."""
    matched, proven = set(), set()
    for path, item in results.items():
        proven_rows = item.get("proven", ())
        for rva, row in item.get("rows", {}).items():
            if not ADDRESS.fullmatch(rva) or not row or row[0] != "MATCH":
                continue
            address = int(rva, 16)
            if owner(address) != path:
                continue
            matched.add(address)
            if rva in proven_rows:
                proven.add(address)
    return matched, proven


def progress(before, after, owner, finished, drafts_before, drafts_after):
    old_match, old_proof = states(before, owner)
    new_match, new_proof = states(after, owner)
    old_finished = {rva for rva in old_proof if finished(rva, False)}
    new_finished = {rva for rva in new_proof if finished(rva, True)}
    return {"matched": len(new_match - old_match), "proven": len(new_proof - old_proof),
            "finished": len(new_finished - old_finished),
            "lost": len((old_match - new_match) | (old_proof - new_proof)),
            "drafts_before": drafts_before, "drafts_after": drafts_after}


def checked_progress(raw):
    if not isinstance(raw, dict) or set(raw) != set(METRICS):
        return {k: None for k in METRICS}
    return {k: value if type(value) is int and 0 <= value <= 10**8 else None for k, value in raw.items()}


def public_table(raw):
    result = checked_progress(raw)
    shown = {k: str(v) if v is not None else "—" for k, v in result.items()}
    return [
        "| Progress | Result |",
        "| --- | ---: |",
        f"| Became MATCH | {shown['matched']} |",
        f"| Became proven | {shown['proven']} |",
        f"| Became FINISHED | {shown['finished']} |",
        f"| Lost credit or proof | {shown['lost']} |",
        f"| Drafts in use | {shown['drafts_before']} → {shown['drafts_after']} |",
    ]

