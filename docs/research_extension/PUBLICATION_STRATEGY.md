# Publication strategy after the confirmation

Date: 2026-11-13. A plan for the authors to approve; the manuscript was not edited. It replaces the story in
`PAPER_RESTRUCTURE_PLAN.md` §3–§4, which assumed the pilot would replicate. Numbers are from
`generated/confirm_report.md` and `CONFIRMATION_INDEPENDENT_AUDIT.md`.

## 1. What kind of paper this is now

**An empirical paper with a registered confirmation at its centre.** Not a method paper.

| Option | Verdict |
|---|---|
| Method paper on CFP ("flip and decoupling certificates") | **No.** The flip half did not replicate; the keep certificate has no support; the discard certificate lost a bug and is inconclusive after correction |
| Method paper on KUU and the cascade | **No.** Multi-family voting, unanimity and escalation exist in prior work; on the confirmation tests KUU is a baseline (TPR 1.000, TNR 0.316) |
| **Empirical study: (i) execution-grounded measurement of LLM triage; (ii) a registered test, on fresh real faults with a control group, of whether single-edit counterfactual outcomes carry evidence of fault side; (iii) an exploratory analysis of what the surviving signal is** | **Yes.** Every part is supported by committed data, and the negative result is informative: it corrects a pilot effect of 0.51 to 0.03 and gives a base rate the literature read does not report |
| Short negative-results paper on C1 alone | possible as a fallback venue format; loses the measurement and the supported half |

The paper's value is its honesty about a non-replication inside a frozen, sealed, registered pipeline. That is
what distinguishes it from the many unregistered positive results on the same benchmarks.

## 2. Title options

1. *Program Fault or Test Fault? LLM Triage of Failing Generated Unit Tests and a Registered Test of Mutation
   Evidence* (keeps the current title's question; recommended)
2. *Does One Small Edit Tell Whether a Failing Generated Test Is Right? A Registered Confirmation on Fresh Real
   Faults*
3. *Opinions and Executions: Measuring LLM Judges and Counterfactual Program Edits for Triage of Failing Generated
   Unit Tests*

Avoid "improving" in the title unless the WDP criterion is met, and then only inside the paper, not the title.

## 3. Contribution statement (replace the current one)

1. **Measurement.** An execution-grounded evaluation of LLM failure triage on repository-level Java against
   buggy/fixed labels, counting lost bug-revealing tests and lost bugs. (Existing; unchanged numbers.)
2. **Judge-only rules as one trade-off.** Voting, debate, cross-family unanimity and escalation occupy one
   TPR–TNR curve; KUU is the keep-heavy end and serves as the baseline. (Existing; reframed. No method claim.)
3. **A registered confirmation with a control group** (OSF kp79c; 572 fresh failing tests, 104 bugs, 21 with a
   bug-revealing test; 246 control failures) of two mutation-derived observables:
   - a single edit that makes the test pass is **not** more frequent for bug-revealing tests
     (+0.028 [−0.137, 0.274]); the pilot's 0.51 is excluded; the rate is about 22–26% for right tests, wrong
     tests and control failures alike;
   - a failure that no single edit changes is more frequent for wrong tests in the pooled analysis
     (+0.243 [0.114, 0.372], Holm p 0.0024); 135 of 136 such failures are wrong tests; the effect is absent in
     one sampling frame and 117 of the 135 lie in two projects;
   - the two certificate rules are inconclusive after correction; one of them lost one bug of 21.
4. **(Exploratory; only after its run and interpretation review.)** A direct test of whether a failure changes
   when the method under test is replaced wholesale, which separates failures for which no entry into the method
   was observed from failures the edit operators could not touch, with their rates under execution labels.
   Level U is reported as an operational observation ("no entry observed, throw-invariant"), never as proof that
   a test cannot reach the method. The descriptive ladder is reported even if the primary criterion is not met,
   provided the run passes its quality checks; if WDP is not finished in time it appears as future work only.

Each item names its evidence status in the text (section 9).

## 4. Research questions

| RQ | Question | Status |
|---|---|---|
| RQ1–RQ3 | as in the current paper (accuracy and lost tests; specification level; matched-budget deliberation) | confirmatory family of the original study, unchanged |
| RQ4 | How far do judge-only rules go, and what is the strongest keep-heavy baseline? | exploratory in the original study; KUU becomes "baseline", not "method" |
| RQ5 | On fresh real faults, do single-edit counterfactual outcomes of the method under test differ between bug-revealing and wrong failing tests? (C1 flip, C2 decoupled) | **confirmatory, registered** |
| RQ6 | Do rules built on those outcomes improve a base rule without losing bugs? (C3, C4; safety outcome) | **confirmatory, registered; underpowered by the registered planning** |
| RQ7 | Where does the decoupling signal hold (frame, project, failure type), and what is it? | exploratory (audit analyses; WDP if run) |

## 5. Section outline

1. **Introduction.** Problem unchanged. New last paragraph: the paper reports a registered confirmation in which
   one of two hypothesised signals failed and the other held with strong qualifiers.
2. **Background and related work.** Add the positioning table (section 7 of this file). State in so many words
   that the executions are those of MUSE, Metallaxis and ProFL and that only the question differs; that
   e-Otter++ validates failing tests against LLM patches conditioned on an issue and was not reproduced; that
   multi-judge voting and escalation are established (Wang et al., Becker et al., TestAgent).
3. **Study design of the measurement** (existing §3).
4. **Results of the measurement** (existing RQ1–RQ4; KUU and the cascade presented as operating points).
5. **Counterfactual program probes: hypotheses and pilot.** Definitions; the pilot (60 PF, 296 TF, 22 bugs) as
   exploratory, with its two estimates; why a confirmation was required.
6. **Registered confirmation.** Registration and what it covers; frames F1, F2 and control with their rules;
   sealing order with commit hashes; population flow; the registered family table; rule table with bugs lost and
   bounds; control group; registered secondary analyses; the registration's counting-against list.
   **Deviations and unmet planning:** 21 PF-bearing bugs against a planned 30–50 (D-145); line-ending handling
   (D-144); template-field reconciliation pending (one sentence, no detail).
7. **What the surviving signal is (exploratory).** Frame and project concentration; failure type; the ten-mutant
   minimum; the two lost bugs as operator gaps. If run: the dependence ladder and CD-U, under the status sentence.
8. **Discussion.** Why a pilot on 22 bugs with known labels overstated the effect (project concentration: 20 of
   40 flipping right tests in one project); what blind single edits cannot show; contrast with issue-conditioned
   patches; what a practitioner can use today (a conservative pre-filter with a measured cost, not a verdict).
9. **Threats to validity** (section 8 of this file).
10. **Conclusion.** Three sentences: the measurement; flip did not replicate; decoupling is precise where it fires
    and fires unevenly.

Appendices: registration text and hashes; frame construction; control-group matching and biases
(`CONTROL_GROUP.md`); audit matrix; per-project tables; power planning table; `STAGE_B_PLAN.md` summarised as
designed and not run.

## 6. Figures and tables

| ID | Content | Source | Status label on the caption |
|---|---|---|---|
| T-A | Population flow: 2,223 calls → 2,209 classes → failing tests → PF / TF / AMB, by tranche | D-144, D-145, dataset summaries | registered data |
| T-B | Registered family C1–C4: estimate, interval, p, Holm p, registered reading | `confirm_analysis_CFP_CONF_ALL.json` | confirmatory |
| F-A | Three flip rates with intervals: PF, TF, control | same | confirmatory (control: reported, not tested) |
| T-C | Pilot beside confirmation: flip and decoupled rates by label | `cfp_tables_CFP_D1_TEST.md`, confirmation JSON | pilot exploratory; confirmation confirmatory |
| T-D | Rule table: TPR, TNR, PF lost, bugs lost, exact upper bound; balanced accuracy last | confirmation JSON | reported, not tested, except C3 and C4 |
| F-B | Forest plot of C2: pooled, F1, F2, leave-one-project-out, without the Jackson projects | secondary JSON files, audit scripts | registered secondaries and exploratory rows marked differently |
| T-E | Decoupled by failure type and stack frame, by label | audit | exploratory |
| T-F | Positioning: MUSE, Metallaxis, ProFL, e-Otter++, judge triage, pseudo-tested methods, this study | `UPDATED_NOVELTY_AND_CONTRIBUTION_ASSESSMENT.md` §2 | — |
| T-G | Evidence status of every result in the paper | `OPUS_EXECUTION_BRIEF.md` §7 | — |
| F-C, T-H | Dependence ladder by label and frame; WDP rule table | `wdp_analysis.json` | exploratory; not externally preregistered |

Existing figures and tables of the measurement stay. The rates figure of RQ4 stays as the judge-only frontier.

## 7. Positioning sentences (to be used nearly verbatim)

- "Running first-order edits of a program against a failing test is the mechanism of mutation-based fault
  localization (MUSE, Metallaxis) and of unified debugging (ProFL), whose CleanFix and NoneFix outcomes correspond
  to our flip and decoupled observables. Those techniques take the failing test as valid and infer where the fault
  is. We ask the question they presuppose."
- "e-Otter++ keeps candidate reproduction tests that fail on the original code and pass on at least one
  LLM-generated patch derived from the issue. It requires an issue report and selects among candidates; it does
  not label a test wrong. We did not reproduce it."
- "A flip is a mutation outcome, not a repair: prior work shows that a single-edit plausible patch is usually not
  the developer's fix (PraPR; Qi et al.), and our confirmation shows it is not evidence that the test is right
  either."
- "Whole-method replacement is extreme mutation as used to find pseudo-tested methods (Niedermayr et al.;
  Vera-Pérez et al.), applied there to passing test suites."
- "A control method is a method the developer's patch did not change. It is not known to be free of defects."

## 8. Threats to validity (to be written out)

| Kind | Threat | What the paper says |
|---|---|---|
| Statistical conclusion | 21 bugs with a bug-revealing test against a planned 30–50; one bug holds 24% of the PF tests; percentile cluster bootstrap with few clusters | C2–C4 underpowered as registered; C1's interval has the planned width for 30 bugs and excludes the pilot's effect but not half of it; intervals approximate |
| Statistical conclusion | bugs are resampled, projects are not | project concentration table; estimate without the two projects |
| Internal | the ten-mutant minimum decides 102 tests | reported by label |
| Internal | frame F2 differs from the pilot's frame | registered as a known limitation; F1 and F2 shown separately |
| Internal | 11 packages refused by the leakage guard | excluded from C3 and C4 only, as registered; 10 TF, 1 PF |
| Construct | TF means "fails identically on the fixed version"; a second real fault is labelled TF | stated; no label audit exists |
| Construct | control methods are "not changed by the fix", in classes that needed a fix | stated wherever the control appears |
| Construct | balanced accuracy hides a lost bug | bugs lost and TPR/TNR lead every rule table |
| External | one benchmark, one language, one generator, tests aimed at fix-changed methods or their classmates; benchmark likely in the models' training data (the probe uses no model) | stated |
| External | no comparison with a patch-based validator on the same tests | e-Otter++ discussed, not reproduced; planned |
| Reporting | exploratory analyses were chosen after seeing the confirmation | each carries its label; the registered tables are printed unchanged and first |
| Reporting | registration template fields were reworded at deposit and their reconciliation with the attached document is pending | one sentence; the attached frozen bundle governs |

## 9. Evidence-status vocabulary (mandatory)

| Word | Used only for |
|---|---|
| confirmatory, registered | C1–C4 and what the registration lists as reported or secondary (OSF kp79c) |
| pre-specified, unregistered, not run | the Stage B plan |
| exploratory | the pilot; the audit's additional analyses; everything from WDP |
| "exploratory; protocol frozen internally in Git before the run; not externally preregistered" | WDP, every time it is introduced (abstract, section 7, captions, conclusion) |

Any Stage B or WDP protocol run before 16 November 2026 was not externally preregistered, and the paper says so
in the section that reports it.

## 10. What the paper must not say

- that flip evidence works, that CK is validated, or that the certificates are safe;
- "significant" for C3 (unadjusted p 0.047, Holm p 0.142);
- that C2's +0.243 is an effect size that generalises, or that C2 holds "across frames";
- that the confirmation proves there is no flip effect;
- that control methods are correct or defect-free;
- that a mutant that makes a test pass is a fix;
- "first", "novel", "state of the art", or that no prior work exists;
- that e-Otter++, ProFL, MUSE or Metallaxis were reproduced or outperformed;
- "preregistered" or "confirmatory" for the pilot, the audit analyses, Stage B or WDP;
- any improvement over a published number from a different sample.

## 11. Abstract skeleton (numbers from the numbers map)

Problem (two sentences, as now). Measurement result (one sentence, existing). "We then tested, in a study
registered before any data existed, whether re-running a failing test on single-edit variants of the method under
test tells which side is at fault. On 572 fresh failing tests from 104 unseen real bugs, an edit that makes the
test pass was no more frequent for bug-revealing tests than for wrong ones (difference 0.03, 95% CI −0.14 to
0.27) or for failures on methods the fix did not change; an exploratory pilot had suggested 0.51. A failure that
no edit changes was a wrong test in 135 of 136 cases (difference 0.24, 0.11 to 0.37), but only in one of two
sampling frames and mostly in two projects. Rules built on these outcomes were inconclusive, and one lost a bug."
One sentence on WDP if run, with its status. One sentence on the implication: the only execution-based
signal that survived concerns whether the failure depends on the method at all, and an effect of 0.51 in a 22-bug
pilot with known labels did not survive a registered test.

## 12. Venue positioning

Deadlines are not asserted here; check the official pages.

| Venue type | Fit |
|---|---|
| The course submission (15 November) | the revised manuscript as specified here |
| Empirical Software Engineering (journal) | best fit for a measurement plus registered confirmation with a non-replication; long threats section welcome |
| Replication and negative-results tracks at software engineering conferences | a short version centred on RQ5 and RQ6 |
| ISSTA, ASE, ICST research tracks | only with a second generator or benchmark and, for a method claim, a fresh registered test of WDP |

## 13. After the deadline (future work, to be listed as such)

1. A registered test of CD-U on tests no probe or judge has seen (second generator or another benchmark); only
   with the authors' approval of any external registration.
2. An LLM-patch arm without an issue report (variant P-b) and, separately labelled, with one (P-a).
3. An independent label audit of TF.
4. Stage B v2, if the ladder shows a graded signal a judge could use.
