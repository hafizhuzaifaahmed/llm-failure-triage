"""Seeded selection of the label-audit rubric examples and calibration instances (D-82; no model call).

Both come from the D1-test judged sample, which is disjoint from the 71-instance audit sample (development split):
rubric examples 2 PF / 2 TF / 2 AMB, then calibration 4 PF / 4 TF / 2 AMB from the remainder. Sorted by instance id
and drawn with one `random.Random(20261103)` stream, so the choice involves no judgement about content.

    python scripts/audit/select_audit_examples.py   -> data/ground_truth_store/audit/audit_examples_selection.json
"""
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

SEED = 20261103
RUBRIC = {"PF": 2, "TF": 2, "AMB": 2}
CALIB = {"PF": 4, "TF": 4, "AMB": 2}


def main():
    samp = json.loads((config.PROCESSED / "sample_D1_test.json").read_text(encoding="utf-8"))
    lab = {l["instance_id"]: l["label"] for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl")}
    audit_ids = {r.split(",")[1] for r in (config.GT_STORE / "audit" / "label_audit_key.csv").read_text(encoding="utf-8-sig").splitlines()[1:] if r}
    pool = {c: sorted(i for i in samp["instance_ids"] if lab.get(i) == c and i not in audit_ids) for c in ("PF", "TF", "AMB")}
    rng = random.Random(SEED)
    rubric = {c: rng.sample(pool[c], n) for c, n in RUBRIC.items()}
    rest = {c: [i for i in pool[c] if i not in rubric[c]] for c in pool}
    calib = {c: rng.sample(rest[c], n) for c, n in CALIB.items()}
    out = {"seed": SEED, "source": "D1-test judged sample, excluding the 71-instance audit sample", "rubric": rubric,
           "calibration": calib}
    dump_json(config.GT_STORE / "audit" / "audit_examples_selection.json", out)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
