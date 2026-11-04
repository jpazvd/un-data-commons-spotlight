# Review of the experiment 002 banners

JP reviews every version on a private review page (a claude.ai artifact) and records, per banner, a verdict
(Looks right, Needs a change, Don't post), what the note is about and a comment; general notes apply to a scope
(all banners, one framing or one design). Claude reads the saved reviews, makes every fix in the scripts
(scripts/spotlight002.py, copy002.py, banner002.py), rebuilds with build_all.py, pushes the batch branches and
replies on each banner and note. A verdict is a note, not the approval: merging the batch PR is the approval.

- `page/make_review_page.py` and `page/template.html` build the page from the four batch branches
  (`python page/make_review_page.py REPO OUT_DIR`): images as committed, captions, alt text, schedule.
- `mocks/` holds design mocks waiting for a decision (round 1: the coverage chart for framing D).
- The saved reviews, notes and replies of each round are exported to `internal/experiment-002-review/`, which is
  never published.

Round 1 (1 to 2 Nov 2026): 4 general notes and 21 banner reviews. The changes are the commits "scripts: review
round 1 rules for experiment 002 banners" (9477ce6) and "Spotlights in batch N: rebuilt with the review round 1
rules" on each batch branch; the pre-registration itself was not amended (its Deviations section is still empty).
