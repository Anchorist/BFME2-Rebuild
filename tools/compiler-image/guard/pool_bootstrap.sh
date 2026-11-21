#!/bin/sh
set -eu
/usr/bin/env -i HOME=/ci PATH=/usr/bin:/bin WINEPREFIX=/ci/wine WINEARCH=win64 \
  WINEDLLOVERRIDES=mscoree,mshtml= WINEDEBUG=-all /usr/bin/wineboot -i
test "$(readlink /ci/wine/dosdevices/z:)" = /
for drive in /ci/wine/dosdevices/*; do
  case "${drive##*/}" in
    c:|z:) ;;
    *) test -L "$drive" && rm -f -- "$drive" ;;
  esac
done
# Warm and verify the local Wine session using a fixed command.
# The compiler and this sanity check use the same network filter.
env -i HOME=/ci PATH=/usr/bin:/bin WINEPREFIX=/ci/wine WINEARCH=win64   WINEDLLOVERRIDES=mscoree,mshtml= WINEDEBUG=-all /usr/bin/python3 /ci/guard/pool_network.py   /usr/bin/wine cmd.exe /d /c echo ready >/dev/null
cd /ci/job
exec /usr/bin/python3 /ci/guard/pool_compiler.py "$@"
