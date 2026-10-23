"""Derive every number shown on a Spotlight banner from its committed data.

Usage:
    python scripts/compute_stats.py spotlights/01-child-marriage

Reads <spotlight>/data/world.csv and <spotlight>/data/countries_latest.csv
(columns: dcid,name,year,value) and writes <spotlight>/stats.json.

The pace calculation compares the average annual change over the observed
world series with the annual change needed to reach the target value by the
target year (default: 0 by 2030, as for SDG 5.3.1 "eliminate").
"""
import argparse
import csv
import json
import pathlib


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [
            {**r, "year": int(r["year"]), "value": float(r["value"])}
            for r in csv.DictReader(f)
        ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spotlight_dir", type=pathlib.Path)
    ap.add_argument("--target-value", type=float, default=0.0)
    ap.add_argument("--target-year", type=int, default=2030)
    ap.add_argument("--stale-cutoff", type=int, default=2020,
                    help="latest estimates in or before this year count as stale")
    ap.add_argument("--top", type=int, default=6)
    a = ap.parse_args()

    world = sorted(read_csv(a.spotlight_dir / "data" / "world.csv"), key=lambda r: r["year"])
    countries = read_csv(a.spotlight_dir / "data" / "countries_latest.csv")

    first, last = world[0], world[-1]
    span = last["year"] - first["year"]
    observed_pace = (first["value"] - last["value"]) / span          # points per year (decline > 0)
    years_left = a.target_year - last["year"]
    required_pace = (last["value"] - a.target_value) / years_left
    at_current_pace = last["value"] - observed_pace * years_left

    top = sorted(countries, key=lambda r: r["value"], reverse=True)[: a.top]
    n = len(countries)
    n_stale = sum(r["year"] <= a.stale_cutoff for r in countries)
    oldest = min(countries, key=lambda r: r["year"])

    stats = {
        "world_first": {"year": first["year"], "value": round(first["value"], 1)},
        "world_last": {"year": last["year"], "value": round(last["value"], 1)},
        "observed_pace_pts_per_year": round(observed_pace, 2),
        "required_pace_pts_per_year": round(required_pace, 2),
        "required_over_observed": round(required_pace / observed_pace, 1),
        "value_at_current_pace_in_target_year": round(at_current_pace, 1),
        "target": {"value": a.target_value, "year": a.target_year},
        "top_countries": [{"name": r["name"], "year": r["year"], "value": r["value"]} for r in top],
        "n_countries": n,
        "n_latest_at_or_before_cutoff": n_stale,
        "share_latest_at_or_before_cutoff_pct": round(100 * n_stale / n),
        "stale_cutoff_year": a.stale_cutoff,
        "oldest_latest_estimate": {"name": oldest["name"], "year": oldest["year"]},
    }
    out = a.spotlight_dir / "stats.json"
    out.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
