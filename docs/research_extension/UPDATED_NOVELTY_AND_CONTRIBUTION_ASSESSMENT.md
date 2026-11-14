# Updated novelty and contribution assessment (after the confirmation)

Date: 2026-11-13. Builds on `NOVELTY_COLLISION_CHECK.md` and `LITERATURE_VERIFICATION_FULLTEXT.md` (two earlier
passes) and does not repeat their searches. It adds a third reading pass on the closest neighbours, a search for
prior use of the mechanism now proposed, a feasibility ruling on an e-Otter++-style baseline, and the choice of
contribution. **No claim of established novelty is made anywhere in this file** (authors' rule, D-140).

Read codes: **full** = whole text read; **part** = the named sections read verbatim; **record** = bibliographic
record or search summary only; **earlier** = read in pass 1 or 2 at the depth stated there.

## 1. What this pass read

| Work | Bibliographic data | Status | Read in this pass |
|---|---|---|---|
| ProFL: Lou, Ghanbari, Li, Zhang, Zhang, Hao, Zhang. *Can Automated Program Repair Refine Fault Localization? A Unified Debugging Approach* | ISSTA 2020; arXiv:1910.01270 (venue, pages and DOI not shown in the text read; take them from the proceedings page before citing) | peer-reviewed | **part**: abstract, §1–3, §4.1 (Definitions 4.1–4.6), start of §4.2, verbatim. §4.2.3 onward, §5, §6 not read (earlier pass read pp. 1–6 and threats) |
| e-Otter++: Ahmed, Ganhotra, Shinnar, Hirzel. *Heterogeneous Prompting and Execution Feedback for SWE Issue Test Generation and Selection* | ICSE 2026 (48th IEEE/ACM ICSE, Rio de Janeiro, 12–18 April 2026); DOI 10.1145/3744916.3787837; arXiv:2508.06365v3 | peer-reviewed | **part**: abstract through the start of §8, verbatim (§2.3, §3.2, §3.3, §4.4 Table 8, §4.6 Table 12, §5, §6) |
| Vera-Pérez, Danglot, Monperrus, Baudry. *A Comprehensive Study of Pseudo-tested Methods* | Empirical Software Engineering; DOI 10.1007/s10664-018-9653-2; arXiv:1807.05030 (arXiv lists "2018, pp. 1–31"; final volume and year to be taken from the DOI page) | peer-reviewed | **part**: abstract, §1–3, §4.1, Algorithm 1, Table 1, verbatim |
| Niedermayr, Juergens, Wagner. *Will my tests tell me if I break this code?* | CSED'16 workshop (at ICSE 2016), Austin; DOI 10.1145/2896941.2896944; arXiv:1611.07163 | peer-reviewed workshop | **full** |
| DeFlaker: Bell, Legunsen, Hilton, Eloussi, Yung, Marinov. *DeFlaker: Automatically Detecting Flaky Tests* | ICSE 2018, pp. 433–444; DOI 10.1145/3180155.3180164 | peer-reviewed | **record** (search summary; full text not opened) |
| Becker et al. *Just-in-Time Catching Test Generation at Meta* | arXiv:2601.22832 (30 Jan 2026). A third-party page lists the FSE 2026 companion proceedings; **not verified** | preprint until verified | earlier (part) |
| TestAgent: Zhang et al. *Multi-Agent LLM Collaboration for Unit Test Generation via Human-Testing-Inspired Workflows* | arXiv:2607.09101 (10 July 2026) | preprint. A different tool paper also named TestAgent is listed in the FSE 2026 demonstrations track; do not conflate them | earlier (full) |
| MUSE (Moon, Kim, Kim, Yoo, ICST 2014, pp. 153–162) | — | peer-reviewed | earlier (full) |
| Metallaxis-FL (Papadakis, Le Traon, STVR 25(5–7):605–628, 2015, DOI 10.1002/stvr.1509) and its ICST 2012 workshop version | — | peer-reviewed | earlier (part; workshop full) |
| Zhao et al. *Evaluating and Mitigating the Misguidance Effect of Buggy Code in LLM-Generated Unit Tests* | arXiv:2607.22883 (a search result says ISSTA 2026; not verified here; already in `references.bib`) | — | record |

Still not opened: Hybrid-MUSE; the TDD-Bench Verified paper; Debroy and Wong (ICST 2010) full text; DeFlaker full
text; ProFL §5–6. Each must be opened before a claim about its content is printed.

## 2. Side-by-side comparison of the closest neighbours

| Aspect | MUSE (2014) | Metallaxis-FL (2012, 2015) | ProFL (2020) | e-Otter++ (2026) | CFP as registered (this project) |
|---|---|---|---|---|---|
| What is perturbed | program statements | program statements | program elements (candidate patches) | program (surrogate patches) | the method under test and its same-class callees |
| How variants are made | mechanical first-order mutants | mechanical first-order mutants | first-order transformations of a repair tool (PraPR); "each patch changes one program element" (Def. 4.1) | an LLM repair pipeline (Agentless, first stage): 40 patches (1 at temperature 0, 39 at 0.8), the 5 most frequent kept (§3.2). The authors reused patches published by Agentless's authors (§5) | mechanical first-order mutants, six operators, at most 80 |
| Required input | faulty program, failing and passing tests | same | "the actual buggy program under test and the original failing test suite", plus all tests run on all patches (§4.2, Def. 4.2) | issue text, repository, 10 candidate tests, 5 patches | buggy program, the failing test; no report, no fixed version, no developer tests |
| Assumption about the failing test | right (program faulty by premise) | its verdict is taken as given | the suite is the oracle; nothing in the text read considers an invalid or flaky failing test | should fail on the old code because the issue says the code is wrong | none: it is the thing in question |
| What is measured | failing→passing and passing→failing under each mutant | any change of test output under each mutant | CleanFix / NoisyFix / NoneFix / NegFix per patch (Defs. 4.3–4.6) | fail-to-pass of each candidate test on each surrogate patch; coverage | per test: FLIP, SHIFT, SAME per mutant; `flip`, `rcf`, `decoupled` |
| Inference drawn | where the fault is | where the fault is | where the fault is (CleanFix > NoisyFix > NoneFix > NegFix) | which candidate test to return | which side is at fault, for each failing test |
| Treatment of "nothing changes" | low suspiciousness | low suspiciousness | NoneFix ranks above NegFix; no reading of an all-NoneFix outcome in the text read | a test that is fail-to-pass on no patch is dropped only if another candidate is; if none is, all are kept (§3.3). No test is called wrong | `decoupled`: evidence the test is wrong |
| Benchmark, language | 14 faulty versions of 5 C programs | C programs (Siemens suite and others) | Defects4J 1.2.0, 395 bugs, Java (plus 1.4.0) | TDD-Bench Verified (449), SWT-bench Lite (276), SWE-rebench (267); Python only | Defects4J 3.0.1, Java; 572 fresh failing tests in 104 bugs |
| Headline evaluation | 7.4 statements examined on average | Ochiai-style ranking gains | 161 of 395 at Top-1 (SBFL and MBFL at most 117) | patch pre-filter raises fail-to-pass from 47.4% to 63.0% on TDD-Bench Verified (Table 8); 42.7% on SWE-rebench with leaderboard patches (Table 12) | flip: not supported (+0.028); decoupled: supported pooled (+0.243), F2 only, two projects |
| Limits stated or evident | most flips are partial fixes; real faults rarely reversed by one mutant (Pearson et al. 2017) | cost of mutant execution | a plausible patch "might be not a genuine fix" (§3.1) | "imperfect patches or tests" carry risk (§6); Python only; issue required | one benchmark and generator; frame- and project-dependent yield; operator gaps |

**Exact distinctions that remain, and those that do not.**

- *Mechanism.* Nothing in CFP's executions is new. First-order edits run against a failing test are MUSE,
  Metallaxis and ProFL. CleanFix or NoisyFix on one failing test is a flip; NoneFix for every patch is `decoupled`.
- *Inference.* In the texts read, MUSE, Metallaxis and ProFL never treat the failing test as the thing in doubt;
  CFP reads the same outcomes as evidence about the test. That is the only difference, and it is a difference of
  question, to be stated in those words.
- *Against e-Otter++.* Same direction of inference for the positive case (a test gains credit when a program
  variant makes it pass). Remaining differences: mechanical variants and no issue text; a verdict per test rather
  than a choice among candidates; and a negative reading ("no variant changes the failure"), which e-Otter++ does
  not have. The first of these is now a **liability, not a selling point**: the positive, flip-based half is the
  half that failed to replicate here, while e-Otter++'s LLM patches conditioned on an issue produced a large gain.
  The honest contrast is that issue-conditioned patches are informative and blind single edits were not.
- *Against judge triage* (Wang et al.; Becker et al.; TestAgent; KUU). They add opinions on one execution; CFP adds
  executions. KUU, multi-family voting and escalation remain non-novel (see `NOVELTY_COLLISION_CHECK.md` A, E.3).

## 3. Claims to abandon or narrow

| Earlier wording | Status | Use instead |
|---|---|---|
| "A flip is evidence the test is right" (C3/C-3 of the restructure plan) | **abandon as a finding**; keep as a tested and unsupported hypothesis | "In a registered confirmation the flip rate did not differ between bug-revealing and wrong tests (+0.028 [−0.137, 0.274]) and equalled the rate on control failures" |
| "Certificate rules that add this evidence to any base rule" | **abandon CK**; **narrow CD** | "Discarding decoupled failures raised KUU's test-fault removal from 0.316 to 0.430 and lost one bug of 21; inconclusive after Holm correction" |
| "No prior work uses model-free first-order mutants … to decide whether a failing generated test or the program is at fault" | keep only as a statement about the works opened, and only for the **decoupling** reading | "In the works we read, none interprets the insensitivity of a failure to edits of the method under test as evidence against the test" |
| "Model-free, no bug report" as an advantage over e-Otter++ | **narrow** | state as a difference in setting; add that the issue-free positive signal did not replicate |
| "CFP reproduces KUU's operating point with no model" (pilot) | **abandon** | confirmation: keep-all + CD gives TPR 0.982, TNR 0.266 with one bug lost; KUU gives 1.000, 0.316 with none |
| Any use of "first", "novel", "state of the art" | not supported by a complete search | omit |

## 4. Is an e-Otter++-style LLM-patch reachability baseline feasible and fair here?

**Ruling: not before 15 November; and no version that fits this setting would be a reproduction.**

| Question | Answer |
|---|---|
| What e-Otter++ needs | an issue text (drives both test and patch generation), a repair pipeline that produces patches **without seeing the candidate tests**, 40 samples reduced to 5, execution of every test on every patch |
| Is a bug report available? | Not in this repository, and by design: the study's setting is test generation with no known bug. Defects4J links each bug to a tracker entry, so reports could be fetched, but using them changes the question to issue reproduction and hands the patch generator a description of the very fix that defines the PF label |
| Variant P-a: patches from the tracker report | closest to e-Otter++; answers a different question; the generator and judges very likely saw Defects4J fixes in training, so "the patch makes the test pass" may be recall of the developer fix. Usable only as a labelled *with-report reference*, never as the baseline for the no-report claim |
| Variant P-b: patches from documentation and signature only (the judge's S1 view), tests unseen | fits the setting; is a re-implementation test, not e-Otter++. This repository already measured a close relative (cross-generation agreement, D-118, AUROC 0.513). Same memorisation caveat |
| Variant P-c: patches conditioned on the failing test | **invalid**: the patch generator can satisfy any expectation; e-Otter++ does not do this |
| Budget | e-Otter++: 40 calls per instance. Here, per method with a scored failure (about 250 methods; exact count from the ledgers): 40 patches ≈ 10,000 generator calls ≈ 45 h on the study GPU at the measured 15–18 s per call; a 5-patch reduction ≈ 1,250 calls ≈ 6 h, plus compilation and execution of every failing test on every patch, plus prompt development on the dev projects first |
| Model and prompt controls a fair run would need | the frozen generator (`gemma4:26b`) with a new repair prompt developed on Cli, Gson and Jsoup only; temperature schedule and patch normalisation fixed before held-out use; patch count fixed; the same 572 tests; the same label rule; rates under both labels and a keep rule ("passes on any patch") beside the mechanical flip; model calls and GPU-seconds reported |
| What would make it unfair | tuning the repair prompt on held-out bugs; conditioning on tests; calling a 5-patch local-model proxy "e-Otter++"; comparing it with CFP without stating that one uses a model and the other does not |
| Deadline | infeasible together with the audit follow-ups, the primary extension and the manuscript changes on one GPU in under two days |

For the paper: discuss e-Otter++ as the nearest neighbour for patch-based validation, state that it was **not
reproduced**, and list variant P-b as planned work. The earlier line "baselines needed in the paper: an LLM-patch
reachability arm" is withdrawn as a requirement for this deadline and kept as future work.

## 5. Candidate technical contributions

Scores 0 (poor) to 3 (good). "Leakage" scores how free the evaluation would be of circularity (3 = clean).
Feasibility is for 15 November. Evidence cited is from `CONFIRMATION_INDEPENDENT_AUDIT.md`.

| # | Candidate | Type | Novelty vs closest work | Technical substance | Fit to C1 failure and C2 heterogeneity | Expected benefit vs KUU | Leakage | Power | Feasible | Cost | Sum | What would falsify it |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Evidence-aware judge: probe report in the prompt, shuffled control (Stage B) | method + mechanism test | 1: tool evidence in a judge prompt is common; the shuffled arm is good design | 1 | 1: two of the report's three lines describe flips, which did not replicate | 1: at best the judge learns the rule CD already applies | 2 | 1 | 1: about 11 GPU-hours at three replicates, plus build | 1 | 9 | B − C ≤ 0, or B below the outside rule |
| 2 | Asymmetric keep / discard / defer policy | policy | 1: Trust-or-Escalate, REAG, conformal cascades | 1 | 2 | 1: no stronger judge exists on these instances to defer to | 2 | 1 | 3 | 3 | 14 | defer set no richer in PF than keep set |
| 3 | Risk-controlled decoupling threshold with a bug-loss bound | calibration | 2 as an application | 2 | 1: 21 + 22 PF-bearing bugs give a certifiable floor near 7–13%; calibration data already seen | 1 | 1 | 0 | 2 | 3 | 12 | the bound is vacuous at any useful discard rate |
| 4 | Adaptive or budgeted probe selection | efficiency | 1 | 1 | 1: probes cost about a second per test; cost is not the constraint | 0 | 3 | 2 | 3 | 3 | 14 | no accuracy change, saving in CPU-seconds only |
| 5 | Learned score: votes + probe features + failure features | model | 1: VALTEST-style; this repository's stacker (D-115) | 1 | 1: pilot-trained weights would carry the flip signal that failed; observed gain from adding decoupling to vote count is AUROC 0.772 → 0.787 | 1 | 1: features chosen after both sets were seen | 1 | 3 | 3 | 12 | cross-sample AUROC no higher than vote count |
| 6 | **Whole-method dependence probes** (replace the method under test wholesale; ask whether the failure changes at all), a dependence ladder, and a certificate CD-U that discards only failures for which no entry into the method under test was observed and which are unchanged when that method throws on entry (an operational observation, not a proof of non-reachability; `TECHNICAL_METHOD_SPEC.md` version 2) | new observable + rule | 2: the transformation is extreme mutation (Niedermayr 2016; Vera-Pérez et al.), applied there to passing suites; in the texts read it is never applied to a failing test or used to judge test validity; DeFlaker makes the analogous independence argument for flaky tests with coverage | 2: a formal dependence definition, removal of the ten-mutant minimum, a mechanism for both observed bug losses | 3: targets exactly the supported half (decoupling), its two failure cases, and the 102 tests the minimum leaves undecided | 2: aims at KUU's TPR with higher TNR at zero model calls | 1–2: designed after both losses were seen; parameter-free; its outcome is not yet observed | 1: 43 PF-bearing bugs, retrospective | 3: about 1,200 tests × at most 4 runs, no GPU | 3 | 17–18 | either lost bug stays lost; or the flag fires for PF tests among those with few mutants; or TNR gain over KUU vanishes |
| 7 | e-Otter++-style patch arm | baseline | — | — | — | — | 1 | 1 | 0 | 0 | — | section 4 |
| 8 | No method: registered confirmation reported as an empirical result | empirical | n/a | n/a | 3 | n/a | 3 | as registered | 3 | 3 | — | n/a |

Why candidate 6 and not the others.

- The confirmation removed one of CFP's two observables. A contribution has to stand on the surviving one.
  Candidates 1 and 5 lean on both; candidates 2 to 4 rearrange existing signals.
- The audit shows *how* the surviving observable fails: both bugs it has ever lost (`Codec_13` in the pilot,
  `Math_59` here) are faults the six operators cannot touch, so every mutant is silent although the failure plainly
  depends on the method. A check that asks the direct question ("does this failure depend on the method under test
  at all?") by replacing the method wholesale is the principled repair, not a tuned threshold.
- The same check gives a verdict where the registered flag cannot (fewer than ten mutants: 125 of 572 tests,
  including 19 PF tests that only the minimum protects).
- It is cheap enough to finish and model-free, so no judge budget has to be matched.

Why it may fail, stated now: the two predictions about `Codec_13` and `Math_59` are reasoned from the source, not
run; wrong tests whose failure depends on the method's value (most wrong assertions) stay kept, so the yield may be
lower than CD's; a bug-revealing test can fail before reaching the method it was generated for when the fault sits
in another fix-changed method or a constructor; and the safest level of the ladder is close to a reachability
check, which a reviewer may call trivial (section 7, challenges 5 and 7).

## 6. Decision

- **Primary direction:** candidate 6, as an **exploratory method contribution** evaluated retrospectively on the
  pilot and confirmation tests. Specification: `TECHNICAL_METHOD_SPEC.md`; protocol and handoff:
  `OPUS_EXECUTION_BRIEF.md`.
- **Fallback:** candidate 8. If the run fails its stop conditions or its primary criterion, the paper is the
  registered empirical result with the audit's qualifiers and no new method.
- **Stage B (candidate 1):** not before 15 November; reasons and a revised design in `STAGE_B_FINAL_PROTOCOL.md`.
- **Paper type:** empirical study with a registered confirmation (the confirmatory core) plus one exploratory
  mechanism study (candidate 6). Not a method paper.

### Contribution statement the evidence supports today

1. An execution-grounded measurement of LLM failure triage on repository-level Java with lost bug-revealing tests
   as an outcome (existing; unchanged).
2. A registered confirmation, on 572 fresh failing tests in 104 unseen real bugs with a control group, of two
   mutation-derived observables as evidence of fault side: the fail-to-pass observable did not replicate; the
   no-change observable was supported in the pooled analysis with 135 of 136 flagged tests wrong, and its yield
   was confined to one sampling frame and largely to two projects.
3. A model-free baseline rate that was missing from the literature read: a single small edit makes a failing
   generated test pass for 22–26% of failures whether the test is right (0.255), wrong (0.226), or aimed at a
   method the fix did not change (0.220).
4. (Only if the extension runs and is reported as exploratory.) Whole-method dependence probes: a direct test of
   whether a failure depends on the method under test, with its rates under execution labels on 928 failing tests.

## 7. Reviewer-style novelty challenge and rebuttal

**Challenge 1.** "This is ProFL's patch categories relabelled. NoneFix is your decoupled; CleanFix is your flip."
*Rebuttal.* Agreed for the executions, and the paper says so. ProFL ranks program locations and, in the text we
read, treats the suite as the oracle. We ask the question it presupposes and report the rates under execution
labels, including a negative result for the CleanFix-like observable. We claim the measurement, not the mechanism.

**Challenge 2.** "e-Otter++ already validates failing tests against program variants and gains 15 points. Yours
failed." *Rebuttal.* Correct, and the comparison is informative rather than embarrassing: e-Otter++ conditions its
patches on an issue that describes the fault; our edits are blind. The confirmation shows blind single edits do not
carry the positive signal. e-Otter++ has no negative reading, which is the part that held up here. We did not
reproduce e-Otter++ and say so.

**Challenge 3.** "Whole-method replacement is Descartes. Nothing new." *Rebuttal.* The transformation is theirs and
is cited as such. They ask whether a *passing* suite notices that a method's body is gone; we ask whether a
*failing* test's failure survives it. In the sections read of both papers no failing test is transformed and no
test is judged invalid (Niedermayr et al. exclude tests that fail on the original code). The result is presented as
exploratory.

**Challenge 4.** "Your supported hypothesis is one project." *Rebuttal.* We report that ourselves: 117 of 135
flagged wrong tests are in two Jackson projects, and the estimate without them is +0.041 [−0.035, 0.108]. We claim
precision (135 of 136), not yield, and we give yield by frame and project.

**Challenge 5.** "Deciding that a test never reaches its target is trivial; any coverage tool does it."
*Rebuttal.* Partly agreed, and it is the reason for the extension: it measures how much of the decoupling signal is
plain non-reachability and how much is not. Coverage would not tell a failure that executes the method but does not
depend on its result from one that does. We have not found the rate of either among failing generated tests
reported against execution labels in the works read; if a reviewer knows one, the contribution reduces to the
registered measurement.

**Challenge 6.** "A post hoc rule that rescues the two cases you already saw." *Rebuttal.* Yes, and it is labelled
exploratory for that reason. What limits the freedom: the rule has no tuned parameter; its return-value
replacements are those of Niedermayr et al. and Vera-Pérez et al., with one added variant (throw on entry) defined
before any run; it was fixed in a committed protocol before it was run; and its evaluation also covers 102 tests
that the earlier rule left undecided and that were not used to design it.

**Challenge 7.** "If most decoupled failures simply never reach the method, the mutation machinery was never
needed." *Rebuttal.* That is a possible outcome of the extension and we would report it as the finding: the part of
CFP that survived confirmation would then reduce to one extra execution per test. The ladder exists to measure
exactly that split.
