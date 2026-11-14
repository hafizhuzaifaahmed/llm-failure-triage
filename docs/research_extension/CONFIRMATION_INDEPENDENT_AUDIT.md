# Independent audit of the CFP confirmation (OSF kp79c)

Date: 2026-11-13. Auditor: lead research model (Fable 5.2), read-only. Repository state audited: branch
`research-extension`, HEAD `3b017f2`, working tree clean.

**Scope.** This audit checks the completed confirmation; it changes no registered result, label, ledger, vote or
script. Everything in sections 3 to 6 that is not in the registration is **exploratory** and is marked so.

**Method.** The registered quantities were recomputed from the per-tranche raw records
(`data/extension/confirm/{F1,F2,CTRL}/labels_*.jsonl`, `instances_*.jsonl`, `votes/*/decisions.jsonl`,
`results/extension/probes/CFP_CONF_{F1,F2,CTRL}/ledger.jsonl`) with code that imports no project module: its own
bug-level bootstrap (10,000 multinomial resamples, a different seed), its own Holm step, its own rule functions and
its own Clopper–Pearson bound. The frozen script was read line by line but not re-run.

## 1. Verdict in five lines

1. **Arithmetic and code: validated.** Every count, estimate, interval, p-value, Holm adjustment, rule row and bound
   in `generated/confirm_report.md` reproduces from raw records. No discrepancy between prose, JSON, script and
   ledgers was found.
2. **Chronology: validated.** Labels were committed before probes ran, ledgers before votes started, and the
   analysis script hash is unchanged since the freeze.
3. **C1 (flip): the non-replication is robust**, not an artefact of one bug or of the power shortfall. The interval
   excludes the pilot's effect; it does not exclude an effect half that size.
4. **C2 (decoupling): supported as registered, but the pooled effect is carried by two projects.** 117 of the 135
   decoupled test faults are in JacksonDatabind and JacksonCore. Without them the estimate is +0.041
   [−0.035, 0.108]. The registered interval resamples bugs, not projects, and does not express this.
5. **C3, C4: inconclusive, and the keep certificate (CK) shows no discriminating power in this sample**
   (`rcf` set for 4 of 55 PF and 32 of 517 TF tests).

## 2. Audit matrix

Severity: **none** = verified, no issue; **wording** = result stands, the paper's wording must carry a qualifier;
**major** = result stands, but an unqualified statement of it would mislead.

| # | Claim or result | Governing definition | Raw source | Code path | Independent check | Result | Severity | Implication for wording |
|---|---|---|---|---|---|---|---|---|
| 1 | 572 scored tests, 55 PF, 517 TF, 104 bugs, 21 with a PF test | Registration, Analysis plan: all scored F1 and F2 failures | per-tranche `labels_*.jsonl` | `confirm_analysis.py` `population()` | recount from tranche files | identical; F1 155 (36/119, 28 bugs, 12 with PF), F2 417 (19/398, 76 bugs, 9 with PF); no bug in both frames | none | "104 bugs" are bugs with at least one scored failing test, out of 322 frame bugs; say so |
| 2 | Labels F1 36/119/5 AMB, F2 19/398/11 AMB, CTRL 246 TF | Registration step 3 | same | labelling driver (D-142) | recount | identical | none | — |
| 3 | No overlap with bugs the original study generated for | Registration, Existing data | `data/ground_truth_store/labels_D1.jsonl`, frame | `build_confirm_frames.py` | set intersection of bug names | 0 of 322 frame bugs appear among the 92 originally labelled bugs | none | — |
| 4 | Ledger flags follow from the mutant records | `ledger.summarise` | ledgers (834 records) | `ledger.py` | flags recomputed from each record's mutant list | 0 mismatches | none | — |
| 5 | Concatenated analysis inputs equal the tranche originals | D-142 | `ALL/concat_manifest.json` | concat driver | sha256 of all 15 sources | 0 mismatches | none | — |
| 6 | C1 = +0.028 [−0.137, 0.274], p 0.7685 | P(flip\|PF) − P(flip\|TF) | ledgers, labels | `rate_contrast(+1)` | own bootstrap | +0.0282 [−0.138, 0.274], p 0.78 | none (arithmetic) | see section 3 |
| 7 | C2 = +0.243 [0.114, 0.372], p 0.0006 | P(dec\|TF) − P(dec\|PF) | same | `rate_contrast(−1)` | own bootstrap | +0.2429 [0.115, 0.372], p 0.0002 | none (arithmetic); **major** (interpretation) | see section 4 |
| 8 | C3 = +0.048 [0.001, 0.099], p 0.0474 | BA(KUU+CD) − BA(KUU), tests with three votes | votes, ledgers | `rule_metrics`, paired weights | own rules and bootstrap | +0.0479 [0.001, 0.099], p 0.044 | wording | the unadjusted p sits on 0.05 and moves with the bootstrap seed (0.047 vs 0.044); never call it significant |
| 9 | C4 = −1 [−3, 0], p 0.7375 | PF lost by 2-of-3+CK minus 2-of-3 | same | same | same | −1 [−3, 0], p 0.72 | none | inconclusive |
| 10 | Holm: 1.000, 0.0024, 0.1422, 1.000 | one family C1–C4, α 0.05 | — | `stats.holm` | by hand: 4×0.0006, 3×0.0474, then capped at 1 | identical | none | — |
| 11 | Bootstrap unit and pairing | bug-level cluster bootstrap, identical resamples for paired differences | — | `stats.bootstrap_weights`, `W[:, bidx]` | code read | one weight matrix per analysis, shared by both arms of C3 and C4; p uses (+1)/(B+1) | none | percentile intervals from 21 PF-bearing clusters can under-cover (section 6) |
| 12 | Missing votes | Registration, Missing data | `decisions.jsonl` | `vsel`, `rm.k_of_n` | recount | 561 with three votes (54 PF); 11 without (10 TF, 1 PF, `Compress_35`); the same 11 ids for all three judges, each with a refusal in `votes/<run>/leakage_rejections.jsonl` (the `guard_D1C_*.jsonl` files hold guard inputs, not outcomes); 1 INVALID vote in 1,683, treated as not a discard vote | none | — |
| 13 | Rule table (7 rows) | `policy.py`, registration | votes, ledgers | `keepvec` | own rule functions | all TPR, TNR, BA, PF lost, bugs lost identical | none | — |
| 14 | Bug-loss upper bounds 0.133 / 0.207 / 0.329 / 0.384 | exact one-sided 95% | — | `bugs_lost` (beta quantile) | own binomial inversion | identical for 0, 1, 3, 4 of 21 | none | — |
| 15 | Control: 246 TF, 0 PF, 59 bugs; flip 0.220 [0.137, 0.321]; decoupled 0.187 | Registration, Control group | CTRL records | control block | own bootstrap | 54/246 = 0.2195 [0.138, 0.323]; 46/246 = 0.187 | none | section 5 |
| 16 | F1 and F2 separately | Secondary analysis 7 | same | same script per frame | own computation, own seed; then the registered seed (row 22) | F1 C1 −0.122, C2 +0.039; F2 C1 +0.125, C2 +0.319: identical. Intervals under a different seed agree to the third decimal **except two C1 upper limits**: F1 0.270 against the registered 0.279, F2 0.408 against 0.413 (corrected 2026-11-13 after the P1 replication; an earlier version of this row wrongly said all agreed to the third decimal) | none (arithmetic); wording | per-frame interval limits carry Monte Carlo error of about ±0.01; print them to two decimals |
| 22 | Registered intervals under the registered seed | seed 20261011, 10,000 multinomial bug resamples | same | `stats.bootstrap_weights` | the same random stream generated independently (`audit_scripts/audit_seedcheck.py`), plus 20 other seeds | **exact reproduction, to four decimals, of all six intervals**: pooled C1 [−0.1372, 0.2735], C2 [0.1140, 0.3723]; F1 C1 [−0.3229, 0.2786], C2 [−0.0833, 0.1563]; F2 C1 [−0.1257, 0.4133], C2 [0.1738, 0.4682]. Across 20 other seeds the F1 C1 upper limit ranges 0.251–0.276 (sd 0.007), F2 C1 0.403–0.427 (sd 0.006), pooled C1 0.268–0.283 (sd 0.004), pooled C2 0.369–0.377 (sd 0.002) | none | the gap in row 16 is seed variation, not a discrepancy |
| 23 | Labels follow from the raw runs | Registration step 3 | `executions/*.json`, both versions | labelling driver | fresh rule implementation (P1 check A2: seeded sample of 60; then every labelled instance) | 60 of 60; then **834 of 834** labels and both stored signatures equal, including all 55 PF and all 16 AMB | none | — |
| 17 | Engine exclusions 0 | Registration, Data exclusion | ledgers | `usable` | recount | 0 excluded in all three tranches | none | but 125 of 572 tests have fewer than ten compiled mutants (section 4.3) |
| 18 | Sealing order | Registration steps 4–6 | git log, `votes.log` | — | timestamps | labels commit `1a58e54` 12:09:02 +05; ledger commit `b332305` 12:52:40; first vote call 12:53:41 (07:53:41Z); analysis `3b017f2` 14:09:50 | none | — |
| 19 | Frozen files unchanged | `cfp_frozen.json` | — | `tests/extension/test_freeze.py` | test run at HEAD | 5 passed | none | — |
| 20 | "C1 adequately powered: counts against" | Registration classification at ≥30 bugs | — | `confirm_report.py` | planning table re-read | realized 21 bugs; realized interval half-width 0.206 equals the planned median at 30 bugs (0.204) | wording | section 3 |
| 21 | Counting-against item 4 marked "yes" | Registration: "close", no threshold | — | `confirm_report.py` | — | a judgement, not a computation | wording | section 5 |

Rows added after the P1 replication (checks A6–A8 by the execution model, `results/extension/audit/A6_A8.md`;
accepted by the authors in their review of freeze commit `3c59196`):

| # | Claim or result | Independent check | Result | Severity | Implication for wording |
|---|---|---|---|---|---|
| 24 | Ledger flags follow from the mutant records (row 4) | A6: flags recomputed from each record's mutant list, without the project's ledger module | 0 mismatches in 834 records | none | — |
| 25 | Concatenated inputs equal the tranche originals (row 5) | A7: sha256 of the 15 sources | 0 mismatches | none | — |
| 26 | Sealing order (row 18) | A8: commit times and run logs | 9 of 9 checks pass: labels commit 07:09:02Z, first probe 07:10:05Z; ledger commit 07:52:40Z, first vote call 07:53:41Z; no later commit touches the label or ledger files | none | a commit or log time shows order of recording, not when a file was written or read; say "committed before", not "could not have been read" |
| 27 | "The probe engine has no code path to the fixed version, to labels or to developer tests (enforced by a unit test that scans its source)" | Registration, Blinding; `tests/extension/test_cfp.py`; direct search of `src/triage_ext/*.py` and `run_probes_tranche.py` | **The property holds; the test is weaker than stated.** Three of the test's forbidden patterns (`runs_f`, `compile_f`, `meta_f`) contain literal backspace characters and can never match. A direct search finds none of those names, nor any label or fixed-version path, in the engine or its driver. The other patterns of the test are effective | wording | write "verified by inspection and by a source scan" and note that three of the scan's patterns were ineffective; the test file is left untouched until after the deadline |

## 3. C1: what the failed replication does and does not show

Registered result: +0.028 [−0.137, 0.274], Holm p 1.000, not supported.

| Check (exploratory) | Result |
|---|---|
| Pilot estimate inside the confirmation interval? | No. The pilot's 0.511 is far above the upper limit 0.274 |
| Half the pilot's effect (0.256) inside? | Yes, just below the upper limit |
| One bug's weight | `Lang_57` supplies 13 of the 55 PF tests, and its method has **zero** compilable mutants, so those 13 can never flip. This is the registered handling (flags false), and it is conservative |
| Without tests that have no mutant | PF 14/42 (0.333) against TF 117/504 (0.232). F1: 8/23 (0.348) against 41/119 (0.345). F2: 6/19 against 76/385 |
| Bug level | 8 of 21 PF-bearing bugs have a flipping PF test; 41 of 83 bugs with only wrong tests have some flip |
| As a ranking score | share of mutants that flip: AUROC 0.526 (pilot: 0.779) |
| Keep certificate `rcf` | 4/55 PF (0.073) against 32/517 TF (0.062); F1: 0/36 against 14/119 |
| Pilot re-read by project | 20 of the pilot's 40 flipping PF tests were in Chart (20/20); Math had 0/11. The pilot effect was concentrated in one project that contributes no PF test here |

Reading. The confirmation rules out an effect of the pilot's size. It does not rule out a small positive effect;
the realized precision is what the planning expected at 30 bugs, so the shortfall to 21 bugs did not widen the
interval beyond plan. In F1, the frame built by the pilot's own rule, the two rates are equal once tests without
mutants are set aside (0.348 against 0.345). The registered reading ("counts against the method") stands and is
stated with the D-145 qualifier; the additional statement the data support is: *a flip is about as common for wrong
tests (0.226), control failures (0.220) and bug-revealing tests (0.255), so it carries no usable evidence of fault
side in this sample.* Do not write "no effect exists".

## 4. C2: supported, with three qualifiers the paper must carry

Registered result: +0.243 [0.114, 0.372], Holm p 0.0024, supported. 135 of 136 decoupled tests are test faults.

### 4.1 Frame heterogeneity (registered secondary analysis 7, plus an exploratory contrast)

| Frame | Decoupled among TF | Decoupled among PF | C2 [95% CI] |
|---|---|---|---|
| F1 | 8/119 (0.067) | 1/36 | +0.039 [−0.083, 0.156] |
| F2 | 127/398 (0.319) | 0/19 | +0.319 [0.174, 0.468] |
| F2 − F1 (exploratory; frames share no bug, independent resamples) | | | +0.280 [0.089, 0.469] |

The frames differ by more than sampling noise. The pooled estimate is a mixture, not a common effect.

### 4.2 Project concentration (exploratory; this is the main qualifier)

| Subset | Tests (PF) | Decoupled TF | Decoupled PF | C2 [bug-level 95% CI] |
|---|---|---|---|---|
| All | 572 (55) | 135 | 1 | +0.243 [0.115, 0.372] |
| Without JacksonDatabind | 361 (52) | 33 | 1 | +0.088 [−0.007, 0.204] |
| Without JacksonCore | 546 (50) | 120 | 1 | +0.222 [0.092, 0.354] |
| Without both Jackson projects | 335 (47) | 18 | 1 | +0.041 [−0.035, 0.108] |
| Project-stratified (Mantel–Haenszel weights) | | | +0.149 |
| Resampling projects instead of bugs (12 clusters; indicative only) | | | [0.032, 0.426] |

- Six bugs hold 92 of the 136 decoupled tests (JacksonDatabind_90, _70, _30, _53, _61 and JacksonCore_7).
- The two Jackson projects hold 229 test faults and only 8 bug-revealing tests. The pooled contrast therefore
  compares mostly Jackson wrong tests with mostly Lang and Math right tests.
- The registered leave-one-project-out range (+0.088 to +0.300) is correct; its lower end is "JacksonDatabind
  removed", and the report gives it without an interval.
- The pilot did not have this pattern: outside Jackson its wrong tests were decoupled at 45/230 (0.196); here the
  figure is 18/288 (0.063). The *yield* of the flag did not transfer across samples; its *precision* did.

### 4.3 Failure type and eligibility (exploratory)

| Failure (type, deepest stack frame) | PF: n / decoupled | TF: n / decoupled |
|---|---|---|
| assertion failure | 28 / 1 | 299 / 42 |
| exception, deepest frame in the method under test | 21 / 0 | 58 / 11 |
| exception, deepest frame in other program code | 6 / 0 | 67 / 41 |
| exception, deepest frame in the test | 0 / 0 | 93 / 41 |

- F1's wrong tests are 93% assertion failures; F2's are 53% exceptions. Decoupling lives where an exception is
  raised outside the method under test (82 of 160 such TF, 0 of 6 such PF). This composition explains much of the
  frame difference.
- The flag is not a restatement of the stack trace: the rule "exception not raised in the method under test" would
  discard 6 PF tests and 160 TF; the decoupled flag discards 1 and 135.
- Fewer than ten compiled mutants (flag can never be set): 21 of 55 PF tests and 104 of 517 TF tests. Among tests
  that could be flagged the contrast is +0.298 [0.130, 0.462].
- **19 PF tests and 83 TF tests have fewer than ten mutants and no mutant that changes the failure.** They escape
  the certificate only through the ten-mutant minimum (13 of the 19 are `Lang_57`, whose method has no mutant).
  The minimum is doing safety work that the registration describes as a definitional detail.
- The one decoupled PF test is `Math_59` (`FastMath.max(float,float)`, assertion failure) with **exactly ten**
  compiled mutants. The guarded variant (secondary analysis 2) does not protect it, because the failure is not an
  exception. The pilot's lost bug (`Codec_13`) and this one are both faults outside what the six operators can
  touch.

Reading. "Supported" stands as the registered outcome. The defensible summary is: *a failure that no single edit
changes was a test fault in 135 of 136 cases; how often the flag fires depended strongly on the sampling frame and
on the project (0.067 of wrong tests in F1, 0.319 in F2, and 117 of 135 in two projects).* The paper must not
present +0.243 as an effect size that transfers.

## 5. C3, C4, rules and the control group

| Rule (561 tests, 54 PF, 21 PF-bearing bugs) | TPR | TNR | Kept tests (PF among them) | Bugs lost |
|---|---|---|---|---|
| keep-all | 1.000 | 0.000 | 561 (54; precision 0.096) | 0 |
| KUU | 1.000 | 0.316 | 401 (54; 0.135) | 0 |
| KUU + CD | 0.982 | 0.430 | 342 (53; 0.155) | 1 (`Math_59`) |
| 2-of-3 | 0.870 | 0.521 | 290 (47; 0.162) | 4 |
| 2-of-3 + CK | 0.889 | 0.501 | 301 (48) | 3 |

- **C3.** The gain is +0.016 in F1 (with the one lost bug) and +0.065 in F2 (no loss). It is a trade: 58 more wrong
  tests discarded for one bug-revealing test and its bug. Holm p 0.142: inconclusive. The paired difference in bugs
  lost is +1 on 21 bugs; the exact bound on KUU + CD's bug-loss rate is 0.207.
- **C4.** CK recovered one PF test (`Time_17`) and kept 10 more wrong tests. With `rcf` at 0.073 for PF and 0.062
  for TF there is no evidence the certificate separates anything. Inconclusive as registered; exploratory reading:
  no support.
- **Judges** (exploratory, for context): M1 TPR 0.593 / TNR 0.746; M2 0.926 / 0.458; M3 0.870 / 0.477. Number of
  program-fault votes as a score: AUROC 0.772; putting decoupled tests last raises it to 0.787 (F1 0.722 → 0.729;
  F2 0.748 → 0.784).
- **Votes and the flag overlap.** Of 135 decoupled TF tests with votes, 77 were already unanimous test-fault votes,
  which KUU discards without the probe. 58 are added by CD.
- **Control group.** 246 failures, all TF, from 59 of the 246 control bugs. No control test revealed the fault. Flip
  0.220 [0.137, 0.321]; decoupled 0.187. The control flip rate, the F1/F2 TF rate (0.226) and the PF rate (0.255)
  are indistinguishable. The registration's fourth counting-against item has no numeric threshold; the report marks
  it "yes" because the PF rate lies inside the control interval. That is a reasonable reading and must be reported
  as a reading: the paper should print the three rates and the absence of a threshold, not the word "met" alone.
  The control says nothing about defect-free code: its methods are methods the patch did not change, in classes
  that needed a fix.

## 6. Limits of the statistical procedure itself

1. **Few PF-bearing clusters.** 21 bugs carry the PF tests and one of them carries 24% of them. Percentile cluster
   bootstrap intervals are known to under-cover with few and unequal clusters. All intervals involving a PF rate
   (C1, C2, C3) should be read as approximate. A delete-one-bug jackknife with a normal interval (P1 check A3)
   gives C1 [−0.199, 0.255] (standard error 0.116) and C2 [0.109, 0.377] (0.068): wider than the bootstrap at C1's
   lower end, the same for C2. Neither changes a reading.
   Interval limits also carry Monte Carlo error from the 10,000 resamples (row 22): across seeds the standard
   deviation of a limit is 0.002–0.004 for the pooled intervals and 0.006–0.007 for the per-frame C1 upper limits.
2. **Only bugs are resampled.** Projects are a second level of clustering (section 4.2). No registered interval
   reflects it.
3. **Two-sided p for directional hypotheses.** Conservative; no issue.
4. **Power.** The planning classified C1 from a simulation at 30 bugs or more. At 21 bugs C2, C3 and C4 are further
   below the planning than registered; their non-support (C3, C4) remains inconclusive, and C2's support came
   despite it.

## 7. Corrections to interpretation (not to registered results)

| # | Where | Now | Should read |
|---|---|---|---|
| 1 | C1 | "adequately powered: counts against the method" | keep, with the D-145 note, and add: the interval excludes the pilot's estimate (0.511) and includes half of it (0.256) |
| 2 | C1 | flip rates only | add that 13 PF tests (one bug) have no mutant, and the rates without mutant-less tests (0.333 against 0.232; F1 0.348 against 0.345), marked exploratory |
| 3 | C2 | "supported" | "supported in the pooled registered analysis; not reproduced in F1; 117 of 135 decoupled test faults lie in two projects; +0.041 [−0.035, 0.108] without them (exploratory)" |
| 4 | C2 | leave-one-project-out range without intervals | name the project behind the lower end and give its interval |
| 5 | C3 | p 0.0474 shown beside the estimate | state Holm p first; add that the gain comes with one lost bug and arises in F2 only |
| 6 | C4 / CK | "inconclusive" | add the `rcf` rates by label; do not describe CK as promising |
| 7 | Rules | balanced accuracy as the summary | lead with (TPR, TNR, bugs lost); balanced accuracy hides a lost bug |
| 8 | Control | "counts against: yes" | three rates, no registered threshold, the reading stated as a reading |
| 9 | Population | "104 bugs" | "104 of the 322 frame bugs produced a scored failing test" |
| 10 | Mutant minimum | a definition | a safety-relevant parameter: it shields 19 PF tests |
| 11 | Prior work (`LITERATURE_VERIFICATION_FULLTEXT.md` entry 17) | "does not state whether a test must pass on one, most or all patches" | e-Otter++ §3.3 keeps tests that are fail-to-pass on **any** patch (re-read 2026-11-13) |

## 8. Read-only checks assigned to Opus

These are independent replications of this audit, not new analyses. None may write under `results/extension/confirm`,
`data/extension/confirm` or any frozen path.

| ID | Check | Expected |
|---|---|---|
| A1 | Re-run this audit's three scripts (`docs/research_extension/audit_scripts/audit_recompute.py`, `audit_robustness.py`, `audit_pilot.py`; they import no project module and write only the path given as their output argument) and store their stdout under `results/extension/audit/` | every figure in sections 2 to 5 of this file |
| A2 | Recompute labels for a seeded sample of 60 instances (20 per tranche, seed 20261113) directly from the execution records (`executions/*.json`, runs on both versions) with a fresh implementation of the label rule in the paper's Section 3.3 | 60 of 60 equal the stored labels |
| A3 | Recompute C1 and C2 with a cluster-robust alternative: a bug-level permutation of the PF/TF label within project is not valid here (labels are test-level), so use the delete-one-bug jackknife standard error and a normal interval | intervals of similar width to the bootstrap; report both |
| A4 | Verify that the 11 tests without votes are the same 11 in all three judges' logs and that each has a guard refusal record | 11 common ids; 10 TF, 1 PF |
| A5 | Verify `git diff 3b017f2 --stat -- src/triage_ext scripts/extension/confirm_analysis.py scripts/extension/run_probes_tranche.py configs/extension/confirm_frame.jsonl` is empty at the time of any new run | empty |

If any expected value fails, stop and report; do not proceed to the extension.

## 9. Outcome of the P1 replication (2026-11-13) and the lead model's adjudication

Opus ran A1–A5 and reported **`P1 RESULT: FAIL`** (`results/extension/audit/P1_SUMMARY.md`, left as written).

| Check | Outcome |
|---|---|
| A1 counts, point estimates, rule rows, bounds, Holm | all identical |
| A1 pooled intervals | within the third decimal |
| A1 per-frame intervals | **two C1 upper limits differ in the second decimal** (F1 0.270 vs 0.279; F2 0.408 vs 0.413). This contradicted row 16 of this file as first written, and is the reason for the FAIL |
| A2 | 60 of 60 labels and signatures |
| A3 | computed (section 6) |
| A4 | the same 11 tests for all three judges, 10 TF and 1 PF; refusals found in `leakage_rejections.jsonl`, not in the guard file as this file had assumed |
| A5 | empty diff; freeze tests pass |

Adjudication (`results/extension/audit/P1_ADJUDICATION.md`):

1. **The registered results are not in question.** With the registered seed, an independent implementation
   reproduces every registered interval exactly (row 22). The two limits that differed are bootstrap seed
   variation, of the size expected with 12 and 9 PF-bearing bugs.
2. **The error was in this audit's wording**, which overstated the agreement of its own different-seed intervals.
   Row 16 is corrected, and correction 12 is added below.
3. The A4 expectation named the wrong file; row 12 is corrected.
4. Follow-up to A2's thin PF coverage (4 PF tests in the sample): the same fresh rule applied to every labelled
   instance gives 834 of 834 (row 23).
5. Whether P1 is treated as passed for the purpose of the freeze (brief step P3) is the **authors' decision**
   under stop condition 1. The lead model's recommendation is to accept it with these corrections.

Correction 12 to section 7: *per-frame interval limits are to be printed to two decimals, with a note that
bootstrap limits carry Monte Carlo error; the registered values are printed as registered.*

Decisions recorded afterwards: the authors accepted P1 as passed for the scope A1–A5
(`results/extension/audit/P1_AUTHOR_ACCEPTANCE.md`), and accepted checks A6–A8 (rows 24 to 26) in their review of
freeze commit `3c59196`. Row 27 was found during that implementation and adds correction 13: *the blinding
statement is worded as in row 27.*
