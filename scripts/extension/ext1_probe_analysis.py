"""EXT-1 (D-134): analysis of a counterfactual-probe ledger. Labels join here and nowhere earlier.

    python scripts/extension/ext1_probe_analysis.py --run CFP_D1_DEV --split dev
    python scripts/extension/ext1_probe_analysis.py --run CFP_D1_TEST --split test --policies

Reports, by execution label: exclusions, the rates of every probe flag, HP-1 (regression-consistent flip) and HP-2
(decoupling) with bug-level cluster-bootstrap 95% CIs, AUROCs, and (with --policies, D-110's common D1-test set) the
certificate rules beside their base rules. Zero model calls; nothing is tuned.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

from triage import config  # noqa: E402
from triage.io_utils import read_jsonl  # noqa: E402
from triage_ext import ledger as lg  # noqa: E402
from triage_ext import policy  # noqa: E402

B = 10_000
FLAGS = ("flip", "rcf", "flip_without_rcf", "coupled", "decoupled")


def boot_weights(n_bugs, seed=config.SEED_BOOTSTRAP):
    rng = np.random.default_rng(seed)
    return rng.multinomial(n_bugs, np.full(n_bugs, 1.0 / n_bugs), size=B).astype(float)


def ci(x):
    x = x[~np.isnan(x)]
    return [round(float(np.percentile(x, 2.5)), 3), round(float(np.percentile(x, 97.5)), 3)] if len(x) else None


def rate(w, mask, flag):
    den = (w * mask).sum(-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, (w * mask * flag).sum(-1) / den, np.nan)


def auroc(score, y):
    pos, neg = score[y == 1], score[y == 0]
    if not len(pos) or not len(neg):
        return None
    gt = (pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()
    return round(float(gt / (len(pos) * len(neg))), 3)


def metrics(w, y, keep, bug_idx, n_bugs):
    """TPR, TNR, BA, PF tests lost, bugs lost for instance weights w (1-D point or 2-D bootstrap)."""
    w = np.atleast_2d(w)
    pf, tf = (y == 1), (y == 0)
    tpr = (w * pf * keep).sum(-1) / np.maximum((w * pf).sum(-1), 1e-12)
    tnr = (w * tf * (1 - keep)).sum(-1) / np.maximum((w * tf).sum(-1), 1e-12)
    lost = (w * pf * (1 - keep)).sum(-1)
    has_pf = np.zeros(n_bugs)
    kept = np.zeros(n_bugs)
    np.add.at(has_pf, bug_idx, pf.astype(float))
    np.add.at(kept, bug_idx, (pf * keep).astype(float))
    bug_lost_ind = ((has_pf > 0) & (kept == 0)).astype(float)
    return {"TPR": tpr, "TNR": tnr, "BA": (tpr + tnr) / 2, "PF_lost": lost, "bug_lost_ind": bug_lost_ind}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--split", required=True, choices=["dev", "test"])
    ap.add_argument("--policies", action="store_true")
    a = ap.parse_args()
    led = {r["instance_id"]: r for r in read_jsonl(ROOT / "results" / "extension" / "probes" / a.run / "ledger.jsonl")}
    labels = {l["instance_id"]: l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl") if l["split"] == a.split}
    missing = sorted(set(labels) - set(led))
    out = {"decision": "D-134", "run": a.run, "split": a.split, "instances_labelled": len(labels),
           "instances_without_ledger": len(missing), "status": "exploratory; zero model calls"}

    # ---- exclusions and mutant counts, by label ----------------------------------------------------------------
    by = {}
    for i, l in labels.items():
        r = led.get(i)
        if r is None:
            continue
        s = r["summary"]
        key = s.get("excluded") or ("too_few_mutants" if s["n_compiled"] < lg.MIN_MUTANTS else "usable_10plus")
        by.setdefault(l["label"], {}).setdefault(key, 0)
        by[l["label"]][key] += 1
    out["by_label_status"] = by

    ids = [i for i, l in labels.items() if l["label"] in ("PF", "TF") and i in led and not led[i]["summary"].get("excluded")]
    y = np.array([1 if labels[i]["label"] == "PF" else 0 for i in ids])
    bugs = sorted({labels[i]["bug_name"] for i in ids})
    bidx = np.array([bugs.index(labels[i]["bug_name"]) for i in ids])
    W = boot_weights(len(bugs))[:, bidx]
    one = np.ones(len(ids))
    out["scored"] = {"instances": len(ids), "PF": int(y.sum()), "TF": int((1 - y).sum()), "bugs": len(bugs),
                     "bugs_with_PF": len({b for b, yy in zip(bidx, y) if yy})}
    S = {i: led[i]["summary"] for i in ids}
    out["n_compiled_quartiles"] = [int(q) for q in np.percentile([S[i]["n_compiled"] for i in ids], [0, 25, 50, 75, 100])]

    # ---- flag rates by label, with HP-1 and HP-2 ---------------------------------------------------------------
    out["flags"] = {}
    for f in FLAGS:
        v = np.array([1.0 if S[i][f] else 0.0 for i in ids])
        p_pf, p_tf = float(v[y == 1].mean()) if y.sum() else None, float(v[y == 0].mean())
        d = rate(W, y == 1, v) - rate(W, y == 0, v)
        n_flag = int(v.sum())
        out["flags"][f] = {"n_flagged": n_flag, "PF_flagged": int(v[y == 1].sum()), "TF_flagged": int(v[y == 0].sum()),
                           "rate_PF": None if p_pf is None else round(p_pf, 3), "rate_TF": round(p_tf, 3),
                           "diff_PF_minus_TF": None if p_pf is None else round(p_pf - p_tf, 3), "diff_ci95": ci(d),
                           "LR": None if (p_pf is None or p_tf == 0) else round(p_pf / p_tf, 2),
                           "PF_share_among_flagged": round(float(y[v == 1].mean()), 3) if n_flag else None,
                           "PF_share_overall": round(float(y.mean()), 3)}
    out["HP1_rcf_supported"] = bool(out["flags"]["rcf"]["diff_ci95"] and out["flags"]["rcf"]["diff_ci95"][0] > 0)
    dec = out["flags"]["decoupled"]
    out["HP2_decoupled_supported"] = bool(dec["diff_ci95"] and dec["diff_ci95"][1] < 0)
    for name, key in (("flip_fraction", "flip_fraction"), ("coupled_fraction", "coupled_fraction")):
        sel = np.array([S[i][key] is not None for i in ids])
        out[f"auroc_{name}"] = auroc(np.array([S[i][key] for i in np.array(ids)[sel]], dtype=float), y[sel]) if sel.any() else None
    amb = [i for i, l in labels.items() if l["label"] == "AMB" and i in led and not led[i]["summary"].get("excluded")]
    out["AMB"] = {f: int(sum(1 for i in amb if led[i]["summary"][f])) for f in FLAGS} | {"n": len(amb)}

    # ---- certificate rules beside their base rules (logged votes; D-110 common set) -----------------------------
    if a.policies:
        import revision_common as rc
        d = rc.build("D1")
        think = {x["instance_id"]: x["label_raw"] for x in
                 read_jsonl(ROOT / "results" / "revision" / "runs" / "REV_THINK_M1" / "decisions.jsonl")
                 if x["arm"] == "J1" and rc.s1(x)}
        cids = list(d.ids)
        cy = np.array([1 if d.lab[i] == rc.PF else 0 for i in cids])
        cbugs = sorted({d.bug[i] for i in cids})
        cb = np.array([cbugs.index(d.bug[i]) for i in cids])
        Wb = boot_weights(len(cbugs))
        Wc = Wb[:, cb]
        summ = [led[i]["summary"] if i in led else None for i in cids]
        bases = {"KA": [{i: rc.PF for i in cids}], "KUU": [d.preds["KUU|S1"][0]], "KUU-NG": [d.preds["KUUNG|S1"][0]],
                 "M1 DEB": [d.preds["DEB|S1"][r] for r in sorted(d.preds["DEB|S1"])],
                 "2-of-3": [d.preds["MAJ3|S1"][0]], "M1 thinking J1": [think],
                 "Sonnet DEB": [d.preds["DEB|S1|SON"][r] for r in sorted(d.preds["DEB|S1|SON"])]}
        plan = {"KA": ["CD"], "KUU": ["CD", "CK+CD"], "KUU-NG": ["CD", "CK+CD"], "M1 DEB": ["CK", "CK+CD"],
                "2-of-3": ["CK", "CK+CD"], "M1 thinking J1": ["CK", "CK+CD"], "Sonnet DEB": ["CK", "CK+CD"]}

        def keep_vec(pred, rule=None):
            lab = [rc.PF if pred.get(i) == rc.PF else rc.TF for i in cids]          # invalid or missing scores TF
            if rule:
                lab = [policy.RULES[rule](l, s) for l, s in zip(lab, summ)]
            return np.array([1.0 if l == rc.PF else 0.0 for l in lab])

        def evaluate(reps, rule=None):
            pts, boots = [], []
            for pred in reps:
                k = keep_vec(pred, rule)
                p = metrics(np.ones(len(cids)), cy, k, cb, len(cbugs))
                b = metrics(Wc, cy, k, cb, len(cbugs))
                p["bugs_lost"] = np.array([p["bug_lost_ind"].sum()])
                b["bugs_lost"] = Wb @ b["bug_lost_ind"]
                pts.append(p)
                boots.append(b)
            keys = ("TPR", "TNR", "BA", "PF_lost", "bugs_lost")
            return ({k: float(np.mean([p[k][0] for p in pts])) for k in keys},
                    {k: np.mean([b[k] for b in boots], axis=0) for k in keys})

        res = {}
        for base, rules in plan.items():
            bp, bb = evaluate(bases[base])
            res[base] = {"base": {k: round(v, 3) for k, v in bp.items()}}
            for rule in rules:
                rp, rb = evaluate(bases[base], rule)
                res[base][rule] = {**{k: round(v, 3) for k, v in rp.items()},
                                   "delta_vs_base": {k: round(rp[k] - bp[k], 3) for k in rp},
                                   "delta_ci95": {k: ci(rb[k] - bb[k]) for k in rp}}
        out["policies"] = {"set": "D-110 common D1-test", "instances": len(cids), "PF": int(cy.sum()),
                           "with_usable_ledger": int(sum(1 for s in summ if s and not s.get("excluded"))),
                           "rules": res}

    dest = ROOT / "results" / "extension" / f"ext1_probe_analysis_{a.run}.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "policies"}, indent=1))
    if a.policies:
        for base, r in out["policies"]["rules"].items():
            print(base, r["base"])
            for rule, v in r.items():
                if rule != "base":
                    print("   +", rule, {k: v[k] for k in ("TPR", "TNR", "BA", "PF_lost", "bugs_lost")}, "dBA", v["delta_vs_base"]["BA"], v["delta_ci95"]["BA"])


if __name__ == "__main__":
    main()
