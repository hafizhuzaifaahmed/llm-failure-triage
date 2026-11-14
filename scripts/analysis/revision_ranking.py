"""WP1.3 (D-114; post hoc, descriptive; zero calls): triage as ranking. AUROC and AUPRC with bug-level CIs, and the
developer inspection view at 10/20/30% of failures inspected: test-level PF recall@k, precision@k and bug-level
recall@k (exact expectation over random tie-breaking). D1 is also reweighted to the D1-test labelled population with
the committed inverse sampling weights. Replicated rules: per replicate, then mean.

    python scripts/analysis/revision_ranking.py  -> results/revision/wp13_ranking.json
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import revision_common as rc  # noqa: E402
from triage import revision_metrics as rm  # noqa: E402
from triage.io_utils import dump_json  # noqa: E402

OUT = rc.OUT / "wp13_ranking.json"
FRACS = (0.10, 0.20, 0.30)
RULES = ["KA", "R0", "J1|S1", "SC|S1", "DEB|S1", "MAJ3|S1", "KUU|S1", "P_M1_E6B|S1", "KUUNG|S1", "J1|S1|SON",
         "DEB|S1|SON"]
SCORE_DEF = {"KA": "constant (every failure tied)", "R0": "R0's binary label (PF = 1)",
             "J1|S1": "c/100 if PF, 1 - c/100 if TF, 0.5 invalid (M1)", "DEB|S1": "as J1, M1 adjudicator",
             "SC|S1": "PF vote share of five samples (M1)", "MAJ3|S1": "3 - valid TF votes (KUU panel)",
             "KUU|S1": "3 - valid TF votes (M1, M2, E6b)", "P_M1_E6B|S1": "2 - valid TF votes (M1, E6b)",
             "KUUNG|S1": "3 - valid TF votes (M1, E6b, Llama)", "J1|S1|SON": "as J1, Sonnet", "DEB|S1|SON": "as J1, Sonnet"}


def mean_ci(vals, samples):
    return float(np.nanmean(vals)), rc.ci(np.nanmean(np.vstack(samples), axis=0))


def run(ds):
    D = rc.build(ds)
    bugs, W = D.weights_W()
    bi = {b: k for k, b in enumerate(bugs)}
    ids = D.ids
    y = [D.lab[i] for i in ids]
    bug_index = np.array([bi[D.bug[i]] for i in ids])
    bl = [D.bug[i] for i in ids]
    w = [D.w[i] for i in ids]
    out = {"dataset": ds, "n_instances": len(ids), "n_pf": int(sum(t == rc.PF for t in y)), "n_bugs": len(bugs),
           "n_bugs_with_pf": len({D.bug[i] for i in ids if D.lab[i] == rc.PF}), "rules": {}}
    for c in RULES:
        if c not in D.scores:
            continue
        reps = sorted(D.scores[c])
        auc, ap, auc_s, ap_s, inspect = [], [], [], [], {f: [] for f in FRACS}
        wauc, wap, winspect, lab_auc = [], [], {f: [] for f in FRACS}, []
        for r in reps:
            s = [D.scores[c][r][i] for i in ids]
            auc.append(rm.auroc(y, s))
            ap.append(rm.auprc(y, s))
            auc_s.append(rm.auroc_bootstrap(y, s, bug_index, W))
            ap_s.append(rm.auprc_bootstrap(y, s, bug_index, W))
            for f in FRACS:
                inspect[f].append(rm.topk_inspection(y, s, bl, f))
            if c in ("J1|S1", "DEB|S1", "J1|S1|SON", "DEB|S1|SON"):     # D-114 direction check: label alone
                lab = [1.0 if D.preds[c][r][i] == rc.PF else 0.0 for i in ids]
                lab_auc.append(rm.auroc(y, lab))
            if ds == "D1":
                wauc.append(rm.auroc(y, s, w))
                wap.append(rm.auprc(y, s, w))
                for f in FRACS:
                    winspect[f].append(rm.topk_inspection_weighted(y, s, bl, w, f))
        a, aci = mean_ci(auc, auc_s)
        p, pci = mean_ci(ap, ap_s)
        row = {"score": SCORE_DEF[c], "replicates": len(reps), "auroc": a, "auroc_ci95": aci, "auprc": p, "auprc_ci95": pci,
               "auprc_random": out["n_pf"] / len(ids)}
        if lab_auc:
            row["auroc_label_only"] = float(np.mean(lab_auc))
        row["inspection"] = {f"top{int(f * 100)}": {k: float(np.nanmean([d[k] for d in inspect[f]]))
                                                   for k in ("k", "recall", "precision", "bug_recall")} for f in FRACS}
        if ds == "D1":
            row["reweighted"] = {"auroc": float(np.nanmean(wauc)), "auprc": float(np.nanmean(wap)),
                                 "auprc_random": float(sum(wi for wi, t in zip(w, y) if t == rc.PF) / sum(w)),
                                 "inspection": {f"top{int(f * 100)}": {k: float(np.nanmean([d[k] for d in winspect[f]]))
                                                                    for k in ("recall", "precision", "bug_recall")}
                                                for f in FRACS}}
        out["rules"][c] = {"name": rc.NAMES[c], **row}
    if ds == "D1":
        out["reweighting"] = {"weights": "TF: committed inverse sampling probability (sample_D1_test.json tf_weights); PF: 1",
                              "population": "D1-test labelled failures (PF + TF, AMB excluded)",
                              "assumption": "the sampled TF represent their project's TF (random draw within project)",
                              "bug_recall_note": "tied tests at the budget boundary included independently with the "
                                                 "boundary share (approximation)",
                              "weighted_pf_share": float(sum(wi for wi, t in zip(w, y) if t == rc.PF) / sum(w))}
    return out


def main():
    res = {"what": "triage as ranking (D-114, post hoc, descriptive)", "decisions": ["D-112", "D-114"],
           "D1": run("D1"), "D2": run("D2")}
    dump_json(OUT, res)
    for ds in ("D1", "D2"):
        print(ds, res[ds]["n_instances"], "PF", res[ds]["n_pf"], "bugs w/ PF", res[ds]["n_bugs_with_pf"])
        for c, r in res[ds]["rules"].items():
            i20 = r["inspection"]["top20"]
            extra = f" label-only {r['auroc_label_only']:.3f}" if "auroc_label_only" in r else ""
            rw = r.get("reweighted")
            rws = (f" | rew AUROC {rw['auroc']:.3f} AUPRC {rw['auprc']:.3f} r@20 {rw["inspection"]["top20"]['recall']:.2f}"
                   f" bug@20 {rw["inspection"]["top20"]['bug_recall']:.2f}") if rw else ""
            print(f"  {r['name']:30s} AUROC {r['auroc']:.3f} {np.round(r['auroc_ci95'], 3)} AUPRC {r['auprc']:.3f}"
                  f" r@20 {i20['recall']:.2f} p@20 {i20['precision']:.2f} bug@20 {i20['bug_recall']:.2f}{extra}{rws}")


if __name__ == "__main__":
    main()
