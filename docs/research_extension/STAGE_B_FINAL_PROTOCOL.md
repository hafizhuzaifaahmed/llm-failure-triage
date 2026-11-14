# Stage B: provenance, assessment and decision

Date: 2026-11-13. **Decision: Stage B is not run before 15 November 2026.** The original plan is preserved
unchanged in `STAGE_B_PLAN.md`. Section 4 holds a revised design (v2) for a later date; it is a design only,
it is **not externally preregistered**, and no registration of any kind is to be made for it before
16 November 2026, nor afterwards without the authors' explicit approval.

## 1. Provenance of `STAGE_B_PLAN.md`

| Fact | Evidence |
|---|---|
| Written and committed once, never edited since | `git log -- docs/research_extension/STAGE_B_PLAN.md`: one commit, `4fb3909`, 2026-11-11T21:33:19+05:00 (D-139) |
| Written **after** the pilot's outcomes were known | pilot recorded in D-137 (commit `4883e66`), earlier the same day; the plan's report template and its hypotheses assume the pilot's flip effect |
| Written **before** the OSF registration | kp79c: 2026-11-12T08:47:01Z |
| Written **before** any confirmation test existed | first generation call 2026-11-12T10:43Z; labels sealed 2026-11-13 (`1a58e54`) |
| **Not covered by the OSF registration** | the registered text never mentions Stage B; the deposited bundle (`osf_deposit/cfp_confirmation_frozen_bundle.zip`, 30 files) does not contain the plan |
| Its own statement about status | Stage B-1 (pilot data): "labels known: exploratory". Stage B-2 (fresh tranche): "needs its own registration addendum before any call" |
| Nothing built or run | no `src/triage_ext/report.py`, no Stage B run name in `configs/local_scope.json` |

**Honest status.** The three-arm design is *pre-specified relative to the confirmation outcomes* and
*unregistered*. If it were run now on the F1 and F2 tests exactly as written, it would be: design fixed before the
confirmation outcomes, executed after them, on data whose labels, probe outcomes and judge votes have been
analysed. That is **exploratory**, however early the design was committed. It could be called confirmatory only on
tests that no probe or judge has yet seen, under a registration made before those tests exist; the plan says the
same of itself. External registration is barred until 16 November, so no confirmatory Stage B can exist by the
deadline.

## 2. Does the three-arm design answer the most important next question?

What the design does well, and should be kept:

- The **shuffled arm** is the right control. B − C isolates content from length, format and position; C − A shows
  what a generic report does by itself. Few prompt-augmentation studies include it.
- Matched calls, model, decoding and output cap; a derangement that reuses every report exactly once, so B and C
  carry the same multiset of text.
- A report with counts and edit kinds only, so that a foreign report is not recognisable and the leakage guard is
  not tripped.
- The outside-rule comparator: if a judge with the report does not beat the certificate applied outside the judge,
  the prompt adds nothing.

Why it is no longer the strongest next experiment:

| # | Reason | Evidence |
|---|---|---|
| 1 | **Two of the report's three lines carry evidence that failed confirmation.** `[C2]` tells the judge that an edit makes the test pass and that siblings still pass. In the confirmation a flip is as common for wrong tests (0.226) as for right ones (0.255), and the sibling-safe flip is no better (0.062 against 0.073) | audit §3 |
| 2 | **The plan's stated threat is now the expected outcome.** The plan warns that a judge may read "an edit makes it pass" as "program fault". With 117 flipping wrong tests against 14 flipping right ones, a judge that follows the report would keep more wrong tests, and the 2-of-3 + CK row already shows that effect from outside (TNR 0.521 → 0.501) | audit §5 |
| 3 | **The useful line can only teach the judge a rule that already exists.** `[C3]` conveys decoupling. The best a judge can do with it is discard decoupled failures, which CD does deterministically at no cost. Under KUU a decoupled wrong test is discarded only if all three judges follow the report; 58 of 135 decoupled wrong tests were not unanimous | audit §5 |
| 4 | **It tests whether a judge can read a report, not whether there is a better method.** The open scientific question after the confirmation is what the surviving signal *is* (non-reachability, insensitivity, or operator gaps), why it is frame- and project-specific, and whether it can be made safe. Stage B is silent on all three | audit §4 |
| 5 | **Changing the report now is a post-outcome alteration.** Dropping the flip lines is sensible and makes every arm's result exploratory by construction | chronology |
| 6 | **Power.** 21 PF-bearing bugs. C3, a simpler paired contrast on the same tests, has an interval of ±0.05 in balanced accuracy and did not survive correction | registered result |
| 7 | **Budget.** The KUU panel on three arms and three replicates is 15,444 calls, about 11 GPU-hours at the measured rate (73 minutes per arm-replicate for the three judges on 588 tests, `confirm_logs/votes.log`), after building a renderer, a wrapper, guard passes and a prompt check. It would displace the audit follow-ups and the manuscript | measured |
| 8 | **Stage B-1 as written (pilot data, M1 only) answers a superseded question.** On the pilot the flip signal is strong, so a positive B − C there would advertise evidence that did not replicate | pilot vs confirmation |

Item-by-item assessment requested in the mandate:

| Design element | Assessment |
|---|---|
| Matched instances, paired comparison | sound |
| Identical prompt, model, decoding, cap, calls | sound; one open check remains (whether the frozen prompt enumerates citable id families; if so the added sentence goes into all three arms and the original arm-A results are shown as an anchor) |
| Shuffle construction | sound; v2 adds stratification so that the foreign report has the same dependence level distribution within failure type |
| Leakage guard | must be applied to every augmented package in all arms, and the refusal sets must be reported per arm; 11 packages are already refused |
| Replicates | 3 per arm; replicates averaged within a bootstrap resample, as planned |
| Primary outcome | the plan lists four hypotheses and no single primary. v2 fixes one (section 4) |
| Multiplicity | Holm over the stated family; bug-level bootstrap |
| Outcomes | TPR, TNR, bugs lost per arm must be reported beside balanced accuracy; balanced accuracy alone hid a lost bug in C3 |
| Thinking-enabled judge | not essential. It failed its development gate, truncates outputs, and costs about 70 s per call. A separately labelled sensitivity analysis on a sample at most |
| Control group | not included. It has no bug-revealing test, so it can add only to TNR and would change the PF:TF mix. It can be reported as a separate descriptive arm (how often each arm discards a control failure) |
| Sample adequacy | not adequate for a confirmatory claim on F1 and F2; fresh tests are needed |

## 3. Decision and what replaces it

1. **No Stage B call before 15 November.** `STAGE_B_PLAN.md` stays as written and is cited as the original design.
2. The next experiment is the dependence ladder (`TECHNICAL_METHOD_SPEC.md`, `OPUS_EXECUTION_BRIEF.md`): no model
   calls, hours not days, and it addresses reasons 3 and 4 directly.
3. Stage B returns to the list only if the ladder shows that a judge could be told something the outside rule
   cannot use, for example a graded level rather than a binary flag. Then v2 below applies, on fresh tests.
4. The paper lists Stage B as designed and not run, with reason 1 as the explanation.

## 4. Stage B v2 (design for a later date; not run; not registered)

Everything that differs from `STAGE_B_PLAN.md` is a change made **after** the confirmation outcomes and is marked †.

| Item | Specification |
|---|---|
| Question | Does a dependence report help a three-judge KUU panel decide, and is any gain due to its content? |
| Arms | **A** package (S1) · **B** package + this test's dependence report · **C** package + a foreign test's report |
| Report † | Three lines, counts only, no source, identifiers or line numbers, never a statement of fault side: `[C1]` whether the failure was identical when the method under test was made to throw on entry; `[C2]` how many fixed-return replacements were tried and how many changed the failure; `[C3]` how many single edits compiled and how many changed the failure. **No line says that an edit makes the test pass** † |
| Shuffle | seeded derangement; the donor test is from a different bug, has the same failure type and † the same dependence level stratum where a donor exists; every report used once |
| Judges † | M1, M2, M3 one-shot, thinking off, S1, the frozen prompts and decoding of the confirmation votes; if the prompt enumerates citable id families, one sentence naming `[C…]` is added to all three arms |
| Replicates | 3 per arm and judge, at replicate indices no committed run has used |
| Data | for a confirmatory reading: failing tests that no probe or judge has seen (a second generator on the frame, or another benchmark). On F1 and F2: exploratory |
| Primary outcome † | balanced accuracy of the KUU decision from arm-B votes minus that from arm-C votes (paired, bug-level bootstrap, 10,000 resamples, replicates averaged within a resample) |
| Safety constraint † | bugs lost by KUU on arm-B votes must not exceed bugs lost by KUU on arm-A votes; reported with the exact one-sided 95% bound |
| Secondary | B − A (practical gain), C − A (length and format); per-judge TPR and TNR; PF tests lost; share of decisions citing a `[C…]` item; invalid-output rate; realised input and output tokens per arm with the plan's 2% and 10% flags |
| Comparator | KUU on arm-A votes with CD-U applied outside. If arm B does not beat it, the in-prompt report adds nothing |
| Multiplicity | Holm over {B − C, B − A} for the KUU decision |
| Thinking-enabled judge | not in the family. Sensitivity only: M1 with thinking on, one replicate, on a seeded sample of every PF test and twice as many TF tests |
| Control group | descriptive only: discard rate of control failures per arm |
| Budget | 15,444 one-shot calls for 572 tests, about 11 GPU-hours; the sensitivity sample about 165 tests × 3 arms × 70 s ≈ 10 hours |
| Preconditions | the ladder has been run and reported; the renderer and derangement are unit-tested; every augmented package passes the leakage guard; the protocol is committed with a decision entry and a content hash before any call |
| Registration | none before 16 November 2026. Afterwards only with the authors' explicit approval. An internal commit is not a preregistration and must not be described as one |
| Interpretation | B − C > 0 with the safety constraint met: the judges use the content. B − C ≈ 0 and B − A > 0: form, not content. B below the outside comparator: keep the rule outside the prompt. Any bug lost by arm B that arm A keeps: the report is unsafe as written |
