"""The front-page progress picture (progress.svg): the approved README design, drawn from measurements.

With every figure present, `card()` returns exactly the bytes of the approved design for the same
numbers (tests/design-reference.svg). A figure that is not measured yet is drawn as a dash with a
plain caption instead of a number; nothing is ever estimated.
"""

STYLE = """
.card{fill:#0d1117;stroke:#30363d}.box{fill:#161b22;stroke:#30363d}.track{fill:#21262d}
.strong{fill:#f0f6fc}.muted{fill:#8b949e}.blue{fill:#3987e5}.orange{fill:#d95926}.green{fill:#3fb950}.red{fill:#f85149}
.sblue{stroke:#3987e5}.sgreen{stroke:#3fb950}.sred{stroke:#f85149}.smuted{stroke:#8b949e}.srule{stroke:#30363d}
.fgreen{fill:#0f2a17;stroke:#3fb950}.fdash{fill:none;stroke:#8b949e}
text{font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif}
@media (prefers-color-scheme: light){
.card{fill:#ffffff;stroke:#d0d7de}.box{fill:#f6f8fa;stroke:#d0d7de}.track{fill:#eaeef2}
.strong{fill:#1f2328}.muted{fill:#59636e}.blue{fill:#2a78d6}.orange{fill:#eb6834}.green{fill:#1a7f37}.red{fill:#cf222e}
.sblue{stroke:#2a78d6}.sgreen{stroke:#1a7f37}.sred{stroke:#cf222e}.smuted{stroke:#59636e}.srule{stroke:#d0d7de}
.fgreen{fill:#e6f4ea;stroke:#1a7f37}.fdash{stroke:#59636e}}
"""
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def svg(w, h, label, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="{label}">\n<style>{STYLE}</style>\n'
            f'<rect class="card" x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12"/>\n{body}\n</svg>\n')


def short_date(day):
    """2026-11-20 -> 20 Nov 2026."""
    year, month, date = (int(part) for part in day[:10].split("-"))
    return f"{date} {MONTHS[month - 1]} {year}"


def card(byte_pct, link_pair, finished, files_equal, date, files_compiled=3253):
    """byte_pct: float; link_pair: (provided, needed) or None; finished: (done, total);
    files_equal: int or None; date: '20 Nov 2026'; files_compiled: int or None."""
    link_pct = 100.0 * link_pair[0] / link_pair[1] if link_pair else None
    bw = 352

    def panel(x, title, pct, caption):
        if pct is None:
            return f'''<rect class="box" x="{x}" y="92" width="400" height="150" rx="10"/>
<text class="muted" x="{x+24}" y="122" font-size="12" font-weight="600" letter-spacing="1.4">{title}</text>
<text class="muted" x="{x+24}" y="178" font-size="54" font-weight="700">—</text>
<text class="muted" x="{x+24}" y="204" font-size="13">{caption}</text>
<rect class="track" x="{x+24}" y="216" width="{bw}" height="10" rx="5"/>'''
        fill = max(6, bw * pct / 100)
        return f'''<rect class="box" x="{x}" y="92" width="400" height="150" rx="10"/>
<text class="muted" x="{x+24}" y="122" font-size="12" font-weight="600" letter-spacing="1.4">{title}</text>
<text class="strong" x="{x+24}" y="178" font-size="54" font-weight="700">{pct:.1f}%</text>
<text class="muted" x="{x+24}" y="204" font-size="13">{caption}</text>
<rect class="track" x="{x+24}" y="216" width="{bw}" height="10" rx="5"/>
<rect class="blue" x="{x+24}" y="216" width="{fill:.1f}" height="10" rx="5"/>'''

    def stat(x, big, small1, small2):
        return f'''<text class="strong" x="{x}" y="286" font-size="24" font-weight="700">{big}</text>
<text class="muted" x="{x}" y="306" font-size="12">{small1}</text>
<text class="muted" x="{x}" y="322" font-size="12">{small2}</text>'''

    if link_pair:
        link_caption = f"of the names a full game needs: {link_pair[0]:,} of {link_pair[1]:,}"
    else:
        link_caption = "not measured yet; the daily build will report it"
    equal_big = f"{files_equal}" if files_equal is not None else "—"
    equal_second = "inside the original game" if files_equal is not None else "inside the original game (not run yet)"
    compiled_big = f"{files_compiled:,}" if files_compiled is not None else "—"
    compiled_second = ("compared with the game every day" if files_compiled is not None
                       else "compared with the game every day (not run yet)")
    body = f'''<text class="muted" x="28" y="36" font-size="12" font-weight="600" letter-spacing="1.4">BATTLE FOR MIDDLE-EARTH II · REBUILD</text>
<text class="muted" x="852" y="36" font-size="12" text-anchor="end">{date} · measured by machine, daily at noon ET</text>
<text class="strong" x="28" y="68" font-size="22" font-weight="700">Road to a game built from source</text>
{panel(28, "BYTE MATCH", byte_pct, "of the original program, rebuilt byte for byte")}
{panel(452, "LINKING", link_pct, link_caption)}
{stat(28, f"{finished[0]:,}", f"functions finished,", f"of {finished[1]:,}")}
{stat(310, equal_big, "rebuilt files play identically", equal_second)}
{stat(592, compiled_big, "source files compiled and", compiled_second)}'''
    link_words = f"linking {link_pct:.1f} percent" if link_pct is not None else "linking not measured yet"
    equal_words = (f"{files_equal} rebuilt files play identically inside the original game" if files_equal is not None
                   else "the game run has not run yet")
    return svg(880, 344, f"Byte match {byte_pct:.1f} percent, {link_words}, {finished[0]} of {finished[1]} "
               f"functions finished, {equal_words}", body)


def from_point(point):
    """The picture for one card measurement (card.measure)."""
    night = point.get("nightly") or {}
    equal = None
    if night.get("simulation_equal") is True and type(night.get("files_substituted")) is int:
        equal = night["files_substituted"]
    # Only the daily build compiles every file; the state may carry files without compiling them.
    compiled = night.get("compiled") if type(night.get("compiled")) is int else None
    byte_pct = 100.0 * point["matched"][0] / point["matched"][1]
    return card(byte_pct, point["linking"], tuple(point["finished"]), equal, short_date(point["measured"]),
                compiled)
