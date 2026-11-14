"""Evaluate decision records against the label store; write tables, contrasts and figures.

    python scripts/analyze.py --runs results/runs/E1E3_main_M1_D1test [results/runs/E4_...] --dataset D1 --split test
    python scripts/analyze.py --smoke   # mock/synthetic pipeline check; writes under results/smoke only
"""
import argparse
import csv
import json
import math
from pathlib import Path

from _common import config
from triage import analysis, figures, glmm, stats
from triage.io_utils import dump_json, read_jsonl

_FROZEN = config.ROOT / "configs" / "local_models.FROZEN.json"
K_T = json.loads(_FROZEN.read_text(encoding="utf-8"))["decoding"]["k_T"] if _FROZEN.exists() else None


def _fmt(v):
    if isinstance(v, float):
        return "" if math.isnan(v) else round(v, 4)
    if isinstance(v, tuple):
        return f"[{v[0]:.3f}, {v[1]:.3f}]"
    return v


def write_csv(rows, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: _fmt(r.get(k)) for k in keys})


def run(decisions, labels, weights, out: Path, smoke: bool, javadoc_ids: set, exclusions: dict | None = None,
        status: str | None = None, heldout_projects: list | None = None, dataset: str = "D1",
        prevalences: dict | None = None):
    exclusions = exclusions or {}
    figures.STAMP = status if status and not smoke else None
    ev = analysis.Evaluation(decisions, labels, weights, exclusions=exclusions)
    conds = sorted(ev.by_cond, key=lambda c: (analysis.ARM_ORDER.index(c.split("|")[0])
                                              if c.split("|")[0] in analysis.ARM_ORDER else 99, c))
    # D-70: baselines are tabulated on the primary level's instance set, like the LLM arms they are read against
    summ = {c: (ev.baseline_summary(c) if c in analysis.BASELINES else ev.summary(c)) for c in conds}
    write_csv(list(summ.values()), out / "tables" / "conditions.csv")
    conf = analysis.confirmatory(ev, javadoc_ids)
    dump_json(out / "tables" / "confirmatory.json", conf)
    res = {"status": status, "n_labelled_instances": len(ev.lab), "n_bugs": len(ev.bugs), "conditions": list(summ),
           "leakage_abort_exclusions": {"rule": "D-70: an instance aborted by the leakage guard at (level, variant) "
                                                "is excluded from every arm there; E1-E3 sets are fixed by Tier 1; "
                                                "baselines use the set of the condition they are compared with; "
                                                "ablations are compared with their parent on the intersection",
                                        "instances": {f"{lv}|{var}": sorted(ids)
                                                      for (lv, var), ids in sorted(exclusions.items())},
                                        "counts_labelled": ev.exclusion_counts(),
                                        "n_per_level": {lv: len(ev.allowed(f"X|{lv}")) for lv in
                                                        sorted({analysis.cond_level(c) for c in conds} - {None})}},
           "confirmatory": conf}
    dump_json(out / "tables" / "exclusions.json", res["leakage_abort_exclusions"])
    # E2 logistic mixed model (exploratory; statsmodels VB, deviation X-02); D-70: instances kept at every level
    e2_drop = set().union(*[exclusions.get((lv, "full"), set()) for lv in ("S0", "S1", "S2")])
    gdf = glmm.rows_from_decisions([d for d in decisions if d["instance_id"] not in e2_drop], ev.lab, ev.meta)
    res["glmm_e2"] = glmm.e2_models(gdf) if len(gdf) else {"status": "not fitted", "reason": "no E2 decisions"}
    dump_json(out / "tables" / "glmm_e2.json", res["glmm_e2"])
    # SC-T fairness check
    sct = [c for c in conds if c.startswith("SC-T|S1")]
    if sct and "DEB|S1" in summ:
        res["sc_t_check"] = vars(ev.contrast("DEB vs SC-T (S1)", ["DEB|S1"], [sct[0]]))
    elif "SC|S1" in summ and "DEB|S1" in summ and K_T == config.SC_SAMPLES:
        # D-59: k_T (P4) equals SC's sample count, so SC is itself the token-matched comparator; no SC-T calls
        res["sc_t_check"] = {**vars(ev.contrast("DEB vs SC (S1; SC = SC-T at k_T = 5, D-59)", ["DEB|S1"], ["SC|S1"])),
                             "note": "no separate SC-T calls (D-59): k_T = SC_SAMPLES, SC decisions are the comparator"}
    # efficiency relative to J1 at the same level
    for c in conds:
        lv = c.split("|")[1] if "|" in c else None
        j = summ.get(f"J1|{lv}")
        s = summ[c]
        if j and "consumed_tokens_per_instance" in s and s["consumed_tokens_per_instance"] > 0 and c != f"J1|{lv}":
            dtok = (s["consumed_tokens_per_instance"] - j["consumed_tokens_per_instance"]) / 1000
            s["delta_f1_vs_J1_per_1k_tokens"] = (s["f1"] - j["f1"]) / dtok if dtok else math.nan
    write_csv(list(summ.values()), out / "tables" / "conditions.csv")
    # A3 re-analysis
    a3 = analysis.a3_reanalysis(decisions)
    if a3:
        ev3 = analysis.Evaluation(decisions + a3, labels, weights, exclusions=exclusions)
        res["A3"] = {c: {k: ev3.summary(c)[k] for k in ("precision", "recall", "f1", "mcc")}
                     for c in ev3.by_cond if "A3" in c}
    # sensitivity: invalid outputs excluded; AMB rescored
    sens = {}
    for name, kw in (("invalid_excluded", {"invalid_policy": "exclude"}), ("AMB_as_PF", {"amb_policy": "as_PF"}),
                     ("AMB_as_TF", {"amb_policy": "as_TF"})):
        e2 = analysis.Evaluation(decisions, labels, weights, exclusions=exclusions, **kw)
        sens[name] = {c: {k: e2.summary(c)[k] for k in ("f1", "mcc")} for c in conds if e2.by_cond.get(c)}
    res["sensitivity_f1"] = sens      # F1 with MCC beside it (D-51: F1 alone hides chance level)
    # McNemar on majority-correct, per confirmatory contrast (sensitivity)
    mc = {}
    for name, a, b, _ in analysis.CONFIRMATORY:
        if len(a) == 1 and a[0] in summ and b[0] in summ:
            ca, cb = ev.majority_correct(a[0]), ev.majority_correct(b[0])
            ids = sorted(ev.comparison_set([a[0], b[0]]))
            mc[name] = stats.mcnemar_exact([ca[i] for i in ids], [cb[i] for i in ids])
    res["mcnemar"] = mc
    # per-project heterogeneity (R5)
    ev_p = ev._restricted(ev.allowed(f"X|{analysis.PRIMARY_LEVEL}"))   # D-70: S1 set for all four, incl. R0
    pp = {c: ev_p.per_project_f1(c) for c in ("J1|S1", "SC|S1", "DEB|S1", "R0") if c in summ}
    res["per_project_f1"] = pp       # D-70: NaN = no PF in the scored set (undefined), 0 = PF present, none found
    res["per_project_counts"] = ev_p.project_counts()
    unscored = sorted(set(heldout_projects or []) - {ev.meta[i]["project"] for i in ev.lab})
    res["projects_without_scored_instances"] = unscored
    wil = {}
    for name, a, b, _ in analysis.CONFIRMATORY:
        if len(a) == 1 and a[0] in pp and b[0] in pp:
            wil[name] = stats.wilcoxon_projects(pp[a[0]], pp[b[0]])
            wil[name]["lopo_delta_f1"] = ev_p.lopo(a, b)
    res["wilcoxon_projects"] = wil
    # D-74: F1 read with MCC and the prevalence-adjusted precision beside it, at this dataset's PF prevalence
    res["prevalence"] = analysis.prevalence_report(ev, summ, dataset, prevalences)
    dump_json(out / "tables" / "prevalence.json", res["prevalence"])
    write_csv(res["prevalence"]["conditions"], out / "tables" / "f1_mcc_precision.csv")
    dump_json(out / "analysis_summary.json", res)
    # figures
    fdir = out / "figures"
    e1 = [summ[c] for c in ("DA", "KA", "R0", "J1|S1", "SC|S1", "SC-T|S1" if sct else "", "DEB|S1") if c in summ]
    if e1:
        figures.prf_bars(e1, fdir / "fig_e1_prf", smoke)
        figures.confusion_grid(e1, fdir / "fig_e1_confusion", smoke)
    if any(c.endswith("|S0") for c in summ):
        figures.spec_levels(summ, fdir / "fig_e2_spec_f1", "f1", smoke)
        figures.spec_levels(summ, fdir / "fig_e2_spec_recall", "recall", smoke)
    llm = [summ[c] for c in conds if "consumed_tokens_per_instance" in summ[c] and c.split("|")[1:2] == ["S1"]
           and len(c.split("|")) == 2]
    if llm:
        figures.pareto(llm, fdir / "fig_e3_pareto", smoke)
    if conf.get("f1"):
        figures.forest(conf["f1"], fdir / "fig_confirmatory_forest", smoke=smoke)
    abl = []
    for c, parent in (("A1|S1", "DEB|S1"), ("A2|S1", "DEB|S1"), ("J1|S1|noF", "J1|S1"), ("SC|S1|noF", "SC|S1"),
                      ("DEB|S1|noF", "DEB|S1"), ("J1|S1|impl", "J1|S1"), ("DEB|S1|impl", "DEB|S1"),
                      ("J1|S2|specprime", "J1|S2")):
        if c in summ and parent in summ:
            ids = {d["instance_id"] for d in ev.by_cond[c]}
            k = ev.contrast(f"{c} − {parent}", [c], [parent], "f1", restrict=ids)
            abl.append(vars(k))
    if abl:
        dump_json(out / "tables" / "ablations.json", abl)
        figures.forest(abl, fdir / "fig_e4_ablations", xlabel="Δ F1 vs parent arm, 95% CI", smoke=smoke)
    if pp:
        figures.per_project(pp, fdir / "fig_r5_per_project", smoke, counts=res["per_project_counts"], unscored=unscored)
    pr = res["prevalence"]
    print(json.dumps({"dataset": dataset, "instances": len(ev.lab), "bugs": len(ev.bugs),
                      "pf_prevalence": _fmt(pr["pf_prevalence"]), "ka_f1": _fmt(pr["ka_f1"]),
                      "f1_mcc_precision_prev_adj": {c: [_fmt(s["f1"]), _fmt(s["mcc"]), _fmt(s["precision_prev_adj"])]
                                                    for c, s in summ.items()}}, indent=1))
    print(analysis.F1_NOT_COMPARABLE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="*", default=[])
    ap.add_argument("--dataset", default="D1")
    ap.add_argument("--split", default="test")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--status", help='written into analysis_summary.json, e.g. "preliminary, Tier 1 only"')
    a = ap.parse_args()
    if a.smoke:
        base = config.ROOT / "results" / "smoke"
        decisions = list(read_jsonl(base / "SMOKE_synthetic" / "decisions.jsonl"))
        labels = list(read_jsonl(base / "synthetic_labels.jsonl"))
        samp = json.loads((base / "synthetic_sample.json").read_text())
        jd = set(samp["javadoc_ids"])
        excl = analysis.abort_exclusions(read_jsonl(base / "SMOKE_synthetic" / "leakage_rejections.jsonl"))
        run(decisions, labels, samp["tf_weights"], base / "analysis", True, jd, excl, "smoke (synthetic)",
            dataset="smoke")
        return
    decisions = [d for r in a.runs for d in read_jsonl(Path(r) / "decisions.jsonl")]
    exclusions = analysis.abort_exclusions(x for r in a.runs for x in read_jsonl(Path(r) / "leakage_rejections.jsonl"))
    labels = list(read_jsonl(config.GT_STORE / f"labels_{a.dataset}.jsonl"))
    samp = json.loads((config.PROCESSED / f"sample_{a.dataset}_{a.split}.json").read_text())
    keep = set(samp["instance_ids"])
    labels = [l for l in labels if l["instance_id"] in keep]
    jd = {i["instance_id"] for i in read_jsonl(config.PROCESSED / f"instances_{a.dataset}.jsonl")
          if i["covariates"]["javadoc_present"]}
    manifest = config.PROCESSED / "split_manifest.json"
    heldout = (json.loads(manifest.read_text())["test_projects"]
               if a.split == "test" and a.dataset == "D1" and manifest.exists() else None)
    prev = {}   # D-74: judged-sample PF prevalence of each dataset (labels only), so the outputs state it side by side
    for ds in ("D1", "D2"):
        lp, sp = config.GT_STORE / f"labels_{ds}.jsonl", config.PROCESSED / f"sample_{ds}_{a.split}.json"
        if lp.exists() and sp.exists():
            prev[ds] = analysis.judged_prevalence(list(read_jsonl(lp)),
                                                  json.loads(sp.read_text(encoding="utf-8"))["instance_ids"])
    run(decisions, labels, samp["tf_weights"], Path(a.out) if a.out else config.RESULTS / f"analysis_{a.dataset}_{a.split}",
        False, jd, exclusions, a.status, heldout, dataset=a.dataset, prevalences=prev)


if __name__ == "__main__":
    main()
