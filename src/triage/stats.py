"""Inference procedures fixed in Phase 2 Section 5.2 and decision rules of Table 18.

Bug-level cluster bootstrap, vectorised: per-bug, per-replicate confusion counts are aggregated by
multinomial bug weights, so one weight matrix serves every condition (paired resampling for free).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
from scipy import stats as sps

from . import config

PF, TF = "PROGRAM_FAULT", "TEST_FAULT"


# ------------------------------------------------------------------------------------------
# Count tensors
# ------------------------------------------------------------------------------------------

def count_tensor(rows: list[dict], bugs: list[str], replicates: list[int]) -> np.ndarray:
    """rows: dicts with bug_id, replicate, y_true, y_pred (scored). Returns (n_bugs, n_reps, 4) TP,FP,FN,TN."""
    bi = {b: i for i, b in enumerate(bugs)}
    ri = {r: i for i, r in enumerate(replicates)}
    T = np.zeros((len(bugs), len(replicates), 4))
    for r in rows:
        if r["y_pred"] is None:
            continue
        t, p = r["y_true"] == PF, r["y_pred"] == PF
        k = 0 if (t and p) else 2 if t else 1 if p else 3
        T[bi[r["bug_id"]], ri[r["replicate"]], k] += 1
    return T


def _metric_from_totals(tot: np.ndarray, metric: str) -> np.ndarray:
    """tot[..., 4] -> metric, vectorised. Averaged over the replicate axis by the caller."""
    tp, fp, fn, tn = tot[..., 0], tot[..., 1], tot[..., 2], tot[..., 3]
    with np.errstate(divide="ignore", invalid="ignore"):
        if metric == "f1":
            return np.where(2 * tp + fp + fn > 0, 2 * tp / (2 * tp + fp + fn), np.nan)
        if metric == "precision":
            return tp / (tp + fp)
        if metric == "recall":
            return tp / (tp + fn)
        if metric == "fpr":
            return fp / (fp + tn)
        if metric == "mcc":
            d = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
            return np.where(d > 0, (tp * tn - fp * fn) / d, 0.0)
    raise ValueError(metric)


def point_estimate(T: np.ndarray, metric: str) -> float:
    return float(np.nanmean(_metric_from_totals(T.sum(axis=0), metric)))


def bootstrap_weights(n_bugs: int, B: int = config.BOOTSTRAP_RESAMPLES, seed: int = config.SEED_BOOTSTRAP):
    rng = np.random.default_rng(seed)
    return rng.multinomial(n_bugs, np.full(n_bugs, 1.0 / n_bugs), size=B).astype(float)


def bootstrap_metric(T: np.ndarray, metric: str, W: np.ndarray) -> np.ndarray:
    n, R, _ = T.shape
    tot = (W @ T.reshape(n, R * 4)).reshape(-1, R, 4)
    return np.nanmean(_metric_from_totals(tot, metric), axis=1)


def percentile_ci(samples: np.ndarray, level: float = 0.95) -> tuple[float, float]:
    a = (1 - level) / 2
    s = samples[~np.isnan(samples)]
    if s.size == 0:  # metric undefined in every resample (e.g. precision of discard-all)
        return float("nan"), float("nan")
    return float(np.quantile(s, a)), float(np.quantile(s, 1 - a))


def bootstrap_p_two_sided(diff_samples: np.ndarray) -> float:
    d = diff_samples[~np.isnan(diff_samples)]
    lo = (np.sum(d <= 0) + 1) / (len(d) + 1)
    hi = (np.sum(d >= 0) + 1) / (len(d) + 1)
    return float(min(1.0, 2 * min(lo, hi)))


@dataclass
class Contrast:
    name: str
    metric: str
    estimate_a: float
    estimate_b: float
    delta: float
    ci95: tuple
    ci90: tuple
    p: float
    p_holm: Optional[float] = None
    conclusion: Optional[str] = None


def paired_contrast(name: str, Ta: np.ndarray, Tb: np.ndarray, metric: str, W: np.ndarray) -> Contrast:
    """Delta = metric(A) - metric(B), bootstrapped with identical bug resamples for A and B."""
    sa, sb = bootstrap_metric(Ta, metric, W), bootstrap_metric(Tb, metric, W)
    d = sa - sb
    ea, eb = point_estimate(Ta, metric), point_estimate(Tb, metric)
    return Contrast(name, metric, ea, eb, ea - eb, percentile_ci(d, 0.95), percentile_ci(d, 0.90),
                    bootstrap_p_two_sided(d))


def holm(pvals: list[float]) -> list[float]:
    m = len(pvals)
    order = np.argsort(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj.tolist()


def holm_adjusted_ci(c: Contrast, adjusted_level: float, diff_samples: np.ndarray) -> tuple:
    return percentile_ci(diff_samples, adjusted_level)


def decide(c: Contrast, sesoi: float = config.SESOI_F1) -> str:
    """Table 18. Uses the Holm-adjusted p for 'demonstrated' and the 90% CI for equivalence."""
    lo90, hi90 = c.ci90
    sig = (c.p_holm if c.p_holm is not None else c.p) < config.ALPHA
    if sig and abs(c.delta) >= sesoi:
        return "effect demonstrated"
    if sig:
        return "detectable but below the practical threshold"
    if lo90 > -sesoi and hi90 < sesoi:
        return "practically equivalent"
    return "inconclusive at this sample size"


# ------------------------------------------------------------------------------------------
# Sensitivity / secondary tests
# ------------------------------------------------------------------------------------------

def mcnemar_exact(correct_a: list[bool], correct_b: list[bool]) -> dict:
    b = sum(a and not c for a, c in zip(correct_a, correct_b))
    c = sum(c and not a for a, c in zip(correct_a, correct_b))
    n = b + c
    p = float(sps.binomtest(b, n, 0.5).pvalue) if n else 1.0
    return {"a_only": b, "b_only": c, "p": p}


def wilcoxon_projects(per_project_a: dict, per_project_b: dict) -> dict:
    keys = sorted(set(per_project_a) & set(per_project_b))
    da = [per_project_a[k] - per_project_b[k] for k in keys
          if not (math.isnan(per_project_a[k]) or math.isnan(per_project_b[k]))]
    nz = sum(x != 0 for x in da)   # zero_method="wilcox" discards zero differences: these are the projects tested
    if len(da) < 2 or all(x == 0 for x in da):
        return {"n_projects": len(da), "n_projects_nonzero": nz, "statistic": None, "p": None}
    res = sps.wilcoxon(da, zero_method="wilcox", alternative="two-sided")
    return {"n_projects": len(da), "n_projects_nonzero": nz, "statistic": float(res.statistic), "p": float(res.pvalue),
            "median_delta": float(np.median(da))}


def cohen_kappa(r1: list, r2: list) -> float:
    cats = sorted(set(r1) | set(r2))
    n = len(r1)
    if n == 0:
        return float("nan")
    po = sum(a == b for a, b in zip(r1, r2)) / n
    pe = sum((r1.count(c) / n) * (r2.count(c) / n) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def leave_one_project_out(rows_a: list[dict], rows_b: list[dict], metric_fn: Callable[[list, list], float]) -> dict:
    """Re-estimate Delta with each project removed in turn. rows carry 'project'."""
    projects = sorted({r["project"] for r in rows_a})
    out = {}
    for p in projects:
        ra = [r for r in rows_a if r["project"] != p]
        rb = [r for r in rows_b if r["project"] != p]
        out[p] = metric_fn(ra, rb)
    return out
