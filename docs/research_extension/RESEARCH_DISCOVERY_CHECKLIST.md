# Research discovery checklist

State on 2026-11-11, branch `research-extension`. **Done** means the artefact exists and was checked; **Designed**
means written but not run; **Blocked** names the blocker.

## Phase 0: reconstruct the project

| Item | Status | Artefact |
|---|---|---|
| Git state, branch, commit discrepancy (`0c16659` deck stamp, `3f320fa` notes, HEAD `5138443`) | Done | `PROJECT_FACT_BASE.md` §1 |
| Repository instructions and standing rules | Done | `PROJECT_FACT_BASE.md` §6 |
| Paper PDF (26 pp) read in full, including Appendices A–H | Done | `EXPERIMENT_AND_RESULT_MAP.md` |
| Deck: all 65 slides and speaker notes extracted; headline numbers spot-checked against the paper | Done (spot check, 12 values; not every number) | `EXPERIMENT_AND_RESULT_MAP.md` §3 |
| Prior notes file `Pasted markdown(20261111-052523).md` | **Not available** on disk; not substituted | `PROJECT_FACT_BASE.md` §1 |
| Separate external reviewer report | Not found; the two mock-review rounds and the response matrix were read | same |
| Decision log | Read directly: the opening entries (D-01 to D-19) and the closing ones (the D-131 result and D-132). **Not read:** D-20 to D-130; their content was taken from the paper's appendices and traceability table, which cite them | — |
| Result provenance table | Done (18 headline claims) | `EXPERIMENT_AND_RESULT_MAP.md` §2 |
| Current architecture and where tests are lost | Done | `CURRENT_ARCHITECTURE.md` |
| Limitations: validity versus scope | Done | `LIMITATIONS_AND_OPEN_QUESTIONS.md` |
| Resources: GPU, RAM, disk, models, WSL, Defects4J checkouts | Done | `PROJECT_FACT_BASE.md` §5 |
| Baseline tests | Done: 356 pass on `5138443` | — |

## Phase 1: literature

| Item | Status | Artefact |
|---|---|---|
| Two scouted searches (SE closest work; decision methods) plus three verification searches | Done, with stated limits: most entries read at abstract or search-summary level | `LITERATURE_MAP.md` |
| Machine-readable comparison | Done (15 rows) | `RELATED_WORK_COMPARISON.csv` |
| Collision check with queries | Done | `NOVELTY_COLLISION_CHECK.md` |
| Full-text reading of the works to be cited | **Not done** (ACM DL and IEEE full texts not opened) | listed per entry by read code |

## Phases 2–3: bottleneck and candidates

| Item | Status | Artefact |
|---|---|---|
| Zero-call error-strata analysis | Done | D-133; `results/extension/ext0_error_strata.json` |
| Bottlenecks ranked with evidence and falsifiers | Done | `GAP_ANALYSIS.md` |
| Ten candidates, rubric, scripted totals | Done | `NOVELTY_CANDIDATES.md` |
| Primary, supporting, fallback selected | Done, before held-out results | `CONTRIBUTION_SELECTION.md` |

## Phases 4–5: method and experiment design

| Item | Status | Artefact |
|---|---|---|
| Formal definition, algorithm, safeguards, ablation plan | Done | `SELECTED_METHOD_SPEC.md` |
| Components, sequence, schemas, limits | Done | `PROPOSED_ARCHITECTURE.md` |
| Staged experiment plan | Done | `EXPERIMENT_BLUEPRINT.md`, `FACTOR_AND_ABLATION_MATRIX.csv` |
| Dataset expansion and audit taxonomy | Designed | `DATASET_EXPANSION_PLAN.md` |
| Preregistration draft | Designed; not registered | `PREREGISTRATION_DRAFT.md` |

## Phases 6–7: prototype and evaluation

| Item | Status | Artefact |
|---|---|---|
| Prototype: mutants, engine, ledger, rules | Done | `src/triage_ext/` |
| Unit tests incl. the prediction-time boundary scan | Done: 22 pass; the study's 356 still pass | `tests/extension/test_cfp.py` |
| Engineering pilot on D1-dev (two scopes) | Done | `results/extension/probes/CFP_D1_DEV`, `CFP_D1_DEV2` |
| Held-out run on D1-test, rules committed first | Done: 369 instances, 1,228 s, zero model calls | `results/extension/probes/CFP_D1_TEST` |
| Pre-committed analyses EXT-1 and EXT-2 | Done | `results/extension/ext1_…`, `ext2_…`; `generated/cfp_tables_CFP_D1_TEST.md` |
| Go / no-go | **Conditional go** | `CONTRIBUTION_EVALUATION.md`; D-137 |
| Stage B (probe report in the judge's package) | Designed; **blocked**: needs a study-server session (authors) | `EXPERIMENT_BLUEPRINT.md` §3 |
| Stage C (fresh real faults) | Designed; **blocked**: generator and execution time (authors) | `PREREGISTRATION_DRAFT.md` |
| Integration tests of the engine against a live checkout | Not written as pytest (the engine runs only inside WSL); the dev split served as the integration run | — |

## Phases 8–9: paper and review readiness

| Item | Status | Artefact |
|---|---|---|
| Paper rebuilt around the contribution | **Not done, by decision**: the result is exploratory and the numbers are not in the numbers map | `PAPER_RESTRUCTURE_PLAN.md` |
| Four corrections the current paper needs regardless | Listed, not applied | `PAPER_RESTRUCTURE_PLAN.md` §5 |
| Venue fit | Done; deadlines from aggregators, unverified | `PAPER_RESTRUCTURE_PLAN.md` §6 |
| Reviewer simulation (three perspectives) | Done by the lead in one pass, not by independent agents | `REVIEWER_SIMULATION.md` |
| Deck | Unchanged | — |

## Validation-stage preparation (authors' instruction of 2026-11-11; D-138, D-139)

| Item | Status | Artefact |
|---|---|---|
| Resource breakdown from measured logs | Done | `RESOURCE_REQUIREMENTS.md` |
| Confirmation frames: unseen bugs (F1, F2) and a matched control group of non-buggy methods | Done (frame built; nothing generated) | `configs/extension/confirm_frame.jsonl`, `confirm_frame_summary.json` |
| Tranche driver, equivalent to the pilot driver | Done: identical ledger on 118 of 118 dev instances | `scripts/extension/run_probes_tranche.py`; `results/extension/probes/CFP_DRYRUN_DEV` |
| Confirmatory analysis (C1–C4, Holm, secondaries, control) | Done; reproduces the pilot's estimates in a dry run that is a software check, not a result | `scripts/extension/confirm_analysis.py`; `results/extension/dryrun/` |
| Configuration frozen by content hash, with a failing test on drift | Done | `configs/extension/cfp_frozen.json`; `tests/extension/test_freeze.py` |
| OSF preregistration | Final text; **not registered** | `OSF_PREREGISTRATION_CFP.md` |
| Stage B (probe report vs package vs shuffled report, matched budgets) | Planned; no code, no call | `STAGE_B_PLAN.md` |
| Full-text literature verification | Done for 16 works (read depth stated per work); novelty claim narrowed | `LITERATURE_VERIFICATION_FULLTEXT.md`; `NOVELTY_COLLISION_CHECK.md` §E |
| Tranche generation pipeline (contexts, dataset tag, guard, scope entry) | **Not built**: it edits the study's scope lock, which needs the authors | `RESOURCE_REQUIREMENTS.md` §4 |
| Generation, execution, labelling, probes on new data, judge votes | **Not started**: awaiting approval | — |

## Confirmation preparation after the authors' decisions (D-140, D-141)

| Item | Status | Artefact |
|---|---|---|
| Authors' nine decisions recorded | Done | D-140 |
| Planning for 30, 40, 50 bugs; powered vs underpowered | Done: C1 adequately powered; C2, C3, C4 underpowered | `generated/power_planning.md`; registration text |
| Separate records per tranche; dataset tags; run identifiers | Done | `data/extension/confirm/`; `configs/extension/confirm_runs.json` |
| Generation contexts and dataset manifest | Done: 679 contexts, none missing | `configs/extension/confirm_dataset_manifest.json` |
| Scope lock | Done: additive only | `configs/local_scope.json` |
| Readiness gate and gated generation driver | Done; 9 tests; gate currently refuses | `scripts/extension/confirm_gate.py`, `confirm_generate.py` |
| Control group documented (criteria, matching, distribution, biases) | Done | `CONTROL_GROUP.md` |
| Registration text with author information, hashes and planning | Final; **not deposited** (needs the authors' OSF account) | `OSF_PREREGISTRATION_CFP.md`; `osf_deposit/` |
| Second full-text verification pass and positioning | Done for 13 further works; two remain unopened | `LITERATURE_VERIFICATION_FULLTEXT.md` sections 5 and 6 |
| Execution readiness report | Done | `EXECUTION_READINESS.md` |
| Tranche drivers for execution, labelling, dataset, guard, votes, concatenation | **Not built**; not needed to start generation | `EXECUTION_READINESS.md` section 4 |
| OSF deposit; study session; generation | **Not started** | preconditions 1 and 3 open |

## Integrity

| Check | Result |
|---|---|
| Files changed under `paper/`, `prompts/`, `configs/`, `data/`, `results/runs_local`, `results/runs_frontier`, `results/heldout`, `results/revision`, `docs/paper` | none (`git diff --name-only master..research-extension`) |
| Decision entries before the work they govern | D-133 before EXT-0; D-134 before any probe; D-135 before the held-out run; D-136 before the held-out analysis; D-137 records the result |
| Paid calls, model calls, external contact, pushes | none |
| Side effect | the default Ollama desktop server was auto-started by `ollama list` during the resource check and is still running; no model was loaded |

## Open items for the authors

1. Approve generator and server time for the fresh-fault run, and decide on external registration.
2. Decide whether to apply the four corrections to the current paper now.
3. Stop the default Ollama server before the next study session.
4. Provide the prior notes file if it should be reconciled.
