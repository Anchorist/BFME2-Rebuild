"""Managed CI child-boundary audit. The supervisor remains outside the compiler namespace."""
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, '/opt/boat-compiler/guard')

from pool_probe import CHECKS, compiler_identity
from pool_protocol import ProtocolError, digest
from pool_worker import read_regular

PROFILE = Path("/opt/boat-compiler/worker.json")

def audit():
    raw = read_regular(PROFILE, 65_536)
    profile = json.loads(raw)
    inventory = Path(profile["inventory_receipt"])
    if (not inventory.is_absolute() or digest(read_regular(inventory, 65_536)) != profile["inventory_sha256"]):
        raise ProtocolError("Compiler inventory differs from the sealed profile.")
    reply = subprocess.run(
        [profile["launcher"], "probe"],
        stdin=subprocess.DEVNULL, capture_output=True,
        env={"PATH": "/usr/bin:/bin", "LANG": "C"}, close_fds=True, timeout=20,
    )
    if reply.returncode or len(reply.stdout) > 65_536:
        raise ProtocolError("Compiler isolation probe was unavailable.")
    result = json.loads(reply.stdout)
    namespace = result.pop("network_namespace", None)
    result["network_namespace_private"] = bool(namespace and namespace != os.readlink("/proc/self/ns/net"))
    if set(result) != CHECKS or any(result[key] is not True for key in CHECKS - {"mount_inventory"}):
        raise ProtocolError("Compiler isolation checks did not pass.")
    mounts = result["mount_inventory"]
    if not isinstance(mounts, list) or not 0 < len(mounts) <= 128:
        raise ProtocolError("Compiler mount inventory is malformed.")
    by_path = {row["path"]: row["options"] for row in mounts}
    if len(by_path) != len(mounts) or sorted(by_path) != sorted(profile["probe_mounts"]):
        raise ProtocolError("Compiler mount inventory differs from the approved profile.")
    if any("ro" not in by_path[path] for path in profile["read_only_mounts"]):
        raise ProtocolError("A sealed tool or staged source mount is writable.")
    result["mount_inventory"] = [{"path": path, "options": opts} for path, opts in sorted(by_path.items())]
    return {
        "profile": digest(raw), "compiler_sha256": compiler_identity(profile), "checks": result,
        "image_inventory_verified": True,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(audit(), sort_keys=True))
    except (OSError, TypeError, ValueError, KeyError, subprocess.SubprocessError):
        raise SystemExit("Managed compiler child audit failed.") from None
