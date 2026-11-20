"""Fetch the private game run's result and prepare it for result.py.

  python3 -B ci/nightly/fold_in.py OUT_DIR

1. Resolves the `results` branch of the private game repository (GAME_REPO, `owner/name`) to one commit with
   GAME_TOKEN (a token that can only read that repository) and reads `meta.json` and `stage2.json` at that commit,
   so the two files always come from the same result.
2. Checks the result names a public run of `.github/workflows/nightly.yml` in this repository and binds it through
   this repository's own API (GH_TOKEN, Actions read): that exact run attempt succeeded on that commit and every
   compile shard 0..SHARDS-1 succeeded in it.
3. Writes OUT_DIR/stage2/stage2.json (scrubbed again) and prints `key=value` lines for GITHUB_OUTPUT: fresh, sha,
   run_id, attempt, game_job. Anything that does not hold is reported in one expected/found line and not folded in.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scrub import scrub  # noqa: E402

MAX_BYTES = 1024 * 1024
MAX_AGE = 20
WORKFLOW = ".github/workflows/nightly.yml"
HEX = set("0123456789abcdef")


def get(api, path, token, raw=False):
    req = urllib.request.Request(f"{api}/{path}", headers={
        "Authorization": "Bearer " + token, "X-GitHub-Api-Version": "2022-11-28",
        "Accept": "application/vnd.github.raw+json" if raw else "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError(f"expected {path} under {MAX_BYTES} bytes; found more")
    return json.loads(data)


def is_sha(value):
    return isinstance(value, str) and len(value) == 40 and not set(value) - HEX


def decide(meta, stage2, now):
    """(ok, reason, values) for one result read at one commit; pure, tested offline."""
    sha = meta.get("sha")
    if not is_sha(sha):
        return False, "expected a 40-hex commit in meta.json; found something else", {}
    if meta.get("workflow") != WORKFLOW:
        return False, f"expected a result of {WORKFLOW}; found one of {str(meta.get('workflow'))[:80]}", {}
    if stage2 is not None and stage2.get("sha") != sha:
        return False, f"expected stage2.json of {sha}; found one of {str(stage2.get('sha'))[:50]}", {}
    try:
        run_id, attempt = int(meta["public_run_id"]), int(meta["public_run_attempt"])
        done = datetime.strptime(meta["finished_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (KeyError, ValueError, TypeError) as e:
        return False, f"expected public_run_id, public_run_attempt and finished_at in meta.json; found {type(e).__name__}", {}
    age = (now - done).total_seconds() / 3600
    if age > MAX_AGE or age < -1:
        return False, f"expected a game result from the last {MAX_AGE} hours; found one {age:.1f} hours old", {}
    job = str(meta.get("game_job", ""))
    if job not in ("success", "failure", "cancelled", "skipped"):
        job = "failure"
    return True, "fresh", {"sha": sha, "run_id": run_id, "attempt": attempt, "game_job": job}


def bind(values, run, jobs, shards):
    """(ok, reason): the named public run attempt is this workflow's, on that commit, with every shard green."""
    if run.get("path") != WORKFLOW:
        return False, f"expected run {values['run_id']} to be {WORKFLOW}; found {str(run.get('path'))[:80]}"
    if run.get("head_sha") != values["sha"] or run.get("head_branch") != "main":
        return False, f"expected run {values['run_id']} on main at {values['sha']}; found {run.get('head_branch')} at {run.get('head_sha')}"
    if run.get("run_attempt") != values["attempt"] or run.get("conclusion") != "success":
        return False, (f"expected attempt {values['attempt']} of run {values['run_id']} to have succeeded; found attempt "
                       f"{run.get('run_attempt')} {run.get('conclusion')}")
    green = {j.get("name") for j in jobs if j.get("conclusion") == "success"}
    missing = [i for i in range(shards) if f"Compile shard {i}" not in green]
    if missing:
        return False, f"expected compile shards 0 to {shards - 1} all successful in that attempt; found {missing[:5]} not"
    return True, "bound"


def stale(out, reason):
    """Not folded in: write the alarm the workflow raises, so a missing or stale game result is never silent."""
    Path(out).mkdir(parents=True, exist_ok=True)
    (Path(out) / "alarms.json").write_text(json.dumps({"nightly-build": {
        "failed": True, "detail": "expected a fresh result from the private game run to publish; found: " + reason}},
        indent=1, sort_keys=True) + "\n")
    print(f"fold-in: not folded in: {reason}")
    return "fresh=false\n"


def main(out):
    repo, token = os.environ.get("GAME_REPO", ""), os.environ.pop("GAME_TOKEN", "")
    own, own_token = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.pop("GH_TOKEN", "")
    api = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    shards = int(os.environ.get("SHARDS", "16"))
    if not repo or not token or not own_token:
        return stale(out, f"repo {repo or 'missing'}, game token {'set' if token else 'missing'}, "
                          f"own token {'set' if own_token else 'missing'}")
    try:
        commit = get(api, f"repos/{repo}/git/ref/heads/results", token)["object"]["sha"]
    except (urllib.error.URLError, ValueError, KeyError) as e:
        return stale(out, f"no readable results branch ({type(e).__name__})")
    if not is_sha(commit):
        return stale(out, "a results branch that does not resolve to one commit")
    meta = get(api, f"repos/{repo}/contents/meta.json?ref={commit}", token, raw=True)
    try:
        stage2 = get(api, f"repos/{repo}/contents/stage2.json?ref={commit}", token, raw=True)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        stage2 = None
        print(f"fold-in: stage2.json absent at {commit[:12]}; the night is reported from meta.json alone")
    ok, reason, values = decide(meta, stage2, datetime.now(timezone.utc))
    if ok:
        run = get(api, f"repos/{own}/actions/runs/{values['run_id']}/attempts/{values['attempt']}", own_token)
        jobs = get(api, f"repos/{own}/actions/runs/{values['run_id']}/attempts/{values['attempt']}/jobs?per_page=100",
                   own_token)["jobs"]
        ok, reason = bind(values, run, jobs, shards)
    print(f"fold-in: result commit {commit[:12]}: {reason}")
    if not ok:
        return stale(out, reason)
    d = Path(out) / "stage2"
    d.mkdir(parents=True, exist_ok=True)
    if stage2 is not None:
        (d / "stage2.json").write_text(json.dumps(scrub(stage2), indent=1, sort_keys=True) + "\n")
    return "fresh=true\n" + "".join(f"{k}={v}\n" for k, v in values.items())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("fold-in: expected one argument OUT_DIR")
    lines = main(sys.argv[1])
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a") as f:
            f.write(lines)
    print(lines, end="")
