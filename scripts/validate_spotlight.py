"""Check that every Spotlight is complete, reproducible and within the house rules.

Usage:
    python scripts/validate_spotlight.py                         # all spotlights
    python scripts/validate_spotlight.py --base origin/main      # also enforce frozen files vs a base ref

Spotlight folders are spotlights/NN-slug (two or three digits). Folders starting with "_" are private
and never published; any other name fails.

Checks, per spotlight folder:
  1. Required files are present; no two folders share a number; meta.json has spotlight (= NN),
     slug (= the folder name), title, sdg_indicator and retrieved_on (the public README table is built from them).
     From Spotlight 02 (house rule of 29 Oct 2026): target_basis, and target_value and target_year equal to
     stats.json's target (both null when the basis is "none"; a per-country basis needs the same threshold).
  2. stats.json reproduces exactly from the saved data with scripts/compute_stats.py (arguments recovered
     from stats.json itself: target, direction, country threshold, stale cutoff, number of countries ranked).
  3. Captions: the sections exist; X <= 280 characters as X counts them (a URL is 23, CJK and emoji 2)
     and Bluesky <= 300; no em-dashes. From Spotlight 02, each of the three has a "Method: ..." line.
  4. Banner: banner.png is 2400x1260 (or 1200x630).
     Experiment 001: a Spotlight listed in assignment.csv declares exactly that arm in meta.json; banner.png
     and banner.dc.html use the assigned ground; the repo link is in the LinkedIn body (body arm) or only in
     the "LinkedIn first comment" (first_comment arm). A Spotlight not listed declares no experiment.
     assignment.csv itself: no Spotlight is listed twice (the last row would silently win); a row above 33
     in one of the original blocks is a make-up and copies one of that block's slots exactly; at most one
     Spotlight per slot has a folder.
  5. With --base (published content is frozen):
     - every Spotlight on the base ref is still there under the same name, with data/*.csv and
       retrieval.json unchanged (new files under data/api_refresh/ are allowed);
     - assignment.csv, posts.csv and outcomes.csv only gain rows at the end; PREREGISTRATION.md only gains lines
       (its "None yet." placeholder under Deviations may go).
Exit code 1 if any check fails.
"""
import argparse, csv, json, pathlib, re, struct, subprocess, sys, tempfile, shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXP = "experiments/001-banner-ground"
REQUIRED = ["data/world.csv", "data/countries_latest.csv", "meta.json", "retrieval.json",
            "stats.json", "banner.dc.html", "banner.png", "captions.md"]
GROUNDS = {"dark": "#0D2433", "light": "#F4F6F7"}
LIMITS = {"X": 280, "Bluesky": 300}
REPO_LINK = "github.com/jpazvd/un-data-commons-spotlight"
HOUSE_RULE_FROM = 2  # target fields and method lines are required from Spotlight 02 (rule of 29 Oct 2026)
SPOTLIGHT_NAME = re.compile(r"^(\d{2,3})-[a-z0-9]+(?:-[a-z0-9]+)*$")
URL = re.compile(r"https?://\S+|\b(?:[a-z0-9-]+\.)+(?:com|org|net|int|io|dev|ai|gov|edu)(?:/\S*)?", re.I)

failures = []


def fail(spot, msg):
    failures.append(f"{spot}: {msg}")


def spotlight_dirs(root):
    """(Spotlight folders in number order, misnamed folders). Shared with build_readme_table.py."""
    spots, other = [], []
    root = pathlib.Path(root)
    for p in root.iterdir() if root.is_dir() else []:
        if p.is_dir() and not p.name.startswith("_"):
            (spots if SPOTLIGHT_NAME.match(p.name) else other).append(p)
    return sorted(spots, key=lambda p: (int(p.name.split("-")[0]), p.name)), sorted(other)


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")


def sections(md):
    out, cur = {}, None
    for line in md.splitlines():
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            cur = m.group(1); out[cur] = []
        elif cur:
            out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def x_length(text):
    """Length as X counts it: 23 per URL; Latin, general punctuation and the like 1; anything else 2."""
    light = lambda c: (ord(c) <= 0x10FF or 0x2000 <= ord(c) <= 0x200D or 0x2010 <= ord(c) <= 0x201F
                       or 0x2032 <= ord(c) <= 0x2037)
    return 23 * len(URL.findall(text)) + sum(1 if light(c) else 2 for c in URL.sub("", text))


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def check_meta(spot):
    meta = json.loads((spot / "meta.json").read_text(encoding="utf-8"))
    missing = [k for k in ("spotlight", "slug", "title", "sdg_indicator", "retrieved_on") if not meta.get(k)]
    if missing:
        fail(spot.name, "meta.json has no " + ", ".join(missing))
    num = int(spot.name.split("-")[0])
    if "spotlight" in meta and meta["spotlight"] != num:
        fail(spot.name, f"meta.json spotlight={meta['spotlight']!r} but the folder number is {num}")
    if "slug" in meta and meta["slug"] != spot.name:
        fail(spot.name, f"meta.json slug={meta['slug']!r} but the folder is {spot.name!r}")
    if num < HOUSE_RULE_FROM:
        return
    basis = meta.get("target_basis")
    if not isinstance(basis, str) or not basis.strip():
        fail(spot.name, 'meta.json has no target_basis (e.g. "SDG 5.3", "SDG 3.2 (per country)", "WHA 2030", '
                        '"IA2030" or "none")')
    elif basis == "none":
        if any(meta.get(k, "absent") is not None for k in ("target_value", "target_year")):
            fail(spot.name, 'meta.json target_basis is "none": target_value and target_year must both be present '
                            'and null')
    else:
        stats = json.loads((spot / "stats.json").read_text(encoding="utf-8"))
        for key, want in (("target_value", stats["target"]["value"]), ("target_year", stats["target"]["year"])):
            if not isinstance(meta.get(key), (int, float)) or float(meta[key]) != float(want):
                fail(spot.name, f"meta.json {key}={meta.get(key)!r} but stats.json's target says {want!r}")
        if "per country" in basis and (stats.get("country_threshold") or {}).get("value") != meta.get("target_value"):
            fail(spot.name, "a per-country target needs compute_stats.py --country-threshold <target_value>")


def check_stats(spot):
    stats = json.loads((spot / "stats.json").read_text(encoding="utf-8"))
    args = ["--target-value", str(stats["target"]["value"]), "--target-year", str(stats["target"]["year"]),
            "--stale-cutoff", str(stats["stale_cutoff_year"]), "--top", str(len(stats["top_countries"]))]
    if "better" in stats:
        args += ["--better", stats["better"]]
    if "country_threshold" in stats:
        args += ["--country-threshold", str(stats["country_threshold"]["value"])]
    with tempfile.TemporaryDirectory() as tmp:
        t = pathlib.Path(tmp) / spot.name
        shutil.copytree(spot / "data", t / "data")
        r = subprocess.run([sys.executable, str(ROOT / "scripts/compute_stats.py"), str(t), *args],
                           capture_output=True, text=True)
        if r.returncode:
            fail(spot.name, f"compute_stats.py failed: {r.stderr.strip()[-300:]}"); return
        if json.loads((t / "stats.json").read_text(encoding="utf-8")) != stats:
            fail(spot.name, "stats.json does not reproduce from data/ with compute_stats.py")


def check_captions(spot):
    sec = sections((spot / "captions.md").read_text(encoding="utf-8"))
    for name in ["LinkedIn", "X", "Bluesky"]:
        if name not in sec:
            fail(spot.name, f"captions.md has no '## {name}' section")
    for name, limit in LIMITS.items():
        n = x_length(sec.get(name, "")) if name == "X" else len(sec.get(name, ""))
        if n > limit:
            fail(spot.name, f"{name} caption is {n} characters (limit {limit})")
    for name, text in sec.items():
        if "—" in text:
            fail(spot.name, f"em-dash in the {name} caption")
    if int(spot.name.split("-")[0]) >= HOUSE_RULE_FROM:
        for name in ["LinkedIn", "X", "Bluesky"]:
            if name in sec and not re.search(r"^Method: \S", sec[name], re.M):
                fail(spot.name, f'the {name} caption has no "Method: ..." line (house rule)')


def check_banner(spot, assignment):
    size = png_size(spot / "banner.png")
    if size not in {(2400, 1260), (1200, 630)}:
        fail(spot.name, f"banner.png is {size}, expected 2400x1260 or 1200x630")
    meta = json.loads((spot / "meta.json").read_text(encoding="utf-8"))
    exp = meta.get("experiment")
    row = assignment.get(spot.name.split("-")[0])
    if not row:
        if exp:
            fail(spot.name, "meta.json declares an experiment but the Spotlight is not in assignment.csv")
        return
    if not exp:
        fail(spot.name, f"assignment.csv assigns {row['ground']}/{row['link_placement']} but meta.json "
                        "has no experiment"); return
    for key in ("block", "ground", "link_placement", "template"):
        if str(exp.get(key)) != row[key]:
            fail(spot.name, f"meta.json experiment.{key}={exp.get(key)!r} but assignment.csv says {row[key]!r}")
    # The ground: what is posted (banner.png, all four corners) and its source.
    from PIL import Image
    want = GROUNDS[row["ground"]]
    rgb = tuple(int(want[i:i + 2], 16) for i in (1, 3, 5))
    with Image.open(spot / "banner.png") as im:
        im = im.convert("RGB")
        corners = [im.getpixel(p) for p in [(2, 2), (im.width - 3, 2), (2, im.height - 3),
                                            (im.width - 3, im.height - 3)]]
    if any(max(abs(a - b) for a, b in zip(c, rgb)) > 2 for c in corners):
        fail(spot.name, f"banner.png is not on the assigned {row['ground']} ground ({want}): corners "
                        + ", ".join("#%02X%02X%02X" % c for c in corners))
    html = (spot / "banner.dc.html").read_text(encoding="utf-8")
    used = {g for g, hexv in GROUNDS.items()
            if re.search(rf"background(?:-color)?\s*:\s*{hexv}\b", html, re.I)}
    if used != {row["ground"]}:
        fail(spot.name, f"banner.dc.html does not use only the assigned {row['ground']} ground ({want})")
    # The link placement, both ways.
    sec = sections((spot / "captions.md").read_text(encoding="utf-8"))
    body, first = sec.get("LinkedIn", ""), sec.get("LinkedIn first comment")
    if row["link_placement"] == "body":
        if REPO_LINK not in body:
            fail(spot.name, "assigned the link in the body, but the LinkedIn caption has no repo link")
        if first is not None:
            fail(spot.name, "assigned the link in the body, but captions.md has a 'LinkedIn first comment'")
    else:
        if first is None or REPO_LINK not in first:
            fail(spot.name, "assigned the link in the first comment, but 'LinkedIn first comment' has no repo link")
        if REPO_LINK in body:
            fail(spot.name, "assigned the link in the first comment, but the LinkedIn caption carries it too")


def check_assignment(rows, spots):
    """Duplicate ids, make-ups that copy no slot, and slots with more than one Spotlight folder."""
    ids = [r["spotlight"] for r in rows]
    for i in sorted({i for i in ids if ids.count(i) > 1}):
        failures.append(f"assignment.csv: Spotlight {i} is listed more than once")
    slot = lambda r: (r["block"], r["link_placement"], r["ground"], r["template"])
    original = [r for r in rows if 2 <= int(r["spotlight"]) <= 33]  # the pre-registered slots
    slots, blocks = {slot(r) for r in original}, {r["block"] for r in original}
    with_folder = {int(p.name.split("-")[0]) for p in spots}
    members = {}
    for r in rows:
        if int(r["spotlight"]) > 33 and r["block"] in blocks and slot(r) not in slots:
            failures.append(f"assignment.csv: make-up {r['spotlight']} does not copy a slot of block {r['block']}")
            continue
        members.setdefault(slot(r), []).append(r["spotlight"])
    for s, nums in members.items():
        if len([n for n in nums if int(n) in with_folder]) > 1:
            failures.append(f"assignment.csv: block {s[0]} {s[2]}/{s[1]} has more than one Spotlight: "
                            + ", ".join(nums))


def check_frozen(base):
    for name in [n for n in git("ls-tree", "-d", "--name-only", f"{base}:spotlights").stdout.splitlines()
                 if SPOTLIGHT_NAME.match(n)]:
        if not (ROOT / "spotlights" / name).is_dir():
            fail(name, f"published on {base} but missing here (removed or renamed)"); continue
        r = git("diff", "--name-only", base, "--", f"spotlights/{name}/data", f"spotlights/{name}/retrieval.json")
        if r.returncode:
            fail(name, f"git diff against {base} failed: {r.stderr.strip()}"); continue
        changed = [p for p in r.stdout.splitlines() if f"spotlights/{name}/data/api_refresh/" not in p]
        if changed:
            fail(name, "published data snapshot changed: " + ", ".join(changed))


def check_append_only(base, rel, rows):
    """rows: lines may only be added at the end; otherwise lines may be inserted anywhere but not changed."""
    old = git("show", f"{base}:{rel}")
    if old.returncode:
        return  # not on the base yet
    path = ROOT / rel
    if not path.exists():
        failures.append(f"{rel}: on {base} but removed here"); return
    old_lines, new_lines = old.stdout.splitlines(), path.read_text(encoding="utf-8").splitlines()
    if rows:
        if new_lines[:len(old_lines)] != old_lines:
            failures.append(f"{rel}: existing rows changed or reordered (rows may only be added at the end)")
        return
    rest = iter(new_lines)
    for line in old_lines:
        if line != "None yet." and not any(line == x for x in rest):
            failures.append(f"{rel}: a line on {base} was changed or removed: {line[:80]!r}"); return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", help="git ref to enforce frozen files against, e.g. origin/main")
    a = ap.parse_args()
    sys.stdout.reconfigure(errors="backslashreplace")  # FAIL lines quote files; Windows consoles are not UTF-8
    apath = ROOT / EXP / "assignment.csv"
    rows = []
    if apath.exists():
        with open(apath, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    assignment = {r["spotlight"]: r for r in rows}
    spots, misnamed = spotlight_dirs(ROOT / "spotlights")
    check_assignment(rows, spots)
    for p in misnamed:
        fail(p.name, "not a Spotlight folder name (NN-slug); prefix it with _ to keep it private")
    numbers = [int(p.name.split("-")[0]) for p in spots]
    for p in spots:
        if numbers.count(int(p.name.split("-")[0])) > 1:
            fail(p.name, "another Spotlight folder has the same number")
    for spot in spots:
        missing = [f for f in REQUIRED if not (spot / f).exists()]
        if missing:
            fail(spot.name, "missing " + ", ".join(missing)); continue
        check_meta(spot); check_stats(spot); check_captions(spot); check_banner(spot, assignment)
    if a.base:
        if git("rev-parse", "--verify", "--quiet", f"{a.base}^{{commit}}").returncode:
            failures.append(f"--base {a.base}: no such commit here (fetch it first, e.g. git fetch origin main)")
        else:
            check_frozen(a.base)
            check_append_only(a.base, f"{EXP}/assignment.csv", rows=True)
            check_append_only(a.base, f"{EXP}/posts.csv", rows=True)
            check_append_only(a.base, f"{EXP}/outcomes.csv", rows=True)
            check_append_only(a.base, f"{EXP}/PREREGISTRATION.md", rows=False)
    print(f"Checked {len(spots)} Spotlight(s).")
    for f in failures:
        print("FAIL", f)
    if failures:
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
