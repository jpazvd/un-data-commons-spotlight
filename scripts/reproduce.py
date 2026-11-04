#!/usr/bin/env python3
"""Re-derive every number on every Spotlight banner from the data committed with it, and compare.

Usage (repo root):
    python scripts/reproduce.py                 # all Spotlights
    python scripts/reproduce.py spotlights/04-maternal-mortality spotlights/05-water-ldc-lldc-sids

For each Spotlight it copies the folder to a temporary directory, recomputes stats.json there and compares it
with the committed file, so nothing in the repository is changed:
- a single-banner Spotlight (01 to 04) with scripts/compute_stats.py, using the options recorded in its
  stats.json (target, target year, stale cutoff, number of countries ranked, direction, country threshold);
- each version of an experiment topic (versions/<F>/) with scripts/spotlight002.py.
It needs only the Spotlight folders and the scripts. Exit status 1 if any stats.json does not reproduce.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent


def single_args(stats):
    args = ["--target-value", str(stats["target"]["value"]), "--target-year", str(stats["target"]["year"]),
            "--stale-cutoff", str(stats["stale_cutoff_year"]), "--top", str(len(stats["top_countries"]))]
    if "better" in stats:
        args += ["--better", stats["better"]]
    if "country_threshold" in stats:
        args += ["--country-threshold", str(stats["country_threshold"]["value"])]
    return args


def check(spot):
    """Yield (label, ok, detail) for every stats.json of one Spotlight folder."""
    with tempfile.TemporaryDirectory() as tmp:
        t = pathlib.Path(tmp) / spot.name
        shutil.copytree(spot, t)
        if (spot / "stats.json").exists():
            stats = json.loads((spot / "stats.json").read_text(encoding="utf-8"))
            r = subprocess.run([sys.executable, str(ROOT / "scripts/compute_stats.py"), str(t), *single_args(stats)],
                               capture_output=True, text=True)
            ok = r.returncode == 0 and json.loads((t / "stats.json").read_text(encoding="utf-8")) == stats
            yield spot.name, ok, r.stderr.strip()[-200:]
        for v in sorted((spot / "versions").glob("*/stats.json")):
            frame = v.parent.name
            r = subprocess.run([sys.executable, str(ROOT / "scripts/spotlight002.py"), "stats", str(t), frame],
                               capture_output=True, text=True)
            new = t / "versions" / frame / "stats.json"
            ok = r.returncode == 0 and json.loads(new.read_text(encoding="utf-8")) == json.loads(v.read_text(encoding="utf-8"))
            yield f"{spot.name}/versions/{frame}", ok, r.stderr.strip()[-200:]


def main(argv):
    spots = [pathlib.Path(a) for a in argv] or sorted(p for p in (ROOT / "spotlights").glob("[0-9]*") if p.is_dir())
    n = bad = 0
    for spot in spots:
        for label, ok, detail in check(spot):
            n += 1
            if not ok:
                bad += 1
                print(f"DIFFERS  {label}  {detail}")
    print(f"{n - bad} of {n} stats.json files reproduce exactly from the committed data.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
