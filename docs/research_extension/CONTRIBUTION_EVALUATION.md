# Contribution evaluation: counterfactual program probes

**Decision: conditional go.** The mechanism carries a real, sizeable signal on held-out real faults and both
hypotheses fixed in advance hold, but the data are 22 bugs whose labels were known before the rules were written, and
one certificate lost a bug. The claim becomes defensible only after the same rules, unchanged, are run on fresh real
faults.

Every number below is in `generated/cfp_tables_CFP_D1_TEST.md`, rendered by script from
`results/extension/ext1_probe_analysis_CFP_D1_TEST.json` and `ext2_probe_ablations_CFP_D1_TEST.json`.
Decisions: D-134 (design), D-135 (scope amendment before the held-out run), D-136 (ablations).

## 1. What was run

| Item | Value |
|---|---|
| Run | `CFP_D1_TEST`, engine at `eb2d231`, 2026-11-11 |
| Data | every labelled D1-test failure: 369 (60 PF, 296 TF, 13 AMB), 95 focal methods, 74 bugs, 22 with a bug-revealing test |
| Model calls | none |
| Wall time | 1,228 s for the whole split with 12 parallel JVMs, about 3.3 s per failing test including mutant compilation; the probe step alone has a median of 0.97 s per test |
| Exclusions | none of the four named kinds; 49 scored instances had fewer than 10 compiled mutants and fall through to the base rule |
| Engineering pilot | D1-dev twice (focal-only scope, then the amended scope); used to debug the engine and disclosed in D-135 |
| Tests | 22 unit tests for the prototype; the study's 356 still pass |

Status of the result: the operator set, cap, thresholds, hypotheses and rules were committed before any held-out
probe ran. The held-out *labels and judge votes* had been seen during the original study, so the result is
exploratory with respect to the study, not a confirmation.

## 2. Does the evidence separate the two kinds of failure?

| Observable | Bug-revealing tests | Wrong tests | Difference [95% CI] | Reading |
|---|---|---|---|---|
| Some single edit makes the test pass (`flip`) | 40 of 60 (0.667) | 46 of 296 (0.155) | 0.511 [0.252, 0.740] | a flip is 4.3 times as likely when the test is right |
| …and no sibling test breaks (`rcf`, HP-1 as fixed) | 17 of 60 (0.283) | 16 of 296 (0.054) | 0.229 [0.007, 0.478] | **HP-1 supported**, narrowly |
| No edit changes the failure at all (`decoupled`, HP-2) | 1 of 60 (0.017) | 61 of 296 (0.206) | −0.189 [−0.309, −0.075] | **HP-2 supported**; 61 of the 62 decoupled failures are wrong tests |

- As a ranking score, the share of mutants that flip the test has AUROC 0.779 over all 356 failures. For
  orientation only (different instance sets, so not a paired comparison): the paper reports 0.622–0.678 for the
  thinking-disabled M1 arms and 0.733 for the three-judge vote count on the 177-instance sample, and 0.554 for a
  classifier on cheap failure features.
- The signal is not the failure type. Failure type alone has AUROC 0.424. Within assertion failures a flip exists for
  28 of 45 right tests against 33 of 177 wrong ones; within exceptions, 12 of 15 against 13 of 119.
- It reaches bugs, not only tests: 14 of the 22 bugs with a bug-revealing test have one that flips; 14 of 52 bugs
  with only wrong tests have any flip.

## 3. Do the certificate rules help?

On the 177 instances for which judge votes exist (60 PF):

| Rule | TPR | TNR | Balanced accuracy | Bugs lost | Δ balanced accuracy [95% CI] |
|---|---|---|---|---|---|
| Keep-all | 1.000 | 0.000 | 0.500 | 0 | |
| Keep-all + CD (no model at all) | 0.983 | 0.205 | 0.594 | 1 | +0.094 [0.040, 0.156] |
| KUU (three judge calls) | 0.983 | 0.205 | 0.594 | 1 | |
| KUU + CK + CD | 0.983 | 0.333 | 0.658 | 1 | +0.064 [0.014, 0.122] |
| KUU-NG | 0.983 | 0.171 | 0.577 | 0 | |
| KUU-NG + CD | 0.967 | 0.350 | 0.659 | 1 | +0.081 [0.031, 0.138] |
| 2-of-3 vote | 0.900 | 0.470 | 0.685 | 2 | |
| 2-of-3 + CK | 0.967 | 0.470 | 0.718 | 0 | +0.033 [0.000, 0.083] |
| 2-of-3 + CK + CD | 0.950 | 0.556 | 0.753 | 1 | +0.068 [0.020, 0.128] |
| Thinking M1 J1 | 0.883 | 0.658 | 0.771 | 3 | |
| Thinking M1 J1 + CK + CD | 0.883 | 0.718 | 0.801 | 3 | +0.030 [−0.018, 0.077] |
| Sonnet debate (frontier) | 0.811 | 0.917 | 0.864 | 4.0 | |
| Sonnet debate + CK | 0.883 | 0.875 | 0.879 | 2.7 | +0.015 [−0.034, 0.093] |

What this shows:

1. **A rule with no model reproduces KUU's operating point.** Discarding only decoupled failures gives the same TPR
   and TNR as three judge calls on this split (0.983, 0.205). It loses one bug; KUU also loses one.
2. **The probe adds to keep-heavy rules.** The decoupling certificate raises the test-fault removal of KUU from 0.205
   to 0.333 and of KUU-NG from 0.171 to 0.350; the balanced-accuracy gains exclude zero.
3. **The keep certificate rescues tests that judges discard.** On the 2-of-3 vote it cuts lost bug-revealing tests
   from 6 to 2 and lost bugs from 2 to 0 without removing fewer test faults. On the frontier judge it cuts lost tests
   from 11.3 to 7.0 (three-replicate means) at a cost of 0.043 in TNR; that gain's interval includes zero.
4. **It does not rescue a strong local judge.** For the thinking judge the balanced-accuracy change is within noise.
5. **Against the best local point in the paper.** The fully local cascade (three judge calls plus a ≈70 s thinking
   call on about 60% of failures) is at TPR 0.950–0.983, TNR 0.530–0.573 on this split (paper Table G9). The 2-of-3
   vote with both certificates is at 0.950, 0.556 with three one-shot calls and about 3 s of CPU. Comparable accuracy
   at a fraction of the GPU time; not shown to be better.

## 4. What the ablations say about the mechanism

| Question | Finding |
|---|---|
| Does the wider region matter? | Mostly for coverage. Focal body only: 209 instances reach 10 mutants, flips 37 of 60 against 35 of 296. With callees: 307 instances, 40 of 60 against 46 of 296. The amendment bought usable instances, not a sharper signal |
| Does the sibling filter help? | It trades coverage for a slightly better ratio: likelihood ratio 4.29 → 5.24, but right-test coverage falls from 40 to 17. Only 71 of 365 flipping mutant runs keep every sibling passing. The dev pilot's explanation holds: siblings generated from buggy code assert buggy behaviour, so real fixes break them |
| Which edits carry the signal? | Literal changes alone flip 26 of 60 right tests and 8 of 296 wrong ones; relational changes 35 and 21; statement deletion 11 and 7. Condition negation is the noisiest (31 and 38). Logical-connector swaps point the other way (2 and 13). No single family is necessary: removing any one leaves at least 38 of 60 |
| Is there parsimony across tests? | A flip shared with another failing test of the same method: 35 of 60 right tests against 31 of 296 wrong ones, a better ratio than any flip (candidate N6) |
| Where does decoupling live? | Mostly in exceptions: 51 of 119 wrong tests that fail with an exception are decoupled, against 10 of 177 assertion failures |

## 5. Error analysis

Fixed bodies were read from the label-side store for this section only (analysis side; the engine cannot open them).

- **The one bug-revealing test flagged decoupled** is `Codec_13`, `isDoubleMetaphoneEqual` called with null
  arguments, failing with a `NullPointerException`. The buggy body is a single statement,
  `doubleMetaphone(value1, …).equals(doubleMetaphone(value2, …))`; the fix replaces the call by a null-safe
  `StringUtils.equals(…)`. All 79 compiled mutants sit in the helper method and none changes an exception raised by
  calling a method on a null result. A fault repaired by *replacing a call* is outside what single edits of existing
  operators can reach or influence: the predicted failure mode of H-dep, and it cost one bug of 22. A guard that never
  applies CD when the exception is raised inside the method under test would have avoided it; that is a rule change
  suggested by this data and so belongs in the next study, not in this result.
- **Bug-revealing tests with no flip** concentrate in `Math_98` (7) and `Math_56` (4). `Math_98`'s fix sizes an array
  by `nRows` instead of `v.length`: a variable replacement, which the operator set does not contain. Twenty of 60
  right tests have no route to passing within the operator set.
- **Wrong tests that flip.** Condition negation alone flips 38 of the 46 wrong tests that flip at all (and 31 of the
  40 right ones): inverting a guard often makes an arbitrary expectation hold. By bug they concentrate in
  `JacksonDatabind_106` (5), `Lang_24` (4) and `Math_73` (4).
- **A flip is not a fix.** In `Chart_17` the bug-revealing clone test passes when `getItemCount() - 1` becomes
  `getItemCount() + 1`; the developer's patch instead clones the object and deep-copies its data. The verdict is right
  and the edit is wrong, which is why a flip is treated as evidence with a measured false-positive rate and is never
  offered as a repair.

## 6. Threats to this result

| Threat | Status |
|---|---|
| Labels and votes of D1-test were known when the rules were designed | open; only fresh faults remove it |
| 22 bugs | every bug-level interval is wide (Δ bugs lost for CD: +1 [0, 3]) |
| The frame guarantees a fix-changed method under every test | open; may flatter the reach hypothesis. A control set of failures on non-buggy methods would measure the flip rate where no bug exists |
| One scope amendment after the dev pilot | disclosed (D-135) with the dev counts; the focal-only scope is reported and shows the same pattern |
| D2 not used | deliberate: a one-line mutant of the fixed version is one edit from passing by construction |
| HP-1's interval lower bound is 0.007 | the filtered form of the certificate is fragile; the unfiltered flip rate is the robust finding |
| Policy table is on 177 instances, flag rates on 356 | stated in each table; the rules need votes, which exist only for the sample |
| Single run | the engine is deterministic apart from timeouts; no ERR-driven flips can occur because a pass must repeat |

## 7. Go / no-go against the gates

| Gate (`CONTRIBUTION_SELECTION.md`) | Result |
|---|---|
| Novelty | passed on the searches run; two neighbouring preprints still to be read in full |
| Feasibility | passed: a whole split in 20 minutes on one laptop, no model |
| Signal | passed: HP-1 and HP-2 both hold; the raw flip difference is 0.511 [0.252, 0.740] |
| Usefulness | partly: balanced accuracy of KUU, KUU-NG and the 2-of-3 vote rises with intervals excluding zero; no gain for the thinking judge; CD lost one bug |
| Confirmation | **not done**; needs fresh real faults (`PREREGISTRATION_DRAFT.md`) |

**Conditional go.** What is supported now: on Defects4J real faults, whether a failing generated test can be made to
pass by one small edit of the method under test, and whether any such edit changes the failure, are informative about
which side is at fault, at a cost of seconds and no model. What is not supported: that the certificate rules are
safe (one bug lost in 22), that they beat the fully local cascade, or that any of this holds beyond this benchmark
and generator.
