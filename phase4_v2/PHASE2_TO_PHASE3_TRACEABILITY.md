# Phase 2 → Phase 3 traceability

Status: written 2026-11-14 on branch `research-extension` at `27a767b`, before any manuscript edit.
Every row names its evidence. "Phase 2" means the submitted `Phase2_Research_Methodology_Design.pdf`
(extracted from `Phase_2_assignment (1).zip`, byte-identical to `Phase_2_assignment.zip`) and
`Phase2_Methodology_Architecture_Diagram.html`. Decision ids (D-nn) are rows of
`docs/tracking/DECISIONS.md`; X-nn are rows of `docs/tracking/EXPERIMENT_DEVIATIONS.md`.

Status vocabulary: **Fully implemented** · **Partially implemented** · **Changed (documented)** ·
**Not implemented** · **Not applicable** · **Unverified**.

Origin of a change: **[T]** technical or resource constraint · **[A]** authors' decision ·
**[S]** later scientific extension · **[F]** instructor feedback.
No change can be tagged [F]: the instructor's feedback on the Phase 2 presentation is recorded nowhere in the
workspace (`docs/tracking/INSTRUCTOR_FEEDBACK_REGISTER.md` is empty; `docs/tracking/INITIAL_AUDIT.md` §6). This is
**unresolved author input**, and it blocks Phase 3 requirement 1 ("incorporate that feedback ... document any
changes"). Nothing below claims that no change was requested.

## 1. Gaps, objectives, questions, hypotheses

| Phase 2 item | What it commits to | Where it is answered | Status |
|---|---|---|---|
| G1 ground-truth triage evaluation | precision/recall/F1 against buggy/fixed labels; bug-revealing tests lost per policy | E1 on D1-test (177 scored at S1), H1; lost tests and lost bugs counted | Fully implemented |
| G2 specification availability | S0/S1/S2 within instance, test and label fixed | E2 full 3×3 factorial, H2a, H2b; exploratory GLMM | Fully implemented (S2 leakage audit not done, see §4) |
| G3 equal-budget architectures | DEB vs SC vs J1 at 5 calls × 512 tokens; SC-T token-matched | E3, H3a, H3b; SC-T with k_T = 5 fixed on dev | Fully implemented |
| O1 measurement basis | execution-labelled failing tests, no LLM in labelling | `src/triage/labeling.py`; labels sealed before judging | Fully implemented |
| O2 (G1) | P/R/F1, retention vs DA and R0 | E1 Table | Fully implemented |
| O3 (G2) | accuracy across S0–S2 | E2 | Fully implemented |
| O4 (G3) | DEB vs SC vs J1, equal budget | E3 | Fully implemented |
| O5 robustness | D2, D3, second model family, prompt paraphrases | D2 and M2 run; D3 and paraphrases not run | Partially implemented |
| RQ1 / H1 | J1 vs R0 F1 at S1 | ΔF1 +0.195 [−0.006, 0.370], p_Holm 0.233 — inconclusive | Answered (inconclusive) |
| RQ2 / H2a, H2b | S1−S0 (Javadoc methods), S2−S1 | H2a −0.050 [−0.091, −0.006], p_Holm 0.116; H2b +0.019, p_Holm 0.798 | Answered (inconclusive) |
| RQ3 / H3a, H3b | DEB−SC; SC−J1 | H3a +0.074, p_Holm 0.532; H3b −0.024, p_Holm 0.798 | Answered (inconclusive) |
| Confirmatory endpoint | PF-class F1, Holm family of five; recall/precision secondary family | `results/heldout/analysis_final/D1_M1/tables/confirmatory.json` | Fully implemented; MCC added beside F1 (D-54) |

Numbers above were read directly from `confirmatory.json` (independent script, not the manuscript build).

## 2. Methodology components (Phase 2 §3)

| Phase 2 commitment | Actual implementation | Evidence | Status | Origin / explanation |
|---|---|---|---|---|
| Within-subjects controlled design, instance = one failing generated JUnit method | Same | `src/triage/runner.py`, analysis set rule D-70 | Fully implemented | — |
| D1: Defects4J 3.0.1, frame of Zhao et al. (318 focal methods / 233 defects), cap 25 per project | Frame **reconstructed** by re-running Zhao et al.'s published selection rule with their replication package: 1,758 candidates → **312 methods / 220 defects**; cap 25 → 234 / 167 | `data/processed/split_manifest.json`; X-03 | Changed (documented) | [T] The final list of 318 is not distributed in the replication package, so the selection rule was re-run; the definition of the population is the same, the count differs by 6 methods / 13 defects. No author-selected exclusion. |
| Project-level split: 3 dev / 14 test projects by seeded draw before generation | Dev = Cli, Gson, Jsoup (39 methods); held-out = 14 projects (195 methods) | `split_manifest.json` | Fully implemented | — |
| D2: seeded faults (Defects4J/Major mutation), ≤ 2 per held-out focal method, killed by a developer test | 284 verified mutants → 468 PF / 349 TF / 65 AMB; judged sample capped at 300 (159/119/22), 270 scored | `data/processed/d2_summary.json`; X-08, D-64 | Fully implemented, kill criterion tightened (X-08) | [A] Stricter kill check prevents a timeout from standing in for an observable fault. |
| D3: GitBug-Java external benchmark (up to 60 bugs) | **Not run** | X-05, D-101, D-103 | Not implemented | [T] GitBug-Java reproduces builds through Docker/`act`; Docker was not installed. D-103 adds that its 2023 bugs predate every 2026 model's training cutoff, so it could not serve its contamination purpose. E5-R2 is reported as not run. |
| C1 environment: one Docker image, digest per run | WSL2 Ubuntu 22.04.5, Defects4J 3.0.1, OpenJDK 11, recorded manifest; reference Dockerfile not used | `env/environment_manifest.json`; X-04 | Changed (documented) | [T] Docker not available on the host. Reproducibility rests on the manifest, not an image digest. |
| C3 context from B only | Same; fixed version used only for labelling | `src/triage/context_builder.py`; leakage guard | Fully implemented | — |
| C4 generator G from a third family (GPT-4.1 default), 3 generations / method, T = 0.7 | **Gemma 4 26B-A4B** (`gemma4:26b`, Q4_K_M), 3 generations / focal method, T 0.7, local | `configs/local_models.FROZEN.json`; D-21, D-57 | Changed (documented) | [A]/[T] D-21: authors moved the study to local open-weight models, zero API spend; G chosen on dev split by criteria fixed in advance. |
| C5 compile, ≤ 3 pruning passes; C6 3 runs on B and F, fresh JVM, 30 s | Same | `src/triage/execution.py`; D-142 timing check | Fully implemented | — |
| §3.4 labelling rule PF/TF/AMB/FLAKY/TIMEOUT/ENV/NC | Same rule, precedence NC > TIMEOUT > ENV > FLAKY | `src/triage/labeling.py`; paper Table 2 | Fully implemented | — |
| Label audit: 100 dev instances (50 PF / 50 TF), two raters, Cohen's κ | **71** dev instances (all 21 dev PF + 50 of 89 TF), two raters, κ 0.936; consensus = execution on 97.2% | `results/audit/label_audit_scores.json`; D-82, D-108 | Partially implemented | [T] The dev split contains only 21 PF instances, so 50 PF were not available. Raters are the authors and saw the fix (disclosed). |
| §3.5 preprocessing (dedup by normalised body hash, stack normalisation, 500-char message cap, Javadoc from B) | Same | `src/triage/preprocess.py` | Fully implemented | — |
| §3.6 evidence package with cited ids; S0/S1/S2 nested | Same | `context_builder.py`, `spec_inference.py` | Fully implemented | — |
| §3.6.1 S2 inferred specification + leakage audit of 60 specifications | Inference implemented (T = 0, lines changed by the fix removed); **the 60-item specification audit was not carried out** (sheet template only) | `docs/audits/TEMPLATE_spec_audit.csv`; no scored spec-audit file | Partially implemented | Not recorded in any decision; **not reported in V1 or V2**. Must be disclosed. |
| §3.7 DEB: 2 advocates × 2 rounds + adjudicator = 5 calls; round-1 independence; anonymised, randomised order; cite evidence ids; log position bias and uncited decisions | Same | `src/triage/arms.py::deb_arm` (seeded `_order_rng`, shuffled "Analyst X/Y"); `schema.py` | Fully implemented | — |
| §3.8 baselines DA, KA, R0, J1, SC, SC-T, DEB; same model, T 0.7, top-p 1.0, 512 output | Same; k_T = 5 from the dev split | `arms.py`; frozen config | Fully implemented | — |
| Models: M1 DeepSeek-V3 family; M2 Qwen3 family | **M1 Qwen3.5 9B** (`qwen3.5:9b`); **M2 Gemma 4 12B** (`gemma4:12b`, shares G's family) | frozen config; D-21, D-57 | Changed (documented) | [A]/[T] Local-only decision (D-21). Consequence: M2 shares the generator's family, so self-preference cannot be excluded (addressed later by M3 and KUU-NG). |
| §3.9 prompt optimisation: ≤ 5 rounds per role, dev only, freeze before test | 5 rounds (v0–v4) both families; set `local_m1b` frozen (D-48, D-57) | `prompts/frozen/local_m1b` | Fully implemented | — |
| Pilot gates P1–P5 | P1 yield passed for G; P2/G-d: **M1 failed** (J1 F1 0.350 vs R0 0.642 on dev); P3 validity passed | `results/dev/GATE_M1b/dev_gates.json`; D-48–D-52 | Implemented; gate failed | [A] Fallback ladder fixed in advance: five prompt rounds, 8-bit quantisation, other family; audit D-51/D-52 found no pipeline defect; M1 kept and the failure reported. Consequence: RQ2/RQ3 describe a judge below its own gate; nulls cannot be generalised to the architectures. |
| §3.10 JSON output schema; one deterministic repair parse; INVALID scored TF (sensitivity: excluded) | Same | `schema.py`, `metrics.py` | Fully implemented | — |
| C9 sampling: all PF, TF at 1:2 stratified by project, IPW weights | Applied **over the split** with proportional, project-stratified TF allocation (dev pilot kept within-project) | D-53, X-07, `SAMPLING_ANALYSIS.md` | Changed (documented) | [A] Text ambiguous; reading fixed before held-out data existed. |
| §4.8 target sizes: D1-test ≈ 720, D2 ≈ 300, D3 ≈ 200 | D1-test judged 193 (177 scored at S1); D2 300 judged (270 scored); D3 0 | sample files | Partially implemented | [T] Generation yield (60 PF on the held-out split) set the size; the planning figure was an estimate. |

## 3. Statistical plan (Phase 2 §5)

| Phase 2 commitment | Actual | Status |
|---|---|---|
| Metrics P, R, F1, FPR, FNR, MCC, confusion matrix, bug-level retention, prevalence-adjusted precision, cost | All reported; TPR/TNR/balanced accuracy added for cross-dataset comparison (D-113) | Fully implemented (+ additions) |
| PR-AUC of SC vote share | Not reported as PR-AUC; ranking reported post hoc as AUROC (D-114) | Changed (post hoc) |
| Bug-level cluster bootstrap, 10,000 resamples; paired | Same | Fully implemented |
| Holm over five F1 tests; secondary recall/precision family | Same | Fully implemented |
| GLMM with lme4 | statsmodels variational Bayes with bug-level bootstrap intervals; lme4 unavailable (X-02, X-06); GEE sensitivity (D-120) | Changed (documented) [T] |
| McNemar, Wilcoxon over projects, LOPO | Same | Fully implemented |
| Equivalence: 90% CI within ±0.05 F1 (TOST) | Applied; no contrast shown equivalent except H2b precision | Fully implemented |
| 3 replicates | 3 replicates for E1–E3 (cut to 2 by D-59, restored by D-66 before any Tier 1 output) | Fully implemented |

## 4. Experiment completion matrix (each sub-experiment separately)

| ID | Planned (Phase 2) | Conducted | Data | Not conducted / why | Claims the evidence supports |
|---|---|---|---|---|---|
| E1 | DA, KA, R0, J1, SC, DEB at S1, 3 reps; H1 | Yes, plus SC-T | D1-test, 177 scored, 3 reps | — | Triage accuracy of a 9B judge against execution labels; H1 inconclusive; DEB F1 0.511 vs KA 0.506, MCC 0.267 [0.126, 0.405]; DEB loses 30 of 60 PF tests |
| E2 | S0/S1/S2 × J1/SC/DEB, 3 reps; H2a, H2b; GLMM | Yes (full 3×3) | D1-test; D2 1 rep | S2 leakage audit (60 specs) not done | No detectable benefit of Javadoc or inferred specification for this judge; inconclusive after Holm |
| E3 | J1, SC, DEB, SC-T at S1; H3a, H3b; cost | Yes | D1-test | — | Debate advantage small and not significant; no equivalence shown; DEB slower |
| E4-A1 | DEB without exchange | Yes, 1 rep | D1-test S1 | — | No evidence the exchange helps (exploratory) |
| E4-A2 | symmetric debate | Yes, 1 rep | D1-test S1 | — | No evidence adversarial roles help (exploratory) |
| E4-A3 | SC threshold 2/5, 4/5 | Yes (re-analysis) | D1-test S1 | — | Threshold moves along recall/precision trade-off |
| E4-A4 | no failure evidence | Yes, 1 rep | D1-test S1 | — | Failure evidence carries the signal; J1/SC fall to chance (exploratory) |
| E4-A5 | buggy body (a); body-derived S2 (b) | Yes, 1 rep | D1-test S1/S2 | — | No significant effect |
| E5-R1 | D2 seeded faults, E1–E3 arms | Yes, all arms and levels, 1 rep | D2, 270 scored | — | Contamination control for recall of fixes, not of original code |
| E5-R2 | D3 GitBug-Java, E3 arms at S1, 3 reps | **No** | — | Docker unavailable (X-05); premise void (D-103) | No external-benchmark generalisation claim |
| E5-R3 | M2 (second family), D1-test + D2 | Yes, J1/SC/DEB at S1, 1 rep (D-61, D-71) | D1-test, D2 | M2 is not a different family from G | Ranking robustness for a second local judge; self-preference not excluded |
| E5-R4 | two J1 prompt paraphrases | **No** | — | Tier 3 cut on time (D-59); D-61/D-66 restored only R3; paraphrases never written (`TASKS.md`) | **No prompt-sensitivity claim. V1 and V2 never mention R4 — an unreported omission that the final paper must disclose.** |
| E5-R5 | per-project F1, Wilcoxon, LOPO | Yes | D1-test | — | No single project drives the confirmatory verdicts |

## 5. Additions after the Phase 2 design (scientific extensions, [S])

These were not part of the approved methodology. None replaces DEB as the originally proposed framework.

| Addition | Decisions | Evidence status | Data |
|---|---|---|---|
| Further judges: 35B exploratory, M3 third family, three-family vote, Sonnet 5.5 frontier reference (E6–E9b) | D-55, D-67, D-82–D-104 | robustness / reference; fixed in advance in the decision log or exploratory | D1-test, D2 |
| RQ4 judge-only rules: KUU, KUU-NG, escalation cascade | D-95, D-105, D-109 | KUU post hoc on D1; hypotheses fixed in advance (internal Git provenance, not externally registered) on D2 | D1-test, D2 |
| Thinking-enabled M1 judge | D-126, D-130, D-131 | fixed in advance on D2; failed its dev gate | D1-test, D2 |
| Revision analyses (rates, ranking, learned baselines, risk threshold, sample size, local cascade) | D-112–D-122, D-132 | post hoc / exploratory | logged decisions |
| Counterfactual program probes (CFP) pilot | D-133–D-137 | exploratory (labels known) | D1-test |
| Registered confirmation C1–C4 | D-138–D-146; OSF `kp79c` | confirmatory, registered | fresh frames F1, F2, CTRL |
| Whole-method dependence probes (WDP) | D-147–D-152 | exploratory; retrospective; protocol frozen internally in Git before the runs; not externally preregistered; designed after the confirmation outcomes were known | pilot, F1, F2, CTRL |

## 6. Summary

- Approved core (G1–G3, O1–O4, RQ1–RQ3, H1–H3b, E1–E4, E5-R1/R3/R5): implemented and executed as designed,
  with documented changes of model, environment, frame count and sampling reading.
- Not implemented: D3 (E5-R2), prompt paraphrases (E5-R4), the S2 specification audit; label audit smaller
  than planned (71 vs 100). R4 and the spec audit are not disclosed in V2.
- The Phase 2 hypotheses all ended **inconclusive** after Holm; none is supported, none shown equivalent.
- Blocking author input: the instructor's Phase 2 feedback and what (if anything) changed because of it.
