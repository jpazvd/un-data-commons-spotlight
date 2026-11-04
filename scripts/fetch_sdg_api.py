"""Re-pull a Spotlight's series from the UN SDG Global Database API and compare it with the snapshot.

The committed CSVs in <spotlight>/data/ are the data each banner was built from and are never
overwritten. This script writes a dated refresh next to them so changes in the source over time
can be audited:

    <spotlight>/data/api_refresh/<YYYY-MM-DD>/response.json   raw API response(s), unchanged
    <spotlight>/data/api_refresh/<YYYY-MM-DD>/series.csv      all filtered records (every area, every year)
    <spotlight>/data/api_refresh/<YYYY-MM-DD>/areas_latest.csv latest year per area

Usage:
    python scripts/fetch_sdg_api.py spotlights/01-child-marriage
    python scripts/fetch_sdg_api.py spotlights/01-child-marriage --input saved_response.json

The series code and dimension filters come from <spotlight>/retrieval.json
("indicator.sdg_series_code" and "indicator.dimensions"). Areas are identified by UN M49 codes
(geoAreaCode; World = 1) and include regional aggregates as well as countries.
"""
import argparse
import csv
import datetime as dt
import json
import pathlib
import sys
import urllib.parse
import urllib.request

API = "https://unstats.un.org/SDGAPI/v1/sdg/Series/Data"
PAGE_SIZE = 10000


def fetch(series_code):
    pages, page = [], 1
    while True:
        q = urllib.parse.urlencode({"seriesCode": series_code, "pageSize": PAGE_SIZE, "page": page})
        with urllib.request.urlopen(f"{API}?{q}", timeout=120) as r:
            body = json.load(r)
        pages.append(body)
        if page >= int(body.get("totalPages") or 1):
            return pages
        page += 1


def matches(rec, dims):
    d = rec.get("dimensions") or {}
    return all(str(d.get(k)) == str(v) for k, v in dims.items())


def filter_rows(pages, series, dims):
    """The records of `series` with the Spotlight's dimensions (shared with check_sdg_api.py)."""
    rows = []
    for p in pages:
        for rec in p.get("data", []):
            if rec.get("series") == series and matches(rec, dims) and rec.get("value") not in (None, ""):
                rows.append({
                    "m49": rec["geoAreaCode"], "name": rec["geoAreaName"],
                    "year": int(float(rec["timePeriodStart"])), "value": float(rec["value"]),
                    "reporting_type": (rec.get("dimensions") or {}).get("Reporting Type", ""),
                    "source": rec.get("source") or "",
                })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spotlight_dir", type=pathlib.Path)
    ap.add_argument("--input", type=pathlib.Path, help="parse a saved API response instead of fetching")
    a = ap.parse_args()

    spec = json.loads((a.spotlight_dir / "retrieval.json").read_text(encoding="utf-8"))["indicator"]
    series, dims = spec["sdg_series_code"], spec["dimensions"]

    if a.input:
        raw = json.loads(a.input.read_text(encoding="utf-8"))
        pages = raw if isinstance(raw, list) else [raw]
    else:
        pages = fetch(series)

    rows = filter_rows(pages, series, dims)
    if not rows:
        sys.exit(f"No records for {series} with {dims}.")

    out = a.spotlight_dir / "data" / "api_refresh" / dt.date.today().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    (out / "response.json").write_text(json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")
    fields = ["m49", "name", "year", "value", "reporting_type", "source"]
    rows.sort(key=lambda r: (int(r["m49"]), r["year"]))
    with open(out / "series.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    latest = {}
    for r in rows:
        if r["m49"] not in latest or r["year"] >= latest[r["m49"]]["year"]:
            latest[r["m49"]] = r
    with open(out / "areas_latest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(latest.values())

    # Compare the World series with the snapshot the banner used.
    snap_path = a.spotlight_dir / "data" / "world.csv"
    snap = {}
    if snap_path.exists():
        with open(snap_path, newline="", encoding="utf-8") as f:
            snap = {int(r["year"]): float(r["value"]) for r in csv.DictReader(f)}
    api_world = {r["year"]: r["value"] for r in rows if str(r["m49"]) == "1"}
    print(f"{series} {dims}: {len(rows)} records, {len(latest)} areas -> {out}")
    print("World series, snapshot vs API:")
    changed = False
    for y in sorted(set(snap) | set(api_world)):
        s, v = snap.get(y), api_world.get(y)
        flag = "" if s is not None and v is not None and abs(s - v) < 1e-9 else "  <-- differs"
        changed |= bool(flag)
        print(f"  {y}: snapshot={s}  api={v}{flag}")
    print("World series unchanged." if not changed else "World series has changed since the snapshot.")


if __name__ == "__main__":
    main()
