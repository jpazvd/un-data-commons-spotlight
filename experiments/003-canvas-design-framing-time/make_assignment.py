"""Experiment 003: the assignment of framings, designs, dates and slots, which is experiment 002's draw (seed 20261102)
with its design arms relabelled in place.

Experiment 002 (template D dark, template D light, Ink) stopped before its first post (its Deviations, 4 Nov 2026)
and experiment 003 takes over its topics, versions, dates and slots with the design arms template D dark,
template E light and template E dark (PREREGISTRATION.md). This script is 002's make_assignment.py with DESIGNS and
TEMPLATE changed and nothing else: the draw enumerates the designs by position (itertools.permutations(DESIGNS),
random.shuffle(list(DESIGNS))), so with the same seed every post keeps its topic, framing, date and slot and its
design label maps D-dark -> D-dark, D-light -> E-light, Ink -> E-dark. check_relabel() in this file verifies that
against 002's committed assignment.csv; analyze.py re-runs main() with other seeds for its randomisation test.

What follows is 002's docstring, which describes the draw.


Input:  topics.csv, the 36 selected topics, with columns spotlight (number), pace (1 or 0), kind ("standard" or
        "data gap"), frames (the framings the topic supports, e.g. "T|L|G|D") and feed_tag.
Output: assignment.csv, one row per post on X, LinkedIn and Bluesky. Run once, before the first post; the committed
        file is never edited (rows may only be added, for logged make-ups).

Design (PREREGISTRATION.md):
- Framings. A pace topic gets T and L, plus G or D (where both are possible, drawn without replacement from a
  seeded shuffle of equal numbers of G and D). A data-gap topic gets D1, D2 and D3. Any other topic gets its three
  framings, or, with four, three of them, the one left out drawn the same way from equal numbers of T, L, G and D,
  so that each is left out about equally often. The order of a topic's framings over the three periods is random.
- Designs. Each topic's three versions take the three designs, in one of the 6 orders over the periods; within each
  stratum (pace, no pace) each order is used three times, so every design appears 12 times in every period. Of
  2,000 seeded shuffles, the one that spreads framings most evenly over designs is kept.
- X: a topic's versions go out on the same day of each 10-day period (10 days apart); 6 days with 4 posts and 4
  with 3; slots 09:00, 13:00, 16:00, 20:00 Rome time, each used once on a 4-post day.
- LinkedIn: one version per topic, in blocks of three topics that hold each design once; one post a day at 11:00
  from 10 November to 9 December, skipping reserved own-post days.
- Bluesky: days 1 to 30 carry the day's first X banner 60 minutes later; days 31 to 60 carry remaining banners at
  12:00 in a seeded order, a topic's Bluesky posts at least 10 days apart; one day in each pair carries the feed tag.
"""
import csv
import datetime as dt
import itertools
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).parent
SEED = 20261102
START = dt.date(2026, 11, 10)
DESIGNS = ("D-dark", "E-light", "E-dark")  # 002's (D-dark, D-light, Ink) relabelled in place: see the docstring
TEMPLATE = {"D-dark": "templates/banner-D-dark.dc.html", "E-light": "templates/banner-E-light.dc.html",
            "E-dark": "templates/banner-E-dark.dc.html"}
SLOTS = ("09:00", "13:00", "16:00", "20:00")
LINKEDIN_RESERVED = {dt.date(2026, 11, 18), dt.date(2026, 11, 19), dt.date(2026, 11, 20)}
LINKEDIN_END = dt.date(2026, 12, 9)
BLUESKY_DAYS = 60


def choose_frames(topics, rng):
    """Three framings per topic, as in the docstring."""
    pace_third = ["G", "D"] * len(topics)
    rng.shuffle(pace_third)
    drops = ["T", "L", "G", "D"] * len(topics)
    rng.shuffle(drops)
    for t in topics:
        options = t["frames"].split("|")
        if t["kind"] == "data gap":
            chosen = ["D1", "D2", "D3"]
        elif t["pace"] == "1":
            rest = [f for f in options if f not in ("T", "L")]
            third = rest[0] if len(rest) == 1 else next(f for f in pace_third if f in rest)
            if len(rest) > 1:
                pace_third.remove(third)
            chosen = ["T", "L", third]
        elif len(options) == 3:
            chosen = options
        else:
            drop = next(f for f in drops if f in options)
            drops.remove(drop)
            chosen = [f for f in options if f != drop]
        assert len(chosen) == 3, t
        rng.shuffle(chosen)
        t["frames_by_period"] = chosen


def main(topics_path=HERE / "topics.csv", out_path=HERE / "assignment.csv", seed=SEED):
    """Draw the assignment and return its rows; write them to out_path unless it is None.

    The defaults give the registered draw. analyze.py calls main(topics_path, None, seed) with other seeds for its
    randomisation test.
    """
    rng = random.Random(seed)
    topics = list(csv.DictReader(open(topics_path, encoding="utf-8")))
    pace = [t for t in topics if t["pace"] == "1"]
    other = [t for t in topics if t["pace"] != "1"]
    assert len(pace) == 18 and len(other) == 18, "topics.csv needs 18 pace and 18 other topics"
    choose_frames(topics, rng)
    orders = list(itertools.permutations(DESIGNS))
    # Each stratum uses each order of designs three times (exact design-by-period balance). Among 2,000 seeded
    # shuffles, keep the one that spreads framings most evenly over designs (least squared deviation from the
    # expected count in each framing-by-design cell).
    best, best_score = None, None
    for _ in range(2000):
        trial = {}
        for group in (pace, other):
            seq = orders * 3
            rng.shuffle(seq)
            trial.update({t["spotlight"]: o for t, o in zip(group, seq)})
        cells = {}
        for t in topics:
            for f, d in zip(t["frames_by_period"], trial[t["spotlight"]]):
                cells[(f, d)] = cells.get((f, d), 0) + 1
        frames = {f for f, _ in cells}
        score = sum((cells.get((f, d), 0) - sum(cells.get((f, e), 0) for e in DESIGNS) / 3) ** 2
                    for f in frames for d in DESIGNS)
        if best_score is None or score < best_score:
            best, best_score = trial, score
    for t in topics:
        t["designs_by_period"] = best[t["spotlight"]]

    all_t = pace + other
    rng.shuffle(all_t)
    counts = [4] * 6 + [3] * 4
    rng.shuffle(counts)
    day_of, k = {}, 0
    for day, c in enumerate(counts, 1):
        for t in all_t[k:k + c]:
            day_of[t["spotlight"]] = day
        k += c
    posts = []
    for period in (1, 2, 3):
        for day in range(1, 11):
            today = [t for t in all_t if day_of[t["spotlight"]] == day]
            slots = rng.sample(SLOTS, len(today))
            date = START + dt.timedelta(days=(period - 1) * 10 + day - 1)
            for t, s in zip(today, slots):
                frame, design = t["frames_by_period"][period - 1], t["designs_by_period"][period - 1]
                posts.append(dict(network="X", spotlight=t["spotlight"], version=f"{t['spotlight']}-{frame}",
                                  frame=frame, design=design, template=TEMPLATE[design], pace=t["pace"],
                                  kind=t["kind"], period=period, date=date.isoformat(), time_rome=s, slot=s))

    # LinkedIn: blocks of three topics, each block holding each design once.
    order_t = all_t[:]
    rng.shuffle(order_t)
    queue = []
    for b in range(0, len(order_t), 3):
        block = order_t[b:b + 3]
        designs = list(DESIGNS)
        rng.shuffle(designs)
        for t, d in zip(block, designs):
            p = t["designs_by_period"].index(d)
            queue.append((b // 3 + 1, t, t["frames_by_period"][p], d))
    day = START
    for pos, (b, t, frame, design) in enumerate(queue, 1):
        while day in LINKEDIN_RESERVED:
            day += dt.timedelta(days=1)
        posted = day <= LINKEDIN_END
        posts.append(dict(network="LinkedIn", spotlight=t["spotlight"], version=f"{t['spotlight']}-{frame}",
                          frame=frame, design=design, template=TEMPLATE[design], pace=t["pace"], kind=t["kind"],
                          linkedin_block=b, linkedin_position=pos, date=day.isoformat() if posted else "",
                          time_rome="11:00" if posted else ""))
        if posted:
            day += dt.timedelta(days=1)

    # Bluesky.
    x_posts = [p for p in posts if p["network"] == "X"]
    feed = {t["spotlight"]: t["feed_tag"] for t in all_t}
    blue, last_day, used = [], {}, set()
    for d in range(30):
        date = (START + dt.timedelta(days=d)).isoformat()
        first = min((p for p in x_posts if p["date"] == date), key=lambda p: p["time_rome"])
        h, m = map(int, first["time_rome"].split(":"))
        blue.append(dict(first, network="Bluesky", time_rome=f"{h + 1:02d}:{m:02d}", bluesky_day=d + 1))
        used.add(first["version"]); last_day[first["spotlight"]] = d
    remaining = [p for p in x_posts if p["version"] not in used]
    rng.shuffle(remaining)
    for d in range(30, BLUESKY_DAYS):
        pick = next(p for p in remaining if d - last_day.get(p["spotlight"], -99) >= 10)
        remaining.remove(pick)
        date = (START + dt.timedelta(days=d)).isoformat()
        blue.append(dict(pick, network="Bluesky", date=date, time_rome="12:00", period="", slot="",
                         bluesky_day=d + 1))
        last_day[pick["spotlight"]] = d
    for i in range(0, BLUESKY_DAYS, 2):
        on = rng.randrange(2)
        for j in (0, 1):
            blue[i + j]["feed_tag_on"] = int(j == on)
            blue[i + j]["feed_tag"] = feed[blue[i + j]["spotlight"]] if j == on else ""
            blue[i + j]["bluesky_pair"] = i // 2 + 1
    posts += blue

    cols = ["network", "spotlight", "version", "frame", "design", "template", "pace", "kind", "date", "time_rome",
            "period", "slot", "linkedin_block", "linkedin_position", "bluesky_day", "bluesky_pair",
            "feed_tag_on", "feed_tag"]
    posts.sort(key=lambda p: (["X", "LinkedIn", "Bluesky"].index(p["network"]), p["date"] or "9999",
                              p["time_rome"], p["spotlight"]))
    if out_path is not None:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(posts)
    return posts


RELABEL = {"D-dark": "D-dark", "D-light": "E-light", "Ink": "E-dark"}


def check_relabel(rows, path_002=HERE.parent / "002-design-framing-time" / "assignment.csv"):
    """True when rows are 002's committed assignment with its designs relabelled and nothing else changed."""
    old = list(csv.DictReader(open(path_002, encoding="utf-8")))
    if len(old) != len(rows):
        return False
    for a, b in zip(old, rows):
        want = dict(a, design=RELABEL[a["design"]], template=TEMPLATE[RELABEL[a["design"]]])
        if any(str(b.get(k, "")) != want[k] for k in want):
            return False
    return True


if __name__ == "__main__":
    args = sys.argv[1:]
    rows = main(*(pathlib.Path(a) for a in args)) if args else main()
    print("relabel of 002's draw:", "verified" if check_relabel(rows) else "DIFFERS")
