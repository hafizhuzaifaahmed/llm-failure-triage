"""Exploratory analyses D1-D4, declared in D-82 before computing (zero model calls; D1-test, S1, judge M1).

    (D1) expected cost r*FN + FP against the miss / false-alarm cost ratio r; break-even ratios against KA and DA
    (D2) calibration (ECE, 10 equal-width bins) and selective triage: discard only a TF said with confidence >= tau,
         tau tuned on the development pilot only (results/dev/GATE_M1b) and applied unchanged to D1-test
    (D3) SC -> DEB cascade: escalate to DEB only when SC's PF vote share is 2/5 or 3/5
    (D4) debate behaviour: concession rate, last-presented bias, flips of the SC majority

Every rule is the one written in D-82. Exploratory: no confirmatory test, no multiplicity correction; reported as such.

    python scripts/analysis/exploratory_d82.py   -> results/heldout/analysis_final/D1_M1/tables/exploratory_d82.json
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import analysis, config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

RUN = ROOT / "results" / "runs_local" / "LOCAL_HO_E1E3_M1"
DEV = ROOT / "results" / "dev" / "GATE_M1b"
OUT = ROOT / "results" / "heldout" / "analysis_final" / "D1_M1" / "tables" / "exploratory_d82.json"
PF, TF = "PROGRAM_FAULT", "TEST_FAULT"
TAUS = (50, 60, 70, 80, 90, 95, 100)
SPLIT = (0.4, 0.6)


def label(d):                      # primary policy: INVALID scored as TF
    return PF if d["label_raw"] == PF else TF


def conf(d):
    """Stated confidence of the decision in [0, 1]; SC uses its majority vote share (D-82)."""
    if d["arm"] == "SC":
        v = d["agreement"]["vote_share_pf"]
        return max(v, 1 - v)
    c = d.get("confidence")
    return None if c is None else c / 100.0


def tf_conf(d):
    """Confidence that the decision is TF (selective rule)."""
    if d["arm"] == "SC":
        return 1 - d["agreement"]["vote_share_pf"]
    c = conf(d)
    return None if c is None or label(d) != TF else c


def selective(d, tau):
    c = tf_conf(d)
    return TF if (label(d) == TF and c is not None and c >= tau / 100.0) else PF


def f1(pairs):
    tp = sum(1 for y, p in pairs if y == "PF" and p == PF)
    fp = sum(1 for y, p in pairs if y == "TF" and p == PF)
    fn = sum(1 for y, p in pairs if y == "PF" and p == TF)
    return 2 * tp / (2 * tp + fp + fn) if tp else 0.0


def main():
    samp = json.loads((config.PROCESSED / "sample_D1_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    lab_all = {l["instance_id"]: l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl")}
    labels = [lab_all[i] for i in keep if i in lab_all]
    rej = list(read_jsonl(RUN / "leakage_rejections.jsonl"))
    excl = analysis.abort_exclusions(rej)
    s1_drop = excl.get(("S1", "full"), set())
    decs = [d for d in read_jsonl(RUN / "decisions.jsonl")
            if d["level"] == "S1" and (d.get("variant") or "full") == "full" and d["arm"] in ("J1", "SC", "DEB")]
    scored = {i for i, l in lab_all.items() if i in keep and l["label"] in ("PF", "TF")} - s1_drop
    decs = [d for d in decs if d["instance_id"] in scored]
    by = {(d["arm"], d["instance_id"], d["replicate"]): d for d in decs}
    w = samp["tf_weights"]
    out = {"what": "exploratory analyses D1-D4 declared in D-82 (zero calls)", "scored_instances": len(scored), "D1": {}, "D2": {},
           "D3": {}, "D4": {}}

    # (D1) cost ratio
    for arm in ("KA", "J1", "SC", "DEB"):
        reps = sorted({r for (a, _, r) in by if a == (arm if arm != "KA" else "J1")})
        rows = []
        for r in reps:
            tp = fp = fn = tn = fpw = tnw = 0.0
            for i in scored:
                y = lab_all[i]["label"]
                p = PF if arm == "KA" else label(by[(arm, i, r)])
                wi = 1.0 if y == "PF" else w.get(i, 1.0)
                if y == "PF":
                    tp += p == PF
                    fn += p == TF
                else:
                    fp += p == PF
                    tn += p == TF
                    fpw += wi * (p == PF)
                    tnw += wi * (p == TF)
            rows.append((tp, fp, fn, tn, fpw, tnw))
        tp, fp, fn, tn, fpw, tnw = np.mean(rows, axis=0)
        rec = {"TP": tp, "FP": fp, "FN": fn, "TN": tn, "FP_natural": fpw, "TN_natural": tnw}
        if arm != "KA":
            rec.update(breakeven_vs_KA=tn / fn if fn else None, breakeven_vs_DA=fp / tp if tp else None,
                       breakeven_vs_KA_natural=tnw / fn if fn else None, breakeven_vs_DA_natural=fpw / tp if tp else None)
        out["D1"][arm] = rec

    # (D2) calibration + selective triage (tau tuned on dev)
    dev_samp = json.loads((config.PROCESSED / "sample_D1_dev_pilot.json").read_text(encoding="utf-8"))
    dev_ids = {i for i in dev_samp["instance_ids"] if lab_all.get(i, {}).get("label") in ("PF", "TF")}
    dev = [d for d in read_jsonl(DEV / "decisions.jsonl") if d["arm"] in ("J1", "SC", "DEB") and d["instance_id"] in dev_ids]
    tuned = {}
    for arm in ("J1", "SC", "DEB"):
        dd = [d for d in dev if d["arm"] == arm]
        scores = {t: f1([(lab_all[d["instance_id"]]["label"], selective(d, t)) for d in dd]) for t in TAUS}
        best = max(scores.values())
        tuned[arm] = max(t for t in TAUS if scores[t] == best)
        out["D2"].setdefault("dev_f1_by_tau", {})[arm] = scores
    out["D2"]["tau"] = tuned
    out["D2"]["dev_instances"] = len(dev_ids)
    ece = {}
    for arm in ("J1", "SC", "DEB"):
        xs = [(conf(d), label(d) == (PF if lab_all[d["instance_id"]]["label"] == "PF" else TF))
              for d in decs if d["arm"] == arm and conf(d) is not None]
        c = np.array([x[0] for x in xs])
        ok = np.array([x[1] for x in xs], dtype=float)
        bins = np.minimum((c * 10).astype(int), 9)
        e = sum(abs(ok[bins == b].mean() - c[bins == b].mean()) * (bins == b).sum() for b in range(10) if (bins == b).any()) / len(c)
        ece[arm] = {"ece": float(e), "n": len(c), "mean_confidence": float(c.mean()), "accuracy": float(ok.mean()),
                    "share_conf_ge_090": float((c >= 0.9).mean())}
    out["D2"]["calibration"] = ece

    # synthetic decision sets for the selective rule and the cascade, scored by the committed Evaluation
    extra = []
    for d in decs:
        tau = tuned[d["arm"]]
        extra.append({**d, "variant": "sel", "label_raw": selective(d, tau)})
    casc_tokens, esc = [], []
    for (a, i, r), d in by.items():
        if a != "SC":
            continue
        v = d["agreement"]["vote_share_pf"]
        e = any(abs(v - s) < 1e-9 for s in SPLIT)
        deb = by[("DEB", i, r)]
        pick = deb if e else d
        sc_c = d["cost"] if isinstance(d["cost"], dict) else json.loads(d["cost"])
        db_c = deb["cost"] if isinstance(deb["cost"], dict) else json.loads(deb["cost"])
        casc_tokens.append(sc_c["input_tokens"] + sc_c["output_tokens"] + (db_c["input_tokens"] + db_c["output_tokens"] if e else 0))
        esc.append(e)
        extra.append({**d, "arm": "SC", "variant": "cascade", "label_raw": pick["label_raw"]})
    ex = dict(excl)
    ex[("S1", "sel")] = s1_drop
    ex[("S1", "cascade")] = s1_drop
    ev = analysis.Evaluation(decs + extra, labels, w, exclusions=ex)
    for arm in ("J1", "SC", "DEB"):
        sel, base = f"{arm}|S1|sel", f"{arm}|S1"
        s, b = ev.summary(sel), ev.summary(base)
        c = vars(ev.contrast(f"{sel} - {base}", [sel], [base], "f1"))
        out["D2"].setdefault("selective", {})[arm] = {"tau": tuned[arm], "f1": s["f1"], "mcc": s["mcc"], "recall": s["recall"],
                                                      "precision": s["precision"], "pf_lost": s["pf_lost"], "parent_f1": b["f1"],
                                                      "parent_pf_lost": b["pf_lost"], "delta_f1": c["delta"], "delta_f1_ci95": c["ci95"],
                                                      "p": c["p"]}
    cs = ev.summary("SC|S1|cascade")
    sc_tok = np.mean([(lambda c: c["input_tokens"] + c["output_tokens"])(d["cost"] if isinstance(d["cost"], dict) else json.loads(d["cost"]))
                      for d in decs if d["arm"] == "SC"])
    deb_tok = np.mean([(lambda c: c["input_tokens"] + c["output_tokens"])(d["cost"] if isinstance(d["cost"], dict) else json.loads(d["cost"]))
                       for d in decs if d["arm"] == "DEB"])
    out["D3"] = {"split_vote_shares": list(SPLIT), "escalation_rate": float(np.mean(esc)), "f1": cs["f1"], "mcc": cs["mcc"],
                 "recall": cs["recall"], "precision": cs["precision"],
                 "tokens_per_instance": float(np.mean(casc_tokens)), "sc_tokens_per_instance": float(sc_tok),
                 "deb_tokens_per_instance": float(deb_tok), "sc_f1": ev.summary("SC|S1")["f1"], "deb_f1": ev.summary("DEB|S1")["f1"],
                 "vs_SC": vars(ev.contrast("cascade - SC", ["SC|S1|cascade"], ["SC|S1"], "f1")),
                 "vs_DEB": vars(ev.contrast("cascade - DEB", ["SC|S1|cascade"], ["DEB|S1"], "f1"))}

    # (D4) debate behaviour
    deb = [d for d in decs if d["arm"] == "DEB"]
    r1_all = [x for d in deb for x in d["agreement"].get("r1_concede", [])]
    r2_all = [x for d in deb for x in d["agreement"].get("r2_concede", [])]
    r1, r2 = [x for x in r1_all if x is not None], [x for x in r2_all if x is not None]   # None: invalid advocate output
    last = [d["agreement"]["sided_with_last_presented"] for d in deb if d["agreement"].get("sided_with_last_presented") is not None]
    bt = binomtest(sum(last), len(last), 0.5)
    flips = [(d, by[("SC", d["instance_id"], d["replicate"])]) for d in deb]
    diff = [(d, s) for d, s in flips if label(d) != label(s)]
    deb_right = sum(1 for d, _ in diff if (label(d) == PF) == (lab_all[d["instance_id"]]["label"] == "PF"))
    out["D4"] = {"concession_rate_r1": float(np.mean(r1)), "concession_rate_r2": float(np.mean(r2)), "n_advocate_outputs_r1": len(r1), "n_advocate_outputs_r2": len(r2), "advocate_outputs_without_concede_field": len(r1_all) - len(r1) + len(r2_all) - len(r2),
                 "last_presented_share": float(np.mean(last)), "last_presented_n": len(last), "last_presented_p": float(bt.pvalue),
                 "flip_rate_vs_sc_majority": len(diff) / len(flips), "flips": len(diff), "deb_correct_share_among_flips": deb_right / len(diff) if diff else None,
                 "deb_flips_to_pf": sum(1 for d, _ in diff if label(d) == PF), "deb_flips_to_tf": sum(1 for d, _ in diff if label(d) == TF)}
    dump_json(OUT, out)
    print(json.dumps({k: out[k] for k in ("D1",)}, indent=0, default=float)[:900])
    print("tau", tuned, "ECE", {a: round(v["ece"], 3) for a, v in ece.items()})
    print("selective", {a: (round(v["f1"], 3), round(v["delta_f1"], 3), [round(x, 3) for x in v["delta_f1_ci95"]]) for a, v in out["D2"]["selective"].items()})
    print("cascade", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in out["D3"].items() if not k.startswith("vs_")},
          round(out["D3"]["vs_SC"]["delta"], 3), [round(x, 3) for x in out["D3"]["vs_SC"]["ci95"]], round(out["D3"]["vs_DEB"]["delta"], 3))
    print("D4", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in out["D4"].items()})


if __name__ == "__main__":
    main()
