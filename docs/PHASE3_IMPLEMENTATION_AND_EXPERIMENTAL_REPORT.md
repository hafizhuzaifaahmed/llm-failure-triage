<!-- generated from docs/phase3/PHASE3_REPORT.src.md by scripts/paper/build_numbers.py; every number is in docs/paper/NUMBERS_MAP.csv -->
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
1,758 candidate methods screened, 312 focal methods from 220 defects
kept (the original reports 318 / 233); the
per-project cap leaves 234 methods from 167 defects. Project split (seeded,
before any generation): development 39 methods (Cli, Gson, Jsoup); held-out 195
methods from 14 projects.

**Generation, execution, labels.** Three generations per focal method by G. Across both D1 splits
2,909 test methods were executed: 2,284 passed on the buggy version,
102 were misguided, 518 did not compile on one version,
6 timed out. Held-out labels: 60 PF, 296 TF,
13 AMB.

**Evaluation samples.** All PF kept; TF sampled to twice the PF count over the split, stratified by project, with
inverse-probability weights. Judged D1-test sample (counts): 60 PF,
120 TF, 13 AMB.
Leakage-guard aborts at S1: 4 instances, excluded from
every arm at that level (D-70) → 177 scored instances at S1
(PF prevalence 0.339).
D2 (seeded faults): 284 mutants → 468 PF,
349 TF, 65 AMB; judged sample capped at
300 (159 PF,
119 TF, 22 AMB),
270 scored; PF prevalence 0.570. D3 (GitBug-Java) not run (needs Docker).

**Models (all local, zero API cost).** Ollama 0.40.13 on NVIDIA GeForce RTX 5070 Ti Laptop GPU
(12,227 MiB VRAM, 31 GB RAM). G = `gemma4:26b`,
M1 = `qwen3.5:9b`, M2 = `gemma4:12b`, all Q4_K_M, thinking off, frozen before any held-out call
(D-57). Judges: temperature 0.7, top-p 1.0,
context 8,192 tokens, output ≤ 512
tokens, per-call seed, 3 replicates for E1–E3; SC = 5 samples; k_T = 5.
Generator selection on dev: reliability 0.595 (CI [0.445, 0.733]), assertion validity 0.725, PF yield
5.0%. M1 development gate: one-shot F1 0.350 (MCC −0.032) vs
R0 0.642 (MCC 0.363) on 55 instances /
12 bugs — **failed**, reported, M1 kept (D-48–D-52). Non-determinism: 0%
label flips over 49 repeated judgements.

**Statistics.** Per-replicate metrics averaged; bug-level cluster bootstrap (10,000 resamples) for CIs and paired
differences; five confirmatory F1 tests Holm-corrected; equivalence margin ±0.05 F1 (90% CI).

## 3. Baseline evaluation (E1, S1, D1-test, judge M1)

| Arm | F1 [95% CI] | MCC [95% CI] | Precision | Recall | Prec. at natural prevalence | PF tests lost |
|---|---|---|---|---|---|---|
| DA (discard-all) | 0 | 0 | n/a | 0 | n/a | 60 |
| KA (keep-all) | 0.506 [0.355, 0.633] | 0 | 0.339 | 1 | 0.172 | 0 |
| R0 (rule-based) | 0.266 [0.110, 0.429] | −0.077 [−0.284, 0.158] | 0.283 | 0.250 | 0.139 | 45 |
| J1 | 0.460 [0.329, 0.556] | 0.174 [0.032, 0.300] | 0.450 | 0.472 | 0.250 | 31.7 |
| SC | 0.436 [0.263, 0.573] | 0.187 [−0.012, 0.366] | 0.480 | 0.400 | 0.272 | 36.0 |
| SC-T | 0.464 [0.289, 0.593] | 0.238 [0.040, 0.408] | 0.524 | 0.417 | 0.311 | 35.0 |
| DEB | 0.511 [0.378, 0.613] | 0.267 [0.126, 0.405] | 0.523 | 0.500 | 0.315 | 30.0 |

Keep-all's F1 (0.506) sits at the level of the best LLM arm with MCC 0; MCC separates the arms
from chance. **Confirmatory tests (Holm):**

| H | Contrast | ΔF1 | 95% CI | p | p (Holm) |
|---|---|---|---|---|---|
| H1 | J1 − R0 | +0.195 | [−0.006, 0.370] | 0.058 | 0.233 |
| H2a | S1 − S0 (Javadoc subset) | −0.050 | [−0.091, −0.006] | 0.023 | 0.116 |
| H2b | S2 − S1 | +0.019 | [−0.024, 0.064] | 0.399 | 0.798 |
| H3a | DEB − SC | +0.074 | [−0.031, 0.201] | 0.177 | 0.532 |
| H3b | SC − J1 | −0.024 | [−0.104, 0.055] | 0.524 | 0.798 |

All five are inconclusive at this sample size (none significant after Holm, none equivalent).

**Specification levels (E2), F1 (MCC):**

| Level | J1 | SC | DEB |
|---|---|---|---|
| S0 | 0.494 (0.220) | 0.502 (0.290) | 0.550 (0.311) |
| S1 | 0.460 (0.174) | 0.436 (0.187) | 0.511 (0.267) |
| S2 | 0.477 (0.202) | 0.493 (0.232) | 0.493 (0.228) |

**Equal budget (E3):** consumed tokens per instance J1 1,913, SC
9,551, SC-T 9,550, DEB
9,188; DEB − SC-T ΔF1 +0.047 [−0.059, 0.168].

**Mixed model (exploratory, PF recall, odds ratios vs S1 with bug-level cluster-bootstrap 95% intervals, 200 refits):** S0 1.315 [0.904, 1.969], S2 1.600 [0.908, 2.729]; on TF instances S0 1.352 [0.997, 1.931].

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

Only JSTestCraft reports a triage metric (audited recall 68.75%\*); JavaOracle reports a precision
of 0.889\* (\* = taken from the paper, not comparable: other language and data, audit-based
labels, different prevalence, larger models). On identical D1-test instances, DEB's F1 exceeds the re-implemented
rule baseline R0 by +0.245 (relative +92.3%), SC (the single-model analogue of
JSTestCraft's vote) by +0.074 and keep-all by +0.004; none is significant after Holm.
DEB's recall (0.500) and precision (0.523) are below the two published figures. No
improvement over a base paper can be computed, because no base paper reports a triage result on this data, metric or
label source.
Our numbers differ from the base papers in language, label source (execution, not an audit), judge size (E9 is the
frontier reference), task and metric, and prevalence; where the designs meet they agree: the effective-test interval
overlaps Zhao et al.'s range (their package carries no generated tests to re-run, D-98), a cross-family vote keeps
recall high (0.900) as JSTestCraft's does, and debate trades away true positives as JavaOracle's
does. E7b (GitBug-Java) was not run: first its setup exceeded the free disk (D-101), and once disk was freed its premise
failed, because its bugs date from 2023 while every model here is a 2026 release, so it cannot test memorisation (D-103).
E7a (a second generator from a third family, D-100) was not run either, because neither candidate passed the D-22
selection on dev: phi4 14B executed 0.378 [0.270, 0.490] of its generated methods (C1, threshold
0.50; C2 0.555, P1 0.136), llama3.1 8B 0.166 [0.099, 0.241] with C2
0.359 [0.210, 0.519]. H7-1 and H7-2 therefore stay untested; the generator remains a threat to
external validity.
The re-implemented three-family vote (E8, the closest analogue of JSTestCraft's three-LLM vote) reached F1
0.614 against SC3's 0.463 (+0.150
[0.024, 0.279], p Holm 0.063).

## 6. Ablation studies (E4, one replicate, vs parent on identical instances)

| Ablation | F1 (MCC) | ΔF1 vs parent [95% CI] | p |
|---|---|---|---|
| A1 no argument exchange (DEB) | 0.526 (0.249) | +0.016 [−0.074, 0.105] | 0.731 |
| A2 neutral debaters (DEB) | 0.561 (0.293) | +0.051 [−0.039, 0.141] | 0.266 |
| A3 SC threshold ≥ 2/5 | 0.546 (0.263) | — | — |
| A3 SC threshold ≥ 4/5 | 0.324 (0.154) | — | — |
| A4 no failure evidence (J1) | 0.297 (0.031) | −0.163 [−0.314, −0.006] | 0.042 |
| A4 no failure evidence (SC) | 0.154 (−0.004) | −0.282 [−0.490, −0.083] | 0.003 |
| A4 no failure evidence (DEB) | 0.389 (0.127) | −0.122 [−0.282, 0.034] | 0.136 |
| A5a buggy body shown (J1) | 0.488 (0.222) | +0.036 [−0.053, 0.122] | 0.406 |
| A5a buggy body shown (DEB) | 0.425 (0.164) | −0.086 [−0.214, 0.045] | 0.193 |
| A5b body-derived spec (J1, S2) | 0.518 (0.231) | +0.042 [−0.040, 0.132] | 0.330 |

Removing the failure evidence is the only change with a clear effect: without it, J1 and SC fell to chance (MCC 0.031 and −0.004) and DEB's F1 also dropped (−0.122, p 0.136), though not significantly.

## 7. Results analysis and discussion

**Robustness (E5), F1 (MCC) at S1:**

| Arm | D1 M1 | D1 M2 | D2 M1 | D2 M2 |
|---|---|---|---|---|
| J1 | 0.460 (0.174) | 0.599 (0.358) | 0.647 (0.301) | 0.787 (0.420) |
| SC | 0.436 (0.187) | 0.599 (0.358) | 0.708 (0.383) | 0.784 (0.410) |
| DEB | 0.511 (0.267) | 0.727 (0.571) | 0.700 (0.392) | 0.855 (0.644) |

D2's PF prevalence (0.570) differs from D1's (0.339), so keep-all
scores F1 0.726 on D2 at MCC 0: F1 is not comparable between D1 and D2. M2 shares the generator's
model family (self-preference cannot be excluded); M2 − M1 for DEB on D1: +0.217
[0.109, 0.314].

**Exploratory qwen3.5:35b (not confirmatory; D-78, D-88, D-89).** Flash attention off, partial offload with shared
GPU memory, RAM gate waived, MoE with about 3B active parameters. J1 complete; DEB completed in E6a; SC stopped by the
safety rule after 5 decisions and not retried. On 177 instances: J1 F1 0.576
(MCC 0.317), DEB 0.644 (MCC 0.426); 35B − M1 for DEB
+0.133 [0.018, 0.247].

**Third-family judge (E6b; D-82, D-85–D-87).** Ministral 3 14B, the first candidate in the order fixed in advance to pass Step 1 and
dev gates G-a/G-b; D1-test S1, one replicate, 177 instances / 60 bugs. F1 (MCC): J1
0.555 (0.234), SC 0.570 (0.274), DEB
0.592 (0.337). H6-1 ΔF1(DEB − SC) +0.022
[−0.033, 0.080], p Holm 0.419 — not supported; H6-2 MCC(DEB)
0.337 [0.226, 0.435], p Holm <0.001 — supported; H6-3
(frozen τ = 80) +0.004 [−0.021, 0.035] — not supported. M2 (the generator's
family) scored above E6b in every arm (DEB −0.135
[−0.223, −0.039]), consistent with family affinity but confounded with the model.

**Three-family vote (E8; D-82, D-83, D-90).** Fresh J1 calls from M1, M2 and E6b; VOTE3 = one each, VOTE5 = 2 + 2 + 1.
F1 (MCC): VOTE3 0.614 (0.369), VOTE5 0.575
(0.282); M1 SC3 0.463, SC 0.436, DEB
0.511. H8-1 VOTE3 − SC3 +0.150 [0.024, 0.279] (p Holm
0.063), H8-2 VOTE5 − SC +0.138 [−0.004, 0.289] (p Holm
0.113), H8-3 VOTE5 − DEB +0.064 [−0.055, 0.182] (p Holm
0.285): none supported after Holm. PF tests lost of 60: VOTE3
6, VOTE5 8, SC 36, DEB
30.

**Disclosed harness faults.** The E6b gate script crashed on a leakage-abort bookkeeping gap before any gate value was
produced (fixed, D-86); a unit test made 17 unplanned calls by a non-selected candidate on D1-test, quarantined unread
(D-87); the generation-truncation check (zero calls) found 5 of 702 generations
(0.7%) cut off by length, so E7a keeps the frozen context (D-91); the G-selection script crashed on
2 llama3.1 classes with unbalanced braces and was fixed, counting them as generated but not
executed, before any of that candidate's values was computed (D-102).

**Keep unless unanimous, KUU (D-95; proposed design principle).** Discard a failure only when one J1 call each from
M1, M2 and E6b all say test fault; keep it otherwise (including on an invalid vote). No tuned parameter: debate's
confidence-100 rule set its threshold on the development split, KUU fits nothing to data. It is a safety rule, not a
better classifier. In JSTestCraft's vote a majority out-votes a dissenting judge; unanimity treats dissent as a reason
to keep. KUU was defined after the D1 vote (post hoc on D1) and tested once on unseen D2 under D-95.
On D1 (post hoc: F1 0.557, 1
of 60 bug-revealing tests lost). **Confirmatory on D2** with fresh calls (270 instances,
64 bugs): F1 0.771 [0.686, 0.837] against keep-all's
0.726 — H10-1 ΔF1 +0.045 [0.005, 0.096], p Holm
0.019, supported; 4 of 154
bug-revealing tests lost against M1 DEB's 56 — H10-2 p Holm
<0.001, supported; 13% of failures discarded; MCC
0.356 against DEB's 0.392.

**Frontier reference point, not a protocol replication (E9; D-92, D-97).** Claude Sonnet 5.5 through the Message Batches
API on the 177 scored instances (J1 one replicate, DEB three; default sampling, no seeds; spend
US$ 13.11): J1 F1 0.745, DEB F1 0.823 (MCC
0.734); H9-1 DEB − J1 +0.077 [0.003, 0.176] (p Holm
0.040) and H9-2 supported; Sonnet − M1 for DEB +0.312
[0.176, 0.441]. DEB's run-to-run F1 range is 0.024 for
Sonnet against 0.221 for M1. Sonnet's training data very likely include Defects4J and
its fixes, so its D1 score may be inflated by memorisation; E9b (D-104) tested this on the D2 seeded faults (below).

**Replicate noise (D-94, exploratory).** M1's F1 range across its three replicates is 0.042 for J1,
0.065 for SC and 0.221 for DEB, so every single-replicate DEB difference across
judges lies within M1's own noise, while the J1, SC and vote-versus-SC differences exceed it.

**Keep unless unanimous with disagreement escalation (D-105; the method).** Tier 1 is KUU's three cross-family J1
votes. A unanimous TF vote discards and a unanimous PF vote keeps. Any disagreement, including an invalid vote, goes to
Sonnet's DEB, whose valid label decides; a missing answer keeps the test. The cascade and its hypotheses were committed (D-105) before any frontier call on D2, so its D2 result is confirmatory and its D1 result post hoc.

*Error diversity, fixed in advance.* On D2, two families miss the same PF test 2.1
times as often as independence predicts. Three samples of one model do so 7.7
times as often (difference [−19.19, −2.55]), and KUU lost 4
tests where same-model unanimity would have lost 18 (M1) and
11 (M2). The diversity is partial: independence predicts
0.62 losses. On D1 (post hoc) the criterion fixed in advance is not met, because KUU's
single loss ties M2's.

*Cascade on D2.*
- 134 of 270 instances escalated
  (50%), so the other half of the failures never left the machine (100% leave for
  any frontier-everywhere option). Per instance: local tier 8.0
  GPU-seconds on one laptop GPU, frontier tier US$ 0.011; Sonnet DEB
  on every instance US$ 0.024. No cost-dominance is claimed.
- **H12-1 is supported.** MCC was 0.666 against KUU's 0.356
  (Δ +0.311 [0.202, 0.460], p Holm <0.001).
- **H12-2 is not supported.** F1 was 0.863 against Sonnet DEB on every instance at
  0.910 (Δ −0.046, 95% CI [−0.081, −0.018]). Its lower bound
  falls below the −0.05 margin, so non-inferiority is not shown.
- PF tests lost: 15 (KUU 4, Sonnet
  13, M1 DEB 56).
- D1 (post hoc): MCC 0.595, F1 0.741 against Sonnet's
  0.823.

**KUU-NG: no generator-family judge (D-109; fixed in advance).** M2 shares the generator's family, so
KUU's protection might rest on a judge reluctant to fault its sibling's tests. KUU-NG replaces M2 with a fourth family
chosen on the development split by the E6b rules: phi4 failed Step 1 (not fully GPU-resident),
llama3.1:8b-instruct-q4_K_M passed Step 1 and gates G-a/G-b. Fresh J1 calls at S1, replicate index 30, for all three members.
- **D2.** F1 0.756 against keep-all's 0.726: H13-1 ΔF1
  +0.029 [0.007, 0.058], p Holm 0.003,
  supported. Bugs lost 0 against M1 DEB's 10:
  H13-2 Δ −10 [−16, −5], p Holm
  <0.001, supported. PF tests lost 1 (KUU
  4, M1 + E6b pair 16).
- **D1** (the data KUU came from): H13-1 ΔF1 +0.040, p Holm
  0.011; H13-2 Δ −7, p Holm
  <0.001; both supported.
- **The price.** KUU-NG discards 7% of failures against KUU's
  13%; MCC 0.288 against
  0.356 (Δ −0.068 [−0.214, 0.101], not
  significant).
- **Member votes (post hoc, D-111).** The new judge's PF miss rate is 0.318 against
  M2's 0.065: it is not lenient, so the protection does not need a generator-family judge.

**Trade-off of every rule (D-110, post hoc, descriptive).** `paper/figures/fig_pareto.pdf` plots each rule's share of
failures discarded against its share of bug-revealing tests lost on D1-test and D2. On D2, single-model arms discard
about half and lose a third or more (M1 DEB 53% discarded,
56 lost); KUU sits at 13% and
4, beside debate at confidence 100
(14%, 6), the only tuned point; the
cascade (38%, 15) reaches Sonnet DEB's
region (42%, 13).

**Memorisation check, E9b (D-104).** Sonnet ran on the 270 D2 instances, one replicate each of J1 and DEB,
spending US$ 7.65 with no refusals.
- **H11-1 is supported.** DEB MCC was 0.788 [0.670, 0.889].
- **H11-2 is supported.** Sonnet's DEB MCC exceeded M1's by +0.396 [0.263, 0.535].
- DEB MCC was 0.734 on D1 and 0.788 on D2. There is
  no drop on faults whose fixes it cannot have seen, though D2 cannot exclude knowledge of the original code.

**Sensitivity analyses requested by two mock reviews (D-106, post hoc).** These are zero-call analyses, fixed
before computing; none re-reads a verdict.
- **MCC family.** On MCC no confirmatory test survives Holm, the same verdict as F1.
- **Two-level bootstrap.** Resampling bugs and replicates widens the confirmatory intervals by up to
  1.6×.
- **Matched operating point.** M1 DEB at confidence 100 discards
  14% and loses
  6 bug-revealing tests. KUU discards
  13% and loses 4.
- **Cost frontier.** Sonnet J1 on every instance (US$ 1.18,
  MCC 0.687) is cheaper than the cascade at a similar MCC, but leaves more
  bugs uncovered (7 against
  2).
- **Deployment prevalence.** At a 5% bug-revealing share, the cascade's precision would be
  0.160.
- **Leave-one-project-out.** H1, H3a and H3b never change sign.
- **Leave-one-judge-out (D-107).** Without M2, the M1 + E6b pair loses
  16 bug-revealing tests on D2 against KUU's 4, so
  much of KUU's protection comes from M2, which shares the generator's family. It still loses far fewer than M1 DEB
  (56). KUU-NG (above) then tested the question with a third family in M2's place.

The triage of every objection is in `docs/paper/MOCK_REVIEW.md`.

**Findings.** (1) Failure evidence carries the signal (A4). (2) DEB has the highest MCC in every dataset × judge
combination, but H3a is not significant (p Holm 0.532), and by F1 SC is higher than DEB under M1 on
D2 (+0.008). (3) Javadoc does not help and trends negative (H2a −0.050, p Holm
0.116). The larger judge M2 improved every arm. The development gate (one-shot F1 below R0's) did not
predict the held-out result (one-shot F1 0.460 vs R0 0.266).

**Gaps and objectives.** G1 (accuracy against buggy/fixed truth): measured; confirmatory effects inconclusive at
177 instances. G2 (specification): no gain from Javadoc or inferred
specifications. G3 (equal budget): small, non-significant debate advantage; SC does not beat J1. RQ4: KUU cut lost
bug-revealing tests without lowering F1, with or without a generator-family judge; escalation recovered MCC but not the
frontier judge's F1.

**Limitations.** Small sample; small local judges instead of the planned API models; M2 shares G's family (a third-family
judge only partly offsets this); D3 not run; the label audit covers development-split instances only (D-108: 71 instances, human–human κ
0.936 [0.638, 1.000], consensus vs execution label
97.2%, both mismatches execution TF judged PF; the sealed LLM rater agreed with
the consensus at κ 0.903, secondary, D-84). The raters are the authors and
saw the developer's fix; the audit still tests the labelling rule, which is mechanical and identical on both splits.
Frame reconstructed; WSL2 instead of Docker; one replicate for E4/E5. Local compute is not priced: KUU used
8.0 and M1 DEB 13.6
GPU-seconds per D2 instance.

## 7b. Analyses added in response to review (D-112 to D-128; post hoc or exploratory)

Each was fixed in advance in the version-controlled decision log (`docs/tracking/DECISIONS.md`) before it was computed (internal provenance, not an external
registration); none joins a Holm family or re-reads a confirmatory verdict. Full tables: paper Appendix G; tracking:
`docs/tracking/REVIEWER_RESPONSE_MATRIX.md`.

- **Rates that do not depend on the class mix (D-113).** TPR = PF kept / PF, TNR = TF removed / TF, balanced accuracy
  (BA) = their mean. On D2: KUU TPR 0.974, TNR 0.267, BA
  0.621; M1 DEB BA 0.697; cascade BA 0.826. KUU is a
  safety rule: it keeps almost every bug-revealing test and removes a minority of test faults. At an assumed 5% PF
  prevalence it keeps 14.3 test faults per
  bug-revealing test kept (keep-all 19.0). A new figure
  (`paper/figures/fig_tradeoff_rates.pdf`) plots PF-loss rate against TF-removal rate on one scale for D1 and D2.
- **Ranking (D-114).** AUROC on D2: KUU vote count 0.756, M1 DEB confidence
  0.760, Sonnet DEB 0.970. Inspecting the top 20% finds more
  bug-revealing tests than random for every judge, but Sonnet's top 20% on D2 covers fewer bugs
  (0.45) than random inspection
  (0.51).
- **Trained baselines (D-115).** Leave-one-project-out on D1-test: failure features alone AUROC
  0.554 [0.394, 0.710]; the three votes, learned, BA 0.698 at
  TPR 0.883 (KUU: BA 0.594, TPR 0.983).
- **Cross-generation agreement (D-118)**, a zero-call signal from the buggy version only: AUROC
  0.513 on D1, 0.708 on D2.
- **Risk-targeted threshold (D-117).** Calibrated on D1 to a 5% PF-loss target, it realised
  0.026 (KUU panel) and
  0.065 (KUU-NG panel) on D2: not a guarantee,
  because D1 and D2 are not exchangeable and KUU was designed on D1.
- **Sample size (D-119).** An MDE of 0.08 on DEB − SC needs about 257 bugs
  (4.3× the 60 now); planning guidance only.
- **Integrity (D-120).** Holm reproduced in all 10 committed families; every
  interval resamples bugs; a frequentist GEE gives no specification effect (S0 OR
  1.258 [0.896, 1.768]).
- **Leakage guard and label noise (D-121).** The guard aborted 8 of
  300 judged D2 instances, 5 on the injected
  line; relabelling up to 10% of TF assertion failures as PF leaves the order of the rules unchanged.
- **All held-out test faults judged (D-124).** 290 D1-test test faults judged by M1, M2, M3 and
  Llama: KUU removes 0.23 of them and keeps
  3.8 test faults per bug-revealing test kept at the natural
  prevalence (keep-all 4.8).
- **Greedy and repeated judges (D-125, D-127).** M1's one-shot judge at temperature 0: BA
  0.589, F1 0.430 (at the frozen 0.7: BA 0.588,
  F1 0.460). M1 DEB over 8 runs: F1 range 0.221, SD
  0.076.
- **Thinking-enabled judge (D-126, one run, exploratory).** M1 with thinking on: BA 0.771,
  F1 0.693, MCC 0.513, 7 of
  60 bug-revealing tests lost, 9 outputs cut off by the output cap;
  6,800 tokens per instance against debate's
  9,188 (not token-matched). Every planned arm ran with thinking off,
  so the RQ2/RQ3 results describe thinking-disabled judges. Followed up in §7c.
- **Judge gates (D-127).** 4 of 4 local judges failed G-d on the
  development pilot, so RQ2/RQ3 nulls describe weak judges, not the factors.
- **Plans, nothing run (D-128).** A Sonnet factorial with a gate-passing judge (estimated new spend US$
  66.14, measured basis US$ 0.023 per DEB decision);
  an OSF-ready RQ4 replication outline; the journal follow-up plan. All need the authors' approval.

## 7c. Thinking-judge follow-up (D-130, D-131)

The thinking-enabled result above came from one exploratory run, so the authors had it tested the way KUU was tested
(D-130): first its development gate, then a D2 confirmation with two hypotheses fixed in advance in the version-controlled decision log, before
any D2 call, then two more D1-test runs. The wording rule for the paper was fixed in the same entry, before the result.
Same configuration in every run: M1 J1 at S1, thinking on, context 16,384 tokens, output cap 8,192.

- **Development gate: failed.** On the 55-instance dev pilot, valid outputs
  96.8% (needs 98%; 2 cut off by the cap)
  and F1 0.312 against R0's 0.642 (thinking off: 0.350).
  The gate is a check, not a stopping rule, so D2 went ahead as fixed in D-130.
- **D2 confirmation: both hypotheses supported** (270 instances,
  64 bugs, one Holm family, thinking J1 against M1 DEB).
  HT-1: MCC 0.659 against 0.392, ΔMCC
  +0.267 [0.146, 0.391], p_Holm <0.001.
  HT-2: 8 against 56
  bug-revealing tests lost, Δ −48 [−65, −32], p_Holm
  <0.001.
- **Output cap.** 9 D2 outputs were cut off. Scoring them as keep instead of TF gives ΔMCC
  +0.253 and Δ lost −51; excluding
  them gives +0.259 and −50.
  The verdict does not depend on the coding.
- **Beside the other rules on D2 (descriptive; BA / TPR / TNR; PF tests lost).** Thinking J1
  0.810 / 0.948 / 0.672;
  8. M1 DEB 0.697 / 0.636 /
  0.759; 56. KUU 0.621 /
  0.974 / 0.267; 4. Cascade
  0.826 / 0.903 / 0.750;
  15. Sonnet DEB 0.893 /
  0.916 / 0.871; 13.
  KUU still keeps 6 bug-revealing tests the thinking judge
  loses (2 the reverse), so the thinking judge is a better
  classifier, not a safety rule.
- **D1-test, three runs (exploratory).** BA 0.771–0.817, MCC
  0.513–0.601, F1 0.693–0.742 (M1 DEB over
  eight runs: F1 0.393–0.614); PF tests lost
  4–7 of 60.
- **Tokens.** Prompt plus generated tokens, thinking included: 6,753 per D1-test
  instance (mean of the runs) and 6,356 per D2 instance, against debate's
  9,188 on D1-test. The arm is not token-matched to debate; it happens to use fewer.
- **What changed in the paper (branch A of the D-130 rule).** The planned-arm findings are scoped to "with thinking
  disabled" in the abstract, contributions and conclusion; the abstract and conclusion report the confirmed result with
  the gate failure beside it; the Discussion has a paragraph on test-time reasoning against orchestration; RQ4 says
  what KUU adds beyond the thinking judge. The claim is limited to M1's own planned arms, because the 12B M2's debate
  scored about as high on D1-test (MCC 0.571, inside the thinking range 0.513–0.601).

## 8. Deviations and reproducibility

Deviations: `docs/tracking/EXPERIMENT_DEVIATIONS.md` (X-01 … X-09) and `docs/tracking/DECISIONS.md` (D-01 … D-128).
Frozen configuration: `configs/local_models.FROZEN.json`; environment manifest: `env/environment_manifest.json`;
reproduction steps: `docs/REPRODUCIBILITY_GUIDE.md` and `docs/local_models/ZERO_COST_REPRODUCIBILITY_PLAN.md`; analysis
commands: `results/heldout/analysis_final/MANIFEST.json`. **TODO (authors):** public repository URL.
