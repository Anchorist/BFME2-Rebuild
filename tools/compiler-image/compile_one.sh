#!/bin/bash
set -euo pipefail
# Compile one translation unit of a BFME2-Rebuild checkout through the
# installed sealed compiler entry (/usr/local/libexec/bfme2-compiler/run)
# and print the COFF object SHA-256 and timestamp-normalized SHA-256.
#
# Usage:
#   bash tools/compiler-image/compile_one.sh <source-file> [--repo DIR] [--out FILE] [--json] [--show-includes]

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec /usr/bin/python3 -B "$SCRIPT_DIR/compile_one.py" "$@"
