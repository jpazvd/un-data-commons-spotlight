#!/usr/bin/env python3
"""Build the dated reference extract of UNICEF's Reference Data Manager indicator registry.

Usage:
    python scripts/build_rdm_reference.py docs/rdm-2026-11            # published indicators (default)
    python scripts/build_rdm_reference.py docs/rdm-2026-11 --all      # every record, published or not

Writes <out_dir>/indicators.csv, one row per indicator: indicatorId, code, helixCode, name_en, isPublished,
ownerAgency, sdg_indicator, is_unicef_reporting_custodian, is_sdg_progress, is_sowc, custodian_name,
editedDate, retrieved_at; and <out_dir>/README.md with the counts and the calls made.

GET /api/indicators gives the short list; the SDG code, custodian flags and custodian name sit in each full
record, so one GET /api/indicators/{helixCode} per row (557 published records on 3 November 2026), with a
short pause between calls. Used for topic selection (which SDG code maps to which helix codes) and refreshed
monthly by the rdm-metadata workflow. Full records are stored only for the indicators a Spotlight uses
(scripts/fetch_rdm_metadata.py). Editor fields are never written.
"""
import argparse
import csv
import datetime as dt
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fetch_rdm_metadata import BASE, classifications, english, fetch_raw, strip  # noqa: E402

FIELDS = ["indicatorId", "code", "helixCode", "name_en", "isPublished", "ownerAgency", "sdg_indicator",
          "is_unicef_reporting_custodian", "is_sdg_progress", "is_sowc", "custodian_name", "editedDate",
          "retrieved_at"]


def row(short, full, retrieved_at):
    eng = english(full) if full else {}
    cl = classifications(full) if full else {}
    names = short.get("language2Name") or {}
    return {
        "indicatorId": short.get("indicatorId"),
        "code": short.get("code"),
        "helixCode": short.get("helixCode"),
        "name_en": eng.get("NAME") or names.get("English", ""),
        "isPublished": short.get("isPublished"),
        "ownerAgency": (short.get("ownerAgency") or {}).get("organization", ""),
        "sdg_indicator": cl.get("SDG Indicator", ""),
        "is_unicef_reporting_custodian": cl.get("Is UNICEF reporting custodian", ""),
        "is_sdg_progress": cl.get("Is SDG Progress indicator", ""),
        "is_sowc": cl.get("Is SOWC", ""),
        "custodian_name": ((full or {}).get("custodian") or {}).get("name", ""),
        "editedDate": short.get("editedDate", ""),
        "retrieved_at": retrieved_at,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("out_dir", type=pathlib.Path)
    ap.add_argument("--all", action="store_true", help="include unpublished records")
    ap.add_argument("--pause", type=float, default=0.2, help="seconds between record calls")
    a = ap.parse_args()
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    shorts = strip(json.loads(fetch_raw(f"{BASE}/api/indicators")))
    wanted = [s for s in shorts if a.all or s.get("isPublished")]
    rows, failed = [], []
    for s in wanted:
        code = s.get("helixCode") or s.get("code")
        try:
            full = strip(json.loads(fetch_raw(f"{BASE}/api/indicators/{code}")))
        except Exception as e:  # noqa: BLE001 - one bad record must not lose the extract
            failed.append(f"{code}: {e}")
            full = None
        rows.append(row(s, full, started))
        time.sleep(a.pause)
    rows.sort(key=lambda r: (r["sdg_indicator"] or "~", r["helixCode"] or ""))
    a.out_dir.mkdir(parents=True, exist_ok=True)
    with (a.out_dir / "indicators.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    with_sdg = sum(1 for r in rows if r["sdg_indicator"])
    (a.out_dir / "README.md").write_text(
        f"# RDM indicator reference, retrieved {started}\n\n"
        f"Built by `scripts/build_rdm_reference.py` from `{BASE}/api/indicators` ({len(shorts)} records, "
        f"{sum(1 for s in shorts if s.get('isPublished'))} published) and one `GET {BASE}/api/indicators/{{helixCode}}` "
        f"per row ({len(rows)} rows, {with_sdg} with an SDG indicator code"
        + (f", {len(failed)} records failed: see below" if failed else "") + ").\n\n"
        "Columns: indicatorId, code, helixCode, name_en, isPublished, ownerAgency, sdg_indicator, "
        "is_unicef_reporting_custodian, is_sdg_progress, is_sowc, custodian_name, editedDate, retrieved_at. "
        "Editor fields are never written. Refreshed monthly; a Spotlight records the helix code it uses in "
        "meta.json as rdm_helix_code and stores the full record as metadata.rdm.json.\n"
        + ("\nFailed records:\n\n" + "\n".join(f"- {x}" for x in failed) + "\n" if failed else ""),
        encoding="utf-8")
    print(f"{a.out_dir / 'indicators.csv'}: {len(rows)} rows, {with_sdg} with an SDG code, {len(failed)} failed")


if __name__ == "__main__":
    main()
