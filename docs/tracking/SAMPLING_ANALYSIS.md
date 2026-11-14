# X-07 — PF/TF evaluation sampling: within-project vs overall 1:2

**Status (2026-11-01, D-53): DECIDED — D1-test uses the overall/proportional reading; dev keeps the within-project reading of its pilot. The other reading is written as a named alternative for each split.** Earlier status: PENDING the authors' review. Not applied. All primary samples (`sample_D1_dev.json`,
`sample_D1_test.json`, and the pilot sample `sample_D1_dev_pilot.json`) use the **within-project** reading,
which is what the pipeline implemented before the corrective pass. The overall/proportional reading is
written only as `sample_D1_<split>_X07_proportional_PENDING.json` so its effect can be measured.
(The previous pass had briefly made the proportional reading the default; that has been reverted.)

## What Phase 2 says

- C9: *"Keep all PF instances and sample TF instances at random, stratified by project, to a PF:TF ratio of 1:2
  (Section 4.8). The sampling weights are stored so that precision can also be reported at the natural
  prevalence."*
- §4.8: *"D1-test ≈ 720 instances (all PF, ≈ 240 expected, plus twice as many TF)."*
- Table 17: prevalence-adjusted precision is *"needed because the evaluation sample has a designed 1:2 ratio."*

Fixed by the text: keep every PF; TF drawn at random; stratification variable = project; a 1:2 ratio;
inverse-probability weights. **Not fixed by the text:** whether the 1:2 ratio must hold inside each project
stratum, or overall with the TF draw stratified by project.

## The two readings

| | Within-project (primary, pre-existing) | Overall / proportional (X-07, pending) |
|---|---|---|
| TF drawn from project *p* | min(2 × PF(*p*), TF(*p*)) | share of 2 × (total PF), proportional to TF(*p*) |
| Project with 0 PF | contributes **0 TF** — absent from the sample | keeps TF in proportion to its TF count |
| Project with TF(*p*) < 2 × PF(*p*) | contributes all its TF; overall ratio falls below 1:2 | quota redistributed; overall ratio stays 1:2 |
| Overall ratio | ≤ 1:2 (exactly 1:2 only if every project has ≥ 2 TF per PF) | exactly 1:2 (if enough TF exist overall) |
| Weights | N_TF(*p*) / n_TF(*p*), vary strongly across projects | nearly uniform across projects |

Worked example (`tests/unit/test_sampling.py`): A (10 PF, 100 TF), B (0 PF, 40 TF), C (2 PF, 60 TF).
Within-project draws 20 / **0** / 4 TF; proportional draws 12 / 5 / 7. Both total 24.

## Is the proposed change consistent with Phase 2?

Both readings satisfy every element the text fixes, so neither contradicts Phase 2 outright; the text is
ambiguous on the one point that matters here.
- Arguments for the **overall** reading: §4.8 states the target as "all PF … plus twice as many TF" for the
  whole of D1-test, and Table 17 speaks of "a designed 1:2 ratio" of the sample, not of each project;
  "stratified by project" is the ordinary description of how a random draw is spread across strata.
  It also keeps the TF class representative of all projects, so FPR is not estimated on a TF population
  that silently excludes projects where the generator found no bug.
- Arguments for the **within-project** reading: "stratified by project, to a PF:TF ratio of 1:2" can be read as
  imposing the ratio per stratum; it is what the code did when Phase 3 began; and it keeps each project's
  PF:TF composition identical, which some per-project comparisons (R5) might prefer.
- Effect on the confirmatory endpoint: F1 depends on FP, so the TF composition can move F1. Under the
  within-project reading, projects with 0 PF contribute nothing to FP. R5 per-project F1 is undefined for a
  0-PF project under either reading.

## What will be measured before a decision

`build_dataset.py` writes both samples and records, per split: number of projects with 0 PF, TF instances and
projects dropped (`projects_dropped`), the realised overall PF:TF ratio, and the weight range. The analysis
can score the same decisions under both samples (TF instances common to both are judged once), so the
effect on F1/precision/FPR is reported side by side. The dev pilot will give the first real numbers; the
decision for D1-test is the authors', before the held-out runs.

## Pilot-only cap (X-09, proposed with the pilot)
The judged dev set is capped at 150 instances by a seeded proportional subsample of the within-project
sample (ratio preserved). Never applied to D1-test.
