# Preregistration: counterfactual program probes for triaging failing generated unit tests

> **Status: final text prepared for deposit. Not yet registered.** External registration on OSF was approved by the
> authors on 2026-11-11 and must be completed before any test is generated. When it is deposited, its identifier,
> URL and timestamp are recorded in `configs/extension/osf_registration.json` together with the content hash of this
> file; the generation driver refuses to run until that record exists and matches this text.
>
> Sections follow the OSF Preregistration template.

## Study information

**Title.** Counterfactual program probes for deciding whether a failing generated unit test or the program is at
fault: a confirmatory study on fresh real faults.

**Authors.** Hafiz Huzaifa Ahmed (corresponding author, i267612@isb.nu.edu.pk) and Saad Ilyas
(i267630@isb.nu.edu.pk), Department of Computer Science, FAST – National University of Computer and Emerging
Sciences, Islamabad, Pakistan. (As given in the project's manuscript; to be confirmed by the authors at deposit.)

**Description.** LLM test generators produce failing tests. A failing test either reveals a real fault in the
program (program fault, PF) or is itself wrong (test fault, TF). We test whether running the failing test against
small systematic edits (first-order mutants) of the method under test, on the buggy program only and without any
language model, yields evidence about which is the case.

**Prior evidence and its status.** An exploratory pilot on Defects4J real faults (repository decision D-137; 60 PF
and 296 TF failing tests in 74 bugs) found that a single edit makes a right test pass more often than a wrong one
(0.667 against 0.155) and that failures no edit changes are almost all wrong tests (61 of 62). The pilot's labels
were known to the analyst when the rules were written, and one design amendment was made after a development-split
run (D-135). The pilot is therefore not confirmatory. This study applies the same engine and rules, unchanged, to
bugs for which no test has ever been generated.

**Hypotheses** (directional; PF = fails on the buggy version and passes on the developer-fixed version; TF = fails on
both with identical failure signatures):

| ID | Hypothesis |
|---|---|
| C1 | A failing test that some single edit of the method under test (or of the same-class methods it calls) makes pass (`flip`) is more often PF: P(flip \| PF) > P(flip \| TF). |
| C2 | A failing test whose failure no such edit changes in any way (`decoupled`) is more often TF: P(decoupled \| TF) > P(decoupled \| PF). |
| C3 | Discarding decoupled failures improves a keep-unless-unanimous panel: balanced accuracy of KUU + CD exceeds KUU's. |
| C4 | Keeping failures with a sibling-safe flip reduces the bug-revealing tests a majority vote discards: PF tests lost by 2-of-3 + CK are fewer than by 2-of-3. |

## Design plan

**Study type.** Observational measurement on generated software artefacts; no human participants.

**Blinding.** The probe engine has no code path to the fixed version, to labels or to developer tests (enforced by a
unit test that scans its source). Labels are computed by execution, written to a new label file and committed before
any probe or judge reads an instance. Judge predictions are stored apart from probe records and are read only by the
analysis script; they are never used to change the engine or its rules. The analysis script is fixed by hash before
data exist.

**Study design.** Every failing generated test in the sealed set is probed once. Each test gets an evidence record
and, for C3 and C4, the one-shot votes of three local judges from different model families. Rules are compared with
their base rules on the same tests (paired).

**Randomisation.** None beyond seeded sampling: the frame's per-bug sample (seed 20261111), the engine's mutant and
sibling samples (seeded from the focal method identifier), generation seeds per call as in the original study.

## Sampling plan

**Existing data.** Registration prior to creation of data. The buggy and fixed program versions are public
(Defects4J 3.0.1). No test for any bug in this study has been generated. The generation inputs (one context per
method) have been extracted from the buggy versions and are fixed by hash in the dataset manifest.

**Data collection procedure.**

1. *Frame* (`configs/extension/confirm_frame.jsonl`, built by `scripts/extension/build_confirm_frames.py`; held-out
   projects only; bugs the original study never generated for). Three tranches with separate records and dataset
   tags:
   - **F1** (`D1C_F1`): 62 methods in 53 bugs. Methods of the original frame (fix-changed, present in both versions,
     public or protected, invoked by name in a bug-triggering test) that the original per-project cap excluded. Six
     generations per method.
   - **F2** (`D1C_F2`): 371 methods in 269 bugs. Fix-changed public or protected methods present in both versions
     whose only exclusion from the original frame was that no bug-triggering test invokes them by name; at most three
     per bug by seeded sample. Three generations per method.
   - **Control** (`D1C_CTRL`): 246 methods in 246 bugs. One method per bug that the fix **did not change**: same
     class as a tranche method, public or protected, body identical in both versions, not named like any fix-changed
     method of that bug, at least five first-order mutants; the one whose mutant count is closest to the tranche
     method's (deterministic; ties by name). Three generations per method. 76 bugs have no eligible method and
     contribute no control. **A control method is not claimed to be free of defects**: it is a method the developer's
     patch left untouched. Matching, project distribution and selection biases are documented in
     `docs/research_extension/CONTROL_GROUP.md`.
2. *Generation.* Gemma 4 26B (`gemma4:26b`, Q4_K_M, digest `001e5dafc3c7…`), Ollama 0.40.13, temperature 0.7, top-p
   1.0, top-k 64, context 8,192, at most 4,096 output tokens, thinking off, the frozen generator prompt
   (`8b08a25d…`), buggy context. 2,223 calls (372 + 1,113 + 738).
3. *Execution and labels.* Each test method alone in its own class copy, three runs on the buggy and three on the
   fixed version, fresh JVM, 30 s limit; the original label rule and exclusions (non-compiling, flaky, timeout,
   environment, AMB) unchanged.
4. *Sealing.* Labels are committed before any probe or judge call. The commit hash is recorded.
5. *Probes.* `scripts/extension/run_probes_tranche.py` with the frozen engine, one run per tranche.
6. *Judge votes.* One-shot judgements of M1 (Qwen3.5 9B), M2 (Gemma 4 12B) and M3 (Ministral 3 14B) at
   specification level S1 with the frozen prompts and decoding, on every F1 and F2 failing test. The control group is
   not judged.

**Sample size.** Fixed by the frame: every frame row, the stated number of generations. 322 bugs, 679 methods.

**Sample size rationale and planning.** The frame contains every unseen bug of the benchmark that either rule admits.
The number of bugs that will yield at least one PF test is not controlled. It is expected to lie between 30 and 50
(an extrapolation: 16% of bugs yielded one under the original frame, and the F2 rule has never been run). An earlier
internal draft targeted 60; that is not reachable and is not promised.

A planning simulation on the pilot data (repository decision D-140; planning only) resampled the pilot's bugs to sets
with 30, 40 and 50 bugs carrying a PF test, under the pilot's effect and under half of it. Entries are the share of
simulated sets in which the hypothesis would be supported at the strictest Holm step (p < 0.0125) with the predicted
sign:

| Bugs with a PF test | Scenario | C1 | C2 | C3 | C4 |
|---|---|---|---|---|---|
| 30 | pilot effect | 0.980 | 0.963 | 0.738 | 0.302 |
| 40 | pilot effect | 0.998 | 0.998 | 0.843 | 0.520 |
| 50 | pilot effect | 1.000 | 1.000 | 0.927 | 0.748 |
| 30 | half effect | 0.830 | 0.362 | 0.058 | 0.128 |
| 40 | half effect | 0.927 | 0.500 | 0.087 | 0.175 |
| 50 | half effect | 0.988 | 0.552 | 0.098 | 0.362 |

Median 95% interval half-widths at 30 / 40 / 50 bugs under the pilot's effect: C1 0.204 / 0.179 / 0.158;
C2 0.098 / 0.086 / 0.077; C3 0.043 / 0.037 / 0.033 (balanced accuracy).

Exact one-sided 95% upper bounds on a rule's bug-loss rate:

| Bugs with a PF test | 0 bugs lost | 1 bug lost | 2 bugs lost |
|---|---|---|---|
| 30 | 0.095 | 0.149 | 0.195 |
| 40 | 0.072 | 0.113 | 0.149 |
| 50 | 0.058 | 0.091 | 0.121 |

**Classification, by a rule fixed before the simulation was run** (adequate = share ≥ 0.80 at p < 0.0125 under half
the pilot's effect with 30 bugs):

| Hypothesis | Classification | How a non-supported result will be read |
|---|---|---|
| C1 | **adequately powered** | evidence against the claim |
| C2 | **underpowered** (adequate only if the pilot's effect holds in full) | inconclusive unless the interval excludes the pilot's estimate |
| C3 | **underpowered** | inconclusive |
| C4 | **underpowered** | inconclusive |

The simulation's limits: it reuses 22 pilot bugs, so it cannot represent between-bug variation the pilot did not
contain; C3 and C4 were simulated on the pilot's 1:2 sample of test faults, while the confirmation judges every
failing test; the pilot's effects may be inflated. The study is not designed to reach any bug count.

**Stopping rule.** None, and none that depends on outcomes. Data collection ends when every frame row has its
generations. No count of labels, flips or bugs is consulted while collecting. A call that fails for a technical
reason is retried under the original study's rules; a method whose generations cannot be produced is reported as
missing.

## Variables

**Manipulated.** None (the evidence is computed, not assigned). Rules are applied to the same tests.

**Measured, per failing test** (engine output; definitions frozen in `src/triage_ext/ledger.py`):

- class of each compiled mutant: FLIP (test passes twice), SHIFT (fails with another outcome type, exception class,
  failing line or message), SAME, ERR (timeout, harness error, or a pass that did not repeat);
- `flip`: at least one FLIP; `rcf`: at least one FLIP on which no sibling test fails; `decoupled`: at least ten
  compiled mutants and none FLIP or SHIFT.

Engine parameters (frozen): operators ROR, AOR, COR, LVR, NEG, STD; at most 80 mutants per focal method (focal body
first, then same-class callees to depth 2); 10 s per mutant run; at most 30 sibling tests per flip; 12 parallel JVMs.

**Decision rules** (frozen in `src/triage_ext/policy.py`): CK keeps a test with `rcf`, otherwise the base rule
decides; CD discards a `decoupled` test, otherwise the base rule decides. Base rules: KUU (discard only if all three
valid votes say test fault; an invalid vote keeps) and 2-of-3 (discard if at least two valid votes say test fault).

**Outcomes.** Execution label (PF, TF). For rules: TPR (share of PF kept), TNR (share of TF discarded), balanced
accuracy, PF tests lost, bugs lost (a bug with a PF test and none kept).

## Analysis plan

**Statistical models.** `scripts/extension/confirm_analysis.py` (hash below).
Unit of resampling: the bug. Bug-level cluster bootstrap, 10,000 resamples, seed 20261011, identical resamples for
paired differences; two-sided bootstrap p with the (+1)/(B+1) correction, as in the original study.

- C1: P(flip | PF) − P(flip | TF) on all scored F1 and F2 failures.
- C2: P(decoupled | TF) − P(decoupled | PF), same population.
- C3: balanced accuracy of KUU + CD minus KUU, on F1 and F2 failures with three votes.
- C4: PF tests lost by 2-of-3 + CK minus 2-of-3, same population.

**Inference criteria.** One Holm family over C1 to C4, α = 0.05. A hypothesis is *supported* when its Holm-adjusted
p is below 0.05 and the difference has the predicted sign; otherwise *not supported*, read according to the
classification above. An effect in the opposite direction is reported as such.

**Data exclusion.** Tests excluded by the original label rule. An instance the engine excludes (method not located,
class does not recompile, test does not compile alone, stored failure not reproduced) stays in the population with
all flags false, so that exclusions cannot favour the method. An instance with fewer than ten compiled mutants keeps
its `flip` and `rcf` flags and can never be `decoupled`. Both counts are reported by label. Development-project
methods are not in the frame.

**Missing data.** A missing or invalid judge vote keeps the test under KUU and is not a discard vote under 2-of-3.
Tests without three votes are excluded from C3 and C4 only, with the count reported.

**Safety outcome (reported, not tested).** Bugs lost by each rule and its base, with the exact binomial one-sided 95%
upper bound on the bug-loss rate over bugs with a PF test.

**Control group (reported, not tested).** On control failures: the flip rate among TF with a bug-level 95% interval
and the decoupled rate among TF, beside the flip rates for TF and PF in F1 and F2. Control tests labelled PF (the
test reveals the fault through a method the fix did not change) are counted and reported separately.
The control answers one question: how often does a single edit make a failing test pass when the method under test
is not one the fix changed.

**Secondary analyses** (stated in advance; none can replace a primary result):

1. `rcf` in place of `flip` in C1.
2. A guarded decoupling flag, never applied when the failure is an exception raised inside the method under test.
3. Flips restricted to literal, relational and statement-deletion edits.
4. Flips shared with another failing test of the same method.
5. Focal-body-only region.
6. Leave-one-project-out for C1 and C2.
7. F1 and F2 separately (the same frozen script run on the F1 rows and on the F2 rows of the frame); the frame rule
   is a factor a reader will ask about.

**Exploratory analysis.** Anything else is labelled exploratory.

## What would count against the method

- C1 not supported (the adequately powered test).
- C2 significant in the opposite direction, or its interval excluding the pilot's estimate from below.
- CD or CK raising the number of bugs lost above its base rule by more than one bug.
- A flip rate among control failures close to the flip rate among bug-revealing tests.

## Other

**Deviations.** A change to any file listed below, to the frame, or to this plan after registration is a deviation:
recorded in `docs/tracking/DECISIONS.md` before the affected result is computed and listed in the paper.
`tests/extension/test_freeze.py` fails if a frozen file or parameter changes.

**Known limitations stated in advance.** One benchmark, one language, one generator. Every test targets a
fix-changed method or a method of a class the fix touched. The benchmark is likely in the training data of the
generator and judges; the probe itself uses no model. F2 is a different sampling rule from the pilot's frame.
The expected number of bugs with a bug-revealing test is small, and three of the four hypotheses are underpowered.

**Relation to prior work.** The observables are those of mutation-based fault localization (fail-to-pass under
mutation: MUSE; any change of test outcome under mutation: Metallaxis) and of unified debugging (ProFL), which read
them as evidence of *where* a fault is and take the failing test as valid. Candidate-patch validation of failing
tests exists for issue reproduction with LLM-generated patches (e-Otter++). No claim of novelty is made in this
registration.

**Frozen materials** (content hash = sha256 of the file with CRLF normalised to LF; manifest
`configs/extension/cfp_frozen.json`, frozen 2026-11-11T16:25:54Z; the four engine files are byte-identical to
repository commit `eb2d231`, the engine that produced the pilot):

| File | sha256 |
|---|---|
| `src/triage_ext/mutate.py` | `e12647ef93d09685af008cf61fa28ae7c5919380e1308431330472f3b3abf613` |
| `src/triage_ext/probe.py` | `a06ac514b37c2d94c0b4cf3f9557dbfc2ea1eb7daf88ef927c8e191d8125b966` |
| `src/triage_ext/ledger.py` | `88370f39aa989b788203f8ca085b7998bff2056919490500c29b3fffc37cb700` |
| `src/triage_ext/policy.py` | `9a160f2c28eb3596fa40907ebea958219d7925ca1bdcc6c5274b7aa94902ea8d` |
| `scripts/extension/run_probes_tranche.py` | `6793890e646ce9383b2f1eb432b5f6a81046a3a8094df264b7cf1665d7a33d14` |
| `scripts/extension/confirm_analysis.py` | `fa279868037c0766e055c80cb3096ce6a7a70b7d3aefc07916fd3c7ebde34b5e` |
| `scripts/extension/build_confirm_frames.py` | `4a15ddd8bb78cf2c6964b8d0f065af7d6aebe33afb2baa576835b81a8092d251` |
| `configs/extension/confirm_frame.jsonl` | `55d55c1e9aadaf5e9e2c2641dfd52639f95700198a601cf3af8c2285fcbb92a3` |

**Generation inputs** (`configs/extension/confirm_dataset_manifest.json`; one prompt hash per method; digest of the
sorted list per tranche):

| Tranche | Methods | Generations | Digest of prompt hashes |
|---|---|---|---|
| F1 | 62 | 372 | `a539db5a444f5e64769dc41c64c7599dd6aa1a2417b3be73692e930e62dabb6f` |
| F2 | 371 | 1,113 | `6fab8b6871495ba1a33933a2e7d3c50a0c9f3b9da0657538f2fe2d09ebcb86a3` |
| Control | 246 | 738 | `7b0e130c55d4c6bcdfc4fd43a5c141fa644f75d14142f5e2994e7cc861a04a8f` |

**To be completed at deposit.** Confirmation of the author list; whether the registration is public or embargoed.
