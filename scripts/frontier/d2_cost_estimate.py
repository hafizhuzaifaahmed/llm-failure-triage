"""Cost estimate for a possible E9 follow-up (a decision for the authors; nothing is called): Claude Sonnet 5.5, J1 and
DEB at S1, one replicate each, on the D2 seeded-fault set, as a memorisation check for the frontier result.

Basis, all measured: the E9 call log (data/raw/llm_calls_frontier/claude-sonnet-5-5.jsonl, batch usage per call) gives
the cost per instance and replicate of each arm on D1-test; the frozen M1 runs give the ratio of tokens consumed per
instance on D2 to D1 for the same arm, which scales the Sonnet cost to D2's prompts.

    python scripts/frontier/d2_cost_estimate.py   -> results/e9/d2_cost_estimate.json
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from triage.io_utils import dump_json  # noqa: E402

LOG = ROOT / "data" / "raw" / "llm_calls_frontier" / "claude-sonnet-5-5.jsonl"
AF = ROOT / "results" / "heldout" / "analysis_final"
E9_INSTANCES, E9_REPS = 177, {"J1": 1, "DEB": 3}


def consumed(dataset, arm):
    with open(AF / f"{dataset}_M1" / "tables" / "conditions.csv", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["condition"] == f"{arm}|S1":
                return float(r["consumed_tokens_per_instance"]), int(float(r["n_instances"]))
    raise KeyError(arm)


def main():
    cost, calls, tin, tout = defaultdict(float), defaultdict(int), defaultdict(int), defaultdict(int)
    with open(LOG, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            arm = r["tag"].split("|")[0]
            cost[arm] += r["cost_usd"] or 0
            calls[arm] += 1
            tin[arm] += r["input_tokens"] or 0
            tout[arm] += r["output_tokens"] or 0
    out = {"basis": "E9 batch usage per call (measured) scaled by the M1 D2/D1 tokens-per-instance ratio",
           "model": "claude-sonnet-5-5", "pricing": "Message Batches API, USD 1 / 5 per million input / output tokens",
           "plan": "J1 and DEB at S1, one replicate each, D2", "arms": {}}
    total = 0.0
    for arm in ("J1", "DEB"):
        per = cost[arm] / (E9_INSTANCES * E9_REPS[arm])
        d1_tok, _ = consumed("D1", arm)
        d2_tok, n_d2 = consumed("D2", arm)
        ratio = d2_tok / d1_tok
        est = per * ratio * n_d2
        total += est
        out["arms"][arm] = {"e9_calls": calls[arm], "e9_cost_usd": round(cost[arm], 4),
                            "e9_input_tokens": tin[arm], "e9_output_tokens": tout[arm],
                            "e9_cost_per_instance_replicate_usd": round(per, 5),
                            "m1_tokens_per_instance_d1": d1_tok, "m1_tokens_per_instance_d2": d2_tok,
                            "d2_over_d1_ratio": round(ratio, 3), "d2_instances": n_d2, "estimate_usd": round(est, 2)}
    out["estimate_usd"] = round(total, 2)
    out["with_30pct_margin_usd"] = round(total * 1.3, 2)
    out["suggested_console_limit_usd"] = int(total * 1.3) + 2
    out["needs"] = "a new API key (the E9 key is to be revoked) and a raised Console limit; D-entry with H9-3 before any call"
    dump_json(ROOT / "results" / "e9" / "d2_cost_estimate.json", out)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
