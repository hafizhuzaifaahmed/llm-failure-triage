"""Error diversity behind keep-unless-unanimous (D-105). Zero model calls; reads committed decision logs only.
Committed before any E9b call. Pre-specified exploratory analysis (no Holm family); D1 is post hoc, D2 is the
pre-registered read.

Question: does KUU protect bug-revealing tests because judges from different families make DIFFERENT mistakes, compared
with the correlated mistakes of repeated samples from one family?

Definitions (instances = the KUU comparison set: scored, PF or TF, not leakage-aborted in any contributing run):
  miss_j(i)       judge j's single-call J1 vote on PF instance i is a valid TEST_FAULT (an invalid vote is not a miss,
                  as KUU keeps on an invalid vote; invalid counts are reported).
  m_j             miss rate = sum_i miss_j(i) / n_PF.
  c_jk            pairwise co-error = share of PF instances both j and k miss; c_123 = all three miss = KUU's loss.
  lift_jk         c_jk / (m_j m_k): 1 = independent errors, > 1 = correlated errors.
  predicted loss  n_PF * m_1 m_2 m_3 (independence) against observed n_PF * c_123.
Cross-family votes: M1, M2, E6b J1 at S1 — D1 the E8 VOTE3 calls (replicate 10), D2 the KUU runs (replicate 20).
Within-family repeats: the first three of the five SC samples (same prompt, same model, independent samples) of each
judge's committed SC run at S1, replicate 0 — D1: M1 LOCAL_HO_E1E3_M1, M2 LOCAL_HO_E5R3_M2, E6b LOCAL_HO_E6B_D1TEST;
D2: M1 LOCAL_HO_E5R1_D2, M2 LOCAL_HO_E5R3_M2_D2 (no E6b SC run exists on D2). Within-family pairwise quantities are
averaged over the three sample pairs; the within-family "unanimous" loss is all three samples TEST_FAULT.
Pairwise agreement on all instances (both valid and equal) is reported for cross- and within-family pairs.
Comparison: mean cross-family lift (over the three pairs) minus mean within-family lift (over the judges available),
and KUU's observed loss minus each judge's within-family unanimous loss, each with a 95% bug-level bootstrap CI
(committed seed and B). Reading fixed in advance: error diversity explains KUU's protection when cross-family lift is
below within-family lift (CI of the difference below 0) and the cross-family unanimous loss is below the within-family
ones; otherwise it does not, and that is reported as such.

    python scripts/analysis/error_diversity.py   -> results/kuu/analysis/error_diversity.json
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config, stats  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

RUNS = ROOT / "results" / "runs_local"
OUT = ROOT / "results" / "kuu" / "analysis" / "error_diversity.json"
TF, PF = "TEST_FAULT", "PROGRAM_FAULT"
PLAN = {
    "D1": {"status": "post hoc (development evidence)", "sample": "sample_D1_test.json", "labels": "labels_D1.jsonl",
           "votes": {"M1": ("LOCAL_HO_E8_VOTE_M1", 10), "M2": ("LOCAL_HO_E8_VOTE_M2", 10),
                     "E6B": ("LOCAL_HO_E8_VOTE_E6B", 10)},
           "sc": {"M1": "LOCAL_HO_E1E3_M1", "M2": "LOCAL_HO_E5R3_M2", "E6B": "LOCAL_HO_E6B_D1TEST"},
           "extra_aborts": ["LOCAL_HO_E1E3_M1"]},
    "D2": {"status": "pre-registered (D-105), exploratory", "sample": "sample_D2_test.json", "labels": "labels_D2.jsonl",
           "votes": {"M1": ("LOCAL_HO_KUU_D2_M1", 20), "M2": ("LOCAL_HO_KUU_D2_M2", 20),
                     "E6B": ("LOCAL_HO_KUU_D2_E6B", 20)},
           "sc": {"M1": "LOCAL_HO_E5R1_D2", "M2": "LOCAL_HO_E5R3_M2_D2"},
           "extra_aborts": ["LOCAL_HO_E5R1_D2"]},
}


def s1(d):
    return d.get("level") == "S1" and (d.get("variant") or "full") == "full"


def aborts(run):
    f = RUNS / run / "leakage_rejections.jsonl"
    return {r["instance_id"] for r in read_jsonl(f) if r.get("level") == "S1"} if f.exists() else set()


def by_bug(values: dict, ids: list, bug_of: dict, bugs: list) -> np.ndarray:
    """Per-bug sums of a 0/1 per-instance indicator, in bug order."""
    bi = {b: k for k, b in enumerate(bugs)}
    v = np.zeros(len(bugs))
    for i in ids:
        v[bi[bug_of[i]]] += values.get(i, 0)
    return v


def ratio(num, den, W):
    with np.errstate(divide="ignore", invalid="ignore"):
        return (W @ num) / (W @ den)


def run(name, plan):
    samp = json.loads((config.PROCESSED / plan["sample"]).read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = {l["instance_id"]: l for l in read_jsonl(config.GT_STORE / plan["labels"]) if l["instance_id"] in keep}
    votes = {}
    for m, (r, rep) in plan["votes"].items():
        for d in read_jsonl(RUNS / r / "decisions.jsonl"):
            if d["arm"] == "J1" and s1(d) and d["replicate"] == rep:
                votes.setdefault(d["instance_id"], {})[m] = d["label_raw"]
    sc = {}
    for m, r in plan["sc"].items():
        for d in read_jsonl(RUNS / r / "decisions.jsonl"):
            if d["arm"] == "SC" and s1(d) and d["replicate"] == 0:
                sc.setdefault(m, {})[d["instance_id"]] = (d.get("votes") or [])[:3]
    ab = set().union(*(aborts(r) for r, _ in plan["votes"].values()), *(aborts(r) for r in plan["extra_aborts"]),
                     *(aborts(r) for r in plan["sc"].values()))
    ids = sorted(i for i, l in labels.items() if l["label"] in ("PF", "TF") and i not in ab
                 and len(votes.get(i, {})) == 3 and all(i in sc[m] for m in sc))
    pf = [i for i in ids if labels[i]["label"] == "PF"]
    bug_of = {i: labels[i]["bug_name"] for i in ids}
    bugs = sorted(set(bug_of.values()))
    W = stats.bootstrap_weights(len(bugs))
    n_pf = by_bug({i: 1 for i in pf}, pf, bug_of, bugs)
    judges = list(plan["votes"])
    miss = {m: {i: int(votes[i][m] == TF) for i in pf} for m in judges}
    est = lambda num: float(num.sum() / n_pf.sum())
    out = {"dataset": name, "status": plan["status"], "n_instances": len(ids), "n_pf": len(pf), "n_bugs": len(bugs),
           "invalid_votes": {m: sum(votes[i][m] not in (TF, PF) for i in ids) for m in judges}}
    mb = {m: by_bug(miss[m], pf, bug_of, bugs) for m in judges}
    out["miss_rate"] = {m: {"est": est(mb[m]), "ci95": stats.percentile_ci(ratio(mb[m], n_pf, W))} for m in judges}
    cross_lift_samples, cross = [], {}
    for a, b in itertools.combinations(judges, 2):
        co = by_bug({i: miss[a][i] * miss[b][i] for i in pf}, pf, bug_of, bugs)
        lift_s = ratio(co, n_pf, W) / (ratio(mb[a], n_pf, W) * ratio(mb[b], n_pf, W))
        agree = sum(votes[i][a] == votes[i][b] and votes[i][a] in (TF, PF) for i in ids) / len(ids)
        cross[f"{a}-{b}"] = {"co_error": est(co), "co_error_ci95": stats.percentile_ci(ratio(co, n_pf, W)),
                             "independent_prediction": est(mb[a]) * est(mb[b]),
                             "lift": est(co) / (est(mb[a]) * est(mb[b])) if est(mb[a]) * est(mb[b]) else None,
                             "lift_ci95": stats.percentile_ci(lift_s), "agreement_all_instances": agree}
        cross_lift_samples.append(lift_s)
    out["cross_family"] = cross
    triple = by_bug({i: int(all(miss[m][i] for m in judges)) for i in pf}, pf, bug_of, bugs)
    pred_s = n_pf.sum() * np.prod([ratio(mb[m], n_pf, W) for m in judges], axis=0)
    out["kuu_loss"] = {"observed": float(triple.sum()), "observed_share": est(triple),
                       "independence_prediction": float(n_pf.sum() * np.prod([est(mb[m]) for m in judges])),
                       "independence_prediction_ci95": stats.percentile_ci(pred_s)}
    within, within_lift_samples = {}, []
    for m, s in sc.items():
        smiss = [{i: int(len(s[i]) > k and s[i][k] == TF) for i in pf} for k in range(3)]
        sb = [by_bug(x, pf, bug_of, bugs) for x in smiss]
        rate = float(np.mean([est(x) for x in sb]))
        rate_s = np.mean([ratio(x, n_pf, W) for x in sb], axis=0)
        cos = [by_bug({i: smiss[a][i] * smiss[b][i] for i in pf}, pf, bug_of, bugs) for a, b in ((0, 1), (0, 2), (1, 2))]
        co = float(np.mean([est(c) for c in cos]))
        co_s = np.mean([ratio(c, n_pf, W) for c in cos], axis=0)
        lift_s = co_s / rate_s ** 2
        un = by_bug({i: int(all(x[i] for x in smiss)) for i in pf}, pf, bug_of, bugs)
        agree = float(np.mean([sum(len(s[i]) > max(a, b) and s[i][a] == s[i][b] and s[i][a] in (TF, PF) for i in ids)
                               / len(ids) for a, b in ((0, 1), (0, 2), (1, 2))]))
        within[m] = {"miss_rate": rate, "co_error": co, "co_error_ci95": stats.percentile_ci(co_s),
                     "lift": co / rate ** 2 if rate else None, "lift_ci95": stats.percentile_ci(lift_s),
                     "unanimous_loss": float(un.sum()), "unanimous_loss_share": est(un),
                     "agreement_all_instances": agree,
                     "kuu_minus_within_unanimous_loss": {
                         "delta": float(triple.sum() - un.sum()),
                         "ci95": stats.percentile_ci(W @ (triple - un))}}
        within_lift_samples.append(lift_s)
    out["within_family"] = within
    d = np.mean(cross_lift_samples, axis=0) - np.mean(within_lift_samples, axis=0)
    cl = float(np.mean([v["lift"] for v in cross.values()]))
    wl = float(np.mean([v["lift"] for v in within.values()]))
    out["comparison"] = {"mean_cross_family_lift": cl, "mean_within_family_lift": wl, "difference": cl - wl,
                         "difference_ci95": stats.percentile_ci(d), "p_two_sided": stats.bootstrap_p_two_sided(d),
                         "error_diversity_supported": bool(stats.percentile_ci(d)[1] < 0 and all(
                             v["kuu_minus_within_unanimous_loss"]["delta"] < 0 for v in within.values())),
                         "reading": "supported when cross-family lift is below within-family lift (CI below 0) and "
                                    "KUU's loss is below every within-family unanimous loss (D-105)"}
    return out


def main():
    res = {k: run(k, p) for k, p in PLAN.items()}
    dump_json(OUT, {"what": "error diversity behind KUU (D-105)", "decisions": ["D-95", "D-105"], **res})
    for k, v in res.items():
        print(k, v["status"], "n", v["n_instances"], "PF", v["n_pf"])
        print("  miss", {m: round(x["est"], 3) for m, x in v["miss_rate"].items()})
        print("  cross lift", {p: round(x["lift"], 2) if x["lift"] else None for p, x in v["cross_family"].items()})
        print("  within lift", {m: round(x["lift"], 2) if x["lift"] else None for m, x in v["within_family"].items()})
        print("  KUU loss", v["kuu_loss"]["observed"], "pred", round(v["kuu_loss"]["independence_prediction"], 2),
              " within unanimous", {m: x["unanimous_loss"] for m, x in v["within_family"].items()})
        print("  comparison", {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v["comparison"].items()
                               if kk != "reading"})


if __name__ == "__main__":
    main()
