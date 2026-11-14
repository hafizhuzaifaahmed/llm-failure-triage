# CFP confirmation: statistical report

Generated from `results/extension/confirm/confirm_analysis_CFP_CONF_ALL.json` by `scripts/extension/confirm_report.py`; do not edit.
Registration: OSF kp79c (https://osf.io/kp79c), 2026-11-12T08:47:01Z; governing text: the attached document and the frozen code it contains. Template-field reconciliation: pending: template fields to be compared with the attached document when readable (docs/research_extension/OSF_RECONCILIATION.md).
Analysis status: confirmatory. Bootstrap: 10000 bug-level resamples, seed 20261011.

## Population (F1 and F2)

| Quantity | Value |
|---|---|
| Scored failing tests | 572 (55 PF, 517 TF) |
| Bugs; bugs with a PF test | 104; 21 |
| Excluded by the engine (kept with all flags false) | 0 |

## Registered family (one Holm family, α = 0.05)

| Hypothesis | Quantity | Estimate | 95% CI | p | p (Holm) | Reading |
|---|---|---|---|---|---|---|
| C1 | P(flip | PF) − P(flip | TF) (14/55 PF, 117/517 TF) | +0.028 | [-0.137, 0.274] | 0.7685 | 1.0000 | **not supported** (adequately powered: counts against the method) |
| C2 | P(decoupled | TF) − P(decoupled | PF) (1/55 PF, 135/517 TF) | +0.243 | [0.114, 0.372] | 0.0006 | 0.0024 | **supported** |
| C3 | balanced accuracy of KUU + CD − KUU | +0.048 | [0.001, 0.099] | 0.0474 | 0.1422 | **not supported: inconclusive** (underpowered by the registered planning) |
| C4 | PF tests lost by 2-of-3 + CK − 2-of-3 | -1.000 | [-3.000, 0.000] | 0.7375 | 1.0000 | **not supported: inconclusive** (underpowered by the registered planning) |

C1 is adequately powered by the registered planning; C2, C3 and C4 are underpowered, so a non-supported result for them is inconclusive unless it meets a counting-against rule stated in the registration.

**Planning range not met (D-145).** 21 bugs carry a PF test; the registration expected 30 to 50 and classified C1 as adequately powered from a simulation at 30 or more. The registered readings above are applied unchanged, but the reading of a non-supported C1 as evidence against the claim rests on a planning assumption that this sample does not meet.

## Decision rules (reported, not tested; 561 tests with three votes, 54 PF)

| Rule | TPR | TNR | Balanced accuracy | PF tests lost | Bugs lost / bugs with PF | 95% upper bound on bug-loss rate |
|---|---|---|---|---|---|---|
| KUU | 1.000 | 0.316 | 0.658 | 0 | 0 / 21 | 0.133 |
| KUU+CD | 0.982 | 0.430 | 0.706 | 1 | 1 / 21 | 0.207 |
| 2-of-3 | 0.870 | 0.521 | 0.696 | 7 | 4 / 21 | 0.384 |
| 2-of-3+CK | 0.889 | 0.501 | 0.695 | 6 | 3 / 21 | 0.329 |
| KUU+CK+CD | 0.982 | 0.420 | 0.701 | 1 | 1 / 21 | 0.207 |
| 2-of-3+CK+CD | 0.870 | 0.564 | 0.717 | 7 | 4 / 21 | 0.384 |
| keep-all+CD | 0.982 | 0.266 | 0.624 | 1 | 1 / 21 | 0.207 |

## Control group (reported, not tested)

| Quantity | Value |
|---|---|
| Control failing tests | 246 (246 TF, 0 PF; 59 bugs) |
| Flip rate among control TF [95% CI] | 0.220 [0.137, 0.321] |
| Decoupled rate among control TF | 0.187 |
| Flip rate among F1/F2 TF | 0.226 |
| Flip rate among F1/F2 PF | 0.255 |

A control method is one the fix did not change; it is not claimed to be free of defects (`CONTROL_GROUP.md`). Control tests labelled PF reveal the fault through a method the fix did not change.

## Secondary analyses (stated in advance; none replaces a primary result)

| Analysis | Estimate | 95% CI | PF flagged | TF flagged |
|---|---|---|---|---|
| rcf_in_place_of_flip | +0.011 | [-0.068, 0.124] | 4/55 | 32/517 |
| guarded_decoupling | +0.222 | [0.096, 0.346] | 1/55 | 124/517 |
| clean_operator_flip | +0.053 | [-0.112, 0.294] | 13/55 | 95/517 |
| focal_body_only_flip | +0.004 | [-0.153, 0.228] | 12/55 | 111/517 |
| shared_flip | +0.049 | [-0.105, 0.271] | 11/55 | 78/517 |

Leave one project out (12 projects): C1 from -0.025 to +0.125; C2 from +0.088 to +0.300.

**F1 and F2 separately** (secondary analysis 7: the same frozen script on each frame's rows; the Holm adjustment inside each run is not a test of the registered family):

| Frame | Scored tests (PF / TF) | Bugs with PF | C1 [95% CI] | C2 [95% CI] | C3 [95% CI] | C4 [95% CI] |
|---|---|---|---|---|---|---|
| F1 | 155 (36 / 119) | 12 | -0.122 [-0.323, 0.279] | +0.039 [-0.083, 0.156] | +0.016 [-0.045, 0.074] | +0.000 [0.000, 0.000] |
| F2 | 417 (19 / 398) | 9 | +0.125 [-0.126, 0.413] | +0.319 [0.174, 0.468] | +0.065 [0.018, 0.128] | -1.000 [-3.000, 0.000] |

## What would count against the method (the registration's list, evaluated item by item)

1. *C1 not supported:* yes (see the D-145 note on the planning range).
2. *C2 significant in the opposite direction, or its interval wholly below the pilot's estimate (0.189):* no (interval [0.114, 0.372]).
3. *CD or CK raising the bugs lost above its base rule by more than one bug:* no (KUU+CD 1 vs KUU 0 (+1); 2-of-3+CK 3 vs 2-of-3 4 (-1); KUU+CK+CD 1 vs KUU 0 (+1); 2-of-3+CK+CD 4 vs 2-of-3 4 (+0); keep-all+CD 1 vs keep-all 0 (+1)).
4. *A flip rate among control failures close to the flip rate among bug-revealing tests:* control TF 0.220 [0.137, 0.321] against F1/F2 PF 0.255. The registration sets no numeric threshold for 'close'; the PF rate lies inside the control interval: yes.
