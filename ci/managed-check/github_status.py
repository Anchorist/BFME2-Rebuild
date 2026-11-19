"""Repository-scoped GitHub status API and protected event binding."""
import os
import re
import urllib.error
import urllib.request

from common import CONTEXT, HEX40, REPO, REPO_ID, encoded, read


class Superseded(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def event():
    if (os.environ.get("GITHUB_REPOSITORY") != REPO
            or os.environ.get("GITHUB_REPOSITORY_ID") != str(REPO_ID)
            or os.environ.get("GITHUB_REF") != "refs/heads/main"
            or os.environ.get("GITHUB_EVENT_NAME") != "pull_request_target"):
        raise ValueError("This workflow requires the approved protected repository and main.")
    payload = read(os.environ["GITHUB_EVENT_PATH"], 2 * 1024**2)
    pr = payload["pull_request"]
    base, head, number = os.environ["GITHUB_SHA"], pr["head"]["sha"], pr["number"]
    validate_pr(pr, number, head)
    if not HEX40.fullmatch(base):
        raise ValueError("The workflow revision is invalid.")
    return {"number": number, "base": base, "head": head, "login": "bfme-boat", "uid": 1,
            "event_association": pr.get("author_association")}


def validate_pr(pr, number, head):
    if (pr["state"] != "open" or type(number) is not int or not 0 < number < 10**9
            or pr["number"] != number or pr["base"]["repo"]["id"] != REPO_ID
            or pr["base"]["ref"] != "main" or not HEX40.fullmatch(head)):
        raise ValueError("The pull request metadata is outside the managed check scope.")


class GitHub:
    def __init__(self):
        self.token = os.environ.pop("BFME_STATUS_TOKEN", None) or os.environ.pop("BFME_READ_TOKEN", None)
        if not self.token or not re.fullmatch(r"[A-Za-zA-Z0-9_.-]{15,2048}", self.token):
            raise ValueError("This protected step requires its repository token.")
        self.api = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def call(self, path, value=None):
        import json
        request = urllib.request.Request("https://api.github.com/repos/" + REPO + "/" + path,
                                         data=encoded(value) if value is not None else None,
                                         headers={"Authorization": "Bearer " + self.token,
                                                  "Accept": "application/vnd.github+json",
                                                  "Content-Type": "application/json"})
        try:
            with self.api.open(request, timeout=25) as response:
                raw = response.read(2 * 1024**2 + 1)
        except urllib.error.HTTPError as exc:
            raise ValueError(f"The GitHub API returned HTTP {exc.code}.") from None
        if len(raw) > 2 * 1024**2:
            raise ValueError("The GitHub API response exceeded the configured limit.")
        return json.loads(raw)

    def current(self, binding):
        number, head, base = (binding[key] for key in ("number", "head", "base"))
        pr = self.call(f"pulls/{number}")
        if pr["state"] != "open" or pr["base"]["ref"] != "main":
            raise Superseded()
        validate_pr(pr, number, head)
        if (pr["head"]["sha"] != head or self.call("git/ref/heads/main")["object"]["sha"] != base):
            raise Superseded()
        return pr

    def status(self, binding, state, text, *, context=CONTEXT):
        run = os.environ["GITHUB_RUN_ID"]
        if not re.fullmatch(r"[1-9][0-9]{0,20}", run):
            raise ValueError("The Actions run ID is invalid.")
        result = self.call("statuses/" + binding["head"], {"state": state, "context": context,
                           "description": text, "target_url": f"https://github.com/{REPO}/actions/runs/{run}"})
        if result.get("state") != state or result.get("context") != context:
            raise ValueError("GitHub did not acknowledge the expected commit status.")


def admitted(pr, event_association=None):
    head_repo = pr.get("head", {}).get("repo") or {}
    roles = {"OWNER", "MEMBER", "COLLABORATOR"}
    return (head_repo.get("id") == REPO_ID
            or pr.get("author_association") in roles
            or event_association in roles
            or any(label.get("name") == "boat-ok" for label in pr.get("labels", ())))

