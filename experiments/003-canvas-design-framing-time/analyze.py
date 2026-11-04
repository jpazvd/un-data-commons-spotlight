"""Pre-specified analysis for experiment 003: canvas and design, framing and posting time (see PREREGISTRATION.md, sections
below). This is experiment 002's analyze.py with the design labels (make_assignment.DESIGNS: D-dark, E-light, E-dark)
and the experiment number changed, nothing else; the models, outcomes, randomisation test and decision rules are 002's.
Original docstring follows.
Outcomes, Analysis, Power, and Looks and decision rules). Committed before the first post; after registration it
changes only to fix a bug, and any change is logged under Deviations in PREREGISTRATION.md.

Usage:
  python3 experiments/003-canvas-design-framing-time/analyze.py                 final read (X and LinkedIn from 16 December
                                                                         2026, Bluesky from 15 January 2027)
  python3 experiments/003-canvas-design-framing-time/analyze.py --interim       the 4 December look: descriptive only
Options: --redraws N (re-draws for the randomisation test, default 10,000), --json PATH (default results.json, or
interim.json with --interim, in the input folder), --dir FOLDER (input folder, default this one), --as-of
YYYY-MM-DD (date for counting posts whose measurement is due, default today), --workers N (processes for the
re-draws). A final read with 10,000 re-draws takes several minutes; the markdown report goes to stdout.

Inputs, in the input folder:
  topics.csv      the 36 selected topics (columns in make_assignment.py)
  assignment.csv  the registered draw (make_assignment.py, seed 20261102)
  posts.csv       one row per post as scheduled and published: network, spotlight, version, metricool_post_id,
                  scheduled_for, published_at, status (published, deleted, corrected or delayed), note
  outcomes.csv    one row per measurement: network, spotlight, version, post_url, published_at, measured_at,
                  days_since_post, impressions, likes_or_reactions, comments_or_replies, reposts_or_shares, quotes,
                  bookmarks, follows, profile_clicks, link_clicks (empty where the network does not report it)
  network is X, LinkedIn or Bluesky; version is the assignment's (e.g. 07-T); dates and times are ISO 8601.

The registered analysis, in prose.

Measurement. Each post is measured once, 7 to 10 days after publication (days_since_post, or measured_at minus
published_at). Only those measurements count; if a post has several, the earliest in the window is used. The
report counts the measurements outside the window and the posts measured only outside it. Run-in posts
(Spotlights 02, 03 and 04) are excluded from every comparison and reported descriptively.

Primary outcomes. X: engagements (likes, reposts, replies, quotes and bookmarks) per 1,000 impressions. LinkedIn:
reactions and comments per 1,000 impressions. Bluesky: likes, reposts, replies and quotes per post. An empty
component counts as 0 and is reported. For X and LinkedIn the modelled outcome is
log((count + 0.5) / impressions x 1,000); posts without impressions are left out and counted.

Models. Ratios are exp(coefficient).
- X: OLS with fixed effects for topic, period and slot, plus framing and design, so framings are compared within
  topic. Data-gap versions have framing levels of their own (D2 and D3; D1 is their base, absorbed by the topic
  effect): they enter the design and slot comparisons, and no framing ratio involves them. Framing ratios are
  reported among T, L, G and D only.
- Pace question: the same X model on the 18 pace topics, with framing coded T, L and the third framing (G or D,
  pooled); T against L and T against the third.
- LinkedIn: OLS with framing (T, L, G, D, and one level for data-gap versions), design and the day of the week
  of publication (one version per topic, so no topic effect).
- Bluesky: negative binomial (NB2) model of interactions per post on the feed tag, with a fixed effect for each
  pair of days (bluesky_pair).

Randomisation inference. The test re-runs make_assignment.main with seeds SEED+1 to SEED+N (N = --redraws). Each
re-draw relabels the posted units and leaves their outcomes where they are, the standard randomisation-inference
approach: on X the unit is a topic in a period, and its observed outcome (with its date and its day of the
period) stays with it while it takes the framing, design and slot that the re-draw gives that topic in that
period; on LinkedIn the unit is a queue position, keeping its day of the week and taking the re-draw's framing and
design for that position; on Bluesky the unit is a day, keeping its post and taking the re-draw's feed tag for
that day. Topic, period, day of week and pair are properties of the unit and are never relabelled. Keeping the
date with the unit assumes that a unit's outcome does not depend on which day of its period it was given; with
that, the test of no effect of any arm is exact, and the intervals below are approximate only through the other
arm effects being set at their estimates.
Interval: for a ratio A / B, the hypothesis log(A / B) = s fixes every unit's outcome under any re-draw (constant
effects on the log scale): the observed outcome minus the fitted effects of its observed labels plus the effects
of its re-drawn labels, with A / B set to s and every other arm effect of every relabelled factor at its
estimate (B is the reference). The statistic is studentised, |estimate - s| / standard error (the OLS one, or the
NB model-based one), recomputed under each re-draw, so that a re-draw whose design is more or less precise than
the observed one is weighed fairly; p(s) = (1 + re-draws at least as extreme) / (1 + re-draws), two-sided. The
90% interval is the set of shifts with p(s) > 0.10, found on a grid of shifts on the log scale around the
estimate (step 0.05 over plus or minus 3, refined to step 0.005 at each end, plus the shift 0) and reported by
its lowest and highest points, so it excludes 1 only if p(0) <= 0.10; the p-value is p(0). For OLS the re-fitted
contrast is linear in s and its residual sum of squares quadratic, so each re-draw is fitted once. For Bluesky
the shift multiplies the count (count x exp(s x (re-drawn tag - observed tag))) and the NB coefficient is refitted
with the dispersion fixed at its estimate on the observed data. A re-draw in which a compared arm is absent from
the analysed units, or the model is rank deficient, is not used for that ratio; the report gives the number used.

Sensitivity. (1) NB2 model of the count with log impressions as offset, with the terms of the X, pace and
LinkedIn models; ratio and a randomisation p-value under the sharp null that no arm has any effect (outcomes fixed,
studentised coefficient refitted under each re-draw with the dispersion fixed at its observed estimate). It has
no interval: inverting it would need a full NB fit per shift, per ratio and per re-draw. (2) The primary models
(with intervals) without the
posts that have a corrected, delayed or deleted row in posts.csv; primary results keep them, as assigned.

Decision rules. An arm is adopted if, against each alternative, its X ratio is at least 1.2 with a 90% interval
that excludes 1 (lower end above 1), and the LinkedIn ratio against the same alternative is not below 1 (a
LinkedIn ratio that cannot be estimated does not block). Otherwise the question is inconclusive.
- Design (D-dark, E-light, E-dark): the adopted arm becomes the Spotlight template; inconclusive keeps D-dark. The
  canvas contrast (E-dark against D-dark) and the ground contrast (E-dark against E-light) are two of the three pairs
  reported for the design factor.
- Framing (T, L, G, D, X model): the adopted frame becomes the default headline where no pace applies;
  inconclusive keeps the house rule's fallback (the level).
- Pace (pace model): T is confirmed if it beats L and the third framing; L or the third leads if it beats T
  (LinkedIn check: T against L for L; T against both G and D for the third). Inconclusive: the rule stays,
  labelled untested.
- Time on X (four slots): no LinkedIn check, as LinkedIn has one time; inconclusive keeps X at LinkedIn plus
  30 minutes.
- Bluesky feed tag: the same rule on the Bluesky ratio and interval, no LinkedIn check; inconclusive keeps tags
  optional.
The final reads come after every post's window has closed (X and LinkedIn 16 to 18 December 2026, Bluesky 15 to
18 January 2027); a verdict computed while posts of its networks are still to be measured is marked provisional.

Interim (--interim). Descriptive only, and no arm comparison is computed: posts measured and missing by network,
the SD of the log outcome by network (run-in posts included), and the minimum detectable ratios restated with
80% power at 10% two-sided, exp(2.486 x SD x sqrt(1/n_a + 1/n_b)), with the planned posts per arm from
assignment.csv. For Bluesky the SD is sqrt(1/mean + dispersion) of interactions per post (moment estimate of the
NB dispersion), the approximation that gives the registered 2.2 at a mean of 2 and a dispersion of 1. With fewer
than 3 measured posts on a network, the registered assumption is used and the report says so.

Tested with Python 3.13.18, numpy 2.5.3, scipy 1.18.1, statsmodels 0.15.0
(pip install --break-system-packages numpy==2.5.3 scipy==1.18.1 statsmodels==0.15.0).
"""
import argparse
import csv
import datetime as dt
import json
import math
import multiprocessing
import os
import pathlib
import statistics as st
import sys
import warnings

import numpy as np
import statsmodels.api as sm
from scipy.optimize import minimize_scalar

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_assignment  # noqa: E402

SEED = make_assignment.SEED
DESIGNS = list(make_assignment.DESIGNS)
SLOTS = list(make_assignment.SLOTS)
FRAMES = ["T", "L", "G", "D"]
GAP_FRAMES = ["D1", "D2", "D3"]
NETWORKS = ["X", "LinkedIn", "Bluesky"]
RUN_IN = {"02": "2026-11-03", "03": "2026-11-05", "04": "2026-11-09"}  # publication dates (PREREGISTRATION.md)
WINDOW = (7, 10)
FLAGGED = {"corrected", "delayed", "deleted"}
COUNTS = {"X": ["likes_or_reactions", "reposts_or_shares", "comments_or_replies", "quotes", "bookmarks"],
          "LinkedIn": ["likes_or_reactions", "comments_or_replies"],
          "Bluesky": ["likes_or_reactions", "reposts_or_shares", "comments_or_replies", "quotes"]}
MIN_RATIO, ALPHA, Z_POWER = 1.2, 0.10, 2.486
REGISTERED_SD, REGISTERED_BLUESKY = 0.48, (2.0, 1.0)  # SD of log response; Bluesky mean and NB dispersion
COARSE, FINE, HALF_WIDTH = 0.05, 0.005, 3.0
TAG_NAME = {"1": "tag on", "0": "no tag"}


def same(v):
    return v


# ---------------------------------------------------------------- inputs

def read_csv(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return [{k.strip(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(f)]


def network(v):
    return {"x": "X", "linkedin": "LinkedIn", "bluesky": "Bluesky"}.get(v.strip().lower(), v.strip())


def spot(v):
    return f"{int(v):02d}" if v.isdigit() else v


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def when(v):
    try:
        return dt.datetime.fromisoformat(v)
    except (TypeError, ValueError):
        return None


def days_since(r):
    d = num(r.get("days_since_post"))
    if d is not None:
        return d
    a, b = when(r.get("published_at")), when(r.get("measured_at"))
    if a is None or b is None:
        return None
    if (a.tzinfo is None) != (b.tzinfo is None):
        a, b = a.replace(tzinfo=None), b.replace(tzinfo=None)
    return (b - a).total_seconds() / 86400


def load(folder, as_of):
    """Experiment and run-in records (one per post, its measurement in the window) and the measurement counts."""
    assignment = read_csv(folder / "assignment.csv")
    posts, outcomes = read_csv(folder / "posts.csv"), read_csv(folder / "outcomes.csv")
    assigned = {(r["network"], r["version"]): r for r in assignment}
    status, published, scheduled = {}, {}, {}
    for p in posts:
        key = (network(p["network"]), p["version"])
        status.setdefault(key, set()).add(p.get("status", "").lower())
        if p.get("published_at"):
            published[key] = p["published_at"]
        if p.get("scheduled_for"):
            scheduled[key] = p["scheduled_for"][:10]
    # The LinkedIn queue moves around JP's own-post days (Design; Deviations of 4 Nov 2026 in 002): a post's due
    # date is the date it was scheduled for when posts.csv has one, and a version with status "not posted" (the
    # queue's unposted tail, 8-T and 36-D2) is not assigned a post at all.
    assignment = [r for r in assignment if "not posted" not in status.get((r["network"], r["version"]), set())]
    for r in assignment:
        r["date"] = scheduled.get((r["network"], r["version"]), r["date"])
    count = {n: dict(outcome_rows=0, outside_window=0, unmatched_rows=0) for n in NETWORKS}
    best, seen = {}, set()
    for r in outcomes:
        n, key = network(r["network"]), (network(r["network"]), r["version"])
        if n not in count:
            continue
        run_in = spot(r["spotlight"]) in RUN_IN
        count[n]["outcome_rows"] += 1
        if not run_in and key not in assigned:
            count[n]["unmatched_rows"] += 1
            continue
        seen.add(key)
        d = days_since(r)
        if d is None or not WINDOW[0] <= d <= WINDOW[1]:
            count[n]["outside_window"] += 1
            continue
        if key not in best or d < best[key][0]:
            best[key] = (d, r, run_in)
    records = []
    for key, (d, r, run_in) in best.items():
        n = key[0]
        parts = [num(r.get(c)) for c in COUNTS[n]]
        total = sum(p or 0 for p in parts)
        imp = num(r.get("impressions"))
        a = assigned.get(key)
        records.append(dict(
            network=n, version=key[1], spotlight=spot(r["spotlight"]), run_in=run_in, a=a, days=d, count=total,
            impressions=imp, empty=[c for c, p in zip(COUNTS[n], parts) if p is None],
            y=math.log((total + 0.5) / imp * 1000) if n != "Bluesky" and imp and imp > 0 else None,
            flagged=bool(status.get(key, set()) & FLAGGED),
            date=(r.get("published_at") or published.get(key) or (a or {}).get("date") or "")[:10]))
    def closed(date):  # the measurement window of a post published on this date has closed
        return dt.date.fromisoformat(date) + dt.timedelta(days=WINDOW[1]) <= as_of

    for n in NETWORKS:
        c = count[n]
        rec = [r for r in records if r["network"] == n]
        posted = [r for r in assignment if r["network"] == n and r["date"]]
        c["assigned_posts"] = len(posted)
        c["due"] = sum(1 for r in posted if closed(r["date"]))
        c["measured"] = sum(1 for r in rec if not r["run_in"])
        c["missing"] = sum(1 for r in posted if closed(r["date"]) and (n, r["version"]) not in best)
        c["pending"] = sum(1 for r in posted if not closed(r["date"]) and (n, r["version"]) not in best)
        c["measured_only_outside_window"] = sum(1 for k in seen if k[0] == n and k not in best)
        c["flagged_posts"] = sum(1 for k, s in status.items() if k[0] == n and k in assigned and s & FLAGGED)
        c["no_impressions"] = sum(1 for r in rec if n != "Bluesky" and r["y"] is None)
        c["empty_component"] = sum(1 for r in rec if r["empty"])
        c["run_in_due"] = sum(1 for d in RUN_IN.values() if closed(d))
        c["run_in_measured"] = sum(1 for r in rec if r["run_in"])
    return assignment, records, count


# ---------------------------------------------------------------- draws

def unit_labels(rows):
    """The randomised labels of one draw, by posted unit: X (spotlight, period) -> (framing, design, slot);
    LinkedIn queue position -> (framing, design); Bluesky day -> (feed tag on,)."""
    lab = {"X": {}, "LinkedIn": {}, "Bluesky": {}}
    for r in rows:
        if r["network"] == "X":
            lab["X"][(str(r["spotlight"]), str(r["period"]))] = (r["frame"], r["design"], r["slot"])
        elif r["network"] == "LinkedIn":
            lab["LinkedIn"][str(r["linkedin_position"])] = (r["frame"], r["design"])
        elif r["network"] == "Bluesky":
            lab["Bluesky"][str(r["bluesky_day"])] = (str(r["feed_tag_on"]),)
    return lab


def one_draw(job):
    topics_path, seed = job
    return unit_labels(make_assignment.main(topics_path, None, seed))


def compact(lab, order, canon):
    """A draw as one tuple of labels per network, in the units' order, sharing equal label tuples."""
    return {n: tuple(canon.setdefault(lab[n][u], lab[n][u]) for u in order[n]) for n in order}


def redraw(topics_path, n, workers, order):
    jobs = [(topics_path, SEED + k) for k in range(1, n + 1)]
    canon, draws = {}, []

    def collect(results):
        for i, lab in enumerate(results, 1):
            draws.append(compact(lab, order, canon))
            if i % 1000 == 0:
                print(f"  {i} of {n} re-draws", file=sys.stderr)

    if workers > 1 and n > 1:
        with multiprocessing.Pool(workers) as pool:
            collect(pool.imap(one_draw, jobs, chunksize=25))
    else:
        collect(map(one_draw, jobs))
    return draws


# ---------------------------------------------------------------- models

def onehot(values, drop_first):
    levels = sorted(set(values))
    cols = levels[1:] if drop_first else levels
    return np.array([[float(v == c) for c in cols] for v in values]).reshape(len(values), len(cols))


def make_model(name, net, recs, units, fixed, factors, order, observed):
    idx = {u: i for i, u in enumerate(order[net])}
    m = dict(name=name, net=net, recs=recs, pos=[idx[u] for u in units], fixed=fixed, factors=factors)
    m["observed"] = labels(m, observed)
    return m


def labels(model, draw):
    """Each relabelled factor's labels for the model's units under one draw."""
    row = draw[model["net"]]
    return {f["name"]: np.array([f["map"](row[i][f["k"]]) for i in model["pos"]]) for f in model["factors"]}


def design(model, lab):
    cols = [model["fixed"]]
    for f in model["factors"]:
        cols.append((lab[f["name"]][:, None] == np.array(f["levels"][1:])[None, :]).astype(float))
    return np.hstack(cols)


def coef(model, beta, factor, level):
    """A level's coefficient (0 for the reference, or for a label without a column, such as D1)."""
    i = model["fixed"].shape[1]
    for f in model["factors"]:
        if f["name"] == factor:
            levels = f["levels"][1:]
            return beta[i + levels.index(level)] if level in levels else np.zeros_like(beta[0])
        i += len(f["levels"]) - 1
    raise KeyError(factor)


def arm_effects(model, beta, lab):
    return sum(np.array([float(coef(model, beta, f["name"], v)) for v in lab[f["name"]]]) for f in model["factors"])


def present(lab, factor, a, b):
    return bool((lab[factor] == a).any() and (lab[factor] == b).any())


def used_columns(X):
    return int((np.abs(X).sum(axis=0) > 0).sum())


def pinv_rank(X):
    """Pseudo-inverse of X, or None if the columns that are not all zero are collinear (an all-zero column, a level
    absent from a draw, gets a zero row: the same fit as without it)."""
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    rank = int((S > S.max() * max(X.shape) * np.finfo(float).eps).sum()) if S.size and S.max() > 0 else 0
    if rank != used_columns(X):
        return None
    return (Vt[:rank].T / S[:rank]) @ U[:, :rank].T


def contrast(model, M, c):
    """Row a minus row b of a coefficient vector or of a pseudo-inverse, for the comparison c = (factor, a, b)."""
    f, a, b = c
    return coef(model, M, f, a) - coef(model, M, f, b)


def build_models(records, order, observed):
    """The registered models, from the experiment records (run-in excluded)."""
    rec = [r for r in records if not r["run_in"] and r["a"]]
    models = {}
    for name, pace_only in (("X", False), ("X pace", True)):
        recs = [r for r in rec if r["network"] == "X" and r["y"] is not None
                and (not pace_only or r["a"]["pace"] == "1")]
        if not recs:
            continue
        units = [(r["a"]["spotlight"], r["a"]["period"]) for r in recs]
        fixed = np.hstack([onehot([u[0] for u in units], False), onehot([u[1] for u in units], True)])
        if pace_only:
            framing = dict(name="framing", k=0, levels=["T", "L", "third"],
                           map=lambda f: "third" if f in ("G", "D") else f)
        else:
            framing = dict(name="framing", k=0, levels=["T", "L", "G", "D", "D2", "D3"], map=same)
        factors = [framing, dict(name="design", k=1, levels=DESIGNS, map=same),
                   dict(name="slot", k=2, levels=SLOTS, map=same)]
        models[name] = make_model(name, "X", recs, units, fixed, factors, order, observed)
    recs = [r for r in rec if r["network"] == "LinkedIn" and r["y"] is not None]
    if recs:
        units = [r["a"]["linkedin_position"] for r in recs]
        dow = [dt.date.fromisoformat(r["date"]).weekday() if r["date"] else -1 for r in recs]
        fixed = np.hstack([np.ones((len(recs), 1)), onehot(dow, True)])
        factors = [dict(name="framing", k=0, levels=["T", "L", "G", "D", "gap"],
                        map=lambda f: "gap" if f in GAP_FRAMES else f),
                   dict(name="design", k=1, levels=DESIGNS, map=same)]
        models["LinkedIn"] = make_model("LinkedIn", "LinkedIn", recs, units, fixed, factors, order, observed)
    recs = [r for r in rec if r["network"] == "Bluesky"]
    if recs:
        units = [r["a"]["bluesky_day"] for r in recs]
        fixed = onehot([int(r["a"]["bluesky_pair"]) for r in recs], False)
        factors = [dict(name="tag", k=0, levels=["0", "1"], map=same)]
        models["Bluesky"] = make_model("Bluesky", "Bluesky", recs, units, fixed, factors, order, observed)
    return models


def pairs_of(levels):
    return [(b, a) for i, a in enumerate(levels) for b in levels[i + 1:]]


PAIRS = {"X": {"framing": pairs_of(FRAMES), "design": pairs_of(DESIGNS), "slot": pairs_of(SLOTS)},
         "X pace": {"framing": [("T", "L"), ("T", "third")]},
         "LinkedIn": {"framing": pairs_of(FRAMES), "design": pairs_of(DESIGNS)},
         "Bluesky": {"tag": [("1", "0")]}}


# ---------------------------------------------------------------- randomisation inference

def interval(estimate, p_at):
    """90% interval by inverting the test over a grid of shifts on the log scale."""
    k = round(HALF_WIDTH / COARSE)
    grid = estimate + COARSE * np.arange(-k, k + 1)
    kept = [s for s in grid if p_at(s) > ALPHA]
    lo, hi = min(kept), max(kept)
    lo_open, hi_open = bool(lo == grid[0]), bool(hi == grid[-1])
    steps = FINE * np.arange(round(COARSE / FINE) + 1)
    if not lo_open:
        lo = min(s for s in lo - COARSE + steps if p_at(s) > ALPHA)
    if not hi_open:
        hi = max(s for s in hi + steps if p_at(s) > ALPHA)
    if p_at(0.0) > ALPHA:  # the shift 0 is a grid point too: the interval excludes 1 only if p(0) <= 0.10
        lo, hi = min(lo, 0.0), max(hi, 0.0)
    return lo, hi, lo_open, hi_open


def result(estimate, p_at, used, n):
    lo, hi, lo_open, hi_open = interval(estimate, p_at)
    return dict(ratio=math.exp(estimate), lo=math.exp(lo), hi=math.exp(hi), lo_open=lo_open, hi_open=hi_open,
                p=float(p_at(0.0)), redraws=used, posts=n)


def t_test(estimate, se, stats):
    """p(s) for an OLS ratio. Each row of stats is one re-draw: (a, b, k, rvv, rvz, rzz). Under the hypothesis
    log(A / B) = s, its re-fitted contrast minus s is a - s * b, and its squared standard error is
    k * (rvv + 2 e rvz + e^2 rzz), e = estimate - s (k: the contrast's variance factor over the residual degrees of
    freedom; r: cross-products of the residuals of the outcome net of arm effects and of the arm indicator)."""
    a, b, k, rvv, rvz, rzz = stats.T

    def p_at(s):
        e = estimate - s
        t = np.abs(a - s * b) / np.sqrt(np.maximum(k * (rvv + 2 * e * rvz + e * e * rzz), 1e-300))
        return (1 + np.sum(t >= abs(e) / se - 1e-9)) / (1 + len(a))
    return p_at


def ols_inference(model, draws, pairs):
    """Ratios with randomisation intervals for an OLS model; pairs is {factor: [(A, B), ...]}."""
    y = np.array([r["y"] for r in model["recs"]])
    n, lab0 = len(y), model["observed"]
    X0 = design(model, lab0)
    out = {f: {(a, b): None for a, b in pairs[f]} for f in pairs}
    P0 = pinv_rank(X0)
    if P0 is None or n - used_columns(X0) < 1:
        return out
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = sm.OLS(y, X0).fit()
    beta, cov = np.asarray(fit.params), np.asarray(fit.cov_params())
    resid = y - X0 @ beta
    s2 = resid @ resid / (n - used_columns(X0))
    todo = [(f, a, b) for f in pairs for a, b in pairs[f] if present(lab0, f, a, b)]
    est, se = {}, {}
    for c in todo:
        h, e = contrast(model, P0, c), contrast(model, np.eye(X0.shape[1]), c)
        est[c], se[c] = float(contrast(model, beta, c)), max(math.sqrt(s2 * h @ h), 1e-12)
        assert abs(est[c] - h @ y) < 1e-8 and abs(se[c] - math.sqrt(e @ cov @ e)) < 1e-6, "OLS fits disagree"
    arms = sorted({c[:2] for c in todo})
    # Columns: the outcome net of the fitted arm effects, then each compared arm's observed indicator.
    Y = np.column_stack([y - arm_effects(model, beta, lab0)] + [(lab0[f] == a).astype(float) for f, a in arms])
    stats = {c: [] for c in todo}
    for draw in draws:
        lab = labels(model, draw)
        X = design(model, lab)
        P = pinv_rank(X)
        df = n - used_columns(X)
        if P is None or df < 1:
            continue
        R = Y - X @ (P @ Y)
        gram = R.T @ R
        for c in todo:
            if not present(lab, *c):
                continue
            h = contrast(model, P, c)
            d, j = h @ Y, 1 + arms.index(c[:2])
            stats[c].append((d[0] + est[c] * d[j], d[j], h @ h / df, gram[0, 0], gram[0, j], gram[j, j]))
    for c in todo:
        s = np.array(stats[c]).reshape(-1, 6)
        out[c[0]][c[1:]] = result(est[c], t_test(est[c], se[c], s), len(s), n)
    return out


def nb_fit_ml(y, X, offset=None):
    """NB2 by maximum likelihood (statsmodels GLM, dispersion by profile likelihood): (dispersion, fitted model)."""
    def fit(alpha):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return sm.GLM(y, X, family=sm.families.NegativeBinomial(alpha=alpha), offset=offset).fit()
    best = minimize_scalar(lambda la: -fit(math.exp(la)).llf, bounds=(math.log(1e-4), math.log(50)),
                           method="bounded", options={"xatol": 1e-4})
    alpha = math.exp(best.x)
    return alpha, fit(alpha)


def nb_irls(y, X, offset, alpha, iters=100):
    """NB2 with the dispersion fixed, by iteratively reweighted least squares (log link): the coefficients and the
    pseudo-inverse of the weighted design at the solution (its contrast rows give standard errors), or None."""
    mu = np.maximum((y + y.mean()) / 2, 0.1)
    eta, beta = np.log(mu), None
    for _ in range(iters):
        sw = np.sqrt(mu / (1 + alpha * mu))
        P = pinv_rank(X * sw[:, None])
        if P is None:
            return None
        beta = P @ ((eta - offset + (y - mu) / mu) * sw)
        eta = np.maximum(X @ beta + offset, -30)
        new = np.exp(eta)
        done = np.max(np.abs(new - mu)) < 1e-10 * (1 + np.max(mu))
        mu = new
        if done:
            break
    P = pinv_rank(X * np.sqrt(mu / (1 + alpha * mu))[:, None])
    return None if P is None else (beta, P)


def nb_tag(Y, T, G, alpha, iters=100):
    """NB2 coefficient of the tag with pair fixed effects, dispersion fixed, for each row of Y and T (one row per
    draw), and its information (1 / variance). Each IRLS step is a weighted regression on the tag within pairs
    (G: units by pairs, 0/1)."""
    mu = np.maximum((Y + Y.mean(axis=1, keepdims=True)) / 2, 0.1)
    eta, beta = np.log(mu), np.zeros(len(Y))
    with np.errstate(divide="ignore", invalid="ignore"):
        for _ in range(iters):
            w = mu / (1 + alpha * mu)
            z = eta + (Y - mu) / mu
            ws = w @ G
            tbar, zbar = ((w * T) @ G) / ws, ((w * z) @ G) / ws
            td, zd = T - tbar @ G.T, z - zbar @ G.T
            new = (w * td * zd).sum(axis=1) / (w * td * td).sum(axis=1)
            eta = np.maximum((zbar - new[:, None] * tbar) @ G.T + new[:, None] * T, -30)
            mu = np.exp(eta)
            done = np.nanmax(np.abs(new - beta)) < 1e-9 if np.isfinite(new).any() else True
            beta = new
            if done:
                break
        w = mu / (1 + alpha * mu)
        td = T - (((w * T) @ G) / (w @ G)) @ G.T
        info = (w * td * td).sum(axis=1)
    return beta, info


def bluesky_inference(model, draws):
    """The feed-tag ratio (NB2 with pair effects) with its randomisation interval."""
    y = np.array([r["count"] for r in model["recs"]], dtype=float)
    lab0 = model["observed"]
    t0 = (lab0["tag"] == "1").astype(float)
    out = {"tag": {("1", "0"): None}}
    if not present(lab0, "tag", "1", "0"):
        return out, None
    X0 = design(model, lab0)
    alpha, fit = nb_fit_ml(y, X0)
    est = float(coef(model, np.asarray(fit.params), "tag", "1"))
    G = model["fixed"]
    b0, info0 = nb_tag(y[None, :], t0[None, :], G, alpha)
    se = 1 / math.sqrt(info0[0])
    assert abs(b0[0] - est) < 1e-4 and abs(se - float(np.asarray(fit.bse)[-1])) < 1e-3, "NB fits disagree"
    T = np.array([labels(model, d)["tag"] == "1" for d in draws], dtype=float).reshape(len(draws), len(y))

    def p_at(s):
        b, info = nb_tag(y * np.exp(s * (T - t0)), T, G, alpha)
        t = np.abs(b - s) * np.sqrt(info)
        ok = np.isfinite(t)
        return (1 + np.sum(t[ok] >= abs(est - s) / se - 1e-9)) / (1 + ok.sum())

    used = int(np.isfinite(nb_tag(y * np.ones_like(T), T, G, alpha)[0]).sum()) if len(draws) else 0
    out["tag"]["1", "0"] = result(est, p_at, used, len(y))
    return out, alpha


def nb_sensitivity(model, draws, pairs):
    """NB2 with log impressions as offset: ratios and p-values under the sharp null of no effect of any arm."""
    y = np.array([r["count"] for r in model["recs"]], dtype=float)
    off = np.log([r["impressions"] for r in model["recs"]])
    lab0 = model["observed"]
    X0 = design(model, lab0)
    alpha, fit = nb_fit_ml(y, X0, off)
    params = np.asarray(fit.params)
    sol = nb_irls(y, X0, off, alpha)
    out = {f: {(a, b): None for a, b in pairs[f]} for f in pairs}
    if sol is None:
        return out, alpha
    todo = [(f, a, b) for f in pairs for a, b in pairs[f] if present(lab0, f, a, b)]
    est, z0 = {}, {}
    for c in todo:
        est[c] = float(contrast(model, params, c))
        z0[c] = est[c] / np.linalg.norm(contrast(model, sol[1], c))
        assert abs(est[c] - float(contrast(model, sol[0], c))) < 1e-4, "NB fits disagree"
    stats = {c: [] for c in todo}
    for draw in draws:
        lab = labels(model, draw)
        sol = nb_irls(y, design(model, lab), off, alpha)
        for c in todo:
            if sol is not None and present(lab, *c):
                stats[c].append(float(contrast(model, sol[0], c)) / np.linalg.norm(contrast(model, sol[1], c)))
    for c in todo:
        z = np.array(stats[c])
        p = (1 + np.sum(np.abs(z) >= abs(z0[c]) - 1e-9)) / (1 + len(z))
        out[c[0]][c[1:]] = dict(ratio=math.exp(est[c]), p=float(p), redraws=len(z), posts=len(y))
    return out, alpha


def primary(models, draws):
    res = {}
    for name, m in models.items():
        if name == "Bluesky":
            res[name] = bluesky_inference(m, draws)[0]
        else:
            res[name] = ols_inference(m, draws, PAIRS[name])
    return res


# ---------------------------------------------------------------- decisions

def oriented(res, a, b):
    """Ratio a / b with its interval from one factor's results, or None."""
    if res is None:
        return None
    r = res.get((a, b))
    if r:
        return r["ratio"], r.get("lo"), r.get("hi")
    r = res.get((b, a))
    if r:
        return 1 / r["ratio"], 1 / r["hi"] if r.get("hi") else None, 1 / r["lo"] if r.get("lo") else None
    return None


def beats(a, b, main, linkedin=None, li_alts=None):
    r = oriented(main, a, b)
    if r is None or r[0] < MIN_RATIO or r[1] <= 1:
        return False
    alts = li_alts or {}
    for la in alts.get(a, [a]):
        for lb in alts.get(b, [b]):
            li = oriented(linkedin, la, lb)
            if li is not None and li[0] < 1:
                return False
    return True


def winner(arms, main, linkedin=None):
    for a in arms:
        if all(beats(a, b, main, linkedin) for b in arms if b != a):
            return a
    return None


def verdicts(res):
    x, li = res.get("X", {}), res.get("LinkedIn", {})
    out = {}
    w = winner(DESIGNS, x.get("design"), li.get("design"))
    out["design"] = (w, f"adopt {w}: it becomes the Spotlight template" if w else
                     "inconclusive: keep D-dark (the registered fallback) and record that the data did not decide it")
    w = winner(FRAMES, x.get("framing"), li.get("framing"))
    out["framing"] = (w, f"adopt {w}: it becomes the default headline where no pace applies" if w else
                      "inconclusive: the house rule's fallback (the level) stays")
    pace, alts = res.get("X pace", {}).get("framing"), {"third": ["G", "D"]}
    lif = li.get("framing")
    if beats("T", "L", pace, lif, alts) and beats("T", "third", pace, lif, alts):
        out["pace"] = ("T", "adopt T: the house rule is confirmed")
    else:
        lead = [a for a in ("L", "third") if beats(a, "T", pace, lif, alts)]
        arm = {"L": "L", "third": "the third framing (G or D)"}
        if len(lead) == 1:
            out["pace"] = (lead[0], f"adopt {arm[lead[0]]}: the required pace moves from the headline to the "
                                    f"caption and {arm[lead[0]]} leads")
        elif lead:
            out["pace"] = ("L or third", "adopt L or the third framing: both beat T, so the required pace moves to "
                                         "the caption; the registered comparisons do not say which of them leads")
        else:
            out["pace"] = (None, "inconclusive: the rule stays, labelled untested")
    w = winner(SLOTS, x.get("slot"))
    out["slot"] = (w, f"adopt {w}: it becomes the X posting time" if w else
                   "inconclusive: X stays at LinkedIn plus 30 minutes")
    w = winner(["1", "0"], res.get("Bluesky", {}).get("tag"))
    out["tag"] = (w and TAG_NAME[w], {"1": "adopt tag on: feed tags go on every Bluesky post",
                                     "0": "adopt no tag", None: "inconclusive: tags stay optional"}[w])
    return out


# ---------------------------------------------------------------- report

def name(level):
    return TAG_NAME.get(level, level)


def fmt_p(p):
    return f"{p:.3f}" if p >= 0.001 else f"{p:.4f}"


def fmt_interval(r):
    if not r or r.get("lo") is None:
        return ""
    return f"{'<' if r['lo_open'] else ''}{r['lo']:.2f} to {'>' if r['hi_open'] else ''}{r['hi']:.2f}"


def estimates_table(rows, li=None):
    head = "| Comparison | X ratio | 90% interval | p | LinkedIn ratio | 90% interval | p |" if li is not None else \
        "| Comparison | Ratio | 90% interval | p |"
    lines = [head, "|" + " --- |" * (head.count("|") - 1)]
    for (a, b), r in rows.items():
        cells = [f"{name(a)} / {name(b)}"]
        cells += [f"{r['ratio']:.2f}", fmt_interval(r), fmt_p(r['p'])] if r else ["not estimable", "", ""]
        if li is not None:
            lr = li.get((a, b)) if li else None
            cells += [f"{lr['ratio']:.2f}", fmt_interval(lr), fmt_p(lr['p'])] if lr else ["not estimable", "", ""]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def model_note(models, res, name_, factor):
    rows = [r for r in (res.get(name_, {}).get(factor) or {}).values() if r]
    if name_ not in models:
        return f"{name_} model: no measured post yet."
    used = f", re-draws used {min(r['redraws'] for r in rows)} to {max(r['redraws'] for r in rows)}" if rows else ""
    return f"{name_} model: {len(models[name_]['recs'])} posts{used}."


def measurement_lines(count):
    keys = [("assigned_posts", "Posts assigned (with a date)"), ("due", "Measurement due by the as-of date"),
            ("measured", "Measured 7 to 10 days after publication"), ("missing", "Due but not measured in the window"),
            ("pending", "Not measured yet, window still open or not reached"),
            ("outcome_rows", "Outcome rows"), ("outside_window", "Outcome rows outside 7 to 10 days"),
            ("measured_only_outside_window", "Posts measured only outside the window"),
            ("unmatched_rows", "Outcome rows matching no assigned post"),
            ("flagged_posts", "Posts corrected, delayed or deleted"),
            ("no_impressions", "Measured without impressions"),
            ("empty_component", "Measured with an empty primary component (counted as 0)"),
            ("run_in_due", "Run-in posts due"), ("run_in_measured", "Run-in posts measured in the window")]
    lines = ["| | X | LinkedIn | Bluesky |", "| --- | --- | --- | --- |"]
    for k, label in keys:
        lines.append(f"| {label} | " + " | ".join(str(count[n][k]) for n in NETWORKS) + " |")
    return lines


def run_in_lines(records):
    rows = sorted((r for r in records if r["run_in"]), key=lambda r: (r["spotlight"], NETWORKS.index(r["network"])))
    if not rows:
        return ["No run-in post measured in the window yet."], []
    lines = ["| Spotlight | Network | Published | Days | Impressions | Primary count | Per 1,000 impressions |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    out = []
    for r in rows:
        rate = r["count"] / r["impressions"] * 1000 if r["impressions"] else None
        imp = "" if r["impressions"] is None else f"{r['impressions']:.0f}"
        per = "" if rate is None else f"{rate:.1f}"
        lines.append(f"| {r['spotlight']} | {r['network']} | {r['date']} | {r['days']:g} | {imp} | "
                     f"{r['count']:.0f} | {per} |")
        out.append(dict(spotlight=r["spotlight"], network=r["network"], published=r["date"], days=r["days"],
                        impressions=r["impressions"], count=r["count"], per_1000=rate))
    return lines, out


def spread_and_power(records, assignment):
    """Interim: SD of the log outcome by network and restated minimum detectable ratios."""
    spread = {}
    for n in NETWORKS:
        rec = [r for r in records if r["network"] == n]
        if n == "Bluesky":
            vals = [math.log(r["count"] + 0.5) for r in rec]
        else:
            vals = [r["y"] for r in rec if r["y"] is not None]
        s = dict(posts=len(vals), run_in=sum(1 for r in rec if r["run_in"]),
                 sd=st.stdev(vals) if len(vals) >= 2 else None)
        if n == "Bluesky" and rec:
            c = [r["count"] for r in rec]
            mean = st.mean(c)
            s["mean_count"] = mean
            s["dispersion"] = max(0.0, (st.variance(c) - mean) / mean ** 2) if len(c) >= 2 and mean > 0 else None
        spread[n] = s

    def sd_for(n):
        s = spread[n]
        if n == "Bluesky":
            if s["posts"] >= 3 and s.get("dispersion") is not None:
                return math.sqrt(1 / s["mean_count"] + s["dispersion"]), "measured"
            return math.sqrt(1 / REGISTERED_BLUESKY[0] + REGISTERED_BLUESKY[1]), "registered assumption"
        return (s["sd"], "measured") if s["posts"] >= 3 else (REGISTERED_SD, "registered assumption")

    x = [r for r in assignment if r["network"] == "X"]
    li = [r for r in assignment if r["network"] == "LinkedIn" and r["date"]]
    bs = [r for r in assignment if r["network"] == "Bluesky"]

    def n_of(rows, key, value):
        return sum(1 for r in rows if r[key] == value)

    def smallest(rows, key, levels):
        return sorted(n_of(rows, key, v) for v in levels)[:2]

    pace = [r for r in x if r["pace"] == "1"]
    plan = [("Design on X (smallest pair of arms)", "X", *smallest(x, "design", DESIGNS), 1.33),
            ("Framing on X, T against L", "X", n_of(x, "frame", "T"), n_of(x, "frame", "L"), 1.35),
            ("Framing on X, T against G", "X", n_of(x, "frame", "T"), n_of(x, "frame", "G"), 1.4),
            ("Framing on X, T against D", "X", n_of(x, "frame", "T"), n_of(x, "frame", "D"), 1.45),
            ("Pace topics on X, T against L", "X", n_of(pace, "frame", "T"), n_of(pace, "frame", "L"), 1.5),
            ("Time slot on X (smallest pair of slots)", "X", *smallest(x, "slot", SLOTS), 1.38),
            ("LinkedIn design (smallest pair of arms)", "LinkedIn", *smallest(li, "design", DESIGNS), 1.8),
            ("Bluesky feed tag, on against off", "Bluesky", *smallest(bs, "feed_tag_on", ["0", "1"]), 2.2)]
    power = []
    for label, n, n1, n2, registered in plan:
        sd, source = sd_for(n)
        mdr = math.exp(Z_POWER * sd * math.sqrt(1 / n1 + 1 / n2)) if n1 and n2 else None
        power.append(dict(comparison=label, network=n, posts=[n1, n2], sd=sd, sd_source=source, mdr=mdr,
                          registered=registered))
    return spread, power


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description="Experiment 003: pre-registered analysis.")
    ap.add_argument("--dir", type=pathlib.Path, default=HERE, help="folder with the four input files")
    ap.add_argument("--redraws", type=int, default=10000, help="re-draws for the randomisation test")
    ap.add_argument("--json", type=pathlib.Path, default=None, help="where to write the results as JSON")
    ap.add_argument("--interim", action="store_true", help="descriptive look only: no arm comparison")
    ap.add_argument("--as-of", type=dt.date.fromisoformat, default=dt.date.today(), help="YYYY-MM-DD")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 1, help="processes for the re-draws")
    a = ap.parse_args(argv)
    folder = a.dir.resolve()
    json_path = a.json or folder / ("interim.json" if a.interim else "results.json")
    assignment, records, count = load(folder, a.as_of)
    if not assignment:
        raise SystemExit(f"no assignment.csv in {folder}")
    mode = "interim look (descriptive only)" if a.interim else "final read"
    out = dict(mode="interim" if a.interim else "final", folder=str(folder), as_of=a.as_of.isoformat(),
               measurement=count)
    lines = [f"# Experiment 003: {mode}", "",
             f"Inputs: {folder}. As of {a.as_of.isoformat()}. Measurement window: {WINDOW[0]} to {WINDOW[1]} days.", "",
             "## Measurements", ""] + measurement_lines(count)
    run_lines, out["run_in"] = run_in_lines(records)
    lines += ["", "## Run-in: Spotlights 02 to 04 (descriptive, in no comparison)", ""] + run_lines

    if a.interim:
        spread, power = spread_and_power(records, assignment)
        out.update(spread=spread, power=power)
        lines += ["", "## Spread of the log outcome (all measured posts, run-in included)", "",
                  "| Network | Posts | Of which run-in | SD | Mean count | NB dispersion |",
                  "| --- | --- | --- | --- | --- | --- |"]
        for n, s in spread.items():
            sd = "" if s["sd"] is None else f"{s['sd']:.2f}"
            mean = f"{s['mean_count']:.2f}" if s.get("mean_count") is not None else ""
            disp = f"{s['dispersion']:.2f}" if s.get("dispersion") is not None else ""
            lines.append(f"| {n} | {s['posts']} | {s['run_in']} | {sd} | {mean} | {disp} |")
        lines += ["", "Bluesky: SD of log(interactions + 0.5); its power uses sqrt(1/mean + dispersion).", "",
                  "## Minimum detectable ratios (80% power, 10% two-sided, z = 2.486)", "",
                  "| Comparison | Planned posts | SD used | Restated | Registered |", "| --- | --- | --- | --- | --- |"]
        for p in power:
            mdr = "" if p["mdr"] is None else f"{p['mdr']:.2f}"
            lines.append(f"| {p['comparison']} | {p['posts'][0]} and {p['posts'][1]} | {p['sd']:.2f} "
                         f"({p['sd_source']}) | {mdr} | {p['registered']} |")
        lines += ["", "Planned posts per arm come from assignment.csv. No arm comparison is computed at this look."]
        print("\n".join(lines))
        json_path.write_text(json.dumps(out, indent=1, default=str))
        return out

    topics_path = folder / "topics.csv"
    order = {n: sorted(unit_labels(assignment)[n]) for n in NETWORKS}
    canon = {}
    observed = compact(unit_labels(assignment), order, canon)
    registered_draw = compact(one_draw((topics_path, SEED)), order, canon)
    matches = registered_draw == observed
    print(f"Re-running the draw with {a.redraws} seeds ({SEED + 1} to {SEED + a.redraws})...", file=sys.stderr)
    draws = redraw(topics_path, a.redraws, a.workers, order)
    models = build_models(records, order, observed)
    res = primary(models, draws)
    decided = verdicts(res)
    out.update(redraws=a.redraws, seeds=[SEED + 1, SEED + a.redraws], assignment_matches_registered_draw=matches)
    lines += ["", "## Randomisation test", "",
              f"{a.redraws} re-draws of make_assignment.py (seeds {SEED + 1} to {SEED + a.redraws}); 90% intervals by "
              "test inversion; p is two-sided, against a ratio of 1.",
              "assignment.csv matches the registered draw from topics.csv (seed 20261102): "
              + ("yes." if matches else "NO. The test assumes it does; check before reading the results.")]

    x, li, pace, blue = res.get("X", {}), res.get("LinkedIn", {}), res.get("X pace", {}), res.get("Bluesky", {})
    sections = [("design", "Design", x.get("design"), li.get("design") or {}, ["X", "LinkedIn"]),
                ("framing", "Framing (X model; data-gap versions in no framing ratio)", x.get("framing"),
                 li.get("framing") or {}, ["X", "LinkedIn"]),
                ("pace", "Pace: the house rule on the 18 pace topics (X)", pace.get("framing"), None, ["X pace"]),
                ("slot", "Time on X", x.get("slot"), None, ["X"]),
                ("tag", "Bluesky feed tag (negative binomial, pair effects)", blue.get("tag"), None, ["Bluesky"])]
    out["questions"] = {}
    for key, title, main_rows, li_rows, notes in sections:
        factor = {"pace": "framing", "tag": "tag"}.get(key, key)
        rows = main_rows if main_rows is not None else {p: None for p in PAIRS[notes[0]][factor]}
        lines += ["", f"## {title}", ""] + estimates_table(rows, li_rows) + [""]
        lines += [model_note(models, res, n, factor) for n in notes]
        if key == "pace":
            lines.append("LinkedIn check for the pace question: T against L, and T against both G and D for the third.")
        nets = {"design": ["X", "LinkedIn"], "framing": ["X", "LinkedIn"], "tag": ["Bluesky"]}.get(key, ["X"])
        pending = {n: count[n]["pending"] for n in nets if count[n]["pending"]}
        if pending:  # the registered final reads come after every post's window has closed
            lines.append("Provisional: not every post is measured yet ("
                         + ", ".join(f"{n} {k}" for n, k in pending.items()) + " posts still to come).")
        lines += ["", f"Verdict{' (provisional)' if pending else ''}: {decided[key][1]}."]
        out["questions"][key] = dict(adopted=decided[key][0], verdict=decided[key][1], provisional=bool(pending),
                                     estimates={f"{name(p[0])} / {name(p[1])}": r for p, r in rows.items()},
                                     linkedin={f"{name(p[0])} / {name(p[1])}": r for p, r in (li_rows or {}).items()})

    lines += ["", "## Sensitivity", "", "### Negative binomial with log impressions as offset", "",
              "Ratio and randomisation p under the sharp null that no arm has any effect (no interval).", "",
              "| Model | Comparison | Ratio | p |", "| --- | --- | --- | --- |"]
    out["sensitivity"] = {"negative_binomial": {}, "without_flagged": None}
    for n in ("X", "X pace", "LinkedIn"):
        if n not in models:
            continue
        nb, alpha = nb_sensitivity(models[n], draws, PAIRS[n])
        out["sensitivity"]["negative_binomial"][n] = dict(
            dispersion=alpha, ratios={f"{f}: {name(p[0])} / {name(p[1])}": r for f in nb for p, r in nb[f].items()})
        for f in nb:
            for p, r in nb[f].items():
                cells = [f"{r['ratio']:.2f}", fmt_p(r['p'])] if r else ["not estimable", ""]
                lines.append(f"| {n} | {name(p[0])} / {name(p[1])} | " + " | ".join(cells) + " |")
    flagged = [r for r in records if r["flagged"] and not r["run_in"] and r["a"]]
    lines += ["", "### Without posts corrected, delayed or deleted", ""]
    if not flagged:
        lines.append("No measured post is flagged: identical to the primary results.")
    else:
        sub = build_models([r for r in records if not r["flagged"]], order, observed)
        res2 = primary(sub, draws)
        left_out = [f"{r['network']} {r['version']}" for r in flagged]
        out["sensitivity"]["without_flagged"] = {
            "posts_left_out": left_out,
            "verdicts": {k: v[1] for k, v in verdicts(res2).items()},
            "estimates": {n: {f"{f}: {name(p[0])} / {name(p[1])}": r for f in res2[n] for p, r in res2[n][f].items()}
                          for n in res2}}
        lines.append(f"Left out: {', '.join(left_out)}.")
        lines += ["", "| Model | Comparison | Ratio | 90% interval | p |", "| --- | --- | --- | --- | --- |"]
        for n in res2:
            for f in res2[n]:
                for p, r in res2[n][f].items():
                    cells = [f"{r['ratio']:.2f}", fmt_interval(r), fmt_p(r['p'])] if r else ["not estimable", "", ""]
                    lines.append(f"| {n} | {f}: {name(p[0])} / {name(p[1])} | " + " | ".join(cells) + " |")
        lines += [""] + [f"Verdict without them, {k}: {v[1]}." for k, v in verdicts(res2).items()]
    print("\n".join(lines))

    def keyed(d):
        return {f"{name(k[0])} / {name(k[1])}" if isinstance(k, tuple) else k: keyed(v) if isinstance(v, dict) else v
                for k, v in d.items()}
    out["models"] = {n: dict(posts=len(models[n]["recs"]), ratios=keyed(res[n])) for n in res}
    json_path.write_text(json.dumps(out, indent=1, default=str))
    return out


if __name__ == "__main__":
    main()
