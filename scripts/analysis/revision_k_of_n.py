"""WP1.5 (D-116; post hoc, descriptive; zero calls): discard when >= k of three judges vote TF (invalid or missing is
not a TF vote), k = 1, 2, 3, for the cross-family panels (KUU, KUU-NG) and within-model triples (the first three of the
five SC samples of M1 and of M2). KUU is k = 3 of the KUU panel. No threshold is selected.

    python scripts/analysis/revision_k_of_n.py  -> results/revision/wp15_k_of_n.json
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import revision_common as rc  # noqa: E402
from triage import revision_metrics as rm  # noqa: E402
from triage import stats  # noqa: E402
from triage.io_utils import dump_json  # noqa: E402

OUT = rc.OUT / "wp15_k_of_n.json"


def evaluate(D, votes_by_rep, k):
    """votes_by_rep: rep -> id -> [three votes]. Scored on the ids every replicate covers."""
    ids = sorted(set.intersection(*(set(v) for v in votes_by_rep.values())))
    bugs, W = D.weights_W(ids)
    bi = {b: n for n, b in enumerate(bugs)}
    reps = sorted(votes_by_rep)
    T = np.zeros((len(bugs), len(reps), 4))
    for ri, r in enumerate(reps):
        for i in ids:
            t, keep = D.lab[i] == rc.PF, rm.k_of_n(votes_by_rep[r][i], k) == rc.PF
            T[bi[D.bug[i]], ri, 0 if (t and keep) else 2 if t else 1 if keep else 3] += 1
    pt, bs = rm.rates_point(T), rm.rates_bootstrap(T, W)
    out = {"n": len(ids), "replicates": len(reps), **pt,
           **{f"{m}_ci95": rc.ci(bs[m]) for m in ("tpr", "tnr", "pf_loss_rate")},
           "mcc": stats.point_estimate(T, "mcc"), "mcc_ci95": rc.ci(stats.bootstrap_metric(T, "mcc", W)),
           "f1": stats.point_estimate(T, "f1"), "pf_lost": float(T.sum(axis=0).mean(axis=0)[2])}
    return out


def run(ds):
    D = rc.build(ds)
    triples = {
        "KUU panel (M1, M2, E6b)": {0: {i: [D.kuu_votes[i].get(m) for m in ("M1", "M2", "E6B")] for i in D.ids}},
        "KUU-NG panel (M1, E6b, Llama)": {0: {i: [D.ng_votes[i].get(m) for m in ("M1", "E6B", "NG")] for i in D.ids}},
    }
    for m in ("M1", "M2"):
        if m in D.sc_votes:
            triples[f"{m} within-model (first 3 SC samples)"] = {r: {i: v[:3] for i, v in d.items() if len(v) >= 3}
                                                                  for r, d in D.sc_votes[m].items()}
    out = {"dataset": ds, "n_common": len(D.ids), "triples": {}}
    for name, vb in triples.items():
        out["triples"][name] = {f"k={k}": evaluate(D, vb, k) for k in (1, 2, 3)}
    return out


def main():
    res = {"what": "k-of-3 discard rules (D-116, post hoc, descriptive)", "decisions": ["D-112", "D-116"],
           "rule": "discard iff >= k valid TF votes of three; k=3 of the KUU panel is KUU; k=2 is D-106's 2-of-3",
           "D1": run("D1"), "D2": run("D2")}
    dump_json(OUT, res)
    for ds in ("D1", "D2"):
        print(ds)
        for name, ks in res[ds]["triples"].items():
            for k, r in ks.items():
                print(f"  {name:38s} {k} n {r['n']} loss {r['pf_loss_rate']:.3f} TF-removal {r['tnr']:.3f} "
                      f"BA {r['ba']:.3f} MCC {r['mcc']:.3f} discarded {r['share_discarded']:.3f}")


if __name__ == "__main__":
    main()
