"""D-24 — choose OLLAMA_NUM_PARALLEL and flash attention on synthetic probes only, with the M1 candidate.

    python scripts/local/server_settings.py --model qwen3.5:9b

For each setting (parallel in 1, 2, 4) x (flash attention 0, 1): restart the server with that environment, load
the model at num_ctx 8192, send `parallel` concurrent streams of typical judge probes, and record aggregate
throughput (completed calls/hour, output tokens/s), GPU residency (size_vram == size, context_length == 8192)
and free VRAM under load. Rule (D-24): highest throughput among settings with 100% GPU residency at 8192.
KV cache stays f16. Writes results/dev/server_settings.json. No dev or held-out data is used.
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config, hwinfo, ollama_server, probes  # noqa: E402
from triage.io_utils import dump_json  # noqa: E402
from triage.ollama import OllamaAPI, VramSampler, load_local_models, model_options, schema_for_role  # noqa: E402

NUM_CTX = 8192


def call(api, model, p, seed):
    body = {"model": model, "messages": [{"role": "user", "content": p["text"]}], "stream": False, "think": False,
            "keep_alive": "30m", "format": schema_for_role(p["role"]),
            "options": {"num_ctx": NUM_CTX, "num_predict": config.MAX_OUTPUT_TOKENS, "temperature": config.TEMPERATURE,
                        "top_p": 1.0, "seed": seed,
                        **model_options(load_local_models()["models"][model])}}
    t0 = time.time()
    out = api.chat(body)
    return out, time.time() - t0


def measure(api, sampler, model, parallel, plist, rounds):
    api.chat({"model": model, "messages": [{"role": "user", "content": "OK"}], "stream": False, "think": False,
              "options": {"num_ctx": NUM_CTX, "num_predict": 4}})
    ps = api.ps().get(model, {})
    jobs = [(p, 9000 + i) for i in range(rounds) for p in plist]
    t0 = time.time()
    with ThreadPoolExecutor(parallel) as ex:
        res = list(ex.map(lambda j: call(api, model, *j), jobs))
    wall = time.time() - t0
    tele = sampler.window(t0, time.time())
    ps2 = api.ps().get(model, {})
    out_tokens = sum((o.get("eval_count") or 0) for o, _ in res)
    gpu = hwinfo.gpu()
    return {"calls": len(res), "wall_s": wall, "calls_per_hour": len(res) / wall * 3600,
            "output_tps_aggregate": out_tokens / wall,
            "median_call_s": sorted(d for _, d in res)[len(res) // 2],
            "size": ps2.get("size"), "size_vram": ps2.get("size_vram"), "context_length": ps2.get("context_length"),
            "gpu_resident": bool(ps2.get("size")) and (ps2.get("size_vram") or 0) >= ps2["size"],
            "ctx_8192": ps2.get("context_length") == NUM_CTX, "peak_vram_mib": tele.get("peak_vram_mib"),
            "free_vram_under_load_gib": ((gpu.get("mem_total_mib") or 0) - (tele.get("peak_vram_mib") or 0)) / 1024,
            "max_gpu_temp_c": tele.get("max_gpu_temp_c"), "size_after_load": ps.get("size")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--rounds", type=int, default=2)
    a = ap.parse_args()
    plist = [p for p in probes.judge_probes() if "typical" in p["id"]]   # 8 typical probes
    sampler = VramSampler.get()
    results = []
    for fa in ("0", "1"):
        for par in (1, 2, 4):
            env = ollama_server.restart({"OLLAMA_NUM_PARALLEL": str(par), "OLLAMA_FLASH_ATTENTION": fa},
                                        tag=f"settings_p{par}_fa{fa}")
            api = OllamaAPI()
            try:
                r = measure(api, sampler, a.model, par, plist, a.rounds)
                r["error"] = None
            except Exception as e:
                r = {"error": f"{type(e).__name__}: {e}"}
            r.update(parallel=par, flash_attention=fa, server_env=env)
            results.append(r)
            print(json.dumps({k: r.get(k) for k in ("parallel", "flash_attention", "calls_per_hour", "gpu_resident",
                                                    "ctx_8192", "free_vram_under_load_gib", "error")}), flush=True)
    eligible = [r for r in results if not r.get("error") and r.get("gpu_resident") and r.get("ctx_8192")]
    choice = max(eligible, key=lambda r: r["calls_per_hour"]) if eligible else None
    out = {"model": a.model, "rule": "highest calls/hour with 100% GPU residency at num_ctx 8192 (D-24); KV f16",
           "results": results, "choice": None if choice is None else
           {"OLLAMA_NUM_PARALLEL": str(choice["parallel"]), "OLLAMA_FLASH_ATTENTION": choice["flash_attention"],
            "calls_per_hour": choice["calls_per_hour"]},
           "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    dump_json(config.ROOT / "results" / "dev" / "server_settings.json", out)
    # restore the base environment; the chosen values are written into configs/local_server_env.json separately
    ollama_server.restart(tag="restore")
    print(json.dumps(out["choice"], indent=1))


if __name__ == "__main__":
    main()
