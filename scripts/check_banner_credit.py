#!/usr/bin/env python3
"""Check the credit line on every banner design against R42 (docs/banner-guidance/BANNER_GUIDANCE.md).

  Spotlight banners (spotlights/**/*.dc.html): no author name anywhere; the GitHub handle (@jpazvd) present,
      since the Spotlight's data and code are published in the public repository.
  Event and campaign banners (assets/**/*.dc.html): never the author name in the footer, and the GitHub handle
      only when .github/public-whitelist.txt publishes the banner (its data and code are then public). The name
      may appear in the body as content (a speaker in a panel line-up); only the footer, the element drawn with a
      top rule, is checked, children included. Text is compared after HTML entities are decoded.

Usage:  python scripts/check_banner_credit.py            exits 1 and lists the files that break the rule
"""
import html
import importlib.util
import pathlib
import re
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
NAME = "João Pedro Azevedo"
HANDLE = "@jpazvd"
TAGS = re.compile(r"<[^>]+>")
# The footer of the event-banner generators: a div whose style draws a 2 px top rule.
TOP_RULE = re.compile(r"border-top:\s*2px solid")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


def text(page: str) -> str:
    return html.unescape(TAGS.sub("", page))


class Footers(HTMLParser):
    """Text of every div drawn with a 2 px top rule, with all its children, entities decoded."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0  # elements open inside the current footer; 0 outside a footer
        self.found = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        if self.depth:
            self.depth += 1
        elif tag == "div" and TOP_RULE.search(dict(attrs).get("style") or ""):
            self.depth = 1
            self.found.append("")

    def handle_endtag(self, tag):
        if self.depth and tag not in VOID:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.found[-1] += data


def footers(page: str) -> list:
    parser = Footers()
    parser.feed(page)
    parser.close()
    return parser.found


def published(rel: str) -> bool:
    """True when the sync publishes this path, using the whitelist matcher of .github/stage_public.py."""
    stage = ROOT / ".github" / "stage_public.py"
    if not stage.exists():  # the public repository carries neither the whitelist nor assets/
        return False
    spec = importlib.util.spec_from_file_location("stage_public", stage)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return any(mod.to_regex(src).match(rel) for _, src, _ in mod.entries())


def main() -> int:
    problems = []
    for f in sorted(ROOT.glob("spotlights/**/*.dc.html")):
        t = text(f.read_text(encoding="utf-8"))
        if NAME in t:
            problems.append(f"{f.relative_to(ROOT)}: Spotlight banner carries the author name")
        if HANDLE not in t:
            problems.append(f"{f.relative_to(ROOT)}: Spotlight banner lacks the GitHub handle {HANDLE}")
    for f in sorted(ROOT.glob("assets/**/*.dc.html")):
        rel = f.relative_to(ROOT).as_posix()
        found = footers(f.read_text(encoding="utf-8"))
        if not found:
            problems.append(f"{rel}: no footer found (expected a div with a 2px top rule)")
        for ft in found:
            if NAME in ft:
                problems.append(f"{rel}: event banner footer carries the author name")
            if HANDLE in ft and not published(rel):
                problems.append(f"{rel}: event banner footer carries {HANDLE}, but the public repository does not "
                                "publish this banner's data and code")
    for p in problems:
        print(p)
    n_s = len(list(ROOT.glob("spotlights/**/*.dc.html")))
    n_a = len(list(ROOT.glob("assets/**/*.dc.html")))
    print(f"checked {n_s} Spotlight and {n_a} event banner designs: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
