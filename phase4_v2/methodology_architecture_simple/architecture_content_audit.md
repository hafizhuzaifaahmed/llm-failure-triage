# Architecture content audit: simplified methodology diagram

**What this audit covers**

- The diagram: `research_methodology_architecture_simple.drawio`, exported as `.pdf`, `.svg` and `.png`.
- The generator: `build_methodology_architecture_simple.py`, run from the repository root.
- The diagram simplifies `../methodology_architecture/research_methodology_architecture.drawio`, which is left unchanged.

**Status key**

| Code | Meaning |
|---|---|
| **R** | Represented in the main architecture |
| **S** | Summarised in a supporting annotation (the experimental strip, a footnote line, or a note inside a stage) |
| **O** | Documented outside the diagram: too detailed for the figure; the source and this audit hold it |

## 1. Sources

| Short name | File | Contents |
|---|---|---|
| Paper | `phase4_v2/PHASE4_FINAL_PAPER.tex` | §III Proposed Methodology (A–F), §IV Experimental Setup with Table III (changes from the approved design), §V Results, §VII Ablation Study |
| Supplement | `phase4_v2/PHASE4_FINAL_SUPPLEMENT.tex` | deviations X-01 to X-07, extended analyses |
| config | `src/triage/config.py` | protocol constants and seeds |
| FROZEN | `configs/local_models.FROZEN.json` | executed models, decoding, k_T (frozen under D-57) |
| cfp / wdp / osf | `configs/extension/cfp_frozen.json`, `wdp_frozen.json`, `osf_registration.json` | the two probe studies and the registered confirmation |
| numbers | `phase4_v2/generated/numbers_v2.tex` | every count the paper prints |
| DECISIONS | `docs/tracking/DECISIONS.md` | decision log (cited only where the paper defers to it, e.g. D-53) |

The figure contains **no numerical research findings**: no F1, MCC, CI or p-value. The only numbers it shows are design parameters, all checked against config, FROZEN or the paper:

- 17 / 3 / 14 projects;
- 3 generations per method, T = 0.7;
- 3 runs, a 30 s timeout;
- 5 calls of ≤ 512 tokens;
- 2 TF per PF.

## 2. Component checklist

### Datasets and partitioning
| Component | Shown as | Status | Source |
|---|---|---|---|
| D1 Defects4J 3.0.1, real faults, 17 projects | cylinder | R | config `D4J_PROJECTS` (17); Paper §IV |
| Frame 312 methods / 220 defects; cap of 25 per project → 234 / 167 sampled | — | O | numbers `split:*`; config `MAX_FOCAL_PER_PROJECT`; Paper Table III (X-03) |
| Project-level split: 3 development, 14 held-out projects | box | R | config `N_DEV_PROJECTS`, `SEED_SPLIT`; numbers `der:n test projects` |
| Development data used only for prompts, calibration (k_T) and the pilot | note | S | Paper §IV; FROZEN `dev_evidence` |
| D2 seeded faults: one killed Major mutant in a held-out focal method (≤ 2 per method), contamination control | cylinder | R (mutant cap: O) | config `MAX_MUTANTS_PER_FOCAL`; `src/triage/d2.py`; Paper §IV |

### Test generation and execution
| Component | Status | Source |
|---|---|---|
| Generator G = Gemma 4 26B-A4B, 3 generations per method, T = 0.7 | R | FROZEN `temperature.generator` = 0.7; config `GENERATIONS_PER_FOCAL`; `src/triage/generation.py` |
| Generation from the buggy context only | O | Paper §IV, `generation.py` |
| Compilation against buggy (B) and fixed (F) versions | R | Paper §III-C |
| Pruning of non-compiling methods, ≤ 3 passes | O | config `MAX_COMPILE_PRUNE_PASSES` |
| Execution: 3 runs on each version, fresh JVM, 30 s timeout | R | config `RUNS_PER_VERSION`, `TEST_TIMEOUT_S`; Paper §III-C |
| Failure evidence: outcome, message, stack trace | R | `src/triage/execution.py`; Paper §III-D |
| Environment: Ubuntu 22.04.5 under WSL2, OpenJDK 11 | S | Paper §IV; Supplement X-04 |
| Recorded environment manifest (instead of the planned Docker image) | O | Paper Table III; Supplement X-04 |

### Preprocessing and evidence
| Component | Status | Source |
|---|---|---|
| Filtering of flaky, timeout, environment and non-compiling outcomes; ENV re-run once | R (re-run: O) | config `ENV_RERUNS`; Paper §III-C |
| De-duplication of test bodies (normalised-body hash) | R | `src/triage/preprocess.py` |
| Normalisation of stack traces (≤ 25 frames, framework frames collapsed, paths and hashes scrubbed) | R (limits: O) | config `MAX_STACK_FRAMES`, `MAX_MESSAGE_CHARS` |
| Length limits: Javadoc ≤ 600, specification ≤ 400, package ≤ 6,000 tokens | R as "length limits" (values: O) | config `MAX_*_TOKENS` |
| Leakage guard: blocks bug ids, fix-changed lines, focal-body lines and paths | R | Paper §III-D; config `LEAKAGE_GUARD` |
| Evidence package with citable item ids; S0 = test + failure + signature, S1 = S0 + Javadoc, S2 = S1 + inferred spec | R | Paper §III-D; `src/triage/context_builder.py` |
| Specification inference: once per method at T = 0, from signature, Javadoc, call sites (≤ 5) and sibling docs; fix-changed lines removed | O | Paper §III-D; config `SPEC_TEMPERATURE`, `MAX_CALL_SITES`; `src/triage/spec_inference.py` |
| Withheld from every method: focal body, fixed version, patch, developer tests, bug ids, labels | S (leakage guard and ground-truth header) | Paper §III-D |

### Triage methods
| Component | Status | Source |
|---|---|---|
| Three families fed by the same evidence package (shared fan-out connector) | R | Paper §III-E, Table II |
| Non-LLM baselines DA, KA, R0 (0 calls) | R | Paper Table II |
| Single-agent LLM J1, SC (majority of 5, ties → TF), SC-T (k_T = 5, token-matched) | R (tie rule, k_T value: O) | Paper Table II; FROZEN `decoding.k_T` |
| DEB: Advocate-P and Advocate-T → Rebuttal-P and Rebuttal-T → Adjudicator → prediction; 5 calls | R | Paper Algorithm 1, §III-E |
| Each rebuttal answers the opposing round-1 argument; the adjudicator reads all four, anonymised | S (note in the stage) | Paper Algorithm 1 |
| Seeded random argument order; the adjudicator decides from cited evidence ids | O | config `SEED_ARGUMENT_ORDER`; Paper §III-E |
| Controls: same judge M1 (Qwen3.5 9B), decoding and evidence for every LLM method | S (control note) | FROZEN `frozen_models.M1`; Paper §IV |
| Decoding values (temperature, top-p, 8,192 context, per-call seed, thinking off, Ollama 0.40.13) | O | FROZEN; Paper §IV |
| Equal budget: SC and DEB 5 calls of ≤ 512 tokens; SC-T matched to DEB's consumed tokens | S (control note) | config `MAX_OUTPUT_TOKENS`; Paper §IV |
| Prompts frozen after 5 development rounds, before any held-out call | O | Paper §IV; DECISIONS D-57 |
| KUU (unanimous TF vote of three judge families) | S (strip: supplementary) | Paper §III-F |

### Prediction interface
| Component | Status | Source |
|---|---|---|
| Structured output: PROGRAM_FAULT or TEST_FAULT, reason, cited evidence ids | R | Paper §III-E; config `LABELS`, `REASON_CATEGORIES`; `src/triage/schema.py` |
| Full JSON schema (summary, descriptive confidence, SC vote share, DEB round positions, cost log) | O | `schema.py` |
| One deterministic repair parse; still-invalid output scored TF | R | Paper §III-E |
| Invalid outputs excluded in a sensitivity analysis | O | Paper §III-E |

### Evaluation
| Component | Status | Source |
|---|---|---|
| Scoring that joins predictions to the sealed labels | R | Paper §III-C, §IV |
| Classification: precision, recall, F1, FPR, FNR, MCC | R | Paper §III-A; `src/triage/metrics.py` |
| TPR, TNR, balanced accuracy, IPW precision, PR-AUC of the SC vote share | O | Paper §III-A, §IV |
| Error and retention: PF tests lost, FP / FN analysis | R | Paper §IV |
| Statistics and cost: bug-level bootstrap, Holm, calls / tokens / latency | R | config statistics block; Paper §IV |
| 10,000 resamples; ±0.05 F1 equivalence on a 90 % CI; McNemar, Wilcoxon and leave-one-project-out sensitivity; exploratory mixed model | O | config; Paper §IV; Supplement X-02 / X-06 |
| Scoring unit (one failing test), replicate averaging, AMB and leakage-aborted instances excluded | O | Paper §IV |

### Sealed ground-truth channel
| Component | Status | Source |
|---|---|---|
| Separate pathway beneath the workflow: execution outcomes → classification → sealed labels → scoring | R | Paper §III-B, §III-C |
| PF = fails on B, passes on F; TF = fails on B and F with the same signature | R | Paper §III-C; `src/triage/labeling.py` |
| Labels never visible to any LLM or triage method; used only at evaluation (dashed connector) | R | Paper §III-C; config `GT_STORE` comment |
| Evaluation sample: all PF plus 2 TF per PF over the split, project-stratified, IPW weights | S (one line in the label box) | config `PF_TO_TF_RATIO`; DECISIONS D-53 |
| Failure signature σ = (outcome type, exception class, failing line), deterministic over 3 runs | O | Paper §III-C |
| AMB (both fail, signatures differ): sensitivity analysis only | O | Paper §III-C |
| Excluded outcomes: flaky, timeout, ENV, non-compiling | O | Paper §III-C |
| Instance selection hands only ids to the context builder | O (deliberately not drawn, see §4) | config `GT_STORE` / `LEAKAGE_GUARD` |

### Experimental conditions and additional analyses (strip)
| Component | Status | Evidential status shown | Source |
|---|---|---|---|
| Specification availability S0 / S1 / S2 (E2; H2a, H2b) | S | solid: confirmatory | Paper §IV |
| Arm comparison (E1; H1) and equal budget (E3; H3a, H3b) | S | solid: confirmatory | Paper §IV |
| Ablations A1–A5b (E4) | S | dashed: exploratory | Paper §VII |
| Robustness: D2, second judge M2 (Gemma 4 12B), per-project analysis (E5) | S | dashed: exploratory | Paper §V-C |
| Further judges (Qwen3.5 35B, Ministral 3 14B), three-family vote, frontier reference judge | O | — | Paper §V-C, Supplement |
| Registered confirmation C1–C4 (OSF kp79c), one Holm family | S | solid: confirmatory | osf; Paper §V (`sec:confirm`) |
| Judge-only rules (KUU, cascade, KUU-NG), mutation-probe pilot, whole-method probes | S | dashed: supplementary or exploratory | Paper §III-F, §V; cfp; wdp |
| Probe mechanics: ≤ 80 mutants, ROR / AOR / COR / LVR / NEG / STD, FLIP / SHIFT / SAME / ERR, ≥ 10 compiled for "decoupled" | O | — | Paper §III-F; cfp |
| Probes run on the buggy version only, without LLMs or labels | S (strip note) | — | Paper §III-F |

### Research questions
| Component | Status | Source |
|---|---|---|
| Analytical objectives footer: accuracy and test loss, specification effect, architecture effect, efficiency, robustness, judge-only and probe-based rules | S | Paper §I (RQ1–RQ6) |
| Hypothesis wording, results, intervals, p-values | O (not shown by design) | Paper §V, tables |

## 3. Exclusions checked
- GitBug-Java and D3 do not appear anywhere. A text search of the `.drawio` file finds "d3" only inside the connector id `ed3`.
- No project-stage or milestone labels ("Phase …", "later additions", chronology).
- Colours used: only `#000000`, `#FFFFFF` and `#F2F2F2` (light-grey stage fill).
- The figure has 90 draw.io cells, against 155 in the previous diagram.
- Nesting is at most two levels: stage, then box.

## 4. Design decisions that affect content
1. **KUU is not drawn as a non-LLM baseline.** It aggregates J1 votes from three LLM judges, so calling it non-LLM would be inaccurate. It sits in the strip under supplementary investigations. This matches the paper, which treats it as a later baseline for the judge-only rules.
2. **No connector from the ground-truth channel to the context builder.** The label-based evaluation sample decides *which* instances are judged, and only instance ids cross. Drawing that link would visually connect labels to a judge's input. The figure therefore keeps the stricter rule that the channel connects only to evaluation, and the sample rule appears as a line inside the sealed-label box.
3. **The rebuttals' cross-input is stated, not drawn.** Each rebuttal receives both round-1 arguments (Algorithm 1). Crossing arrows were replaced by straight same-side arrows plus a one-line note.
4. **No dashed line marks LLM calls.** Every LLM component is named in its family title ("Single-agent LLM", "DEB", "Gemma 4", "M1"). Dashed lines are reserved for (a) sealed labels and (b) exploratory or supplementary status, as the brief requires.

## 5. Export and verification
- **Canvas.** draw.io's A3 landscape page, 1654 × 1169 units. 1 unit = 0.254 mm = 0.72 pt on A3.
- **Font sizes.** The smallest text is 16 units (11.5 pt). Stage headers are 17 units (12.2 pt); the title is 22 units (15.8 pt).
- **Exports.** The official diagrams.net viewer engine (`viewer-static.min.js`, `Graph.getSvg()`) produced the SVG in headless Chrome, because draw.io Desktop is not installed.
  - **PDF:** one A3 landscape page, 420 × 297 mm (checked with pypdf), with vector text.
  - **PNG:** 2×, 3308 × 2338 px.
- **Editor check (14 Nov 2026).** Opened in the diagrams.net editor at app.diagrams.net: one page, "Methodology architecture". Shapes are native and selectable; selecting the Adjudicator showed its Style, Text and Arrange panels. The editor rendered in its dark UI theme; the file's page background is white.
- **Quality review.** Three render passes, each checked at full page and on zoomed crops at full resolution, plus a 150 dpi raster of the PDF. Fixes made:
  - the connector that crossed the ground-truth header;
  - orphan line wraps ("(F)", "arguments", "same decoding");
  - unequal box heights;
  - the predictions arrow landing on a single metric box (Scoring is now its own box);
  - a legend dash too short to read as dashed;
  - the C1–C4 wording: C1–C2 are mutation-outcome rates, not certificates.
- **Readability questions from the brief, answered on the final render.**
  - Main flow: left to right, six stages, single entry and exit arrows.
  - Ground-truth isolation: separate heavy-bordered channel, header rule, one dashed arrow into Scoring only.
  - Families: three labelled blocks fed by one fan-out.
  - DEB: a three-column sequence plus one note.
  - Readable at A3: yes, minimum 11.5 pt.
