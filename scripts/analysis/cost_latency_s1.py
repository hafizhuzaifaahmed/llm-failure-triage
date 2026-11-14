"""Cost and latency per arm from the call logs (D-80): D1-test, S1, judge M1, arms J1 / SC / SC-T / DEB.

Every decision stores the keys of the model calls it made; each key is looked up in the frozen call log
(`data/raw/llm_calls_local/qwen3.5_9b.jsonl`), which records the tokens and wall time of the call. Per decision
(instance × replicate) the calls are summed; calls run one at a time (OLLAMA_NUM_PARALLEL = 1), so the summed wall time
is the decision's latency. Reported over the scored S1 set (labelled, D-70 aborts excluded): calls per instance, mean
input and output tokens per instance, median and 90th-percentile wall time per instance. Zero API cost throughout.
The per-decision sums are cross-checked against the decision records' own cost fields, which conditions.csv averages.

    python scripts/analysis/cost_latency_s1.py   -> results/heldout/analysis_final/D1_M1/tables/cost_latency_s1.json
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

RUN = ROOT / "results" / "runs_local" / "LOCAL_HO_E1E3_M1"
CALL_LOG = ROOT / "data" / "raw" / "llm_calls_local" / "qwen3.5_9b.jsonl"
OUT = ROOT / "results" / "heldout" / "analysis_final" / "D1_M1" / "tables" / "cost_latency_s1.json"
ARMS = ("J1", "SC", "SC-T", "DEB")


def main():
    samp = json.loads((config.PROCESSED / "sample_D1_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labelled = {l["instance_id"] for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl")
                if l["instance_id"] in keep and l["label"] in ("PF", "TF")}
    aborted = {r["instance_id"] for r in read_jsonl(RUN / "leakage_rejections.jsonl")
               if r.get("level") == "S1" and (r.get("variant") or "full") == "full"}
    scored = labelled - aborted
    decs = [d for d in read_jsonl(RUN / "decisions.jsonl")
            if d["arm"] in ARMS and d["level"] == "S1" and (d.get("variant") or "full") == "full"
            and d["instance_id"] in scored]
    wanted = set()
    for d in decs:
        c = d["cost"] if isinstance(d["cost"], dict) else json.loads(d["cost"])
        d["_cost"] = c
        wanted.update(c["call_keys"])
    calls = {}
    with open(CALL_LOG, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r["key"] in wanted and r["key"] not in calls:
                calls[r["key"]] = (int(r["input_tokens"]), int(r["output_tokens"]), float(r["latency_s"]))
    missing = wanted - set(calls)
    if missing:
        raise SystemExit(f"{len(missing)} call keys not in the call log")
    out = {"what": "cost and latency per arm from the call log, D1-test S1 judge M1 (D-80)", "call_log": str(CALL_LOG.relative_to(ROOT).as_posix()),
           "scored_instances": len(scored), "cost_usd": 0.0, "arms": {}}
    for arm in ARMS:
        ds = [d for d in decs if d["arm"] == arm]
        per = np.array([[len(d["_cost"]["call_keys"]), sum(calls[k][0] for k in d["_cost"]["call_keys"]),
                         sum(calls[k][1] for k in d["_cost"]["call_keys"]), sum(calls[k][2] for k in d["_cost"]["call_keys"])]
                        for d in ds], dtype=float)
        rec = np.array([[d["_cost"]["calls"], d["_cost"]["input_tokens"], d["_cost"]["output_tokens"], d["_cost"]["latency_s"]]
                        for d in ds], dtype=float)
        agree = bool(np.allclose(per[:, :3], rec[:, :3]) and np.allclose(per[:, 3], rec[:, 3], atol=0.01 * per[:, 0].max()))
        out["arms"][arm] = {"decisions": len(ds), "instances": len({d["instance_id"] for d in ds}),
                            "replicates": len({d["replicate"] for d in ds}),
                            "calls_per_instance": float(per[:, 0].mean()),
                            "input_tokens_per_instance": float(per[:, 1].mean()),
                            "output_tokens_per_instance": float(per[:, 2].mean()),
                            "wall_s_median": float(np.median(per[:, 3])), "wall_s_p90": float(np.quantile(per[:, 3], 0.9)),
                            "wall_s_mean": float(per[:, 3].mean()), "matches_decision_cost_fields": agree}
        a = out["arms"][arm]
        print(f"{arm:5s} n={a['decisions']} calls={a['calls_per_instance']:.2f} in={a['input_tokens_per_instance']:.0f} "
              f"out={a['output_tokens_per_instance']:.0f} med={a['wall_s_median']:.2f}s p90={a['wall_s_p90']:.2f}s match={agree}")
    j1, deb = out["arms"]["J1"], out["arms"]["DEB"]
    out["deb_over_j1"] = {"calls": deb["calls_per_instance"] / j1["calls_per_instance"],
                          "tokens": (deb["input_tokens_per_instance"] + deb["output_tokens_per_instance"])
                                    / (j1["input_tokens_per_instance"] + j1["output_tokens_per_instance"]),
                          "median_wall": deb["wall_s_median"] / j1["wall_s_median"]}
    dump_json(OUT, out)


if __name__ == "__main__":
    main()
