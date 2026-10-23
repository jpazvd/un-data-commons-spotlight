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
  meta.json                   SDG series code, dimensions, variable DCID, source/provenance, retrieval date
  retrieval.json              Exact calls and parameters used to pull the data, plus the
                              equivalent UN SDG API query
  data/api_refresh/<date>/    Optional later re-pulls from the SDG API (never replace the snapshot)
  stats.json                  Every derived number on the banner (written by compute_stats.py)
  banner.dc.html              Banner source (design file)
  banner.png / banner.jpg     Rendered banner (2400x1260 / 1200x630)
  captions.md                 LinkedIn and X post text
scripts/
  compute_stats.py            Data -> stats.json
  render_banner.py            banner.dc.html -> PNG/JPEG
  fetch_sdg_api.py            Re-pull a series from the UN SDG API and compare with the snapshot
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

## Data snapshots and refreshes

Source databases are revised over time, so each spotlight keeps the exact data its banner was
built from (`data/*.csv`), together with the indicator code and the calls used to pull it
(`retrieval.json`). These files are never edited after publication.

To check whether the source has changed since a banner was made:

```bash
python scripts/fetch_sdg_api.py spotlights/01-child-marriage
```

This queries the UN SDG Global Database API, for example
`https://unstats.un.org/SDGAPI/v1/sdg/Series/Data?seriesCode=SP_DYN_MRBF18&pageSize=10000`,
filters to the spotlight's dimensions (here Age 20-24, Sex FEMALE), saves the raw response and
tidy CSVs under `data/api_refresh/<today>/`, and prints the World series next to the snapshot.
The API identifies areas by UN M49 code (World = 1) and includes regional aggregates.

## Data and attribution

Data are retrieved from the UN System Data Commons; `meta.json` in each spotlight records the
SDG series code and dimensions, the Data Commons variable (DCID), the provenance and custodian
source, and the retrieval date.
Country values are each country's latest available year, so they are not directly comparable
across countries. Please cite the original custodian source shown on each banner.
