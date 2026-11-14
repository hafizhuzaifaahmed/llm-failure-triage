# Mock review, round 2 (raw)

This review was written on 9 Nov 2026 by a fresh subagent with no repository access and no conversation history. It
read only the paper PDF built at commit cc238e0, after the cascade (D-105) and E9b were added. Page numbers are the PDF's
printed numbers. `MOCK_REVIEW.md` holds the triage.

## Reviewer 1: research methods

| # | Objection | Pages | Damage |
|---|---|---|---|
| R1-1 | **The primary judge failed its own development gate, and RQ2/RQ3 still rest on it.** M1's one-shot F1 was 0.350 against R0's 0.642. Its best arm only ties keep-all, while stronger judges change the picture (M2 DEB MCC 0.571, Sonnet 0.734). *Fix:* narrow RQ2/RQ3 to "a sub-gate small local judge"; re-run E2/E3 on M2 as a pre-declared second primary; show that the fallback ladder was itself written in advance. | 6–8, 10, 13, 16 | HIGH |
| R1-2 | **The pre-registration cannot be audited, and the decision log is a garden of forking paths.** There are more than 100 decision entries; the log is private, not a public timestamped registry; red TODOs remain (Phase-2 feedback, DOI, repository URL, audit). *Fix:* remove the TODOs; deposit the protocol, log and call logs with a DOI and commit timestamps; add a planned-vs-executed table that classifies each deviation by when it happened. | 5, 7, 9, 13, 14 | HIGH |
| R1-3 | **KUU's success was close to guaranteed, and it was never tested against the right baseline.** A unanimity rule loses few tests by construction; on D2 its MCC is below M1 DEB's. The fair comparator is a single judge at a matched discard rate; cascades with deferral and selective classification are established and not cited. *Fix:* recast KUU as an instantiation of those patterns, cite the prior work, and compare at matched discard rate. | 2, 5–6, 9, 17, 18 | HIGH |
| R1-4 | **A single frontier call per instance dominates escalation on MCC and cost.** Sonnet J1 on every instance reaches MCC 0.687 with about 270 calls; the cascade reaches 0.666 with 670. "Half the cost" is measured against the most expensive reference, and the cascade loses more tests than Sonnet DEB. *Fix:* report the full cost–quality frontier and restate the claim. | 1, 9–10, 18 | HIGH |
| R1-5 | **The error-diversity explanation is confounded and stated causally.** "Cross-family" pairs are different models of different sizes and accuracies; "within-family" is resampling one model; family was never isolated, and the D1 criterion failed. *Fix:* add a same-family multi-model triple, use accuracy-matched controls, and change "because" to "consistent with". | 1, 9, 19 | MEDIUM |

## Reviewer 2: software testing

| # | Objection | Pages | Damage |
|---|---|---|---|
| R2-1 | **The buggy/fixed differential is unvalidated ground truth, and the audit has not been done.** A pass on P_F may be incidental; an identical double failure may expose a different latent bug; AMB cases are excluded; κ is a TODO. *Fix:* complete the two-rater audit with per-direction disagreement, re-score under audited labels, and describe the AMB pool. | 3–4, 13, 14 | HIGH |
| R2-2 | **The task does not resemble deployment, especially in prevalence.** Every focal method is buggy; prevalence is 0.339 by design and 0.570 on D2; KUU and the cascade are evaluated only on D2. *Fix:* report precision, MCC and false-alarm burden at the frame's natural prevalence and at an assumed 2–5%; add failures from non-buggy methods. | 2, 6, 8–10 | HIGH |
| R2-3 | **D2 seeded faults do not control contamination, and D1 is contaminated for the frontier judge.** D2 mutates the most memorised code; mutants are small and local; the guard caught the mutated line in 5 of 8 aborts; D3 was dropped for a weak reason; A4 does not argue against memorisation. *Fix:* run D3 or another post-cutoff set, report the mutant operator mix, test memorisation directly, and present D2 as a robustness set. | 6, 9, 12, 13, 19 | HIGH |
| R2-4 | **One small generator, a strawman rule baseline, and generator-family overlap.** The TF population is one model's error profile; M2 shares the generator's family; R0 is not the triage of [10, 14] it claims to stand for. *Fix:* add a second generator, characterise TF failure types, and strengthen R0 or stop calling it a re-implementation. | 4, 6, 9–10, 16 | MEDIUM |
| R2-5 | **Test-level "lost" counts are not what a tester cares about.** A bug is lost only if all its bug-revealing tests are discarded. *Fix:* report bugs retained for every arm, KUU and the cascade, and recompute the break-even per bug. | 1, 7–9, 17 | MEDIUM |

## Reviewer 3: statistics

| # | Objection | Pages | Damage |
|---|---|---|---|
| R3-1 | **The intervals leave out decoding variance, which is larger than every effect tested.** The bootstrap holds the replicate mean fixed; DEB's replicate range is 0.221; D2 and frontier results rest on one replicate yet report p_Holm < 0.001. *Fix:* use a two-stage bootstrap or a replicate random effect, add replicates, or use greedy decoding. | 7, 9–10, 13, 18–19 | HIGH |
| R3-2 | **The metric was switched.** F1 was the registered primary; MCC, added later, carries the abstract's positive messages; the non-inferiority test runs on F1 with an unjustified −0.05 margin. *Fix:* one primary metric per hypothesis as registered; justify the margin; show non-inferiority on MCC too. | 1, 3, 7, 9–10, 14 | HIGH |
| R3-3 | **The confirmatory family was underpowered, so "inconclusive" was the expected result.** There is no a priori power calculation; the Discussion still draws directional conclusions; a 6-project Wilcoxon cannot go below p = 0.031; McNemar on replicate-averaged labels is undefined. *Fix:* state the a priori MDE or admit none; remove directional readings; explain or drop McNemar; give the n needed. | 7–9, 12, 17 | MEDIUM–HIGH |
| R3-4 | **The bootstrap does not reproduce the sampling design.** Project clustering and stratification are ignored; P_adj has no interval; leave-one-project-out is promised but not shown; cross-dataset MCC comparisons are not like-for-like. *Fix:* a stratified project→bug bootstrap with weights, CIs for P_adj, LOPO results, prevalence-standardised comparisons. | 6–8, 13, 16 | MEDIUM |
| R3-5 | **Many Holm families and trivial nulls inflate the "supported" count, and ratio statistics are unstable.** Error is not controlled across the paper; H6-2, H9-2 and H11-1 test only MCC > 0; the lift ratio has an unstable, skewed interval. *Fix:* one paper-level family or a gatekeeping hierarchy; relabel MCC > 0 tests as sanity checks; report co-error on a difference scale with BCa; count all tests. | 7, 9, 18–19 | MEDIUM |
