"""E9 frontier reference point, not a protocol replication (D-92, D-96, D-97): Claude Sonnet 5.5, J1 (one replicate) and
DEB (three replicates, D-97) at S1 on the 177
scored D1-test instances. Zero model calls. Committed before any E9 output exists.

  H9-1  ΔF1(DEB − J1) > 0           } two-sided bug-level bootstrap p; reported unadjusted and Holm over the two;
  H9-2  MCC(DEB) > 0 (CI excludes 0) } supported when p_Holm < alpha and the estimate is > 0. Exploratory: no family with
                                       M1's confirmatory tests.
  Sonnet − M1 per arm (F1, MCC; M1 on its three replicates): reported, not tested.
  Descriptive extra (D-95 was pre-registered first): Sonnet's J1 beside KUU on D1 (post hoc) and M1's J1 — F1, MCC,
  PF tests lost.
  D-97: DEB's run-to-run spread (per-replicate F1 and MCC, range, SD) for Sonnet beside M1's.
  Also reported: refusals, invalid rate, calls, and the spend from logged usage.
Every output carries the label and the deviations from the local protocol (sampling defaults, no seeds, structured
outputs instead of Ollama's format, thinking off via between_tools).

    python scripts/analysis/e9_analysis.py   -> results/e9/analysis/e9_d1test.json
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import analysis, config, frontier, stats  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

RUN = ROOT / "results" / "runs_frontier" / "E9_SONNET55_D1TEST"
M1 = ROOT / "results" / "runs_local" / "LOCAL_HO_E1E3_M1"
KUU = ROOT / "results" / "kuu" / "analysis" / "kuu_d1_posthoc.json"
OUT = ROOT / "results" / "e9" / "analysis" / "e9_d1test.json"
DEVIATIONS = ["Claude Sonnet 5.5 through the Message Batches API (a deviation from the zero-API-cost rule, D-21)",
              "the model's default sampling: temperature/top_p/top_k cannot be sent (a 400 on this model)",
              "no seeds; samples are not seed-reproducible", "structured outputs (closed schema) instead of Ollama's format",
              "thinking off via between_tools (no tools sent)", "J1 one replicate, DEB three (M1: three each)"]
KEYS = ("f1", "f1_ci95", "mcc", "mcc_ci95", "precision", "recall", "pf_lost", "invalid_rate", "n_instances")


def s1(d):
    return d.get("level") == "S1" and (d.get("variant") or "full") == "full"


def main():
    son = [{**d, "variant": "SON"} for d in read_jsonl(RUN / "decisions.jsonl") if d["arm"] in ("J1", "DEB") and s1(d)]
    m1 = [d for d in read_jsonl(M1 / "decisions.jsonl") if d["arm"] in ("J1", "DEB") and s1(d)]
    samp = json.loads((config.PROCESSED / "sample_D1_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl") if l["instance_id"] in keep]
    aborted = {r["instance_id"] for f in (M1 / "leakage_rejections.jsonl", RUN / "leakage_rejections.jsonl")
               for r in read_jsonl(f) if r.get("level") == "S1"}
    ev = analysis.Evaluation(son + m1, labels, samp["tf_weights"],
                             exclusions={("S1", "full"): aborted, ("S1", "SON"): aborted})
    conds = ["J1|S1|SON", "DEB|S1|SON", "J1|S1", "DEB|S1"]
    ids = ev.comparison_set(conds)
    evr = ev._restricted(ids)
    h1 = evr.contrast("H9-1 DEB - J1 (Sonnet)", ["DEB|S1|SON"], ["J1|S1|SON"], "f1")
    deb = evr.summary("DEB|S1|SON")
    p2 = stats.bootstrap_p_two_sided(stats.bootstrap_metric(evr.tensor("DEB|S1|SON"), "mcc", evr.W))
    adj = stats.holm([h1.p, p2])
    hyp = {"H9-1": {"what": "ΔF1(DEB − J1) > 0", "delta": h1.delta, "ci95": h1.ci95, "p": h1.p, "p_holm": adj[0],
                    "supported": bool(adj[0] < config.ALPHA and h1.delta > 0)},
           "H9-2": {"what": "MCC(DEB) > 0", "mcc": deb["mcc"], "ci95": deb["mcc_ci95"], "p": p2, "p_holm": adj[1],
                    "ci_excludes_0": bool(deb["mcc_ci95"][0] > 0), "supported": bool(adj[1] < config.ALPHA and deb["mcc"] > 0)}}
    # D-97: Sonnet's run-to-run spread for DEB (three replicates) beside M1's (replicate_noise.json, D-94)
    spread = {}
    for name, c in (("sonnet", "DEB|S1|SON"), ("m1", "DEB|S1")):
        T = evr.tensor(c)
        row = {}
        for m in ("f1", "mcc"):
            v = [stats.point_estimate(T[:, i:i + 1, :], m) for i in range(T.shape[1])]
            row[m] = {"per_replicate": v, "range": max(v) - min(v) if v else None,
                      "sd": float(np.std(v, ddof=1)) if len(v) > 1 else None}
        spread[name] = row
    calls = list(read_jsonl(frontier.LOG_DIR / "claude-sonnet-5-5.jsonl"))
    kuu = json.loads(KUU.read_text(encoding="utf-8")) if KUU.exists() else None
    out = {"label": frontier.LABEL, "model": frontier.MODEL, "deviations_from_local_protocol": DEVIATIONS,
           "decisions": ["D-92", "D-96", "D-97"], "dataset": "D1", "split": "test", "level": "S1",
           "n_instances": len(ids), "n_bugs": len(evr.bugs),
           "summary": {c: {k: evr.summary(c).get(k) for k in KEYS} for c in conds}, "hypotheses": hyp,
           "sonnet_minus_m1": {f"{a}": {m: vars(evr.contrast(f"{a} Sonnet-M1", [f"{a}|S1|SON"], [f"{a}|S1"], m))
                                        for m in ("f1", "mcc")} for a in ("J1", "DEB")},
           "descriptive_extra_vs_kuu": {"sonnet_j1": {k: evr.summary("J1|S1|SON").get(k) for k in ("f1", "mcc", "pf_lost")},
                                        "m1_j1": {k: evr.summary("J1|S1").get(k) for k in ("f1", "mcc", "pf_lost")},
                                        "kuu_d1_posthoc": ({k: kuu["summary"]["KUU|S1"].get(k) for k in ("f1", "mcc", "pf_lost")}
                                                           if kuu else None),
                                        "note": "descriptive only; KUU on D1 is post hoc"},
           "deb_run_to_run_spread": spread,
           "calls": len(calls), "refusals": sum(c.get("finish_reason") == "refusal" for c in calls),
           "failed_after_resubmission": sum(str(c.get("finish_reason", "")).startswith("error:") for c in calls),
           "spend_usd": sum(c.get("cost_usd") or 0.0 for c in calls), "cap_usd": frontier.CAP_USD,
           "note": "frontier reference point, not a protocol replication; exploratory. " + analysis.F1_NOT_COMPARABLE}
    dump_json(OUT, out)
    r = lambda v: round(v, 3)
    print(f"E9 {out['model']} n={out['n_instances']} calls={out['calls']} refusals={out['refusals']} "
          f"spend ${out['spend_usd']:.2f}")
    for c, s in out["summary"].items():
        print(f"  {c}: F1 {r(s['f1'])} MCC {r(s['mcc'])} lost {r(s['pf_lost'])}")
    for h, v in hyp.items():
        est = v.get("delta", v.get("mcc"))
        print(f"  {h}: {r(est)} {[r(x) for x in v['ci95']]} p_holm={r(v['p_holm'])} supported={v['supported']}")


if __name__ == "__main__":
    main()
