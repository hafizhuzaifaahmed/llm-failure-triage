"""D-126: read the thinking probe (dev split) and either write the held-out run config or record why it is not run.

Rules fixed in D-126: not run if any probe call was not GPU-resident, if more than 1 of 3 outputs has no valid answer,
or if the projected duration (probe median call time x held-out instances) does not fit before the deadline after the
WP2.4 run. Otherwise the latency limit of the stopping rule is 3 x the probe's median call latency.

    python scripts/local/revision_think_gate.py [--after-utc ISO]   -> configs/revision/REV_THINK_M1.json or a 'not run' record
"""
import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "results" / "revision" / "runs" / "REV_THINK_PROBE_M1" / "decisions.jsonl"
CALLS = ROOT / "data" / "raw" / "llm_calls_local_revision" / "qwen3.5_9b.jsonl"
OUT_CFG = ROOT / "configs" / "revision" / "REV_THINK_M1.json"
OUT_REC = ROOT / "results" / "revision" / "think_gate.json"
DEADLINE = datetime(2026, 11, 12, 23, 59, tzinfo=timezone.utc).replace(tzinfo=None)   # local 23:59, compared naively
N_HELDOUT = 193


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--after-local", help="local time WP2.4 is expected to end (ISO); default now")
    a = ap.parse_args()
    ds = [json.loads(l) for l in open(PROBE, encoding="utf-8")]
    calls = [json.loads(l) for l in open(CALLS, encoding="utf-8")]
    calls = [c for c in calls if c.get("max_tokens") == 8192]
    lat = [c["latency_s"] for c in calls]
    resident = [bool((c.get("local") or {}).get("gpu_resident")) for c in calls]
    invalid = sum(d["label_raw"] not in ("PROGRAM_FAULT", "TEST_FAULT") for d in ds)
    med = statistics.median(lat) if lat else None
    start = datetime.fromisoformat(a.after_local) if a.after_local else datetime.now()
    hours = (med or 0) * N_HELDOUT / 3600
    fits = (start.timestamp() + hours * 3600) < DEADLINE.timestamp()
    rec = {"decision": "D-126", "probe_calls": len(calls), "probe_decisions": len(ds), "latencies_s": lat,
           "median_latency_s": med, "gpu_resident": resident, "invalid_outputs": invalid,
           "eval_counts": [(c.get("local") or {}).get("eval_count") for c in calls],
           "thinking_chars": [(c.get("local") or {}).get("thinking_chars") for c in calls],
           "projected_hours": hours, "projected_start_local": start.isoformat(timespec="minutes"),
           "deadline_local": DEADLINE.isoformat(), "fits_deadline": fits}
    reasons = []
    if len(calls) < 3 or len(ds) < 3:
        reasons.append(f"probe incomplete ({len(calls)} calls, {len(ds)} decisions)")
    if not all(resident):
        reasons.append("a probe call was not fully GPU-resident")
    if invalid > 1:
        reasons.append(f"{invalid} of 3 probe outputs had no valid answer")
    if not fits:
        reasons.append(f"projected {hours:.1f} h does not fit before the deadline")
    rec["run_heldout"] = not reasons
    rec["reasons_not_run"] = reasons
    if not reasons:
        rec["max_median_latency_s"] = round(3 * med, 3)
        cfg = {"name": "REV_THINK_M1", "decision": "D-126", "member": "M1", "dataset": "D1", "split": "test",
               "prompt_set": "local_m1b", "sample_file": "data/processed/sample_D1_test.json",
               "spec_patch": {"think": True, "num_ctx": 16384}, "max_tokens": 8192,
               "max_median_latency_s": rec["max_median_latency_s"],
               "_latency_rule": "3 x the D-126 probe's median call latency (results/revision/think_gate.json)",
               "conditions": [{"arm": "J1", "levels": ["S1"], "replicate_indices": [60]}]}
        OUT_CFG.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8", newline="\n")
    OUT_REC.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in rec.items() if k not in ("latencies_s",)}, indent=1))


if __name__ == "__main__":
    main()
