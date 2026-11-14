# Paper restructure plan and venue fit

**The paper was not edited in this pass.** Two reasons. The new result is exploratory, and rewriting the manuscript
around it now would claim more than the evidence supports. And the repository's rules route every number through
`scripts/paper/build_numbers.py`; the extension's numbers are not in that map yet. What follows is the plan and the
exact text changes it implies, for the authors to approve.

## 1. What the paper is today, stated plainly

An execution-grounded measurement of LLM failure triage with small local judges, in which no confirmatory hypothesis
survived correction, followed by a conservative voting rule (KUU) and a cascade that the paper itself describes as an
operating point. Its strongest assets are the label construction, the frozen protocol and the call log. Its weakest
is the "Method" contribution: three-family judging and escalation exist in published work (Meta's catching-test
judges; Trust or Escalate; REAG), and on the paper's own rates KUU sits on the same trade-off curve as a tuned
single-judge threshold.

## 2. Recommended structure: one combined paper, with the method claim replaced

| Option | Verdict |
|---|---|
| Measurement paper only (drop the method claim) | Honest and submittable to an empirical venue now, but thin: inconclusive confirmatory results from sub-gate judges |
| Method paper on the probes alone | Premature: one exploratory run on 22 bugs |
| Benchmark paper | Not yet: the fresh set and the audit do not exist |
| **Combined: the measurement motivates the mechanism, and a registered run on fresh faults validates it** | **Recommended**, once the fresh-fault run exists. The empirical findings (evidence carries the signal; deliberation does not move the frontier) are the reason the mechanism is the right next step, so the two halves make one argument |

Do not split. The measurement without a mechanism is a course-project evaluation; the mechanism without the
measurement has no motivation and no baselines.

## 3. Proposed argument, section by section

1. **Problem.** Repair-first generators destroy bug-revealing tests; triage is the step that decides. Unchanged.
2. **Gap.** Published triage for generated tests (JSTestCraft, Wang et al., Meta) asks models to judge one failing
   run. Nobody has measured that judgement against execution labels, and nobody obtains further evidence by
   executing the program. Two citations to add: Wang et al. (APSEC 2025), Becker et al. (arXiv:2601.22832).
3. **Study 1, measurement (existing RQ1–RQ3, unchanged numbers).** Judges over a static package: accuracy, lost
   tests, the A4 ablation, the nulls with their minimum detectable effects.
4. **Study 2, how far opinions go (existing RQ4, reframed).** KUU, k-of-n, the cascades and the thinking judge
   presented as *points on one trade-off*, with the rates figure as the centrepiece. KUU stops being "the method"
   and becomes the strongest judge-only baseline.
5. **Insight.** A failing run shows that test and program differ, not which is wrong; more opinions about one
   observation add no information; controlled re-execution does.
6. **Method: counterfactual program probes.** Definitions, the two hypotheses with their stated failure modes, the
   certificate rules, cost. From `SELECTED_METHOD_SPEC.md`.
7. **Study 3, pilot (D-137), labelled exploratory**, then **Study 4, registered run on fresh faults**.
8. **Discussion.** What the probe cannot see (faults of omission, replaced calls, tiny methods), plausible edits are
   not fixes, the frame guarantees a nearby fault.
9. **Threats, reproducibility, cost.** As now, plus the probe's CPU cost and zero egress.

## 4. Contribution statement, before and after

**Now (paper §1):** Framework · Method (KUU and escalation) · Findings.

**Proposed** (each with the artefact that proves it):

| Contribution | Evidence required | State |
|---|---|---|
| C-1. An execution-grounded evaluation of LLM failure triage on repository-level Java, with lost bug-revealing tests as the outcome | `results/heldout/analysis_final`, label store, call logs | exists |
| C-2. Evidence that judge-only rules (voting, debate, cross-family unanimity, cascades) occupy one trade-off curve and that the failure evidence, not the deliberation, carries their signal | Tables G1, G4, B3; rates figure | exists; needs the reframing |
| C-3. Counterfactual program probes: a model-free way to obtain evidence about fault side from the buggy program alone, with two observables whose evidential value is measured | `src/triage_ext`, `results/extension`, D-134 to D-137 | exploratory; **needs the fresh-fault run** |
| C-4. Certificate rules that add this evidence to any base rule, and their measured effect on lost bugs and removed test faults | same | exploratory; one bug lost in 22 |
| C-5. A sealed fresh real-fault set with the lifecycle outcome | `DATASET_EXPANSION_PLAN.md` | not started |

KUU, KUU-NG and the cascade stay in the paper as baselines and as the motivation for C-3. The abstract should no
longer end on them.

## 5. Text that must change even if nothing else does

| Where | Now | Change |
|---|---|---|
| Related work, Table 1 | closest studies: JSTestCraft, JavaOracle, VALTEST, Maddila et al., Zhao et al. | add Wang et al. (same judgement, 43 hand-labelled tests) and Becker et al. (three-family judge ensemble on failing catching tests) |
| §3.6 | "JSTestCraft also asks three LLMs" as the only precedent | state that multi-family judging and escalation are established, and that KUU's unanimity is a threshold choice |
| Contributions | "Method (RQ4)" | demote to a baseline unless and until C-3 replaces it |
| §8.1 | "about 257 bugs rather than 60" | reconcile with the label store: 22 bugs carry the 60 bug-revealing tests |

These four are corrections, not new claims, and can be made in the current paper under the existing process.

## 6. Venue fit

Deadlines were read from aggregator pages on 2026-11-11 and must be checked on the official sites.

| Venue | Fit | Bar relative to the current evidence |
|---|---|---|
| ISSTA 2027 (research; abstract about 8 Jan 2027 per aggregators) | Best topical fit: test oracles, generated tests, mutation | Needs the fresh-fault run. With only the pilot, reviewers will call the method post hoc on 22 bugs. Feasible only if generation starts immediately |
| ASE 2027 (deadline not found) | Good fit for a tool-backed mechanism | Same requirement; more tolerant of an engineering contribution, still expects more than one benchmark and one generator |
| FSE 2027 research | Closed (full papers were due 2 Oct 2026) | — |
| ICSE 2028 | Strongest venue; expects a second generator or benchmark and an independent label audit | Not reachable without T2–T4 of the dataset plan and external raters |
| ICST 2027 / AST / a mutation workshop | A short paper on the pilot alone, clearly labelled exploratory | Reachable now; lower impact |
| EMSE or TOSEM (journal) | Suits the combined paper with full appendices and the registered replication | The right home once Study 4 exists; journals accept the measurement-plus-mechanism shape and long threats sections |
| JSS / IST | The measurement paper as it stands, with the four corrections | Reachable soonest; would spend the mechanism's novelty cheaply if included unconfirmed |

Recommendation: do not submit the mechanism before the fresh-fault run. If a deadline must be met with existing
evidence, submit the measurement paper with the corrections in §5 and keep the mechanism for the combined paper.

## 7. What "ready" would require

1. The registered fresh-fault run (C1–C4 of the preregistration draft) with at least 60 bugs carrying a
   bug-revealing test.
2. A control set of failures on non-buggy methods, to answer "the frame hands you a nearby fault".
3. An independent label audit on held-out items, so that "test fault" is not partly "second real fault".
4. Stage B (probe report in the judge's package), to answer evidence versus reasoning.
5. One of: a second generator, a second benchmark, or post-cutoff bugs.
6. The numbers of the extension routed through the numbers map.

Items 1 and 2 are the minimum for a credible method claim. Items 3 to 5 decide the tier of the venue.
