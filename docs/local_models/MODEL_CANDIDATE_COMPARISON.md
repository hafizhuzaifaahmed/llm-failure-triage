# Model Candidate Comparison (PLANNING ONLY — nothing measured yet)

Sources checked 2026-10-31: the Ollama library pages for `gemma4` and `qwen3.5`, Ollama API documentation
(chat, ps, thinking), and secondary sources for licences and the Qwen3.5-35B architecture. **No model has been
downloaded or run.** "Published" columns are what those sources state; "Measured" columns are blank until
Step 1 of `MODEL_SELECTION_PROTOCOL.md` runs. Where a source is secondary or silent, it says so.

## 1. Published facts

| Role | Candidate (Ollama tag) | Family | Architecture / params (published) | Download size (Ollama page) | Context (page) | Thinking (page) | Licence | Verification status |
|---|---|---|---|---|---|---|---|---|
| G (test first) | Gemma 4 26B A4B — `gemma4:26b` | Gemma (Google) | MoE, 25.2 B total / 3.8 B active | 16–19 GB | 256 K | on by default; enabled by `<\|think\|>` in the system prompt; with thinking off, the 26B still emits an empty thought block | secondary sources: Apache 2.0; one directory still lists the Gemma Terms of Use | architecture from the Ollama page; **licence unconfirmed** → read `/api/show license` |
| G | Qwen3.5-35B-A3B — `qwen3.5:35b` | Qwen (Alibaba) | secondary sources: MoE, 35 B total / 3 B active; the Ollama page does **not** state "A3B" | 22 GB | 256 K | family tagged "thinking"; toggle not documented on the page → `think` field + `/api/show thinking` | secondary sources: Apache 2.0 | **architecture and licence unconfirmed at primary source**; confirm the tag maps to 35B-A3B via `/api/show model_info` |
| G fallback | Qwen2.5-Coder-7B-Instruct — `qwen2.5-coder:7b` | Qwen | dense 7 B (not re-checked in this pass) | not re-checked | not re-checked | none expected | not re-checked | **all fields to verify** |
| Judge | Qwen3.5-9B — `qwen3.5:9b` | Qwen | 9 B (page gives size label only) | 6.6–7.6 GB | 256 K | family tagged "thinking" | secondary: Apache 2.0 | dense vs MoE and licence to confirm via `/api/show` |
| Judge | Gemma 4 12B — `gemma4:12b` | Gemma | secondary: 12 B dense | 7.7–8.0 GB | 256 K | thinking on by default; empty thought block when off | as `gemma4:26b` | architecture from a secondary source |
| Judge fallback | Gemma 4 E4B — `gemma4:e4b` | Gemma | 4.5 B effective (8 B with embeddings) | 6.6–9.5 GB | 128 K | as above | as above | Ollama page |

Notes on the published facts
- All candidates are multimodal (text + image) in Ollama. Only text is used; the vision encoder may still
  occupy memory and must be accounted for in the residency check.
- Ollama download sizes are ranges because several quantizations exist; the default tag's quantization is not
  stated on the pages and must be read from `/api/show details.quantization_level`.
- "Family" for the separation rule is the developer lineage. Qwen2.5-Coder and Qwen3.5 count as one family.

## 2. Expected fit on the target machine (reasoning from file sizes — an expectation, not a measurement)

| Candidate | Weights vs 12 GB VRAM | Expectation at num_ctx 8192 | Consequence |
|---|---|---|---|
| `gemma4:26b` | 16–19 GB > 12 GB | partial offload to RAM; MoE with 3.8 B active should keep decoding usable | acceptable for G (runs once); RAM headroom must be checked against WSL |
| `qwen3.5:35b` | 22 GB ≫ 12 GB | larger offload than Gemma (about half of the weights in RAM) | slower generation; RAM pressure with 31 GB total — never concurrent with WSL execution |
| `qwen3.5:9b` | 6.6–7.6 GB | plausibly 100% GPU with 8 K KV cache | must be verified: KV-cache size depends on layer/head counts not stated on the page |
| `gemma4:12b` | 7.7–8.0 GB | plausibly 100% GPU, tighter margin | if residency fails at the default quant, the protocol retries the next smaller quant once, then `gemma4:e4b` |
| `gemma4:e4b` | 6.6–9.5 GB | likely fits | capacity downgrade; residency fallback only |

## 3. Measurement sheet (to be filled by Step 1; blank by design)

| Field | gemma4:26b | qwen3.5:35b | qwen2.5-coder:7b | qwen3.5:9b | gemma4:12b | gemma4:e4b |
|---|---|---|---|---|---|---|
| manifest digest | | | | | | |
| quantization_level | | | | | | |
| parameter count (model_info) | | | | | | |
| licence (verbatim hash) | | | | | | |
| `thinking.values` / default | | | | | | |
| `size` / `size_vram` at 8192 | | | | | | |
| free VRAM under load | | | | | | |
| RAM used / free | | | | | | |
| prompt tok/s (median) | | | | | | |
| generate tok/s (median) | | | | | | |
| load time | | | | | | |
| JSON-schema valid (of 20) | | | | | | |
| empty thinking with think off (of 20) | | | | | | |
| T = 0 identical outputs (of 5) | | | | | | |
| feasibility verdict | | | | | | |

## 4. The two possible configurations

| | Option A | Option B |
|---|---|---|
| G | Gemma 4 26B A4B | Qwen3.5-35B-A3B |
| M1 (primary judge) | Qwen3.5-9B | Gemma 4 12B (fallback E4B for residency only) |
| M2 (robustness) | Gemma 4 12B | Qwen3.5-9B |
| G–M1 family | different ✓ | different ✓ |
| M1–M2 family | different ✓ | different ✓ |
| G–M2 family | **shared (Gemma)** — limitation | **shared (Qwen)** — limitation |
| Which one applies | decided by Step 2 (G selection on dev); M1 and M2 follow by rule | same |
| If G falls back to Qwen2.5-Coder-7B | the Qwen family is now G → becomes Option B's judge assignment (M1 = Gemma 4 12B) | unchanged (already Qwen) |
