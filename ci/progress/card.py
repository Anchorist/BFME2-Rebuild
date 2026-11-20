"""Write the progress card (PROGRESS.md, progress.svg, history.svg, history.json, card.json).

    python3 -B ci/progress/card.py --checkout . --state-dir STATE --nightly NIGHTLY.json|'' \
        --previous-history HISTORY.json|'' --out OUT

Inputs, and nothing else: the `state` branch (verdicts per function for one main commit),
the ledger and source tree of that same main commit (`config/map.json`, `src/`, `include/`),
the nightly result (`nightly` branch, `latest.json`; optional), and the previous history.
The figures are computed by `ci/managed-state/progress_card.card_measure` (the formulas the
pull-request report uses); this file only arranges them for readers. Every formula is in
`ci/progress/README.md`. Same inputs give the same bytes: the date shown is the main commit's.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CI = HERE.parent
for extra in (CI / "managed-state", CI / "managed-check", CI / "state"):
    sys.path.insert(1, str(extra))

from gitrepo import Git  # noqa: E402  (ci/managed-state)
from progress_card import card_measure, subsystem  # noqa: E402,F401
from source_definitions import global_class_defs  # noqa: E402
from layout import Refused, canonical, join  # noqa: E402  (ci/state)

HISTORY_LIMIT = 2000
BARS = (
    ("matched", "Code matched",
     "Share of the original program's code, by bytes, that our source compiles back to exactly."),
    ("proven", "Code proven",
     "Share of the code, by bytes, whose match the checker could also prove (relocations and data references agree)."),
    ("linking", "Linking",
     "Share of the names a full link of the game needs that our source already provides."),
    ("finished", "Finished functions",
     "Functions that are matched, proven, live in a properly named file, and whose class is declared in a real header."),
)
CHECKLIST = (
    ("starts", "Starts"),
    ("menu", "Reaches the main menu"),
    ("skirmish", "Plays a skirmish"),
    ("simulation_equal", "Equals the original game"),
    ("save_load", "Saves and loads"),
)


def pct(pair):
    return None if not pair or not pair[1] else 100.0 * pair[0] / pair[1]


def main_date(checkout, sha):
    raw = subprocess.check_output(["git", "-C", str(checkout), "show", "-s", "--format=%ct", sha], text=True)
    return datetime.fromtimestamp(int(raw), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def nightly_view(nightly):
    """The nightly result reduced to what the card shows; None when it has not run."""
    if not isinstance(nightly, dict) or not nightly.get("sha"):
        return None
    flags = {key: nightly.get(key) if type(nightly.get(key)) is bool else None for key, _ in CHECKLIST}
    frames = nightly.get("equal_frames")
    pair = nightly.get("provided_required_symbols")
    ok_pair = (isinstance(pair, list) and len(pair) == 2 and all(type(n) is int for n in pair)
               and 0 <= pair[0] <= pair[1] and pair[1] > 0)
    return {"sha": str(nightly["sha"])[:40], "date": str(nightly.get("date", ""))[:25], **flags,
            "equal_frames": frames if type(frames) is int and frames > 0 else None,
            "control_caught": nightly.get("control_caught") if type(nightly.get("control_caught")) is bool else None,
            "linking": pair if ok_pair else None}


def measure(checkout, state, nightly):
    git = Git(Path(checkout) / ".git")
    raw = card_measure(git, state["sha"], state, global_class_defs, None)
    night = nightly_view(nightly)
    return {"main": state["sha"], "date": main_date(checkout, state["sha"]),
            "matched": raw["matched_bytes"], "proven": raw["proven_bytes"], "finished": raw["finished_rows"],
            "linking": night["linking"] if night else None,
            "subsystems": {k: list(v) for k, v in sorted(raw["components"].items())},
            "drafts_in_use": raw["drafts_in_use"], "nightly": night}


def history_with(previous, point):
    rows = {row["main"]: row for row in previous if isinstance(row, dict) and "main" in row}
    rows[point["main"]] = {key: point[key] for key in ("main", "date", "matched", "proven", "linking", "finished")}
    ordered = sorted(rows.values(), key=lambda r: (r["date"], r["main"]))
    return ordered[-HISTORY_LIMIT:]


def drops(history, point):
    """Lines naming every headline count that is lower than at the previous main measured."""
    earlier = [row for row in history if row["main"] != point["main"] and row["date"] <= point["date"]]
    if not earlier:
        return []
    before = earlier[-1]
    lines = []
    for key, label, _ in BARS:
        old, new = before.get(key), point.get(key)
        if old and new and new[0] < old[0]:
            lines.append(f"{label}: expected at least {old[0]:,} (main {before['main'][:12]}, {before['date']}), "
                         f"found {new[0]:,} (main {point['main'][:12]}, {point['date']})")
    return lines


def figure(pair, unit):
    value = pct(pair)
    if value is None:
        return "not measured yet"
    return f"{value:.1f}% ({pair[0]:,} of {pair[1]:,} {unit})"


def text_bar(pair):
    value = pct(pair)
    if value is None:
        return "`░░░░░░░░░░░░░░░░░░░░`"
    fill = int(round(value / 5))
    return "`" + "█" * fill + "░" * (20 - fill) + "`"


def markdown(point, history):
    units = {"matched": "bytes", "proven": "bytes", "linking": "names", "finished": "functions"}
    lines = ["# Progress", "",
             f"Measured on main commit `{point['main'][:12]}` ({point['date']}). "
             "This page is written by a workflow from the measurements alone; nobody edits it.", "",
             "![Progress](progress.svg)", ""]
    for key, label, meaning in BARS:
        lines += [f"**{label}**: {text_bar(point[key])} {figure(point[key], units[key])}  ", meaning, ""]
    lines += ["## Does the rebuilt game run?", ""]
    night = point["nightly"]
    if night is None:
        lines += ["The nightly build has not run yet. Each line below will say passed or failed once it has.", ""]
        lines += [f"- {label}: not run yet" for _, label in CHECKLIST]
    else:
        lines += [f"Nightly build of main commit `{night['sha'][:12]}` ({night['date'] or 'date not given'}).", ""]
        for key, label in CHECKLIST:
            if key == "simulation_equal" and night["equal_frames"]:
                label = f"Equals the original game for {night['equal_frames']:,} frames"
            result = night[key]
            lines.append(f"- {label}: " + ("passed" if result is True else "failed" if result is False else "not run yet"))
        if night["control_caught"] is False:
            lines.append("- Warning: the deliberately changed control run was not caught, so the comparison above cannot be trusted tonight.")
    lines += ["", "## By part of the game", "",
              "Code matched, by bytes, in each part of the source tree.", "",
              "| Part | Matched | |", "| --- | ---: | --- |"]
    for name, pair in point["subsystems"].items():
        lines.append(f"| {name} | {figure(pair, 'bytes')} | {text_bar(pair)} |")
    lines += ["", f"Provisional (Draft) headers still included by source: {point['drafts_in_use']:,}.", "",
              "## Over time", "", "![Progress over time](history.svg)", "",
              "| Main commit | Date (UTC) | Matched | Proven | Linking | Finished |",
              "| --- | --- | ---: | ---: | ---: | ---: |"]
    for row in reversed(history[-30:]):
        cells = [f"{pct(row[k]):.2f}%" if pct(row.get(k)) is not None else "—"
                 for k in ("matched", "proven", "linking", "finished")]
        lines.append(f"| `{row['main'][:12]}` | {row['date']} | " + " | ".join(cells) + " |")
    lines += ["", "How each figure is computed: [ci/progress/README.md](https://github.com/Open-BFME/BFME2-Rebuild/blob/main/ci/progress/README.md).", ""]
    return "\n".join(lines)


STYLE = """<style>
.bg{fill:#fcfcfb}.t1{fill:#0b0b0b}.t2{fill:#52514e}.track{fill:#e4e3df}.fill{fill:#2a78d6}
.grid{stroke:#e4e3df;stroke-width:1}.s1{stroke:#2a78d6}.s2{stroke:#eb6834}.s3{stroke:#1baf7a}.s4{stroke:#eda100}
.d1{fill:#2a78d6}.d2{fill:#eb6834}.d3{fill:#1baf7a}.d4{fill:#eda100}
@media (prefers-color-scheme: dark){.bg{fill:#1a1a19}.t1{fill:#f0efec}.t2{fill:#c3c2b7}.track{fill:#383835}
.fill{fill:#3987e5}.grid{stroke:#383835}.s1{stroke:#3987e5}.s2{stroke:#d95926}.s3{stroke:#199e70}.s4{stroke:#c98500}
.d1{fill:#3987e5}.d2{fill:#d95926}.d3{fill:#199e70}.d4{fill:#c98500}}
text{font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif}
</style>"""


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def bars_svg(point):
    width, row = 640, 46
    height = 40 + row * len(BARS)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Progress: four bars">',
           STYLE, f'<rect class="bg" width="{width}" height="{height}" rx="6"/>',
           f'<text class="t2" x="16" y="24" font-size="12">Main {point["main"][:12]} · {point["date"][:10]}</text>']
    for i, (key, label, _) in enumerate(BARS):
        y = 40 + i * row
        value = pct(point[key])
        shown = "not measured yet" if value is None else f"{value:.1f}%"
        out.append(f'<text class="t1" x="16" y="{y + 14}" font-size="14" font-weight="600">{esc(label)}</text>')
        out.append(f'<text class="t1" x="{width - 16}" y="{y + 14}" font-size="14" text-anchor="end">{shown}</text>')
        out.append(f'<rect class="track" x="16" y="{y + 22}" width="{width - 32}" height="10" rx="4"/>')
        if value:
            w = max(4.0, (width - 32) * value / 100)
            out.append(f'<rect class="fill" x="16" y="{y + 22}" width="{w:.1f}" height="10" rx="4"/>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def history_svg(history):
    width, height, left, right, top, bottom = 640, 260, 44, 110, 20, 36
    plot_w, plot_h = width - left - right, height - top - bottom
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Progress over time, percent">',
           STYLE, f'<rect class="bg" width="{width}" height="{height}" rx="6"/>']
    for tick in (0, 25, 50, 75, 100):
        y = top + plot_h * (1 - tick / 100)
        out.append(f'<line class="grid" x1="{left}" x2="{left + plot_w}" y1="{y:.1f}" y2="{y:.1f}"/>')
        out.append(f'<text class="t2" x="{left - 6}" y="{y + 4:.1f}" font-size="11" text-anchor="end">{tick}%</text>')
    points = history[-365:]
    if len(points) < 2:
        out.append(f'<text class="t2" x="{left + plot_w / 2}" y="{top + plot_h / 2}" font-size="13" text-anchor="middle">The chart starts once two main commits are measured.</text>')
    else:
        stamps = [datetime.strptime(r["date"], "%Y-%m-%dT%H:%M:%SZ").timestamp() for r in points]
        lo, hi = stamps[0], max(stamps[-1], stamps[0] + 1)
        x = lambda s: left + plot_w * (s - lo) / (hi - lo)  # noqa: E731
        out.append(f'<text class="t2" x="{left}" y="{height - 12}" font-size="11">{points[0]["date"][:10]}</text>')
        out.append(f'<text class="t2" x="{left + plot_w}" y="{height - 12}" font-size="11" text-anchor="end">{points[-1]["date"][:10]}</text>')
        labels = []
        for n, (key, label, _) in enumerate(BARS, 1):
            series = [(x(s), pct(r.get(key))) for s, r in zip(stamps, points) if pct(r.get(key)) is not None]
            if not series:
                continue
            path = " ".join(f"{'M' if i == 0 else 'L'}{px:.1f},{top + plot_h * (1 - v / 100):.1f}" for i, (px, v) in enumerate(series))
            out.append(f'<path class="s{n}" d="{path}" fill="none" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
            labels.append([top + plot_h * (1 - series[-1][1] / 100), n, label])
        labels.sort()
        for i in range(1, len(labels)):  # keep end labels at least 14 px apart
            labels[i][0] = max(labels[i][0], labels[i - 1][0] + 14)
        for y, n, label in labels:
            out.append(f'<rect class="d{n}" x="{left + plot_w + 8}" y="{y - 4:.1f}" width="8" height="8" rx="2"/>')
            out.append(f'<text class="t1" x="{left + plot_w + 20}" y="{y + 4:.1f}" font-size="11">{esc(label)}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def build(checkout, state_read, nightly, previous_history):
    state = join(state_read)
    point = measure(checkout, state, nightly)
    history = history_with(previous_history, point)
    return {
        "card.json": canonical(point),
        "history.json": canonical(history),
        "PROGRESS.md": markdown(point, history).encode(),
        "progress.svg": bars_svg(point).encode(),
        "history.svg": history_svg(history).encode(),
    }, drops(history, point)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", default=".")
    parser.add_argument("--state-dir", required=True, help="a checkout or export of the state branch")
    parser.add_argument("--nightly", default="")
    parser.add_argument("--previous-history", default="")
    parser.add_argument("--out", required=True)
    parser.add_argument("--drops", default="", help="file to write lines naming figures that went down")
    args = parser.parse_args()
    root = Path(args.state_dir)
    try:
        nightly = json.loads(Path(args.nightly).read_bytes()) if args.nightly and Path(args.nightly).is_file() else None
        previous = json.loads(Path(args.previous_history).read_bytes()) \
            if args.previous_history and Path(args.previous_history).is_file() else []
        files, down = build(args.checkout, lambda p: (root / p).read_bytes(), nightly, previous)
    except (Refused, ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"::error::progress card: expected a complete state and ledger for one main commit, found: {error}")
        return 1
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (out / name).write_bytes(data)
    point = json.loads(files["card.json"])
    print(f"Progress card for main {point['main']}: matched {figure(point['matched'], 'bytes')}, "
          f"proven {figure(point['proven'], 'bytes')}, finished {figure(point['finished'], 'functions')}, "
          f"linking {figure(point['linking'], 'names')}.")
    if args.drops:
        Path(args.drops).write_text("".join(line + "\n" for line in down))
    for line in down:
        print(f"::warning::went down: {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
