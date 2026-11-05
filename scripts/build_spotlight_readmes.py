#!/usr/bin/env python3
"""Write a README.md in every Spotlight folder, and in every version folder, so that GitHub shows the banners.

GitHub lists a folder's files and renders only its README.md, so without one a Spotlight folder shows no banner
(and an experiment topic keeps its banners two levels down, in versions/<F>/). Each README shows the banner(s),
the headline as drawn, and links to the post text, every number, the alt text, the design source and the data.

Usage (repo root):
    python scripts/build_spotlight_readmes.py                    # write them under spotlights/
    python scripts/build_spotlight_readmes.py --check            # exit 1 if a README differs from what it would write
    python scripts/build_spotlight_readmes.py --root sync-staging  # the same for another copy (sync-to-public)

Everything comes from the files in the folder (meta.json, banner.dc.html, the file list); nothing is typed.
--check fails on a README that is out of date; a folder with no README yet is reported, not failed (the sync
writes it for the public repo, and the next run of this script for this one).
"""
import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_readme_table as T  # noqa: E402

FRAMES = {"T": "what it would take", "L": "the long view", "G": "behind the average", "D": "the data behind it",
          "D1": "the data behind it (1 of 3)", "D2": "the data behind it (2 of 3)", "D3": "the data behind it (3 of 3)"}
ORDER = ["T", "L", "G", "D", "D1", "D2", "D3"]
NOTE = "<!-- Written by scripts/build_spotlight_readmes.py from the files in this folder; do not edit. -->"


def headline(folder: pathlib.Path) -> str:
    s = (folder / "banner.dc.html").read_text(encoding="utf-8")
    m = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
    text = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))) if m else ""
    return re.sub(r"\s+", " ", text).strip()


def alt(text: str) -> str:
    return re.sub(r"[\[\]]", "", text)


def links(prefix: str, folder: pathlib.Path) -> str:
    items = [("Post text and comments", "captions.md"), ("Every number", "stats.json"), ("Alt text", "alt.txt"),
             ("Design source", "banner.dc.html"), ("Full-size banner", "banner.png")]
    return " · ".join(f"[{label}]({prefix}{name})" for label, name in items if (folder / name).exists())


def banner_block(prefix: str, folder: pathlib.Path) -> list[str]:
    head = headline(folder)
    return [f"[![{alt(head)}]({prefix}banner.jpg)]({prefix}banner.png)", "", f"**{head}**", "",
            links(prefix, folder), ""]


def header(m: dict) -> list[str]:
    bits = [f"SDG {m['sdg_indicator']}"]
    if m.get("sdg_series_code"):
        bits.append(f"series {m['sdg_series_code']}")
    if m.get("retrieved_on"):
        bits.append(f"data retrieved {m['retrieved_on']}")
    return [" · ".join(bits), ""]


def data_section(spot: pathlib.Path) -> list[str]:
    out = ["## Data and calls", ""]
    files = sorted(p.relative_to(spot).as_posix() for p in (spot / "data").rglob("*") if p.is_file()) \
        if (spot / "data").exists() else []
    for name in ("meta.json", "retrieval.json", "metadata.rdm.json") + (("stats.json",) if (spot / "stats.json").exists() else ()):
        if (spot / name).exists():
            files.append(name)
    out += [f"- [{f}]({f})" for f in files]
    out += ["", "Every number re-derives from these files: `python scripts/reproduce.py " + f"spotlights/{spot.name}`", ""]
    return out


def topic_readme(spot: pathlib.Path) -> dict[pathlib.Path, str]:
    m = json.loads((spot / "meta.json").read_text(encoding="utf-8"))
    nn = f"{m['spotlight']:02d}"
    out = {}
    lines = [f"# Spotlight {nn} · {m['title']}", "", NOTE, ""] + header(m)
    versions = (m.get("experiment") or {}).get("versions") or []
    versions = [v for v in versions if (spot / "versions" / v["frame"] / "banner.dc.html").exists()]
    if versions:
        versions.sort(key=lambda v: ORDER.index(v["frame"]) if v["frame"] in ORDER else 99)
        lines += [f"{len(versions)} version{'s' if len(versions) > 1 else ''} of this topic, each with its own headline "
                  "framing and banner design.", ""]
        for v in versions:
            f = v["frame"]
            vdir = spot / "versions" / f
            title = f"{f} · {FRAMES.get(f, f)} · template {T.DESIGN.get(v['design'], v['design'])}"
            lines += [f"## {title}", ""] + banner_block(f"versions/{f}/", vdir)
            out[vdir / "README.md"] = "\n".join(
                [f"# Spotlight {nn}-{f} · {m['title']}", "", NOTE, "", f"{FRAMES.get(f, f).capitalize()} · template "
                 f"{T.DESIGN.get(v['design'], v['design'])} · [all versions of this topic](../../)", ""]
                + banner_block("", vdir)).rstrip() + "\n"
    elif (spot / "banner.dc.html").exists():
        design = T.banners(m).replace("one banner (", "").rstrip(")")
        design = f"template {design}" if design[:2] in ("E ", "D ") else design
        lines += [f"Design: {design}.", ""] + banner_block("", spot)
    lines += data_section(spot)
    out[spot / "README.md"] = "\n".join(lines).rstrip() + "\n"
    return out


def main(argv):
    check = "--check" in argv
    root = pathlib.Path(argv[argv.index("--root") + 1]) if "--root" in argv else pathlib.Path(__file__).resolve().parent.parent
    stale, missing, written = [], [], 0
    for spot in sorted(p for p in (root / "spotlights").glob("[0-9]*") if p.is_dir()):
        for path, text in topic_readme(spot).items():
            if check:
                if not path.exists():
                    missing.append(path)
                elif path.read_text(encoding="utf-8") != text:
                    stale.append(path)
            else:
                path.write_text(text, encoding="utf-8", newline="\n")
                written += 1
    if check:
        for p in missing:
            print(f"note: no README yet: {p.relative_to(root)} (run scripts/build_spotlight_readmes.py)")
        for p in stale:
            print(f"FAIL: out of date: {p.relative_to(root)} (run scripts/build_spotlight_readmes.py)")
        sys.exit(1 if stale else 0)
    print(f"Wrote {written} README.md files under {root / 'spotlights'}")


if __name__ == "__main__":
    main(sys.argv[1:])
