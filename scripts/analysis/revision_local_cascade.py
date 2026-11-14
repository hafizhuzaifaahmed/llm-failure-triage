"""Fully local cascade (D-132; POST HOC on both sets; zero model calls). Reads committed decisions only.

Rule (exactly one, fixed in D-132 before this script read any vote): the D-105 cascade with Tier 2 replaced by the
logged thinking-enabled M1 J1 decision, everything else unchanged.
  Tier 1  KUU's three J1 votes (M1, M2, E6b): all three valid TEST_FAULT -> discard; all three valid PROGRAM_FAULT -> keep.
  Tier 2  anything else (disagreement, an invalid or missing vote) -> the thinking M1 J1 decision: a valid TEST_FAULT or
          PROGRAM_FAULT decides; an invalid answer (including one cut off by the output cap) or a missing one keeps.
Reported beside KUU, thinking J1 alone (primary coding, invalid -> TF), the Sonnet cascade and Sonnet DEB on D-110's
common sets; D1-test once per thinking run. Bug-level cluster bootstrap (committed seed, 10,000 resamples): 95% CIs for
MCC and BA, and descriptive paired 95% CIs for local cascade minus Sonnet cascade in MCC and BA. No p-value, no test.

    python scripts/analysis/revision_local_cascade.py  -> results/revision/local_cascade.json
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import revision_common as rc  # noqa: E402
import revision_think as rt  # noqa: E402
from triage import stats  # noqa: E402
from triage import revision_metrics as rm  # noqa: E402
from triage.io_utils import dump_json  # noqa: E402

OUT = rc.OUT / "local_cascade.json"
MEMBERS = ("M1", "M2", "E6B")
COMPARE = {"KUU|S1": "KUU", "CAS|S1": "Sonnet cascade", "DEB|S1|SON": "Sonnet DEB"}


def tier1(votes):
    """Unanimous valid votes decide; anything else escalates (None). Same as scripts/analysis/cascade.py."""
    if len(votes) == 3 and all(v == rc.TF for v in votes):
        return rc.TF
    if len(votes) == 3 and all(v == rc.PF for v in votes):
        return rc.PF
    return None


def local_cascade(votes, thinking_label):
    """D-132: Tier 1 as D-105; Tier 2 the thinking J1 label if valid, otherwise keep."""
    t = tier1(votes)
    if t is not None:
        return t
    return thinking_label if thinking_label in (rc.TF, rc.PF) else rc.PF


def tensor_reps(D, ids, preds_by_rep):
    """(bugs, replicates, 4) count tensor; bugs sorted as everywhere else in the revision analyses."""
    bugs = sorted({D.bug[i] for i in ids})
    bi = {b: n for n, b in enumerate(bugs)}
    reps = sorted(preds_by_rep)
    T = np.zeros((len(bugs), len(reps), 4))
    for k, r in enumerate(reps):
        for i in ids:
            t, p = D.lab[i] == rc.PF, preds_by_rep[r][i] == rc.PF
            T[bi[D.bug[i]], k, 0 if (t and p) else 2 if t else 1 if p else 3] += 1
    return T


def describe(D, ids, preds_by_rep, W):
    T = tensor_reps(D, ids, preds_by_rep)
    pt, bs = rm.rates_point(T), rm.rates_bootstrap(T, W)
    bl = [rm.bugs_lost([(D.bug[i], D.lab[i], p[i]) for i in ids]) for p in preds_by_rep.values()]
    return {"f1": stats.point_estimate(T, "f1"), "mcc": stats.point_estimate(T, "mcc"),
            "mcc_ci95": rc.ci(stats.bootstrap_metric(T, "mcc", W)), "ba": pt["ba"], "ba_ci95": rc.ci(bs["ba"]),
            "tpr": pt["tpr"], "tnr": pt["tnr"], "pf_lost": float(T[:, :, 2].sum(axis=0).mean()),
            "bugs_lost": float(np.mean(bl)), "share_discarded": pt["share_discarded"], "replicates": T.shape[1],
            "n": len(ids)}


def paired(D, ids, a, b, W):
    Ta, Tb = tensor_reps(D, ids, a), tensor_reps(D, ids, b)
    c = stats.paired_contrast("local - Sonnet cascade", Ta, Tb, "mcc", W)
    ra, rb = rm.rates_bootstrap(Ta, W)["ba"], rm.rates_bootstrap(Tb, W)["ba"]
    return {"mcc": {"delta": c.delta, "ci95": list(c.ci95)},
            "ba": {"delta": rm.rates_point(Ta)["ba"] - rm.rates_point(Tb)["ba"], "ci95": rc.ci(ra - rb)}}


def one_set(ds, calls):
    D = rc.build(ds)
    ids = D.ids
    bugs = sorted({D.bug[i] for i in ids})
    W = stats.bootstrap_weights(len(bugs))
    assert all(i in D.kuu_votes for i in ids), "a common-set instance has no KUU votes"
    votes = {i: [D.kuu_votes[i].get(m) for m in MEMBERS] for i in ids}
    comp = {c: {r: {i: (rc.PF if p[i] == rc.PF else rc.TF) for i in ids} for r, p in D.preds[c].items()}
            for c in COMPARE}
    out = {"n_instances": len(ids), "n_bugs": len(bugs),
           "share_escalated": sum(tier1(votes[i]) is None for i in ids) / len(ids),
           "comparators": {nm: describe(D, ids, comp[c], W) for c, nm in COMPARE.items()}, "runs": {}}
    for name, rep in rt.RUNS[ds]:
        run = rt.load_run(name, rep, calls)
        if run is None:
            out["runs"][str(rep)] = {"status": "not run"}
            continue
        lab = {i: (run[i]["label"] if i in run else None) for i in ids}
        esc = [i for i in ids if tier1(votes[i]) is None]
        local = {0: {i: local_cascade(votes[i], lab[i]) for i in ids}}
        alone = {0: {i: (rc.PF if lab[i] == rc.PF else rc.TF) for i in ids}}
        out["runs"][str(rep)] = {
            "run": name, "missing_in_thinking_run": sum(lab[i] is None for i in ids),
            "escalated": len(esc), "escalated_kept_as_invalid": sum(lab[i] not in (rc.TF, rc.PF) for i in esc),
            "local_cascade": describe(D, ids, local, W), "thinking_alone": describe(D, ids, alone, W),
            "local_minus_sonnet_cascade": paired(D, ids, local, comp["CAS|S1"], W)}
    done = [v for v in out["runs"].values() if "local_cascade" in v]
    out["range"] = {}
    for part in ("local_cascade", "thinking_alone"):
        out["range"][part] = {m: {"min": min(v[part][m] for v in done), "max": max(v[part][m] for v in done),
                                  "mean": float(np.mean([v[part][m] for v in done]))}
                              for m in ("f1", "mcc", "ba", "tpr", "tnr", "pf_lost", "bugs_lost", "share_discarded")}
    return out


def main():
    calls = rt.call_index()
    res = {"what": "fully local cascade: KUU unanimity, disagreements to the logged thinking-enabled M1 J1 (D-132)",
           "status": "post hoc on both sets (D2 seen; D1-test exploratory); to be confirmed on fresh data",
           "D2": one_set("D2", calls), "D1": one_set("D1", calls)}
    dump_json(OUT, res)
    for ds in ("D2", "D1"):
        r = res[ds]
        print(ds, "n", r["n_instances"], "escalated", round(r["share_escalated"], 3))
        for rep, v in r["runs"].items():
            if "local_cascade" in v:
                lc, ta, dd = v["local_cascade"], v["thinking_alone"], v["local_minus_sonnet_cascade"]
                print(f"  run {rep}: local BA {lc['ba']:.3f} MCC {lc['mcc']:.3f} F1 {lc['f1']:.3f} lost {lc['pf_lost']:.0f}"
                      f" bugs {lc['bugs_lost']:.0f} | alone BA {ta['ba']:.3f} | dBA {dd['ba']['delta']:+.3f} {dd['ba']['ci95']}"
                      f" dMCC {dd['mcc']['delta']:+.3f} {dd['mcc']['ci95']} | invalid-kept {v['escalated_kept_as_invalid']}")
        for nm, c in r["comparators"].items():
            print(f"  {nm:15s} BA {c['ba']:.3f} MCC {c['mcc']:.3f} F1 {c['f1']:.3f} lost {c['pf_lost']:.1f} bugs {c['bugs_lost']:.1f}")


if __name__ == "__main__":
    main()
