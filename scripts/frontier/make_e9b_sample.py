"""The E9b sample (D-104): the D2 test instances that M1 scored at S1, so no paid call is spent on an instance the
analysis never scores. Scored = in the committed D2 test sample, labelled PF or TF (AMB is never scored), and not
aborted by the S1 leakage guard in M1's committed D2 run (LOCAL_HO_E5R1_D2, D-70). Labels are read only to drop AMB.

    python scripts/frontier/make_e9b_sample.py   -> data/processed/sample_D2_test_E9B_scored.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

OUT = config.PROCESSED / "sample_D2_test_E9B_scored.json"
M1_RUN = ROOT / "results" / "runs_local" / "LOCAL_HO_E5R1_D2"


def main():
    samp = json.loads((config.PROCESSED / "sample_D2_test.json").read_text(encoding="utf-8"))
    lab = {l["instance_id"]: l["label"] for l in read_jsonl(config.GT_STORE / "labels_D2.jsonl")}
    aborted = {r["instance_id"] for r in read_jsonl(M1_RUN / "leakage_rejections.jsonl") if r.get("level") == "S1"}
    ids = sorted(i for i in samp["instance_ids"] if lab.get(i) in ("PF", "TF") and i not in aborted)
    dump_json(OUT, {"what": "E9b sample: the scored D2 test instances at S1 (D-104)", "source": "sample_D2_test.json",
                    "dataset": "D2", "split": "test", "instance_ids": ids, "n": len(ids),
                    "excluded_amb": sum(lab.get(i) == "AMB" for i in samp["instance_ids"]),
                    "excluded_aborted": len(aborted & set(samp["instance_ids"])), "tf_weights": samp.get("tf_weights")})
    print(len(ids))


if __name__ == "__main__":
    main()
