# Updated Model Configuration Proposal — local open-weight models (PLANNING ONLY)

Two configurations, of which exactly one will apply, chosen by the development-split procedure in
`MODEL_SELECTION_PROTOCOL.md`. No file in `configs/` is created or changed by this proposal; the JSON below
is a draft of `configs/local_models.FROZEN.json`, to be written only after Steps 1–5 have run and the authors
approve. Fields marked `"<measured>"` are filled from `/api/show`, `/api/ps` and `/api/version` at freeze time.

## 1. Decision logic

```
Step 1  feasibility of every candidate (alone, num_ctx = 8192, synthetic probes only)
        judge fails 100% GPU residency at default quant → retry next smaller quant once → else fallback (Gemma: e4b)
        G candidates may offload to RAM
Step 1b project Tier-1 GPU time from measured judge throughput → if it exceeds the time available, STOP for the authors
Step 2  generate + execute dev tests with each feasible G; choose by
        reliability > assertion validity > coverage > uniqueness/stability (5-pp tolerance bands), subject to P1 (PF ≥ 3%)
        G = Gemma 4 26B A4B  →  OPTION A        G = Qwen3.5-35B-A3B (or Qwen2.5-Coder fallback)  →  OPTION B
Step 3  freeze G; the selected G's dev tests are the dev set; label by execution; label audit
Step 4  M1 := judge from the family ≠ G  (rule, not contest); prompt development on dev; gates G-a…G-d
        failure → fallback ladder (prompts → quantization → stop for the authors)
Step 5  M2 := remaining judge; feasibility + G-a/G-b only; used for E5-R3 only
Step 6  write and hash configs/local_models.FROZEN.json; runner refuses any digest mismatch
```

## 2. Option A — G Gemma 4 26B A4B; M1 Qwen3.5-9B; M2 Gemma 4 12B

```json
{
  "status": "DRAFT — not frozen, not executed",
  "option": "A",
  "runtime": {"engine": "ollama", "version": "<measured>",
              "server_env": {"OLLAMA_FLASH_ATTENTION": "<fixed before Step 1>", "OLLAMA_KV_CACHE_TYPE": "f16",
                             "OLLAMA_NUM_PARALLEL": "<fixed before Step 1>", "OLLAMA_MAX_LOADED_MODELS": "1",
                             "OLLAMA_KEEP_ALIVE": "30m"}},
  "hardware": {"gpu": "NVIDIA GeForce RTX 5070 Ti Laptop GPU", "vram_mib": 12227, "driver": "<measured>",
               "cpu": "Intel Core Ultra 9 275HX", "ram_gb": 31, "os": "Windows 11"},
  "roles": {
    "G":  {"tag": "gemma4:26b",  "family": "gemma", "digest": "<measured>", "quantization": "<measured>",
           "gpu_resident": "partial (offload allowed)",
           "options": {"num_ctx": 8192, "num_predict": 4096, "temperature": 0.7, "top_p": 1.0, "seed": "per-call, derived"},
           "think": false, "format": null},
    "M1": {"tag": "qwen3.5:9b",  "family": "qwen",  "digest": "<measured>", "quantization": "<measured>",
           "gpu_resident": "required 100%",
           "options": {"num_ctx": 8192, "num_predict": 512, "temperature": 0.7, "top_p": 1.0, "seed": "per-call, derived"},
           "spec_inferencer_options": {"temperature": 0.0, "num_predict": 512},
           "think": false, "format": "schema:judge_v1"},
    "M2": {"tag": "gemma4:12b",  "family": "gemma", "digest": "<measured>", "quantization": "<measured>",
           "gpu_resident": "required 100%", "use": "E5-R3 only",
           "options": {"num_ctx": 8192, "num_predict": 512, "temperature": 0.7, "top_p": 1.0, "seed": "per-call, derived"},
           "think": false, "format": "schema:judge_v1"}
  },
  "family_check": {"G!=M1": true, "M1!=M2": true, "G==M2": "limitation: shared family (gemma)"},
  "prompt_set_hash": "<frozen after dev prompt development>",
  "scope": {"selection_splits": ["dev"], "forbidden_for_selection": ["test", "D2", "D3"]}
}
```

## 3. Option B — G Qwen3.5-35B-A3B; M1 Gemma 4 12B; M2 Qwen3.5-9B

Identical structure, with `G.tag = "qwen3.5:35b"` (family qwen; tag-to-architecture mapping confirmed via
`/api/show model_info` before use), `M1.tag = "gemma4:12b"` (residency fallback `gemma4:e4b`, reported if used),
`M2.tag = "qwen3.5:9b"`, `family_check.G==M2 = "limitation: shared family (qwen)"`.
If G falls back to `qwen2.5-coder:7b`, Option B's judge assignment applies (Qwen family = G).

## 4. Settings common to both options and why

| Setting | Value | Reason |
|---|---|---|
| `num_ctx` | 8192, sent on every request | Ollama's default may be lower; an unset context silently truncates. Covers prompt + output |
| `num_predict` (judges) | 512 | Phase 2 per-call output cap |
| `temperature` / `top_p` | 0.7 / 1.0 (judges, G); 0.0 (Spec Inferencer) | Phase 2 |
| `top_k`, `min_p` | set explicitly to the model's documented defaults, recorded | Ollama defaults could change between versions |
| `seed` | per call = hash(instance, arm, level, variant, replicate, sample index) | reproducible replicates where the runtime allows |
| `think` | false (Gemma: thinking token not injected) | primary comparisons without reasoning mode; verified per call |
| `format` | Table 11 JSON schema for judges; advocate schema for DEB rounds; none for G | Phase 2 "schema-constrained decoding where supported" |
| quantization | the frozen one, identical for every primary arm; same within each model across levels/arms | Phase 2 controlled variables |
| KV cache type | f16 (not quantized) | quantized KV changes outputs; fixed for all calls |
| one model loaded at a time | `OLLAMA_MAX_LOADED_MODELS = 1` | residency measurements stay valid |

## 5. Code changes needed before any local run (NOT implemented in this planning task)
1. `OllamaBackend` in `src/triage/llm.py`: `POST /api/chat`, sends `options` + `think` + `format`, returns
   `prompt_eval_count`, `prompt_eval_cached_count`, `eval_count`, durations, `done_reason`,
   `message.thinking`; cost 0 with `cost_source = "local"`.
2. Digest pin: at client start and every N calls, compare `/api/show` digest with the frozen config; mismatch → stop.
3. Local scope lock: a `configs/local_scope.json` read by the same `scope.Scope` checks (splits, experiments,
   models), because the USD budget guard does not apply to a zero-cost backend.
4. Context guard: refuse a request whose estimated input + `num_predict` exceeds `num_ctx`; after the call,
   flag `prompt_eval_count + prompt_eval_cached_count ≥ num_ctx − num_predict` as possibly truncated.
5. Thinking guard: non-empty `message.thinking` with `think: false` → INVALID + flag.
6. VRAM sampler: nvidia-smi every 200 ms during a call → peak VRAM; `/api/ps` → `size_vram`/`size`.
7. GPU-time ledger replacing the USD ledger for local runs; request key includes the model digest.
8. Defects4J coverage for G-selection criterion 3 (`defects4j coverage` on F for the passing generated tests).
All changes get unit tests with a fake Ollama server before any real model is used.

## 6. Compute-time projection (method; numbers are placeholders until measured)
`hours = Σ_component calls × (mean_prompt_tokens / prompt_tps + mean_output_tokens / gen_tps) / parallel_slots / 3600`
using Step 1 throughput. Call counts from `scripts/estimate_cost.py --scope full` (Tier 1 ≈ 96 k judge calls;
G = (234 D1 focal methods + 284 verified D2 mutants + up to 60 D3 bugs, D3 currently blocked) × 3 generations
≈ 1,554–1,734 generations, each up to 4,096 output tokens on a partly RAM-offloaded MoE model). The projection is computed and shown to the authors before Step 2;
it determines whether Tier 1 fits the time available, not which model is chosen.
