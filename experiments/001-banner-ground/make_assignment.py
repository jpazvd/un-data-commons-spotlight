"""Pre-registered random assignment for experiment 001 (banner ground: dark vs light).

Unit: one Spotlight (the same banner is posted on LinkedIn, X and Bluesky).
Design: 2x2 factorial in blocks of four consecutive Spotlights (02-05, 06-09, ...).
  Factor 1, link placement (fixed by design): odd number = repo link in the LinkedIn body,
  even number = repo link in the LinkedIn first comment.
  Factor 2, ground (randomised): within each block, one odd and one even Spotlight are
  drawn at random to get the dark banner; the other two get the light banner.
  So each block contains every combination exactly once.
Run:  python experiments/001-banner-ground/make_assignment.py   (writes assignment.csv)
"""
import csv, pathlib, random

SEED = 20261023          # fixed before any Spotlight in the experiment was produced
FIRST, BLOCKS = 2, 8     # Spotlights 02-33

rng = random.Random(SEED)
rows = []
for b in range(BLOCKS):
    nums = list(range(FIRST + 4 * b, FIRST + 4 * b + 4))
    odd = [n for n in nums if n % 2]; even = [n for n in nums if not n % 2]
    dark = {rng.choice(odd), rng.choice(even)}
    for n in nums:
        rows.append({"spotlight": f"{n:02d}", "block": b + 1,
                     "link_placement": "body" if n % 2 else "first_comment",
                     "ground": "dark" if n in dark else "light",
                     "template": f"templates/banner-D-{'dark' if n in dark else 'light'}.dc.html"})
out = pathlib.Path(__file__).with_name("assignment.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(f"wrote {out.name}: {len(rows)} Spotlights, {sum(r['ground']=='dark' for r in rows)} dark")
