#!/bin/bash
set -euo pipefail
# Install the matching outer Wine packages (9.0~repack-4build3) on the host.
[[ $(id -u) == 0 && -d /opt/boat-compiler && ! -e /run/docker.sock ]]
version='9.0~repack-4build3'
if [[ ! -x /usr/bin/wine ]]; then
    export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=l
    apt-get install -y --no-install-recommends "wine=$version" "wine64=$version"
fi
test -x /usr/bin/wine
[[ $(dpkg-query -W -f='${Version}' wine) == "$version" ]]
[[ $(dpkg-query -W -f='${Version}' wine64) == "$version" ]]
[[ ! -e /run/docker.sock ]]
sha256sum "$(readlink -f /usr/bin/wine)"
