#!/bin/bash
set -euo pipefail
# Allow only ci-compile to traverse /root so the probe can confirm ENOENT on
# /root/.ssh without granting read access to /root or any of its children.
[[ $(id -u) == 0 && -d /opt/boat-compiler && ! -L /opt/boat-compiler ]]
[[ ! -e /root/.ssh && ! -L /root/.ssh && ! -e /run/docker.sock ]]
find /root -mindepth 1 -maxdepth 1 \( -type f -o -type d \) -exec chmod go-rwx -- '{}' +
[[ -z $(find /root -mindepth 1 -maxdepth 1 -type l -print -quit) ]]
setfacl -m 'u:ci-compile:--x' /root
setpriv --reuid=ci-compile --regid=ci-compile --clear-groups python3 -B - <<'PY'
import errno, os
try:
    os.lstat("/root/.ssh")
except OSError as exc:
    assert exc.errno == errno.ENOENT, exc
else:
    raise AssertionError("private SSH state still present")
assert not os.access("/root", os.R_OK)
PY
