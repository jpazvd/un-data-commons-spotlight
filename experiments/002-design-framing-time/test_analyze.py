"""Tests for analyze.py on synthetic data: a known design effect is recovered, no effect gives no adoption, and
the interim look shows no arm comparison. Synthetic only: nothing here is a real topic or a real outcome.

Run: python3 -m pytest experiments/002-design-framing-time/test_analyze.py
  or python3 experiments/002-design-framing-time/test_analyze.py
"""
import csv
import datetime as dt
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_assignment  # noqa: E402

REDRAWS = 200  # the registered number is 10,000; fewer keep the test fast
AS_OF = "2027-02-01"
POST_COLS = ["network", "spotlight", "version", "metricool_post_id", "scheduled_for", "published_at", "status", "note"]
OUTCOME_COLS = ["network", "spotlight", "version", "post_url", "published_at", "measured_at", "days_since_post",
                "impressions", "likes_or_reactions", "comments_or_replies", "reposts_or_shares", "quotes", "bookmarks",
                "follows", "profile_clicks", "link_clicks"]
RUN_IN = {"02": "2026-11-03", "03": "2026-11-05", "04": "2026-11-09"}


def write_csv(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def write_topics(path):
    """36 synthetic topics: 18 with a pace, 3 data-gap topics and 15 other standard topics."""
    tags = ["#EduSky", "#EconSky", "#PolicySky"]
    pace_frames, other_frames = ["T|L|G|D", "T|L|G", "T|L|D"], ["T|L|G|D", "T|L|G", "L|G|D", "T|G|D"]
    rows = []
    for i in range(36):
        if i < 18:
            pace, kind, frames = "1", "standard", pace_frames[i % 3]
        elif i < 21:
            pace, kind, frames = "0", "data gap", "D1|D2|D3"
        else:
            pace, kind, frames = "0", "standard", other_frames[i % 4]
        rows.append(dict(spotlight=f"{i + 5:02d}", pace=pace, kind=kind, frames=frames, feed_tag=tags[i % 3]))
    write_csv(path, ["spotlight", "pace", "kind", "frames", "feed_tag"], rows)


def outcome_row(rng, net, spotlight, version, published, days, mean_rate, impressions=None):
    """One measurement: a Poisson count split into the network's components."""
    measured = dt.datetime.fromisoformat(published) + dt.timedelta(days=days)
    row = dict(network=net, spotlight=spotlight, version=version, post_url=f"https://example.org/{net}/{version}",
               published_at=published, measured_at=measured.isoformat(), days_since_post=days)
    if net == "Bluesky":
        likes, reposts, replies, quotes = rng.multinomial(rng.poisson(mean_rate), [0.7, 0.15, 0.1, 0.05])
        row.update(likes_or_reactions=likes, reposts_or_shares=reposts, comments_or_replies=replies, quotes=quotes)
        return row
    imp = impressions or int(rng.lognormal(7, 0.3))
    total = rng.poisson(imp * mean_rate / 1000)
    row.update(impressions=imp, follows=rng.poisson(1), link_clicks=rng.poisson(3))
    if net == "X":
        likes, reposts, replies, quotes, bookmarks = rng.multinomial(total, [0.6, 0.15, 0.1, 0.05, 0.1])
        row.update(likes_or_reactions=likes, reposts_or_shares=reposts, comments_or_replies=replies, quotes=quotes,
                   bookmarks=bookmarks, profile_clicks=rng.poisson(5))
    else:
        reactions, comments = rng.multinomial(total, [0.85, 0.15])
        row.update(likes_or_reactions=reactions, comments_or_replies=comments, reposts_or_shares=rng.poisson(2))
    return row


def build(folder, ink, seed=7):
    """topics.csv, the registered draw, and simulated posts.csv and outcomes.csv. The only effect is Ink's, on X and
    LinkedIn (rate x ink); topics differ in level. One X post is also measured at 12 days, one LinkedIn post only at
    5 days, and one X post is deleted and corrected; run-in posts 02 to 04 are measured on every network."""
    folder = pathlib.Path(folder)
    write_topics(folder / "topics.csv")
    make_assignment.main(folder / "topics.csv", folder / "assignment.csv")
    rng = np.random.default_rng(seed)
    with open(folder / "assignment.csv", encoding="utf-8") as f:
        assignment = list(csv.DictReader(f))
    level = {}
    posts, outcomes = [], []
    first_x, first_li = None, None
    for r in assignment:
        if not r["date"]:
            continue
        net = r["network"]
        level.setdefault(r["spotlight"], float(np.exp(rng.normal(0, 0.3))))
        published = f"{r['date']}T{r['time_rome']}:00+01:00"
        posts.append(dict(network=net, spotlight=r["spotlight"], version=r["version"], metricool_post_id="",
                          scheduled_for=published, published_at=published, status="published", note=""))
        if net == "Bluesky":
            mean = 8 * level[r["spotlight"]]
            outcomes.append(outcome_row(rng, net, r["spotlight"], r["version"], published, 8, mean))
            continue
        effect = ink if r["design"] == "Ink" else 1.0
        rate = (25 if net == "X" else 30) * level[r["spotlight"]] * effect * float(np.exp(rng.normal(0, 0.15)))
        if net == "LinkedIn" and first_li is None:
            first_li = r
            outcomes.append(outcome_row(rng, net, r["spotlight"], r["version"], published, 5, rate))
            continue
        outcomes.append(outcome_row(rng, net, r["spotlight"], r["version"], published, 8, rate))
        if net == "X" and first_x is None:
            first_x = r
            outcomes.append(outcome_row(rng, net, r["spotlight"], r["version"], published, 12, rate))
            posts[-1]["status"] = "deleted"
            posts.append(dict(posts[-1], status="corrected", note="synthetic correction"))
    for s, day in RUN_IN.items():
        for net in ("X", "LinkedIn", "Bluesky"):
            published = f"{day}T13:00:00+01:00"
            outcomes.append(outcome_row(rng, net, s, s, published, 7.5, 20 if net != "Bluesky" else 6))
            posts.append(dict(network=net, spotlight=s, version=s, metricool_post_id="", scheduled_for=published,
                              published_at=published, status="published", note="run-in"))
    write_csv(folder / "posts.csv", POST_COLS, posts)
    write_csv(folder / "outcomes.csv", OUTCOME_COLS, outcomes)


def run(folder, *extra):
    cmd = [sys.executable, str(HERE / "analyze.py"), "--dir", str(folder), "--redraws", str(REDRAWS),
           "--as-of", AS_OF, "--json", str(pathlib.Path(folder) / "out.json"), *extra]
    done = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    assert done.returncode == 0, done.stderr
    return done.stdout, json.loads((pathlib.Path(folder) / "out.json").read_text())


class TestAnalyze(unittest.TestCase):
    def test_draw_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            write_topics(tmp / "topics.csv")
            rows = make_assignment.main(tmp / "topics.csv", None)
            self.assertEqual(list(tmp.iterdir()), [tmp / "topics.csv"])
            written = make_assignment.main(tmp / "topics.csv", tmp / "assignment.csv")
            self.assertEqual(rows, written)
            self.assertNotEqual(rows, make_assignment.main(tmp / "topics.csv", None, make_assignment.SEED + 1))

    def test_design_effect_recovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(tmp, ink=1.5)
            text, res = run(tmp)
            design = res["questions"]["design"]
            for key in ("Ink / D-dark", "Ink / D-light"):
                r = design["estimates"][key]
                self.assertTrue(1.3 < r["ratio"] < 1.75, (key, r))
                self.assertGreater(r["lo"], 1, (key, r))
                self.assertEqual(r["redraws"], REDRAWS)
            self.assertEqual(design["adopted"], "Ink")
            self.assertIn("Verdict: adopt Ink", text)
            m = res["measurement"]
            self.assertEqual(m["X"]["measured"], 108)
            self.assertEqual(m["X"]["outside_window"], 1)
            self.assertEqual(m["LinkedIn"]["measured_only_outside_window"], 1)
            self.assertEqual(m["LinkedIn"]["missing"], 1)
            self.assertEqual(m["X"]["flagged_posts"], 1)
            self.assertEqual([m[n]["run_in_measured"] for n in ("X", "LinkedIn", "Bluesky")], [3, 3, 3])
            self.assertEqual(res["models"]["X"]["posts"], 108)
            self.assertEqual(len(res["sensitivity"]["without_flagged"]["posts_left_out"]), 1)

    def test_no_effect_inconclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(tmp, ink=1.0)
            text, res = run(tmp)
            for q, v in res["questions"].items():
                self.assertIsNone(v["adopted"], (q, v["verdict"]))
                self.assertTrue(v["verdict"].startswith("inconclusive"), (q, v["verdict"]))
            self.assertNotIn("adopt", text)

    def test_interim_shows_no_arm_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            build(tmp, ink=1.5)
            text, res = run(tmp, "--interim")
            for word in ("Verdict", "adopt", "inconclusive", "90% interval", " / ", "Ink /", "/ D-dark"):
                self.assertNotIn(word, text)
            for key in ("questions", "models", "sensitivity"):
                self.assertNotIn(key, res)
            self.assertEqual(res["mode"], "interim")
            self.assertTrue(all(p["mdr"] and p["mdr"] > 1 for p in res["power"]))


if __name__ == "__main__":
    unittest.main()
