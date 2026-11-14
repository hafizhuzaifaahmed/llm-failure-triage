# Research state, 2026-11-13 (handoff and fresh-session entry point)

Branch `research-extension`, HEAD `3b017f2` when this was written. The eight files of this design phase are new and
**uncommitted**; nothing else in the repository was touched. No model call, no probe run, no external action.

## 1. Where things stand

| Item | State |
|---|---|
| Confirmation (OSF kp79c) | complete, analysed, committed (`3b017f2`). Results unchanged by this phase |
| Independent audit | done: `CONFIRMATION_INDEPENDENT_AUDIT.md`. Arithmetic, code and chronology validated; interpretation qualified |
| Prior art, third pass | done: `UPDATED_NOVELTY_AND_CONTRIBUTION_ASSESSMENT.md` |
| Contribution chosen | empirical paper with a registered confirmation; one **exploratory** extension, whole-method dependence probes (WDP) |
| Stage B | **not run before 15 November**; original plan untouched; v2 design in `STAGE_B_FINAL_PROTOCOL.md` |
| e-Otter++-style baseline | not feasible or fair before the deadline; future work |
| Opus handoff | `OPUS_EXECUTION_BRIEF.md`, waiting for the authors' approval |
| Paper and deck | plans only: `PUBLICATION_STRATEGY.md`, `DEFENCE_DECK_RESTRUCTURE.md`; `paper/` untouched |
| OSF template-field reconciliation (Priority 1) | deferred by the authors; not touched |

### Update, later on 2026-11-13: authors' conditional approval

- Approved: P1 (audit replication); implementation, engineering run (`WDP_D1_DEV`) and freeze; `_v2` manuscript
  and deck.
- **Not approved yet:** `WDP_D1_TEST` and the three `WDP_CONF_*` runs. They wait for the authors' review of the
  freeze commit (brief rule 0.8, step P3b).
- `TECHNICAL_METHOD_SPEC.md` and `OPUS_EXECUTION_BRIEF.md` are at **version 2**: the throw variant writes an entry
  marker; a static screen flags tests that could intercept a `Throwable` or `Error`; level U is an operational
  observation ("no entry observed, throw-invariant") and is never assigned when entry was recorded or the screen
  fires; WDP runs on existing data are "retrospective evaluation runs".
- The ladder is reported even if the primary criterion is not met, provided the quality checks pass. If WDP
  threatens the manuscript, the manuscript wins and WDP becomes future work (default cut-off 2026-11-14 20:00 +05).
- Open questions 2 to 4 of section 4 below are answered: `_v2` copies yes; ladder retained; audit scripts stay.

## 2. Findings to carry forward (all in the audit file with sources)

1. Every registered number reproduces from raw tranche records with independent code.
2. C1 (flip): +0.028 [−0.137, 0.274]. Excludes the pilot's 0.511, includes half of it. Flip rates: PF 0.255,
   TF 0.226, control 0.220. In F1 without mutant-less tests: 0.348 against 0.345. `rcf`: 4/55 PF, 32/517 TF.
3. C2 (decoupled): +0.243 [0.114, 0.372], Holm p 0.0024; 135 of 136 flagged tests are TF. F1 +0.039, F2 +0.319;
   F2 − F1 = +0.280 [0.089, 0.469] (exploratory). 117 of 135 flagged TF are in JacksonDatabind and JacksonCore;
   without both: +0.041 [−0.035, 0.108] (exploratory).
4. Decoupling lives in exceptions raised outside the method under test (82 of 160 such TF; 0 of 6 such PF).
5. Fewer than ten compiled mutants: 21/55 PF, 104/517 TF. The minimum alone shields 19 PF and 83 TF tests.
6. Lost bugs of the decoupling certificate: `Codec_13` (pilot) and `Math_59` (confirmation, exactly ten mutants);
   both are operator gaps.
7. Rules on 561 tests: KUU 1.000 / 0.316 / 0 bugs lost; KUU + CD 0.982 / 0.430 / 1; 2-of-3 0.870 / 0.521 / 4.
   C3 Holm p 0.142 (unadjusted 0.047, seed-sensitive). C4 inconclusive.
8. Pilot re-read: 20 of its 40 flipping PF tests were in Chart.
9. Correction to an earlier document: e-Otter++ keeps tests that are fail-to-pass on **any** patch (§3.3).

## 3. Decisions made in this phase

| # | Decision | Where |
|---|---|---|
| 1 | Registered readings stand; eleven wording corrections | audit §7 |
| 2 | Abandon flip and CK as findings; narrow CD; no novelty claim | assessment §3 |
| 3 | Primary extension: WDP with certificate CD-U; primary outcome ΔTNR over KUU on 561 confirmation tests; safety: no additional bug lost; exploratory | `TECHNICAL_METHOD_SPEC.md`, brief §2 |
| 4 | Fallback: empirical paper without a method | brief §1 |
| 5 | No Stage B before 15 November | `STAGE_B_FINAL_PROTOCOL.md` §3 |
| 6 | No e-Otter++-style arm before 15 November | assessment §4 |
| 7 | No external registration of anything before 16 November; afterwards only with the authors' approval | all files |

## 4. Open questions for the authors

1. Approve the brief as written (go / no-go for P1–P5)?
2. Approve editing copies of the manuscript and deck (`*_v2`), leaving the submitted files intact?
3. If the WDP criterion is not met, include the ladder as a descriptive subsection or leave WDP out entirely?
4. May the three audit scripts stay under `docs/research_extension/audit_scripts/`?

## 5. Next actions

| Who | Action |
|---|---|
| Authors | read the decision report; answer section 4 |
| Opus | brief steps P1 → P5, then P7; stop at any stop condition |
| Fable | P6: interpretation and claim-alignment review from the brief, `wdp_report.md`, `wdp_analysis.json`, run manifests and the changed-file list only |

## 6. Files of this phase

`CONFIRMATION_INDEPENDENT_AUDIT.md` · `UPDATED_NOVELTY_AND_CONTRIBUTION_ASSESSMENT.md` ·
`STAGE_B_FINAL_PROTOCOL.md` · `TECHNICAL_METHOD_SPEC.md` · `OPUS_EXECUTION_BRIEF.md` · `PUBLICATION_STRATEGY.md` ·
`DEFENCE_DECK_RESTRUCTURE.md` · this file · `audit_scripts/` (three read-only scripts and a README).

Sources read on the web in this phase, with depth, are listed in the assessment §1.
