"""Parameter-recovery validation of the statsmodels GLMM on simulated data with known effects.
This validates the estimator, not any research hypothesis."""
import numpy as np
import pandas as pd
import pytest

from triage import glmm

TRUE = {"Intercept": 0.6, "S0": -0.5, "S2": 0.35, "J1": -0.3, "DEB": 0.15}


def simulate(seed=1, n_proj=14, bugs_per_proj=8, inst_per_bug=3, reps=3):
    rng = np.random.default_rng(seed)
    rows = []
    for p in range(n_proj):
        up = rng.normal(0, 0.3)
        for b in range(bugs_per_proj):
            ub = rng.normal(0, 0.4)
            for i in range(inst_per_bug):
                ui = rng.normal(0, 0.7)
                iid = f"p{p}b{b}i{i}"
                for spec in ("S0", "S1", "S2"):
                    for arch in ("J1", "SC", "DEB"):
                        eta = TRUE["Intercept"] + TRUE.get(spec, 0) + TRUE.get(arch, 0) + up + ub + ui
                        for _ in range(reps):
                            rows.append({"correct": int(rng.random() < 1 / (1 + np.exp(-eta))), "spec": spec,
                                         "arch": arch, "project": f"p{p}", "bug": f"p{p}b{b}", "instance": iid,
                                         "y_true": "PROGRAM_FAULT"})
    return pd.DataFrame(rows)


def test_glmm_recovers_known_main_effects():
    res = glmm.fit(simulate())
    est = {t["term"]: t["log_odds"] for t in res["terms"]}
    got = {
        "S0": est["C(spec, Treatment('S1'))[T.S0]"], "S2": est["C(spec, Treatment('S1'))[T.S2]"],
        "J1": est["C(arch, Treatment('SC'))[T.J1]"], "DEB": est["C(arch, Treatment('SC'))[T.DEB]"],
    }
    for k, v in got.items():
        assert v == pytest.approx(TRUE[k], abs=0.2), (k, v)
    inter = [t for t in res["terms"] if ":" in t["term"]]
    assert len(inter) == 4 and all(abs(t["log_odds"]) < 0.35 for t in inter)   # true interactions are 0
    assert set(res["random_effect_sd"]) == {"project", "bug", "instance"}


def test_e2_models_refuses_tiny_subsets():
    df = simulate(n_proj=1, bugs_per_proj=1, inst_per_bug=1, reps=1).head(10)
    assert glmm.e2_models(df)["PF_recall"]["status"] == "not fitted"
