"""Draw experiment 002 banners: one chart per framing, the same content in each of the three designs.

Usage (normally called by experiments/002-design-framing-time/build_versions.py):
    python scripts/banner002.py spotlights/NN-slug F DESIGN      # writes versions/F/banner.dc.html

The three designs differ only in frame, type and palette (PREREGISTRATION.md, "Arms"): template D on a dark ground,
template D on a light ground, and Ink (identity 5, layout v2). The words are the same in all three: series line,
headline with one phrase in the design's signal colour, an evidence line, the chart's labels and the footer.
Charts are drawn to scale from stats.json. Rules kept from layout v2: no y-axis numbers or gridlines (the baseline
stays), first and latest years only on time axes, at most four annotations at 28 px, axis labels 20 to 22 px. The one
exception is the ranked-gap chart (gap_columns), which states what a bar is and carries values in points (review round 1).

Footer (review round 1, 2 Nov 2026): no byline; left-aligned; the data line (source, series code, extraction date),
"Data and code: @jpazvd on GitHub", and a Notes line that defines every acronym shown on the banner (ACRONYMS), except
the names of agencies, organizations and monitoring programmes, and "SDG" (JP, 2 Nov 2026).
"""
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
W = 1088
STYLES = {  # as docs/identity-2026-10/tools/make_v2.py
    "Ink": dict(ground="#FFFFFF", ink="#000000", data="#000000", signal="#B3126B", grey="#5B6470", light="#B8BEC6",
                band="#F2F2F2", base="#000000", byline="#3F454D", rule="#000000", evidence="#3F454D"),
    "D-light": dict(ground="#F4F6F7", ink="#101820", data="#0B6E99", signal="#B4531A", grey="#56626C", light="#B9C6CE",
                    band="#E6EBEE", base="#9AA6AF", byline="#3E4A54", rule="#C9D1D6", evidence="#3E4A54"),
    "D-dark": dict(ground="#0D2433", ink="#FFFFFF", data="#4FC3E8", signal="#F2A541", grey="#8FB3C7", light="#3B5A6D",
                   band="#12313F", base="#3B5A6D", byline="#C9D8E1", rule="#23465B", evidence="#C9D8E1"),
}
CHART_H = {"Ink": 262, "D-light": 252, "D-dark": 252}
FONT = "IBM Plex Sans, Arial, sans-serif"
HANDLE = "@jpazvd"
ACRONYMS = {  # defined in the footer's Notes line when they appear in the banner's visible text, in order of appearance
    "LDCs": "least developed countries", "LDC": "least developed country",
    "LLDCs": "landlocked developing countries", "LLDC": "landlocked developing country",
    "SIDS": "small island developing states",
    "NEET": "not in education, employment or training",
    "DTP3": "third dose of diphtheria, tetanus and pertussis vaccine",
    "DTP": "diphtheria, tetanus and pertussis vaccine",
    "MCV2": "second dose of measles-containing vaccine",
    "PCV3": "third dose of pneumococcal conjugate vaccine",
    "HPV": "human papillomavirus",
    "HIV": "human immunodeficiency virus",
    "MPI": "multidimensional poverty index",
    "NZ": "New Zealand",
}
NOT_DEFINED = {"UN", "WHO", "UNICEF", "UNESCO", "ILO", "UNFPA", "UNAIDS", "UNDP", "SDG", "SDGS",  # agencies and SDGs
               "JMP", "UIS", "JME", "IGME", "MMEIG", "WUENIC", "DESA", "IPU", "GHO", "DHS", "MICS"}  # programmes, bodies


def visible_text(*parts):
    """Plain text of the given strings and SVG fragments (tags and the aria-label attribute removed)."""
    out = []
    for p_ in parts:
        p_ = re.sub(r'aria-label="[^"]*"', "", str(p_ or ""))
        out.append(html.unescape(re.sub(r"<[^>]+>", " ", p_)))
    return " ".join(out)


def acronym_notes(text_):
    """'LDCs, least developed countries; ...' for the acronyms in text_, in order of first appearance."""
    seen, found = set(), []
    for m in re.finditer(r"(?<![A-Za-z0-9_])([A-Z][A-Z0-9]*[A-Z0-9]s?)(?![A-Za-z0-9_])", text_):
        a = m.group(1)
        if a in seen or a.upper() in NOT_DEFINED:
            continue
        seen.add(a)
        if a in ACRONYMS:
            found.append(f"{a}, {ACRONYMS[a]}")
        elif not re.fullmatch(r"[A-Z]{1,2}\d?", a):  # two letters (or one and a digit) are not taken as acronyms
            raise ValueError(f"acronym {a!r} is shown on the banner but has no definition in banner002.ACRONYMS")
    return "; ".join(found)


def fmt(v, unit, nd=1):
    if v is None:
        return "n/a"
    s = f"{v:,.{nd}f}"
    return f"{s}%" if unit == "%" else f"{s}{unit}"


def num(v, nd=1):
    return f"{v:,.{nd}f}"


def esc(s):
    return html.escape(str(s), quote=True)


def svg_open(h, aria):
    return (f'<svg viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{esc(aria)}" '
            f'style="display: block; flex: 0 0 auto">')


def text(x, y, s, size=28, fill="#000", anchor="start", weight=600, extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}"{extra}>{esc(s)}</text>')


# ------------------------------------------------------------------ chart builders

def line_chart(st, h, lines, unit, target=None, aria="", labels=None):
    """lines: [{"pts": [[y, v], ...], "role": "lead"|"world"|"other", "label": str}]. target: dict with
    value, year, observed, required (per year), last (year, value) to draw the pace fan."""
    allpts = [p for l in lines for p in l["pts"]]
    y0 = min(p[0] for p in allpts)
    y1 = max(p[0] for p in allpts)
    ty = target["year"] if target else y1
    vals = [p[1] for p in allpts]
    if target:
        vals += [target["value"], target["proj"]]
    vmax = max(vals) * 1.12 if max(vals) > 0 else 1
    x0 = 70
    x1 = 730 if target else (760 if any(l.get("label") for l in lines if l["role"] != "lead") else 830)
    top, bottom = 30, h - 42
    X = lambda yr: x0 + (yr - y0) / max(1, (ty - y0)) * (x1 - x0)
    Y = lambda v: bottom - v / vmax * (bottom - top)
    out = [svg_open(h, aria)]
    if target:
        ly = target["last"][0]
        out.append(f'<rect x="{X(ly):.1f}" y="{top - 12}" width="{X(ty) - X(ly):.1f}" height="{bottom - top + 12}" fill="{st["band"]}"></rect>')
        out.append(text((X(ly) + X(ty)) / 2, top + 12, f"{ty - ly} years left", 22, st["grey"], "middle"))
    out.append(f'<line x1="{x0}" y1="{bottom}" x2="{x1}" y2="{bottom}" stroke="{st["base"]}" stroke-width="2"></line>')
    out.append(text(x0 - 14, bottom + 7, "0", 22, st["grey"], "end", 400))
    out.append(text(x0, bottom + 32, str(y0), 22, st["grey"], "middle", 400))
    out.append(text(X(y1), bottom + 32, str(y1), 22, st["grey"], "middle", 400))
    if target and ty != y1:
        out.append(text(x1, bottom + 32, str(ty), 22, st["ink"], "middle", 600))
    order = sorted(lines, key=lambda l: {"other": 0, "world": 1, "lead": 2}[l["role"]])
    for l in order:
        pts = " ".join(f"{X(y):.1f},{Y(v):.1f}" for y, v in l["pts"])
        col, wd = {"lead": (st["data"], 7), "world": (st["grey"], 4), "other": (st["light"], 3)}[l["role"]]
        out.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{wd}" stroke-linejoin="round" stroke-linecap="round"></polyline>')
    lead = next(l for l in lines if l["role"] == "lead")
    (ya, va), (yb, vb) = lead["pts"][0], lead["pts"][-1]
    out.append(f'<circle cx="{X(ya):.1f}" cy="{Y(va):.1f}" r="9" fill="{st["data"]}"></circle>')
    out.append(f'<circle cx="{X(yb):.1f}" cy="{Y(vb):.1f}" r="11" fill="{st["ground"]}" stroke="{st["data"]}" stroke-width="5"></circle>')
    lab_a = f"{fmt(va, unit)} in {ya}"
    lab_b = f"{fmt(vb, unit)} in {yb}"
    rising = vb > va
    # first label above the start point (below it if the line starts near the top); last label clear of the line
    # first label on the side away from where the line goes: above a falling start, below a rising one
    second = lead["pts"][1][1] if len(lead["pts"]) > 1 else vb
    ya_lab = Y(va) - 18 if second <= va else Y(va) + 40
    if ya_lab < top + 10:
        ya_lab = Y(va) + 40
    if ya_lab > bottom - 6:
        ya_lab = Y(va) - 18
    if labels and len(lines) > 2:  # several lines: put the first label under the lead's start, clear of the others
        ya_lab = Y(va) + 40 if Y(va) + 40 < bottom - 6 else Y(va) - 18
    out.append(text(X(ya) + 18, ya_lab, lab_a, 28, st["ink"]))
    if target:
        out.append(text(X(yb) - 18, Y(vb) + (-22 if rising else 44), lab_b, 28, st["ink"], "end"))
        yp, yt = Y(target["proj"]), Y(target["value"])
        if abs(yp - yt) < 40:
            yp, yt = (yp - 20, yt + 20) if yp < yt else (yp + 20, yt - 20)
        out.append(f'<line x1="{X(yb):.1f}" y1="{Y(vb):.1f}" x2="{x1}" y2="{Y(target["proj"]):.1f}" stroke="{st["data"]}" stroke-width="4" stroke-dasharray="3 10" stroke-linecap="round"></line>')
        out.append(f'<line x1="{X(yb):.1f}" y1="{Y(vb):.1f}" x2="{x1}" y2="{Y(target["value"]):.1f}" stroke="{st["signal"]}" stroke-width="5" stroke-dasharray="14 9"></line>')
        out.append(f'<circle cx="{x1}" cy="{Y(target["proj"]):.1f}" r="8" fill="{st["ground"]}" stroke="{st["data"]}" stroke-width="4"></circle>')
        out.append(f'<circle cx="{x1}" cy="{Y(target["value"]):.1f}" r="10" fill="{st["signal"]}"></circle>')
        out.append(text(x1 + 22, yp + 10, target["proj_label"], 28, st["ink"]))
        out.append(text(x1 + 22, yt + 10, target["target_label"], 28, st["signal"]))
    else:
        out.append(text(X(yb) + 22, Y(vb) + 10, lab_b, 28, st["ink"]))
        if labels:
            for l in lines:
                if l["role"] == "world":
                    (_, wv) = l["pts"][-1]
                    yy = Y(wv) + 8
                    if abs(yy - (Y(vb) + 10)) < 30:
                        yy += 30 if yy > Y(vb) else -30
                    out.append(text(X(l["pts"][-1][0]) + 22, yy, f"World {fmt(wv, unit)}", 22, st["grey"], weight=600))
        lab = lead.get("label")
        if lab:
            out.append(text(X(yb) + 22, Y(vb) + 40, lab, 22, st["data"], weight=600))
    out.append("</svg>")
    return "\n".join(out)


def hbars(st, h, rows, unit, aria="", ref=None, pair=None, legend=None, value_fmt=None, target_line=None):
    """rows: [{"label", "value", "role": "lead"|"other", "value2"?}]. pair: draw value2 as a second thin bar."""
    n = len(rows)
    lab_w = 330
    x0, x1 = lab_w + 12, W - 150
    top = 36 if legend else 6
    row_h = (h - top - 6) / n
    vals = [r["value"] for r in rows] + [r.get("value2") or 0 for r in rows]
    if target_line is not None:
        vals.append(target_line[1])
    vmax = max(vals) * 1.05 if max(vals) > 0 else 1
    X = lambda v: x0 + max(0, v) / vmax * (x1 - x0)
    vf = value_fmt or (lambda v: fmt(v, unit))
    out = [svg_open(h, aria)]
    if legend:
        out.append(f'<rect x="{x0}" y="6" width="22" height="16" fill="{st["data"]}"></rect>')
        out.append(text(x0 + 30, 21, legend[0], 22, st["ink"], weight=600))
        if pair:
            lx = x0 + 40 + 11.5 * len(legend[0]) + 30
            out.append(f'<rect x="{lx:.1f}" y="6" width="22" height="16" fill="{st["signal"]}"></rect>')
            out.append(text(lx + 30, 21, legend[1], 22, st["ink"], weight=600))
    for i, r in enumerate(rows):
        yc = top + row_h * (i + 0.5)
        lead = r.get("role") == "lead"
        col = st["data"] if lead or pair else st["light"] if r.get("role") == "other" else st["grey"]
        if r.get("role") == "world" and not pair:
            col = st["grey"]
        bh = min(30, row_h * 0.62) if not pair else min(16, row_h * 0.36)
        out.append(text(lab_w, yc + 7, r["label"], 22, st["ink"] if lead or r.get("role") == "world" else st["grey"], "end",
                        600 if lead or r.get("role") == "world" else 400))
        if pair:
            out.append(f'<rect x="{x0}" y="{yc - bh - 1:.1f}" width="{X(r["value"]) - x0:.1f}" height="{bh:.1f}" fill="{st["data"]}"></rect>')
            out.append(f'<rect x="{x0}" y="{yc + 1:.1f}" width="{X(r["value2"]) - x0:.1f}" height="{bh:.1f}" fill="{st["signal"]}"></rect>')
            if row_h >= 40:
                out.append(text(X(r["value"]) + 8, yc - 3, vf(r["value"]), 20, st["ink"], weight=600))
                out.append(text(X(r["value2"]) + 8, yc + bh - 1, vf(r["value2"]), 20, st["signal"], weight=600))
            else:  # rows too tight for two labels: one label, both values, after the longer bar
                xe = max(X(r["value"]), X(r["value2"])) + 8
                out.append(f'<text x="{xe:.1f}" y="{yc + 7:.1f}" font-family="{FONT}" font-size="20" font-weight="600">'
                           f'<tspan fill="{st["ink"]}">{esc(vf(r["value"]))}</tspan><tspan fill="{st["grey"]}"> / </tspan>'
                           f'<tspan fill="{st["signal"]}">{esc(vf(r["value2"]))}</tspan></text>')
        else:
            out.append(f'<rect x="{x0}" y="{yc - bh / 2:.1f}" width="{X(r["value"]) - x0:.1f}" height="{bh:.1f}" fill="{col}"></rect>')
            out.append(text(X(r["value"]) + 10, yc + 8, vf(r["value"]), 22, st["ink"] if lead else st["grey"],
                            weight=600 if lead else 400))
    out.append(f'<line x1="{x0}" y1="{top - 4}" x2="{x0}" y2="{h - 2}" stroke="{st["base"]}" stroke-width="2"></line>')
    if target_line is not None:
        tx = X(target_line[1])
        out.append(f'<line x1="{tx:.1f}" y1="{top - 4}" x2="{tx:.1f}" y2="{h - 2}" stroke="{st["signal"]}" stroke-width="3" stroke-dasharray="10 7"></line>')
    out.append("</svg>")
    return "\n".join(out)


def ranked_columns(st, h, values, aria="", ref=None, split=None, zero=False, notes=(), unit=""):
    """values: list of numbers, ranked high to low. split: index where colour changes (data | light).
    ref: (label, value) for a horizontal reference line. zero: values may be negative (gaps), baseline at 0."""
    n = len(values)
    x0, x1 = 50, W - 10
    top, bottom = 50, h - 34
    vmax = max(values + [ref[1] if ref else 0])
    vmin = min(values + [0]) if zero else 0
    span = (vmax - vmin) or 1
    Y = lambda v: bottom - (v - vmin) / span * (bottom - top)
    bw = (x1 - x0) / n
    out = [svg_open(h, aria)]
    for i, v in enumerate(values):
        col = st["data"] if (split is None or i < split) else st["light"]
        ya, yb = sorted((Y(v), Y(0)))
        out.append(f'<rect x="{x0 + i * bw + bw * 0.12:.1f}" y="{ya:.1f}" width="{bw * 0.76:.2f}" height="{max(1, yb - ya):.1f}" fill="{col}"></rect>')
    out.append(f'<line x1="{x0}" y1="{Y(0):.1f}" x2="{x1}" y2="{Y(0):.1f}" stroke="{st["base"]}" stroke-width="2"></line>')
    out.append(text(x0 - 10, Y(0) + 7, "0", 22, st["grey"], "end", 400))
    if ref:
        out.append(f'<line x1="{x0}" y1="{Y(ref[1]):.1f}" x2="{x1}" y2="{Y(ref[1]):.1f}" stroke="{st["ink"]}" stroke-width="2.5" stroke-dasharray="4 6"></line>')
        out.append(text(x1, Y(ref[1]) - 12, ref[0], 28, st["ink"], "end"))
    for (x_frac, y_val, s, col_key, anchor) in notes:
        out.append(text(x0 + x_frac * (x1 - x0), Y(y_val) if y_val is not None else top - 14, s, 28, st[col_key], anchor))
    out.append("</svg>")
    return "\n".join(out)


def signed(v, nd=1):
    return ("+" if v > 0 else "\u2212" if v < 0 else "") + num(abs(v), nd)


def gap_columns(st, h, rows, wa, wb, unit="%", aria="", nd=1):
    """One bar per country: rows are [name, year, a, b, a - b], ranked high to low. The chart says what a bar is,
    which way is which, and carries values in points (review round 1: 15-G, 19-G)."""
    n = len(rows)
    vals = [r[4] for r in rows]
    x0, x1 = 66, W - 6
    top, bottom = 76, h - 6
    vmax, vmin = max(vals + [0]), min(vals + [0])
    raw = (vmax - vmin) or 1
    step = next(s_ for s_ in (1, 2, 5, 10, 20, 25, 50, 100, 200) if raw / s_ <= 4)
    lo_t = (vmin // step) * step if -vmin >= 0.25 * step else 0  # no empty band for a sliver of bars on one side
    hi_t = -((-vmax) // step) * step if vmax >= 0.25 * step else 0
    span = (hi_t - lo_t) or 1
    Y = lambda v: bottom - (v - lo_t) / span * (bottom - top)
    bw = (x1 - x0) / n
    pts_word = "percentage points" if unit == "%" else unit.strip()
    out = [svg_open(h, aria),
           text(0, 22, f"Each bar is one country's latest survey: {wa} minus {wb}, in {pts_word}", 21, st["ink"], weight=600),
           text(0, 50, f"Above 0, {wa} higher; below 0, {wb} higher", 21, st["grey"], weight=400)]
    t = lo_t
    while t <= hi_t + 1e-9:
        if t != 0:
            out.append(f'<line x1="{x0}" y1="{Y(t):.1f}" x2="{x1}" y2="{Y(t):.1f}" stroke="{st["light"]}" stroke-width="1"></line>')
        out.append(text(x0 - 10, Y(t) + 7, signed(t, 0), 20, st["grey"], "end", 400))
        t += step
    for i, v in enumerate(vals):
        ya, yb = sorted((Y(v), Y(0)))
        out.append(f'<rect x="{x0 + i * bw + bw * 0.12:.1f}" y="{ya:.1f}" width="{bw * 0.76:.2f}" height="{max(1, yb - ya):.1f}" fill="{st["data"]}"></rect>')
    out.append(f'<line x1="{x0}" y1="{Y(0):.1f}" x2="{x1}" y2="{Y(0):.1f}" stroke="{st["base"]}" stroke-width="2"></line>')
    lo_i = min(range(n), key=lambda i: vals[i])
    hi_i = max(range(n), key=lambda i: vals[i])
    # The two extremes are named on the empty side of the zero line, next to their bars (the first and last bars).
    if vals[lo_i] < 0 and lo_t < 0:
        r = rows[lo_i]
        out.append(text(x1, Y(0) - 10, f"{r[0]}, {r[1]}: {signed(vals[lo_i], nd)}", 21, st["ink"], "end", 600))
    if vals[hi_i] > 0 and hi_i != lo_i:
        r = rows[hi_i]
        lab = f"{r[0]}, {r[1]}: {signed(vals[hi_i], nd)}"
        if lo_t < 0:
            out.append(text(x0 + 2, Y(0) + 26, lab, 21, st["ink"], "start", 600))
        else:
            out.append(text(x0 + hi_i * bw + bw * 0.94 + 8, max(Y(vals[hi_i]) - 8, top - 6), lab, 21, st["ink"], "start", 600))
    out.append("</svg>")
    return "\n".join(out)


def year_histogram(st, h, by_year, cutoff, aria="", note=None, show_stale=True):
    years = [y for y, _ in by_year]
    ymin, ymax = min(years), max(years)
    span = list(range(ymin, ymax + 1))
    counts = dict((y, n) for y, n in by_year)
    nmax = max(counts.values())
    x0, x1 = 50, W - 20
    top, bottom = 52, h - 40
    bw = (x1 - x0) / len(span)
    Y = lambda n: bottom - n / nmax * (bottom - top)
    out = [svg_open(h, aria)]
    for i, y in enumerate(span):
        n = counts.get(y, 0)
        if not n:
            continue
        col = st["signal"] if y <= cutoff else st["data"]
        out.append(f'<rect x="{x0 + i * bw + bw * 0.1:.1f}" y="{Y(n):.1f}" width="{bw * 0.8:.1f}" height="{bottom - Y(n):.1f}" fill="{col}"></rect>')
    out.append(f'<line x1="{x0}" y1="{bottom}" x2="{x1}" y2="{bottom}" stroke="{st["base"]}" stroke-width="2"></line>')
    ticks = sorted({ymin, ymax} | ({cutoff} if ymin < cutoff < ymax else set()))
    for y in ticks:
        out.append(text(x0 + (span.index(y) + 0.5) * bw, bottom + 30, str(y), 22,
                        st["ink"] if y == cutoff else st["grey"], "middle", 600 if y == cutoff else 400))
    if show_stale:
        out.append(text(x0, top - 18, f"latest value in {cutoff} or earlier", 22, st["signal"], weight=600))
    out.append(text(x1, top - 18, f"after {cutoff}", 22, st["data"], "end", 600))
    if note:
        out.append(note(x0, x1, top, bottom, bw, span))
    out.append("</svg>")
    return "\n".join(out)


def waffle(st, h, n_with, n_total, aria="", labels=("with data", "no data")):
    cols = 33
    rows = -(-n_total // cols)
    cell = min((W - 360) / cols, (h - 20) / rows)
    gap = cell * 0.18
    out = [svg_open(h, aria)]
    for i in range(n_total):
        r, c = divmod(i, cols)
        col = st["data"] if i < n_with else st["light"]
        out.append(f'<rect x="{c * cell:.1f}" y="{10 + r * cell:.1f}" width="{cell - gap:.1f}" height="{cell - gap:.1f}" fill="{col}"></rect>')
    lx = cols * cell + 30
    out.append(f'<rect x="{lx:.1f}" y="{h / 2 - 58:.1f}" width="26" height="26" fill="{st["data"]}"></rect>')
    out.append(text(lx + 38, h / 2 - 36, f"{n_with} {labels[0]}", 28, st["ink"]))
    out.append(f'<rect x="{lx:.1f}" y="{h / 2 + 12:.1f}" width="26" height="26" fill="{st["light"]}"></rect>')
    out.append(text(lx + 38, h / 2 + 34, f"{n_total - n_with} {labels[1]}", 28, st["grey"]))
    out.append("</svg>")
    return "\n".join(out)


# ------------------------------------------------------------------ pages

def no_break(s):
    return re.sub(r"\b([A-Za-z0-9]+-[A-Za-z0-9.]+)\b", r'<span style="white-space: nowrap">\1</span>', s)


def headline_html(text_, signal, colour):
    h = no_break(esc(text_))
    if signal:
        sig = no_break(esc(signal))
        if h.count(sig) != 1:
            raise ValueError(f"signal {signal!r} must occur once in the headline {text_!r}")
        h = h.replace(sig, f'<span style="color: {colour}">{sig}</span>')
    return h


def footer(c, svg, rule, colour, strong):
    """Left-aligned: data line, code handle, and Notes defining the acronyms the banner shows."""
    notes = acronym_notes(visible_text(c["series"], c["indicator"], c["headline"], c["evidence"], svg, c["data_line"]))
    out = (f'<div style="display: flex; flex-direction: column; gap: 2px; border-top: 2px solid {rule}; padding-top: 10px; '
           f'font-size: 16px; line-height: 1.3; color: {colour}; text-align: left">\n'
           f'<div>{esc(c["data_line"])} · <span style="white-space: nowrap">Data and code: <span style="font-weight: 600; color: {strong}">{HANDLE}</span> on GitHub</span></div>\n')
    if notes:
        out += f'<div>Notes: {esc(notes)}.</div>\n'
    return out + "</div>"


def page(design, c, svg):
    """c: dict with series, indicator, headline, signal, evidence, data_line, title."""
    st = STYLES[design]
    if design == "Ink":
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{esc(c['title'])} · Ink</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700&amp;family=IBM+Plex+Sans:wght@400;600&amp;display=swap">
<style>
body{{margin:0}}
</style>
</helmet>
<div style="width: 1200px; height: 630px; box-sizing: border-box; padding: 24px 56px 24px; background: #FFFFFF; color: #000000; font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif; display: flex; flex-direction: column; gap: 12px; border-top: 10px solid #000000; overflow: hidden">

<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 24px; font-size: 24px">
<span style="font-weight: 600; color: #000000; white-space: nowrap">{esc(c['series'])}</span>
<span style="color: #5B6470; text-align: right">{esc(c['indicator'])}</span>
</div>

<div style="display: flex; flex-direction: column; gap: 8px">
<h1 style="margin: 0; font-family: 'Space Grotesk', 'Helvetica Neue', Arial, sans-serif; font-weight: 700; font-size: 46px; line-height: 1.06; letter-spacing: -0.015em; color: #000000; max-width: 1088px; text-wrap: balance">{headline_html(c['headline'], c['signal'], st['signal'])}</h1>
<p style="margin: 0; font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif; font-weight: 600; font-size: 26px; line-height: 1.2; color: {st['evidence']}">{esc(c['evidence'])}</p>
</div>

<div style="flex: 1 1 auto; display: flex; align-items: flex-end">
{svg}
</div>

{footer(c, svg, "#000000", "#3F454D", "#000000")}

</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":1200,"height":630}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
"""
    dark = design == "D-dark"
    ground, ink, eyebrow = ("#0D2433", "#FFFFFF", "#8FB3C7") if dark else ("#F4F6F7", "#101820", "#56626C")
    rule, byl = ("#23465B", "#C9D8E1") if dark else ("#C9D1D6", "#3E4A54")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{esc(c['title'])} · {design}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..100,500..800&amp;family=IBM+Plex+Sans:wght@400;600&amp;family=IBM+Plex+Mono:wght@500&amp;display=swap">
<style>
body{{margin:0}}
</style>
</helmet>
<div style="width: 1200px; height: 630px; box-sizing: border-box; padding: 32px 56px 26px; background: {ground}; color: {ink}; font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif; display: flex; flex-direction: column; gap: 12px; overflow: hidden">

<div style="font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace; font-weight: 500; font-size: 20px; letter-spacing: 0.06em; text-transform: uppercase; color: {eyebrow}">{esc(c['series'])} · {esc(c['indicator'])}</div>

<div style="display: flex; flex-direction: column; gap: 6px">
<h1 style="margin: 0; font-family: 'Archivo', 'Arial Narrow', Arial, sans-serif; font-stretch: 78%; font-weight: 800; font-size: 54px; line-height: 1.0; letter-spacing: -0.01em; color: {ink}; max-width: 1088px; text-wrap: balance">{headline_html(c['headline'], c['signal'], st['signal'])}</h1>
<p style="margin: 0; font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif; font-weight: 600; font-size: 26px; line-height: 1.2; color: {st['evidence']}">{esc(c['evidence'])}</p>
</div>

<div style="flex: 1 1 auto; display: flex; align-items: flex-end">
{svg}
</div>

{footer(c, svg, rule, byl, ink)}

</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":1200,"height":630}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
"""
