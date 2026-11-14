"""E8 three-family vote (D-82, D-83, D-90) on D1-test S1: H8-1..H8-3 with Holm. Zero model calls.
Committed before any E8 call is made.

  VOTE3 = majority of one fresh J1-prompt call each from M1, M2 and the E6b judge (replicate index 10 of each);
  VOTE5 = majority of indices 11 and 12 of M1 and of M2 plus index 11 of the E6b judge (2 + 2 + 1);
  SC3   = majority of the first three of each committed M1 SC decision's five ordered votes (no call);
  SC, DEB = the committed M1 (confirmatory judge) SC and DEB at S1, all three replicates.
  Every majority uses the committed SC aggregation rule (`arms.aggregate_votes`: majority over valid votes, a tie among
  valid votes resolves to TF, all invalid -> INVALID), so an invalid member is handled as in SC.

  H8-1  ΔF1(VOTE3 − SC3) > 0     H8-2  ΔF1(VOTE5 − SC) > 0     H8-3  ΔF1(VOTE5 − DEB) ≠ 0
  Holm over the three (two-sided bug-level bootstrap p, committed seed); H8-1 / H8-2 supported when the
  Holm-adjusted p < alpha and the estimate is > 0, H8-3 when the Holm-adjusted p < alpha. The Table 18 reading
  (`stats.decide`, SESOI) is reported beside each. VOTE is one replicate, SC3/SC/DEB three (averaged), on the same
  instances (D-70: S1 leakage aborts of any contributing run dropped). Descriptive: each model's fresh J1, the
  unanimity rate, MCC with CIs, calls per instance.

    python scripts/analysis/e8_analysis.py   -> results/e8/analysis/e8_d1test.json
"""
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import analysis, arms, config, stats  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

RUNS = ROOT / "results" / "runs_local"
OUT = ROOT / "results" / "e8" / "analysis" / "e8_d1test.json"
M1_RUN = "LOCAL_HO_E1E3_M1"
VOTE_RUNS = {"M1": "LOCAL_HO_E8_VOTE_M1", "M2": "LOCAL_HO_E8_VOTE_M2", "E6B": "LOCAL_HO_E8_VOTE_E6B"}
VOTE3 = {"M1": (10,), "M2": (10,), "E6B": (10,)}
VOTE5 = {"M1": (11, 12), "M2": (11, 12), "E6B": (11,)}
CALLS = {"VOTE3": 3, "VOTE5": 5, "SC3": 3, "SC": 5, "DEB": 5}


def s1_full(d):
    return d.get("level") == "S1" and (d.get("variant") or "full") == "full"


def rejections(run):
    f = RUNS / run / "leakage_rejections.jsonl"
    return {r["instance_id"] for r in read_jsonl(f) if r.get("level") == "S1"} if f.exists() else set()


def vote(by, members, iid, arm):
    labels = [by.get((m, iid, rep)) for m, reps in members.items() for rep in reps]
    if any(x is None for x in labels):
        return None
    agg = arms.aggregate_votes(labels, len(labels))
    return {"instance_id": iid, "arm": arm, "level": "S1", "variant": "full", "replicate": 0, "model": "vote",
            "label_raw": agg["label_raw"], "votes": labels, "agreement": {k: agg[k] for k in ("n_pf", "n_tf", "n_invalid")}}


def main():
    m1 = [d for d in read_jsonl(RUNS / M1_RUN / "decisions.jsonl")]
    base = [d for d in m1 if d["arm"] in ("SC", "DEB") and s1_full(d)]
    ka = [d for d in m1 if d["arm"] == "KA"]
    sc3 = [{**d, "arm": "SC3", "label_raw": arms.aggregate_votes(d["votes"][:3], 3)["label_raw"], "votes": d["votes"][:3]}
           for d in base if d["arm"] == "SC"]
    by, fresh = {}, []
    for m, run in VOTE_RUNS.items():
        for d in read_jsonl(RUNS / run / "decisions.jsonl"):
            if d["arm"] == "J1" and s1_full(d):
                by[(m, d["instance_id"], d["replicate"])] = d["label_raw"]
                fresh.append({**d, "arm": f"J1{m}", "replicate": d["replicate"] - 10})
    iids = sorted({k[1] for k in by})
    v3 = [x for x in (vote(by, VOTE3, i, "VOTE3") for i in iids) if x]
    v5 = [x for x in (vote(by, VOTE5, i, "VOTE5") for i in iids) if x]
    aborted = rejections(M1_RUN).union(*(rejections(r) for r in VOTE_RUNS.values()))
    samp = json.loads((config.PROCESSED / "sample_D1_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl") if l["instance_id"] in keep]
    ev = analysis.Evaluation(base + sc3 + v3 + v5 + ka + fresh, labels, samp["tf_weights"],
                             exclusions={("S1", "full"): aborted})
    conds = ["VOTE3|S1", "VOTE5|S1", "SC3|S1", "SC|S1", "DEB|S1"]
    ids = ev.comparison_set(conds)
    evr = ev._restricted(ids)
    fam = [evr.contrast("H8-1 VOTE3 - SC3", ["VOTE3|S1"], ["SC3|S1"], "f1"),
           evr.contrast("H8-2 VOTE5 - SC", ["VOTE5|S1"], ["SC|S1"], "f1"),
           evr.contrast("H8-3 VOTE5 - DEB", ["VOTE5|S1"], ["DEB|S1"], "f1")]
    for c, p in zip(fam, stats.holm([c.p for c in fam])):
        c.p_holm = p
        c.conclusion = stats.decide(c)
    rule = {"H8-1": lambda c: c.p_holm < config.ALPHA and c.delta > 0,
            "H8-2": lambda c: c.p_holm < config.ALPHA and c.delta > 0,
            "H8-3": lambda c: c.p_holm < config.ALPHA}
    hyp = {c.name.split()[0]: {**asdict(c), "supported": bool(rule[c.name.split()[0]](c))} for c in fam}
    keys = ("f1", "f1_ci95", "mcc", "mcc_ci95", "precision", "recall", "pf_lost", "invalid_rate", "n_instances")
    summ = {c: {k: evr.summary(c).get(k) for k in keys} for c in conds}
    fresh_c = {m: f"J1{m}|S1" for m in VOTE_RUNS}
    in_set = [x for x in v3 + v5 if x["instance_id"] in ids]
    out = {"what": "E8 three-family vote (D-82/D-83/D-90)", "dataset": "D1", "split": "test", "level": "S1",
           "decisions": ["D-82", "D-83", "D-90"], "n_instances": len(ids), "n_bugs": len(evr.bugs),
           "pf_prevalence": analysis.judged_prevalence(labels, sorted(ids)), "aborted_excluded": sorted(aborted),
           "members": {"VOTE3": VOTE3, "VOTE5": VOTE5}, "calls_per_instance": CALLS,
           "summary": summ, "hypotheses": hyp, "holm_family": ["H8-1", "H8-2", "H8-3"], "alpha": config.ALPHA,
           "fresh_j1": {m: {k: evr.summary(c).get(k) for k in ("f1", "f1_ci95", "mcc", "mcc_ci95", "n_instances")}
                        for m, c in fresh_c.items() if evr.by_cond.get(c)},
           "unanimity": {a: sum(1 for x in in_set if x["arm"] == a and len(set(x["votes"])) == 1)
                         / max(1, sum(1 for x in in_set if x["arm"] == a)) for a in ("VOTE3", "VOTE5")},
           "ka_f1": evr.baseline_summary("KA")["f1"],
           "note": ("Votes are formed offline from fresh J1-prompt calls (replicate indices 10-12, no committed call "
                    "reused); SC3/SC/DEB are the confirmatory judge M1's committed decisions. " + analysis.F1_NOT_COMPARABLE)}
    dump_json(OUT, out)
    r = lambda v: round(v, 3)
    print(f"E8  n={out['n_instances']} bugs={out['n_bugs']}")
    for c in conds:
        s = summ[c]
        print(f"  {c}: F1 {r(s['f1'])} {[r(x) for x in s['f1_ci95']]}  MCC {r(s['mcc'])}")
    for h, v in hyp.items():
        print(f"  {h}: Δ {r(v['delta'])} {[r(x) for x in v['ci95']]} p={r(v['p'])} p_holm={r(v['p_holm'])} "
              f"supported={v['supported']} ({v['conclusion']})")


if __name__ == "__main__":
    main()
