"""Probe the same restricted runtime used by the compiler on an operator-provisioned worker."""
import errno
import json
import os
import socket
import stat
import subprocess
import sys
from pathlib import Path

from pool_protocol import ProtocolError, digest
from pool_worker import compiler_identity, read_regular

PRIVATE = ("/root/.ssh", "/run/secrets", "/run/credentials", "/var/run/docker.sock")
PROVIDER_CREDENTIALS = "/run/credentials"
SENSITIVE_ENV = ("GITHUB_TOKEN", "GH_TOKEN", "BOAT_KEY", "BOAT_TOKEN", "SSH_AUTH_SOCK",
                 "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN")
CHECKS = {"private_paths_absent", "credential_environment_absent", "no_new_privileges",
          "network_sockets_denied", "mount_inventory", "private_mounts_absent", "network_namespace_private",
          "unprivileged_compiler", "no_inherited_network_descriptors"}
NET_FAMILIES = tuple(getattr(socket, name) for name in ("AF_INET", "AF_INET6", "AF_PACKET",
                                                       "AF_NETLINK", "AF_VSOCK") if hasattr(socket, name))


def check_network():
    for family in NET_FAMILIES:
        try:
            test = socket.socket(family, socket.SOCK_STREAM if family in {socket.AF_INET, socket.AF_INET6}
                                 else socket.SOCK_DGRAM)
        except OSError as error:
            if error.errno in {errno.EPERM, errno.EACCES, errno.EAFNOSUPPORT, errno.EPROTONOSUPPORT}:
                continue
            return False
        else:
            test.close()
            return False
    return True


def absent(path):
    try:
        os.lstat(path)
    except FileNotFoundError:
        return True
    except OSError:
        return False
    else:
        return False


def empty_provider_directory(path):
    """Accept only the provider's root-owned empty directory, using one directory descriptor."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError:
        return False
    try:
        info = os.fstat(descriptor)
        if info.st_uid != 0 or info.st_gid != 0 or stat.S_IMODE(info.st_mode) != 0o755:
            return False
        if os.listdir(descriptor):
            return False
        current = os.stat(path, follow_symlinks=False)
        return (current.st_dev, current.st_ino) == (info.st_dev, info.st_ino)
    except OSError:
        return False
    finally:
        os.close(descriptor)


def outer_private_paths_absent():
    """The outer provider can recreate an empty credentials directory even without credentials."""
    return all(absent(path) or (path == PROVIDER_CREDENTIALS and empty_provider_directory(path))
               for path in PRIVATE)


def inspect(extra=()):
    mounts = []
    for line in Path("/proc/self/mountinfo").read_text().splitlines():
        fields = line.split(" - ", 1)[0].split()
        mounts.append({"path": fields[4].replace("\\040", " "), "root": fields[3].replace("\\040", " "),
                       "options": fields[5].split(",")})
    status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
    descriptors = []
    for fd in Path("/proc/self/fd").iterdir():
        try:
            descriptors.append(os.readlink(fd))
        except FileNotFoundError:
            continue
    return {"network_namespace": os.readlink("/proc/self/ns/net"),
            "unprivileged_compiler": os.geteuid() != 0 and int(status["CapEff"].strip(), 16) == 0,
            "no_inherited_network_descriptors": not any(x.startswith("socket:") for x in descriptors),
            "private_paths_absent": all(absent(p) for p in (*PRIVATE, *extra)),
            "credential_environment_absent": all(k not in os.environ for k in SENSITIVE_ENV),
            "no_new_privileges": status.get("NoNewPrivs", "").strip() == "1",
            "network_sockets_denied": check_network(),
            "private_mounts_absent": all(not any(row[k].startswith(p) for p in (*PRIVATE, *extra)
                                                   for k in ("path", "root")) for row in mounts),
            "mount_inventory": mounts}


def prove(profile_path):
    raw = read_regular(profile_path, 65_536)
    profile = json.loads(raw)
    inventory = Path(profile["inventory_receipt"])
    if (not inventory.is_absolute() or digest(read_regular(inventory, 65_536)) != profile["inventory_sha256"]):
        raise ProtocolError("Operator image inventory differs from the clean profile.")
    if not outer_private_paths_absent():
        raise ProtocolError("The dedicated worker still has a private project path.")
    launcher = profile["launcher"]
    completed = subprocess.run([launcher, "probe"], stdin=subprocess.DEVNULL, capture_output=True,
                               env={"PATH": "/usr/bin:/bin", "LANG": "C"}, timeout=20)
    if completed.returncode or len(completed.stdout) > 65_536:
        raise ProtocolError("Worker isolation probe did not complete.")
    result = json.loads(completed.stdout)
    namespace = result.pop("network_namespace", "")
    result["network_namespace_private"] = bool(namespace and namespace != os.readlink("/proc/self/ns/net"))
    if set(result) != CHECKS or any(result[key] is not True for key in CHECKS - {"mount_inventory"}):
        raise ProtocolError("Worker isolation probe failed.")
    mounts = result["mount_inventory"]
    expected = profile["probe_mounts"]
    if not isinstance(mounts, list) or not mounts or len(mounts) > 128:
        raise ProtocolError("Invalid worker mount inventory.")
    if sorted(row["path"] for row in mounts) != sorted(expected):
        raise ProtocolError("Worker mount inventory differs from the clean profile.")
    by_path = {row["path"]: row for row in mounts}
    if any("ro" not in by_path[path]["options"] for path in profile["read_only_mounts"]):
        raise ProtocolError("A sealed tool or source mount is writable.")
    # Scratch bind roots include per-job names. The caller authenticates the worker
    # and compares the stable inventory of guest mount paths and options.
    result["mount_inventory"] = [{"path": mount["path"], "options": mount["options"]}
                                 for mount in sorted(mounts, key=lambda item: item["path"])]
    return {"profile": digest(raw), "compiler_sha256": compiler_identity(profile), "checks": result,
            "image_inventory_verified": True,
            "outer_private_paths_absent": True}


if __name__ == "__main__":
    if sys.argv[1:] == ["inspect"]:
        print(json.dumps(inspect(), sort_keys=True))
    elif len(sys.argv) == 2:
        print(json.dumps(prove(Path(sys.argv[1])), sort_keys=True))
    else:
        raise SystemExit("Usage: pool_probe.py INSTALLED_PROFILE")
