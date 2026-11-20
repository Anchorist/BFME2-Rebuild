"""Read only this protected run's deadline-bound recovery artifacts."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
import re
import urllib.error
import urllib.parse
import urllib.request
from zipfile import ZipFile

from common import HEX64, REPO, REPO_ID, read
from github_status import NoRedirect
from wide_recovery import GROUP_LIMIT, active_run

ZIP_LIMIT = 24 * 1024**2
LEASE_LIMIT = 64 * 1024
ROOT = "https://api.github.com/repos/" + REPO + "/"
STORAGE_SUFFIXES = (".blob.core.windows.net", ".actions.githubusercontent.com")
NAME_PATTERN = re.compile(r"bfme-recovery-(primary|reserve|lease)-[1-9][0-9]{0,19}(?:-[0-9]+){0,2}\Z")


def epoch(value):
    ts = datetime.fromisoformat(value)
    if ts.tzinfo is None:
        raise ValueError("A GitHub artifact lacks an authenticated UTC timestamp.")
    return int(ts.timestamp())


class ArtifactPending(Exception):
    """GitHub lists this immutable artifact, but its ZIP is temporarily unreadable."""


def unavailable_zip(status):
    return status in (404, 409, 429) or 500 <= status < 600


class Actions:
    def __init__(self, head, *, base=None):
        self.run = active_run()
        self.head = head
        self.base = base
        self.run_head = head
        self.token = os.environ.pop("BFME_RECOVERY_READ_TOKEN", "")
        if (os.environ.get("GITHUB_REPOSITORY") != REPO
                or os.environ.get("GITHUB_REPOSITORY_ID") != str(REPO_ID)
                or not re.fullmatch(r"[0-9a-f]{40}", head)
                or not re.fullmatch(r"[A-Za-z0-9_.-]{15,2048}", self.token)):
            raise ValueError("Recovery requires the protected repository and read-only Actions token.")
        self.api = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, path):
        return urllib.request.Request(ROOT + path, headers={
            "Authorization": "Bearer " + self.token, "Accept": "application/vnd.github+json",
        })

    @staticmethod
    def bounded(response, limit):
        with response:
            value = response.read(limit + 1)
        if len(value) > limit:
            raise ValueError("A GitHub recovery response exceeded the configured size.")
        return value

    def get(self, path):
        try:
            response = self.api.open(self.request(path), timeout=12)
            return json.loads(self.bounded(response, 2 * 1024**2))
        except urllib.error.HTTPError as exc:
            raise ValueError(f"Expected protected GitHub recovery metadata; found HTTP {exc.code}.") from None
        except (urllib.error.URLError, TimeoutError):
            raise ValueError("Expected protected GitHub recovery metadata; found unavailable service.") from None

    def anchor(self):
        row = self.get(f"actions/runs/{self.run['id']}/attempts/{self.run['attempt']}")
        expected = {"pull_request_target": self.head, "repository_dispatch": self.base}.get(row["event"])
        if (str(row["id"]) != self.run["id"] or str(row["run_attempt"]) != self.run["attempt"]
                or expected is None or row["head_sha"] != expected
                or row["path"] != ".github/workflows/managed-pr.yml"):
            raise ValueError("Expected the protected recovery attempt and revision. Found different Actions metadata.")
        self.run_head = expected
        return epoch(row["run_started_at"])

    def inventory(self, names, *, earliest, cutoff):
        if not all(NAME_PATTERN.fullmatch(name) for name in names):
            raise ValueError("Unexpected recovery artifact name.")
        found = {}
        for page in range(1, 9):
            rows = self.get(f"actions/runs/{self.run['id']}/artifacts?per_page=100&page={page}")["artifacts"]
            for row in rows:
                name = row["name"]
                if name not in names:
                    continue
                run = row["workflow_run"]
                if (str(run["id"]) != self.run["id"] or run["repository_id"] != REPO_ID
                        or run["head_sha"] != self.run_head or row["expired"]):
                    raise ValueError("The recovery artifact has foreign provenance.")
                if not earliest <= epoch(row["created_at"]) < cutoff:
                    continue
                digest = row.get("digest", "")
                if (name in found or type(row["id"]) is not int or row["id"] <= 0
                        or not digest.startswith("sha256:") or not HEX64.fullmatch(digest[7:])
                        or type(row["size_in_bytes"]) is not int or not 0 < row["size_in_bytes"] <= ZIP_LIMIT):
                    raise ValueError("Duplicate or unsigned Actions recovery artifact.")
                found[name] = (row["id"], digest[7:])
            if len(rows) < 100:
                return found
        raise ValueError("Recovery artifact pagination exceeds the configured bound.")

    def download(self, artifact):
        ident, expected = artifact
        try:
            response = self.api.open(self.request(f"actions/artifacts/{ident}/zip"), timeout=12)
        except urllib.error.HTTPError as error:
            if error.code != 302:
                if unavailable_zip(error.code):
                    raise ArtifactPending(f"GitHub ZIP {ident} is unavailable (HTTP {error.code}).") from None
                raise ValueError(f"Expected a protected GitHub ZIP; found HTTP {error.code}.") from None
            location = error.headers["Location"]
            error.close()
            url = urllib.parse.urlsplit(location)
            if (url.scheme != "https" or not url.hostname or url.username or url.password
                    or url.port not in (443, None)
                    or not url.hostname.endswith(STORAGE_SUFFIXES)):
                raise ValueError("Unexpected artifact storage origin.")
            # A signed storage URL authenticates the ZIP. Never forward the repo token.
            try:
                response = self.api.open(urllib.request.Request(location), timeout=15)
            except urllib.error.HTTPError as exc:
                if unavailable_zip(exc.code):
                    raise ArtifactPending(f"Signed ZIP {ident} is unavailable (HTTP {exc.code}).") from None
                raise ValueError(f"Expected a signed storage ZIP; found HTTP {exc.code}.") from None
            except (urllib.error.URLError, TimeoutError):
                raise ArtifactPending(f"Signed ZIP {ident} is temporarily unreachable.") from None
        except (urllib.error.URLError, TimeoutError):
            raise ArtifactPending(f"GitHub ZIP {ident} is temporarily unreachable.") from None
        data = self.bounded(response, ZIP_LIMIT)
        if sha256(data).hexdigest() != expected:
            raise ValueError("Recovery artifact ZIP differs from its GitHub digest.")
        return data

    def extract(self, artifact, allowed, limit, output, *, require_all=True):
        output = Path(output)
        with ZipFile(BytesIO(self.download(artifact))) as archive:
            seen = set()
            for item in archive.infolist():
                name = item.filename
                parts = PurePosixPath(name).parts
                if item.is_dir():
                    if (len(parts) != 1 or not any(path.startswith(parts[0] + "/") for path in allowed)):
                        raise ValueError("Unexpected directory in recovery ZIP.")
                    continue
                if name not in allowed or name in seen or item.file_size > limit:
                    raise ValueError("Unexpected or oversized recovery ZIP member.")
                mode = (item.external_attr >> 16) & 0o170000
                if mode not in (0, 0o100000):
                    raise ValueError("Non-file entry in trusted recovery ZIP.")
                seen.add(name)
                to = output / name
                to.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                with archive.open(item) as src, to.open("xb") as dest:
                    data = src.read(limit + 1)
                    if len(data) > limit:
                        raise ValueError("Recovery decompression exceeded the configured limit.")
                    dest.write(data)
            if require_all and seen != allowed:
                raise ValueError("Missing trusted recovery ZIP member.")
        return seen

    def primary(self, artifacts, names, output):
        def save(name):
            dest = Path(output) / names[name]
            try:
                self.extract(artifacts[name], {"group.json"}, GROUP_LIMIT, dest)
            except ArtifactPending as exc:
                print(f"Expected primary checkpoint {name}; found {exc} Retrying before freeze.", flush=True)
                return None
            return name
        with ThreadPoolExecutor(max_workers=6) as threads:
            return {name for name in threads.map(save, sorted(artifacts)) if name is not None}
