"""Diagnostic only — not a gate and not used to change any rule. Synthetic probes, no dev or held-out data.

    python scripts/local/validity_diagnostic.py --model qwen3.5:9b [--seeds 5]

Re-sends the 20 Step 1 judge probes with `--seeds` further seeds (same options as feasibility.py: T = 0.7,
top_p 1.0, num_predict 512, the model's explicit Modelfile extras) and records validity, done_reason and the tail
of every invalid output, so a single failed probe can be read against a rate with a confidence interval.
Writes results/dev/feasibility/<slug>_validity_diagnostic.json.
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config, probes  # noqa: E402
from triage.io_utils import dump_json  # noqa: E402
from triage.ollama import OllamaAPI, load_local_models, model_options, schema_for_role, truncation_suspected  # noqa: E402
from triage.schema import parse_output  # noqa: E402


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [c - h, c + h]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--seeds", type=int, default=5)
    a = ap.parse_args()
    spec = load_local_models()["models"][a.model]
    api = OllamaAPI()
    plist = probes.judge_probes()
    rows = []
    for s in range(a.seeds):
        for i, p in enumerate(plist):
            seed = 2000 + 100 * s + i
            body = {"model": a.model, "messages": [{"role": "user", "content": p["text"]}], "stream": False,
                    "think": False, "keep_alive": "30m", "format": schema_for_role(p["role"]),
                    "options": {"num_ctx": 8192, "num_predict": config.MAX_OUTPUT_TOKENS,
                                "temperature": config.TEMPERATURE, "top_p": 1.0, "seed": seed, **model_options(spec)}}
            out = api.chat(body)
            msg = out.get("message") or {}
            c = msg.get("content") or ""
            parsed = parse_output(c, "judge")
            tok = out.get("prompt_eval_count") or 0          # includes the cached prefix (D-37)
            row = {"probe": p["id"], "seed": seed, "valid": parsed.ok, "repaired": parsed.repaired,
                   "done_reason": out.get("done_reason"), "eval_count": out.get("eval_count"),
                   "thinking_empty": not (msg.get("thinking") or "").strip(),
                   "truncated": truncation_suspected(len(p["text"]), tok, 8192, config.MAX_OUTPUT_TOKENS)}
            if not parsed.ok:
                row["content_head"], row["content_tail"] = c[:300], c[-400:]
            rows.append(row)
            print(f"seed{s} {p['id']:16s} valid={parsed.ok} {out.get('done_reason')} out={out.get('eval_count')}",
                  flush=True)
    k = sum(r["valid"] for r in rows)
    res = {"model": a.model, "digest": spec.get("digest"), "probe_set_hash": probes.probe_set_hash(),
           "note": "diagnostic only; the Step 1 verdict is the one in <slug>.json and is not altered by this file",
           "n": len(rows), "valid": k, "valid_rate": k / len(rows), "valid_rate_wilson95": wilson(k, len(rows)),
           "invalid_by_probe": {}, "invalid_done_reasons": {}, "any_truncated": any(r["truncated"] for r in rows),
           "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "rows": rows}
    for r in rows:
        if not r["valid"]:
            res["invalid_by_probe"][r["probe"]] = res["invalid_by_probe"].get(r["probe"], 0) + 1
            res["invalid_done_reasons"][r["done_reason"]] = res["invalid_done_reasons"].get(r["done_reason"], 0) + 1
    slug = a.model.replace("/", "_").replace(":", "_")
    dump_json(config.ROOT / "results" / "dev" / "feasibility" / f"{slug}_validity_diagnostic.json", res)
    print(json.dumps({k2: res[k2] for k2 in ("n", "valid", "valid_rate", "valid_rate_wilson95", "invalid_by_probe",
                                             "invalid_done_reasons", "any_truncated")}, indent=1))


if __name__ == "__main__":
    main()
