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
  4. Banner: banner.png is 2400x1260 (or 1200x630) for a template D design, 2400x2400 (or 1200x1200) for a
     template E design (revision 3).
  4b. Metadata (revision 3): a Spotlight whose meta.json names rdm_helix_code (not "none") has a
     metadata.rdm.json for that code (scripts/fetch_rdm_metadata.py) with no editor field or @unicef.org
     address in its decoded contents, and its meta.json subtitle is the text shown in banner.dc.html (the
     data-subtitle element, entities decoded) and is the record's English DEFINITION or declares a shortened
     form (subtitle_from "rdm:DEFINITION, shortened", optionally saying how, e.g. "(first sentence)"); the
     Definition line is looked for in the visible text (comments, scripts, styles and attributes excluded).
     The live comparison with the registry is the rdm-metadata workflow's job, not this script's.
     Experiment 001: a Spotlight listed in assignment.csv declares exactly that arm in meta.json; banner.png
     and banner.dc.html use the assigned ground; the repo link is in the LinkedIn body (body arm) or only in
     the "LinkedIn first comment" (first_comment arm). A Spotlight not listed declares no experiment.
     A run-in Spotlight of experiment 003 (meta.json experiment {"id": "003", "role": "run-in", "palette": ...},
     Spotlights 02 to 04 after 001 stopped) keeps 001's ground as its template E palette, is square, and has the
     repo link in the first comment only, whatever 001's link-placement arm said.
     assignment.csv itself: no Spotlight is listed twice (the last row would silently win); a row above 33
     in one of the original blocks is a make-up and copies one of that block's slots exactly; at most one
     Spotlight per slot has a folder.
  5. With --base (published content is frozen):
     - every Spotlight on the base ref is still there under the same name, with data/*.csv and
       retrieval.json unchanged (new files under data/api_refresh/ are allowed);
     - assignment.csv, posts.csv and outcomes.csv only gain rows at the end; PREREGISTRATION.md only gains lines
       (its "None yet." placeholder under Deviations may go).
Experiment 002 Spotlights (meta.json experiment.id "002") are topic folders with one subfolder per version:
  data/ (world.csv, countries_latest.csv, membership.csv and the topic's other snapshots), meta.json,
  retrieval.json, and versions/<F>/ with stats.json, banner.dc.html, banner.png and captions.md. Checked:
  the versions in meta.json are exactly the topic's rows in experiments/002-design-framing-time/assignment.csv
  (framing and design); every stats.json reproduces from data/ with scripts/spotlight002.py; captions have
  LinkedIn, X, Bluesky and "Bluesky with feed tag" within limits, a Method line each and no em-dash; banner.png
  is 2400x1260 on the assigned design's ground and its series line names the Spotlight. Experiment 001's checks
  do not apply to them, and 002's assignment, posts and outcomes files are append-only like 001's.
Exit code 1 if any check fails.
"""
import argparse, csv, html, json, pathlib, re, struct, subprocess, sys, tempfile, shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXP = "experiments/001-banner-ground"
REQUIRED = ["data/world.csv", "data/countries_latest.csv", "meta.json", "retrieval.json",
            "stats.json", "banner.dc.html", "banner.png", "captions.md"]
GROUNDS = {"dark": "#0D2433", "light": "#F4F6F7"}
BANNER_SIZES = {(2400, 1260), (1200, 630), (2400, 2400), (1200, 1200)}  # template D (landscape), template E (square)
LIMITS = {"X": 280, "Bluesky": 300}
REPO_LINK = "github.com/jpazvd/un-data-commons-spotlight"
EXP2 = "experiments/002-design-framing-time"
EXP3 = "experiments/003-canvas-design-framing-time"
DESIGN_GROUND = {"D-dark": "#0D2433", "D-light": "#F4F6F7", "Ink": "#FFFFFF", "E-dark": "#0D2433", "E-light": "#F4F6F7"}
DESIGN_SIZES = {"E-dark": {(2400, 2400), (1200, 1200)}, "E-light": {(2400, 2400), (1200, 1200)}}  # others: landscape
RDM_API = "https://rdmapi.unicef.org/api/indicators/"
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


def check_rdm(spot):
    """Revision 3: the stored Reference Data Manager record and the subtitle written from it."""
    meta = json.loads((spot / "meta.json").read_text(encoding="utf-8"))
    code = meta.get("rdm_helix_code")
    path = spot / "metadata.rdm.json"
    if code in (None, "", "none"):
        if path.exists():
            fail(spot.name, "metadata.rdm.json is present but meta.json names no rdm_helix_code")
        return
    if not path.exists():
        fail(spot.name, f"meta.json names rdm_helix_code {code!r} but metadata.rdm.json is missing"); return
    snap = json.loads(path.read_text(encoding="utf-8"))
    decoded = json.dumps(snap, ensure_ascii=False)  # the decoded contents: a \u0040 or other escape cannot hide
    for key in ("source", "url", "retrieved_at", "sha256_raw", "record"):
        if key not in snap:
            fail(spot.name, f"metadata.rdm.json has no {key!r}")
    if re.search(r"[A-Za-z0-9._%+-]+@unicef\.org", decoded, re.I):
        fail(spot.name, "metadata.rdm.json stores an @unicef.org address (editor fields must be stripped)")
    if re.search(r'"(editedBy|createdBy|changePublishStatusBy)"', decoded):
        fail(spot.name, "metadata.rdm.json stores an editor field")
    record = snap.get("record") or {}
    if record.get("helixCode") != code:
        fail(spot.name, f"metadata.rdm.json is for {record.get('helixCode')!r}, meta.json names {code!r}")
    eng = {a.get("attributeCode"): a.get("value") for a in record.get("attributes", [])
           if a.get("languageISO") == "eng"}
    subtitle, origin = meta.get("subtitle"), meta.get("subtitle_from")
    if not subtitle:
        fail(spot.name, "meta.json has rdm_helix_code but no subtitle (the banner's subtitle text)"); return
    design = (spot / "banner.dc.html").read_text(encoding="utf-8")
    design = re.sub(r"<!--.*?-->|<(script|style)\b.*?</\1>", "", design, flags=re.S)  # not shown on the banner
    # The subtitle as shown: the data-subtitle element's text, tags removed and entities decoded (banner_e.py
    # escapes it), so a comment or an attribute cannot stand in for it and an apostrophe or ampersand passes.
    m = re.search(r"<span\b[^>]*\bdata-subtitle\b[^>]*>(.*?)</span>", design, re.S)
    shown = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))).strip() if m else None
    if shown is None:
        fail(spot.name, "banner.dc.html has no data-subtitle element (the subtitle as shown on the banner)")
    elif shown != re.sub(r"\s+", " ", subtitle).strip():
        fail(spot.name, f"the subtitle shown in banner.dc.html is {shown!r}, not meta.json's")
    visible = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", design)))  # element text only, no attributes
    if f"Definition: UNICEF Reference Data Manager, indicator {code}" not in visible:
        fail(spot.name, f'banner.dc.html must say "Definition: UNICEF Reference Data Manager, indicator {code}" '
                        "when the subtitle comes from the registry (JP, 3 Nov 2026)")
    definition = re.sub(r"\s+", " ", str(eng.get("DEFINITION") or "")).strip()
    if re.sub(r"\s+", " ", subtitle).strip() == definition:
        if origin not in (None, "rdm:DEFINITION"):
            fail(spot.name, f"subtitle equals DEFINITION but subtitle_from is {origin!r}")
    elif not (isinstance(origin, str) and origin.startswith("rdm:DEFINITION, shortened")):  # the builders add how
        fail(spot.name, 'subtitle differs from the record\'s DEFINITION: set subtitle_from to '
                        '"rdm:DEFINITION, shortened" (optionally saying how, e.g. "(first sentence)") '
                        'or use the definition verbatim')


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
    if size not in BANNER_SIZES:
        fail(spot.name, f"banner.png is {size}, expected one of " + ", ".join("%dx%d" % s for s in sorted(BANNER_SIZES)))
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
    # A run-in Spotlight of experiment 003 (001 stopped before any post; 02 to 04 are 002's, then 003's,
    # run-in): it keeps 001's ground, declares the template E palette, and the repo link is the first comment on
    # every network (JP, 3 Nov 2026), so 001's link-placement arm no longer applies to it.
    run_in = exp.get("id") == "003" and exp.get("role") == "run-in"
    if run_in:
        if exp.get("palette") != row["ground"] or (exp.get("from_001") or {}).get("ground") != row["ground"]:
            fail(spot.name, f"run-in palette {exp.get('palette')!r} is not 001's assigned ground {row['ground']!r}")
        if size not in {(2400, 2400), (1200, 1200)}:
            fail(spot.name, f"a template E run-in banner must be square, banner.png is {size}")
        row = {**row, "link_placement": "first_comment"}
        sec_all = sections((spot / "captions.md").read_text(encoding="utf-8"))
        for name in ("X", "Bluesky"):
            if REPO_LINK in sec_all.get(name, ""):
                fail(spot.name, f"run-in: the {name} caption carries the repo link (it is a thread reply, never the body)")
    else:
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


def topic_experiment(spot):
    """"002" or "003" for a topic folder of that experiment (one subfolder per version), else None."""
    try:
        exp = (json.loads((spot / "meta.json").read_text(encoding="utf-8")).get("experiment") or {}).get("id")
    except (OSError, ValueError):
        return None
    if exp == "003" and (meta_exp_role(spot) == "run-in"):
        return None  # a run-in Spotlight (02 to 04) is a single-version folder, checked by the 001 rules
    return exp if exp in ("002", "003") else None


def meta_exp_role(spot):
    try:
        return (json.loads((spot / "meta.json").read_text(encoding="utf-8")).get("experiment") or {}).get("role")
    except (OSError, ValueError):
        return None


def is_002(spot):
    return topic_experiment(spot) is not None


def check_002(spot, rows2, exp="002"):
    """An experiment 002 or 003 topic folder (see the module docstring). rows2: that experiment's assignment."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import spotlight002
    need = ["data/world.csv", "data/countries_latest.csv", "data/membership.csv", "meta.json", "retrieval.json"]
    missing = [f for f in need if not (spot / f).exists()]
    if missing:
        fail(spot.name, "missing " + ", ".join(missing)); return
    meta = json.loads((spot / "meta.json").read_text(encoding="utf-8"))
    num = int(spot.name.split("-")[0])
    for k in ("spotlight", "slug", "title", "sdg_indicator", "retrieved_on", "target_basis"):
        if not meta.get(k):
            fail(spot.name, f"meta.json has no {k}")
    if meta.get("spotlight") != num or meta.get("slug") != spot.name:
        fail(spot.name, "meta.json spotlight and slug must match the folder")
    if meta.get("target_basis") == "none" and (meta.get("target_value") is not None or meta.get("target_year") is not None):
        fail(spot.name, 'target_basis "none" needs null target_value and target_year')
    want = sorted((r["frame"], r["design"]) for r in rows2 if r["spotlight"] == str(num) and r["network"] == "X")
    have = sorted((v["frame"], v["design"]) for v in meta["experiment"].get("versions", []))
    rep = meta.get("replacement_of")
    if rep:  # a replacement folder (Spotlight 22, 4 Nov 2026) holds only the frames it replaces
        want = [w for w in want if w[0] in rep["frames"]]
    if want != have:
        fail(spot.name, f"meta.json versions {have} but assignment.csv ({exp}) says {want}")
    for frame, design in have:
        vdir = spot / "versions" / frame
        miss = [f for f in ("stats.json", "banner.dc.html", "banner.png", "captions.md") if not (vdir / f).exists()]
        if miss:
            fail(spot.name, f"version {frame} missing " + ", ".join(miss)); continue
        try:
            again = json.loads(json.dumps(spotlight002.stats(spot, frame)))
        except Exception as e:  # noqa: BLE001
            fail(spot.name, f"version {frame}: spotlight002.py failed: {e}"); continue
        if again != json.loads((vdir / "stats.json").read_text(encoding="utf-8")):
            fail(spot.name, f"version {frame}: stats.json does not reproduce from data/ with spotlight002.py")
        sec = sections((vdir / "captions.md").read_text(encoding="utf-8"))
        for name in ("LinkedIn", "X", "Bluesky", "Bluesky with feed tag"):
            text = sec.get(name)
            if text is None:
                fail(spot.name, f"version {frame}: captions.md has no '## {name}'"); continue
            n = x_length(text) if name == "X" else len(text)
            limit = 280 if name == "X" else 300 if name.startswith("Bluesky") else 3000
            if n > limit:
                fail(spot.name, f"version {frame}: {name} caption is {n} characters (limit {limit})")
            if "\u2014" in text:
                fail(spot.name, f"version {frame}: em-dash in the {name} caption")
            if not re.search(r"(^|\s)Method: \S", text):
                fail(spot.name, f"version {frame}: the {name} caption has no Method line")
        sizes = DESIGN_SIZES.get(design, {(2400, 1260), (1200, 630)})
        if png_size(vdir / "banner.png") not in sizes:
            fail(spot.name, f"version {frame}: banner.png is not {'2400x2400' if design.startswith('E-') else '2400x1260'} ({design})")
        if exp == "003":
            check_003_version(spot, frame, design, sec, vdir)
        from PIL import Image
        rgb = tuple(int(DESIGN_GROUND[design][i:i + 2], 16) for i in (1, 3, 5))
        with Image.open(vdir / "banner.png") as im:
            im = im.convert("RGB")
            corners = [im.getpixel((2, im.height - 3)), im.getpixel((im.width - 3, im.height - 3))]
        if any(max(abs(a - b) for a, b in zip(c, rgb)) > 2 for c in corners):
            fail(spot.name, f"version {frame}: banner.png is not on the {design} ground")
        html = (vdir / "banner.dc.html").read_text(encoding="utf-8")
        # Review round 1 (2 Nov 2026): series line without a number, no byline, footer with the series code,
        # the extraction date and the GitHub handle, and a headline that names what is measured.
        if "UN Data Commons Spotlight" not in html or re.search(r"Data Commons Spotlight \d", html):
            fail(spot.name, f"version {frame}: the series line must read \"UN Data Commons Spotlight\" with no number")
        if "Jo\u00e3o Pedro Azevedo" in html or "@jpazvd" not in html:
            fail(spot.name, f"version {frame}: the footer must carry @jpazvd and no byline")
        if f"extracted {spotlight_day(meta['retrieved_on'])}" not in html:
            fail(spot.name, f"version {frame}: the footer does not give the extraction date")
        import copy002
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
        head = re.sub(r"<[^>]+>", "", h1.group(1)) if h1 else ""
        fam = json.loads((vdir / "stats.json").read_text(encoding="utf-8")).get("family")
        if not copy002.names_construct(unescape(head), fam):
            fail(spot.name, f"version {frame}: the headline does not name what is measured: {head!r}")


def check_003_version(spot, frame, design, sec, vdir):
    """Experiment 003 (4 Nov 2026): the repo link is the first comment on every network and never in the body; the
    second comment is the Reference Data Manager record when the banner's subtitle comes from it (template E shows
    "Definition: UNICEF Reference Data Manager, indicator <code>"); a template E version keeps e.meta.json."""
    body, first, second = sec.get("LinkedIn", ""), sec.get("LinkedIn first comment"), sec.get("Second comment")
    if first is None or REPO_LINK not in first:
        fail(spot.name, f"version {frame}: 'LinkedIn first comment' must carry the repo link")
    for name in ("LinkedIn", "X", "Bluesky", "Bluesky with feed tag"):
        if REPO_LINK in sec.get(name, ""):
            fail(spot.name, f"version {frame}: the {name} body carries the repo link (it is the first comment)")
    html = (vdir / "banner.dc.html").read_text(encoding="utf-8")
    m = re.search(r"Definition: UNICEF Reference Data Manager, indicator ([A-Za-z0-9_.-]+)", html)
    if design.startswith("E-"):
        if not (vdir / "e.meta.json").exists():
            fail(spot.name, f"version {frame}: template E version without e.meta.json")
        if m and (second is None or f"{RDM_API}{m.group(1)}" not in second):
            fail(spot.name, f"version {frame}: the banner names RDM indicator {m.group(1)} but 'Second comment' has no link to its record")
        if not m and second is not None:
            fail(spot.name, f"version {frame}: a 'Second comment' but the banner names no RDM indicator")
        if "countries and areas" in html:
            fail(spot.name, f"version {frame}: house wording is 'countries and territories' (JP, 3 Nov 2026)")
    if second is not None and not re.search(re.escape(RDM_API) + r"[A-Za-z0-9_.-]+", second):
        fail(spot.name, f"version {frame}: 'Second comment' is not a Reference Data Manager record link")


def spotlight_day(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m - 1]} {y}"


def unescape(s):
    import html as _h
    return _h.unescape(s)


def check_assignment(rows, spots):
    """Duplicate ids, make-ups that copy no slot, and slots with more than one Spotlight folder."""
    ids = [r["spotlight"] for r in rows]
    for i in sorted({i for i in ids if ids.count(i) > 1}):
        failures.append(f"assignment.csv: Spotlight {i} is listed more than once")
    slot = lambda r: (r["block"], r["link_placement"], r["ground"], r["template"])
    original = [r for r in rows if 2 <= int(r["spotlight"]) <= 33]  # the pre-registered slots
    slots, blocks = {slot(r) for r in original}, {r["block"] for r in original}
    with_folder = {int(p.name.split("-")[0]) for p in spots if not is_002(p)}  # 002 and 003 topics are not 001's
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
            if (ROOT / "spotlights" / f"_{name}").is_dir():  # retired (private, never published again), data kept
                check_retired(base, name); continue
            fail(name, f"published on {base} but missing here (removed or renamed)"); continue
        r = git("diff", "--name-only", base, "--", f"spotlights/{name}/data", f"spotlights/{name}/retrieval.json")
        if r.returncode:
            fail(name, f"git diff against {base} failed: {r.stderr.strip()}"); continue
        changed = [p for p in r.stdout.splitlines() if f"spotlights/{name}/data/api_refresh/" not in p]
        if changed:
            fail(name, "published data snapshot changed: " + ", ".join(changed))


def check_retired(base, name):
    """spotlights/_<name> keeps every data file and retrieval.json of spotlights/<name> on the base, byte for byte."""
    listing = git("ls-tree", "-r", base, "--", f"spotlights/{name}/data", f"spotlights/{name}/retrieval.json")
    if listing.returncode:
        fail(name, f"git ls-tree on {base} failed: {listing.stderr.strip()}"); return
    for line in listing.stdout.splitlines():
        blob, path = line.split()[2], line.split("\t")[1]
        if f"spotlights/{name}/data/api_refresh/" in path:
            continue
        here = ROOT / "spotlights" / f"_{name}" / pathlib.Path(path).relative_to(f"spotlights/{name}")
        if not here.exists():
            fail(name, f"retired as _{name}, but {path} is missing there"); continue
        h = subprocess.run(["git", "hash-object", str(here)], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        if h != blob:
            fail(name, f"retired as _{name}, but {path} changed")


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
        if line not in ("None yet.", "- (none yet)") and not any(line == x for x in rest):
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
    rows2, rows3 = [], []
    if (ROOT / EXP2 / "assignment.csv").exists():
        with open(ROOT / EXP2 / "assignment.csv", encoding="utf-8", newline="") as f:
            rows2 = list(csv.DictReader(f))
    if (ROOT / EXP3 / "assignment.csv").exists():
        with open(ROOT / EXP3 / "assignment.csv", encoding="utf-8", newline="") as f:
            rows3 = list(csv.DictReader(f))
    spots, misnamed = spotlight_dirs(ROOT / "spotlights")
    check_assignment(rows, spots)
    for p in misnamed:
        fail(p.name, "not a Spotlight folder name (NN-slug); prefix it with _ to keep it private")
    numbers = [int(p.name.split("-")[0]) for p in spots]
    for p in spots:
        if numbers.count(int(p.name.split("-")[0])) > 1:
            # Allowed once: experiment 003 topic folders that replace one number's versions between them, each
            # naming its frames (replacement_of.frames), with no frame in two folders (Spotlight 22, 4 Nov 2026).
            same = [q for q in spots if q.name.split("-")[0] == p.name.split("-")[0]]
            frames = []
            for q in same:
                try:
                    mq = json.loads((q / "meta.json").read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    mq = {}
                if topic_experiment(q) != "003" or not (mq.get("replacement_of") or {}).get("frames"):
                    fail(p.name, "another Spotlight folder has the same number"); break
                frames += mq["replacement_of"]["frames"]
            else:
                if len(frames) != len(set(frames)):
                    fail(p.name, "two folders of this number hold the same version frame")
                num = p.name.split("-")[0]
                want = sorted(r["frame"] for r in rows3 if r["spotlight"] == str(int(num)) and r["network"] == "X")
                if sorted(frames) != want:
                    fail(p.name, f"the folders of this number hold frames {sorted(frames)} but assignment.csv (003) has {want}")
    for spot in spots:
        if is_002(spot):
            check_002(spot, rows3 if topic_experiment(spot) == "003" else rows2, topic_experiment(spot)); continue
        missing = [f for f in REQUIRED if not (spot / f).exists()]
        if missing:
            fail(spot.name, "missing " + ", ".join(missing)); continue
        check_meta(spot); check_stats(spot); check_captions(spot); check_banner(spot, assignment); check_rdm(spot)
    if a.base:
        if git("rev-parse", "--verify", "--quiet", f"{a.base}^{{commit}}").returncode:
            failures.append(f"--base {a.base}: no such commit here (fetch it first, e.g. git fetch origin main)")
        else:
            check_frozen(a.base)
            check_append_only(a.base, f"{EXP}/assignment.csv", rows=True)
            check_append_only(a.base, f"{EXP}/posts.csv", rows=True)
            check_append_only(a.base, f"{EXP}/outcomes.csv", rows=True)
            check_append_only(a.base, f"{EXP}/PREREGISTRATION.md", rows=False)
            for name in ("assignment.csv", "posts.csv", "outcomes.csv", "topics.csv"):
                check_append_only(a.base, f"{EXP2}/{name}", rows=True)
                check_append_only(a.base, f"{EXP3}/{name}", rows=True)
            check_append_only(a.base, f"{EXP2}/PREREGISTRATION.md", rows=False)
    print(f"Checked {len(spots)} Spotlight(s).")
    for f in failures:
        print("FAIL", f)
    if failures:
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
