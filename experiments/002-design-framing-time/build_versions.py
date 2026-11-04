"""Build experiment 002 versions: stats, banner, captions and alt text, rendered and measured.

Usage:
    python build_versions.py SPEC.json
SPEC.json: [{"topic_dir": "spotlights/05-...", "spotlight": 5, "frame": "T", "design": "Ink", "feed_tag": "#EconSky"}, ...]

For each version: versions/<F>/stats.json (scripts/spotlight002.py), banner.dc.html (scripts/banner002.py with the
words of scripts/copy002.py), banner.png and banner.jpg (2400x1260 and 1200x630, the same renderer as
scripts/render_banner.py), captions.md and alt.txt. The first headline that fits in two lines without the page
overflowing is kept; a version where none fits, or the evidence line wraps, is reported and not written.
A headline that does not name what is measured (copy002.names_construct) is never kept. If the evidence line wraps,
its shorter form (evidence_alt) is tried before moving to the next headline.
"""
import json
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import banner002 as B  # noqa: E402
import copy002 as C  # noqa: E402
import render_banner as R  # noqa: E402
import spotlight002 as S  # noqa: E402
from PIL import Image  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

MEASURE = """() => {
  const root = document.querySelector('body > div');
  const h1 = document.querySelector('h1');
  const p = h1.nextElementSibling;
  const lh = parseFloat(getComputedStyle(h1).lineHeight);
  const plh = parseFloat(getComputedStyle(p).lineHeight);
  const svg = document.querySelector('svg').getBoundingClientRect();
  const by = root.lastElementChild.getBoundingClientRect();
  return {lines: Math.round(h1.getBoundingClientRect().height / lh),
          ev_lines: Math.round(p.getBoundingClientRect().height / plh),
          overflow: root.scrollHeight > 631 || svg.bottom > by.top + 1 || by.bottom > 631};
}"""


SPACE = """() => {
  const root = document.querySelector('body > div');
  const p = document.querySelector('h1').nextElementSibling;
  const by = root.lastElementChild.getBoundingClientRect();
  return by.top - 12 - (p.getBoundingClientRect().bottom + 12);
}"""


def write_page(out, html):
    fd, tmp = tempfile.mkstemp(prefix=".m.", suffix=".html", dir=out)
    os.close(fd)
    page = pathlib.Path(tmp)
    page.write_text(R.build_page(html, "banner.dc.html"), encoding="utf-8")
    return page


def run(spec):
    report = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        tab = browser.new_page(viewport={"width": R.W, "height": R.H}, device_scale_factor=2)
        for v in spec:
            topic = ROOT / v["topic_dir"]
            meta = json.loads((topic / "meta.json").read_text(encoding="utf-8"))
            meta["retrieval"] = json.loads((topic / "retrieval.json").read_text(encoding="utf-8"))
            f, design = v["frame"], v["design"]
            out = topic / "versions" / f
            out.mkdir(parents=True, exist_ok=True)
            st = S.stats(topic, f)
            (out / "stats.json").write_text(json.dumps(st, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            if not st.get("ok"):
                report.append((v["topic_dir"], f, design, "NOT SUPPORTED: " + st.get("reason", "")))
                continue
            tf = {}
            if f != "T" and meta.get("target_basis") not in (None, "none"):
                sT = S.stats(topic, "T")
                if sT.get("ok"):
                    cT = C.content(sT, meta, v["spotlight"], design)
                    tf = {"tfig": cT["tfig"], "tfig_short": cT["tfig_short"]}
            c = {**C.content(st, meta, v["spotlight"], design), **tf}
            chosen = None
            if c.get("headlines_last"):  # a last resort with its own signal phrase
                c["headlines"] = c["headlines"] + [c["headlines_last"][0]]
            for head in c["headlines"]:
                if c.get("headlines_last") and head == c["headlines_last"][0]:
                    c["signal"] = c["headlines_last"][1]
                if c["signal"] and head.count(c["signal"]) != 1:
                    continue
                if not C.names_construct(head, st["family"]):
                    continue
                # first pass: how much height does the chart get under this headline?
                small = C.content(st, meta, v["spotlight"], design, h=60)
                sm = {**small, "headline": head}
                if small.get("headlines_last") and head == small["headlines_last"][0]:
                    sm["signal"] = small["headlines_last"][1]
                if small.get("evidence_alt") and head == small["headlines"][-1]:
                    sm["evidence"] = small["evidence_alt"]
                page = write_page(out, B.page(design, sm, small["svg"]))
                tab.goto(page.as_uri()); tab.evaluate("document.fonts.ready"); tab.wait_for_timeout(120)
                avail = tab.evaluate(SPACE)
                page.unlink(missing_ok=True)
                c = {**C.content(st, meta, v["spotlight"], design, h=max(150, min(340, int(avail) - 6))), **tf}
                if c.get("headlines_last") and head == c["headlines_last"][0]:
                    c["signal"] = c["headlines_last"][1]
                if c["signal"] and head.count(c["signal"]) != 1:
                    continue
                cc = {**c, "headline": head}
                if c.get("evidence_alt") and head == c["headlines"][-1]:
                    cc["evidence"] = c["evidence_alt"]
                html = B.page(design, cc, c["svg"])
                page = write_page(out, html)
                tab.goto(page.as_uri())
                tab.evaluate("document.fonts.ready")
                tab.wait_for_timeout(150)
                m = tab.evaluate(MEASURE)
                if m["ev_lines"] > 1 and c.get("evidence_alt") and cc["evidence"] != c["evidence_alt"]:
                    page.unlink(missing_ok=True)
                    cc["evidence"] = c["evidence_alt"]
                    html = B.page(design, cc, c["svg"])
                    page = write_page(out, html)
                    tab.goto(page.as_uri())
                    tab.evaluate("document.fonts.ready")
                    tab.wait_for_timeout(150)
                    m = tab.evaluate(MEASURE)
                if m["lines"] <= 2 and not m["overflow"] and m["ev_lines"] <= 1:
                    chosen = (head, html, page, m, cc)
                    break
                page.unlink(missing_ok=True)
            if not chosen:
                report.append((v["topic_dir"], f, design, f"NO FIT: {c['headlines']} last={m}"))
                continue
            head, html, page, m, c = chosen
            (out / "banner.dc.html").write_text(html, encoding="utf-8")
            png, jpg = out / "banner.png", out / "banner.jpg"
            tab.screenshot(path=str(png), clip={"x": 0, "y": 0, "width": R.W, "height": R.H})
            page.unlink(missing_ok=True)
            Image.open(png).convert("RGB").resize((R.W, R.H), Image.LANCZOS).save(jpg, quality=86, optimize=True,
                                                                                   progressive=True)
            caps = C.captions(c, head, meta, v.get("feed_tag") or meta["experiment"]["feed_tag"], f)
            (out / "captions.md").write_text(f"# Spotlight {v['spotlight']:02d}-{f} · {meta['title']}: post captions\n\n"
                                             + caps, encoding="utf-8")
            alt = B.esc(c["svg"].split('aria-label="', 1)[1].split('"', 1)[0])
            (out / "alt.txt").write_text(f"{head}. {c['evidence']} " + html_unescape(alt) + "\n", encoding="utf-8")
            report.append((v["topic_dir"], f, design, f"ok: {head}"))
        browser.close()
    return report


def html_unescape(s):
    import html
    return html.unescape(html.unescape(s))


if __name__ == "__main__":
    spec = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    for r in run(spec):
        print(" | ".join(map(str, r)))
