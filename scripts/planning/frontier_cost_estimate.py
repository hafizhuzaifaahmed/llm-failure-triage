"""Frontier-judge cost ESTIMATE only (D-82): nothing is called, and the study's zero-API-cost rule stands unless the
authors decide otherwise.

Tokens per instance are the measured J1 and DEB means from the call log (cost_latency_s1.json, M1's tokenizer); the
D1-test scored set is the 177 instances. List prices are Anthropic's published standard and Batch API rates, read from
the pricing page on the access date below (recorded here as data, with their source). Caveats carried into the output:
a different tokenizer changes the counts, and these models bill thinking tokens as output (thinking cannot be fully
disabled on Claude Opus 5.5 or Claude Sonnet 5.5), which this estimate does not include.

    python scripts/planning/frontier_cost_estimate.py   -> results/planning/frontier_cost_estimate.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COST = ROOT / "results" / "heldout" / "analysis_final" / "D1_M1" / "tables" / "cost_latency_s1.json"
OUT = ROOT / "results" / "planning" / "frontier_cost_estimate.json"
PRICES = {  # USD per million tokens, standard / batch; source and access date below
    "claude-fable-5-1": {"input": 10.0, "output": 50.0, "batch_input": 5.0, "batch_output": 25.0},
    "claude-opus-5-5": {"input": 4.0, "output": 20.0, "batch_input": 2.0, "batch_output": 10.0},
    "claude-sonnet-5-5": {"input": 2.0, "output": 10.0, "batch_input": 1.0, "batch_output": 5.0},
}
SOURCE = {"url": "https://platform.claude.com/docs/en/about-claude/pricing", "accessed": "2026-11-03",
          "note": "standard base input/output rates; Batch API rates are 50% of standard on both"}


def main():
    c = json.loads(COST.read_text(encoding="utf-8"))
    n = c["scored_instances"]
    tok = {a: (c["arms"][a]["input_tokens_per_instance"], c["arms"][a]["output_tokens_per_instance"]) for a in ("J1", "DEB")}
    rows = {}
    for m, p in PRICES.items():
        per = {a: (i * p["input"] + o * p["output"]) / 1e6 for a, (i, o) in tok.items()}
        per_b = {a: (i * p["batch_input"] + o * p["batch_output"]) / 1e6 for a, (i, o) in tok.items()}
        one = n * (per["J1"] + per["DEB"])
        rows[m] = {"usd_per_instance_J1": per["J1"], "usd_per_instance_DEB": per["DEB"],
                   "usd_one_replicate": one, "usd_three_replicates": 3 * one,
                   "usd_one_replicate_batch": n * (per_b["J1"] + per_b["DEB"]),
                   "usd_three_replicates_batch": 3 * n * (per_b["J1"] + per_b["DEB"]), **{f"price_{k}": v for k, v in p.items()}}
    out = {"what": "frontier-judge cost estimate, J1 + DEB on the D1-test scored set (D-82); nothing called", "scored_instances": n,
           "tokens_per_instance_measured_M1": {a: {"input": i, "output": o} for a, (i, o) in tok.items()},
           "price_source": SOURCE, "models": rows,
           "caveats": ["token counts measured with M1's tokenizer; a Claude tokenizer gives different counts",
                       "thinking tokens are billed as output and are not included (not fully disableable on Opus 5.5 / Sonnet 5.5)",
                       "zero-API-cost rule: running this needs the authors' explicit decision; nothing is called"]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for m, r in rows.items():
        print(m, round(r["usd_one_replicate"], 2), round(r["usd_three_replicates"], 2), "batch", round(r["usd_one_replicate_batch"], 2))


if __name__ == "__main__":
    main()
