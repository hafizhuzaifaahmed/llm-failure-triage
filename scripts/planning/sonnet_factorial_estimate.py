"""Planning only (D-128; nothing is called): cost of the specification x architecture factorial with Claude Sonnet 5.5
as the judge on D1-test (S0/S1/S2 x J1/SC/DEB, three replicates), from MEASURED usage only.

Measured: E9's logged batch cost per decision at S1 (J1, DEB) on D1-test. Estimated: SC = five J1-prompt samples; S0 and
S2 scaled from S1 by M1's measured consumed-token ratio per arm and level (the package grows with the specification);
the development-gate check on the dev pilot (63 instances) at S1 for J1, SC and DEB. The prices embedded in the logged
cost are those of the run date; they must be re-verified before any call.

    python scripts/planning/sonnet_factorial_estimate.py  -> results/planning/sonnet_factorial_estimate.json
"""
import ast
import csv
import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "planning" / "sonnet_factorial_estimate.json"
E9 = ROOT / "results" / "runs_frontier" / "E9_SONNET55_D1TEST" / "decisions.jsonl"
COND = ROOT / "results" / "heldout" / "analysis_final" / "D1_M1" / "tables" / "conditions.csv"
N_TEST, N_DEV, REPS = 177, 63, 3
MARGIN = 0.30


def cost(d):
    c = d.get("cost")
    return (ast.literal_eval(c) if isinstance(c, str) else c) or {}


def main():
    rows = [json.loads(l) for l in open(E9, encoding="utf-8")]
    per = {a: st.mean(cost(d).get("cost_usd", 0.0) for d in rows if d["arm"] == a) for a in ("J1", "DEB")}
    spent = {a: sum(cost(d).get("cost_usd", 0.0) for d in rows if d["arm"] == a) for a in ("J1", "DEB")}
    T = {r["condition"]: r for r in csv.DictReader(open(COND, encoding="utf-8"))}
    ratio = {a: {lv: float(T[f"{a}|{lv}"]["consumed_tokens_per_instance"]) / float(T[f"{a}|S1"]["consumed_tokens_per_instance"])
                 for lv in ("S0", "S1", "S2")} for a in ("J1", "SC", "DEB")}
    unit = {"J1": per["J1"], "SC": 5 * per["J1"], "DEB": per["DEB"]}
    cells, total = {}, 0.0
    for a in ("J1", "SC", "DEB"):
        for lv in ("S0", "S1", "S2"):
            c = unit[a] * ratio[a][lv] * N_TEST * REPS
            cells[f"{a}|{lv}"] = round(c, 2)
            total += c
    reusable = spent["DEB"] + spent["J1"]           # E9 already holds S1 DEB x3 and S1 J1 x1 on the same instances
    gate = sum(unit[a] for a in ("J1", "SC", "DEB")) * N_DEV
    new = total - reusable + gate
    res = {"what": "Sonnet 5.5 factorial cost estimate (planning, nothing called; D-128)",
           "measured": {"e9_usd_per_decision_S1": per, "e9_spent_usd": spent,
                        "source": "results/runs_frontier/E9_SONNET55_D1TEST/decisions.jsonl (logged batch cost)"},
           "estimated": {"sc_rule": "5 x J1 cost", "level_scaling": ratio, "cells_usd": cells,
                         "full_factorial_usd": round(total, 2), "reusable_from_e9_usd": round(reusable, 2),
                         "dev_gate_check_usd": round(gate, 2), "new_spend_usd": round(new, 2),
                         "with_30pct_margin_usd": round(new * (1 + MARGIN), 2)},
           "n_test_instances": N_TEST, "n_dev_instances": N_DEV, "replicates": REPS,
           "caveats": ["prices are those embedded in the E9 logs (batch API, run date); re-verify before any call",
                       "SC samples are assumed to cost five J1 calls (no Sonnet SC was run)",
                       "S0/S2 scaling borrows M1's token ratios; Sonnet's output lengths may differ",
                       "the Anthropic key used for E9/E9b is being revoked; a new key and author approval are needed"]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(res["estimated"], indent=1))


if __name__ == "__main__":
    main()
