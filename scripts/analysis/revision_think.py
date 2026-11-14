"""Thinking-judge follow-up (D-130). Zero calls; reads committed decisions and call logs only.

  gate    dev-pilot gate of thinking M1 (dev_gates.json written by scripts/local/dev_gates.py)
  d2      HT-1 (dMCC thinking J1 - M1 DEB > 0) and HT-2 (PF lost thinking J1 - M1 DEB < 0), one Holm family, paired
          bug-level bootstrap on D-110's D2 set; primary coding: a capped (or any invalid) output scores TF
  d1      the three D1 runs (replicates 60, 63, 64) on D-110's D1 set, beside DEB's eight-run spread
  cap     output-cap sensitivity for every thinking run (TF / keep / excluded) and HT-1/HT-2 under each (not in the family)
  tokens  consumed tokens per instance = prompt_eval_count + eval_count (eval_count includes thinking)
A part whose run is missing is reported as not available, never filled in.

    python scripts/analysis/revision_think.py  -> results/revision/think_followup.json
"""
import ast
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import revision_common as rc  # noqa: E402
from triage import config, stats  # noqa: E402
from triage import revision_metrics as rm  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

OUT = rc.OUT / "think_followup.json"
REV = rc.OUT / "runs"
CALLS = rc.ROOT / "data" / "raw" / "llm_calls_local_revision" / "qwen3.5_9b.jsonl"
RUNS = {"D1": [("REV_THINK_M1", 60), ("REV_THINK_D1R2_M1", 63), ("REV_THINK_D1R3_M1", 64)],
        "D2": [("REV_THINK_D2_M1", 62)], "dev": [("REV_THINK_DEV_M1", 61)]}
DEB_TOKENS_KEY = "DEB|S1"
COMPARE_D2 = {"KUU|S1": "KUU", "KUUNG|S1": "KUU-NG", "CAS|S1": "Cascade", "DEB|S1|SON": "Sonnet DEB", "DEB|S1": "M1 DEB"}


def _cost(d):
    c = d.get("cost")
    return (ast.literal_eval(c) if isinstance(c, str) else c) or {}


def call_index():
    out = {}
    if CALLS.exists():
        for l in open(CALLS, encoding="utf-8"):
            x = json.loads(l)
            loc = x.get("local") or {}
            out[x["key"]] = {"done_reason": loc.get("done_reason"), "eval_count": loc.get("eval_count"),
                             "prompt_eval_count": loc.get("prompt_eval_count"), "thinking_chars": loc.get("thinking_chars")}
    return out


def load_run(name, rep, calls):
    f = REV / name / "decisions.jsonl"
    if not f.exists():
        return None
    out = {}
    for d in read_jsonl(f):
        if d["arm"] == "J1" and d.get("level") == "S1" and d["replicate"] == rep:
            keys = _cost(d).get("call_keys") or []
            capped = bool(keys) and (calls.get(keys[0]) or {}).get("done_reason") == "length"
            out[d["instance_id"]] = {"label": d["label_raw"], "capped": capped and d["label_raw"] == rc.INV,
                                     "tokens": _cost(d).get("input_tokens", 0) + _cost(d).get("output_tokens", 0),
                                     "eval": (calls.get(keys[0]) or {}).get("eval_count") if keys else None}
    return out


def tensor(D, ids, pred):
    bugs = sorted({D.bug[i] for i in ids})
    bi = {b: n for n, b in enumerate(bugs)}
    T = np.zeros((len(bugs), 1, 4))
    for i in ids:
        p = pred[i]
        if p is None:
            continue
        t, k = D.lab[i] == rc.PF, p == rc.PF
        T[bi[D.bug[i]], 0, 0 if (t and k) else 2 if t else 1 if k else 3] += 1
    return T, bugs


def describe(D, ids, pred, W):
    T, bugs = tensor(D, ids, pred)
    pt, bs = rm.rates_point(T), rm.rates_bootstrap(T, W)
    tot = T.sum(axis=0)[0]
    return {**{k: pt[k] for k in ("tpr", "tnr", "ba", "pf_loss_rate", "share_discarded")},
            "ba_ci95": rc.ci(bs["ba"]), "tpr_ci95": rc.ci(bs["tpr"]), "tnr_ci95": rc.ci(bs["tnr"]),
            "mcc": stats.point_estimate(T, "mcc"), "mcc_ci95": rc.ci(stats.bootstrap_metric(T, "mcc", W)),
            "f1": stats.point_estimate(T, "f1"), "pf_lost": float(tot[2]),
            "bugs_lost": rm.bugs_lost([(D.bug[i], D.lab[i], pred[i]) for i in ids if pred[i] is not None]),
            "n": int(sum(1 for i in ids if pred[i] is not None))}


def think_pred(run, ids, policy):
    return {i: rm.cap_policy_label(run[i]["label"], run[i]["capped"], policy) for i in ids}


def hypotheses(D, ids, think, deb):
    """HT-1 dMCC and HT-2 dPF-lost, paired bug-level bootstrap, Holm over both. ids: instances scored in both arms."""
    Ta, bugs = tensor(D, ids, think)
    Tb, _ = tensor(D, ids, deb)
    W = stats.bootstrap_weights(len(bugs))
    c1 = stats.paired_contrast("HT-1", Ta, Tb, "mcc", W)
    fa, fb = Ta[:, 0, 2], Tb[:, 0, 2]
    dfn = W @ (fa - fb)
    d2 = float(fa.sum() - fb.sum())
    p2 = stats.bootstrap_p_two_sided(dfn)
    ph = stats.holm([c1.p, p2])
    h1 = {"delta": c1.delta, "mcc_thinking": c1.estimate_a, "mcc_deb": c1.estimate_b, "ci95": list(c1.ci95), "p": c1.p,
          "p_holm": ph[0], "supported": bool(ph[0] < config.ALPHA and c1.delta > 0)}
    h2 = {"delta": d2, "pf_lost_thinking": float(fa.sum()), "pf_lost_deb": float(fb.sum()), "ci95": rc.ci(dfn),
          "p": p2, "p_holm": ph[1], "supported": bool(ph[1] < config.ALPHA and d2 < 0)}
    return {"HT-1": h1, "HT-2": h2, "n_instances": len(ids), "n_bugs": len(bugs), "alpha": config.ALPHA}


def d2_part(calls):
    run = load_run(*RUNS["D2"][0], calls)
    if run is None:
        return {"status": "not run"}
    D = rc.build("D2")
    ids = [i for i in D.ids if i in run]
    missing = [i for i in D.ids if i not in run]
    deb = {i: (rc.PF if D.preds["DEB|S1"][0][i] == rc.PF else rc.TF) for i in ids}
    out = {"status": "run", "n_common": len(D.ids), "n_scored": len(ids), "not_decided_in_thinking_run": len(missing),
           "capped": sum(run[i]["capped"] for i in ids),
           "invalid": sum(run[i]["label"] == rc.INV for i in ids), "policies": {}}
    for pol in rm.CAP_POLICIES:
        tp = think_pred(run, ids, pol)
        keep = [i for i in ids if tp[i] is not None]
        out["policies"][pol] = {"hypotheses": hypotheses(D, keep, tp, deb), "n": len(keep)}
    out["confirmatory"] = out["policies"]["as_TF"]["hypotheses"]
    out["both_supported"] = out["confirmatory"]["HT-1"]["supported"] and out["confirmatory"]["HT-2"]["supported"]
    bugs = sorted({D.bug[i] for i in ids})
    W = stats.bootstrap_weights(len(bugs))
    desc = {"Thinking M1 J1": describe(D, ids, think_pred(run, ids, "as_TF"), W)}
    for c, nm in COMPARE_D2.items():
        r0 = sorted(D.preds[c])[0]
        desc[nm] = describe(D, ids, {i: (rc.PF if D.preds[c][r0][i] == rc.PF else rc.TF) for i in ids}, W)
    out["descriptive"] = desc
    # does KUU add protection beyond the thinking judge? PF tests the thinking judge drops that KUU keeps, and vice versa
    tp = think_pred(run, ids, "as_TF")
    kuu = D.preds["KUU|S1"][0]
    pf = [i for i in ids if D.lab[i] == rc.PF]
    out["kuu_vs_thinking"] = {"pf_lost_by_thinking_kept_by_kuu": sum(tp[i] == rc.TF and kuu[i] == rc.PF for i in pf),
                              "pf_lost_by_kuu_kept_by_thinking": sum(tp[i] == rc.PF and kuu[i] == rc.TF for i in pf),
                              "pf_lost_by_both": sum(tp[i] == rc.TF and kuu[i] == rc.TF for i in pf),
                              "kuu_then_thinking_discard_only_if_both": describe(
                                  D, ids, {i: (rc.TF if tp[i] == rc.TF and kuu[i] == rc.TF else rc.PF) for i in ids}, W)}
    out["tokens_per_instance"] = float(np.mean([run[i]["tokens"] for i in ids]))
    return out


def d1_part(calls):
    D = rc.build("D1")
    bugs = sorted({D.bug[i] for i in D.ids})
    W = stats.bootstrap_weights(len(bugs))
    per = {}
    for name, rep in RUNS["D1"]:
        run = load_run(name, rep, calls)
        if run is None:
            per[str(rep)] = {"status": "not run"}
            continue
        ids = [i for i in D.ids if i in run]
        row = {"run": name, "n_scored": len(ids), "not_decided": len(D.ids) - len(ids),
               "capped": sum(run[i]["capped"] for i in ids), "invalid": sum(run[i]["label"] == rc.INV for i in ids),
               "tokens_per_instance": float(np.mean([run[i]["tokens"] for i in ids])), "policies": {}}
        for pol in rm.CAP_POLICIES:
            tp = think_pred(run, ids, pol)
            row["policies"][pol] = describe(D, ids, tp, W)
        row.update({k: row["policies"]["as_TF"][k] for k in ("ba", "mcc", "f1", "tpr", "tnr", "pf_lost", "ba_ci95", "mcc_ci95")})
        per[str(rep)] = row
    done = [v for v in per.values() if "ba" in v]
    summ = {}
    for m in ("ba", "mcc", "f1", "tpr", "tnr", "pf_lost", "tokens_per_instance"):
        vals = [v[m] for v in done]
        if vals:
            summ[m] = {"mean": float(np.mean(vals)), "min": min(vals), "max": max(vals), "range": max(vals) - min(vals)}
    wp2 = json.loads((rc.OUT / "wp2_local_runs.json").read_text(encoding="utf-8"))
    deb = {m: {k: wp2["deb8"]["spread"][m][k] for k in ("min", "max", "range", "mean")} for m in ("ba", "mcc", "f1")}
    return {"runs": per, "n_runs": len(done), "summary": summ, "deb_eight_runs": deb}


def gate_part():
    f = REV / RUNS["dev"][0][0] / "dev_gates.json"
    if not f.exists():
        return {"status": "not available"}
    g = json.loads(f.read_text(encoding="utf-8"))
    return {"status": "run", **{k: g.get(k) for k in ("G_a", "G_b", "G_c", "G_d", "G_a_valid_rate", "G_a_runaway_D39",
                                                      "G_d_detail", "n_instances", "passes_required")},
            "m1_original": json.loads((rc.ROOT / "results/dev/GATE_M1b/dev_gates.json").read_text(encoding="utf-8"))["G_d_detail"]}


def main():
    calls = call_index()
    T = {r["condition"]: r for r in __import__("csv").DictReader(open(
        rc.ROOT / "results/heldout/analysis_final/D1_M1/tables/conditions.csv", encoding="utf-8"))}
    res = {"what": "thinking-judge follow-up (D-130): gate, D2 confirmation, D1 replicates, cap sensitivity, tokens",
           "decisions": ["D-130"], "gate": gate_part(), "d2": d2_part(calls), "d1": d1_part(calls),
           "deb_tokens_per_instance_D1": float(T[DEB_TOKENS_KEY]["consumed_tokens_per_instance"]),
           "token_note": "consumed tokens = Ollama prompt_eval_count + eval_count; eval_count counts every generated "
                         "token, thinking included; not token-matched to DEB"}
    dump_json(OUT, res)
    g = res["gate"]
    print("gate", g.get("status"), {k: g.get(k) for k in ("G_a", "G_b", "G_c", "G_d")}, (g.get("G_d_detail") or {}).get("J1_f1"))
    d2 = res["d2"]
    if d2.get("status") == "run":
        for h, v in d2["confirmatory"].items():
            if h.startswith("HT"):
                print(h, {k: (round(x, 4) if isinstance(x, float) else x) for k, x in v.items()})
        for nm, v in d2["descriptive"].items():
            print(f"  {nm:16s} BA {v['ba']:.3f} TPR {v['tpr']:.3f} TNR {v['tnr']:.3f} MCC {v['mcc']:.3f} PF lost {v['pf_lost']:.0f} bugs lost {v['bugs_lost']}")
        print("  capped", d2["capped"], {p: (round(v["hypotheses"]["HT-1"]["delta"], 3), v["hypotheses"]["HT-1"]["supported"],
                                          v["hypotheses"]["HT-2"]["delta"], v["hypotheses"]["HT-2"]["supported"]) for p, v in d2["policies"].items()})
        print("  kuu vs thinking", {k: v for k, v in d2["kuu_vs_thinking"].items() if not isinstance(v, dict)})
    for r, v in res["d1"]["runs"].items():
        print("D1", r, {k: (round(v[k], 3) if isinstance(v.get(k), float) else v.get(k)) for k in ("ba", "mcc", "f1", "pf_lost", "capped", "tokens_per_instance")})
    print("D1 summary", {m: {k: round(x, 3) for k, x in s.items()} for m, s in res["d1"]["summary"].items()})


if __name__ == "__main__":
    main()
