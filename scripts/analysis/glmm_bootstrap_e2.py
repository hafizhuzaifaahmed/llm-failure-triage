"""Planned E2 mixed-model intervals (X-06, D-19; produced under D-79): bug-level cluster bootstrap of the GLMM odds ratios.

The final analysis (D-75) fitted the E2 mixed model but wrote only its variational intervals, which the protocol does
not report (they under-covered in simulation). This adds the planned intervals, `glmm.cluster_bootstrap_ci` with its
defaults (B = 200 refits, seed 20261011, CPU only), on exactly the rows `scripts/analyze.py` fits: the same runs, the
same labelled sample, the same D-70 drop of instances aborted at any level, the same invalid-as-TF policy. The point
estimates are re-fitted and checked against the committed glmm_e2.json before anything is written.

    python scripts/analysis/glmm_bootstrap_e2.py [--B 200]   -> results/heldout/analysis_final/D1_M1/tables/glmm_e2_bootstrap.json
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import analysis, config, glmm  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

RUNS = [ROOT / "results" / "runs_local" / r for r in ("LOCAL_HO_E1E3_M1", "LOCAL_HO_E4_M1")]
OUT = ROOT / "results" / "heldout" / "analysis_final" / "D1_M1" / "tables"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=200)
    ap.add_argument("--out", default=str(OUT / "glmm_e2_bootstrap.json"))
    a = ap.parse_args()
    decisions = [d for r in RUNS for d in read_jsonl(r / "decisions.jsonl")]
    exclusions = analysis.abort_exclusions(x for r in RUNS for x in read_jsonl(r / "leakage_rejections.jsonl"))
    samp = json.loads((config.PROCESSED / "sample_D1_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl") if l["instance_id"] in keep]
    ev = analysis.Evaluation(decisions, labels, samp["tf_weights"], exclusions=exclusions)
    e2_drop = set().union(*[exclusions.get((lv, "full"), set()) for lv in ("S0", "S1", "S2")])
    gdf = glmm.rows_from_decisions([d for d in decisions if d["instance_id"] not in e2_drop], ev.lab, ev.meta)
    committed = json.loads((OUT / "glmm_e2.json").read_text(encoding="utf-8"))
    out = {"what": "bug-level cluster-bootstrap 95% intervals for the E2 GLMM odds ratios (planned, X-06/D-19; D-79)",
           "function": "triage.glmm.cluster_bootstrap_ci", "B": a.B, "seed": 20261011, "models": {}}
    for cls, name in (("PROGRAM_FAULT", "PF_recall"), ("TEST_FAULT", "TF_specificity")):
        sub = gdf[gdf["y_true"] == cls]
        point = glmm.fit(sub)
        ref = {t["term"]: t["odds_ratio"] for t in committed[name]["terms"]}
        mism = [t["term"] for t in point["terms"] if abs(t["odds_ratio"] - ref[t["term"]]) > 1e-9]
        if len(sub) != committed[name]["n_rows"] or mism:
            raise SystemExit(f"{name}: re-fit does not reproduce glmm_e2.json (rows {len(sub)}, mismatched {mism})")
        t0 = time.time()
        ci = glmm.cluster_bootstrap_ci(sub, B=a.B)
        out["models"][name] = {"n_rows": len(sub), "wall_s": round(time.time() - t0, 1),
                               "terms": [{"term": t["term"], "odds_ratio": t["odds_ratio"],
                                          "or_ci95_bootstrap": ci[t["term"]]["or_ci95_bootstrap"]}
                                         for t in point["terms"]]}
        print(name, len(sub), "rows", out["models"][name]["wall_s"], "s")
        for t in out["models"][name]["terms"]:
            print(f"  {t['term'][:70]:70s} OR {t['odds_ratio']:.3f} [{t['or_ci95_bootstrap'][0]:.3f}, {t['or_ci95_bootstrap'][1]:.3f}]")
    dump_json(Path(a.out), out)


if __name__ == "__main__":
    main()
