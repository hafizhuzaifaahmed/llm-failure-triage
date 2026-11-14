# Reviewer simulation (not peer review)

Three reviewer perspectives on the *proposed combined paper* (`PAPER_RESTRUCTURE_PLAN.md`) as it would stand today,
with the pilot as its only evidence for the mechanism. Written by the lead researcher in one pass; separate
reviewer agents were not used because the session's usage limit had already interrupted two agents. Treat the
verdicts as a checklist of what a hostile reader would say, not as a forecast.

## Reviewer A: software testing and empirical SE

**Summary of the submission as A reads it.** Measures LLM triage of failing generated tests against buggy/fixed
labels; shows judge-only rules trade bug retention against test-fault removal; proposes running the failing test on
mutants of the method under test and using flips and insensitivity as evidence.

| # | Concern | Severity | What would change the verdict |
|---|---|---|---|
| A1 | The method is evaluated on the benchmark it was designed against, with 22 bugs | **fatal for a method claim** | a sealed fresh-fault run of the unchanged engine |
| A2 | The frame puts a fix-changed method under every test. Of course a small edit often fixes it. In real use most failing tests target correct code | major | flip rate on failures of non-buggy methods; report P(flip) at realistic bug prevalence |
| A3 | A flip is a plausible patch, and plausible patches overfit (two decades of APR). 46 wrong tests flip | major | the paper must present the flip as evidence with its false-positive rate, never as a repair; show precision of the keep certificate at 5% prevalence |
| A4 | Sibling tests come from the same generator shown the same buggy code; "regression-consistent" is not independent evidence. The data agree: the filter removes most true fixes | major | use developer tests that predate the bug as the regression set where history allows, or drop the filter and say why |
| A5 | "Decoupled" lost a real bug whose fix replaces a call. Faults of omission are common in Defects4J | major | the guarded variant, registered; bugs lost with an exact bound |
| A6 | Java, Defects4J, one generator | major for a top venue | a second benchmark or generator |
| A7 | Fail-on-both is called a test fault even when it exposes a second fault | moderate | the independent audit |
| A8 | Mutation operators are hand-rolled regex edits, not Major or PIT | moderate | either justify (no build integration needed, runs on any checkout) or re-run with Major's operators as a robustness check |
| A9 | MUSE and Metallaxis did this in 2014 | moderate | a precise paragraph: same observable, different inference; MUSE conditions on the test being right |

**A's likely verdict today:** reject as a method paper; accept-with-major-revision as an empirical paper if the
mechanism is presented as a preliminary study and A1 is promised.

## Reviewer B: AI for SE and LLM systems

| # | Concern | Severity | What would change the verdict |
|---|---|---|---|
| B1 | The LLM part of the paper is weak judges that fail their own gate. The frontier reference is one closed model on a memorised benchmark | major | a gate-passing open judge, or the registered factorial with a frontier model |
| B2 | The interesting question is unanswered: does a judge *given* the probe report decide better? Certificates bolted on the outside avoid it | major | Stage B: report versus no report versus shuffled report, thinking on and off |
| B3 | The probe gives no gain on the thinking judge (+0.030, interval through zero) and a non-significant one on the frontier judge. As models improve, is the mechanism obsolete? | major | show complementarity at fixed model strength on larger data; argue cost: seconds of CPU against 70 s of GPU per call and zero egress |
| B4 | No agent. The related-work framing invokes evidence-gathering agents, then delivers a fixed schedule | moderate | either drop the agent framing or add the adaptive variant as a matched-budget arm |
| B5 | Missing baselines: an LLM asked to propose a minimal program patch and a minimal test patch (repairability by generation); a learned combiner over probe flags and votes with leave-one-project-out | moderate | add both; the second is zero-call on existing data but must be registered first |
| B6 | KUU, KUU-NG, cascade, fully local cascade: four names for points on one curve | moderate | collapse to one baseline family in the main text |
| B7 | Prior art on three-family judges (Meta) and calibrated cascades (Trust or Escalate, REAG) is absent from the bibliography | moderate | cite and position |

**B's likely verdict today:** weak reject. Sees the probe as a sound idea whose interaction with LLM judges, the part
this community cares about, is untested.

## Reviewer C: statistics, experimental design, reproducibility

| # | Concern | Severity | What would change the verdict |
|---|---|---|---|
| C1 | The pilot is called "fixed in advance" but the analyst knew every label and vote. Researcher degrees of freedom remain in the choice of operators and rules | **fatal for any confirmatory wording** | external registration before generation; the paper must say "exploratory" wherever the pilot appears |
| C2 | A scope amendment after looking at dev results that included label counts | major | already disclosed; keep both scopes in the main table (they agree) |
| C3 | HP-1's interval is [0.007, 0.478]. One bug moves it across zero | major | do not headline the filtered certificate; headline the unfiltered rate with its interval |
| C4 | Policy deltas are computed on a 1:2 sample with votes; flag rates on all 356. Two populations in one argument | moderate | obtain votes for the remaining test faults (the study already did this for four judges, Table G7a) and recompute on one population |
| C5 | Bug-level outcomes with 22 clusters: "bugs lost 1 against 1" carries no information. Report the bound | moderate | exact binomial upper bounds beside every bugs-lost count |
| C6 | Many rule-by-base combinations, no multiplicity control | moderate | acceptable for discovery if labelled; the registration fixes four tests in one family |
| C7 | Clustering by bug ignores project structure; 11 projects, a few dominate (Chart, Lang, Math) | moderate | leave-one-project-out for the two rate differences; a project-level sensitivity bootstrap |
| C8 | Operator-level findings (negation is noisy, connector swaps invert) are post hoc and invite tuning | moderate | keep the operator set fixed in the registered run; treat pruning as a secondary analysis |
| C9 | Determinism and environment: results depend on JVM timing through the 10 s limit | minor | report ERR counts per instance (in the ledger) and a re-run agreement check |
| C10 | Extension numbers are not in the paper's numbers map | minor | route them through `build_numbers.py` before any text cites them |

**C's likely verdict today:** the design discipline is unusually good for an exploratory study and the labelling of
status is honest; cannot be reviewed as a confirmatory result.

## Synthesis: prioritised revision plan

| Priority | Action | Addresses | Needs |
|---|---|---|---|
| 1 | Fresh sealed real-fault run of the unchanged engine under an external registration | A1, C1, C3, C5 | generator and server time; authors' approval |
| 2 | Control failures on non-buggy methods | A2 | generation |
| 3 | Stage B: probe report inside the judge's package, with a shuffled-report control | B2, B3 | local judge sessions |
| 4 | Guarded decoupling certificate and operator pruning, as registered secondary analyses | A5, C8 | nothing new |
| 5 | Votes for all held-out test faults so rates and policies share one population | C4 | already available for four judges on D1-test (zero calls to recompute for KUU and KUU-NG) |
| 6 | Citations and positioning: Wang et al., Becker et al., Trust or Escalate, REAG, MUSE, OASIs, Neyman–Pearson | A9, B7 | full-text reading of each |
| 7 | Independent label audit | A7 | external raters |
| 8 | A second generator or benchmark | A6, B1 | days to weeks |
| 9 | Collapse KUU variants into one baseline family; replace the "Method (RQ4)" contribution | B6 | text only |
| 10 | Major's operators as a robustness arm; leave-one-project-out | A8, C7 | CPU only |

Items 5, 6, 9 and 10 need no new data and no approval. Item 5 was not done in this pass because it is a new analysis
on held-out labels and should be entered in the decision log first.
