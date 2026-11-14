"""Post hoc sensitivity analyses requested by the mock reviews (D-106). Zero model calls; committed before computing.
None re-reads a confirmatory verdict: each reports how an estimate or verdict behaves under one stated change.

  (a) MCC family (R3-2 both rounds). The five confirmatory contrasts (analysis.CONFIRMATORY; same evaluation, D-70
      exclusions, sampling weights and bug resamples as confirmatory.json) on MCC instead of F1, Holm over the five.
  (b) Two-level bootstrap (round 1 R3-3, round 2 R3-1). The same five F1 contrasts; each draw resamples bugs AND, per
      arm, its replicates (with replacement, seed 20261109). Reported beside the bug-only interval with the widening
      factor (two-level CI width / bug-only CI width).
  (c) Operating points on D2 (round 1 R1-3, round 2 R1-3). KUU against: the cross-family 2-of-3 majority of the same
      votes; M1 and M2 discarding only when all five (or the first three) of their own SC samples say TEST_FAULT; and
      M1 DEB discarding only at stated confidence 100 (the D-82 selective rule's threshold). F1, MCC, precision, recall,
      PF tests lost, share discarded, MCC(KUU) − MCC(rule) paired. Descriptive.
  (d) Cost–quality frontier on D2 (round 2 R1-4). Frontier calls and US$ (from the E9b decisions' logged cost) with
      MCC, F1, PF tests lost and bugs with no PF test kept, for Sonnet J1 and DEB on every instance and the cascade to
      each; local judges counted as 3 local calls per instance. Descriptive.
  (e) Deployment prevalence (round 2 R2-2). Precision at an assumed PF prevalence π of 0.05 and 0.02 from each rule's
      recall and false-positive rate, P = πR / (πR + (1 − π)FPR), on D1 (post hoc rules) and D2. Descriptive.
  (f) Co-error on a difference scale (round 2 R3-5). Excess co-error = joint miss rate − product of miss rates, mean
      over cross-family pairs and over within-family sample pairs, with 95% bug-level CIs, D1 and D2. Descriptive.
  (g) Leave-one-project-out (round 2 R3-4): the committed LOPO ΔF1 of H1, H3a, H3b (analysis_summary.json), min and
      max and whether any sign flips. No computation beyond the summary.

    python scripts/analysis/review_sensitivity.py   -> results/heldout/analysis_final/D1_M1/tables/review_sensitivity.json
"""
import ast
import itertools
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

from triage import analysis, config, stats  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

import mde_sensitivity  # noqa: E402  (the committed evaluation loader of the confirmatory analysis)

TABLES = ROOT / "results" / "heldout" / "analysis_final" / "D1_M1" / "tables"
RUNS = ROOT / "results" / "runs_local"
FRONT = ROOT / "results" / "runs_frontier"
TF, PF = "TEST_FAULT", "PROGRAM_FAULT"
SEED_REPS = 20261109


def mcc_family(ev, jd):
    cs = [ev.contrast(name, a, b, "mcc", restrict=jd if sub == "javadoc" else None)
          for name, a, b, sub in analysis.CONFIRMATORY]
    adj = stats.holm([c.p for c in cs])
    out = []
    for c, p in zip(cs, adj):
        d = vars(c)
        d["p_holm"] = p
        d["significant_after_holm"] = bool(p < config.ALPHA)
        out.append(d)
    return out


def two_level(ev, jd):
    rng = np.random.default_rng(SEED_REPS)
    out = []
    for name, a, b, sub in analysis.CONFIRMATORY:
        evr = ev._restricted(ev.comparison_set(a + b, jd if sub == "javadoc" else None))
        W = evr.W

        def boot(cs):
            vals = []
            for c in cs:
                T = evr.tensor(c)
                n, R = T.shape[0], T.shape[1]
                B = W.shape[0]
                idx = rng.integers(0, R, size=(B, R))
                tot = (W @ T.reshape(n, R * 4)).reshape(B, R, 4)
                tot = np.take_along_axis(tot, idx[:, :, None].repeat(4, axis=2), axis=1)
                vals.append(np.nanmean(stats._metric_from_totals(tot, "f1"), axis=1))
            return np.mean(vals, axis=0)
        d = boot(a) - boot(b)
        bug_only = (np.mean([stats.bootstrap_metric(evr.tensor(c), "f1", W) for c in a], axis=0)
                    - np.mean([stats.bootstrap_metric(evr.tensor(c), "f1", W) for c in b], axis=0))
        ci2, ci1 = stats.percentile_ci(d), stats.percentile_ci(bug_only)
        out.append({"name": name, "ci95_bug_only": ci1, "ci95_two_level": ci2,
                    "widening_factor": (ci2[1] - ci2[0]) / (ci1[1] - ci1[0]) if ci1[1] > ci1[0] else None,
                    "p_two_level": stats.bootstrap_p_two_sided(d),
                    "replicates": {c: int(evr.tensor(c).shape[1]) for c in a + b}})
    return out


def s1(d):
    return d.get("level") == "S1" and (d.get("variant") or "full") == "full"


def d2_votes():
    votes = {}
    for m, run in {"M1": "LOCAL_HO_KUU_D2_M1", "M2": "LOCAL_HO_KUU_D2_M2", "E6B": "LOCAL_HO_KUU_D2_E6B"}.items():
        for d in read_jsonl(RUNS / run / "decisions.jsonl"):
            if d["arm"] == "J1" and s1(d) and d["replicate"] == 20:
                votes.setdefault(d["instance_id"], {})[m] = d["label_raw"]
    return votes


def operating_points():
    samp = json.loads((config.PROCESSED / "sample_D2_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / "labels_D2.jsonl") if l["instance_id"] in keep]
    aborted = set(json.loads((ROOT / "results" / "kuu" / "analysis" / "kuu_d2.json").read_text(encoding="utf-8"))
                  ["aborted_excluded"])
    syn, rules = [], []

    def add(i, arm, lab):
        syn.append({"instance_id": i, "arm": arm, "level": "S1", "variant": "full", "replicate": 0, "label_raw": lab})
        if arm not in rules:
            rules.append(arm)
    for i, v in d2_votes().items():
        vs = [v.get(m) for m in ("M1", "M2", "E6B")]
        add(i, "KUU", TF if all(x == TF for x in vs) else PF)
        add(i, "MAJ3", TF if sum(x == TF for x in vs) >= 2 else PF)
    for m, run in {"M1": "LOCAL_HO_E5R1_D2", "M2": "LOCAL_HO_E5R3_M2_D2"}.items():
        for d in read_jsonl(RUNS / run / "decisions.jsonl"):
            if d["arm"] == "SC" and s1(d) and d["replicate"] == 0:
                v = d.get("votes") or []
                for k in (5, 3):
                    add(d["instance_id"], f"{m}SC{k}U", TF if len(v) >= k and all(x == TF for x in v[:k]) else PF)
    for d in read_jsonl(RUNS / "LOCAL_HO_E5R1_D2" / "decisions.jsonl"):
        if d["arm"] == "DEB" and s1(d) and d["replicate"] == 0:
            conf = d.get("confidence")
            add(d["instance_id"], "M1DEBtau100",
                TF if d["label_raw"] == TF and conf is not None and float(conf) >= 100 else PF)
    ev = analysis.Evaluation(syn, labels, samp.get("tf_weights"), exclusions={("S1", "full"): aborted})
    conds = [f"{r}|S1" for r in rules]
    evr = ev._restricted(ev.comparison_set(conds))
    keys = ("f1", "f1_ci95", "mcc", "mcc_ci95", "precision", "recall", "pf_lost")
    summ = {}
    for c in conds:
        s = {k: evr.summary(c).get(k) for k in keys}
        rows = [x for x in syn if x["arm"] == c.split("|")[0] and x["instance_id"] in evr.lab]
        s["share_discarded"] = sum(x["label_raw"] == TF for x in rows) / len(rows) if rows else None
        summ[c] = s
    return {"n_instances": len(evr.lab), "n_bugs": len(evr.bugs), "summary": summ,
            "kuu_minus_rule_mcc": {c: vars(evr.contrast(f"KUU - {c}", ["KUU|S1"], [c], "mcc")) for c in conds[1:]},
            "note": "descriptive; same-family rules discard only when all k samples of ONE model say TEST_FAULT"}


def _cost(d):
    c = d.get("cost")
    if isinstance(c, str):
        c = ast.literal_eval(c)
    return float((c or {}).get("cost_usd") or 0.0), int((c or {}).get("calls") or 0)


def frontier_table():
    cas = json.loads((ROOT / "results" / "cascade" / "analysis" / "cascade_d2.json").read_text(encoding="utf-8"))
    votes = d2_votes()
    escalated = {i for i, v in votes.items()
                 if not (all(v.get(m) == TF for m in ("M1", "M2", "E6B")) or all(v.get(m) == PF for m in ("M1", "M2", "E6B")))}
    tot = {}
    for d in read_jsonl(FRONT / "E9B_SONNET55_D2" / "decisions.jsonl"):
        if not s1(d):
            continue
        usd, calls = _cost(d)
        arm = d["arm"]
        t = tot.setdefault(arm, {"all_usd": 0.0, "all_calls": 0, "esc_usd": 0.0, "esc_calls": 0})
        t["all_usd"] += usd
        t["all_calls"] += calls
        if d["instance_id"] in escalated:
            t["esc_usd"] += usd
            t["esc_calls"] += calls
    rows = {}
    for name, cond, arm, part in (("Sonnet J1, every instance", "J1|S1|SON", "J1", "all"),
                                  ("Sonnet DEB, every instance", "DEB|S1|SON", "DEB", "all"),
                                  ("Cascade to Sonnet J1", "CASJ1|S1", "J1", "esc"),
                                  ("Cascade to Sonnet DEB", "CAS|S1", "DEB", "esc"),
                                  ("KUU (no frontier)", "KUU|S1", None, None)):
        s = cas["summary"][cond]
        rows[name] = {"frontier_calls": tot[arm][f"{part}_calls"] if arm else 0,
                      "frontier_usd": tot[arm][f"{part}_usd"] if arm else 0.0,
                      "local_calls": 3 * cas["n_instances"] if cond in ("CAS|S1", "CASJ1|S1", "KUU|S1") else 0,
                      "mcc": s["mcc"], "f1": s["f1"], "pf_lost": s["pf_lost"],
                      "bugs_with_no_pf_kept": cas["bugs_with_no_pf_kept"][cond]}
    return {"rows": rows, "escalated": len(escalated & set(votes)),
            "cascade_minus_sonnet_deb_mcc": cas["cascade_minus_sonnet_deb_mcc"],
            "note": "frontier costs are batch-API USD from logged usage; local compute is not priced"}


def deployment_precision():
    out = {}
    files = {"D1": ROOT / "results" / "cascade" / "analysis" / "cascade_d1_posthoc.json",
             "D2": ROOT / "results" / "cascade" / "analysis" / "cascade_d2.json"}
    for ds, f in files.items():
        j = json.loads(f.read_text(encoding="utf-8"))
        n_pf = j["pf_prevalence"]["PF"]
        n_tf = j["pf_prevalence"]["TF"]
        rows = {}
        for c in ("KUU|S1", "CAS|S1", "DEB|S1|SON", "DEB|S1"):
            s = j["summary"][c]
            tp, fn, p = s["TP"], s["FN"], s["precision"]
            fp = tp * (1 - p) / p if p else 0.0
            reps = max(1, round((tp + fn) / n_pf)) if n_pf else 1
            fpr = fp / (n_tf * reps) if n_tf else None
            rec = s["recall"]
            rows[c] = {"recall": rec, "fpr": fpr,
                       **{f"precision_at_{pi}": (pi * rec / (pi * rec + (1 - pi) * fpr)) if fpr is not None and (pi * rec + (1 - pi) * fpr) > 0 else None
                          for pi in (0.05, 0.02)}}
        out[ds] = {"status": j["status"], "rules": rows}
    return out


def excess_coerror():
    import error_diversity as ed
    out = {}
    for name, plan in ed.PLAN.items():
        samp = json.loads((config.PROCESSED / plan["sample"]).read_text(encoding="utf-8"))
        keep = set(samp["instance_ids"])
        labels = {l["instance_id"]: l for l in read_jsonl(config.GT_STORE / plan["labels"]) if l["instance_id"] in keep}
        votes, sc = {}, {}
        for m, (r, rep) in plan["votes"].items():
            for d in read_jsonl(RUNS / r / "decisions.jsonl"):
                if d["arm"] == "J1" and s1(d) and d["replicate"] == rep:
                    votes.setdefault(d["instance_id"], {})[m] = d["label_raw"]
        for m, r in plan["sc"].items():
            for d in read_jsonl(RUNS / r / "decisions.jsonl"):
                if d["arm"] == "SC" and s1(d) and d["replicate"] == 0:
                    sc.setdefault(m, {})[d["instance_id"]] = (d.get("votes") or [])[:3]
        ab = set().union(*(ed.aborts(r) for r, _ in plan["votes"].values()), *(ed.aborts(r) for r in plan["extra_aborts"]),
                         *(ed.aborts(r) for r in plan["sc"].values()))
        ids = sorted(i for i, l in labels.items() if l["label"] in ("PF", "TF") and i not in ab
                     and len(votes.get(i, {})) == 3 and all(i in sc[m] for m in sc))
        pf = [i for i in ids if labels[i]["label"] == "PF"]
        bug_of = {i: labels[i]["bug_name"] for i in ids}
        bugs = sorted(set(bug_of.values()))
        W = stats.bootstrap_weights(len(bugs))
        n = ed.by_bug({i: 1 for i in pf}, pf, bug_of, bugs)
        rate = lambda x: ed.ratio(ed.by_bug(x, pf, bug_of, bugs), n, W)
        point = lambda x: sum(x.values()) / len(pf)
        cross_s, cross_p = [], []
        for a, b in itertools.combinations(plan["votes"], 2):
            ma = {i: int(votes[i][a] == TF) for i in pf}
            mb = {i: int(votes[i][b] == TF) for i in pf}
            jab = {i: ma[i] * mb[i] for i in pf}
            cross_s.append(rate(jab) - rate(ma) * rate(mb))
            cross_p.append(point(jab) - point(ma) * point(mb))
        within_s, within_p = [], []
        for m, s in sc.items():
            ms = [{i: int(len(s[i]) > k and s[i][k] == TF) for i in pf} for k in range(3)]
            for a, b in ((0, 1), (0, 2), (1, 2)):
                jab = {i: ms[a][i] * ms[b][i] for i in pf}
                within_s.append(rate(jab) - rate(ms[a]) * rate(ms[b]))
                within_p.append(point(jab) - point(ms[a]) * point(ms[b]))
        cs, ws = np.mean(cross_s, axis=0), np.mean(within_s, axis=0)
        out[name] = {"excess_cross": float(np.mean(cross_p)), "excess_cross_ci95": stats.percentile_ci(cs),
                     "excess_within": float(np.mean(within_p)), "excess_within_ci95": stats.percentile_ci(ws),
                     "difference": float(np.mean(cross_p) - np.mean(within_p)),
                     "difference_ci95": stats.percentile_ci(cs - ws), "n_pf": len(pf)}
    return out


def lopo():
    s = json.loads((ROOT / "results" / "heldout" / "analysis_final" / "D1_M1" / "analysis_summary.json")
                   .read_text(encoding="utf-8"))
    out = {}
    for h, v in s.get("wilcoxon_projects", {}).items():
        lo = v.get("lopo_delta_f1")
        if lo:
            vals = list(lo.values())
            out[h] = {"min": min(vals), "max": max(vals), "projects": len(vals),
                      "sign_flips": bool(min(vals) < 0 < max(vals))}
    return out


def main():
    ev, jd = mde_sensitivity.evaluation()
    out = {"what": "post hoc sensitivity analyses requested by the mock reviews (D-106)", "decisions": ["D-106"],
           "mcc_family": mcc_family(ev, jd), "two_level_bootstrap": two_level(ev, jd),
           "operating_points_d2": operating_points(), "frontier_d2": frontier_table(),
           "deployment_precision": deployment_precision(), "excess_coerror": excess_coerror(), "lopo": lopo(),
           "note": "post hoc sensitivity; no confirmatory verdict is re-read"}
    dump_json(TABLES / "review_sensitivity.json", out)
    r = lambda v: round(v, 3) if isinstance(v, float) else v
    for c in out["mcc_family"]:
        print(f"  MCC {c['name']}: {r(c['delta'])} {[r(x) for x in c['ci95']]} p_holm={r(c['p_holm'])}")
    for c in out["two_level_bootstrap"]:
        print(f"  2L {c['name']}: bug-only {[r(x) for x in c['ci95_bug_only']]} two-level {[r(x) for x in c['ci95_two_level']]} x{r(c['widening_factor'])}")
    for c, s in out["operating_points_d2"]["summary"].items():
        print(f"  D2 {c}: F1 {r(s['f1'])} MCC {r(s['mcc'])} lost {r(s['pf_lost'])} discarded {r(s['share_discarded'])}")
    for k, v in out["frontier_d2"]["rows"].items():
        print(f"  frontier {k}: calls {v['frontier_calls']} ${r(v['frontier_usd'])} MCC {r(v['mcc'])} lost {r(v['pf_lost'])} bugs {v['bugs_with_no_pf_kept']}")
    for ds, v in out["deployment_precision"].items():
        print(f"  deploy {ds}:", {c: (r(x['precision_at_0.05']), r(x['precision_at_0.02'])) for c, x in v["rules"].items()})
    for ds, v in out["excess_coerror"].items():
        print(f"  excess {ds}: cross {r(v['excess_cross'])} within {r(v['excess_within'])} diff {r(v['difference'])} {[r(x) for x in v['difference_ci95']]}")
    print("  lopo", out["lopo"])


if __name__ == "__main__":
    main()
