# Experiment 002: data checks of the 50 proposals

Run on 1 November 2026. Each proposal's data were retrieved from the UN System Data Commons with the calls in
`data/calls_plan.json`, made exactly as planned by sub-agents working through `data/batches/`. Every response was
saved verbatim from the session transcripts by `extract_calls.py` (`data/raw/<id>.json`, indexed in
`data/calls_index.json`). `build_topic_data.py` writes each topic's snapshot from those responses, and
`scripts/spotlight002.py check` says which framings the snapshot supports, under the rules in PREREGISTRATION.md.

Notes on method:

- Membership of SDG regions and groupings comes from the Data Commons' own containment, through under-five
  mortality calls. Four SDG regions return no countries directly, so they are composed of their M49 subregions
  (Northern Africa and Western Asia; Central and Southern Asia; Eastern and South-eastern Asia; Northern, Western,
  Southern and Eastern Europe with Northern America). The Data Commons lists the Turks and Caicos Islands under
  Northern Europe; it is left out of Europe and Northern America (in M49 it is in the Caribbean). This gives 194
  countries and areas in the eight SDG regions. The Data Commons' list of LDCs still includes Bhutan and Sao Tome and
  Principe, which have graduated (UNCTAD's UN list of least developed countries, 44 countries, read on 1 November
  2026); they are left out of LDC counts. The LDC aggregates are the custodians' own and are used as published.
- World counts of countries with data use the 194 countries and areas of the eight SDG regions, so that coverage and
  recency figures share one base.
- "Behind the average" with a breakdown uses published aggregates by group where the source has them. Otherwise it
  counts the countries of the place where the gap points one way, using only countries with both groups from the
  same year, and only with 10 such countries or more.
- Leading regions in comparisons are chosen among places with five countries or more (Australia and New Zealand
  has two). A long-view comparison uses the years all places share; if that span is under 10 years, the place whose
  series starts latest is left out (named in the Method line) until the span reaches 10 years.
- Numbers are stored at four decimals and rounded once, when the words and charts are written.
- An independent review of all 108 versions (1 November 2026) led to these fixes before the banners were final:
  single rounding, the LDC list, one base for World counts, the long-view span rule, wording by direction of progress,
  past tense for survey gaps, the source named for breakdown data, and no repeated headline between topics.
- World Bank aggregates for the eight conditional topics were checked with the World Bank Data360 tools; those
  calls are saved with the others.

## Results

| Proposal | Pace | Indicator | Place | Breakdown | Framings proposed | Supported | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P01 | 1 | Pre-primary participation | Fragile and conflict-affected situations against the World | wealth | T, L, G, D |  | fail: no World Bank indicator for SDG 4.2.2 with published aggregates (WB_HCP_ORG_LEARNING is attendance, with no World or FCS values) |
| P02 | 1 | Maternal mortality | Fragile and conflict-affected situations against the World | none | T, L, G |  | fail: the FCS aggregate exists only in the superseded HNP release (2000 to 2020), whose World values differ from the current series (2020: 223 in HNP, 211 in WDI) |
| P03 | 1 | Pre-primary participation | World Bank income groups compared | sex | T, L, G, D |  | fail: no World Bank indicator for SDG 4.2.2 with income-group aggregates |
| P04 | 1 | Child marriage before 18 | World Bank income groups compared | wealth | T, L, G, D |  | fail: no low- or high-income aggregates for SP.M18.2024.FE.ZS in WDI, HNP or Gender Statistics |
| P05 | 1 | Safely managed drinking water | LDCs, LLDCs and SIDS compared with the World | none | T, L, G, D | T, L, G, D | pass. Spotlight 5 |
| P06 | 1 | Safely managed sanitation | LDCs, LLDCs and SIDS compared with the World | none | T, L, G, D | T, L, G, D | pass. Spotlight 6 |
| P07 | 1 | Child marriage before 18 | LDCs, LLDCs and SIDS compared with the World | location | T, L, G, D | T, L, G, D | pass. Spotlight 7 |
| P08 | 1 | Child marriage before 15 | Landlocked developing countries (LLDCs) | location | T, L, G, D | T, L, G, D | pass. Spotlight 8 |
| P09 | 1 | Safely managed sanitation | Least developed countries (LDCs) | location | T, L, G, D | T, L, G, D | pass. Spotlight 9 |
| P10 | 1 | Safely managed drinking water | SDG regions compared | none | T, L, G, D | T, L, G, D | pass. Spotlight 10 |
| P11 | 1 | Pre-primary participation | SDG regions compared | sex | T, L, G, D | T, L, G, D | pass. Spotlight 11 |
| P12 | 1 | School completion | SDG regions compared | sex | T, L, G, D | T, L, G, D | pass. Spotlight 12 |
| P13 | 1 | Child marriage before 18 | SDG regions compared | location | T, L, G, D | T, L, G, D | pass. Spotlight 13 |
| P14 | 1 | Child marriage before 15 | World | none | T, L, D | T, L, D | pass. Spotlight 14 |
| P15 | 1 | School completion | World | wealth | T, L, G, D | T, L, G, D | pass. Spotlight 15 |
| P16 | 1 | Safely managed drinking water | World | none | T, L, D | T, L, D | pass. Spotlight 16 |
| P17 | 1 | Safely managed sanitation | World | none | T, L, D | T, L, D | pass. Spotlight 17 |
| P18 | 1 | Learning proficiency | World | sex | T, L, G, D | T, L, G, D | pass; dropped by JP on 1 November 2026: SDG 4.1.1 has no numeric target under the house rule, so no pace |
| P19 | 1 | Learning proficiency | Europe and Northern America | sex | T, L, G, D | T, L, G, D | pass; dropped by JP on 1 November 2026: SDG 4.1.1 has no numeric target under the house rule, so no pace |
| P20 | 1 | Safely managed sanitation | Northern Africa and Western Asia | location | T, L, G, D | T, L, G, D | pass. Spotlight 18 |
| P21 | 1 | School completion | Northern Africa and Western Asia | wealth | T, L, G, D | T, L, G, D | pass. Spotlight 19 |
| P22 | 1 | Safely managed drinking water | Northern Africa and Western Asia | location | T, L, G, D | T, L, D | pass (G: 8 countries with both groups in the same year (needs 10)). Spotlight 20 |
| P23 | 1 | School completion | Eastern and South-eastern Asia | wealth | T, L, G, D | T, L, G, D | pass. Spotlight 21 |
| P24 | 1 | Safely managed drinking water | Eastern and South-eastern Asia | location | T, L, G, D | T, L, G, D | pass. Spotlight 22 |
| P25 | 0 | Birth registration | Fragile and conflict-affected situations against the World | wealth | T, G, D |  | fail: the FCS aggregate exists only in the superseded HNP release (2010 and 2018), not in current WDI |
| P26 | 0 | Infant mortality | Fragile and conflict-affected situations against the World | none | T, L, G |  | fail: the FCS aggregate exists only in the superseded HNP release (to 2022); World 2022 is 29.3 in WDI, 27.9 in HNP |
| P27 | 0 | Wasting | World Bank income groups compared | wealth | T, L, G, D |  | fail: WDI publishes wasting by income group (2000 to 2024), but the classification's fiscal year could not be established from the tools, so G and D (country counts within groups) cannot be done; two framings left |
| P28 | 0 | HPV immunization | World Bank income groups compared | none | T, L, G |  | fail: WB_HCP_HPV_VAC has no World, income-group or FCS values |
| P29 | 0 | Family planning demand satisfied (modern methods) | LDCs, LLDCs and SIDS compared with the World | none | T, L, G, D | T, L, G, D | pass. Spotlight 23 |
| P30 | 0 | Skilled birth attendance | LDCs, LLDCs and SIDS compared with the World | wealth | T, L, G, D | T, L, G, D | pass. Spotlight 24 |
| P31 | 0 | Anaemia in women 15-49 | LDCs, LLDCs and SIDS compared with the World | none | T, L, G | T, L, G | pass. Spotlight 25 |
| P32 | 0 | Child overweight | Small island developing states (SIDS) | location | T, L, G | T, L, G | pass. Spotlight 26 |
| P33 | 0 | Youth NEET | Small island developing states (SIDS) | location | T, L, G, D | T, L, G, D | pass. Spotlight 27 |
| P34 | 0 | Stunting | Small island developing states (SIDS) | location | T, L, G | T, L, G | pass. Spotlight 28 |
| P35 | 0 | Women in local government | Landlocked developing countries (LLDCs) | none | T, L, D | T, L, D | pass. Spotlight 29 |
| P36 | 0 | DTP3 immunization | SDG regions compared | wealth | T, L, G | T, L, G | pass. Spotlight 30 |
| P37 | 0 | Child labour | SDG regions compared | sex | T, G, D | T, G, D | pass; the series is SL_TLF_CHLDEA (economic activity), so it is labelled that way, with no target wording. Spotlight 31 |
| P38 | 0 | MCV2 immunization | SDG regions compared | none | T, L, G | T, L, G | pass. Spotlight 32 |
| P39 | 0 | PCV3 immunization | SDG regions compared | none | T, L, G | T, L, G | pass. Spotlight 33 |
| P40 | 0 | Youth NEET | World | sex | T, L, G, D | T, L, G, D | pass. Spotlight 34 |
| P41 | 0 | Child overweight | World | sex | T, L, G | T, L, G | pass. Spotlight 35 |
| P42 | 0 | Violent discipline | World | none | D1, D2, D3 | D1, D2, D3 | pass. Spotlight 36 |
| P43 | 0 | Child multidimensional poverty | World | none | D1, D2, D3 | D1, D2, D3 | pass. Spotlight 37 |
| P44 | 0 | Early childhood development | World | none | D1, D2, D3 | D1, D2, D3 | pass. Spotlight 38 |
| P45 | 0 | Neonatal mortality | Eastern and South-eastern Asia | location | T, L, G | T, L | fail: fewer than three framings (G: 8 countries with both groups in the same year (needs 10)) |
| P46 | 0 | Women in national parliaments | Latin America and the Caribbean | none | T, L, D | T, L, D | pass. Spotlight 39 |
| P47 | 0 | Under-five mortality | Eastern and South-eastern Asia | location | T, L, G | T, L | fail: fewer than three framings (G: 8 countries with both groups in the same year (needs 10)) |
| P48 | 0 | Under-five mortality | Oceania excluding Australia and New Zealand | wealth | T, L, G | T, L | fail: fewer than three framings (G: 7 countries with both groups in the same year (needs 10)) |
| P49 | 0 | Adolescent birth rate | Central and Southern Asia | location | T, L, G, D | T, L, G, D | pass. Spotlight 40 |
| P50 | 0 | New HIV infections among adolescents | Oceania excluding Australia and New Zealand | sex | T, L, G |  | fail: fewer than three framings (T: no published value for the place; L: no published series of two years or more; G: 5 countries with both groups in the same year (needs 10)) |

## Selection

36 topics, as registered: 18 with a pace (P05 to P17 and P20 to P24) and 18 without (P29 to P44, P46 and P49).
Exactly 18 proposals without a pace passed, so all of them are in. Of the 20 with a pace that passed, JP dropped
P18 and P19 on 1 November 2026. No proposal had to be replaced. Spotlight numbers 05 to 40 follow proposal order
(`topics.csv`).

