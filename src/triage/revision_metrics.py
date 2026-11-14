"""Metrics added in the review-response pass (D-112 to D-121). Pure functions, no I/O; every one is unit-tested on
hand-computed fixtures (tests/unit/test_revision_metrics.py).

Convention (D-112): PF is the positive class. TP = PF kept, FN = PF discarded, TN = TF discarded, FP = TF kept.
TPR = PF-retention = TP/(TP+FN); TNR = TF-removal = TN/(TN+FP); PF-loss rate = 1 - TPR; BA = (TPR+TNR)/2.
A score is "higher = more likely PF"; a developer inspects failures in descending score.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Callable, Optional, Sequence

import numpy as np

PF, TF, INVALID = "PROGRAM_FAULT", "TEST_FAULT", "INVALID"


# ------------------------------------------------------------------ rates
def rates_from_totals(tot: np.ndarray) -> dict:
    """tot[..., 4] = TP, FP, FN, TN (any leading shape). Undefined denominators give NaN, never a substitute."""
    tot = np.asarray(tot, dtype=float)
    tp, fp, fn, tn = tot[..., 0], tot[..., 1], tot[..., 2], tot[..., 3]
    with np.errstate(divide="ignore", invalid="ignore"):
        tpr = np.where(tp + fn > 0, tp / (tp + fn), np.nan)
        tnr = np.where(tn + fp > 0, tn / (tn + fp), np.nan)
        n = tp + fp + fn + tn
        disc = np.where(n > 0, (fn + tn) / n, np.nan)
    return {"tpr": tpr, "tnr": tnr, "ba": (tpr + tnr) / 2, "pf_loss_rate": 1 - tpr, "share_discarded": disc}


def rates_point(T: np.ndarray) -> dict:
    """T: (bugs, replicates, 4) count tensor. Per replicate, then mean over replicates (the primary convention)."""
    r = rates_from_totals(T.sum(axis=0))
    return {k: float(np.nanmean(v)) for k, v in r.items()}


def rates_bootstrap(T: np.ndarray, W: np.ndarray) -> dict:
    """Bug-level cluster bootstrap: W (B, bugs) multinomial counts; returns (B,) samples per rate."""
    n, R, _ = T.shape
    tot = (W @ T.reshape(n, R * 4)).reshape(-1, R, 4)
    r = rates_from_totals(tot)
    with np.errstate(all="ignore"):
        return {k: np.nanmean(v, axis=1) for k, v in r.items()}


def precision_at_prevalence(tpr: float, tnr: float, pi: float) -> float:
    num = pi * tpr
    den = num + (1 - pi) * (1 - tnr)
    return num / den if den > 0 else float("nan")


def false_alarms_per_kept_pf(tpr: float, tnr: float, pi: float) -> float:
    """Expected TF tests kept per PF test kept at PF prevalence pi: (1-pi)(1-TNR) / (pi TPR)."""
    num = (1 - pi) * (1 - tnr)
    den = pi * tpr
    return num / den if den > 0 else float("nan")


# ------------------------------------------------------------------ scores
def pf_score(label: Optional[str], confidence) -> float:
    """Stated confidence in the stated label -> P(PF)-like score: c/100 for PF, 1 - c/100 for TF, 0.5 otherwise."""
    if label not in (PF, TF) or confidence is None:
        return 0.5
    c = max(0.0, min(100.0, float(confidence))) / 100.0
    return c if label == PF else 1.0 - c


def tf_confidence(label: Optional[str], confidence) -> float:
    return 1.0 - pf_score(label, confidence)


def n_valid_tf(votes: Sequence[Optional[str]]) -> int:
    return sum(v == TF for v in votes)


def k_of_n(votes: Sequence[Optional[str]], k: int) -> str:
    """Discard (TF) iff at least k votes are valid TF; an invalid or missing vote is not a TF vote."""
    return TF if n_valid_tf(votes) >= k else PF


def keep_score(votes: Sequence[Optional[str]], n: int = 3) -> int:
    """n - (valid TF votes): 'discard iff score == 0' is unanimity (KUU) when all n votes are present."""
    return n - n_valid_tf(votes)


# ------------------------------------------------------------------ ranking metrics
def _as_arrays(y, s, w):
    y = np.asarray([bool(t) if isinstance(t, (bool, np.bool_)) else t == PF for t in y], dtype=bool)
    s = np.asarray(s, dtype=float)
    w = np.ones(len(s)) if w is None else np.asarray(w, dtype=float)
    return y, s, w


def auroc(y, s, w=None) -> float:
    """Weighted Mann-Whitney AUROC, ties count 1/2. NaN when a class is absent (never substituted)."""
    y, s, w = _as_arrays(y, s, w)
    sp, sn, wp, wn = s[y], s[~y], w[y], w[~y]
    if wp.sum() == 0 or wn.sum() == 0:
        return float("nan")
    K = (sp[:, None] > sn[None, :]) + 0.5 * (sp[:, None] == sn[None, :])
    return float(wp @ K @ wn / (wp.sum() * wn.sum()))


def auprc(y, s, w=None) -> float:
    """Step-wise average precision over distinct thresholds (ties form one step), weighted; NaN without positives."""
    y, s, w = _as_arrays(y, s, w)
    P = w[y].sum()
    if P == 0:
        return float("nan")
    ap, tp_prev = 0.0, 0.0
    tp_c, all_c = 0.0, 0.0
    for thr in np.unique(s)[::-1]:
        g = s == thr
        tp_c += w[g & y].sum()
        all_c += w[g].sum()
        ap += (tp_c - tp_prev) / P * (tp_c / all_c)
        tp_prev = tp_c
    return float(ap)


def _groups(s: np.ndarray):
    """Item indices grouped by distinct score, highest score first."""
    order = np.argsort(-s, kind="stable")
    out, cur, last = [], [], None
    for i in order:
        if last is not None and s[i] != last:
            out.append(cur)
            cur = []
        cur.append(i)
        last = s[i]
    if cur:
        out.append(cur)
    return out


def auroc_bootstrap(y, s, bug_index: np.ndarray, W: np.ndarray, w=None) -> np.ndarray:
    """Bug-level bootstrap of AUROC: item weight = W[b, bug] (x sampling weight). Returns (B,) samples."""
    y, s, w = _as_arrays(y, s, w)
    Wi = W[:, bug_index] * w[None, :]
    Wp, Wn = Wi[:, y], Wi[:, ~y]
    sp, sn = s[y], s[~y]
    K = (sp[:, None] > sn[None, :]) + 0.5 * (sp[:, None] == sn[None, :])
    num = np.einsum("bi,ij,bj->b", Wp, K, Wn)
    den = Wp.sum(axis=1) * Wn.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(den > 0, num / den, np.nan)


def auprc_bootstrap(y, s, bug_index: np.ndarray, W: np.ndarray, w=None) -> np.ndarray:
    y, s, w = _as_arrays(y, s, w)
    Wi = W[:, bug_index] * w[None, :]
    gs = _groups(s)
    G = np.zeros((len(s), len(gs)))
    for j, g in enumerate(gs):
        G[g, j] = 1.0
    tp_g = (Wi * y[None, :]) @ G
    all_g = Wi @ G
    tp_c, all_c = np.cumsum(tp_g, axis=1), np.cumsum(all_g, axis=1)
    P = tp_c[:, -1]
    with np.errstate(divide="ignore", invalid="ignore"):
        prec = np.where(all_c > 0, tp_c / all_c, 0.0)
        ap = (tp_g * prec).sum(axis=1) / P
    return np.where(P > 0, ap, np.nan)


def topk_inspection(y, s, bugs, frac: float) -> dict:
    """Inspect k = floor(frac * N) failures in descending score; ties at the boundary broken uniformly at random.
    Returns exact expectations: test-level PF recall@k, precision@k, and bug-level recall@k (share of bugs with a PF
    test that get >= 1 PF test inspected; hypergeometric within the boundary tie group)."""
    y, s, _ = _as_arrays(y, s, None)
    N = len(s)
    k = int(math.floor(frac * N + 1e-9))
    n_pf = int(y.sum())
    bug_pf = defaultdict(int)
    for b, t in zip(bugs, y):
        if t:
            bug_pf[b] += 1
    out = {"k": k, "n": N, "n_pf": n_pf, "n_bugs_with_pf": len(bug_pf)}
    if n_pf == 0:
        return {**out, "recall": float("nan"), "precision": float("nan") if k == 0 else 0.0, "bug_recall": float("nan")}
    taken, exp_pf = 0, 0.0
    p_bug = {b: 0.0 for b in bug_pf}
    for g in _groups(s):
        if taken >= k:
            break
        m = len(g)
        r = min(m, k - taken)
        pf_in = [i for i in g if y[i]]
        exp_pf += len(pf_in) * r / m
        tb = defaultdict(int)
        for i in pf_in:
            tb[bugs[i]] += 1
        for b, t in tb.items():
            miss = math.comb(m - t, r) / math.comb(m, r) if r < m else 0.0
            p_bug[b] = 1 - (1 - p_bug[b]) * miss
        taken += r
    return {**out, "recall": exp_pf / n_pf, "precision": exp_pf / k if k else float("nan"),
            "bug_recall": float(np.mean(list(p_bug.values())))}


def topk_inspection_weighted(y, s, bugs, w, frac: float) -> dict:
    """As topk_inspection on a weighted population (weights = inverse sampling probabilities). The budget is frac of
    the total weight; a boundary tie group is included in proportion phi; bug-level recall uses independent inclusion
    of tied tests (1 - (1-phi)^t), an approximation stated with the result."""
    y, s, w = _as_arrays(y, s, w)
    K = frac * w.sum()
    P = w[y].sum()
    bug_pf = {b for b, t in zip(bugs, y) if t}
    if P == 0:
        return {"recall": float("nan"), "precision": float("nan"), "bug_recall": float("nan")}
    mass, exp_pf = 0.0, 0.0
    p_bug = {b: 0.0 for b in bug_pf}
    for g in _groups(s):
        if mass >= K - 1e-12:
            break
        gm = w[g].sum()
        phi = min(1.0, (K - mass) / gm)
        exp_pf += phi * sum(w[i] for i in g if y[i])
        tb = defaultdict(int)
        for i in g:
            if y[i]:
                tb[bugs[i]] += 1
        for b, t in tb.items():
            p_bug[b] = 1 - (1 - p_bug[b]) * (1 - phi) ** t
        mass += phi * gm
    return {"recall": exp_pf / P, "precision": exp_pf / K if K else float("nan"),
            "bug_recall": float(np.mean(list(p_bug.values()))), "weighted_budget": K}


# ------------------------------------------------------------------ conformal risk control
def crc_threshold(losses: Sequence[Callable[[float], float]], grid: Sequence[float], alpha: float, B: float = 1.0):
    """Conformal risk control (Angelopoulos et al.): the smallest lambda on `grid` with
    (n/(n+1)) * mean_u L_u(lambda) + B/(n+1) <= alpha, for losses nonincreasing in lambda and bounded by B.
    Returns (lambda_hat or None if no grid point qualifies, the bound at lambda_hat, n)."""
    n = len(losses)
    if n == 0:
        return None, float("nan"), 0
    for lam in sorted(grid):
        risk = float(np.mean([L(lam) for L in losses]))
        bound = n / (n + 1) * risk + B / (n + 1)
        if bound <= alpha:
            return lam, bound, n
    return None, float("nan"), n


# ------------------------------------------------------------------ output-cap scoring (D-130)
CAP_POLICIES = ("as_TF", "keep", "exclude")


def cap_policy_label(label_raw: Optional[str], capped: bool, policy: str) -> Optional[str]:
    """Scored label of one decision under an output-cap policy. Only a call cut off by the output cap changes:
    'as_TF' (the primary-arm policy) scores it TF, 'keep' scores it PF, 'exclude' drops it (None). Any other
    invalid output keeps the primary coding (TF)."""
    if policy not in CAP_POLICIES:
        raise ValueError(policy)
    if label_raw in (PF, TF):
        return label_raw
    if capped and policy == "keep":
        return PF
    if capped and policy == "exclude":
        return None
    return TF


def bugs_lost(rows) -> int:
    """rows: (bug, y_true, y_pred). Bugs with >= 1 PF test of which none is kept (predicted PF)."""
    has, kept = set(), set()
    for b, t, p in rows:
        if t == PF:
            has.add(b)
            if p == PF:
                kept.add(b)
    return len(has - kept)
