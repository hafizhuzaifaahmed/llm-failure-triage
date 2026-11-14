"""Keep-unless-unanimous cross-family triage, KUU (D-95). Zero model calls. Committed before any KUU number is computed.

Rule (no tunable parameter): one J1 call each from M1, M2 and the E6b judge; DISCARD (TF) only if all three votes are
valid and TF; otherwise KEEP (PF). A missing or invalid vote counts as keep.

  D1-test  POST HOC (development evidence): the members are the committed E8 VOTE3 calls (replicate index 10 of each
           model). KUU was defined after the E8 results were seen, so this read is labelled post hoc everywhere.
  D2       CONFIRMATORY: fresh J1 calls on D2 at S1, one replicate (index 20), runs LOCAL_HO_KUU_D2_{M1,M2,E6B}.
           H10-1  ΔF1(KUU − KA) > 0
           H10-2  bug-revealing tests lost: FN(KUU) − FN(M1 DEB) < 0, paired bug-level bootstrap
           Holm over the two (two-sided bootstrap p, committed seed and B); H10-1 supported when p_Holm < alpha and
           Δ > 0, H10-2 when p_Holm < alpha and Δ < 0. M1 DEB is the committed D2 run (LOCAL_HO_E5R1_D2).
Reported beside: F1, MCC, precision, recall, PF tests lost, bugs with no PF test kept, share discarded, with bug-level
95% CIs. D-70: an instance aborted by the S1 leakage guard in any contributing run is dropped.

    python scripts/analysis/kuu_analysis.py d1   -> results/kuu/analysis/kuu_d1_posthoc.json
    python scripts/analysis/kuu_analysis.py d2   -> results/kuu/analysis/kuu_d2.json
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
OUT = ROOT / "results" / "kuu" / "analysis"
TF, PF = "TEST_FAULT", "PROGRAM_FAULT"
PLAN = {
    "d1": {"dataset": "D1", "sample": "sample_D1_test.json", "labels": "labels_D1.jsonl", "replicate": 10,
           "members": {"M1": "LOCAL_HO_E8_VOTE_M1", "M2": "LOCAL_HO_E8_VOTE_M2", "E6B": "LOCAL_HO_E8_VOTE_E6B"},
           "baseline_run": "LOCAL_HO_E1E3_M1", "status": "post hoc (development evidence; KUU defined after E8)",
           "out": "kuu_d1_posthoc.json"},
    "d2": {"dataset": "D2", "sample": "sample_D2_test.json", "labels": "labels_D2.jsonl", "replicate": 20,
           "members": {"M1": "LOCAL_HO_KUU_D2_M1", "M2": "LOCAL_HO_KUU_D2_M2", "E6B": "LOCAL_HO_KUU_D2_E6B"},
           "baseline_run": "LOCAL_HO_E5R1_D2", "status": "confirmatory (D-95)", "out": "kuu_d2.json"},
}
KEYS = ("f1", "f1_ci95", "mcc", "mcc_ci95", "precision", "precision_ci95", "recall", "recall_ci95", "pf_lost", "TP", "FN",
        "n_instances")


def kuu(votes: list) -> str:
    """Discard only on three valid TF votes; anything else (a PF vote, an invalid or missing vote) keeps the test."""
    return TF if len(votes) == 3 and all(v == TF for v in votes) else PF


def s1(d):
    return d.get("level") == "S1" and (d.get("variant") or "full") == "full"


def rejections(run):
    f = RUNS / run / "leakage_rejections.jsonl"
    return {r["instance_id"] for r in read_jsonl(f) if r.get("level") == "S1"} if f.exists() else set()


def fn_difference(ev, a: str, b: str):
    """FN(a) − FN(b) summed over instances, paired over the same bug resamples (b averaged over its replicates)."""
    fa = ev.tensor(a)[:, :, 2].mean(axis=1)
    fb = ev.tensor(b)[:, :, 2].mean(axis=1)
    d = ev.W @ (fa - fb)
    return float((fa - fb).sum()), stats.percentile_ci(d, 0.95), stats.bootstrap_p_two_sided(d)


def lost_bugs(ev, c: str) -> float:
    """Bugs with at least one PF test in the set and none kept (mean over replicates)."""
    T = ev.tensor(c)
    has_pf = (T[:, 0, 0] + T[:, 0, 2]) > 0
    return float(np.mean([(has_pf & (T[:, r, 0] == 0)).sum() for r in range(T.shape[1])]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["d1", "d2"])
    plan = PLAN[ap.parse_args().which]
    votes = {}
    for m, run in plan["members"].items():
        for d in read_jsonl(RUNS / run / "decisions.jsonl"):
            if d["arm"] == "J1" and s1(d) and d["replicate"] == plan["replicate"]:
                votes.setdefault(d["instance_id"], {})[m] = d["label_raw"]
    base_all = list(read_jsonl(RUNS / plan["baseline_run"] / "decisions.jsonl"))
    base = [d for d in base_all if d["arm"] in ("SC", "DEB") and s1(d)] + [d for d in base_all if d["arm"] == "KA"]
    samp = json.loads((config.PROCESSED / plan["sample"]).read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / plan["labels"]) if l["instance_id"] in keep]
    aborted = rejections(plan["baseline_run"]).union(*(rejections(r) for r in plan["members"].values()))
    kd = [{"instance_id": i, "arm": "KUU", "level": "S1", "variant": "full", "replicate": 0, "model": "kuu",
           "label_raw": kuu([v.get(m) for m in plan["members"]]), "votes": [v.get(m) for m in plan["members"]]}
          for i, v in votes.items() if i in keep]
    ev = analysis.Evaluation(base + kd, labels, samp.get("tf_weights"), exclusions={("S1", "full"): aborted})
    conds = ["KUU|S1", "DEB|S1", "SC|S1"]
    ids = ev.comparison_set(conds)
    evr = ev._restricted(ids)
    summ = {c: {k: evr.summary(c).get(k) for k in KEYS} for c in conds + ["KA"]}
    summ["KA"] = {k: evr.baseline_summary("KA").get(k) for k in KEYS}
    in_set = [x for x in kd if x["instance_id"] in evr.lab]
    discarded = sum(x["label_raw"] == TF for x in in_set)
    out = {"what": "keep-unless-unanimous cross-family triage, KUU (D-95)", "status": plan["status"],
           "dataset": plan["dataset"], "level": "S1", "member_runs": plan["members"], "replicate_index": plan["replicate"],
           "n_instances": len(ids), "n_bugs": len(evr.bugs),
           "pf_prevalence": analysis.judged_prevalence(labels, sorted(ids)), "aborted_excluded": sorted(aborted),
           "summary": summ, "share_discarded": discarded / len(in_set) if in_set else None,
           "invalid_or_missing_votes": sum(1 for x in in_set for v in x["votes"] if v not in (TF, PF)),
           "bugs_with_no_pf_kept": {c: lost_bugs(evr, c) for c in conds}}
    h1 = evr.contrast("H10-1 KUU - KA", ["KUU|S1"], ["KA"], "f1")
    d2, ci2, p2 = fn_difference(evr, "KUU|S1", "DEB|S1")
    adj = stats.holm([h1.p, p2])
    hyp = {"H10-1": {"what": "ΔF1(KUU − KA) > 0", "delta": h1.delta, "ci95": h1.ci95, "p": h1.p, "p_holm": adj[0],
                     "supported": bool(adj[0] < config.ALPHA and h1.delta > 0)},
           "H10-2": {"what": "PF tests lost: FN(KUU) − FN(M1 DEB) < 0", "delta": d2, "ci95": ci2, "p": p2, "p_holm": adj[1],
                     "supported": bool(adj[1] < config.ALPHA and d2 < 0)}}
    if plan["dataset"] == "D1":
        for h in hyp.values():
            h["supported"] = None
            h["note"] = "post hoc on D1: computed with the same rule for comparison, never a test of H10"
    out["hypotheses"] = hyp
    out["kuu_minus_deb_f1"] = vars(evr.contrast("KUU - DEB", ["KUU|S1"], ["DEB|S1"], "f1"))
    out["kuu_minus_sc_f1"] = vars(evr.contrast("KUU - SC", ["KUU|S1"], ["SC|S1"], "f1"))
    out["note"] = ("KUU is a proposed design principle (keep by default, discard on cross-family agreement); it was "
                   "defined after the D1 vote results, so D1 is development evidence and D2 is the test. "
                   + analysis.F1_NOT_COMPARABLE)
    dump_json(OUT / plan["out"], out)
    r = lambda v: round(v, 3)
    print(f"KUU {plan['dataset']} ({plan['status']}) n={out['n_instances']} bugs={out['n_bugs']} "
          f"discarded={r(out['share_discarded'])}")
    for c, s in summ.items():
        print(f"  {c}: F1 {r(s['f1'])} MCC {r(s['mcc'])} P {r(s['precision']) if s['precision'] == s['precision'] else 'n/a'} "
              f"R {r(s['recall'])} lost {r(s['pf_lost'])}")
    for h, v in hyp.items():
        print(f"  {h}: Δ {r(v['delta'])} {[r(x) for x in v['ci95']]} p={r(v['p'])} p_holm={r(v['p_holm'])} supported={v['supported']}")


if __name__ == "__main__":
    main()
