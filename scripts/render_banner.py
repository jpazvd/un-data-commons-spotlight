"""Render a Spotlight banner (.dc.html artboard) to PNG and JPEG.

Usage:
    python scripts/render_banner.py spotlights/01-child-marriage

Reads <spotlight>/banner.dc.html and writes:
    <spotlight>/banner.png   2400x1260 (2x), for LinkedIn and X
    <spotlight>/banner.jpg   1200x630, lightweight copy

Requirements (see README):
    pip install -r requirements.txt && python -m playwright install chromium
    npm install          # fetches the banner fonts (@fontsource) into node_modules/

Fonts are loaded from local files so the render is identical offline.
"""
import pathlib
import re
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
NM = ROOT / "node_modules"
W, H = 1200, 630


def font_face(family, rel, weight, extra=""):
    path = NM / rel
    if not path.exists():
        sys.exit(f"Missing font {path}. Run `npm install` in the repo root.")
    return (f"@font-face{{font-family:'{family}';src:url('{path.as_uri()}') format('woff2');"
            f"font-weight:{weight};font-style:normal;{extra}}}")


def build_page(dc_html: str) -> str:
    # The .dc.html format wraps the design in <x-dc>; <helmet> holds web-font links
    # that we replace with local @font-face rules.
    body = re.search(r"<x-dc>(.*)</x-dc>", dc_html, re.S).group(1)
    body = re.sub(r"<helmet>.*?</helmet>", "", body, flags=re.S)
    css = "\n".join([
        font_face("Archivo", "@fontsource-variable/archivo/files/archivo-latin-wdth-normal.woff2",
                  "100 900", "font-stretch:62% 125%;"),
        *[font_face("IBM Plex Sans",
                    f"@fontsource/ibm-plex-sans/files/ibm-plex-sans-latin-{w}-normal.woff2", w)
          for w in (400, 500, 600)],
        *[font_face("IBM Plex Mono",
                    f"@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-{w}-normal.woff2", w)
          for w in (400, 500)],
        "html,body{margin:0;background:#0D2433}",
    ])
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    spot = pathlib.Path(sys.argv[1]).resolve()
    page = spot / ".render.html"
    page.write_text(build_page((spot / "banner.dc.html").read_text(encoding="utf-8")), encoding="utf-8")
    png, jpg = spot / "banner.png", spot / "banner.jpg"
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
    print(f"wrote {png.relative_to(ROOT)} and {jpg.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
