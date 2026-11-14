"""Held-out GPU-time projection for the freeze report, from MEASURED dev costs (not synthetic estimates).

    python scripts/local/project_heldout.py [--explore qwen3.5:35b]

Per-arm GPU-seconds come from the dev call logs of the frozen configuration (GATE_M1b for M1, CHECK_M2 for M2,
the dev generation run for G, the dev spec inference for M1). Sizes are the D-31 planning values (D1-test 720,
D2 300 judged instances; generation 195 + 284 methods/mutants x 3); k_T from P4. S0/S2 are costed like S1.
With --explore, the D-55 exploratory check is costed by scaling M1's measured per-arm seconds by the ratio of the
two models' median wall time on the identical Step 1 synthetic judge probes, and the D-55 inclusion rule is
applied: include iff Tier 1 + Tier 2 + the check <= available GPU-hours (D-31: to 2026-11-13 23:59 x 0.80).
Writes results/dev/projection_heldout.json.
"""
import argparse
import json
import os
import statistics
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402
from triage.ollama import LOCAL_CALL_LOG_DIR  # noqa: E402

DEADLINE, DUTY = datetime(2026, 11, 13, 23, 59), 0.80
N_D1, N_D2, N_METHODS, N_MUTANTS = 720, 300, 195, 284


def slug(m):
    return m.replace("/", "__").replace(":", "_")


def calls():
    out = {}
    for f in Path(LOCAL_CALL_LOG_DIR).glob("*.jsonl"):
        if not f.name.startswith("_"):
            out.update({r["key"]: r for r in read_jsonl(f)})
    return out


def per_arm(run, C):
    acc = {}
    for d in read_jsonl(config.ROOT / "results" / "dev" / run / "decisions.jsonl"):
        ks = (d.get("cost") or {}).get("call_keys") or []
        if ks:
            acc.setdefault(d["arm"], []).append(sum((C[k].get("local") or {}).get("gpu_seconds", 0) for k in ks if k in C))
    return {a: statistics.mean(v) for a, v in acc.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--explore")
    a = ap.parse_args()
    C = calls()
    m1, m2 = per_arm("GATE_M1b", C), per_arm("CHECK_M2", C)
    gen = statistics.mean(r["latency_s"] for r in C.values() if r["role"] == "generator")
    spec = statistics.mean(r["latency_s"] for r in C.values() if r["role"] == "spec_inferencer")
    k_t = json.loads((config.ROOT / "results/dev/GATE_M1b/dev_gates.json").read_text())["P4"]["k_T"]
    inst1 = m1["J1"] + m1["SC"] + m1["DEB"]
    sct = m1["SC"] / config.SC_SAMPLES * k_t
    h = lambda s: s / 3600
    tier1 = {"E1-E3 D1-test (3 levels x 3 reps)": h(N_D1 * 3 * config.REPLICATES * inst1),
             "SC-T S1 (3 reps)": h(N_D1 * config.REPLICATES * sct),
             "S2 spec inference (M1)": h(N_METHODS * spec),
             "G generation (D1 + D2)": h((N_METHODS + N_MUTANTS) * config.GENERATIONS_PER_FOCAL * gen),
             "D2 E1-E3 (3 levels x 1 rep)": h(N_D2 * 3 * inst1)}
    e4 = m1["DEB"] * 2 + inst1 + (m1["J1"] + m1["DEB"]) + m1["J1"]      # A1, A2, A4 (J1+SC+DEB), A5a, A5b
    tier2 = {"E4 ablations S1 (1 rep)": h(N_D1 * e4), "S2' spec inference (A5b)": h(N_METHODS * spec)}
    tier3 = {"E5-R3 M2 S1 (D1-test + D2, 1 rep)": h((N_D1 + N_D2) * (m2["J1"] + m2["SC"] + m2["DEB"])),
             "R4 paraphrases (J1 x 2)": h(N_D1 * 2 * m1["J1"])}
    avail = (DEADLINE - datetime.now()).total_seconds() / 3600 * DUTY
    t1, t2, t3 = sum(tier1.values()), sum(tier2.values()), sum(tier3.values())
    out = {"utc": datetime.now().astimezone().isoformat(timespec="seconds"), "available_gpu_hours": avail,
           "basis_seconds": {"M1_per_instance": m1, "M2_per_instance": m2, "G_per_generation": gen,
                             "spec_per_method": spec, "k_T": k_t},
           "planning_sizes": {"D1_test": N_D1, "D2": N_D2, "methods": N_METHODS, "mutants": N_MUTANTS},
           "tier1": tier1, "tier2": tier2, "tier3": tier3, "tier1_h": t1, "tier2_h": t2, "tier3_h": t3,
           "fits": {"tier1": t1 <= avail, "tier1+2": t1 + t2 <= avail, "tier1+2+3": t1 + t2 + t3 <= avail}}
    if a.explore:
        fe = json.loads((config.ROOT / "results/dev/feasibility" / f"{slug(a.explore)}.json").read_text())
        fm = json.loads((config.ROOT / "results/dev/feasibility" / "qwen3.5_9b.json").read_text())
        ratio = fe["summary"]["median_wall_s"] / fm["summary"]["median_wall_s"]
        ex = h(N_D1 * inst1 * ratio)
        out["exploratory"] = {"model": a.explore, "wall_ratio_vs_M1_on_probes": ratio, "hours": ex,
                              "rule": "D-55: include iff tier1 + tier2 + exploratory <= available",
                              "included": t1 + t2 + ex <= avail}
    dump_json(config.ROOT / "results" / "dev" / "projection_heldout.json", out)
    print(f"available {avail:.1f} h | tier1 {t1:.1f} | tier2 {t2:.1f} | tier3 {t3:.1f} | fits {out['fits']}")
    for k, v in {**tier1, **tier2, **tier3}.items():
        print(f"  {k:40s} {v:6.1f} h")
    if "exploratory" in out:
        print("exploratory:", json.dumps(out["exploratory"]))


if __name__ == "__main__":
    main()
