# Limitations and open questions

Each item cites where the evidence sits. "Validity" means the limitation could make a stated conclusion wrong;
"scope" means the conclusion holds but for fewer situations than a reader might assume.

## 1. Limitations that threaten validity

| # | Limitation | Evidence | Which conclusion it threatens |
|---|---|---|---|
| V1 | **Few independent units.** D1-test's 60 bug-revealing tests sit in 22 bugs; dev has 5 such bugs | `labels_D1.jsonl` (counted in `PROJECT_FACT_BASE.md`) | Every bug-level claim on real faults. With 22 clusters and zero observed losses, the 95% upper bound on the bug-loss rate is 12.7% |
| V2 | **Every local judge fails its development gate** (one-shot F1 below the rule baseline R0 on dev) | Paper Table G6; `configs/local_models.FROZEN.json` | RQ2 and RQ3: the nulls describe sub-gate judges, not specifications or architectures |
| V3 | **No confirmatory hypothesis survives correction**; design MDE ≈ 0.17 F1 for debate vs self-consistency | Table B2, Table C1 | Any reading of RQ1–RQ3 as a negative result |
| V4 | **The label rule misfiles second faults.** A test exposing a real fault the patch does not touch fails on both versions and is TF | §8.1; audit: both mismatches of 71 items are execution-TF judged PF (`results/audit`) | TNR of every rule is slightly overstated, PF loss slightly understated; direction known, size unmeasured on held-out data |
| V5 | **Raters are the authors, saw the fix, rated dev items only** | §8.1, D-108 | The label-validity claim |
| V6 | **RQ4 is a chain of follow-ups chosen after earlier results**; its tests were fixed before their calls, the choice of what to test was not | §8.1; D-95, D-105, D-109, D-130, D-132 | KUU, the cascade and the thinking judge as *methods*; only D2 (seeded faults) is unseen data for them |
| V7 | **D2 is not real faults.** One-line Major mutants in the fixed version; may be recognisable; the guard removed the D2 instances whose evidence showed the injected line (5 of 8 aborts) | §8.1, Table G5 | Generalisation of every D2-confirmed claim to real faults |
| V8 | **Benchmark memorisation.** Defects4J and its fixes are very likely in the training data, most of all for the frontier judge; D3 was not run | §8.1; D-101, D-103 | The frontier reference point and, to a lesser degree, the local judges |
| V9 | **One replicate** for ablations, D2, M2 and the frontier judge; M1 debate's run-to-run F1 range is 0.221 | Table D2, Table G7(d) | Any single-run difference between debate arms |
| V10 | **Sampling.** TF sampled 1:2 on D1-test; prevalence 0.339 in the scored set against 0.17 in the labelled population and ≈0.02–0.05 in generation | §4; Table G7(a) | F1 and precision; rates (TPR, TNR) are unaffected |
| V11 | **Sibling tests are not an independent oracle.** Generated tests that pass on the buggy version include tests that assert the buggy behaviour (102 misguided of 2,909) | `dataset_summary_D1.json`; dev pilot, D-135 | Any use of "passing generated tests still pass" as a regression check (affects the extension's regression-consistent flip) |

## 2. Limitations of scope

| # | Limitation | Evidence |
|---|---|---|
| S1 | One language (Java), one benchmark (Defects4J), 14 held-out projects, 11 with labelled failures | fact base |
| S2 | One test generator; two candidate second generators failed selection | D-100, D-102 |
| S3 | Small local judges (8–14 B) plus one frontier reference; thinking tested in one family only | Table G6, J-T1 |
| S4 | Focal methods are fix-changed methods invoked by a trigger test: the frame guarantees a bug is near every test | `frame.py`; no failures from non-buggy control methods (mock review #8) |
| S5 | The end of the lifecycle is unmeasured: no repair or deletion stage, no "bugs still detected" outcome | `CURRENT_ARCHITECTURE.md` §3; J-F5 |
| S6 | Cost is reported in GPU-seconds and API dollars, not developer time | Table E4 |
| S7 | Judges see one static failing run; nothing is executed at decision time | `CURRENT_ARCHITECTURE.md` §2 |
| S8 | Per-project cap of 25 left 78 frame methods ungenerated | `split_manifest.json`; J-A2 |

## 3. Open scientific questions, ranked

1. **What evidence decides an assertion failure?** On D1-test 117 of the 177 scored failures are assertion failures
   raised in the test. There, cross-family unanimity removes 5 of 72 test faults while keeping all 45 bug-revealing
   tests; the thinking judge removes 48 and loses 4; the frontier judge removes 66 and loses 9
   (`results/extension/ext0_error_strata.json`). The question a judge must answer is which of two values is intended,
   and the static package holds one run. What additional observation would move this?
2. **Is the judge short of evidence or short of reasoning?** Thinking mode lifted the same 9B judge from balanced
   accuracy ≈0.59 to 0.77–0.82 on the same package (Table G8), which says reasoning. A4 says the failure evidence
   carries all the signal (Table B3), which says evidence. Both can be true; no experiment separates them.
3. **Can anything be learned from executing the buggy program further?** Untested before this extension (J-F4 was
   deferred as "a new system").
4. **How many of the labelled test faults are second real faults?** Needs the independent audit (J-D1).
5. **Does any of it hold on fresh real faults, a second generator, post-cutoff bugs?** J-A2, J-A4, J-C2.
6. **What does a developer gain?** At 5% prevalence KUU leaves about 14 test faults per bug-revealing test kept
   against 19 untriaged (Table G1). No rule in the study changes that order of magnitude except the frontier judge.
