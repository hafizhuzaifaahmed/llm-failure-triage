# Phase 3 — Implementation and Experimental Evaluation

**LLM-Based Failure Triage for Generated Unit Tests.** Hafiz Huzaifa Ahmed, Saad Ilyas (FAST-NUCES Islamabad).

Status: all experiments are complete (tag `experiments-complete`). Every number below is generated from the committed
analysis outputs by `scripts/paper/build_numbers.py`; `docs/paper/NUMBERS_MAP.csv` gives the source file and field of
each one. Results come from `results/heldout/analysis_final/` (primary) `results/expl_35b/analysis/` (exploratory), `results/e6b/analysis/` and `results/e8/analysis/`.
Setup counts marked in the map as `setup` come from the dataset, configuration and development files named there.

The brief's seven components map to sections 1–7; section 8 covers deviations and reproducibility.

**Research questions.** RQ1 accuracy against buggy/fixed truth and bug-revealing tests kept; RQ2 specification level;
RQ3 debate against self-consistency at equal budget. **RQ4**, added after the primary study: can a keep-by-default rule
that discards only on cross-family unanimity cut lost bug-revealing tests without lowering F1, and can escalating
disagreements recover accuracy cheaply? Its tests were fixed in advance in the version-controlled decision log before any of their calls (D-95,
D-105, D-109); that is internal provenance, not an external registration.

## 1. Implementation of the proposed methodology

The approved Phase 2 pipeline is implemented as the Python package `src/triage/` plus a Java single-test runner;
stage-to-module mapping: `docs/tracking/METHODOLOGY_TRACEABILITY.md`.

| Component | Module |
|---|---|
| D1 frame, cap, project split, buggy-side context | `frame.py` |
| Test generation from the buggy focal method | `generation.py` |
| Compile on buggy/fixed versions with pruning; 3 fresh-JVM runs per version | `execution.py`, `SingleTestRunner.java` |
| Ground-truth labeller (PF / TF / AMB / excluded categories) | `labeling.py` |
| Label store isolated from every judging module | `dataset.py`, `context_builder.judge_view` |
| Evidence packages S0 / S1 / S2 with cited ids, truncation, leakage check | `context_builder.py` |
| Specification inferencer (S2, body-derived S2′) | `spec_inference.py` |
| Arms DA, KA, R0, J1, SC, SC-T, DEB and ablations A1, A2, A4, A5 | `arms.py`, `context_builder.py` |
| Local model client (Ollama), call log, replay, stop/resume | `ollama.py`, `llm.py`, `sessions.py` |
| Leakage guard on the live call path | `dataset.guard_record`, `runner.py` |
| Metrics, bug-level bootstrap, Holm, McNemar, TOST, Wilcoxon, LOPO, mixed model | `metrics.py`, `stats.py`, `analysis.py`, `glmm.py` |
| D2 seeded faults (Major mutants) | `mutants.py`, `d2.py` |
| Figures | `figures.py` |

**Changes to the Phase 2 methodology.** The instructor's feedback on the Phase 2 presentation is not recorded in the
project (`docs/tracking/INSTRUCTOR_FEEDBACK_REGISTER.md`). **TODO (authors):** state the feedback and what changed, or
that no change was requested. Changes made for other reasons (section 8): locally served open-weight models replace the
API-served models (D-21); MCC is reported beside every F1 (D-54); the sampling ratio is read as overall (D-53); the
analysis set rule for leakage aborts (D-70).

## 2. Dataset, preprocessing and experimental setup

**D1 frame (Defects4J 3.0.1).** Zhao et al.'s selection rule was re-run with their replication package:
{{split:candidates}} candidate methods screened, {{split:frame_methods}} focal methods from {{split:frame_bugs}} defects
kept (the original reports {{split:reference_frame_zhao:methods}} / {{split:reference_frame_zhao:bugs}}); the
per-project cap leaves {{split:sampled_methods}} methods from {{split:sampled_bugs}} defects. Project split (seeded,
before any generation): development {{der:dev methods}} methods (Cli, Gson, Jsoup); held-out {{der:test methods}}
methods from {{der:n test projects}} projects.

**Generation, execution, labels.** Three generations per focal method by G. Across both D1 splits
{{ds1:executed_methods}} test methods were executed: {{ds1:exclusions:PASS}} passed on the buggy version,
{{ds1:exclusions:MISGUIDED}} were misguided, {{ds1:exclusions:NC}} did not compile on one version,
{{ds1:exclusions:TIMEOUT}} timed out. Held-out labels: {{der:d1 test PF labelled}} PF, {{der:d1 test TF labelled}} TF,
{{der:d1 test AMB labelled}} AMB.

**Evaluation samples.** All PF kept; TF sampled to twice the PF count over the split, stratified by project, with
inverse-probability weights. Judged D1-test sample (counts): {{sum:prevalence:judged_sample_prevalence_by_dataset:D1:PF}} PF,
{{sum:prevalence:judged_sample_prevalence_by_dataset:D1:TF}} TF, {{sum:prevalence:judged_sample_prevalence_by_dataset:D1:AMB}} AMB.
Leakage-guard aborts at S1: {{sum:leakage_abort_exclusions:counts_labelled:S1|full:instances}} instances, excluded from
every arm at that level (D-70) → {{sum:leakage_abort_exclusions:n_per_level:S1}} scored instances at S1
(PF prevalence {{sum:prevalence:pf_prevalence}}).
D2 (seeded faults): {{d2rep:before_cap:d2_units_total}} mutants → {{d2rep:before_cap:labelled_instances:PF}} PF,
{{d2rep:before_cap:labelled_instances:TF}} TF, {{d2rep:before_cap:labelled_instances:AMB}} AMB; judged sample capped at
{{d2rep:judged_sample:cap}} ({{sum2:prevalence:judged_sample_prevalence_by_dataset:D2:PF}} PF,
{{sum2:prevalence:judged_sample_prevalence_by_dataset:D2:TF}} TF, {{sum2:prevalence:judged_sample_prevalence_by_dataset:D2:AMB}} AMB),
{{d2:DEB|S1:n_instances}} scored; PF prevalence {{sum2:prevalence:pf_prevalence}}. D3 (GitBug-Java) not run (needs Docker).

**Models (all local, zero API cost).** Ollama {{frozen:runtime:version}} on {{frozen:hardware:name}}
({{frozen:hardware:mem_total_mib@0}} MiB VRAM, {{frozen:hardware:ram_total_gib@0}} GB RAM). G = `{{frozen:roles:G}}`,
M1 = `{{frozen:roles:M1}}`, M2 = `{{frozen:roles:M2}}`, all Q4_K_M, thinking off, frozen before any held-out call
(D-57). Judges: temperature {{frozen:frozen_models:M1:temperature:judges@1}}, top-p {{frozen:frozen_models:M1:top_p@1}},
context {{frozen:frozen_models:M1:num_ctx@int}} tokens, output ≤ {{frozen:frozen_models:M1:num_predict:judge_roles}}
tokens, per-call seed, {{frozen:decoding:replicates}} replicates for E1–E3; SC = 5 samples; k_T = {{frozen:decoding:k_T}}.
Generator selection on dev: reliability {{gsel:C1}} (CI {{gsel:C1_ci95}}), assertion validity {{gsel:C2}}, PF yield
{{gsel:P1@pct}}. M1 development gate: one-shot F1 {{devgate:G_d_detail:J1_f1}} (MCC {{devgate:G_d_detail:J1_mcc}}) vs
R0 {{devgate:G_d_detail:R0_f1}} (MCC {{devgate:G_d_detail:R0_mcc}}) on {{devgate:n_instances}} instances /
{{devgate:n_bugs}} bugs — **failed**, reported, M1 kept (D-48–D-52). Non-determinism: {{nondet:T0.7:label_flip_rate@pct0}}
label flips over {{nondet:n}} repeated judgements.

**Statistics.** Per-replicate metrics averaged; bug-level cluster bootstrap (10,000 resamples) for CIs and paired
differences; five confirmatory F1 tests Holm-corrected; equivalence margin ±0.05 F1 (90% CI).

## 3. Baseline evaluation (E1, S1, D1-test, judge M1)

| Arm | F1 [95% CI] | MCC [95% CI] | Precision | Recall | Prec. at natural prevalence | PF tests lost |
|---|---|---|---|---|---|---|
| DA (discard-all) | {{d1:DA:f1}} | {{d1:DA:mcc}} | n/a | {{d1:DA:recall}} | n/a | {{d1:DA:pf_lost}} |
| KA (keep-all) | {{d1:KA:f1}} {{d1:KA:f1_ci95}} | {{d1:KA:mcc}} | {{d1:KA:precision}} | {{d1:KA:recall}} | {{d1:KA:precision_prev_adj}} | {{d1:KA:pf_lost}} |
| R0 (rule-based) | {{d1:R0:f1}} {{d1:R0:f1_ci95}} | {{d1:R0:mcc}} {{d1:R0:mcc_ci95}} | {{d1:R0:precision}} | {{d1:R0:recall}} | {{d1:R0:precision_prev_adj}} | {{d1:R0:pf_lost}} |
| J1 | {{d1:J1|S1:f1}} {{d1:J1|S1:f1_ci95}} | {{d1:J1|S1:mcc}} {{d1:J1|S1:mcc_ci95}} | {{d1:J1|S1:precision}} | {{d1:J1|S1:recall}} | {{d1:J1|S1:precision_prev_adj}} | {{d1:J1|S1:pf_lost@1}} |
| SC | {{d1:SC|S1:f1}} {{d1:SC|S1:f1_ci95}} | {{d1:SC|S1:mcc}} {{d1:SC|S1:mcc_ci95}} | {{d1:SC|S1:precision}} | {{d1:SC|S1:recall}} | {{d1:SC|S1:precision_prev_adj}} | {{d1:SC|S1:pf_lost@1}} |
| SC-T | {{d1:SC-T|S1:f1}} {{d1:SC-T|S1:f1_ci95}} | {{d1:SC-T|S1:mcc}} {{d1:SC-T|S1:mcc_ci95}} | {{d1:SC-T|S1:precision}} | {{d1:SC-T|S1:recall}} | {{d1:SC-T|S1:precision_prev_adj}} | {{d1:SC-T|S1:pf_lost@1}} |
| DEB | {{d1:DEB|S1:f1}} {{d1:DEB|S1:f1_ci95}} | {{d1:DEB|S1:mcc}} {{d1:DEB|S1:mcc_ci95}} | {{d1:DEB|S1:precision}} | {{d1:DEB|S1:recall}} | {{d1:DEB|S1:precision_prev_adj}} | {{d1:DEB|S1:pf_lost@1}} |

Keep-all's F1 ({{d1:KA:f1}}) sits at the level of the best LLM arm with MCC {{d1:KA:mcc}}; MCC separates the arms
from chance. **Confirmatory tests (Holm):**

| H | Contrast | ΔF1 | 95% CI | p | p (Holm) |
|---|---|---|---|---|---|
| H1 | J1 − R0 | {{conf:f1:H1:delta}} | {{conf:f1:H1:ci95}} | {{conf:f1:H1:p}} | {{conf:f1:H1:p_holm}} |
| H2a | S1 − S0 (Javadoc subset) | {{conf:f1:H2a:delta}} | {{conf:f1:H2a:ci95}} | {{conf:f1:H2a:p}} | {{conf:f1:H2a:p_holm}} |
| H2b | S2 − S1 | {{conf:f1:H2b:delta}} | {{conf:f1:H2b:ci95}} | {{conf:f1:H2b:p}} | {{conf:f1:H2b:p_holm}} |
| H3a | DEB − SC | {{conf:f1:H3a:delta}} | {{conf:f1:H3a:ci95}} | {{conf:f1:H3a:p}} | {{conf:f1:H3a:p_holm}} |
| H3b | SC − J1 | {{conf:f1:H3b:delta}} | {{conf:f1:H3b:ci95}} | {{conf:f1:H3b:p}} | {{conf:f1:H3b:p_holm}} |

All five are inconclusive at this sample size (none significant after Holm, none equivalent).

**Specification levels (E2), F1 (MCC):**

| Level | J1 | SC | DEB |
|---|---|---|---|
| S0 | {{d1:J1|S0:f1}} ({{d1:J1|S0:mcc}}) | {{d1:SC|S0:f1}} ({{d1:SC|S0:mcc}}) | {{d1:DEB|S0:f1}} ({{d1:DEB|S0:mcc}}) |
| S1 | {{d1:J1|S1:f1}} ({{d1:J1|S1:mcc}}) | {{d1:SC|S1:f1}} ({{d1:SC|S1:mcc}}) | {{d1:DEB|S1:f1}} ({{d1:DEB|S1:mcc}}) |
| S2 | {{d1:J1|S2:f1}} ({{d1:J1|S2:mcc}}) | {{d1:SC|S2:f1}} ({{d1:SC|S2:mcc}}) | {{d1:DEB|S2:f1}} ({{d1:DEB|S2:mcc}}) |

**Equal budget (E3):** consumed tokens per instance J1 {{d1:J1|S1:consumed_tokens_per_instance@0}}, SC
{{d1:SC|S1:consumed_tokens_per_instance@0}}, SC-T {{d1:SC-T|S1:consumed_tokens_per_instance@0}}, DEB
{{d1:DEB|S1:consumed_tokens_per_instance@0}}; DEB − SC-T ΔF1 {{sum:sc_t_check:delta}} {{sum:sc_t_check:ci95}}.

**Mixed model (exploratory, PF recall, odds ratios vs S1 with bug-level cluster-bootstrap 95% intervals, {{glmmb:B}} refits):** S0 {{glmmb:models:PF_recall:terms:1:odds_ratio}} {{glmmb:models:PF_recall:terms:1:or_ci95_bootstrap}}, S2 {{glmmb:models:PF_recall:terms:2:odds_ratio}} {{glmmb:models:PF_recall:terms:2:or_ci95_bootstrap}}; on TF instances S0 {{glmmb:models:TF_specificity:terms:1:odds_ratio}} {{glmmb:models:TF_specificity:terms:1:or_ci95_bootstrap}}.

## 4. Graphical results

All figures are in `results/heldout/analysis_final/<analysis>/figures/` (PNG and PDF):

- E1 precision/recall/F1/MCC with CIs: [D1, M1](../results/heldout/analysis_final/D1_M1/figures/fig_e1_prf.png),
  [D2, M1](../results/heldout/analysis_final/D2_M1/figures/fig_e1_prf.png),
  [D1, M2](../results/heldout/analysis_final/D1_M2/figures/fig_e1_prf.png),
  [D2, M2](../results/heldout/analysis_final/D2_M2/figures/fig_e1_prf.png)
- Confusion matrices: [D1, M1](../results/heldout/analysis_final/D1_M1/figures/fig_e1_confusion.png)
- Confirmatory forest plot: [D1, M1](../results/heldout/analysis_final/D1_M1/figures/fig_confirmatory_forest.png)
- E2 F1 and recall by level: [F1](../results/heldout/analysis_final/D1_M1/figures/fig_e2_spec_f1.png),
  [recall](../results/heldout/analysis_final/D1_M1/figures/fig_e2_spec_recall.png)
- E3 cost–performance: [D1, M1](../results/heldout/analysis_final/D1_M1/figures/fig_e3_pareto.png)
- E4 ablations: [D1, M1](../results/heldout/analysis_final/D1_M1/figures/fig_e4_ablations.png)
- Per-project F1: [D1, M1](../results/heldout/analysis_final/D1_M1/figures/fig_r5_per_project.png)

## 5. Comparison with existing research

Only JSTestCraft reports a triage metric (audited recall {{cit:jstestcraft recall}}%\*); JavaOracle reports a precision
of {{cit:javaoracle precision}}\* (\* = taken from the paper, not comparable: other language and data, audit-based
labels, different prevalence, larger models). On identical D1-test instances, DEB's F1 exceeds the re-implemented
rule baseline R0 by {{der:d1 DEB-R0 f1}} (relative {{der:d1 DEB-R0 f1 rel@spct}}), SC (the single-model analogue of
JSTestCraft's vote) by {{conf:f1:H3a:delta}} and keep-all by {{der:d1 DEB-KA f1}}; none is significant after Holm.
DEB's recall ({{d1:DEB|S1:recall}}) and precision ({{d1:DEB|S1:precision}}) are below the two published figures. No
improvement over a base paper can be computed, because no base paper reports a triage result on this data, metric or
label source.
Our numbers differ from the base papers in language, label source (execution, not an audit), judge size (E9 is the
frontier reference), task and metric, and prevalence; where the designs meet they agree: the effective-test interval
overlaps Zhao et al.'s range (their package carries no generated tests to re-run, D-98), a cross-family vote keeps
recall high ({{e8:summary:VOTE3|S1:recall}}) as JSTestCraft's does, and debate trades away true positives as JavaOracle's
does. E7b (GitBug-Java) was not run: first its setup exceeded the free disk (D-101), and once disk was freed its premise
failed, because its bugs date from 2023 while every model here is a 2026 release, so it cannot test memorisation (D-103).
E7a (a second generator from a third family, D-100) was not run either, because neither candidate passed the D-22
selection on dev: phi4 14B executed {{e7a:tried:0:C1}} {{e7a:tried:0:C1_ci95}} of its generated methods (C1, threshold
0.50; C2 {{e7a:tried:0:C2}}, P1 {{e7a:tried:0:P1}}), llama3.1 8B {{e7a:tried:1:C1}} {{e7a:tried:1:C1_ci95}} with C2
{{e7a:tried:1:C2}} {{e7a:tried:1:C2_ci95}}. H7-1 and H7-2 therefore stay untested; the generator remains a threat to
external validity.
The re-implemented three-family vote (E8, the closest analogue of JSTestCraft's three-LLM vote) reached F1
{{e8:summary:VOTE3|S1:f1}} against SC3's {{e8:summary:SC3|S1:f1}} ({{e8:hypotheses:H8-1:delta}}
{{e8:hypotheses:H8-1:ci95}}, p Holm {{e8:hypotheses:H8-1:p_holm}}).

## 6. Ablation studies (E4, one replicate, vs parent on identical instances)

| Ablation | F1 (MCC) | ΔF1 vs parent [95% CI] | p |
|---|---|---|---|
| A1 no argument exchange (DEB) | {{d1:A1|S1:f1}} ({{d1:A1|S1:mcc}}) | {{abl:A1|S1-DEB|S1:delta}} {{abl:A1|S1-DEB|S1:ci95}} | {{abl:A1|S1-DEB|S1:p}} |
| A2 neutral debaters (DEB) | {{d1:A2|S1:f1}} ({{d1:A2|S1:mcc}}) | {{abl:A2|S1-DEB|S1:delta}} {{abl:A2|S1-DEB|S1:ci95}} | {{abl:A2|S1-DEB|S1:p}} |
| A3 SC threshold ≥ 2/5 | {{sum:A3:SC|S1|A3 v>=2/5:f1}} ({{sum:A3:SC|S1|A3 v>=2/5:mcc}}) | — | — |
| A3 SC threshold ≥ 4/5 | {{sum:A3:SC|S1|A3 v>=4/5:f1}} ({{sum:A3:SC|S1|A3 v>=4/5:mcc}}) | — | — |
| A4 no failure evidence (J1) | {{d1:J1|S1|noF:f1}} ({{d1:J1|S1|noF:mcc}}) | {{abl:J1|S1|noF-J1|S1:delta}} {{abl:J1|S1|noF-J1|S1:ci95}} | {{abl:J1|S1|noF-J1|S1:p}} |
| A4 no failure evidence (SC) | {{d1:SC|S1|noF:f1}} ({{d1:SC|S1|noF:mcc}}) | {{abl:SC|S1|noF-SC|S1:delta}} {{abl:SC|S1|noF-SC|S1:ci95}} | {{abl:SC|S1|noF-SC|S1:p}} |
| A4 no failure evidence (DEB) | {{d1:DEB|S1|noF:f1}} ({{d1:DEB|S1|noF:mcc}}) | {{abl:DEB|S1|noF-DEB|S1:delta}} {{abl:DEB|S1|noF-DEB|S1:ci95}} | {{abl:DEB|S1|noF-DEB|S1:p}} |
| A5a buggy body shown (J1) | {{d1:J1|S1|impl:f1}} ({{d1:J1|S1|impl:mcc}}) | {{abl:J1|S1|impl-J1|S1:delta}} {{abl:J1|S1|impl-J1|S1:ci95}} | {{abl:J1|S1|impl-J1|S1:p}} |
| A5a buggy body shown (DEB) | {{d1:DEB|S1|impl:f1}} ({{d1:DEB|S1|impl:mcc}}) | {{abl:DEB|S1|impl-DEB|S1:delta}} {{abl:DEB|S1|impl-DEB|S1:ci95}} | {{abl:DEB|S1|impl-DEB|S1:p}} |
| A5b body-derived spec (J1, S2) | {{d1:J1|S2|specprime:f1}} ({{d1:J1|S2|specprime:mcc}}) | {{abl:J1|S2|specprime-J1|S2:delta}} {{abl:J1|S2|specprime-J1|S2:ci95}} | {{abl:J1|S2|specprime-J1|S2:p}} |

Removing the failure evidence is the only change with a clear effect: without it, J1 and SC fell to chance (MCC {{d1:J1|S1|noF:mcc}} and {{d1:SC|S1|noF:mcc}}) and DEB's F1 also dropped ({{abl:DEB|S1|noF-DEB|S1:delta}}, p {{abl:DEB|S1|noF-DEB|S1:p}}), though not significantly.

## 7. Results analysis and discussion

**Robustness (E5), F1 (MCC) at S1:**

| Arm | D1 M1 | D1 M2 | D2 M1 | D2 M2 |
|---|---|---|---|---|
| J1 | {{d1:J1|S1:f1}} ({{d1:J1|S1:mcc}}) | {{d1m2:J1|S1:f1}} ({{d1m2:J1|S1:mcc}}) | {{d2:J1|S1:f1}} ({{d2:J1|S1:mcc}}) | {{d2m2:J1|S1:f1}} ({{d2m2:J1|S1:mcc}}) |
| SC | {{d1:SC|S1:f1}} ({{d1:SC|S1:mcc}}) | {{d1m2:SC|S1:f1}} ({{d1m2:SC|S1:mcc}}) | {{d2:SC|S1:f1}} ({{d2:SC|S1:mcc}}) | {{d2m2:SC|S1:f1}} ({{d2m2:SC|S1:mcc}}) |
| DEB | {{d1:DEB|S1:f1}} ({{d1:DEB|S1:mcc}}) | {{d1m2:DEB|S1:f1}} ({{d1m2:DEB|S1:mcc}}) | {{d2:DEB|S1:f1}} ({{d2:DEB|S1:mcc}}) | {{d2m2:DEB|S1:f1}} ({{d2m2:DEB|S1:mcc}}) |

D2's PF prevalence ({{sum2:prevalence:pf_prevalence}}) differs from D1's ({{sum:prevalence:pf_prevalence}}), so keep-all
scores F1 {{d2:KA:f1}} on D2 at MCC {{d2:KA:mcc}}: F1 is not comparable between D1 and D2. M2 shares the generator's
model family (self-preference cannot be excluded); M2 − M1 for DEB on D1: {{r3:D1:m2_minus_m1:DEB:f1:delta}}
{{r3:D1:m2_minus_m1:DEB:f1:ci95}}.

**Exploratory qwen3.5:35b (not confirmatory; D-78, D-88, D-89).** Flash attention off, partial offload with shared
GPU memory, RAM gate waived, MoE with about 3B active parameters. J1 complete; DEB completed in E6a; SC stopped by the
safety rule after {{x35o:decisions_by_arm:SC}} decisions and not retried. On {{e6a:n_instances}} instances: J1 F1 {{e6a:summary:35B:J1:f1}}
(MCC {{e6a:summary:35B:J1:mcc}}), DEB {{e6a:summary:35B:DEB:f1}} (MCC {{e6a:summary:35B:DEB:mcc}}); 35B − M1 for DEB
{{e6a:35b_minus:DEB 35B-M1:f1:delta}} {{e6a:35b_minus:DEB 35B-M1:f1:ci95}}.

**Third-family judge (E6b; D-82, D-85–D-87).** Ministral 3 14B, the first candidate in the order fixed in advance to pass Step 1 and
dev gates G-a/G-b; D1-test S1, one replicate, {{e6b:n_instances}} instances / {{e6b:n_bugs}} bugs. F1 (MCC): J1
{{e6b:summary:J1:f1}} ({{e6b:summary:J1:mcc}}), SC {{e6b:summary:SC:f1}} ({{e6b:summary:SC:mcc}}), DEB
{{e6b:summary:DEB:f1}} ({{e6b:summary:DEB:mcc}}). H6-1 ΔF1(DEB − SC) {{e6b:hypotheses:H6-1:delta}}
{{e6b:hypotheses:H6-1:ci95}}, p Holm {{e6b:hypotheses:H6-1:p_holm}} — not supported; H6-2 MCC(DEB)
{{e6b:hypotheses:H6-2:mcc}} {{e6b:hypotheses:H6-2:ci95}}, p Holm {{e6b:hypotheses:H6-2:p_holm}} — supported; H6-3
(frozen τ = {{e6b:hypotheses:H6-3:tau}}) {{e6b:hypotheses:H6-3:delta}} {{e6b:hypotheses:H6-3:ci95}} — not supported. M2 (the generator's
family) scored above E6b in every arm (DEB {{e6b:family_check:e6b_minus:DEB E6B-M2:f1:delta}}
{{e6b:family_check:e6b_minus:DEB E6B-M2:f1:ci95}}), consistent with family affinity but confounded with the model.

**Three-family vote (E8; D-82, D-83, D-90).** Fresh J1 calls from M1, M2 and E6b; VOTE3 = one each, VOTE5 = 2 + 2 + 1.
F1 (MCC): VOTE3 {{e8:summary:VOTE3|S1:f1}} ({{e8:summary:VOTE3|S1:mcc}}), VOTE5 {{e8:summary:VOTE5|S1:f1}}
({{e8:summary:VOTE5|S1:mcc}}); M1 SC3 {{e8:summary:SC3|S1:f1}}, SC {{e8:summary:SC|S1:f1}}, DEB
{{e8:summary:DEB|S1:f1}}. H8-1 VOTE3 − SC3 {{e8:hypotheses:H8-1:delta}} {{e8:hypotheses:H8-1:ci95}} (p Holm
{{e8:hypotheses:H8-1:p_holm}}), H8-2 VOTE5 − SC {{e8:hypotheses:H8-2:delta}} {{e8:hypotheses:H8-2:ci95}} (p Holm
{{e8:hypotheses:H8-2:p_holm}}), H8-3 VOTE5 − DEB {{e8:hypotheses:H8-3:delta}} {{e8:hypotheses:H8-3:ci95}} (p Holm
{{e8:hypotheses:H8-3:p_holm}}): none supported after Holm. PF tests lost of {{e6b:pf_prevalence:PF}}: VOTE3
{{e8:summary:VOTE3|S1:pf_lost@0}}, VOTE5 {{e8:summary:VOTE5|S1:pf_lost@0}}, SC {{e8:summary:SC|S1:pf_lost@0}}, DEB
{{e8:summary:DEB|S1:pf_lost@0}}.

**Disclosed harness faults.** The E6b gate script crashed on a leakage-abort bookkeeping gap before any gate value was
produced (fixed, D-86); a unit test made {{q87:calls}} unplanned calls by a non-selected candidate on D1-test, quarantined unread
(D-87); the generation-truncation check (zero calls) found {{gtr:signals:union}} of {{gtr:generations}} generations
({{gtr:union_share@pct}}) cut off by length, so E7a keeps the frozen context (D-91); the G-selection script crashed on
{{e7a:tried:1:unparseable_classes}} llama3.1 classes with unbalanced braces and was fixed, counting them as generated but not
executed, before any of that candidate's values was computed (D-102).

**Keep unless unanimous, KUU (D-95; proposed design principle).** Discard a failure only when one J1 call each from
M1, M2 and E6b all say test fault; keep it otherwise (including on an invalid vote). No tuned parameter: debate's
confidence-100 rule set its threshold on the development split, KUU fits nothing to data. It is a safety rule, not a
better classifier. In JSTestCraft's vote a majority out-votes a dissenting judge; unanimity treats dissent as a reason
to keep. KUU was defined after the D1 vote (post hoc on D1) and tested once on unseen D2 under D-95.
On D1 (post hoc: F1 {{kuu1:summary:KUU|S1:f1}}, {{kuu1:summary:KUU|S1:pf_lost@0}}
of {{sum:prevalence:PF}} bug-revealing tests lost). **Confirmatory on D2** with fresh calls ({{kuu2:n_instances}} instances,
{{kuu2:n_bugs}} bugs): F1 {{kuu2:summary:KUU|S1:f1}} {{kuu2:summary:KUU|S1:f1_ci95}} against keep-all's
{{kuu2:summary:KA:f1}} — H10-1 ΔF1 {{kuu2:hypotheses:H10-1:delta}} {{kuu2:hypotheses:H10-1:ci95}}, p Holm
{{kuu2:hypotheses:H10-1:p_holm}}, supported; {{kuu2:summary:KUU|S1:pf_lost@0}} of {{kuu2:pf_prevalence:PF}}
bug-revealing tests lost against M1 DEB's {{kuu2:summary:DEB|S1:pf_lost@0}} — H10-2 p Holm
{{kuu2:hypotheses:H10-2:p_holm}}, supported; {{kuu2:share_discarded@pct0}} of failures discarded; MCC
{{kuu2:summary:KUU|S1:mcc}} against DEB's {{kuu2:summary:DEB|S1:mcc}}.

**Frontier reference point, not a protocol replication (E9; D-92, D-97).** Claude Sonnet 5.5 through the Message Batches
API on the {{e9:n_instances}} scored instances (J1 one replicate, DEB three; default sampling, no seeds; spend
US$ {{e9:spend_usd@2}}): J1 F1 {{e9:summary:J1|S1|SON:f1}}, DEB F1 {{e9:summary:DEB|S1|SON:f1}} (MCC
{{e9:summary:DEB|S1|SON:mcc}}); H9-1 DEB − J1 {{e9:hypotheses:H9-1:delta}} {{e9:hypotheses:H9-1:ci95}} (p Holm
{{e9:hypotheses:H9-1:p_holm}}) and H9-2 supported; Sonnet − M1 for DEB {{e9:sonnet_minus_m1:DEB:f1:delta}}
{{e9:sonnet_minus_m1:DEB:f1:ci95}}. DEB's run-to-run F1 range is {{e9:deb_run_to_run_spread:sonnet:f1:range}} for
Sonnet against {{e9:deb_run_to_run_spread:m1:f1:range}} for M1. Sonnet's training data very likely include Defects4J and
its fixes, so its D1 score may be inflated by memorisation; E9b (D-104) tested this on the D2 seeded faults (below).

**Replicate noise (D-94, exploratory).** M1's F1 range across its three replicates is {{rn:noise:J1:f1:range}} for J1,
{{rn:noise:SC:f1:range}} for SC and {{rn:noise:DEB:f1:range}} for DEB, so every single-replicate DEB difference across
judges lies within M1's own noise, while the J1, SC and vote-versus-SC differences exceed it.

**Keep unless unanimous with disagreement escalation (D-105; the method).** Tier 1 is KUU's three cross-family J1
votes. A unanimous TF vote discards and a unanimous PF vote keeps. Any disagreement, including an invalid vote, goes to
Sonnet's DEB, whose valid label decides; a missing answer keeps the test. The cascade and its hypotheses were committed (D-105) before any frontier call on D2, so its D2 result is confirmatory and its D1 result post hoc.

*Error diversity, fixed in advance.* On D2, two families miss the same PF test {{ed:D2:comparison:mean_cross_family_lift@1}}
times as often as independence predicts. Three samples of one model do so {{ed:D2:comparison:mean_within_family_lift@1}}
times as often (difference {{ed:D2:comparison:difference_ci95@ci2}}), and KUU lost {{ed:D2:kuu_loss:observed@0}}
tests where same-model unanimity would have lost {{ed:D2:within_family:M1:unanimous_loss@0}} (M1) and
{{ed:D2:within_family:M2:unanimous_loss@0}} (M2). The diversity is partial: independence predicts
{{ed:D2:kuu_loss:independence_prediction@2}} losses. On D1 (post hoc) the criterion fixed in advance is not met, because KUU's
single loss ties M2's.

*Cascade on D2.*
- {{cas2:escalation:escalated@0}} of {{cas2:n_instances}} instances escalated
  ({{cas2:escalation:share_escalated@pct0}}), so the other half of the failures never left the machine (100% leave for
  any frontier-everywhere option). Per instance: local tier {{pareto:D2:points:CAS|S1:local_gpu_s_per_instance@1}}
  GPU-seconds on one laptop GPU, frontier tier US$ {{pareto:D2:points:CAS|S1:frontier_usd_per_instance@3}}; Sonnet DEB
  on every instance US$ {{pareto:D2:points:DEB|S1|SON:frontier_usd_per_instance@3}}. No cost-dominance is claimed.
- **H12-1 is supported.** MCC was {{cas2:summary:CAS|S1:mcc}} against KUU's {{cas2:summary:KUU|S1:mcc}}
  (Δ {{cas2:hypotheses:H12-1:delta}} {{cas2:hypotheses:H12-1:ci95}}, p Holm {{cas2:hypotheses:H12-1:p_holm}}).
- **H12-2 is not supported.** F1 was {{cas2:summary:CAS|S1:f1}} against Sonnet DEB on every instance at
  {{cas2:summary:DEB|S1|SON:f1}} (Δ {{cas2:hypotheses:H12-2:delta}}, 95% CI {{cas2:hypotheses:H12-2:ci95}}). Its lower bound
  falls below the −0.05 margin, so non-inferiority is not shown.
- PF tests lost: {{cas2:summary:CAS|S1:pf_lost@0}} (KUU {{cas2:summary:KUU|S1:pf_lost@0}}, Sonnet
  {{cas2:summary:DEB|S1|SON:pf_lost@0}}, M1 DEB {{cas2:summary:DEB|S1:pf_lost@0}}).
- D1 (post hoc): MCC {{cas1:summary:CAS|S1:mcc}}, F1 {{cas1:summary:CAS|S1:f1}} against Sonnet's
  {{cas1:summary:DEB|S1|SON:f1}}.

**KUU-NG: no generator-family judge (D-109; fixed in advance).** M2 shares the generator's family, so
KUU's protection might rest on a judge reluctant to fault its sibling's tests. KUU-NG replaces M2 with a fourth family
chosen on the development split by the E6b rules: phi4 failed Step 1 (not fully GPU-resident),
{{kuungsel:selected}} passed Step 1 and gates G-a/G-b. Fresh J1 calls at S1, replicate index 30, for all three members.
- **D2.** F1 {{kuung:D2:summary:KUUNG|S1:f1}} against keep-all's {{kuung:D2:summary:KA:f1}}: H13-1 ΔF1
  {{kuung:D2:hypotheses:H13-1:delta}} {{kuung:D2:hypotheses:H13-1:ci95}}, p Holm {{kuung:D2:hypotheses:H13-1:p_holm}},
  supported. Bugs lost {{kuung:D2:summary:KUUNG|S1:bugs_lost@0}} against M1 DEB's {{kuung:D2:summary:DEB|S1:bugs_lost@0}}:
  H13-2 Δ {{kuung:D2:hypotheses:H13-2:delta@0}} {{kuung:D2:hypotheses:H13-2:ci95@ci0}}, p Holm
  {{kuung:D2:hypotheses:H13-2:p_holm}}, supported. PF tests lost {{kuung:D2:summary:KUUNG|S1:pf_lost@0}} (KUU
  {{kuung:D2:summary:KUU|S1:pf_lost@0}}, M1 + E6b pair {{kuung:D2:summary:PAIR_M1_E6B|S1:pf_lost@0}}).
- **D1** (the data KUU came from): H13-1 ΔF1 {{kuung:D1:hypotheses:H13-1:delta}}, p Holm
  {{kuung:D1:hypotheses:H13-1:p_holm}}; H13-2 Δ {{kuung:D1:hypotheses:H13-2:delta@0}}, p Holm
  {{kuung:D1:hypotheses:H13-2:p_holm}}; both supported.
- **The price.** KUU-NG discards {{kuung:D2:summary:KUUNG|S1:share_discarded@pct0}} of failures against KUU's
  {{kuung:D2:summary:KUU|S1:share_discarded@pct0}}; MCC {{kuung:D2:summary:KUUNG|S1:mcc}} against
  {{kuung:D2:summary:KUU|S1:mcc}} (Δ {{kuung:D2:kuung_minus_kuu_mcc:delta}} {{kuung:D2:kuung_minus_kuu_mcc:ci95}}, not
  significant).
- **Member votes (post hoc, D-111).** The new judge's PF miss rate is {{kuungm:D2:kuung:NG:miss_rate_on_pf}} against
  M2's {{kuungm:D2:kuu:M2:miss_rate_on_pf}}: it is not lenient, so the protection does not need a generator-family judge.

**Trade-off of every rule (D-110, post hoc, descriptive).** `paper/figures/fig_pareto.pdf` plots each rule's share of
failures discarded against its share of bug-revealing tests lost on D1-test and D2. On D2, single-model arms discard
about half and lose a third or more (M1 DEB {{pareto:D2:points:DEB|S1:share_discarded@pct0}} discarded,
{{pareto:D2:points:DEB|S1:pf_lost@0}} lost); KUU sits at {{pareto:D2:points:KUU|S1:share_discarded@pct0}} and
{{pareto:D2:points:KUU|S1:pf_lost@0}}, beside debate at confidence 100
({{pareto:D2:points:TAU|S1:share_discarded@pct0}}, {{pareto:D2:points:TAU|S1:pf_lost@0}}), the only tuned point; the
cascade ({{pareto:D2:points:CAS|S1:share_discarded@pct0}}, {{pareto:D2:points:CAS|S1:pf_lost@0}}) reaches Sonnet DEB's
region ({{pareto:D2:points:DEB|S1|SON:share_discarded@pct0}}, {{pareto:D2:points:DEB|S1|SON:pf_lost@0}}).

**Memorisation check, E9b (D-104).** Sonnet ran on the {{e9b:n_instances}} D2 instances, one replicate each of J1 and DEB,
spending US$ {{e9b:spend_usd@2}} with no refusals.
- **H11-1 is supported.** DEB MCC was {{e9b:summary:DEB|S1|SON:mcc}} {{e9b:hypotheses:H11-1:ci95}}.
- **H11-2 is supported.** Sonnet's DEB MCC exceeded M1's by {{e9b:hypotheses:H11-2:delta}} {{e9b:hypotheses:H11-2:ci95}}.
- DEB MCC was {{e9b:sonnet_d1_minus_d2_mcc:DEB:mcc_d1}} on D1 and {{e9b:sonnet_d1_minus_d2_mcc:DEB:mcc_d2}} on D2. There is
  no drop on faults whose fixes it cannot have seen, though D2 cannot exclude knowledge of the original code.

**Sensitivity analyses requested by two mock reviews (D-106, post hoc).** These are zero-call analyses, fixed
before computing; none re-reads a verdict.
- **MCC family.** On MCC no confirmatory test survives Holm, the same verdict as F1.
- **Two-level bootstrap.** Resampling bugs and replicates widens the confirmatory intervals by up to
  {{rv:two_level_bootstrap:1:widening_factor@1}}×.
- **Matched operating point.** M1 DEB at confidence 100 discards
  {{rv:operating_points_d2:summary:M1DEBtau100|S1:share_discarded@pct0}} and loses
  {{rv:operating_points_d2:summary:M1DEBtau100|S1:pf_lost@0}} bug-revealing tests. KUU discards
  {{rv:operating_points_d2:summary:KUU|S1:share_discarded@pct0}} and loses {{rv:operating_points_d2:summary:KUU|S1:pf_lost@0}}.
- **Cost frontier.** Sonnet J1 on every instance (US$ {{rv:frontier_d2:rows:Sonnet J1, every instance:frontier_usd@2}},
  MCC {{rv:frontier_d2:rows:Sonnet J1, every instance:mcc}}) is cheaper than the cascade at a similar MCC, but leaves more
  bugs uncovered ({{rv:frontier_d2:rows:Sonnet J1, every instance:bugs_with_no_pf_kept@0}} against
  {{rv:frontier_d2:rows:Cascade to Sonnet DEB:bugs_with_no_pf_kept@0}}).
- **Deployment prevalence.** At a 5% bug-revealing share, the cascade's precision would be
  {{rv:deployment_precision:D2:rules:CAS|S1:precision_at_0.05}}.
- **Leave-one-project-out.** H1, H3a and H3b never change sign.
- **Leave-one-judge-out (D-107).** Without M2, the M1 + E6b pair loses
  {{loo:D2:summary:M1_E6B|S1:pf_lost@0}} bug-revealing tests on D2 against KUU's {{loo:D2:summary:KUU|S1:pf_lost@0}}, so
  much of KUU's protection comes from M2, which shares the generator's family. It still loses far fewer than M1 DEB
  ({{loo:D2:summary:DEB|S1:pf_lost@0}}). KUU-NG (above) then tested the question with a third family in M2's place.

The triage of every objection is in `docs/paper/MOCK_REVIEW.md`.

**Findings.** (1) Failure evidence carries the signal (A4). (2) DEB has the highest MCC in every dataset × judge
combination, but H3a is not significant (p Holm {{conf:f1:H3a:p_holm}}), and by F1 SC is higher than DEB under M1 on
D2 ({{der:d2 SC-DEB f1}}). (3) Javadoc does not help and trends negative (H2a {{conf:f1:H2a:delta}}, p Holm
{{conf:f1:H2a:p_holm}}). The larger judge M2 improved every arm. The development gate (one-shot F1 below R0's) did not
predict the held-out result (one-shot F1 {{d1:J1|S1:f1}} vs R0 {{d1:R0:f1}}).

**Gaps and objectives.** G1 (accuracy against buggy/fixed truth): measured; confirmatory effects inconclusive at
{{sum:leakage_abort_exclusions:n_per_level:S1}} instances. G2 (specification): no gain from Javadoc or inferred
specifications. G3 (equal budget): small, non-significant debate advantage; SC does not beat J1. RQ4: KUU cut lost
bug-revealing tests without lowering F1, with or without a generator-family judge; escalation recovered MCC but not the
frontier judge's F1.

**Limitations.** Small sample; small local judges instead of the planned API models; M2 shares G's family (a third-family
judge only partly offsets this); D3 not run; the label audit covers development-split instances only (D-108: {{aud:n_items}} instances, human–human κ
{{aud2:raters:kappa}} {{aud2:raters:kappa_ci95_bug_bootstrap}}, consensus vs execution label
{{aud2:consensus_vs_execution:agreement@pct1}}, both mismatches execution TF judged PF; the sealed LLM rater agreed with
the consensus at κ {{aud2:llm_rater_secondary_D84:consensus_vs_C:kappa}}, secondary, D-84). The raters are the authors and
saw the developer's fix; the audit still tests the labelling rule, which is mechanical and identical on both splits.
Frame reconstructed; WSL2 instead of Docker; one replicate for E4/E5. Local compute is not priced: KUU used
{{pareto:D2:points:KUU|S1:local_gpu_s_per_instance@1}} and M1 DEB {{pareto:D2:points:DEB|S1:local_gpu_s_per_instance@1}}
GPU-seconds per D2 instance.

## 7b. Analyses added in response to review (D-112 to D-128; post hoc or exploratory)

Each was fixed in advance in the version-controlled decision log (`docs/tracking/DECISIONS.md`) before it was computed (internal provenance, not an external
registration); none joins a Holm family or re-reads a confirmatory verdict. Full tables: paper Appendix G; tracking:
`docs/tracking/REVIEWER_RESPONSE_MATRIX.md`.

- **Rates that do not depend on the class mix (D-113).** TPR = PF kept / PF, TNR = TF removed / TF, balanced accuracy
  (BA) = their mean. On D2: KUU TPR {{rv11:D2:rules:KUU|S1:tpr}}, TNR {{rv11:D2:rules:KUU|S1:tnr}}, BA
  {{rv11:D2:rules:KUU|S1:ba}}; M1 DEB BA {{rv11:D2:rules:DEB|S1:ba}}; cascade BA {{rv11:D2:rules:CAS|S1:ba}}. KUU is a
  safety rule: it keeps almost every bug-revealing test and removes a minority of test faults. At an assumed 5% PF
  prevalence it keeps {{rv11:D2:rules:KUU|S1:at_prevalence:0.0500:false_alarms_per_kept_pf@1}} test faults per
  bug-revealing test kept (keep-all {{rv11:D2:rules:KA:at_prevalence:0.0500:false_alarms_per_kept_pf@1}}). A new figure
  (`paper/figures/fig_tradeoff_rates.pdf`) plots PF-loss rate against TF-removal rate on one scale for D1 and D2.
- **Ranking (D-114).** AUROC on D2: KUU vote count {{rv13:D2:rules:KUU|S1:auroc}}, M1 DEB confidence
  {{rv13:D2:rules:DEB|S1:auroc}}, Sonnet DEB {{rv13:D2:rules:DEB|S1|SON:auroc}}. Inspecting the top 20% finds more
  bug-revealing tests than random for every judge, but Sonnet's top 20% on D2 covers fewer bugs
  ({{rv13:D2:rules:DEB|S1|SON:inspection:top20:bug_recall@2}}) than random inspection
  ({{rv13:D2:rules:KA:inspection:top20:bug_recall@2}}).
- **Trained baselines (D-115).** Leave-one-project-out on D1-test: failure features alone AUROC
  {{rv14:lopo:features:auroc}} {{rv14:lopo:features:auroc_ci95}}; the three votes, learned, BA {{rv14:lopo:votes:ba}} at
  TPR {{rv14:lopo:votes:tpr}} (KUU: BA {{rv11:D1:rules:KUU|S1:ba}}, TPR {{rv11:D1:rules:KUU|S1:tpr}}).
- **Cross-generation agreement (D-118)**, a zero-call signal from the buggy version only: AUROC
  {{rv17:D1:auroc_cg}} on D1, {{rv17:D2:auroc_cg}} on D2.
- **Risk-targeted threshold (D-117).** Calibrated on D1 to a 5% PF-loss target, it realised
  {{rv16:panels:KUU:thresholds:tests_alpha0.05:D2_evaluation:pf_loss_rate}} (KUU panel) and
  {{rv16:panels:KUU-NG:thresholds:tests_alpha0.05:D2_evaluation:pf_loss_rate}} (KUU-NG panel) on D2: not a guarantee,
  because D1 and D2 are not exchangeable and KUU was designed on D1.
- **Sample size (D-119).** An MDE of 0.08 on DEB − SC needs about {{rv18:tests:H3a:by_mde:0.08:bugs_alpha_005}} bugs
  ({{rv18:tests:H3a:by_mde:0.08:multiplier_alpha_005@1}}× the {{rv18:tests:H3a:n0_bugs}} now); planning guidance only.
- **Integrity (D-120).** Holm reproduced in {{der:holm all match}} {{der:holm families}} committed families; every
  interval resamples bugs; a frequentist GEE gives no specification effect (S0 OR
  {{rv19:mixed_model:gee:PF_recall:terms:1:odds_ratio}} {{rv19:mixed_model:gee:PF_recall:terms:1:or_ci95_robust}}).
- **Leakage guard and label noise (D-121).** The guard aborted {{rv110:guard:D2:aborted_at_S1_any_run}} of
  {{rv110:guard:D2:judged}} judged D2 instances, {{rv110:guard:D2:aborted_matched_kind:themutatedline}} on the injected
  line; relabelling up to 10% of TF assertion failures as PF leaves the order of the rules unchanged.
- **All held-out test faults judged (D-124).** {{rv2:tf296:n_tf_judged}} D1-test test faults judged by M1, M2, M3 and
  Llama: KUU removes {{rv2:tf296:rules:KUU:all:tnr@2}} of them and keeps
  {{rv2:tf296:rules:KUU:all:false_alarms_per_kept_pf@1}} test faults per bug-revealing test kept at the natural
  prevalence (keep-all {{rv2:tf296:rules:Keepall:all:false_alarms_per_kept_pf@1}}).
- **Greedy and repeated judges (D-125, D-127).** M1's one-shot judge at temperature 0: BA
  {{rv2:greedy:temperature_0:50:ba}}, F1 {{rv2:greedy:temperature_0:50:f1}} (at the frozen 0.7: BA {{rv11:D1:rules:J1|S1:ba}},
  F1 {{rv11:D1:rules:J1|S1:f1}}). M1 DEB over {{rv2:deb8:n_replicates}} runs: F1 range {{rv2:deb8:spread:f1:range}}, SD
  {{rv2:deb8:spread:f1:sd}}.
- **Thinking-enabled judge (D-126, one run, exploratory).** M1 with thinking on: BA {{rv2:think:heldout:60:ba}},
  F1 {{rv2:think:heldout:60:f1}}, MCC {{rv2:think:heldout:60:mcc}}, {{rv2:think:heldout:60:FN@0}} of
  {{sum:prevalence:PF}} bug-revealing tests lost, {{rv2:think:heldout:60:invalid@0}} outputs cut off by the output cap;
  {{rv2:think:heldout:60:consumed_tokens_per_instance@0}} tokens per instance against debate's
  {{rv2:think:deb_consumed_tokens_per_instance_table@0}} (not token-matched). Every planned arm ran with thinking off,
  so the RQ2/RQ3 results describe thinking-disabled judges. Followed up in §7c.
- **Judge gates (D-127).** {{der:local judges failing G-d@int}} of {{der:local judges gated}} local judges failed G-d on the
  development pilot, so RQ2/RQ3 nulls describe weak judges, not the factors.
- **Plans, nothing run (D-128).** A Sonnet factorial with a gate-passing judge (estimated new spend US$
  {{sfc:estimated:new_spend_usd@2}}, measured basis US$ {{sfc:measured:e9_usd_per_decision_S1:DEB@5}} per DEB decision);
  an OSF-ready RQ4 replication outline; the journal follow-up plan. All need the authors' approval.

## 7c. Thinking-judge follow-up (D-130, D-131)

The thinking-enabled result above came from one exploratory run, so the authors had it tested the way KUU was tested
(D-130): first its development gate, then a D2 confirmation with two hypotheses fixed in advance in the version-controlled decision log, before
any D2 call, then two more D1-test runs. The wording rule for the paper was fixed in the same entry, before the result.
Same configuration in every run: M1 J1 at S1, thinking on, context 16,384 tokens, output cap 8,192.

- **Development gate: failed.** On the {{tk:gate:n_instances@int}}-instance dev pilot, valid outputs
  {{tk:gate:G_a_valid_rate:J1@pct1}} (needs 98%; {{tk:gate:G_a_runaway_D39:J1:invalid_length@int}} cut off by the cap)
  and F1 {{tk:gate:G_d_detail:J1_f1}} against R0's {{tk:gate:G_d_detail:R0_f1}} (thinking off: {{tk:gate:m1_original:J1_f1}}).
  The gate is a check, not a stopping rule, so D2 went ahead as fixed in D-130.
- **D2 confirmation: both hypotheses supported** ({{tk:d2:confirmatory:n_instances@int}} instances,
  {{tk:d2:confirmatory:n_bugs@int}} bugs, one Holm family, thinking J1 against M1 DEB).
  HT-1: MCC {{tk:d2:descriptive:ThinkingM1J1:mcc}} against {{tk:d2:descriptive:M1DEB:mcc}}, ΔMCC
  {{tk:d2:confirmatory:HT-1:delta}} {{tk:d2:confirmatory:HT-1:ci95}}, p_Holm {{tk:d2:confirmatory:HT-1:p_holm}}.
  HT-2: {{tk:d2:confirmatory:HT-2:pf_lost_thinking@int}} against {{tk:d2:confirmatory:HT-2:pf_lost_deb@int}}
  bug-revealing tests lost, Δ {{tk:d2:confirmatory:HT-2:delta@int}} {{tk:d2:confirmatory:HT-2:ci95@ci0}}, p_Holm
  {{tk:d2:confirmatory:HT-2:p_holm}}.
- **Output cap.** {{tk:d2:capped@int}} D2 outputs were cut off. Scoring them as keep instead of TF gives ΔMCC
  {{tk:d2:policies:keep:hypotheses:HT-1:delta}} and Δ lost {{tk:d2:policies:keep:hypotheses:HT-2:delta@int}}; excluding
  them gives {{tk:d2:policies:exclude:hypotheses:HT-1:delta}} and {{tk:d2:policies:exclude:hypotheses:HT-2:delta@int}}.
  The verdict does not depend on the coding.
- **Beside the other rules on D2 (descriptive; BA / TPR / TNR; PF tests lost).** Thinking J1
  {{tk:d2:descriptive:ThinkingM1J1:ba}} / {{tk:d2:descriptive:ThinkingM1J1:tpr}} / {{tk:d2:descriptive:ThinkingM1J1:tnr}};
  {{tk:d2:descriptive:ThinkingM1J1:pf_lost@int}}. M1 DEB {{tk:d2:descriptive:M1DEB:ba}} / {{tk:d2:descriptive:M1DEB:tpr}} /
  {{tk:d2:descriptive:M1DEB:tnr}}; {{tk:d2:descriptive:M1DEB:pf_lost@int}}. KUU {{tk:d2:descriptive:KUU:ba}} /
  {{tk:d2:descriptive:KUU:tpr}} / {{tk:d2:descriptive:KUU:tnr}}; {{tk:d2:descriptive:KUU:pf_lost@int}}. Cascade
  {{tk:d2:descriptive:Cascade:ba}} / {{tk:d2:descriptive:Cascade:tpr}} / {{tk:d2:descriptive:Cascade:tnr}};
  {{tk:d2:descriptive:Cascade:pf_lost@int}}. Sonnet DEB {{tk:d2:descriptive:SonnetDEB:ba}} /
  {{tk:d2:descriptive:SonnetDEB:tpr}} / {{tk:d2:descriptive:SonnetDEB:tnr}}; {{tk:d2:descriptive:SonnetDEB:pf_lost@int}}.
  KUU still keeps {{tk:d2:kuu_vs_thinking:pf_lost_by_thinking_kept_by_kuu@int}} bug-revealing tests the thinking judge
  loses ({{tk:d2:kuu_vs_thinking:pf_lost_by_kuu_kept_by_thinking@int}} the reverse), so the thinking judge is a better
  classifier, not a safety rule.
- **D1-test, three runs (exploratory).** BA {{tk:d1:summary:ba:min}}–{{tk:d1:summary:ba:max}}, MCC
  {{tk:d1:summary:mcc:min}}–{{tk:d1:summary:mcc:max}}, F1 {{tk:d1:summary:f1:min}}–{{tk:d1:summary:f1:max}} (M1 DEB over
  eight runs: F1 {{tk:d1:deb_eight_runs:f1:min}}–{{tk:d1:deb_eight_runs:f1:max}}); PF tests lost
  {{tk:d1:summary:pf_lost:min@0}}–{{tk:d1:summary:pf_lost:max@0}} of {{sum:prevalence:PF}}.
- **Tokens.** Prompt plus generated tokens, thinking included: {{tk:d1:summary:tokens_per_instance:mean@0}} per D1-test
  instance (mean of the runs) and {{tk:d2:tokens_per_instance@0}} per D2 instance, against debate's
  {{tk:deb_tokens_per_instance_D1@0}} on D1-test. The arm is not token-matched to debate; it happens to use fewer.
- **What changed in the paper (branch A of the D-130 rule).** The planned-arm findings are scoped to "with thinking
  disabled" in the abstract, contributions and conclusion; the abstract and conclusion report the confirmed result with
  the gate failure beside it; the Discussion has a paragraph on test-time reasoning against orchestration; RQ4 says
  what KUU adds beyond the thinking judge. The claim is limited to M1's own planned arms, because the 12B M2's debate
  scored about as high on D1-test (MCC {{d1m2:DEB|S1:mcc}}, inside the thinking range {{tk:d1:summary:mcc:min}}–{{tk:d1:summary:mcc:max}}).

## 8. Deviations and reproducibility

Deviations: `docs/tracking/EXPERIMENT_DEVIATIONS.md` (X-01 … X-09) and `docs/tracking/DECISIONS.md` (D-01 … D-128).
Frozen configuration: `configs/local_models.FROZEN.json`; environment manifest: `env/environment_manifest.json`;
reproduction steps: `docs/REPRODUCIBILITY_GUIDE.md` and `docs/local_models/ZERO_COST_REPRODUCIBILITY_PLAN.md`; analysis
commands: `results/heldout/analysis_final/MANIFEST.json`. **TODO (authors):** public repository URL.
