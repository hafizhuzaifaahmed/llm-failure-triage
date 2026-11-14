<!-- generated from docs/paper/src/PRESENTATION_OUTLINE.src.md by scripts/paper/build_numbers.py; every number is in docs/paper/NUMBERS_MAP.csv -->
# Presentation outline — 15 slides (Phase 3/4 defense)

> **Superseded (9 Nov 2026).** The defense deck is `paper/DEFENSE_DECK.pptx`, built by `scripts/paper/build_deck.py` from `docs/paper/src/DEFENSE_DECK.src.md`. This outline is kept for history and is no longer updated.

Rendered by `scripts/paper/build_numbers.py`; every number resolves from `docs/paper/NUMBERS_MAP.csv`. Figures are the
committed ones in `paper/figures/` (PDF for print, PNG where noted for slides). Speaker notes in italics. Keep one
message per slide; the backup questions are in `docs/paper/DEFENSE_QA.md`.

---

**1. Title.** LLM-Based Failure Triage for Generated Unit Tests — Hafiz Huzaifa Ahmed, Saad Ilyas (FAST-NUCES
Islamabad). Advanced AI, Phase 3/4.
*One line: we score whether an LLM can tell a bug-revealing failure from a wrong test, against execution ground truth.*

**2. The problem.** Generated tests fail often, and most generators repair or discard every failing test — which also
throws away the few that reveal real bugs. Zhao et al. report that only 2.09–4.54% of generated
tests are bug-revealing; our own records give 1.94%
[1.07, 3.00].
*Why it matters: a triage stage must find a few program faults among many wrong tests.*

**3. Gaps and questions.** G1 no accuracy measurement against buggy/fixed truth; G2 specification assumed, never
varied; G3 multi-agent gains without budget matching. RQ1 accuracy and lost bug-revealing tests; RQ2 specification
level S0/S1/S2; RQ3 debate vs self-consistency at equal budget.

**4. Method.** Figure: `paper/figures/fig_architecture_phase2.png`. Tests run on the buggy and the fixed version; the
label (PF = fails on buggy, passes on fixed) never passes through an LLM and joins only at evaluation.
*Stress: no human or LLM decides a label.*

**5. Arms at equal budget.** J1 one call; SC majority of 5; DEB two advocates over two rounds plus an adjudicator,
5 calls; SC-T token-matched; baselines discard-all, keep-all, rule-based R0.
DEB consumed 9,188 tokens per instance against SC's
9,551.

**6. Setup.** Defects4J frame reconstructed; held-out projects; local open-weight models frozen before any held-out call
(judge M1 Qwen3.5 9B, M2 Gemma 4 12B, generator Gemma 4 26B). 177 scored
instances from 60 bugs, 60 of them PF.

**7. RQ1 — accuracy.** Figure: `fig_e1_prf_D1.pdf`. DEB F1 0.511 vs keep-all 0.506; MCC
0.267 vs 0. DEB rejects 89.3 test faults per replicate that keep-all keeps.
*F1 alone flatters keep-all; MCC shows the signal.*

**8. Confirmatory tests.** Figure: `fig_confirmatory_D1.pdf`. No hypothesis survived Holm; DEB − SC ΔF1
+0.074 [−0.031, 0.201]. Sensitivity: the design detects ΔF1 of about
0.17 for DEB vs SC — far larger than any observed difference.

**9. RQ2 — specification.** Figure: `fig_e2_spec_f1_D1.pdf`. Javadoc did not help and trended negative
(H2a ΔF1 −0.050, p_Holm 0.116); S0 was best for every arm.

**10. What carries the signal.** Figures: `fig_e3_pareto_D1.pdf`, `fig_e4_ablations_D1.pdf`. Without the failure
evidence, J1 and SC fall to chance (MCC 0.031, −0.004).
*The judge reads the failure message, not the benchmark.*

**11. Robustness.** M2 scored higher on every arm (DEB +0.217
[0.109, 0.314]); seeded faults D2 keep DEB above chance (MCC 0.392); the exploratory
35B judge (different runtime, D-78) reached DEB F1 0.644.

**12. Third family, the vote and a frontier reference (E6b, E8, E9).** Figure: `fig_judges_votes_D1.png`. Ministral 3
14B: DEB above chance, not above SC. The three-family vote lost 6 of
60 bug-revealing tests where SC lost 36. Frontier reference (Claude
Sonnet 5.5, not a replication): DEB F1 0.823, run-to-run range
0.024 vs M1's 0.221.
*Single-replicate DEB differences are within M1's own run-to-run noise (D-94).*

**13. KUU — keep unless unanimous (the method).** Discard only when three judge families agree it is a test fault.
Post hoc on D1; confirmed on D2: 4 of 154 bug-revealing tests lost
vs debate's 56, F1 0.771 vs keep-all's 0.726
(p Holm 0.019).
*The practical message: keep by default, discard on cross-family agreement.*

**14. Practical takeaways (exploratory).** DEB beats keeping every failure only while a missed bug costs less than
3.0 false alarms. Selective DEB (τ = 100) discards
15.1% of failures and loses 3.3 of 60
bugs. Judges are overconfident (stated 0.95 vs accuracy
0.67).

**15. Limits, honesty and next steps.** Small sample; small local judges; Defects4J possibly memorised (D2 and the
evidence ablation argue against it, D3 not run); two-rater label audit pending, with a sealed blind LLM third rater
(D-84). Every deviation and harness fault is a dated D-entry (e.g. D-86, D-87, D-89). Next: a larger sample, a second generator (both E7a candidates failed the dev selection, C1
0.38 and 0.17, D-102) and an external benchmark newer than the judges' cutoffs (GitBug-Java's 2023 bugs are not, D-103).
*Close on the protocol: execution labels, frozen prompts, every number regenerable from the call log.*
