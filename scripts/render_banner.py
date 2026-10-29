"""Render a banner design (.dc.html artboard) to PNG and JPEG.

Usage:
    python scripts/render_banner.py spotlights/01-child-marriage      (renders <folder>/banner.dc.html)
    python scripts/render_banner.py templates/banner-D-dark.dc.html   (renders any .dc.html file)

Writes, beside the design:
    banner.png (or <name>.png)   2400x1260 (2x), for LinkedIn and X
    banner.jpg (or <name>.jpg)   1200x630, lightweight copy

Requirements (see README):
    pip install -r requirements.txt && python -m playwright install chromium
    npm install          # fetches the banner fonts (@fontsource) into node_modules/

Fonts are loaded from local files so the render is identical offline. The families and weights
come from the design's <helmet> font link; a family missing from FONTS or from node_modules
stops the render instead of falling back to a system font.
"""
import os
import pathlib
import re
import sys
import tempfile
import urllib.parse

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
NM = ROOT / "node_modules"
W, H = 1200, 630

# Local file for each family a design may request; {w} is the weight. Add new families here
# and in package.json.
FONTS = {
    "Archivo": "@fontsource-variable/archivo/files/archivo-latin-wdth-normal.woff2",
    "IBM Plex Sans": "@fontsource/ibm-plex-sans/files/ibm-plex-sans-latin-{w}-normal.woff2",
    "IBM Plex Mono": "@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-{w}-normal.woff2",
    "IBM Plex Sans Condensed":
        "@fontsource/ibm-plex-sans-condensed/files/ibm-plex-sans-condensed-latin-{w}-normal.woff2",
    "Source Serif 4": "@fontsource/source-serif-4/files/source-serif-4-latin-{w}-normal.woff2",
    "Source Sans 3": "@fontsource/source-sans-3/files/source-sans-3-latin-{w}-normal.woff2",
    "Space Grotesk": "@fontsource/space-grotesk/files/space-grotesk-latin-{w}-normal.woff2",
}
# Variable fonts: one file covers the weight range, plus their other axes.
VARIABLE = {"Archivo": ("100 900", "font-stretch:62% 125%;")}
# The latin subsets have no arrows or math operators (→, ≈). Every face takes them from
# Noto Sans Math, so they never come from whatever system font is installed.
SYMBOLS = "@fontsource/noto-sans-math/files/noto-sans-math-latin-400-normal.woff2"
SYMBOL_RANGE = "U+2190-21FF,U+2200-22FF"


def font_file(rel):
    path = NM / rel
    if not path.exists():
        sys.exit(f"Missing font {path}. Run `npm install` in the repo root.")
    return path.as_uri()


def font_face(family, rel, weight, extra=""):
    return (f"@font-face{{font-family:'{family}';src:url('{font_file(rel)}') format('woff2');"
            f"font-weight:{weight};font-style:normal;{extra}}}")


def requested_fonts(helmet):
    """(family, [weights]) for each family=... in the helmet's Google Fonts link."""
    out = []
    for fam, spec in re.findall(r"family=([^:&\"']+)(?::([^&\"']*))?", helmet):
        fam = urllib.parse.unquote_plus(fam)
        weights = ["400"]
        if spec and "@" in spec:
            axes, values = spec.split("@", 1)
            axes = axes.split(",")
            if "wght" in axes:
                weights = [v.split(",")[axes.index("wght")] for v in values.split(";")]
        out.append((fam, weights))
    return out


def build_page(dc_html: str, name: str) -> str:
    # The .dc.html format wraps the design in <x-dc>; <helmet> holds web-font links
    # that we replace with local @font-face rules.
    m = re.search(r"<x-dc>(.*)</x-dc>", dc_html, re.S)
    if not m:
        sys.exit(f"{name}: no <x-dc> ... </x-dc> wrapper, so it is not a .dc.html design")
    helmet = re.search(r"<helmet>(.*?)</helmet>", m.group(1), re.S)
    fonts = requested_fonts(helmet.group(1)) if helmet else []
    if not fonts:
        sys.exit(f"{name}: no font link in <helmet>, so the fonts to load are unknown")
    faces = []
    for fam, weights in fonts:
        if fam not in FONTS:
            sys.exit(f"{name}: font '{fam}' is not in FONTS in {pathlib.Path(__file__).name}")
        if fam in VARIABLE:
            weights, extra = [VARIABLE[fam][0]], VARIABLE[fam][1]
        else:
            extra = ""
        for w in weights:
            faces.append(font_face(fam, FONTS[fam].format(w=w), w, extra))
            faces.append(font_face(fam, SYMBOLS, w, f"{extra}unicode-range:{SYMBOL_RANGE};"))
    body = re.sub(r"<helmet>.*?</helmet>", "", m.group(1), flags=re.S)
    css = "\n".join(faces + ["html,body{margin:0;background:#0D2433}"])
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>"


def shown(path):
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    target = pathlib.Path(sys.argv[1]).resolve()
    if target.is_dir():    # a Spotlight folder: render its banner.dc.html
        folder, stem, src = target, "banner", target / "banner.dc.html"
        if not src.is_file():
            sys.exit(f"{shown(target)} has no banner.dc.html")
    elif target.is_file():  # a single design file: render <name>.png / <name>.jpg beside it
        if not target.name.lower().endswith(".dc.html"):
            sys.exit(f"{shown(target)} is not a .dc.html file")
        folder, stem, src = target.parent, target.name[:-len(".dc.html")], target
    else:
        sys.exit(f"No such file or folder: {sys.argv[1]}")
    # A page per render, so parallel renders in one folder never read each other's page.
    fd, tmp = tempfile.mkstemp(prefix=f".{stem}.", suffix=".render.html", dir=folder)
    os.close(fd)
    page = pathlib.Path(tmp)
    page.write_text(build_page(src.read_text(encoding="utf-8"), src.name), encoding="utf-8")
    png, jpg = folder / f"{stem}.png", folder / f"{stem}.jpg"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            tab = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
            tab.goto(page.as_uri())
            tab.evaluate("document.fonts.ready")
            tab.wait_for_timeout(300)
            tab.screenshot(path=str(png), clip={"x": 0, "y": 0, "width": W, "height": H})
            browser.close()
    finally:
        page.unlink(missing_ok=True)
    Image.open(png).convert("RGB").resize((W, H), Image.LANCZOS).save(
        jpg, quality=86, optimize=True, progressive=True)
    print(f"wrote {shown(png)} and {shown(jpg)}")


if __name__ == "__main__":
    main()
