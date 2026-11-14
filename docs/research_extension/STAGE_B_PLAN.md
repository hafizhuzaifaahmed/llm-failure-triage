# Stage B plan: does probe evidence help a judge?

Plan only. No call has been made and no code for it exists yet. It needs a study-server session, so it starts only
on the authors' word. It is separate from the confirmation in `OSF_PREREGISTRATION_CFP.md` and touches none of its
frozen files.

## 1. Question

The pilot wrapped judges from the outside with certificate rules. Stage B asks the question that design avoids:
given the probe's observations **inside** its evidence, does a judge decide better, and is any gain due to the
information or merely to a longer prompt?

## 2. Arms

| Arm | Evidence shown to the judge |
|---|---|
| **A** package | the study's evidence package at level S1, unchanged |
| **B** package + probe report | A plus a probe report built from this test's own ledger record |
| **C** package + shuffled report | A plus a probe report built from **another** test's ledger record |

**Probe report.** Rendered deterministically from the ledger, after the failure section, with citable ids. It holds
counts and edit kinds only: no source text, no identifiers, no line numbers.

```
[C1] 44 single edits of the method under test and its helper methods were compiled; this test was re-run on each.
[C2] 1 edit makes this test pass (kind: relational operator). Of 11 other generated tests of this method, 11 still pass with that edit.
[C3] 12 edits change the failure (another value or another exception); 31 leave the failure exactly as it is.
```
(Illustrative numbers.) When no edit compiled, `[C1]` says so and `[C2]`, `[C3]` state zero. The report never says
which side is at fault.

Why no code in the report: (i) at S1 the judge does not see the method body, so a code fragment would refer to
something outside its evidence; (ii) a shuffled report with foreign identifiers would be recognisable as foreign, and
arm C would stop being a control; (iii) a fragment could coincide with a line that exists only in the fixed version
and trip the leakage guard.

**Shuffle.** A seeded derangement: each test receives the report of a different test that (a) belongs to a different
bug and (b) has the same failure type (assertion failure or exception). Every report is used exactly once, so arms B
and C contain the same multiset of reports.

## 3. Matched budgets

| Budget | A | B | C | How it is matched |
|---|---|---|---|---|
| Model, digest, prompt set, decoding, seed schedule | same | same | same | one configuration file per judge |
| Calls per test | 1 | 1 | 1 | by construction |
| Output cap | same | same | same | 512 tokens thinking off; 8,192 thinking on (the D-130 configuration) |
| Input tokens | package | package + report | package + report | **B and C are matched exactly in aggregate** (same reports, permuted) and per test to within the digits of three numbers, because the template is fixed. A is shorter by the report: at most 80 words, against a mean package of about 1,700 tokens (measured on dev, frozen config), so under 8% |
| Wall time and GPU-seconds | logged | logged | logged | reported per arm from the call log |

The contrast that isolates information is **B − C**: identical length, format and position; only the content's link
to the test differs. **B − A** is the practical gain. **C − A** shows what added length and format do by themselves.
Realised input and output tokens per arm are reported from the call log; any arm whose mean input tokens differ from
B's by more than 2% (C) or 10% (A) is flagged.

## 4. Judges and data

| Item | Stage B-1 (exploratory) | Stage B-2 (confirmatory, only if B-1 shows an effect) |
|---|---|---|
| Data | D-110's common D1-test set, 177 tests; ledger `CFP_D1_TEST` already exists | F1 and F2 failures of the sealed fresh tranche |
| Judges | M1 one-shot, thinking off (3 replicates); M1 one-shot, thinking on (1 run) | the same |
| Calls | 1,593 + 531 | about 3 × 1,025 per judge |
| GPU time (from measured call times) | about 45 min + about 10.3 h | about 1.5 h + about 60 h; thinking-on would be run on a sample |
| Status | labels known: exploratory | needs its own registration addendum before any call |

## 5. Hypotheses and analysis

| ID | Contrast | Judge | Reading if supported |
|---|---|---|---|
| S1 | balanced accuracy B − C > 0 | thinking off | the judge uses the information |
| S2 | balanced accuracy B − C > 0 | thinking on | information still helps a reasoning judge |
| S3 | balanced accuracy B − A > 0 | thinking off | practical gain |
| S4 | balanced accuracy B − A > 0 | thinking on | practical gain |

- Bug-level cluster bootstrap, 10,000 resamples, paired; replicates averaged within a resample. Holm over S1–S4 in
  Stage B-2. Stage B-1 reports intervals without tests.
- Reported beside them: C − A; TPR, TNR, PF tests lost, bugs lost per arm; the share of decisions that cite a
  `[C…]` item; invalid-output rate per arm; the interaction (B − C with thinking off) − (B − C with thinking on).
- Reading the interaction: a gain with thinking off and none with thinking on means evidence substitutes for
  reasoning; a gain in both means they add; no gain in either means the judge cannot use this evidence and the
  certificate rules remain the only route.
- Comparator: the certificate rule CK + CD wrapped around arm A's decisions, on the same tests. If arm B does not
  beat it, putting the report inside the prompt adds nothing over applying the rule outside.

## 6. What must be built first (not frozen files)

1. `src/triage_ext/report.py`: the renderer and the seeded derangement, with unit tests (report is a pure function
   of the ledger record; derangement respects bug and failure type; every report used once).
2. A wrapper that appends the report to a copy of the package text and registers the `[C…]` ids so that citation
   checking accepts them. The study's `context_builder.py` and prompts are not edited.
3. Every augmented package must pass the existing leakage guard.
4. **Open check:** if the frozen judge prompt enumerates the id families a judge may cite, the three arms need one
   added sentence naming `[C…]`. In that case the modified prompt is used for all three arms, and the original
   prompt's arm-A results from the study are shown beside them as the anchor. This is settled by reading the prompt,
   before any call, and entered in the decision log.
5. Run names and one configuration file per judge added to the scope file (needs the authors).

## 7. Threats

- D1-test labels are known; B-1 cannot confirm anything.
- The thinking-on judge failed its development gate and truncates some outputs; cap-coding sensitivity is reported
  as in D-130.
- A judge may read the report as an instruction ("an edit makes it pass, so it is a program fault"). That is why
  the shuffled arm exists: if C moves decisions as much as B, the judge is following form, not content.
- One judge family. Other families are a follow-up (J-T1).
