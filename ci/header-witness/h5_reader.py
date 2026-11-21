"""Read already-published H5 evidence (header-h5.json) for the exact pull request, head, main and merge tree.

The same issuer and artifact checks as the declaration reader (ci/managed-check/header_h2_action.read_published):
the current bot Boat status names the protected comparison run and attempt; that attempt's admission decision must
name this pull request, head, main and tree; its `bfme-header-h5-<attempt>` artifact must be unique, unexpired,
from that run and created after this read started; the receipt inside must carry the same binding and issuer. Any
miss raises, which the header rules show as held. Runs in the token step of the header rules, never in the
token-free preview.
"""
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

MAX_H5_BYTES = 256 * 1024
KEYS = ("number", "base", "head", "tree")


def _h2():
    here = Path(__file__).resolve().parents[1] / "managed-check"
    sys.path.insert(0, str(here))
    import header_h2_action
    return header_h2_action


def verified(doc, binding, run, repo_id):
    expected = {"repo": repo_id, **{key: binding[key] for key in KEYS},
                "issuer": {"run": run["id"], "attempt": run["attempt"]}}
    if (not isinstance(doc, dict) or doc.get("version") != 1 or doc.get("binding") != expected
            or not isinstance(doc.get("headers"), dict) or not isinstance(doc.get("held"), list)):
        raise ValueError("The H5 receipt does not bind the current protected attempt.")
    return doc


def read_published(binding):
    h2 = _h2()
    if (type(binding["number"]) is not int or not 0 < binding["number"] < 10**9
            or binding["base"] != os.environ["GITHUB_SHA"]
            or any(not h2.HEX40.fullmatch(binding[key]) for key in ("head", "base", "tree"))):
        raise ValueError("Use an exact current protected pull request binding.")
    api = h2.Actions(binding["head"], base=binding["base"])
    if not h2.current(api, binding):
        raise ValueError("The pull request or protected main moved before H5 readback.")
    run = h2.published_issuer(api, binding)
    api.run = run
    started = api.anchor()
    decision_artifact = h2.named_artifact(api, run, "bfme-admission-status-" + run["attempt"], started, 4096)
    with TemporaryDirectory(prefix="bfme-header-h5-") as scratch:
        api.extract(decision_artifact, {"decision.json"}, 4096, scratch)
        decision = h2.own_decision(h2.read(Path(scratch) / "decision.json", 4096))
    if any(decision[key] != binding[key] for key in KEYS):
        raise ValueError("The comparison admitted a different pull request.")
    artifact = h2.named_artifact(api, run, "bfme-header-h5-" + run["attempt"], started, MAX_H5_BYTES)
    with TemporaryDirectory(prefix="bfme-header-h5-") as scratch:
        api.extract(artifact, {"header-h5.json"}, MAX_H5_BYTES, scratch)
        doc = verified(h2.read(Path(scratch) / "header-h5.json", MAX_H5_BYTES), binding, run, h2.REPO_ID)
    if h2.published_issuer(api, binding) != run or not h2.current(api, binding):
        raise ValueError("A newer protected attempt or a moved pull request superseded the H5 evidence.")
    return doc
