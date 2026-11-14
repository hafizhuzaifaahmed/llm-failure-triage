# Full-text literature verification (2026-11-11)

A read-only verifier fetched and read the works below; the lead researcher re-checked the one that changes the
novelty claim (e-Otter++) with a separate search. **Read** says what was opened: *full* = whole text; *part* = named
sections or the first ≈100,000 characters of a long HTML page; *record* = bibliographic record only.
arXiv HTML pages were read through a summarising fetcher, so wording is paraphrased throughout.
This file corrects `LITERATURE_MAP.md` where they differ.

## 1. Headline: the novelty claim must be narrowed

The earlier claim was "no prior work uses mutant or patch reachability to decide test-versus-program blame".
**The patch half of that claim is wrong.**

**e-Otter++** (Ahmed, Ganhotra, Shinnar, Hirzel. *Heterogeneous Prompting and Execution Feedback for SWE Issue Test
Generation and Selection*; v1 titled *Execution-Feedback Driven Test Generation from SWE Issues*. arXiv:2508.06365;
v3 lists ICSE 2026. Read: part, plus search confirmation) generates candidate code patches with an LLM-based repair
tool (40 patches, the 5 most frequent kept) and keeps candidate reproduction tests that fail on the old code and pass
on a candidate patch. Its stated reasoning is that passing on generated patches predicts passing on the true fix.
It reports 63.0% fail-to-pass on TDD-Bench Verified. That is patch reachability used as evidence that a failing test
is valid.

What remains distinct in this project, and the wording to use:

| Aspect | e-Otter++ | Counterfactual program probes |
|---|---|---|
| Source of counterfactual programs | LLM-generated patches from an issue description | mechanical first-order mutants; no model |
| Needs a bug report | yes (issue text drives test and patch generation) | no: only the program and the failing test |
| Output | which candidate test to select | a verdict about fault side for every failing test |
| Negative evidence | none | `decoupled`: no edit changes the failure |
| Setting | issue reproduction (SWE-bench family, Python) | unit-test generation without a known bug (Java) |
| Evaluated as | fail-to-pass rate of the selected test | rates under execution labels; lost bug-revealing tests |

**Defensible claim:** to our knowledge, no prior work uses model-free first-order mutants of the method under test,
without a bug report, to decide whether a failing generated test or the program is at fault, nor uses the
insensitivity of a failure to every such mutant as evidence against the test.

## 2. Verified entries

| # | Work | Read | Verified content |
|---|---|---|---|
| 1 | Moon, Kim, Kim, Yoo. *Ask the Mutants: Mutating Faulty Programs for Fault Localization* (MUSE). ICST 2014, pp. 153–162. Peer-reviewed | full | Two conjectures: failing tests are more likely to pass on a mutant of the faulty statement than of a correct one; passing tests are more likely to fail on a mutant of a correct statement than of the faulty one. Suspiciousness averages, over a statement's mutants, the share of failing tests that turn passing minus a weighted share of passing tests that turn failing. The program is faulty by premise; faulty tests or oracles are never considered. 14 faulty versions of five C programs; 7.4 statements examined on average. Its Table III reports failing-to-passing flips per mutant of 12.93 on faulty statements and 0.68 on correct ones, so flips also arise away from the fault. Most flips are partial fixes |
| 2 | Papadakis, Le Traon. *Metallaxis-FL: mutation-based fault localization*. STVR 25(5–7):605–628, 2015. DOI 10.1002/stvr.1509. Peer-reviewed | part | Uses *kills* (any change in test output), not fail-to-pass, with an Ochiai-style formula over mutants. It is therefore the precedent for the **decoupled** observable (does any mutant change the failure), not for flips. No mention of faulty tests. The 2012 workshop version was not opened |
| 3 | Pearson, Campos, Just, Fraser, Abreu, Ernst, Pang, Keller. *Evaluating and improving fault localization*. ICSE 2017. Peer-reviewed | full (paper), part (technical report) | On 310 real Defects4J faults MUSE ranks last of seven techniques; the paper attributes this to almost no real fault being reversible by a single mutant. Also: 10% of real faults involve a non-mutatable executable statement, 30% of fixes are omissions, 76% span several statements. **The share of real faults for which some mutant makes a failing test pass is not stated.** Their "reversible" means a mutant that fixes every failing test, a stronger condition than a flip of one generated test |
| 4 | Just, Jalali, Inozemtseva, Ernst, Holmes, Fraser. *Are Mutants a Valid Substitute for Real Faults in Software Testing?* FSE 2014, pp. 654–665. Peer-reviewed | full | 357 real faults; 73% coupled to mutants, 27% not; of the uncoupled, most have no feasible operator (algorithm changes, deletions, similar-method calls). Coupling here means a fault-triggering test kills extra mutants of the *fixed* version; it does not mean a mutant of the buggy version repairs it |
| 5 | Smith, Barr, Le Goues, Brun. *Is the Cure Worse Than the Disease? Overfitting in Automated Program Repair*. ESEC/FSE 2015. Peer-reviewed | part | 998 IntroClass bugs; a median patch that passes the whole training suite passes 75.0% of a held-out suite |
| 6 | Qi, Long, Achour, Rinard. *An Analysis of Patch Plausibility and Correctness for Generate-and-Validate Patch Generation Systems*. ISSTA 2015. Peer-reviewed | part | Of GenProg's patches, correct for 2 of 105 defects; RSRepair 2 of 24; AE 3 of 105. Most plausible patches delete functionality. Kali, which only deletes, forces a condition or inserts a return, matches the three tools: essentially this project's statement-deletion and condition-negation operators |
| 7 | Ghanbari, Benton, Zhang. *Practical Program Repair via Bytecode Mutation* (PraPR). ISSTA 2019, pp. 19–30. DOI 10.1145/3293882.3330559. Peer-reviewed | arXiv v1 full | 395 Defects4J bugs: basic mutators give a plausible patch for 113 bugs and a genuine one for 17–18; all mutators 148 and 43. So for most bugs where a single mutant passes the tests, that mutant is not the fix |
| 8 | Debroy, Wong. *Using Mutation to Automatically Suggest Fixes for Faulty Programs*. ICST 2010, pp. 65–74. DOI 10.1109/ICST.2010.66 | record | Not read. PraPR summarises its hypothesis: if mutators mimic programmer errors, mutating a defective program can fix it. That is the reach hypothesis, in print since 2010, for repair |
| 9 | Jahangirova, Clark, Harman, Tonella. *Test Oracle Assessment and Improvement* (OASIs). ISSTA 2016, pp. 247–258. Peer-reviewed | part | Mutation finds oracle false negatives; a human decides. It notes that a mutant may by accident fix a program fault, in which case the fault is in the program and not the assertion, and expects this to be very rare. The nearest explicit statement of the flip inference, left to the human |
| 10 | Wang, Zhong, Wen, Liu. *Multi-agent Assisted Automatic Test Generation for Java JSON Libraries*. arXiv:2410.09414; APSEC 2025 | full | The validator is GPT-4o with definitions and few-shot examples, sees test code and execution result, majority of three queries. No probing, mutation or patching. 43 tests; accuracy 72.1% and 69.8%; near chance on exception failures |
| 11 | Becker et al. *Just-in-Time Catching Test Generation at Meta*. arXiv:2601.22832. **Submitted** to the FSE 2026 industry track; not yet peer-reviewed | part | Rule-based assessors and three LLM judges combined by median; judges see test, failure, diff and inferred intent. **Nothing is re-executed on modified code to assess a catch.** Mutation is used only to generate tests. Over 98% precision at flagging false positives (class imbalance noted by the authors); recall not reported |
| 12 | Zhang, Shang, Gu, Zhou, Fang, Chen, Xiao. *Multi-Agent LLM Collaboration for Unit Test Generation via Human-Testing-Inspired Workflows* (TestAgent). arXiv:2607.09101. Preprint | full | **Keeps** a failing test attributed to the focal method only if three LLM voters unanimously call it a real defect. Voters see the test, the error and a reasoning trace. Mutation is used for scoring, not blame. A unanimity rule over three LLM votes, with the opposite default to this project's KUU |
| 13 | Konstantinou, Degiovanni, Papadakis. v1 *Do LLMs generate test oracles that capture the actual or the expected program behaviour?*; v2 *Can we find bugs using LLM-generated oracles?* arXiv:2410.21136. Preprint | v1 full, v2 part | LLMs classify a correct assertion on buggy code correctly 32–37% of the time (v1; 31–72% across four models in v2). Recommends LLMs for discarding invalid assertions, with the caveat that accuracy drops on buggy code |
| 14 | Long, Zhao, Wang. *LogicHunter*. arXiv:2607.06195. Preprint | part | A ReAct oracle with code search, documentation search and sandboxed reproduction scripts. No mutation or patching of the program under test. Precision 91.17%, recall 72.14% |
| 15 | Amusuo et al. *FalseCrashReducer*. arXiv:2510.02185. Preprint | part | A crash validator reasons over the stack trace and call sites about feasibility from entry points. No mutation, patching or re-execution on modified code |
| 16 | Hao, Lan, Zhang, Guo, Zhang. *Is This a Bug or an Obsolete Test?* ECOOP 2013 | part | Seven features (call-graph complexity, change, test results) in a decision tree. No mutation or repair. Reports that applying a spectrum-based localizer directly could hardly classify failure causes |

Corrections to earlier documents:

- Becker et al. is **submitted**, not accepted; the earlier map said "FSE 2026 industry track (per Meta's blog)".
- Metallaxis is the ancestor of the *decoupled* observable; MUSE of *flip*. The earlier documents named MUSE for both.
- TestAgent was listed as unread; it uses three-voter unanimity to *keep* a failing test, a direct neighbour of KUU.

## 3. Not opened or not found

Debroy and Wong (full text); the 2012 Metallaxis workshop paper; Otter, UTBoost, FixCheck, UTFix (search summaries
only); TestRefiner (not found); two test-code fault-localization preprints seen in search results and not opened
(arXiv:2506.19045, 2605.07957); Stein et al., STVR 2024, on recreating Defects4J faults by repeated mutation
(search summary only). Each must be opened before it is cited.

## 4. Objections a reviewer can ground in these papers, and where the project stands

| # | Objection | Grounding | Status in this project |
|---|---|---|---|
| 1 | Real faults are almost never reversed by one mutant, so flips on right tests should be rare | Pearson et al.; Just et al. | The pilot measured it for *generated* tests: a flip exists for 40 of 60 bug-revealing tests (14 of 22 bugs). A flip of one generated test is a weaker condition than reversing a fault. The confirmation's C1 tests whether this holds on unseen bugs |
| 2 | A passing mutant is an overfit, not a fix | PraPR; Qi et al.; Smith et al. | Agreed and designed for: a flip is evidence with a measured false-positive rate (46 of 296 wrong tests in the pilot), never a repair. Chart_17 in the pilot is an explicit example of a right verdict from a wrong edit |
| 3 | The premise comes from work that assumes the test is right; flips also occur on correct statements | MUSE Table III; Debroy and Wong | This is the gap the study fills: flip rates under *both* labels, and on methods with no fault (the control group, added for this reason) |
| 4 | "No mutant changes the failure" may reflect operator gaps or a missing-code fault | Pearson et al. (30% omissions, 10% non-mutatable); Just et al. | Observed once in the pilot (Codec_13, a replaced call). The ten-mutant minimum, the guarded variant and the bugs-lost bound address it; C2 and the safety outcome test it |
| 5 | Patch-based validation of failing tests exists; LLM-judge triage is established | e-Otter++; Wang et al.; TestAgent; Meta | Claim narrowed (section 1). Baselines needed in the paper: an LLM-patch reachability arm in the manner of e-Otter++, the judge-only rules already measured, and Hao et al.'s feature classifier as the classical baseline (the study's failure-feature classifier is its analogue) |

## 5. Second verification pass (2026-11-12)

Same method and read codes. "Extractor" means arXiv HTML read through a summarising fetcher.

| # | Work | Read | Verified content |
|---|---|---|---|
| 17 | e-Otter++ (as in section 1), arXiv:2508.06365 v3; the arXiv comment says accepted at ICSE 2026 | full body via extractor | Patches: an LLM repair tool produces 40 patches (one at temperature 0, 39 at 0.8); the 5 most frequent after normalisation are kept. Selection over 10 candidate tests is rule-based: each test runs on the old code and on each of the 5 patches; fail-to-pass tests are kept, grouped by failure type, ties broken by line coverage. **The paper does not state whether a test must pass on one, most or all patches**; its fallback wording implies at least one. A test that passes on no patch is dropped only if another candidate is fail-to-pass; if none is, all candidates are kept. It never labels a test wrong and never abstains. Ablation on TDD-Bench Verified (449 instances): without the patch filter 44.7% (random tie-break) or 47.4% (coverage); with it 61.8% or 63.0%. Python only; the issue text is a required input; no mutation |
| 18 | Ahmed, Ganhotra, Pan, Shinnar, Sinha, Hirzel. *Otter: Generating Tests from Issues to Validate SWE Patches*. arXiv:2502.05368 (ICML 2025 per a search result; proceedings page not opened) | extractor | No candidate patches in test selection; tests that pass on the old code are discarded. Tests are later used to filter patches |
| 19 | Lou, Ghanbari, Li, Zhang, Hao, Zhang. *Can automated program repair refine fault localization?* (ProFL). ISSTA 2020; read as arXiv:1910.01270 v1 | pp. 1-6 and threats | Runs first-order patches (those of PraPR) against the suite and sorts program elements by what a patch does: **CleanFix** (some failing tests pass, no passing test breaks), **NoisyFix** (some failing pass, some passing break), **NoneFix** (nothing changes), **NegFix** (no failing test passes, some passing break). Ranks CleanFix > NoisyFix > NoneFix > NegFix to refine localization: 161 of 395 faults at top-1. The suite is simply the oracle; no category considers that a failing test may be wrong |
| 20 | Papadakis, Le Traon. *Using Mutants to Locate "Unknown" Faults*. ICST 2012 workshops, pp. 691-700 | full | Assumes mutants on a statement behave like a fault on that statement. A kill is any output difference between mutant and original, independent of pass or fail. Test verdicts are taken as given |
| 21 | Chen et al. *CodeT*. arXiv:2207.10397 v2 | extractor | Groups sampled solutions by the set of generated tests they pass and scores a group by its size times the number of tests passed. No test is ever labelled wrong |
| 22 | Yu, Zhu, He, Kang. *UTBoost*. arXiv:2506.09289 (ACL 2025 per a search result) | extractor | Generates extra tests and compares gold-patched with agent-patched programs on them; differences are reviewed by hand. Patches judge patches and test sufficiency; no automatic judgement that a test is wrong |
| 23 | Molina, Copia, Gorla. *Improving Patch Correctness Analysis via Random Testing and Large Language Models* (FixCheck). ICST 2024 | full | Validates a **patch**; the original fault-revealing test is presumed correct. Discards generated failing tests whose trace is unlike the original failure. No program mutation |
| 24 | Rahman et al. *UTFix*. arXiv:2503.14924 (OOPSLA 2025 per the arXiv comment) | extractor, about 85% | Assumes the changed method is right and the test is at fault; always repairs the test |
| 25 | Daniel, Jagannath, Dig, Marinov. *ReAssert*. ASE 2009 | abstract and introduction | States that the developer must first decide whether code or test is at fault; repairs tests only in the latter case |
| 26 | Saboor Yaraghi et al. *Efficient Black-Box Fault Localization for System-Level Test Code Using Large Language Models*. arXiv:2506.19045 (accepted at TSE 2026 per arXiv); Gharachorlu et al. *SPARK*. arXiv:2605.07957 | first 30-45% | Both localize faults inside **test** code and presuppose the cause is in the test. No blame step, no mutation in the parts read |
| 27 | Ahmed, Stein, Herbold, Trautsch, Grabowski. Reproduction of real faults with repeated mutations. STVR 2024 (DOI 10.1002/stvr.1874 per the group page); read as arXiv:2104.02517 v2 | PDF text | Defects4J 2.0, 1,011 file changes analysed: fully reproduced by default operators 24 (2.4%), by the extended operator set of the authors 75 (7.4%); partially 287 and 717 |
| 28 | Li, Zhang. *Transforming programs and tests in tandem for fault localization*. OOPSLA 2017 | targeted sections | Instruments tests to record every assertion outcome; does not perturb test semantics or assign blame |
| 29 | Debroy, Wong. ICST 2010 | **full text not accessible** | Second-hand only: operator replacement within a class and negated decisions on statements ranked by a spectrum localizer. Fix counts and the test assumption remain unverified |

Not opened in either pass: Hybrid-MUSE; the TDD-Bench Verified paper itself; proceedings pages for Otter, UTBoost and
CodeT; the journal version of entry 27; later parts of entries 24 and 26. Three further collision searches found two
works that use program mutants on *passing* tests to judge oracle strength (not failing-test blame) and none that
adjudicates a failing test with program mutants.

## 6. Positioning

| Work | What is perturbed | Who makes the perturbation | What is assumed about the failing test | What is inferred | Needs a fixed version or bug report |
|---|---|---|---|---|---|
| MUSE (2014) | program | mechanical first-order mutants | it is right (the program is faulty by premise) | where the fault is | no |
| Metallaxis (2012, 2015) | program | mechanical first-order mutants | its verdict is taken as given | where the fault is | no |
| Debroy and Wong (2010) | program | mechanical mutants (second-hand) | not verified | a candidate fix | not verified |
| PraPR (2019) | program | mechanical bytecode mutants | the suite is the oracle | a plausible patch | no |
| ProFL (2020) | program | mechanical first-order patches | the suite is the oracle; validity not questioned | where the fault is | no |
| OASIs (2016) | program and inputs | mechanical mutants; generated tests | a human decides | oracle weaknesses | no |
| CodeT (2023) | neither (samples programs and tests) | LLM | nothing; tests are never labelled | which program to return | task description |
| e-Otter++ (2026) | program (five surrogate patches) | LLM | it should fail on the old code, because the issue says the program is buggy | which candidate test to return | issue text required |
| LLM-judge triage (Wang et al.; Meta; TestAgent; KUU in this project) | nothing | none | nothing | a verdict from reading one failing run | no |
| **CFP (this project)** | program (method under test and its same-class callees) | mechanical first-order mutants | **nothing: it is the hypothesis under test** | flip: evidence the test is right; decoupled: evidence the test is wrong | no |

**How to state the relation, precisely.**

- *Against MUSE, Metallaxis and ProFL.* The executions are the same kind: first-order edits of the program run
  against a failing test. The CleanFix and NoisyFix categories of ProFL correspond to a flip, and "every edit is
  NoneFix" corresponds to decoupled. Those works read the outcome as the *location* of the fault and never treat the
  failing test as the thing in doubt; an all-NoneFix result is not interpreted. CFP reads the same outcomes as
  evidence about the test. The difference is the inference and the question, not the mechanism, and the paper must
  say so in those words.
- *Against e-Otter++.* Same direction of inference (a test gains credit when some program variant makes it pass).
  Differences: variants are LLM patches conditioned on an issue; the program is known to be buggy; the output is a
  choice among candidates, not a verdict per test; a test that passes on no patch is not called wrong; there is no
  counterpart of decoupled; Python issue reproduction rather than Java unit-test generation without a report.
- *Against LLM-judge triage.* Those methods add opinions about one execution; CFP adds executions.
- *Against repair.* PraPR and the overfitting literature show a passing edit is usually not the fix; CFP uses the
  edit as evidence only, and its false-positive rate is what the study measures.

**No claim of established novelty is made.** The statement the evidence supports is: in the works opened across two
verification passes, none uses mechanical mutants of the program under test to judge whether a failing test is right
or wrong. Works not opened are listed above; a reviewer may know others.
