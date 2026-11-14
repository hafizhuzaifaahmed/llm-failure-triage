"""Logistic mixed model for E2 (Phase 2 Section 5.2), fitted with statsmodels instead of lme4 (deviation X-02).

    correct ~ specification * architecture + (1 | project) + (1 | bug) + (1 | instance)

fitted separately on PF instances (models recall) and TF instances (models specificity), one row per
(instance, condition, replicate). statsmodels' BinomialBayesMixedGLM is fitted by variational Bayes
(`fit_vb`): it returns approximate posterior means and SDs.

Validation (tests/unit/test_glmm.py, glmm_coverage_study.py, 20 simulated data sets with known effects):
point estimates are close to unbiased (mean bias about -0.02 on the log-odds scale), but the nominal 95%
VB intervals covered the true value in only 50-70% of replications, and the bug-level variance collapsed
(0.05 vs. a true SD of 0.4) into the instance level. Consequently: the VB intervals are NOT reported;
odds ratios are reported as point estimates with bug-level cluster-bootstrap intervals
(`cluster_bootstrap_ci`), and the GLMM stays exploratory, as in Phase 2. No confirmatory test depends on it.
"""
from __future__ import annotations

import math
import warnings

import numpy as np
import pandas as pd
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

FORMULA = "correct ~ C(spec, Treatment('S1')) * C(arch, Treatment('SC'))"
VC = {"project": "0 + C(project)", "bug": "0 + C(bug)", "instance": "0 + C(instance)"}
GLMM_VB_SEED = 20261102   # D-70: fit_vb draws its starting SDs at random; every fit starts from this seed


def fit(df: pd.DataFrame, formula: str = FORMULA, vc: dict | None = None) -> dict:
    """df columns: correct (0/1), spec, arch, project, bug, instance."""
    vc = vc or VC
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = BinomialBayesMixedGLM.from_formula(formula, vc, df)
        res = model.fit_vb(rng=GLMM_VB_SEED)
    names = model.exog_names
    fe_mean, fe_sd = np.asarray(res.fe_mean), np.asarray(res.fe_sd)
    terms = []
    for n, m, s in zip(names, fe_mean, fe_sd):
        terms.append({"term": n, "log_odds": float(m), "sd": float(s), "odds_ratio": math.exp(m),
                      "or_ci95_approx": [math.exp(m - 1.96 * s), math.exp(m + 1.96 * s)]})
    vcs = {n: float(np.exp(v)) for n, v in zip(model.vcp_names, np.asarray(res.vcp_mean))}
    return {"n_rows": len(df), "terms": terms, "random_effect_sd": vcs, "method": "statsmodels fit_vb",
            "vb_seed": GLMM_VB_SEED, "formula": formula, "vc": vc}


def cluster_bootstrap_ci(df: pd.DataFrame, B: int = 200, seed: int = 20261011, formula: str = FORMULA) -> dict:
    """Bug-level cluster bootstrap of the fixed-effect point estimates (refit per resample).

    Used INSTEAD of the VB intervals, whose 95% coverage measured 50-70% in the parameter-recovery study
    (tests/unit/glmm_coverage_record.json). Resampled bugs are relabelled so a bug drawn twice becomes two
    clusters. The coverage of these bootstrap intervals has not itself been simulated (cost: ~B refits each).
    """
    rng = np.random.default_rng(seed)
    bugs = df["bug"].unique()
    groups = {b: g for b, g in df.groupby("bug")}
    draws = []
    for b in range(B):
        parts = []
        for j, bug in enumerate(rng.choice(bugs, size=len(bugs), replace=True)):
            g = groups[bug].copy()
            g["bug"] = f"{bug}#{j}"
            g["instance"] = g["instance"] + f"#{j}"
            parts.append(g)
        r = fit(pd.concat(parts, ignore_index=True), formula)
        draws.append({t["term"]: t["log_odds"] for t in r["terms"]})
    out = {}
    for term in draws[0]:
        v = np.array([d[term] for d in draws])
        out[term] = {"or_ci95_bootstrap": [float(np.exp(np.quantile(v, 0.025))), float(np.exp(np.quantile(v, 0.975)))],
                     "B": B}
    return out


def rows_from_decisions(decisions: list[dict], gt: dict, meta: dict, policy_invalid_as_tf: bool = True) -> pd.DataFrame:
    """One row per decision of the 3x3 factorial (arms J1/SC/DEB, levels S0/S1/S2, full variant)."""
    out = []
    for d in decisions:
        if d["arm"] not in ("J1", "SC", "DEB") or (d.get("variant") or "full") != "full":
            continue
        iid = d["instance_id"]
        if iid not in gt:
            continue
        pred = d["label_raw"]
        if pred == "INVALID":
            if not policy_invalid_as_tf:
                continue
            pred = "TEST_FAULT"
        out.append({"correct": int(pred == gt[iid]), "spec": d["level"], "arch": d["arm"],
                    "project": meta[iid]["project"], "bug": meta[iid]["bug_name"], "instance": iid,
                    "y_true": gt[iid]})
    return pd.DataFrame(out)


def e2_models(df: pd.DataFrame) -> dict:
    out = {}
    for cls, name in (("PROGRAM_FAULT", "PF_recall"), ("TEST_FAULT", "TF_specificity")):
        sub = df[df["y_true"] == cls]
        if sub["spec"].nunique() < 2 or sub["arch"].nunique() < 2 or len(sub) < 30:
            out[name] = {"status": "not fitted", "reason": f"insufficient rows/levels ({len(sub)} rows)"}
            continue
        out[name] = {"status": "fitted", **fit(sub)}
    return out
