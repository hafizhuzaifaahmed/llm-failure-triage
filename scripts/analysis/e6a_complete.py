"""E6a (D-82, D-88): the completed EXPLORATORY qwen3.5:35b read against M1 and M2 on D1-test S1, now with SC.

Same rules as expl_35b_compare.py, whose loaders and condition names are reused unchanged: the 35b ran under
conditions that differ from M1's (configs/expl_35b.json "differences_from_M1", repeated in the output); no Holm, no
hypothesis test. The scored set is the labelled D1-test instances with a 35b decision in all three arms, minus the S1
leakage aborts of any of the three runs (D-70). M1 on all its replicates, M2 and the 35b on their single replicate.
Committed before any E6a decision exists.

    python scripts/analysis/e6a_complete.py   -> results/expl_35b/analysis/e6a_complete.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import expl_35b_compare as base  # noqa: E402
from triage import analysis, config, expl_profile  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

base.ARMS = ("J1", "SC", "DEB")
ARMS, MODELS, cond = base.ARMS, base.MODELS, base.cond
OUT = base.OUT / "e6a_complete.json"
PAIRS = (("DEB", "SC"), ("SC", "J1"), ("DEB", "J1"))


def main():
    p = expl_profile.load()
    loaded = {m: base.load(*v) for m, v in MODELS.items()}
    decs = [d for ds, _ in loaded.values() for d in ds]
    aborted = set().union(*(x for _, x in loaded.values()))
    samp = json.loads((config.PROCESSED / "sample_D1_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl") if l["instance_id"] in keep]
    excl = {("S1", v): aborted for v in ("full", "M2", "35B")}
    ev = analysis.Evaluation(decs, labels, samp["tf_weights"], exclusions=excl)
    done35 = {a: {d["instance_id"] for d in loaded["35B"][0] if d["arm"] == a} for a in ARMS}
    ids = ev.comparison_set([cond(a, m) for a in ARMS for m in MODELS], restrict=set.intersection(*done35.values()))
    evr = ev._restricted(ids)
    oc = json.loads((ROOT / "results" / "expl_35b" / "outcome.json").read_text(encoding="utf-8"))
    out = {"label": p["label"], "model": p["model_tag"], "differences_from_M1": p["differences_from_M1"],
           "decisions": ["D-55", "D-67", "D-76", "D-77", "D-78", "D-82", "D-88"],
           "dataset": "D1", "split": "test", "level": "S1", "n_instances": len(ids), "n_bugs": len(evr.bugs),
           "pf_prevalence": analysis.judged_prevalence(labels, sorted(ids)),
           "decided_35b_per_arm": {a: len(v) for a, v in done35.items()}, "aborted_excluded": sorted(aborted),
           "server_starts": {k: {x: v.get(x) for x in ("calls", "call_cap", "within_cap", "stop_reason")}
                             for k, v in oc.get("e6a", {}).items()},
           "summary": {m: {a: {k: evr.summary(cond(a, m))[k] for k in ("f1", "f1_ci95", "mcc", "mcc_ci95",
                                                                       "precision", "recall")} for a in ARMS}
                       for m in MODELS},
           "within_model": {m: {f"{a}-{b}": {k: vars(evr.contrast(f"{a}-{b} ({m})", [cond(a, m)], [cond(b, m)], k))
                                             for k in ("f1", "mcc")} for a, b in PAIRS} for m in MODELS},
           "35b_minus": {f"{a} 35B-{m}": {k: vars(evr.contrast(f"{a} 35B-{m}", [cond(a, "35B")], [cond(a, m)], k))
                                          for k in ("f1", "mcc")} for a in ARMS for m in ("M1", "M2")},
           "note": ("EXPLORATORY: no confirmatory test, no multiplicity correction; the 35b ran under different "
                    "conditions from M1 (see differences_from_M1), across two server starts, so differences are not "
                    "attributable to the model alone and are not equivalent to the original proprietary-model design. "
                    + analysis.F1_NOT_COMPARABLE)}
    dump_json(OUT, out)
    r = lambda v: round(v, 3)
    print(f"EXPLORATORY 35b (E6a)  n={out['n_instances']} bugs={out['n_bugs']} starts={out['server_starts']}")
    for m in MODELS:
        print(" ", m, {a: (r(out["summary"][m][a]["f1"]), r(out["summary"][m][a]["mcc"])) for a in ARMS},
              {k: (r(v["f1"]["delta"]), [r(c) for c in v["f1"]["ci95"]]) for k, v in out["within_model"][m].items()})
    for k, v in out["35b_minus"].items():
        print(" ", k, {x: (r(v[x]["delta"]), [r(c) for c in v[x]["ci95"]]) for x in ("f1", "mcc")})


if __name__ == "__main__":
    main()
