#!/bin/bash
set -euo pipefail
# Verify the installed /usr/local/libexec/bfme2-compiler entry and sealed
# /opt/boat-compiler runtime with the isolation probe and one-file compile
# controls (good compile with case-mismatched header + C2065 + C1189 errors).
#
# Usage:
#   sudo bash control.sh [--install]

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR=/usr/local/libexec/bfme2-compiler
TARGET="$TARGET_DIR/run"

INSTALL=0
if [[ ${1:-} == --install ]]; then
    INSTALL=1
elif [[ $# -gt 0 ]]; then
    echo "Usage: $0 [--install]" >&2
    exit 2
fi

[[ $(id -u) == 0 ]]
cd /opt/boat-compiler

if [[ $INSTALL -eq 1 ]]; then
    install -d -m 755 "$TARGET_DIR"
    install -m 444 "$SCRIPT_DIR/managed_probe.py" "$TARGET_DIR/managed_probe.py"
    install -m 555 "$SCRIPT_DIR/run" "$TARGET"
fi

test -x "$TARGET"
test -f "$TARGET_DIR/managed_probe.py"
sha256sum -c --quiet input.sha256 runtime-files.sha256
systemd-tmpfiles --create /etc/tmpfiles.d/boat-compiler.conf

work=$(mktemp -d /tmp/bfme2-compiler-control.XXXXXX)
trap 'rm -f -- "$work"/{probe,request,reply}.json; rmdir -- "$work"' EXIT

GITHUB_TOKEN=synthetic-supervisor-sentinel ACTIONS_RUNTIME_TOKEN=synthetic-runtime-sentinel \
    "$TARGET" probe > "$work/probe.json"

jq -e '.image_inventory_verified and .checks.credential_environment_absent and .checks.private_paths_absent and .checks.private_mounts_absent and .checks.network_sockets_denied and .checks.network_namespace_private and .checks.unprivileged_compiler and .checks.no_inherited_network_descriptors and .checks.no_new_privileges' \
    "$work/probe.json" >/dev/null

PYTHONPATH=/opt/boat-compiler/guard python3 -B - "$work" <<'PY'
import json
import sys
from pathlib import Path
from pool_protocol import digest, encode, pack_sources
from pool_worker import json_bytes

work = Path(sys.argv[1])
profile = digest(Path("/opt/boat-compiler/worker.json").read_bytes())
sources = {
    "include/control_header.h": b"#define CONTROL_VALUE 17\n",
    "src/control_ok.cpp": b'#include "control_headEr.h"\nextern "C" int control_value() { return CONTROL_VALUE; }\n',
    "src/control_bad_id.cpp": b"int control_bad() { return undeclared_control_symbol; }\n",
    "src/control_bad_directive.cpp": b"#error isolated synthetic diagnostic\n",
}
flags = ["-nologo", "-c", "-showIncludes", "-Iinclude"]
env = {"WINEPATH": ["vc/Vc7/bin", "vc/Common7/IDE", "vcruntime"]}
plan = [
    {
        "tu": tu,
        "source": digest(sources[tu]),
        "flags": flags,
        "env": env,
        "contract": digest(json_bytes([flags, env, tu])),
    }
    for tu in ("src/control_ok.cpp", "src/control_bad_id.cpp", "src/control_bad_directive.cpp")
]
req = {
    "version": 1,
    "profile": profile,
    "source": pack_sources({k: encode(v) for k, v in sources.items()}),
    "plan": plan,
}
(work / "request.json").write_bytes(json_bytes(req))
PY

GITHUB_TOKEN=synthetic-supervisor-sentinel ACTIONS_RUNTIME_TOKEN=synthetic-runtime-sentinel \
    "$TARGET" compile < "$work/request.json" > "$work/reply.json"

PYTHONPATH=/opt/boat-compiler/guard python3 -B - "$work" <<'PY'
import hashlib
import json
import sys
from pathlib import Path
from pool_protocol import MAX_OBJECT, check_object, decode, digest

work = Path(sys.argv[1])
raw = (work / "reply.json").read_bytes()
assert b"synthetic-supervisor-sentinel" not in raw
assert b"synthetic-runtime-sentinel" not in raw
doc = json.loads(raw)
req_bytes = (work / "request.json").read_bytes()
assert doc["request"] == digest(req_bytes)

good, bad_id, bad_dir = doc["results"]
assert good["status"] == "compiled"
obj = decode(good["artifact"], MAX_OBJECT)
assert check_object(obj) == good["sha256"]
normalized_sha = hashlib.sha256(obj[:4] + b"\x00\x00\x00\x00" + obj[8:]).hexdigest()
expected_hdr = ["source", "include/control_header.h", digest(b"#define CONTROL_VALUE 17\n")]
assert good["includes"] == [expected_hdr], good["includes"]
assert bad_id["status"] == "error" and "C2065" in bad_id["diagnostics"]
assert "undeclared_control_symbol" not in bad_id["diagnostics"]
assert bad_dir["status"] == "error" and "C1189" in bad_dir["diagnostics"]
assert "isolated synthetic diagnostic" not in bad_dir["diagnostics"]

audit = json.loads((work / "probe.json").read_bytes())
summary = {
    "compiler": audit["compiler_sha256"],
    "image": digest(Path("/opt/boat-compiler/image-inventory.json").read_bytes()),
    "profile": audit["profile"],
    "control_object_sha256": good["sha256"],
    "control_normalized_object_sha256": normalized_sha,
    "control_object_bytes": len(obj),
    "source_include": good["includes"][0],
    "c2065_diagnostic": bad_id["diagnostics"],
    "c1189_diagnostic": bad_dir["diagnostics"],
    "local_child_audit": audit["checks"],
}
print(json.dumps(summary, indent=2, sort_keys=True))
PY
