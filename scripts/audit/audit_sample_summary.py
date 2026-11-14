"""Counts that describe the label-audit sample (D-45), for the paper's numbers map. No rater sheet is read.

The audit sample is every PF and a seeded 50 of the TF instances of the labelled D1 development split (AMB excluded):
this script only counts the committed key against the committed labels.

    python scripts/audit/audit_sample_summary.py   -> data/ground_truth_store/audit/audit_sample_summary.json
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

OUT = config.GT_STORE / "audit" / "audit_sample_summary.json"


def main():
    key = list(csv.DictReader((config.GT_STORE / "audit" / "label_audit_key.csv").open(encoding="utf-8-sig")))
    labels = {l["instance_id"]: l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl")}
    dev = Counter(l["label"] for l in labels.values() if l["split"] == "dev")
    items = [labels[r["instance_id"]] for r in key]
    out = {"what": "label-audit sample (D-45): counts only", "n_items": len(key),
           "splits": dict(Counter(l["split"] for l in items)), "labels": dict(Counter(r["auto_label"] for r in key)),
           "projects": dict(Counter(l["project"] for l in items)),
           "dev_split_labels": dict(dev), "held_out_items": sum(l["split"] != "dev" for l in items)}
    dump_json(OUT, out)
    print(out)


if __name__ == "__main__":
    main()
