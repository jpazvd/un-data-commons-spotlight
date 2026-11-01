# UN Data Commons Spotlight

A recurring series of banners, each highlighting one statistic on children and women from the
[UN System Data Commons](https://unstats.un.org/sdgs/dataportal). Every number on a banner is
derived from the data committed in this repository, by the scripts committed here.

<!-- spotlights:start -->
| # | Topic | SDG indicator | Data retrieved |
|---|-------|---------------|----------------|
| 01 | [Child marriage](spotlights/01-child-marriage) | 5.3.1 | 2026-10-23 |
| 02 | [Under-five mortality](spotlights/02-under-five-mortality) | 3.2.1 | 2026-10-31 |
<!-- spotlights:end -->

The table is rebuilt from each Spotlight's `meta.json` when content is published (`scripts/build_readme_table.py`).

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
  render_banner.py            banner.dc.html (or any .dc.html design) -> PNG/JPEG
  fetch_sdg_api.py            Re-pull a series from the UN SDG API and compare with the snapshot
  check_sdg_api.py            Same comparison, by script, for CI; writes the survey sources of the named countries
```

## Banner templates

| Dark | Light |
| --- | --- |
| ![Template D, dark](templates/banner-D-dark.jpg) | ![Template D, light](templates/banner-D-light.jpg) |

Earlier designs and why they were retired: [docs/design-history](docs/design-history/README.md).

## Experiments

Banner style: from Spotlight 02 the banner template is not chosen by hand. It is read from
[`experiments/001-banner-ground/assignment.csv`](experiments/001-banner-ground/assignment.csv), a seeded random
assignment registered before the experiment started. See
[`PREREGISTRATION.md`](experiments/001-banner-ground/PREREGISTRATION.md) for the question, design, outcomes,
power and decision rule, and `analyze.py` for the pre-specified analysis.

## Reproduce a banner

```bash
pip install -r requirements.txt
python -m playwright install chromium
npm install                      # banner fonts (@fontsource packages) into node_modules/

python scripts/compute_stats.py spotlights/01-child-marriage   # re-derives every figure
python scripts/render_banner.py spotlights/01-child-marriage   # re-renders the banner
python scripts/render_banner.py templates/banner-D-dark.dc.html  # any design file: writes banner-D-dark.png/.jpg beside it
```

The renderer loads the families and weights named in the design's `<helmet>` font link from `node_modules/`, and
stops if one is missing, so a render never silently falls back to a system font.

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

## Licence and citation

Code: MIT. Banners, captions and text: CC BY 4.0. Data: the custodian sources' terms (see each Spotlight's
`meta.json`). How to cite: [`CITATION.cff`](CITATION.cff). Each published Spotlight has a tag, `spotlight-NN`.
