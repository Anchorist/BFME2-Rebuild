"""Render source findings for the Actions summary without changing the rules."""

import json
import re


PATH_FIXES = {
    "This path is maintainer-owned or outside the eligible source and header roots.":
        "Remove this path from your pull request and ask a maintainer to handle any required change there.",
    "The path does not follow compiler CI filename limits.":
        "Shorten the path and use plain filename characters with a letter, digit or underscore at the start of each component.",
    "This change adds a source translation unit.":
        "Move the new code into an existing .c or .cpp file and remove this new file.",
    "This change deletes an existing source translation unit.":
        "Restore the deleted .c or .cpp file and make your change in that file.",
    "This change adds a Draft header.":
        "Move the new header out of include/Draft and update any includes of it.",
    "This change deletes a permanent header.":
        "Restore this permanent header before submitting your pull request.",
    "The path has a non-source Git file mode.":
        "Restore this path as a regular, non-executable UTF-8 file.",
    "The blob is not UTF-8.":
        "Save this file as UTF-8 text.",
    "The blob contains a non-text control character or bare CR.":
        "Remove the control character on this line or convert the line ending to LF or CRLF.",
}

TYPE_FIXES = {
    "void pointer": ("untyped pointers",
                     "Replace void * on this line with a pointer to the actual object type used by the caller."),
    "reinterpret cast": ("reinterpret casts",
                         "Remove this reinterpret_cast and carry the actual object or pointer type through to this line."),
    "c pointer cast": ("C-style pointer casts",
                       "Remove this C-style pointer cast and give the pointer its actual type where it is declared or passed."),
    "this arithmetic": ("offsets from this",
                        "Replace the offset calculation with direct access to the typed member or base class."),
    "cast call result": ("casts of return values",
                         "Declare the function's actual return type and use the returned value without a cast here."),
}


TEXT_ENTITIES = str.maketrans({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    **{char: f"&#{ord(char)};" for char in "[]()*\x60_|\\@#"},
})


def public_text(text):
    return json.dumps(text, ensure_ascii=True)[1:-1].translate(TEXT_ENTITIES)


def contributor_copy(rule, message, remedy):
    if rule == "G1":
        if message in PATH_FIXES:
            return message, PATH_FIXES[message]
        if message.startswith("Function ") and " moved from " in message:
            return message, "Restore the function body to the original source file named above."
        size = re.fullmatch(r"The file exceeds ([0-9]+) bytes\.", message)
        if size:
            return message, f"Reduce this file to at most {size[1]} bytes."
    if rule == "G4":
        kind, _, rest = message.partition(" increased by ")
        if kind in TYPE_FIXES and rest:
            label, fix = TYPE_FIXES[kind]
            return f"The number of {label} increased by {rest}", fix
    if rule == "G6":
        scope = re.fullmatch(r"([0-9]+) source files contain real changes beyond Draft include/use updates\. The limit is ([0-9]+)\.",
                             message)
        if scope:
            return (f"This pull request makes substantive edits in {scope[1]} source files.",
                    f"Move this file's edits to a separate pull request so this one changes at most {scope[2]} source files.")
        if message == "A literal include still points to a deleted Draft header.":
            return message, "Point this include at the permanent header or keep the Draft header until all includes are updated."
    return message, remedy


def public_report(items, rules):
    table = ["| Rule | Result |", "| --- | --- |"]
    findings = []
    for item in items:
        rule = item["id"]
        state = {"pass": "Pass", "fail": "Fail", "blocked": "Fail (blocked by G1)"}[item["status"]]
        table.append(f"| {rule} {rules[rule]} | {state} |")
        findings.extend(item["findings"])
    lines = table
    size = sum(len(line) + 1 for line in lines)
    if findings:
        lines.append("")
    for finding in findings:
        rule, line = finding["rule"], finding["line"]
        if rule not in rules or type(line) is not int or line < 1:
            raise ValueError("Invalid source finding")
        message, remedy = contributor_copy(rule, finding["message"], finding["remedy"])
        path = public_text(finding["path"])
        prose = public_text(message + " " + remedy)
        row = f"- <code>{path}:{line}</code> **{rule}** <span>{prose}</span>"
        size += len(row) + 1
        if size > 949_500:
            lines.append("**More findings:** Split the change into smaller pull requests and check each one again.")
            break
        lines.append(row)
    return "\n".join(lines) + "\n"
