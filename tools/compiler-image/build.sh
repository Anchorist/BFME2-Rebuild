#!/bin/bash
set -euo pipefail
# End-to-end builder for the BFME II isolated compiler image on a fresh
# Ubuntu 24.04 (noble) x86_64 machine.
#
# Usage:
#   sudo bash build.sh --inputs /path/to/inputs [--allow-other-compiler] [--scrub-ssh-host-keys]
#
# Runs:
#   1. fresh-install.sh  (host packages, ci-compile user, minimal noble + Wine 9.0 rootfs,
#                         prefix, tools, guard, root ACL, initial manifests)
#   2. outer-wine.sh     (matching outer Wine 9.0 packages)
#   3. seal.sh seal      (runtime file/symlink/package sealing + isolation probe)
#   4. control.sh --install (install /usr/local/libexec/bfme2-compiler/{run,managed_probe.py}
#                            and verify probe + one-file compile + diagnostic controls)

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

INPUTS=""
FRESH_ARGS=()
SEAL_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --inputs)
            INPUTS="${2:-}"
            FRESH_ARGS+=(--inputs "$INPUTS")
            shift 2
            ;;
        --allow-other-compiler)
            FRESH_ARGS+=(--allow-other-compiler)
            shift
            ;;
        --scrub-ssh-host-keys)
            SEAL_ARGS+=(--scrub-ssh-host-keys)
            shift
            ;;
        -h|--help)
            sed -n '2,16p' "$0"
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            echo "Usage: $0 --inputs DIR [--allow-other-compiler] [--scrub-ssh-host-keys]" >&2
            exit 2
            ;;
    esac
done

if [[ -z $INPUTS ]]; then
    echo "Usage: $0 --inputs DIR [--allow-other-compiler] [--scrub-ssh-host-keys]" >&2
    exit 2
fi

[[ $(id -u) == 0 && $(uname -m) == x86_64 ]]

echo "==> Step 1/4: fresh-install.sh"
bash "$SCRIPT_DIR/fresh-install.sh" "${FRESH_ARGS[@]}"

echo "==> Step 2/4: outer-wine.sh"
bash "$SCRIPT_DIR/outer-wine.sh"

echo "==> Step 3/4: seal.sh seal"
bash "$SCRIPT_DIR/seal.sh" seal "${SEAL_ARGS[@]}"

echo "==> Step 4/4: control.sh --install"
bash "$SCRIPT_DIR/control.sh" --install
