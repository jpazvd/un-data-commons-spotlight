#!/usr/bin/env python3
"""Check a stored RDM metadata snapshot against the live Reference Data Manager, by script.

Usage:
    python scripts/check_rdm_metadata.py <folder>              # <folder>/metadata.rdm.json
    python scripts/check_rdm_metadata.py <folder> --offline    # structure and privacy checks only

Checks:
  - the file has source, url, retrieved_at, sha256_raw and record;
  - no editor field or @unicef.org address survives anywhere in the file (privacy), scanning the decoded JSON
    so an escaped address (\u0040) cannot hide;
  - unless --offline: the stored url is the registry's own address for the record's helixCode (nothing else is
    fetched), and the record re-fetched from it, with the same fields stripped, equals the stored record;
    otherwise the changed keys are printed and the exit code is 1. A difference means the
    registry changed since the draft: re-run fetch_rdm_metadata.py, redraft the subtitle if DEFINITION moved,
    and log it under Deviations when the Spotlight is in an experiment.
Exit code 1 on any failure.
"""
import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fetch_rdm_metadata import BASE, DROP, fetch_raw, strip  # noqa: E402

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@unicef\.org", re.I)


def walk(obj, path="record"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")
    else:
        yield path, obj


def diff(a, b):
    """Paths whose leaf values differ between two records."""
    fa, fb = dict(walk(a)), dict(walk(b))
    return sorted(p for p in set(fa) | set(fb) if fa.get(p, "<missing>") != fb.get(p, "<missing>"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("folder", type=pathlib.Path)
    ap.add_argument("--offline", action="store_true", help="skip the live comparison")
    a = ap.parse_args()
    path = a.folder / "metadata.rdm.json"
    if not path.is_file():
        sys.exit(f"{path}: missing")
    text = path.read_text(encoding="utf-8")
    snap = json.loads(text)
    problems = []
    for key in ("source", "url", "retrieved_at", "sha256_raw", "record"):
        if key not in snap:
            problems.append(f"missing key {key!r}")
    if EMAIL.search(json.dumps(snap, ensure_ascii=False)):  # decoded: catches \u0040 and other JSON escapes
        problems.append("an @unicef.org address is stored in the file")
    for p, _ in walk(snap.get("record", {})):
        if any(f".{d}" in p for d in DROP):
            problems.append(f"editor field stored at {p}")
            break
    if problems:
        print(f"{path}: FAIL"); [print("  -", p) for p in problems]; sys.exit(1)
    if a.offline:
        print(f"{path}: structure and privacy OK (offline)"); return
    url = f"{BASE}/api/indicators/{snap['record'].get('helixCode')}"  # the registry's own address, never the file's
    if snap["url"] != url:
        print(f"{path}: FAIL, url is {snap['url']!r}, the registry record for this helixCode is {url}"); sys.exit(1)
    live = strip(json.loads(fetch_raw(url)))
    if snap["record"] != live:
        changed = diff(snap["record"], live)  # leaf paths for the report; the gate is equality of the whole record
        print(f"{path}: FAIL, the registry record differs from the stored copy at {len(changed)} path(s):")
        for p in changed[:40]:
            print("  -", p)
        if not changed:
            print("  - (a structural difference: an empty list or object, or a type, with no leaf value changed)")
        sys.exit(1)
    print(f"{path}: OK, matches {snap['url']} (stored {snap['retrieved_at']})")


if __name__ == "__main__":
    main()
