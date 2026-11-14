"""WP1.1-1.2 (D-113; post hoc, descriptive; zero calls): prevalence-independent rates of every rule, false alarms per
kept PF test at stated prevalences, the invalid-as-keep sensitivity, Sonnet E9 vs E9b on rates, and the common-scale
trade-off figure (x = PF-loss rate, y = TF-removal rate).

    python scripts/analysis/revision_rates.py  -> results/revision/wp11_rates.json, paper/figures/fig_tradeoff_rates.pdf
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import revision_common as rc  # noqa: E402
from triage import config, stats  # noqa: E402
from triage import revision_metrics as rm  # noqa: E402
from triage.io_utils import dump_json  # noqa: E402

OUT = rc.OUT / "wp11_rates.json"
FIG = rc.ROOT / "paper" / "figures" / "fig_tradeoff_rates"
ORDER = ["KA", "DA", "R0", "J1|S1", "SC|S1", "SC-T|S1", "DEB|S1", "TAU|S1", "VOTE3|S1", "MAJ3|S1", "KUU|S1",
         "P_M1_E6B|S1", "P_M1_M2|S1", "P_M2_E6B|S1", "KUUNG|S1", "CAS|S1", "J1|S1|SON", "DEB|S1|SON"]
PREVS = (0.05, 0.02)


def summarise(D, T, W):
    pt = rm.rates_point(T)
    bs = rm.rates_bootstrap(T, W)
    out = {k: pt[k] for k in pt}
    for k in ("tpr", "tnr", "ba", "pf_loss_rate"):
        out[f"{k}_ci95"] = rc.ci(bs[k])
    for m in ("f1", "mcc"):
        out[m] = stats.point_estimate(T, m)
        out[f"{m}_ci95"] = rc.ci(stats.bootstrap_metric(T, m, W))
    tot = T.sum(axis=0).mean(axis=0)
    out.update(TP=float(tot[0]), FP=float(tot[1]), FN=float(tot[2]), TN=float(tot[3]), replicates=int(T.shape[1]))
    prevs = list(PREVS) + ([D.pop_prev] if D.ds == "D1" else [])
    out["at_prevalence"] = {}
    for p in prevs:
        fa = rm.false_alarms_per_kept_pf(pt["tpr"], pt["tnr"], p)
        fa_s = (1 - p) * (1 - bs["tnr"]) / (p * bs["tpr"])
        out["at_prevalence"][f"{p:.4f}"] = {"pi": p, "precision": rm.precision_at_prevalence(pt["tpr"], pt["tnr"], p),
                                            "false_alarms_per_kept_pf": fa, "false_alarms_ci95": rc.ci(fa_s)}
    return out


def run(ds):
    D = rc.build(ds)
    D.pop_prev, D.pop_n = rc.population_prevalence(D)
    bugs, W = D.weights_W()
    rules = {}
    for c in ORDER:
        if c in D.preds:
            rules[c] = {"name": rc.NAMES[c], **summarise(D, D.tensor(c), W)}
    sens = {}
    for c in ("J1|S1", "SC|S1", "SC-T|S1", "DEB|S1"):
        if c in D.preds:
            n_inv = sum(v == rc.INV for r in D.preds[c].values() for v in r.values())
            a, b = summarise(D, D.tensor(c), W), summarise(D, D.tensor(c, policy="as_PF"), W)
            sens[c] = {"invalid_decisions": n_inv, "primary_invalid_as_TF": {k: a[k] for k in ("tpr", "tnr", "ba", "f1", "mcc")},
                       "invalid_as_keep": {k: b[k] for k in ("tpr", "tnr", "ba", "f1", "mcc")}}
    n_pf = sum(1 for i in D.ids if D.lab[i] == rc.PF)
    return D, W, {"dataset": ds, "n_instances": len(D.ids), "n_pf": n_pf, "n_tf": len(D.ids) - n_pf, "n_bugs": len(bugs),
                  "sample_pf_prevalence": n_pf / len(D.ids),
                  "population_pf_prevalence": D.pop_prev if ds == "D1" else None, "population_n": D.pop_n,
                  "population_note": ("D1-test labelled failures (PF/(PF+TF), AMB excluded)" if ds == "D1" else
                                      "the D2 mutant population is not a deployment population; no natural prevalence"),
                  "rules": rules, "invalid_sensitivity": sens}


def e9_vs_e9b(res, built):
    out = {}
    (D1, W1), (D2, _) = built["D1"], built["D2"]
    _, W2 = D2.weights_W(seed=config.SEED_BOOTSTRAP + 1)       # independent resamples for the unpaired difference
    for c in ("J1|S1|SON", "DEB|S1|SON"):
        b1, b2 = rm.rates_bootstrap(D1.tensor(c), W1), rm.rates_bootstrap(D2.tensor(c), W2)
        row = {}
        for k in ("tpr", "tnr", "ba"):
            d = res["D1"]["rules"][c][k] - res["D2"]["rules"][c][k]
            row[k] = {"D1": res["D1"]["rules"][c][k], "D2": res["D2"]["rules"][c][k], "d1_minus_d2": d,
                      "d1_minus_d2_ci95": rc.ci(b1[k] - b2[k])}
        out[c] = row
    out["note"] = ("unpaired dataset contrast (different instances, fault process and prevalence), not a method effect; "
                   "D2 resampled with the committed seed + 1")
    return out


def reviewer_figures(res):
    k = json.loads((rc.ROOT / "results" / "kuung" / "analysis" / "kuung.json").read_text(encoding="utf-8"))
    r2 = res["D2"]["rules"]
    return {
        "kuung_share_discarded_D2": r2["KUUNG|S1"]["share_discarded"],
        "kuu_share_discarded_D2": r2["KUU|S1"]["share_discarded"],
        "cascade_share_discarded_D2": r2["CAS|S1"]["share_discarded"],
        "kuung_share_discarded_D1": res["D1"]["rules"]["KUUNG|S1"]["share_discarded"],
        "kuu_share_discarded_D1": res["D1"]["rules"]["KUU|S1"]["share_discarded"],
        "kuung_minus_ka_f1_D2": k["D2"]["hypotheses"]["H13-1"]["delta"],
        "kuu_precision_at_005_D2": r2["KUU|S1"]["at_prevalence"]["0.0500"]["precision"],
        "kuu_false_alarms_per_kept_pf_at_005_D2": r2["KUU|S1"]["at_prevalence"]["0.0500"]["false_alarms_per_kept_pf"],
        "kuung_false_alarms_per_kept_pf_at_005_D2": r2["KUUNG|S1"]["at_prevalence"]["0.0500"]["false_alarms_per_kept_pf"],
        "note": ("share discarded = (FN+TN)/N on D-110's common set; the reviewer's '7-13%' is KUU-NG to KUU on D2 (the "
                 "cascade discards more); +0.029 is H13-1 (KUU-NG - keep-all F1, D2); the 0.065 precision is D-106's "
                 "KUU precision at an assumed 5% PF prevalence, recomputed here from TPR and TNR"),
    }


def plot(res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    show = {"KA": "Keep all", "DA": "Discard all", "R0": "Rule R0", "J1|S1": "One judge", "SC|S1": "Voting (SC)",
            "DEB|S1": "Debate", "TAU|S1": "Debate, conf. 100*", "MAJ3|S1": "2-of-3 vote", "KUU|S1": "KUU",
            "KUUNG|S1": "KUU-NG", "CAS|S1": "Cascade", "J1|S1|SON": "Sonnet J1", "DEB|S1|SON": "Sonnet debate",
            "P_M1_E6B|S1": "pair w/o Gemma"}
    off = {"D1": {"KA": (5, 4), "DA": (-5, -6), "R0": (5, -2), "J1|S1": (5, -4), "SC|S1": (5, -6), "DEB|S1": (-5, -7),
                  "TAU|S1": (5, -1), "MAJ3|S1": (5, 1), "KUU|S1": (5, 3), "KUUNG|S1": (5, -5), "CAS|S1": (5, 1),
                  "J1|S1|SON": (5, -1), "DEB|S1|SON": (0, 8), "P_M1_E6B|S1": (5, 0)},
           "D2": {"KA": (5, 4), "DA": (-5, -6), "R0": (5, -2), "J1|S1": (5, 3), "SC|S1": (5, -6), "DEB|S1": (5, 2),
                  "TAU|S1": (6, 6), "MAJ3|S1": (5, -3), "KUU|S1": (6, -5), "KUUNG|S1": (5, -6), "CAS|S1": (5, 2),
                  "J1|S1|SON": (5, -2), "DEB|S1|SON": (5, 2), "P_M1_E6B|S1": (5, 0)}}
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.5), sharey=True)
    for ax, ds in zip(axes, ("D1", "D2")):
        for c, p in res[ds]["rules"].items():
            if c not in show:
                continue
            x, y = p["pf_loss_rate"], p["tnr"]
            ours = c in ("KUU|S1", "KUUNG|S1", "CAS|S1")
            col = "#0B8A7D" if ours else ("#C2413B" if c in ("J1|S1", "SC|S1", "DEB|S1", "TAU|S1") else "#5F6B7A")
            mk = "D" if ours else ("s" if "SON" in c else "o")
            ax.scatter(x, y, s=30, marker=mk, facecolors="none" if c == "TAU|S1" else col, edgecolors=col,
                       linewidths=1.2, zorder=3)
            dx, dy = off[ds].get(c, (5, 0))
            ax.annotate(show[c], (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=6.2, color=col,
                        ha="center" if dx == 0 else ("left" if dx > 0 else "right"), va="center")
        tp = thinking_point(ds)                   # D-130: the thinking judge, if its runs exist
        if tp is not None:
            ax.scatter(tp[0], tp[1], s=70, marker="*", color="#7B3FA0", zorder=4)
            ax.annotate("M1 thinking", tp, xytext=(6, -7), textcoords="offset points", fontsize=6.2,
                        color="#7B3FA0", ha="left", va="center")
        ax.plot([0, 1], [0, 1], ls=":", lw=0.8, color="#9AA3AD", zorder=1)
        ax.set_xlim(-0.03, 1.03)
        ax.set_ylim(-0.03, 1.03)
        ax.set_title(f"{ds} ({'real faults' if ds == 'D1' else 'seeded faults'})", fontsize=9)
        ax.set_xlabel("PF-loss rate = 1 − TPR", fontsize=8)
        ax.grid(alpha=0.25)
        ax.tick_params(labelsize=7)
        ax.set_aspect("equal")
    axes[0].set_ylabel("TF-removal rate = TNR", fontsize=8)
    fig.text(0.5, -0.07, "Same axes for both datasets; neither rate depends on the PF:TF mix. Top-left is ideal; the dotted "
             "diagonal is a coin that discards at random.\nDiamonds: this study's rules; squares: Claude Sonnet 5.5; "
             "hollow: threshold tuned on the development split"
             + ("; star: M1 with thinking enabled (D1: mean of its runs; D2: one run)." if thinking_point("D1") else "."),
             ha="center", fontsize=6.4)
    fig.tight_layout()
    fig.savefig(FIG.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(FIG.with_suffix(".png"), dpi=220, bbox_inches="tight")


def thinking_point(ds):
    """(PF-loss rate, TNR) of thinking-enabled M1 J1 from results/revision/think_followup.json (D-130): D1 the mean of
    its runs, D2 its confirmation run; None if not available. Presentation only."""
    f = rc.OUT / "think_followup.json"
    if not f.exists():
        return None
    r = json.loads(f.read_text(encoding="utf-8"))
    if ds == "D1":
        s = r["d1"].get("summary") or {}
        return (1 - s["tpr"]["mean"], s["tnr"]["mean"]) if "tpr" in s else None
    d = (r["d2"].get("descriptive") or {}).get("Thinking M1 J1")
    return (d["pf_loss_rate"], d["tnr"]) if d else None


def main():
    built, res = {}, {"what": "prevalence-independent rates (D-113, post hoc, descriptive)", "decisions": ["D-112", "D-113"],
                      "convention": "PF positive; TPR = TP/(TP+FN) PF-retention; TNR = TN/(TN+FP) TF-removal; "
                                    "BA = (TPR+TNR)/2; F1 depends on prevalence, MCC on sample composition"}
    for ds in ("D1", "D2"):
        D, W, r = run(ds)
        built[ds] = (D, W)
        res[ds] = r
    res["sonnet_e9_vs_e9b"] = e9_vs_e9b(res, built)
    res["reviewer_figures"] = reviewer_figures(res)
    dump_json(OUT, res)
    plot(res)
    for ds in ("D1", "D2"):
        print(ds, res[ds]["n_instances"], "PF", res[ds]["n_pf"])
        for c, p in res[ds]["rules"].items():
            print(f"  {p['name']:32s} TPR {p['tpr']:.3f} TNR {p['tnr']:.3f} BA {p['ba']:.3f} F1 {p['f1']:.3f} "
                  f"MCC {p['mcc']:.3f} FA@5% {p['at_prevalence']['0.0500']['false_alarms_per_kept_pf']:.1f}")
    print(json.dumps(res["reviewer_figures"], indent=1))
    print(json.dumps(res["sonnet_e9_vs_e9b"], indent=1)[:1500])


if __name__ == "__main__":
    main()
