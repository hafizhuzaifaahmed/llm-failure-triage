"""Coverage of the statsmodels-VB GLMM's approximate 95% intervals on simulated data (estimator validation).

    python tests/unit/glmm_coverage_study.py 20
Writes tests/unit/glmm_coverage_record.json.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "src"), str(HERE)]

from test_glmm import TRUE, simulate  # noqa: E402
from triage import glmm  # noqa: E402

KEYS = {"S0": "C(spec, Treatment('S1'))[T.S0]", "S2": "C(spec, Treatment('S1'))[T.S2]",
        "J1": "C(arch, Treatment('SC'))[T.J1]", "DEB": "C(arch, Treatment('SC'))[T.DEB]"}


def main(n):
    hits = {k: 0 for k in KEYS}
    bias = {k: [] for k in KEYS}
    re = []
    for s in range(n):
        r = glmm.fit(simulate(seed=100 + s))
        t = {x["term"]: x for x in r["terms"]}
        for k, name in KEYS.items():
            m, sd = t[name]["log_odds"], t[name]["sd"]
            hits[k] += (m - 1.96 * sd) <= TRUE[k] <= (m + 1.96 * sd)
            bias[k].append(m - TRUE[k])
        re.append(r["random_effect_sd"])
        print(s, {k: round(bias[k][-1], 3) for k in KEYS}, flush=True)
    out = {"replications": n, "coverage_95": {k: hits[k] / n for k in KEYS},
           "mean_bias": {k: sum(v) / n for k, v in bias.items()},
           "mean_random_effect_sd": {k: sum(d[k] for d in re) / n for k in re[0]},
           "true_random_effect_sd": {"project": 0.3, "bug": 0.4, "instance": 0.7}}
    (HERE / "glmm_coverage_record.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20)
