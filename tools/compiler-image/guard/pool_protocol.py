"""Data validation shared by the dedicated compiler and the trusted receiver."""
import base64
import binascii
import hashlib
import json
import re
import struct
import zlib
from pathlib import PurePosixPath

MAX_OBJECT = 16 * 1024**2
MAX_DIAGNOSTICS = 2048
MAX_FILES = 20_000
MAX_SOURCE = 64 * 1024**2
MAX_FILE = 1024**2
MAX_SOURCE_ENVELOPE = 92 * 1024**2
VERSION = 1
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
PART = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_+.-]{0,95}\Z")
DEVICE = re.compile(r"(?:CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|COM\d|LPT\d)(?:\.|$)", re.I)
TOKEN = re.compile(r'''//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*' ''', re.X)
DIRECTIVE = re.compile(r"^\s*#\s*(\w+)(.*)$")
INCLUDE = re.compile(r'''\s*(?:"([^"]+)"|<([^>]+)>)\s*\Z''')
LOCAL_PRAGMA = re.compile(r"\s*(?:once|pack\s*\([A-Za-z0-9_, \t-]*\)|"
                          r"warning\s*\([A-Za-z0-9_,:; \t-]*\))\s*\Z")
DIAGNOSTIC = re.compile(r"^(?:[\\/]?)([A-Za-z0-9_ ./+\\-]+)\((\d{1,8})\)\s*:\s*"
                        r"((?:fatal )?error|warning)\s+(C\d{4})\s*:\s*(.+)$", re.I)


class ProtocolError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(data):
    return base64.b64encode(data).decode("ascii")


def decode(text, limit):
    if not isinstance(text, str) or len(text) > 4 * ((limit + 2) // 3):
        raise ProtocolError("Invalid encoded artifact size.")
    try:
        data = base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ProtocolError("Invalid encoded artifact.") from error
    if len(data) > limit:
        raise ProtocolError("Decoded artifact exceeds its size limit.")
    return data


def pack_sources(files):
    raw = json.dumps(files, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    if len(raw) > MAX_SOURCE_ENVELOPE:
        raise ProtocolError("Source projection envelope is too large.")
    return {"zlib": encode(zlib.compress(raw, 3)), "sha256": digest(raw)}


def unpack_sources(package):
    if not isinstance(package, dict) or set(package) != {"zlib", "sha256"}:
        raise ProtocolError("Invalid source projection envelope.")
    packed = decode(package["zlib"], MAX_SOURCE_ENVELOPE)
    decoder = zlib.decompressobj()
    try:
        raw = decoder.decompress(packed, MAX_SOURCE_ENVELOPE + 1)
    except zlib.error as error:
        raise ProtocolError("Invalid compressed source projection.") from error
    if (len(raw) > MAX_SOURCE_ENVELOPE or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail
            or digest(raw) != package["sha256"]):
        raise ProtocolError("Incomplete, trailing or mismatched source projection.")
    return json.loads(raw)


def relative(path):
    return (isinstance(path, str) and 0 < len(path) <= 220
            and all(PART.fullmatch(p) and not p.endswith(".") and not DEVICE.match(p)
                    for p in path.split("/")))


def source_path(path):
    return (relative(path) and path.split("/")[0] in {"src", "include"}
            and PurePosixPath(path).suffix.lower() in {".c", ".cpp", ".h", ".hpp", ".hh", ".inl", ".inc", ".tbl"})


def safe_diagnostics(tu, output, allowed=()):
    """Return short located compiler messages. Ignore source echoes and external path messages."""
    result = []
    paths = {p.casefold(): p for p in (*allowed, tu)}
    for raw in output[:MAX_DIAGNOSTICS * 16].splitlines():
        match = DIAGNOSTIC.fullmatch(raw.strip())
        if not match:
            continue
        name = match[1].replace("\\", "/").removeprefix("./")
        path = paths.get(name.casefold())
        if not path:
            continue
        line, level, code, message = match.groups()[1:]
        if any(ord(c) < 32 or ord(c) == 127 for c in message):
            continue
        # Render portable locations and generic diagnostics for input/lookup failures.
        result.append(f"{path}({line}): {level.lower()} {code.upper()}: MSVC compiler diagnostic.")
        if len(result) >= 8:
            break
    return "\n".join(result)[:MAX_DIAGNOSTICS]


def contributed_source_problem(data):
    """Admission screen for changed source; the launcher provides the security boundary."""
    text = data.decode("utf-8-sig")
    if any(ord(c) < 32 and c not in "\n\r\t" for c in text):
        return 1, "Unsupported source control character."
    # Normalize source continuation before recognizing preprocessor directives.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\\[ \t]*\n", "", text)
    if re.search(r"\?\?[=/'()!<>-]", text) or "%:" in text:
        return 1, "Alternate preprocessor spellings are unsupported."
    def remove_comment(match):
        value = match[0]
        return re.sub(r"[^\n]", " ", value) if value.startswith(("//", "/*")) else value
    text = TOKEN.sub(remove_comment, text)
    for number, line in enumerate(text.splitlines(), 1):
        match = DIRECTIVE.fullmatch(line)
        if match:
            name, arguments = match.groups()
            if name == "include":
                found = INCLUDE.fullmatch(arguments)
                if not found or not relative((found[1] or found[2]).replace("\\", "/")):
                    return number, "Use a literal include within the project or installed headers."
            elif name == "pragma":
                if not LOCAL_PRAGMA.fullmatch(arguments):
                    return number, "This pragma requires maintainer review."
            elif name not in {"if", "ifdef", "ifndef", "else", "elif", "endif", "define", "undef", "error"}:
                return number, "This preprocessor directive requires maintainer review."
        code = TOKEN.sub(" ", line)
        if re.search(r"\b(?:__pragma|_Pragma)\b", code):
            return number, "Inline pragmas require maintainer review."
    return None


def check_object(data):
    """Check the bounds of raw x86 COFF before offering it to the installed parser."""
    if not isinstance(data, bytes) or not 20 <= len(data) <= MAX_OBJECT:
        raise ProtocolError("Invalid object size.")
    machine, sections, _, symbols_at, symbols, optional, _ = struct.unpack_from("<HHLLLHH", data)
    section_end = 20 + sections * 40
    if machine != 0x14C or not 0 < sections <= 4096 or optional or section_end > len(data):
        raise ProtocolError("Only bounded 32-bit x86 COFF objects are accepted.")
    if not section_end <= symbols_at <= len(data) or not 0 < symbols <= 250_000:
        raise ProtocolError("Invalid COFF symbol table.")
    strings_at = symbols_at + symbols * 18
    if strings_at + 4 > len(data):
        raise ProtocolError("Incomplete COFF symbol table.")
    size, = struct.unpack_from("<L", data, strings_at)
    if size < 4 or size != len(data) - strings_at:
        raise ProtocolError("Invalid COFF string table.")
    extents = []
    for section in range(sections):
        fields = struct.unpack_from("<8sLLLLLLHHL", data, 20 + section * 40)
        _, _, _, raw_size, raw_at, rel_at, lines_at, rel_count, lines, flags = fields
        if raw_size > MAX_OBJECT:
            raise ProtocolError("COFF declared section size is too large.")
        extents.append(raw_size)
        if raw_size and (raw_at or not flags & 0x80) and not (
                section_end <= raw_at and raw_at + raw_size <= symbols_at):
            raise ProtocolError("Invalid COFF section payload.")
        if flags & 0x01000000:
            if rel_count != 0xFFFF or not section_end <= rel_at <= symbols_at - 10:
                raise ProtocolError("Invalid COFF relocation overflow record.")
            rel_count, = struct.unpack_from("<L", data, rel_at)
        if rel_count and not (section_end <= rel_at and rel_at + 10 * rel_count <= symbols_at):
            raise ProtocolError("Invalid COFF relocation table.")
        # The first entry of an overflow table is its bounded count, not a relocation.
        start = 1 if flags & 0x01000000 else 0
        for index in range(start, rel_count):
            offset, symbol, kind = struct.unpack_from("<LLH", data, rel_at + index * 10)
            if kind and (symbol >= symbols or offset >= raw_size):
                raise ProtocolError("Invalid COFF relocation target.")
        if lines and not (section_end <= lines_at and lines_at + 6 * lines <= symbols_at):
            raise ProtocolError("Invalid COFF line table.")
    if sum(extents) > 4 * MAX_OBJECT:
        raise ProtocolError("COFF declared section sizes exceed their aggregate limit.")
    index = 0
    while index < symbols:
        at = symbols_at + index * 18
        name, value, section, _, storage, aux = struct.unpack_from("<8sLhHBB", data, at)
        if index + aux >= symbols or not -2 <= section <= sections:
            raise ProtocolError("Invalid COFF symbol or auxiliary range.")
        if section > 0 and value > extents[section - 1]:
            raise ProtocolError("COFF symbol points outside its section.")
        if name[:4] == b"\0" * 4:
            name_at, = struct.unpack_from("<L", name, 4)
            start = strings_at + name_at
            if not 4 <= name_at < size or data.find(b"\0", start, start + 4097) < 0:
                raise ProtocolError("Invalid COFF long symbol name.")
        if storage == 105 and aux == 1:
            target, = struct.unpack_from("<L", data, at + 18)
            if target >= symbols:
                raise ProtocolError("Invalid COFF weak extern target.")
        index += aux + 1
    return digest(data)
