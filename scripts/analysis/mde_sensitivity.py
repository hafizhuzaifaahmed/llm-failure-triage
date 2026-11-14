"""Post hoc sensitivity analysis (D-80): minimum detectable ΔF1 of each confirmatory test at 80% power.

    MDE = (z_{1-α/2} + z_{0.80}) × SE,   SE = standard deviation of the bug-level bootstrap ΔF1

computed at α = 0.05 and at the Holm α for the smallest p (0.05 / 5). It describes what effect sizes this sample could
have detected; it is not "observed power" (which is a function of the observed p and adds nothing) and is not used to
re-read any confirmatory result.

The bootstrap distribution is the one the confirmatory analysis used: the same evaluation (runs, labels, D-70
exclusions, sampling weights), the same contrasts (`analysis.CONFIRMATORY`), the same bug resamples (seed, B). The
script rebuilds each ΔF1 sample and checks that its point estimate, 95% CI and p reproduce the committed
confirmatory.json exactly before it reports any SE.

    python scripts/analysis/mde_sensitivity.py   -> results/heldout/analysis_final/D1_M1/tables/mde_sensitivity.json
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import analysis, config, stats  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

RUNS = [ROOT / "results" / "runs_local" / r for r in ("LOCAL_HO_E1E3_M1", "LOCAL_HO_E4_M1")]
TABLES = ROOT / "results" / "heldout" / "analysis_final" / "D1_M1" / "tables"
ALPHA, POWER, M = 0.05, 0.80, 5


def evaluation():
    decisions = [d for r in RUNS for d in read_jsonl(r / "decisions.jsonl")]
    exclusions = analysis.abort_exclusions(x for r in RUNS for x in read_jsonl(r / "leakage_rejections.jsonl"))
    samp = json.loads((config.PROCESSED / "sample_D1_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl") if l["instance_id"] in keep]
    jd = {i["instance_id"] for i in read_jsonl(config.PROCESSED / "instances_D1.jsonl") if i["covariates"]["javadoc_present"]}
    return analysis.Evaluation(decisions, labels, samp["tf_weights"], exclusions=exclusions), jd


def delta_samples(ev, a, b, restrict):
    """The ΔF1 bootstrap sample exactly as Evaluation.contrast builds it."""
    evr = ev._restricted(ev.comparison_set(a + b, restrict))
    boot = lambda cs: np.mean([stats.bootstrap_metric(evr.tensor(c), "f1", evr.W) for c in cs], axis=0)
    point = lambda cs: float(np.mean([stats.point_estimate(evr.tensor(c), "f1") for c in cs]))
    return boot(a) - boot(b), point(a) - point(b), len(evr.lab), len(evr.bugs)


def main():
    ev, jd = evaluation()
    committed = {c["name"]: c for c in json.loads((TABLES / "confirmatory.json").read_text(encoding="utf-8"))["f1"]}
    z = {"z_power": float(norm.ppf(POWER)), "z_alpha_005": float(norm.ppf(1 - ALPHA / 2)),
         "z_alpha_holm_min": float(norm.ppf(1 - ALPHA / M / 2))}
    rows = []
    for name, a, b, sub in analysis.CONFIRMATORY:
        d, delta, n, nb = delta_samples(ev, a, b, jd if sub == "javadoc" else None)
        c = committed[name]
        rep = {"delta": delta, "ci95": stats.percentile_ci(d, .95), "p": stats.bootstrap_p_two_sided(d)}
        if not (abs(rep["delta"] - c["delta"]) < 1e-12 and np.allclose(rep["ci95"], c["ci95"], atol=1e-12, rtol=0)
                and abs(rep["p"] - c["p"]) < 1e-12):
            raise SystemExit(f"{name}: rebuilt bootstrap does not reproduce confirmatory.json ({rep} vs {c})")
        se = float(np.nanstd(d, ddof=1))
        rows.append({"name": name, "contrast": f"{' + '.join(a)} vs {' + '.join(b)}", "n_instances": n, "n_bugs": nb,
                     "delta": delta, "se_bootstrap": se,
                     "mde_alpha_005": (z["z_alpha_005"] + z["z_power"]) * se,
                     "mde_alpha_holm_min": (z["z_alpha_holm_min"] + z["z_power"]) * se,
                     "abs_delta_over_mde_005": abs(delta) / ((z["z_alpha_005"] + z["z_power"]) * se),
                     "reproduces_committed": True})
    out = {"what": "post hoc sensitivity: minimum detectable ΔF1 at 80% power from the bug-level bootstrap SE (D-80)",
           "not": "observed power; no confirmatory result is re-read",
           "alpha": ALPHA, "alpha_holm_smallest_p": ALPHA / M, "power": POWER, **z,
           "bootstrap": {"B": int(config.BOOTSTRAP_RESAMPLES), "seed": int(config.SEED_BOOTSTRAP)}, "tests": rows}
    dump_json(TABLES / "mde_sensitivity.json", out)
    for r in rows:
        print(f"{r['name']:4s} n={r['n_instances']} bugs={r['n_bugs']} Δ={r['delta']:+.3f} SE={r['se_bootstrap']:.3f} "
              f"MDE05={r['mde_alpha_005']:.3f} MDEholm={r['mde_alpha_holm_min']:.3f}")


if __name__ == "__main__":
    main()
