"""Judge dev gates (MODEL_SELECTION_PROTOCOL Step 4 with D-23) and gate P4 (k_T). Dev pilot only — not a result.

    python scripts/local/dev_gates.py --run results/dev/GATE_M1 [--required a,b,c,d]

G-a  >= 98% schema-valid outputs per arm (J1, SC samples, DEB incl. advocates) after the one repair parse
G-b  >= 90% of valid decisions cite >= 1 evidence id, and >= 95% of cited ids exist in the package
G-c  dev J1 PF-F1 within [0.2, 0.9]
G-d  dev J1 PF-F1 point estimate > max(F1_KA, F1_R0); bug-level cluster-bootstrap CI of the difference reported (D-23)
D-39 runaway rate: INVALID outputs that hit num_predict (finish_reason = length) — the J11 failure mode — per arm
P4   k_T = smallest odd k with k x (mean J1 consumed tokens per call) >= mean DEB consumed tokens per instance
"""
import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import analysis, config, stats  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402
from triage.ollama import ADVOCATE_ROLES, LOCAL_CALL_LOG_DIR  # noqa: E402
from triage.schema import parse_output  # noqa: E402


def runaway_counts(decisions, log_dir=LOCAL_CALL_LOG_DIR):
    """D-39: per arm, calls whose output is INVALID and stopped at num_predict (the J11 failure mode)."""
    keys = {k for d in decisions for k in (d.get("cost") or {}).get("call_keys", [])}
    calls = {}
    for f in Path(log_dir).glob("*.jsonl"):
        if f.name.startswith("_"):
            continue
        for r in read_jsonl(f):
            if r["key"] in keys:
                calls[r["key"]] = r
    out = {}
    for d in decisions:
        arm = d["arm"]
        o = out.setdefault(arm, {"calls": 0, "invalid": 0, "invalid_length": 0})
        for k in (d.get("cost") or {}).get("call_keys", []):
            r = calls.get(k)
            if r is None:
                continue
            kind = "advocate" if r["role"] in ADVOCATE_ROLES else "judge"
            bad = not parse_output(r["text"], kind).ok
            o["calls"] += 1
            o["invalid"] += bad
            o["invalid_length"] += bad and r.get("finish_reason") == "length"
    for o in out.values():
        o["runaway_rate"] = o["invalid_length"] / o["calls"] if o["calls"] else None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--required", default="a,b,c,d")
    ap.add_argument("--baselines-from", help="take the model-free DA/KA/R0 decisions from another run (M2 check)")
    ap.add_argument("--call-log-dir", help="call log of a profile model (D-82 E6b); default: the frozen call log")
    a = ap.parse_args()
    run = Path(a.run)
    decisions = list(read_jsonl(run / "decisions.jsonl"))
    if a.baselines_from:
        have = {d["arm"] for d in decisions}
        decisions += [d for d in read_jsonl(Path(a.baselines_from) / "decisions.jsonl")
                      if d["arm"] in ("DA", "KA", "R0") and d["arm"] not in have]
    sample = json.loads((config.PROCESSED / "sample_D1_dev_pilot.json").read_text())
    keep = set(sample["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl") if l["instance_id"] in keep and l["split"] == "dev"]
    rej = run / "leakage_rejections.jsonl"
    rejections = list(read_jsonl(rej)) if rej.exists() else []
    ev = analysis.Evaluation(decisions, labels, sample["tf_weights"],
                             exclusions=analysis.abort_exclusions(rejections))   # D-70 / D-86
    out = {"run": str(run), "n_instances": len(ev.lab), "n_bugs": len(ev.bugs),
           "leakage_aborts": sorted({(r["arm"], r["instance_id"]) for r in rejections}),
           "label_counts": {k: sum(1 for l in labels if l["label"] == k) for k in ("PF", "TF", "AMB")},
           "note": "DEV PILOT — gate check, not a research result"}

    def arm(name):
        return [d for d in decisions if d["arm"] == name and d.get("level") in (None, "S1")
                and (d.get("variant") or "full") == "full"]
    # G-a
    j1, sc, deb = arm("J1"), arm("SC"), arm("DEB")
    va = {}
    if j1:
        va["J1"] = 1 - sum(d["label_raw"] == "INVALID" for d in j1) / len(j1)
    if sc:
        va["SC"] = 1 - sum(d.get("invalid_samples", 0) for d in sc) / sum(d["agreement"]["k"] for d in sc)
    if deb:
        bad = sum((d["label_raw"] == "INVALID") + d["agreement"].get("invalid_advocate_outputs", 0) for d in deb)
        va["DEB"] = 1 - bad / (5 * len(deb))
    out["G_a_valid_rate"] = va
    out["G_a"] = bool(va) and all(v >= 0.98 for v in va.values())
    out["G_a_runaway_D39"] = runaway_counts(j1 + sc + deb, **({"log_dir": Path(a.call_log_dir)} if a.call_log_dir else {}))
    # G-b
    gb = {}
    for nm, ds in (("J1", j1), ("SC", sc), ("DEB", deb)):
        valid = [d for d in ds if d["label_raw"] != "INVALID"]
        if not valid:
            continue
        cite = sum(bool(d.get("evidence_ids")) for d in valid) / len(valid)
        good = sum(len(d.get("evidence_ids") or []) for d in valid)
        badc = sum(len(d.get("invalid_evidence_ids") or []) for d in valid)
        gb[nm] = {"cite_rate": cite, "cited_ids_exist_rate": good / (good + badc) if good + badc else 1.0}
    out["G_b_citations"] = gb
    out["G_b"] = bool(gb) and all(v["cite_rate"] >= 0.90 and v["cited_ids_exist_rate"] >= 0.95 for v in gb.values())
    # metrics with CIs
    summ = {c: ev.summary(c) for c in ev.by_cond}
    keep_keys = ("precision", "precision_ci95", "recall", "recall_ci95", "f1", "f1_ci95", "mcc", "mcc_ci95", "fpr",
                 "fnr", "TP", "FP", "FN", "TN", "invalid_rate", "n_instances")
    out["metrics"] = {c: {k: s.get(k) for k in keep_keys} for c, s in summ.items()}
    f1 = lambda c: summ[c]["f1"] if c in summ else math.nan
    out["G_c"] = 0.2 <= f1("J1|S1") <= 0.9
    best = "KA" if f1("KA") >= f1("R0") else "R0"
    con = ev.contrast(f"J1|S1 - {best}", ["J1|S1"], [best], "f1")
    mcc = lambda c: summ[c]["mcc"] if c in summ else math.nan
    out["G_d_detail"] = {"J1_f1": f1("J1|S1"), "KA_f1": f1("KA"), "R0_f1": f1("R0"), "best_trivial": best,
                         "J1_mcc": mcc("J1|S1"), "KA_mcc": mcc("KA"), "R0_mcc": mcc("R0"),
                         "delta": con.delta, "delta_ci95_bug_bootstrap": con.ci95,
                         "rule": "D-23: point estimate must exceed max(F1_KA, F1_R0); CI reported, not required"}
    out["G_d"] = f1("J1|S1") > max(f1("KA"), f1("R0"))
    # P4 / k_T
    if j1 and deb:
        j1_tok = sum(d["cost"]["input_tokens"] + d["cost"]["output_tokens"] for d in j1) / len(j1)
        deb_tok = sum(d["cost"]["input_tokens"] + d["cost"]["output_tokens"] for d in deb) / len(deb)
        sc_tok = (sum(d["cost"]["input_tokens"] + d["cost"]["output_tokens"] for d in sc) / len(sc)) if sc else None
        k = 1
        while k * j1_tok < deb_tok:
            k += 2 if k > 1 else 2
        k = k if k % 2 == 1 else k + 1
        out["P4"] = {"J1_tokens_per_call": j1_tok, "SC_tokens_per_instance": sc_tok, "DEB_tokens_per_instance": deb_tok,
                     "k_T": k, "note": "tokens = prompt_eval_count (includes cached prefix, D-37) + eval_count"}
    req = set(a.required.split(","))
    out["required"] = sorted(req)
    out["passes_required"] = all(out[f"G_{g}"] for g in req)
    dump_json(run / "dev_gates.json", out)
    print(json.dumps({k: out[k] for k in ("n_instances", "label_counts", "G_a_valid_rate", "G_a", "G_a_runaway_D39", "G_b_citations",
                                           "G_b", "G_c", "G_d", "G_d_detail", "passes_required")}, indent=1, default=str))
    if "P4" in out:
        print(json.dumps(out["P4"], indent=1))
    for c, m in out["metrics"].items():   # F1 always next to MCC (D-51)
        print(f"{c:8s} F1 {m['f1']:.3f} {m['f1_ci95']}  MCC {m['mcc']:.3f} {m['mcc_ci95']}")


if __name__ == "__main__":
    main()
