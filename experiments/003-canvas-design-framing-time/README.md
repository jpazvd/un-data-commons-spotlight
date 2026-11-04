# Experiment 003: canvas and design, framing and posting time

Registered by the merge of `PREREGISTRATION.md`. Replaces experiment 002 before its first post; same topics, draw and
dates, with the design arms template E dark, template E light and template D dark.

- `PREREGISTRATION.md`: questions, arms, design, outcomes, analysis, decision rules, Provenance (what is 002's).
- `topics.csv`: 002's 36 topics, unchanged.
- `assignment.csv`: 002's draw with the design labels replaced in place; `make_assignment.py` reproduces it (seed
  20261102) and `check_relabel()` verifies it against 002's file.
- `build_versions_e.py`: builds every version into `spotlights/<slug>/versions/<frame>/` (template E with
  `scripts/banner_e.py`, D dark as 002 built it), with captions carrying the two comments; `--check` compares the E
  headlines with the revision 3 batch index.
- `analyze.py`, `test_analyze.py`: 002's analysis with the design labels changed (`python3 -m unittest` in this folder).
- `posts.csv`, `outcomes.csv`: filled by the scheduling and measurement runs, append-only.
