"""Mock of the redesigned coverage chart (framing D): every member country counted, with or without data.

Usage: python experiments/002-design-framing-time/review/mocks/coverage_mock.py OUT_DIR   (topics 16, 21 and 09 must be
built in spotlights/ first, e.g. with build_all.py). Not part of the build: the redesign waits for JP's choice.
"""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts')); sys.path.insert(0, str(ROOT / 'experiments/002-design-framing-time'))
import spotlight002 as S, banner002 as B, copy002 as C, render_banner as R
from playwright.sync_api import sync_playwright
OUT = pathlib.Path(sys.argv[1])
SHORTN = {"DPR Korea": "North Korea", "Congo [DRC]": "DR Congo", "Lao PDR": "Laos", "Lao People’s Democratic Republic": "Laos", "Timor-Leste": "Timor-Leste", "Democratic Republic of the Congo": "DR Congo", "Central African Republic": "Central African Rep.",
          "Lao People's Democratic Republic": "Laos", "Laos": "Laos", "United Republic of Tanzania": "Tanzania",
          "Sao Tome and Principe": "São Tomé and Príncipe", "Democratic People's Republic of Korea": "North Korea",
          "North Korea": "North Korea", "Syrian Arab Republic": "Syria", "Iran (Islamic Republic of)": "Iran",
          "State of Palestine": "Palestine", "Palestinian Territories": "Palestine",
          "Republic of the Congo": "Congo", "Saudi Arabia": "Saudi Arabia", "South Sudan": "South Sudan"}
CUT = 2020


def legend(st, y):
    out, x = [], 0
    for col, lab, hollow in ((st["data"], f"latest value after {CUT}", False), (st["signal"], f"{CUT} or earlier", False),
                             (st["light"], "no data", True)):
        fill = "none" if hollow else col
        out.append(f'<rect x="{x}" y="{y - 16}" width="18" height="18" fill="{fill}" stroke="{col}" stroke-width="2"></rect>')
        out.append(B.text(x + 26, y, lab, 21, st["ink"], weight=600))
        x += 26 + len(lab) * 11 + 34
    return out


def region_bars(st, h, rows, aria):
    """rows: (label, recent, older, none). Bars to one scale: a bar's length is the region's number of countries."""
    x0, x1 = 250, B.W - 110
    top = 40
    rh = (h - top) / len(rows)
    mx = max(r[1] + r[2] + r[3] for r in rows)
    k = (x1 - x0) / mx
    out = [B.svg_open(h, aria)] + legend(st, 20)
    for i, (lab, a, b, c) in enumerate(rows):
        y = top + i * rh + rh * 0.18
        bh = rh * 0.64
        out.append(B.text(x0 - 12, y + bh * 0.75, lab, 20, st["ink"], "end", 400))
        x = x0
        for n, col, hollow in ((a, st["data"], False), (b, st["signal"], False), (c, st["light"], True)):
            if n:
                fill = "none" if hollow else col
                out.append(f'<rect x="{x + 1:.1f}" y="{y:.1f}" width="{n * k - 2:.1f}" height="{bh:.1f}" fill="{fill}" stroke="{col}" stroke-width="2"></rect>')
                x += n * k
        out.append(B.text(x + 10, y + bh * 0.75, f"{a + b} of {a + b + c}", 20, st["ink"], "start", 600))
    out.append("</svg>")
    return "\n".join(out)


def tiles(st, h, items, aria, cols):
    """items: (name, year or None), sorted: recent first, then older, then none. One tile per country."""
    rows = -(-len(items) // cols)
    top = 40
    tw, th = B.W / cols, (h - top) / rows
    out = [B.svg_open(h, aria)] + legend(st, 20)
    fs = 17 if cols <= 6 else 14
    for i, (name, year) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = c * tw, top + r * th
        col = st["light"] if year is None else st["data"] if year > CUT else st["signal"]
        fill = "none" if year is None else col
        out.append(f'<rect x="{x + 3:.1f}" y="{y + 3:.1f}" width="{tw - 6:.1f}" height="{th - 6:.1f}" fill="{fill}" stroke="{col}" stroke-width="2"></rect>')
        ink = st["ink"] if year is None else st["ground"]
        out.append(B.text(x + 10, y + th / 2 - 1, name, fs, ink, "start", 600))
        out.append(B.text(x + 10, y + th / 2 + fs + 1, "no data" if year is None else str(year), fs, ink, "start", 400))
    out.append("</svg>")
    return "\n".join(out)


def build(slug, frame, design, mode, cols=6):
    topic = ROOT / "spotlights" / slug
    meta = json.loads((topic / "meta.json").read_text()); meta["retrieval"] = json.loads((topic / "retrieval.json").read_text())
    st = S.stats(topic, frame)
    t = S.Topic(topic)
    c = C.content(st, meta, meta["spotlight"], design)
    c["headline"] = c["headlines"][0]
    h = 300
    if mode == "regions":
        rows = []
        for p in S.SDG_REGIONS:
            m = t.members.get(p, {})
            yrs = [t.countries[x][1] for x in m if x in t.countries]
            rows.append((S.SHORT[p], sum(1 for y in yrs if y > CUT), sum(1 for y in yrs if y <= CUT), len(m) - len(yrs)))
        rows.sort(key=lambda r: -(r[1] + r[2] + r[3]))
        svg = region_bars(B.STYLES[design], h, rows, "mock")
    else:
        m = t.members_of(t.main_place())
        items = [(SHORTN.get(n, n), t.countries[x][1] if x in t.countries else None) for x, n in m.items()]
        items.sort(key=lambda it: (0 if it[1] and it[1] > CUT else 1 if it[1] else 2, -(it[1] or 0), it[0]))
        svg = tiles(B.STYLES[design], h, items, "mock", cols)
    html = B.page(design, c, svg)
    return html


with sync_playwright() as p:
    br = p.chromium.launch(); tab = br.new_page(viewport={"width": R.W, "height": R.H}, device_scale_factor=2)
    for name, args in [("16-D", ("16-safely-managed-water-world", "D", "D-light", "regions")),
                       ("21-D", ("21-primary-completion-e-se-asia", "D", "Ink", "tiles", 6)),
                       ("09-D", ("09-sanitation-ldcs", "D", "D-dark", "tiles", 8))]:
        slug = [d.name for d in (ROOT / "spotlights").glob(name[:2] + "-*")][0]
        html = build(slug, *args[1:])
        f = OUT / f"{name}.html"; f.write_text(R.build_page(html, "banner.dc.html"))
        tab.goto(f.as_uri()); tab.evaluate("document.fonts.ready"); tab.wait_for_timeout(200)
        tab.screenshot(path=str(OUT / f"{name}.png"), clip={"x": 0, "y": 0, "width": R.W, "height": R.H})
        print(name, slug)
    br.close()
