"""WP1.4 (D-115; exploratory; zero calls): trained baselines on D1-test with leave-one-project-out validation, and one
exploratory D1 -> D2 transfer.

Models (scikit-learn LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000), threshold 0.5 fixed in D-115,
one-hot encoders fitted inside each training fold, unknown categories ignored, nothing tuned):
  stacker      KUU members' J1 votes (M1, M2, E6b; PF 1, TF 0, invalid 0.5) + failure features
  features     failure features only (no LLM)
  votes        votes only
  stacker+cg   stacker + the WP1.7 cross-generation count (buggy version only)
  features+cg  features + cross-generation count
Failure features (buggy version only): assertion vs exception; exception-class family; deepest project frame
(test/focal/main/none); expected and actual values present.

    python scripts/analysis/revision_learned.py  -> results/revision/wp14_learned.json
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import revision_common as rc  # noqa: E402
from triage import revision_metrics as rm  # noqa: E402
from triage import stats  # noqa: E402
from triage.io_utils import dump_json  # noqa: E402

OUT = rc.OUT / "wp14_learned.json"
CG = rc.OUT / "wp17_cross_gen.json"
MODELS = {"stacker": ("votes", "feat"), "features": ("feat",), "votes": ("votes",), "stacker+cg": ("votes", "feat", "cg"),
          "features+cg": ("feat", "cg")}
FAMILIES = [("assertion", ("AssertionError", "ComparisonFailure", "AssertionFailedError")),
            ("NullPointerException", ("NullPointerException",)),
            ("IllegalArgumentException", ("IllegalArgumentException", "NumberFormatException")),
            ("IllegalStateException", ("IllegalStateException",)),
            ("IndexOutOfBounds", ("IndexOutOfBoundsException", "ArrayIndexOutOfBoundsException",
                                  "StringIndexOutOfBoundsException")),
            ("ClassCastException", ("ClassCastException",)),
            ("UnsupportedOperationException", ("UnsupportedOperationException",)),
            ("ArithmeticException", ("ArithmeticException",))]


def exc_family(exc):
    simple = (exc or "").rsplit(".", 1)[-1]
    for name, members in FAMILIES:
        if simple in members:
            return name
    return "other"


def vote_value(v):
    return 1.0 if v == rc.PF else 0.0 if v == rc.TF else 0.5


def rows(D, cg):
    X = []
    for i in D.ids:
        x = D.instances[i]
        f, cov = x["failure"], x["covariates"]
        v = D.kuu_votes[i]
        X.append({"assertion": 1.0 if cov["failure_type"] == "assertion_failure" else 0.0,
                  "family": exc_family(f.get("exception_class")), "frame": cov["deepest_frame"],
                  "has_values": 1.0 if f.get("expected") is not None and f.get("actual") is not None else 0.0,
                  "v_M1": vote_value(v.get("M1")), "v_M2": vote_value(v.get("M2")), "v_E6B": vote_value(v.get("E6B")),
                  "cg": float(cg[i]["cg"])})
    return X


def pipeline(groups):
    from sklearn.compose import ColumnTransformer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder
    num = []
    cat = []
    if "feat" in groups:
        num += ["assertion", "has_values"]
        cat += ["family", "frame"]
    if "votes" in groups:
        num += ["v_M1", "v_M2", "v_E6B"]
    if "cg" in groups:
        num += ["cg"]
    tr = [("num", "passthrough", num)] + ([("cat", OneHotEncoder(handle_unknown="ignore"), cat)] if cat else [])
    return Pipeline([("pre", ColumnTransformer(tr)),
                     ("lr", LogisticRegression(C=1.0, class_weight="balanced", max_iter=1000))]), num + cat


def frame(X, cols):
    import pandas as pd
    return pd.DataFrame(X)[cols]


def score(D, ids, prob, W, bugs):
    bi = {b: n for n, b in enumerate(bugs)}
    y = [D.lab[i] for i in ids]
    T = np.zeros((len(bugs), 1, 4))
    for i, p in zip(ids, prob):
        t, k = D.lab[i] == rc.PF, p >= 0.5
        T[bi[D.bug[i]], 0, 0 if (t and k) else 2 if t else 1 if k else 3] += 1
    pt, bs = rm.rates_point(T), rm.rates_bootstrap(T, W)
    bug_index = np.array([bi[D.bug[i]] for i in ids])
    out = {k: pt[k] for k in ("tpr", "tnr", "ba", "pf_loss_rate", "share_discarded")}
    out.update({f"{k}_ci95": rc.ci(bs[k]) for k in ("tpr", "tnr", "ba")})
    for m in ("f1", "mcc"):
        out[m] = stats.point_estimate(T, m)
        out[f"{m}_ci95"] = rc.ci(stats.bootstrap_metric(T, m, W))
    out["auroc"] = rm.auroc(y, prob)
    out["auroc_ci95"] = rc.ci(rm.auroc_bootstrap(y, prob, bug_index, W))
    out["auprc"] = rm.auprc(y, prob)
    out["auprc_ci95"] = rc.ci(rm.auprc_bootstrap(y, prob, bug_index, W))
    out["inspection_top20"] = rm.topk_inspection(y, prob, [D.bug[i] for i in ids], 0.20)
    tot = T.sum(axis=0)[0]
    out.update(TP=float(tot[0]), FP=float(tot[1]), FN=float(tot[2]), TN=float(tot[3]))
    return out


def main():
    cgres = json.loads(CG.read_text(encoding="utf-8"))
    D1, D2 = rc.build("D1"), rc.build("D2")
    X1, X2 = rows(D1, cgres["D1"]["per_instance"]), rows(D2, cgres["D2"]["per_instance"])
    y1 = np.array([1 if D1.lab[i] == rc.PF else 0 for i in D1.ids])
    proj = np.array([D1.project[i] for i in D1.ids])
    bugs1, W1 = D1.weights_W()
    bugs2, W2 = D2.weights_W()
    res = {"what": "trained baselines, leave-one-project-out on D1-test; D1 -> D2 transfer (D-115, exploratory)",
           "decisions": ["D-112", "D-115", "D-118"], "n_D1": len(D1.ids), "n_D2": len(D2.ids),
           "fixed_settings": {"model": "LogisticRegression(C=1.0, class_weight='balanced', max_iter=1000)",
                              "threshold": 0.5, "encoders": "one-hot fitted per training fold, unknown ignored",
                              "tuning": "none"},
           "projects": {}, "lopo": {}, "transfer_D1_to_D2": {}, "coefficients_full_D1": {}}
    for p in sorted(set(proj)):
        m = proj == p
        res["projects"][p] = {"n": int(m.sum()), "PF": int(y1[m].sum()), "TF": int((1 - y1[m]).sum()),
                              "training_has_both_classes": bool(len(set(y1[~m])) == 2)}
    for name, groups in MODELS.items():
        oof = np.full(len(D1.ids), np.nan)
        folds = {}
        for p in sorted(set(proj)):
            te = proj == p
            if len(set(y1[~te])) < 2:
                folds[p] = {"status": "unfit: training fold lacks a class"}
                continue
            pipe, cols = pipeline(groups)
            pipe.fit(frame([X1[k] for k in np.where(~te)[0]], cols), y1[~te])
            prob = pipe.predict_proba(frame([X1[k] for k in np.where(te)[0]], cols))[:, 1]
            oof[te] = prob
            yt = y1[te]
            pred = prob >= 0.5
            folds[p] = {"n": int(te.sum()), "PF": int(yt.sum()), "TF": int((1 - yt).sum()),
                        "tpr": float(pred[yt == 1].mean()) if yt.sum() else None,
                        "tnr": float((~pred[yt == 0]).mean()) if (1 - yt).sum() else None}
        fitted = ~np.isnan(oof)
        ids = [i for i, f in zip(D1.ids, fitted) if f]
        bugs_s, W_s = (bugs1, W1) if len(ids) == len(D1.ids) else D1.weights_W(ids)
        res["lopo"][name] = {"groups": list(groups), "n_scored": int(fitted.sum()),
                             **score(D1, ids, list(oof[fitted]), W_s, bugs_s), "folds": folds}
        pipe, cols = pipeline(groups)
        pipe.fit(frame(X1, cols), y1)
        res["coefficients_full_D1"][name] = dict(zip(pipe.named_steps["pre"].get_feature_names_out().tolist(),
                                                     pipe.named_steps["lr"].coef_[0].round(4).tolist()))
        prob2 = pipe.predict_proba(frame(X2, cols))[:, 1]
        res["transfer_D1_to_D2"][name] = score(D2, D2.ids, list(prob2), W2, bugs2)
    res["note"] = ("pooled out-of-fold predictions scored once with bug-level CIs; a fold's own TPR/TNR is null when it "
                   "lacks the class; the transfer is exploratory, not a confirmation (D2 differs in fault process and "
                   "prevalence; the D2 votes come from the KUU D2 runs)")
    dump_json(OUT, res)
    print("projects", res["projects"])
    for part in ("lopo", "transfer_D1_to_D2"):
        print(part)
        for name, r in res[part].items():
            print(f"  {name:12s} TPR {r['tpr']:.3f} TNR {r['tnr']:.3f} BA {r['ba']:.3f} {np.round(r['ba_ci95'], 3)} "
                  f"F1 {r['f1']:.3f} MCC {r['mcc']:.3f} AUROC {r['auroc']:.3f} {np.round(r['auroc_ci95'], 3)} "
                  f"AUPRC {r['auprc']:.3f}")


if __name__ == "__main__":
    main()
