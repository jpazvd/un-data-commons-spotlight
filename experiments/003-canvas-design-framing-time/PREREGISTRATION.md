# Experiment 003: canvas and design, framing and posting time

Drafted 2026-11-04 from experiment 002's pre-registration of 1 November 2026. Author: João Pedro Azevedo.
Status: proposed. It is registered when this file is merged into `main`, before the first post of the experiment.
From then on the design, outcomes, analysis and decision rules below are fixed; any change is logged under
Deviations, with its date and reason.

Experiment 003 replaces experiment 002 (template D dark, template D light, Ink), which stops before any of its
posts was published, with no outcome data (see the Deviations of
`experiments/002-design-framing-time/PREREGISTRATION.md`, 4 November 2026). Everything in 002 carries over
unchanged, with one exception: the design arms. JP decided on 4 November 2026 that template E, the square banner
of revision 3 (`docs/revision-3-2026-11/RECOMMENDATIONS.md`), reviewed in full on 3 November (Phase 2, 108
versions in both palettes, version 4 after the review: `docs/revision-3-2026-11/batch/REVIEW.md`), is the content
of the design experiment now rather than in January 2027. The topics, versions, framings, time slots, Bluesky
pairs, dates, outcomes, models and decision rules are 002's; the seeded draw is 002's with its three design
labels replaced in place (see Provenance). 001's question (dark against light) is carried into this experiment
as two of its three arms, on the new canvas.

## Questions

1. **Design.** Which banner design draws the most response: template E on a dark ground, template E on a light
   ground, or template D on a dark ground (the design 002 would have fallen back to, and the one the run-in
   posted on 3 November)? Two contrasts are pre-specified: the canvas (E dark against D dark: square canvas,
   headline as legend, registry definition as subtitle, direct labels, CC BY footer, as one bundle) and the
   ground (E dark against E light).
2. **Framing.** Which headline draws the most response: what it would take (the house rule of 31 October 2026),
   the long view (the observed trend), the gap behind the average, or the data behind the number? For topics
   where a target gives a pace, does the house rule beat the observed trend?
3. **Time on X.** Which of four posting times draws the most response on X?
4. **Feeds on Bluesky.** Does a community feed tag raise interactions on Bluesky?

## Units: topics and versions

- **Topic.** One SDG indicator, one place and, optionally, a breakdown (wealth quintile, urban and rural
  residence, or sex). A topic can be as simple as a global trend. Each topic is one Spotlight number with three
  versions, named by framing (`NN-T`, `NN-L`, `NN-G`, `NN-D`). The place is one of:
  - the World;
  - one SDG region (seven of the eight: the draw's place list left out Australia and New Zealand by mistake, see
    Amendments);
  - the SDG regions compared;
  - country groupings compared: least developed countries (LDCs), landlocked developing countries (LLDCs) and
    small island developing states (SIDS), against the World;
  - one grouping: LDCs, LLDCs or SIDS;
  - World Bank income groups compared;
  - fragile and conflict-affected situations (FCS, World Bank list) against the World.
- **Coverage rule.** The indicator needs good country coverage: at least 100 places with data in the latest
  snapshot of the 31 October 2026 catalogue (`docs/catalogue-2026-10/catalogue.json`; its moderate or strong
  country fact). An indicator below 100 places enters only as a **data-gap topic**: World or SDG regions compared,
  no breakdown, and all three versions about its data gaps. An indicator collected only where it applies is
  neither (female genital mutilation, measured where the practice is concentrated), and is not eligible.
- **Framings a topic supports.** A good-coverage topic needs at least three of the four framings below, and a
  topic with a pace to the target needs T and L. By place: one SDG region needs a published aggregate series for
  the indicator in that region; regions compared need a moderate or strong group fact covering at least 6 of the
  8 SDG regions; a grouping needs to be listed in that fact (all three for groupings compared); the observed trend
  needs a published series of two years or more for the place. Income groups and FCS are not places in the Data
  Commons (the catalogue run found no place for them), so these topics are conditional: they go ahead only if the
  World Bank publishes aggregates for the same series and groups, checked before the draw.
- **No two topics share an indicator and a place,** so no two topics share a "what it would take", trend or
  "data behind it" headline.
- **Selection.** A seeded draw (`propose_topics.py`, seed 20261101) proposes 50 topics: 24 with a pace and 26
  without, with quotas by place type (4 FCS, 4 income groups, 6 groupings compared, 6 one grouping, 8 regions
  compared, 10 World, 12 one region), every eligible indicator family at least once, at most 5 per family (child
  marriage before 18 and before 15 count as one family), at most one data-gap topic per family. 31 indicators
  qualify, 3 of them only as data-gap topics (early childhood development, child multidimensional poverty, violent
  discipline). I select 36: 18 with a pace and 18 without. I select on accuracy and sensitivity, not on expected
  performance. The selection is recorded in `topics.csv` before the assignment is drawn. Results apply to topics
  like these, not to every indicator.
- **Data checks before the draw.** Each selected topic must pass the usual Spotlight checks for all three
  versions (snapshot, SDG API check, numbers re-derived by script). Every group figure is a published aggregate:
  the UN SDG aggregates in the Data Commons for regions, LDCs, LLDCs and SIDS; the World Bank's for income groups
  and FCS. No aggregate is computed from country values. Counts of countries use the custodian's country values
  and, for income groups and FCS, the World Bank's classification in force when the data are retrieved, cited
  with its fiscal year. A place other than the World (each group, in a comparison) needs at least 10 countries
  with both groups of its breakdown, where it has one, for the "behind the average" version. A topic that fails is
  replaced by the next unselected proposal of the same stratum in proposal order, and the replacement is listed in
  `topics.csv`.

## Arms

**Framing (four arms, three per topic).** Every number comes from the topic's data snapshot and is re-derived by
script, as for every Spotlight.

| Arm | Headline leads with | Chart |
| --- | --- | --- |
| T, what it would take | The house rule (production task STEP 2b): the required pace in the indicator's units where the target and trend give one; for a per-country threshold, the number of countries still to reach it; otherwise the level, with no target wording | Trend with the required path, or countries against the threshold |
| L, the long view | The observed trend: the change since the base year, in the indicator's units, with the base and latest values | The trend |
| G, behind the average | The gap between the two ends of the breakdown (poorest and richest fifth, rural and urban, girls and boys), same source and year, as published aggregates by group or as a count of countries where the gap points one way; with no breakdown, the gap between the places compared (the highest and lowest region or group, against the World) | Groups side by side |
| D, the data behind it | Coverage and recency: how many countries have data and how recent their latest values are | Countries by year of their latest value |

Data-gap topics take three data versions instead: D1, how many countries have any data; D2, how recent the
latest values are; D3, which regions have data. They count in the design comparison, not in the framing one.

Wording rules for all arms: neutral and factual; a gap describes groups, never blames them; a data headline
describes the data, never the performance of a national statistical office; no fear, scarcity or urgency
framing (experiment principle 8). Captions follow the post craft rules; every caption keeps the "what it would
take" figure where one exists, and one "Method: " line.

**Design (three arms; every topic gets all three).**

| Arm | Template | Material |
| --- | --- | --- |
| E dark | `templates/banner-E-dark.dc.html`, drawn by `scripts/banner_e.py` | revision 3, Phase 2, version 4 (`docs/revision-3-2026-11/batch/`, dark palette) |
| E light | `templates/banner-E-light.dc.html`, drawn by `scripts/banner_e.py` | the same, light palette |
| D dark | `templates/banner-D-dark.dc.html`, drawn by `scripts/banner002.py` | experiment 002's D dark versions as merged (pull requests #24 to #27, review round 1) |

What the arms share: the same `stats.json` and so the same numbers; the same headline candidates, evidence line,
data line and chart data (`scripts/copy002.py`); the series line "UN Data Commons Spotlight · SDG x.y.z"; the
footer with custodian, series code, extraction date and "Data and code: @jpazvd on GitHub"; the same captions
and the same two comments. What differs between E and D is the revision 3 bundle: a 1:1 canvas instead of 1.9:1;
the headline as legend (group names in their series colours, no legend box); a subtitle that defines the measure
(the DEFINITION of the indicator's record in UNICEF's Reference Data Manager where the family has one, else the
SDG series name) and a "Definition: UNICEF Reference Data Manager, indicator <code>" footer line; direct labels at
the ends of each series; "· CC BY 4.0" in the data line; chart text no smaller than 26 px on the 1200 px
artboard. Two smaller differences are recorded rather than removed: (1) an E banner carries the headline
candidate that fits two lines at 56 px on the square canvas, which for some versions is the next candidate
rather than the one the D banner carries (`e.meta.json` in the version folder lists it under `flags`); (2) the
14 versions JP revised or replaced on 3 November 2026 (`REVIEW.md`) differ in E from their D banner in what the
chart shows (five coverage charts drawn by SDG region with countries with and without data stacked; three
waffles and two two-bar charts redrawn to fill their space; 22-G redrawn for every region that publishes both
aggregates; 27-L with the 2020 to 2021 band shaded). Spotlight 22's trend and pace versions (22-L, 22-T) use a
replacement series in every arm (safely managed sanitation for the same region, Data Commons calls of 4 November
2026), because the published water aggregate for Eastern and South-eastern Asia has a break; 22-G keeps the
water series. The house wording "countries and territories" is used in every arm (six D dark banners that said
"countries and areas" were rebuilt with it, with no other change: 26-T, 28-T, 34-T, 35-T, 37-D1, 38-D1). So the
design comparison is of E as reviewed against D as merged, and a difference between E and D dark is the effect
of the bundle, not of the canvas alone.

**Time on X (four slots, Rome time):** 09:00 (Europe morning), 13:00 (Europe midday), 16:00 (US East morning),
20:00 (US afternoon, Latin America afternoon).

**Bluesky feed tag (two arms):** the topic's feed tag on, or no hashtag. The tag is fixed per indicator in
`topics.csv` before the draw: #EduSky for learning and early childhood, #EconSky for poverty, labour and
water and sanitation, #PolicySky for the rest.

## Design

- **Framings per topic.** A pace topic gets T and L, plus G or D (where both are possible, drawn without
  replacement from a seeded shuffle of equal numbers of G and D, so the two are chosen about equally often), so
  the house rule meets the observed trend on all 18 pace topics. A data-gap topic gets D1, D2 and D3. Any other
  topic gets its three framings or, with four, three of them, the one left out drawn without replacement from a
  seeded shuffle of equal numbers of T, L, G and D, so that each is left out about equally often. The order of a
  topic's framings over the three periods is random.
- **Designs per topic.** Each topic's three versions take the three designs, in one of the 6 orders over the
  periods; within each stratum (pace, no pace) each order is used three times, so every design appears exactly 12
  times in every period. Among 2,000 seeded shuffles, the one that spreads framings most evenly over designs is
  kept (on a test selection: within one post of even in every framing).
- **X.** Three periods of 10 days, 10 November to 9 December 2026. A topic is posted on the same day of each
  period, so its versions are exactly 10 days apart. 36 topics over 10 days: 6 days with 4 posts and 4 days
  with 3. On a day with 4 posts each slot is used once; with 3, one slot is left out at random. 108 posts.
- **LinkedIn.** One banner a day at 11:00 Rome time, 10 November to 9 December, from a queue of one version per
  topic, in blocks of three topics that hold each design once. My own posts take a day out of the queue, which
  then moves on by a day: 18, 19 and 20 November are reserved now, and any other own-post day is logged when it
  is set. About 27 posts are expected; the rest of the queue is not posted. Logged under 002 on 4 November 2026
  and carried here: 13 and 14 November are own-post days too (COP31), so from 19-T on 15 November the queue runs
  one day later than `assignment.csv` and ends with 37-D3 on 9 December; 8-T and 36-D2 (queue positions 26 and
  27) are not posted and have "not posted" rows in `posts.csv`, which `analyze.py` reads (a LinkedIn post's due
  date is its `scheduled_for` date there). Own X and Bluesky posts in the run are logged in 002's Deviations.
- **Bluesky.** One banner a day for 60 days, 10 November 2026 to 8 January 2027, 60 minutes after its X post
  where there is one. Days 1 to 30 carry the day's first X banner; days 31 to 60 carry 30 of the remaining
  banners in a seeded order that keeps a topic's Bluesky posts at least 10 days apart. Within each pair of
  consecutive days, one day is drawn at random for the feed tag.
- **The draw.** `make_assignment.py`, seed 20261102, reads `topics.csv` and writes `assignment.csv`. Both are
  committed, with `analyze.py`, before the first post. The production and promotion tasks read the assignment
  and never choose an arm, a slot or a date.

## Run-in: Spotlights 02 to 04

- Spotlights 02 (under-five mortality, SDG 3.2.1), 03 (women in national parliaments, SDG 5.5.1) and 04 (maternal
  mortality, SDG 3.1.1) were produced under experiment 001 and were 002's run-in; they are 003's run-in for the
  same reason (single-version banners).
- 02 was posted on 3 November 2026 with its template D light banner (LinkedIn 11:00, X 13:00, Bluesky 14:00 Rome
  time). 03 (Thursday 5 November; LinkedIn 11:00, X 16:00, Bluesky 17:00) and 04 (Monday 9 November; LinkedIn
  11:00, X 20:00, Bluesky 21:00) are posted with their template E pilot renders (`docs/revision-3-2026-11/pilot`,
  pull request #31) on 001's assigned ground, 03 light and 04 dark, so that the square banner and the two
  comments are exercised on all three networks before the main run; merged as the run-in pull request of
  4 November 2026. The repo link is the first comment on every network; 04 carries the Reference Data Manager
  record (MNCH_MMR) as its second comment, 03 has no record (custodian IPU).
- Purpose: (1) test the whole pipeline (scheduling at the experiment's times, measurement at 7 to 10 days, outcome
  rows); (2) measure the level and spread of X engagements and Bluesky interactions on Spotlight posts, which the
  power figures below only assume. The re-estimate restates what the experiment can detect; it changes nothing in
  the design.
- Run-in posts are excluded from every comparison of arms and reported descriptively.

## Outcomes

Each post is measured once, 7 to 10 days after publication, from Metricool, and appended to `outcomes.csv`.

- **X, primary:** engagements per 1,000 impressions, where engagements are likes, reposts, replies, quotes and
  bookmarks. Secondary: reposts and quotes per 1,000 impressions, impressions, profile clicks, new follows.
- **LinkedIn, primary:** reactions and comments per 1,000 impressions. Secondary: comments per 1,000
  impressions, impressions, shares.
- **Bluesky, primary:** likes, reposts, replies and quotes per post (Bluesky reports no impressions).
  Secondary: new followers per week.

## Analysis

- **X and LinkedIn:** the outcome is log((count + 0.5) / impressions × 1,000). X model: fixed effects for topic,
  period and slot, plus framing and design, so framings are compared within topic. Data-gap versions (D1 to D3)
  enter the design comparison and are left out of the framing comparison. LinkedIn model: framing, design and day
  of the week (one version per topic, so no topic effect). Effects are reported as ratios, exp(coefficient), with
  90% intervals from a randomisation test that re-runs `make_assignment.py`'s draw with 10,000 other seeds.
- **Pace question:** the same X model on the 18 pace topics, comparing T with L (all 18 topics) and with the
  third framing (G or D).
- **Bluesky:** negative binomial model of interactions per post on the feed-tag arm with a pair effect;
  ratio and 90% interval as above.
- **Sensitivity:** a negative binomial model with log impressions as offset; results without posts that were
  corrected, delayed or deleted.

## Power, stated in advance

From my 27 LinkedIn posts of 16 September to 28 October 2026, the SD of log response per 1,000 is 0.48.
Assuming X varies as much (it may not), with 80% power and a 10% two-sided test:

- Design on X, 36 posts per arm: a ratio of about 1.33. Comparisons within topic should do better. The canvas and
  ground contrasts are each a pair of these arms, so the same figure applies to each.
- Framing on X, with about 32 T, 31 L, 20 G and 16 D posts (a test selection; restated when `topics.csv` is
  drawn): T against L about 1.35, against G about 1.4, against D about 1.45.
- The pace question, T against L on 18 topics: about 1.5.
- Time slot on X, 27 posts per slot: about 1.38.
- LinkedIn, about 8 posts per arm: about 1.8; LinkedIn is read alongside X, not on its own.
- Bluesky, 30 posts per arm, if posts average 2 interactions: about 2.2.

These figures are re-estimated at the interim from the data, without looking at arm differences.

## Looks and decision rules

- **4 December 2026:** descriptive only, as part of the strategy review. Variance re-estimate; no arm
  comparison is used to change anything.
- **Final read for X and LinkedIn: 16 to 18 December 2026** (every post measured at 7 days or more).
- **Final read for Bluesky: 15 to 18 January 2027.**
- **Rule for every question:** an arm is adopted if it beats each alternative by a ratio of at least 1.2 on the
  X primary outcome with a 90% interval that excludes 1, and the LinkedIn estimate does not point the other
  way (a ratio below 1 against the same alternative). Otherwise the result is inconclusive. Two questions have
  no LinkedIn check: time on X (LinkedIn has one slot) and the Bluesky feed tag, which is judged on the Bluesky
  primary outcome alone, with the same ratio and interval thresholds.
- **Design:** the adopted arm becomes the Spotlight template. Inconclusive: keep D dark (001's pre-registered
  fallback, for contrast in a light feed, and the design posted so far) and record that the data did not decide
  it. The two pre-specified contrasts are reported with the three-arm result: canvas (E dark against D dark) and
  ground (E dark against E light), each with its ratio and 90% interval; a contrast that meets the rule's
  threshold is reported as such even when the three-arm adoption rule is not met, and informs the next
  pre-registration, not the template.
- **Pace (house rule):** if L, or the third framing, beats T on the pace topics under the rule above, the
  required pace moves from the headline to the caption and the winning frame leads. If T beats the others, the
  rule is confirmed. Inconclusive: the rule stays, labelled untested.
- **Framing on other topics:** an adopted frame becomes the default headline where no pace applies.
  Inconclusive: the house rule's fallback (the level) stays.
- **Time on X:** an adopted slot becomes the X posting time. Inconclusive: X stays at LinkedIn plus 30 minutes.
- **Bluesky:** if the tag wins, feed tags go on every Bluesky post. Inconclusive: tags stay optional.

## Changes allowed during the run (set in advance)

No change to arms, slots, dates, caption style or hashtags once posting starts, except:

1. **Errors.** A post with a wrong number is deleted and its corrected version goes out in the next free slot
   of the same network. It stays in the analysis as assigned, flagged; the change is logged below.
2. **Guardrail.** If a network warns or limits the account, or net followers on a network fall in two
   consecutive weeks, that network's cadence drops from then on: X to 2 posts a day, its 09:00 and 20:00 posts
   not published; LinkedIn or Bluesky, which post once a day, to no further experiment posts (paused). Logged
   below; the analysis uses the published posts.
3. **Own posts.** As in Design (LinkedIn queue moves by a day). My own posts on X and Bluesky do not move the
   schedule; their dates and times are logged.
4. **Pipeline check on day 3:** that Metricool returns impressions for each X and LinkedIn post, and interaction
   counts (likes, reposts, replies, quotes) for each Bluesky post, which reports no impressions. Not a look at
   results.

## Threats

- Topics are selected, not drawn at random; the arms are randomised within topic, so comparisons are internally
  valid, but they describe topics like these.
- Novelty and fatigue across periods: period effects are in the X model and balanced by design.
- X's rule on "duplicative or substantially similar posts" on one account: a topic's versions have different
  headlines and charts and are 10 days apart.
- The design arms differ as bundles (E against D) and by the review of 3 November 2026 (14 E versions redrawn,
  see Arms), so a difference between E and D dark is not attributable to the canvas alone. The ground contrast
  (E dark against E light) is clean: the same drawing in two palettes.
- Template E was reviewed by JP on 3 November 2026 and template D by the review rounds of 2 November; neither
  arm was tuned to the other's outcome, and no outcome data existed when the arms were set.
- The run-in Spotlights 03 and 04 go out on template E before the first experiment post; they are descriptive
  and excluded from every comparison, as in 002.
- Three or four posts a day on X is itself a change from the cadence before; it is not tested and is reported.
- LinkedIn and X audiences overlap a little; arms are balanced on both networks.
- Bluesky days 31 to 60 fall in the holiday season; pairs of consecutive days balance it between arms.

## Deviations

- (none yet)

## Provenance: what is 002's and what changed (4 November 2026, before any post of 002 or 003)

- `topics.csv` is 002's file, unchanged (the 36 topics selected on 1 November 2026; the data checks in
  `experiments/002-design-framing-time/DATA_CHECKS.md` still apply, the data snapshots are the same files).
- `assignment.csv` is 002's registered draw (`make_assignment.py`, seed 20261102) with the design labels replaced
  in place: D-dark stays D-dark, D-light becomes E-light, Ink becomes E-dark. Every post keeps its topic, framing,
  date, slot, LinkedIn block and position, Bluesky day, pair and feed tag. `make_assignment.py` here is 002's
  script with `DESIGNS` and `TEMPLATE` changed and nothing else; the draw enumerates designs by position, so the
  same seed gives the relabelled file, and `check_relabel()` verifies it against 002's committed file (run:
  "relabel of 002's draw: verified"). The balance 002 established holds by construction: each design 12 times in
  every period on X, each block of three LinkedIn topics holding each design once.
- `analyze.py` and `test_analyze.py` are 002's with the design labels and the experiment number changed.
- The 72 E versions are built by `build_versions_e.py` from the same `stats.json` files as 002's banners, with
  `scripts/banner_e.py` (revision 3, version 4 rules and REVISIONS); each version folder keeps `e.meta.json`
  (headline as drawn, subtitle and its source, RDM code, flags). Every E headline is the one in the version 4 batch
  index except 39-L, reworded on 4 November so that it names the measure as `validate` requires ("Women in
  parliament, Latin America and the Caribbean: up 21.4 points since 2000"; the batch's wording, from a Copilot
  comment on pull request #32, did not). Spotlight 22-G's `stats.json` is now computed by `scripts/spotlight002.py`
  (the topic's meta.json lowers the places threshold to the three regions that publish both aggregates, with its
  reason) instead of written by hand as in the batch; the aggregates are the same, and the headline gap is now
  computed from the unrounded values like every other banner (26.7 points, where the batch's hand-rounded inputs
  gave 26.8), with the years line saying that only three SDG regions publish both aggregates. The 36 D dark versions are 002's files, except
  the six rebuilt for the house wording and 22-T (replacement series). Every version's `captions.md` carries the
  rule of 3 November 2026: no link in the body, the repo link as the first comment, the RDM record link as the
  second comment where the family has a record.
- 002's amendments before the first post (2 and 4 November 2026: review round 1's header and footer in every arm,
  the three rules amended as the scripts implement them, the draw described as drawn, the seven SDG regions)
  all carry over and are part of this registration.
- Experiment 002's folder, scripts and files stay on `main` as its record; 002 is reported as stopped without
  data. The number 003 was provisionally reserved for Spanish captions on X in `RECOMMENDATIONS.md`; that test, if
  run, takes the next number.
- The phase table in `docs/revision-3-2026-11/RECOMMENDATIONS.md` (E designed during 002, tested from 12 January
  2027) is superseded by this registration: the final read for X and LinkedIn is 16 to 18 December 2026, for
  Bluesky 15 to 18 January 2027, as in 002.
