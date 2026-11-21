"""Compiler-only worker. The operator supplies the launcher and immutable tool profile."""
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

from pool_protocol import (DIGEST, MAX_DIAGNOSTICS, MAX_FILE, MAX_FILES, MAX_OBJECT, MAX_SOURCE,
                           ProtocolError, VERSION, check_object, decode, digest, encode, relative,
                           safe_diagnostics, source_path, unpack_sources)

MAX_REQUEST = 92 * 1024**2
MAX_PLAN = 8
MAX_HEADERS = 4096
MAX_LOG = 4 * 1024**2
ROLE = re.compile(r"[a-z][a-z0-9-]{0,39}\Z")
FLAG = re.compile(r"-(?:nologo|c|showIncludes|W[0-4]|O[12bdgistxy][0-9-]*|Ob[0-2]|Oy-?|"
                  r"G[3-7BRSdrsyFfhz]-?|GS-?|Gy-?|EH[sca-]+|arch:SSE2?|Zc:[A-Za-z]+-?|"
                  r"D[A-Za-z_][A-Za-z0-9_]*(?:=[A-Za-z0-9_]*)?|U[A-Za-z_]+|Zp[1248]?|"
                  r"J|vmg|vm[bsmv]|GX-?|GF|Gm-?|MD|MT|ML)\Z")
PATH_ENV = frozenset(("INCLUDE", "LIB", "WINEPATH"))
PLAIN_ENV = frozenset(("LANG", "LC_ALL", "WINEDLLOVERRIDES", "WINEDEBUG"))
PLAIN = re.compile(r"[A-Za-z0-9_.=,;@+-]{0,200}\Z")
INCLUDED = re.compile(r"^[ \t]*Note: including file:[ \t]*(.+)$", re.M)


def read_regular(path, limit):
    dir_fd = os.open(path.parent, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dir_fd)
    finally:
        os.close(dir_fd)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 0 < info.st_size <= limit:
            raise ProtocolError("Invalid compiler output file.")
        data = stream.read(limit + 1)
        if len(data) != info.st_size:
            raise ProtocolError("Compiler output changed while being read.")
        return data


def json_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def wine_path(path):
    return "Z:" + str(path).replace("/", "\\")


def include_path(path, roots):
    """Recover the canonical spelling of an MSVC include on a case-sensitive filesystem."""
    try:
        return path.resolve(strict=True)
    except FileNotFoundError:
        parts = Path(os.path.normpath(path)).parts
        folded = tuple(piece.casefold() for piece in parts)
        for root in roots:
            prefix = tuple(piece.casefold() for piece in root.parts)
            if folded[:len(prefix)] != prefix:
                continue
            current = root
            for part in parts[len(prefix):]:
                exact = current / part
                if exact.exists() and not exact.is_symlink():
                    current = exact
                    continue
                matches = [item for item in current.iterdir() if item.name.casefold() == part.casefold()]
                if len(matches) != 1 or matches[0].is_symlink():
                    raise ProtocolError("A staged include has no unique canonical spelling.")
                current = matches[0]
            return current.resolve(strict=True)
        raise ProtocolError("An include resolved outside the clean compiler inputs.")


class Layout:
    def __init__(self, roots, job, guest_job="/ci/job"):
        self.roots = roots
        self.job = job
        self.guest_job = Path(guest_job)
        if self.guest_job != Path("/ci/job"):
            raise ProtocolError("The clean runtime uses a fixed guest job path.")

    def tool_path(self, token):
        role, separator, rest = token.partition("/")
        if role not in self.roots or (separator and not relative(rest)):
            raise ProtocolError("Unknown installed compiler path.")
        return wine_path(self.roots[role] / rest)

    def flag(self, flag):
        if isinstance(flag, str) and FLAG.fullmatch(flag):
            return flag
        if isinstance(flag, str) and flag.startswith("-I"):
            token = flag[2:]
            if token in {"include", "src"} or source_path(token + "/probe.h"):
                return flag
            if token.startswith("@"):
                return "-I" + self.tool_path(token[1:])
        raise ProtocolError("Unrecognized compiler option.")

    def environment(self, options):
        if not isinstance(options, dict) or set(options) - PATH_ENV - PLAIN_ENV:
            raise ProtocolError("Unrecognized compiler environment setting.")
        env = {}
        for key, value in options.items():
            if key in PATH_ENV:
                if not isinstance(value, list) or len(value) > 32 or any(not isinstance(x, str) for x in value):
                    raise ProtocolError("Invalid compiler environment path list.")
                env[key] = ";".join(self.tool_path(x) for x in value)
            elif not isinstance(value, str) or not PLAIN.fullmatch(value):
                raise ProtocolError("Invalid compiler environment value.")
            else:
                env[key] = value
        return env

    def record(self, raw, files, tu):
        raw = raw.strip().replace("\\", "/")
        if raw[:3].casefold() == "z:/":
            native = Path(raw[2:])
            if native.is_relative_to(self.guest_job):
                native = self.job / native.relative_to(self.guest_job)
        elif not Path(raw).is_absolute() and len(raw) <= 512 and ":" not in raw and "\0" not in raw:
            native = self.job / raw
        else:
            raise ProtocolError("Compiler referenced an unexpected dependency path.")
        native = include_path(native, (self.job, *self.roots.values()))
        if native.is_relative_to(self.job):
            path = native.relative_to(self.job).as_posix()
            if path == tu:
                return None
            if path in files:
                return "source", path, files[path]
        for role, root in self.roots.items():
            if native.is_relative_to(root):
                return role, native.relative_to(root).as_posix(), digest(read_regular(native, MAX_FILE))
        raise ProtocolError("An include resolved outside the clean compiler inputs.")


def stage(job, source):
    if not isinstance(source, dict) or not 0 < len(source) <= MAX_FILES:
        raise ProtocolError("Invalid source projection.")
    data_digests, names, total = {}, set(), 0
    for path, encoded in source.items():
        if not source_path(path) or path.casefold() in names:
            raise ProtocolError("Invalid or case-colliding input path.")
        names.add(path.casefold())
        data = decode(encoded, MAX_FILE)
        total += len(data)
        if total > MAX_SOURCE:
            raise ProtocolError("Source projection exceeds its size limit.")
        data_digests[path] = digest(data)
        target = job / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return data_digests


ERROR_DIRECTIVE_DIAGNOSTIC = re.compile(
    r"(?P<path>[^()]+)\((?P<line>[1-9][0-9]{0,7})\): fatal error C(?:1189|1004): MSVC compiler diagnostic\."
)
ERROR_DIRECTIVE = re.compile(rb"^[ \t]*#[ \t]*error(?:[ \t]|$)")


def directive_crash_diagnostics(tu, text, job, files):
    """Return only fatal diagnostics tied to a staged literal error directive."""
    found = []
    for line in safe_diagnostics(tu, text, files).splitlines():
        hit = ERROR_DIRECTIVE_DIAGNOSTIC.fullmatch(line)
        if not hit or hit["path"] not in files:
            continue
        source = read_regular(job / hit["path"], MAX_FILE)
        if digest(source) != files[hit["path"]]:
            raise ProtocolError("Source changed after compiler admission.")
        lines = re.split(rb"\r\n|\r|\n", source.removeprefix(b"\xef\xbb\xbf"))
        n = int(hit["line"])
        if n <= len(lines) and ERROR_DIRECTIVE.match(lines[n - 1]):
            found.append(line)
    return "\n".join(found)


def one(profile, layout, job, files, entry, index):
    tu, flags = entry["tu"], entry["flags"]
    if (tu not in files or not tu.startswith("src/") or Path(tu).suffix.lower() not in {".c", ".cpp"}
            or entry["source"] != files[tu] or not isinstance(flags, list) or len(flags) > 128
            or "-c" not in flags or "-showIncludes" not in flags
            or not DIGEST.fullmatch(entry["contract"])):
        raise ProtocolError("Invalid compiler plan.")
    mapped = list(map(layout.flag, flags))
    env = layout.environment(entry["env"])
    # The launcher receives a private job directory. It supplies the sealed tool root,
    # private writable output and no-network process tree from the operator image.
    out = job / "out" / f"{index}.obj"
    # Allow the trusted Wine bootstrap to unpack its larger system DLLs.
    # The sealed launcher drops the limit to MAX_OBJECT before compiling.
    command = ["/usr/bin/prlimit", "--fsize=67108864:67108864", "--core=0:0",
               "--cpu=420:430", "--nofile=1024:1024", "--", str(profile["launcher"]), "compile",
               str(job), str(profile["wine"]),
               str(profile["compiler"]), *mapped, "-Foout/" + out.name, tu.replace("/", "\\")]
    log_path = job / f"{index}.log"
    with log_path.open("w+b") as log:
        try:
            result = subprocess.run(command, cwd=job, env=dict(env, PATH="/usr/bin:/bin"),
                                    stdin=subprocess.DEVNULL, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=profile["timeout_s"], check=False)
        except subprocess.TimeoutExpired as error:
            raise ProtocolError("Compiler did not finish inside its deadline.") from error
        log.seek(0)
        raw = log.read(MAX_LOG + 1)
    if len(raw) > MAX_LOG:
        raise ProtocolError("Compiler launcher log exceeds its limit.")
    text = raw.decode("utf-8", "replace")
    response = {"tu": tu, "contract": entry["contract"], "source": files[tu]}
    if result.returncode == 139 and not os.path.lexists(out):
        diagnostics = directive_crash_diagnostics(tu, text, job, files)
        if diagnostics:
            return dict(response, status="error", diagnostics=diagnostics)
    if not 0 <= result.returncode <= 2:
        raise ProtocolError("Compiler launcher did not return a normal result.")
    if result.returncode:
        diagnostics = safe_diagnostics(tu, text, files)
        if not diagnostics:
            raise ProtocolError("Compiler reported a failure without a source diagnostic.")
        return dict(response, status="error", diagnostics=diagnostics)
    includes = set()
    for raw_include in INCLUDED.findall(text):
        entry = layout.record(raw_include, files, tu)
        if entry is not None:
            includes.add(entry)
        if len(includes) > MAX_HEADERS:
            raise ProtocolError("Too many compiler dependencies.")
    payload = read_regular(out, MAX_OBJECT)
    return dict(response, status="compiled", artifact=encode(payload), sha256=check_object(payload),
                includes=sorted(includes))


def compiler_identity(profile):
    compiler = Path(profile["compiler"])
    if not compiler.is_absolute() or not DIGEST.fullmatch(profile["compiler_sha256"]):
        raise ProtocolError("Incorrect installed compiler identity.")
    actual = digest(read_regular(compiler, MAX_OBJECT))
    if actual != profile["compiler_sha256"]:
        raise ProtocolError("Installed compiler differs from the sealed profile.")
    return actual


def run_worker(profile_path, request_bytes):
    profile_data = read_regular(profile_path, 65_536)
    profile = json.loads(profile_data)
    request = json.loads(request_bytes)
    pin = digest(profile_data)
    plan = request["plan"]
    if (request["version"] != VERSION or request["profile"] != pin
            or type(plan) is not list or not 0 < len(plan) <= MAX_PLAN
            or len({entry["tu"] for entry in plan}) != len(plan)):
        raise ProtocolError("Request does not match this dedicated compiler profile.")
    roots = {key: Path(path).resolve(strict=True) for key, path in profile["roots"].items()}
    if ("source" in roots or not roots or any(not ROLE.fullmatch(k) or not p.is_dir() for k, p in roots.items())):
        raise ProtocolError("Invalid installed compiler profile.")
    compiler_identity(profile)
    for key in ("launcher", "wine", "compiler", "scratch"):
        path = Path(profile[key])
        if not path.is_absolute() or not path.exists():
            raise ProtocolError("Missing installed compiler path.")
    with tempfile.TemporaryDirectory(prefix="compile-", dir=profile["scratch"]) as name:
        job = Path(name)
        for section in ("src", "include", "out"):
            (job / section).mkdir(mode=0o700)
        sources = stage(job, unpack_sources(request["source"]))
        layout = Layout(roots, job)
        results = [one(profile, layout, job, sources, entry, i) for i, entry in enumerate(plan)]
    return {"version": VERSION, "request": digest(request_bytes), "profile": pin, "results": results}


if __name__ == "__main__":
    os.umask(0o077)
    if len(sys.argv) != 2:
        raise SystemExit("Usage: pool_worker.py INSTALLED_PROFILE")
    raw = sys.stdin.buffer.read(MAX_REQUEST + 1)
    try:
        if not raw or len(raw) > MAX_REQUEST:
            raise ProtocolError("Compiler request exceeds its size limit.")
        response = run_worker(Path(sys.argv[1]), raw)
        sys.stdout.buffer.write(json_bytes(response) + b"\n")
    except (OSError, TypeError, ValueError, KeyError):
        # Worker failures never become contributor compiler diagnostics.
        raise SystemExit("Dedicated compiler job is unavailable.")
