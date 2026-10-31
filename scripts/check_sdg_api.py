"""Compare a Spotlight's snapshot with the UN SDG Global Database API, by script.

Usage:
    python scripts/check_sdg_api.py spotlights/NN-slug --out <dir>
    python scripts/check_sdg_api.py spotlights/NN-slug --out <dir> --input saved_response.json

Re-pulls the series named in retrieval.json, with the same filters as fetch_sdg_api.py, and checks:
  - the World series (M49 1): every year in data/world.csv against the API;
  - every country in stats.json top_countries: identified by its UN M49 code (the ISO 3166-1 numeric
    code of its Data Commons dcid in data/countries_latest.csv; by exact name only for a place with no
    ISO code), its API record for the same year must have the same value. A value that matches another
    area is never accepted. Gives the survey source, and whether the API now has a later year for it.
Writes <out>/top_country_sources_sdgapi.csv (the format of data/top_country_sources_sdgapi.csv) and
<out>/summary.md, prints the summary, and exits 1 if anything differs or is missing.

The sdg-api workflow runs this on every pull request that touches a Spotlight, because the cloud
session that produces Spotlights cannot reach unstats.un.org and a page read through WebFetch is a
model's summary, not parsed JSON. A later API revision is a reason to explain, not to edit the snapshot.
Needs pycountry (pip install pycountry).
"""
import argparse
import csv
import json
import pathlib
import sys

import pycountry

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fetch_sdg_api import fetch, filter_rows  # noqa: E402

FIELDS = ["m49", "name", "year", "value", "source", "reporting_type"]  # as in Spotlight 01's file
TOL = 1e-9  # snapshot values are copied unchanged from the source, so any larger gap is a revision to report


def num(v):
    """A value written without loss: 61.0 as 61, otherwise the shortest repr (76.312345, not 76.3123)."""
    return str(int(v)) if v.is_integer() else repr(v)


def m49_of(dcid):
    """UN M49 code of a Data Commons country dcid (country/<ISO3>): for countries it is the ISO 3166-1 numeric code."""
    c = pycountry.countries.get(alpha_3=dcid[len("country/"):]) if dcid.startswith("country/") else None
    return int(c.numeric) if c else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spotlight_dir", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--input", type=pathlib.Path, help="parse a saved API response instead of fetching")
    a = ap.parse_args()
    spot = a.spotlight_dir
    spec = json.loads((spot / "retrieval.json").read_text(encoding="utf-8"))["indicator"]
    series, dims = spec["sdg_series_code"], spec["dimensions"]
    if a.input:
        raw = json.loads(a.input.read_text(encoding="utf-8"))
        pages = raw if isinstance(raw, list) else [raw]
    else:
        pages = fetch(series)
    rows = filter_rows(pages, series, dims)
    ok = True
    out = [f"### {spot.name}: SDG API `{series}` {json.dumps(dims)}", ""]

    with open(spot / "data" / "world.csv", newline="", encoding="utf-8") as f:
        snap = {int(r["year"]): float(r["value"]) for r in csv.DictReader(f)}
    api = {r["year"]: r["value"] for r in rows if str(r["m49"]) == "1"}
    diffs = [(y, v, api.get(y)) for y, v in sorted(snap.items()) if api.get(y) is None or abs(api[y] - v) > TOL]
    if diffs:
        ok = False
        out += [f"**World series: {len(diffs)} of {len(snap)} snapshot years differ.**", "",
                "| Year | Snapshot | API |", "| --- | --- | --- |"]
        out += [f"| {y} | {num(s)} | {'missing' if v is None else num(v)} |" for y, s, v in diffs]
    else:
        out.append(f"World series: all {len(snap)} snapshot years match the API.")
    later = sorted(y for y in api if snap and y > max(snap))
    if later:
        out.append(f"The API also has later World years: {', '.join(map(str, later))}.")

    stats = json.loads((spot / "stats.json").read_text(encoding="utf-8"))
    with open(spot / "data" / "countries_latest.csv", newline="", encoding="utf-8") as f:
        dcids = {r["name"]: r["dcid"] for r in csv.DictReader(f)}
    out += ["", "| Country (snapshot) | Year | Value | API match | Survey source | Later API year |",
            "| --- | --- | --- | --- | --- | --- |"]
    matched = []
    for c in stats["top_countries"]:
        code = m49_of(dcids.get(c["name"], ""))
        if code is not None:
            own = [r for r in rows if int(r["m49"]) == code]
        else:  # no ISO 3166 code (e.g. Kosovo): only an exact name identifies it
            own = [r for r in rows if r["name"].casefold() == c["name"].casefold()]
        same_year = [r for r in own if r["year"] == c["year"]]
        cands = [r for r in same_year if abs(r["value"] - c["value"]) <= TOL]
        if len(cands) != 1:
            ok = False
            area = f"M49 {code}" if code is not None else "this name"
            if not own:
                why = f"no API record for {area}"
            elif not same_year:
                why = f"{area} has no {c['year']} record; API years " + ", ".join(sorted({str(r["year"]) for r in own}))
            elif not cands:
                why = f"{area} has " + ", ".join(num(r["value"]) for r in same_year) + f" for {c['year']}"
            else:
                why = f"{len(cands)} API records for {area} in {c['year']}"
            out.append(f"| {c['name']} | {c['year']} | {num(c['value'])} | **not matched** ({why}) | | |")
            continue
        r = cands[0]
        matched.append(r)
        newer = max(x["year"] for x in own)
        out.append(f"| {c['name']} | {c['year']} | {num(c['value'])} | {r['name']} (M49 {r['m49']}) | "
                   f"{r['source'] or 'not given'} | {newer if newer > r['year'] else ''} |")

    a.out.mkdir(parents=True, exist_ok=True)
    with open(a.out / "top_country_sources_sdgapi.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows({**r, "value": num(r["value"])} for r in matched)
    out += ["", "Result: **matches**" if ok else "Result: **differs or not matched**: explain in the pull request."]
    text = "\n".join(out) + "\n"
    (a.out / "summary.md").write_text(text, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
