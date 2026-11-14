"""E7a second generator (D-82, D-100): H7-1 and H7-2 on the D1G2 test sample judged by M1. Zero model calls.
Committed before any E7a generation.

  H7-1  ΔF1(J1 without failure evidence − J1) < 0 on the new tests   } Holm over the two (two-sided bug-level bootstrap
  H7-2  MCC(DEB) > 0 (95% bug-level CI excludes 0)                   } p); H7-1 supported when p_Holm < alpha and Δ < 0,
                                                                        H7-2 when p_Holm < alpha and MCC > 0.
Reported beside: F1, MCC, precision, recall, PF tests lost per arm and baseline; the corpus (generated, executed, PF
share of executed tests, judged sample, prevalence) from dataset_summary_D1G2.json; set against G's D1-test values,
descriptively. D-70: leakage aborts are dropped per level and variant. AMB is outside the primary analysis.

    python scripts/analysis/e7a_analysis.py   -> results/e7a/analysis/e7a_d1g2.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import analysis, config, stats  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

DATASET = "D1G2"
RUN = ROOT / "results" / "runs_local" / "LOCAL_HO_E7A_M1"
OUT = ROOT / "results" / "e7a" / "analysis" / "e7a_d1g2.json"
KEYS = ("f1", "f1_ci95", "mcc", "mcc_ci95", "precision", "recall", "pf_lost", "invalid_rate", "n_instances")


def main():
    decs = list(read_jsonl(RUN / "decisions.jsonl"))
    samp = json.loads((config.PROCESSED / f"sample_{DATASET}_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / f"labels_{DATASET}.jsonl") if l["instance_id"] in keep]
    rej = list(read_jsonl(RUN / "leakage_rejections.jsonl"))
    ev = analysis.Evaluation(decs, labels, samp.get("tf_weights"), exclusions=analysis.abort_exclusions(rej))
    c1 = ev.contrast("H7-1 J1 noF - J1", ["J1|S1|noF"], ["J1|S1"], "f1")
    deb_ids = ev.comparison_set(["DEB|S1"])
    evd = ev._restricted(deb_ids)
    deb = evd.summary("DEB|S1")
    p2 = stats.bootstrap_p_two_sided(stats.bootstrap_metric(evd.tensor("DEB|S1"), "mcc", evd.W))
    adj = stats.holm([c1.p, p2])
    hyp = {"H7-1": {"what": "ΔF1(J1 noF − J1) < 0", "delta": c1.delta, "ci95": c1.ci95, "p": c1.p, "p_holm": adj[0],
                    "supported": bool(adj[0] < config.ALPHA and c1.delta < 0)},
           "H7-2": {"what": "MCC(DEB) > 0", "mcc": deb["mcc"], "ci95": deb["mcc_ci95"], "p": p2, "p_holm": adj[1],
                    "ci_excludes_0": bool(deb["mcc_ci95"][0] > 0), "supported": bool(adj[1] < config.ALPHA and deb["mcc"] > 0)}}
    summ = {c: {k: ev.summary(c).get(k) for k in KEYS} for c in ("J1|S1", "J1|S1|noF", "SC|S1", "DEB|S1") if ev.by_cond.get(c)}
    summ["KA"] = {k: ev.baseline_summary("KA").get(k) for k in KEYS}
    summ["R0"] = {k: ev.baseline_summary("R0").get(k) for k in KEYS} if ev.by_cond.get("R0") else None
    corpus_f = config.PROCESSED / f"dataset_summary_{DATASET}.json"
    corpus = json.loads(corpus_f.read_text(encoding="utf-8")) if corpus_f.exists() else None
    sel = json.loads((ROOT / "results" / "e7a" / "selection.json").read_text(encoding="utf-8"))
    out = {"what": "E7a second generator (D-82, D-100)", "generator": sel.get("selected"), "dataset": DATASET,
           "split": "test", "level": "S1", "decisions": ["D-82", "D-91", "D-100"],
           "n_instances": len(ev.lab), "n_bugs": len(ev.bugs), "pf_prevalence": analysis.judged_prevalence(labels, sorted(ev.lab)),
           "aborts": sorted({(r["arm"], r.get("variant") or "full", r["instance_id"]) for r in rej}),
           "summary": summ, "hypotheses": hyp, "holm_family": ["H7-1", "H7-2"], "alpha": config.ALPHA, "corpus": corpus,
           "note": "robustness of the findings to the generator; the first generator's D1-test values are compared "
                   "descriptively only. " + analysis.F1_NOT_COMPARABLE}
    dump_json(OUT, out)
    r = lambda v: round(v, 3)
    print(f"E7a {out['generator']} n={out['n_instances']} bugs={out['n_bugs']} prevalence {out['pf_prevalence']}")
    for c, s in summ.items():
        if s:
            print(f"  {c}: F1 {r(s['f1'])} MCC {r(s['mcc'])} lost {r(s['pf_lost'])}")
    for h, v in hyp.items():
        est = v.get("delta", v.get("mcc"))
        print(f"  {h}: {r(est)} {[r(x) for x in v['ci95']]} p_holm={r(v['p_holm'])} supported={v['supported']}")


if __name__ == "__main__":
    main()
