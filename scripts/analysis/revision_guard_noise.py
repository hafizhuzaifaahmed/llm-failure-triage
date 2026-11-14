"""WP1.10-1.11 (D-121; post hoc; zero calls).

1.10  Leakage-guard selection effect: which judged instances the S1 guard aborted (any run of the dataset), by label,
      project and matched string kind, and how the judged sample's PF prevalence and project mix change without them.
      Nothing aborted is restored.
1.11  Label-noise sensitivity for the label rule's blind spot: a share q of execution-TF *assertion-failure* instances
      relabelled PF (q = 0.02, 0.05, 0.10 and the D-108 audit rate), 1,000 seeded draws each; distribution of TPR, TNR,
      BA, MCC and AUROC per rule. A noise model, not an estimate of the actual noise.

    python scripts/analysis/revision_guard_noise.py  -> results/revision/wp110_wp111.json
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import revision_common as rc  # noqa: E402
from triage import config  # noqa: E402
from triage import revision_metrics as rm  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

OUT = rc.OUT / "wp110_wp111.json"
SEED = 20261109
DRAWS = 1000
QS = (0.02, 0.05, 0.10)
RULES = ["KA", "DEB|S1", "KUU|S1", "KUUNG|S1", "CAS|S1", "DEB|S1|SON"]


def guard(ds):
    D = rc.build(ds)
    samp = D.sample
    judged = set(samp["instance_ids"])
    lab = {l["instance_id"]: l for l in D.labels_all}
    runs = [p for p in (rc.RUNS).iterdir() if p.is_dir() and (p / "experiment.json").exists()
            and json.loads((p / "experiment.json").read_text(encoding="utf-8")).get("dataset") == ds]
    ab = {}
    for p in runs:
        for r in read_jsonl(p / "leakage_rejections.jsonl") if (p / "leakage_rejections.jsonl").exists() else []:
            if r.get("level") == "S1" and r["instance_id"] in judged:
                ab.setdefault(r["instance_id"], set()).add(p.name)
    kinds = {}
    if ds == "D2":
        for x in json.loads((rc.ROOT / "results" / "heldout" / "d2_abort_vs_mutant.json").read_text(encoding="utf-8")):
            kinds.setdefault(x["instance_id"], set()).add(x["matched_is"])

    def prev(ids):
        c = Counter(lab[i]["label"] for i in ids)
        return {"PF": c["PF"], "TF": c["TF"], "AMB": c["AMB"],
                "pf_prevalence_scored": c["PF"] / (c["PF"] + c["TF"]) if c["PF"] + c["TF"] else None}
    rest = judged - set(ab)
    return {"judged": len(judged), "aborted_at_S1_any_run": len(ab),
            "aborted_by_label": dict(Counter(lab[i]["label"] for i in ab)),
            "aborted_by_project": dict(Counter(lab[i]["project"] for i in ab)),
            "aborted_matched_kind": {k: sum(1 for i in ab if k in kinds.get(i, ())) for k in
                                     sorted({x for v in kinds.values() for x in v})} if kinds else None,
            "runs_reporting_aborts": sorted({r for v in ab.values() for r in v}),
            "judged_with_aborts": prev(judged), "judged_without_aborts": prev(rest),
            "project_share_judged": {p: n / len(judged) for p, n in Counter(lab[i]["project"] for i in judged).items()},
            "project_share_scored": {p: n / len(rest) for p, n in Counter(lab[i]["project"] for i in rest).items()},
            "share_aborted": len(ab) / len(judged)}


def audit_rate():
    a = json.loads((rc.ROOT / "results" / "audit" / "label_audit_scores.json").read_text(encoding="utf-8"))
    c = a["consensus_vs_execution"]["confusion_consensus_by_execution"]       # consensus label -> execution label -> n
    tf_audited = sum(c[k]["TF"] for k in c)
    return c["PF"]["TF"] / tf_audited, c["PF"]["TF"], tf_audited


def noise(ds, qs):
    D = rc.build(ds)
    ids = D.ids
    cand = [n for n, i in enumerate(ids) if D.lab[i] == rc.TF and D.instances[i]["covariates"]["failure_type"] == "assertion_failure"]
    y0 = np.array([D.lab[i] == rc.PF for i in ids])
    preds = {c: [np.array([score_pred(D.preds[c][r][i]) for i in ids]) for r in sorted(D.preds[c])] for c in RULES}
    scores = {c: [np.array([D.scores[c][r][i] for i in ids]) for r in sorted(D.scores[c])] for c in RULES if c in D.scores}
    rng = np.random.default_rng(SEED)
    out = {"n": len(ids), "tf_assertion_candidates": len(cand), "rules": {}}
    base = {}
    for c in RULES:
        base[c] = metrics(y0, preds[c], scores.get(c))
    out["no_noise"] = base
    for q in qs:
        m = int(round(q * len(cand)))
        draws = {c: [] for c in RULES}
        for _ in range(DRAWS):
            y = y0.copy()
            if m:
                y[rng.choice(cand, size=m, replace=False)] = True
            for c in RULES:
                draws[c].append(metrics(y, preds[c], scores.get(c)))
        out["rules"][f"q={q:.4f}"] = {"relabelled": m, **{c: summarise(draws[c]) for c in RULES}}
    return out


def score_pred(lab):
    return lab == rc.PF          # INVALID scores TF in primary arms; synthesized rules are PF/TF already


def metrics(y, preds, scores):
    vals = {"tpr": [], "tnr": [], "ba": [], "mcc": []}
    for p in preds:
        tp, fn = np.sum(y & p), np.sum(y & ~p)
        tn, fp = np.sum(~y & ~p), np.sum(~y & p)
        r = rm.rates_from_totals(np.array([tp, fp, fn, tn], dtype=float))
        d = np.sqrt(float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)))
        vals["tpr"].append(float(r["tpr"]))
        vals["tnr"].append(float(r["tnr"]))
        vals["ba"].append(float(r["ba"]))
        vals["mcc"].append(float((tp * tn - fp * fn) / d) if d else 0.0)
    out = {k: float(np.mean(v)) for k, v in vals.items()}
    if scores:
        out["auroc"] = float(np.mean([rm.auroc(y, s) for s in scores]))
    return out


def summarise(rows):
    keys = rows[0].keys()
    return {k: {"median": float(np.median([r[k] for r in rows])),
                "p2.5": float(np.percentile([r[k] for r in rows], 2.5)),
                "p97.5": float(np.percentile([r[k] for r in rows], 97.5))} for k in keys}


def main():
    rate, k, n = audit_rate()
    qs = tuple(QS) + (rate,)
    res = {"what": "leakage-guard selection effect and label-noise sensitivity (D-121, post hoc)",
           "decisions": ["D-112", "D-121"],
           "guard": {"D1": guard("D1"), "D2": guard("D2")},
           "noise_model": {"relabel": "execution-TF assertion-failure instances -> PF, uniformly at random",
                           "draws": DRAWS, "seed": SEED,
                           "audit_rate": {"value": rate, "consensus_PF_on_execution_TF": k, "execution_TF_audited": n,
                                          "caveat": "development split, author raters who saw the fix (D-108)"}},
           "noise": {"D1": noise("D1", qs), "D2": noise("D2", qs)}}
    dump_json(OUT, res)
    for ds in ("D1", "D2"):
        g = res["guard"][ds]
        print(ds, "guard", {k: g[k] for k in ("judged", "aborted_at_S1_any_run", "aborted_by_label", "aborted_matched_kind",
                                             "share_aborted")}, g["judged_with_aborts"], g["judged_without_aborts"])
        nz = res["noise"][ds]
        print("  candidates", nz["tf_assertion_candidates"])
        for q, rr in nz["rules"].items():
            print("  ", q, "relabelled", rr["relabelled"], {c: (round(rr[c]["ba"]["median"], 3), round(rr[c]["tpr"]["median"], 3))
                                                         for c in RULES})
        print("   no noise", {c: (round(v["ba"], 3), round(v["tpr"], 3)) for c, v in nz["no_noise"].items()})


if __name__ == "__main__":
    main()
