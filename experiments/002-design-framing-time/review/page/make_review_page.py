"""Build the experiment 002 banner review page from the four batch branches.

Usage: python make_review_page.py REPO OUT_DIR

Reads every version's banner.png, captions.md, alt.txt and stats.json with `git show` from
spotlight/002-batch-1..4 (what the batch PRs carry), writes OUT_DIR/img/<version>-<sha8>.jpg
(1600 px wide) and OUT_DIR/banner-review.html. Nothing is recomputed: the page shows the committed files.
"""
import csv
import hashlib
import io
import json
import pathlib
import re
import subprocess
import sys

from PIL import Image

REPO = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2]).resolve()
EXP = REPO / "experiments" / "002-design-framing-time"
HERE = pathlib.Path(__file__).resolve().parent
GH = "https://github.com/jpazvd/un-data-commons-spotlight-dev"
PRS = {1: 24, 2: 25, 3: 26, 4: 27}
BATCHES = {1: [16, 29, 23, 24, 7, 32, 28, 33, 12], 2: [18, 11, 17, 9, 19, 30, 15, 10, 14],
           3: [38, 20, 5, 8, 37, 36, 21, 35, 27], 4: [6, 34, 22, 39, 25, 31, 40, 13, 26]}
FRAME_NAME = {"T": "What it would take", "L": "The long view", "G": "Behind the average",
              "D": "The data behind it", "D1": "Any data", "D2": "How recent", "D3": "Which regions"}
ILO = ("Its World value, 7.8% in 2024 (girls 6.9%, boys 8.6%), sits very close to the ILO-UNICEF estimate of child "
       "labour in 2024 (almost 8 per cent of children; 7% of girls, 9% of boys; ilo.org, 2024 global estimates). "
       "The series is labelled economic activity, ages 5 to 17. Check with the custodian which of the two the "
       "regional aggregates measure before this posts.")
MPI = ("28 of the 47 latest values are dated 2010 (stats.json, by_year), nearly all EU members plus Iceland, Norway "
       "and Turkey. Before a data-gap claim posts, check SD_MDP_MUHC for those countries against the SDG API.")
FLAGS = {
    "26-G": ("In 10 of the 25 countries the rural and urban values are less than a point apart (stats.json, "
             "n_gap_under_1). The LinkedIn note says so; the banner, X and Bluesky count all 18 urban-higher "
             "countries. Keep, or count only gaps of a point or more?"),
    "31-T": ILO, "31-G": ILO,
    "37-D1": MPI, "37-D2": MPI, "37-D3": MPI,
}


def git(*args, binary=False):
    r = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, check=True)
    return r.stdout if binary else r.stdout.decode("utf-8")


def sections(md):
    out, cur = {}, None
    for line in md.splitlines():
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            cur = m.group(1); out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def main():
    topics = {int(t["spotlight"]): t for t in csv.DictReader(open(EXP / "topics.csv", encoding="utf-8"))}
    rows = list(csv.DictReader(open(EXP / "assignment.csv", encoding="utf-8")))
    batch_of = {nn: b for b, nns in BATCHES.items() for nn in nns}
    (OUT / "img").mkdir(parents=True, exist_ok=True)
    for old in (OUT / "img").glob("*.jpg"):
        old.unlink()
    commits = {b: git("rev-parse", "--short", f"spotlight/002-batch-{b}").strip() for b in BATCHES}
    items = []
    for r in sorted((r for r in rows if r["network"] == "X"), key=lambda r: (int(r["spotlight"]), int(r["period"]))):
        nn, frame = int(r["spotlight"]), r["frame"]
        t, b = topics[nn], batch_of[nn]
        branch = f"spotlight/002-batch-{b}"
        base = f"spotlights/{t['slug']}"
        vdir = f"{base}/versions/{frame}"
        png = git("show", f"{branch}:{vdir}/banner.png", binary=True)
        sha = hashlib.sha256(png).hexdigest()
        meta = json.loads(git("show", f"{branch}:{base}/meta.json"))
        stats = json.loads(git("show", f"{branch}:{vdir}/stats.json"))
        sec = sections(git("show", f"{branch}:{vdir}/captions.md"))
        alt = git("show", f"{branch}:{vdir}/alt.txt").strip()
        posts = []
        for rr in rows:
            if rr["version"] == r["version"] and rr["date"]:
                posts.append({"net": rr["network"], "date": rr["date"], "time": rr["time_rome"],
                              "tag": rr["feed_tag"] if rr.get("feed_tag_on") == "1" else ""})
        posts.sort(key=lambda p: (p["date"], p["time"]))
        tagged = any(p["net"] == "Bluesky" and p["tag"] for p in posts)
        vid = f"{nn:02d}-{frame}"
        name = f"img/{vid}-{sha[:8]}.jpg"
        im = Image.open(io.BytesIO(png)).convert("RGB").resize((1600, 840), Image.LANCZOS)
        im.save(OUT / name, "JPEG", quality=86, optimize=True, progressive=True)
        items.append({
            "id": vid, "version": r["version"], "nn": nn, "frame": frame, "frameName": FRAME_NAME[frame], "design": r["design"],
            "period": int(r["period"]), "topic": meta["title"], "sdg": t["sdg"], "custodian": stats.get("custodian", ""),
            "kind": t["kind"], "pace": t["pace"] == "1", "batch": b, "pr": PRS[b], "prUrl": f"{GH}/pull/{PRS[b]}",
            "branch": branch, "commit": commits[b], "img": name, "sha": sha[:12], "alt": alt,
            "x": sec["X"], "li": sec["LinkedIn"], "bs": sec["Bluesky with feed tag"] if tagged else sec["Bluesky"],
            "posts": posts, "treeUrl": f"{GH}/tree/{branch}/{vdir}", "statsUrl": f"{GH}/blob/{branch}/{vdir}/stats.json",
            "dataUrl": f"{GH}/tree/{branch}/{base}/data", "flag": FLAGS.get(vid, ""),
        })
    build = {"date": subprocess.run(["date", "+%-d %b %Y"], capture_output=True, text=True).stdout.strip(),
             "branches": [{"branch": f"spotlight/002-batch-{b}", "commit": commits[b], "pr": PRS[b]} for b in BATCHES]}
    js = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    html = (HERE / "template.html").read_text(encoding="utf-8")
    html = html.replace("/*__ITEMS__*/[]", js(items)).replace("/*__BUILD__*/{}", js(build))
    assert "__ITEMS__" not in html and "__BUILD__" not in html
    (OUT / "banner-review.html").write_text(html, encoding="utf-8")
    nets = {}
    for i in items:
        for p in i["posts"]:
            nets[p["net"]] = nets.get(p["net"], 0) + 1
    print(len(items), "versions;", nets, "; flags:", sum(bool(i["flag"]) for i in items),
          "; html", round(len(html.encode()) / 1e3), "KB; images",
          round(sum(f.stat().st_size for f in (OUT / "img").glob("*.jpg")) / 1e6, 1), "MB")


if __name__ == "__main__":
    main()
