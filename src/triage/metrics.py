"""Classification metrics with PF as the positive class (Phase 2 Section 5.1, Table 17).

Accuracy is deliberately absent. Replicates are scored separately and averaged by the caller
(`per_replicate_then_mean`), never pooled as if they were independent instances.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable, Optional

import numpy as np

PF, TF, INVALID = "PROGRAM_FAULT", "TEST_FAULT", "INVALID"


def score_label(label_raw: str, invalid_policy: str = "as_TF") -> Optional[str]:
    """Primary analysis: INVALID -> TF. Sensitivity: invalid_policy='exclude' returns None."""
    if label_raw == INVALID:
        return TF if invalid_policy == "as_TF" else None
    return label_raw


def confusion(y_true: Iterable[str], y_pred: Iterable[str], weights: Optional[Iterable[float]] = None) -> dict:
    tp = fp = fn = tn = 0.0
    ws = weights if weights is not None else None
    for i, (t, p) in enumerate(zip(y_true, y_pred)):
        if p is None:
            continue
        w = 1.0 if ws is None else ws[i]
        if t == PF and p == PF:
            tp += w
        elif t == PF:
            fn += w
        elif p == PF:
            fp += w
        else:
            tn += w
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn}


def _div(a, b):
    return a / b if b else float("nan")


def from_counts(c: dict) -> dict:
    tp, fp, fn, tn = c["TP"], c["FP"], c["FN"], c["TN"]
    p = _div(tp, tp + fp)
    r = _div(tp, tp + fn)
    f1 = _div(2 * tp, 2 * tp + fp + fn)  # equals 2PR/(P+R); defined as 0 when TP=0 and FP+FN>0
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = (tp * tn - fp * fn) / denom if denom else 0.0
    return {"precision": p, "recall": r, "f1": f1, "fpr": _div(fp, fp + tn), "fnr": _div(fn, fn + tp),
            "mcc": mcc, "pf_lost": fn, **c}


def classification_metrics(y_true, y_pred) -> dict:
    return from_counts(confusion(y_true, y_pred))


def prevalence_adjusted_precision(y_true, y_pred, tf_weights) -> float:
    """TF instances weighted by inverse sampling probability (1 for PF, which are all kept)."""
    c = confusion(y_true, y_pred, tf_weights)
    return _div(c["TP"], c["TP"] + c["FP"])


def bug_level_retention(bug_ids, y_true, y_pred) -> float:
    """Share of bugs with >=1 PF instance for which >=1 PF instance is predicted PF."""
    has_pf, kept = set(), set()
    for b, t, p in zip(bug_ids, y_true, y_pred):
        if t == PF:
            has_pf.add(b)
            if p == PF:
                kept.add(b)
    return _div(len(kept), len(has_pf))


def average_precision(y_true, scores) -> float:
    """PR-AUC as step-wise average precision. Used ONLY for the SC vote share."""
    y = np.array([t == PF for t in y_true], dtype=float)
    s = np.asarray(scores, dtype=float)
    if y.sum() == 0:
        return float("nan")
    ap, prev_r = 0.0, 0.0
    for thr in np.unique(s)[::-1]:
        pred = s >= thr
        tp = (pred & (y == 1)).sum()
        p = tp / pred.sum()
        r = tp / y.sum()
        ap += p * (r - prev_r)
        prev_r = r
    return float(ap)


def per_replicate_then_mean(records: list[dict], gt: dict, invalid_policy: str = "as_TF",
                            tf_weights: Optional[dict] = None, bug_of: Optional[dict] = None) -> dict:
    """records: decision records of ONE condition (arm x level x variant x model). gt: instance_id -> PF/TF."""
    by_rep = defaultdict(list)
    for r in records:
        if r["instance_id"] in gt:
            by_rep[r["replicate"]].append(r)
    per = []
    for rep, rs in sorted(by_rep.items()):
        y_true = [gt[r["instance_id"]] for r in rs]
        y_pred = [score_label(r["label_raw"], invalid_policy) for r in rs]
        m = classification_metrics(y_true, y_pred)
        if tf_weights:
            w = [1.0 if gt[r["instance_id"]] == PF else tf_weights.get(r["instance_id"], 1.0) for r in rs]
            m["precision_prev_adj"] = prevalence_adjusted_precision(y_true, y_pred, w)
        if bug_of:
            m["bug_retention"] = bug_level_retention([bug_of[r["instance_id"]] for r in rs], y_true, y_pred)
        m["invalid_rate"] = sum(r["label_raw"] == INVALID for r in rs) / len(rs)
        m["n"] = len(rs)
        per.append(m)
    keys = per[0].keys() if per else []
    mean = {k: float(np.nanmean([m[k] for m in per])) for k in keys}
    mean["replicates"] = len(per)
    mean["per_replicate"] = per
    return mean
