# Mock review, round 1 (raw)

This is the raw output of an independent reviewer on 9 Nov 2026. The reviewer was a fresh subagent with no repository
access and no conversation history. It reviewed only the paper PDF built at commit ea79269, which was **before** the
cascade (D-105) was added. Page numbers are the PDF's printed numbers.

The triage of these objections is in `MOCK_REVIEW.md`.

## Reviewer 1: Research methods

| # | Objection | Pages | Damage |
|---|---|---|---|
| R1-1 | **The primary judge failed its own development gate and was kept.** M1's development pilot had J1 F1 0.350 against R0's 0.642 and a negative MCC. The rationale ("project composition") came after the fact. Every RQ2 and RQ3 null can be read as "this judge was too weak". *Fix:* scope RQ2/RQ3 to "a sub-gate 9B judge" and bring the M2, 35B and Sonnet results forward as the test. | 6, 14, 16 | HIGH |
| R1-2 | **The abstract and conclusion claim more than the confirmatory evidence supports.** "The failure evidence, not the architecture, carries most of the signal" rests on the exploratory, single-replicate A4 ablation and on a possibly contaminated frontier judge. "Javadoc did not help" is a non-significant result with failed equivalence. Unlike results are mixed in one sentence. *Fix:* separate confirmatory, exploratory and post hoc results, and say "no detectable effect; equivalence not shown". | 1, 2, 11–13 | HIGH |
| R1-3 | **KUU is a post hoc rule confirmed against a comparator it beats by construction.** H10-2 (fewer lost tests than debate) is nearly tautological for a unanimity rule; H10-1 is a thin margin (+0.045, lower bound 0.005, one replicate); MCC is below DEB's. It reads as a point on the precision/recall trade-off, not a better principle. *Fix:* compare with other conservative operating points (SC v ≥ 2/5, DEB τ = 100, VOTE5) and report break-even cost ratios. | 1, 2, 9, 13, 17 | HIGH |
| R1-4 | **The manuscript is unfinished, and the pre-registration cannot be checked.** It has red TODOs (Phase-2 feedback, URL/DOI, κ audit, declarations) and no registry, timestamp or hash a panel could inspect. *Fix:* remove every TODO, publish the DOI, give a dated hash-stamped pre-registration, and state the Phase-2 feedback. | 5, 7, 13, 14 | HIGH |
| R1-5 | **There are many deviations and adaptive scope changes.** About a hundred decision entries, replaced models, a reconstructed frame, scope added by time rules, mid-run fixes and 17 unplanned calls. External validity is narrow. *Fix:* add a deviation table classified by whether it could affect a confirmatory result and when it happened relative to the first held-out data; narrow the claims. | 6, 13–16, 18 | MEDIUM |

## Reviewer 2: Software testing

| # | Objection | Pages | Damage |
|---|---|---|---|
| R2-1 | **The buggy/fixed labels do not cleanly separate program fault from test fault, and the audit is missing.** A double failure may expose a second, unfixed bug; a pass on P_F may come from an incidental patch change. κ is still a TODO. *Fix:* complete the audit on held-out instances, check TF against later fixed revisions, and bound how much label noise could move F1 and MCC. | 3, 4, 13, 15 | HIGH |
| R2-2 | **The baselines are weak or loose analogues.** R0 is a single unstable rule; no established non-LLM triage method is implemented; "re-implementations" are inspired-by analogues; +92.3% over R0 inflates a non-significant difference. *Fix:* add a learned baseline, drop relative percentages, and rename the base-paper rows "inspired by". | 4, 10–12, 16 | MEDIUM |
| R2-3 | **D2 seeded faults are not a clean contamination control.** One-line mutants contradict their documentation more blatantly than real faults do; the guard caught the mutated line in 5 of 8 aborts; a model that memorised the original source can spot a mutant. E9b's "no model can have seen" premise is therefore wrong. *Fix:* describe and stratify by operator; use post-cutoff bugs for a real contamination control. | 6, 9, 13, 18 | MEDIUM–HIGH |
| R2-4 | **The triage population is filtered and enriched until it no longer looks like the real task.** Only deterministic, single-signature failures are kept; the sample is enriched to 1 PF : 2 TF while the natural yield is about 5%; all PF instances come from one generator. *Fix:* report results at natural prevalence and exclusion counts; restrict the claim to deterministic single-signature failures. | 4, 6–8 | MEDIUM |
| R2-5 | **The Javadoc result has a mechanical alternative explanation.** Length caps could truncate or dilute the failure section; the Javadoc of P_B may document the buggy behaviour. *Fix:* report truncation per level, run a length-matched control, and stratify H2a by whether the Javadoc describes the bug. | 3–5, 7, 12, 15 | MEDIUM |

## Reviewer 3: Statistics

| # | Objection | Pages | Damage |
|---|---|---|---|
| R3-1 | **The study was underpowered from the start, and its nulls are read as negatives.** MDEs are 0.27 (H1), 0.165 (H3a) and about 0.06 (specification); the ±0.05 equivalence margin could never be met. *Fix:* rephrase every null as "inconclusive; effects smaller than MDE X cannot be excluded", move Table C1 forward, and state the sample needed. | 7, 8, 13, 16 | HIGH |
| R3-2 | **F1 is the primary metric under a prevalence set by design.** Keep-all reaches 0.506; the IPW weights are used for precision only; D2 F1 is not comparable; KUU was confirmed on F1. *Fix:* expected-cost or decision-curve analysis at natural prevalence; re-run the confirmatory family on MCC as a sensitivity analysis. | 3, 6–10, 17 | HIGH |
| R3-3 | **The CIs ignore decoding (replicate) variance.** DEB's replicate range (0.221) exceeds every confirmatory ΔF1; the bootstrap resamples bugs only; single-replicate results carry unestimated noise. *Fix:* use a two-level bootstrap (bugs × replicates) or a replicate random effect, and treat within-noise comparisons as uninformative. | 6, 7, 13, 17 | HIGH |
| R3-4 | **The multiplicity structure is fragmented, and some tests are trivial.** There are many small Holm families; tests against zero (H6-2, H9-2) and H10-2 carry "p_Holm < 0.001" in the same notation as the confirmatory tests; the bootstrap p construction is not stated. *Fix:* list every family with its α and registration date, label the H10 tests, and state the p construction. | 7, 9, 17, 18 | MEDIUM |
| R3-5 | **There are too few independent units.** About 60 uneven bugs (Chart has 20 PF); the percentile intervals may under-cover; a 6-project Wilcoxon can never go below p = 0.031; the McNemar inputs are unclear. *Fix:* check coverage by simulation or use BCa; demote the Wilcoxon; state the McNemar construction; run leave-one-bug-out for Chart. | 7, 14, 16 | MEDIUM |
