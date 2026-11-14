"""WP1.6 (D-117; exploratory; zero calls): a risk-targeted discard threshold. Score s = (valid TF votes of the panel)
+ M1 DEB's TF-confidence (mean over available replicates); discard iff s >= lambda. lambda chosen on D1-test PF units
by conformal risk control (CRC) for the PF-loss rate, evaluated once on D2. Two loss units: PF tests, and bugs (loss =
share of the bug's PF tests discarded). The CRC guarantee needs exchangeable calibration and test units and a
calibration set independent of the rule's design; both conditions are checked and reported, and when they fail the
threshold is a heuristic, not a bound.

    python scripts/analysis/revision_risk.py  -> results/revision/wp16_risk.json
"""
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import revision_common as rc  # noqa: E402
from triage import revision_metrics as rm  # noqa: E402
from triage import stats  # noqa: E402
from triage.io_utils import dump_json  # noqa: E402

OUT = rc.OUT / "wp16_risk.json"
PANELS = {"KUU": ("kuu_votes", ("M1", "M2", "E6B")), "KUU-NG": ("ng_votes", ("M1", "E6B", "NG"))}
ALPHAS = (0.05, 0.10)


def scores(D, panel):
    attr, members = PANELS[panel]
    votes = getattr(D, attr)
    out = {}
    for i in D.ids:
        d = [rm.tf_confidence(*D.m1deb[r][i]) for r in D.m1deb if i in D.m1deb[r]]
        out[i] = rm.n_valid_tf([votes[i].get(m) for m in members]) + (float(np.mean(d)) if d else 0.5)
    return out


def evaluate(D, s, lam):
    bugs, W = D.weights_W()
    bi = {b: n for n, b in enumerate(bugs)}
    T = np.zeros((len(bugs), 1, 4))
    for i in D.ids:
        t, keep = D.lab[i] == rc.PF, s[i] < lam
        T[bi[D.bug[i]], 0, 0 if (t and keep) else 2 if t else 1 if keep else 3] += 1
    pt, bs = rm.rates_point(T), rm.rates_bootstrap(T, W)
    return {**pt, "pf_loss_rate_ci95": rc.ci(bs["pf_loss_rate"]), "tnr_ci95": rc.ci(bs["tnr"]),
            "mcc": stats.point_estimate(T, "mcc"), "pf_lost": float(T.sum(axis=0)[0][2])}


def main():
    D1, D2 = rc.build("D1"), rc.build("D2")
    res = {"what": "risk-targeted discard threshold (D-117, exploratory)", "decisions": ["D-112", "D-117"],
           "score": "valid TF votes (0-3) + M1 DEB TF-confidence (0-1, mean over replicates); discard iff s >= lambda",
           "assumption_checks": {
               "exchangeable_calibration_and_test": "not met: D1 real faults (PF prevalence 0.34 in the sample) vs D2 "
                                                    "seeded single-line mutants (0.57); different fault process",
               "calibration_independent_of_rule_design": "not met: KUU was defined after the D1 votes (D-95); the "
                                                         "score and its components were chosen with D1 seen",
               "clustering": "PF tests cluster in bugs; the bug-level variant uses bugs as units",
               "finite_sample": "CRC needs (n/(n+1))R + 1/(n+1) <= alpha; with n calibration units the smallest "
                                "attainable bound is 1/(n+1)"},
           "verdict": "risk-targeted heuristic threshold, not a guaranteed bound (two of the conditions fail)",
           "panels": {}}
    for panel in PANELS:
        s1, s2 = scores(D1, panel), scores(D2, panel)
        grid = sorted(set(s1.values())) + [float("inf")]
        pf1 = [i for i in D1.ids if D1.lab[i] == rc.PF]
        test_losses = [lambda lam, x=s1[i]: float(x >= lam) for i in pf1]
        by_bug = defaultdict(list)
        for i in pf1:
            by_bug[D1.bug[i]].append(s1[i])
        bug_losses = [lambda lam, xs=tuple(xs): float(np.mean([x >= lam for x in xs])) for xs in by_bug.values()]
        rows = {}
        for unit, losses in (("tests", test_losses), ("bugs", bug_losses)):
            for a in ALPHAS:
                lam, bound, n = rm.crc_threshold(losses, grid, a)
                row = {"unit": unit, "alpha": a, "n_calibration_units": n, "lambda": lam, "crc_bound_on_D1": bound,
                       "smallest_attainable_bound": 1 / (n + 1)}
                if lam is not None:
                    row["D1_in_sample"] = evaluate(D1, s1, lam)
                    row["D2_evaluation"] = evaluate(D2, s2, lam)
                    row["D2_realised_loss_within_alpha"] = row["D2_evaluation"]["pf_loss_rate"] <= a
                rows[f"{unit}_alpha{a}"] = row
        res["panels"][panel] = {"grid": [g if g != float("inf") else "inf" for g in grid], "thresholds": rows,
                                "kuu_equivalent_lambda": 3.0}
    dump_json(OUT, res)
    for p, r in res["panels"].items():
        for k, row in r["thresholds"].items():
            d2 = row.get("D2_evaluation") or {}
            print(p, k, "lambda", row["lambda"], "n", row["n_calibration_units"],
                  "D1 loss", round((row.get("D1_in_sample") or {}).get("pf_loss_rate", float("nan")), 3),
                  "D2 loss", round(d2.get("pf_loss_rate", float("nan")), 3), "D2 TF-removal",
                  round(d2.get("tnr", float("nan")), 3), "D2 disc", round(d2.get("share_discarded", float("nan")), 3))


if __name__ == "__main__":
    main()
