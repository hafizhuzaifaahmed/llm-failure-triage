"""E5-R3 cross-model check (Phase 2 R3): the E3 arms at S1 with M2, on D1-test and D2, "checking whether the
architecture ranking depends on the model". Exploratory robustness: no confirmatory test, no Holm.

For each dataset: the arm ranking by F1 and MCC under M1 and under M2, the within-model architecture contrasts
(DEB-SC, SC-J1, DEB-J1) under each model, and M2-M1 per arm, all on one instance set (labelled, minus the S1
leakage aborts of either run, D-70) with the bug-clustered paired bootstrap. M1 is scored on all its replicates
(3 on D1-test, 1 on D2), M2 on its single replicate. M2 decisions are held under the variant tag "M2" in memory
only, so the two models never share a condition name.

    python scripts/analysis/model_robustness_r3.py   -> results/heldout/analysis_final/R3/
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import analysis, config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

RUNS = ROOT / "results" / "runs_local"
OUT = ROOT / "results" / "heldout" / "analysis_final" / "R3"
SETS = {"D1": ("LOCAL_HO_E1E3_M1", "LOCAL_HO_E5R3_M2"), "D2": ("LOCAL_HO_E5R1_D2", "LOCAL_HO_E5R3_M2_D2")}
ARMS = ("J1", "SC", "DEB")
PAIRS = (("DEB", "SC"), ("SC", "J1"), ("DEB", "J1"))
METRICS = ("f1", "mcc", "precision", "recall")


def load(run: str, tag: str | None):
    ds = [d for d in read_jsonl(RUNS / run / "decisions.jsonl")
          if d["arm"] in ARMS and d.get("level") == "S1" and (d.get("variant") or "full") == "full"]
    rj = [r for r in read_jsonl(RUNS / run / "leakage_rejections.jsonl")
          if r["arm"] in ARMS and r.get("level") == "S1" and (r.get("variant") or "full") == "full"]
    if tag:
        ds = [{**d, "variant": tag} for d in ds]
    return ds, {r["instance_id"] for r in rj}


def cond(arm: str, model: str) -> str:
    return f"{arm}|S1" if model == "M1" else f"{arm}|S1|M2"


def one(dataset: str) -> dict:
    m1_run, m2_run = SETS[dataset]
    d1, x1 = load(m1_run, None)
    d2, x2 = load(m2_run, "M2")
    samp = json.loads((config.PROCESSED / f"sample_{dataset}_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / f"labels_{dataset}.jsonl") if l["instance_id"] in keep]
    aborted = x1 | x2
    ev = analysis.Evaluation(d1 + d2, labels, samp["tf_weights"],
                             exclusions={("S1", "full"): aborted, ("S1", "M2"): aborted})
    ids = ev.comparison_set([cond(a, m) for a in ARMS for m in ("M1", "M2")])
    evr = ev._restricted(ids)
    out = {"dataset": dataset, "runs": {"M1": m1_run, "M2": m2_run}, "n_instances": len(ids),
           "n_bugs": len(evr.bugs), "aborted_excluded": sorted(aborted), "abort_sets_equal": x1 == x2,
           "replicates": {m: sorted({d["replicate"] for d in ds}) for m, ds in (("M1", d1), ("M2", d2))},
           "summary": {}, "ranking": {}, "within_model": {}, "m2_minus_m1": {}}
    for m in ("M1", "M2"):
        out["summary"][m] = {a: {k: evr.summary(cond(a, m))[k] for k in METRICS + ("precision_prev_adj",)}
                             for a in ARMS}
        out["ranking"][m] = {k: sorted(ARMS, key=lambda a: -out["summary"][m][a][k]) for k in ("f1", "mcc")}
        out["within_model"][m] = {f"{a}-{b}": {k: vars(ev.contrast(f"{a}-{b} ({m})", [cond(a, m)], [cond(b, m)], k,
                                                                    restrict=ids)) for k in ("f1", "mcc")}
                                  for a, b in PAIRS}
    out["ranking_same"] = {k: out["ranking"]["M1"][k] == out["ranking"]["M2"][k] for k in ("f1", "mcc")}
    out["contrast_signs_agree"] = {
        f"{a}-{b}": {k: (out["within_model"]["M1"][f"{a}-{b}"][k]["delta"] > 0)
                     == (out["within_model"]["M2"][f"{a}-{b}"][k]["delta"] > 0) for k in ("f1", "mcc")}
        for a, b in PAIRS}
    out["m2_minus_m1"] = {a: {k: vars(ev.contrast(f"{a} M2-M1", [cond(a, "M2")], [cond(a, "M1")], k, restrict=ids))
                              for k in ("f1", "mcc")} for a in ARMS}
    out["note"] = ("Exploratory robustness (Phase 2 R3): no confirmatory test, no multiplicity correction. "
                   + analysis.F1_NOT_COMPARABLE)
    return out


def main():
    res = {d: one(d) for d in SETS}
    dump_json(OUT / "r3_model_robustness.json", res)
    for d, r in res.items():
        print(f"{d}: n={r['n_instances']} bugs={r['n_bugs']} ranking F1 M1={r['ranking']['M1']['f1']} "
              f"M2={r['ranking']['M2']['f1']} same={r['ranking_same']}")


if __name__ == "__main__":
    main()
