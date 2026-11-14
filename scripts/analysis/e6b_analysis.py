"""E6b third-family judge (D-82, D-85..D-87) on D1-test S1: the pre-registered H6-1, H6-2, H6-3 and the descriptive
family check. Zero model calls. Committed before any E6b held-out output is read.

  H6-1  ΔF1(DEB − SC) > 0                          } Holm over the two (two-sided bug-level bootstrap p; a hypothesis is
  H6-2  MCC(DEB) > 0 (95% bug-level CI excludes 0)  } supported when its Holm-adjusted p < alpha and the estimate is > 0)
  H6-3  ΔF1(selective SC − its own SC) > 0 at the frozen τ = 80 (tuned on the dev pilot for M1's SC, D2 of D-82);
        one-sided reading of the two-sided 95% interval (supported when its lower bound is > 0); outside the Holm
        family. ΔF1 of the selective rule against keep-all reported, not tested; the arm's own MCC reported
        (no MCC difference against keep-all, whose MCC is 0 by definition — D-82 correction).
  Family check (D-82 purpose: M2 shares the generator's family): per arm, paired E6b − M1 and E6b − M2 deltas in F1
        and MCC on the common instance set, and each model's DEB − SC and SC − J1. Descriptive: no test.

E6b and M2 are scored on their single replicate, M1 on all three (as in R3 and the 35b comparison). KA is model-free
and taken from the M1 run. Instances aborted by the S1 leakage guard in any of the three runs are dropped (D-70).
If the stopping rule ended a pass early, the scored set is the instances with an E6b decision in every arm compared.

    python scripts/analysis/e6b_analysis.py   -> results/e6b/analysis/e6b_d1test.json
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import exploratory_d82 as x  # noqa: E402
from triage import analysis, config, expl_profile, stats  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

RUNS = ROOT / "results" / "runs_local"
OUT = ROOT / "results" / "e6b" / "analysis" / "e6b_d1test.json"
MODELS = {"M1": ("LOCAL_HO_E1E3_M1", None), "M2": ("LOCAL_HO_E5R3_M2", "M2"), "E6B": ("LOCAL_HO_E6B_D1TEST", "E6B")}
ARMS = ("J1", "SC", "DEB")
TAU_SC = 80                                     # frozen (D-82 H6-3); asserted against the committed D2 output


def cond(arm: str, model: str, sel: bool = False) -> str:
    base = f"{arm}|S1" if model == "M1" else f"{arm}|S1|{model}"
    return base + "_sel" if sel else base


def load(run: str, tag):
    keep = lambda r: r["arm"] in ARMS and r.get("level") == "S1" and (r.get("variant") or "full") == "full"
    ds = [d for d in read_jsonl(RUNS / run / "decisions.jsonl") if keep(d)]
    rf = RUNS / run / "leakage_rejections.jsonl"
    rj = {r["instance_id"] for r in read_jsonl(rf) if keep(r)} if rf.exists() else set()
    return ([{**d, "variant": tag} for d in ds] if tag else ds), rj


def metric_p(ev, c: str, metric: str) -> float:
    """Two-sided bootstrap p of metric(c) against 0 (H6-2), same bug resamples as every other interval."""
    return stats.bootstrap_p_two_sided(stats.bootstrap_metric(ev.tensor(c), metric, ev.W))


def main():
    tau = json.loads((ROOT / "results" / "heldout" / "analysis_final" / "D1_M1" / "tables" / "exploratory_d82.json")
                     .read_text(encoding="utf-8"))["D2"]["tau"]["SC"]
    assert tau == TAU_SC, f"frozen τ for SC is {TAU_SC}, committed D2 says {tau}"
    prof = json.loads(expl_profile.E6B_PROFILE_FILE.read_text(encoding="utf-8"))
    sel_rec = json.loads((ROOT / "results" / "e6b" / "selection.json").read_text(encoding="utf-8"))
    assert sel_rec["selected"] == prof["model_tag"]
    loaded = {m: load(*v) for m, v in MODELS.items()}
    aborted = set().union(*(a for _, a in loaded.values()))
    m1_all = list(read_jsonl(RUNS / MODELS["M1"][0] / "decisions.jsonl"))
    ka = [d for d in m1_all if d["arm"] == "KA"]
    e6 = loaded["E6B"][0]
    sel = [{**d, "variant": "E6B_sel", "label_raw": x.selective(d, TAU_SC)} for d in e6 if d["arm"] == "SC"]
    samp = json.loads((config.PROCESSED / "sample_D1_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl") if l["instance_id"] in keep]
    excl = {("S1", v): aborted for v in ("full", "M2", "E6B", "E6B_sel")}
    decs = [d for ds, _ in loaded.values() for d in ds] + sel + ka
    ev = analysis.Evaluation(decs, labels, samp["tf_weights"], exclusions=excl)

    decided = {a: {d["instance_id"] for d in e6 if d["arm"] == a} for a in ARMS}
    e6_ids = ev.comparison_set([cond(a, "E6B") for a in ARMS] + [cond("SC", "E6B", True)],
                               restrict=set.intersection(*decided.values()))
    eve = ev._restricted(e6_ids)

    # H6-1, H6-2 (Holm over the two)
    h1 = eve.contrast("H6-1 DEB - SC (E6b)", [cond("DEB", "E6B")], [cond("SC", "E6B")], "f1")
    deb = eve.summary(cond("DEB", "E6B"))
    p2 = metric_p(eve, cond("DEB", "E6B"), "mcc")
    adj = stats.holm([h1.p, p2])
    hyp = {"H6-1": {"what": "ΔF1(DEB − SC) > 0", "delta": h1.delta, "ci95": h1.ci95, "p": h1.p, "p_holm": adj[0],
                    "estimate_DEB": h1.estimate_a, "estimate_SC": h1.estimate_b,
                    "supported": bool(adj[0] < config.ALPHA and h1.delta > 0)},
           "H6-2": {"what": "MCC(DEB) > 0", "mcc": deb["mcc"], "ci95": deb["mcc_ci95"], "p": p2, "p_holm": adj[1],
                    "ci_excludes_0": bool(deb["mcc_ci95"][0] > 0),
                    "supported": bool(adj[1] < config.ALPHA and deb["mcc"] > 0)},
           "holm_family": ["H6-1", "H6-2"], "alpha": config.ALPHA}

    # H6-3 (exploratory, outside the family)
    sc_sel, sc = cond("SC", "E6B", True), cond("SC", "E6B")
    h3 = eve.contrast("H6-3 selective SC - SC (E6b)", [sc_sel], [sc], "f1")
    vka = eve.contrast("selective SC - KA (E6b)", [sc_sel], ["KA"], "f1")
    s_sel, s_sc = eve.summary(sc_sel), eve.summary(sc)
    sel_in = [d for d in sel if d["instance_id"] in eve.lab]
    hyp["H6-3"] = {"what": "ΔF1(selective SC − its own SC) > 0 at frozen τ = 80", "tau": TAU_SC,
                   "delta": h3.delta, "ci95": h3.ci95, "p": h3.p, "supported": bool(h3.ci95[0] > 0),
                   "reading": "one-sided reading of the two-sided 95% interval (D-82); exploratory, outside the Holm family",
                   "selective_f1": s_sel["f1"], "sc_f1": s_sc["f1"], "selective_mcc": s_sel["mcc"],
                   "selective_mcc_ci95": s_sel["mcc_ci95"], "pf_lost_selective": s_sel["pf_lost"],
                   "pf_lost_sc": s_sc["pf_lost"], "pf_in_set": s_sel["TP"] + s_sel["FN"],
                   "share_discarded": sum(d["label_raw"] == x.TF for d in sel_in) / len(sel_in) if sel_in else None,
                   "vs_keep_all": {"ka_f1": eve.baseline_summary("KA")["f1"], "delta_f1": vka.delta, "ci95": vka.ci95,
                                   "note": "reported, not tested"}}

    # descriptive family check on the common instance set of all three models
    common = ev.comparison_set([cond(a, m) for a in ARMS for m in MODELS], restrict=e6_ids)
    evc = ev._restricted(common)
    fam = {"n_instances": len(common), "n_bugs": len(evc.bugs),
           "summary": {m: {a: {k: evc.summary(cond(a, m))[k] for k in ("f1", "f1_ci95", "mcc", "mcc_ci95", "precision", "recall")}
                           for a in ARMS} for m in MODELS},
           "e6b_minus": {f"{a} E6B-{m}": {k: vars(evc.contrast(f"{a} E6B-{m}", [cond(a, "E6B")], [cond(a, m)], k))
                                          for k in ("f1", "mcc")} for a in ARMS for m in ("M1", "M2")},
           "within_model": {m: {"DEB-SC": vars(evc.contrast(f"DEB-SC ({m})", [cond("DEB", m)], [cond("SC", m)], "f1")),
                                "SC-J1": vars(evc.contrast(f"SC-J1 ({m})", [cond("SC", m)], [cond("J1", m)], "f1"))}
                            for m in MODELS},
           "note": "descriptive, no test: M2 shares the generator's (Gemma) family, E6b is outside it (D-82)"}

    out = {"label": prof["label"], "model": prof["model_tag"], "digest": prof["model_spec"]["digest"],
           "differences_from_M1": prof["differences_from_M1"], "decisions": ["D-82", "D-85", "D-86", "D-87"],
           "dataset": "D1", "split": "test", "level": "S1", "replicates": {m: sorted({d["replicate"] for d in ds})
                                                                          for m, (ds, _) in loaded.items()},
           "n_instances": len(e6_ids), "n_bugs": len(eve.bugs),
           "pf_prevalence": analysis.judged_prevalence(labels, sorted(e6_ids)),
           "e6b_decided_per_arm": {a: len(v) for a, v in decided.items()}, "aborted_excluded": sorted(aborted),
           "summary": {a: {k: eve.summary(cond(a, "E6B"))[k] for k in ("f1", "f1_ci95", "mcc", "mcc_ci95", "precision",
                                                                       "recall", "invalid_rate", "pf_lost")} for a in ARMS},
           "hypotheses": hyp, "family_check": fam,
           "note": ("E6b is a robustness check with a third model family, not confirmatory evidence for the primary "
                    "hypotheses and not the stronger-judge evidence (E6a, E9). " + analysis.F1_NOT_COMPARABLE)}
    dump_json(OUT, out)
    r = lambda v: round(v, 3)
    print(f"E6b {out['model']}  n={out['n_instances']} bugs={out['n_bugs']}")
    for a in ARMS:
        s = out["summary"][a]
        print(f"  {a}: F1 {r(s['f1'])} {[r(c) for c in s['f1_ci95']]}  MCC {r(s['mcc'])} {[r(c) for c in s['mcc_ci95']]}")
    for h in ("H6-1", "H6-2", "H6-3"):
        v = hyp[h]
        est = v.get("delta", v.get("mcc"))
        print(f"  {h}: {r(est)} {[r(c) for c in v['ci95']]} p={r(v['p'])} p_holm={r(v['p_holm']) if 'p_holm' in v else '-'} "
              f"supported={v['supported']}")


if __name__ == "__main__":
    main()
