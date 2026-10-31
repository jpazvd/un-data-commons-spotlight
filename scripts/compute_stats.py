"""Derive every number shown on a Spotlight banner from its committed data.

Usage:
    python scripts/compute_stats.py spotlights/01-child-marriage
    python scripts/compute_stats.py spotlights/NN-slug --target-value 25 --better lower --country-threshold 25

Reads <spotlight>/data/world.csv and <spotlight>/data/countries_latest.csv
(columns: dcid,name,year,value) and writes <spotlight>/stats.json.

The pace calculation compares the average annual change over the observed
world series with the annual change needed to reach the target value by the
target year (default: 0 by 2030, as for SDG 5.3.1 "eliminate").

`better` says which direction is progress (default: inferred, lower if the target
is below the first world value). `trend` says whether the world series moves
towards an unmet target; the acceleration multiple (`required_over_observed`) is
given only then, and is null when the trend is flat, away from the target, or the
target is already met. With --country-threshold (a per-country target such as
SDG 3.2.1's 25 per 1,000), `country_threshold` counts the countries whose latest
estimate does not meet it.
"""
import argparse
import csv
import json
import pathlib
import sys


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
    ap.add_argument("--better", choices=["lower", "higher"],
                    help="direction of progress (default: inferred from the target)")
    ap.add_argument("--country-threshold", type=float,
                    help="per-country target: count countries whose latest value does not meet it")
    ap.add_argument("--stale-cutoff", type=int, default=2020,
                    help="latest estimates in or before this year count as stale")
    ap.add_argument("--top", type=int, default=6)
    a = ap.parse_args()

    world = sorted(read_csv(a.spotlight_dir / "data" / "world.csv"), key=lambda r: r["year"])
    countries = read_csv(a.spotlight_dir / "data" / "countries_latest.csv")

    first, last = world[0], world[-1]
    span = last["year"] - first["year"]
    years_left = a.target_year - last["year"]
    if span <= 0 or years_left <= 0:
        sys.exit("need at least two world years, and a target year after the last one")
    observed_pace = (first["value"] - last["value"]) / span          # points per year (decline > 0)
    required_pace = (last["value"] - a.target_value) / years_left
    at_current_pace = last["value"] - observed_pace * years_left
    better = a.better or ("lower" if a.target_value < first["value"] else "higher")
    sign = 1 if better == "lower" else -1
    progress, remaining = sign * observed_pace, sign * (last["value"] - a.target_value)
    trend = ("target met" if remaining <= 0 else "towards target" if progress > 0
             else "flat" if progress == 0 else "away from target")

    top = sorted(countries, key=lambda r: r["value"], reverse=True)[: a.top]
    n = len(countries)
    n_stale = sum(r["year"] <= a.stale_cutoff for r in countries)
    oldest = min(countries, key=lambda r: r["year"])

    stats = {
        "world_first": {"year": first["year"], "value": round(first["value"], 1)},
        "world_last": {"year": last["year"], "value": round(last["value"], 1)},
        "better": better,
        "trend": trend,
        "observed_pace_pts_per_year": round(observed_pace, 2),
        "required_pace_pts_per_year": round(required_pace, 2),
        "required_over_observed": round(required_pace / observed_pace, 1) if trend == "towards target" else None,
        "value_at_current_pace_in_target_year": round(at_current_pace, 1),
        "target": {"value": a.target_value, "year": a.target_year},
        "top_countries": [{"name": r["name"], "year": r["year"], "value": r["value"]} for r in top],
        "n_countries": n,
        "n_latest_at_or_before_cutoff": n_stale,
        "share_latest_at_or_before_cutoff_pct": round(100 * n_stale / n),
        "stale_cutoff_year": a.stale_cutoff,
        "oldest_latest_estimate": {"name": oldest["name"], "year": oldest["year"]},
    }
    if a.country_threshold is not None:
        t = a.country_threshold
        missing = [r for r in countries if (r["value"] > t if better == "lower" else r["value"] < t)]
        stats["country_threshold"] = {"value": t, "n_not_meeting": len(missing), "n": n}
    out = a.spotlight_dir / "stats.json"
    out.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
