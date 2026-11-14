"""Keep-unless-unanimous with disagreement escalation: a two-tier cascade (D-105). Zero model calls; reads committed
decision logs. Committed before any E9b call, so its D2 read is confirmatory.

Rule (no tunable parameter):
  Tier 1  the three local single-call J1 votes (M1 Qwen 3.5 9B, M2 Gemma 4 12B, E6b Ministral 3 14B):
          all three valid TEST_FAULT -> discard (TEST_FAULT); all three valid PROGRAM_FAULT -> keep (PROGRAM_FAULT).
  Tier 2  any disagreement, including an invalid or missing vote -> escalate to Sonnet 5.5 DEB, whose valid label decides.
          A missing or invalid Sonnet decision -> keep (PROGRAM_FAULT).
Secondary (descriptive): the same cascade escalating to Sonnet J1.

  D2  CONFIRMATORY. Tier 1 = LOCAL_HO_KUU_D2_{M1,M2,E6B} (replicate 20); Tier 2 = E9b (E9B_SONNET55_D2, one replicate).
      H12-1  MCC(cascade) > MCC(KUU): paired bug-level bootstrap, two-sided p; supported when p_Holm < alpha and Δ > 0.
      H12-2  F1(cascade) − F1(Sonnet DEB on all instances) > −0.05 (non-inferiority at the study's ±0.05 margin):
             one-sided bootstrap p = (#{Δ* <= −0.05} + 1) / (B + 1); supported when p_Holm < alpha.
      Holm over the two. Descriptive: share escalated, frontier calls and cost (from the E9b decisions' logged cost)
      against Sonnet DEB on every instance, PF tests lost, bugs with no PF test kept, precision, recall, F1, MCC.
  D1  POST HOC (development evidence): Tier 1 = the E8 VOTE3 calls (replicate 10); Tier 2 = E9 Sonnet DEB, each of its
      three replicates giving one cascade replicate (metrics averaged over replicates, as everywhere). Hypotheses are
      computed with the same rule for comparison, never as a test.
Instances: scored (PF or TF), not leakage-aborted at S1 in any contributing run (D-70), and present in every condition.
MCC is the primary metric where datasets differ in prevalence; F1 is reported because H12-2 is about F1.

    python scripts/analysis/cascade.py d1   -> results/cascade/analysis/cascade_d1_posthoc.json
    python scripts/analysis/cascade.py d2   -> results/cascade/analysis/cascade_d2.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import analysis, config, stats  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

RUNS = ROOT / "results" / "runs_local"
FRONT = ROOT / "results" / "runs_frontier"
OUT = ROOT / "results" / "cascade" / "analysis"
TF, PF = "TEST_FAULT", "PROGRAM_FAULT"
MARGIN = 0.05
PLAN = {
    "d1": {"dataset": "D1", "sample": "sample_D1_test.json", "labels": "labels_D1.jsonl", "vote_rep": 10,
           "members": {"M1": "LOCAL_HO_E8_VOTE_M1", "M2": "LOCAL_HO_E8_VOTE_M2", "E6B": "LOCAL_HO_E8_VOTE_E6B"},
           "m1_run": "LOCAL_HO_E1E3_M1", "frontier_run": "E9_SONNET55_D1TEST",
           "status": "post hoc (development evidence)", "out": "cascade_d1_posthoc.json"},
    "d2": {"dataset": "D2", "sample": "sample_D2_test.json", "labels": "labels_D2.jsonl", "vote_rep": 20,
           "members": {"M1": "LOCAL_HO_KUU_D2_M1", "M2": "LOCAL_HO_KUU_D2_M2", "E6B": "LOCAL_HO_KUU_D2_E6B"},
           "m1_run": "LOCAL_HO_E5R1_D2", "frontier_run": "E9B_SONNET55_D2",
           "status": "confirmatory (D-105)", "out": "cascade_d2.json"},
}
KEYS = ("f1", "f1_ci95", "mcc", "mcc_ci95", "precision", "recall", "pf_lost", "TP", "FN", "n_instances")


def tier1(votes: list):
    """Unanimous valid votes decide; anything else escalates (returns None)."""
    if len(votes) == 3 and all(v == TF for v in votes):
        return TF
    if len(votes) == 3 and all(v == PF for v in votes):
        return PF
    return None


def cascade(votes: list, escalated_label) -> str:
    t = tier1(votes)
    if t is not None:
        return t
    return escalated_label if escalated_label in (TF, PF) else PF


def kuu(votes: list) -> str:
    return TF if len(votes) == 3 and all(v == TF for v in votes) else PF


def s1(d):
    return d.get("level") == "S1" and (d.get("variant") or "full") == "full"


def aborts(path: Path):
    f = path / "leakage_rejections.jsonl"
    return {r["instance_id"] for r in read_jsonl(f) if r.get("level") == "S1"} if f.exists() else set()


def lost_bugs(ev, c: str) -> float:
    T = ev.tensor(c)
    has_pf = (T[:, 0, 0] + T[:, 0, 2]) > 0
    return float(np.mean([(has_pf & (T[:, r, 0] == 0)).sum() for r in range(T.shape[1])]))


def cost_of(d) -> float:
    c = d.get("cost")
    if isinstance(c, str):
        import ast
        c = ast.literal_eval(c)
    return float((c or {}).get("cost_usd") or 0.0), int((c or {}).get("calls") or 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["d1", "d2"])
    plan = PLAN[ap.parse_args().which]
    votes = {}
    for m, run in plan["members"].items():
        for d in read_jsonl(RUNS / run / "decisions.jsonl"):
            if d["arm"] == "J1" and s1(d) and d["replicate"] == plan["vote_rep"]:
                votes.setdefault(d["instance_id"], {})[m] = d["label_raw"]
    front = [d for d in read_jsonl(FRONT / plan["frontier_run"] / "decisions.jsonl") if s1(d)]
    son = {}                                  # (arm, replicate) -> {instance: decision}
    for d in front:
        son.setdefault((d["arm"], d["replicate"]), {})[d["instance_id"]] = d
    deb_reps = sorted(r for a, r in son if a == "DEB")
    j1_reps = sorted(r for a, r in son if a == "J1")
    samp = json.loads((config.PROCESSED / plan["sample"]).read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / plan["labels"]) if l["instance_id"] in keep]
    aborted = aborts(RUNS / plan["m1_run"]) | aborts(FRONT / plan["frontier_run"]) | set().union(
        *(aborts(RUNS / r) for r in plan["members"].values()))
    syn = []
    for i, v in votes.items():
        vs = [v.get(m) for m in plan["members"]]
        syn.append({"instance_id": i, "arm": "KUU", "level": "S1", "variant": "full", "replicate": 0,
                    "label_raw": kuu(vs)})
        for k, r in enumerate(deb_reps):
            e = son[("DEB", r)].get(i)
            syn.append({"instance_id": i, "arm": "CAS", "level": "S1", "variant": "full", "replicate": k,
                        "label_raw": cascade(vs, e["label_raw"] if e else None), "escalated": tier1(vs) is None})
            if e:
                syn.append({**e, "arm": "DEB", "variant": "SON", "replicate": k})
        for k, r in enumerate(j1_reps):
            e = son[("J1", r)].get(i)
            syn.append({"instance_id": i, "arm": "CASJ1", "level": "S1", "variant": "full", "replicate": k,
                        "label_raw": cascade(vs, e["label_raw"] if e else None)})
            if e:
                syn.append({**e, "arm": "J1", "variant": "SON", "replicate": k})
    m1 = [d for d in read_jsonl(RUNS / plan["m1_run"] / "decisions.jsonl") if d["arm"] == "DEB" and s1(d)]
    m1 += [d for d in read_jsonl(RUNS / plan["m1_run"] / "decisions.jsonl") if d["arm"] == "KA"]
    ev = analysis.Evaluation(syn + m1, labels, samp.get("tf_weights"),
                             exclusions={("S1", "full"): aborted, ("S1", "SON"): aborted})
    conds = ["CAS|S1", "KUU|S1", "DEB|S1|SON", "CASJ1|S1", "J1|S1|SON", "DEB|S1"]
    ids = ev.comparison_set(conds)
    evr = ev._restricted(ids)
    summ = {c: {k: evr.summary(c).get(k) for k in KEYS} for c in conds}
    summ["KA"] = {k: evr.baseline_summary("KA").get(k) for k in KEYS}
    # H12-1: MCC(cascade) - MCC(KUU), paired
    h1 = evr.contrast("H12-1 CAS - KUU (MCC)", ["CAS|S1"], ["KUU|S1"], "mcc")
    # H12-2: F1(cascade) - F1(Sonnet DEB on all), non-inferiority at -0.05, one-sided bootstrap p
    ta, tb = evr.tensor("CAS|S1"), evr.tensor("DEB|S1|SON")
    dist = stats.bootstrap_metric(ta, "f1", evr.W) - stats.bootstrap_metric(tb, "f1", evr.W)
    dist = dist[~np.isnan(dist)]
    d2 = stats.point_estimate(ta, "f1") - stats.point_estimate(tb, "f1")
    p2 = float((np.sum(dist <= -MARGIN) + 1) / (len(dist) + 1))
    adj = stats.holm([h1.p, p2])
    hyp = {"H12-1": {"what": "MCC(cascade) > MCC(KUU), paired", "delta": h1.delta, "ci95": h1.ci95, "p": h1.p,
                     "p_holm": adj[0], "supported": bool(adj[0] < config.ALPHA and h1.delta > 0)},
           "H12-2": {"what": "F1(cascade) − F1(Sonnet DEB on all) > −0.05 (non-inferiority)", "delta": d2,
                     "ci95": stats.percentile_ci(dist, 0.95), "ci90": stats.percentile_ci(dist, 0.90),
                     "margin": -MARGIN, "p_one_sided": p2, "p_holm": adj[1], "supported": bool(adj[1] < config.ALPHA)}}
    if plan["dataset"] == "D1":
        for h in hyp.values():
            h["supported"] = None
            h["note"] = "post hoc on D1: same rule, for comparison only, never a test of H12"
    in_set = sorted(evr.lab)
    esc = {i: tier1([votes[i].get(m) for m in plan["members"]]) is None for i in in_set if i in votes}
    n_esc = sum(esc.values())
    cost_all, calls_all, cost_esc, calls_esc = 0.0, 0, 0.0, 0
    for k, r in enumerate(deb_reps):
        for i in in_set:
            e = son[("DEB", r)].get(i)
            if e:
                c, n = cost_of(e)
                cost_all += c
                calls_all += n
                if esc.get(i):
                    cost_esc += c
                    calls_esc += n
    nr = max(len(deb_reps), 1)
    out = {"what": "keep-unless-unanimous with disagreement escalation, two-tier cascade (D-105)",
           "status": plan["status"], "dataset": plan["dataset"], "level": "S1", "tier1_runs": plan["members"],
           "tier2_run": plan["frontier_run"], "sonnet_deb_replicates": len(deb_reps), "n_instances": len(ids),
           "n_bugs": len(evr.bugs), "pf_prevalence": analysis.judged_prevalence(labels, sorted(ids)),
           "summary": summ, "hypotheses": hyp,
           "escalation": {"escalated": n_esc, "share_escalated": n_esc / len(esc) if esc else None,
                          "tier1_discard": sum(1 for i in in_set if i in votes and tier1([votes[i].get(m) for m in plan["members"]]) == TF),
                          "tier1_keep": sum(1 for i in in_set if i in votes and tier1([votes[i].get(m) for m in plan["members"]]) == PF),
                          "frontier_calls_cascade_per_replicate": calls_esc / nr,
                          "frontier_calls_all_per_replicate": calls_all / nr,
                          "frontier_cost_cascade_usd_per_replicate": cost_esc / nr,
                          "frontier_cost_all_usd_per_replicate": cost_all / nr,
                          "frontier_cost_saved_share": 1 - cost_esc / cost_all if cost_all else None,
                          "local_calls_per_instance": 3},
           "bugs_with_no_pf_kept": {c: lost_bugs(evr, c) for c in conds},
           "cascade_minus_kuu_f1": vars(evr.contrast("CAS - KUU F1", ["CAS|S1"], ["KUU|S1"], "f1")),
           "cascade_minus_sonnet_deb_mcc": vars(evr.contrast("CAS - SON DEB MCC", ["CAS|S1"], ["DEB|S1|SON"], "mcc")),
           "note": "frontier tier = frontier reference point, not a protocol replication. " + analysis.F1_NOT_COMPARABLE}
    OUT.mkdir(parents=True, exist_ok=True)
    dump_json(OUT / plan["out"], out)
    r = lambda v: round(v, 3) if isinstance(v, float) else v
    print(f"cascade {plan['dataset']} ({plan['status']}) n={out['n_instances']} bugs={out['n_bugs']} "
          f"escalated={out['escalation']['escalated']} ({r(out['escalation']['share_escalated'])})")
    for c, s in summ.items():
        print(f"  {c}: F1 {r(s['f1'])} MCC {r(s['mcc'])} P {r(s['precision'])} R {r(s['recall'])} lost {r(s['pf_lost'])}")
    for h, v in hyp.items():
        print(f"  {h}: {r(v['delta'])} {[r(x) for x in v['ci95']]} p_holm={r(v['p_holm'])} supported={v['supported']}")
    print("  cost saved share", r(out["escalation"]["frontier_cost_saved_share"]))


if __name__ == "__main__":
    main()
