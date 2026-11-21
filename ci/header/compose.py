"""Compose the header rules H1-H8 into the one decision a pull request sees: "BFME II / Header rules".

Pure and deterministic: the same component results give the same status, byte for byte. Each component reports
for the exact (base, head, merged tree); the producers are the wide check (H1), the declaration check (H2,
which also names ledger requests, H9), the header source checks (H3, H4, H6, H7, H8) and the layout check (H5).

Order of the decision:
  1. any rule FAILED                 -> failure  "<Hn>: <message> (main X)"        the author must change something
  2. a ledger request (H9)           -> pending  "Held: ledger request <id> (main X)"  waits, never fails
  3. a rule that is not built yet    -> pending  "Held: rule not built: H2, H5 (main X)"   never passed (ruling)
  4. a rule still collecting proof   -> pending  "Held: <Hn> <message> (main X)"
  5. otherwise                       -> success  "Header rules passed (main X)"
The landing workflow reads exactly these forms (ci/landing/lander.py, BFME_AUTO_HEADERS).
"""
from html import escape


CONTEXT = "BFME II / Header rules"
RULES = ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8")
STATES = ("pass", "held", "fail", "missing")
LIMIT = 140


def marker(base):
    return f"(main {base[:12]})"


def _fit(text, base):
    """A status description is at most 140 characters and always ends with the main marker."""
    tail = " " + marker(base)
    room = LIMIT - len(tail)
    text = " ".join(str(text).split())
    if len(text) > room:
        text = text[:room - 1].rstrip() + "…"
    return text + tail


def table_text(text):
    return escape(" ".join(str(text).split()), quote=False).replace("|", "&#124;")


def compose(base, components, ledger_request=None):
    """components: {rule: {"state": pass|held|fail|missing, "message": str, "path": str, "line": int, "remedy": str}}.

    A rule absent from `components`, or reported "missing", is a rule that is not built (or not run) for this head.
    Returns (state, description, report_lines).
    """
    rows = []
    for rule in RULES:
        item = components.get(rule) or {"state": "missing"}
        state = item.get("state")
        if state not in STATES:
            raise ValueError(f"Expected a state in {STATES} for {rule}. Found {state!r}.")
        rows.append((rule, state, item))
    report = ["| Rule | Result | Where | What to do |", "|---|---|---|---|"]
    for rule, state, item in rows:
        where = f"{item.get('path', '')}:{item['line']}" if item.get("path") and item.get("line") else item.get("path", "")
        what = item.get("remedy") or item.get("message") or ""
        shown = {"pass": "passed", "held": "waiting", "fail": "needs a fix", "missing": "not built yet"}[state]
        report.append(f"| {rule} | {shown} | {table_text(where)} | {table_text(what)} |")
    failed = [(rule, item) for rule, state, item in rows if state == "fail"]
    if failed:
        rule, item = failed[0]
        return "failure", _fit(f"{rule}: {item.get('message', 'refused')}", base), report
    if ledger_request:
        return "pending", _fit(f"Held: ledger request {ledger_request}", base), report
    missing = [rule for rule, state, _ in rows if state == "missing"]
    if missing:
        return "pending", _fit(f"Held: rule not built: {', '.join(missing)}", base), report
    held = [(rule, item) for rule, state, item in rows if state == "held"]
    if held:
        rule, item = held[0]
        return "pending", _fit(f"Held: {rule} {item.get('message', 'waiting for its proof')}", base), report
    return "success", _fit("Header rules passed", base), report


def from_preview(result):
    """Map one header-preview result (H3 H4 H6 H7 H8) to component rows."""
    components = {}
    for item in result.get("preview", []):
        findings = item.get("findings") or []
        first = findings[0] if findings else {}
        state = {"pass": "pass", "held": "held", "fail": "fail", "failure": "fail"}.get(item.get("state"), "held")
        components[item["rule"]] = {"state": state, "message": first.get("message", ""), "path": first.get("path", ""),
                                    "line": first.get("line"), "remedy": first.get("remedy", "")}
    h4 = components.get("H4")
    leads = (result.get("declaration_review") or {}).get("candidates") or []
    if h4 and h4["state"] == "held" and leads:
        first = leads[0]
        name = first["declaration"]
        h4.update(message=f"waiting to compare {name}.", path=first["path"], line=first["line"],
                  remedy=f"If you removed or changed {name}, restore it or add Removed-Declaration: {name} "
                         "to the last commit. Otherwise wait for its declaration comparison.")
    return components


def from_wide_status(status, base):
    """H1 from the BFME II / Boat status on the exact head: the wide check's verdict for this main."""
    if not status:
        return {"state": "held", "message": "The wide comparison has not reported for this commit."}
    text = status.get("description") or ""
    if not text.endswith(marker(base)):
        return {"state": "held", "message": "The wide comparison has not reported on this main."}
    if status.get("state") == "success":
        return {"state": "pass", "message": text}
    if status.get("state") == "failure":
        return {"state": "fail", "message": "The wide comparison refused this change.",
                "remedy": "Open the BFME II / Boat details for the files that lost a match."}
    return {"state": "held", "message": "The wide comparison is still running."}
