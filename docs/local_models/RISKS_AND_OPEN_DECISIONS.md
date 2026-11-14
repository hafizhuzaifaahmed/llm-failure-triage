# Technical Risks and Open Decisions (PLANNING ONLY)

## Technical risks

| ID | Risk | Why it matters | Mitigation in the protocol |
|---|---|---|---|
| R1 | **GPU time may not fit the deadline.** Tier 1 is ≈ 96 k judge calls (E1–E3 factorial, SC-T, D2), plus ≈ 1,550–1,730 generations with a partly RAM-offloaded MoE model at up to 4,096 output tokens each. Phase 3 is due 15 November. | Phase 2 says Tier 1 is never reduced; if it cannot finish, something approved must change | Step 1b projects wall time from measured throughput and stops for the authors before any generation |
| R2 | **Ollama is not installed** on this machine (checked 2026-10-31). | Everything depends on it | install is an authors' action (excluded from this task); version pinned once installed |
| R3 | **Silent truncation.** Ollama's `num_ctx` covers prompt + output; an unset or too small context truncates input without error. | A truncated evidence package corrupts results invisibly | `num_ctx = 8192` on every request; pre-call size guard; post-call check `prompt_eval_count + prompt_eval_cached_count ≥ num_ctx − num_predict` flags possible truncation; DEB adjudicator input must fit 7,680 tokens |
| R4 | **Thinking cannot be fully disabled** for some model, or Gemma's "empty thought block" leaks text. | Changes the object of study and token counts | `/api/show thinking.values` must include `false`; per-call check that `message.thinking` is empty; violations are INVALID and flagged; tokens of empty blocks counted |
| R5 | **Judge not 100% GPU-resident at 8 K** (KV cache size unknown until loaded; vision encoder resident). | Offload slows calls and breaks the residency requirement | one smaller-quant retry; Gemma → E4B for residency only; reported |
| R6 | **RAM contention:** G offload (≈ 6–11 GB in RAM) + WSL Defects4J execution (WSL limit 15 GB) on 31 GB. | Out-of-memory kills (already seen in D2 with five workers) | never run G and WSL execution concurrently; ≥ 4 GB free RAM required |
| R7 | **Small judges may fail P2/G-d** (KA's F1 is 0.50 at the designed 1:2 prevalence). | Blocks the pipeline or tempts model switching on dev outcomes | fixed gates; failure → stop for the authors (report as finding, or switch configuration and disclose) |
| R8 | **Tag drift:** Ollama tags can be re-pushed with different weights. | Irreproducible results | digest pin + blob hashes; optional blob archive (decision D7) |
| R9 | **GPU non-determinism** with flash attention / parallel slots. | Replicates are not bit-reproducible | settings fixed; variance measured on dev and reported |
| R10 | **Schema-constrained decoding** (`format`) may change accuracy or produce degenerate JSON for some models. | Arm differences could reflect formatting | identical for all arms; validity gate; Phase 2's single deterministic repair parse is kept, but no call is ever re-issued without the schema (arms stay identical) |
| R11 | **Unconfirmed facts:** Qwen3.5-35B-A3B architecture behind `qwen3.5:35b`, default quantizations, licences (Gemma 4 sources conflict). | Wrong reporting | read from `/api/show` at Step 1; licence stored verbatim |
| R12 | **Generator–M2 shared family.** | Self-preference in E5-R3 | disclosed limitation; M2 is robustness-only |
| R13 | **Dev split is small** (39 methods, 27 bugs, expected few dozen PF instances). | Wide CIs; G-selection differences may be noise; gate G-d may fail for power, not quality | 5-pp tolerance bands; paired method-level CIs; gate outcome reported with its CI |
| R14 | **Code not yet adapted** (Ollama backend, digest pin, local scope lock, context/thinking guards, VRAM sampler, GPU-time ledger, coverage for G selection). | Protocol cannot run as written | listed in `UPDATED_MODEL_CONFIG_PROPOSAL.md` §5, each with unit tests against a fake server |
| R15 | **Multimodal builds** may carry extra memory and template behaviour. | Residency and token counts | measured in Step 1 |

## Open decisions for the authors

| ID | Decision | Options | Recommendation |
|---|---|---|---|
| D1 | Adopt the local-model design (L-1 … L-10) in place of the API design | adopt / keep API pilot / both | needs your decision; the paid pilot request (`PILOT_READINESS_REPORT.md`) becomes moot if you adopt local-only |
| D2 | Install Ollama (which version) | latest stable at install time, then pinned | pin whatever version Step 0 records |
| D3 | If Tier 1 does not fit the time available (R1) | reduce replicates 3 → 2 / restrict SC-T / extend timeline / drop D2 from Tier 1 | decide after Step 1b numbers; any choice is a reported deviation |
| D4 | If M1 fails G-c/G-d after the fallback ladder | report as a finding / switch configuration (disclosed) | report as a finding (switching is selection on dev outcome) |
| D5 | Gemma E4B as judge fallback for residency only | accept / reject | accept, reported if used |
| D6 | Server settings fixed in Step 0 (flash attention, KV type, parallel slots) | fix for speed (parallel > 1) vs for determinism (parallel = 1) | decide after measuring both in Step 1 on synthetic probes |
| D7 | Archive GGUF blobs with the release | archive (≈ 30–40 GB) / digests only | digests + upstream cards; archive if storage allows |
| D8 | Status of X-01 / D-18 (OpenRouter pins) and the paid pilot | withdraw / keep as alternative | withdraw if D1 = adopt |
| D9 | X-07 sampling | unchanged: pending your review | — |
| D10 | Instructor feedback | still needed for the feedback register | — |
