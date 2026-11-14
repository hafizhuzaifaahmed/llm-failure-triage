"""Confirmatory analysis of CFP on a sealed tranche (D-138; the preregistered family C1 to C4 and its secondaries).

    python scripts/extension/confirm_analysis.py --run CFP_CONFIRM --instances <instances.jsonl> --labels <labels.jsonl>
        --frame configs/extension/confirm_frame.jsonl --votes M1=<run dir> M2=<run dir> M3=<run dir> --replicate 0

Primary family (one Holm family, alpha 0.05, two-sided bug-level bootstrap p), on tranches F1 and F2:
  C1  P(flip | PF) - P(flip | TF) > 0
  C2  P(decoupled | TF) - P(decoupled | PF) > 0
  C3  balanced accuracy of KUU + CD minus KUU > 0
  C4  PF tests lost by 2-of-3 + CK minus 2-of-3 < 0
Reported beside the family, not tested: bugs lost per rule with an exact binomial 95% upper bound; the secondary
analyses; the control group (tranche CTRL). Labels are read here and nowhere earlier. Frozen by cfp_frozen.json.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config, stats  # noqa: E402
from triage import revision_metrics as rm  # noqa: E402
from triage.io_utils import read_jsonl  # noqa: E402
from triage_ext import ledger as lg  # noqa: E402
from triage_ext import policy  # noqa: E402

PF, TF = policy.PF, policy.TF
CLEAN_OPS = {"LVR", "ROR", "STD"}           # secondary analysis 3: the pilot's cleanest operator families
ALPHA = 0.05


def ci(x):
    lo, hi = stats.percentile_ci(np.asarray(x, dtype=float), 0.95)
    return [round(lo, 4), round(hi, 4)]


def wrate(w, mask, flag):
    den = (w * mask).sum(-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, (w * mask * flag).sum(-1) / den, np.nan)


def rate_contrast(y, flag, W, sign=+1):
    """sign=+1: rate among PF minus rate among TF; sign=-1: the reverse. Point, CI, bootstrap p."""
    one = np.ones((1, len(y)))
    pf, tf = (y == 1).astype(float), (y == 0).astype(float)
    point = float((wrate(one, pf, flag) - wrate(one, tf, flag))[0]) * sign
    d = (wrate(W, pf, flag) - wrate(W, tf, flag)) * sign
    d = d[~np.isnan(d)]
    return {"PF_flagged": int((flag * pf).sum()), "PF": int(pf.sum()), "TF_flagged": int((flag * tf).sum()),
            "TF": int(tf.sum()), "difference": round(point, 4), "ci95": ci(d),
            "p": float(stats.bootstrap_p_two_sided(d))}


def rule_metrics(w, y, keep):
    w = np.atleast_2d(w)
    pf, tf = (y == 1), (y == 0)
    tpr = (w * pf * keep).sum(-1) / np.maximum((w * pf).sum(-1), 1e-12)
    tnr = (w * tf * (1 - keep)).sum(-1) / np.maximum((w * tf).sum(-1), 1e-12)
    return {"TPR": tpr, "TNR": tnr, "BA": (tpr + tnr) / 2, "PF_lost": (w * pf * (1 - keep)).sum(-1)}


def bugs_lost(y, keep, bidx, n_bugs):
    has, kept = np.zeros(n_bugs), np.zeros(n_bugs)
    np.add.at(has, bidx, (y == 1).astype(float))
    np.add.at(kept, bidx, ((y == 1) * keep).astype(float))
    n, k = int((has > 0).sum()), int(((has > 0) & (kept == 0)).sum())
    upper = float(sps.beta.ppf(0.95, k + 1, n - k)) if n > k else 1.0      # exact one-sided 95% (Clopper-Pearson)
    return {"bugs_with_PF": n, "bugs_lost": k, "upper95_bug_loss_rate": round(upper, 4) if n else None}


def guarded(summary, inst):
    """Secondary 2: decoupling certificate, never applied to an exception raised inside the method under test."""
    cov = inst.get("covariates", {})
    return bool(summary.get("decoupled")) and not (cov.get("failure_type") == "exception" and cov.get("deepest_frame") == "focal")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--instances", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--frame", default=None)
    ap.add_argument("--split", default=None, help="restrict instances to one split (dry run on pilot data only)")
    ap.add_argument("--votes", nargs="*", default=[], help="M1=<run dir> M2=<run dir> M3=<run dir>")
    ap.add_argument("--replicate", type=int, default=0)
    ap.add_argument("--seed", type=int, default=config.SEED_BOOTSTRAP)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    led = {r["instance_id"]: r for r in read_jsonl(ROOT / "results" / "extension" / "probes" / a.run / "ledger.jsonl")}
    inst = {r["instance_id"]: r for r in read_jsonl(Path(a.instances)) if a.split is None or r.get("split") == a.split}
    lab = {l["instance_id"]: l for l in read_jsonl(Path(a.labels)) if l["instance_id"] in inst}
    tranche = {r["focal_id"]: r["tranche"] for r in read_jsonl(Path(a.frame))} if a.frame else {}
    out = {"decision": "D-138", "run": a.run, "seed": a.seed, "resamples": config.BOOTSTRAP_RESAMPLES,
           "status": "DRY RUN ON PILOT DATA: software check only, not a result" if a.dry_run else "confirmatory"}

    def population(tranches):
        ids = [i for i, l in lab.items() if l["label"] in ("PF", "TF") and i in led
               and (not tranche or tranche.get(inst[i]["focal_id"]) in tranches)]
        return ids

    ids = population({"F1", "F2"})
    y = np.array([1 if lab[i]["label"] == "PF" else 0 for i in ids])
    bugs = sorted({lab[i]["bug_name"] for i in ids})
    bidx = np.array([bugs.index(lab[i]["bug_name"]) for i in ids])
    Wb = stats.bootstrap_weights(len(bugs), seed=a.seed)
    W = Wb[:, bidx]
    S = [led[i]["summary"] for i in ids]
    usable = np.array([0.0 if s.get("excluded") else 1.0 for s in S])

    def flag(name, key="summary"):
        """1.0 where the instance has a usable ledger and the named flag is set in the chosen summary."""
        return np.array([1.0 if (not led[i]["summary"].get("excluded") and (led[i].get(key) or {}).get(name)) else 0.0
                         for i in ids])

    out["population"] = {"instances": len(ids), "PF": int(y.sum()), "TF": int((1 - y).sum()), "bugs": len(bugs),
                         "bugs_with_PF": len({b for b, yy in zip(bidx, y) if yy}),
                         "excluded_by_engine": int((1 - usable).sum())}
    fam = {"C1": rate_contrast(y, flag("flip"), W, +1), "C2": rate_contrast(y, flag("decoupled"), W, -1)}

    # ---- rules that need judge votes -------------------------------------------------------------------------
    votes = {}
    for spec in a.votes:
        name, d = spec.split("=", 1)
        for r in read_jsonl(Path(d) / "decisions.jsonl"):
            if r["arm"] == "J1" and r.get("level") == "S1" and (r.get("variant") or "full") == "full" and r["replicate"] == a.replicate:
                votes.setdefault(r["instance_id"], {})[name] = r["label_raw"]
    if votes:
        vsel = np.array([len(votes.get(i, {})) == 3 for i in ids])
        vid = [i for i, s in zip(ids, vsel) if s]
        vy, vb, vW = y[vsel], bidx[vsel], W[:, vsel]
        vs = [led[i]["summary"] for i in vid]

        def keepvec(base, rule=None):
            labs = [base(i) for i in vid]
            if rule:
                labs = [policy.RULES[rule](l, s) for l, s in zip(labs, vs)]
            return np.array([1.0 if l == PF else 0.0 for l in labs])

        def kuu(i):
            return rm.k_of_n([votes[i].get(m) for m in ("M1", "M2", "M3")], 3)

        def maj(i):
            return rm.k_of_n([votes[i].get(m) for m in ("M1", "M2", "M3")], 2)

        k0, k1 = keepvec(kuu), keepvec(kuu, "CD")
        m0, m1 = keepvec(maj), keepvec(maj, "CK")
        one = np.ones(len(vid))
        d3 = rule_metrics(vW, vy, k1)["BA"] - rule_metrics(vW, vy, k0)["BA"]
        d4 = rule_metrics(vW, vy, m1)["PF_lost"] - rule_metrics(vW, vy, m0)["PF_lost"]
        fam["C3"] = {"difference": round(float(rule_metrics(one, vy, k1)["BA"][0] - rule_metrics(one, vy, k0)["BA"][0]), 4),
                     "ci95": ci(d3), "p": float(stats.bootstrap_p_two_sided(d3))}
        fam["C4"] = {"difference": round(float(rule_metrics(one, vy, m1)["PF_lost"][0] - rule_metrics(one, vy, m0)["PF_lost"][0]), 4),
                     "ci95": ci(d4), "p": float(stats.bootstrap_p_two_sided(d4))}
        out["rules"] = {"instances_with_three_votes": len(vid), "PF": int(vy.sum())}
        for name, k in (("KUU", k0), ("KUU+CD", k1), ("2-of-3", m0), ("2-of-3+CK", m1),
                        ("KUU+CK+CD", keepvec(kuu, "CK+CD")), ("2-of-3+CK+CD", keepvec(maj, "CK+CD")),
                        ("keep-all+CD", keepvec(lambda i: PF, "CD"))):
            m = rule_metrics(one, vy, k)
            out["rules"][name] = {**{q: round(float(v[0]), 4) for q, v in m.items()}, **bugs_lost(vy, k, vb, len(bugs))}

    names = sorted(fam)
    adj = stats.holm([fam[n]["p"] for n in names])
    expect = {"C1": +1, "C2": +1, "C3": +1, "C4": -1}
    for n, p_adj in zip(names, adj):
        fam[n]["p_holm"] = float(p_adj)
        fam[n]["supported"] = bool(p_adj < ALPHA and np.sign(fam[n]["difference"]) == expect[n])
    out["family"] = fam
    if len(names) < 4:
        out["family_note"] = "C3 and C4 need three judge votes per instance; not computed without --votes"

    # ---- secondary analyses (outside the family) --------------------------------------------------------------
    sec = {"rcf_in_place_of_flip": rate_contrast(y, flag("rcf"), W, +1),
           "guarded_decoupling": rate_contrast(y, np.array([1.0 if (u and guarded(s, inst[i])) else 0.0
                                                              for i, s, u in zip(ids, S, usable)]), W, -1),
           "clean_operator_flip": rate_contrast(y, np.array([1.0 if any(m["class"] == lg.FLIP and m["operator"] in CLEAN_OPS
                                                                           for m in led[i]["mutants"]) else 0.0 for i in ids]), W, +1),
           "focal_body_only_flip": rate_contrast(y, flag("flip", "summary_focal_only"), W, +1)}
    flipped_by = defaultdict(set)
    for i in ids:
        for m in led[i]["mutants"]:
            if m["class"] == lg.FLIP:
                flipped_by[(led[i]["focal_id"], m["mid"])].add(i)
    shared = np.array([1.0 if any(len(flipped_by[(led[i]["focal_id"], m["mid"])]) >= 2
                                  for m in led[i]["mutants"] if m["class"] == lg.FLIP) else 0.0 for i in ids])
    sec["shared_flip"] = rate_contrast(y, shared, W, +1)
    lopo = {}
    projects = sorted({lab[i]["project"] for i in ids})
    for p in projects:
        keep = np.array([lab[i]["project"] != p for i in ids])
        if y[keep].sum() and (1 - y[keep]).sum():
            fl, de = flag("flip")[keep], flag("decoupled")[keep]
            lopo[p] = {"C1": round(float(fl[y[keep] == 1].mean() - fl[y[keep] == 0].mean()), 4),
                       "C2": round(float(de[y[keep] == 0].mean() - de[y[keep] == 1].mean()), 4)}
    sec["leave_one_project_out"] = lopo
    out["secondary"] = sec

    # ---- control group ----------------------------------------------------------------------------------------
    cids = population({"CTRL"}) if tranche else []
    if cids:
        cl = np.array([1 if lab[i]["label"] == "PF" else 0 for i in cids])
        cf = np.array([1.0 if led[i]["summary"].get("flip") else 0.0 for i in cids])
        cd = np.array([1.0 if led[i]["summary"].get("decoupled") else 0.0 for i in cids])
        tf_focal = flag("flip")[y == 0]
        cb = sorted({lab[i]["bug_name"] for i in cids})
        cW = stats.bootstrap_weights(len(cb), seed=a.seed)[:, np.array([cb.index(lab[i]["bug_name"]) for i in cids])]
        ctf = (cl == 0).astype(float)
        out["control"] = {"instances": len(cids), "TF": int(ctf.sum()), "PF": int(cl.sum()), "bugs": len(cb),
                          "flip_rate_TF": round(float(cf[cl == 0].mean()), 4) if ctf.sum() else None,
                          "flip_rate_TF_ci95": ci(wrate(cW, ctf, cf)) if ctf.sum() else None,
                          "decoupled_rate_TF": round(float(cd[cl == 0].mean()), 4) if ctf.sum() else None,
                          "flip_rate_TF_in_F1F2": round(float(tf_focal.mean()), 4) if len(tf_focal) else None,
                          "flip_rate_PF_in_F1F2": round(float(flag("flip")[y == 1].mean()), 4) if y.sum() else None,
                          "note": "PF among controls are tests that reveal the bug through a method the fix did not change"}
    else:
        out["control"] = None

    dest = Path(a.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("status", "population")}, indent=1))
    print("family:", {n: (fam[n]["difference"], fam[n]["supported"]) for n in names})


if __name__ == "__main__":
    main()
