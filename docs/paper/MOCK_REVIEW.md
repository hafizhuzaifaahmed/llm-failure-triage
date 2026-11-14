# Mock review and triage (queue item 7)

Two independent reviewers, each a fresh subagent with no repository access and no history, read only the paper PDF.
Each played three senior roles: research methods, software testing and statistics.

- **Round 1** (`MOCK_REVIEW_round1_raw.md`): the PDF at ea79269, before the cascade.
- **Round 2** (`MOCK_REVIEW_round2_raw.md`): the PDF at cc238e0, with the cascade and E9b.

Every objection is triaged below. Each gets one or more of:
- **answered:** the paper already deals with it; the entry says where;
- **fixed now:** fixed by wording or a zero-call analysis, under D-106 when it is an analysis;
- **limitation:** a genuine limitation; the entry says where Threats and DEFENSE_QA state it;
- **authors:** needs the authors.

The D-106 analyses were pre-registered (6f5fa1a) before they were computed. Their results are in Appendix F of the paper
and in `results/heldout/analysis_final/D1_M1/tables/review_sensitivity.json`.

## The objections most likely to matter in the room

| # | Objection (round) | Triage | What now answers it |
|---|---|---|---|
| 1 | **M1 failed its own development gate, so RQ2/RQ3 describe a weak judge** (R1-1 both rounds) | fixed now + limitation | The Threats Deviations sentence now says that RQ2 and RQ3 describe a judge below its own gate, which is why M2, the 35B and the frontier judge are reported beside it. Appendix C ("Development gate versus held-out result") explains the decision to keep M1 (D-52). DEFENSE_QA 1 and 13. **Limitation:** E2/E3 were not re-run confirmatorily on M2; that needs a new pre-registered study. |
| 2 | **TODOs and an unauditable pre-registration** (R1-4 round 1, R1-2 round 2) | authors + fixed at release | The red TODOs are the authors' items: instructor feedback, declarations, URL, DOI, κ. Release v1.0 makes the decision log, every D-entry's file hashes and the git history public. Each D-entry names the commit it precedes (e.g. D-105 at 7191845 before E9b's first batch). Appendix A lists every deviation. |
| 3 | **KUU's success is near-guaranteed by its operating point; no matched baseline; not novel** (R1-3 both rounds) | fixed now | (a) D-106(c): at a similar discard rate, M1's debate at confidence 100 loses 6 bug-revealing tests (14% discarded) against KUU's 4 (13%). The paper now says KUU's advantage at its operating point is small and that KUU alone is a conservative operating point, not a better classifier. (b) The method now cites the cascade-with-deferral and selective-prediction patterns it applies (FrugalGPT; Geifman and El-Yaniv) and positions itself as their instance for triage. DEFENSE_QA 22 and 24. |
| 4 | **Sonnet J1 on every instance dominates the cascade on MCC per dollar** (R1-4 round 2) | fixed now | D-106(d) shows the full D2 frontier. Sonnet J1 everywhere: US$ 1.18, MCC 0.687, 7 bugs uncovered. Cascade to DEB: US$ 3.22, MCC 0.666, 2 bugs uncovered. The Results now say Sonnet J1 is cheaper at a similar MCC but leaves more bugs uncovered, and the cost claim is "half the cost of Sonnet DEB", not cost-dominance. DEFENSE_QA 25. |
| 5 | **Labels unaudited** (R2-1 both rounds) | answered (D-108) | The blind two-rater audit is scored: human–human κ 0.936 (bug-level CI [0.638, 1.0]); the consensus matches the execution label on 97.2% of 71 items; both mismatches are execution TF judged PF. The LLM rater agrees with the consensus at κ 0.903 (secondary). Threats (Construct) and DEFENSE_QA 4 report it. **Remaining limitation:** the audit sample is from the development split. |
| 6 | **Decoding variance is missing from the intervals** (R3-3 round 1, R3-1 round 2) | fixed now + limitation | D-106(b), a two-level bootstrap over bugs and replicates, widens the confirmatory intervals by 1.04–1.62×. No Holm verdict changes. H2a's unadjusted interval now includes zero, and the Discussion now says so. Threats and DEFENSE_QA 19 report it. **Limitation:** the D2 and frontier results have one replicate (justified for Sonnet by its 0.024 range, D-94/D-104); stated in Threats. |
| 7 | **Metric switching: F1 registered, MCC in the headlines; NI margin unjustified** (R3-2 both rounds) | answered + fixed now | MCC was added beside F1 (D-54, D-74) before any held-out call; H1–H3b stay on F1 as registered. D-106(a) re-runs the five on MCC: no test survives Holm, the same verdict. The ±0.05 margin is the study's pre-registered SESOI for equivalence, reused for H12-2 in D-105 before any E9b call. The cascade − Sonnet DEB MCC difference is reported in `cascade_d2.json`. |
| 8 | **Prevalence unlike deployment** (R2-4 round 1, R2-2 round 2) | fixed now + limitation | D-106(e): at an assumed 5% bug-revealing share, D2 precision is KUU 0.065, cascade 0.16, Sonnet DEB 0.27. The Appendix F reading and DEFENSE_QA 26 say these rules suit a stage whose job is not to lose bugs. P_adj at the frame's natural prevalence is already in Table 4. **Limitation:** no failures from non-buggy control methods. |
| 9 | **D2 is not a contamination control; the frontier judge is contaminated on D1** (R2-3 both rounds) | fixed now + limitation | Appendix E and Threats say D2 removes recall of the fixes, not knowledge of the original code. E9b found no drop (MCC 0.734 on D1, 0.788 on D2), which is reported as descriptive. DEFENSE_QA 5 and 21. **Limitation:** D3/GitBug-Java not run. D-101 records the disk failure; D-103 records that its 2023 bugs predate every 2026 model, so it could not be a post-cutoff control either. |
| 10 | **Underpowered; nulls read as negatives** (R3-1 round 1, R3-3 round 2) | fixed now | The Discussion paragraph is now "Debate and Javadoc: inconclusive". The conclusion now reads "inconclusive rather than absent", and the abstract reports Javadoc as "no detectable benefit". The MDEs are in Table C1, Threats and DEFENSE_QA 2. The design had no a priori power target; the authors should say so if asked. |

## The rest

| Objection (round) | Triage | Where |
|---|---|---|
| Abstract overclaims; confirmatory, exploratory and post hoc results are mixed (R1-2, r1) | fixed now | The abstract labels the ablations "exploratory" and the KUU/cascade evidence "pre-registered on seeded faults"; the conclusion matches. |
| Many deviations / forking paths (R1-5, r1) | answered | Appendix A lists every deviation with its D-entry; harness faults are disclosed in Appendix D. |
| Error diversity confounded and stated causally (R1-5, r2) | fixed now + limitation | "because" is now "consistent with" in the abstract and conclusion. The Results and Appendix F state the model-versus-resample confound. D-106(f) gives the difference scale: D2 −0.034 [−0.051, −0.018], D1 interval includes 0. **Limitation:** no same-family multi-model triple. |
| Baselines weak; R0 not the cited triage; +92.3% inflates (R2-2 r1, R2-4 r2) | answered + limitation | The re-implementation-fidelity table in Appendix B states for each arm where it departs from the base approach. The improvement analysis is required by the brief and is marked not significant. **Limitation:** no learned non-LLM baseline. |
| One generator; generator-family overlap with M2 (R2-4, r2) | limitation | E7a's two candidates failed the dev selection (D-100, D-102); Threats (External) and DEFENSE_QA 14. |
| Javadoc result may be mechanical (truncation, P_B Javadoc) (R2-5, r1) | answered + limitation | Package truncation is recorded per instance (the evidence package's `truncated` fields); Table B1's D2 case discusses documented buggy behaviour. **Limitation:** no length-matched control. |
| Tests lost, not bugs lost (R2-5, r2) | fixed now | "Bugs with no bug-revealing test kept" is reported for KUU, the cascade, both Sonnet arms and M1 DEB (Appendix F(d); `cascade_d2.json`). The break-even per bug is not recomputed (limitation). |
| p-value construction not stated (R3-4, r1) | fixed now | Metrics paragraph: two-sided, twice the smaller tail share, +1 corrected. |
| Many Holm families, trivial MCC > 0 tests (R3-4 r1, R3-5 r2) | fixed now + limitation | Appendix F labels H6-2, H9-2 and H11-1 as sanity checks. Each family was registered in its own D-entry and is labelled confirmatory, robustness or exploratory. **Limitation:** no paper-level gatekeeping family. |
| Few clusters; Wilcoxon power; McNemar inputs; Chart influence (R3-5, r1) | fixed now | D-106(g): leave-one-project-out ΔF1 for H1/H3a/H3b never changes sign (H1 0.12–0.24, H3a 0.04–0.11, Chart included). Appendix F states McNemar's input: majority correctness over three replicates. Wilcoxon stays a sensitivity analysis; its p-value cannot go below 0.031 with six projects (rehearse this). |
| Bootstrap ignores project stratification; P_adj has no CI; cross-dataset MCC (R3-4, r2) | fixed now + limitation | LOPO is reported (D-106(g)); cross-dataset comparisons (D1 − D2 MCC) are labelled descriptive. **Limitation:** no stratified project→bug bootstrap; no CI for P_adj. |

## What the authors should rehearse

1. **The gate failure.** Open with the scope: RQ2/RQ3 are about a small sub-gate judge, and the stronger judges are why
   we report M2, the 35B and Sonnet.
2. **KUU at a matched discard rate.** Concede the small margin (4 against 6 lost). The case rests on two things: no
   tuned threshold, and escalation lifting MCC to 0.666.
3. **Cost.** Sonnet J1 everywhere is cheaper at similar MCC. The cascade is about bugs uncovered (2 against 7), not MCC
   per dollar.
4. **Contamination.** D2 rules out recall of the fixes, not knowledge of the original code; GitBug-Java's 2023 bugs
   would not have helped either (D-103).
