#!/usr/bin/env python3
"""Launcher template for a clean, operator-provisioned compiler-only Boat image."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Fixed installation paths inside the independently prepared VM. The operator
# provisions them from the approved runtime and tool manifests.
ROOTFS = Path("/opt/boat-compiler/rootfs")
TOOLS = Path("/opt/boat-compiler/tools")
MODULES = Path("/opt/boat-compiler/guard")
SCRATCH = Path("/var/lib/boat-compiler/stage")
JOBS = Path("/var/lib/boat-compiler/jobs")
BWRAP = "/usr/bin/bwrap"
PYTHON = "/usr/bin/python3"
COMPILER = "/opt/boat-compiler/tools/vc/Vc7/bin/cl.exe"
WINE = "/usr/bin/wine"
GUEST_JOB = "/ci/job"
GUARD = "/ci/guard"
ENV_KEYS = {"LANG", "LC_ALL", "INCLUDE", "LIB", "WINEPATH", "WINEDLLOVERRIDES"}


def launch(task, job, argv, prefix):
    # All bindings other than the ephemeral output and Wine prefix are read-only.
    base = [BWRAP, "--unshare-all", "--die-with-parent", "--cap-drop", "ALL",
            "--clearenv", "--ro-bind", str(ROOTFS), "/", "--proc", "/proc", "--dev", "/dev",
            "--tmpfs", "/tmp", "--dir", "/ci", "--dir", GUEST_JOB,
            "--ro-bind", str(TOOLS), str(TOOLS), "--ro-bind", str(MODULES), GUARD,
            "--bind", str(prefix), "/ci/wine", "--bind", str(job / "out"), GUEST_JOB + "/out"]
    for section in ("src", "include"):
        base += ["--ro-bind", str(job / section), GUEST_JOB + "/" + section]
    env = {k: os.environ[k] for k in ENV_KEYS if k in os.environ}
    env.update(HOME="/ci", PATH="/usr/bin:/bin", WINEPREFIX="/ci/wine",
               WINEDEBUG="-all", TMPDIR="/tmp", WINEARCH="win64", XDG_CACHE_HOME="/tmp", PYTHONDONTWRITEBYTECODE="1")
    for key, value in env.items():
        base += ["--setenv", key, value]
    if task == "probe":
        command = [*base, "--chdir", GUEST_JOB, "--", PYTHON, GUARD + "/pool_network.py",
                   PYTHON, GUARD + "/pool_probe.py", "inspect"]
    else:
        command = [*base, "--", "/bin/sh", GUARD + "/pool_bootstrap.sh", *argv]
    return subprocess.run(command, stdin=subprocess.DEVNULL, env={"PATH": "/usr/bin:/bin", "LANG": "C"}).returncode


def main():
    os.umask(0o077)
    task = sys.argv[1] if len(sys.argv) > 1 else ""
    if task not in {"probe", "compile"}:
        raise SystemExit("Unknown compiler launcher operation.")
    for path in (ROOTFS, TOOLS, MODULES):
        if not path.is_dir() or path.is_symlink() or path.stat().st_uid != 0 or path.stat().st_mode & 0o022:
            raise SystemExit("The clean compiler image is not installed or is writable.")
    with tempfile.TemporaryDirectory(prefix="launcher-", dir=SCRATCH) as work:
        place = Path(work)
        prefix = place / "wine"
        prefix.mkdir(mode=0o700)
        argv = sys.argv[3:]
        if task == "probe":
            if len(sys.argv) != 2:
                raise SystemExit("Unexpected probe arguments.")
            job = place / "probe"
            job.mkdir()
            for sub in ("src", "include", "out"):
                (job / sub).mkdir()
        else:
            job = Path(sys.argv[2]).resolve(strict=True)
            if (job.parent != JOBS or argv[:2] != [WINE, COMPILER] or "-c" not in argv
                    or any(not (job / sub).is_dir() or (job / sub).is_symlink() for sub in ("src", "include", "out"))):
                raise SystemExit("The request is outside the installed compiler contract.")
        return launch(task, job, argv, prefix)


if __name__ == "__main__":
    sys.exit(main())
