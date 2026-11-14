# Novelty collision check (2026-11-11)

Each idea is listed with what already exists, the exact searches run, and the gap that survives. Verdicts are
conservative: "no direct prior work found" means a documented search found none, not that none exists.
Reading depth for every cited work is in `LITERATURE_MAP.md`.

## A. Ideas the current paper already claims

| Idea | Verdict | Closest work | What survives |
|---|---|---|---|
| LLM judge decides whether a failing generated test is a real bug | **Already explored** | Wang et al. (APSEC 2025): GPT-4o few-shot validator with a 3-query vote on 43 hand-labelled tests. Becker et al. (Meta, FSE 2026 industry): rules plus a three-family judge median on failing catching tests. JSTestCraft (already cited): three-LLM vote | Scoring against buggy/fixed execution labels on repository-level Java, with lost bug-revealing tests counted. That is an evaluation contribution, not a method |
| Three judges from different families | **Already explored** | Becker et al. use Llama, Gemini and Claude and take the median; JSTestCraft takes a majority | Unanimity-to-discard instead of majority or median. A different operating point on the same votes (the paper already says so: Appendix F(c), Table G4) |
| Cascade that escalates disagreement to a stronger judge | **Already explored** in ML and once in SE | FrugalGPT; Trust or Escalate (ICLR 2025) with guarantees; REAG (ASE 2026) inside SE | Application to PF/TF triage with a privacy argument. No guarantee is attached in the paper |
| Debate vs self-consistency at equal budget | Partially explored outside testing | Smit et al. (ICML 2024), Wang et al. (ACL 2024) question debate against single-agent baselines (seen in search summaries only) | The triage-specific null result; inconclusive at this sample size |

**Consequence.** KUU and the cascade cannot carry a novelty claim. Two works that must be cited are missing from
`paper/references.bib`: Wang et al. (APSEC 2025) and Becker et al. (arXiv:2601.22832).

## B. Candidate extensions

| # | Idea | Verdict | Closest work | Remaining gap |
|---|---|---|---|---|
| C1 | Evidence-gathering triage agent that runs bounded diagnostic actions on the buggy program | No direct prior work found; explored in adjacent domains | LogicHunter's agentic oracle (agent frameworks), FalseCrashReducer (fuzz drivers), Agentic PBT, AutoSD | No work runs probes on the buggy program only to output PF / TF / defer for failing generated JUnit tests, scored against fixed-version ground truth |
| C2 | Independent re-derivation of the expected value (cross-generation or code-blind) as a validity signal | Partially explored | CANDOR, ConVerTest, CodeT, Differential Prompting, TrickCatcher, Doc2OracLL, Zhao et al. | Used to produce or select oracles, never measured as a post-hoc signal on an already failing test. **This repository already measured the cross-generation form and found no signal on real faults** (AUROC 0.513, D-118), and 15–21% of derived specs keep the defect (Zhao et al.) |
| **C3** | **Program-side counterfactual probes: which small edits of the program change or remove the failure** | **No direct prior work found** | MUSE and Metallaxis use the same observable for fault *localization* and assume the failing test is right. OASIs uses mutation on oracle quality with a human in the loop. Test-side repair (YATE, ChatAssert, TaRGET) changes only the test | Nobody uses the reachability of a passing state by a small program edit, or the insensitivity of a failure to every edit, as evidence about *which side is at fault* |
| C4 | Benchmark with a richer label taxonomy and full lifecycle | Partially explored | Zhao et al.'s four execution labels; Meta's proprietary 15-pattern false-positive table; Shang et al.'s build-error breakdown | No public labelled set of failing generated tests with causes beyond PF/TF and with the outcome after repair or deletion |
| C5 | End-to-end evaluation: bugs preserved against developer inspection workload | Partially explored | Mathews and Nagappan count bugs lost without triage; Meta reports workload cut without recall; Self-Repair Trap uses a mutation proxy | Both axes together, for triage policies, with execution ground truth, in Java |
| M1 | Risk-controlled discard threshold with a bound on lost bug-revealing tests | Done in ML, not applied to this task | Neyman–Pearson classification (Tong et al. 2018) is the i.i.d. core; Learn-then-Test; hierarchical conformal for clusters | The bug-level loss ("a bug loses all its revealing tests") with bugs as calibration units. With 22 bugs the certifiable floor is about 13% at 95% confidence, so the data cannot support a useful guarantee yet |
| M2/M3 | Three-way keep / discard / defer with a calibrated cascade | Pre-empted as a generic method | Trust or Escalate; REAG; SCOPE; Conformal Cascade | An asymmetric, cluster-calibrated version for PF/TF. Incremental without new evidence signals |
| M4 | Score built from cross-family disagreement, execution features and confidence | Partially explored; **already tried here** | VALTEST, ESE; this repository's stacker (D-115) | The stacker added nothing over the votes (Table G3). A new score needs a new signal, which is what C3 supplies |

## C. Searches run

Scout 1 (software engineering, 29 tool uses) and scout 2 (decision methods) list their queries in their reports; the
ones that bear on C3 were: "'test or program' which to repair… 'repairability'"; "'repair the test' and 'repair the
program'… 'dual repair' / 'bidirectional repair'"; "mutation-based probe decide whether failing test or program is
faulty 'faulty test' identification"; "LLM agent validates suspected bug by executing probes 'relaxed assertion' /
'counterfactual test' / 'test variants'"; "'is the bug in the test or the code' failure attribution agent".

Lead researcher, three further searches (2026-11-11):

1. `mutation analysis to determine whether failing test or program is faulty "test fault" OR "faulty test" fail-to-pass mutants blame`
   → only mutation-based fault localization (MUSE, Metallaxis) and mutation-testing theory; nothing on blame.
2. `MUSE "Ask the mutants: mutating faulty programs for fault localization" Moon Kim Kim Yoo ICST 2014`
   → metadata confirmed (ICST 2014, pp. 153–162; ICST 2024 most-influential-paper award page).
3. `LLM-generated test failure "program repair" as oracle decide "test is wrong" or "code is wrong" plausible patch existence evidence bug-revealing test 2025 2026`
   → AssertFlip, a 2026 study of validation evidence in repair agents (Xu and Wu), STING, VibePass; none uses patch
   or mutant reachability to decide test-versus-program blame.

## D. What a reviewer could still raise against C3

- "This is MUSE with the labels swapped." Answer needed in the paper: MUSE conditions on the test being right; the
  quantity here, P(a passing state is one edit away | the test is right) against the same probability when the test
  is wrong, is not measured in the localization literature.
- "Plausible patches overfit" (the APR literature on overfitting). A flip is evidence, not proof; this is why the
  rates under both labels are the object of study, and why a flip that breaks sibling tests is recorded separately.
- "Sibling tests are themselves generated from buggy code." True, and the development pilot shows the consequence:
  misguided siblings assert the buggy behaviour, so a real fix breaks them (D-135).
- Full texts of the 2026 preprints near C1 (LogicHunter, FalseCrashReducer) were not read beyond abstracts.

## E. Revision after full-text verification (2026-11-11, later the same day)

Details and read status: `LITERATURE_VERIFICATION_FULLTEXT.md`. Three changes to the verdicts above.

1. **C3 is narrowed, not withdrawn.** e-Otter++ (Ahmed, Ganhotra, Shinnar, Hirzel; arXiv:2508.06365; ICSE 2026 per
   v3) keeps candidate reproduction tests that fail on the old code and pass on LLM-generated candidate patches.
   That is patch reachability as evidence that a failing test is valid. The earlier wording "mutant or patch
   reachability" over-claimed. What is still not found in prior work: model-free first-order mutants of the method
   under test, no bug report, a fault-side verdict for every failing test, and insensitivity to every mutant used as
   evidence against the test.
2. **Ancestry corrected.** MUSE (fail-to-pass under mutation) is the ancestor of `flip`; Metallaxis (any change in
   test output under mutation) is the ancestor of `decoupled`; Debroy and Wong (2010) state the reach hypothesis for
   repair; OASIs remarks that a mutant which fixes a program fault would show the fault is in the program, and leaves
   it to a human. All of them assume the failing test is right or defer the judgement.
3. **A further neighbour of KUU.** TestAgent (arXiv:2607.09101) keeps a failing test only when three LLM voters are
   unanimous that it is a real defect: three-vote unanimity with the opposite default. Together with Meta's judge
   median and Wang et al.'s validator this closes the case that KUU is not a novel method.

Baselines this implies for the paper (none run yet): an LLM-patch reachability arm in the manner of e-Otter++
(candidate patches from a local model; a test is kept if it passes on one), beside the judge-only rules already
measured and the failure-feature classifier.

Base-rate evidence a reviewer will cite against the reach hypothesis (Pearson et al., ICSE 2017: almost no real
fault is reversible by one mutant; PraPR: a single-mutant plausible patch exists for 113 of 395 Defects4J bugs and is
genuine for 17–18) bounds a *stronger* condition than a flip of one generated test, and is the reason the
confirmation measures flip rates under both labels and on a control group.

## F. Second verification pass (2026-11-12)

Details: `LITERATURE_VERIFICATION_FULLTEXT.md` sections 5 and 6.

- **ProFL** (Lou et al., ISSTA 2020) is the closest *mechanical* neighbour and was missing from every earlier
  document here. It runs first-order patches against failing tests and names the outcomes: CleanFix and NoisyFix are
  the flip of this project, NoneFix for every patch is its decoupled. It uses them to rank fault locations and does
  not question the failing test. The remaining difference of C3 from ProFL, MUSE and Metallaxis is therefore the
  inference drawn (about the test, not the location), and nothing in the execution.
- **e-Otter++** confirmed in detail: a test that passes on no candidate patch is not judged wrong, and the paper does
  not say how many patches a test must pass on.
- **Wording rule adopted (authors, D-140):** no document in this workstream claims established novelty. The
  supported statement is limited to the works actually opened, and lists those that were not.
- Baselines implied for the paper (none run): ProFL-style categories reported per failing test, and an LLM-patch
  reachability arm in the manner of e-Otter++.
