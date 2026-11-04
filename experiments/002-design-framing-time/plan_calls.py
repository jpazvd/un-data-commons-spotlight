"""Plan the UN System Data Commons calls behind experiment 002's data checks.

Reads proposals.csv and the 31 October 2026 catalogue, and writes data/calls_plan.json: for each indicator
family, the exact tool calls (tool, args) that give every number the topic's versions may use.

  base series      get_observations(base, Earth, all)                         World trend and level
  aggregates       get_child_observations(base, Earth, GeoRegion|UNGeoRegion,  published series for SDG regions,
                   1990-2026)                                                 LDCs, LLDCs and SIDS
  countries        get_child_observations(base, Earth, Country, latest)       coverage, recency, thresholds
  breakdown        for each end of the breakdown (poorest/richest fifth, rural/urban, girls/boys):
                   countries latest, World series and aggregates, as above     gap "behind the average"
  membership       get_child_observations(<u5mr base>, <SDG region or grouping>, Country, latest), 11 calls:
                   the countries of each SDG region and of LDCs, LLDCs and SIDS (under-five mortality covers
                   199 countries and areas)

Breakdown variables: the variable whose attributes are the base's plus the breakdown group (exact match first,
then one that drops attributes the base has, never one that adds others), preferring the base's own provider.
No value is computed here.
"""
import csv
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CAT = json.loads((ROOT / "docs/catalogue-2026-10/catalogue.json").read_text())
THEMES = {t["theme"]: t for t in CAT["themes"]}
RANGE = {"date": "range", "date_range_start": "1990", "date_range_end": "2026"}

SDG_REGIONS = {
    "SubSaharanAfrica": "Sub-Saharan Africa",
    "undata-geo/G00103000": "Northern Africa and Western Asia",
    "undata-geo/G00116000": "Central and Southern Asia",
    "undata-geo/G00122000": "Eastern and South-eastern Asia",
    "LatinAmericaAndCaribbean": "Latin America and the Caribbean",
    "undata-geo/G00145000": "Oceania excluding Australia and New Zealand",
    "AustraliaAndNewZealand": "Australia and New Zealand",
    "undata-geo/G00126000": "Europe and Northern America",
}
GROUPINGS = {
    "undata-geo/G00404000": "Least developed countries (LDCs)",
    "undata-geo/G00403000": "Landlocked developing countries (LLDCs)",
    "undata-geo/G00405000": "Small Island Developing States (SIDS)",
}
BREAKDOWN = {
    "wealth": ("Wealth quantile", [("Lowest quintile",), ("Highest quintile",)]),
    "location": ("Urbanization", [("Rural", "Rural area (degree of urbanization)"),
                                  ("Urban", "Urban area (degree of urbanization)")]),
    "sex": ("Sex", [("Female",), ("Male",)]),
}
PREF = ["undata/sdg/", "undata/unicef/", "undata/who/", "undata/"]
# Breakdowns with no variable that only adds the group to the base's attributes. Wealth: the catalogue's wealth pair
# with the most countries with both groups. Location: the custodian's survey-based series for the same measure.
OVERRIDES = {
    ("overweight", "location"): ["undata/who/NUT_ANTH_SH.AGE--Y0T4__EST_BASIS--SURVEY__NUT_STATUS--OVERWEIGHT__URBANIZATION--R",
                                 "undata/who/NUT_ANTH_SH.AGE--Y0T4__EST_BASIS--SURVEY__NUT_STATUS--OVERWEIGHT__URBANIZATION--U"],
    ("nmr", "location"): ["undata/who/MORT_NEONATAL_RATE.AGE--D0T27__EST_BASIS--SURVEY__URBANIZATION--R",
                          "undata/who/MORT_NEONATAL_RATE.AGE--D0T27__EST_BASIS--SURVEY__URBANIZATION--U"],
}


def wealth_pair(theme):
    pairs = [w for w in theme.get("wealth") or [] if w.get("poorest") and w.get("richest")]
    if not pairs:
        return [None, None]
    w = max(pairs, key=lambda w: (w.get("n_both_same_year") or 0, w.get("n_both") or 0))
    return [w["poorest"], w["richest"]]


def provider(dcid):
    return "/".join(dcid.split("/")[:2]) + "/"


def pick(theme, dim, labels):
    base = theme["bases"][0]
    base_attrs = next((v["attributes"] for v in theme["variables"] if v["dcid"] == base["dcid"]), {})
    cands = []
    for v in theme["variables"]:
        a = v.get("attributes") or {}
        if a.get(dim) not in labels:
            continue
        rest = {k: x for k, x in a.items() if k != dim}
        if any(base_attrs.get(k) != x for k, x in rest.items()):
            continue  # adds or changes an attribute the base does not have
        exact = rest == base_attrs
        same = provider(v["dcid"]) == provider(base["dcid"])
        pref = next(i for i, p in enumerate(PREF) if v["dcid"].startswith(p))
        cands.append((not exact, not same, pref, len(v["dcid"]), v["dcid"]))
    return sorted(cands)[0][-1] if cands else None


def main():
    props = list(csv.DictReader(open(HERE / "proposals.csv", encoding="utf-8")))
    fams = {}
    for p in props:
        fams.setdefault(p["theme"], []).append(p)
    plan = {"retrieval_plan_for": "experiment 002 proposals P01-P50", "families": [], "membership": []}
    u5 = THEMES["u5mr"]["bases"][0]["dcid"]
    for dcid, name in {**SDG_REGIONS, **GROUPINGS}.items():
        plan["membership"].append({"place": dcid, "name": name, "tool": "get_child_observations",
                                   "args": {"variable_dcid": u5, "parent_place_dcid": dcid,
                                            "child_place_type": "Country", "date": "latest"}})
    for th, ps in fams.items():
        t = THEMES[th]
        base = t["bases"][0]["dcid"]
        calls = [
            {"role": "world", "tool": "get_observations",
             "args": {"variable_dcid": base, "place_dcid": "Earth", "date": "all"}},
            {"role": "countries", "tool": "get_child_observations",
             "args": {"variable_dcid": base, "parent_place_dcid": "Earth", "child_place_type": "Country",
                      "date": "latest"}},
        ]
        non_world = any(p["place_type"] != "world" for p in ps)
        if non_world:
            for typ in ("UNGeoRegion", "GeoRegion"):
                calls.append({"role": f"aggregates_{typ}", "tool": "get_child_observations",
                              "args": {"variable_dcid": base, "parent_place_dcid": "Earth",
                                       "child_place_type": typ, **RANGE}})
        breakdowns = {}
        for p in ps:
            b = p["breakdown"]
            if b in BREAKDOWN and b not in breakdowns:
                dim, ends = BREAKDOWN[b]
                pair = OVERRIDES.get((th, b)) or [pick(t, dim, labels) for labels in ends]
                if b == "wealth" and None in pair:
                    pair = wealth_pair(t)
                breakdowns[b] = pair
                for end, var in zip(("low", "high") if b == "wealth" else ("a", "b"), pair):
                    if not var:
                        continue
                    calls.append({"role": f"{b}_{end}_countries", "tool": "get_child_observations",
                                  "args": {"variable_dcid": var, "parent_place_dcid": "Earth",
                                           "child_place_type": "Country", "date": "latest"}})
                    calls.append({"role": f"{b}_{end}_world", "tool": "get_observations",
                                  "args": {"variable_dcid": var, "place_dcid": "Earth", "date": "all"}})
                    if non_world:
                        for typ in ("UNGeoRegion", "GeoRegion"):
                            calls.append({"role": f"{b}_{end}_aggregates_{typ}", "tool": "get_child_observations",
                                          "args": {"variable_dcid": var, "parent_place_dcid": "Earth",
                                                   "child_place_type": typ, **RANGE}})
        plan["families"].append({
            "theme": th, "label": t["label"], "sdg": t["sdg_indicator"], "series_codes": t["series_codes"],
            "target_basis": t["target_basis"], "base": base, "breakdowns": breakdowns,
            "proposals": [p["proposal"] for p in ps], "calls": calls})
    out = HERE / "data" / "calls_plan.json"
    out.write_text(json.dumps(plan, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    n = sum(len(f["calls"]) for f in plan["families"]) + len(plan["membership"])
    print(f"{len(plan['families'])} families, {n} calls -> {out}")
    for f in plan["families"]:
        print(f["theme"], len(f["calls"]), f["proposals"], {k: v for k, v in f["breakdowns"].items()})


if __name__ == "__main__":
    main()
