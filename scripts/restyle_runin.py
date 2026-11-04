"""Apply the review-round-1 header and footer rules (2 Nov 2026) to the hand-authored banners of Spotlights 01 to 04.

Usage:
    python scripts/restyle_runin.py            # rewrites spotlights/0[1-4]-*/banner.dc.html, then run render_banner.py

A banner that already carries the new header and footer is left as it is, so the command can be re-run on the
committed files (it reports "already restyled").

Rules, as for experiment 002 (scripts/banner002.py): the series line reads "UN Data Commons Spotlight" with no number;
no byline; a left-aligned footer with the data source, the SDG series code, the extraction date (meta.json
retrieved_on) and "Data and code: @jpazvd on GitHub"; a Notes line only if the banner shows an acronym that is not an
agency, organization or monitoring programme name. None of the four banners shows one, so none gets a Notes line.
Every value comes from the folder's meta.json and retrieval.json; nothing else in the banner changes.
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
HANDLE = "@jpazvd"


def day(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {MONTHS[m - 1]} {y}"


def restyle(folder):
    page = folder / "banner.dc.html"
    s = page.read_text(encoding="utf-8")
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    ind = json.loads((folder / "retrieval.json").read_text(encoding="utf-8"))["indicator"]
    code, extracted = ind["sdg_series_code"], day(meta["retrieved_on"])
    if ">UN Data Commons Spotlight" in s and "Data and code: <span style=\"font-weight: 600; color: " in s:
        return None  # already restyled
    if meta["spotlight"] == 1:  # the pre-identity layout: mono header with two spans, 12 px footer with two spans
        s, n = re.subn(r"<span>UN System Data Commons · Spotlight 01</span>", "<span>UN Data Commons Spotlight</span>", s)
        assert n == 1
        old = re.search(r'(<div style="display: flex; justify-content: space-between; gap: 24px; font-size: 12px; '
                        r'line-height: 1.4; color: #8FB3C7; border-top: 1px solid #23465B; padding-top: 12px">)\n'
                        r'<span>(.*?)</span>\n<span style="flex: 0 0 auto;[^"]*">(.*?)</span>\n</div>', s, re.S)
        assert old, "01 footer not found"
        src = old.group(2).replace("Source: United Nations, SDG Global Database (UNSD), indicator 5.3.1, via the UN System "
                                   "Data Commons.", f"Data: UN SDG Global Database (UNSD), series {code}, extracted "
                                   f"{extracted}, via the UN System Data Commons.")
        new = (f'<div style="display: flex; flex-direction: column; gap: 2px; font-size: 12px; line-height: 1.4; '
               f'color: #8FB3C7; border-top: 1px solid #23465B; padding-top: 12px; text-align: left">\n'
               f'<div>{src} <span style="white-space: nowrap">Data and code: <span style="font-weight: 600; color: '
               f'#FFFFFF">{HANDLE}</span> on GitHub</span></div>\n</div>')
        return s.replace(old.group(0), new)
    s, n = re.subn(rf">Data Commons Spotlight {meta['spotlight']:02d} · SDG ", ">UN Data Commons Spotlight · SDG ", s)
    assert n == 1, folder
    old = re.search(r'<div style="display: flex; justify-content: space-between; align-items: baseline; gap: 24px; '
                    r'border-top: 2px solid (#[0-9A-F]{6}); padding-top: 12px; font-size: 22px; color: (#[0-9A-F]{6})">\n'
                    r'<span style="font-weight: 600; white-space: nowrap; color: (#[0-9A-F]{6})">João Pedro Azevedo</span>\n'
                    r'<span>Data: (.*?) via UN SDG Global Database · data \+ code on GitHub</span>\n</div>', s)
    assert old, f"{folder.name}: footer not found"
    rule, colour, strong, custodian = old.groups()
    line = f"Data: {custodian} via UN SDG Global Database, series {code}, extracted {extracted}"
    new = (f'<div style="display: flex; flex-direction: column; gap: 2px; border-top: 2px solid {rule}; padding-top: 10px; '
           f'font-size: 16px; line-height: 1.3; color: {colour}; text-align: left">\n'
           f'<div>{html.escape(line)} · <span style="white-space: nowrap">Data and code: <span style="font-weight: 600; '
           f'color: {strong}">{HANDLE}</span> on GitHub</span></div>\n</div>')
    return s.replace(old.group(0), new)


if __name__ == "__main__":
    for folder in sorted((ROOT / "spotlights").glob("0[1-4]-*")):
        out = restyle(folder)
        if out is None:
            print("already restyled", folder.name)
            continue
        (folder / "banner.dc.html").write_text(out, encoding="utf-8", newline="\n")
        print("restyled", folder.name)
