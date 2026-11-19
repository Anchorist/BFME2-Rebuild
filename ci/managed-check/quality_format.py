"""Render the deterministic, contributor-facing check report."""
import re

from progress_delta import public_table

RULES = {
    "empty": ("Measurable source", "Make a C or C++ source change before requesting comparison."),
    "source-intake": ("Source intake", "Use up to 60 regular UTF-8 C or C++ files under src/ and include/. Split large changes into smaller pull requests."),
    "no-includers": ("Header coverage", "Connect the header to an existing ledger-owned translation unit."),
    "wide-cap": ("Comparison size", "Split the header changes into smaller pull requests or ask a maintainer about this dependency scope."),
    "native-source": ("Native source checks", "Review the source check above and restore the expected source or compiler contract."),
    "protected-path": ("Protected path", "Remove workflow, checker, ledger, configuration or baseline edits from this source PR."),
    "source-policy": ("Compiler input policy", "Use a project-relative literal include and an approved source directive."),
    "compile": ("Compile success", "Fix the compiler errors at the source locations above and push the corrected patch."),
    "regression": ("Credit and proof retention", "Restore the earlier matched behavior or correct the changed definition."),
    "verified": ("Object VERIFIED retention", "Restore the object's previous verified contents and dependencies."),
    "duplicate": ("One definition", "Keep one canonical definition and update its includers."),
    "declaration": ("Protected declaration", "Restore the declaration or include its qualified Removed-Declaration trailer and explain the removal."),
    "annotation": ("FUNCTION annotation integrity", "Restore the existing FUNCTION annotation."),
    "assembly": ("Inline assembly policy", "Replace the disallowed inline assembly with source."),
    "attribution": ("Source attribution", "Keep the existing attribution and source ownership metadata."),
    "deletion": ("Ledger-owned translation unit", "Retain the mapped translation unit and submit any ownership move separately."),
    "new_tu": ("Ledger admission", "Use the existing owner translation unit or submit a separate trusted ledger update."),
    "conflict": ("Main compatibility", "Rebase this branch on main and push the corrected patch."),
    "data": ("Data identity", "Preserve the credited data definition or the referenced symbol's existing identity."),
    "wrong-reference": ("Reference identity", "Use the correct referenced object or function identity."),
    "reference-proof": ("Reference proof", "Restore the previously proven reference and its typed provider."),
    "placeholder-type": ("Type names", "Use the evidenced name of the represented type."),
    "type-placement": ("Class definition placement", "Put the canonical class definition in an existing project header."),
    "partial-body": ("New function body match", "Match the reference body before landing the new function."),
}


def quoted(value):
    payload = str(value)
    marker = chr(96) * (1 + max((len(s) for s in re.findall(chr(96) + "+", payload)), default=0))
    return marker + " " + payload + " " + marker


def instruction_cell(record):
    return quoted(f"+0x{record['offset']:X} {record['text']}") if record else "—"


def append_function(out, row, label, location):
    main = "- " + quoted(label) + " · " + quoted(location)
    if row.get("rva"):
        main += " · " + quoted(row["rva"])
    main += f" · {row['old']} → {row['new']}"
    if row.get("pct") is not None:
        main += f" · {row['pct']:.1f}%"
    if row.get("compiled_size") is not None and row.get("retail_size") is not None:
        main += f" · compiled {row['compiled_size']} B, reference {row['retail_size']} B"
    if row.get("first") is not None:
        main += f" · first difference at function offset +0x{row['first']:X}"
    if row.get("explanation"):
        main += " · " + row["explanation"]
    out.append(main)
    actual = row.get("compiled_listing", [])
    if actual:
        out.extend(["", "| Compiled instructions |", "| --- |"])
        out.extend(f"| {instruction_cell(item)} |" for item in actual)
        out.append("")


def quality_report(base, head, result):
    labels = {"ok": "Pass", "regression": "Fail", "gate": "Fail", "conflict": "Conflict",
              "nothing": "No source change", "pending": "Pending", "infrastructure": "Infrastructure failure"}
    out = [f"**BFME II / Boat — {labels[result['kind']]}**", "",
           f"Head {quoted(head[:12])} on main {quoted(base[:12])}."]
    edited = result.get("edited", [])
    identities = {(row.get("owner"), row.get("rva")) for row in edited if row.get("rva")}
    if edited:
        out += ["", "**Changed or added functions**"]
        for row in edited:
            append_function(out, row, row["function"], f"{row['path']}:{row['line']}")
    collateral = [row for row in result.get("lost", []) if (row["path"], row["rva"]) not in identities]
    if collateral or result.get("objects"):
        out += ["", "**Regressions outside edited functions**"]
        for row in collateral:
            item = dict(row, explanation="Compiler errors prevent checking this translation unit."
                        if row["new"] == "COMPILE_ERROR" else "The checked credit or proof was lost.")
            append_function(out, item, row.get("name") or row["rva"], row["path"])
        for path in result.get("objects", []):
            out.append("- " + quoted(path) + " · Object VERIFIED was lost.")
    errors = result.get("diagnostics", [])
    diagnostic_lines = ["", "**Compiler diagnostics**", *("- " + quoted(line) for line in errors)] if errors else []
    required = []
    notices = list(dict.fromkeys(result.get("rules", [])))
    if notices:
        required += ["", "**Refusing rules**"]
        required += [f"- **{RULES[tag][0]}** · {RULES[tag][1]}" for tag in notices if tag in RULES]
    messages = result.get("messages", [])
    if messages:
        required += ["", *("- " + line for line in messages)]
    measure = ["", *public_table(result.get("progress"))]
    if "judged" in result:
        measure += ["", f"{result['judged']} translation units checked."]
    limit = 7900
    foot = required + measure
    # Keep diagnostics and remedies visible when a wide change has dozens of rows.
    diagnostic_lines = bounded_prefix(diagnostic_lines, min(2600, limit - encoded_size(foot) - 512))
    visible = bounded_prefix(out, limit - encoded_size(diagnostic_lines + foot))
    return "\n".join(visible + diagnostic_lines + foot)


def encoded_size(lines):
    return sum(len(line.encode()) + 1 for line in lines)


def bounded_prefix(lines, budget):
    if encoded_size(lines) <= budget:
        return lines
    more = ["", "Additional entries omitted from this section."]
    budget -= encoded_size(more)
    result = []
    for line in lines:
        cost = len(line.encode()) + 1
        if cost > budget:
            break
        result.append(line)
        budget -= cost
    return result + more

