"""Deterministic plain text for an exact-parent inline-virtual CI result."""
import json


def effect_text(effect):
    if effect is None:
        return "unavailable"
    if effect["kind"] == "pure":
        return "calls pure virtual handler"
    value = json.dumps(effect["value"], ensure_ascii=True, separators=(",", ":"))
    if effect["kind"] == "this":
        text = f"returns receiver plus {value}"
    elif effect["kind"] == "read":
        text = f"returns the receiver field {value}"
    else:
        text = f"returns {value} ({effect['kind']})"
    if effect["pop"]:
        text += f", pops {effect['pop']} stack bytes"
    if effect["write"]:
        write = json.dumps(effect["write"], ensure_ascii=True, separators=(",", ":"))
        text += f", writes receiver field {write}"
    return text


def render(evidence):
    status = evidence["status"]
    title = {
        "pass": "inline-virtual passed.",
        "fail": "inline-virtual refused. Make the virtual slot behave as the reference does.",
        "needs-evidence": "inline-virtual pending evidence. The exact parent comparison is incomplete.",
    }[status]
    lines = [title]
    for row in sorted(evidence["findings"], key=lambda item: (item["table_rva"], item["slot"], item["fingerprint"])):
        change = row["comparison_to_parent"]
        if change == "retained-from-parent":
            continue
        lines.append(f"{row['owner']} slot {row['slot']} (table 0x{row['table_rva']:08x})")
        lines.append(f"  Candidate {effect_text(row['ours'])}")
        lines.append(f"  Reference {effect_text(row['reference'])}")
        if change == "prior-unresolved":
            lines.append("  The parent has no authenticated comparable slot witness in the supplied closure.")
    for side in ("parent", "head"):
        scope = evidence["coverage"][side]
        if scope["required_tus"] != scope["authenticated_tus"]:
            lines.append(f"{side.capitalize()} compiler proofs: {scope['authenticated_tus']}/{scope['required_tus']} translation units.")
    return "\n".join(lines) + "\n"
