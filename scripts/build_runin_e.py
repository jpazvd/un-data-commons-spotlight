#!/usr/bin/env python3
"""Build the run-in banners of experiment 003, Spotlights 03 (light) and 04 (dark), on template E, version 4.

Usage (repo root):
    python scripts/build_runin_e.py                                   # writes spotlights/03-*/ and 04-*/ banner.dc.html, alt.txt
    python scripts/render_banner.py spotlights/03-women-in-parliament # then render each
    python scripts/render_banner.py spotlights/04-maternal-mortality

The drawing is the revision 3 pilot's (docs/revision-3-2026-11/pilot/build_pilot.py, Phase 1, kept there as the
review record), brought to the rules of Phase 2, version 4 (docs/revision-3-2026-11/batch/REVIEW.md;
scripts/banner_e.py), which the experiment banners follow (JP, 4 Nov 2026: every banner in the queue aligned
with revision 3, Phase 2, version 4):
- the series line names the topic after the indicator, "UN Data Commons Spotlight · SDG x.y.z · <topic>";
- the Notes line defines every acronym shown that is not an agency, organization or programme, as banner_e.py
  does, including one the subtitle spells out (version 4 keeps the note; the pilot skipped it);
- a shaded period on a line chart where the series has a kink in the COVID-19 years, labelled with its years,
  as on 27-L (04: the world ratio rises from 210.5 in 2020 to 241.9 in 2021 and falls to 202.6 in 2022);
- no label crossed by a line (04: the "in 2030" projection label sat on the target line).
Numbers come from the merged Spotlight folders (data/world.csv, stats.json, meta.json, metadata.rdm.json);
nothing is typed. The Phase 1 description of the pilot follows.

Template E (docs/revision-3-2026-11/RECOMMENDATIONS.md): a 1200x1200 artboard; a headline of at most two
lines whose group names carry the series colours (no legend); a subtitle that defines the measure, then the
years; one chart with direct labels and at most one callout. Palette: "light" (template D light) or "dark"
(template D dark), since the palette is inherited from experiment 002's result.

Revision 3 is cumulative on revision 2. The header and footer follow review round 1 (2 Nov 2026, pull request
#29, scripts/restyle_runin.py; the same rules in scripts/banner002.py): the series line reads
"UN Data Commons Spotlight · SDG x.y.z" with no Spotlight number; there is no byline; the footer is
left-aligned and reads "Data: <custodian> via UN SDG Global Database, series <sdg_series_code>, extracted
<d Mon yyyy> · Data and code: @jpazvd on GitHub", followed by a Notes line that defines every acronym shown
on the banner except the names of agencies, organizations and monitoring programmes and "SDG", and except an
acronym the banner already spells out. Revision 3 adds only "· CC BY 4.0" to the data line. The series code
and extraction date are read from the Spotlight's meta.json, never typed.

When the subtitle comes from UNICEF's Reference Data Manager (JP, 3 Nov 2026), the footer says so on its own
line, "Definition: UNICEF Reference Data Manager, indicator <helix code>", and a second comment on the post
carries the link to that record, after the first comment with the GitHub repo link (first-comments.md);
an indicator with no RDM record (03, custodian IPU) shows no such line and gets no second comment.
"""
import datetime
import html as html_lib
import re
import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

PALETTES = {
    "light": dict(bg="#F4F6F7", ink="#101820", muted="#56626C", soft="#3E4A54", grid="#D8DEE2", axis="#9AA6AF",
                  rule="#C9D1D6", blue="#0B6E99", bluetint="#9DC6D8", orange="#B4531A", orangetint="#E3B59A",
                  grey="#7A8790"),
    "dark": dict(bg="#0D2433", ink="#FFFFFF", muted="#8FB3C7", soft="#C9D8E1", grid="#1F3D50", axis="#3B5A6D",
                 rule="#23465B", blue="#4FC3E8", bluetint="#2E6E8A", orange="#F2A541", orangetint="#8C6A3A",
                 grey="#8FB3C7"),
}

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
<div style="width: 1200px; height: 1200px; box-sizing: border-box; padding: 52px 56px 36px; background: {bg}; color: {ink}; font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif; display: flex; flex-direction: column; gap: 18px">

<div style="font-family: 'IBM Plex Mono', ui-monospace, Menlo, monospace; font-weight: 500; font-size: 26px; letter-spacing: 0.08em; text-transform: uppercase; color: {muted}">UN Data Commons Spotlight · SDG {sdg} · {topic}</div>

<h1 style="margin: 0; font-family: 'Archivo', 'Arial Narrow', Arial, sans-serif; font-stretch: 78%; font-weight: 800; font-size: {hsize}px; line-height: 1.02; letter-spacing: -0.01em; color: {ink}; max-width: 1088px">{headline}</h1>

<div style="font-size: 30px; line-height: 1.3; color: {soft}; max-width: 1088px"><span data-subtitle>{subtitle}</span><br><span style="color: {muted}">{years}</span></div>

{svg}

<div style="margin-top: auto; display: flex; flex-direction: column; gap: 2px; border-top: 2px solid {rule}; padding-top: 14px; font-size: 26px; line-height: 1.35; color: {soft}; text-align: left">
<div>Data: {custodian} via UN SDG Global Database, series {series}, extracted {extracted} · <span style="white-space: nowrap">Data and code: <span style="font-weight: 600; color: {ink}">@jpazvd</span> on GitHub</span> · CC BY 4.0</div>{definition}{notes}
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


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [{k: (float(v) if k in ("value", "year") else v) for k, v in r.items()} for r in csv.DictReader(f)]


def rdm_definition(folder):
    snap = json.loads((ROOT / "spotlights" / folder / "metadata.rdm.json").read_text(encoding="utf-8"))
    eng = {a["attributeCode"]: a["value"] for a in snap["record"]["attributes"] if a.get("languageISO") == "eng"}
    return eng["DEFINITION"]


def fmt(v, d=1):
    return f"{v:,.{d}f}"


# Review round 1 (scripts/banner002.py): acronyms defined in the footer's Notes line when shown on the banner,
# except agencies, organizations, monitoring programmes and "SDG" (version 4: also one the banner spells out).
ACRONYMS = {"LDCs": "least developed countries", "LLDCs": "landlocked developing countries",
            "SIDS": "small island developing states", "NEET": "not in education, employment or training",
            "MMR": "maternal mortality ratio", "HIV": "human immunodeficiency virus", "MPI": "multidimensional poverty index"}
NOT_DEFINED = {"UN", "WHO", "UNICEF", "UNESCO", "ILO", "UNFPA", "UNAIDS", "UNDP", "SDG", "SDGS",
               "JMP", "UIS", "JME", "IGME", "MMEIG", "WUENIC", "DESA", "IPU", "GHO", "DHS", "MICS", "CC", "BY"}


def visible_text(*parts):
    out = []
    for part in parts:
        part = re.sub(r'aria-label="[^"]*"', "", str(part or ""))
        out.append(html_lib.unescape(re.sub(r"<[^>]+>", " ", part)))
    return " ".join(out)


def notes_line(p, *parts):
    text = visible_text(*parts)
    shown = []
    for m in re.finditer(r"\b[A-Z][A-Z0-9]{1,}s?\b", text):
        a = m.group(0)
        key = a if a in ACRONYMS else a.rstrip("s")
        if key.upper() in NOT_DEFINED or key not in ACRONYMS or key in shown:
            continue
        shown.append(key)
    if not shown:
        return ""
    body = "; ".join(f"{k}, {ACRONYMS[k]}" for k in shown)
    return f'\n<div style="color: {p["muted"]}">Notes: {body}.</div>'


RDM_URL = "https://rdmapi.unicef.org/api/indicators/{code}"


def definition_line(p, helix_code):
    if helix_code == "none":
        return ""
    return f'\n<div style="color: {p["muted"]}">Definition: UNICEF Reference Data Manager, indicator {helix_code}</div>'


def spot_meta(spot):
    """Series code and extraction date from the merged Spotlight's meta.json (review round 1 footer)."""
    meta = json.loads((spot / "meta.json").read_text(encoding="utf-8"))
    d = datetime.date.fromisoformat(meta["retrieved_on"])
    return meta["sdg_series_code"], f"{d.day} {d.strftime('%b %Y')}"


def line_chart(p, series, x0, x1, y0, y1, w=1088, h=600, left=92, right=70, top=46, bottom=66, ticks=(), yfmt=lambda v: str(v)):
    """Shared frame for a line chart: returns helper functions and the grid/axis markup."""
    sx = lambda x: left + (x - x0) / (x1 - x0) * (w - left - right)
    sy = lambda y: top + (y1 - y) / (y1 - y0) * (h - top - bottom)
    parts = [f'<g font-family="IBM Plex Sans, Arial, sans-serif" font-size="28" fill="{p["muted"]}">']
    for t in ticks:
        parts.append(f'<line x1="{left}" y1="{sy(t):.1f}" x2="{w-right}" y2="{sy(t):.1f}" stroke="{p["grid"]}" stroke-width="1.5"></line>')
        parts.append(f'<text x="{left-14}" y="{sy(t)+9:.1f}" text-anchor="end">{yfmt(t)}</text>')
    parts.append(f'<line x1="{left}" y1="{sy(y0):.1f}" x2="{w-right}" y2="{sy(y0):.1f}" stroke="{p["axis"]}" stroke-width="2"></line>')
    parts.append("</g>")
    return sx, sy, "\n".join(parts)


def build_03(p):
    spot = ROOT / "spotlights/03-women-in-parliament"
    stats = json.loads((spot / "stats.json").read_text(encoding="utf-8"))
    world = read_csv(spot / "data/world.csv")
    top = stats["top_countries"][0]
    first, last = stats["world_first"], stats["world_last"]
    sx, sy, frame = line_chart(p, world, 2000, 2026, 0, 70, ticks=(0, 25, 50), yfmt=lambda v: f"{v}%")
    pts = " ".join(f"{sx(r['year']):.1f},{sy(r['value']):.1f}" for r in world)
    g = [f'<svg viewBox="0 0 1088 600" width="1088" height="600" role="img" aria-label="Share of seats in national parliaments held by women, world, 1 January of each year: {first["value"]} percent in {first["year"]}, {last["value"]} percent in {last["year"]}; parity at 50 percent shown as a reference; highest share in {int(top["year"])}: {top["name"]} {fmt(top["value"], 2)} percent." style="display: block; flex: 0 0 auto">', frame]
    g.append(f'<line x1="{sx(2000):.1f}" y1="{sy(50):.1f}" x2="{sx(2026):.1f}" y2="{sy(50):.1f}" stroke="{p["grey"]}" stroke-width="3" stroke-dasharray="14 9"></line>')
    g.append(f'<polyline points="{pts}" fill="none" stroke="{p["blue"]}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"></polyline>')
    g.append(f'<circle cx="{sx(2000):.1f}" cy="{sy(first["value"]):.1f}" r="10" fill="{p["blue"]}"></circle>')
    g.append(f'<circle cx="{sx(2026):.1f}" cy="{sy(last["value"]):.1f}" r="12" fill="{p["bg"]}" stroke="{p["blue"]}" stroke-width="5"></circle>')
    g.append(f'<g font-family="IBM Plex Sans, Arial, sans-serif" font-size="28" fill="{p["muted"]}">')
    for yr in (2000, 2010, 2020, 2026):
        g.append(f'<text x="{sx(yr):.1f}" y="{sy(0)+36:.1f}" text-anchor="middle">{yr}</text>')
    g.append("</g>")
    g.append(f'<g font-family="IBM Plex Sans, Arial, sans-serif" font-weight="600" font-size="30">')
    g.append(f'<text x="{sx(2000)+18:.1f}" y="{sy(first["value"])+42:.1f}" fill="{p["ink"]}">{first["value"]}% in {first["year"]}</text>')
    g.append(f'<text x="{sx(2026)-18:.1f}" y="{sy(last["value"])-24:.1f}" text-anchor="end" fill="{p["blue"]}">{last["value"]}% in {last["year"]}</text>')
    g.append(f'<text x="{sx(2000):.1f}" y="{sy(50)-14:.1f}" fill="{p["grey"]}">Parity: 50% of seats</text>')
    g.append(f'<circle cx="{sx(2026):.1f}" cy="{sy(top["value"]):.1f}" r="8" fill="{p["bluetint"]}"></circle>')
    g.append(f'<text x="{sx(2026)-18:.1f}" y="{sy(top["value"])+10:.1f}" text-anchor="end" fill="{p["soft"]}" font-weight="400">Highest in {int(top["year"])}: {top["name"]}, {fmt(top["value"], 2)}%</text>')
    g.append("</g></svg>")
    series, extracted = spot_meta(spot)
    return dict(
        title="Spotlight 03 · template E", series=series, extracted=extracted,
        hsize=56,
        headline=f'<span style="color: {p["blue"]}">Women held {last["value"]}% of parliament seats</span> in {last["year"]}, up from {first["value"]}% in {first["year"]}; <span style="color: {p["grey"]}">parity</span> is 50%',
        subtitle="The proportion of seats held by women in national parliaments, currently as of 1 January of reporting year",
        years=f"Single or lower chambers, {first['year']} to {last['year']}; SDG target 5.5 sets no number.",
        svg="\n".join(g), custodian="IPU", sdg="5.5.1", topic="women in parliament",
        alt=(f"Banner: women held {last['value']}% of seats in national parliaments worldwide in {last['year']}, up from "
             f"{first['value']}% in {first['year']}; highest share {top['name']} {fmt(top['value'], 2)}%. Parity (50%) shown as "
             f"a reference. Data: IPU via UN SDG Global Database, indicator 5.5.1."),
        subtitle_from="SDG metadata 5.5.1a (UN Statistics Division), see sources.md", rdm_helix_code="none")


def build_04(p):
    spot = ROOT / "spotlights/04-maternal-mortality"
    stats = json.loads((spot / "stats.json").read_text(encoding="utf-8"))
    world = read_csv(spot / "data/world.csv")
    first, last, tgt = stats["world_first"], stats["world_last"], stats["target"]
    peak = next(r for r in world if int(r["year"]) == 2021)  # the kink inside the shaded COVID-19 years
    req, obs, proj = round(stats["required_pace_pts_per_year"], 1), round(stats["observed_pace_pts_per_year"], 1), round(stats["value_at_current_pace_in_target_year"], 1)
    sx, sy, frame = line_chart(p, world, 2000, 2030, 0, 350, right=60, ticks=(0, 100, 200, 300))
    pts = " ".join(f"{sx(r['year']):.1f},{sy(r['value']):.1f}" for r in world)
    g = [f'<svg viewBox="0 0 1088 600" width="1088" height="600" role="img" aria-label="Maternal mortality ratio, world: {first["value"]} deaths per 100,000 live births in {first["year"]}, {last["value"]} in {last["year"]}; at the observed pace of {obs} a year it would be about {proj} in {tgt["year"]}; the SDG target of {int(tgt["value"])} needs {req} a year; 2020 to 2021 shaded, {fmt(peak["value"])} in 2021." style="display: block; flex: 0 0 auto">', frame]
    g.append(f'<rect x="{sx(last["year"]):.1f}" y="{sy(350):.1f}" width="{sx(2030)-sx(last["year"]):.1f}" height="{sy(0)-sy(350):.1f}" fill="{p["grid"]}" fill-opacity="0.45"></rect>')
    # version 4: the COVID-19 years shaded and labelled, as on 27-L (REVIEW.md); the kink is the 2021 value
    shade = (2020, 2021, "2020 to 2021")
    g.append(f'<rect x="{sx(shade[0]):.1f}" y="{sy(350):.1f}" width="{sx(shade[1])-sx(shade[0]):.1f}" height="{sy(0)-sy(350):.1f}" fill="{p["grid"]}" fill-opacity="0.45"></rect>')
    g.append(f'<text x="{(sx(shade[0])+sx(shade[1]))/2:.1f}" y="{sy(350)+30:.1f}" text-anchor="middle" font-family="IBM Plex Sans, Arial, sans-serif" font-size="26" fill="{p["muted"]}">{shade[2]}</text>')
    g.append(f'<line x1="{sx(last["year"]):.1f}" y1="{sy(last["value"]):.1f}" x2="{sx(2030):.1f}" y2="{sy(tgt["value"]):.1f}" stroke="{p["orange"]}" stroke-width="5" stroke-dasharray="14 9"></line>')
    g.append(f'<line x1="{sx(last["year"]):.1f}" y1="{sy(last["value"]):.1f}" x2="{sx(2030):.1f}" y2="{sy(proj):.1f}" stroke="{p["grey"]}" stroke-width="4" stroke-dasharray="3 10" stroke-linecap="round"></line>')
    g.append(f'<text x="{(sx(last["year"])+sx(2030))/2:.1f}" y="{sy(350)+30:.1f}" text-anchor="middle" font-family="IBM Plex Sans, Arial, sans-serif" font-size="26" fill="{p["muted"]}">projections</text>')
    g.append(f'<polyline points="{pts}" fill="none" stroke="{p["blue"]}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"></polyline>')
    g.append(f'<circle cx="{sx(2000):.1f}" cy="{sy(first["value"]):.1f}" r="10" fill="{p["blue"]}"></circle>')
    g.append(f'<circle cx="{sx(last["year"]):.1f}" cy="{sy(last["value"]):.1f}" r="12" fill="{p["bg"]}" stroke="{p["blue"]}" stroke-width="5"></circle>')
    g.append(f'<circle cx="{sx(2030):.1f}" cy="{sy(tgt["value"]):.1f}" r="10" fill="{p["bg"]}" stroke="{p["orange"]}" stroke-width="4"></circle>')
    g.append(f'<rect x="{sx(2030)-9:.1f}" y="{sy(proj)-9:.1f}" width="18" height="18" fill="{p["bg"]}" stroke="{p["grey"]}" stroke-width="4"></rect>')
    g.append(f'<g font-family="IBM Plex Sans, Arial, sans-serif" font-size="28" fill="{p["muted"]}">')
    for yr in (2000, 2010, 2023, 2030):
        g.append(f'<text x="{sx(yr):.1f}" y="{sy(0)+36:.1f}" text-anchor="middle">{yr}</text>')
    g.append("</g>")
    g.append(f'<g font-family="IBM Plex Sans, Arial, sans-serif" font-weight="600" font-size="30">')
    g.append(f'<text x="{sx(2000)+18:.1f}" y="{sy(first["value"])-20:.1f}" fill="{p["ink"]}">{first["value"]} in {first["year"]}</text>')
    g.append(f'<text x="{sx(last["year"])-18:.1f}" y="{sy(last["value"])+52:.1f}" text-anchor="end" fill="{p["ink"]}">{last["value"]} in {last["year"]}</text>')
    # version 4: above the dotted projection line, clear of the target line (the pilot put it on the target line)
    g.append(f'<text x="{sx(2030)+4:.1f}" y="{sy(proj)-62:.1f}" text-anchor="end" fill="{p["grey"]}">{proj} in 2030</text>')
    g.append(f'<text x="{sx(2030)-16:.1f}" y="{sy(tgt["value"])+42:.1f}" text-anchor="end" fill="{p["orange"]}">SDG target {int(tgt["value"])}: {req} a year</text>')
    g.append("</g></svg>")
    series, extracted = spot_meta(spot)
    return dict(
        title="Spotlight 04 · template E", series=series, extracted=extracted,
        hsize=56,
        headline=f'Maternal mortality <span style="color: {p["orange"]}">below {int(tgt["value"])} by 2030 means cutting {req} a year</span>; <span style="color: {p["blue"]}">since {first["year"]}, {obs} a year</span>',
        # the record's first sentence, as banner_e.rdm_subtitle() shortens it: the stored record stays the source
        subtitle=re.split(r"(?<=[.;])\s+", re.sub(r"\s+", " ", rdm_definition("04-maternal-mortality")).strip())[0],
        years=f"MMEIG estimates, world series {first['year']} to {last['year']}; the shaded band to {tgt['year']} holds projections, not data.",
        svg="\n".join(g), custodian="UN MMEIG", sdg="3.1.1", topic="maternal mortality",
        alt=(f"Banner: getting world maternal mortality below {int(tgt['value'])} per 100,000 live births by {tgt['year']} means "
             f"cutting it {req} a year; since {first['year']} it has fallen {obs} a year, from {first['value']} to "
             f"{last['value']} in {last['year']}. The years 2020 to 2021 are shaded; the ratio rose to {fmt(peak['value'])} in "
             f"2021. Data: MMEIG via UN SDG Global Database, indicator 3.1.1."),
        subtitle_from="rdm:DEFINITION, shortened (first sentence)", rdm_helix_code="MNCH_MMR")


def main():
    for slug, pal, build in (("03-women-in-parliament", "light", build_03), ("04-maternal-mortality", "dark", build_04)):
        p = PALETTES[pal]
        d = build(p)
        d["definition"] = definition_line(p, d["rdm_helix_code"])
        d["notes"] = notes_line(p, d["headline"], d["subtitle"], d["years"], d["svg"], d["custodian"], d["definition"])
        page = HEAD.format(**p, **{k: v for k, v in d.items() if k in ("title", "hsize", "headline", "subtitle", "years", "svg", "custodian", "sdg", "topic", "series", "extracted", "definition", "notes")})
        out = ROOT / "spotlights" / slug
        (out / "banner.dc.html").write_text(page, encoding="utf-8")
        (out / "alt.txt").write_text(d["alt"] + "\n", encoding="utf-8")
        print("wrote", (out / "banner.dc.html").relative_to(ROOT), "and alt.txt")


if __name__ == "__main__":
    main()
