# Experiment blueprint

Three stages. Stage A is what this pass ran. Stages B and C are designed, not run; each needs something this pass
could not use (new generation time, local model sessions, or an author approval). The status column is exact.

## 1. Research questions

| RQ | Question | Hypothesis | Estimand | Unit | Falsified if |
|---|---|---|---|---|---|
| X1 | Does a failing test that is right have a passing state one small program edit away more often than one that is wrong? | H-reach: P(flip \| PF) > P(flip \| TF) | difference of the two rates | instance; intervals resample bugs | the bug-level 95% interval of the difference includes 0 |
| X2 | Is a failure that no edit of the method under test can change a test fault? | H-dep: P(decoupled \| TF) > P(decoupled \| PF) | difference of the two rates; PF share among decoupled instances | same | interval includes 0, or the PF share among decoupled is not below the base share |
| X3 | Do certificate rules built on X1 and X2 move a base rule off the existing TPR–TNR frontier without losing bugs? | CK raises TPR of a discarding judge; CD raises TNR of a keeping rule; bugs lost do not rise | paired differences in TPR, TNR, balanced accuracy, PF tests lost, bugs lost | same | no base rule improves in balanced accuracy with an interval excluding 0, or bugs lost rise |
| X4 | Is a judge short of evidence or of reasoning? | A probe report in the package raises the same judge's balanced accuracy at equal calls | paired difference, judge with vs without report | same | interval includes 0 for every judge |

X1–X3 are discovery on D1 (Stage A) and confirmation on fresh faults (Stage C). X4 is Stage B.

## 2. Stage A: mechanism pilot on existing real faults — **run in this pass**

| Item | Value |
|---|---|
| Data | D1-dev (engineering only) and D1-test, all labelled instances: 60 PF, 296 TF, 13 AMB; 76 bugs, 22 with a PF test |
| Status | Exploratory. Probe outcomes on D1-test were unseen when the rules were fixed (D-134 to D-136); labels and judge votes were not |
| Probes | fixed operator set, cap 80, depth 2, 10 s timeout; one run per mutant, a pass re-run once |
| Primary outputs | HP-1 (as fixed: regression-consistent flip), HP-2 (decoupling), both with bug-level bootstrap intervals; raw flip rate beside them |
| Policies | CK on M1 debate, thinking M1 J1, 2-of-3, Sonnet debate; CD on keep-all, KUU, KUU-NG; CK+CD |
| Ablations | scope, sibling filter, operator leave-one-out, failure-type strata, bug level, shared flips, cost (D-136) |
| Model calls | none |
| Stopping rule | neither HP-1 nor HP-2 holds → negative result, no extension |

## 3. Stage B: evidence versus reasoning — **designed, not run**

Needs local model sessions on the frozen server (≈1.7 s per one-shot call, ≈70 s with thinking; measured in D-131).

| Factor | Levels | Why |
|---|---|---|
| Evidence | package (S1) · package + probe report | the mechanism under test |
| Judge | M1 one-shot, thinking off · M1 one-shot, thinking on | the two ends of the "reasoning" axis already measured |
| Control | package + a *shuffled* probe report (another instance's report) | separates information from added length and format |

Design: 3 × 2 on D1-test's 177 common instances, 3 replicates for thinking-off, 1 for thinking-on (as in the study).
Equal calls by construction; tokens reported, and the shuffled-report arm matches tokens.
Primary contrast: report − no report, within judge. Interaction (report × thinking) answers X4 directly: if the report
helps the thinking-off judge and not the thinking-on judge, evidence substitutes for reasoning; if it helps both, they
add. Holm over the two within-judge contrasts.
Cost estimate (not measured): thinking-off 177 × 3 arms × 3 replicates ≈ 1,600 calls ≈ 45 min; thinking-on 177 × 3 ≈ 530
calls ≈ 10 h. The report must first pass the leakage guard on every instance.

## 4. Stage C: confirmation on fresh real faults — **designed, not run**

The only stage that can make a claim confirmatory. Details in `DATASET_EXPANSION_PLAN.md` and
`PREREGISTRATION_DRAFT.md`.

| Item | Value |
|---|---|
| Data | the 78 focal methods the per-project cap left out (53 further defects), never generated for, never judged |
| Generation | frozen generator, 3 generations per method, buggy context; identical harness |
| Sealing | labels computed and stored before any probe or judge reads the instances |
| Probes and rules | the Stage A engine and rules, byte-identical (commit pinned) |
| Judges | KUU panel and thinking M1 J1 on the frozen server, to give the rules their base predictions |
| Primary hypotheses | the Stage A findings that survive, restated before generation |
| Power | see below |

**What Stage C can and cannot detect.** D1-test yielded 60 PF tests in 22 bugs from 195 methods (0.11 bugs with a PF
test per method). At that rate 78 methods give about 9 bugs with a PF test and about 24 PF tests (an extrapolation,
not a measurement). That is too few for a bug-level test of a rule. It is enough for the instance-level rate
difference in X1 only if the Stage A effect is large. The plan therefore asks for more generations per method across
*all* 312 frame methods and treats the 78 as the first sealed tranche. Target: at least 60 bugs with a PF test, the
size at which zero losses certify a bug-loss rate below 5% (1 − 0.05^(1/60) = 0.049).

## 5. Baselines

| Baseline | Source | In Stage A |
|---|---|---|
| Keep-all, discard-all, R0 | committed | yes |
| M1 one-shot, self-consistency, debate | committed decisions | debate as a CK base |
| KUU, KUU-NG, 2-of-3 | committed | yes |
| Thinking M1 J1 | committed | yes |
| Fully local cascade, Sonnet cascade | committed | reported beside, not wrapped |
| Sonnet debate (frontier reference) | committed | yes, as a CK base |
| Failure-feature classifier, vote stacker | committed (`wp14_learned.json`) | compared through failure-type strata (EXT-2 d) |
| Closest published methods | Meta's judge ensemble and Wang et al.'s validator are judge-over-fixed-package designs; the study's J1/SC/2-of-3 arms are their local analogues. No re-implementation is claimed | — |

No rule here sees the fixed version. Base rules and certificate rules use the same instances and the same bootstrap.
Budget: the probe adds CPU seconds and no calls, so a call-matched comparison is trivially satisfied; the fair
comparison is against the same base rule without the probe, which is what the paired differences report.

## 6. Outcomes

Primary (safety): PF tests lost and bugs lost. Primary (utility): TNR. Reported together as (TPR, TNR) and balanced
accuracy, which do not depend on the PF:TF mix. Secondary: test faults kept per bug-revealing test kept at 5% and at
the labelled prevalence; coverage of each certificate (share of failures it decides); CPU seconds per failure.
Not used as a headline: F1 and MCC (they move with prevalence; the paper shows why).

## 7. Statistics

- Unit: the bug. All intervals are bug-level cluster bootstrap, 10,000 resamples, seed `config.SEED_BOOTSTRAP`,
  identical resamples for paired differences.
- Stage A: no p-value and no multiplicity family. The labels were seen before; the stage is discovery.
- Stage C: one Holm family over the confirmatory hypotheses listed in the preregistration draft.
- Missing data rules, fixed in D-134: an excluded instance (four named reasons) or one with fewer than 10 compiled
  mutants gets the base rule; exclusions are counted by label only after probing; AMB is reported apart.
- Non-determinism: a pass must repeat to count as a flip; timeouts are class ERR, never a flip or a shift.
- Sensitivity: focal-only scope; flips with no sibling available counted as not regression-consistent; leave one
  project out for the rate differences (Stage C).
- Guarantees: none is claimed. A bug-level upper bound is reported as a description (exact binomial on bugs).

## 8. Threats specific to the extension

| Threat | Handling |
|---|---|
| The frame puts a known fix-changed method under every test, so "a small edit fixes it" may be easier here than in the wild | stated; Stage C cannot remove it; a control set of failures on non-buggy methods is listed in the dataset plan |
| D1-test labels were used to design earlier rules | Stage A is labelled exploratory; Stage C is the test |
| Mutation operators resemble the D2 construction (Major mutants) | D2 is **not** used to evaluate the probe: a one-line mutant of the fixed version is, by construction, one edit from a passing state, so D2 would be circular |
| Sibling tests are generated from buggy code | flip and rcf are both reported; the dev pilot already showed the filter removes true fixes |
| Overfitting patches | a flip is treated as evidence with a measured false-positive rate, never as proof |
