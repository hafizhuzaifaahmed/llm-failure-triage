"""Hand-computed fixtures for the review-response metrics (D-112 to D-121). Synthetic data only."""
import math

import numpy as np
import pytest

from triage import revision_metrics as rm
from triage.metrics import average_precision

PF, TF, INV = rm.PF, rm.TF, rm.INVALID


def test_rates_hand_counts():
    # TP=6, FP=2, FN=4, TN=8 -> TPR 0.6, TNR 0.8, BA 0.7, loss 0.4, discarded (4+8)/20 = 0.6
    r = rm.rates_from_totals(np.array([6, 2, 4, 8]))
    assert r["tpr"] == pytest.approx(0.6) and r["tnr"] == pytest.approx(0.8)
    assert r["ba"] == pytest.approx(0.7) and r["pf_loss_rate"] == pytest.approx(0.4)
    assert r["share_discarded"] == pytest.approx(0.6)


def test_rates_zero_denominators_are_nan_not_substituted():
    r = rm.rates_from_totals(np.array([0, 3, 0, 2]))          # no PF at all
    assert math.isnan(float(r["tpr"])) and float(r["tnr"]) == pytest.approx(0.4)
    assert math.isnan(float(r["ba"]))
    r = rm.rates_from_totals(np.array([2, 0, 1, 0]))          # no TF at all
    assert math.isnan(float(r["tnr"]))


def test_rates_point_averages_replicates():
    # bug-level tensor, 2 bugs x 2 replicates; rep0 TPR 1.0, rep1 TPR 0.5 -> mean 0.75
    T = np.zeros((2, 2, 4))
    T[0, 0] = [1, 0, 0, 1]
    T[1, 0] = [1, 0, 0, 0]
    T[0, 1] = [1, 1, 0, 0]
    T[1, 1] = [0, 0, 1, 0]
    p = rm.rates_point(T)
    assert p["tpr"] == pytest.approx(0.75)
    assert p["tnr"] == pytest.approx((1.0 + 0.0) / 2)


def test_rates_bootstrap_identity_weights():
    T = np.zeros((2, 1, 4))
    T[0, 0] = [2, 1, 0, 1]
    T[1, 0] = [0, 0, 2, 2]
    W = np.array([[1.0, 1.0], [2.0, 0.0], [0.0, 2.0]])     # identity, bug 0 twice, bug 1 twice
    b = rm.rates_bootstrap(T, W)
    assert b["tpr"][0] == pytest.approx(0.5) and b["tpr"][1] == pytest.approx(1.0)
    assert b["tpr"][2] == pytest.approx(0.0)                # bug 1 twice: TP 0, FN 4
    assert b["tnr"][2] == pytest.approx(1.0)                # TN 4, FP 0
    T0 = np.zeros((2, 1, 4))
    T0[0, 0] = [0, 1, 0, 1]
    T0[1, 0] = [1, 0, 0, 0]
    assert math.isnan(rm.rates_bootstrap(T0, np.array([[2.0, 0.0]]))["tpr"][0])   # resample without PF -> NaN


def test_prevalence_translation():
    # TPR 0.9, TNR 0.2, pi 0.05: precision = .045/(.045+.76) = 0.05590; false alarms per kept PF = .76/.045 = 16.89
    assert rm.precision_at_prevalence(0.9, 0.2, 0.05) == pytest.approx(0.045 / 0.805)
    assert rm.false_alarms_per_kept_pf(0.9, 0.2, 0.05) == pytest.approx(0.76 / 0.045)
    assert math.isnan(rm.false_alarms_per_kept_pf(0.0, 0.2, 0.05))


def test_pf_score_direction_and_invalid():
    assert rm.pf_score(PF, 80) == pytest.approx(0.8)
    assert rm.pf_score(TF, 80) == pytest.approx(0.2)
    assert rm.pf_score(INV, 80) == 0.5 and rm.pf_score(PF, None) == 0.5
    assert rm.tf_confidence(TF, 100) == pytest.approx(1.0)


def test_k_of_n_and_keep_score_invalid_is_not_tf():
    v = [TF, TF, INV]
    assert rm.k_of_n(v, 1) == TF and rm.k_of_n(v, 2) == TF and rm.k_of_n(v, 3) == PF
    assert rm.keep_score(v) == 1
    assert rm.keep_score([TF, TF, TF]) == 0                     # KUU discards iff score == 0
    assert rm.k_of_n([TF, None], 2) == PF                       # a missing vote keeps


def test_auroc_hand_example_with_ties():
    # PF scores [0.9, 0.5], TF scores [0.5, 0.1]: pairs (0.9>0.5)=1, (0.9>0.1)=1, (0.5=0.5)=.5, (0.5>0.1)=1 -> 3.5/4
    y = [PF, PF, TF, TF]
    s = [0.9, 0.5, 0.5, 0.1]
    assert rm.auroc(y, s) == pytest.approx(0.875)
    assert rm.auroc(y, [0.5] * 4) == pytest.approx(0.5)
    assert math.isnan(rm.auroc([PF, PF], [0.1, 0.2]))           # single class -> undefined


def test_auroc_weights_duplicate_items():
    y = [PF, TF, TF]
    s = [0.6, 0.7, 0.1]
    # weight 2 on the high TF equals duplicating it: pairs vs TF(0.7) x2 = 0, vs TF(0.1) = 1 -> 1/3
    assert rm.auroc(y, s, [1, 2, 1]) == pytest.approx(1 / 3)
    assert rm.auroc([PF, TF, TF, TF], [0.6, 0.7, 0.7, 0.1]) == pytest.approx(1 / 3)


def test_auprc_matches_existing_average_precision_and_hand_value():
    y = [PF, TF, PF, TF]
    s = [0.9, 0.8, 0.7, 0.1]
    # steps: thr .9 P=1 R=.5; .8 no gain; .7 P=2/3 R=1 -> AP = .5*1 + .5*2/3 = 0.8333
    assert rm.auprc(y, s) == pytest.approx(0.5 + 0.5 * 2 / 3)
    assert rm.auprc(y, s) == pytest.approx(average_precision(y, s))
    # a tie of PF and TF at the top: one step, P = 1/2, R = 1/2, then the second PF at .7: P=2/3, R=1
    y2, s2 = [PF, TF, PF], [0.9, 0.9, 0.7]
    assert rm.auprc(y2, s2) == pytest.approx(0.5 * 0.5 + 0.5 * 2 / 3)
    assert math.isnan(rm.auprc([TF, TF], [0.2, 0.3]))


def test_bootstrap_ranking_equals_point_at_identity():
    y = [PF, PF, TF, TF, TF]
    s = [0.9, 0.4, 0.5, 0.1, 0.4]
    bug_index = np.array([0, 1, 1, 2, 2])
    W = np.array([[1.0, 1.0, 1.0], [0.0, 3.0, 0.0]])
    a = rm.auroc_bootstrap(y, s, bug_index, W)
    p = rm.auprc_bootstrap(y, s, bug_index, W)
    assert a[0] == pytest.approx(rm.auroc(y, s)) and p[0] == pytest.approx(rm.auprc(y, s))
    # resample = bug 1 three times: items (PF .4, TF .5) each weight 3 -> AUROC 0, AP = .5 (one step at .4)
    assert a[1] == pytest.approx(0.0)
    assert p[1] == pytest.approx(rm.auprc([PF, TF], [0.4, 0.5]))


def test_topk_exact_expectation_with_boundary_tie():
    # 10 failures, budget 20% -> k=2. Scores: one PF at 0.9 (bug A) alone at the top; then a tie of 4 at 0.5:
    # PF (bug B), PF (bug B), TF, TF. r = 1 of m = 4.
    y = [PF, PF, PF, TF, TF, TF, TF, TF, TF, TF]
    s = [0.9, 0.5, 0.5, 0.5, 0.5, 0.1, 0.1, 0.1, 0.1, 0.1]
    bugs = ["A", "B", "B", "C", "C", "C", "D", "D", "D", "D"]
    r = rm.topk_inspection(y, s, bugs, 0.20)
    assert r["k"] == 2
    exp_pf = 1 + 2 * 1 / 4                                        # 1.5 PF expected among the 2 inspected
    assert r["recall"] == pytest.approx(exp_pf / 3)
    assert r["precision"] == pytest.approx(exp_pf / 2)
    # bug A certainly found; bug B found unless the one pick is a TF: 1 - C(2,1)/C(4,1) = 0.5 -> mean(1, .5) = .75
    assert r["bug_recall"] == pytest.approx(0.75)


def test_topk_multiple_tests_per_bug_bug_vs_test_recall_differ():
    y = [PF, PF, PF, TF]
    s = [0.9, 0.8, 0.1, 0.2]
    bugs = ["A", "A", "B", "C"]
    r = rm.topk_inspection(y, s, bugs, 0.5)                       # k = 2: both of bug A's PF tests
    assert r["recall"] == pytest.approx(2 / 3)
    assert r["bug_recall"] == pytest.approx(0.5)                  # A found, B not


def test_topk_edge_cases():
    r = rm.topk_inspection([TF, TF], [0.1, 0.2], ["A", "B"], 0.5)
    assert math.isnan(r["recall"]) and math.isnan(r["bug_recall"])
    r = rm.topk_inspection([PF, TF], [0.1, 0.2], ["A", "B"], 0.10)   # k = 0
    assert r["k"] == 0 and r["recall"] == 0.0 and math.isnan(r["precision"])


def test_topk_weighted_reduces_to_unweighted_without_ties():
    y = [PF, TF, PF, TF, TF]
    s = [0.9, 0.8, 0.7, 0.2, 0.1]
    bugs = ["A", "A", "B", "B", "C"]
    u = rm.topk_inspection(y, s, bugs, 0.6)
    w = rm.topk_inspection_weighted(y, s, bugs, [1] * 5, 0.6)
    assert w["recall"] == pytest.approx(u["recall"]) and w["bug_recall"] == pytest.approx(u["bug_recall"])


def test_topk_weighted_hand_value():
    # TF at the top carries weight 3 (stands for three population TF). Total weight 1+3+1 = 5, budget 40% = 2:
    # the 0.9 group (TF, weight 3) is included with phi = 2/3; no PF inspected.
    y, s, bugs, w = [TF, PF, TF], [0.9, 0.5, 0.1], ["A", "B", "C"], [3, 1, 1]
    r = rm.topk_inspection_weighted(y, s, bugs, w, 0.4)
    assert r["recall"] == pytest.approx(0.0) and r["bug_recall"] == pytest.approx(0.0)
    r = rm.topk_inspection_weighted(y, s, bugs, w, 0.7)            # budget 3.5: TF fully (3), PF with phi = .5
    assert r["recall"] == pytest.approx(0.5) and r["bug_recall"] == pytest.approx(0.5)


def test_crc_threshold_hand():
    # 9 PF calibration units with scores; loss = 1 if s >= lam. alpha 0.2: need (9/10)*risk + 1/10 <= .2 -> risk <= 1/9
    scores = [0, 0, 0, 1, 1, 2, 2, 3, 3]
    losses = [lambda lam, x=x: float(x >= lam) for x in scores]
    lam, bound, n = rm.crc_threshold(losses, [0, 1, 2, 3, 4], 0.2)
    assert n == 9 and lam == 4                    # at lam=3 two units lost: risk 2/9 > 1/9; lam 4 -> risk 0
    assert bound == pytest.approx(0.1)
    lam, bound, n = rm.crc_threshold(losses, [0, 1, 2, 3, 3.5, 4], 0.2)
    assert lam == 3.5
    lam, bound, n = rm.crc_threshold(losses, [0, 1, 2, 3, 4], 0.35)   # risk <= (.35-.1)*10/9 = .278 -> lam 3 (2/9)
    assert lam == 3
    lam, bound, _ = rm.crc_threshold(losses, [0, 1, 2, 3, 4], 0.05)   # 1/10 > .05: infeasible even at risk 0
    assert lam is None


def test_cap_policy_label_only_capped_calls_change():
    for pol in rm.CAP_POLICIES:
        assert rm.cap_policy_label(PF, False, pol) == PF and rm.cap_policy_label(TF, True, pol) == TF
        assert rm.cap_policy_label(INV, False, pol) == TF          # an uncapped invalid keeps the primary coding
    assert rm.cap_policy_label(INV, True, "as_TF") == TF
    assert rm.cap_policy_label(INV, True, "keep") == PF
    assert rm.cap_policy_label(INV, True, "exclude") is None
    with pytest.raises(ValueError):
        rm.cap_policy_label(INV, True, "drop")


def test_bugs_lost_counts_bugs_not_tests():
    rows = [("A", PF, TF), ("A", PF, PF), ("B", PF, TF), ("B", PF, TF), ("C", TF, TF), ("D", PF, None)]
    assert rm.bugs_lost(rows) == 2          # B (both lost) and D (its only PF test excluded/not kept); A keeps one
