# Experiment 002: design, framing and posting time

Drafted 2026-11-01; places, breakdowns and framings made flexible the same day. Author: João Pedro Azevedo.
Status: proposed. It is registered when this file is merged into `main`, before the first post of the experiment.
From then on the design, outcomes, analysis and decision rules below are fixed; any change is logged under
Deviations, with its date and reason.

Experiment 002 replaces experiment 001 (banner ground, dark against light), which stops before any of its
Spotlights was published (see the Deviations of `experiments/001-banner-ground/PREREGISTRATION.md`). 001's
question is carried into this experiment: its two arms are two of the three design arms below.

## Questions

1. **Design.** Which banner design draws the most response: template D on a dark ground, template D on a light
   ground, or Ink?
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

| Arm | Template |
| --- | --- |
| D dark | `templates/banner-D-dark.dc.html` (001's dark arm) |
| D light | `templates/banner-D-light.dc.html` (001's light arm) |
| Ink | identity 5, Ink (`docs/identity-2026-10/templates/banner-I5-ink.dc.html`, layout v2) |

The series line and byline strip carry the same words in all arms.

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
  is set. About 27 posts are expected; the rest of the queue is not posted.
- **Bluesky.** One banner a day for 60 days, 10 November 2026 to 8 January 2027, 60 minutes after its X post
  where there is one. Days 1 to 30 carry the day's first X banner; days 31 to 60 carry 30 of the remaining
  banners in a seeded order that keeps a topic's Bluesky posts at least 10 days apart. Within each pair of
  consecutive days, one day is drawn at random for the feed tag.
- **The draw.** `make_assignment.py`, seed 20261102, reads `topics.csv` and writes `assignment.csv`. Both are
  committed, with `analyze.py`, before the first post. The production and promotion tasks read the assignment
  and never choose an arm, a slot or a date.

## Run-in: Spotlights 02 to 04

- Spotlights 02 (under-five mortality, SDG 3.2.1), 03 (women in national parliaments, SDG 5.5.1) and 04 (maternal
  mortality, SDG 3.1.1) were produced under experiment 001 and never published. They join experiment 002 as its
  run-in, because their banners are built as single versions; their indicators can still be drawn as topics for
  other places.
- They are posted before the main run, one post per network each, with their banners and captions as merged:
  02 on Tuesday 3 November, 03 on Thursday 5 November, 04 on Monday 9 November 2026. LinkedIn at 11:00; X at
  13:00, 16:00 and 20:00 respectively; Bluesky 60 minutes after X (Rome time). Merging each pull request is the
  approval; the posts are scheduled for these times, not by the promotion task.
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

- Design on X, 36 posts per arm: a ratio of about 1.33. Comparisons within topic should do better.
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
  fallback, for contrast in a light feed) and record that the data did not decide it.
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
- Three or four posts a day on X is itself a change from the cadence before; it is not tested and is reported.
- LinkedIn and X audiences overlap a little; arms are balanced on both networks.
- Bluesky days 31 to 60 fall in the holiday season; pairs of consecutive days balance it between arms.

## Deviations

- **4 Nov 2026, own-post days (Changes allowed, item 3).** `assignment.csv` has 195 rows with a date (108 X, 60
  Bluesky, 27 LinkedIn); 193 of them were scheduled in Metricool on 4 Nov 2026 (108 X, 60 Bluesky, 25 LinkedIn),
  live, at the registered times, the two LinkedIn rows left out being the tail of the shifted queue below. Two
  LinkedIn posts of my own were already scheduled for 13 and 14 Nov 2026 at 11:00 (COP31), so, as registered,
  those days leave the LinkedIn queue and the queue moves on: 19-T posts on 15 Nov, 9-D on 16 Nov, 38-D3 on 17 Nov,
  6-L on 21 Nov and so on in queue order, ending with 37-D3 on 9 Dec; 8-T and 36-D2 (queue positions 26 and 27)
  are not posted. X and Bluesky dates and slots are unchanged. My own posts on X and Bluesky in the run, logged
  as registered: X 10 Nov 11:30 and 16:00; 11 Nov 09:00, 13:40, 14:10 and 15:00; 12 Nov 10:00; 13, 14, 19 and
  20 Nov 13:00 (the 13:00 ones also on Bluesky). Six of them share a minute with an experiment X post (10 Nov
  16:00, 11 Nov 09:00, 13, 14, 19 and 20 Nov 13:00).
- **4 Nov 2026: experiment 002 stops before its first post, with no outcome data** (`posts.csv` and `outcomes.csv`
  are empty; the first post was due on 10 November; the 193 posts scheduled in Metricool under the entry above
  are re-pointed to experiment 003's versions before they publish). JP decided that template E, the square banner of revision 3
  (`docs/revision-3-2026-11/RECOMMENDATIONS.md`), reviewed in full on 3 November 2026 (108 versions in both
  palettes, version 4 after the review), is the content of the design experiment now rather than from January
  2027. Adding E inside 002 is ruled out by experiment principle 3 (a factor is crossed, not swapped in), so 002 is
  replaced by experiment 003 (`experiments/003-canvas-design-framing-time/PREREGISTRATION.md`), which keeps 002's
  topics, versions, framings, slots, dates, Bluesky pairs, outcomes, models and decision rules, and its seeded draw
  with the three design labels replaced in place (D-dark stays, D-light becomes E-light, Ink becomes E-dark). This
  folder, its scripts and files stay as the record; `assignment.csv` is not changed and `analyze.py` is not run for a
  result. The run-in Spotlights 02 to 04 become 003's run-in; 02 was posted on 3 November under this file's run-in
  rules, 03 and 04 go out on template E (003's run-in section). 002's amendments of 2 and 4 November carry into 003.

## Amendments before the first post

- **2 Nov 2026, review round 1 (no experiment 002 post has gone out).** After JP reviewed the banners on the
  review page, the same changes were made to every version, in all three designs and all framings, by script
  (scripts/banner002.py, scripts/copy002.py; commit 9477ce6 on experiment/002-draw):
  the series line reads "UN Data Commons Spotlight" with no number; the byline is removed and the footer gives the
  source, the series or indicator code, the extraction date, "Data and code: @jpazvd on GitHub" and notes defining
  acronyms; pace headlines say which way the indicator must move; evidence lines give a year for each value; every
  headline names what is measured; ranked-gap charts say what a bar is. The words stay identical across the three
  designs, so the design contrast is unchanged; topics, versions, assignment.csv, slots and dates are unchanged.
  The run-in Spotlights 02 to 04 get the same header and footer (PR #29). A redesign of the coverage charts
  (framing D) is pending; if adopted, it will be logged here before 10 Nov.
- **4 Nov 2026, review round 2 (no experiment 002 post has gone out).** Three rules could not be applied as
  written to every network and are amended above, with no change to arms, topics, versions, assignment.csv,
  slots, dates, outcomes or models: (1) the adoption rule's LinkedIn check does not apply to time on X (LinkedIn
  has one slot) or to the Bluesky feed tag, which is judged on the Bluesky primary outcome alone, as
  `analyze.py` (PR #23) implements; (2) the guardrail's 09:00 and 20:00 posts exist only on X, so on LinkedIn or
  Bluesky, which post once a day, the response is to pause that network's experiment posts; (3) the day-3
  pipeline check asks for impressions on X and LinkedIn and interaction counts on Bluesky, which reports no
  impressions.
- **4 Nov 2026, review round 2, continued (no experiment 002 post has gone out).** Two points found in the
  scripts after the draw and the banners were built; the draw is kept and the description is corrected, rather
  than redrawing and rebuilding 108 versions. (1) Framings per topic: `make_assignment.py` draws the third
  framing of a flexible pace topic, and the framing a four-framing topic leaves out, without replacement from
  seeded shuffles of equal numbers of each option; it does not alternate or rotate them, as the design said.
  The wording above now describes the draw. In the registered draw, 8 of the 14 flexible pace topics took G and
  6 took D; of the 5 four-framing topics, T, L and G were left out once, once and three times. (2) Places:
  `propose_topics.py` lists seven SDG regions, leaving out Australia and New Zealand, although the catalogue
  holds its aggregates. Topics for that region had no chance of being proposed; one-region results describe
  the seven regions listed.
