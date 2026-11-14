# WDP retrospective evaluation: interpretation review

Date: 2026-11-14. **Status: exploratory; retrospective; protocol frozen internally in Git before the run (freeze
commit `08ec9af`, manifest `bae8ad9a4d3ddbbf0f0149dd97e8c3f59aaa16f3dd9441d4fb47491cc2bb06cd`); not externally
preregistered; designed after the confirmation outcomes were known.** Nothing here changes any registered result of
the CFP confirmation (OSF kp79c).

Reviewer: Claude Opus 5.5, in the session the authors switched to that model. The original mandate assigned this
review to Claude Fable 5.2; the authors may want a Fable pass before the text goes into the paper.

Sources: `results/extension/wdp/wdp_analysis.json` (frozen analysis, run unchanged),
`docs/research_extension/generated/wdp_report.md`, `results/extension/wdp/run_status.json`. Interpretation rules
applied: `OPUS_EXECUTION_BRIEF.md` section 7, fixed before the run.

## 1. Did the run qualify for interpretation?

| Gate | Result |
|---|---|
| Authorisation | D-151 committed (`89cd8e5`) with the approval file before any run |
| One invocation per run, within the window | yes: 07:15–07:33 UTC (12:15–12:33 +05:00); no retry |
| Completeness | all four ledgers complete (369, 160, 428, 246 records; none missing, duplicated or extra); committed (`7453b84`) before the analysis |
| Frozen code | freeze check passes before and after; each run's metadata names approved commit `08ec9af` and execution commit `89cd8e5` |
| Marker consistency over every raw record | 0 violations (surfaced throws: D1-test 285, F1 143, F2 223, CTRL 151) |
| Technical ND | 0 in D1-test, F1, CTRL; 17 in F2 (4.1%, below the 5% cap), all `no_x_ret` |
| Malformed records, exclusions | 0, 0 |
| Registered rows reproduced | KUU, KUU + CD, 2-of-3 equal the registered analysis to four decimals |
| Populations | as specified (CONF-votes 561 / 54 PF; PILOT-votes 177 / 60 PF; CTRL 246) |

All quality checks pass, so both the primary criterion and the descriptive ladder may be reported.

Note on run metadata: each `run_meta.json` lists about 45 paths as modified in `worktree_dirty_paths`. That list
was produced by git inside WSL, which reads CRLF working-tree copies of LF-committed files as modified (the D-144
effect). Every listed file checked differs from its committed blob only in line endings, and the confirmation's
label and instance files still match, byte for byte, the hashes sealed in its concat manifest on 13 November.

## 2. Primary criterion: MET

On the 561 confirmation tests with three judge votes (54 bug-revealing, 21 bugs with one):

| Quantity | Value |
|---|---|
| ΔTNR, KUU + CD-U minus KUU | **+0.104**, 95% bug-level CI [0.037, 0.201] |
| ΔTPR | 0.000 [0.000, 0.000] |
| Bugs lost: KUU / KUU + CD-U | 0 / 0 (no additional bug) |
| `Math_59`'s decoupled bug-revealing test | level **WS** (predicted WS; required not U) |

All three conditions of the criterion hold: (i) no additional bug lost; (ii) the interval's lower limit is above 0;
(iii) `Math_59` is not level U.

Secondary checks of the same claim:

- **Pilot** (177 tests with votes, 60 bug-revealing, 22 bugs): ΔTNR +0.060 [0.008, 0.143], no additional bug lost
  (KUU's existing loss, `Codec_9`, is unchanged). The pilot's lost bug under the registered certificate, `Codec_13`,
  is level **WS**.
- **Pooled bound** (the brief's rule, computed only because both conditions held): 0 additional bugs lost of 43
  bugs with a bug-revealing test; one-sided 95% upper bound 0.067. **The rule was designed with knowledge of these
  bugs, so the bound is optimistic and is not a guarantee.**
- **Against the registered certificate** (KUU + CD): TNR −0.010 [−0.071, 0.043], one bug fewer lost (`Math_59`
  kept). CD-U keeps CD's test-fault removal and removes its bug loss in this sample.

## 3. What level U is in these data

| Data | Bug-revealing tests at U | Wrong tests at U | P(U \| TF) − P(U \| PF) |
|---|---|---|---|
| Confirmation F1 + F2 | **0 of 55** | 171 of 517 | +0.331 [0.192, 0.479] |
| Pilot D1-test | **0 of 60** | 57 of 296 | +0.193 [0.073, 0.335] |
| Control (all TF) | — | 64 of 246 | — |

No bug-revealing test in either sample reached level U.

**How the registered `decoupled` flag splits** (wrong tests):

| | U | RI | WS | ND |
|---|---|---|---|---|
| Confirmation (135) | **112** | 16 | 5 | 2 |
| Pilot (61) | **49** | 10 | 2 | 0 |
| Control (46) | **41** | 3 | 2 | 0 |

The two bug-revealing tests the registered flag ever caught are both WS. Brief section 7 fixed the reading for this
outcome before the run, and it applies: **most of what survived of CFP's decoupling signal is an entry check —
"the method under test was not entered and the failure is unchanged when it throws" — obtainable with one extra
execution per test.** The mutation machinery is not what carries it.

**The ten-mutant minimum's stratum** (tests the registered flag could never decide): confirmation bug-revealing
19 → WS 17, ND 2, U 0; wrong 83 → U 59, WS 7, RI 4, ND 13. WDP decides most of these, again with no bug-revealing
test at U.

## 4. Where the gain comes from: the same concentration as C2

| Subset | Wrong tests at U | ΔTNR [95% CI] | Additional bugs lost |
|---|---|---|---|
| F1 | 8 of 119 | +0.034 [0.000, 0.130] | 0 |
| F2 | 163 of 398 | +0.126 [0.041, 0.244] | 0 |
| Without both Jackson projects | 18 of 288 | +0.046 [0.009, 0.101] | 0 |
| Leave one project out | range +0.043 (JacksonDatabind removed) to +0.137 | | 0 in every case |

The gain is real outside the two Jackson projects (interval above zero) but about a third of its pooled size, and in
F1 the interval reaches zero. As with C2, the pooled +0.104 is a mixture, not an effect size that transfers across
frames or projects.

## 5. Practical reading

| Rule (561 confirmation tests) | TPR | TNR | Bugs lost | Kept | Judge calls |
|---|---|---|---|---|---|
| keep-all | 1.000 | 0.000 | 0 | 561 | 0 |
| keep-all + CD-U | 1.000 | 0.337 | 0 | 390 | **0** |
| KUU | 1.000 | 0.316 | 0 | 401 | 3 per test |
| KUU + CD-U | 1.000 | 0.420 | 0 | 348 | 3 per test (513 avoidable for the 171 U tests) |
| KUU + CD (registered) | 0.982 | 0.430 | 1 | 342 | 3 per test |

- In this sample, the model-free rule keep-all + CD-U removed slightly more wrong tests than the three-judge KUU
  baseline (0.337 against 0.316) with no bug lost. That comparison was not a pre-specified contrast and has no
  interval here; report it as a descriptive observation.
- At an assumed 5% prevalence of bug-revealing tests, a developer would read about 11.0 wrong tests per
  bug-revealing test kept under KUU + CD-U, against 13.0 under KUU.
- Cost: about 0.5 s and 3.5 test executions per failing test (first-order probes: about 2 s), no model call, no GPU.

## 6. What may and may not be written

**May be written** (brief section 7, criterion met, no additional bug lost on the pilot):

> In an exploratory, retrospective evaluation, discarding failures for which no entry into the method under test
> was observed and which were unchanged when that method was made to throw removed 10.4 percentage points more wrong
> tests than KUU (95% CI 3.7 to 20.1) with no additional bug lost on 21 confirmation bugs and 22 pilot bugs with a
> bug-revealing test, at no model cost. The gain was concentrated in one sampling frame and two projects (+4.6
> points without them), and most of the signal is an entry check rather than a mutation effect.

Always with: TPR, TNR and bugs lost; the pooled bound 0.067 **with its caveat**; the status sentence; the frame and
project concentration; that level U is "no entry observed and throw-invariant", an operational observation.

**May not be written:** "validated", "safe", "guarantee", "confirms", "held-out", "unreachable"; any comparison with
published numbers from other samples; that the rule generalises across frames or projects; that it was
pre-registered.

## 7. Limits that bound this result

1. **Designed with knowledge of the outcome.** Level U, the certificate and criterion (iii) were defined after both
   lost bugs (`Codec_13`, `Math_59`) and the confirmation's labels were known. That the two lost bugs are now WS is
   what the design aimed at, not independent evidence; the informative parts are the 0-of-115 bug-revealing tests at
   U and the 102 previously undecided tests.
2. **Small and concentrated.** 21 + 22 bugs with a bug-revealing test; the gain is mostly F2 and two projects.
3. **Mostly an entry check.** A reviewer can fairly say the surviving signal needs one execution, not mutation.
4. **One benchmark, one generator, one language.**
5. **A fresh, registered test is needed** before any claim beyond this sample (tests no probe or judge has seen,
   e.g. a second generator); external registration only with the authors' approval.

## 8. Recommendation for the paper and deck

Replace the WDP placeholder in `phase4_v2/` with a short exploratory subsection and one slide: the ladder table, the
criterion result in the words of section 6, the concentration table, and the limits of section 7, under the full
status sentence. This review recommends it; the authors decide.
