"""Discard–loss trade-off of every triage rule (D-110; post hoc, descriptive). Zero model calls.

For D1-test and D2, each rule is placed by the share of failures it discards (x) and the share of bug-revealing tests
it loses (y), on one common instance set per dataset (scored, PF or TF, not leakage-aborted in any contributing run).
Rules: keep-all, discard-all, M1 J1 / SC / DEB, M1 DEB discarding only at stated confidence 100 (the D-82 selective
rule, tau tuned on the development split: the only tuned point), KUU, its three judge pairs (D-107), KUU-NG (D-109),
the cascade (D-105), and Sonnet J1 / DEB (E9, E9b). Replicated rules are averaged over replicates. Beside each point:
F1, MCC, local GPU seconds per instance (sum of the logged wall time of the local calls; the cascade's local tier only)
and frontier US$ per instance (logged batch cost), and the share of instances whose evidence leaves the machine.
Descriptive only; no test.

    python scripts/analysis/pareto.py   -> results/pareto/pareto.json, paper/figures/fig_pareto.pdf (+ .png)
"""
import ast
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

from triage import analysis, config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

import kuu_analysis as ka  # noqa: E402

RUNS, FRONT = ROOT / "results" / "runs_local", ROOT / "results" / "runs_frontier"
OUT = ROOT / "results" / "pareto" / "pareto.json"
FIG = ROOT / "paper" / "figures" / "fig_pareto"
TF, PF = "TEST_FAULT", "PROGRAM_FAULT"
PLAN = {
    "D1": {"sample": "sample_D1_test.json", "labels": "labels_D1.jsonl", "m1": "LOCAL_HO_E1E3_M1",
           "kuu": ({"M1": "LOCAL_HO_E8_VOTE_M1", "M2": "LOCAL_HO_E8_VOTE_M2", "E6B": "LOCAL_HO_E8_VOTE_E6B"}, 10),
           "ng": ({"M1": "LOCAL_HO_KUUNG_D1_M1", "E6B": "LOCAL_HO_KUUNG_D1_E6B", "NG": "LOCAL_HO_KUUNG_D1_NG"}, 30),
           "frontier": "E9_SONNET55_D1TEST"},
    "D2": {"sample": "sample_D2_test.json", "labels": "labels_D2.jsonl", "m1": "LOCAL_HO_E5R1_D2",
           "kuu": ({"M1": "LOCAL_HO_KUU_D2_M1", "M2": "LOCAL_HO_KUU_D2_M2", "E6B": "LOCAL_HO_KUU_D2_E6B"}, 20),
           "ng": ({"M1": "LOCAL_HO_KUUNG_D2_M1", "E6B": "LOCAL_HO_KUUNG_D2_E6B", "NG": "LOCAL_HO_KUUNG_D2_NG"}, 30),
           "frontier": "E9B_SONNET55_D2"},
}
LABELS = {"KA": "Keep all", "DA": "Discard all", "J1|S1": "One judge (J1)", "SC|S1": "Repeated voting (SC)",
          "DEB|S1": "Debate (DEB)", "TAU|S1": "Debate, confidence 100*", "KUU|S1": "KUU",
          "P_M1_E6B|S1": "KUU pair M1+E6b", "P_M1_M2|S1": "KUU pair M1+M2", "P_M2_E6B|S1": "KUU pair M2+E6b",
          "KUUNG|S1": "KUU-NG", "CAS|S1": "Cascade", "J1|S1|SON": "Sonnet J1", "DEB|S1|SON": "Sonnet DEB"}
OURS = {"KUU|S1", "KUUNG|S1", "CAS|S1"}
TUNED = {"TAU|S1"}


def _cost(d):
    c = d.get("cost")
    if isinstance(c, str):
        c = ast.literal_eval(c)
    return c or {}


def s1(d):
    return d.get("level") == "S1" and (d.get("variant") or "full") == "full"


def unanimous(vs):
    return TF if vs and all(v == TF for v in vs) else PF


def run(ds):
    plan = PLAN[ds]
    samp = json.loads((config.PROCESSED / plan["sample"]).read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / plan["labels"]) if l["instance_id"] in keep]
    m1 = [d for d in read_jsonl(RUNS / plan["m1"] / "decisions.jsonl")]
    syn, gpu = [], {}

    def add(i, arm, rep, lab, secs=None):
        syn.append({"instance_id": i, "arm": arm, "level": "S1", "variant": "full", "replicate": rep, "label_raw": lab,
                    "agreement": {}})
        if secs is not None:
            gpu.setdefault(f"{arm}|S1", []).append(secs)
    for d in m1:
        if d["arm"] in ("J1", "SC", "DEB") and s1(d):
            gpu.setdefault(f"{d['arm']}|S1", []).append(float(_cost(d).get("latency_s") or 0.0))
        if d["arm"] == "DEB" and s1(d):
            conf = d.get("confidence")
            add(d["instance_id"], "TAU", d["replicate"],
                TF if d["label_raw"] == TF and conf is not None and float(conf) >= 100 else PF,
                float(_cost(d).get("latency_s") or 0.0))
    panels = {}
    for key in ("kuu", "ng"):
        runs, rep = plan[key]
        v, t = {}, {}
        for m, r in runs.items():
            for d in read_jsonl(RUNS / r / "decisions.jsonl"):
                if d["arm"] == "J1" and s1(d) and d["replicate"] == rep:
                    v.setdefault(d["instance_id"], {})[m] = d["label_raw"]
                    t[d["instance_id"]] = t.get(d["instance_id"], 0.0) + float(_cost(d).get("latency_s") or 0.0)
        panels[key] = (v, t)
    kv, kt = panels["kuu"]
    nv, nt = panels["ng"]
    front = [d for d in read_jsonl(FRONT / plan["frontier"] / "decisions.jsonl") if s1(d)]
    son = {}
    for d in front:
        son.setdefault((d["arm"], d["replicate"]), {})[d["instance_id"]] = d
    deb_reps = sorted(r for a, r in son if a == "DEB")
    usd, leaves = {}, {}
    for i in keep:
        v = kv.get(i, {})
        if len(v) == 3:
            vs = [v.get(m) for m in ("M1", "M2", "E6B")]
            add(i, "KUU", 0, unanimous(vs), kt.get(i))
            for name, (a, b) in {"P_M1_E6B": ("M1", "E6B"), "P_M1_M2": ("M1", "M2"), "P_M2_E6B": ("M2", "E6B")}.items():
                add(i, name, 0, unanimous([v.get(a), v.get(b)]))
            esc = not (all(x == TF for x in vs) or all(x == PF for x in vs))
            for k, r in enumerate(deb_reps):
                e = son[("DEB", r)].get(i)
                lab = (vs[0] if not esc else (e["label_raw"] if e and e["label_raw"] in (TF, PF) else PF))
                add(i, "CAS", k, lab, kt.get(i) if k == 0 else None)
                if k == 0:
                    usd.setdefault("CAS|S1", []).append(float(_cost(e).get("cost_usd") or 0.0) if (esc and e) else 0.0)
                    leaves.setdefault("CAS|S1", []).append(1.0 if esc else 0.0)
        n = nv.get(i, {})
        if len(n) == 3:
            add(i, "KUUNG", 0, unanimous([n.get(m) for m in ("M1", "E6B", "NG")]), nt.get(i))
    for (arm, r), dd in son.items():
        for i, d in dd.items():
            syn.append({**d, "variant": "SON"})
            if r == min(x for a, x in son if a == arm):
                usd.setdefault(f"{arm}|S1|SON", []).append(float(_cost(d).get("cost_usd") or 0.0))
                leaves.setdefault(f"{arm}|S1|SON", []).append(1.0)
    base = [d for d in m1 if (d["arm"] in ("J1", "SC", "DEB") and s1(d)) or d["arm"] in ("KA", "DA")]
    aborted = ka.rejections(plan["m1"]).union(*(ka.rejections(r) for r in plan["kuu"][0].values()),
                                              *(ka.rejections(r) for r in plan["ng"][0].values()))
    ev = analysis.Evaluation(syn + base, labels, samp.get("tf_weights"),
                             exclusions={("S1", "full"): aborted, ("S1", "SON"): aborted})
    conds = ["J1|S1", "SC|S1", "DEB|S1", "TAU|S1", "KUU|S1", "P_M1_E6B|S1", "P_M1_M2|S1", "P_M2_E6B|S1", "KUUNG|S1",
             "CAS|S1", "J1|S1|SON", "DEB|S1|SON"]
    conds = [c for c in conds if ev.by_cond.get(c)]
    ids = ev.comparison_set(conds)
    evr = ev._restricted(ids)
    n_pf = sum(1 for i in ids if evr.lab[i] == PF)
    pts = {}
    for c in conds + [b for b in ("KA", "DA") if ev.by_cond.get(b)]:
        T = evr.tensor(c)
        tot = T.sum(axis=0)                                 # per replicate TP, FP, FN, TN
        disc = (tot[:, 2] + tot[:, 3]) / tot.sum(axis=1)
        lost = tot[:, 2]
        s = evr.summary(c) if c not in ("KA", "DA") else evr.baseline_summary(c)
        pts[c] = {"label": LABELS[c], "share_discarded": float(np.mean(disc)), "pf_lost": float(np.mean(lost)),
                  "share_pf_lost": float(np.mean(lost)) / n_pf if n_pf else None, "f1": s.get("f1"), "mcc": s.get("mcc"),
                  "tuned_parameter": c in TUNED, "ours": c in OURS,
                  "local_gpu_s_per_instance": float(np.mean(gpu[c])) if c in gpu else (0.0 if c in ("KA", "DA") else None),
                  "frontier_usd_per_instance": float(np.mean(usd[c])) if c in usd else 0.0,
                  "share_leaving_machine": float(np.mean(leaves[c])) if c in leaves else 0.0}
    return {"dataset": ds, "n_instances": len(ids), "n_pf": n_pf, "points": pts,
            "note": "descriptive, post hoc (D-110); * = parameter tuned on the development split"}


def plot(res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    # Presentation only: label positions are placed by hand so that no two labels overlap. Keep-all is the origin and
    # discard-all sits at (100, 100), off the drawn range; both are stated in the caption line.
    short = {"J1|S1": "One judge", "SC|S1": "Repeated voting", "DEB|S1": "Debate", "CAS|S1": "Cascade",
             "J1|S1|SON": "Sonnet, one judge", "DEB|S1|SON": "Sonnet debate", "KUU|S1": "KUU",
             "KUUNG|S1": "KUU-NG", "TAU|S1": "Debate, conf. 100\n(tuned)", "P_M1_E6B|S1": "pair without\nGemma"}
    main_lab = {  # (dx, dy) in points, horizontal alignment
        "D1": {"J1|S1": (-6, 0, "right"), "SC|S1": (0, 8, "center"), "DEB|S1": (6, -5, "left"),
               "CAS|S1": (-6, 1, "right"), "DEB|S1|SON": (6, -4, "left"), "J1|S1|SON": (6, 0, "left")},
        "D2": {"J1|S1": (6, 2, "left"), "SC|S1": (4, -9, "left"), "DEB|S1": (6, -3, "left"),
               "CAS|S1": (-6, 2, "right"), "DEB|S1|SON": (6, -4, "left"), "J1|S1|SON": (6, 0, "left")}}
    inset_lab = {  # text position in data coordinates of the inset
        "D1": {"KUUNG|S1": (3.0, 5.0), "KUU|S1": (8.0, 8.4), "TAU|S1": (17.5, 5.2), "P_M1_E6B|S1": (13.0, 11.6)},
        "D2": {"KUUNG|S1": (0.5, 5.0), "KUU|S1": (5.0, 8.4), "TAU|S1": (17.0, 6.6), "P_M1_E6B|S1": (8.0, 11.6)}}
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4), sharey=True)
    for ax, ds in zip(axes, ("D1", "D2")):
        pts = {c: p for c, p in res[ds]["points"].items() if c != "DA"}
        ins = ax.inset_axes([0.13, 0.42, 0.46, 0.54])
        for c, p in pts.items():
            x, y = 100 * p["share_discarded"], 100 * p["share_pf_lost"]
            col = "#0B8A7D" if p["ours"] else ("#C2413B" if c in ("DEB|S1", "SC|S1", "J1|S1") else "#5F6B7A")
            mk = "D" if p["ours"] else ("s" if "SON" in c else "o")
            small = c in ("P_M1_M2|S1", "P_M2_E6B|S1")
            for a, sz in ((ax, 34), (ins, 30)):
                a.scatter(x, y, s=14 if small else sz, marker=mk, facecolors="none" if p["tuned_parameter"] else col,
                          edgecolors=col, linewidths=1.3, zorder=3, alpha=0.6 if small else 1.0)
            if c in main_lab[ds]:
                dx, dy, ha = main_lab[ds][c]
                ax.annotate(short[c], (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=6.4, color=col,
                            ha=ha, va="center")
            if c in inset_lab[ds]:
                ins.annotate(short[c], (x, y), xytext=inset_lab[ds][c], textcoords="data", fontsize=5.8, color=col,
                             ha="left", va="center",
                             arrowprops=dict(arrowstyle="-", color=col, lw=0.6, shrinkA=1, shrinkB=3))
        ins.set_xlim(-1.5, 28)
        ins.set_ylim(-1, 12.5)
        ins.tick_params(labelsize=5.5, length=2)
        ins.grid(alpha=0.25)
        ins.set_facecolor("#FBFBFB")
        ax.indicate_inset_zoom(ins, edgecolor="#9AA3AD", lw=0.6)
        ax.set_title(f"{ds} ({'real faults' if ds == 'D1' else 'seeded faults'})", fontsize=9)
        ax.set_xlabel("Failures discarded (%)", fontsize=8)
        ax.grid(alpha=0.25)
        ax.tick_params(labelsize=7)
        ax.set_xlim(-2, 82)
        ax.set_ylim(-2, 70)
    axes[0].set_ylabel("Bug-revealing tests lost (%)", fontsize=8)
    fig.text(0.5, -0.03, "Diamonds: this study's rules; squares: Claude Sonnet 5.5; hollow: threshold tuned on the development "
             "split; small dots: the other two KUU pairs.\nKeep-all is the origin; discard-all is (100, 100), off the "
             "chart. Better rules sit lower (fewer bug-revealing tests lost) and further right (more failures removed).", ha="center", fontsize=6.6)
    fig.tight_layout()
    FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(FIG.with_suffix(".png"), dpi=220, bbox_inches="tight")


def main():
    res = {"what": "discard–loss trade-off of every triage rule (D-110, post hoc, descriptive)", "decisions": ["D-110"],
           "D1": run("D1"), "D2": run("D2")}
    dump_json(OUT, res)
    plot(res)
    r = lambda v: round(v, 3) if isinstance(v, float) else v
    for ds in ("D1", "D2"):
        print(ds, "n", res[ds]["n_instances"], "PF", res[ds]["n_pf"])
        for c, p in res[ds]["points"].items():
            print(f"  {p['label']:28s} disc {r(p['share_discarded'])} lost {r(p['pf_lost'])} F1 {r(p['f1'])} MCC {r(p['mcc'])} "
                  f"gpu_s {r(p['local_gpu_s_per_instance'])} usd {r(p['frontier_usd_per_instance'])} leaves {r(p['share_leaving_machine'])}")


if __name__ == "__main__":
    main()
