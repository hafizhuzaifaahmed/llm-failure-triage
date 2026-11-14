# Gap analysis: the scientific bottleneck

Written before any held-out probe result was read. Evidence paths are in `EXPERIMENT_AND_RESULT_MAP.md` and
`LIMITATIONS_AND_OPEN_QUESTIONS.md`.

## 1. Bottlenecks, ranked

### B1. Every method reads one static failing run; none can ask the program a second question

- **Repository evidence.** All arms, KUU, the cascades and the learned baselines consume the same evidence package
  built from `runs_b[0]` (`CURRENT_ARCHITECTURE.md` §2). Removing the failure section drops the judges to chance
  (A4, Table B3), so the one run they see is where all their signal comes from. Changing how the judges *deliberate*
  over that run (voting, debate, a third family, a learned combiner over votes) moved rules along one trade-off curve
  and not off it (Tables G1, G3, G4; Fig. 2). On assertion failures, the largest stratum, cross-family unanimity
  removes 5 of 72 test faults (`ext0_error_strata.json`).
- **Literature evidence.** The two closest industrial and academic systems (Meta's catching-test judges; Wang et
  al.'s validator) also read a fixed package. The only evidence-gathering oracles found are in other domains
  (LogicHunter, FalseCrashReducer). `NOVELTY_COLLISION_CHECK.md` C1, C3.
- **Why it matters.** Deciding PF against TF is a question about intent. A failing run shows that expectation and
  behaviour differ; it does not show which is wrong. More opinions about the same observation cannot add information
  that the observation lacks.
- **Solved when.** A rule that uses new execution evidence reaches a point above the existing TPR–TNR frontier of the
  local rules on real faults, with a bug-level interval excluding zero, on data its design did not see.
- **Falsified if.** Execution-derived evidence is no better than chance at separating PF from TF, or adds nothing to
  the judges once combined (the pattern the cheap failure features showed: AUROC 0.554, Table G3).

### B2. Too few independent bugs to confirm anything on real faults

- **Repository evidence.** 22 bugs carry D1-test's 60 bug-revealing tests; no confirmatory test survived correction;
  about 257 bugs are needed for an MDE of 0.08 on the debate contrast (Table G5).
- **Literature evidence.** Zhao et al. report 2.09–4.54% effective tests, so real bug-revealing failures are scarce
  by nature; no public labelled set of failing generated tests exists (collision check, C4).
- **Why it matters.** Every method claim on real faults, including any new one, is underpowered at the bug level.
- **Solved when.** A fresh, sealed real-fault set several times larger exists (the 78 capped-out methods first, then
  more generations per method, then a second generator).
- **Falsified if.** Not a hypothesis; a resource constraint.

### B3. The label and the outcome are narrower than the problem

- **Repository evidence.** Fail-on-both is TF even when the test exposes a second real fault (both audit mismatches);
  the lifecycle stops at the triage decision (no repair, no "bug still detected").
- **Literature evidence.** Mathews and Nagappan count bugs lost but have no triage; Meta reports workload but not
  recall. Nobody reports both axes (collision check, C5).
- **Why it matters.** A reviewer in software testing will ask what happens to the suite, not to the label.
- **Solved when.** An independent audit gives the second-fault rate, and a repair stage gives bugs detected after
  triage per policy.
- **Falsified if.** The audit finds the second-fault rate negligible and the order of rules is unchanged end to end
  (then B3 is a scope note, not a bottleneck).

### B4. The judges are below their own gate

- **Repository evidence.** Table G6. Thinking mode helps one family (Table G8) and still fails the gate.
- **Why it matters less than B1.** It is a property of the models available on one laptop, already disclosed, and it
  will be overtaken by better open models without any research contribution. A contribution whose power comes from
  execution rather than from the judge is robust to it.

### B5. KUU and the cascade are operating points, not mechanisms

- **Repository evidence.** At a matched discard rate a single judge's confidence threshold loses 6 tests to KUU's 4
  (Appendix F(c)); learned vote weights move along the same curve; KUU's MCC is below debate's.
- **Literature evidence.** Three-family judging and escalation exist (Meta; Trust or Escalate; REAG).
- **Consequence.** Not a bottleneck to solve but a framing to correct: the paper's "Method" contribution is weak.

## 2. Answers to the questions the brief asked

| Question | Answer from the evidence |
|---|---|
| Does the judge lack diagnostic evidence, or is its reasoning weak? | Both, and they are confounded in the existing data. Reasoning: thinking mode gained ≈0.2 balanced accuracy on the same package. Evidence: nothing but the failure run carries signal, and no rule over votes leaves the frontier. Only B1's experiment separates them |
| Can the judge collect runtime evidence? | No. Nothing is executed at decision time |
| Can an expectation be checked against independent generations? | Tried: agreement among failing generations is uninformative on real faults (AUROC 0.513) |
| Is KUU a conservative point on a familiar trade-off? | Yes (B5) |
| Does the cascade justify its external calls? | Not on the paper's own numbers: Sonnet J1 everywhere is cheaper at a similar MCC; the fully local cascade is within 0.06 balanced accuracy with nothing leaving the machine (post hoc) |
| Is ranking or deferral more useful than a binary label? | As a *formulation*, yes; as a contribution, no: the scores available rank poorly (panel AUROC 0.73–0.76) and calibrated cascades are published |
| Can the system bound the risk of discarding a real bug? | Not usefully with 22 bugs (floor ≈13% at 95% confidence) |
| Are the labels too coarse? | For second faults, yes; size unknown until an independent audit |
| Method, benchmark, or evaluation? | A method contribution is only credible if it brings new evidence (B1). A benchmark contribution (B2, B3) is credible but needs weeks of generation and raters |
| Enough data for an architecture claim? | Enough to *pilot* a mechanism on 22 + 5 bugs; not enough to confirm one |

## 3. The gap, stated once

No published or in-repository method for this task obtains evidence about fault *side* by executing the program under
controlled change. The study's own results say the missing ingredient is evidence, the literature says nobody has
supplied it for this task, and the infrastructure to test it (834 compiled checkouts, a single-test runner, a label
store the probe cannot reach) already exists.
