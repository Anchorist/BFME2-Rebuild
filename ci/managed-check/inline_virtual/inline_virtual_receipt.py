"""Write the private inline-virtual receipt for CI's exact admitted projection."""
from hashlib import sha256
import json
import os
import secrets
import stat
import subprocess

from inline_virtual_shadow import HASH, PIN
from inline_virtual_ratchet import evaluate


def encoded(doc):
    return (json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("ascii")


def receipt_key(binding):
    return sha256(encoded(binding)[:-1]).hexdigest()


def validate_binding(repo, binding, candidate_pin):
    if set(binding) != {"head", "base", "tree"} or not all(
        isinstance(value, str) and PIN.fullmatch(value) for value in (*binding.values(), candidate_pin)
    ):
        raise ValueError("virtual receipt needs full head, base, tree and candidate pins")
    root = ["git", "--git-dir", os.fspath(repo)]
    subprocess.run(
        [*root, "merge-base", "--is-ancestor", binding["base"], candidate_pin],
        check=True, stdout=subprocess.DEVNULL,
    )
    tree = subprocess.check_output([*root, "rev-parse", f"{candidate_pin}^{{tree}}"], text=True).strip()
    if tree != binding["tree"]:
        raise ValueError("virtual receipt tree differs from the admitted compiler projection")


def make_receipt(repo, binding, candidate_pin, policy_sha256, head_report, base_report, *, scope_complete):
    """The trusted planner supplies the admitted binding and recomputed closure."""
    validate_binding(repo, binding, candidate_pin)
    if not isinstance(policy_sha256, str) or not HASH.fullmatch(policy_sha256):
        raise ValueError("virtual receipt policy is unpinned")
    evidence = evaluate(head_report, base_report, expected_head=candidate_pin,
                        expected_parent=binding["base"], scope_complete=scope_complete)
    state = "pending" if evidence["status"] == "needs-evidence" else evidence["status"]
    result = {
        "binding": dict(binding), "policy_sha256": policy_sha256,
        "verdict": state, "state": state,
        "evidence_sha256": sha256(encoded(evidence)).hexdigest(),
    }
    return result, evidence


def write_private_receipt(directory, receipt):
    """Atomically replace the operator-private consumer file for this binding."""
    name = f'{receipt_key(receipt["binding"])}.inline_virtual.json'
    temp_name = f".{name}.{secrets.token_hex(6)}"
    dirfd = os.open(directory, os.O_DIRECTORY | os.O_NOFOLLOW | os.O_RDONLY)
    try:
        info = os.fstat(dirfd)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise PermissionError("virtual receipt directory must be operator-private")
        fd = os.open(temp_name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600, dir_fd=dirfd)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(encoded(receipt))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, name, src_dir_fd=dirfd, dst_dir_fd=dirfd)
        finally:
            try:
                os.unlink(temp_name, dir_fd=dirfd)
            except FileNotFoundError:
                pass
    finally:
        os.close(dirfd)
    return name
