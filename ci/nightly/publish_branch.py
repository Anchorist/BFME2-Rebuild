"""Add one night's result to the `nightly` branch: latest.json, SUMMARY.md and history/<date>-<commit>.json.

  python3 -B ci/nightly/publish_branch.py RESULT_DIR

Reads NIGHTLY_PUSH_TOKEN (contents: write) and GITHUB_REPOSITORY. Only this workflow writes the branch. A lost race
(another push in between) is retried on the new tip, at most three times.
"""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

BRANCH = "nightly"
IDENTITY = {"GIT_AUTHOR_NAME": "github-actions[bot]", "GIT_COMMITTER_NAME": "github-actions[bot]",
            "GIT_AUTHOR_EMAIL": "41898282+github-actions[bot]@users.noreply.github.com",
            "GIT_COMMITTER_EMAIL": "41898282+github-actions[bot]@users.noreply.github.com"}
README = """# Nightly results

Written only by `.github/workflows/nightly.yml`. `latest.json` is the newest night (format in
`ci/nightly/README.md` on main), `SUMMARY.md` its readable summary, `history/` one file per night.
"""


def run(git_dir, *args, data=None, env=None, check=True):
    r = subprocess.run(["git", "--git-dir", str(git_dir), *args], input=data, capture_output=True,
                       env=env, check=False)
    if check and r.returncode:
        raise SystemExit(f"nightly publish: expected git {args[0]} to succeed; found exit {r.returncode}: "
                         f"{r.stderr.decode(errors='replace').strip()[-300:]}")
    return r


def files_for(result_dir):
    n = json.loads((Path(result_dir) / "nightly.json").read_text())
    day = time.strftime("%Y-%m-%d", time.gmtime())
    latest = (Path(result_dir) / "nightly.json").read_bytes()
    return {"latest.json": latest, "SUMMARY.md": (Path(result_dir) / "summary.md").read_bytes(),
            f"history/{day}-{n['commit'][:12]}.json": latest, "README.md": README.encode()}, n


def main(result_dir):
    token = os.environ.pop("NIGHTLY_PUSH_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or not repo:
        raise SystemExit("nightly publish: expected NIGHTLY_PUSH_TOKEN and GITHUB_REPOSITORY; found "
                         f"token {'set' if token else 'missing'}, repository {repo or 'missing'}")
    auth = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    env = dict(os.environ, GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
               GIT_CONFIG_VALUE_0=f"AUTHORIZATION: basic {auth}", GIT_TERMINAL_PROMPT="0", **IDENTITY)
    url = os.environ.get("NIGHTLY_PUSH_URL") or f"https://github.com/{repo}.git"
    files, n = files_for(result_dir)
    with tempfile.TemporaryDirectory(prefix="bfme-nightly-publish-") as d:
        g = Path(d) / "repo.git"
        subprocess.run(["git", "init", "-q", "--bare", str(g)], check=True)
        for attempt in range(3):
            got = run(g, "fetch", "-q", "--depth=1", url, f"+refs/heads/{BRANCH}:refs/remotes/{BRANCH}", env=env, check=False)
            parent = run(g, "rev-parse", "-q", "--verify", f"refs/remotes/{BRANCH}", check=False).stdout.decode().strip() \
                if got.returncode == 0 else ""
            index_env = dict(env, GIT_INDEX_FILE=str(Path(d) / f"index{attempt}"))
            if parent:
                run(g, "read-tree", parent, env=index_env)
            for path, data in files.items():
                blob = run(g, "hash-object", "-w", "--stdin", data=data).stdout.decode().strip()
                run(g, "update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", env=index_env)
            tree = run(g, "write-tree", env=index_env).stdout.decode().strip()
            msg = f"Nightly {n['result']} for main {n['commit']}\n".encode()
            commit = run(g, "commit-tree", tree, *(["-p", parent] if parent else []), data=msg, env=env).stdout.decode().strip()
            pushed = run(g, "push", "-q", url, f"{commit}:refs/heads/{BRANCH}", env=env, check=False)
            if pushed.returncode == 0:
                print(f"Published nightly result {n['result']} for main {n['commit'][:12]} as {commit[:12]} on {BRANCH}.")
                return 0
            print(f"nightly publish: push attempt {attempt + 1} was refused (expected a fast-forward of {BRANCH}); "
                  "retrying on the new tip.", flush=True)
        raise SystemExit(f"nightly publish: expected to update {BRANCH} within 3 attempts; found every push refused")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("nightly publish: expected one argument RESULT_DIR; found " + str(len(sys.argv) - 1))
    sys.exit(main(sys.argv[1]))
