#!/usr/bin/env python3
"""Fetch one indicator record from UNICEF's Reference Data Manager (RDM) and store it beside a Spotlight.

Usage:
    python scripts/fetch_rdm_metadata.py <helix_code> <folder>
    python scripts/fetch_rdm_metadata.py CME_MRY0T4 spotlights/02-under-five-mortality

Writes <folder>/metadata.rdm.json:
    source, url, retrieved_at (UTC), sha256_raw (of the body as served), record (the JSON record with the
    editor fields removed at every level: editedBy, createdBy, changePublishStatusBy carry staff email
    addresses and must never reach the public repo).

The record is UNICEF's registry entry for the indicator: name, definition, numerator and denominator,
the SDG metadata text blocks (method, limitations, data sources, ...), classifications (SDG code, custodian
flags) and related indicators. Template E banners take their subtitle from DEFINITION and their
statistician's note from SDG_METHOD and SDG_LIMIT. The values on a banner never come from here.

The RDM host is not reachable from the cloud sessions that draft Spotlights, so the drafting session saves
a draft copy with its web fetch tool and the rdm-metadata workflow re-fetches by script and compares
(scripts/check_rdm_metadata.py). Standard library only, so CI needs no install step.
Service documentation: https://rdmapi.unicef.org/api/doc/index.html (checked 3 November 2026).
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import pathlib
import sys
import urllib.error
import urllib.request

BASE = "https://rdmapi.unicef.org"
DROP = {"editedBy", "createdBy", "changePublishStatusBy"}
SOURCE = "UNICEF Reference Data Manager API"


EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def strip(obj):
    """The record without the editor fields, at every level, and without any e-mail address written inside a
    text attribute (some definitions name a contact; MNCH_SAB did, 3 Nov 2026): "[address removed]" stands in."""
    if isinstance(obj, dict):
        return {k: strip(v) for k, v in obj.items() if k not in DROP}
    if isinstance(obj, list):
        return [strip(x) for x in obj]
    if isinstance(obj, str):
        return EMAIL.sub("[address removed]", obj)
    return obj


def fetch_raw(url, timeout=60):
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": "un-data-commons-spotlight (rdm metadata)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def english(record):
    """English attributes of a record, by attribute code."""
    return {a["attributeCode"]: a.get("value") for a in record.get("attributes", [])
            if a.get("languageISO") == "eng"}


def classifications(record):
    return {c["name"]: c.get("value") for c in record.get("classifications", [])}


def snapshot(helix_code):
    url = f"{BASE}/api/indicators/{helix_code}"
    body = fetch_raw(url)
    record = strip(json.loads(body))
    return {
        "source": SOURCE,
        "url": url,
        "retrieved_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sha256_raw": hashlib.sha256(body).hexdigest(),
        "record": record,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("helix_code", help="RDM helix code, e.g. CME_MRY0T4")
    ap.add_argument("folder", type=pathlib.Path, help="folder that receives metadata.rdm.json")
    a = ap.parse_args()
    try:
        out = snapshot(a.helix_code)
    except urllib.error.HTTPError as e:
        sys.exit(f"{a.helix_code}: HTTP {e.code} from {BASE}")
    except (urllib.error.URLError, TimeoutError) as e:
        sys.exit(f"{a.helix_code}: cannot reach {BASE}: {e}")
    a.folder.mkdir(parents=True, exist_ok=True)
    path = a.folder / "metadata.rdm.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    eng = english(out["record"])
    print(path)
    print("NAME:", eng.get("NAME"))
    print("DEFINITION:", eng.get("DEFINITION"))
    print("SDG Indicator:", classifications(out["record"]).get("SDG Indicator"))


if __name__ == "__main__":
    main()
