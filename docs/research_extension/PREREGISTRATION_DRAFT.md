# Preregistration draft: counterfactual program probes on fresh real faults

> **SUPERSEDED on 2026-11-11 by `OSF_PREREGISTRATION_CFP.md` (D-138).** Kept for the record. Its data plan (the 78
> capped-out methods, a target of 60 bugs reached by adding generations) proved infeasible: those methods hold 53
> unseen bugs and extra generations add tests, not bugs.

Draft for the authors. Not registered anywhere. It becomes a registration only when the authors deposit it (for
example on OSF) **before** the first generation call for the new data. Until then it is internal provenance.

## 1. Background and status of prior evidence

A pilot on Defects4J real faults (D-137; 60 bug-revealing and 296 wrong failing tests in 74 bugs) found that a single
edit of the method under test makes a right test pass more often than a wrong one (0.667 against 0.155), and that
failures no edit can change are almost all wrong tests (61 of 62). The labels of that data were known when the rules
were written, so the pilot is exploratory. This study tests the same engine and rules, unchanged, on data that does
not exist yet.

## 2. Data

- **Source.** Defects4J 3.0.1 focal methods selected by the unchanged frame rule (`src/triage/frame.py`).
- **Tranche T1.** The 78 focal methods excluded from the original study by the per-project cap of 25.
- **Tranche T2.** Further generations (4 to 9) for all 312 frame methods. Tests generated in the original study are
  not part of the confirmation set.
- **Generator.** The frozen generator and prompt of `configs/local_models.FROZEN.json`, new seeds.
- **Labels.** The unchanged execution rule. Labels are written to a new label file and committed before any probe or
  judge reads an instance. AMB, flaky, timeout and non-compiling tests are excluded as before.
- **Stopping rule for data collection.** Generate T1 completely, then T2 in whole passes over the frame (one extra
  generation for every method per pass) until the sealed set holds at least 60 bugs with a bug-revealing test or nine
  generations per method are reached, whichever comes first. The count of bugs is read from the label file only; no
  probe or judge result is consulted.
- **Analysis population.** Held-out projects only. Methods of the three development projects are reported apart.

## 3. Procedure

Pinned commit of `src/triage_ext/` (the engine that produced `CFP_D1_TEST`). Operators, cap 80, callee depth 2,
10 s timeout, minimum of 10 compiled mutants, sibling rule and exclusions as in D-134 and D-135.
Base-rule predictions: one-shot votes of M1, M2 and M3 on the frozen server (KUU and the 2-of-3 vote), and the
thinking-enabled M1 one-shot judge at the D-130 configuration.

## 4. Hypotheses (one Holm family, α = 0.05, two-sided bootstrap p)

| ID | Hypothesis | Statistic |
|---|---|---|
| C1 | A flip is more frequent for bug-revealing tests | P(flip \| PF) − P(flip \| TF) > 0 |
| C2 | Decoupling is more frequent for wrong tests | P(decoupled \| TF) − P(decoupled \| PF) > 0 |
| C3 | The decoupling certificate improves KUU | balanced accuracy of KUU + CD minus KUU > 0 |
| C4 | The keep certificate reduces the tests a majority vote loses | PF tests lost by 2-of-3 + CK minus 2-of-3 < 0 |

Safety outcome reported beside C3 and C4, not tested: bugs lost by each rule and its base, with the exact binomial
95% upper bound on the bug-loss rate over bugs with a bug-revealing test.

Each hypothesis is *supported* if its Holm-adjusted p is below 0.05, *not supported* otherwise. A result in the
opposite direction is reported as such.

## 5. Secondary analyses (stated in advance, outside the family)

1. The regression-consistent flip (`rcf`) in place of `flip` in C1.
2. A guarded decoupling certificate that is never applied when the failure is an exception raised inside the method
   under test (suggested by the one bug lost in the pilot).
3. Flips restricted to literal, relational and statement-deletion edits (the pilot's cleanest operators), and flips
   shared with another failing test of the same method.
4. Focal-body-only region.
5. Leave-one-project-out rates for C1 and C2.
6. The flip rate on control failures from non-buggy methods (tranche T3), if generated.

None of these can replace a primary result.

## 6. Statistics

Bug-level cluster bootstrap, 10,000 resamples, a seed committed with this document; identical resamples for paired
differences; p two-sided with the (+1)/(B+1) correction, as in the original study (`src/triage/stats.py`).
An instance without a usable ledger gets the base rule. Invalid judge outputs keep the test under KUU and the vote and
score as discard for the thinking judge, as in the paper.

## 7. Sample size

With 60 bugs carrying a bug-revealing test, zero lost bugs give a 95% upper bound of 4.9% on the bug-loss rate.
For C1, the pilot's difference was 0.511 with a bootstrap interval of [0.252, 0.740] on 22 such bugs. If the standard
error scales as the inverse square root of the number of bugs (an assumption, as in the paper's planning table), 60
bugs give an interval half-width near 0.15, enough to detect a difference of half the pilot's size. No power claim is
made for C3 and C4; the pilot's effects there were small.

## 8. What would count against the method

- C1 or C2 not supported.
- Either certificate raising the number of bugs lost above its base rule by more than one bug in the sealed set.
- A flip rate on non-buggy control methods close to the rate for bug-revealing tests.

## 9. Deviations

Any change to the engine, the operators, the thresholds or the family after the first generation call is a deviation,
recorded in `docs/tracking/DECISIONS.md` before the affected result is computed, and listed in the paper.

## 10. What the authors must decide before this can run

| Item | Needed |
|---|---|
| Compute | several hours of generator time and execution per pass; a study-server session for the judge votes |
| Registration | whether to deposit this document externally (not approved in pass 2) |
| Seed and commit | fixed at deposit time |
