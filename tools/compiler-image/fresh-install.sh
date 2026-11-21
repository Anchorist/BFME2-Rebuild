#!/bin/bash
set -euo pipefail
# Build /opt/boat-compiler on a fresh Ubuntu 24.04 (noble) x86_64 host from
# user-supplied compiler, SDK, and STLport inputs.
#
# Usage:
#   sudo bash fresh-install.sh --inputs /path/to/inputs [--allow-other-compiler]
#
# The --inputs directory must contain:
#   vc/          (Vc7/bin, Vc7/include, Vc7/lib, Vc7/PlatformSDK/Include, Common7/IDE)
#   vcruntime/   (msvcp71.dll, msvcr71.dll)
#   dx/Include/  (August 2005 DirectX SDK headers)
#   stlport/     (STLport 4.5.3)
#   stlport-4.6/ (pristine STLport 4.6)
#   overlay/     (base, bfmealloc, bfmealloc_alloconly, bfmehashtable, bfmelist)
#   allocator/   (stl/_alloc.h)

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT=/opt/boat-compiler
ROOTFS="$ROOT/rootfs"
USER_NAME=ci-compile
WINE_VERSION='9.0~repack-4build3'
EXPECTED_CL_SHA='2ecf86a3edfd3deae498e08298e210e984537ce9e11759930561e43f40bd2515'

INPUTS=""
ALLOW_OTHER_COMPILER=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --inputs)
            INPUTS="${2:-}"
            shift 2
            ;;
        --allow-other-compiler)
            ALLOW_OTHER_COMPILER=1
            shift
            ;;
        *)
            echo "Usage: $0 --inputs DIR [--allow-other-compiler]" >&2
            exit 2
            ;;
    esac
done

[[ $(id -u) == 0 && $(uname -m) == x86_64 ]]
[[ -n $INPUTS && -d $INPUTS ]]
[[ ! -e $ROOT && ! -L $ROOT ]]
[[ ! -e /var/lib/boat-compiler && ! -L /var/lib/boat-compiler ]]
[[ $(findmnt -n -T /var/lib -o FSTYPE) == ext4 ]]

for sub in vc/Vc7/bin/cl.exe vc/Vc7/include vc/Vc7/lib vc/Vc7/PlatformSDK/Include vc/Common7/IDE \
           vcruntime/msvcp71.dll vcruntime/msvcr71.dll dx/Include stlport stlport-4.6/stlport \
           overlay/base allocator/stl/_alloc.h; do
    if [[ ! -e "$INPUTS/$sub" ]]; then
        echo "Missing required input path: $INPUTS/$sub" >&2
        exit 1
    fi
done

actual_cl_sha=$(sha256sum "$INPUTS/vc/Vc7/bin/cl.exe" | cut -d' ' -f1)
if [[ $ALLOW_OTHER_COMPILER -eq 0 && $actual_cl_sha != "$EXPECTED_CL_SHA" ]]; then
    echo "cl.exe SHA-256 mismatch: got $actual_cl_sha, expected $EXPECTED_CL_SHA" >&2
    echo "Pass --allow-other-compiler to override for an experimental build." >&2
    exit 1
fi

umask 022
export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=l
apt-get update -q --allow-releaseinfo-change || apt-get update -q --allow-releaseinfo-change -o Dir::Etc::sourceparts=-
apt-get install -y --no-install-recommends \
    acl bubblewrap debootstrap gcc gcc-multilib jq python3 ubuntu-keyring util-linux zstd

for tool in /usr/bin/bwrap /usr/bin/python3 /usr/bin/setpriv /usr/sbin/debootstrap; do
    test -x "$tool"
done

# Detach any default Docker daemon so the compiler boundary has no /run/docker.sock.
if [[ -e /run/docker.sock || -L /run/docker.sock ]]; then
    [[ -S /run/docker.sock && ! -L /run/docker.sock ]]
    systemctl stop docker.socket docker.service containerd.service 2>/dev/null || true
    systemctl mask --runtime docker.socket docker.service containerd.service 2>/dev/null || true
    if systemctl is-active --quiet docker.socket || systemctl is-active --quiet docker.service; then
        echo "Docker daemon is still active." >&2
        exit 7
    fi
    if [[ -S /run/docker.sock ]]; then
        rm -- /run/docker.sock
    fi
    [[ ! -e /run/docker.sock && ! -L /run/docker.sock ]]
fi

for path in /var/run/docker.sock /run/secrets; do
    [[ ! -e $path && ! -L $path ]]
done

if ! id "$USER_NAME" >/dev/null 2>&1; then
    useradd --create-home --shell /bin/sh "$USER_NAME"
fi
usermod --password '*' "$USER_NAME"
[[ $(id -Gn "$USER_NAME") == "$USER_NAME" ]]

# Verify the host AppArmor/kernel configuration permits unprivileged bwrap namespaces.
runuser -u "$USER_NAME" -- bwrap --unshare-all --ro-bind / / --dev /dev --proc /proc /bin/true

if [[ -d /root/.ssh && ! -L /root/.ssh ]]; then
    if [[ -n $(find /root/.ssh -mindepth 1 -maxdepth 1 ! -name authorized_keys -print -quit) ]]; then
        echo "Unexpected files under /root/.ssh; remove or inspect them first." >&2
        exit 3
    fi
    rm -f -- /root/.ssh/authorized_keys
    rmdir -- /root/.ssh
fi
if [[ -d /run/credentials && -z $(find /run/credentials -mindepth 1 -print -quit) ]]; then
    rmdir -- /run/credentials || true
fi

install -d -m 755 "$ROOT" "$ROOT/tools" "$ROOT/guard"

# Copy user-supplied compiler, SDK, and STLport trees into /opt/boat-compiler/tools.
for subdir in vc vcruntime dx stlport stlport-4.6 overlay allocator; do
    cp -a --no-preserve=ownership "$INPUTS/$subdir" "$ROOT/tools/$subdir"
done

# Install the sealed guard scripts.
for f in pool_bootstrap.sh pool_compiler.py pool_network.py pool_probe.py pool_protocol.py pool_worker.py; do
    install -m 0444 "$SCRIPT_DIR/guard/$f" "$ROOT/guard/$f"
done
install -m 0555 "$SCRIPT_DIR/guard/pool_launcher.py" "$ROOT/guard/pool_launcher.py"
install -m 0444 "$SCRIPT_DIR/worker-template.json" "$ROOT/worker-template.json"

chown -R root:root "$ROOT/tools" "$ROOT/guard"
chmod -R a+rX,go-w "$ROOT/tools" "$ROOT/guard"
chmod 0555 "$ROOT/guard/pool_launcher.py"

# Build the minimal Ubuntu 24.04 (noble) rootfs with Wine 9.0 (amd64 + i386).
debootstrap --variant=minbase --include=ca-certificates,python3,util-linux \
    --keyring=/usr/share/keyrings/ubuntu-archive-keyring.gpg \
    noble "$ROOTFS" https://archive.ubuntu.com/ubuntu

cat > "$ROOTFS/etc/apt/sources.list" <<'APT'
deb https://archive.ubuntu.com/ubuntu noble main universe
deb https://archive.ubuntu.com/ubuntu noble-updates main universe
deb https://security.ubuntu.com/ubuntu noble-security main universe
APT

chroot "$ROOTFS" dpkg --add-architecture i386
chroot "$ROOTFS" apt-get update -q
chroot "$ROOTFS" apt-get install -y --no-install-recommends \
    "wine=$WINE_VERSION" \
    "wine32:i386=$WINE_VERSION" \
    "wine64=$WINE_VERSION" \
    "wine32-preloader:i386=$WINE_VERSION" \
    "wine64-preloader=$WINE_VERSION"
chroot "$ROOTFS" apt-get clean

# Preload direct Linux i386 socket syscalls inside the sealed rootfs so
# pool_network.py can keep i386 socketcall(102) denied while allowing AF_UNIX.
shim_work=$(mktemp -d /var/tmp/wine-socket-shim.XXXXXX)
trap 'rm -rf -- "$shim_work"' EXIT
gcc -m32 -Wall -Wextra -Werror -fPIC -O2 -nostdlib -shared \
    -I/usr/include/x86_64-linux-gnu "$SCRIPT_DIR/wine_socket_direct.c" -o "$shim_work/i386.so"
printf '%s\n' '/* The x86-64 runtime already uses direct socket syscalls. */' > "$shim_work/empty.c"
gcc -m64 -Wall -Wextra -Werror -fPIC -O2 -nostdlib -shared "$shim_work/empty.c" -o "$shim_work/amd64.so"
install -m 0444 "$shim_work/i386.so" "$ROOTFS/usr/lib/i386-linux-gnu/wine-socket-direct.so"
install -m 0444 "$shim_work/amd64.so" "$ROOTFS/usr/lib/x86_64-linux-gnu/wine-socket-direct.so"
printf '%s\n' '/$LIB/wine-socket-direct.so' > "$ROOTFS/etc/ld.so.preload"
chmod 0644 "$ROOTFS/etc/ld.so.preload"
rm -rf -- "$shim_work"
trap - EXIT
chroot "$ROOTFS" /bin/true

[[ ! -e $ROOTFS/root/.ssh && ! -e $ROOTFS/run/credentials ]]
chmod 0711 "$ROOTFS/root"

# Mount points required by pool_launcher.py inside the read-only rootfs.
install -d -m 755 \
    "$ROOTFS/opt/boat-compiler/tools" \
    "$ROOTFS/ci/guard" \
    "$ROOTFS/ci/wine" \
    "$ROOTFS/ci/job/src" \
    "$ROOTFS/ci/job/include" \
    "$ROOTFS/ci/job/out"

cat > /etc/tmpfiles.d/boat-compiler.conf <<'TMP'
d /run/boat-compiler 0755 root root -
d /var/lib/boat-compiler 0755 root root -
d /var/lib/boat-compiler/jobs 0700 ci-compile ci-compile -
d /var/lib/boat-compiler/stage 0700 ci-compile ci-compile -
TMP
chmod 0644 /etc/tmpfiles.d/boat-compiler.conf
systemd-tmpfiles --create /etc/tmpfiles.d/boat-compiler.conf

# Initialize a template Wine prefix inside the isolated rootfs and normalize large DLLs.
install -d -m 700 -o "$USER_NAME" -g "$USER_NAME" "$ROOT/prefix"
runuser -u "$USER_NAME" -- bwrap --unshare-all --die-with-parent --cap-drop ALL --clearenv \
    --ro-bind "$ROOTFS" / --dev /dev --proc /proc --tmpfs /tmp \
    --bind "$ROOT/prefix" /ci/wine \
    --setenv HOME /ci --setenv PATH /usr/bin:/bin \
    --setenv WINEARCH win32 --setenv WINEPREFIX /ci/wine \
    --setenv WINEDEBUG -all --setenv WINEDLLOVERRIDES 'mscoree,mshtml=' -- \
    /bin/sh -ec 'wineboot -i && wineserver -w'
test -f "$ROOT/prefix/system.reg"
find "$ROOT/prefix/dosdevices" -mindepth 1 -maxdepth 1 ! -name c: ! -name z: -delete

prefix_sys="$ROOT/prefix/drive_c/windows/system32"
pack_win32="/usr/lib/i386-linux-gnu/wine/i386-windows"
for dll in wined3d.dll mshtml.dll; do
    if [[ -f "$prefix_sys/$dll" && ! -L "$prefix_sys/$dll" && -f "$ROOTFS$pack_win32/$dll" ]]; then
        if cmp -s "$prefix_sys/$dll" "$ROOTFS$pack_win32/$dll"; then
            ln -s -- "$pack_win32/$dll" "$prefix_sys/$dll.new"
            mv -fT -- "$prefix_sys/$dll.new" "$prefix_sys/$dll"
        fi
    fi
done
test -z "$(find "$ROOT/prefix" -xdev -type f -size +16777216c -print -quit)"

chown -R root:root "$ROOT/prefix"
chmod -R a+rX,go-w "$ROOT/prefix"
chmod 0755 "$ROOT/prefix"

bash "$SCRIPT_DIR/root-probe-access.sh"

cd "$ROOT"
find tools guard -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > input.sha256
chroot "$ROOTFS" dpkg-query -W -f='${Package}:${Architecture}\t${Version}\n' | LC_ALL=C sort > runtime-packages.tsv

python3 -B - <<'PY'
import hashlib, json
from pathlib import Path
root = Path("/opt/boat-compiler")
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
payload = {
    "approved_inputs_sha256": sha(root / "input.sha256"),
    "runtime_packages_sha256": sha(root / "runtime-packages.tsv"),
    "compiler_sha256": sha(root / "tools/vc/Vc7/bin/cl.exe"),
    "os": "ubuntu-noble",
}
(root / "image-inventory.json").write_text(json.dumps(payload, sort_keys=True) + "\n")
PY

probe_tmp=$(mktemp /run/boat-compiler/probe-initial.XXXXXX.json)
trap 'rm -f -- "$probe_tmp"' EXIT
env -i PATH=/usr/sbin:/usr/bin:/bin LANG=C \
    setpriv --reuid="$USER_NAME" --regid="$USER_NAME" --clear-groups -- \
    "$ROOT/guard/pool_launcher.py" probe > "$probe_tmp"

python3 -B - "$probe_tmp" <<'PY'
import hashlib, json, sys
from pathlib import Path
root = Path("/opt/boat-compiler")
profile = json.loads((root / "worker-template.json").read_bytes())
probe = json.loads(Path(sys.argv[1]).read_bytes())
inventory = json.loads((root / "image-inventory.json").read_bytes())
profile["compiler_sha256"] = inventory["compiler_sha256"]
profile["inventory_sha256"] = hashlib.sha256((root / "image-inventory.json").read_bytes()).hexdigest()
profile["probe_mounts"] = sorted(x["path"] for x in probe["mount_inventory"])
(root / "worker.json").write_text(json.dumps(profile, sort_keys=True) + "\n")
PY

rm -f -- "$ROOT/worker-template.json"
chmod 0644 "$ROOT"/{input.sha256,runtime-packages.tsv,image-inventory.json,worker.json}
