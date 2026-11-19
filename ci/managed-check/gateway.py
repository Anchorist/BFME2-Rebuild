"""Client for a separately provisioned compile-only Boat gateway.

The legacy replay transport does not implement this protocol.
"""
import base64
import json
import os
import re
import socket
import stat
import struct
from pathlib import Path

from gitrepo import DECLARATION, Git, OID, safe_path
from pool_protocol import diagnostic_message
from progress_delta import checked_progress
from quality_format import RULES
from reporting import MSVC, ROW, STATES, SYMBOL, numeric, safe_listing

VERSION = 1
MAX_REPLY = 96 * 1024
RUN_SECONDS = {"small": 6400, "wide": 8400}
RESPONSE_MARGIN = 100
SAFE_STATES = STATES | {"MATCH / proven", "MATCH / unproven", "UNMEASURED"}
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
CODE = re.compile(r"C\d{4}\Z")
MESSAGES = {
    "unavailable": "The Boat checker is temporarily unavailable. The bot will retry.",
    "source_policy": "A compiler input policy rejected a changed file.",
    "compile": "A translation unit that compiled on main failed to compile with this patch.",
    "annotation": "FUNCTION annotations changed. Restore the ledger-owned annotations.",
    "assembly": "Inline assembly requires an approved allowlist entry.",
    "declaration": "A protected declaration was removed. Name it with Removed-Declaration in the tip commit message and explain why.",
    "duplicate": "A global class has duplicate definitions. Keep one definition and update its includers.",
    "attribution": "The source or attribution gate refused the patch. Check the project rules.",
    "deletion": "A translation unit was removed. Ask a maintainer about coordinating the ledger movement.",
    "new_tu": "A translation unit needs an approved ledger entry. Ask a maintainer to coordinate its addition.",
    "conflict": "Rebase the pull request on current main.",
    "other": "A landing gate refused the patch. Ask a maintainer for the gate category.",
}


class GatewayUnavailable(Exception):
    pass


def read_exact(stream, length):
    data = stream.read(length)
    if len(data) != length:
        raise GatewayUnavailable("Incomplete gateway response")
    return data


def projected_row(row, changed):
    if not safe_path(row.get("path")) or not ROW.fullmatch(row.get("rva", "")):
        raise GatewayUnavailable("Invalid row address or path")
    old, new = row.get("old"), row.get("new")
    if old not in SAFE_STATES or new not in SAFE_STATES:
        raise GatewayUnavailable("Invalid row verdict")
    pct = row.get("pct")
    match = new in {"MATCH / proven", "MATCH / unproven"}
    if match:
        pct = 100.0
    elif type(pct) not in {int, float} or not 0 <= pct <= 100 or new != "PARTIAL":
        pct = None
    name = row.get("name")
    if not isinstance(name, str) or not SYMBOL.fullmatch(name):
        name = None
    return {"path": row["path"], "rva": row["rva"], "name": name, "size": numeric(row.get("size"), 2**31),
            "old": old, "new": new, "pct": pct,
            "first": numeric(row.get("first"), 2**31) if new == "PARTIAL" and pct is not None else None,
            "compiled_size": numeric(row.get("compiled_size"), 2**31),
            "retail_size": numeric(row.get("retail_size"), 2**31),
            "compiled_listing": safe_listing(row.get("compiled_listing", [])) if row["path"] in changed else []}


def projection(reply, changed):
    kind = reply["kind"]
    if kind not in {"ok", "regression", "gate", "conflict", "nothing", "pending"}:
        raise GatewayUnavailable("Unknown verdict")
    result = {"kind": kind, "progress": checked_progress(reply.get("progress")),
              "rules": [c for c in reply.get("codes", [])[:18] if c in RULES]}
    if kind in {"ok", "regression"}:
        for label in ("gains", "judged", "lost_count", "verified_count"):
            result[label] = numeric(reply.get(label), 10**8)
            if result[label] is None:
                raise GatewayUnavailable("Missing verdict count")
        for group in ("lost", "gained", "near"):
            result[group] = [projected_row(x, changed) for x in reply.get(group, [])[:20]]
        result["objects"] = [path for path in reply.get("objects", [])[:20] if safe_path(path)]
        result["diagnostics"] = []
        for row in reply.get("diagnostics", [])[:20]:
            path, value = row.get("path"), row.get("code", "")
            line = numeric(row.get("line"), 10**7)
            message = diagnostic_message(row.get("message"))
            if path in changed and line and CODE.fullmatch(value) and message:
                result["diagnostics"].append(f"{path}({line}): error {value}: {message}")
        result["edited"] = []
        for row in reply.get("edited", [])[:40]:
            path = row.get("path")
            function, owner = row.get("function"), row.get("owner")
            line = numeric(row.get("line"), 10**7)
            if path not in changed or not line or not safe_path(owner) or not isinstance(function, str) or not SYMBOL.fullmatch(function):
                continue
            identifier = row.get("rva")
            if identifier is None:
                entry = {"path": path, "rva": None, "old": row.get("old"), "new": row.get("new")}
                if entry["old"] not in SAFE_STATES or entry["new"] not in SAFE_STATES:
                    continue
            else:
                entry = projected_row(row, changed)
            reason = {"UNKNOWN_RVA": "No unique owned ledger row was found for this definition.",
                      "UNMEASURED": "The checker has no comparison for this function on this head.",
                      "MISSING": "The compiler output lacks a usable body for this row.",
                      "COMPILE_ERROR": "The source file did not compile.",
                      "PARTIAL": "The emitted body differs from the reference."}
            entry.update(function=function, owner=owner, line=line, explanation=reason.get(entry["new"], ""))
            result["edited"].append(entry)
    result["messages"] = []
    if kind == "gate":
        allowed = {"Unsupported source control character.", "Alternate preprocessor spellings are unsupported.",
                   "Use a literal include within the project or installed headers.",
                   "This pragma requires maintainer review.", "This preprocessor directive requires maintainer review.",
                   "Inline pragmas require maintainer review.", "Resource includes are maintainer-only."}
        for note in reply.get("source_policy", [])[:8]:
            path, line, policy = note.get("path"), numeric(note.get("line"), 10**7), note.get("policy")
            if path in changed and line and policy in allowed:
                result["messages"].append(f"{path}({line}): {policy}")
    if kind == "pending":
        result["messages"] = [MESSAGES["unavailable"]]
    return result


def check(task, config):
    endpoint = Path(config["socket"])
    digest = config["isolation_manifest_sha256"]
    if not endpoint.is_absolute() or not SHA256.fullmatch(digest):
        raise GatewayUnavailable("Invalid gateway configuration")
    owner = int(config.get("uid", os.getuid()))
    try:
        dir_stat, file_stat = endpoint.parent.lstat(), endpoint.lstat()
        if (not stat.S_ISDIR(dir_stat.st_mode) or not stat.S_ISSOCK(file_stat.st_mode)
                or dir_stat.st_uid != owner or file_stat.st_uid != owner
                or stat.S_IMODE(dir_stat.st_mode) != 0o700 or stat.S_IMODE(file_stat.st_mode) != 0o600):
            raise GatewayUnavailable("The gateway socket or directory has unsafe permissions")

        candidate = task["candidate"]
        git = Git(task["receiver"])
        changes = git.changes(candidate["base"], candidate["commit"])
        if git.value("rev-parse", candidate["commit"] + "^{tree}") != candidate["tree"]:
            raise GatewayUnavailable("Candidate tree moved")
        content = []
        for item in changes:
            data = git.run("cat-file", "blob", item.oid).stdout if item.mode != "000000" else None
            content.append({"path": item.path, "oid": item.oid,
                            "content": base64.b64encode(data).decode("ascii") if data is not None else None})
        binding = {key: candidate[key] for key in ("head", "base", "tree")}
        binding.update(request=task["key"], action=task["action"], checker=task["checker"],
                       isolation=digest, version=VERSION)
        message = git.run("show", "-s", "--no-show-signature", "--format=%B", candidate["commit"], "--").stdout
        declarations = DECLARATION.findall(message.decode("ascii"))
        raw = json.dumps({"binding": binding, "lane": task["lane"], "pull": task["number"],
                          "reach": task["reach"], "source": content, "declarations": declarations}).encode()
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)
            sock.connect(str(endpoint))
            _, peer_uid, _ = struct.unpack("3i", sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
            if peer_uid != owner:
                raise GatewayUnavailable("Unexpected gateway peer")
            sock.settimeout(RUN_SECONDS[task["lane"]] + RESPONSE_MARGIN)
            sock.sendall(struct.pack(">I", len(raw)) + raw)
            with sock.makefile("rb") as stream:
                length, = struct.unpack(">I", read_exact(stream, 4))
                if length > MAX_REPLY:
                    raise GatewayUnavailable("Oversized gateway response")
                reply = json.loads(read_exact(stream, length))
        if reply["binding"] != binding:
            raise GatewayUnavailable("Gateway receipt does not match the requested revision")
        if task["action"] == "land" and reply["kind"] == "ok":
            if reply.get("landed_tree") != candidate["tree"] or not OID.fullmatch(reply.get("scratch_landing", "")):
                raise GatewayUnavailable("No matching land.py scratch result")
            # The same authorized source tree is rooted at the public commit, so no private history is published.
            key = reply.get("state_receipt", "")
            if not SHA256.fullmatch(key):
                raise GatewayUnavailable("No matching private landing state receipt")
            return {"kind": "ok", "commit": candidate["commit"], "writer_receipt": key}
        return projection(reply, {x.path for x in changes})
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise GatewayUnavailable("Gateway unavailable or returned a malformed receipt") from error
