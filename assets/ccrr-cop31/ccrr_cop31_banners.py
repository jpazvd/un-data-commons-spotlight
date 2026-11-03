#!/usr/bin/env python3
"""
CCRR 2026 — COP31 social banners (reproducible generator)

Builds three 1080x1350 banners (SVG + PNG) in the house style
(IBM Plex Sans / Mono, UNICEF cyan #1CABE2, slate ink, warm paper):

  B1  Children exposed to at least N of eight climate hazards  (ranked bars)
  B3  Heat and education stat tiles
  B4  Finance-day stat tiles (LLDCs, adaptation returns)

B1 is computed from the published pipeline data in the unicef/CCRR repository
(Country_level_hazard_exposure/Hazard_Population_Exposure.csv, admin-0 rows).
The script prints a reconciliation table against the figures printed in the
report so that any drift between repo and PDF is visible before posting.
B3 and B4 use figures as printed in the report (see FIGURES below).

Usage:
  python3 ccrr_cop31_banners.py --repo /path/to/unicef/ccrr --out ./out
"""
import argparse, os, re, sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

# ---------------------------------------------------------------- style
CYAN   = "#1CABE2"   # UNICEF cyan
INK    = "#1D2A33"   # slate ink
INK2   = "#5B6770"   # secondary text
GRAY   = "#C5CED6"   # de-emphasis bars
PAPER  = "#FAF7F2"   # warm paper
RULE   = "#E4DED5"
W, H   = 10.8, 13.5  # inches -> 1080x1350 @ 100 dpi (PNG exported at 200 dpi)

SOURCE = ("Source: UNICEF, Children's Climate Risk Report 2026 — Global Child Hazard "
          "Database; WorldPop children's population layer.")
LINK   = "data.unicef.org/resources/childrens-climate-risk-report-2026"
HAZARDS = ("Eight climate hazards: riverine floods, coastal floods, droughts, tropical storms, "
           "heatwaves, extreme heat, fires, sand and dust storms.")

def setup_fonts():
    fdir = os.path.expanduser("~/.local/share/fonts")
    for f in os.listdir(fdir) if os.path.isdir(fdir) else []:
        if f.lower().endswith(".ttf"):
            fm.fontManager.addfont(os.path.join(fdir, f))
    names = {f.name for f in fm.fontManager.ttflist}
    sans = "IBM Plex Sans" if "IBM Plex Sans" in names else "DejaVu Sans"
    mono = "IBM Plex Mono" if "IBM Plex Mono" in names else "DejaVu Sans Mono"
    plt.rcParams.update({"font.family": sans, "svg.fonttype": "none",
                         "figure.facecolor": PAPER, "savefig.facecolor": PAPER})
    return sans, mono

def canvas():
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1080); ax.set_ylim(1350, 0); ax.axis("off")
    return fig, ax

def header(ax, kicker, title_lines, sub=None, y0=90):
    ax.text(72, y0, kicker, color=CYAN, fontsize=13, fontweight="semibold", va="top")
    y = y0 + 46
    for line in title_lines:
        ax.text(72, y, line, color=INK, fontsize=34, fontweight="bold", va="top"); y += 52
    if sub:
        ax.text(72, y + 10, sub, color=INK2, fontsize=15, va="top"); y += 40
    return y

def footer(ax, mono, extra=None):
    ax.plot([72, 1008], [1218, 1218], color=RULE, lw=1.2)
    y = 1236
    if extra:
        ax.text(72, y, extra, color=INK2, fontsize=10.5, va="top", wrap=True); y += 34
    ax.text(72, y, SOURCE, color=INK2, fontsize=10.5, va="top", wrap=True); y += 34
    ax.text(72, y, LINK, color=CYAN, fontsize=10.5, va="top", family=mono)
    ax.text(1008, y, "#COP31", color=INK2, fontsize=11, va="top", ha="right", family=mono)

def fmt(m):  # millions -> label
    return f"{m/1000:.1f} billion" if m >= 950 else f"{m:,.0f} million"

# ---------------------------------------------------------------- data
REPORT_MHC = {1: 2300, 2: 2000, 3: 1100, 4: 364, 5: 53, 6: 4, 7: 0.123}   # as printed (p.4, p.12)

def load_mhc(repo):
    p = os.path.join(repo, "Country_level_hazard_exposure", "Hazard_Population_Exposure.csv")
    df = pd.read_csv(p, low_memory=False)
    a0 = df[df["ucode"].str.match(r"^[A-Z]{3}_V1$", na=False)]
    out = {k: a0[f"pop_topic_ge_{k}"].sum() / 1e6 for k in range(1, 9)}
    out["child_pop"] = a0["pop_child_total"].sum() / 1e6
    return out

def reconcile(mhc):
    print(f"{'at least N hazards':22s}{'repo (M)':>12s}{'report':>12s}")
    for k in range(1, 8):
        print(f"{k:<22d}{mhc[k]:>12.1f}{REPORT_MHC[k]:>12}")
    print(f"child population (repo): {mhc['child_pop']:.0f} M")

# ---------------------------------------------------------------- banners
def banner_bars(mhc, out, mono):
    fig, ax = canvas()
    y = header(ax, "CHILDREN'S CLIMATE RISK REPORT 2026",
               ["1.1 billion children are exposed", "to at least three climate hazards"],
               "Number of children exposed to at least N of the eight climate hazards analysed")
    ks = [1, 2, 3, 4, 5, 6]
    vals = [mhc[k] for k in ks]
    top, bottom = y + 70, 1150
    bh = 86; gap = (bottom - top - bh * len(ks)) / (len(ks) - 1)
    x0, xmax = 300, 1008
    scale = (xmax - x0) / max(vals)
    for i, (k, v) in enumerate(zip(ks, vals)):
        yy = top + i * (bh + gap)
        col = CYAN if k == 3 else GRAY
        wpx = max(v * scale, 6)
        ax.add_patch(FancyBboxPatch((x0, yy), wpx, bh, boxstyle="round,pad=0,rounding_size=4",
                                    fc=col, ec="none"))
        ax.text(x0 - 22, yy + bh / 2, f"At least {k}", color=INK if k == 3 else INK2,
                fontsize=19, fontweight="semibold" if k == 3 else "normal", ha="right", va="center")
        label = fmt(v)
        inside = wpx > 260
        ax.text(x0 + wpx - 16 if inside else x0 + wpx + 14, yy + bh / 2, label,
                color=("white" if k == 3 else INK) if inside else INK,
                fontsize=21, fontweight="bold", ha="right" if inside else "left", va="center")
    ax.text(x0, top - 26, "children, 2025 (all countries, areas and territories)", color=INK2,
            fontsize=12, va="bottom")
    footer(ax, mono, HAZARDS)
    save(fig, out, "ccrr_cop31_b1_multihazard")

def tiles(ax, items, y0, mono):
    y = y0
    for big, unit, desc in items:
        ax.add_patch(FancyBboxPatch((72, y), 936, 250, boxstyle="round,pad=0,rounding_size=10",
                                    fc="white", ec=RULE, lw=1.2))
        ax.plot([72, 72], [y + 18, y + 232], color=CYAN, lw=6, solid_capstyle="round")
        ax.text(110, y + 34, big, color=INK, fontsize=54, fontweight="bold", va="top")
        ax.text(110, y + 112, unit, color=CYAN, fontsize=16, fontweight="semibold", va="top")
        ax.text(110, y + 150, desc, color=INK2, fontsize=15.5, va="top", wrap=True)
        y += 280
    return y

def banner_heat(out, mono):
    fig, ax = canvas()
    y = header(ax, "CHILDREN'S CLIMATE RISK REPORT 2026",
               ["Heat is already disrupting", "children's learning"])
    tiles(ax, [
        ("1.5 billion", "CHILDREN EXPOSED TO HEATWAVES",
         "More frequent, longer or more severe heatwaves, measured against each area's own\nlong-term average."),
        ("1.2 billion", "CHILDREN EXPOSED TO EXTREME HEAT",
         "Days above a fixed threshold of 35°C."),
        ("242 million", "STUDENTS WITH SCHOOLING DISRUPTED IN 2024",
         "At least 242 million students in 85 countries and territories had their schooling\ndisrupted by climate-related hazardous events in 2024."),
    ], y + 50, mono)
    footer(ax, mono, "Heat figures: children under 18, 2025. Schooling figure: UNICEF analysis cited in the report (Chapter 4).")
    save(fig, out, "ccrr_cop31_b3_heat_education")

def banner_finance(out, mono):
    fig, ax = canvas()
    y = header(ax, "CHILDREN'S CLIMATE RISK REPORT 2026",
               ["Adaptation finance has to reach", "where children are most exposed"])
    tiles(ax, [
        ("268 million", "CHILDREN LIVE IN LANDLOCKED DEVELOPING COUNTRIES",
         "About 11 per cent of the world's children, on 12 per cent of the world's land surface."),
        ("nearly 20%", "OF GLOBAL DROUGHTS IN THE PAST DECADE HIT LLDCs",
         "A disproportionate share of drought exposure, compounded by constrained fiscal space\nand difficult access to international climate finance."),
        ("US$10", "IN BENEFITS FOR EVERY US$1 INVESTED IN ADAPTATION",
         "Over a ten-year period, according to World Resources Institute analysis cited in the\nreport's recommendations."),
    ], y + 50, mono)
    footer(ax, mono, "Figures as printed in the report (Chapters 5 and 6).")
    save(fig, out, "ccrr_cop31_b4_finance")

def save(fig, out, name):
    os.makedirs(out, exist_ok=True)
    fig.savefig(os.path.join(out, name + ".svg"))
    fig.savefig(os.path.join(out, name + ".png"), dpi=200)
    plt.close(fig)
    print("wrote", name)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True); ap.add_argument("--out", default="out")
    a = ap.parse_args()
    sans, mono = setup_fonts(); print("fonts:", sans, "/", mono)
    mhc = load_mhc(a.repo); reconcile(mhc)
    banner_bars(mhc, a.out, mono); banner_heat(a.out, mono); banner_finance(a.out, mono)
