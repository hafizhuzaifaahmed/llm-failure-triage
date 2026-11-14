# Control group: failures on methods the fix did not change

Decision D-138 (definition), D-140 (authors' approval and wording). Counts below are computed from
`configs/extension/confirm_frame.jsonl`; nothing has been generated for any of these methods.

## 1. What the control group is, and what it is not

A **control method** is a method that the developer's fix for a given bug did **not change**: its body is identical in
the buggy and the fixed version.

It is **not** claimed to be free of defects. The fix repairs one reported bug; a control method may contain an
unrelated, unreported fault, may behave wrongly because it calls a method the fix did change, or may sit in a class
whose state the fault corrupts. "Not fix-changed" is a fact about the patch, not about correctness.

What the control group estimates: how often a single small edit makes a failing generated test pass, and how often
no edit changes the failure, **when the method under test is not where the known fault was repaired**. This is the
flip rate a deployed triage stage would mostly face, since most methods a generator targets are not under repair.

## 2. Selection criteria (all applied to the buggy version unless stated)

For each of the 322 confirmation bugs, candidate control methods are taken from the class file of that bug's tranche
methods, visited in order of focal identifier. A method is eligible when it is:

1. a method (not a constructor) with a body, not `abstract` or `native`;
2. `public` or `protected`;
3. present in the fixed version with the same name and signature, and with a body that is identical after whitespace
   normalisation (this is the only use of the fixed version: frame construction, as in the original study);
4. not named like any method the fix changed in that bug (so an overload of a repaired method cannot be a control);
5. able to yield at least five first-order mutants under the frozen operator set.

Criterion 5 is label-free and exists because a method with nothing to mutate cannot show a flip either way.

## 3. Matching procedure

Among eligible methods of the first class that has any, the one whose number of first-order mutants is closest to
that of the bug's tranche method in that class is chosen; ties are broken by method name, then parameter types.
The choice is deterministic: no random draw and no seed. One control per bug.

Matching is on **opportunity to flip** (how many edits the probe can try), not on behaviour, size in lines, cyclomatic
complexity, call depth or test difficulty.

| Quantity | Value |
|---|---|
| Bugs in the confirmation frame | 322 |
| Bugs with a control method | 246 |
| Bugs without an eligible method | 76 |
| Controls matched to an F1 method / an F2 method | 44 / 202 |
| Mutants in the control method: median (quartiles) | 10 (6, 22) |
| Mutants in the matched tranche method: median (quartiles) | 11 (3, 29) |
| Absolute difference in mutant count: median | 4 |
| Pairs within 5 mutants / within 10 mutants | 134 / 186 of 246 |
| Control has more mutants / fewer mutants than its match | 123 / 93 |
| Matched tranche methods with zero mutants | 16 |

## 4. Project distribution

| Project | Bugs in frame | Bugs with a control | Share |
|---|---|---|---|
| Chart | 8 | 8 | 1.00 |
| Closure | 55 | 36 | 0.65 |
| Codec | 5 | 2 | 0.40 |
| Compress | 16 | 16 | 1.00 |
| Csv | 3 | 3 | 1.00 |
| JacksonCore | 11 | 11 | 1.00 |
| JacksonDatabind | 80 | 65 | 0.81 |
| JacksonXml | 4 | 4 | 1.00 |
| JxPath | 16 | 13 | 0.81 |
| Lang | 26 | 22 | 0.85 |
| Math | 72 | 51 | 0.71 |
| Mockito | 15 | 5 | 0.33 |
| Time | 11 | 10 | 0.91 |
| **Total** | **322** | **246** | **0.76** |

JacksonDatabind, Math and Closure supply 152 of the 246 controls (62%).

## 5. Selection biases, stated in advance

| Bias | Direction and consequence | Handling |
|---|---|---|
| **Same class as a repaired method.** Controls share fields, helpers and callers with the faulty code | A control test can fail because of the known fault (through shared state or a call into a changed method). Such a test passes on the fixed version and is labelled PF | Counted and reported separately; the control estimate uses control failures labelled TF. The count of control PF is itself informative: it is how often a fault is revealed through a method the fix did not touch |
| **Minimum of five mutants.** Trivial accessors and delegators are excluded | Controls are more "mutable" than a typical method; this raises the chance of a flip and makes the control a conservative (harder) comparison for the method | Stated; the F1/F2 methods have no such floor, and 16 matched tranche methods have zero mutants |
| **Imperfect matching.** Only 134 of 246 pairs are within five mutants; controls tend to have slightly more mutants where the tranche method is tiny and fewer where it is large | Flip opportunity is not equal within pairs | The analysis reports rates, not paired differences. Mutant counts per test are in the ledgers and are reported descriptively beside the rates |
| **76 bugs have no control**, unevenly: Mockito 10 of 15, Closure 19 of 55, Math 21 of 72 lack one | The control sample under-represents classes with few public unchanged methods (small classes, or classes the fix rewrote broadly) | Project distribution reported (section 4). A comparison restricted to bugs that have a control is exploratory: the frozen script run on those bugs' frame rows |
| **Public or protected only**, same as the tranche methods | No bias between groups; limits both to the visible API | — |
| **One control per bug**, tranche bugs have up to three methods and F1 has six generations | Control failures are fewer per bug | Rates are bug-clustered; intervals resample bugs |
| **Generated by the same model from buggy-version context** | A wrong test on a control can still encode behaviour of the buggy class | Inherent to the setting; identical for all groups |
| **Not fix-changed is not correct** | A control may have an unknown fault; a test revealing it fails on both versions and is labelled TF | Cannot be removed without an independent audit; stated wherever the control is reported. It biases the control's TF flip rate upward if unknown faults are small-edit faults |

## 6. What the control group cannot show

- It does not give the flip rate on arbitrary correct code: every control sits in a class that needed a fix.
- It does not validate labels.
- It is reported, not tested: no hypothesis in the registered family depends on it, and no threshold is derived from
  it.

## 7. How it is used in the analysis

The frozen analysis script reports, for control failures labelled TF, the flip rate with a bug-level 95% interval and
the decoupled rate, beside the flip rates for TF and PF failures of the F1 and F2 methods. The registration states in
advance that a control flip rate close to the PF flip rate would count against the method.
