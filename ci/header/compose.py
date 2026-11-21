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
RULES = ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H10")
WIDE_ADMITTED = "Admitted by rule: header change, wide check"     # ci/admission/admit.py ADMITTED_WIDE
DAILY_LIMIT = "Held: daily limit, retried automatically"          # ci/admission/admit.py DAILY_LIMIT
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
    held.sort(key=lambda row: row[0] != "H10")     # a budget hold explains why the wide check (H1) waits
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


def from_h2(result):
    """H2 from the compiler check's verified declaration receipt (status pass | held | refuse, findings).
    Returns (H2 component, ledger request or None). A ledger request holds; it never fails."""
    findings = [item for item in result.get("findings") or [] if isinstance(item, dict)]

    def first(status):
        return next((item for item in findings if item.get("status") == status), None)

    refused = first("refuse")
    if result.get("status") == "refuse" or refused:
        item = refused or {}
        return {"state": "fail", "message": f"{item.get('declaration', 'a declaration')}: "
                f"{item.get('reason', 'does not compile to the name the ledger holds')}.",
                "path": item.get("header", ""), "line": item.get("line") or 0}, None
    request = first("ledger_request")
    if request:
        return {"state": "held", "message": request.get("reason", "")}, request.get("declaration") or "for a declaration"
    held = first("held")
    if result.get("status") == "held" or held:
        return {"state": "held", "message": (held or {}).get("reason", "the declaration check is still collecting proof")}, None
    if result.get("status") == "pass":
        return {"state": "pass", "message": "every changed declaration compiles to its ledger name"}, None
    return {"state": "held", "message": "the declaration check gave no verdict"}, None


def from_h5(doc, paths):
    """H5 from the bound layout receipt: for every changed header, the measured layout and the typed-use witnesses.
    Same rule as the layout join: unchanged or compatible shape passes; every moved member needs a newly matched
    function that uses it; size, base and slot changes wait for a witness form. It never fails."""
    def held(message):
        return {"state": "held", "message": message[:120]}
    if doc.get("held"):
        return held(str(doc["held"][0]))
    headers = doc.get("headers") if isinstance(doc.get("headers"), dict) else {}
    for path in paths:
        item = headers.get(path)
        if not isinstance(item, dict):
            return held(f"no layout evidence for {path}")
        if item.get("held"):
            return held(str(item["held"][0]))
        layout = item.get("layout") or {}
        atoms = layout.get("atoms")
        if layout.get("complete") is not True or not isinstance(atoms, list):
            return held(f"the layout of {path} is not completely measured")
        if not atoms:
            if layout.get("compatible_shape") is not True:
                return held(f"the layout of {path} was not certified unchanged")
            continue
        reads = (item.get("access") or {}).get("reads") or []
        for atom in atoms:
            name = f"{atom.get('qualified_class')}::{atom.get('identity')}"
            if atom.get("kind") != "member":
                return held(f"{atom.get('qualified_class')}: a {atom.get('kind')} change needs a witness this check "
                            "does not have yet")
            if not any(all(read.get(key) == atom.get(key) for key in ("header", "qualified_class", "kind", "identity"))
                       and read.get("observed") == atom.get("after") and read.get("operation") == "access"
                       for read in reads if isinstance(read, dict)):
                return held(f"{name} moved; it needs a newly matched function that uses it")
    return {"state": "pass", "message": "Every changed layout is unchanged in shape or used by a new match."}


def from_admission(status, wide):
    """H10, the wide budget, from the bot's BFME II / Admission status on this head and the H1 row already composed.
    It never fails: over budget, a header change waits and is retried automatically."""
    if (wide or {}).get("state") in ("pass", "fail"):
        return {"state": "pass", "message": "The wide check ran on this main."}
    text = (status or {}).get("description") or ""
    if (status or {}).get("state") == "success" and text.startswith(WIDE_ADMITTED):
        return {"state": "pass", "message": "The wide check was admitted within the daily budget."}
    if text.startswith(DAILY_LIMIT):
        return {"state": "held", "message": "daily limit for wide checks reached; retried automatically",
                "remedy": "Nothing to do: the wide check starts when the daily budget allows."}
    if text.startswith("Waiting for a maintainer"):
        return {"state": "held", "message": "a maintainer starts the wide check for header changes",
                "remedy": "Nothing to do: header changes are started by a maintainer while automatic headers are off."}
    return {"state": "held", "message": "no wide check admitted for this commit yet",
            "remedy": "Nothing to do: admission runs on every push and hourly."}


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
