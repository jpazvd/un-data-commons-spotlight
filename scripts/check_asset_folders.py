#!/usr/bin/env python3
"""Check the folders under assets/ against R45 (docs/banner-guidance/BANNER_GUIDANCE.md).

  - every folder is named <NNN>-<slug> (three digits from 001, lower-case slug), or _<NNN>-<slug> once retired;
  - the numbers are unique and run from 001 with no gap, retired folders included, so a number is never
    reused and a folder is retired rather than deleted;
  - with --base, every numbered folder on the base branch is still here, under the same name or retired with a
    leading underscore, so the last folder cannot be deleted (no gap shows) and no number or slug changes;
  - assets/README.md has one table row per folder, linked as [`<name>`](<name>/), whose first cell is the
    folder's number, no row for a folder that does not exist, and no numbered row in any other form.

Usage:  python scripts/check_asset_folders.py [--base origin/main]   exits 1 and lists what breaks the rule
        (exits 0 where there is no assets/ folder, as in the public repository)
"""
import argparse
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
INDEX = ASSETS / "README.md"
NAME = re.compile(r"^_?(?!000)(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*$")
ROW = re.compile(r"^\|\s*(\S+)\s*\|\s*\[`([^`]+)`\]\(([^)]+)\)")
NUMBERED_ROW = re.compile(r"^\|\s*_?\d+\s*\|")


def base_folders(ref: str) -> list[str]:
    """Names of the folders under assets/ on another commit, read from git."""
    out = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "-d", "--name-only", ref, "assets/"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or f"git ls-tree {ref} failed")
    return [line.split("/", 1)[1] for line in out.stdout.splitlines() if "/" in line]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", help="git ref of the branch this one merges into, e.g. origin/main")
    args = parser.parse_args()
    if not ASSETS.is_dir():  # scripts/*.py is published; the public repository carries no assets/
        print("SKIP: no assets/ folder here")
        return 0
    problems = []
    folders = sorted(p.name for p in ASSETS.iterdir() if p.is_dir())
    numbers = {}
    for name in folders:
        m = NAME.match(name)
        if not m:
            problems.append(f"{name}: not named <NNN>-<slug> (three digits from 001, lower-case slug)")
            continue
        numbers.setdefault(int(m.group(1)), []).append(name)
    for n, names in sorted(numbers.items()):
        if len(names) > 1:
            problems.append(f"number {n:03d} used by more than one folder: {', '.join(names)}")
    missing = sorted(set(range(1, max(numbers, default=0) + 1)) - set(numbers))
    if missing:
        problems.append("numbers missing (retire a folder with a leading underscore, never delete it): "
                        + ", ".join(f"{n:03d}" for n in missing))
    if args.base:
        try:
            before = base_folders(args.base)
        except RuntimeError as e:
            problems.append(f"cannot read assets/ on {args.base}: {e}")
            before = []
        for name in before:
            if not NAME.match(name):  # folders named before R45 are renamed once, into the scheme
                continue
            if name.startswith("_"):
                if name not in folders:
                    problems.append(f"{name}: retired on {args.base} but not here; a retired folder stays as it is")
            elif name not in folders and "_" + name not in folders:
                problems.append(f"{name}: on {args.base} but not here; keep it, renamed _{name} if the campaign "
                                "is dropped (a number and slug are never deleted or changed)")

    if not INDEX.exists():
        problems.append("assets/README.md is missing: it lists every folder with its post dates")
        rows = {}
    else:
        rows = {}
        for line in INDEX.read_text(encoding="utf-8").splitlines():
            m = ROW.match(line)
            if not m:
                if NUMBERED_ROW.match(line):
                    problems.append("assets/README.md: row not in the form | NNN | [`<name>`](<name>/) |: "
                                    + line[:70])
                continue
            number, name, link = m.groups()
            if name in rows:
                problems.append(f"assets/README.md: {name} has more than one row")
            rows[name] = number
            if link.rstrip("/") != name:
                problems.append(f"assets/README.md: the row for {name} links to {link}")
            fm = NAME.match(name)
            if fm and number.lstrip("_") != fm.group(1):
                problems.append(f"assets/README.md: the row for {name} is numbered {number}")
    for name in folders:
        if name not in rows:
            problems.append(f"assets/README.md: no row for {name}")
    for name in rows:
        if name not in folders:
            problems.append(f"assets/README.md: a row for {name}, which is not a folder in assets/")

    if problems:
        print("FAIL: assets/ does not follow R45")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"OK: {len(folders)} asset folders, numbered 001 to {max(numbers, default=0):03d}, all in assets/README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
