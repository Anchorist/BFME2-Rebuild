#!/bin/bash
set -euo pipefail
# Seal or verify /opt/boat-compiler manifests, symlinks, package inventory, and
# unprivileged isolation probe.
#
# Usage:
#   sudo bash seal.sh seal [--scrub-ssh-host-keys]
#   sudo bash seal.sh verify

[[ $(id -u) == 0 ]]
cd /opt/boat-compiler
mode=${1:-}
scrub_ssh=0
if [[ ${2:-} == --scrub-ssh-host-keys ]]; then
    scrub_ssh=1
elif [[ $# -gt 1 ]]; then
    echo "Usage: $0 seal|verify [--scrub-ssh-host-keys]" >&2
    exit 2
fi
[[ $mode == seal || $mode == verify ]]

if [[ -d /run/credentials && -z $(find /run/credentials -mindepth 1 -print -quit) ]]; then
    rmdir -- /run/credentials || true
fi
if [[ -d /root/.ssh && ! -L /root/.ssh ]]; then
    if find /root/.ssh -mindepth 1 -maxdepth 1 ! -name authorized_keys -print -quit | grep -q .; then
        echo "Unexpected root SSH state" >&2
        exit 3
    fi
    rm -f -- /root/.ssh/authorized_keys
    rmdir -- /root/.ssh
fi
for path in /root/.config/boat /root/.config/gh; do
    if [[ -L $path ]]; then
        unlink "$path"
    elif [[ -d $path ]]; then
        rm -rf --one-file-system -- "$path"
    fi
    [[ ! -e $path && ! -L $path ]]
done
[[ ! -e /root/.ssh && ! -e /var/run/docker.sock ]]

sha256sum -c --quiet input.sha256

if [[ $mode == seal ]]; then
    [[ ! -e runtime-files.sha256 && ! -e runtime-links.tsv ]]
    find rootfs prefix -xdev -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > runtime-files.sha256
    find rootfs prefix -xdev -type l -printf '%p\t%l\n' | LC_ALL=C sort > runtime-links.tsv
    chmod 0644 runtime-files.sha256 runtime-links.tsv
    python3 -B - <<'PY'
import hashlib, json
from pathlib import Path
inventory = Path("image-inventory.json")
profile = Path("worker.json")
obj = json.loads(inventory.read_bytes())
data = json.loads(profile.read_bytes())
for filename in ("runtime-files.sha256", "runtime-links.tsv"):
    obj[filename] = hashlib.sha256(Path(filename).read_bytes()).hexdigest()
inventory.write_text(json.dumps(obj, sort_keys=True) + "\n")
data["inventory_sha256"] = hashlib.sha256(inventory.read_bytes()).hexdigest()
profile.write_text(json.dumps(data, sort_keys=True) + "\n")
PY
fi

sha256sum -c --quiet runtime-files.sha256
cmp -s runtime-links.tsv <(find rootfs prefix -xdev -type l -printf '%p\t%l\n' | LC_ALL=C sort)
chroot rootfs dpkg-query -W -f='${Package}:${Architecture}\t${Version}\n' | LC_ALL=C sort | cmp -s - runtime-packages.tsv
systemd-tmpfiles --create /etc/tmpfiles.d/boat-compiler.conf

env -i PATH=/usr/sbin:/usr/bin:/bin LANG=C \
    setpriv --reuid=ci-compile --regid=ci-compile --clear-groups -- \
    python3 -B "$PWD/guard/pool_probe.py" "$PWD/worker.json" > /run/boat-compiler/profile-probe.json

python3 -B - <<'PY'
import hashlib, json
from pathlib import Path
inv = Path("image-inventory.json")
def h(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
x = json.loads(inv.read_bytes())
assert x["runtime-files.sha256"] == h("runtime-files.sha256")
assert x["runtime-links.tsv"] == h("runtime-links.tsv")
assert x["runtime_packages_sha256"] == h("runtime-packages.tsv")
assert x["approved_inputs_sha256"] == h("input.sha256")
assert x["compiler_sha256"] == h("tools/vc/Vc7/bin/cl.exe")
print(json.dumps({
    "image": h(inv),
    "profile": h("worker.json"),
    "compiler": x["compiler_sha256"],
    "probe_unenrolled": h("/run/boat-compiler/profile-probe.json"),
    "runtime_files": sum(1 for _ in open("runtime-files.sha256")),
}, sort_keys=True))
PY

if [[ $mode == seal && $scrub_ssh -eq 1 ]]; then
    find /etc/ssh -maxdepth 1 -type f -name 'ssh_host_*_key' -delete
fi
