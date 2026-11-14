<!-- generated from docs/paper/src/REVISION_REPORT_D81.src.md by scripts/paper/build_numbers.py; every number is in docs/paper/NUMBERS_MAP.csv -->
# Revision report — D-81 corrections (2026-11-03)

Rendered by `scripts/paper/build_numbers.py`; every number resolves from `docs/paper/NUMBERS_MAP.csv`. Changed text is LaTeX source with values substituted. No model call; no data, run, configuration or result changed.

| # | Correction | Done |
|---|---|---|
| 1 | Title set; running title kept | yes |
| 2 | A4 overclaim: J1 and SC fell to chance, DEB's F1 dropped but not significantly (abstract qualifier added) | yes, in Conclusion, Discussion, Failure cases, Ablation, and the Phase 3 report |
| 3 | Keep-all margin replaced by the two values (DEB 0.511 vs keep-all 0.506) in abstract and Conclusion; derived margin dropped from the paper | yes |
| 4 | MDE range replaced by a single value (about 0.06) | yes |
| 5 | Conclusion: "between architectures (MDE 0.17 for DEB vs SC)" | yes |
| 6 | Tables B2 and B3 pinned below the Appendix B heading (non-float, same numbering and caption style; `[H]` from the float package clashes with the template) | yes |

Checks: main text through the Conclusion ends on page 13 (three short trims, listed below, keep it there); abstract 250 words; numbers-map check run (all keys resolved, 24/24 published figures found in their sources). `REVISION_REPORT_D80.md` is marked as superseded in part.

## Before / after

**1 Title** — `paper/PHASE4_RESEARCH_PAPER.tex`

- before: \title[LLM Failure Triage for Generated Unit Tests]{LLM-Based Failure Triage for Generated Unit Tests: Failure Evidence, Specification Availability and Multi-Agent Debate under an Equal Budget with Local Open-Weight Judges}
- after: \title[LLM Failure Triage for Generated Unit Tests]{Program Fault or Test Fault? Evaluating LLM Triage of Generated Unit Tests Against Buggy/Fixed Ground Truth}

**2+3 Abstract** — `paper/PHASE4_RESEARCH_PAPER.tex`

- before: No LLM arm exceeded keep-all's F1 (0.506) by more than 0.004, and MCC places the arms above chance but weak
- after: The best arm, DEB, reached F1 0.511 against keep-all's 0.506, and MCC places the arms above chance but weak

**2 Abstract** — `paper/PHASE4_RESEARCH_PAPER.tex`

- before: Removing the failure evidence lowered F1 for every arm, by 0.122 to 0.282, while
- after: Removing the failure evidence lowered F1 for every arm (significant for J1 and SC, unadjusted), by 0.122 to 0.282, while

**2 Ablation (A4)** — `paper/PHASE4_RESEARCH_PAPER.tex`

- before: and MCC falls to −0.004 (SC) and 0.031 (J1), i.e.\ chance.
- after: and MCC falls to −0.004 (SC) and 0.031 (J1), i.e.\ chance; DEB's F1 also dropped (−0.122, 95\% CI [−0.282, 0.034], $p$ 0.136), though not significantly, and its MCC stayed at 0.127.

**2 Discussion, Failure evidence matters** — `paper/PHASE4_RESEARCH_PAPER.tex`

- before: The clearest result is A4: without the failure section every arm is at chance.
- after: The clearest result is A4: without the failure section, J1 and SC fell to chance and DEB's F1 also dropped, though not significantly.

**2 Discussion, Failure cases (K1 sentence)** — `paper/PHASE4_RESEARCH_PAPER.tex`

- before: the evidence whose removal (A4) left every arm at chance.
- after: the evidence without which (A4) J1 and SC fell to chance and DEB's F1 also dropped, though not significantly.

**3+5 Conclusion** — `paper/PHASE4_RESEARCH_PAPER.tex`

- before: No LLM arm exceeded keep-all's F1 by more than 0.004, MCC placed the arms above chance but low, and no confirmatory hypothesis was supported after correction; the post hoc sensitivity analysis shows that the sample could detect only large differences between arms.
- after: The best arm, DEB, reached F1 0.511 against keep-all's 0.506, MCC placed the arms above chance but low, and no confirmatory hypothesis was supported after correction; the post hoc sensitivity analysis shows that the sample could detect only large differences between architectures (MDE 0.17 for DEB vs SC).

**2 Conclusion** — `paper/PHASE4_RESEARCH_PAPER.tex`

- before: The component that mattered was the failure evidence: without it, every arm fell to chance.
- after: The component that mattered was the failure evidence: without it, J1 and SC fell to chance and DEB's F1 also dropped, though not significantly.

**4 Threats, Statistical conclusion (MDE)** — `paper/PHASE4_RESEARCH_PAPER.tex`

- before: differences of about 0.06--0.06 for the specification contrasts
- after: differences of about 0.06 for the specification contrasts

**6 Appendix B tables** — `paper/PHASE4_RESEARCH_PAPER.tex`

- before: Tables B2 and B3 placed with [h] (floated above the Appendix B heading)
- after: Tables B2 and B3 placed with [H] (float package), fixed below the heading

**2 Phase 3 report, ablations** — `docs/phase3/PHASE3_REPORT.src.md`

- before: Removing the failure evidence is the only change with a clear effect; without it every arm is at chance (MCC near 0).
- after: Removing the failure evidence is the only change with a clear effect: without it, J1 and SC fell to chance (MCC 0.031 and −0.004) and DEB's F1 also dropped (−0.122, p 0.136), though not significantly.

**page budget: Discussion, Development gate** — `paper/PHASE4_RESEARCH_PAPER.tex`

- before: Reporting the failed gate instead of selecting further kept that noise out of the held-out design.
- after: (sentence removed)

**page budget: Conclusion, future work** — `paper/PHASE4_RESEARCH_PAPER.tex`

- before: Future work should repeat the confirmatory tests with a stronger judge from another family than the generator's on a larger held-out sample, add an external benchmark (D3), and study cost-sensitive vote thresholds.
- after: Future work should repeat the confirmatory tests with a stronger judge from another family on a larger sample, add an external benchmark (D3) and study cost-sensitive vote thresholds.

**page budget: Discussion, Judge size and family** — `paper/PHASE4_RESEARCH_PAPER.tex`

- before: M2 improved F1 for every arm on both datasets, and the exploratory MoE judge also scored above M1. Size, family and runtime differ together, and M2 shares the generator's family, so the gain cannot be assigned to size; the 9B judge is, however, the bottleneck of the confirmatory study.
- after: M2 improved F1 for every arm on both datasets and the exploratory 35B judge also scored above M1, but size, family and runtime differ together and M2 shares the generator's family, so the gain cannot be assigned to size.

