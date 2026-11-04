"""Words and chart for one experiment 002 version, from its stats.json only.

content(stats, topic_meta, spotlight, design) -> dict with headline candidates, signal, evidence, aria text,
captions and the chart SVG. Every number is read from stats.json (scripts/spotlight002.py), never typed.
Voice (post craft rules): first person where there is an "I", factual and plain, no em-dashes, no hype; a gap
describes groups and never blames them; a data headline describes the data, never a statistical office.

Review round 1 (2 Nov 2026, JP's comments on the review page): every headline names what is measured
(names_construct); a pace headline says which way the indicator has to move ("needs coverage to rise ...") and, where
it fits, how many times its pace so far; an evidence line gives each value with its own year ("from 26.3% in 2000 to
36.9% in 2024"); the series line is "UN Data Commons Spotlight" with no number; the data line names the series code
and the extraction date.
"""
import banner002 as B
import spotlight002 as S

REPO = "github.com/jpazvd/un-data-commons-spotlight"
GOAL = {  # (goal phrase for the house-rule headline, object of the verb)
    "water": ("Safely managed drinking water for all", "coverage"),
    "sanitation": ("Safely managed sanitation for all", "coverage"),
    "school_completion": ("Every child completing primary school", "the rate"),
    "pre_primary": ("Every child in organized learning before primary", "participation"),
    "child_marriage_18": ("Ending child marriage", "the share"),
    "child_marriage_15": ("Ending marriage before 15", "the share"),
}
GOAL_SHORT = {"water": "Safely managed water for all", "sanitation": "Safely managed sanitation for all",
              "school_completion": "Primary completion for all", "pre_primary": "Pre-primary participation for all",
              "child_marriage_18": "Ending child marriage", "child_marriage_15": "Ending marriage before 15"}


def names_construct(headline, family):
    """True if the headline names what is measured: the indicator's short or long name, or its goal phrase."""
    fam, h = S.FAMILY[family], headline.lower()
    keys = [fam["short"], fam["what"], GOAL.get(family, ("",))[0], GOAL_SHORT.get(family, "")]
    return any(k and k.lower() in h for k in keys)


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def day(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {MONTHS[m - 1]} {y}"


def source_of(st, meta):
    """(source text, database, code label) for the data the chart shows."""
    f, k = st["frame"], st["kind"]
    ind = (meta.get("retrieval") or {}).get("indicator") or {}
    codes = ind.get("sdg_series_codes") or []
    if f == "G" and k in ("country_gaps", "groups", "groups_compared") and ind.get("breakdown_variables"):
        var = ind["breakdown_variables"][0]
        code = var.split("/")[-1].split(".")[0]
        if st.get("breakdown_source") and st["breakdown_source"] != "UN SDG Global Database":
            return st["breakdown_source"], "UN System Data Commons", f"indicator {code}"
        return st["custodian"], "UN SDG Global Database", f"series {code}"
    return st["custodian"], "UN SDG Global Database", (f"series {', '.join(codes)}" if codes else None)


def short_place(name):
    d = S_dcid(name)
    return S.SHORT.get(d, name)


SDG_TAG = {"1": "#SDG1", "2": "#SDG2", "3": "#SDG3", "4": "#SDG4", "5": "#SDG5", "6": "#SDG6", "8": "#SDG8",
           "16": "#SDG16"}


def S_dcid(name):
    for d, n in {**S.SDG_REGIONS, **S.GROUPINGS}.items():
        if n.lower() == name.lower() or name.lower().startswith(n.lower()):
            return d
    return name


def cap(s):
    return s[:1].upper() + s[1:]


def per_year(x, unit):
    if abs(x) < 0.05:
        return "under 0.1 points a year" if unit == "%" else f"under 0.1{unit} a year"
    return f"{B.num(abs(x))} points a year" if unit == "%" else f"{B.num(abs(x))}{unit} a year"


def pts(x, unit, nd=1):
    return f"{B.num(abs(x), nd)} points" if unit == "%" else f"{B.num(abs(x), nd)}{unit}"


def in_place(place):
    return "Worldwide" if place == "World" else f"In {place}"


def place_name(p):
    return "the world" if p == "World" else p


def content(st, meta, nn, design, h=None):
    f, k, u = st["frame"], st["kind"], st["unit"]
    fam = S.FAMILY[st["family"]]
    dec = fam.get("decimals", 1)
    _fmt = B.fmt
    B_fmt = lambda v, unit, nd=None: _fmt(v, unit, dec if nd is None else nd)
    pts_ = lambda x, unit: pts(x, unit, dec)
    short, what = fam["short"], fam["what"]
    better = st["better"]
    style = B.STYLES[design]
    h = h or B.CHART_H[design]
    sdg = meta["sdg_indicator"]
    src, db, code = source_of(st, meta)
    extracted = day(meta["retrieved_on"])
    c = {"series": "UN Data Commons Spotlight", "indicator": f"SDG {sdg} · {short}",
         "data_line": f"Data: {src} via {db}" + (f", {code}" if code else "") + f", extracted {extracted}",
         "source": src, "db": db, "code": code, "extracted": extracted,
         "title": f"Spotlight {nn:02d}-{f}"}
    tfig = tfig_short = None  # the "what it would take" line every caption keeps where a target gives one

    if k == "pace":
        goal, obj = GOAL[st["family"]]
        place = st["place"]
        verb = "raising" if better == "higher" else "cutting"
        rise = "rise" if better == "higher" else "fall"
        rising = "rising" if better == "higher" else "falling"
        req, obs = st["required_per_year"], st["observed_per_year"]
        (y0, v0), (y1, v1) = (st["first"]["year"], st["first"]["value"]), (st["last"]["year"], st["last"]["value"])
        ty, tv = st["target"]["year"], st["target"]["value"]
        sig = per_year(req, u)
        lead = goal if place == "World" else f"In {place}, {goal[0].lower() + goal[1:]}"
        lead_s = goal if place == "World" else f"In {S.SHORT.get(S_dcid(place), place)}, {goal[0].lower() + goal[1:]}"
        obj_txt = f" {obj}"
        gs = GOAL_SHORT[st["family"]]
        gsl = gs if place == "World" else f"In {short_place(place)}, {gs[0].lower() + gs[1:]}"
        moved = "risen" if v1 > v0 else "fallen"
        if st["trend"] == "towards target" and abs(req) <= abs(obs) * 1.05:
            c["headlines"] = [f"{lead} by {ty} needs {obj} to keep {rising} {sig}, about its pace since {y0}",
                              f"{lead_s} by {ty} needs {obj} to keep {rising} {sig}, about its pace since {y0}",
                              f"{gsl} by {ty} needs {obj} to keep {rising} {sig}, about its pace so far",
                              f"{gsl} by {ty} needs {obj} to keep {rising} {sig}"]
            c["signal"] = sig
            c["evidence"] = f"So far it has {moved} {per_year(obs, u)}, from {B_fmt(v0, u)} in {y0} to {B_fmt(v1, u)} in {y1}."
            c["evidence_alt"] = f"It has {moved} {per_year(obs, u)}, from {B_fmt(v0, u)} in {y0} to {B_fmt(v1, u)} in {y1}."
        elif st["trend"] == "towards target":
            mult = st.get("required_over_observed")
            faster = (f", {B.num(mult)} times its pace since {y0}" if mult and mult >= 1.5 else
                      f", faster than since {y0}" if mult else "")
            c["headlines"] = ([f"{x}{faster}" for x in (f"{lead} by {ty} needs {obj} to {rise} {sig}",
                                                        f"{lead_s} by {ty} needs {obj} to {rise} {sig}",
                                                        f"{gsl} by {ty} needs {obj} to {rise} {sig}")] if faster else []) + [
                f"{lead} by {ty} needs {obj} to {rise} {sig}",
                f"{lead_s} by {ty} needs {obj} to {rise} {sig}",
                f"{gsl} by {ty} needs {obj} to {rise} {sig}",
                f"{gsl} by {ty} needs a {rise} of {sig}"]
            c["signal"] = sig
            c["evidence"] = f"So far it has {moved} {per_year(obs, u)}, from {B_fmt(v0, u)} in {y0} to {B_fmt(v1, u)} in {y1}."
            c["evidence_alt"] = f"It has {moved} {per_year(obs, u)}, from {B_fmt(v0, u)} in {y0} to {B_fmt(v1, u)} in {y1}."
        else:
            moved = {"flat": "has not moved", "away from target": "has moved away from the target",
                     "target met": "has already met the target"}[st["trend"]]
            c["headlines"] = [f"{cap(short)} {'in ' + place if place != 'World' else 'worldwide'} {moved} since {y0}"]
            c["signal"] = None
            c["evidence"] = f"From {B_fmt(v0, u)} in {y0} to {B_fmt(v1, u)} in {y1}."
        tfig = f"{lead} by {ty} needs {obj} to {rise} {sig}, against {per_year(obs, u)} since {y0}."
        tfig_short = f"{gsl} by {ty} needs {obj} to {rise} {sig}."
        proj = st["at_current_pace"]
        if st["target"].get("kind") == "universal":
            proj = min(proj, 100.0)
        c["svg"] = B.line_chart(style, h, [{"pts": st["series"], "role": "lead"}], u, target={
            "year": ty, "value": tv, "proj": proj, "last": (y1, v1),
            "proj_label": f"≈{B_fmt(proj, u)} at {B.num(abs(obs))} a year",
            "target_label": f"{B_fmt(tv, u, 0)} at {B.num(abs(req))} a year"},
            aria=(f"{cap(what)}, {place_name(place)}: {B_fmt(v0, u)} in {y0}, {B_fmt(v1, u)} in {y1}. At that pace "
                  f"about {B_fmt(proj, u)} in {ty}; reaching {B_fmt(tv, u, 0)} needs {per_year(req, u)}."))
        c["method"] = f"Method: linear, points per year, {y0} to {y1} for the trend and {y1} to {ty} for the target."
        c["note"] = ("A statistician's note: both paces are straight lines, the observed one over the whole series and the "
                     "required one from the latest estimate to the target. The multiple between them changes with the base "
                     "year; the required pace does not.")
        c["question"] = f"Where has {short} moved at anything like {sig}, and what made it possible?"
        if st["required_over_observed"]:
            c["detail"] = (f"That is {B.num(st['required_over_observed'])} times the pace of the last {y1 - y0} years.")

    elif k == "pace_compared":
        goal, obj = GOAL[st["family"]]
        rows = st["places"]
        lead_row = next(r for r in rows if r["dcid"] == st["lead"])
        ty, tv = st["target"]["year"], st["target"]["value"]
        rise = "rise" if better == "higher" else "fall"
        gs = GOAL_SHORT[st["family"]]
        sig = per_year(lead_row["required_per_year"], u)
        nm = S.SDG_REGIONS.get(lead_row["dcid"], S.GROUPINGS.get(lead_row["dcid"], lead_row["place"]))
        lp = lead_row["place"]
        c["headlines"] = [f"{goal} by {ty} needs {obj} in {nm} to {rise} {sig}",
                          f"{goal} by {ty} needs {obj} in {lp} to {rise} {sig}",
                          f"{gs} by {ty} needs {obj} in {lp} to {rise} {sig}",
                          f"{gs} by {ty} needs a {rise} of {sig} in {lp}"]
        if st["place_type"] == "groupings":  # the three groups together, so no headline repeats a one-group topic
            reqs = sorted(abs(r["required_per_year"]) for r in rows if r["dcid"] != "Earth")
            sig = f"{B.num(reqs[0])} to {B.num(reqs[-1])} points a year"
            c["headlines"] = [f"{goal} by {ty} needs {obj} to {rise} {sig} in LDCs, LLDCs and SIDS",
                              f"{gs} by {ty} needs {obj} to {rise} {sig} in LDCs, LLDCs and SIDS",
                              f"{gs} by {ty} needs a {rise} of {sig} in LDCs, LLDCs and SIDS",
                              f"{gs} by {ty} needs a {rise} of {sig} in LDCs, LLDCs, SIDS",
                              f"{gs} by {ty} needs a {rise} of {sig}"]
        c["signal"] = sig
        y0, y1 = lead_row["first"]["year"], lead_row["last"]["year"]
        v0_, v1_ = lead_row["first"]["value"], lead_row["last"]["value"]
        moved = "risen" if v1_ > v0_ else "fallen"
        c["evidence"] = (f"In {lp} it has {moved} {per_year(lead_row['observed_per_year'], u)}, "
                         f"from {B_fmt(v0_, u)} in {y0} to {B_fmt(v1_, u)} in {y1}.")
        c["evidence_alt"] = (f"{short_place(lp)}: {'up' if v1_ > v0_ else 'down'} {per_year(lead_row['observed_per_year'], u)}, "
                             f"from {B_fmt(v0_, u)} in {y0} to {B_fmt(v1_, u)} in {y1}.")
        tfig = f"{goal} by {ty} needs {obj} in {nm} to {rise} {sig}, against {per_year(lead_row['observed_per_year'], u)} since {y0}."
        tfig_short = f"{gs} by {ty} needs {obj} in {lp} to {rise} {sig}."
        if st["place_type"] == "groupings":
            tfig = f"{goal} by {ty} needs {obj} to {rise} {sig} in LDCs, LLDCs and SIDS."
            tfig_short = f"{gs} by {ty} needs {obj} to {rise} {sig} in LDCs, LLDCs and SIDS."
        sign = 1 if better == "higher" else -1
        data = sorted(rows, key=lambda r: -sign * r["required_per_year"])
        c["svg"] = B.hbars(style, h, [{"label": r["place"], "value": max(0, sign * r["observed_per_year"]),
                                        "value2": max(0, sign * r["required_per_year"]),
                                        "role": "lead" if r["dcid"] == st["lead"] else "other"} for r in data],
                           u, pair=True, legend=("pace since the base year", f"pace needed to {ty}"),
                           value_fmt=lambda v: B.num(v),
                           aria="; ".join(f"{r['place']}: {B.num(abs(r['observed_per_year']))} a year observed, "
                                          f"{B.num(abs(r['required_per_year']))} needed" for r in data))
        c["method"] = (f"Method: linear, points per year, from each place's first published year to its latest, and from "
                       f"there to {ty}; published aggregates.")
        c["note"] = ("A statistician's note: these are the custodian's published aggregates, not averages I computed. The "
                     "paces are straight lines, which is simple on purpose.")
        c["question"] = (f"Which {short_place(nm)} have moved {short} fastest, and how?" if lead_row["dcid"] in S.GROUPINGS
                         else f"Which countries in {nm} have moved {short} fastest, and how?")

    elif k == "level":
        place, y, v = st["place"], st["last"]["year"], st["last"]["value"]
        val = B_fmt(v, u)
        wp = "Worldwide" if place == "World" else place
        if u == "%":
            c["headlines"] = [f"{wp} in {y}: {val} of {what}", f"{cap(short)}, {place_name(place)}: {val} in {y}"]
        else:
            c["headlines"] = [f"{wp} in {y}: {B.num(v)} {what}", f"{cap(short)}, {place_name(place)}: {val} in {y}"]
        c["signal"] = val if u == "%" else B.num(v)
        ranked = st["ranked"]
        ys = [r[1] for r in ranked]
        c["evidence"] = (f"{len(ranked)} countries and areas, latest values from {min(ys)} to {max(ys)}." if min(ys) != max(ys)
                         else f"{len(ranked)} countries and areas, all with values for {max(ys)}.")
        vals = [r[2] for r in ranked]
        c["svg"] = B.ranked_columns(style, h, vals, ref=(f"{short_place(place)}: {val}", v), unit=u,
                                    notes=[(0.0, None, f"{ranked[0][0]} {B_fmt(ranked[0][2], u)}", "ink", "start")],
                                    aria=f"{len(vals)} countries ranked, from {ranked[0][0]} {B_fmt(ranked[0][2], u)} to "
                                         f"{ranked[-1][0]} {B_fmt(ranked[-1][2], u)}; {place} {val} in {y}.")
        c["method"] = f"Method: published aggregate for {y}; countries at their latest year."
        c["note"] = (("A statistician's note: the line is the custodian's published aggregate; the bars are each country's "
                      f"value for {max(ys)}, so they share a year. The aggregate is the custodian's own, not an average of "
                      "the bars.") if min(ys) == max(ys) else
                     ("A statistician's note: the line is the custodian's published aggregate; the bars are each country's "
                      "latest value, so they come from different years and are not directly comparable."))
        c["question"] = f"What has moved {short} most in the countries you work with?"

    elif k == "level_compared":
        y, rows = st["year"], st["places"]
        world = next((r for r in rows if r["dcid"] == "Earth"), None)
        sign = 1 if better == "higher" else -1
        others = sorted([r for r in rows if r["dcid"] != "Earth"], key=lambda r: -r["value"])
        if world:
            val = B_fmt(world["value"], u)
            c["headlines"] = ([f"Worldwide in {y}: {val} of {what}"] if u == "%" else
                              [f"Worldwide in {y}: {B.num(world['value'])} {what}"]) + [f"{cap(short)} worldwide: {val} in {y}"]
            c["signal"] = val if u == "%" else B.num(world["value"])
        else:
            top = others[0]
            c["headlines"] = [f"{cap(short)}: {B_fmt(top['value'], u)} in {top['place']}, {y}"]
            c["signal"] = B_fmt(top["value"], u)
        c["evidence"] = f"From {B_fmt(others[0]['value'], u)} in {others[0]['place']} to {B_fmt(others[-1]['value'], u)} in {others[-1]['place']}."
        bars = others + ([world] if world else [])
        c["svg"] = B.hbars(style, h, [{"label": r["place"], "value": r["value"],
                                        "role": "world" if r["dcid"] == "Earth" else "lead"} for r in bars], u,
                           value_fmt=lambda v: B_fmt(v, u),
                           aria="; ".join(f"{r['place']} {B_fmt(r['value'], u)}" for r in bars) + f", {y}.")
        c["method"] = f"Method: published aggregates, {y}."
        c["note"] = "A statistician's note: these are the custodian's published aggregates for each group, not averages I computed."
        c["question"] = (f"What would it take to bring {short} in {others[-1 if sign > 0 else 0]['place']} "
                         f"{'up' if sign > 0 else 'down'} to the World level?")

    elif k == "trend":
        place = st["place"]
        (y0, v0), (y1, v1) = (st["first"]["year"], st["first"]["value"]), (st["last"]["year"], st["last"]["value"])
        ch = round(round(v1, dec) - round(v0, dec), dec)
        word = "risen" if ch > 0 else "fallen" if ch < 0 else "stayed at"
        sig = pts_(ch, u)
        where = "" if place == "World" else f" in {place}"
        if abs(st["per_year"]) < 0.05 or ch == 0:
            sig = f"{B_fmt(v1, u)} in {y1}"
            c["headlines"] = [f"Since {y0}, {short}{where} has barely moved: {sig}",
                              f"{cap(short)}{where} has barely moved since {y0}: {sig}"]
            c["signal"] = sig
        elif ch == 0:
            c["headlines"] = [f"Since {y0}, {short}{where} has not moved"]
            c["signal"] = None
        else:
            ws = "" if place == "World" else f" in {S.SHORT.get(S_dcid(place), place)}"
            updown = "up" if ch > 0 else "down"
            c["headlines"] = [f"Since {y0}, {short}{where} has {word} {sig}", f"{cap(short)}{where}: {updown} {sig} since {y0}",
                              f"{cap(short)}{ws}: {updown} {sig} since {y0}"]
            c["signal"] = sig
        c["evidence"] = f"From {B_fmt(v0, u)} in {y0} to {B_fmt(v1, u)} in {y1}: {per_year(st['per_year'], u)}."
        c["evidence_alt"] = f"{B_fmt(v0, u)} in {y0}, {B_fmt(v1, u)} in {y1}: {per_year(st['per_year'], u)}."
        c["svg"] = B.line_chart(style, h, [{"pts": st["series"], "role": "lead"}], u,
                                aria=f"{cap(what)}, {place_name(place)}: {B_fmt(v0, u)} in {y0} to {B_fmt(v1, u)} in {y1}.")
        c["method"] = f"Method: published series, {y0} to {y1}; change in {'percentage points' if u == '%' else 'the indicator units'}."
        c["note"] = ("A statistician's note: these are the custodian's published series. A single year can be revised when new data come in, so I read the direction over the whole period rather than year to year.")
        c["question"] = f"What has moved {short} most in the places you work in, and how do you know?"

    elif k == "trend_compared":
        y0, y1, rows = st["from"], st["to"], st["places"]
        lead = next(r for r in rows if r["dcid"] == st["lead"])
        nm = S.SDG_REGIONS.get(lead["dcid"], S.GROUPINGS.get(lead["dcid"], lead["place"]))
        lch = round(round(lead["last"], dec) - round(lead["first"], dec), dec)
        word = "raised" if lch > 0 else "cut"
        has = "have" if lead["dcid"] in S.GROUPINGS else "has"
        sig = pts_(lch, u)
        grp = "region" if st["place_type"] == "regions_compared" else "group"
        c["headlines"] = [f"Since {y0}, {nm} {has} {word} {short} by {sig}, the most of any {grp}",
                          f"{nm}: {short} {'up' if lch > 0 else 'down'} {sig} since {y0}",
                          f"{lead['place']}: {short} {'up' if lch > 0 else 'down'} {sig} since {y0}"]
        if st["place_type"] == "groupings":
            g3 = [r for r in rows if r["dcid"] != "Earth"]
            chs = [(r["place"], round(round(r["last"], dec) - round(r["first"], dec), dec)) for r in g3]
            ups = all(x > 0 for _, x in chs); downs = all(x < 0 for _, x in chs)
            if ups or downs:
                verb_ = "risen" if ups else "fallen"
                sig = f"{B.num(abs(chs[0][1]), dec)} points in {chs[0][0]}"
                b_, c_ = f"{B.num(abs(chs[1][1]), dec)} in {chs[1][0]}", f"{B.num(abs(chs[2][1]), dec)} in {chs[2][0]}"
                c["headlines"] = [f"Since {y0}, {short} has {verb_} {sig}, {b_} and {c_}",
                                  f"{cap(short)}: {'up' if ups else 'down'} {sig}, {b_} and {c_} since {y0}",
                                  f"{cap(short)} since {y0}: {sig}, {b_}, {c_}"]
        c["signal"] = sig
        world = next((r for r in rows if r["dcid"] == "Earth"), None)
        c["evidence"] = (f"{lead['place']}: from {B_fmt(lead['first'], u)} in {y0} to {B_fmt(lead['last'], u)} in {y1}."
                         + (f" World: from {B_fmt(world['first'], u)} to {B_fmt(world['last'], u)}." if world else ""))
        c["evidence_alt"] = (f"{lead['place']}: {B_fmt(lead['first'], u)} in {y0}, {B_fmt(lead['last'], u)} in {y1}."
                             + (f" World: {B_fmt(world['first'], u)} to {B_fmt(world['last'], u)}." if world else ""))
        lines = [{"pts": r["series"], "role": "lead" if r["dcid"] == st["lead"] else "world" if r["dcid"] == "Earth" else "other",
                  "label": None} for r in rows]
        c["svg"] = B.line_chart(style, h, lines, u, labels=True,
                                aria="; ".join(f"{r['place']}: {B_fmt(r['first'], u)} in {y0} to {B_fmt(r['last'], u)} in {y1}" for r in rows))
        lo_ = st.get("left_out") or []
        c["method"] = (f"Method: published aggregates, {y0} to {y1}" +
                       (f"; left out because their series start later: {', '.join(lo_)}." if lo_ else "."))
        c["note"] = "A statistician's note: these are the custodian's published aggregates, not averages I computed from country values."
        c["question"] = f"What lies behind the change in {short} in {nm}, and what could others learn from it?"

    elif k in ("groups", "groups_compared"):
        a, b = st["groups"]
        wa, wb = S.group_word(st["family"], a), S.group_word(st["family"], b)
        prep = "in" if st["breakdown"] == "location" else "for"
        if k == "groups":
            place, y, va, vb = st["place"], st["year"], st[a], st[b]
            diff = abs(va - vb)
            sig = pts(diff, u) + " apart"
            where = "worldwide" if st["dcid"] == "Earth" else f"in {S.SDG_REGIONS.get(st['dcid'], S.GROUPINGS.get(st['dcid'], place))}"
            pl = "Worldwide" if st["dcid"] == "Earth" else short_place(S.SDG_REGIONS.get(st['dcid'], S.GROUPINGS.get(st['dcid'], place)))
            c["headlines"] = [f"{cap(short)} {where}: {B_fmt(va, u)} {prep} {wa}, {B_fmt(vb, u)} {prep} {wb}",
                              f"{cap(short)}, {pl}: {B_fmt(va, u)} {prep} {wa}, {B_fmt(vb, u)} {prep} {wb}",
                              f"{cap(short)}: {B_fmt(va, u)} {prep} {wa}, {B_fmt(vb, u)} {prep} {wb}"]
            c["signal"] = f"{B_fmt(va, u)} {prep} {wa}"
            c["evidence"] = f"Published aggregates for {y}: a gap of {pts(diff, u)}."
            c["evidence_alt"] = f"{pl}, published aggregates for {y}: a gap of {pts(diff, u)}."
            rows = [{"label": cap(wa), "value": va, "role": "lead"}, {"label": cap(wb), "value": vb, "role": "lead"}]
            c["svg"] = B.hbars(style, min(h, 170), rows, u, aria=f"{cap(short)} {where}, {y}: {wa} {B_fmt(va, u)}, {wb} {B_fmt(vb, u)}.")
        else:
            rows = st["places"]
            non_world = [r for r in rows if r["dcid"] != "Earth"]
            widest = max(non_world, key=lambda r: abs(r[a] - r[b]))
            nm = S.SDG_REGIONS.get(widest["dcid"], S.GROUPINGS.get(widest["dcid"], widest["place"]))
            y = widest["year"]
            diff = abs(widest[a] - widest[b])
            sig = pts(diff, u)
            c["headlines"] = [f"The widest gap in {short} between {wa} and {wb} is in {nm}: {sig}",
                              f"{cap(short)}: a {sig.replace(' points', '-point')} gap between {wa} and {wb} in {nm}",
                              f"{cap(short)}: the widest gap between {wa} and {wb} is {sig}, in {widest['place']}",
                              f"Widest gap in {short}: {sig}, in {widest['place']}"]
            c["signal"] = sig
            c["evidence"] = f"{nm}: {B_fmt(widest[a], u)} {prep} {wa}, {B_fmt(widest[b], u)} {prep} {wb}, {y}."
            data = sorted(rows, key=lambda r: -abs(r[a] - r[b]))
            c["svg"] = B.hbars(style, h, [{"label": r["place"], "value": r[a], "value2": r[b],
                                            "role": "lead" if r["dcid"] == widest["dcid"] else "other"} for r in data],
                               u, pair=True, legend=(cap(wa), cap(wb)),
                               aria="; ".join(f"{r['place']}: {wa} {B_fmt(r[a], u)}, {wb} {B_fmt(r[b], u)} ({r['year']})" for r in data))
        years = sorted({r["year"] for r in st["places"]}) if k == "groups_compared" else [y]
        c["method"] = (f"Method: published aggregates by group, latest year with both groups ({y})." if len(years) == 1 else
                       f"Method: published aggregates by group, each region's latest year with both groups "
                       f"({years[0]} to {years[-1]}).")
        c["note"] = "A statistician's note: these are the custodian's published aggregates by group, not averages I computed from country values."
        c["question"] = f"Where have you seen the gap in {short} between {wa} and {wb} close, and how was it measured?"

    elif k == "country_gaps":
        a, b = st["groups"]
        wa, wb = S.group_word(st["family"], a), S.group_word(st["family"], b)
        n, na, nb = st["n"], st["n_a_worse"], st["n_b_worse"]
        worse_word = "higher" if better == "lower" else "lower"
        if na >= nb:
            k_, w1, w2 = na, wa, wb
        else:
            k_, w1, w2 = nb, wb, wa
        place = st["place"]
        where = "" if place == "World" else f" in {place}"
        grp_ = S_dcid(place) in S.GROUPINGS
        unit_ = short_place(place) if grp_ else "countries"
        sig = f"all {n} {unit_}" if k_ == n else f"{k_} of {n} {unit_}"
        if grp_:
            where = ""
        wshort = {"wealth": ("for the poorest fifth", "for the richest fifth"), "location": ("in rural areas", "in urban areas"),
                  "sex": (f"for {wa}", f"for {wb}")}[st["breakdown"]][0 if na >= nb else 1]
        cmp_ = {"wealth": ("among the poorest fifth than the richest", "among the richest fifth than the poorest"),
                "location": ("in rural than in urban areas", "in urban than in rural areas"),
                "sex": (f"among {wa} than {wb}", f"among {wb} than {wa}")}[st["breakdown"]][0 if na >= nb else 1]
        where_s = "" if place == "World" or grp_ else f" in {S.SHORT.get(S_dcid(place), place)}"
        c["headlines"] = [f"In {sig}{where}, {short} was {worse_word} {cmp_} in the latest survey",
                          f"In {sig}{where}, {short} was {worse_word} {cmp_}",
                          f"{cap(short)} was {worse_word} {cmp_} in {sig}{where_s}",
                          f"{cap(short)} was {worse_word} {wshort} in {sig}{where_s}",
                          f"{cap(short)} was {worse_word} {wshort} in {sig}"]
        c["signal"] = sig
        c["evidence"] = (f"Latest surveys with both groups, {st['years'][0]} to {st['years'][1]}; "
                         f"median gap {pts(st['median_gap'], u)}.")
        c["evidence_alt"] = (f"{place}: same-survey comparisons, {st['years'][0]} to {st['years'][1]}; "
                             f"median gap {pts(st['median_gap'], u)}." if place != "World" else None)
        c["svg"] = B.gap_columns(style, h, st["gaps"], wa, wb, unit=u, nd=dec,
                                 aria=f"Gap between {wa} and {wb} in {n} countries{where}, ranked; {na} with {wa} {worse_word}, {nb} with {wb} {worse_word}.")
        c["method"] = (f"Method: latest year per country with both groups from the same survey ({st['years'][0]} to "
                       f"{st['years'][1]}); counts, not an average.")
        c["note"] = ("A statistician's note: each country is compared with itself, within one survey, so this does not rest on "
                     "comparing countries measured in different years. It tells you where the gap points, not how large it is: "
                     f"in {st['n_gap_under_1']} of the {n} countries the two groups are less than "
                     f"{'one point' if u == '%' else '1' + u} apart.")
        c["question"] = f"Where have you seen the gap in {short} between {wa} and {wb} close, and how was it measured?"

    elif k == "places_gap":
        y, rows = st["year"], st["places"]
        hi = next(r for r in rows if r["dcid"] == st["highest"])
        lo = next(r for r in rows if r["dcid"] == st["lowest"])
        nh = S.SDG_REGIONS.get(hi["dcid"], S.GROUPINGS.get(hi["dcid"], hi["place"]))
        nl = S.SDG_REGIONS.get(lo["dcid"], S.GROUPINGS.get(lo["dcid"], lo["place"]))
        sig = pts_(st["difference"], u) + " apart"
        c["headlines"] = [f"{cap(short)}: {nh} and {nl} are {sig}", f"{cap(short)}: {hi['place']} and {lo['place']} are {sig}",
                          f"{cap(short)} is {sig} across {'regions' if st['place_type'] == 'regions_compared' else 'groups'}"]
        c["signal"] = sig
        c["evidence"] = f"{hi['place']} {B_fmt(hi['value'], u)}, {lo['place']} {B_fmt(lo['value'], u)}, in {y}."
        world = next((r for r in rows if r["dcid"] == "Earth"), None)
        others = sorted([r for r in rows if r["dcid"] != "Earth"], key=lambda r: -r["value"])
        bars = others + ([world] if world else [])
        c["svg"] = B.hbars(style, h, [{"label": r["place"], "value": r["value"],
                                        "role": "world" if r["dcid"] == "Earth" else ("lead" if r["dcid"] in (hi["dcid"], lo["dcid"]) else "other")}
                                       for r in bars], u, value_fmt=lambda v: B_fmt(v, u),
                           aria="; ".join(f"{r['place']} {B_fmt(r['value'], u)}" for r in bars) + f", {y}.")
        c["method"] = f"Method: published aggregates, {y}; difference in {'percentage points' if u == '%' else 'the indicator units'}."
        c["note"] = "A statistician's note: these are the custodian's published aggregates, not averages I computed from country values."
        c["question"] = f"What would it take to close the gap in {short} between {nh} and {nl}?"

    elif k in ("coverage", "recency", "any_data"):
        place = st["place"]
        n, ns, cut = st["n_with_data"], st["n_stale"], st["stale_cutoff"]
        where = "" if place == "World" else f" in {place}"
        if k == "any_data":
            m, nm_ = st["n_members"], st["n_members_with_data"]
            sig = f"{nm_} of {m}"
            c["headlines"] = [f"{sig} countries and areas have any data on {short}"]
            c["signal"] = sig
            c["evidence"] = f"Counted over the {m} countries and areas of the eight SDG regions."
            c["svg"] = B.waffle(style, h, nm_, m, aria=f"{nm_} of {m} countries and areas with data on {short}.")
        else:
            m = st["n_members"]
            none_ = m - st["n_members_with_data"]
            if k == "recency" or ns >= 0.2 * n:
                sig = f"for {ns}" if k == "coverage" else f"{ns} of the {n}"
                if k == "coverage":
                    grp_ = S_dcid(place) in S.GROUPINGS
                    nm_ = f"All {n}" if n == m else f"{n} of {m}"
                    lead_ = (f"{n} countries and areas" if place == "World" else
                             f"{nm_} {short_place(place)}" if grp_ else f"{nm_} countries in {place}")
                    lead_s = (f"{n} countries and areas" if place == "World" else
                              f"{nm_} {short_place(place)}" if grp_ else f"{nm_} countries in {short_place(place)}")
                    c["headlines"] = [f"{lead_} have data on {short}; {sig}, the latest is from {cut} or earlier",
                                      f"{lead_s} have data on {short}; {sig}, the latest is from {cut} or earlier",
                                      f"{cap(short)}: {n} countries with data{where}; {sig}, nothing after {cut}",
                                      f"{lead_s} have data on {short}; {sig}, nothing after {cut}",
                                      f"{cap(short)}: for {ns} of the {n} countries with data, nothing after {cut}"]
                elif ns == 0:
                    sig = f"all {n}"
                    c["headlines"] = [f"For {sig} countries with data on {short}, the latest is from after {cut}",
                                      f"{cap(short)}: {sig} countries with data have a value from after {cut}"]
                else:
                    c["headlines"] = [f"For {sig} countries with data on {short}, the latest is from {cut} or earlier",
                                      f"{cap(short)}: for {sig} countries with data, the latest is from {cut} or earlier",
                                      f"{cap(short)}: {sig} countries with data have nothing after {cut}"]
                c["signal"] = sig
            else:
                sig = f"{st['n_members_with_data']} of {m}" if place == "World" else (f"All {n}" if n == m else f"{n} of {m}")
                if place == "World":
                    c["headlines"] = [f"{sig} countries and areas have data on {short}",
                                      f"{cap(short)}: data for {sig} countries and areas"]
                else:
                    c["headlines"] = ([f"{sig} {short_place(place)} have data on {short}"] if S_dcid(place) in S.GROUPINGS else
                                      [f"{sig} countries in {place} have data on {short}",
                                       f"{sig} countries in {short_place(place)} have data on {short}"])
                c["signal"] = sig
            lo_, hi_, md_ = st['latest_year_min'], st['latest_year_max'], st['median_latest_year']
            span_ = f"latest values {lo_} to {hi_}; median year {md_}" if lo_ != hi_ else f"all latest values are for {hi_}"
            c["evidence"] = f"{cap(span_)}."
            if place != "World":
                c["evidence"] = f"{short_place(place)}: {span_}."
            if place == "World" and not (k == "recency" or ns >= 0.2 * n):
                c["evidence"] = f"Out of {m} in the eight SDG regions; {span_}."
            c["svg"] = B.year_histogram(style, h, st["by_year"], cut, show_stale=ns > 0,
                                        aria=f"Countries{where} by year of their latest value on {short}: {n} in all, {ns} in {cut} or earlier.")
        c["method"] = (f"Method: countries and areas of the eight SDG regions with any value in the database." if k == "any_data"
                       else f"Method: each country's latest value in the database; {cut} or earlier counts as not recent.")
        c["note"] = ("A statistician's note: \"latest value\" means each country's most recent estimate, so values sit in "
                     "different years and are not directly comparable. A gap here is a gap in the data, not a judgement on "
                     "any statistical office.")
        c["question"] = f"Which countries have found a way to measure {short} more often, and what made it possible?"

    elif k == "coverage_compared":
        rows = sorted(st["places"], key=lambda r: -(r["share"] or 0))
        cut = st["stale_cutoff"]
        if st["place_type"] == "groupings":
            parts = [f"{r['n_with_data']} of {r['n_members']} {r['place']}" for r in st["places"]]
            low = min(st["places"], key=lambda r: r["share"] or 0)
            sig = f"{low['n_with_data']} of {low['n_members']} {low['place']}"
            c["headlines"] = [f"Data on {short} cover {parts[0]}, {parts[1]} and {parts[2]}",
                              f"{cap(short)}: data for {parts[0]}, {parts[1]} and {parts[2]}"]
        else:
            big = [r for r in rows if r["n_members"] >= 5]
            hi, lo = big[0], big[-1]
            sig = f"{B.num(lo['share'], 0)}% in {S.SDG_REGIONS[lo['dcid']]}"
            c["headlines"] = [f"{cap(short)}: data for {B.num(hi['share'], 0)}% of countries in {S.SDG_REGIONS[hi['dcid']]}, {sig}",
                              f"{cap(short)}: data for {B.num(hi['share'], 0)}% of countries in {hi['place']}, {B.num(lo['share'], 0)}% in {lo['place']}"]
            c["headlines_last"] = (f"{cap(short)}: data for {B.num(lo['share'], 0)}% of countries in {lo['place']}",
                                   f"{B.num(lo['share'], 0)}% of countries")
        c["signal"] = sig
        nst = sum(r["n_stale"] for r in st["places"]); nwd = sum(r["n_with_data"] for r in st["places"])
        nds, ndw = st.get("n_distinct_stale", nst), st.get("n_distinct_with_data", nwd)  # each country once
        c["evidence"] = (f"Countries with any value; for {nds} of the {ndw} with data, the latest is from {cut} or earlier."
                         if st["place_type"] == "groupings" else
                         f"Countries of each SDG region with any value; {nst} of {nwd} have nothing after {cut}.")
        c["svg"] = B.hbars(style, h, [{"label": r["place"], "value": r["share"] or 0, "role": "lead"} for r in rows], "%",
                           value_fmt=lambda v: f"{B.num(v, 0)}%",
                           aria="; ".join(f"{r['place']}: {r['n_with_data']} of {r['n_members']} countries with data" for r in rows))
        c["method"] = (f"Method: countries and areas with any value in the database, by membership, each counted once; "
                       f"{cut} or earlier counts as not recent.")
        c["note"] = ("A statistician's note: \"latest value\" means each country's most recent estimate, so values sit in "
                     "different years. A gap here is a gap in the data, not a judgement on any statistical office.")
        c["question"] = f"Which countries have found a way to measure {short} more often, and what made it possible?"

    elif k == "regions_data":
        rows = sorted(st["regions"], key=lambda r: -(r["share"] or 0))
        big = [r for r in rows if r["n_members"] >= 5]
        hi, lo = big[0], big[-1]
        nh, nl = S.SDG_REGIONS[hi["dcid"]], S.SDG_REGIONS[lo["dcid"]]
        top = B.num(hi["share"], 0)
        if lo["share"]:
            sig = f"{B.num(lo['share'], 0)}%"
            c["headlines"] = [f"{cap(short)}: data for {top}% of countries in {nh}, {sig} in {nl}",
                              f"{cap(short)}: data for {top}% of countries in {hi['place']}, {sig} in {lo['place']}",
                              f"Data on {short}: {top}% of countries in {hi['place']}, {sig} in {lo['place']}"]
        else:
            sig = f"none in {nl}"
            c["headlines"] = [f"{cap(short)}: data for {top}% of countries in {nh}, {sig}",
                              f"{cap(short)}: data for {top}% of countries in {hi['place']}, none in {lo['place']}",
                              f"Data on {short}: {top}% of countries in {hi['place']}, none in {lo['place']}"]
            if sig not in c["headlines"][1]:
                sig = f"none in {lo['place']}"
                c["headlines"] = c["headlines"][1:] + [f"{cap(short)}: {top}% of countries in {hi['place']}, {sig}"]
            nz = sum(1 for r in rows if not r["share"])
            words = {1: "one SDG region", 2: "two SDG regions", 3: "three SDG regions"}
            c["headlines_last"] = (f"{cap(short)}: no data at all in {words.get(nz, f'{nz} SDG regions')}",
                                   "no data at all")
        c["signal"] = sig
        c["evidence"] = f"{st['n_universe_with_data']} of {st['n_universe']} countries and areas in the eight SDG regions have any data."
        c["svg"] = B.hbars(style, h, [{"label": r["place"], "value": r["share"] or 0, "role": "lead"} for r in rows], "%",
                           value_fmt=lambda v: f"{B.num(v, 0)}%",
                           aria="; ".join(f"{r['place']}: {r['n_with_data']} of {r['n_members']} countries with data" for r in rows))
        c["method"] = "Method: countries and areas with any value in the database, by SDG region membership."
        c["note"] = ("A statistician's note: a region with few data points is not a region with a small problem; it is one "
                     "where we know less. Most of these figures come from national household surveys.")
        c["question"] = f"Where has a country started measuring {short} for the first time, and what made it possible?"
    else:
        raise ValueError(k)

    c["tfig"], c["tfig_short"] = tfig, tfig_short
    c.setdefault("detail", None)
    c["method_short"] = method_short(st)
    if fam.get("method_note"):
        c["method"] = c["method"].rstrip(".") + f"; series {fam['method_note']}."
        c["method_short"] = c["method_short"].rstrip(".") + f"; {fam['method_note'].split(',')[0]}, previous definition."
    return c


def method_short(st):
    k = st["kind"]
    if k == "pace":
        return f"Method: linear pace, {st['first']['year']} to {st['last']['year']}; target year {st['target']['year']}."
    if k == "pace_compared":
        r = next(x for x in st["places"] if x["dcid"] == st["lead"])
        return f"Method: linear pace on published aggregates, from {r['first']['year']} for {r['place']}."
    if k in ("level",):
        return f"Method: published aggregate, {st['last']['year']}; countries at their latest year."
    if k in ("level_compared", "places_gap"):
        return f"Method: published aggregates, {st['year']}."
    if k == "trend":
        return f"Method: published series, {st['first']['year']} to {st['last']['year']}."
    if k == "trend_compared":
        return f"Method: published aggregates, {st['from']} to {st['to']}."
    if k == "groups":
        return f"Method: published aggregates by group, {st['year']}."
    if k == "groups_compared":
        return "Method: published aggregates by group, latest year with both."
    if k == "country_gaps":
        return "Method: gap within each country's latest survey with both groups."
    if k == "any_data":
        return "Method: any value in the database, eight SDG regions."
    if k in ("coverage", "recency", "coverage_compared"):
        return f"Method: latest value per country; {st['stale_cutoff']} or earlier is not recent."
    return "Method: countries with any value in the database, by SDG region."


def x_len(s):
    import re
    s = re.sub(r"https?://\S+", "x" * 23, s)
    return sum(1 if ord(ch) <= 0x10FF or 0x2000 <= ord(ch) <= 0x206F else 2 for ch in s)


def captions(c, headline, meta, feed_tag, frame):
    """captions.md text. X <= 280 and Bluesky <= 300 characters, each with a Method line."""
    sdg_goal = meta["sdg_indicator"].split(".")[0]
    topic_tag = SDG_TAG.get(sdg_goal, "#DataForChildren")
    first = headline + "."
    ev = c["evidence"]
    custodian = c["source"]
    db_line = (f"Data: {custodian}, {c['db']}" + (f" ({c['code']}, extracted {c['extracted']})" if c.get("code") else
                                                 f" (extracted {c['extracted']})")
               + (", via the UN System Data Commons." if c["db"] != "UN System Data Commons" else "."))
    tf = c.get("tfig_short") if frame != "T" else None
    p2 = " ".join(x for x in [c.get("tfig") if frame != "T" else None, c.get("detail")] if x)
    li = [f"{first} {ev}", ""]
    if p2:
        li += [p2, ""]
    li += [c["note"], "", c["question"], "", c["method"], "",
           db_line, "",
           f"Data and code: https://{REPO}", "", f"#OfficialStatistics #DataForChildren {topic_tag}"]
    ms = c["method_short"]
    data = f"Data: {custodian}."

    def fit(parts, limit, fn):
        txt = " ".join(p for p in parts if p)
        return txt if fn(txt) <= limit else None

    x = None
    for parts in ([first, ev, tf, ms, data, "#OfficialStatistics #DataForChildren"],
                  [first, ev, tf, ms, data, "#OfficialStatistics"],
                  [first, tf, ms, data, "#OfficialStatistics"],
                  [first, tf, ms, data], [first, ms, data]):
        x = fit(parts, 280, x_len)
        if x:
            break
    blue = blue_tag = None
    for parts in ([first, ev, tf, ms, f"Data + code: {REPO}"], [first, tf, ms, f"Data + code: {REPO}"],
                  [first, tf, ms]):
        blue, blue_tag = fit(parts, 300, len), fit(parts + [feed_tag], 300, len)
        if blue and blue_tag:
            break
    if not (x and blue and blue_tag):
        raise ValueError(f"caption too long: {headline}")
    return "\n".join(["## LinkedIn", "", *li, "", "## X", "", x, "", "## Bluesky", "", blue, "",
                      "## Bluesky with feed tag", "", blue_tag, ""])
