# UN Data Commons Spotlight

A recurring series of banners, each highlighting one statistic on children and women from the
[UN System Data Commons](https://unstats.un.org/sdgs/dataportal). Every number on a banner is
derived from the data committed in this repository, by the scripts committed here.

| # | Topic | SDG indicator | Date |
|---|-------|---------------|------|
| 01 | [Child marriage](spotlights/01-child-marriage) | 5.3.1 | 2026-10-23 |

## Layout

```
spotlights/<NN-slug>/
  data/world.csv              World series as retrieved (dcid, name, year, value)
  data/countries_latest.csv   Latest value per country as retrieved
  meta.json                   Variable DCID, source/provenance, retrieval date
  stats.json                  Every derived number on the banner (written by compute_stats.py)
  banner.dc.html              Banner source (design file)
  banner.png / banner.jpg     Rendered banner (2400x1260 / 1200x630)
  captions.md                 LinkedIn and X post text
scripts/
  compute_stats.py            Data -> stats.json
  render_banner.py            banner.dc.html -> PNG/JPEG
```

## Reproduce a banner

```bash
pip install -r requirements.txt
python -m playwright install chromium
npm install                      # banner fonts (Archivo, IBM Plex) into node_modules/

python scripts/compute_stats.py spotlights/01-child-marriage   # re-derives every figure
python scripts/render_banner.py spotlights/01-child-marriage   # re-renders the banner
```

`compute_stats.py` options: `--target-value` and `--target-year` (default 0 by 2030),
`--stale-cutoff` (default 2020; latest estimates in or before this year count as stale),
`--top` (number of countries ranked).

## Data and attribution

Data are retrieved from the UN System Data Commons; `meta.json` in each spotlight records the
exact statistical variable (DCID), the provenance and custodian source, and the retrieval date.
Country values are each country's latest available year, so they are not directly comparable
across countries. Please cite the original custodian source shown on each banner.
