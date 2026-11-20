"""Fetch only an authenticated state artifact for this checkout, with bounded input."""

from hashlib import file_digest
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "managed-check"))
from common import HEX40, HEX64, REPO, REPO_ID
from github_status import GitHub
from gitrepo import Git, GitFailure
from state_evidence import LIMIT

WORKFLOW = ".github/workflows/state.yml"
RUN_ID = re.compile(r"[1-9][0-9]{0,19}\Z")


def select_run(api, sha):
    filters = urllib.parse.urlencode({"head_sha": sha, "branch": "main", "status": "success",
                                      "per_page": 10})
    runs = api.call("actions/workflows/state.yml/runs?" + filters)["workflow_runs"]
    for item in runs:
        if (item.get("path") == WORKFLOW and item.get("head_sha") == sha
                and item.get("head_branch") == "main" and item.get("status") == "completed"
                and item.get("event") in {"push", "workflow_dispatch", "repository_dispatch"}
                and item.get("conclusion") == "success"
                and (item.get("repository") or {}).get("id") == REPO_ID
                and RUN_ID.fullmatch(str(item.get("id", "")))
                and RUN_ID.fullmatch(str(item.get("run_attempt", "")))):
            return item["id"], item["run_attempt"]
    return None


def select_artifact(api, run, attempt):
    name = f"bfme-exact-main-state-{attempt}"
    artifacts = api.call(f"actions/runs/{run}/artifacts?name={name}&per_page=5")["artifacts"]
    rows = [item for item in artifacts if item.get("name") == name and not item.get("expired")]
    if len(rows) != 1:
        return None
    row = rows[0]
    size = row.get("size_in_bytes")
    digest = (row.get("digest") or "").removeprefix("sha256:")
    if (type(size) is not int or not 0 < size <= LIMIT or not HEX64.fullmatch(digest)
            or not RUN_ID.fullmatch(str(row.get("id", "")))):
        return None
    return row["id"], size, digest


def download(api, artifact, archive_size, digest, output):
    if not 0 < archive_size <= LIMIT:
        raise ValueError("The state archive exceeds its allowance.")
    url = f"https://api.github.com/repos/{REPO}/actions/artifacts/{artifact}/zip"
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + api.token})
    try:
        with api.api.open(req, timeout=15):
            raise ValueError("Expected a GitHub artifact storage redirect.")
    except urllib.error.HTTPError as error:
        if error.code != 302:
            raise
        url = error.headers["Location"]
        error.close()
    parts = urllib.parse.urlsplit(url)
    host = parts.hostname or ""
    if (parts.scheme != "https" or parts.username or parts.password or parts.port not in (443, None)
            or not host.endswith((".blob.core.windows.net", ".actions.githubusercontent.com"))):
        raise ValueError("GitHub returned an unexpected artifact storage host.")
    # No GitHub token is sent to artifact storage, and redirects are disabled.
    with tempfile.TemporaryFile() as archive:
        with api.api.open(urllib.request.Request(url), timeout=20) as response:
            left = LIMIT
            while left:
                block = response.read(min(65536, left))
                if not block:
                    break
                archive.write(block)
                left -= len(block)
            if left == LIMIT or response.read(1):
                raise ValueError("Unexpected state package size.")
        archive.seek(0)
        if file_digest(archive, "sha256").hexdigest() != digest:
            raise ValueError("GitHub artifact digest did not match.")
        with zipfile.ZipFile(archive) as bundle:
            members = bundle.infolist()
            if (len(members) != 1 or members[0].filename != "base-state.json"
                    or not 0 < members[0].file_size <= LIMIT):
                raise ValueError("The state package must contain one bounded JSON file.")
            with bundle.open(members[0]) as source, output.open("xb") as target:
                shutil.copyfileobj(source, target, 65536)


def main(output, *, parent=False):
    sha = os.environ["GITHUB_SHA"]
    if (os.environ["GITHUB_REPOSITORY"] != REPO or os.environ["GITHUB_REPOSITORY_ID"] != str(REPO_ID)
            or os.environ["GITHUB_REF"] != "refs/heads/main" or not HEX40.fullmatch(sha)):
        raise ValueError("Use the exact protected repository and main.")
    if parent:
        if os.environ.get("GITHUB_EVENT_NAME") not in {"push", "workflow_dispatch", "repository_dispatch"}:
            raise ValueError("Only the trusted state workflow may carry the parent.")
        checkout = Git(Path.cwd() / ".git")
        try:
            sha = checkout.rev(sha + "^")
        except GitFailure:
            print("Main has no predecessor in the state checkout.")
            return
    temporary = output.with_name(output.name + ".partial")
    try:
        api = GitHub()
        run = select_run(api, sha)
        ref = select_artifact(api, *run) if run else None
        if ref:
            download(api, *ref, temporary)
            temporary.replace(output)
            print("Downloaded state produced for this exact protected revision.")
            return
    except (OSError, LookupError, TypeError, ValueError, zipfile.BadZipFile):
        # Storage URLs are signed, so never include exceptions or URLs in logs.
        print("Protected main state could not be fetched.")
    finally:
        temporary.unlink(missing_ok=True)
    print("Using a fresh measurement of the protected parent.")


if __name__ == "__main__":
    os.umask(0o077)
    main(Path(sys.argv[1]), parent=sys.argv[2:] == ["--parent"])

