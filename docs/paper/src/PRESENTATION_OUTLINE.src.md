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
throws away the few that reveal real bugs. Zhao et al. report that only {{cit:zhao lo}}–{{cit:zhao hi}}% of generated
tests are bug-revealing; our own records give {{zhao:subsets:all_D1:share_effective_pct@2}}%
{{zhao:subsets:all_D1:ci95_pct@ci2}}.
*Why it matters: a triage stage must find a few program faults among many wrong tests.*

**3. Gaps and questions.** G1 no accuracy measurement against buggy/fixed truth; G2 specification assumed, never
varied; G3 multi-agent gains without budget matching. RQ1 accuracy and lost bug-revealing tests; RQ2 specification
level S0/S1/S2; RQ3 debate vs self-consistency at equal budget.

**4. Method.** Figure: `paper/figures/fig_architecture_phase2.png`. Tests run on the buggy and the fixed version; the
label (PF = fails on buggy, passes on fixed) never passes through an LLM and joins only at evaluation.
*Stress: no human or LLM decides a label.*

**5. Arms at equal budget.** J1 one call; SC majority of 5; DEB two advocates over two rounds plus an adjudicator,
{{cost:arms:DEB:calls_per_instance@0}} calls; SC-T token-matched; baselines discard-all, keep-all, rule-based R0.
DEB consumed {{d1:DEB|S1:consumed_tokens_per_instance@0}} tokens per instance against SC's
{{d1:SC|S1:consumed_tokens_per_instance@0}}.

**6. Setup.** Defects4J frame reconstructed; held-out projects; local open-weight models frozen before any held-out call
(judge M1 Qwen3.5 9B, M2 Gemma 4 12B, generator Gemma 4 26B). {{sum:leakage_abort_exclusions:n_per_level:S1}} scored
instances from {{r3:D1:n_bugs}} bugs, {{sum:prevalence:PF}} of them PF.

**7. RQ1 — accuracy.** Figure: `fig_e1_prf_D1.pdf`. DEB F1 {{d1:DEB|S1:f1}} vs keep-all {{d1:KA:f1}}; MCC
{{d1:DEB|S1:mcc}} vs {{d1:KA:mcc}}. DEB rejects {{d1:DEB|S1:TN@1}} test faults per replicate that keep-all keeps.
*F1 alone flatters keep-all; MCC shows the signal.*

**8. Confirmatory tests.** Figure: `fig_confirmatory_D1.pdf`. No hypothesis survived Holm; DEB − SC ΔF1
{{conf:f1:H3a:delta}} {{conf:f1:H3a:ci95}}. Sensitivity: the design detects ΔF1 of about
{{mde:tests:H3a:mde_alpha_005@2}} for DEB vs SC — far larger than any observed difference.

**9. RQ2 — specification.** Figure: `fig_e2_spec_f1_D1.pdf`. Javadoc did not help and trended negative
(H2a ΔF1 {{conf:f1:H2a:delta}}, p_Holm {{conf:f1:H2a:p_holm}}); S0 was best for every arm.

**10. What carries the signal.** Figures: `fig_e3_pareto_D1.pdf`, `fig_e4_ablations_D1.pdf`. Without the failure
evidence, J1 and SC fall to chance (MCC {{d1:J1|S1|noF:mcc}}, {{d1:SC|S1|noF:mcc}}).
*The judge reads the failure message, not the benchmark.*

**11. Robustness.** M2 scored higher on every arm (DEB +{{r3:D1:m2_minus_m1:DEB:f1:delta@abs}}
{{r3:D1:m2_minus_m1:DEB:f1:ci95}}); seeded faults D2 keep DEB above chance (MCC {{d2:DEB|S1:mcc}}); the exploratory
35B judge (different runtime, D-78) reached DEB F1 {{e6a:summary:35B:DEB:f1}}.

**12. Third family, the vote and a frontier reference (E6b, E8, E9).** Figure: `fig_judges_votes_D1.png`. Ministral 3
14B: DEB above chance, not above SC. The three-family vote lost {{e8:summary:VOTE3|S1:pf_lost@0}} of
{{e6b:pf_prevalence:PF}} bug-revealing tests where SC lost {{e8:summary:SC|S1:pf_lost@0}}. Frontier reference (Claude
Sonnet 5.5, not a replication): DEB F1 {{e9:summary:DEB|S1|SON:f1}}, run-to-run range
{{e9:deb_run_to_run_spread:sonnet:f1:range}} vs M1's {{e9:deb_run_to_run_spread:m1:f1:range}}.
*Single-replicate DEB differences are within M1's own run-to-run noise (D-94).*

**13. KUU — keep unless unanimous (the method).** Discard only when three judge families agree it is a test fault.
Post hoc on D1; confirmed on D2: {{kuu2:summary:KUU|S1:pf_lost@0}} of {{kuu2:pf_prevalence:PF}} bug-revealing tests lost
vs debate's {{kuu2:summary:DEB|S1:pf_lost@0}}, F1 {{kuu2:summary:KUU|S1:f1}} vs keep-all's {{kuu2:summary:KA:f1}}
(p Holm {{kuu2:hypotheses:H10-1:p_holm}}).
*The practical message: keep by default, discard on cross-family agreement.*

**14. Practical takeaways (exploratory).** DEB beats keeping every failure only while a missed bug costs less than
{{xd:D1:DEB:breakeven_vs_KA@1}} false alarms. Selective DEB (τ = {{sel:arms:DEB:tau}}) discards
{{sel:arms:DEB:share_discarded@pct}} of failures and loses {{sel:arms:DEB:pf_lost@1}} of {{sel:arms:DEB:pf_in_set}}
bugs. Judges are overconfident (stated {{xd:D2:calibration:DEB:mean_confidence@2}} vs accuracy
{{xd:D2:calibration:DEB:accuracy@2}}).

**15. Limits, honesty and next steps.** Small sample; small local judges; Defects4J possibly memorised (D2 and the
evidence ablation argue against it, D3 not run); two-rater label audit pending, with a sealed blind LLM third rater
(D-84). Every deviation and harness fault is a dated D-entry (e.g. D-86, D-87, D-89). Next: a larger sample, a second generator (both E7a candidates failed the dev selection, C1
{{e7a:tried:0:C1@2}} and {{e7a:tried:1:C1@2}}, D-102) and an external benchmark newer than the judges' cutoffs (GitBug-Java's 2023 bugs are not, D-103).
*Close on the protocol: execution labels, frozen prompts, every number regenerable from the call log.*
