# CFP result tables, run `CFP_D1_TEST` (generated; do not edit)

Source: `results/extension/ext1_probe_analysis_CFP_D1_TEST.json`, `results/extension/ext2_probe_ablations_CFP_D1_TEST.json`.
Intervals: bug-level cluster bootstrap, 10,000 resamples. PF = program fault (bug-revealing), TF = test fault.

## T1. Instances

| Quantity | Value |
|---|---|
| Labelled instances with a ledger record | 369 of 369 |
| Scored (PF or TF, not excluded) | 356 (60 PF, 296 TF) |
| Bugs; bugs with a PF test | 74; 22 |
| Compiled mutants per instance: min / q1 / median / q3 / max | 0 / 16 / 35 / 64 / 79 |
| AMB: status counts | too_few_mutants 3, usable_10plus 10 |
| PF: status counts | too_few_mutants 8, usable_10plus 52 |
| TF: status counts | too_few_mutants 41, usable_10plus 255 |

## T2. Probe flags by execution label

| Flag | PF flagged | TF flagged | Rate PF | Rate TF | Difference [95% CI] | Likelihood ratio | PF share among flagged (overall) |
|---|---|---|---|---|---|---|---|
| flip | 40 of 60 | 46 of 296 | 0.667 | 0.155 | 0.511 [0.252, 0.740] | 4.29 | 0.465 (0.169) |
| rcf | 17 of 60 | 16 of 296 | 0.283 | 0.054 | 0.229 [0.007, 0.478] | 5.24 | 0.515 (0.169) |
| flip_without_rcf | 23 of 60 | 30 of 296 | 0.383 | 0.101 | 0.282 [0.059, 0.529] | 3.78 | 0.434 (0.169) |
| coupled | 58 of 60 | 212 of 296 | 0.967 | 0.716 | 0.250 [0.117, 0.387] | 1.35 | 0.215 (0.169) |
| decoupled | 1 of 60 | 61 of 296 | 0.017 | 0.206 | -0.189 [-0.309, -0.075] | 0.08 | 0.016 (0.169) |

HP-1 (regression-consistent flip, as fixed in D-134): supported. HP-2 (decoupling): supported.
AUROC of the flip fraction: 0.779; of the coupled fraction: 0.720.
AMB instances (n = 13): flip 1, rcf 0, decoupled 0.

## T3. Certificate rules beside their base rules (D-110 common D1-test, 177 instances, 60 PF)

| Rule | TPR | TNR | Balanced accuracy | PF tests lost | Bugs lost | Δ balanced accuracy [95% CI] | Δ TPR [95% CI] | Δ TNR [95% CI] | Δ bugs lost [95% CI] |
|---|---|---|---|---|---|---|---|---|---|
| **KA** | 1.000 | 0.000 | 0.500 | 0.0 | 0.0 | — | — | — | — |
| KA + CD | 0.983 | 0.205 | 0.594 | 1.0 | 1.0 | +0.094 [0.040, 0.156] | -0.017 [-0.064, 0.000] | +0.205 [0.094, 0.331] | +1.0 [0.000, 3.000] |
| **KUU** | 0.983 | 0.205 | 0.594 | 1.0 | 1.0 | — | — | — | — |
| KUU + CD | 0.967 | 0.333 | 0.650 | 2.0 | 2.0 | +0.056 [0.009, 0.110] | -0.017 [-0.064, 0.000] | +0.128 [0.035, 0.237] | +1.0 [0.000, 3.000] |
| KUU + CK+CD | 0.983 | 0.333 | 0.658 | 1.0 | 1.0 | +0.064 [0.014, 0.122] | +0.000 [-0.054, 0.052] | +0.128 [0.035, 0.237] | +0.0 [-3.000, 3.000] |
| **KUU-NG** | 0.983 | 0.171 | 0.577 | 1.0 | 0.0 | — | — | — | — |
| KUU-NG + CD | 0.967 | 0.350 | 0.659 | 2.0 | 1.0 | +0.081 [0.031, 0.138] | -0.017 [-0.064, 0.000] | +0.179 [0.076, 0.296] | +1.0 [0.000, 3.000] |
| KUU-NG + CK+CD | 0.967 | 0.350 | 0.659 | 2.0 | 1.0 | +0.081 [0.031, 0.138] | -0.017 [-0.064, 0.000] | +0.179 [0.076, 0.296] | +1.0 [0.000, 3.000] |
| **M1 DEB** | 0.500 | 0.764 | 0.632 | 30.0 | 7.0 | — | — | — | — |
| M1 DEB + CK | 0.594 | 0.721 | 0.658 | 24.3 | 5.7 | +0.026 [-0.017, 0.076] | +0.094 [0.023, 0.187] | -0.043 [-0.087, -0.009] | -1.3 [-3.667, 0.000] |
| M1 DEB + CK+CD | 0.578 | 0.778 | 0.678 | 25.3 | 6.7 | +0.046 [-0.008, 0.102] | +0.078 [-0.008, 0.175] | +0.014 [-0.051, 0.078] | -0.3 [-3.000, 2.667] |
| **2-of-3** | 0.900 | 0.470 | 0.685 | 6.0 | 2.0 | — | — | — | — |
| 2-of-3 + CK | 0.967 | 0.470 | 0.718 | 2.0 | 0.0 | +0.033 [0.000, 0.083] | +0.067 [0.000, 0.167] | +0.000 [0.000, 0.000] | -2.0 [-5.000, 0.000] |
| 2-of-3 + CK+CD | 0.950 | 0.556 | 0.753 | 3.0 | 1.0 | +0.068 [0.020, 0.128] | +0.050 [-0.030, 0.154] | +0.085 [0.021, 0.159] | -1.0 [-4.000, 2.000] |
| **M1 thinking J1** | 0.883 | 0.658 | 0.771 | 7.0 | 3.0 | — | — | — | — |
| M1 thinking J1 + CK | 0.900 | 0.615 | 0.758 | 6.0 | 2.0 | -0.013 [-0.038, 0.014] | +0.017 [0.000, 0.062] | -0.043 [-0.087, -0.009] | -1.0 [-3.000, 0.000] |
| M1 thinking J1 + CK+CD | 0.883 | 0.718 | 0.801 | 7.0 | 3.0 | +0.030 [-0.018, 0.077] | +0.000 [-0.054, 0.052] | +0.060 [-0.029, 0.145] | +0.0 [-3.000, 3.000] |
| **Sonnet DEB** | 0.811 | 0.917 | 0.864 | 11.3 | 4.0 | — | — | — | — |
| Sonnet DEB + CK | 0.883 | 0.875 | 0.879 | 7.0 | 2.7 | +0.015 [-0.034, 0.093] | +0.072 [0.000, 0.225] | -0.043 [-0.087, -0.009] | -1.3 [-3.667, 0.000] |
| Sonnet DEB + CK+CD | 0.867 | 0.875 | 0.871 | 8.0 | 3.7 | +0.006 [-0.051, 0.085] | +0.056 [-0.045, 0.212] | -0.043 [-0.087, -0.009] | -0.3 [-3.333, 2.667] |

## T4. Ablations (EXT-2)

| Ablation | Setting | PF flipped | TF flipped | Rate PF | Rate TF |
|---|---|---|---|---|---|
| Region | focal_plus_callees (≥10 mutants: 307 instances) | 40 of 60 | 46 of 296 | 0.667 | 0.155 |
| Region | focal_body_only (≥10 mutants: 209 instances) | 37 of 60 | 35 of 296 | 0.617 | 0.118 |
| Operators | all | 40 of 60 | 46 of 296 | 0.667 | 0.155 |
| Operators | without_ROR | 40 of 60 | 45 of 296 | 0.667 | 0.152 |
| Operators | only_ROR | 35 of 60 | 21 of 296 | 0.583 | 0.071 |
| Operators | without_AOR | 39 of 60 | 44 of 296 | 0.650 | 0.149 |
| Operators | only_AOR | 5 of 60 | 3 of 296 | 0.083 | 0.010 |
| Operators | without_COR | 40 of 60 | 46 of 296 | 0.667 | 0.155 |
| Operators | only_COR | 2 of 60 | 13 of 296 | 0.033 | 0.044 |
| Operators | without_LVR | 40 of 60 | 43 of 296 | 0.667 | 0.145 |
| Operators | only_LVR | 26 of 60 | 8 of 296 | 0.433 | 0.027 |
| Operators | without_NEG | 38 of 60 | 38 of 296 | 0.633 | 0.128 |
| Operators | only_NEG | 31 of 60 | 38 of 296 | 0.517 | 0.128 |
| Operators | without_STD | 38 of 60 | 45 of 296 | 0.633 | 0.152 |
| Operators | only_STD | 11 of 60 | 7 of 296 | 0.183 | 0.024 |
| Failure type | assertion_failure (AUROC of flip fraction 0.753) | 28 of 45 | 33 of 177 | 0.622 | 0.186 |
| Failure type | exception (AUROC of flip fraction 0.848) | 12 of 15 | 13 of 119 | 0.800 | 0.109 |
| Shared flip | flipped by a mutant that flips another failing test of the method | 35 of 60 | 31 of 296 | 0.583 | 0.105 |

| Further quantity | Value |
|---|---|
| rcf, focal_plus_callees: PF / TF | 17 of 60 / 16 of 296 |
| decoupled, focal_plus_callees: PF / TF | 1 of 60 / 61 of 296 |
| rcf, focal_body_only: PF / TF | 14 of 60 / 11 of 296 |
| decoupled, focal_body_only: PF / TF | 0 of 60 / 56 of 296 |
| decoupled within assertion_failure: PF / TF | 0 of 45 / 10 of 177 |
| decoupled within exception: PF / TF | 1 of 15 / 51 of 119 |
| AUROC of failure type alone (exception = 1) | 0.424 |
| Flip mutant runs; regression-consistent; vacuous (no sibling) | 365; 71; 0 |
| Bugs with a PF test; of which some PF test flips | 22; 14 |
| TF-only bugs; of which any test flips | 52; 14 |
| Probe seconds per instance: median / 90th percentile / total over 369 | 0.97 / 3.87 / 737.4 |
