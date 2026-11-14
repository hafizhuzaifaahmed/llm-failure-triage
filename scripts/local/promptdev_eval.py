"""Evaluate one prompt-development round (D-33). Dev pilot only — not a result.

    python scripts/local/promptdev_eval.py --run results/dev/PROMPTDEV_v0

Per condition (J1|S1, J1|S2, DEB|S1): schema validity (DEB counts advocate outputs too, as in G-a), the D-39
runaway count, PF precision / recall / F1 / MCC with bug-level cluster-bootstrap CIs, and the confusion matrix.
Writes <run>/round_eval.json. The D-33 trigger and stop rules are applied by reading these numbers; nothing here
changes a prompt.
"""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import analysis, config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

_spec = importlib.util.spec_from_file_location("dev_gates", ROOT / "scripts" / "local" / "dev_gates.py")
dev_gates = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dev_gates)

KEEP = ("n_instances", "precision", "precision_ci95", "recall", "recall_ci95", "f1", "f1_ci95", "mcc", "mcc_ci95",
        "fpr", "fnr", "TP", "FP", "FN", "TN", "invalid_rate")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    run = Path(a.run)
    decisions = list(read_jsonl(run / "decisions.jsonl"))
    sample = json.loads((config.PROCESSED / "sample_D1_dev_pilot.json").read_text())
    keep = set(sample["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl") if l["instance_id"] in keep and l["split"] == "dev"]
    judged = {d["instance_id"] for d in decisions}
    labels = [l for l in labels if l["instance_id"] in judged]      # leakage-rejected instances leave every arm
    ev = analysis.Evaluation(decisions, labels, sample["tf_weights"])
    out = {"run": str(run), "prompt_set": json.loads((run / "experiment.json").read_text()).get("prompt_set"),
           "n_labelled_instances": len(labels), "note": "DEV PILOT — prompt development, not a result",
           "conditions": {}}
    for cond in sorted(ev.by_cond):
        # validity over EVERY judged decision of the condition, AMB included, exactly as G-a counts it (D-47);
        # ev.by_cond only holds the PF/TF instances that enter the metrics
        ds = [d for d in decisions if analysis.cond_name(d) == cond]
        s = ev.summary(cond)
        arm = ds[0]["arm"]
        if arm == "DEB":
            bad = sum((d["label_raw"] == "INVALID") + d["agreement"].get("invalid_advocate_outputs", 0) for d in ds)
            valid = 1 - bad / (5 * len(ds))
        else:
            valid = 1 - sum(d["label_raw"] == "INVALID" for d in ds) / len(ds)
        out["conditions"][cond] = {"valid_rate": valid, "runaway_D39": dev_gates.runaway_counts(ds).get(arm),
                                   **{k: s.get(k) for k in KEEP}}
    dump_json(run / "round_eval.json", out)
    for c, v in out["conditions"].items():
        print(f"{c:8s} valid={v['valid_rate']:.3f} F1={v['f1']:.3f} {v['f1_ci95']} P={v['precision']:.3f} "
              f"R={v['recall']:.3f} MCC={v['mcc']:.3f} TP={v['TP']} FP={v['FP']} FN={v['FN']} TN={v['TN']} "
              f"runaway={v['runaway_D39']}")


if __name__ == "__main__":
    main()
