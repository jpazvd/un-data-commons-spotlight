"""Rebuild the Spotlight table in README.md from each Spotlight's meta.json.

Usage:
    python scripts/build_readme_table.py README.md
    python scripts/build_readme_table.py sync-staging/README.md --spotlights sync-staging/spotlights

The table sits between the markers <!-- spotlights:start --> and <!-- spotlights:end -->.
Spotlight pull requests never edit it: sync-to-public rebuilds it in the public copy, so
open Spotlight pull requests do not conflict with each other over the README. Spotlight
folders are found by the same rule as validate_spotlight.py, which also checks that every
meta.json has the fields used here; the validate workflow runs this script on a copy of
the README so a missing marker fails before merge, not at publication.
"""
import argparse
import json
import os
import pathlib
import re
import sys

from validate_spotlight import spotlight_dirs

START, END = "<!-- spotlights:start -->", "<!-- spotlights:end -->"
HEAD = ["| # | Topic | SDG indicator | Banners | Data retrieved |",
        "|---|-------|---------------|---------|----------------|"]
DESIGN = {"E-dark": "E dark", "E-light": "E light", "D-dark": "D dark", "D-light": "D light", "Ink": "Ink"}


def cell(value) -> str:
    text = ", ".join(map(str, value)) if isinstance(value, list) else str(value)
    return re.sub(r"([\\|\[\]])", r"\\\1", text)


def banners(m: dict) -> str:
    """What the folder publishes: its versions (framing and design) for an experiment topic, else one banner."""
    exp = m.get("experiment") or {}
    versions = exp.get("versions") or []
    if versions:
        order = ["T", "L", "G", "D", "D1", "D2", "D3"]
        versions = sorted(versions, key=lambda v: order.index(v["frame"]) if v["frame"] in order else 99)
        return ", ".join(f"{v['frame']} ({DESIGN.get(v['design'], v['design'])})" for v in versions)
    if exp.get("role") == "run-in":
        return f"one banner (E {exp.get('palette', '')})".replace(" )", ")")
    if exp.get("ground"):
        return f"one banner (D {exp['ground']})"
    if m.get("design"):  # a Spotlight outside any experiment names its design in meta.json (01: design A)
        return f"one banner ({m['design'].split(' (')[0]})"
    return "one banner"


def rows(readme: pathlib.Path, spot_root: pathlib.Path) -> list[str]:
    """One row per Spotlight number. A number held by several folders (Spotlight 22: replacement topics that
    share its versions, 4 Nov 2026) gets one row listing each folder with what it holds."""
    groups = {}
    for d in spotlight_dirs(spot_root)[0]:
        meta_path = d / "meta.json"
        if not meta_path.exists():
            sys.exit(f"FAIL: {meta_path} missing")
        m = json.loads(meta_path.read_text(encoding="utf-8"))
        missing = [k for k in ("title", "sdg_indicator", "retrieved_on") if not m.get(k)]
        if missing:
            sys.exit(f"FAIL: {meta_path} has no {', '.join(missing)}")
        groups.setdefault(d.name.split("-")[0], []).append((d, m))
    out = []
    for num, items in groups.items():
        links, sdgs, kinds, dates = [], [], [], []
        for d, m in items:
            link = pathlib.Path(os.path.relpath(d, readme.parent)).as_posix()
            links.append(f"[{cell(m['title'])}]({link})")
            sdgs.append(cell(m["sdg_indicator"]))
            kinds.append(banners(m))
            dates.append(cell(m["retrieved_on"]))
        uniq = lambda xs: "; ".join(dict.fromkeys(xs))
        out.append(f"| {num} | {'; '.join(links)} | {uniq(sdgs)} | {'; '.join(kinds)} | {uniq(dates)} |")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("readme")
    ap.add_argument("--spotlights", help="spotlights folder (default: next to the README)")
    a = ap.parse_args()
    readme = pathlib.Path(a.readme)
    spot_root = pathlib.Path(a.spotlights) if a.spotlights else readme.parent / "spotlights"
    text = readme.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        sys.exit(f"FAIL: {readme} has no {START} ... {END} markers")
    body = rows(readme, spot_root)
    new = pattern.sub(lambda _: "\n".join([START] + HEAD + body + [END]), text, count=1)
    readme.write_text(new, encoding="utf-8", newline="\n")  # LF on Windows too
    print(f"Wrote {len(body)} Spotlight rows to {readme}")


if __name__ == "__main__":
    main()
