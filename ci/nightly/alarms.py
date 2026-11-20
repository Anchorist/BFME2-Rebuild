"""Raise or clear each nightly alarm through the repository's shared alarm tool (ci/alarms/alarm.py).

  python3 -B ci/nightly/alarms.py ALARMS_JSON RUN_URL

ALARMS_JSON is {kind: {"failed": bool, "detail": text}} from result.py. One issue per kind: a failing kind opens or
updates its issue, a clean kind closes it. A kind this night did not measure is not touched.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

TOOL = Path(__file__).resolve().parents[1] / "alarms/alarm.py"
KINDS = ("nightly-build", "nightly-crash", "nightly-differs", "nightly-control")


def commands(alarms, run_url, detail_dir):
    out = []
    for kind in KINDS:
        if kind not in alarms:
            continue
        a = alarms[kind]
        f = Path(detail_dir) / (kind + ".txt")
        f.write_text(a["detail"] + "\n")
        out.append([sys.executable, "-B", str(TOOL), "set", kind, "--failed", "true" if a["failed"] else "false",
                    "--detail-file", str(f), "--run-url", run_url])
    return out


def main(path, run_url):
    alarms = json.loads(Path(path).read_text())
    unknown = sorted(set(alarms) - set(KINDS))
    if unknown:
        print(f"::error::nightly alarms: expected kinds {', '.join(KINDS)}; found {', '.join(unknown)}")
        return 1
    if not TOOL.is_file():
        print(f"::error::nightly alarms: expected the shared alarm tool at ci/alarms/alarm.py; found none")
        return 1
    worst = 0
    with tempfile.TemporaryDirectory(prefix="bfme-nightly-alarm-") as d:
        for cmd in commands(alarms, run_url, d):
            r = subprocess.run(cmd, env=dict(os.environ), capture_output=True, text=True)
            print((r.stdout + r.stderr).strip())
            if r.returncode:
                print(f"::error::nightly alarms: expected the alarm tool to accept {cmd[4]}; found exit {r.returncode}")
                worst = 1
    return worst


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("nightly alarms: expected arguments ALARMS_JSON RUN_URL; found " + " ".join(sys.argv[1:]))
        sys.exit(1)
    sys.exit(main(*sys.argv[1:]))
