"""Exact-parent ratchet over trusted, authenticated inline-virtual reports."""
from collections import Counter

from inline_virtual_shadow import PIN, fingerprint, mark_parent


def verified_report(report, pin):
    if not PIN.fullmatch(pin) or report["pin"] != pin:
        raise ValueError("inline-virtual receipt is for the wrong pin")
    required = report["required_tus"]
    taken = report["authenticated_tus"]
    if type(required) is not int or type(taken) is not int or not 0 <= taken <= required:
        raise ValueError("invalid inline-virtual authentication counts")
    if any(row["fingerprint"] != fingerprint(row) for row in report["findings"]):
        raise ValueError("inline-virtual fingerprint differs from reported effect")
    return required == taken and not any(
        str(hole[0]).startswith("src/") for hole in report["coverage_holes"]
    )


def evaluate(head, parent, *, expected_head, expected_parent, scope_complete):
    """Report exact debt, proved new findings and findings needing more evidence."""
    head_complete = verified_report(head, expected_head)
    parent_complete = verified_report(parent, expected_parent)
    if head["requested_owners"] != parent["requested_owners"]:
        raise ValueError("candidate and parent inline-virtual scopes differ")
    if type(scope_complete) is not bool:
        raise ValueError("inline-virtual scope must be validated by the caller")

    candidate = {"findings": [dict(row) for row in head["findings"]]}
    mark_parent(candidate, parent)
    counts = Counter(item["comparison_to_parent"] for item in candidate["findings"])
    complete = head_complete and parent_complete and scope_complete
    if complete and counts["changed-from-comparable-parent"]:
        status = "fail"
    elif not complete or counts["prior-unresolved"]:
        status = "needs-evidence"
    else:
        status = "pass"

    return {
        "format": 1, "head": expected_head, "parent": expected_parent,
        "status": status, "accepted": status == "pass",
        "complete_input_scope": complete,
        "requested_owners": head["requested_owners"],
        "findings": candidate["findings"],
        "counts": dict(sorted(counts.items())),
        "coverage": {
            side: {key: report[key] for key in ("required_tus", "authenticated_tus", "coverage_holes")}
            for side, report in (("head", head), ("parent", parent))
        },
    }
