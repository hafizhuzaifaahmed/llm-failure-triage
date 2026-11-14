"""Frontier-judge all-arms cost ESTIMATE (D-92; queue item 10): nothing is called.

Same method and prices as frontier_cost_estimate.py (imported, so the two cannot drift), applied to every primary
condition rather than J1 + DEB only. Tokens per instance are M1's measured means per condition from the committed
D1-test table (`conditions.csv`, call-log based, M1's tokenizer); the scored set is the 177 S1 instances. Scopes:
  s1_three_arms   J1, SC, DEB at S1                         (E3 core)
  grid            J1, SC, DEB at S0, S1, S2 and SC-T at S1   (E1-E3 grid)
each at one replicate and at three, standard and Batch API rates. Thinking tokens bill as output and are not in M1's
counts; a sensitivity line doubles every output count (an assumption, not a measurement).

    python scripts/planning/frontier_cost_all_arms.py   -> results/planning/frontier_cost_all_arms.json
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "planning"))

import frontier_cost_estimate as base  # noqa: E402

TABLE = ROOT / "results" / "heldout" / "analysis_final" / "D1_M1" / "tables" / "conditions.csv"
OUT = ROOT / "results" / "planning" / "frontier_cost_all_arms.json"
SCOPES = {"s1_three_arms": ["J1|S1", "SC|S1", "DEB|S1"],
          "grid": [f"{a}|{lv}" for a in ("J1", "SC", "DEB") for lv in ("S0", "S1", "S2")] + ["SC-T|S1"]}


def main():
    rows = {r["condition"]: r for r in csv.DictReader(TABLE.open(encoding="utf-8"))}
    n = json.loads(base.COST.read_text(encoding="utf-8"))["scored_instances"]
    tok = {c: (float(rows[c]["input_tokens_per_instance"]), float(rows[c]["output_tokens_per_instance"]))
           for s in SCOPES.values() for c in s}
    out = {"what": "frontier-judge all-arms cost estimate (D-92); nothing called", "scored_instances": n,
           "tokens_per_instance_measured_M1": {c: {"input": i, "output": o} for c, (i, o) in tok.items()},
           "price_source": base.SOURCE, "scopes": SCOPES, "models": {}}
    for m, p in base.PRICES.items():
        r = {}
        for name, conds in SCOPES.items():
            std = n * sum(i * p["input"] + o * p["output"] for i, o in (tok[c] for c in conds)) / 1e6
            bat = n * sum(i * p["batch_input"] + o * p["batch_output"] for i, o in (tok[c] for c in conds)) / 1e6
            bat2 = n * sum(i * p["batch_input"] + 2 * o * p["batch_output"] for i, o in (tok[c] for c in conds)) / 1e6
            r[name] = {"usd_one_replicate": std, "usd_three_replicates": 3 * std, "usd_one_replicate_batch": bat,
                       "usd_three_replicates_batch": 3 * bat, "usd_one_replicate_batch_output_x2": bat2,
                       "usd_three_replicates_batch_output_x2": 3 * bat2}
        out["models"][m] = r
    out["caveats"] = base.json.loads(base.OUT.read_text(encoding="utf-8"))["caveats"] + [
        "output_x2 is a sensitivity assumption for thinking tokens, not a measurement"]
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for m, r in out["models"].items():
        print(m, {k: (round(v["usd_one_replicate_batch"], 2), round(v["usd_three_replicates_batch"], 2),
                      round(v["usd_three_replicates_batch_output_x2"], 2)) for k, v in r.items()})


if __name__ == "__main__":
    main()
