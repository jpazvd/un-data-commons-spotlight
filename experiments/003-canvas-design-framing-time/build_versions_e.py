#!/usr/bin/env python3
"""Build experiment 003's versions in spotlights/: the template E versions from the revision 3 material, the template
D dark versions as experiment 002 built them, and every version's captions with the two comments.

Usage (repo root; pip install -r requirements.txt, npm ci, the Playwright Chromium):
    python experiments/003-canvas-design-framing-time/build_versions_e.py [--only 07,22] [--check]

For each X row of assignment.csv (one per version), in the topic's folder spotlights/<slug>/versions/<frame>/:
  - design E-light or E-dark: scripts/banner_e.py draws the banner (the same stats.json, headline candidates,
    evidence, data line and chart data as the 002 version; the rules of revision 3; REVISIONS for the 14 versions
    changed after JP's review of 3 November 2026), and this script keeps its banner.dc.html, banner.png (2400x2400),
    banner.jpg (1200x1200), e.meta.json (headline, subtitle and its source, RDM code, flags) and alt.txt, and
    writes captions.md from the words as drawn (scripts/copy002.py, captions) with the rule of 3 November 2026: the
    body carries no link; "LinkedIn first comment" is the repo link; "Second comment" is the indicator's Reference
    Data Manager record when the subtitle comes from it. House wording ("countries and territories") throughout.
  - design D-dark: the banner stays as experiment 002 built it (pull requests #24 to #27), except the versions whose
    banner carried "countries and areas" (REBUILD) and a version with no banner yet (Spotlight 22-T, a replacement
    series), which experiment 002's build_versions.py rebuilds with the house wording. captions.md is rewritten with
    the same comment rule.
  - meta.json: experiment id 003, the versions with their 003 designs, 002's kept under experiment_002.
Spotlight 22: its three versions live in two topic folders (22-sanitation-east-se-asia for L and T,
22-water-regions-urban-rural for G), the replacements JP accepted on 4 November 2026; each folder's meta.json
names only its frames.

--check compares every template E headline with the revision 3 batch index (docs/revision-3-2026-11/batch/index.csv,
version 4) and reports any that differ, then exits.
"""
import argparse
import csv
import json
import pathlib
import re
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
E2 = ROOT / "experiments" / "002-design-framing-time"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(E2))
import banner_e as E  # noqa: E402
import copy002 as C  # noqa: E402
import build_versions as BV  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

REPO = "https://github.com/jpazvd/un-data-commons-spotlight"
FIRST = f"Data and code: {REPO}"
REBUILD = {"26-T", "28-T", "34-T", "35-T", "37-D1", "38-D1"}  # D-dark banners that said "countries and areas"
BATCH_INDEX = ROOT / "docs/revision-3-2026-11/batch/index.csv"


def topic_folders():
    """spotlight number -> {frame or '*': folder}. A replacement folder (meta.replacement_of) serves its frames."""
    out = {}
    for d in sorted((ROOT / "spotlights").glob("[0-9][0-9]-*")):
        m = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        exp = m.get("experiment") or {}
        if exp.get("id") not in ("002", "003") or "versions" not in exp:
            continue  # Spotlights 01 to 04 are single-version folders, not topics of this experiment
        nn = int(m["spotlight"])
        rep = m.get("replacement_of")
        if rep:
            for f in rep["frames"]:
                out.setdefault(nn, {})[f] = d
        else:
            out.setdefault(nn, {})["*"] = d
    return out


def folder_for(folders, nn, frame):
    f = folders[nn]
    return f.get(frame) or f["*"]


def comments_sections(text, second):
    """captions.md with the link rule of 3 November 2026 and the house wording."""
    sec, order = {}, []
    cur = None
    head = []
    for line in text.splitlines():
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            cur = m.group(1); order.append(cur); sec[cur] = []
        elif cur is None:
            head.append(line)
        else:
            sec[cur].append(line)
    body = {k: "\n".join(v).strip() for k, v in sec.items()}
    li = body["LinkedIn"]
    li = re.sub(r"\n*Data and code: https://github\.com/jpazvd/un-data-commons-spotlight\n*", "\n\n", li).strip()
    li = re.sub(r"\n{3,}", "\n\n", li)
    body["LinkedIn"] = li
    for k in ("Bluesky", "Bluesky with feed tag"):
        if k in body:
            body[k] = re.sub(r"\s*Data \+ code: github\.com/jpazvd/un-data-commons-spotlight", "", body[k]).strip()
    body["LinkedIn first comment"] = FIRST
    if second:
        body["Second comment"] = second
    order = [k for k in order if k not in ("LinkedIn first comment", "Second comment")]
    i = order.index("LinkedIn") + 1
    order[i:i] = ["LinkedIn first comment"] + (["Second comment"] if second else [])
    out = "\n".join(head).rstrip() + "\n\n" + "\n\n".join(f"## {k}\n\n{body[k]}" for k in order) + "\n"
    return E.house(out)


def write_e_version(r, vdir, feed_tag, frame):
    """Move banner_e's files into the version folder; write alt.txt, captions.md and e.meta.json."""
    out_dir = pathlib.Path(r["_out_dir"])
    stem = f"{r['spotlight']:02d}-{frame}-E-{r['palette']}"
    shutil.move(out_dir / f"{stem}.dc.html", vdir / "banner.dc.html")
    shutil.move(out_dir / f"{stem}.png", vdir / "banner.png")
    shutil.move(out_dir / f"{stem}.jpg", vdir / "banner.jpg")
    (out_dir / f"{stem}.meta.json").unlink()
    (vdir / "alt.txt").write_text(r["alt"] + "\n", encoding="utf-8")
    meta = r["topic_meta"]
    caps = C.captions(r["content"], r["headline"], meta, feed_tag, frame)
    text = f"# Spotlight {r['spotlight']:02d}-{frame} · {meta['title']}: post captions\n\n" + caps
    (vdir / "captions.md").write_text(comments_sections(text, r.get("second_comment")), encoding="utf-8")
    keep = {k: v for k, v in r.items() if k not in ("content", "topic_meta", "_out_dir")}
    (vdir / "e.meta.json").write_text(json.dumps(keep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def rebuild_d_dark(topic, nn, frame, feed_tag, second):
    """Experiment 002's builder with the house wording applied to every word it draws."""
    original = C.content

    def housed(*a, **k):
        c = original(*a, **k)
        for key in ("headlines", ):
            c[key] = [E.house(x) for x in c[key]]
        if c.get("headlines_last"):
            c["headlines_last"] = (E.house(c["headlines_last"][0]), E.house(c["headlines_last"][1]))
        for key in ("signal", "evidence", "evidence_alt", "method", "method_short", "question", "svg", "note", "detail"):
            if c.get(key):
                c[key] = E.house(c[key])
        return c

    C.content = housed
    try:
        rep = BV.run([{"topic_dir": str(topic.relative_to(ROOT)), "spotlight": nn, "frame": frame,
                       "design": "D-dark", "feed_tag": feed_tag}])
    finally:
        C.content = original
    for p in topic.rglob(".m.*"):
        p.unlink()
    vdir = topic / "versions" / frame
    text = (vdir / "captions.md").read_text(encoding="utf-8")
    (vdir / "captions.md").write_text(comments_sections(text, second), encoding="utf-8")
    return rep[0][3]


def rdm_second(frame_dir_meta_family):
    _, origin, code, url = E.rdm_subtitle(frame_dir_meta_family)
    return f"Definition, UNICEF Reference Data Manager ({code}): {url}" if url and origin and origin.startswith("rdm:") else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", help="topic numbers, comma-separated")
    ap.add_argument("--check", action="store_true", help="compare the E headlines with the batch index and exit")
    a = ap.parse_args()
    only = {int(x) for x in a.only.split(",")} if a.only else None
    rows = [r for r in csv.DictReader(open(HERE / "assignment.csv", encoding="utf-8")) if r["network"] == "X"]
    topics = {int(t["spotlight"]): t for t in csv.DictReader(open(HERE / "topics.csv", encoding="utf-8"))}
    folders = topic_folders()
    if a.check:
        idx = {(r["spotlight"].zfill(2), r["frame"], r["palette"]): r["headline"]
               for r in csv.DictReader(open(BATCH_INDEX, encoding="utf-8"))}
        bad = 0
        for r in rows:
            if not r["design"].startswith("E-"):
                continue
            nn = int(r["spotlight"]); vdir = folder_for(folders, nn, r["frame"]) / "versions" / r["frame"]
            if not (vdir / "e.meta.json").exists():
                print(f"{r['version']}: not built"); bad += 1; continue
            head = json.loads((vdir / "e.meta.json").read_text(encoding="utf-8"))["headline"]
            want = idx.get((f"{nn:02d}", r["frame"], r["design"][2:]))
            if head != want:
                print(f"{r['version']} {r['design']}: {head!r} but the batch index says {want!r}"); bad += 1
        print(f"{bad} difference(s) with the revision 3 batch index (version 4)")
        sys.exit(1 if bad else 0)
    report, later = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        tab = browser.new_page(viewport={"width": 1200, "height": 1200}, device_scale_factor=2)
        for r in rows:
            nn, frame, design = int(r["spotlight"]), r["frame"], r["design"]
            if only and nn not in only:
                continue
            topic = folder_for(folders, nn, frame)
            vdir = topic / "versions" / frame
            vdir.mkdir(parents=True, exist_ok=True)
            feed_tag = topics[nn]["feed_tag"]
            if design.startswith("E-"):
                with tempfile.TemporaryDirectory(dir=HERE) as tmp:
                    res = E.build(topic, frame, design[2:], tmp, png=True, tab=tab)
                    if not res.get("ok"):
                        report.append((r["version"], design, "FAILED " + res.get("reason", ""))); continue
                    res["_out_dir"] = tmp
                    write_e_version(res, vdir, feed_tag, frame)
                report.append((r["version"], design, f"ok: {res['headline']}"
                               + (" | " + "; ".join(res["flags"]) if res.get("flags") else "")))
            else:
                family = json.loads((vdir / "stats.json").read_text(encoding="utf-8"))["family"] if (vdir / "stats.json").exists() else None
                second = rdm_second(family) if family else None
                if r["version"] in REBUILD or not (vdir / "banner.dc.html").exists():
                    later.append((r, topic, vdir, nn, frame, feed_tag, family, second))
                else:
                    text = (vdir / "captions.md").read_text(encoding="utf-8")
                    (vdir / "captions.md").write_text(comments_sections(text, second), encoding="utf-8")
                    report.append((r["version"], design, "kept; captions rewritten"))
        browser.close()
    for r, topic, vdir, nn, frame, feed_tag, family, second in later:  # 002's builder opens its own browser
        out = rebuild_d_dark(topic, nn, frame, feed_tag, second)
        if family is None:
            st = json.loads((vdir / "stats.json").read_text(encoding="utf-8"))
            second = rdm_second(st["family"])
            text = (vdir / "captions.md").read_text(encoding="utf-8")
            (vdir / "captions.md").write_text(comments_sections(text, second), encoding="utf-8")
        report.append((r["version"], r["design"], "rebuilt, " + out))
    # meta.json: experiment 003 with the versions each folder holds.
    for nn, fmap in folders.items():
        if only and nn not in only:
            continue
        mine = [r for r in rows if int(r["spotlight"]) == nn]
        for d in sorted(set(fmap.values())):
            mp = d / "meta.json"
            m = json.loads(mp.read_text(encoding="utf-8"))
            held = [r for r in mine if folder_for(folders, nn, r["frame"]) == d]
            exp = m.get("experiment") or {}
            if exp.get("id") == "002":
                m["experiment_002"] = exp  # 002's record of the topic, kept as it was
            exp = {**{k: v for k, v in exp.items() if k not in ("id", "versions")},
                   "id": "003", "versions": [{"version": r["version"], "frame": r["frame"], "design": r["design"],
                                              "template": r["template"]} for r in sorted(held, key=lambda r: r["period"])]}
            m["experiment"] = exp
            mp.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for line in report:
        print(" | ".join(line))
    bad = [x for x in report if x[2].startswith("FAILED")]
    if bad:
        sys.exit(f"{len(bad)} version(s) failed")


if __name__ == "__main__":
    main()
