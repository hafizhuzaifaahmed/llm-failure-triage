# Pilot-readiness report — FINAL DRAFT FOR APPROVAL

Date: 2026-10-30. **No paid API call has been made. No experiment has been run with a real model.**
`configs/budget.json` does not exist, so every paid entry point refuses to run. Paid calls start only after the
authors explicitly approve this report and create that file from `configs/budget.pilot.PROPOSED.json`.

Every number below is a software-verification result, a local data-preparation measurement (no LLM), or a cost
*estimate*. None is a research result.

---

## 1. What the pilot is — and is not

| | |
|---|---|
| Data | **Development split only**: projects Cli, Gson, Jsoup — 39 focal methods from 27 defects |
| Purpose | real generated tests + labels; pilot gates P1–P5; prompt development and freeze |
| Models | M1 `deepseek/deepseek-chat-v3-0324` and G `openai/gpt-4.1` only (M2 not used) |
| Spend | **hard maximum US$16.00** total provider expenditure, enforced in code |
| Providers | one pinned provider per model, **no fallbacks** |
| Not included | any held-out (14 test projects) call; D2 or D3 generation; M2; ablations; S2′; extra generations if P1 fails; any expansion toward the full programme |

## 2. Confirmation: the pilot uses only development data and cannot reach the held-out set

Enforced by code (`src/triage/scope.py`), not by convention. The approved budget file carries the scope:
`allowed_splits: ["dev"]`, `allowed_experiments: ["PILOT_dev"]`, `allowed_models: [M1, G]`,
`require_pinned_no_fallback: true`.

| Path to held-out data | Control | Tested by |
|---|---|---|
| Test generation for a held-out focal method | `generate_tests.py` refuses a non-dev split and checks the split of every context before any prompt is built | `test_held_out_items_are_refused` |
| Spec inference for a held-out method | `infer_specs.py`: same check; `--split` is mandatory for paid runs; `--prime` (S2′) refused in the pilot scope | same |
| Judging held-out instances | `run_experiment.execute` refuses (a) any experiment other than `PILOT_dev`, (b) any split other than `dev`, (c) any sampled instance whose split differs from the experiment's | `test_paid_run_refuses_unapproved_experiment_and_test_split` |
| Held-out instances existing at all | none can: held-out tests are never generated, because (1) is refused | — |
| Using another model | the client refuses any model not in `allowed_models` before sending | `test_unapproved_model_is_refused_before_sending` |
| Fallback to another host | routing must pin one provider with `allow_fallbacks: false`, else refused; if the response reports a different provider, the call is logged and counted and the run **stops** | `test_fallback_routing_is_refused`, `test_provider_mismatch_stops_and_is_counted` |
| Labels reaching a judge | judges read instances only; the label store is read only by `analyze.py`; packages are checked against the leakage guard before every call | `test_guard_rejects_bug_ids_and_fixed_lines_before_any_call`, mock e2e |

Two facts stated for completeness: (i) the B-side code contexts of the 195 held-out focal methods already exist
on local disk from the frame build; under the scope lock they are never placed in a prompt. (ii) The Spec
Inferencer's call-site context comes from the focal method's own project, so dev prompts contain only dev-project
code.

## 3. Final D2 build (local; Major; no LLM, no cost)

Source: `data/processed/d2_mutants.jsonl`, summary `data/processed/d2_summary.json` (`scripts/summarise_d2.py`).
D2 is not used by the pilot; it is built now because it needs no LLM.

**All 195 held-out focal methods processed (final).** The last one, Math_15 `FastMath.pow` (a class with
≈ 8,600 mutants), reached the 2-hour limit of Major's kill analysis and is recorded as `ANALYSIS_FAILED`.

| Outcome per focal method | Count |
|---|---|
| ≥ 1 verified mutant (`OK`) | **148** |
| no killed mutant in the focal method (`NONE_KILLED`) | 14 |
| class has no applicable operator (`NO_CLASS_MUTANTS`) | 13 |
| no mutant inside the focal method (`NO_FOCAL_MUTANTS`) | 5 |
| killed mutants exist but none could be placed/verified (`NONE_VERIFIED`) | 5 |
| Major could not mutate the project (`MUTATION_FAILED`): Mockito "Cannot mutate project" ×5; Math_54 `Dfp` first pass exceeded 1 h ×1 | 6 |
| kill analysis failed (`ANALYSIS_FAILED`): Math_16 `FastMath.cosh` killed for memory (5 parallel workers) ×1; Math_15 `FastMath.pow` exceeded the 2 h limit ×1; Mockito ×2 | 4 |

**Verified mutants: 284** (1.92 per OK method; cap is 2), by operator ROR 76, LVR 60, AOR 51, COR 51,
STD 45, SOR 1; by project Lang 50, Chart 42, Compress 42, Math 41, Time 34, JacksonDatabind 26,
JacksonCore 22, Mockito 9, Codec 5, Closure 4, JxPath 4, Csv 2, JacksonXml 2, Collections 1.
Each verified mutant lies inside the focal method, is killed (FAIL/EXC) by Major's analysis, compiles, and
fails ≥ 1 relevant developer test when built from source. Placement attempts: 284 verified, 18 not placeable,
7 did not compile, 1 not killed when built from source, 1 verification timeout. 97.9% of all focal-method
mutants in processed methods can be placed exactly in source.

Limitations to report: the 10 tool failures (Mockito with Major; three very large Math classes) and the 14 + 5 + 13
methods without a usable mutant reduce D2 coverage of Mockito, Closure and Math relative to the frame. A
single-worker retry of `FastMath.cosh` is possible later at no cost; it is not needed for the pilot.

## 4. Deviation X-07 — sampling (PENDING, not applied)

Full analysis: `docs/tracking/SAMPLING_ANALYSIS.md`.

**What Phase 2 says.** C9: "Keep all PF instances and sample TF instances at random, stratified by project, to a
PF:TF ratio of 1:2." §4.8: "D1-test ≈ 720 instances (all PF, ≈ 240 expected, plus twice as many TF)." The text
does not say whether the 1:2 ratio holds **inside each project** or **overall**.

**The issue.** Applied within each project, a project that yields no PF instance contributes no TF instance and
disappears from the sample, and a project with fewer than twice as many TF as PF pulls the overall ratio below
1:2. Applied overall (TF quota = 2 × total PF, spread across projects in proportion to their TF counts), every
project stays represented and the overall ratio is exactly 1:2.

**Consistency with Phase 2.** Both readings satisfy everything the text fixes (all PF kept, random TF, project
strata, 1:2, inverse-probability weights); neither contradicts it. §4.8's "all PF … plus twice as many TF"
leans toward the overall reading; C9's word order can be read either way.

**What is done now.** The proposal is **not applied**. The primary samples, including the pilot sample, use the
within-project reading the pipeline already implemented; the overall reading is generated only as files named
`…_X07_proportional_PENDING.json`, so its effect (projects dropped, realised ratio, weights, and — once decisions
exist — F1/precision/FPR) can be measured side by side. The decision for D1-test is yours, after the pilot.
(The previous pass had made the proportional reading the default; that was reverted.)

## 5. Final provider-pinned models, pricing and spending configuration

From `configs/providers.json` (OpenRouter endpoint API, 2026-10-30). OpenRouter bills inference at the provider's
listed price without markup and takes 5.5% when credits are bought.

| Role | Model id | Pinned provider (routing) | Rate in / out per 1M | Other endpoints (used only for the conservative bound) |
|---|---|---|---|---|
| M1 | `deepseek/deepseek-chat-v3-0324` | GMICloud fp8 — `{"order": ["gmicloud/fp8"], "only": ["gmicloud"], "allow_fallbacks": false, "require_parameters": true}` | $0.29 / $1.14 | SiliconFlow $0.25 / $1.00 |
| G | `openai/gpt-4.1` | OpenAI — `{"order": ["openai"], "only": ["openai"], "allow_fallbacks": false, "require_parameters": true}` | $2.00 / $8.00 | Azure $2.00 / $8.00; Azure swedencentral $2.20 / $8.80 |
| M2 (not in pilot) | `qwen/qwen3-235b-a22b-2507` | DeepInfra fp8 | $0.09 / $0.55 | — |

**Spending configuration** (`configs/budget.pilot.PROPOSED.json`, inactive until approved):
`approved_usd: 16`, `scope: dev_pilot`, splits `[dev]`, experiments `[PILOT_dev]`, models `[M1, G]`, pinned/no-fallback required.

**How the $16 is enforced.** Before every HTTP attempt the client journals a reservation equal to the call's
maximum possible cost (highest listed endpoint rate, 2.5 chars/token, full output cap) and refuses if recorded
spend + possibly-charged reservations + in-flight reservations + this reservation would exceed $16. The cost
recorded for a completed call is the provider-reported `usage.cost`. Failed attempts that may have reached the
provider, and orphaned attempts after a crash, stay counted at their maximum. A crash after the provider
accepted a request but before its response was logged can cause that request to be sent again (and charged
twice); this is bounded and counted, not impossible.
**Recommended external backstop:** also set a $16 credit limit on the OpenRouter API key itself.

## 6. Pilot cost — exact scope

| Step | Model | Calls (max) | Input tok/call exp. / cons. | Output tok/call exp. / cap | Expected $ | Conservative $ |
|---|---|---|---|---|---|---|
| P0 test generation (39 × 3) | G | 117 | 779 / 1,090 | 2,500 / 4,096 | 2.52 | 4.95 |
| P1 S2 specs (39) | M1 | 39 | 1,554 / 2,175 | 300 / 512 | 0.03 | 0.05 |
| P2 J1 at S1 (≤ 150) | M1 | 150 | 1,560 / 2,184 | 200 / 512 | 0.10 | 0.20 |
| P3 SC at S1 (5 × ≤ 150) | M1 | 750 | 1,560 / 2,184 | 200 / 512 | 0.51 | 1.00 |
| P4 DEB at S1 (5 × ≤ 150) | M1 | 750 | 1,990 / 2,786 | 260 / 512 | 0.66 | 1.15 |
| P5 prompt dev: J1 (≤ 5 rounds) | M1 | 750 | 1,560 / 2,184 | 200 / 512 | 0.51 | 1.00 |
| P6 prompt dev: advocates + adjudicator (≤ 5 rounds) | M1 | 3,750 | 1,990 / 2,786 | 260 / 512 | 3.28 | 5.74 |
| P7 prompt dev: Spec Inferencer (≤ 5 × 39) | M1 | 195 | 1,554 / 2,175 | 300 / 512 | 0.15 | 0.26 |
| P8 Spec Inferencer scoring: J1 at S2 (≤ 5 × ≤ 150) | M1 | 750 | 1,988 / 2,784 | 200 / 512 | 0.60 | 1.15 |
| P9 R4 paraphrase validity (2 × ≤ 150) | M1 | 300 | 1,560 / 2,184 | 200 / 512 | 0.20 | 0.40 |
| **Total** | | **7,551** | | | **8.57** | **15.91** |

Expected tokens: GPT-4.1 ≈ 91 k in / 293 k out; DeepSeek-V3 ≈ 13.85 M in / 1.78 M out.
Conservative = highest endpoint rate (G $2.20/$8.80), 2.5 chars/token (measured ≈ 3.5), every output at its cap,
+10% for failed attempts that may be charged. P0/P1/P7 input sizes come from the real prompts of the 39 dev
methods; judge inputs use a fixed stub for the not-yet-existing failing test (751 chars, 10 frames).
**Hard ceiling: $16.00. Credit top-up incl. 5.5% fee: $16.88.** The judged set is capped at 150 instances (X-09).

**Stopping rules** (stop and report before further spend): P1 PF yield < 3%; P3 invalid ≥ 2% in an arm after the
allowed revisions; systematic label-audit disagreement (P5); guard at the ceiling; provider mismatch; any
anomalous leakage-rejection rate.

**Deliverables.** (1) Dev generated tests, raw executions, labels, PF/TF/AMB and exclusion counts (P1).
(2) Blinded label-audit sheets for both authors (100 dev instances; fewer if the dev split yields fewer) and
spec-audit sheets. (3) Measured tokens per call per arm → k_T and a re-estimated full-programme cost (P4).
(4) Dev J1 F1 and invalid-output rates (P2, P3). (5) Frozen prompt set with hashes, incl. two J1 paraphrases.
(6) A pilot report with real spend from the call log vs this estimate, and X-07's measured effect on dev.

## 7. Corrective items and verification (both passes)

| # | Item | Result |
|---|---|---|
| 1 | Leakage guard on the live path | wired into `run_experiment.execute`/`Runner`; short-id hole fixed; e2e test + mock planted leak: 0 of 12,330 prompts |
| 2 | Budget safety | unknown price = error; journal; possibly-charged accounting; replay mode; honest docs |
| 3 | Paper accuracy | data availability, regeneration claim, abstract tense, MitGen, tables, X-07 wording; authors and emails set |
| 4 | GLMM | implemented; VB intervals under-cover (50–70%) → bootstrap intervals (X-06); not run on real data |
| 5 | D2 + audits | D2 built (§3); audit generator, scorer, instructions ready; sheets need real data |
| 6 | Sampling | X-07 analysed, **pending, not applied** |
| 7 | Provider and cost | pinned, verified, provider-reported cost stored; scope lock added |

| Check (this pass) | Result |
|---|---|
| Unit tests | **70 passed** |
| Defects4J Lang-1 integration | **PASSED** (all 7 label rules + NC pruning) |
| Mock e2e via `run_experiment.execute` | 3,424 decisions, 0 errors, 34 rejections (planted leak), 0 leaks sent |
| No mock output in research locations | **CLEAN** |

Bugs found and fixed across the passes: short bug ids escaped the leakage check; stale compile metadata after a
re-checkout; Major offset semantics; CRLF offsets; unsorted seeded order; concurrent preparation of a shared
checkout; GLMM interval under-coverage (methodological).

## 8. Still unexecuted
All experiments E1–E5; GLMM on real data; human audits; D3 (blocked: Docker); R4 paraphrases (written before the
freeze); D2 test generation (needs a separate held-out approval).

## 9. Decisions requested
1. Approve this report → create `configs/budget.json` from the proposed file and set `OPENROUTER_API_KEY` yourself
   (recommended: a $16 credit limit on the key).
2. Approve the provider change and pins (X-01, D-18).
3. Instructor feedback text (none recorded yet).
X-07 stays pending until you have reviewed its measured effect.
