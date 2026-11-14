"""KUU-NG member votes (POST HOC, descriptive; written after the D-109 analysis was run).

For each member of the original KUU panel (M1, M2, E6b) and of KUU-NG (M1, E6b, llama3.1), on the D-109 instance set:
share of TEST_FAULT votes, miss rate on PF (TEST_FAULT vote on a PROGRAM_FAULT instance) and recall on TF.
It answers whether KUU-NG's protection again rests on one judge that rarely votes TEST_FAULT. No test.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

from triage import config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

import kuung_analysis as kn  # noqa: E402

OUT = ROOT / "results" / "kuung" / "analysis" / "kuung_members.json"


def rates(votes: dict, gold: dict, ids, m: str) -> dict:
    v = [(votes.get(i, {}).get(m), gold[i]) for i in ids]
    pf = [x for x, g in v if g == "PF"]
    tf = [x for x, g in v if g == "TF"]
    return {"share_tf_votes": sum(x == kn.TF for x, _ in v) / len(v),
            "miss_rate_on_pf": sum(x == kn.TF for x in pf) / len(pf) if pf else None,
            "recall_on_tf": sum(x == kn.TF for x in tf) / len(tf) if tf else None,
            "invalid": sum(x not in (kn.TF, kn.PF) for x, _ in v)}


def main():
    res = json.loads(kn.OUT.read_text(encoding="utf-8"))
    out = {"status": "post hoc, descriptive (written after the D-109 analysis)"}
    for ds, plan in kn.PLAN.items():
        ng = kn.votes_of(plan["ng"], 30)
        orig = kn.votes_of(plan["orig"]["members"], plan["orig"]["replicate"])
        samp = json.loads((config.PROCESSED / plan["sample"]).read_text(encoding="utf-8"))
        keep = set(samp["instance_ids"])
        gold = {l["instance_id"]: l["label"] for l in read_jsonl(config.GT_STORE / plan["labels"])
                if l["instance_id"] in keep}
        ids = sorted(i for i in keep if len(ng.get(i, {})) == 3 and len(orig.get(i, {})) == 3
                     and gold.get(i) in ("TF", "PF"))
        out[ds] = {"n": len(ids), "n_reported_by_d109": res[ds]["n_instances"],
                   "kuung": {m: rates(ng, gold, ids, m) for m in ("M1", "E6B", "NG")},
                   "kuu": {m: rates(orig, gold, ids, m) for m in ("M1", "M2", "E6B")}}
        print(ds, out[ds]["n"])
        for panel in ("kuu", "kuung"):
            for m, r in out[ds][panel].items():
                print(f"  {panel:5s} {m:4s} TF-share {r['share_tf_votes']:.3f} PF-miss {r['miss_rate_on_pf']:.3f}"
                      f" TF-recall {r['recall_on_tf']:.3f} invalid {r['invalid']}")
    dump_json(OUT, out)


if __name__ == "__main__":
    main()
