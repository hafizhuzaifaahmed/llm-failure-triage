"""E9b memorisation check (D-104): Claude Sonnet 5.5, J1 and DEB at S1, one replicate each, on the scored D2 seeded-fault
instances. Zero model calls. Committed before any E9b output exists.

  H11-1  MCC(Sonnet DEB, D2) > 0                      } two-sided bug-level bootstrap p (B and seed as every analysis);
  H11-2  ΔMCC(Sonnet DEB − M1 DEB) on D2 > 0, paired  } Holm over the two; supported when p_Holm < alpha and the
                                                         estimate is > 0. M1 DEB = the committed D2 run LOCAL_HO_E5R1_D2
                                                         (all its replicates, as every D2 figure in the paper).
  MCC, not F1, because D2's PF prevalence differs from D1's (F1 depends on prevalence).
  Descriptive, not tested: Sonnet's D1 − D2 MCC for DEB and J1 (D1 from results/e9/analysis/e9_d1test.json; D1 DEB has
  three replicates, D2 one); F1 per arm; Sonnet J1 on D2; M1 J1 on D2; refusals, invalid rate, calls, spend.
Labelled "frontier reference point, not a protocol replication"; exploratory, no family with M1's confirmatory tests.

    python scripts/analysis/e9b_analysis.py   -> results/e9b/analysis/e9b_d2.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import analysis, config, frontier, stats  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

RUN = ROOT / "results" / "runs_frontier" / "E9B_SONNET55_D2"
LOG = ROOT / "data" / "raw" / "llm_calls_frontier_e9b" / "claude-sonnet-5-5.jsonl"
M1 = ROOT / "results" / "runs_local" / "LOCAL_HO_E5R1_D2"
E9 = ROOT / "results" / "e9" / "analysis" / "e9_d1test.json"
OUT = ROOT / "results" / "e9b" / "analysis" / "e9b_d2.json"
CAP_USD = 11.00
DEVIATIONS = ["Claude Sonnet 5.5 through the Message Batches API (a deviation from the zero-API-cost rule, D-21)",
              "the model's default sampling: temperature/top_p/top_k cannot be sent (a 400 on this model)",
              "no seeds; samples are not seed-reproducible", "structured outputs (closed schema) instead of Ollama's format",
              "thinking off via between_tools (no tools sent)",
              "J1 and DEB one replicate each (justified by Sonnet's DEB run-to-run F1 range 0.024 in E9, D-94/D-97)"]
KEYS = ("f1", "mcc", "mcc_ci95", "precision", "recall", "pf_lost", "invalid_rate", "n_instances")


def s1(d):
    return d.get("level") == "S1" and (d.get("variant") or "full") == "full"


def main():
    son = [{**d, "variant": "SON"} for d in read_jsonl(RUN / "decisions.jsonl") if d["arm"] in ("J1", "DEB") and s1(d)]
    m1 = [d for d in read_jsonl(M1 / "decisions.jsonl") if d["arm"] in ("J1", "DEB") and s1(d)]
    samp = json.loads((config.PROCESSED / "sample_D2_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / "labels_D2.jsonl") if l["instance_id"] in keep]
    aborted = {r["instance_id"] for f in (M1 / "leakage_rejections.jsonl", RUN / "leakage_rejections.jsonl")
               for r in read_jsonl(f) if r.get("level") == "S1"}
    ev = analysis.Evaluation(son + m1, labels, samp.get("tf_weights"),
                             exclusions={("S1", "full"): aborted, ("S1", "SON"): aborted})
    conds = ["J1|S1|SON", "DEB|S1|SON", "J1|S1", "DEB|S1"]
    ids = ev.comparison_set(conds)
    evr = ev._restricted(ids)
    deb = evr.summary("DEB|S1|SON")
    p1 = stats.bootstrap_p_two_sided(stats.bootstrap_metric(evr.tensor("DEB|S1|SON"), "mcc", evr.W))
    h2 = evr.contrast("H11-2 DEB Sonnet - M1 (MCC)", ["DEB|S1|SON"], ["DEB|S1"], "mcc")
    adj = stats.holm([p1, h2.p])
    hyp = {"H11-1": {"what": "MCC(Sonnet DEB, D2) > 0", "mcc": deb["mcc"], "ci95": deb["mcc_ci95"], "p": p1,
                     "p_holm": adj[0], "supported": bool(adj[0] < config.ALPHA and deb["mcc"] > 0)},
           "H11-2": {"what": "ΔMCC(Sonnet DEB − M1 DEB) on D2 > 0, paired, bug-level bootstrap", "delta": h2.delta,
                     "ci95": h2.ci95, "p": h2.p, "p_holm": adj[1],
                     "supported": bool(adj[1] < config.ALPHA and h2.delta > 0)}}
    e9 = json.loads(E9.read_text(encoding="utf-8"))
    d1_minus_d2 = {}
    for arm in ("J1", "DEB"):
        d1 = e9["summary"][f"{arm}|S1|SON"]["mcc"]
        d2 = evr.summary(f"{arm}|S1|SON")["mcc"]
        d1_minus_d2[arm] = {"mcc_d1": d1, "mcc_d2": d2, "d1_minus_d2": d1 - d2,
                            "note": "descriptive, not tested; different instances and prevalence; D1 DEB has three "
                                    "replicates, D2 one"}
    calls = list(read_jsonl(LOG))
    out = {"label": frontier.LABEL, "model": frontier.MODEL, "deviations_from_local_protocol": DEVIATIONS,
           "decisions": ["D-92", "D-97", "D-104"], "dataset": "D2", "split": "test", "level": "S1",
           "n_instances": len(ids), "n_bugs": len(evr.bugs),
           "pf_prevalence": analysis.judged_prevalence(labels, sorted(ids)),
           "summary": {c: {k: evr.summary(c).get(k) for k in KEYS} for c in conds}, "hypotheses": hyp,
           "sonnet_minus_m1": {a: {m: vars(evr.contrast(f"{a} Sonnet-M1", [f"{a}|S1|SON"], [f"{a}|S1"], m))
                                   for m in ("f1", "mcc")} for a in ("J1", "DEB")},
           "sonnet_d1_minus_d2_mcc": d1_minus_d2,
           "calls": len(calls), "refusals": sum(c.get("finish_reason") == "refusal" for c in calls),
           "failed_after_resubmission": sum(str(c.get("finish_reason", "")).startswith("error:") for c in calls),
           "spend_usd": sum(c.get("cost_usd") or 0.0 for c in calls), "cap_usd": CAP_USD,
           "note": "frontier reference point, not a protocol replication; memorisation check (D-104); exploratory. "
                   + analysis.F1_NOT_COMPARABLE}
    dump_json(OUT, out)
    r = lambda v: round(v, 3)
    print(f"E9b {out['model']} n={out['n_instances']} calls={out['calls']} refusals={out['refusals']} "
          f"spend ${out['spend_usd']:.2f}")
    for c, s in out["summary"].items():
        print(f"  {c}: F1 {r(s['f1'])} MCC {r(s['mcc'])} lost {r(s['pf_lost'])}")
    for h, v in hyp.items():
        est = v.get("delta", v.get("mcc"))
        print(f"  {h}: {r(est)} {[r(x) for x in v['ci95']]} p_holm={r(v['p_holm'])} supported={v['supported']}")
    for a, v in d1_minus_d2.items():
        print(f"  Sonnet {a} MCC D1 {r(v['mcc_d1'])} - D2 {r(v['mcc_d2'])} = {r(v['d1_minus_d2'])}")


if __name__ == "__main__":
    main()
