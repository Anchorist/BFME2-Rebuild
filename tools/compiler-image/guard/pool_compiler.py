"""Activate the compiler filter before reducing its descriptor limit."""
import os
import sys

from pool_protocol import MAX_OBJECT

env = {"HOME": "/ci", "PATH": "/usr/bin:/bin", "WINEPREFIX": "/ci/wine",
       "WINEARCH": "win64", "WINEDEBUG": "-all", "WINEDLLOVERRIDES": "mscoree,mshtml="}
for key in ("LANG", "LC_ALL", "INCLUDE", "LIB", "WINEPATH", "WINEDLLOVERRIDES"):
    if key in os.environ:
        env[key] = os.environ[key]
python = "/usr/bin/python3"
limit = f"--fsize={MAX_OBJECT}:{MAX_OBJECT}"
os.execve(python, [python, "/ci/guard/pool_network.py", "/usr/bin/prlimit",
                   limit, "--nofile=128:128", "--", *sys.argv[1:]], env)
