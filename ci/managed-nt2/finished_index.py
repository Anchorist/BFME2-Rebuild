"""Find strictly evidenced FINISHED rows in the exact source and owner trees."""
import functools
import io
import json
from pathlib import PurePosixPath
import posixpath
import re
import tarfile

from gitrepo import safe_path
from progress_delta import ADDRESS, DRAFT, HEADERS, INCLUDE

NAMED = re.compile(r"(?:[OG][0-9A-Fa-f]{8}|rva[0-9a-fA-F]{6,8}|FUN_[0-9a-fA-F]+)\Z", re.I)
MEMBER = re.compile(r"^(?:\?[^?@]+@|\?\?[01])([A-Za-z_]\w*)@@[A-X]")
GLOBAL = re.compile(r"^\?[^?@]+@@Y|^[A-Za-z_]\w*(?:@\d+)?$")
MAX_SOURCE_ARCHIVE = 128 * 1024**2
MAX_MAP = 128 * 1024**2
REAL_HEADERS = HEADERS + (".hh",)


def is_named_tu(path):
    return (safe_path(path) and path.startswith("src/") and not path.startswith("src/unk/")
            and not NAMED.fullmatch(PurePosixPath(path).stem))


class Owners:
    def __init__(self, git, base):
        ref = base + ":config/map.json"
        if int(git.value("cat-file", "-s", ref)) > MAX_MAP:
            raise ValueError("The trusted owner map exceeds its size limit.")
        document = json.loads(git.run("cat-file", "blob", ref).stdout)
        index = {}
        for obj in document["objects"]:
            identity = obj["object_id"]
            if identity in index:
                raise ValueError("The trusted owner map repeats an object identity.")
            index[identity] = obj.get("tu")
        self.functions = {}
        self.metadata = {}
        for row in document["rows"]:
            address = row.get("rva")
            if not isinstance(address, str) or not ADDRESS.fullmatch(address):
                continue
            rva = int(address, 16)
            self.metadata[rva] = {"name": row.get("name"), "size": row.get("size")}
            if row.get("role") != "owned":
                continue
            if rva in self.functions:
                raise ValueError("The trusted owner map repeats an owned function address.")
            source = index.get(row.get("object"))
            self.functions[rva] = (source, row.get("name") or "", row.get("size"))

    def path(self, rva):
        return self.functions.get(rva, (None, "", None))[0]

    def __call__(self, address):
        return self.metadata.get(int(address, 16), {})


class RealHeaders:
    def __init__(self, git, tree, definitions):
        raw = git.run("archive", "--format=tar", tree, "--", "src", "include").stdout
        if len(raw) > MAX_SOURCE_ARCHIVE:
            raise ValueError("The exact source tree exceeds the progress census limit.")
        self.includes = {}
        self.classes = {}
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
            for entry in archive:
                name = entry.name
                if not entry.isfile() or not safe_path(name):
                    continue
                with archive.extractfile(entry) as stream:
                    content = stream.read()
                self.includes[name] = tuple(m[1].decode("utf-8", "surrogateescape")
                                            for line in content.splitlines() if (m := INCLUDE.match(line)))
                if name.startswith("include/") and not name.startswith(DRAFT) and name.lower().endswith(REAL_HEADERS):
                    self.classes[name] = definitions(content.decode("utf-8", "replace"))

    def resolve(self, origin, label):
        token = label.replace("\\", "/")
        for path in (token, "include/" + token, posixpath.join(posixpath.dirname(origin), token)):
            candidate = posixpath.normpath(path)
            if candidate in self.includes and candidate.startswith("include/"):
                return candidate
        return None

    @functools.lru_cache(maxsize=4096)
    def closure(self, owner):
        stack = [owner]
        seen = set()
        while stack:
            path = stack.pop()
            for label in self.includes.get(path, ()):
                child = self.resolve(path, label)
                if child and child not in seen:
                    seen.add(child)
                    stack.append(child)
        return seen

    def ready(self, owner, name):
        if not is_named_tu(owner) or owner not in self.includes:
            return False
        if GLOBAL.match(name):
            return True
        member = MEMBER.match(name)
        return bool(member) and sum(member[1] in self.classes.get(header, ())
                                    for header in self.closure(owner)) == 1

