"""Pre-specified analysis for experiment 001 (see PREREGISTRATION.md). Do not change after 2026-10-23
except to fix a bug; any change is recorded in the deviations log of PREREGISTRATION.md.

Usage: python experiments/001-banner-ground/analyze.py [--network linkedin] [--outcome comment_rate]

Outcomes (per post, measured 7-10 days after publication):
  comment_rate     log((comments + 0.5) / impressions * 1000)      PRIMARY (LinkedIn)
  impressions      log(impressions)                                 secondary
  reaction_rate    log((reactions + 0.5) / impressions * 1000)      secondary
  share_rate       log((shares + 0.5) / impressions * 1000)         secondary
  bookmarks        log(bookmarks + 0.5)                             secondary (X)
  follows          log(follows + 0.5)                               secondary (X)
  engagement       log(likes + replies + reposts + quotes + 0.5)    secondary (Bluesky, no impressions)

Estimand: ratio dark / light, from the mean within-block difference in the log outcome
(complete blocks only; the 2x2 design balances link placement within each block).
Inference: exact randomisation test over the 4 allowed dark assignments per block
(one body and one first-comment Spotlight dark: one odd and one even number in the original
slots), and a 90% interval from a block bootstrap.
The link-placement effect (first comment / body) is estimated the same way, descriptively:
it was not randomised, it alternates by Spotlight number.
"""
import argparse, csv, itertools, math, pathlib, random, statistics as st

HERE = pathlib.Path(__file__).resolve().parent


def load():
    assign = {r["spotlight"]: r for r in csv.DictReader(open(HERE / "assignment.csv"))}
    out = list(csv.DictReader(open(HERE / "outcomes.csv")))
    return assign, out


def value(r, outcome):
    f = lambda k: float(r[k]) if r.get(k) not in (None, "") else None
    imp = f("impressions")
    if outcome == "impressions":
        return math.log(imp) if imp else None
    if outcome in ("comment_rate", "reaction_rate", "share_rate"):
        key = {"comment_rate": "comments_or_replies", "reaction_rate": "reactions_or_likes",
               "share_rate": "shares_or_reposts"}[outcome]
        return math.log((f(key) + 0.5) / imp * 1000) if imp and f(key) is not None else None
    if outcome in ("bookmarks", "follows"):
        return math.log(f(outcome) + 0.5) if f(outcome) is not None else None
    if outcome == "engagement":
        parts = [f(k) or 0 for k in ("reactions_or_likes", "comments_or_replies", "shares_or_reposts", "quotes")]
        return math.log(sum(parts) + 0.5)
    raise SystemExit(f"unknown outcome {outcome}")


def block_effects(blocks, factor):
    """Mean of (mean y | level 1) - (mean y | level 0) within each complete block."""
    eff = []
    for rows in blocks.values():
        a = [y for lv, y in rows if lv == 1]; b = [y for lv, y in rows if lv == 0]
        eff.append(st.mean(a) - st.mean(b))
    return eff


def ground_result(complete, assign):
    """The primary estimate over the given complete blocks, as the line main() prints."""
    ground = {b: [(int(assign[k]["ground"] == "dark"), y) for k, y in v] for b, v in complete.items()}
    est = st.mean(block_effects(ground, None))
    # exact randomisation distribution: in each block, one body and one first-comment Spotlight are
    # dark. The strata come from link_placement, not the number's parity: they coincide for the
    # original slots, and a make-up (PREREGISTRATION.md, Deviations) keeps its slot's placement.
    perms = []
    for b, v in complete.items():
        body = [k for k, _ in v if assign[k]["link_placement"] == "body"]
        first = [k for k, _ in v if assign[k]["link_placement"] == "first_comment"]
        perms.append([{o, e} for o in body for e in first])
    ys = {b: dict(v) for b, v in complete.items()}
    null = []
    for combo in itertools.product(*perms):
        effs = []
        for (b, yv), dark in zip(ys.items(), combo):
            effs.append(st.mean([yv[k] for k in dark]) - st.mean([yv[k] for k in yv if k not in dark]))
        null.append(st.mean(effs))
    p = sum(abs(x) >= abs(est) - 1e-12 for x in null) / len(null)
    rng = random.Random(1); effs = block_effects(ground, None); boots = []
    for _ in range(5000):
        boots.append(st.mean(rng.choice(effs) for _ in effs))
    boots.sort(); lo, hi = boots[int(0.05 * len(boots))], boots[int(0.95 * len(boots)) - 1]
    interval = (f"90% block-bootstrap interval {math.exp(lo):.2f} to {math.exp(hi):.2f}"
                if len(complete) >= 4 else "no interval until 4 complete blocks")
    return (f"Ground, dark / light: ratio {math.exp(est):.2f} ({interval}), "
            f"randomisation p = {p:.3f} over {len(null)} assignments")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", default="linkedin")
    ap.add_argument("--outcome", default="comment_rate")
    a = ap.parse_args()
    assign, out = load()
    rows = [r for r in out if r["network"] == a.network and r["spotlight"] in assign
            and r["days_since_post"] and 7 <= float(r["days_since_post"]) <= 10]
    data = {}
    for r in rows:  # one measurement per Spotlight: the earliest in the 7-10 day window
        k = r["spotlight"]
        if k not in data or float(r["days_since_post"]) < float(data[k]["days_since_post"]):
            data[k] = r
    by_block = {}
    for k, r in data.items():
        y = value(r, a.outcome)
        if y is not None:
            by_block.setdefault(assign[k]["block"], []).append((k, y))
    complete = {b: v for b, v in by_block.items() if len(v) == 4}
    n_all = sum(len(v) for v in by_block.values())
    print(f"{a.network} · {a.outcome}: {n_all} posts measured, {len(complete)} complete blocks of 4")
    if not complete:
        print("No complete block yet: nothing to estimate."); return

    print(ground_result(complete, assign))
    # Sensitivity, pre-registered 30 Oct 2026 (PREREGISTRATION.md, Deviations): a make-up is posted
    # months after the rest of its block, so also report the estimate without those blocks.
    original = {r["block"] for k, r in assign.items() if 2 <= int(k) <= 33}
    mixed = {b for b, v in complete.items() if b in original and any(int(k) > 33 for k, _ in v)}
    if mixed:
        rest = {b: v for b, v in complete.items() if b not in mixed}
        print(f"Sensitivity, without the {len(mixed)} block(s) holding a make-up: "
              + (ground_result(rest, assign) if rest else "no complete block left"))

    link = {b: [(int(assign[k]["link_placement"] == "first_comment"), y) for k, y in v] for b, v in complete.items()}
    le = st.mean(block_effects(link, None))
    print(f"Link placement, first comment / body (not randomised, descriptive): ratio {math.exp(le):.2f}")


if __name__ == "__main__":
    main()
