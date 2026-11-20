#!/usr/bin/env bash
# One game run of a linked image, on the private nightly image.
#   play.sh JOB_DIR IMAGE_EXE NIGHTLY_ROOT TOOL.py ARGS...
# NIGHTLY_ROOT holds game/ (installed game), prefix64/ (Wine prefix), py64/ (Windows Python), appdata/ and
# harness/ (the game test tools). Each run gets private copies of the prefix and the small game files; the large
# archives are linked read-only. Results land in JOB_DIR/out; JOB_DIR/out/done.json records the exit code.
set -u
J=$1 IMG=$2 R=$3; shift 3; TOOL=$1; shift
for need in "$R/game" "$R/prefix64" "$R/py64" "$R/appdata" "$R/harness/tools/$TOOL" "$IMG"; do
  if [ ! -e "$need" ]; then echo "play.sh: expected $need; found nothing" >&2; exit 90; fi
done
for cmd in wine wineserver Xvfb xauth mcookie; do
  command -v "$cmd" >/dev/null || { echo "play.sh: expected the command $cmd on the image; found none" >&2; exit 91; }
done
W=$(mktemp -d "${RUNNER_TEMP:-/tmp}/bfme-play.XXXXXX"); S=$W/slot
mkdir -p "$S/game" "$J/out" "$J/image"
cp "$IMG" "$J/image/exit.exe"
mkdir -p "$J/harness" && cp -a "$R/harness/." "$J/harness/"; mkdir -p "$J/harness/build"
cp "$(dirname "$0")/regset.py" "$J/regset.py"
for d in prefix64 appdata py64; do mkdir -p "$S/$d" && cp -a "$R/$d/." "$S/$d/"; done
( cd "$R/game" && find . -type d -exec mkdir -p "$S/game/{}" \; \
  && find . -type f -size +20M -exec ln -s "$R/game/{}" "$S/game/{}" \; \
  && find . -type f ! -size +20M -exec cp -p "{}" "$S/game/{}" \; )
cp "$J/image/exit.exe" "$S/game/game.dat"
DD=$S/prefix64/dosdevices
for p in "$DD"/?:; do n=$(basename "$p"); [ "$n" = c: ] || rm -f "$p"; done
ln -s "$S/game" "$DD/g:"; ln -s "$S/py64" "$DD/p:"; ln -s "$S/appdata" "$DD/s:"; ln -s "$J/harness" "$DD/h:"; ln -s "$J" "$DD/i:"
D=:91
X=$(mktemp -d); export XAUTHORITY=$X/auth
xauth -q -f "$XAUTHORITY" add "$D" . "$(mcookie)"
export WINEPREFIX=$S/prefix64 WINEARCH=win64 WINEDEBUG=-all DISPLAY=$D BFME_PRIVATE_DISPLAY=$D \
       LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe PYTHONUTF8=1 PYTHONUNBUFFERED=1
if [ -e "/tmp/.X11-unix/X${D#:}" ]; then echo "play.sh: expected display $D free; found it in use" >&2; exit 97; fi
Xvfb "$D" -auth "$XAUTHORITY" -nolisten tcp -screen 0 2048x1536x24 +extension GLX >/dev/null 2>&1 & XP=$!
for _ in $(seq 50); do [ -e "/tmp/.X11-unix/X${D#:}" ] && break; sleep 0.2; done
cleanup() { wineserver -k 2>/dev/null; kill $XP 2>/dev/null; wait $XP 2>/dev/null; rm -rf "$X" "$W"; }
trap cleanup EXIT
T0=$(date -u +%s)
cd "$J/harness" || exit 98
wine 'P:\python.exe' 'I:\regset.py' 2>&1 | tr -d '\r' | tail -1
wineserver -w
timeout --kill-after=60 6600 nice -n 10 wine 'P:\python.exe' "H:\\tools\\$TOOL" "$@" --game-dir 'G:\' --appdata 'S:\' \
  --real-image 'I:\image\exit.exe' > "$J/out/tool.log" 2>&1
RC=$?
wineserver -k 2>/dev/null
find "$J/harness/build" -newermt "@$T0" -type f \( -name '*.json' -o -name '*.txt' -o -name '*.log' \) -exec cp {} "$J/out/" \; 2>/dev/null
printf '{"rc":%s,"seconds":%s}\n' "$RC" "$(( $(date -u +%s) - T0 ))" > "$J/out/done.json"
echo "play.sh: $TOOL exit $RC"
exit 0
