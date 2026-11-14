"""Step 1 — feasibility of one model, alone, on synthetic probes only (MODEL_SELECTION_PROTOCOL.md).

    python scripts/local/feasibility.py --model qwen3.5:9b --role judge
    python scripts/local/feasibility.py --model gemma4:26b --role generator

Writes results/dev/feasibility/<model>.json (+ licence text). Talks to the raw Ollama API: probes are not study
calls and never enter the study call log. Pass rules are the protocol's, fixed before running.
"""
import argparse
import json
import re
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config, hwinfo, probes  # noqa: E402
from triage.io_utils import dump_json, sha256_text  # noqa: E402
from triage.ollama import OllamaAPI, VramSampler, load_local_models, model_options, schema_for_role, truncation_suspected  # noqa: E402
from triage.schema import parse_output  # noqa: E402

OUT = config.ROOT / "results" / "dev" / "feasibility"
NUM_CTX = 8192
EXTRA = {}   # model sampling extras from configs/local_models.json (D-34), identical to study calls


def slug(m):
    return m.replace("/", "__").replace(":", "_")


def unload_all(api):
    for name in list(api.ps()):
        api.unload(name)
    for _ in range(30):
        if not api.ps():
            return
        time.sleep(1)


THINK = {"value": False}   # D-85: None for a model with no thinking channel -> the field is not sent


def chat(api, model, text, role, num_predict, temperature, seed, think=None, keep_alive="30m"):
    think = THINK["value"] if think is None else think
    body = {"model": model, "messages": [{"role": "user", "content": text}], "stream": False, "think": think,
            "keep_alive": keep_alive,
            "options": {"num_ctx": NUM_CTX, "num_predict": num_predict, "temperature": temperature, "top_p": 1.0,
                        "seed": seed, **EXTRA}}
    if body["think"] is None:
        del body["think"]
    schema = schema_for_role(role)
    if schema is not None:
        body["format"] = schema
    t0 = time.time()
    out = api.chat(body)
    return out, t0, time.time()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--role", choices=["judge", "generator"], required=True)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--profile", help="runtime profile (configs/expl_35b.json D-67, configs/e6b.json D-82): its server, spec and output dir")
    a = ap.parse_args()
    global OUT
    if a.profile:
        from triage import expl_profile
        prof = expl_profile.load(Path(a.profile))
        if a.model != prof["model_tag"]:
            raise SystemExit(f"profile {a.profile} serves {prof['model_tag']}, not {a.model}")
        api = OllamaAPI(prof["base_url"], timeout_s=prof["first_response_timeout_s"])
        spec, OUT = prof["model_spec"], expl_profile.resolve(prof["feasibility_dir"])
    else:
        api, spec = OllamaAPI(), load_local_models()["models"].get(a.model)
    sampler = VramSampler.get()
    if not spec or not spec.get("digest"):
        raise SystemExit(f"{a.model} is not registered (run scripts/local/register_models.py)")
    EXTRA.update(model_options(spec))
    THINK["value"] = spec.get("think", False)
    rec = {"model": a.model, "role": a.role, "utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "ollama_version": api.version(), "num_ctx": NUM_CTX, "probe_set_hash": probes.probe_set_hash(),
           "gpu_idle": hwinfo.gpu(), "ram_before": hwinfo.ram()}
    unload_all(api)
    show = api.show(a.model)
    tags = api.tags()
    rec["digest"] = tags.get(a.model, {}).get("digest")
    rec["digest_matches_config"] = rec["digest"] == spec["digest"]
    rec["sampling_extras"] = dict(EXTRA)
    rec["details"] = show.get("details")
    mi = show.get("model_info") or {}
    rec["model_info"] = {k: v for k, v in mi.items() if isinstance(v, (int, float, str)) and
                         any(s in k for s in ("parameter_count", "architecture", "context_length", "block_count",
                                              "head_count", "embedding_length", "expert"))}
    rec["capabilities"] = show.get("capabilities")
    rec["thinking_meta"] = show.get("thinking")
    lic = show.get("license") or ""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{slug(a.model)}_license.txt").write_text(lic, encoding="utf-8")
    rec["license_sha256"] = sha256_text(lic)
    rec["license_head"] = lic[:300]
    rec["template_sha256"] = sha256_text(show.get("template") or "")

    # warm load
    out, t0, t1 = chat(api, a.model, "Reply with the word OK.", "none", 8, 0.0, 1)
    rec["load_duration_s"] = (out.get("load_duration") or 0) / 1e9
    ps = api.ps().get(a.model, {})
    rec["residency"] = {"size": ps.get("size"), "size_vram": ps.get("size_vram"),
                        "context_length": ps.get("context_length"),
                        "gpu_fraction": (ps.get("size_vram") or 0) / ps["size"] if ps.get("size") else None}
    rec["gpu_after_load"] = hwinfo.gpu()
    rec["ram_after_load"] = hwinfo.ram()
    rec["ollama_working_set_gib"] = hwinfo.ollama_working_set_gib()

    plist = probes.judge_probes() if a.role == "judge" else probes.generator_probes(n=a.n)
    plist = plist[: a.n]
    num_predict = config.MAX_OUTPUT_TOKENS if a.role == "judge" else 4096
    rows = []
    for i, p in enumerate(plist):
        out, t0, t1 = chat(api, a.model, p["text"], p["role"], num_predict, config.TEMPERATURE, 1000 + i)
        msg = out.get("message") or {}
        content, thinking = msg.get("content") or "", msg.get("thinking") or ""
        pe, pc, ec = out.get("prompt_eval_count") or 0, out.get("prompt_eval_cached_count") or 0, out.get("eval_count") or 0
        if a.role == "judge":
            valid = parse_output(content, "judge").ok
        else:
            valid = bool(re.search(r"```(?:java)?\s*\n.*?@Test.*?```", content, re.S))
        tele = sampler.window(t0, t1)
        ps = api.ps().get(a.model, {})
        rows.append({"id": p["id"], "chars": len(p["text"]), "prompt_eval_count": pe, "prompt_eval_cached_count": pc,
                     "eval_count": ec, "chars_per_token": len(p["text"]) / pe if pe else None,   # D-37: pe includes cached
                     "prefill_tps": (pe - pc) / (out["prompt_eval_duration"] / 1e9) if out.get("prompt_eval_duration") and pe > pc else None,
                     "gen_tps": ec / (out["eval_duration"] / 1e9) if out.get("eval_duration") else None,
                     "wall_s": t1 - t0, "done_reason": out.get("done_reason"), "valid": valid,
                     "thinking_chars": len(thinking), "thinking_empty": not thinking.strip(),
                     "fits_ctx": not truncation_suspected(len(p["text"]), pe, NUM_CTX, num_predict), "size_vram": ps.get("size_vram"), "size": ps.get("size"),
                     **tele})
        print(f"  {p['id']:16s} in={pe:5d} out={ec:4d} valid={valid} think={len(thinking)} {t1 - t0:6.1f}s", flush=True)
    rec["probes"] = rows

    # repeatability: one typical probe x5 at T=0 and x5 at T=0.7, fixed seed
    rp = plist[6] if len(plist) > 6 else plist[0]
    rep = {}
    for temp in (0.0, 0.7):
        texts = []
        for _ in range(5):
            out, _, _ = chat(api, a.model, rp["text"], rp["role"], num_predict, temp, 4242)
            texts.append((out.get("message") or {}).get("content") or "")
        rep[str(temp)] = {"identical_outputs": max(texts.count(t) for t in texts), "of": 5}
    rec["repeatability"] = rep

    # D-27: prompt caching in the SC pattern (same prompt, 5 samples, different seeds)
    if a.role == "judge":
        cache_rows = []
        for j in range(5):
            out, t0, t1 = chat(api, a.model, plist[7]["text"], "judge", num_predict, config.TEMPERATURE, 7000 + j)
            cache_rows.append({"sample": j, "prompt_eval_count": out.get("prompt_eval_count"),
                               "prompt_eval_cached_count": out.get("prompt_eval_cached_count"),
                               "prompt_eval_s": (out.get("prompt_eval_duration") or 0) / 1e9,
                               "eval_s": (out.get("eval_duration") or 0) / 1e9, "wall_s": t1 - t0})
        rec["sc_prefix_caching"] = cache_rows

    # verdicts (pass rules fixed in MODEL_SELECTION_PROTOCOL.md Step 1)
    res = rec["residency"]
    total_mib = rec["gpu_after_load"].get("mem_total_mib") or 0
    peak_mib = max((r.get("peak_vram_mib") or 0) for r in rows)
    gpu_free_gib = (total_mib - peak_mib) / 1024 if peak_mib else (rec["gpu_after_load"].get("mem_free_mib") or 0) / 1024
    rec["free_vram_under_load_gib"] = gpu_free_gib
    v = {
        "licence_recorded": bool(lic.strip()),
        "context_length_8192": res["context_length"] == NUM_CTX,
        "gpu_resident_100pct": bool(res["size"]) and res["size_vram"] is not None and res["size_vram"] >= res["size"],
        "free_vram_ge_0.5gib": gpu_free_gib >= 0.5,
        "ram_free_ge_4gib": rec["ram_after_load"]["free_gib"] >= 4.0,
        "thinking_off_empty_all": all(r["thinking_empty"] for r in rows),
        "valid_rate": sum(r["valid"] for r in rows) / len(rows),
        "all_fit_ctx": all(r["fits_ctx"] for r in rows),
        "thinking_can_be_false": (rec["thinking_meta"] is None) or (False in (rec["thinking_meta"] or {}).get("values", [False])),
    }
    if a.role == "judge":
        v["passes"] = (v["context_length_8192"] and v["gpu_resident_100pct"] and v["free_vram_ge_0.5gib"]
                       and v["thinking_off_empty_all"] and v["valid_rate"] >= 0.98 and v["all_fit_ctx"])
    else:
        v["passes"] = (v["context_length_8192"] and v["ram_free_ge_4gib"] and v["thinking_off_empty_all"]
                       and v["valid_rate"] >= 0.95)
    rec["verdict"] = v
    rec["summary"] = {
        "median_prefill_tps": statistics.median([r["prefill_tps"] for r in rows if r["prefill_tps"]]),
        "median_gen_tps": statistics.median([r["gen_tps"] for r in rows if r["gen_tps"]]),
        "median_wall_s": statistics.median([r["wall_s"] for r in rows]),
        "min_chars_per_token": min(r["chars_per_token"] for r in rows if r["chars_per_token"]),
        "median_chars_per_token": statistics.median([r["chars_per_token"] for r in rows if r["chars_per_token"]]),
        "max_prompt_tokens": max(r["prompt_eval_count"] for r in rows),
        "peak_vram_mib": max((r.get("peak_vram_mib") or 0) for r in rows),
        "max_gpu_temp_c": max((r.get("max_gpu_temp_c") or 0) for r in rows),
    }
    rec["utc_end"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    dump_json(OUT / f"{slug(a.model)}.json", rec)
    print(json.dumps({"verdict": v, "summary": rec["summary"], "residency": res}, indent=1))


if __name__ == "__main__":
    main()
