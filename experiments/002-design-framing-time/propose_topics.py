"""Experiment 002, phase 1: propose 50 topics from the UN System Data Commons catalogue of 31 October 2026.

A topic is one indicator, one place and, optionally, a breakdown (wealth, residence or sex). Each topic gets
three versions, each with a different headline, chosen from the framings its data support:

  T  what it would take   the house rule: required pace, countries short of a per-country threshold, or the
                          level; needs a value for the place
  L  the long view        the observed trend; needs a published series with at least two years for the place
  G  behind the average   the gap across the breakdown, or between the places compared; needs a breakdown with
                          a moderate or strong fact, or a comparison place
  D  the data behind it   coverage and recency; needs a moderate or strong freshness fact

Coverage rule: the indicator needs good country coverage, at least 100 places in the latest snapshot (the
catalogue's moderate or strong country fact). An indicator below that enters only as a data-gap topic: World or
SDG regions compared, no breakdown, all three versions about its data gaps (D1 coverage, D2 recency, D3 which
regions have data). An indicator collected only where it applies is neither (female genital mutilation).
A good-coverage topic needs at least three framings; a topic with a pace needs T and L.

Place types and what makes them eligible:
  world             the World (T needs a world value, L a world series of two years or more)
  region            one SDG region with a published aggregate series for the indicator
  regions_compared  the SDG regions side by side; a moderate or strong group fact with at least 6 of 8 SDG regions
  groupings         LDCs, LLDCs and SIDS side by side, against the World; all three in the group fact
  grouping          one of LDCs, LLDCs or SIDS; listed in the group fact
  income_groups     World Bank income groups side by side        } not places in the Data Commons (31 October
  fcv               fragile and conflict-affected situations      } run); conditional on World Bank published
                    against the World                             } aggregates for the same series (phase 2)

Draw (seed 20261101): 24 topics with a pace and 26 without, quotas by place type (QUOTA, scarcest first), every
eligible indicator family at least once, at most 5 per family, one topic per family and place, at most one
data-gap topic per family.

Run: python3 experiments/002-design-framing-time/propose_topics.py   (writes proposals.csv next to this file)
No data values are computed here: eligibility comes from the catalogue run and is checked again in phase 2.
"""
import collections
import csv
import json
import pathlib
import random
import re

HERE = pathlib.Path(__file__).parent
CAT = json.loads((HERE.parents[1] / "docs/catalogue-2026-10/catalogue.json").read_text())
SEED, MAX_PER_FAMILY, GOOD_COVERAGE = 20261101, 5, 100
BY_DESIGN = {"fgm"}  # collected only where the practice is concentrated: low country count is not a data gap
QUOTA = {  # place type: (pace stratum, other stratum), in filling order
    "fcv": (2, 2), "income_groups": (2, 2), "groupings": (3, 3), "grouping": (2, 4),
    "regions_compared": (4, 4), "world": (5, 5), "region": (6, 6)}
# Seven of the eight SDG regions: Australia and New Zealand was left out by mistake, found after the draw and the
# banners were built (PREREGISTRATION.md, Amendments before the first post, 4 Nov 2026). Kept as drawn.
SDG_REGIONS = ["Sub-Saharan Africa", "Northern Africa and Western Asia", "Central and Southern Asia",
               "Eastern and South-eastern Asia", "Latin America and the Caribbean",
               "Oceania excluding Australia and New Zealand", "Europe and Northern America"]
GROUPINGS = {"LDCs": "Least developed countries", "LLDCs": "Landlocked developing countries",
             "SIDS": "Small island developing states"}
PLACE_LABEL = {"world": "World", "regions_compared": "SDG regions compared",
               "groupings": "LDCs, LLDCs and SIDS compared with the World",
               "income_groups": "World Bank income groups compared",
               "fcv": "Fragile and conflict-affected situations against the World"}
COMPARISONS = {"regions_compared", "groupings", "income_groups", "fcv"}
CAT_NAME = {"LDCs": "Least developed countries (LDCs)", "LLDCs": "Landlocked developing countries (LLDCs)",
            "SIDS": "Small Island Developing States (SIDS)"}
FAMILY = {"child_marriage_18": "child_marriage", "child_marriage_15": "child_marriage"}
FEED = {"learning_proficiency": "#EduSky", "school_completion": "#EduSky", "pre_primary": "#EduSky",
        "ecd": "#EduSky", "child_poverty_mpi": "#EconSky", "youth_neet": "#EconSky", "child_labour": "#EconSky",
        "water": "#EconSky", "sanitation": "#EconSky"}  # everything else: #PolicySky
BREAKDOWN = {"wealth": "poorest and richest fifth", "location": "rural and urban", "sex": "girls and boys",
             "none": "no breakdown"}
strong = lambda f: f.get("strength") in ("moderate", "strong")

aggregate_series = collections.defaultdict(set)
for a in CAT["aggregates_found"]:
    for v in a["values"]:
        if int(v["n_points"]) >= 2:
            aggregate_series[v["theme"]].add(a["name"])

frame = []
for t in CAT["themes"]:
    facts = collections.defaultdict(list)
    for f in t["facts"]:
        if strong(f):
            facts[f["kind"]].append(f)
    places = None
    for f in t["facts"]:
        m = re.search(r"\((\d+) places", f["fact"]) if f["kind"] == "countries" else None
        places = int(m.group(1)) if m else places
    good = places is not None and places >= GOOD_COVERAGE
    if not good and t["theme"] in BY_DESIGN:
        continue
    world = t["bases"][0].get("world", {}) if t["bases"] else {}
    world_level = bool(world.get("last_year"))
    world_trend = world_level and world.get("first_year") and world["first_year"] != world["last_year"]
    pace = bool(facts.get("pace"))
    fresh = bool(facts.get("freshness"))
    breakdowns = [b for b in ("wealth", "location", "sex") if facts.get(b)]
    group_fact = facts["groups"][0]["fact"] if facts.get("groups") else ""
    m = re.search(r"(\d+) of 8 SDG regions", group_fact)
    n_regions = int(m.group(1)) if m else 0
    listed = {g for g in GROUPINGS if re.search(rf"\b{g}\b", group_fact)}
    has_aggregates = bool(aggregate_series[t["theme"]]) or n_regions > 0

    places_for = [("world", "World")]
    places_for += [("region", r) for r in SDG_REGIONS if r in aggregate_series[t["theme"]]]
    if n_regions >= 6:
        places_for.append(("regions_compared", PLACE_LABEL["regions_compared"]))
    if listed == set(GROUPINGS):
        places_for.append(("groupings", PLACE_LABEL["groupings"]))
    places_for += [("grouping", GROUPINGS[g] + f" ({g})") for g in sorted(listed)]
    if has_aggregates:
        places_for += [("income_groups", PLACE_LABEL["income_groups"]), ("fcv", PLACE_LABEL["fcv"])]

    base = dict(theme=t["theme"], family=FAMILY.get(t["theme"], t["theme"]), indicator=t["label"],
                sdg=t["sdg_indicator"], target_basis=t["target_basis"] or "none", places_in_snapshot=places,
                feed_tag=FEED.get(t["theme"], "#PolicySky"), group_fact=group_fact,
                coverage_fact=(facts["freshness"][0]["fact"] if fresh else f"{places} places in the latest snapshot"))
    if not good:  # data-gap topic
        for ptype, place in places_for:
            if ptype in ("world", "regions_compared"):
                frame.append(dict(base, pace=0, kind="data gap", place_type=ptype, place=place, breakdown="none",
                                  compares=BREAKDOWN["none"], frames="D1|D2|D3", conditional=0))
        continue
    series = aggregate_series[t["theme"]]
    for ptype, place in places_for:
        level = world_level if ptype == "world" else True  # every other place was admitted on a published aggregate
        if ptype == "world":
            trend = world_trend
        elif ptype == "region":
            trend = place in series
        elif ptype == "regions_compared":
            trend = any(r in series for r in SDG_REGIONS)
        elif ptype == "groupings":
            trend = all(CAT_NAME[g] in series for g in GROUPINGS)
        elif ptype == "grouping":
            trend = any(CAT_NAME[g] in series for g in GROUPINGS if place.endswith(f"({g})"))
        else:  # income groups, FCS: conditional; a world series of two years or more is the proxy until phase 2
            trend = world_trend
        for b in breakdowns + ["none"]:
            frames = [f for f, ok in (("T", level), ("L", trend), ("G", b != "none" or ptype in COMPARISONS),
                                      ("D", fresh)) if ok]
            if len(frames) < 3 or (pace and not {"T", "L"} <= set(frames)):
                continue
            frame.append(dict(base, pace=int(pace), kind="standard", place_type=ptype, place=place, breakdown=b,
                              compares=BREAKDOWN[b] if b != "none" or ptype not in COMPARISONS
                              else "the places compared",
                              frames="|".join(frames), conditional=int(ptype in ("income_groups", "fcv"))))

rng = random.Random(SEED)
by_family = collections.Counter()
seen, gap_families, picked = set(), set(), []


def take(r):
    picked.append(r); by_family[r["family"]] += 1; seen.add((r["family"], r["place"]))
    if r["kind"] == "data gap":
        gap_families.add(r["family"])


def allowed(r):
    return (by_family[r["family"]] < MAX_PER_FAMILY and (r["family"], r["place"]) not in seen
            and not (r["kind"] == "data gap" and r["family"] in gap_families))


for stratum in (1, 0):
    pool = [r for r in frame if r["pace"] == stratum]
    rng.shuffle(pool)
    for ptype, quota in QUOTA.items():
        n = quota[0] if stratum == 1 else quota[1]
        got = 0
        for r in pool:
            if got >= n:
                break
            if r["place_type"] == ptype and allowed(r):
                take(r); got += 1
        if got < n:
            print(f"warning: stratum {stratum}, {ptype}: {got} of {n}")
    # Every eligible family at least once: a missing family replaces a topic of the most represented family at
    # the same place type.
    missing = sorted({r["family"] for r in pool} - {r["family"] for r in picked if r["pace"] == stratum})
    rng.shuffle(missing)
    for fam in missing:
        counts = collections.Counter(r["family"] for r in picked if r["pace"] == stratum)
        done = False
        for out in sorted((r for r in picked if r["pace"] == stratum and counts[r["family"]] >= 2),
                          key=lambda r: -counts[r["family"]]):
            cands = [r for r in pool if r["family"] == fam and r["place_type"] == out["place_type"]
                     and (r["family"], r["place"]) not in seen
                     and not (r["kind"] == "data gap" and fam in gap_families)]
            if cands:
                picked.remove(out); by_family[out["family"]] -= 1; seen.discard((out["family"], out["place"]))
                take(cands[0]); done = True
                break
        if not done:
            print(f"warning: stratum {stratum}: could not include {fam}")

picked.sort(key=lambda r: (-r["pace"], list(QUOTA).index(r["place_type"])))
for i, r in enumerate(picked, 1):
    r["proposal"] = f"P{i:02d}"

cols = ["proposal", "pace", "kind", "indicator", "sdg", "target_basis", "place_type", "place", "breakdown",
        "compares", "frames", "conditional", "feed_tag", "places_in_snapshot", "theme", "family", "group_fact",
        "coverage_fact"]
with open(HERE / "proposals.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(picked)

print(f"Eligible frame: {len(frame)} topics from {len({r['theme'] for r in frame})} indicators "
      f"({sum(r['pace'] for r in frame)} with a pace, {sum(r['kind'] == 'data gap' for r in frame)} data-gap)")
print(f"Proposed: {len(picked)} ({sum(r['pace'] for r in picked)} with a pace, "
      f"{sum(r['conditional'] for r in picked)} conditional, {sum(r['kind'] == 'data gap' for r in picked)} data-gap, "
      f"{sum(r['breakdown'] == 'none' for r in picked)} without a breakdown)")
print(f"By place type: {dict(collections.Counter(r['place_type'] for r in picked))}")
print(f"Framings offered: {dict(collections.Counter(r['frames'] for r in picked))}")
print(f"Families ({len(by_family)}): {dict(collections.Counter(r['family'] for r in picked))}")
