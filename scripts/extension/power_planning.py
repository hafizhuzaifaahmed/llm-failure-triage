"""EXT-3 (D-140): planning simulation for the CFP confirmation. Planning only; not a result.

Resamples the pilot's bugs (ledger CFP_D1_TEST, labels known) into sets with 30, 40 and 50 bugs that carry a
bug-revealing (PF) test, other bugs in the pilot's proportion, under two scenarios: the pilot's effect, and half of
it (each test's probe flags are kept with probability 1/2 and otherwise replaced by the flags of a test drawn from
the label-pooled set, which halves every flag-rate difference in expectation). For C1 to C4 it reports how often
the bootstrap p falls below 0.05 and below 0.0125 (the strictest Holm step for four tests), and the median interval
half-width. It also tabulates exact one-sided 95% upper bounds on a bug-loss rate.

    python scripts/extension/power_planning.py  -> results/extension/planning/power_planning.json
                                                   docs/research_extension/generated/power_planning.md
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage import revision_metrics as rm  # noqa: E402
from triage.io_utils import read_jsonl  # noqa: E402

SEED, SIMS, INNER = 20261111, 400, 1000
N_PF_BUGS = (30, 40, 50)
SCENARIOS = {"pilot_effect": 1.0, "half_effect": 0.5}
VOTE_RUNS = {"M1": "LOCAL_HO_E8_VOTE_M1", "M2": "LOCAL_HO_E8_VOTE_M2", "M3": "LOCAL_HO_E8_VOTE_E6B"}
ADEQUATE = 0.80


def p_two_sided(d):
    lo = (np.sum(d <= 0) + 1) / (len(d) + 1)
    hi = (np.sum(d >= 0) + 1) / (len(d) + 1)
    return float(min(1.0, 2 * min(lo, hi)))


def wrate(w, mask, flag):
    den = (w * mask).sum(-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, (w * mask * flag).sum(-1) / den, np.nan)


def main():
    led = {r["instance_id"]: r for r in read_jsonl(ROOT / "results" / "extension" / "probes" / "CFP_D1_TEST" / "ledger.jsonl")}
    lab = {l["instance_id"]: l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl")
           if l["split"] == "test" and l["label"] in ("PF", "TF") and l["instance_id"] in led}
    votes = {}
    for name, run in VOTE_RUNS.items():
        for r in read_jsonl(ROOT / "results" / "runs_local" / run / "decisions.jsonl"):
            if r["arm"] == "J1" and r.get("level") == "S1" and (r.get("variant") or "full") == "full" and r["replicate"] == 10:
                votes.setdefault(r["instance_id"], {})[name] = r["label_raw"]
    ids = sorted(lab)
    y = np.array([1 if lab[i]["label"] == "PF" else 0 for i in ids])
    bug_names = sorted({lab[i]["bug_name"] for i in ids})
    bug = np.array([bug_names.index(lab[i]["bug_name"]) for i in ids])
    flags = np.array([[1.0 if led[i]["summary"].get(f) else 0.0 for f in ("flip", "rcf", "decoupled")] for i in ids])
    has3 = np.array([len(votes.get(i, {})) == 3 for i in ids])
    kuu_keep = np.array([1.0 if (has3[k] and rm.k_of_n([votes[i].get(m) for m in ("M1", "M2", "M3")], 3) == rm.PF) else 0.0
                         for k, i in enumerate(ids)])
    maj_keep = np.array([1.0 if (has3[k] and rm.k_of_n([votes[i].get(m) for m in ("M1", "M2", "M3")], 2) == rm.PF) else 0.0
                         for k, i in enumerate(ids)])
    pf_bugs = np.array(sorted({b for b, yy in zip(bug, y) if yy}))
    tf_bugs = np.array(sorted(set(bug) - set(pf_bugs)))
    members = {b: np.where(bug == b)[0] for b in range(len(bug_names))}
    ratio = len(tf_bugs) / len(pf_bugs)
    rng = np.random.default_rng(SEED)
    out = {"decision": "D-140", "status": "PLANNING SIMULATION ON PILOT DATA; not a result", "seed": SEED,
           "simulated_sets_per_cell": SIMS, "inner_resamples": INNER,
           "pilot": {"instances": len(ids), "PF": int(y.sum()), "bugs_with_PF": len(pf_bugs), "other_bugs": len(tf_bugs),
                     "instances_with_three_votes": int(has3.sum())},
           "cells": {}, "adequate_rule": "share >= 0.80 at p < 0.0125 under half_effect with 30 bugs"}

    for scen, keep_prob in SCENARIOS.items():
        for n in N_PF_BUGS:
            m = int(round(n * ratio))
            hits = {h: {"p05": 0, "p0125": 0, "hw": [], "sign_ok": 0} for h in ("C1", "C2", "C3", "C4")}
            for _ in range(SIMS):
                chosen = np.concatenate([rng.choice(pf_bugs, n, replace=True), rng.choice(tf_bugs, m, replace=True)])
                idx = np.concatenate([members[b] for b in chosen])
                cl = np.concatenate([np.full(len(members[b]), k) for k, b in enumerate(chosen)])
                yy, fl = y[idx], flags[idx].copy()
                if keep_prob < 1.0:                      # shrink: replace flags by a label-blind donor's flags
                    swap = rng.random(len(idx)) >= keep_prob
                    fl[swap] = flags[rng.integers(0, len(ids), int(swap.sum()))]
                W = rng.multinomial(len(chosen), np.full(len(chosen), 1.0 / len(chosen)), size=INNER).astype(float)[:, cl]
                pf, tf = (yy == 1).astype(float), (yy == 0).astype(float)
                one = np.ones((1, len(idx)))
                d = {"C1": wrate(W, pf, fl[:, 0]) - wrate(W, tf, fl[:, 0]),
                     "C2": wrate(W, tf, fl[:, 2]) - wrate(W, pf, fl[:, 2])}
                pt = {"C1": float((wrate(one, pf, fl[:, 0]) - wrate(one, tf, fl[:, 0]))[0]),
                      "C2": float((wrate(one, tf, fl[:, 2]) - wrate(one, pf, fl[:, 2]))[0])}
                v = has3[idx]
                if v.any() and pf[v].sum() and tf[v].sum():
                    Wv, pv, tv = W[:, v], pf[v], tf[v]
                    k0, m0 = kuu_keep[idx][v], maj_keep[idx][v]
                    k1 = np.where(fl[v, 2] == 1, 0.0, k0)                    # CD: discard a decoupled failure
                    m1 = np.where(fl[v, 1] == 1, 1.0, m0)                    # CK: keep a sibling-safe flip

                    def ba(w, keep):
                        return ((w * pv * keep).sum(-1) / np.maximum((w * pv).sum(-1), 1e-12)
                                + (w * tv * (1 - keep)).sum(-1) / np.maximum((w * tv).sum(-1), 1e-12)) / 2

                    ov = np.ones((1, int(v.sum())))
                    d["C3"] = ba(Wv, k1) - ba(Wv, k0)
                    pt["C3"] = float((ba(ov, k1) - ba(ov, k0))[0])
                    d["C4"] = (Wv * pv * (1 - m1)).sum(-1) - (Wv * pv * (1 - m0)).sum(-1)
                    pt["C4"] = float(((ov * pv * (1 - m1)).sum(-1) - (ov * pv * (1 - m0)).sum(-1))[0])
                expect = {"C1": 1, "C2": 1, "C3": 1, "C4": -1}
                for h, dd in d.items():
                    dd = dd[~np.isnan(dd)]
                    p = p_two_sided(dd)
                    ok = np.sign(pt[h]) == expect[h]
                    hits[h]["p05"] += int(p < 0.05 and ok)
                    hits[h]["p0125"] += int(p < 0.0125 and ok)
                    hits[h]["sign_ok"] += int(ok)
                    hits[h]["hw"].append(float(np.percentile(dd, 97.5) - np.percentile(dd, 2.5)) / 2)
            out["cells"][f"{scen}|{n}"] = {
                "bugs_with_PF": n, "other_bugs": m, "scenario": scen,
                **{h: {"share_p_below_0.05": round(v["p05"] / SIMS, 3), "share_p_below_0.0125": round(v["p0125"] / SIMS, 3),
                       "share_predicted_sign": round(v["sign_ok"] / SIMS, 3),
                       "median_ci_half_width": round(float(np.median(v["hw"])), 3) if v["hw"] else None}
                   for h, v in hits.items()}}
    out["bug_loss_upper95"] = {str(n): {str(k): round(float(sps.beta.ppf(0.95, k + 1, n - k)), 4) for k in (0, 1, 2)}
                               for n in N_PF_BUGS}
    out["classification"] = {h: ("adequately powered" if out["cells"]["half_effect|30"][h]["share_p_below_0.0125"] >= ADEQUATE
                                 else "underpowered") for h in ("C1", "C2", "C3", "C4")}
    dest = ROOT / "results" / "extension" / "planning" / "power_planning.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8")

    L = ["# Planning simulation for the CFP confirmation (generated; do not edit)", "",
         "Source: `results/extension/planning/power_planning.json` (D-140). **Planning only, on pilot data; not a result.**",
         f"{SIMS} simulated sets per cell, {INNER} inner resamples, seed {SEED}. Shares count sets where the bootstrap p is "
         "below the threshold *and* the estimate has the predicted sign.", "",
         "## Share of simulated sets in which each hypothesis would be supported", "",
         "| Scenario | Bugs with a PF test | Hypothesis | p < 0.05 | p < 0.0125 (strictest Holm step) | Median 95% CI half-width |",
         "|---|---|---|---|---|---|"]
    for key, c in out["cells"].items():
        for h in ("C1", "C2", "C3", "C4"):
            L.append(f"| {c['scenario']} | {c['bugs_with_PF']} | {h} | {c[h]['share_p_below_0.05']:.3f} | "
                     f"{c[h]['share_p_below_0.0125']:.3f} | {c[h]['median_ci_half_width']} |")
    L += ["", "## Exact one-sided 95% upper bound on the bug-loss rate", "",
          "| Bugs with a PF test | 0 bugs lost | 1 bug lost | 2 bugs lost |", "|---|---|---|---|"]
    for n, row in out["bug_loss_upper95"].items():
        L.append(f"| {n} | {row['0']:.3f} | {row['1']:.3f} | {row['2']:.3f} |")
    L += ["", "## Classification (rule fixed in D-140: share >= 0.80 at p < 0.0125, half effect, 30 bugs)", "",
          "| Hypothesis | Classification |", "|---|---|"]
    L += [f"| {h} | {c} |" for h, c in out["classification"].items()]
    md = ROOT / "docs" / "research_extension" / "generated" / "power_planning.md"
    md.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(L[8:]))


if __name__ == "__main__":
    main()
