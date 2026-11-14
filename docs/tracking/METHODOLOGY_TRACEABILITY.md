# Methodology traceability

Phase 1 gap → Phase 2 design → Phase 3 implementation → experiment → evidence → Phase 4 section.
"Evidence" names the artefact that will hold the measurement; nothing is measured yet unless stated.

| Gap | Phase 2 design decision | Implementation (file) | Verified how | Experiment | Evidence artefact | Paper section |
|---|---|---|---|---|---|---|
| G1 | Frame of [12], 25/project cap, 3/14 project split (§3.2) | `src/triage/frame.py`, `scripts/build_frame.py` | frame run log; split manifest | all | `data/processed/split_manifest.json`, `frame_d1.jsonl` | 6.2, 7.1 |
| G1 | Generator G from buggy focal method, 3 generations, T=0.7 (C4) | `src/triage/generation.py`, `prompts/dev/v0/generator.txt` | unit/mock run | all | `data/interim/candidates/`, call log | 6.2 |
| G1 | Compile on B and F, prune ≤3 passes (C5) | `execution.compile_on_both` | Lang-1 fixture: NC method pruned | all | `data/raw/executions/` | 6.3 |
| G1 | 3 runs × B and F, fresh JVM, 30 s (C6–C7) | `execution.run_method`, `src/java/.../SingleTestRunner.java` | Lang-1 fixture (real B/F) | all | `data/raw/executions/` | 6.3 |
| G1 | σ = (outcome, exception, test line); PF/TF/AMB/excluded (§3.4, Table 6) | `src/triage/labeling.py` | 10 unit tests + Lang-1 fixture: PF, TF, AMB, PASS, MISGUIDED, TIMEOUT, FLAKY all correct | all | `data/ground_truth_store/labels_*.jsonl` | 6.3 |
| G1 | Label store isolated from judges (§3.4) | `context_builder.judge_view` whitelist; runner never opens `ground_truth_store/` | unit test `test_judge_view_strips_labels` | all | code | 6.3 |
| G1 | Label audit (100, two raters, κ) | `stats.cohen_kappa`; audit sheet generator (to do) | κ unit test | P5 | `results/audit/label_audit.csv` | 7.2 |
| G1 | Baselines DA, KA, R0 (Table 10) | `arms.policy_arm`, `arms.r0_arm` | unit tests | E1 | decisions | 6.5 |
| G1 | Metrics P/R/F1/FPR/FNR/MCC, prevalence-adjusted P, bug retention, PF lost (§5.1) | `src/triage/metrics.py`, `analysis.py` | unit tests with hand-computed values | E1 | `results/analysis_*/tables/conditions.csv` | 8.1 |
| G2 | S0/S1/S2 nested packages, body hidden (§3.6, Table 8) | `src/triage/context_builder.py` | unit tests: nesting, byte-identical T/F/Sig sections, no leakage | E2 | packages logged per decision | 6.4 |
| G2 | Spec Inferencer, once per focal method, T=0, ≤400 tokens, cached (§3.6.1) | `src/triage/spec_inference.py` | mock run | E2 | `data/processed/specs/` | 6.4 |
| G2 | Spec leakage audit (60 specs, κ) | audit sheet (to do) | — | E2 | `results/audit/spec_audit.csv` | 8.2 |
| G3 | J1, SC (5), SC-T (k_T) with same prompt (Table 10) | `arms.j1_arm`, `arms.sc_arm`, `arms.aggregate_votes` | unit tests: 5 calls, tie→TF, vote share | E1, E3 | decisions | 6.5 |
| G3 | DEB: 5 calls, R1 independent, R2 sees opponent, anonymised randomised adjudication (§3.7) | `arms.deb_arm` | unit tests: 5 calls; R1 prompts contain no opponent text; adjudicator sees only "Analyst X/Y" | E1–E3 | decisions + call log (all five outputs) | 6.5 |
| G3 | Equal allocated budget; consumed tokens logged; SC-T check (§4.5) | `llm.CallResult`, `result_cost_dict`, `run_experiment.py` (k_T guard) | mock run logs tokens | E3 | cost columns in `conditions.csv` | 8.3 |
| G3 | Ablations A1–A5 (§4.6) | A1/A2 `deb_arm(variant=)`, A3 `analysis.a3_reanalysis`, A4/A5 `build_package(include_failure/impl, spec_override)` | unit tests A1, A4, A5a; mock run of all | E4 | `tables/ablations.json` | 10 |
| all | Bootstrap (10k, bug clusters), paired, Holm, McNemar, TOST ±0.05, Wilcoxon, LOPO (§5.2) | `src/triage/stats.py`, `analysis.py` | unit tests (Holm reference values, zero-delta, large-delta) | E1–E5 | `analysis_summary.json` | 8 |
| all | Decision rules (Table 18) | `stats.decide` | unit test | E1–E3 | `confirmatory.json` | 8 |
| G1 | Leakage controls (§3.5, §3.6): no bug ids, fixed version or body reach a judge | `dataset.guard_record`, `context_builder.leakage_check`, `runner` pre-call check, `run_experiment.execute` | e2e test via `execute`; mock e2e with planted leak (0/12,330 prompts) | all | `leakage_rejections.jsonl` | 6.4 |
| G2 | GLMM spec × arch, project/bug/instance effects (§5.2) | `src/triage/glmm.py`, `analyze.py` | parameter recovery + 20-run coverage study (VB under-covers → bootstrap CIs) | E2 | `tables/glmm_e2.json` | 8.2 |
| G1 | Label audit 100 / spec audit 60 (§3.4, §3.6.1) | `src/triage/audit.py`, `make_audit_sheets.py`, `score_audits.py` | 3 unit tests (stratification, blinding, κ) | P5, E2 | `docs/audits/*`, `results/audit/*` | 7.2, 8.2 |
| robustness | D2 seeded faults (Table 4) | `src/triage/mutants.py`, `scripts/build_d2.py` | 5 unit tests; real Major runs on held-out methods | E5-R1 | `data/processed/d2_mutants.jsonl` | 8.5 |
| robustness | M2, paraphrases, per-project (§4.7) | M2: `E5_R3_M2.json`; R5 in `analyze.py`; paraphrases: written before the freeze | — | E5 | — | 8.5 |
| robustness | D3 GitBug-Java | **blocked** (Docker) | — | E5-R2 | — | 8.5 |
