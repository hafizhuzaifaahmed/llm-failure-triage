"""D-64 report for the D2 sample, to be stated alongside the D2 results (evaluation side: reads the label store).

    python scripts/analysis/d2_sample_report.py

Reports (1) how many D2 units and instances existed before the cap (units with >= 1 triage instance, labelled
instances by class, the uncapped C9 sample size), (2) the realised PF:TF ratio and AMB count in the judged sample,
and (3) the share of judged instances from the largest base bug, since the bootstrap clusters on base bug.
Writes results/heldout/d2_sample_report.json.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage.dataset import allocate  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

CAP = 300   # D-64


def report(labels: list[dict], samp: dict, n_units_total: int) -> dict:
    by_id = {l["instance_id"]: l for l in labels}
    judged = [by_id[i] for i in samp["instance_ids"]]
    uncapped = allocate(labels, mode=samp["mode"], ratio=samp["ratio"], seed=samp["seed"], cap=None)
    cls = Counter(l["label"] for l in judged)
    bugs = Counter(l["bug_name"] for l in judged)
    top_bug, top_n = bugs.most_common(1)[0] if bugs else (None, 0)
    return {
        "before_cap": {"d2_units_total": n_units_total,
                       "units_with_a_triage_instance": len({l["focal_id"] for l in labels}),
                       "labelled_instances": dict(Counter(l["label"] for l in labels)),
                       "c9_sample_size_uncapped": len(uncapped["instance_ids"])},
        "judged_sample": {"n": len(judged), "capped": samp["capped"], "cap": samp.get("cap"), "seed": samp["seed"],
                          "mode": samp["mode"], "by_class": dict(cls),
                          "realised_tf_per_pf": (cls["TF"] / cls["PF"]) if cls["PF"] else None},
        "clustering": {"base_bugs": len(bugs), "largest_base_bug": top_bug, "largest_base_bug_instances": top_n,
                       "largest_base_bug_share": top_n / len(judged) if judged else None},
    }


def main():
    labels = [l for l in read_jsonl(config.GT_STORE / "labels_D2.jsonl") if l["split"] == "test"]
    samp = json.loads((config.PROCESSED / "sample_D2_test.json").read_text(encoding="utf-8"))
    n_units = len(list((config.INTERIM / "context_D2").glob("*.json")))
    out = report(labels, samp, n_units)
    dump_json(config.ROOT / "results" / "heldout" / "d2_sample_report.json", out)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
