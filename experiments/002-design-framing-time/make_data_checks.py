"""Write DATA_CHECKS.md: which framings each of the 50 proposals supports, from the saved responses.

Usage: python make_data_checks.py   (builds each proposal's snapshot in a temporary folder, then checks it)
The World Bank results for the eight conditional proposals come from the Data360 calls saved in data/raw/
(see the notes in the table); the selection paragraph records JP's decision of 1 November 2026.
"""
import csv, sys, os, pathlib, tempfile
HERE = pathlib.Path(__file__).resolve().parent
os.chdir(HERE)
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent.parent / "scripts"))
import spotlight002 as S
import build_topic_data as BT
_tmp = tempfile.TemporaryDirectory()
SC = _tmp.name
props=list(csv.DictReader(open('proposals.csv')))
topics={t['proposal']:t for t in csv.DictReader(open('topics.csv'))}
WB={"P01":"fail: no World Bank indicator for SDG 4.2.2 with published aggregates (WB_HCP_ORG_LEARNING is attendance, with no World or FCS values)",
"P02":"fail: the FCS aggregate exists only in the superseded HNP release (2000 to 2020), whose World values differ from the current series (2020: 223 in HNP, 211 in WDI)",
"P03":"fail: no World Bank indicator for SDG 4.2.2 with income-group aggregates",
"P04":"fail: no low- or high-income aggregates for SP.M18.2024.FE.ZS in WDI, HNP or Gender Statistics",
"P25":"fail: the FCS aggregate exists only in the superseded HNP release (2010 and 2018), not in current WDI",
"P26":"fail: the FCS aggregate exists only in the superseded HNP release (to 2022); World 2022 is 29.3 in WDI, 27.9 in HNP",
"P27":"fail: WDI publishes wasting by income group (2000 to 2024), but the classification's fiscal year could not be established from the tools, so G and D (country counts within groups) cannot be done; two framings left",
"P28":"fail: WB_HCP_HPV_VAC has no World, income-group or FCS values"}
fx=lambda s: s.replace("|", ", ")
L=["# Experiment 002: data checks of the 50 proposals","",
"Run on 1 November 2026. Each proposal's data were retrieved from the UN System Data Commons with the calls in",
"`data/calls_plan.json`, made exactly as planned by sub-agents working through `data/batches/`. Every response was",
"saved verbatim from the session transcripts by `extract_calls.py` (`data/raw/<id>.json`, indexed in",
"`data/calls_index.json`). `build_topic_data.py` writes each topic's snapshot from those responses, and",
"`scripts/spotlight002.py check` says which framings the snapshot supports, under the rules in PREREGISTRATION.md.","",
"Notes on method:","",
"- Membership of SDG regions and groupings comes from the Data Commons' own containment, through under-five",
"  mortality calls. Four SDG regions return no countries directly, so they are composed of their M49 subregions",
"  (Northern Africa and Western Asia; Central and Southern Asia; Eastern and South-eastern Asia; Northern, Western,",
"  Southern and Eastern Europe with Northern America). The Data Commons lists the Turks and Caicos Islands under",
"  Northern Europe; it is left out of Europe and Northern America (in M49 it is in the Caribbean). This gives 194",
"  countries and areas in the eight SDG regions. The Data Commons' list of LDCs still includes Bhutan and Sao Tome and",
"  Principe, which have graduated (UNCTAD's UN list of least developed countries, 44 countries, read on 1 November",
"  2026); they are left out of LDC counts. The LDC aggregates are the custodians' own and are used as published.",
"- World counts of countries with data use the 194 countries and areas of the eight SDG regions, so that coverage and",
"  recency figures share one base.",
"- \"Behind the average\" with a breakdown uses published aggregates by group where the source has them. Otherwise it",
"  counts the countries of the place where the gap points one way, using only countries with both groups from the",
"  same year, and only with 10 such countries or more.",
"- Leading regions in comparisons are chosen among places with five countries or more (Australia and New Zealand",
"  has two). A long-view comparison uses the years all places share; if that span is under 10 years, the place whose",
"  series starts latest is left out (named in the Method line) until the span reaches 10 years.",
"- Numbers are stored at four decimals and rounded once, when the words and charts are written.",
"- An independent review of all 108 versions (1 November 2026) led to these fixes before the banners were final:",
"  single rounding, the LDC list, one base for World counts, the long-view span rule, wording by direction of progress,",
"  past tense for survey gaps, the source named for breakdown data, and no repeated headline between topics.",
"- World Bank aggregates for the eight conditional topics were checked with the World Bank Data360 tools; those",
"  calls are saved with the others.","",
"## Results","",
"| Proposal | Pace | Indicator | Place | Breakdown | Framings proposed | Supported | Result |",
"| --- | --- | --- | --- | --- | --- | --- | --- |"]
for p in props:
    pid=p['proposal']
    if pid in WB:
        sup=""; res=WB[pid]
    else:
        BT.build(pid, pathlib.Path(SC) / pid)
        c=S.check(f"{SC}/{pid}")
        ok=[f for f,v in c.items() if v['ok']]
        sup=", ".join(ok)
        why="; ".join(f"{f}: {v['reason']}" for f,v in c.items() if not v['ok'])
        need_ok=(len(ok)>=3) and (p['pace']!='1' or ('T' in ok and 'L' in ok))
        res=("pass" if need_ok else "fail: fewer than three framings")+(f" ({why})" if why else "")
        if pid=="P37": res+="; the series is SL_TLF_CHLDEA (economic activity), so it is labelled that way, with no target wording"
        if pid in ("P18","P19"): res+="; dropped by JP on 1 November 2026: SDG 4.1.1 has no numeric target under the house rule, so no pace"
    if pid in topics: res+=f". Spotlight {topics[pid]['spotlight']}"
    L.append(f"| {pid} | {p['pace']} | {p['indicator']} | {p['place']} | {p['breakdown']} | {fx(p['frames'])} | {sup} | {res} |")
L+=["","## Selection","",
"36 topics, as registered: 18 with a pace (P05 to P17 and P20 to P24) and 18 without (P29 to P44, P46 and P49).",
"Exactly 18 proposals without a pace passed, so all of them are in. Of the 20 with a pace that passed, JP dropped",
"P18 and P19 on 1 November 2026. No proposal had to be replaced. Spotlight numbers 05 to 40 follow proposal order",
"(`topics.csv`).",""]
open('DATA_CHECKS.md','w').write("\n".join(L)+"\n")
