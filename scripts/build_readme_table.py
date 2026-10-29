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
HEAD = ["| # | Topic | SDG indicator | Data retrieved |", "|---|-------|---------------|----------------|"]


def cell(value) -> str:
    text = ", ".join(map(str, value)) if isinstance(value, list) else str(value)
    return re.sub(r"([\\|\[\]])", r"\\\1", text)


def rows(readme: pathlib.Path, spot_root: pathlib.Path) -> list[str]:
    out = []
    for d in spotlight_dirs(spot_root)[0]:
        meta_path = d / "meta.json"
        if not meta_path.exists():
            sys.exit(f"FAIL: {meta_path} missing")
        m = json.loads(meta_path.read_text(encoding="utf-8"))
        missing = [k for k in ("title", "sdg_indicator", "retrieved_on") if not m.get(k)]
        if missing:
            sys.exit(f"FAIL: {meta_path} has no {', '.join(missing)}")
        link = pathlib.Path(os.path.relpath(d, readme.parent)).as_posix()
        out.append(f"| {d.name.split('-')[0]} | [{cell(m['title'])}]({link}) | {cell(m['sdg_indicator'])} "
                   f"| {cell(m['retrieved_on'])} |")
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
