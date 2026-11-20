"""Render a measured project progress card from exact protected repository artifacts."""
from collections import defaultdict
from datetime import date
from pathlib import PurePosixPath
import re

from finished_index import Owners, RealHeaders
from progress_delta import drafts_in_use, states
from state_snapshot import authoritative_units, OID, SHA

HISTORY_LIMIT = 45
RUNTIME_FIELDS = ("starts", "menu", "skirmish", "simulation_equal", "save_load")
MEASURES = (("Code matched · owned bytes", "matched_bytes"), ("Code proven · owned bytes", "proven_bytes"),
            ("Linking · required names provided", "link_symbols"), ("Finished · owned functions", "finished_rows"))


def subsystem(tu):
    parts = PurePosixPath(tu).parts if tu else ()
    if len(parts) > 5 and parts[:2] == ("src", "Code"):
        if parts[2] in {"GameEngine", "GameEngineDevice"} and parts[3] == "Source":
            return parts[2] + " / " + parts[4]
        return parts[2]
    return parts[1] if len(parts) > 2 else "Unplaced"


def acceptable_pair(value):
    return (isinstance(value, list) and len(value) == 2 and all(type(n) is int for n in value)
            and 0 <= value[0] <= value[1] and value[1] > 0)


def card_measure(git, pin, state, definitions, runtime=None):
    if not OID.fullmatch(pin) or state["sha"] != pin or not SHA.fullmatch(state["checker"]):
        raise ValueError("Measure the progress card from one exact protected main snapshot.")
    if sorted(state["tus"]) != authoritative_units(git.path, pin):
        raise ValueError("The progress state is incomplete. Keep the last dated card.")
    owners = Owners(git, pin)
    headers = RealHeaders(git, pin, definitions)
    matched, proven = states(state["tus"], owners.path)
    by_component = defaultdict(lambda: [0, 0])
    counts = {"matched_bytes": [0, 0], "proven_bytes": [0, 0], "finished_rows": [0, 0]}
    for rva, (source, name, size) in owners.functions.items():
        if type(size) is not int or size < 0:
            raise ValueError("An owned function is missing its exact reference size.")
        counts["matched_bytes"][1] += size
        counts["proven_bytes"][1] += size
        counts["finished_rows"][1] += 1
        group = by_component[subsystem(source)]
        group[1] += size
        if rva in matched:
            counts["matched_bytes"][0] += size
            group[0] += size
        if rva in proven:
            counts["proven_bytes"][0] += size
            if headers.ready(source, name):
                counts["finished_rows"][0] += 1
    runtime = runtime if isinstance(runtime, dict) and runtime.get("sha") == pin else {}
    pair = runtime.get("provided_required_symbols")
    flags = {field: runtime.get(field) if type(runtime.get(field)) is bool else None
             for field in RUNTIME_FIELDS}
    frames = runtime.get("equal_frames")
    frames = frames if type(frames) is int and frames > 0 and flags["simulation_equal"] is True else None
    return {"sha": pin, "checker": state["checker"], **counts,
            "link_symbols": pair if acceptable_pair(pair) else None,
            "runtime": flags, "equal_frames": frames, "components": dict(by_component),
            "drafts_in_use": drafts_in_use(git, pin)}


def ratio(value):
    return 100 * value[0] / value[1] if acceptable_pair(value) else None


def bar(value):
    pct = ratio(value)
    if pct is None:
        return "Awaiting measurement"
    fill = round(pct / 5)
    return ("█" * fill + "░" * (20 - fill) + f"  {pct:.1f}%"
            + f"  ({value[0]:,} of {value[1]:,})")


def current_card(day, measurement, previous):
    parsed = date.fromisoformat(day)
    if parsed.isoformat() != day:
        raise ValueError("Use a UTC calendar date for the progress card.")
    before = previous.get("history", [])
    history = {row["date"]: row for row in before if date.fromisoformat(row["date"]) < parsed}
    stage = {"date": day, **measurement}
    history[day] = {label: stage[label] for label in ("date", "sha", *(key for _, key in MEASURES))}
    return {"schema": 1, "current": stage, "history": [history[d] for d in sorted(history)[-HISTORY_LIMIT:]]}


def markdown(card):
    item = card["current"]
    lines = ["# BFME II progress", "", f"Measured {item['date']} UTC on {item['sha'][:12]}.", "",
             "| Measure | Progress |", "| --- | --- |"]
    lines.extend(f"| {label} | {bar(item[key])} |" for label, key in MEASURES)
    lines += ["", "A finished function is matched and proven, lives in a named file, and for a member function has exactly one reachable canonical class definition outside Draft.",
              "", "## Nightly runtime", ""]
    frames = item["equal_frames"]
    runtime_labels = ("Starts", "Reaches the menu", "Plays a skirmish",
                      f"Matches the reference for {frames:,} frames" if frames else "Matches the reference simulation",
                      "Saves and loads")
    for label, key in zip(runtime_labels, RUNTIME_FIELDS):
        result = item["runtime"][key]
        text = "Passed" if result is True else "Failed" if result is False else "Awaiting this revision"
        lines.append(f"- {label} · {text}")
    lines += ["", "## Matched code by subsystem", "", "| Subsystem | Owned bytes |", "| --- | --- |"]
    for label, value in sorted(item["components"].items()):
        if not re.fullmatch(r"[A-Za-z0-9_.+ /-]{1,100}", label):
            raise ValueError("The ledger uses an unsupported subsystem label.")
        lines.append(f"| {label} | {bar(value)} |")
    lines += ["", f"Draft headers in use · {item['drafts_in_use']:,}", "", "## Progress over time", ""]
    points = [row for row in card["history"] if ratio(row["matched_bytes"]) is not None]
    if len(points) > 1:
        dates = ", ".join(row["date"] for row in points)
        percentages = ", ".join(f"{ratio(row['matched_bytes']):.2f}" for row in points)
        fence = chr(96) * 3
        lines += [fence + "mermaid", "xychart-beta", '    title "Owned code bytes matched"',
                  f"    x-axis [{dates}]", '    y-axis "Percent" 0 --> 100',
                  f"    line [{percentages}]", fence, "",
                  "| Date (UTC) | Matched |", "| --- | ---: |"]
        lines.extend(f"| {row['date']} | {ratio(row['matched_bytes']):.2f}% |" for row in points)
    else:
        lines.append("The trend appears once measurements exist on two dates.")
    return "\n".join(lines) + "\n"

