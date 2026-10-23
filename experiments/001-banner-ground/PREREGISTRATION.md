# Experiment 001: banner ground, dark vs light

Registered 2026-10-23, before Spotlight 02 was produced. Author: João Pedro Azevedo.
The design, outcomes and analysis below are fixed. Any change is logged under Deviations, with its date and reason.

## Question

Does a dark banner (ink-blue ground) bring more conversation than an identical light banner, for the
Data Commons Spotlight posts on LinkedIn, X and Bluesky?

Why it matters: a dark image contrasts with a light feed and may stop the scroll; a light image looks
closer to a statistical publication. Both are plausible, so the choice should come from data.

## Arms

Both arms use the same layout (template D): one headline sentence of up to two lines, one annotated chart,
a byline strip; about 50 words on the image including axis labels (template A had about 175);
smallest text 20 px at 1200 px wide.
They differ only in the palette.

| Arm | Template | Ground |
| --- | --- | --- |
| Dark | `templates/banner-D-dark.dc.html` | #0D2433 |
| Light | `templates/banner-D-light.dc.html` | #F4F6F7 |

Everything else is held to the same rules in both arms: caption rules from the strategy document,
posting time chosen by Metricool's best-time data, same order (LinkedIn, X +30 min, Bluesky +60 min).

## Design

- Unit: one Spotlight. The same arm is used on all three networks.
- Spotlights 02 to 33, in eight blocks of four consecutive Spotlights (02–05, 06–09, …).
- Link placement on LinkedIn alternates by number: odd = repo link in the post body, even = in the first comment.
- Within each block, one odd and one even Spotlight are drawn at random to get the dark banner, so each block
  holds every combination of ground and link placement once.
- The draw is in `assignment.csv`, made by `make_assignment.py` with seed 20261023 and committed before
  Spotlight 02. The production task reads the arm from that file and never chooses it.
- Spotlight 01 (template A) is not part of the experiment.

## Outcomes

Each Spotlight post is measured once, 7 to 10 days after publication, from Metricool, and appended to `outcomes.csv`.

- **Primary:** LinkedIn comment rate, log((comments + 0.5) / impressions × 1,000).
- **Secondary:** LinkedIn impressions, reaction rate and share rate; X impressions, bookmarks and new follows;
  Bluesky likes + replies + reposts + quotes (Bluesky gives no impressions).
- **Link placement:** LinkedIn impressions, first comment against body. Descriptive only, because it was not randomised.

## Analysis

`analyze.py`: ratio dark / light from the mean within-block difference in the log outcome, using complete blocks only;
an exact randomisation test over the four allowed assignments per block; a 90% block-bootstrap interval once
four blocks are complete.

## Power, stated in advance

From my 22 LinkedIn posts of 16 Sep to 22 Oct 2026, the SD of the log comment rate is 0.9 and of log impressions 1.25.
With 32 Spotlights (80% power, 10% two-sided), the experiment can detect a dark/light ratio of about 2.2× in
comment rate and 3.0× in impressions. Smaller differences will not be distinguishable from noise. Spotlight posts
share one format, so their variance should be lower than this mixed baseline; it is re-estimated at the interim.

## Looks and decision rule

- **Interim, 4 December 2026** (about 3 complete blocks): descriptive only, plus a re-estimate of the variance.
  No decision, unless one arm is worse on the primary outcome in every complete block and on LinkedIn impressions.
- **Final, after Spotlight 33** (about late January 2027): adopt the arm with the higher primary outcome if the
  ratio is at least 1.2 and the 90% interval excludes 1. If inconclusive, decide on LinkedIn impressions by the same
  rule; if still inconclusive, keep dark, for contrast in a light feed, and record that the data did not decide it.
- The experiment can be extended by whole blocks if the interim variance shows that 32 is too few; that decision is
  made at the interim, before seeing the final comparison.

## Threats

- Topic varies from Spotlight to Spotlight; randomisation within blocks balances it on average, not in each pair.
- My own posting around the Spotlights changes the feed; the one-post-per-day rule limits overlap.
- Followers who see both arms may react to novelty; blocks spread both arms evenly over time.
- If I edit a draft heavily before approving it, that is recorded in the Deviations log.

## Deviations

None yet.
