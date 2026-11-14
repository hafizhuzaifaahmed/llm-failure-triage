# Zero-Cost Reproducibility Plan (PLANNING ONLY)

Goal: a reader with comparable hardware can rebuild every number at zero API cost, and a reader without a GPU
can recompute every metric from released artefacts. Nothing below has been executed.

## 1. What is pinned
| Layer | Pin | Where recorded |
|---|---|---|
| Ollama runtime | exact version (`/api/version`) and installer hash | `configs/local_models.FROZEN.json`, `env/environment_manifest.json` |
| Server behaviour | `OLLAMA_FLASH_ATTENTION`, `OLLAMA_KV_CACHE_TYPE`, `OLLAMA_NUM_PARALLEL`, `OLLAMA_MAX_LOADED_MODELS`, `OLLAMA_KEEP_ALIVE`, `OLLAMA_CONTEXT_LENGTH` | frozen config |
| Model weights | Ollama tag **and** manifest digest **and** SHA-256 of every GGUF blob (projector included); chat template hash; licence text hash | frozen config |
| Decoding | `num_ctx`, `num_predict`, `temperature`, `top_p`, `top_k`, `min_p`, `think`, `format` schema hash, seed derivation rule | frozen config + every call record |
| Prompts | prompt-set hash and per-file hashes (`prompts/frozen/<name>/MANIFEST.json`) | frozen config, `experiment.json` |
| Data | frame, split, samples, D2 mutants, labels (unchanged pipeline, seeds in `config.py`) | `data/processed`, `data/ground_truth_store` |
| Hardware | GPU, VRAM, driver, CUDA, CPU, RAM, OS | frozen config |
| Python client environment | `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8` (D-73): without them Windows Python reads files in the local code page (cp1252) and the D2 dataset build fails on the first non-ASCII candidate. Set by `scripts/local/session_env.ps1`/`.sh` (Windows) and `scripts/wsl/run.sh` (WSL) | `env/environment_manifest.json` (`python_env`) |

Ollama tags can be re-pushed with different weights. The digest check makes a mismatch fail loudly; it cannot
restore old weights. **Open decision for the authors:** archive the exact GGUF blobs (≈ 7–8 GB per judge,
16–22 GB for G) alongside the release, or rely on the digest plus the upstream model card.

## 2. Determinism and variance
- Same weights + runtime + options + seed reproduce outputs only to the extent the GPU kernels are deterministic;
  batching (`OLLAMA_NUM_PARALLEL > 1`) and flash attention can change results. Both are fixed for the study.
- Measured before the freeze (dev only): T = 0 repeat agreement and T = 0.7 fixed-seed repeat agreement (label
  flip rates on 50 dev instances). Reported in the paper's setup.
- Phase 2's three replicates remain the inferential answer to stochasticity; per-call seeds make them auditable.

## 3. Three levels of reproduction
Every level: run the Python entry points from a shell that has sourced `scripts/local/session_env.ps1` or `.sh` first (D-73).

| Level | Needs | Command (once implemented) | Reproduces |
|---|---|---|---|
| R-A Recompute | released decisions + labels | `python scripts/analyze.py --runs …` | every table, CI, test and figure exactly |
| R-B Replay | released call log | `python scripts/run_experiment.py <cfg> --replay` | every decision from logged responses, no GPU, no network |
| R-C Re-run | Ollama + same digests + GPU | `python scripts/run_experiment.py <cfg>` (local backend) | new draws; expected to agree within the measured variance, not bit-for-bit |

## 4. Released artefacts (on completion; none released yet)
Frozen config and its hash; prompts; generated tests; raw executions; labels; leakage-guard file; samples
(both X-07 readings); call log with prompts, outputs, thinking text, token counts, durations, VRAM and seeds;
decisions; analysis outputs; D2 mutants; environment manifests; this plan.

## 5. Zero-cost accounting
USD cost is 0 by construction (no API). The ledger records GPU-seconds, energy proxy (GPU-seconds × measured
board power, optional) and wall time per arm, so the paper's efficiency analysis (F1 per 1,000 tokens, calls,
latency) stays intact; "cost" in USD is reported as not applicable.

## 6. Isolation guarantees carried over
Label store isolation, the leakage guard before every call, and the scope lock (dev-only selection) apply
unchanged to the local backend once code change 3 in `UPDATED_MODEL_CONFIG_PROPOSAL.md` §5 is made.
