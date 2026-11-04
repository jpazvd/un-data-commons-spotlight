#!/usr/bin/env python3
"""Template E (revision 3) for an experiment 002 version: the same words and chart data as the version's
template D or Ink banner, redrawn on the 1200x1200 canvas of template E, in the light or dark palette.

Usage (repo root, with experiment 002's scripts on the path until pull request #23 merges):
    PYTHONPATH=<checkout of experiment/002-draw>/scripts python scripts/banner_e.py \\
        <checkout of a spotlight/002-batch-N branch>/spotlights/NN-slug FRAME PALETTE OUT_DIR
    FRAME is the version (T, L, G, D, D1, D2, D3); PALETTE is light or dark. Writes OUT_DIR/NN-F-E-PALETTE.dc.html,
    .jpg (1200x1200) and .meta.json; --png also writes the 2400x2400 PNG.

What is reused, so that nothing is retyped: the version's stats.json (every number), scripts/copy002.py (the
headline candidates, the signal phrase, the evidence line, the data line, the chart) and scripts/banner002.py
(the chart builders and the acronym rules). Template E adds (docs/revision-3-2026-11/RECOMMENDATIONS.md):
  - a 1:1 canvas; the chart gets the height left between the subtitle and the footer, measured in the browser;
  - a headline of at most two lines at 56 px whose signal phrase is in the signal colour and whose group names
    carry their series colours (lead: data colour; World: grey; other groups: the tint), so there is no legend;
  - a subtitle that defines the measure: the DEFINITION attribute of the indicator's record in UNICEF's
    Reference Data Manager (the stored metadata.rdm.json for the topic's helix code, fetched by the rdm-metadata
    workflow), verbatim when it is short and its first sentence otherwise; where the custodian is not UNICEF
    and no record exists, the SDG series name from the topic's retrieval.json; then the evidence line (years);
  - review round 1's header and footer (pull request #29): "UN Data Commons Spotlight · SDG x.y.z · <short name>",
    no byline, the data line with series code and extraction date, "Data and code: @jpazvd on GitHub", plus
    revision 3's "· CC BY 4.0"; a "Definition: UNICEF Reference Data Manager, indicator <code>" line when the
    registry is used (JP, 3 Nov 2026); a Notes line for acronyms other than agencies and programmes;
  - chart text no smaller than 26 px on the 1200 px artboard (the pilot's lesson at 390 px).
The headline is the one the version carries (chosen by build_versions.py); if it runs to three lines at 56 px
the next candidate from copy002 is tried, and the one used is recorded in the meta.json with its line count.
"""
import argparse
import html
import json
import os
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import banner002 as B  # noqa: E402  (experiment/002-draw, pull request #23)
import copy002 as C  # noqa: E402
import render_banner as R  # noqa: E402
import spotlight002 as S  # noqa: E402
from PIL import Image  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PALETTES = {  # as docs/revision-3-2026-11/pilot/build_pilot.py, from template D light and dark
    "light": dict(bg="#F4F6F7", ink="#101820", muted="#56626C", soft="#3E4A54", grid="#D8DEE2", axis="#9AA6AF",
                  rule="#C9D1D6", blue="#0B6E99", bluetint="#9DC6D8", orange="#B4531A", grey="#7A8790"),
    "dark": dict(bg="#0D2433", ink="#FFFFFF", muted="#8FB3C7", soft="#C9D8E1", grid="#1F3D50", axis="#3B5A6D",
                 rule="#23465B", blue="#4FC3E8", bluetint="#2E6E8A", orange="#F2A541", grey="#8FB3C7"),
}
# banner002's chart style keys, from the template E palette: data (lead series), signal, grey (World), light (other)
STYLE = {
    "light": dict(ground="#F4F6F7", ink="#101820", data="#0B6E99", signal="#B4531A", grey="#56626C", light="#6FA3C0",
                  band="#E6EBEE", base="#9AA6AF", byline="#3E4A54", rule="#C9D1D6", evidence="#3E4A54"),
    "dark": dict(ground="#0D2433", ink="#FFFFFF", data="#4FC3E8", signal="#F2A541", grey="#8FB3C7", light="#6E97B0",
                 band="#12313F", base="#3B5A6D", byline="#C9D8E1", rule="#23465B", evidence="#C9D8E1"),
}
# "light" is the colour of the other groups' lines and bars and of their names in the headline: a mid tone that reads
# as text (the pilot's pale tint did not), still clearly second to the lead series.
SIZE = {20: 26, 21: 26, 22: 26, 24: 28, 26: 28, 28: 30}  # chart text sizes in banner002 -> template E
HANDLE = "@jpazvd"
RDM_URL = "https://rdmapi.unicef.org/api/indicators/{code}"
# Which RDM indicator defines each experiment 002 family (docs/revision-3-2026-11/batch/README.md says why; a
# family absent here has no record that measures the same thing, or its custodian is not UNICEF).
RDM_BY_FAMILY = {
    "water": "WS_PPL_W-SM", "sanitation": "WS_PPL_S-SM",
    "child_marriage_18": "PT_F_20-24_MRD_U18", "child_marriage_15": "PT_F_20-24_MRD_U15",
    "pre_primary": "ED_ANAR_L02", "school_completion": "ED_CR_L1",
    "family_planning": "MNCH_DEMAND_FP", "sba": "MNCH_SAB", "anaemia_women": "NT_ANE_WOM_15_49_MOD",
    "overweight": "NT_ANT_WHZ_PO2", "stunting": "NT_ANT_HAZ_NE2",
    "dtp3": "IM_DTP3", "mcv2": "IM_MCV2", "pcv3": "IM_PCV3",
    "violent_discipline": "PT_CHLD_1-14_PS-PSY-V_CGVR", "ecd": "ECD_CHLD_LMPSL", "abr": "MNCH_ABR",
}
RDM_DIR = ROOT / "docs/revision-3-2026-11/rdm"
MAX_VERBATIM = 230  # characters: a longer DEFINITION is cut to its first sentence
EXTRA_ACRONYMS = {"MMR": "maternal mortality ratio", "ISCED": "International Standard Classification of Education",
                  "SD": "standard deviation", "BMI": "body mass index", "U5MR": "under-five mortality rate"}
NOT_DEFINED_EXTRA = {"CC", "BY", "RDM", "ECD", "WASH", "IGME", "JMP", "JME", "WUENIC", "MMEIG", "IPU", "ILO", "UIS"}

# Review of 3 Nov 2026 (dashboard verdicts, docs/revision-3-2026-11/batch/REVIEW.md): per-version revisions.
REVISIONS = {
    "09-D": {"stats_frame": "D3", "chart": "regions_stacked"},   # show all SDG regions, with and without data stacked
    "16-D": {"stats_frame": "D3", "chart": "regions_stacked"},
    "17-D": {"stats_frame": "D3", "chart": "regions_stacked"},
    "20-D": {"stats_frame": "D3", "chart": "regions_stacked"},
    "39-D": {"stats_frame": "D3", "chart": "regions_stacked"},
    "27-L": {"shade": (2020, 2021, "2020 to 2021")},              # shade the COVID-19 years to read the kink against them
    # JP, 5 Nov 2026: the headline gap is the difference of the two values as the banner shows them, and the text
    # says so (gap_as_shown); the years note is shortened so that the sentence fits the X and Bluesky posts.
    "22-G": {"years_note": "only three SDG regions publish both", "gap_as_shown": True},
    # Copilot review of PR #32, 4 Nov 2026: the measure is the share of seats, not women, so it does not "rise"; the
    # version's own candidate ran to three lines, so the short name leads (copy002.names_construct checks it).
    "39-L": {"headline": "Women in parliament, Latin America and the Caribbean: up 21.4 points since 2000"},
}
HOUSE_WORDS = [("countries and areas", "countries and territories")]  # JP, 3 Nov 2026


def house(text_):
    for a, b in HOUSE_WORDS:
        text_ = text_.replace(a, b).replace(a[:1].upper() + a[1:], b[:1].upper() + b[1:])
    return text_


HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
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
<div style="width: 1200px; height: 1200px; box-sizing: border-box; padding: 52px 56px 36px; background: {bg}; color: {ink}; font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif; display: flex; flex-direction: column; gap: 18px; overflow: hidden">

<div style="font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace; font-weight: 500; font-size: 26px; letter-spacing: 0.08em; text-transform: uppercase; color: {muted}">{series} · {indicator}</div>

<h1 style="margin: 0; font-family: 'Archivo', 'Arial Narrow', Arial, sans-serif; font-stretch: 78%; font-weight: 800; font-size: {hsize}px; line-height: 1.02; letter-spacing: -0.01em; color: {ink}; max-width: 1088px">{headline}</h1>

<div style="font-size: 30px; line-height: 1.3; color: {soft}; max-width: 1088px"><span data-subtitle>{subtitle}</span><br><span style="color: {muted}">{years}</span></div>

<div style="flex: 1 1 auto; display: flex; align-items: flex-end">
{svg}
</div>

<div style="display: flex; flex-direction: column; gap: 2px; border-top: 2px solid {rule}; padding-top: 14px; font-size: 26px; line-height: 1.35; color: {soft}; text-align: left">
<div>{data_line} · <span style="white-space: nowrap">Data and code: <span style="font-weight: 600; color: {ink}">@jpazvd</span> on GitHub</span> · CC BY 4.0</div>{definition}{notes}
</div>

</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":1200,"height":1200}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
"""

MEASURE = """() => {
  const root = document.querySelector('body > div');
  const h1 = document.querySelector('h1');
  const lh = parseFloat(getComputedStyle(h1).lineHeight);
  const sub = h1.nextElementSibling;
  const chart = sub.nextElementSibling;
  const foot = root.lastElementChild;
  const svg = document.querySelector('svg');
  let fill = null;
  if (svg) { let top = Infinity, bottom = -Infinity;
    for (const el of svg.querySelectorAll('rect, circle, polyline, path, text')) { const r = el.getBoundingClientRect(); if (r.height === 0 && r.width === 0) continue; top = Math.min(top, r.top); bottom = Math.max(bottom, r.bottom); }
    const space = foot.getBoundingClientRect().top - 18 - sub.getBoundingClientRect().bottom - 18;
    fill = space > 0 && bottom > top ? (bottom - top) / space : null; }
  return {lines: Math.round(h1.getBoundingClientRect().height / lh), fill: fill,
          space: foot.getBoundingClientRect().top - 18 - sub.getBoundingClientRect().bottom - 18,
          overflow: root.scrollHeight > 1201 || foot.getBoundingClientRect().bottom > 1201
                    || (svg && svg.getBoundingClientRect().bottom > foot.getBoundingClientRect().top + 1),
          foot_bottom: foot.getBoundingClientRect().bottom};
}"""


def esc(s):
    return html.escape(str(s), quote=True)


def scaled_text(x, y, s, size=28, fill="#000", anchor="start", weight=600, extra=""):
    return _text(x, y, s, SIZE.get(size, max(size, 26)), fill, anchor, weight, extra)


_text = B.text
B.text = scaled_text  # every chart builder in banner002 draws its text through B.text


def hbars_e(st, h, rows, unit, aria="", ref=None, pair=None, legend=None, value_fmt=None, target_line=None):
    """banner002.hbars with room for 26 px labels (label column 430 px) and no legend box: the headline names the
    groups in their colours; a paired chart's two series are told apart by the first row's inline labels."""
    n = len(rows)
    if n <= 3 and not pair:  # two or three bars: use the height the chart has (review, 3 Nov 2026: balance the white space)
        h = max(h, int((CURRENT.get("h") or 400) * 0.8))
    lab_w = 430
    x0, x1 = lab_w + 14, B.W - 170
    top = 40 if (pair and legend) else 6
    row_h = (h - top - 6) / n
    vals = [r["value"] for r in rows] + [r.get("value2") or 0 for r in rows]
    if target_line is not None:
        vals.append(target_line[1])
    vmax = max(vals) * 1.05 if max(vals) > 0 else 1
    X = lambda v: x0 + max(0, v) / vmax * (x1 - x0)
    vf = value_fmt or (lambda v: B.fmt(v, unit))
    out = [B.svg_open(h, aria)]
    if pair and legend:  # the two series named once, in their colours, as words rather than swatches
        out.append(B.text(x0, 26, legend[0], 24, st["data"], weight=600))
        out.append(B.text(x0 + 13.5 * len(legend[0]) + 36, 26, legend[1], 24, st["signal"], weight=600))
    for i, r in enumerate(rows):
        yc = top + row_h * (i + 0.5)
        lead = r.get("role") == "lead"
        col = st["data"] if lead or pair else st["light"] if r.get("role") == "other" else st["grey"]
        if r.get("role") == "world" and not pair:
            col = st["grey"]
        bh = min(34 if n > 3 else 84, row_h * 0.62) if not pair else min(18, row_h * 0.36)
        out.append(B.text(lab_w, yc + 8, r["label"], 24, st["ink"] if lead or r.get("role") == "world" else st["grey"], "end",
                          600 if lead or r.get("role") == "world" else 400))
        if pair:
            out.append(f'<rect x="{x0}" y="{yc - bh - 1:.1f}" width="{X(r["value"]) - x0:.1f}" height="{bh:.1f}" fill="{st["data"]}"></rect>')
            out.append(f'<rect x="{x0}" y="{yc + 1:.1f}" width="{X(r["value2"]) - x0:.1f}" height="{bh:.1f}" fill="{st["signal"]}"></rect>')
            if row_h >= 56:
                out.append(B.text(X(r["value"]) + 8, yc - 3, vf(r["value"]), 22, st["ink"], weight=600))
                out.append(B.text(X(r["value2"]) + 8, yc + bh + 1, vf(r["value2"]), 22, st["signal"], weight=600))
            else:
                xe = max(X(r["value"]), X(r["value2"])) + 8
                out.append(f'<text x="{xe:.1f}" y="{yc + 8:.1f}" font-family="{B.FONT}" font-size="26" font-weight="600">'
                           f'<tspan fill="{st["ink"]}">{esc(vf(r["value"]))}</tspan><tspan fill="{st["grey"]}"> / </tspan>'
                           f'<tspan fill="{st["signal"]}">{esc(vf(r["value2"]))}</tspan></text>')
        else:
            out.append(f'<rect x="{x0}" y="{yc - bh / 2:.1f}" width="{X(r["value"]) - x0:.1f}" height="{bh:.1f}" fill="{col}"></rect>')
            out.append(B.text(X(r["value"]) + 10, yc + 9, vf(r["value"]), 24, st["ink"] if lead else st["grey"],
                              weight=600 if lead else 400))
    out.append(f'<line x1="{x0}" y1="{top - 4}" x2="{x0}" y2="{h - 2}" stroke="{st["base"]}" stroke-width="2"></line>')
    if target_line is not None:
        tx = X(target_line[1])
        out.append(f'<line x1="{tx:.1f}" y1="{top - 4}" x2="{tx:.1f}" y2="{h - 2}" stroke="{st["signal"]}" stroke-width="3" stroke-dasharray="10 7"></line>')
    out.append("</svg>")
    return "\n".join(out)


B.hbars = hbars_e


def line_chart_e(st, h, lines, unit, target=None, aria="", labels=None):
    """banner002.line_chart, with every line the headline can name labelled at its end (name and latest value):
    the Spotlight 05-L class of error (three groups named, one labelled) cannot happen on template E."""
    allpts = [pt for l in lines for pt in l["pts"]]
    y0, y1 = min(pt[0] for pt in allpts), max(pt[0] for pt in allpts)
    ty = target["year"] if target else y1
    vals = [pt[1] for pt in allpts]
    if target:
        vals += [target["value"], target["proj"]]
    vmax = max(vals) * 1.12 if max(vals) > 0 else 1
    x0 = 70
    if target:
        x1 = 730
    else:  # room on the right for the longest end label (name and value) at 26 to 28 px
        longest = max((len(f"{line_name(l)} {B.fmt(l['pts'][-1][1], unit)} in {l['pts'][-1][0]}") if len(lines) > 1
                       else len(f"{B.fmt(l['pts'][-1][1], unit)} in {l['pts'][-1][0]}")) for l in lines)
        x1 = int(max(540, min(830, B.W - 30 - 14.5 * longest)))
    top, bottom = 30, h - 42
    X = lambda yr: x0 + (yr - y0) / max(1, (ty - y0)) * (x1 - x0)
    Y = lambda v: bottom - v / vmax * (bottom - top)
    out = [B.svg_open(h, aria)]
    if target:
        ly = target["last"][0]
        out.append(f'<rect x="{X(ly):.1f}" y="{top - 12}" width="{X(ty) - X(ly):.1f}" height="{bottom - top + 12}" fill="{st["band"]}"></rect>')
        out.append(B.text((X(ly) + X(ty)) / 2, top + 12, f"{ty - ly} years left", 22, st["grey"], "middle"))
    if CURRENT.get("shade"):  # a shaded period, e.g. the COVID-19 years, with its label
        sa, sb, slab = CURRENT["shade"]
        sa, sb = max(sa, y0), min(sb, ty)
        if sb > sa:
            out.append(f'<rect x="{X(sa):.1f}" y="{top - 12}" width="{X(sb) - X(sa):.1f}" height="{bottom - top + 12}" fill="{st["band"]}"></rect>')
            out.append(B.text((X(sa) + X(sb)) / 2, top + 12, slab, 22, st["grey"], "middle"))
    out.append(f'<line x1="{x0}" y1="{bottom}" x2="{x1}" y2="{bottom}" stroke="{st["base"]}" stroke-width="2"></line>')
    out.append(B.text(x0 - 14, bottom + 7, "0", 22, st["grey"], "end", 400))
    out.append(B.text(x0, bottom + 32, str(y0), 22, st["grey"], "middle", 400))
    out.append(B.text(X(y1), bottom + 32, str(y1), 22, st["grey"], "middle", 400))
    if target and ty != y1:
        out.append(B.text(x1, bottom + 32, str(ty), 22, st["ink"], "middle", 600))
    order = sorted(lines, key=lambda l: {"other": 0, "world": 1, "lead": 2}[l["role"]])
    for l in order:
        pts = " ".join(f"{X(y):.1f},{Y(v):.1f}" for y, v in l["pts"])
        col, wd = {"lead": (st["data"], 7), "world": (st["grey"], 4), "other": (st["light"], 3.5)}[l["role"]]
        out.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{wd}" stroke-linejoin="round" stroke-linecap="round"></polyline>')
    lead = next(l for l in lines if l["role"] == "lead")
    (ya, va), (yb, vb) = lead["pts"][0], lead["pts"][-1]
    out.append(f'<circle cx="{X(ya):.1f}" cy="{Y(va):.1f}" r="9" fill="{st["data"]}"></circle>')
    out.append(f'<circle cx="{X(yb):.1f}" cy="{Y(vb):.1f}" r="11" fill="{st["ground"]}" stroke="{st["data"]}" stroke-width="5"></circle>')
    lab_a = f"{B.fmt(va, unit)} in {ya}"
    second = lead["pts"][1][1] if len(lead["pts"]) > 1 else vb
    ya_lab = Y(va) - 18 if second <= va else Y(va) + 40
    if ya_lab < top + 10:
        ya_lab = Y(va) + 40
    if ya_lab > bottom - 6:
        ya_lab = Y(va) - 18
    if len(lines) > 1:
        ya_lab = Y(va) + 40 if Y(va) + 40 < bottom - 6 else Y(va) - 18
    out.append(B.text(X(ya) + 18, ya_lab, lab_a, 28, st["ink"]))
    if target:
        rising = vb > va
        out.append(B.text(X(yb) - 18, Y(vb) + (-22 if rising else 44), f"{B.fmt(vb, unit)} in {yb}", 28, st["ink"], "end"))
        yp, yt = Y(target["proj"]), Y(target["value"])
        if abs(yp - yt) < 40:
            yp, yt = (yp - 20, yt + 20) if yp < yt else (yp + 20, yt - 20)
        # projection in grey with a square end marker, inside the band (pilot review, 3 Nov 2026)
        out.append(f'<line x1="{X(yb):.1f}" y1="{Y(vb):.1f}" x2="{x1}" y2="{Y(target["proj"]):.1f}" stroke="{st["grey"]}" stroke-width="4" stroke-dasharray="3 10" stroke-linecap="round"></line>')
        out.append(f'<line x1="{X(yb):.1f}" y1="{Y(vb):.1f}" x2="{x1}" y2="{Y(target["value"]):.1f}" stroke="{st["signal"]}" stroke-width="5" stroke-dasharray="14 9"></line>')
        out.append(f'<rect x="{x1 - 8}" y="{Y(target["proj"]) - 8:.1f}" width="16" height="16" fill="{st["ground"]}" stroke="{st["grey"]}" stroke-width="4"></rect>')
        out.append(f'<circle cx="{x1}" cy="{Y(target["value"]):.1f}" r="10" fill="{st["signal"]}"></circle>')
        out.append(B.text(x1 + 22, yp + 10, target["proj_label"], 28, st["grey"]))
        out.append(B.text(x1 + 22, yt + 10, target["target_label"], 28, st["signal"]))
    else:
        # end labels for every line: name (when there are several) and latest value, pushed apart so none overlap
        ends = []
        for l in lines:
            (ye, ve) = l["pts"][-1]
            name = l.get("name") or line_name(l)
            col = {"lead": st["data"], "world": st["grey"], "other": st["light"]}[l["role"]]
            label = (f"{name} {B.fmt(ve, unit)}" if (name and len(lines) > 1) else B.fmt(ve, unit)) + (f" in {ye}" if l["role"] == "lead" else "")
            ends.append([Y(ve) + 10, label, col, X(ye), 600 if l["role"] == "lead" else 600 if l["role"] == "world" else 500])
        ends.sort(key=lambda e: e[0])
        for i in range(1, len(ends)):
            if ends[i][0] - ends[i - 1][0] < 34:
                ends[i][0] = ends[i - 1][0] + 34
        for i in range(len(ends) - 1, -1, -1):
            if ends[i][0] > bottom - 4:
                ends[i][0] = bottom - 4
            if i > 0 and ends[i][0] - ends[i - 1][0] < 34:  # keep the gap at every step, not only when clamping
                ends[i - 1][0] = ends[i][0] - 34
        for yy, label, col, xe, wt in ends:
            out.append(B.text(xe + 22, yy, label, 28 if wt == 600 else 26, col, weight=wt))
    out.append("</svg>")
    return "\n".join(out)


B.line_chart = line_chart_e


def waffle_e(st, h, n_with, n_total, aria="", labels=("with data", "no data")):
    """banner002.waffle with 20 columns, so the cells fill the chart's height (review, 3 Nov 2026)."""
    cols = 20
    rows = -(-n_total // cols)
    cell = min((B.W - 380) / cols, (h - 20) / rows)
    gap = cell * 0.16
    out = [B.svg_open(h, aria)]
    for i in range(n_total):
        r, c = divmod(i, cols)
        col = st["data"] if i < n_with else st["light"]
        out.append(f'<rect x="{c * cell:.1f}" y="{10 + r * cell:.1f}" width="{cell - gap:.1f}" height="{cell - gap:.1f}" fill="{col}"></rect>')
    lx = cols * cell + 40
    yc = 10 + rows * cell / 2
    out.append(f'<rect x="{lx:.1f}" y="{yc - 52:.1f}" width="28" height="28" fill="{st["data"]}"></rect>')
    out.append(B.text(lx + 40, yc - 29, f"{n_with} {labels[0]}", 28, st["ink"]))
    out.append(f'<rect x="{lx:.1f}" y="{yc + 14:.1f}" width="28" height="28" fill="{st["light"]}"></rect>')
    out.append(B.text(lx + 40, yc + 37, f"{n_total - n_with} {labels[1]}", 28, st["grey"]))
    out.append("</svg>")
    return "\n".join(out)


B.waffle = waffle_e


def regions_stacked(st, h, rows, aria=""):
    """One bar per SDG region, countries with data (data colour) and without (tint) stacked to the region's
    membership; the count at the end of each bar (review, 3 Nov 2026: 09-D, 16-D, 17-D, 20-D, 39-D)."""
    n = len(rows)
    lab_w = 400
    x0, x1 = lab_w + 14, B.W - 150
    top = 44
    row_h = (h - top - 6) / n
    vmax = max(r["n_members"] for r in rows) or 1
    X = lambda v: x0 + v / vmax * (x1 - x0)
    out = [B.svg_open(h, aria)]
    out.append(B.text(x0, 26, "with data", 24, st["data"], weight=600))
    out.append(B.text(x0 + 150, 26, "no data", 24, st["grey"], weight=600))
    for i, r in enumerate(rows):
        yc = top + row_h * (i + 0.5)
        bh = min(40, row_h * 0.66)
        out.append(B.text(lab_w, yc + 9, r["place"], 24, st["ink"], "end", 600))
        out.append(f'<rect x="{x0}" y="{yc - bh / 2:.1f}" width="{X(r["n_with_data"]) - x0:.1f}" height="{bh:.1f}" fill="{st["data"]}"></rect>')
        out.append(f'<rect x="{X(r["n_with_data"]):.1f}" y="{yc - bh / 2:.1f}" width="{X(r["n_members"]) - X(r["n_with_data"]):.1f}" height="{bh:.1f}" fill="{st["light"]}"></rect>')
        out.append(B.text(X(r["n_members"]) + 12, yc + 9, f"{r['n_with_data']} of {r['n_members']}", 24, st["ink"], weight=600))
    out.append(f'<line x1="{x0}" y1="{top - 4}" x2="{x0}" y2="{h - 2}" stroke="{st["base"]}" stroke-width="2"></line>')
    out.append("</svg>")
    return "\n".join(out)


CURRENT = {"stats": None, "shade": None}  # the version being drawn, so line_chart_e can name each line from its place


def line_name(l):
    """The place whose series copy002 passed as this line's points (trend_compared), else ''."""
    st = CURRENT["stats"] or {}
    for r in st.get("places", []):
        if r.get("series") == l["pts"]:
            return S.SHORT.get(r["dcid"], r["place"]) if len(r["place"]) > 18 else r["place"]
    return st.get("place", "") if st.get("places") is None else ""


def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def version_headline(vdir):
    """The headline the version's merged banner carries (chosen by build_versions.py)."""
    src = (vdir / "banner.dc.html").read_text(encoding="utf-8")
    m = re.search(r"<h1[^>]*>(.*?)</h1>", src, re.S)
    return strip_tags(m.group(1)) if m else None


def gap_as_shown(st):
    """For a two-group gap: the widest place's gap as the difference of the two values as shown (one decimal),
    the same gap from the unrounded values, and the sentence that says which difference it is."""
    a, b = st["groups"]
    rows = [r for r in st["places"] if r["dcid"] != "Earth"]
    w = max(rows, key=lambda r: abs(r[a] - r[b]))
    hi, lo = (b, a) if w[b] >= w[a] else (a, b)
    vh, vl = round(w[hi], 1), round(w[lo], 1)
    unit = st.get("unit", "")
    exact, shown = f"{abs(w[a] - w[b]):.1f} points", f"{vh - vl:.1f} points"
    return exact, shown, f"That is {vh:.1f}{unit} {hi} minus {vl:.1f}{unit} {lo}, {w['year']}."


def place_roles(st):
    """{name: role} for the places the chart draws, so the headline can colour them."""
    roles = {}
    lead = st.get("lead")
    if st["kind"] in ("pace_compared", "groups_compared", "groups", "country_gaps"):
        return roles  # paired bars: the colours mean observed and needed (or the two groups), not the places
    for r in st.get("places", []) + st.get("regions", []):
        role = "world" if r["dcid"] == "Earth" else "lead" if (lead and r["dcid"] == lead) else "other"
        if st["kind"] in ("coverage_compared", "regions_data", "level_compared") and role == "other":
            role = "lead"  # single-colour bars: every group is drawn in the data colour
        if st["kind"] == "places_gap" and r["dcid"] in (st.get("highest"), st.get("lowest")):
            role = "lead"
        names = {r["place"], S.SDG_REGIONS.get(r["dcid"], r["place"]), S.GROUPINGS.get(r["dcid"], r["place"]),
                 S.SHORT.get(r["dcid"], r["place"])}
        for n in names:
            roles[n] = role
    if st.get("place") and not st.get("places"):
        roles[st["place"]] = "lead"
        roles[S.SHORT.get(C.S_dcid(st["place"]), st["place"])] = "lead"
    return roles


def headline_html(text_, signal, roles, st_style):
    """Signal phrase in the signal colour (once); each group name outside it in its series colour."""
    h = B.no_break(esc(text_))
    colour = {"lead": st_style["data"], "world": st_style["grey"], "other": st_style["light"]}
    if signal:
        sig = B.no_break(esc(signal))
        if h.count(sig) != 1:
            raise ValueError(f"signal {signal!r} must occur once in {text_!r}")
        pre, post = h.split(sig)
    else:
        pre, post, sig = h, "", ""
    names = sorted((n for n in roles if n and n.lower() not in ("world", "the world") or n == "World"), key=len, reverse=True)
    def colour_names(part):
        for n in names:
            pat = re.compile(r"(?<![A-Za-z])" + re.escape(B.no_break(esc(n))) + r"(?![A-Za-z])")
            part = pat.sub(lambda m: f'<span style="color: {colour[roles[n]]}">{m.group(0)}</span>', part, count=1)
        return part
    if sig and any(re.search(r"(?<![A-Za-z])" + re.escape(B.no_break(esc(n))) + r"(?![A-Za-z])", sig) for n in names):
        # the signal phrase names a group: the names carry their colours and the phrase stays in ink
        return colour_names(h)
    out = colour_names(pre) + (f'<span style="color: {st_style["signal"]}">{sig}</span>' if sig else "") + colour_names(post)
    return re.sub(r'<span style="color: [^"]+">(<span style="color: [^"]+">[^<]*</span>)</span>', r"\1", out)


def rdm_subtitle(family):
    """(subtitle, subtitle_from, helix_code, record_url) from the stored RDM record, or Nones."""
    code = RDM_BY_FAMILY.get(family)
    if not code:
        return None, None, None, None
    path = RDM_DIR / code / "metadata.rdm.json"
    if not path.exists():
        return None, None, code, None
    snap = json.loads(path.read_text(encoding="utf-8"))
    eng = {a["attributeCode"]: a["value"] for a in snap["record"]["attributes"] if a.get("languageISO") == "eng"}
    definition = re.sub(r"\s+", " ", (eng.get("DEFINITION") or "").strip())
    if not definition:
        return None, None, code, snap["url"]
    if len(definition) <= MAX_VERBATIM:
        return definition, "rdm:DEFINITION", code, snap["url"]
    first = re.split(r"(?<=[.;])\s+", definition)[0].strip()
    return first, "rdm:DEFINITION, shortened (first sentence)", code, snap["url"]


def series_subtitle(meta):
    name = ((meta.get("retrieval") or {}).get("indicator") or {}).get("variable_name") or meta["title"]
    name = re.sub(r"\s*\[([^\]]*)\]", lambda m: " (" + m.group(1).replace("=", ": ").lower() + ")", name).strip()
    return name, "sdg series name (retrieval.json variable_name, UN System Data Commons)"


def acronym_notes(text_):
    """banner002's Notes rule with the extra definitions above; unknown acronyms are returned, not raised."""
    saved, saved_nd = dict(B.ACRONYMS), set(B.NOT_DEFINED)  # both restored: page() runs several times per banner
    B.ACRONYMS.update(EXTRA_ACRONYMS)
    B.NOT_DEFINED.update(NOT_DEFINED_EXTRA)
    unknown = []
    try:
        while True:
            try:
                notes = B.acronym_notes(text_)
                break
            except ValueError as e:
                a = re.search(r"acronym '([^']+)'", str(e)).group(1)
                unknown.append(a)
                B.NOT_DEFINED.add(a.upper())
    finally:
        B.ACRONYMS.clear(); B.ACRONYMS.update(saved)
        B.NOT_DEFINED.clear(); B.NOT_DEFINED.update(saved_nd)
    return notes, unknown


def phase0_flags(headline, labels_text, st, roles):
    """The two Phase 0 checks (docs/revision-3-2026-11/phase0_check.py) on the finished banner."""
    flags = []
    named = [n for n in roles if re.search(r"(?<![A-Za-z])" + re.escape(n) + r"s?(?![A-Za-z])", headline)]
    if len(named) >= 2 and len({roles[n] for n in named}) >= 2:  # a comparison: two or more series named
        unl = [n for n in named if not re.search(r"(?<![A-Za-z])" + re.escape(n) + r"s?(?![A-Za-z])", labels_text, re.I)]
        if unl:
            flags.append("named but not labelled on the chart: " + ", ".join(sorted(set(unl))))
    def leaves(o):
        if isinstance(o, dict):
            for v in o.values(): yield from leaves(v)
        elif isinstance(o, list):
            for v in o: yield from leaves(v)
        elif isinstance(o, (int, float)) and not isinstance(o, bool):
            yield float(o)
    values = set(leaves(st))
    for n in re.findall(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?![\w,])", headline):
        v = float(n.replace(",", "")); dec = len(n.split(".")[1]) if "." in n else 0
        if 1990 <= v <= 2035 and dec == 0:
            continue
        if re.search(r"(before|aged|ages|under|over)\s+\d+", headline) and v in {5, 15, 17, 18, 19, 49}:
            continue
        if re.search(r"per\s+" + re.escape(n) + r"\b", headline):  # a unit: per 1,000, per 100,000
            continue
        if not any(round(abs(x), dec) == v or abs(abs(x) - v) < 0.051 for x in values):
            flags.append(f"headline number {n} not in stats.json")
    return flags


def build(topic, frame, palette, out_dir, png=False, tab=None):
    topic = pathlib.Path(topic).resolve()
    vdir = topic / "versions" / frame
    meta = json.loads((topic / "meta.json").read_text(encoding="utf-8"))
    meta["retrieval"] = json.loads((topic / "retrieval.json").read_text(encoding="utf-8"))
    nn = meta["spotlight"]
    rev = REVISIONS.get(f"{nn:02d}-{frame}", {})
    if rev.get("stats_frame"):
        st = S.stats(topic, rev["stats_frame"])
        st["frame"] = frame
    elif (vdir / "stats.json").exists():
        st = json.loads((vdir / "stats.json").read_text(encoding="utf-8"))
    else:  # a replacement topic with no 002 version: compute and keep the stats beside it
        st = S.stats(topic, frame)
        vdir.mkdir(parents=True, exist_ok=True)
        (vdir / "stats.json").write_text(json.dumps(st, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if not st.get("ok"):
        return {"spotlight": nn, "frame": frame, "palette": palette, "ok": False, "reason": st.get("reason", "stats not ok")}
    CURRENT["shade"] = rev.get("shade")
    version = next((v for v in meta["experiment"]["versions"] if v["frame"] == frame), {})
    design = version.get("design", "D-light")
    p = PALETTES[palette]
    style = STYLE[palette]
    B.STYLES[f"E-{palette}"] = style  # copy002 looks the chart style up by design name
    subtitle, origin, code, url = rdm_subtitle(st["family"])
    if subtitle is None:
        subtitle, origin = series_subtitle(meta)
    roles = place_roles(st)
    chosen = rev.get("headline") or (version_headline(vdir) if (vdir / "banner.dc.html").exists() and not rev.get("stats_frame") else None)
    if chosen:
        chosen = house(chosen)
    gap = gap_as_shown(st) if rev.get("gap_as_shown") else None
    if gap and chosen:
        chosen = chosen.replace(gap[0], gap[1])

    def content(h):
        CURRENT["h"] = h
        tf = {}
        if frame != "T" and meta.get("target_basis") not in (None, "none"):
            sT = S.stats(topic, "T")
            if sT.get("ok"):
                cT = C.content(sT, meta, nn, f"E-{palette}", h=h)
                tf = {"tfig": cT["tfig"], "tfig_short": cT["tfig_short"]}
        cc = {**C.content(st, meta, nn, f"E-{palette}", h=h), **tf}
        if rev.get("chart") == "regions_stacked":
            rows_ = sorted(st["regions"], key=lambda r: -(r["share"] or 0))
            cc["svg"] = regions_stacked(B.STYLES[f"E-{palette}"], h, rows_,
                                        aria="; ".join(f"{r['place']}: {r['n_with_data']} of {r['n_members']} countries and territories with data" for r in rows_))
            short_ = S.FAMILY[st["family"]]["short"]
            nw, nu = st["n_universe_with_data"], st["n_universe"]
            cc["headlines"] = [f"{nw} of {nu} countries and territories have data on {short_}",
                               f"Data on {short_}: {nw} of {nu} countries and territories, by SDG region"] + cc["headlines"]
            cc["signal"] = f"{nw} of {nu}"
            if cc.get("headlines_last"):
                cc["headlines_last"] = None
        for k in ("headlines", ):
            cc[k] = [house(x) for x in cc[k]]
        if cc.get("headlines_last"):
            cc["headlines_last"] = (house(cc["headlines_last"][0]), house(cc["headlines_last"][1]))
        for k in ("signal", "evidence", "evidence_alt", "method", "method_short", "question", "svg"):
            if cc.get(k):
                cc[k] = house(cc[k])
        if rev.get("years_note"):
            cc["method_short"] = (cc.get("method_short") or cc["method"]).rstrip(".") + "; " + rev["years_note"] + "."
        if gap:  # the gap as shown leads every candidate, and the evidence says it is the difference
            cc["headlines"] = [x.replace(gap[0], gap[1]) for x in cc["headlines"]]
            cc["signal"] = cc["signal"].replace(gap[0], gap[1])
            cc["evidence"] = gap[2]
        return cc

    CURRENT["stats"] = st
    c = content(300)
    candidates = list(c["headlines"]) + ([c["headlines_last"][0]] if c.get("headlines_last") else [])
    stale = None
    if chosen in candidates:
        candidates = [chosen] + [x for x in candidates if x != chosen]
    elif chosen and rev.get("headline"):  # an explicit revision wording leads, whatever copy002 proposes
        candidates = [chosen] + candidates
    elif chosen:  # the version's banner carries a headline copy002 no longer proposes (its stats changed): not reused
        stale = chosen
        chosen = None

    def signal_for(head, cc):
        if cc.get("headlines_last") and head == cc["headlines_last"][0]:
            return cc["headlines_last"][1]
        return cc["signal"]

    def page(cc, head, h_chart, hsize=56):
        cc = content(h_chart) if h_chart != 300 else cc
        sig = signal_for(head, cc)
        if sig and head.count(sig) != 1:
            sig = None
        evidence = re.sub(r"^Method:\s*", "", cc.get("method_short") or cc["method"]).strip()
        evidence = evidence[:1].upper() + evidence[1:]
        definition = (f'\n<div style="color: {p["muted"]}">Definition: UNICEF Reference Data Manager, indicator {code}</div>'
                      if origin and origin.startswith("rdm:") else "")
        notes, unknown = acronym_notes(B.visible_text(cc["series"], cc["indicator"], head, subtitle, evidence, cc["svg"],
                                                      cc["data_line"], definition))
        html_ = HEAD.format(title=f"Spotlight {nn:02d}-{frame} · template E {palette}", hsize=hsize, bg=p["bg"], ink=p["ink"], muted=p["muted"],
                            soft=p["soft"], rule=p["rule"], series=esc(cc["series"]), indicator=esc(cc["indicator"]),
                            headline=headline_html(head, sig, roles, style), subtitle=esc(subtitle), years=esc(evidence),
                            svg=cc["svg"], data_line=esc(cc["data_line"]), definition=definition,
                            notes=(f'\n<div style="color: {p["muted"]}">Notes: {esc(notes)}.</div>' if notes else ""))
        return html_, cc, sig, unknown

    out_dir = pathlib.Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{nn:02d}-{frame}-E-{palette}"
    result = None
    for hsize in (56, 52, 48):  # the version's headline first at 56 px; the next candidates; then smaller type
        for head in candidates:
            try:
                html_, cc, sig, unknown = page(c, head, 300, hsize)
            except ValueError:
                continue
            tmp = write_page(out_dir, html_)
            tab.goto(tmp.as_uri()); tab.evaluate("document.fonts.ready"); tab.wait_for_timeout(120)
            m = tab.evaluate(MEASURE)
            tmp.unlink(missing_ok=True)
            if m["lines"] > 2:
                continue
            h_chart = int(max(300, min(640, m["space"])))
            html_, cc, sig, unknown = page(c, head, h_chart, hsize)
            tmp = write_page(out_dir, html_)
            tab.goto(tmp.as_uri()); tab.evaluate("document.fonts.ready"); tab.wait_for_timeout(150)
            m = tab.evaluate(MEASURE)
            if m["overflow"] or m["lines"] > 2:
                h_chart = int(max(240, h_chart - 60))
                html_, cc, sig, unknown = page(c, head, h_chart, hsize)
                tmp.unlink(missing_ok=True)
                tmp = write_page(out_dir, html_)
                tab.goto(tmp.as_uri()); tab.evaluate("document.fonts.ready"); tab.wait_for_timeout(150)
                m = tab.evaluate(MEASURE)
            if m["overflow"] or m["lines"] > 2:
                tmp.unlink(missing_ok=True)
                continue
            result = (head, html_, cc, sig, unknown, tmp, m, h_chart, hsize)
            break
        if result:
            break
    if not result:
        return {"spotlight": nn, "frame": frame, "palette": palette, "ok": False, "reason": "no headline fits in two lines"}
    head, html_, cc, sig, unknown, tmp, m, h_chart, hsize = result
    (out_dir / f"{stem}.dc.html").write_text(html_, encoding="utf-8")
    png_path, jpg_path = out_dir / f"{stem}.png", out_dir / f"{stem}.jpg"
    tab.screenshot(path=str(png_path), clip={"x": 0, "y": 0, "width": 1200, "height": 1200})
    tmp.unlink(missing_ok=True)
    Image.open(png_path).convert("RGB").resize((1200, 1200), Image.LANCZOS).save(jpg_path, quality=86, optimize=True, progressive=True)
    if not png:
        png_path.unlink()
    labels = " ".join(strip_tags(t) for t in re.findall(r"<text[^>]*>(.*?)</text>", cc["svg"], re.S))
    flags = phase0_flags(head, labels, st, roles)
    if unknown:
        flags.append("acronym shown without a definition: " + ", ".join(unknown))
    if len(subtitle) > MAX_VERBATIM:
        flags.append(f"subtitle is long ({len(subtitle)} characters): shorten by hand or move to the caption")
    if chosen and head != chosen:
        flags.append(f"headline differs from the version's ({chosen!r}): three lines at 56 px")
    if stale:
        flags.append(f"the version's headline ({stale!r}) is not among copy002's candidates for its stats.json and was not reused")
    if hsize != 56:
        flags.append(f"headline at {hsize} px: no candidate fits two lines at 56 px")
    if m.get("fill") is not None and m["fill"] < 0.5:
        flags.append(f"chart uses {m['fill']:.0%} of its height: too much empty space (review, 3 Nov 2026)")
    if rev:
        flags.append("revised after the review of 3 Nov 2026: " + ", ".join(f"{k}={v}" for k, v in rev.items()))
    if meta.get("replacement_of"):
        flags.append(f"replacement series: {meta['replacement_of']['reason']}")
    alt = html.unescape(html.unescape(cc["svg"].split('aria-label="', 1)[1].split('"', 1)[0]))
    out = {"spotlight": nn, "frame": frame, "palette": palette, "ok": True, "slug": topic.name, "title": meta["title"],
           "sdg_indicator": meta["sdg_indicator"], "family": st["family"], "kind": st["kind"], "custodian": st.get("custodian"),
           "design_as_built": design, "headline": head, "headline_lines": m["lines"], "headline_px": hsize, "signal": sig,
           "subtitle": subtitle, "subtitle_from": origin, "rdm_helix_code": code or "none", "rdm_url": url,
           "years": cc["evidence"], "data_line": cc["data_line"], "chart_height": h_chart, "chart_fill": m.get("fill"), "flags": flags,
           "revision": rev or None, "replacement_of": meta.get("replacement_of"),
           "alt": f"{head}. {cc['evidence']} {alt}", "method": cc.get("method_short"), "question": cc.get("question"),
           "first_comment": "Data and code: https://github.com/jpazvd/un-data-commons-spotlight",
           "second_comment": (f"Definition, UNICEF Reference Data Manager ({code}): {url}" if url and origin.startswith("rdm:") else None)}
    (out_dir / f"{stem}.meta.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    # For a caller that writes the version's captions (experiments/003-.../build_versions_e.py): the words as drawn,
    # which copy002.captions takes, and the meta.json of the topic as read. Not written to the meta file.
    return {**out, "content": cc, "topic_meta": meta}


def write_page(out_dir, html_):
    fd, tmp = tempfile.mkstemp(prefix=".e.", suffix=".html", dir=out_dir)
    os.close(fd)
    page = pathlib.Path(tmp)
    page.write_text(R.build_page(html_, "banner.dc.html"), encoding="utf-8")
    return page


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topic"); ap.add_argument("frame"); ap.add_argument("palette", choices=list(PALETTES))
    ap.add_argument("out_dir"); ap.add_argument("--png", action="store_true")
    a = ap.parse_args()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        tab = browser.new_page(viewport={"width": 1200, "height": 1200}, device_scale_factor=2)
        r = build(a.topic, a.frame, a.palette, a.out_dir, a.png, tab)
        browser.close()
    print(json.dumps({k: r.get(k) for k in ("spotlight", "frame", "palette", "ok", "headline", "flags", "reason")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
