"""Small GitHub REST client for the landing job.

Reads always work. Writes (merge, statuses, comments, dispatches) are refused
unless the job runs in live mode, so a dry run cannot change anything.
"""
import json
import re
import urllib.error
import urllib.request

LIMIT = 4 * 1024**2


class ApiError(Exception):
    pass


class ReadOnly(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def printable(text, limit=200):
    text = "".join(ch if ch.isprintable() else " " for ch in str(text))
    return text[:limit]


class Api:
    def __init__(self, repo, token, live):
        if not token or not re.fullmatch(r"[A-Za-z0-9_.-]{15,2048}", token):
            raise ApiError("Expected the landing job token in BFME_LANDING_TOKEN. Found none or a malformed value.")
        self._token = token
        self.live = live
        self.root = f"https://api.github.com/repos/{repo}/"
        self.graphql = "https://api.github.com/graphql"
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        self.writes = []

    def _send(self, method, path, body):
        data = json.dumps(body, sort_keys=True).encode("utf-8") if body is not None else None
        url = self.graphql if path == "graphql" else self.root + path
        request = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": "Bearer " + self._token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json"})
        try:
            with self.opener.open(request, timeout=30) as response:
                code, raw = response.status, response.read(LIMIT + 1)
        except urllib.error.HTTPError as exc:
            code, raw = exc.code, exc.read(LIMIT + 1)
        except (urllib.error.URLError, OSError) as exc:
            raise ApiError(f"Expected a response from GitHub for {method} {path.split('?')[0]}. "
                           f"Found a connection failure ({type(exc).__name__}).") from None
        if len(raw) > LIMIT:
            raise ApiError(f"Expected at most {LIMIT} bytes from {path.split('?')[0]}. Found more.")
        try:
            payload = json.loads(raw) if raw.strip() else None
        except ValueError:
            payload = None
        return code, payload

    def call(self, path):
        code, payload = self._send("GET", path, None)
        if code != 200:
            raise ApiError(f"Expected HTTP 200 from GET {path.split('?')[0]}. Found HTTP {code}.")
        return payload

    def write(self, method, path, body):
        if not self.live:
            raise ReadOnly(f"Expected no writes in dry-run mode. Found an attempted {method} {path}.")
        self.writes.append((method, path, body))
        return self._send(method, path, body)

    def mutate(self, query, variables):
        """A GraphQL mutation (writes, so live only). Returns the data object or raises with GitHub's message."""
        if not self.live:
            raise ReadOnly("Expected no writes in dry-run mode. Found an attempted GraphQL mutation.")
        self.writes.append(("POST", "graphql", {"query": query, "variables": variables}))
        code, payload = self._send("POST", "graphql", {"query": query, "variables": variables})
        errors = (payload or {}).get("errors") if isinstance(payload, dict) else None
        if code != 200 or errors or not isinstance((payload or {}).get("data"), dict):
            detail = printable((errors or [{}])[0].get("message", "") if errors else "", 160)
            raise ApiError(f"Expected HTTP 200 and data from the GraphQL mutation. Found HTTP {code} {detail}".rstrip() + ".")
        return payload["data"]
