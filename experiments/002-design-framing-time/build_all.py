"""Rebuild every experiment 002 Spotlight from the saved Data Commons responses, in one command.

Usage (from the repo root or this folder):
    python experiments/002-design-framing-time/build_all.py            # all 36 topics, 108 versions
    python experiments/002-design-framing-time/build_all.py 05 13      # only these Spotlights

Steps, all from committed files:
  1. For each topic in topics.csv, build_topic_data.py writes spotlights/<slug>/data/*.csv, retrieval.json and
     meta.json from data/raw/ (the verbatim responses); meta.json then gets the topic's versions from
     assignment.csv (X rows, by period) and its supported framings from topics.csv.
  2. build_versions.py writes each assigned version: stats.json (scripts/spotlight002.py), the words
     (scripts/copy002.py), banner.dc.html (scripts/banner002.py), banner.png and banner.jpg (Chromium through
     Playwright, fonts from node_modules as scripts/render_banner.py), captions.md and alt.txt.
Requirements: pip install -r requirements.txt; npm ci (fonts); python -m playwright install chromium.
"""
import csv
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import build_topic_data as BT  # noqa: E402
import build_versions as BV  # noqa: E402


def main(only=()):
    topics = list(csv.DictReader(open(HERE / "topics.csv", encoding="utf-8")))
    rows = list(csv.DictReader(open(HERE / "assignment.csv", encoding="utf-8")))
    spec = []
    for t in topics:
        nn = int(t["spotlight"])
        if only and nn not in only:
            continue
        folder = ROOT / "spotlights" / t["slug"]
        missing = BT.build(t["proposal"], folder, nn, t["slug"])
        if missing:
            sys.exit(f"Spotlight {nn}: calls not in data/raw: {missing}")
        meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        versions = sorted((r for r in rows if r["network"] == "X" and r["spotlight"] == str(nn)), key=lambda r: r["period"])
        meta["experiment"]["versions"] = [{k: r[k] for k in ("version", "frame", "design", "template")} for r in versions]
        meta["experiment"]["frames_supported"] = t["frames"]
        (folder / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        spec += [{"topic_dir": f"spotlights/{t['slug']}", "spotlight": nn, "frame": r["frame"], "design": r["design"],
                  "feed_tag": t["feed_tag"]} for r in versions]
    report = BV.run(spec)
    for p in (ROOT / "spotlights").rglob(".m.*"):
        p.unlink()
    bad = [r for r in report if not r[3].startswith("ok")]
    for r in report:
        print(" | ".join(map(str, r)))
    if bad:
        sys.exit(f"{len(bad)} version(s) not built")


if __name__ == "__main__":
    main({int(a) for a in sys.argv[1:]})
