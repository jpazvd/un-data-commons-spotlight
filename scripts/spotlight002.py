"""Experiment 002 Spotlights: places, families, and the numbers behind each framing.

Usage:
    python scripts/spotlight002.py stats spotlights/NN-slug F     # write versions/F/stats.json (F = T, L, G, D, D1, D2, D3)
    python scripts/spotlight002.py check spotlights/NN-slug       # which framings the topic's data support, and why

Every number on an experiment 002 banner or caption comes from stats.json, and stats.json comes only from the
topic's committed data/*.csv files (see experiments/002-design-framing-time/build_topic_data.py), so the
validator can re-derive it. The framings (PREREGISTRATION.md, "Arms"):

  T  what it would take (house rule, production task STEP 2b): the pace needed to reach a global target by its
     year, against the observed pace; for a per-country threshold, the number of countries still above it;
     with no numeric target, the level, with no target wording.
  L  the long view: the change since the base year, in the indicator's units.
  G  behind the average: the gap between the two ends of the breakdown (published aggregates by group, or the
     number of countries where the gap points one way, with at least 10 countries with both groups in the same
     year); with no breakdown, the gap between the places compared.
  D  the data behind it: how many countries have data and how recent their latest values are.
  D1, D2, D3 (data-gap topics): how many countries have any data; how recent; which SDG regions have data.

Method, fixed: paces are linear, in the indicator's units per year, from the first to the latest year of the
published series; "stale" means a latest value from 2020 or earlier (as compute_stats.py); no aggregate is
computed from country values.
"""
import csv
import json
import math
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXP = ROOT / "experiments" / "002-design-framing-time"
STALE_CUTOFF = 2020
MIN_COUNTRIES_GAP = 10

SDG_REGIONS = {  # the eight SDG regions, in the order of the UN SDG Report
    "SubSaharanAfrica": "Sub-Saharan Africa",
    "undata-geo/G00103000": "Northern Africa and Western Asia",
    "undata-geo/G00116000": "Central and Southern Asia",
    "undata-geo/G00122000": "Eastern and South-eastern Asia",
    "LatinAmericaAndCaribbean": "Latin America and the Caribbean",
    "undata-geo/G00145000": "Oceania excluding Australia and New Zealand",
    "AustraliaAndNewZealand": "Australia and New Zealand",
    "undata-geo/G00126000": "Europe and Northern America",
}
SHORT = {
    "SubSaharanAfrica": "Sub-Saharan Africa",
    "undata-geo/G00103000": "N. Africa and W. Asia",
    "undata-geo/G00116000": "Central and S. Asia",
    "undata-geo/G00122000": "E. and S.-E. Asia",
    "LatinAmericaAndCaribbean": "Latin America, Caribbean",
    "undata-geo/G00145000": "Oceania (excl. Aus., NZ)",
    "AustraliaAndNewZealand": "Australia and NZ",
    "undata-geo/G00126000": "Europe and N. America",
    "undata-geo/G00404000": "LDCs",
    "undata-geo/G00403000": "LLDCs",
    "undata-geo/G00405000": "SIDS",
    "Earth": "World",
}
GROUPINGS = {
    "undata-geo/G00404000": "Least developed countries",
    "undata-geo/G00403000": "Landlocked developing countries",
    "undata-geo/G00405000": "Small island developing states",
}
# Membership: the Data Commons lists the countries of these places directly ...
DIRECT_MEMBERSHIP = {k: v for k, v in {**SDG_REGIONS, **GROUPINGS}.items()
                     if k in ("SubSaharanAfrica", "LatinAmericaAndCaribbean", "undata-geo/G00145000",
                              "AustraliaAndNewZealand", *GROUPINGS)}
# ... and the other four SDG regions through their M49 subregions (the region itself returns no countries).
COMPOSED_REGIONS = {
    "undata-geo/G00103000": ("Northern Africa and Western Asia", ["NorthernAfrica", "WesternAsia"]),
    "undata-geo/G00116000": ("Central and Southern Asia", ["CentralAsia", "SouthernAsia"]),
    "undata-geo/G00122000": ("Eastern and South-eastern Asia", ["EasternAsia", "SouthEasternAsia"]),
    "undata-geo/G00126000": ("Europe and Northern America",
                             ["NorthernEurope", "WesternEurope", "SouthernEurope", "EasternEurope",
                              "undata-geo/G00136000"]),
}
# The Data Commons lists the Turks and Caicos Islands under Northern Europe; in M49 it is in the Caribbean. Its LDC list
# still has Bhutan and Sao Tome and Principe, which graduated in December 2023 and in 2024 (UNCTAD, UN list of least
# developed countries, 44 countries, read on 1 November 2026: unctad.org/topic/vulnerable-economies/least-developed-countries/list).
NOT_IN_REGION = {"undata-geo/G00126000": ("country/TCA",), "undata-geo/G00404000": ("country/BTN", "country/STP")}
# Display names: the UN short names where the Data Commons uses others.
NAME_FIX = {"East Timor": "Timor-Leste", "Macedonia [FYROM]": "North Macedonia", "Swaziland": "Eswatini",
            "Ivory Coast": "Côte d'Ivoire", "Cape Verde": "Cabo Verde", "Czech Republic": "Czechia",
            "Turkey": "Türkiye", "Palestinian Territories": "State of Palestine", "Burma": "Myanmar",
            "Laos": "Lao PDR", "North Korea": "DPR Korea", "South Korea": "Republic of Korea",
            "Federated States of Micronesia": "Micronesia (Fed. States of)", "Vietnam": "Viet Nam",
            "Syria": "Syrian Arab Republic", "Russia": "Russian Federation", "Iran": "Iran (Islamic Rep. of)",
            "Bolivia": "Bolivia (Plurinational State of)", "Tanzania": "United Republic of Tanzania",
            "Moldova": "Republic of Moldova", "Venezuela": "Venezuela (Bolivarian Rep. of)",
            "Democratic Republic of the Congo": "DR Congo", "Republic of the Congo": "Congo"}
PROVIDER = {"undata/sdg/": "UN SDG Global Database", "undata/unicef/": "UNICEF Data Warehouse",
            "undata/who/": "WHO Global Health Observatory", "undata/ilo/": "ILOSTAT", "undata/unfpa/": "UNFPA"}


def nm(name):
    return NAME_FIX.get(name, name)

GROUPS = {"wealth": ("poorest", "richest"), "location": ("rural", "urban"), "sex": ("female", "male")}

# Indicator families: what is measured, in which units, which direction is progress, who is the custodian,
# and the target used by the house rule (STEP 2b). Custodians as listed in the UN SDG indicator metadata.
FAMILY = {
    "water": dict(what="people using safely managed drinking water", short="safely managed drinking water",
                  unit="%", better="higher", custodian="WHO/UNICEF JMP", target=("universal", 100, 2030, "SDG 6.1")),
    "sanitation": dict(what="people using safely managed sanitation", short="safely managed sanitation",
                       unit="%", better="higher", custodian="WHO/UNICEF JMP", target=("universal", 100, 2030, "SDG 6.2")),
    "school_completion": dict(what="children completing primary school", short="primary completion",
                              unit="%", better="higher", custodian="UNESCO UIS", target=("universal", 100, 2030, "SDG 4.1")),
    "pre_primary": dict(what="children in organized learning a year before primary school", short="pre-primary participation",
                        unit="%", better="higher", custodian="UNESCO UIS", target=("universal", 100, 2030, "SDG 4.2")),
    "learning_proficiency": dict(what="children at the end of primary school reading at a minimum level",
                                 short="minimum reading proficiency", unit="%", better="higher", custodian="UNESCO UIS",
                                 target=None),  # house rule: 4.1.1 has no numeric target
    "child_marriage_18": dict(what="women aged 20 to 24 first married or in union before 18", short="child marriage",
                              unit="%", better="lower", custodian="UNICEF", target=("elimination", 0, 2030, "SDG 5.3")),
    "child_marriage_15": dict(what="women aged 20 to 24 first married or in union before 15", short="marriage before 15",
                              unit="%", better="lower", custodian="UNICEF", target=("elimination", 0, 2030, "SDG 5.3")),
    "mmr": dict(what="maternal deaths per 100,000 live births", short="maternal mortality", unit=" per 100,000",
                better="lower", custodian="MMEIG", target=("numeric", 70, 2030, "SDG 3.1")),
    "birth_registration": dict(what="children under 5 whose births are registered", short="birth registration",
                               unit="%", better="higher", custodian="UNICEF", target=("universal", 100, 2030, "SDG 16.9")),
    "imr": dict(what="infant deaths per 1,000 live births", short="infant mortality", unit=" per 1,000",
                better="lower", custodian="UN IGME", target=None),
    "wasting": dict(what="children under 5 who are wasted", short="wasting", unit="%", better="lower",
                    custodian="UNICEF/WHO/World Bank JME", target=None),
    "hpv": dict(decimals=0, what="girls with the final dose of HPV vaccine", short="HPV vaccine coverage", unit="%",
                better="higher", custodian="WHO/UNICEF WUENIC", target=None),
    "family_planning": dict(what="women aged 15 to 49 whose need for family planning is met with modern methods",
                            short="demand met with modern methods", unit="%", better="higher",
                            custodian="UN DESA Population Division and UNFPA", target=None),
    "sba": dict(what="births attended by skilled health personnel", short="skilled birth attendance", unit="%",
                better="higher", custodian="UNICEF and WHO", target=None),
    "anaemia_women": dict(what="women aged 15 to 49 with anaemia", short="anaemia in women", unit="%",
                          better="lower", custodian="WHO", target=None),
    "overweight": dict(what="children under 5 who are overweight", short="child overweight", unit="%",
                       better="lower", custodian="UNICEF/WHO/World Bank JME", target=None),
    "youth_neet": dict(what="young people aged 15 to 24 not in education, employment or training",
                       short="youth NEET rate", unit="%", better="lower", custodian="ILO", target=None,
                       method_note="SL_TLF_NEET, which the source labels the previous definition"),
    "stunting": dict(what="children under 5 who are stunted", short="stunting", unit="%", better="lower",
                     custodian="UNICEF/WHO/World Bank JME", target=None),
    "women_local_gov": dict(what="seats in local government held by women", short="women in local government",
                            unit="%", better="higher", custodian="UN Women", target=None),
    "women_parliament": dict(what="seats in national parliaments held by women", short="women in parliament",
                             unit="%", better="higher", custodian="IPU", target=None),
    "dtp3": dict(decimals=0, what="children receiving three doses of DTP vaccine", short="DTP3 coverage", unit="%",
                 better="higher", custodian="WHO/UNICEF WUENIC", target=None),
    "mcv2": dict(decimals=0, what="children receiving a second dose of measles vaccine", short="MCV2 coverage", unit="%",
                 better="higher", custodian="WHO/UNICEF WUENIC", target=None),
    "pcv3": dict(decimals=0, what="children receiving three doses of pneumococcal vaccine", short="PCV3 coverage", unit="%",
                 better="higher", custodian="WHO/UNICEF WUENIC", target=None),
    "violent_discipline": dict(what="children aged 1 to 14 punished violently by caregivers in the past month",
                               short="violent discipline", unit="%", better="lower", custodian="UNICEF",
                               target=("elimination", 0, 2030, "SDG 16.2")),
    "child_poverty_mpi": dict(what="children living in multidimensional poverty (national definitions)",
                              short="child multidimensional poverty", unit="%", better="lower",
                              custodian="national statistical offices", target=None),
    "ecd": dict(what="children aged 24 to 59 months developmentally on track", short="early childhood development",
                unit="%", better="higher", custodian="UNICEF", target=None),
    "nmr": dict(what="neonatal deaths per 1,000 live births", short="neonatal mortality", unit=" per 1,000",
                better="lower", custodian="UN IGME", target=("per_country_threshold", 12, 2030, "SDG 3.2")),
    "u5mr": dict(what="deaths before age five per 1,000 live births", short="under-five mortality", unit=" per 1,000",
                 better="lower", custodian="UN IGME", target=("per_country_threshold", 25, 2030, "SDG 3.2")),
    "abr": dict(what="births per 1,000 girls aged 15 to 19", short="adolescent birth rate", unit=" per 1,000",
                better="lower", custodian="UN DESA Population Division and UNFPA", target=None),
    "hiv_adolescents": dict(what="new HIV infections per 1,000 uninfected adolescents aged 15 to 19",
                            short="new HIV infections, ages 15 to 19", unit=" per 1,000", better="lower",
                            custodian="UNAIDS", target=None),
    # SDG 8.7.1 series SL_TLF_CHLDEA: economic activity only (not household chores). Named as the source names it,
    # and with no target wording: SDG target 8.7 is about child labour as defined by ILO and UNICEF.
    "child_labour": dict(what="children aged 5 to 17 engaged in economic activity", short="economic activity, ages 5 to 17",
                         unit="%", better="lower", custodian="ILO and UNICEF", target=None),
}
SEX_WORDS = {"youth_neet": ("young women", "young men"), "anaemia_women": ("women", "men")}
GROUP_WORDS = {"poorest": "the poorest fifth", "richest": "the richest fifth", "rural": "rural areas",
               "urban": "urban areas", "female": "girls", "male": "boys"}


def group_word(family, g):
    if g in ("female", "male") and family in SEX_WORDS:
        return SEX_WORDS[family][0 if g == "female" else 1]
    return GROUP_WORDS[g]


def proposals():
    with open(EXP / "proposals.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def places_of(prop):
    """Data Commons dcids of the topic's place(s); the World is always 'Earth'."""
    t, name = prop["place_type"], prop["place"]
    if t == "world":
        return ["Earth"]
    if t == "regions_compared":
        return list(SDG_REGIONS) + ["Earth"]
    if t == "groupings":
        return list(GROUPINGS) + ["Earth"]
    for d, n in {**SDG_REGIONS, **GROUPINGS}.items():
        if n.lower().startswith(name.lower()[:20]) or name.lower().startswith(n.lower()[:20]):
            return [d]
    raise ValueError(f"no place for {name!r}")


def target(theme):
    t = FAMILY[theme]["target"]
    if not t:
        return {"basis": "none", "value": None, "year": None}
    kind, value, year, sdg = t
    basis = f"{sdg} (per country)" if kind == "per_country_threshold" else sdg
    return {"basis": basis, "value": value, "year": year, "kind": kind}


def title(prop):
    return f"{prop['indicator']}, {prop['place']}" + (f", by {prop['breakdown']}" if prop["breakdown"] in GROUPS else "")


# ---------------------------------------------------------------- reading a topic folder

def _csv(path):
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class Topic:
    def __init__(self, folder):
        self.dir = pathlib.Path(folder)
        self.meta = json.loads((self.dir / "meta.json").read_text(encoding="utf-8"))
        x = self.meta["experiment"]
        self.family, self.place_type, self.places = x["family"], x["place_type"], x["place_dcids"]
        self.breakdown = x["breakdown"] if x["breakdown"] in GROUPS else None
        # Places a comparison needs: 6 of the 8 SDG regions, 3 for groupings (PREREGISTRATION.md), unless the topic's
        # meta.json sets experiment.min_places_compared with its reason (Spotlight 22-G, JP, 4 Nov 2026: three regions
        # publish both rural and urban aggregates; the chart shows them and says so).
        self.min_places = x.get("min_places_compared")
        self.fam = FAMILY[self.family]
        self.better = self.fam["better"]
        d = self.dir / "data"
        self.world = sorted((int(r["year"]), float(r["value"])) for r in _csv(d / "world.csv"))
        self.countries = {r["dcid"]: (nm(r["name"]), int(r["year"]), float(r["value"]))
                          for r in _csv(d / "countries_latest.csv")}
        ret = json.loads((self.dir / "retrieval.json").read_text(encoding="utf-8")) if (self.dir / "retrieval.json").exists() else {}
        bv = ((ret.get("indicator") or {}).get("breakdown_variables") or [None])[0] or ""
        self.breakdown_source = next((v for k, v in PROVIDER.items() if bv.startswith(k)), None)
        self.series, self.names = {}, {"Earth": "World"}
        for r in _csv(d / "place_series.csv"):
            self.series.setdefault(r["place_dcid"], []).append((int(r["year"]), float(r["value"])))
            self.names[r["place_dcid"]] = r["name"]
        for k in self.series:
            self.series[k].sort()
        if self.world:
            self.series["Earth"] = self.world
        self.members = {}
        for r in _csv(d / "membership.csv"):
            self.members.setdefault(r["place_dcid"], {})[r["dcid"]] = nm(r["name"])
        self.universe = {c: n for p in SDG_REGIONS for c, n in self.members.get(p, {}).items()}
        self.bd_c = {}
        for r in _csv(d / "breakdown_countries.csv"):
            self.bd_c.setdefault(r["group"], {})[r["dcid"]] = (nm(r["name"]), int(r["year"]), float(r["value"]))
        self.bd_a = {}
        for r in _csv(d / "breakdown_aggregates.csv"):
            self.bd_a.setdefault((r["place_dcid"], r["group"]), []).append((int(r["year"]), float(r["value"])))
        for k in self.bd_a:
            self.bd_a[k].sort()

    def need(self):
        return int(self.min_places) if self.min_places else (6 if self.place_type == "regions_compared" else 3)

    def compared(self):
        return self.place_type in ("regions_compared", "groupings")

    def main_place(self):
        return self.places[0]

    def members_of(self, place):
        return self.universe if place == "Earth" else self.members.get(place, {})

    def countries_in(self, place):
        """Latest values of the countries and areas of a place (all places returned, for the World)."""
        m = self.members_of(place)
        return {c: v for c, v in self.countries.items() if c in m}


def r1(x):  # stored at four decimals; words and charts round once, when they are written
    return None if x is None else round(x, 4)


r2 = r1


# ---------------------------------------------------------------- framings

def pace(series, tv, ty, better):
    (y0, v0), (y1, v1) = series[0], series[-1]
    span, left = y1 - y0, ty - y1
    if span <= 0 or left <= 0:
        return None
    sign = 1 if better == "lower" else -1
    observed = (v1 - v0) / span            # signed change per year (indicator units)
    required = (tv - v1) / left            # signed change per year needed
    progress, remaining = -sign * observed, -sign * (tv - v1)
    trend = ("target met" if remaining <= 0 else "towards target" if progress > 0
             else "flat" if progress == 0 else "away from target")
    return {"first": {"year": y0, "value": r1(v0)}, "last": {"year": y1, "value": r1(v1)},
            "observed_per_year": r2(observed), "required_per_year": r2(required), "trend": trend,
            "years_left": left, "at_current_pace": r1(v1 + observed * left),
            "required_over_observed": r1(required / observed) if trend == "towards target" and observed else None,
            "series": [[y, v] for y, v in series]}


def frame_T(t):
    tg = target(t.family)
    base = {"frame": "T", "target": tg}
    if tg.get("kind") == "per_country_threshold":
        thr = tg["value"]
        out = {}
        for p in ([t.main_place()] if not t.compared() else t.places):
            cs = t.countries_in(p)
            above = sorted(((n, y, v) for n, y, v in cs.values() if v > thr), key=lambda x: -x[2])
            out[p] = {"place": t.names.get(p, SDG_REGIONS.get(p, p)), "n": len(cs), "n_above": len(above),
                      "years": sorted({y for _, y, _ in cs.values()}),
                      "ranked": [[n, y, v] for n, y, v in sorted(cs.values(), key=lambda x: -x[2])]}
        p = t.main_place()
        o = out[p]
        if o["n"] < MIN_COUNTRIES_GAP:
            return {**base, "ok": False, "reason": f"only {o['n']} countries with data in the place"}
        return {**base, "ok": True, "kind": "threshold", "threshold": thr, **o,
                "place_value": (t.series.get(p) or [[None, None]])[-1]}
    if tg.get("kind") in ("elimination", "universal", "numeric"):
        if not t.compared():
            s = t.series.get(t.main_place())
            if not s or len(s) < 2:
                return {**base, "ok": False, "reason": "no published series of two years or more for the place"}
            pc = pace(s, tg["value"], tg["year"], t.better)
            if not pc:
                return {**base, "ok": False, "reason": "latest year at or after the target year"}
            return {**base, "ok": True, "kind": "pace", "place": t.names.get(t.main_place(), "World"), **pc}
        rows = []
        for p in t.places:
            s = t.series.get(p)
            if s and len(s) >= 2:
                pc = pace(s, tg["value"], tg["year"], t.better)
                if pc:
                    rows.append({"dcid": p, "place": SHORT.get(p, p), **{k: v for k, v in pc.items() if k != "series"}})
        need = t.need()
        if len([r for r in rows if r["dcid"] != "Earth"]) < need:
            return {**base, "ok": False, "reason": f"fewer than {need} places with a published series"}
        big = [r for r in rows if r["dcid"] != "Earth" and len(t.members.get(r["dcid"], {})) >= 5]
        lead = max(big, key=lambda r: abs(r["last"]["value"] - tg["value"]))
        return {**base, "ok": True, "kind": "pace_compared", "places": rows, "lead": lead["dcid"]}
    # no numeric target: the level, no target wording
    if not t.compared():
        p = t.main_place()
        s = t.series.get(p)
        if not s:
            return {**base, "ok": False, "reason": "no published value for the place"}
        cs = t.countries_in(p)
        return {**base, "ok": True, "kind": "level", "place": t.names.get(p, "World"),
                "last": {"year": s[-1][0], "value": r1(s[-1][1])}, "n": len(cs),
                "ranked": [[n, y, v] for n, y, v in sorted(cs.values(), key=lambda x: -x[2])]}
    rows = level_rows(t)
    if rows is None:
        return {**base, "ok": False, "reason": "too few places with a published value in a common year"}
    return {**base, "ok": True, "kind": "level_compared", **rows}


def level_rows(t, year=None):
    """Latest common year of the places compared, and each place's value in it."""
    have = {p: dict(t.series[p]) for p in t.places if t.series.get(p)}
    need = t.need()
    non_world = [p for p in have if p != "Earth"]
    if len(non_world) < need:
        return None
    years = set.intersection(*(set(have[p]) for p in non_world))
    if not years:
        return None
    y = year or max(years)
    rows = [{"dcid": p, "place": SHORT.get(p, p), "value": r1(have[p][y])} for p in have if y in have[p]]
    return {"year": y, "places": rows}


def frame_L(t):
    base = {"frame": "L"}
    if not t.compared():
        s = t.series.get(t.main_place())
        if not s or len(s) < 2:
            return {**base, "ok": False, "reason": "no published series of two years or more"}
        (y0, v0), (y1, v1) = s[0], s[-1]
        return {**base, "ok": True, "kind": "trend", "place": t.names.get(t.main_place(), "World"),
                "first": {"year": y0, "value": r1(v0)}, "last": {"year": y1, "value": r1(v1)},
                "change": r1(v1 - v0), "per_year": r2((v1 - v0) / (y1 - y0)), "series": [[y, v] for y, v in s]}
    have = {p: t.series[p] for p in t.places if t.series.get(p) and len(t.series[p]) >= 2}
    need = t.need()
    if len([p for p in have if p != "Earth"]) < need:
        return {**base, "ok": False, "reason": f"fewer than {need} places with a series of two years or more"}
    # all places over their common years; if that span is under 10 years, leave out the place whose series starts
    # latest (or, if it starts with the others, ends earliest) until it reaches 10 years or too few places are left
    left_out = []
    while True:
        y0 = max(s[0][0] for s in have.values())
        y1 = min(s[-1][0] for s in have.values())
        if y1 - y0 >= 10 or len([p for p in have if p != "Earth"]) <= need:
            break
        cand = [p for p in have if p != "Earth"]
        drop = max(cand, key=lambda p: (have[p][0][0], -have[p][-1][0]))
        left_out.append(SHORT.get(drop, drop))
        del have[drop]
    if y1 <= y0:
        return {**base, "ok": False, "reason": "no common span of years across the places"}
    rows = []
    for p, s in have.items():
        d = dict(s)
        if y0 in d and y1 in d:
            rows.append({"dcid": p, "place": SHORT.get(p, p), "first": r1(d[y0]), "last": r1(d[y1]),
                         "change": r1(d[y1] - d[y0]), "series": [[y, v] for y, v in s if y0 <= y <= y1]})
    sign = 1 if t.better == "higher" else -1
    lead = max((r for r in rows if r["dcid"] != "Earth" and len(t.members.get(r["dcid"], {})) >= 5),
               key=lambda r: sign * r["change"])
    return {**base, "ok": True, "kind": "trend_compared", "from": y0, "to": y1, "places": rows, "lead": lead["dcid"],
            "left_out": left_out}


def frame_G(t):
    base = {"frame": "G"}
    if t.breakdown:
        a, b = GROUPS[t.breakdown]
        # 1. published aggregates by group for the place(s)
        pts = []
        for p in t.places:
            sa, sb = dict(t.bd_a.get((p, a), [])), dict(t.bd_a.get((p, b), []))
            common = set(sa) & set(sb)
            if common:
                y = max(common)
                pts.append({"dcid": p, "place": SHORT.get(p, p), "year": y, a: r1(sa[y]), b: r1(sb[y])})
        if not t.compared() and pts:
            return {**base, "ok": True, "kind": "groups", "groups": [a, b], **pts[0]}
        if t.compared():
            need = t.need()
            if len([x for x in pts if x["dcid"] != "Earth"]) >= need:
                return {**base, "ok": True, "kind": "groups_compared", "groups": [a, b], "places": pts}
        # 2. countries where the gap points one way (same year for both groups)
        p = "Earth" if t.compared() else t.main_place()
        m = t.members_of(p)
        ga, gb = t.bd_c.get(a, {}), t.bd_c.get(b, {})
        both = [(c, ga[c][0], ga[c][1], ga[c][2], gb[c][2]) for c in ga
                if c in gb and ga[c][1] == gb[c][1] and (m is None or c in m)]
        if len(both) < MIN_COUNTRIES_GAP:
            return {**base, "ok": False,
                    "reason": f"{len(both)} countries with both groups in the same year (needs {MIN_COUNTRIES_GAP})"}
        # disadvantage of group a (poorest, rural, girls) against group b
        sign = 1 if t.better == "lower" else -1
        worse_a = sum(1 for *_, va, vb in both if sign * (va - vb) > 0)
        worse_b = sum(1 for *_, va, vb in both if sign * (va - vb) < 0)
        gaps = sorted(([n, y, r1(va), r1(vb), r1(va - vb)] for _, n, y, va, vb in both), key=lambda x: -x[4])
        n_small = sum(1 for *_, va, vb in both if abs(va - vb) < 1)
        return {**base, "ok": True, "kind": "country_gaps", "groups": [a, b], "n_gap_under_1": n_small,
                "place": "World" if p == "Earth" else t.names.get(p, SDG_REGIONS.get(p, GROUPINGS.get(p, p))),
                "n": len(both), "n_a_worse": worse_a, "n_b_worse": worse_b, "n_equal": len(both) - worse_a - worse_b,
                "years": [min(x[1] for x in gaps), max(x[1] for x in gaps)],
                "median_gap": r1(statistics.median(x[4] for x in gaps)), "gaps": gaps}
    if t.compared():
        rows = level_rows(t)
        if rows is None:
            return {**base, "ok": False, "reason": "too few places with a published value in a common year"}
        # extremes among places of five countries or more (Australia and New Zealand has two)
        non_world = [r for r in rows["places"] if r["dcid"] != "Earth" and len(t.members.get(r["dcid"], {})) >= 5]
        hi = max(non_world, key=lambda r: r["value"])
        lo = min(non_world, key=lambda r: r["value"])
        return {**base, "ok": True, "kind": "places_gap", **rows, "highest": hi["dcid"], "lowest": lo["dcid"],
                "difference": r1(hi["value"] - lo["value"]),
                "ratio": r1(hi["value"] / lo["value"]) if lo["value"] else None}
    return {**base, "ok": False, "reason": "no breakdown and no places compared"}


def coverage(t, place):
    cs = t.countries_in(place)
    m = t.members_of(place)
    years = [y for _, y, _ in cs.values()]
    by_year = {}
    for y in years:
        by_year[y] = by_year.get(y, 0) + 1
    in_members = len([c for c in cs if c in m]) if place == "Earth" else len(cs)
    return {"place": "World" if place == "Earth" else t.names.get(place, SDG_REGIONS.get(place, GROUPINGS.get(place, place))),
            "n_with_data": len(cs), "n_members": len(m), "n_members_with_data": in_members,
            "n_stale": sum(1 for y in years if y <= STALE_CUTOFF), "stale_cutoff": STALE_CUTOFF,
            "latest_year_max": max(years) if years else None, "latest_year_min": min(years) if years else None,
            "median_latest_year": statistics.median_low(years) if years else None,
            "by_year": sorted([[y, n] for y, n in by_year.items()])}


def frame_D(t, frame="D"):
    base = {"frame": frame}
    if frame == "D" and t.compared():
        rows = []
        for p in [x for x in t.places if x != "Earth"]:
            cv = coverage(t, p)
            rows.append({"dcid": p, "place": SHORT.get(p, p), **{k: cv[k] for k in ("n_with_data", "n_members", "n_stale")},
                         "share": r1(100 * cv["n_with_data"] / cv["n_members"]) if cv["n_members"] else None})
        if not any(r["n_with_data"] for r in rows):
            return {**base, "ok": False, "reason": "no country data"}
        out = {**base, "ok": True, "kind": "coverage_compared", "places": rows, "stale_cutoff": STALE_CUTOFF}
        if t.place_type == "groupings":  # groupings overlap (a country can be an LDC and an LLDC): count each once
            seen = {}
            for p in [x for x in t.places if x != "Earth"]:
                seen.update(t.countries_in(p))
            out.update({"n_distinct_with_data": len(seen),
                        "n_distinct_stale": sum(1 for _, y, _ in seen.values() if y <= STALE_CUTOFF)})
        return out
    if frame in ("D", "D2", "D1"):
        p = "Earth" if frame != "D" else t.main_place()
        cv = coverage(t, p)
        if cv["n_with_data"] < 1:
            return {**base, "ok": False, "reason": "no country data"}
        kind = {"D": "coverage", "D1": "any_data", "D2": "recency"}[frame]
        return {**base, "ok": True, "kind": kind, **cv}
    rows = []
    for p in SDG_REGIONS:
        m = t.members.get(p, {})
        n = len([c for c in t.countries if c in m])
        rows.append({"dcid": p, "place": SHORT[p], "n_members": len(m), "n_with_data": n,
                     "share": r1(100 * n / len(m)) if m else None})
    return {**base, "ok": True, "kind": "regions_data", "regions": rows,
            "n_universe": len(t.universe), "n_universe_with_data": len([c for c in t.countries if c in t.universe])}


FRAMES = {"T": frame_T, "L": frame_L, "G": frame_G, "D": frame_D,
          "D1": lambda t: frame_D(t, "D1"), "D2": lambda t: frame_D(t, "D2"), "D3": lambda t: frame_D(t, "D3")}


def stats(folder, frame):
    t = Topic(folder)
    s = FRAMES[frame](t)
    s.update({"family": t.family, "what": t.fam["what"], "unit": t.fam["unit"], "better": t.better,
              "custodian": t.fam["custodian"], "breakdown": t.breakdown, "place_type": t.place_type,
              "stale_cutoff": STALE_CUTOFF, "breakdown_source": t.breakdown_source})
    return s


def check(folder):
    t = Topic(folder)
    if t.fam.get("invalid"):
        return {f: {"ok": False, "reason": t.fam["invalid"]} for f in ("T", "L", "G", "D")}
    frames = t.meta["experiment"]["frames_proposed"].split("|")
    return {f: {k: v for k, v in FRAMES[f](t).items() if k in ("ok", "reason", "kind")} for f in frames}


def main(argv):
    if len(argv) >= 3 and argv[0] == "stats":
        folder, frame = pathlib.Path(argv[1]), argv[2]
        s = stats(folder, frame)
        out = folder / "versions" / frame / "stats.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(s, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(out)
    elif len(argv) >= 2 and argv[0] == "check":
        print(json.dumps(check(argv[1]), indent=1))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
