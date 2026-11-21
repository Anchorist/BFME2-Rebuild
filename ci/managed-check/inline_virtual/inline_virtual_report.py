"""Deterministic plain text for an exact-parent inline-virtual CI result."""
import json
import re


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
    elif effect["kind"] == "x87-read":
        width, offset = effect["value"]
        text = f"loads the {width}-bit receiver field at {offset} into the x87 return register"
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
    if typed_scope := evidence.get("typed_scope"):
        lines.append(f"Protected comparison selected {len(typed_scope['tables'])} virtual table(s).")
        source_scope = typed_scope.get("source_scope", {})
        if not source_scope.get("complete", True):
            for path in source_scope.get("compiler_changes", ())[:4]:
                lines.append(f"Protected compiler settings differ for {path}.")
            for item in source_scope["material"][:4]:
                lines.append(f"Complete virtual owner and descendant evidence is needed for {item}.")
    for side in ("parent", "head"):
        scope = evidence["coverage"][side]
        if scope["required_tus"] != scope["authenticated_tus"]:
            lines.append(f"{side.capitalize()} compiler proofs: {scope['authenticated_tus']}/{scope['required_tus']} translation units.")
        if contextual := scope.get("context_table_holes"):
            lines.append(f"{side.capitalize()} unrelated table observations: {len(contextual)} with incomplete evidence.")
        selected = [(target, reason) for target, reason in scope["coverage_holes"]
                    if re.fullmatch(r"[?$@A-Za-z0-9_]{1,160}", target)
                    and re.fullmatch(r"[A-Za-z0-9 _-]{1,120}", reason)]
        for table, reason in selected[:4]:
            lines.append(f"{side.capitalize()} {table}: {reason}.")
    return "\n".join(lines) + "\n"
