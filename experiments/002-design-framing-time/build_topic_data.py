"""Write the data snapshot of an experiment 002 topic from the saved Data Commons responses.

Usage:
    python build_topic_data.py P10 OUT_DIR [--spotlight NN --slug SLUG]

Reads data/calls_plan.json (the planned calls), data/calls_index.json and data/raw/<id>.json (every response,
verbatim, saved by extract_calls.py) and writes into OUT_DIR:

  data/world.csv                World series of the indicator (dcid,name,year,value)
  data/countries_latest.csv     each country's or area's latest value (dcid,name,year,value)
  data/place_series.csv         published aggregate series of the topic's place(s) (place_dcid,name,year,value)
  data/breakdown_countries.csv  latest value of each end of the breakdown, per country (dcid,name,group,year,value)
  data/breakdown_aggregates.csv published aggregates by group, where the source has them (place_dcid,name,group,year,value)
  data/membership.csv           countries and areas of the 8 SDG regions and of LDCs, LLDCs and SIDS
  retrieval.json                indicator, every call (tool, exact args, raw response id) and the file it fed
  meta.json                     topic description, target and experiment fields

Every value is written exactly as returned (Python repr of the parsed JSON number). Nothing is computed here.
"""
import argparse
import csv
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import spotlight002 as S  # noqa: E402

PLAN = json.loads((HERE / "data" / "calls_plan.json").read_text(encoding="utf-8"))
INDEX = json.loads((HERE / "data" / "calls_index.json").read_text(encoding="utf-8"))
U5 = "undata/sdg/SH_DYN_MORT.AGE--Y0T4"


def key(tool, args):
    return tool.split("__")[-1], json.dumps(args, sort_keys=True)


BY = {}
for r in INDEX:  # the latest successful result for each exact call
    if not r["is_error"]:
        BY[key(r["tool"], r["args"])] = r


def call(tool, args):
    r = BY.get(key(tool, args))
    if not r:
        return None, None
    rec = json.loads((HERE / "data" / "raw" / f"{r['id']}.json").read_text(encoding="utf-8"))
    return json.loads(rec["response"]), r


def rows_of(resp):
    """(dcid, name, types, year, value) for every data row, in the order returned."""
    if not resp:
        return []
    ent = {e[0]: (e[1], e[2]) for e in (resp.get("entityMetadata") or {}).get("rows") or []}
    out = []
    for place, date, value in (resp.get("data") or {}).get("rows") or []:
        name, types = ent.get(place, (place, []))
        out.append((place, name, types, date, value))
    return out


def write(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def v(x):
    return repr(x) if isinstance(x, float) else str(x)


def membership(log):
    """Countries and areas of each SDG region and grouping (from the under-five mortality calls)."""
    mem = []
    seen = set()
    for dcid, name in S.DIRECT_MEMBERSHIP.items():
        args = {"variable_dcid": U5, "parent_place_dcid": dcid, "child_place_type": "Country", "date": "latest"}
        resp, r = call("get_child_observations", args)
        log.append(("get_child_observations", args, r, "data/membership.csv"))
        for c, cname, types, _, _ in rows_of(resp):
            if c in S.NOT_IN_REGION.get(dcid, ()):
                continue
            mem.append((dcid, name, c, cname))
            if dcid in S.SDG_REGIONS:
                seen.add(c)
    for dcid, (name, parts) in S.COMPOSED_REGIONS.items():
        for part in parts:
            args = {"variable_dcid": U5, "parent_place_dcid": part, "child_place_type": "Country", "date": "latest"}
            resp, r = call("get_child_observations", args)
            log.append(("get_child_observations", args, r, "data/membership.csv"))
            for c, cname, types, _, _ in rows_of(resp):
                if c in seen or c in S.NOT_IN_REGION.get(dcid, ()):
                    continue
                seen.add(c)
                mem.append((dcid, name, c, cname))
    return mem


def build(pid, out, spotlight=None, slug=None):
    prop = next(p for p in S.proposals() if p["proposal"] == pid)
    fam = next(f for f in PLAN["families"] if pid in f["proposals"])
    calls = {c["role"]: c for c in fam["calls"]}
    log = []

    def get(role):
        c = calls.get(role)
        if not c:
            return []
        resp, r = call(c["tool"], c["args"])
        return resp, r, c

    def fetch(role, saved_as):
        c = calls.get(role)
        if not c:
            return [], None
        resp, r = call(c["tool"], c["args"])
        log.append((c["tool"], c["args"], r, saved_as))
        return rows_of(resp), resp

    data = out / "data"
    world, wresp = fetch("world", "data/world.csv")
    write(data / "world.csv", ["dcid", "name", "year", "value"], [(d, n, y, v(x)) for d, n, _, y, x in world])
    ctry, cresp = fetch("countries", "data/countries_latest.csv")
    write(data / "countries_latest.csv", ["dcid", "name", "year", "value"], [(d, n, y, v(x)) for d, n, _, y, x in ctry])

    places = S.places_of(prop)
    agg_rows = []
    for typ in ("UNGeoRegion", "GeoRegion"):
        rows, _ = fetch(f"aggregates_{typ}", "data/place_series.csv") if f"aggregates_{typ}" in calls else ([], None)
        agg_rows += [(d, n, y, v(x)) for d, n, _, y, x in rows if d in places]
    write(data / "place_series.csv", ["place_dcid", "name", "year", "value"], agg_rows)

    b = prop["breakdown"]
    bd_c, bd_a = [], []
    if b in S.GROUPS:
        pair = fam["breakdowns"][b]
        ends = ("low", "high") if b == "wealth" else ("a", "b")
        for end, group in zip(ends, S.GROUPS[b]):
            rows, _ = fetch(f"{b}_{end}_countries", "data/breakdown_countries.csv")
            bd_c += [(d, n, group, y, v(x)) for d, n, _, y, x in rows]
            rows, _ = fetch(f"{b}_{end}_world", "data/breakdown_aggregates.csv")
            bd_a += [(d, n, group, y, v(x)) for d, n, _, y, x in rows]
            for typ in ("UNGeoRegion", "GeoRegion"):
                if f"{b}_{end}_aggregates_{typ}" in calls:
                    rows, _ = fetch(f"{b}_{end}_aggregates_{typ}", "data/breakdown_aggregates.csv")
                    bd_a += [(d, n, group, y, v(x)) for d, n, _, y, x in rows if d in places]
        write(data / "breakdown_countries.csv", ["dcid", "name", "group", "year", "value"], bd_c)
        write(data / "breakdown_aggregates.csv", ["place_dcid", "name", "group", "year", "value"], bd_a)
    write(data / "membership.csv", ["place_dcid", "place_name", "dcid", "name"], membership(log))

    src = cresp.get("sourceMetadata", {}) if cresp else {}
    fam_meta = S.FAMILY[fam["theme"]]
    retrieval = {
        "topic": pid,
        "retrieved_on": min((r["result_at"] or "")[:10] for _, _, r, _ in log if r),
        "indicator": {
            "sdg_indicator": fam["sdg"], "sdg_series_codes": fam["series_codes"],
            "data_commons_variable_dcid": fam["base"], "variable_name": (cresp or {}).get("variable", {}).get("name"),
            "data_commons_facet_id": src.get("sourceId"), "provenance_url": src.get("provenanceUrl"),
            "unit": src.get("unit"), "breakdown_variables": fam["breakdowns"].get(b) if b in S.GROUPS else None,
        },
        "custodian": fam_meta["custodian"],
        "method_note": ("Every value is copied unchanged from the UN System Data Commons responses saved under "
                        "experiments/002-design-framing-time/data/raw/ (one file per call, named by raw_id). "
                        "No aggregate is computed from country values. Membership of SDG regions comes from the "
                        "Data Commons' own containment (under-five mortality calls); see "
                        "scripts/spotlight002.py for regions composed of their subregions."),
        "data_commons_calls": [{"tool": t.split("__")[-1], "args": a, "raw_id": r["id"] if r else None,
                                "result_at": r["result_at"] if r else None, "saved_as": s}
                               for t, a, r, s in log],
    }
    (out / "retrieval.json").write_text(json.dumps(retrieval, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tgt = S.target(fam["theme"])
    meta = {
        "spotlight": spotlight, "slug": slug, "title": S.title(prop), "sdg_indicator": fam["sdg"],
        "retrieved_on": retrieval["retrieved_on"],
        "target_value": tgt["value"], "target_year": tgt["year"], "target_basis": tgt["basis"],
        "experiment": {"id": "002", "proposal": pid, "family": fam["theme"], "pace": int(prop["pace"]),
                       "kind": prop["kind"], "place_type": prop["place_type"], "place": prop["place"],
                       "place_dcids": places, "breakdown": prop["breakdown"], "frames_proposed": prop["frames"],
                       "feed_tag": prop["feed_tag"], "versions": []},
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    missing = [(t, a) for t, a, r, _ in log if not r]
    return missing


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("proposal")
    ap.add_argument("out", type=pathlib.Path)
    ap.add_argument("--spotlight", type=int)
    ap.add_argument("--slug")
    a = ap.parse_args()
    miss = build(a.proposal, a.out, a.spotlight, a.slug)
    if miss:
        print("MISSING CALLS:", miss)
        sys.exit(1)
