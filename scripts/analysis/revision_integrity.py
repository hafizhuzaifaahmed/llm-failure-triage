"""WP1.9 (D-120; zero calls): statistical integrity checks and a frequentist sensitivity for the E2 mixed model.

(a) resampling unit of every analysis script that reports an interval (static audit of the code);
(b) Holm recomputed from each committed family's stored unadjusted p and compared with the stored p_Holm;
(c) positive class: F1 recomputed from stored TP/FP/FN for every single-replicate row of the condition tables;
(d) GEE logistic (binomial, exchangeable, clusters = bugs, bias-reduced sandwich SEs because there are few clusters)
    on exactly the rows of the committed E2 GLMM; sensitivity/exploratory, the committed GLMM output is untouched.

    python scripts/analysis/revision_integrity.py  -> results/revision/wp19_integrity.json
"""
import csv
import json
import math
import re
import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import revision_common as rc  # noqa: E402
from triage import analysis, config, glmm, stats  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

OUT = rc.OUT / "wp19_integrity.json"
AF = rc.ROOT / "results" / "heldout" / "analysis_final"
FAMILIES = [  # (family, file, path to the hypothesis container, members)
    ("confirmatory F1 (H1-H3b)", AF / "D1_M1/tables/confirmatory.json", ["f1"], None),
    ("secondary recall/precision", AF / "D1_M1/tables/confirmatory.json", ["secondary"], None),
    ("E6b (H6-1, H6-2)", rc.ROOT / "results/e6b/analysis/e6b_d1test.json", ["hypotheses"], ["H6-1", "H6-2"]),
    ("E8 (H8-1..H8-3)", rc.ROOT / "results/e8/analysis/e8_d1test.json", ["hypotheses"], ["H8-1", "H8-2", "H8-3"]),
    ("E9 (H9-1, H9-2)", rc.ROOT / "results/e9/analysis/e9_d1test.json", ["hypotheses"], ["H9-1", "H9-2"]),
    ("KUU D2 (H10-1, H10-2)", rc.ROOT / "results/kuu/analysis/kuu_d2.json", ["hypotheses"], ["H10-1", "H10-2"]),
    ("E9b (H11-1, H11-2)", rc.ROOT / "results/e9b/analysis/e9b_d2.json", ["hypotheses"], ["H11-1", "H11-2"]),
    ("cascade D2 (H12-1, H12-2)", rc.ROOT / "results/cascade/analysis/cascade_d2.json", ["hypotheses"], ["H12-1", "H12-2"]),
    ("KUU-NG D2 (H13-1, H13-2)", rc.ROOT / "results/kuung/analysis/kuung.json", ["D2", "hypotheses"], ["H13-1", "H13-2"]),
    ("KUU-NG D1 (H13-1, H13-2)", rc.ROOT / "results/kuung/analysis/kuung.json", ["D1", "hypotheses"], ["H13-1", "H13-2"]),
]


def resampling_audit():
    out = []
    for f in sorted((rc.ROOT / "scripts" / "analysis").glob("*.py")) + [rc.ROOT / "scripts" / "analyze.py"]:
        t = f.read_text(encoding="utf-8")
        if "ci95" not in t and "percentile_ci" not in t:
            continue
        if "label_audit" in f.name:
            unit = "bug (rng.choice over bugs), B = 2,000 as fixed in D-82"
        elif re.search(r"multinomial\(len\(bugs\)", t):
            unit = "bug (multinomial over bugs)"
        elif re.search(r"Evaluation|bootstrap_weights|weights_W|revision_common|kuu_analysis", t):
            unit = "bug (stats.bootstrap_weights, B = 10,000, committed seed)"
        else:
            unit = "UNVERIFIED"
        out.append({"script": f.relative_to(rc.ROOT).as_posix(), "resampling_unit": unit})
    return out


def holm_check():
    out = []
    for fam, f, path, members in FAMILIES:
        d = json.loads(f.read_text(encoding="utf-8"))
        for p in path:
            d = d[p]
        items = list(d) if isinstance(d, list) else [dict(d[m], name=m) for m in members]
        ps = [x.get("p", x.get("p_one_sided")) for x in items]
        stored = [x["p_holm"] for x in items]
        rec = stats.holm(ps)
        out.append({"family": fam, "file": f.relative_to(rc.ROOT).as_posix(), "size": len(items),
                    "members": [f"{x.get('name')}{'~' + x['metric'] if 'metric' in x and x['metric'] != 'f1' else ''}"
                                for x in items],
                    "max_abs_difference": float(max(abs(a - b) for a, b in zip(rec, stored))),
                    "matches": bool(all(abs(a - b) < 1e-9 for a, b in zip(rec, stored)))})
    return out


def f1_check():
    out = []
    for name in ("D1_M1", "D2_M1", "D1_M2", "D2_M2"):
        f = AF / name / "tables" / "conditions.csv"
        n_rows = n_bad = 0
        for r in csv.DictReader(open(f, encoding="utf-8")):
            if r.get("replicates") not in ("1", "1.0"):
                continue
            tp, fp, fn = float(r["TP"]), float(r["FP"]), float(r["FN"])
            f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else float("nan")
            n_rows += 1
            if not (math.isnan(f1) and r["f1"] in ("", "nan")) and abs(f1 - float(r["f1"])) > 5e-5:      # the table stores 4 decimals
                n_bad += 1
        out.append({"table": f.relative_to(rc.ROOT).as_posix(), "single_replicate_rows": n_rows, "mismatches": n_bad})
    return out


def gee():
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    runs = [rc.RUNS / r for r in ("LOCAL_HO_E1E3_M1", "LOCAL_HO_E4_M1")]
    decisions = [d for r in runs for d in read_jsonl(r / "decisions.jsonl")]
    exclusions = analysis.abort_exclusions(x for r in runs for x in read_jsonl(r / "leakage_rejections.jsonl"))
    samp = json.loads((config.PROCESSED / "sample_D1_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl") if l["instance_id"] in keep]
    ev = analysis.Evaluation(decisions, labels, samp["tf_weights"], exclusions=exclusions)
    drop = set().union(*[exclusions.get((lv, "full"), set()) for lv in ("S0", "S1", "S2")])
    df = glmm.rows_from_decisions([d for d in decisions if d["instance_id"] not in drop], ev.lab, ev.meta)
    committed = json.loads((AF / "D1_M1/tables/glmm_e2_bootstrap.json").read_text(encoding="utf-8"))
    out = {}
    for cls, name in (("PROGRAM_FAULT", "PF_recall"), ("TEST_FAULT", "TF_specificity")):
        sub = df[df["y_true"] == cls].copy()
        if len(sub) != committed["models"][name]["n_rows"]:
            raise SystemExit(f"{name}: {len(sub)} rows differ from the committed GLMM's {committed['models'][name]['n_rows']}")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = smf.gee(glmm.FORMULA, groups="bug", data=sub, family=sm.families.Binomial(),
                        cov_struct=sm.cov_struct.Exchangeable())
            r = m.fit(cov_type="bias_reduced")
        ci = r.conf_int()
        terms = []
        for t in r.params.index:
            terms.append({"term": t, "odds_ratio": float(np.exp(r.params[t])),
                          "or_ci95_robust": [float(np.exp(ci.loc[t, 0])), float(np.exp(ci.loc[t, 1]))],
                          "p": float(r.pvalues[t])})
        glmm_terms = {t["term"]: t for t in committed["models"][name]["terms"]}
        out[name] = {"n_rows": len(sub), "n_clusters": int(sub["bug"].nunique()), "terms": terms,
                     "glmm_vb_point_and_bootstrap": {k: {"odds_ratio": v["odds_ratio"], "or_ci95_bootstrap": v["or_ci95_bootstrap"]}
                                                     for k, v in glmm_terms.items()},
                     "working_correlation": float(r.cov_struct.dep_params)}
    return out


def main():
    res = {"what": "statistical integrity checks and GEE sensitivity (D-120)", "decisions": ["D-112", "D-120"],
           "resampling_audit": resampling_audit(), "holm": holm_check(), "positive_class_f1": f1_check(),
           "mixed_model": {"status": "R (lme4, glmmTMB) not installed; the statsmodels VB GLMM keeps only its committed "
                                     "bug-bootstrap intervals (its VB intervals under-covered, 50-70% in the repository's "
                                     "simulation) and is de-emphasised; GEE below is a frequentist population-averaged "
                                     "sensitivity, exploratory",
                           "gee": gee()}}
    dump_json(OUT, res)
    for r in res["resampling_audit"]:
        print(f"  {r['script']:50s} {r['resampling_unit']}")
    for r in res["holm"]:
        print(f"  Holm {r['family']:32s} size {r['size']:2d} matches {r['matches']} maxdiff {r['max_abs_difference']:.2e}")
    print(res["positive_class_f1"])
    for name, g in res["mixed_model"]["gee"].items():
        print(name, g["n_rows"], "rows", g["n_clusters"], "clusters, rho", round(g["working_correlation"], 3))
        for t in g["terms"]:
            print(f"   {t['term'][:62]:62s} OR {t['odds_ratio']:.3f} {np.round(t['or_ci95_robust'], 3)} p {t['p']:.3f}")


if __name__ == "__main__":
    main()
