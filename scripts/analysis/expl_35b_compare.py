"""EXPLORATORY qwen3.5:35b (D-67/D-76/D-78) read against M1 and M2 on D1-test, J1 and DEB at S1.

Not a confirmatory result and not a like-for-like model comparison: the 35b ran under conditions that differ from
M1's (configs/expl_35b.json "differences_from_M1", repeated in every output here). No Holm, no hypothesis test.

The 35b's D-78 safety abort stopped DEB before every instance was reached and SC never started, so the scored set is
the labelled D1-test instances with a 35b decision in BOTH arms, minus the S1 leakage aborts of any of the three runs
(D-70). M1 is scored on all its replicates, M2 and the 35b on their single replicate (as in R3). Decisions are held
under the variant tags "M2" / "35B" in memory only, so no condition name is shared between models.

    python scripts/analysis/expl_35b_compare.py   -> results/expl_35b/analysis/
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import analysis, config, expl_profile  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

RUNS = ROOT / "results" / "runs_local"
OUT = ROOT / "results" / "expl_35b" / "analysis"
MODELS = {"M1": ("LOCAL_HO_E1E3_M1", None), "M2": ("LOCAL_HO_E5R3_M2", "M2"), "35B": ("EXPL_35B_D1TEST", "35B")}
ARMS = ("J1", "DEB")
METRICS = ("f1", "mcc", "precision", "recall")


def load(run: str, tag):
    keep = lambda r: r["arm"] in ARMS and r.get("level") == "S1" and (r.get("variant") or "full") == "full"
    ds = [d for d in read_jsonl(RUNS / run / "decisions.jsonl") if keep(d)]
    rj = {r["instance_id"] for r in read_jsonl(RUNS / run / "leakage_rejections.jsonl") if keep(r)}
    return ([{**d, "variant": tag} for d in ds] if tag else ds), rj


def cond(arm: str, model: str) -> str:
    return f"{arm}|S1" if model == "M1" else f"{arm}|S1|{model}"


def main():
    p = expl_profile.load()
    label = {"label": p["label"], "model": p["model_tag"], "differences_from_M1": p["differences_from_M1"],
             "decisions": ["D-67", "D-76", "D-77", "D-78"]}
    loaded = {m: load(*v) for m, v in MODELS.items()}
    decs = [d for ds, _ in loaded.values() for d in ds]
    aborted = set().union(*(x for _, x in loaded.values()))
    samp = json.loads((config.PROCESSED / "sample_D1_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl") if l["instance_id"] in keep]
    excl = {("S1", "full"): aborted, ("S1", "M2"): aborted, ("S1", "35B"): aborted}
    ev = analysis.Evaluation(decs, labels, samp["tf_weights"], exclusions=excl)
    done35 = {a: {d["instance_id"] for d in loaded["35B"][0] if d["arm"] == a} for a in ARMS}
    attempted = {a: done35[a] | {r["instance_id"] for r in read_jsonl(RUNS / MODELS["35B"][0] / "leakage_rejections.jsonl")
                                 if r["arm"] == a} for a in ARMS}
    not_reached = sorted(attempted["J1"] - attempted["DEB"])
    ids = ev.comparison_set([cond(a, m) for a in ARMS for m in MODELS], restrict=done35["J1"] & done35["DEB"])
    evr = ev._restricted(ids)
    out = {**label, "dataset": "D1", "split": "test", "level": "S1", "runs": {m: v[0] for m, v in MODELS.items()},
           "n_instances": len(ids), "n_bugs": len(evr.bugs),
           "pf_prevalence": analysis.judged_prevalence(labels, sorted(ids)),
           "deb_not_reached_by_35b": not_reached, "sc": "not run (D-78 safety abort during DEB)",
           "aborted_excluded": sorted(aborted), "replicates": {m: sorted({d["replicate"] for d in ds})
                                                              for m, (ds, _) in loaded.items()},
           "summary": {m: {a: {k: evr.summary(cond(a, m))[k] for k in METRICS + ("precision_prev_adj",)}
                           for a in ARMS} for m in MODELS},
           "deb_minus_j1": {m: {k: vars(ev.contrast(f"DEB-J1 ({m})", [cond("DEB", m)], [cond("J1", m)], k, restrict=ids))
                                for k in ("f1", "mcc")} for m in MODELS},
           "35b_minus": {f"{a} 35B-{m}": {k: vars(ev.contrast(f"{a} 35B-{m}", [cond(a, "35B")], [cond(a, m)], k,
                                                               restrict=ids)) for k in ("f1", "mcc")}
                         for a in ARMS for m in ("M1", "M2")},
           "note": ("EXPLORATORY: no confirmatory test, no multiplicity correction; the 35b ran under different "
                    "conditions from M1 (see differences_from_M1), so differences are not attributable to the model "
                    "alone and are not equivalent to the original proprietary-model design. "
                    + analysis.F1_NOT_COMPARABLE)}
    dump_json(OUT / "LABEL.json", label)
    dump_json(OUT / "expl_35b_vs_m1_m2.json", out)
    print(f"EXPLORATORY 35b  n={out['n_instances']} bugs={out['n_bugs']} not_reached(DEB)={len(not_reached)}")
    for m in MODELS:
        print(m, {a: {k: round(out["summary"][m][a][k], 3) for k in ("f1", "mcc")} for a in ARMS},
              "DEB-J1 F1", round(out["deb_minus_j1"][m]["f1"]["delta"], 3))
    for k, v in out["35b_minus"].items():
        print(k, {x: (round(v[x]["delta"], 3), [round(c, 3) for c in v[x]["ci95"]]) for x in ("f1", "mcc")})


if __name__ == "__main__":
    main()
