# Model Selection Protocol — zero-cost local open-weight models (PLANNING ONLY)

Status: **proposal, not executed.** Nothing in this document has been run: Ollama is not installed on the
machine (checked 2026-10-31: no binary on PATH or in the default install folders), no weights are downloaded,
no inference has been performed. Every "measured" quantity below is a field to be filled by the procedure.

Scope rule that governs every step: **only the development split (Cli, Gson, Jsoup; 39 focal methods,
27 defects) may inform any choice** — model, quantization, prompt, threshold or gate. Held-out instances
(14 projects, 195 methods), D2 seeded faults, and any held-out execution outcome are never read by any
selection step. This is enforced in code by the existing scope lock (`src/triage/scope.py`), which will be
extended to the local backend before any step runs (see `UPDATED_MODEL_CONFIG_PROPOSAL.md` §5).

All criteria and thresholds below are fixed **before** any candidate is run. They may not be revised after
seeing candidate results; a revision requires a dated entry in `docs/tracking/DECISIONS.md` stating why, and
is reported as a deviation.

---

## Step 0 — Environment freeze (before any model is loaded)

Recorded once, into `configs/local_models.FROZEN.json` (draft in `UPDATED_MODEL_CONFIG_PROPOSAL.md`):

| Item | How it is recorded |
|---|---|
| Ollama runtime version | `GET /api/version` |
| GPU, driver, CUDA | `nvidia-smi` (RTX 5070 Ti Laptop, 12,227 MiB, driver 616.56 at planning time) |
| CPU, RAM, OS | Core Ultra 9 275HX, 31 GB, Windows 11 (host) |
| Ollama server environment | `OLLAMA_FLASH_ATTENTION`, `OLLAMA_KV_CACHE_TYPE`, `OLLAMA_NUM_PARALLEL`, `OLLAMA_MAX_LOADED_MODELS`, `OLLAMA_CONTEXT_LENGTH`, `OLLAMA_KEEP_ALIVE` — all set explicitly, never left at defaults, because each changes memory use and possibly outputs |
| Concurrency rule | generation (G, RAM offload) never runs at the same time as WSL test execution (both need tens of GB of RAM on a 31 GB machine) |

## Step 1 — Feasibility, one model at a time

Candidates (from the authors' brief): G — `gemma4:26b` (Gemma 4 26B A4B), `qwen3.5:35b` (Qwen3.5-35B-A3B,
architecture to be confirmed from `/api/show`), fallback Qwen2.5-Coder-7B-Instruct. Judges — `qwen3.5:9b`,
`gemma4:12b`, Gemma fallback `gemma4:e4b`.

Each candidate is loaded **alone** (no other model resident), with every request carrying
`options.num_ctx = 8192` explicitly. The probe set is fixed and contains **no dev or held-out instance**:
20 synthetic prompts shaped like the real ones (a judge evidence package built from a synthetic Java method;
a generator prompt for a synthetic class), so feasibility cannot leak data or tune anything.

| Measurement | Source | Pass rule (fixed in advance) |
|---|---|---|
| Model digest, quantization, family, parameter size, context length, licence text, chat template | `GET /api/show` (`details`, `model_info`, `license`, `template`, `capabilities`, `thinking`), `GET /api/tags` (`digest`) | recorded; licence must permit research use and be stored verbatim |
| GPU residency at num_ctx 8192 | `GET /api/ps` → `size`, `size_vram`, `context_length` | **Judges: `size_vram == size` (100% GPU) with `context_length == 8192`** and ≥ 0.5 GiB free VRAM (nvidia-smi) under the probe load. **G: offload allowed**, recorded as `size − size_vram` |
| RAM | Windows process working set of the Ollama runner + system free RAM | G must leave ≥ 4 GB free system RAM |
| Throughput | response `prompt_eval_count/prompt_eval_duration`, `eval_count/eval_duration` (median of 20) | recorded; feeds the compute-time projection (Step 1b) |
| Load time | `load_duration` | recorded |
| Thinking controls | `/api/show` → `thinking.values`, `thinking.default`; then probes with `think: false` | **must be able to answer with empty `message.thinking`** (Qwen: `think:false`; Gemma 4: thinking token omitted; Ollama applies the template — verified from responses, not assumed). The Ollama Gemma 4 page states that the 12B/26B/31B models still emit an empty thought block when thinking is off; its tokens must be counted (they are in `eval_count`) and the block must contain no text |
| JSON validity | `format` = the Table 11 JSON schema; parse with the existing `schema.parse_output` | judges: ≥ 98% of 20 probes valid; G: code block extractable in ≥ 95% |
| Truncation safety | `prompt_eval_count + prompt_eval_cached_count + num_predict ≤ num_ctx` on the largest probe | must hold; see risk R3 |
| Repeatability | same prompt × 5 at T = 0 with fixed `seed`; same prompt × 5 at T = 0.7, fixed seed | recorded (identical-output rate); non-determinism is reported, not a failure |

A judge that fails 100% GPU residency at num_ctx 8192 at its default quantization is retried once at the
next smaller standard quantization **of the same model**; if that fails too, the candidate is replaced by its
named fallback (Gemma: `gemma4:e4b`). The quantization actually used is the one frozen for all primary arms.

### Step 1b — Compute-time projection (decision gate on scope, not on models)
From the measured judge throughput, project the wall time of Tier 1 (E1–E3 factorial, SC-T, D2) and Tier 2/3
using the call plan in `scripts/estimate_cost.py --scope full` (≈ 96 k Tier 1 calls). If Tier 1 cannot finish
before the submission date with the measured throughput, **stop and report to the authors** — Phase 2 says
Tier 1 is never reduced, so any reduction (e.g. fewer replicates) is an authors' decision and a deviation.

## Step 2 — Select G (development split only)

Each G candidate that passed Step 1 generates tests for the 39 dev focal methods (3 generations each,
T = 0.7, max 4,096 output tokens, thinking off, same generator prompt `prompts/dev/v0/generator.txt`), and the
tests are compiled and executed on dev B and F versions with the existing harness. Criteria in strict
priority order; a lower criterion is consulted only when the higher one is within its tolerance band:

| Priority | Criterion (dev, per candidate) | Definition | Tolerance band |
|---|---|---|---|
| 1 | Compile/execution reliability | share of generated test methods that compile on both B and F and execute without TIMEOUT/ENV/FLAKY | 5 pp |
| 2 | Assertion validity | share of executed test methods that **pass on F** (their oracle agrees with the fixed program) | 5 pp |
| 3 | Line/branch coverage | mean focal-method line and branch coverage on F of the passing tests (Defects4J `coverage`) | 5 pp |
| 4 | Uniqueness / stability | share of unique normalised bodies; SD of criterion 1 across the 3 generations | 5 pp / 5 pp |
| 5 | PF/TF/AMB yield | reported for transparency only; **never maximised** | — |

**Gate (from Phase 2, P1):** PF instances ≥ 3% of executed tests on dev. A candidate that fails P1 is not
selected even if it wins criteria 1–4. If no candidate passes P1, apply the Phase 2 yield fallbacks in order
(more generations per method; the specification-based generation prompt of [12]); these apply to the
selected G only and are documented.

Differences are reported with method-level paired bootstrap 95% CIs (39 methods); a difference inside its
tolerance band counts as a tie regardless of its point estimate. Ties on all of 1–4 → the candidate with the
larger GPU-resident fraction (faster, more reproducible) wins; if still tied → `gemma4:26b` (listed first by
the authors, more memory headroom).

**Freeze G** (digest, quantization, options, prompt hash) before Step 3. G is never revisited after the judges
have been evaluated.

## Step 3 — Generate and label the development set with the frozen G
The dev tests from the selected G candidate in Step 2 **are** the dev set (no re-generation, so selection and
labelling use the same artefacts). Labels come only from execution (unchanged Phase 2 rules); the label audit
(100 dev instances) runs here.

## Step 4 — M1 (primary judge) = the judge candidate from the other family

M1 is fixed by the family rule, not by a performance contest: G = Gemma → M1 = `qwen3.5:9b`;
G = Qwen → M1 = `gemma4:12b`. "Family" means developer lineage: Qwen2.5-Coder and Qwen3.5 are the same family;
Gemma 4 12B, 26B and E4B are the same family.

M1 is then checked on the labelled dev instances (pilot sample, within-project 1:2 reading, cap 150) as a
**gate**, with the dev-version prompts:

| Gate | Rule (fixed in advance) |
|---|---|
| G-a output validity | ≥ 98% schema-valid outputs per arm (J1, SC, DEB) after the one deterministic repair (= Phase 2 P3) |
| G-b evidence citations | ≥ 90% of valid outputs cite ≥ 1 evidence id, and ≥ 95% of cited ids exist in the package |
| G-c floor/ceiling | dev J1 F1 within [0.2, 0.9] (= Phase 2 P2) |
| G-d above trivial baselines | dev J1 PF-F1 exceeds max(F1_KA, F1_R0) and the bug-level cluster-bootstrap 95% CI of the difference excludes 0. (DA has F1 = 0; KA has F1 = 2p/(1+p) = 0.50 at the designed 1:2 prevalence.) |

Reported for M1 on dev: PF precision, recall, F1, MCC, FPR, FNR, all with bug-level cluster-bootstrap CIs
(10,000 resamples), and the confusion matrix — labelled as **dev pilot, not a result**.

Prompt development (≤ 5 revision rounds per prompt, Phase 2 §3.9) happens on dev with M1 **before** the gate
is applied for the final time; G-d is evaluated once, on the frozen prompts.

### If M1 fails a gate — fallback procedure (in order; each step documented)
1. **G-a/G-b failure:** remaining prompt-revision rounds within the 5-round budget (format-only examples are
   allowed by Phase 2 if validity fails).
2. **Residency/quality failure of the model itself:** the same model at the next larger quantization that is
   still 100% GPU-resident at num_ctx 8192; for Gemma, `gemma4:e4b` is a capacity *downgrade* and is used only
   for residency failures, never to fix a quality failure.
3. **G-c or G-d still failing after 1–2:** stop and report to the authors. Options then are (a) proceed and
   report the failure as a finding (a local 9–12B judge that does not beat keep-all is itself evidence for
   RQ1), or (b) switch to the other configuration (Option B/A), which requires re-selecting G from the other
   family and regenerating the dev set. Option (b) is model selection on the dev outcome; it must be reported
   as such.

## Step 5 — M2 = the remaining judge, robustness only
M2 is used only for E5-R3 (E3 arms at S1, one replicate, D1-test and D2), never for E1–E4. M2 shares a family
with G in both configurations; this is reported as a limitation (self-preference risk in the robustness check
only). M2 passes Step 1 feasibility and gates G-a and G-b on dev; G-c/G-d are reported, not required.

## Step 6 — Freeze
One immutable file, `configs/local_models.FROZEN.json`, hashed (SHA-256 recorded in `DECISIONS.md` and in every
run's `experiment.json`), containing: Ollama version; server environment variables; for G, M1, M2: tag, manifest
digest, GGUF blob digests, quantization, family, parameter counts, licence hash, chat-template hash,
`num_ctx`, `num_predict`, `temperature`, `top_p`, `top_k`, `min_p`, `seed` policy, `think` setting, `format`
(schema hash), `keep_alive`; prompt-set hash; dev-gate outcomes. The runner refuses to call a model whose
live `/api/show` digest differs from the frozen one.

## Thinking-mode protocol
- Primary comparisons: thinking OFF for every model (`think: false`; for Gemma 4, the thinking token is not
  injected). Verified per call: `message.thinking` must be empty or absent; non-empty thinking → the call is
  logged, flagged and counted as INVALID for that arm (never silently accepted).
- All generated tokens are logged, including any thinking-channel text, so SC-T token matching uses actual
  consumed tokens (`prompt_eval_count + prompt_eval_cached_count + eval_count`, the latter including any
  empty thought block).

## Per-call logging (added to the existing call log)
prompt tokens (`prompt_eval_count`, `prompt_eval_cached_count`), output tokens (`eval_count`), durations
(`total`, `load`, `prompt_eval`, `eval`), `done_reason`, model digest, `size_vram/size` from `/api/ps` at call
time, peak VRAM from an nvidia-smi sampler (200 ms) over the call, CPU-offload bytes (`size − size_vram`),
thinking text and its length, seed, all options. Cost in USD is 0; the ledger records GPU-seconds instead.

## GPU non-determinism plan
Before the freeze, on 50 dev instances: J1 at T = 0 with a fixed seed, run twice → label-flip rate (pure
runtime non-determinism); J1 at T = 0.7 with a fixed seed, run twice → flip rate with sampling. Both are
reported. Phase 2's three replicates are kept; replicate seeds are fixed and distinct (seed = f(instance,
arm, replicate, sample index)), so a replicate is reproducible to the extent the runtime is deterministic.
