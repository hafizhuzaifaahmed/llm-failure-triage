# Experiment and result map

Status: reconstructed from the paper PDF at `5138443`, the decision log and the result directories. Status codes follow
the paper's Table H1: **C** confirmatory family of the approved design; **F** hypotheses fixed in the decision log before
their calls (internal provenance, not externally registered); **P** post hoc; **X** exploratory.

## 1. Research questions and designs

| RQ | Question | Experiment | Unit | Data | Status |
|---|---|---|---|---|---|
| RQ1 | Accuracy of LLM triage against buggy/fixed labels; bug-revealing tests kept | E1: R0, J1, SC, SC-T, DEB at S1, 3 replicates | instance, bootstrap clustered by bug | D1-test, 177 scored | C (H1) |
| RQ2 | Effect of specification level S0/S1/S2 | E2 | same | D1-test | C (H2a, H2b) |
| RQ3 | Debate vs self-consistency at equal allocated budget | E3 | same | D1-test | C (H3a, H3b) |
| — | Ablations A1–A5 | E4, one replicate | same | D1-test | X |
| — | Robustness: D2, second judge M2, 35B, third family, frontier | E5–E9b | same | D1-test, D2 | F / X |
| RQ4 | Keep-unless-unanimous (KUU), cascade, KUU-NG | D-95, D-105, D-109 | same; bugs lost also reported | D2 (F), D1-test (P) | F on D2 |
| — | Thinking-enabled M1 judge | D-126, D-130, D-131 | same | D1-test (X), D2 (F) | F on D2 |
| — | Rates, ranking, learned baselines, k-of-n, risk threshold, cross-generation, sample size | D-112 to D-122 | same | logged decisions only | P / X |
| — | Fully local cascade | D-132 | same | logged decisions | P |

## 2. Headline claims and their provenance

| # | Claim (as printed) | Value | Raw source | Script | Decision | Where |
|---|---|---|---|---|---|---|
| 1 | Best planned arm at S1 barely beats keep-all on F1 | DEB F1 0.511 vs KA 0.506; MCC 0.267 [0.126, 0.405] | `results/runs_local/LOCAL_HO_E1E3_M1` | `scripts/analyze.py` → `results/heldout/analysis_final/D1_M1` | D-57, D-75 | Abstract, Table 4; deck (6 hits of 0.511) |
| 2 | No confirmatory hypothesis survives Holm | H1 p_Holm 0.233; H3a 0.532; H2a 0.116 | `…/D1_M1/tables/confirmatory.json` | `analyze.py` | D-23 | §5.4, Table B2 |
| 3 | Single-judge arms lose about half the PF tests | DEB loses 30 of 60, SC 36, R0 45 | same | same | — | Table 4 |
| 4 | Failure evidence carries the signal (A4) | ΔF1 −0.282 SC, −0.163 J1; MCC to chance | `LOCAL_HO_E4_M1` | `analyze.py` | D-59 | §7, Table B3 (X) |
| 5 | Javadoc: no detectable benefit | H2a ΔF1 −0.050 [−0.091, −0.006], p_Holm 0.116 | E1E3 run | `analyze.py` | — | §5.2 |
| 6 | KUU on D2 | loses 4 of 154 PF vs DEB's 56; F1 0.771 vs KA 0.726; MCC 0.356 < DEB 0.392 | `results/runs_local/LOCAL_HO_KUU_D2_*` | `scripts/analysis/kuu_analysis.py` → `results/kuu/analysis` | D-95 | §5.6, Table E1 |
| 7 | KUU-NG | loses 1 PF test, 0 bugs; discards 7% | `LOCAL_HO_KUUNG_*` | `kuung_analysis.py` → `results/kuung/analysis` | D-109 | §5.6, Table E3 |
| 8 | Cascade to Sonnet DEB | MCC 0.666 vs KUU 0.356; 50% escalated; F1 0.863 vs Sonnet DEB 0.910, non-inferiority not shown | `results/runs_frontier/E9B_SONNET55_D2` | `scripts/analysis/cascade.py` → `results/cascade/analysis` | D-105 | §5.6 |
| 9 | Frontier reference | Sonnet DEB D1 F1 0.823, BA 0.864; D2 BA 0.893; AUROC 0.943 / 0.970 | `results/runs_frontier/E9_*`, `E9B_*` | `e9_analysis.py`, `e9b_analysis.py`, `revision_ranking.py` | D-92 to D-104 | App. D, Table G1, G2 |
| 10 | Thinking-enabled M1 J1 | D2 MCC 0.659 vs DEB 0.392, 8 vs 56 PF lost; D1 BA 0.771–0.817; fails gate G-a and G-d | `results/revision/runs/REV_THINK_*` | `scripts/analysis/revision_think.py` → `think_followup.json`, `think_gate.json` | D-130, D-131 | Abstract, Table G8 |
| 11 | Rates on a common scale | KUU D2 TPR 0.974 / TNR 0.267 / BA 0.621; DEB BA 0.697; cascade 0.826 | logged decisions | `revision_rates.py` → `wp11_rates.json` | D-113 | Table G1, Fig. 2 |
| 12 | Ranking | KUU-panel AUROC 0.733 (D1) / 0.756 (D2); DEB 0.678 / 0.760 | logged | `revision_ranking.py` → `wp13_ranking.json` | D-114 | Table G2 |
| 13 | Learned baselines | failure-features LR AUROC 0.554 (LOPO); votes-only BA 0.698 | logged | `revision_learned.py` → `wp14_learned.json` | D-115 | Table G3 |
| 14 | Cross-generation agreement | AUROC 0.513 [0.418, 0.617] on D1, 0.708 on D2 | execution records, B side only | `revision_cross_gen.py` → `wp17_cross_gen.json` | D-118 | Table G5 |
| 15 | Risk-targeted threshold | D2 PF-loss 0.026 (KUU panel) / 0.065 (KUU-NG panel); stated to be a heuristic, not a guarantee | logged | `revision_risk.py` → `wp16_risk.json` | D-117 | Table G5 |
| 16 | Fully local cascade | D2 BA 0.765, MCC 0.593, 6 PF tests and 0 bugs lost | logged | `revision_local_cascade.py` → `local_cascade.json` | D-132 | Table G9 |
| 17 | Label audit | 71 dev items, human–human κ 0.936; consensus matches execution on 97.2%; both mismatches are execution-TF judged PF | `docs/audits/label_audit_rater_*.csv` | `scripts/analysis/label_audit.py` → `results/audit` | D-82, D-108 | §8.1 |
| 18 | Power | MDE at 80% power ≈ 0.17 F1 for DEB vs SC; ≈ 257 bugs for an MDE of 0.08 | — | `mde_sensitivity.py`, `revision_sample_size.py` | D-119 | Table C1, G5 |

## 3. Deck against paper and repository

- All 65 slides were extracted with speaker notes (`python-pptx`). Slides 1–23 tell the main story; 24–65 are backup,
  including Q&A slides 30–38.
- Spot-checked values appear in the deck with the paper's value: 0.511, 0.267, 0.659, 0.392, "4 of 154", 0.666, 0.356,
  0.823, 0.771, 0.826, 0.765, 257. None was found with a different value.
- The deck does not print the cascade's F1 (0.863) or Sonnet DEB's D2 F1 (0.910); the paper does. This is an omission,
  not a conflict.
- The deck is a presentation-level map. The paper and `NUMBERS_MAP.csv` are the authority.

## 4. Things a reader can misread

| Issue | Detail |
|---|---|
| "60" | D1-test has 60 PF *tests* in **22 bugs** (label store). The sample-size sentence ("about 257 bugs rather than 60", from `results/revision/wp18_sample_size.json`) uses 60 as the current number of bug clusters; the label store shows 76 bugs with any instance and 22 with a PF test, and I could not reproduce 60 as a bug count from it. Flagged for the authors; whichever count is meant, the number of bugs that can lose a bug-revealing test on D1-test is 22. |
| D1 and D2 F1 | Not comparable (PF prevalence 0.339 vs 0.570). Only TPR, TNR, BA and MCC travel between them. |
| KUU "method" | Defined after the D1 vote was seen; D2 is its only test fixed in advance. On D2 its MCC is below debate's. |
| "Confirmed" for the thinking judge | Confirmed against debate on seeded faults; it failed the gate it was held to. |
| D2 as contamination control | Removes recall of the fix, not knowledge of the original code; single-line mutants may be recognisable. |
| Every local judge | Fails development gate G-d, so RQ2 and RQ3 describe sub-gate judges. |
