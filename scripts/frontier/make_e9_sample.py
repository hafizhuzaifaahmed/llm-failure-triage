"""The E9 sample (D-92, D-96): the D1-test instances that are scored at S1, so no paid call is spent on an instance the
analysis never scores. Scored = in the committed D1-test sample, labelled PF or TF (AMB is never scored), and not
aborted by the S1 leakage guard in M1's run (D-70). Labels are read only to drop AMB.

    python scripts/frontier/make_e9_sample.py   -> data/processed/sample_D1_test_E9_scored.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

OUT = config.PROCESSED / "sample_D1_test_E9_scored.json"


def main():
    samp = json.loads((config.PROCESSED / "sample_D1_test.json").read_text(encoding="utf-8"))
    lab = {l["instance_id"]: l["label"] for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl")}
    aborted = {r["instance_id"] for r in read_jsonl(ROOT / "results" / "runs_local" / "LOCAL_HO_E1E3_M1" / "leakage_rejections.jsonl")
               if r.get("level") == "S1"}
    ids = sorted(i for i in samp["instance_ids"] if lab.get(i) in ("PF", "TF") and i not in aborted)
    dump_json(OUT, {"what": "E9 sample: the scored D1-test instances at S1 (D-96)", "source": "sample_D1_test.json",
                    "instance_ids": ids, "n": len(ids), "excluded_amb": sum(lab.get(i) == "AMB" for i in samp["instance_ids"]),
                    "excluded_aborted": len(aborted & set(samp["instance_ids"])), "tf_weights": samp.get("tf_weights")})
    print(len(ids))


if __name__ == "__main__":
    main()
