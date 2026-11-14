Status: exploratory; protocol frozen internally in Git before the run; not externally preregistered; designed after the confirmation outcomes were known.

# Whole-method dependence probes (WDP): retrospective evaluation report

Level U means: no entry observed and throw-invariant (an operational observation, not a proof that the test cannot reach the method). Model calls: 0. Bootstrap: bug-level, 10000 resamples, seed 20261113, percentile intervals.

## Populations

| population | instances | PF | TF | bugs | bugs with PF |
|---|---|---|---|---|---|
| CONF-all | 572 | 55 | 517 | 104 | 21 |
| CONF-votes | 561 | 54 | 507 | 102 | 21 |
| PILOT-all | 356 | 60 | 296 | 74 | 22 |
| PILOT-votes | 177 | 60 | 117 | 60 | 22 |
| CTRL | 246 | 0 | 246 | 59 | 0 |

## Primary outcome (CONF-votes)

dTNR = TNR(KUU + CD-U) - TNR(KUU) = 0.1045, 95% interval [0.0368, 0.2009].

- (i) safety (KUU + CD-U loses exactly the bugs KUU loses): True (KUU loses 0; additional: none)
- (ii) interval lower limit above 0: True
- (iii) the decoupled PF test of Math_59 is not level U: True (levels: WS)

**Primary criterion: MET.**

Pooled bound: additional bugs lost 0 of 43 PF-bearing bugs, one-sided 95% upper bound 0.0673; the rule was designed with knowledge of these bugs, so the bound is optimistic and is not a guarantee.

## Secondary outcomes (descriptive)

### 1. Pilot (PILOT-votes)

dTNR 0.0598, interval [0.0080, 0.1429]; additional bugs lost: none; level of the decoupled PF test of Codec_13: WS.

### 2. KUU + CD-U against KUU + CD (CONF-votes)

- TPR: 0.0185 [0.0000, 0.0741]
- TNR: -0.0099 [-0.0705, 0.0425]
- BA: 0.0043 [-0.0294, 0.0408]
- PF_lost: -1.0000 [-3.0000, 0.0000]
- bugs_lost: -1 [-3.0000, 0.0000]

### 3. P(U | TF) - P(U | PF)

- CONF-all, U: TF 171/517, PF 0/55, difference 0.3308 [0.1920, 0.4785]
- CONF-all, U_or_RI: TF 191/517, PF 0/55, difference 0.3694 [0.2269, 0.5124]
- PILOT-all, U: TF 57/296, PF 0/60, difference 0.1926 [0.0731, 0.3354]
- PILOT-all, U_or_RI: TF 73/296, PF 0/60, difference 0.2466 [0.1250, 0.3863]

### 4. The ladder

#### By dataset

| group | label | n | FS | WS | RI | U | ND | ND by reason |
|---|---|---|---|---|---|---|---|---|
| CONF | PF | 55 | 35 | 18 | 0 | 0 | 2 | no_x_ret 2 |
| CONF | TF | 517 | 299 | 12 | 20 | 171 | 15 | no_x_ret 15 |
| PILOT | PF | 60 | 58 | 2 | 0 | 0 | 0 | - |
| PILOT | TF | 296 | 212 | 8 | 16 | 57 | 3 | throw_swallowed 3 |
| CTRL | TF | 246 | 174 | 3 | 5 | 64 | 0 | - |

#### By frame

| group | label | n | FS | WS | RI | U | ND | ND by reason |
|---|---|---|---|---|---|---|---|---|
| CTRL | TF | 246 | 174 | 3 | 5 | 64 | 0 | - |
| D1-test | PF | 60 | 58 | 2 | 0 | 0 | 0 | - |
| D1-test | TF | 296 | 212 | 8 | 16 | 57 | 3 | throw_swallowed 3 |
| F1 | PF | 36 | 21 | 15 | 0 | 0 | 0 | - |
| F1 | TF | 119 | 108 | 3 | 0 | 8 | 0 | - |
| F2 | PF | 19 | 14 | 3 | 0 | 0 | 2 | no_x_ret 2 |
| F2 | TF | 398 | 191 | 9 | 20 | 163 | 15 | no_x_ret 15 |

#### By project

| group | label | n | FS | WS | RI | U | ND | ND by reason |
|---|---|---|---|---|---|---|---|---|
| Chart | PF | 20 | 20 | 0 | 0 | 0 | 0 | - |
| Chart | TF | 40 | 36 | 0 | 0 | 4 | 0 | - |
| Closure | PF | 2 | 2 | 0 | 0 | 0 | 0 | - |
| Closure | TF | 15 | 15 | 0 | 0 | 0 | 0 | - |
| Codec | PF | 8 | 7 | 1 | 0 | 0 | 0 | - |
| Codec | TF | 65 | 63 | 1 | 1 | 0 | 0 | - |
| Collections | TF | 4 | 0 | 2 | 2 | 0 | 0 | - |
| Compress | PF | 10 | 10 | 0 | 0 | 0 | 0 | - |
| Compress | TF | 130 | 82 | 0 | 4 | 29 | 15 | no_x_ret 12, throw_swallowed 3 |
| Csv | TF | 14 | 14 | 0 | 0 | 0 | 0 | - |
| JacksonCore | PF | 5 | 2 | 3 | 0 | 0 | 0 | - |
| JacksonCore | TF | 51 | 24 | 6 | 1 | 20 | 0 | - |
| JacksonDatabind | PF | 3 | 3 | 0 | 0 | 0 | 0 | - |
| JacksonDatabind | TF | 321 | 105 | 6 | 20 | 190 | 0 | - |
| JxPath | TF | 1 | 0 | 1 | 0 | 0 | 0 | - |
| Lang | PF | 38 | 25 | 13 | 0 | 0 | 0 | - |
| Lang | TF | 247 | 230 | 3 | 0 | 14 | 0 | - |
| Math | PF | 27 | 23 | 2 | 0 | 0 | 2 | no_x_ret 2 |
| Math | TF | 121 | 83 | 1 | 3 | 31 | 3 | no_x_ret 3 |
| Mockito | PF | 1 | 0 | 1 | 0 | 0 | 0 | - |
| Mockito | TF | 10 | 1 | 2 | 3 | 4 | 0 | - |
| Time | PF | 1 | 1 | 0 | 0 | 0 | 0 | - |
| Time | TF | 40 | 32 | 1 | 7 | 0 | 0 | - |

#### Inside the registered decoupled set

| group | label | n | FS | WS | RI | U | ND | ND by reason |
|---|---|---|---|---|---|---|---|---|
| CONF | PF | 1 | 0 | 1 | 0 | 0 | 0 | - |
| CONF | TF | 135 | 0 | 5 | 16 | 112 | 2 | no_x_ret 2 |
| PILOT | PF | 1 | 0 | 1 | 0 | 0 | 0 | - |
| PILOT | TF | 61 | 0 | 2 | 10 | 49 | 0 | - |
| CTRL | TF | 46 | 0 | 2 | 3 | 41 | 0 | - |

### 5. Low-mutant stratum

#### Fewer than ten compiled first-order mutants, no FLIP or SHIFT

| group | label | n | FS | WS | RI | U | ND | ND by reason |
|---|---|---|---|---|---|---|---|---|
| CONF | PF | 19 | 0 | 17 | 0 | 0 | 2 | no_x_ret 2 |
| CONF | TF | 83 | 0 | 7 | 4 | 59 | 13 | no_x_ret 13 |
| PILOT | PF | 1 | 0 | 1 | 0 | 0 | 0 | - |
| PILOT | TF | 23 | 0 | 6 | 6 | 8 | 3 | throw_swallowed 3 |
| CTRL | TF | 26 | 0 | 1 | 2 | 23 | 0 | - |

### 6-7. Rule tables

#### CONF-votes (561 tests, 54 PF, 21 bugs with PF)

| rule | TPR | TNR | BA | PF_lost | bugs_lost | upper95_bug_loss_rate | tests_kept | PF_share_of_kept | wrong_kept_per_PF_kept_labelled | wrong_kept_per_PF_kept_at_5pct | bugs lost |
|---|---|---|---|---|---|---|---|---|---|---|---|
| KUU | 1.0000 | 0.3156 | 0.6578 | 0 | 0 | 0.1329 | 401 | 0.1347 | 6.4259 | 13.0039 | - |
| 2-of-3 | 0.8704 | 0.5207 | 0.6955 | 7 | 4 | 0.3844 | 290 | 0.1621 | 5.1702 | 10.4628 | Compress_35, Lang_17, Math_94, Time_17 |
| keep-all | 1.0000 | 0.0000 | 0.5000 | 0 | 0 | 0.1329 | 561 | 0.0963 | 9.3889 | 19.0000 | - |
| KUU+CD | 0.9815 | 0.4300 | 0.7057 | 1 | 1 | 0.2067 | 342 | 0.1550 | 5.4528 | 11.0347 | Math_59 |
| KUU+CD-U | 1.0000 | 0.4201 | 0.7101 | 0 | 0 | 0.1329 | 348 | 0.1552 | 5.4444 | 11.0178 | - |
| KUU+CD-UR | 1.0000 | 0.4477 | 0.7239 | 0 | 0 | 0.1329 | 334 | 0.1617 | 5.1852 | 10.4931 | - |
| 2-of-3+CD-U | 0.8704 | 0.5661 | 0.7182 | 7 | 4 | 0.3844 | 267 | 0.1760 | 4.6809 | 9.4725 | Compress_35, Lang_17, Math_94, Time_17 |
| keep-all+CD-U | 1.0000 | 0.3373 | 0.6686 | 0 | 0 | 0.1329 | 390 | 0.1385 | 6.2222 | 12.5917 | - |

#### PILOT-votes (177 tests, 60 PF, 22 bugs with PF)

| rule | TPR | TNR | BA | PF_lost | bugs_lost | upper95_bug_loss_rate | tests_kept | PF_share_of_kept | wrong_kept_per_PF_kept_labelled | wrong_kept_per_PF_kept_at_5pct | bugs lost |
|---|---|---|---|---|---|---|---|---|---|---|---|
| KUU | 0.9833 | 0.2051 | 0.5942 | 1 | 1 | 0.1981 | 152 | 0.3882 | 1.5763 | 15.3585 | Codec_9 |
| 2-of-3 | 0.9000 | 0.4701 | 0.6850 | 6 | 2 | 0.2595 | 116 | 0.4655 | 1.1481 | 11.1871 | Codec_9, Compress_16 |
| keep-all | 1.0000 | 0.0000 | 0.5000 | 0 | 0 | 0.1273 | 177 | 0.3390 | 1.9500 | 19.0000 | - |
| KUU+CD | 0.9667 | 0.3333 | 0.6500 | 2 | 2 | 0.2595 | 136 | 0.4265 | 1.3448 | 13.1034 | Codec_13, Codec_9 |
| KUU+CD-U | 0.9833 | 0.2650 | 0.6241 | 1 | 1 | 0.1981 | 145 | 0.4069 | 1.4576 | 14.2025 | Codec_9 |
| KUU+CD-UR | 0.9833 | 0.3419 | 0.6626 | 1 | 1 | 0.1981 | 136 | 0.4338 | 1.3051 | 12.7162 | Codec_9 |
| 2-of-3+CD-U | 0.9000 | 0.4957 | 0.6979 | 6 | 2 | 0.2595 | 113 | 0.4779 | 1.0926 | 10.6458 | Codec_9, Compress_16 |
| keep-all+CD-U | 1.0000 | 0.1368 | 0.5684 | 0 | 0 | 0.1273 | 161 | 0.3727 | 1.6833 | 16.4017 | - |

The 5% column assumes a prevalence of 0.05: (1 - pi)(1 - TNR) / (pi * TPR).

### 8. Pre-filter

- CONF-votes: level_U 171, share_level_U 0.3048, judge_calls_avoided 513, level_U_already_discarded_by_KUU 118
- PILOT-votes: level_U 16, share_level_U 0.0904, judge_calls_avoided 48, level_U_already_discarded_by_KUU 9
- CONF-all: level_U 171, share_level_U 0.2990
- PILOT-all: level_U 57, share_level_U 0.1601
- CTRL: level_U 64, share_level_U 0.2602

### 9. Heterogeneity

- F1: 153 tests, 36 PF; dTNR 0.0342 [0.0000, 0.1304], additional bugs lost none
- F2: 408 tests, 18 PF; dTNR 0.1256 [0.0411, 0.2440], additional bugs lost none
- without_Jackson: 331 tests, 46 PF; dTNR 0.0456 [0.0093, 0.1013], additional bugs lost none
- without Chart: dTNR 0.1036, additional bugs lost none
- without Closure: dTNR 0.1047, additional bugs lost none
- without Codec: dTNR 0.1162, additional bugs lost none
- without Compress: dTNR 0.1070, additional bugs lost none
- without Csv: dTNR 0.1054, additional bugs lost none
- without JacksonCore: dTNR 0.1091, additional bugs lost none
- without JacksonDatabind: dTNR 0.0425, additional bugs lost none
- without JxPath: dTNR 0.1047, additional bugs lost none
- without Lang: dTNR 0.1373, additional bugs lost none
- without Math: dTNR 0.0970, additional bugs lost none
- without Mockito: dTNR 0.1050, additional bugs lost none
- without Time: dTNR 0.1062, additional bugs lost none
- CONF-all without Chart: U TF 170/512, PF 0/55, difference 0.3320; U_or_RI TF 190/512, PF 0/55, difference 0.3711
- CONF-all without Closure: U TF 171/516, PF 0/53, difference 0.3314; U_or_RI TF 191/516, PF 0/53, difference 0.3702
- CONF-all without Codec: U TF 171/466, PF 0/55, difference 0.3670; U_or_RI TF 191/466, PF 0/55, difference 0.4099
- CONF-all without Compress: U TF 166/468, PF 0/53, difference 0.3547; U_or_RI TF 184/468, PF 0/53, difference 0.3932
- CONF-all without Csv: U TF 171/513, PF 0/55, difference 0.3333; U_or_RI TF 191/513, PF 0/55, difference 0.3723
- CONF-all without JacksonCore: U TF 156/496, PF 0/50, difference 0.3145; U_or_RI TF 176/496, PF 0/50, difference 0.3548
- CONF-all without JacksonDatabind: U TF 33/309, PF 0/52, difference 0.1068; U_or_RI TF 37/309, PF 0/52, difference 0.1197
- CONF-all without JxPath: U TF 171/516, PF 0/55, difference 0.3314; U_or_RI TF 191/516, PF 0/55, difference 0.3702
- CONF-all without Lang: U TF 171/394, PF 0/29, difference 0.4340; U_or_RI TF 191/394, PF 0/29, difference 0.4848
- CONF-all without Math: U TF 159/474, PF 0/39, difference 0.3354; U_or_RI TF 177/474, PF 0/39, difference 0.3734
- CONF-all without Mockito: U TF 171/514, PF 0/55, difference 0.3327; U_or_RI TF 191/514, PF 0/55, difference 0.3716
- CONF-all without Time: U TF 171/509, PF 0/54, difference 0.3360; U_or_RI TF 191/509, PF 0/54, difference 0.3752

### 10. Control group

#### CTRL

| group | label | n | FS | WS | RI | U | ND | ND by reason |
|---|---|---|---|---|---|---|---|---|
| CTRL | TF | 246 | 174 | 3 | 5 | 64 | 0 | - |

### 11. Cost

| frame | tests | seconds mean | executions mean | first-order seconds mean |
|---|---|---|---|---|
| D1-test | 356 | 0.4750 | 3.4940 | 2.0070 |
| F1 | 155 | 0.4260 | 3.7810 | 3.0870 |
| F2 | 417 | 0.6100 | 3.3450 | 1.7140 |
| CTRL | 246 | 0.5240 | 3.6460 | 2.1980 |

### 12. Diagnostics

```
{
 "D1-test": {
  "PF": {
   "n": 60,
   "exclusions": {},
   "ND_by_reason": {},
   "ND_throw_swallowed": 0,
   "ND_swallow_risk": 0,
   "malformed_ids": [],
   "no_record_ids": [],
   "first_order_unusable_ids": [],
   "variants_not_compiled": {},
   "variant_ERR": {},
   "entered_by_level": {
    "FS": {
     "True": 58
    },
    "WS": {
     "True": 2
    },
    "RI": {},
    "U": {},
    "ND": {}
   },
   "marker_violations": 0,
   "surfaced": 60,
   "x_throw_changed_not_entered": 0,
   "x_throw_same_x_ret_changed": 0
  },
  "TF": {
   "n": 296,
   "exclusions": {},
   "ND_by_reason": {
    "throw_swallowed": 3
   },
   "ND_throw_swallowed": 3,
   "ND_swallow_risk": 0,
   "malformed_ids": [],
   "no_record_ids": [],
   "first_order_unusable_ids": [],
   "variants_not_compiled": {},
   "variant_ERR": {},
   "entered_by_level": {
    "FS": {
     "False": 9,
     "True": 203
    },
    "WS": {
     "True": 8
    },
    "RI": {
     "True": 16
    },
    "U": {
     "False": 57
    },
    "ND": {
     "True": 3
    }
   },
   "marker_violations": 0,
   "surfaced": 212,
   "x_throw_changed_not_entered": 0,
   "x_throw_same_x_ret_changed": 0
  }
 },
 "F1": {
  "PF": {
   "n": 36,
   "exclusions": {},
   "ND_by_reason": {},
   "ND_throw_swallowed": 0,
   "ND_swallow_risk": 0,
   "malformed_ids": [],
   "no_record_ids": [],
   "first_order_unusable_ids": [],
   "variants_not_compiled": {},
   "variant_ERR": {},
   "entered_by_level": {
    "FS": {
     "True": 21
    },
    "WS": {
     "True": 15
    },
    "RI": {},
    "U": {},
    "ND": {}
   },
   "marker_violations": 0,
   "surfaced": 34,
   "x_throw_changed_not_entered": 0,
   "x_throw_same_x_ret_changed": 0
  },
  "TF": {
   "n": 119,
   "exclusions": {},
   "ND_by_reason": {},
   "ND_throw_swallowed": 0,
   "ND_swallow_risk": 0,
   "malformed_ids": [],
   "no_record_ids": [],
   "first_order_unusable_ids": [],
   "variants_not_compiled": {},
   "variant_ERR": {},
   "entered_by_level": {
    "FS": {
     "False": 2,
     "True": 106
    },
    "WS": {
     "True": 3
    },
    "RI": {},
    "U": {
     "False": 8
    },
    "ND": {}
   },
   "marker_violations": 0,
   "surfaced": 108,
   "x_throw_changed_not_entered": 0,
   "x_throw_same_x_ret_changed": 0
  }
 },
 "F2": {
  "PF": {
   "n": 19,
   "exclusions": {},
   "ND_by_reason": {
    "no_x_ret": 2
   },
   "ND_throw_swallowed": 0,
   "ND_swallow_risk": 0,
   "malformed_ids": [],
   "no_record_ids": [],
   "first_order_unusable_ids": [],
   "variants_not_compiled": {},
   "variant_ERR": {},
   "entered_by_level": {
    "FS": {
     "True": 14
    },
    "WS": {
     "True": 3
    },
    "RI": {},
    "U": {},
    "ND": {
     "True": 2
    }
   },
   "marker_violations": 0,
   "surfaced": 14,
   "x_throw_changed_not_entered": 0,
   "x_throw_same_x_ret_changed": 0
  },
  "TF": {
   "n": 398,
   "exclusions": {},
   "ND_by_reason": {
    "no_x_ret": 15
   },
   "ND_throw_swallowed": 0,
   "ND_swallow_risk": 0,
   "malformed_ids": [],
   "no_record_ids": [],
   "first_order_unusable_ids": [],
   "variants_not_compiled": {},
   "variant_ERR": {},
   "entered_by_level": {
    "FS": {
     "False": 5,
     "True": 186
    },
    "WS": {
     "True": 9
    },
    "RI": {
     "True": 20
    },
    "U": {
     "False": 163
    },
    "ND": {
     "True": 15
    }
   },
   "marker_violations": 0,
   "surfaced": 199,
   "x_throw_changed_not_entered": 0,
   "x_throw_same_x_ret_changed": 6
  }
 },
 "CTRL": {
  "PF": {
   "n": 0,
   "exclusions": {},
   "ND_by_reason": {},
   "ND_throw_swallowed": 0,
   "ND_swallow_risk": 0,
   "malformed_ids": [],
   "no_record_ids": [],
   "first_order_unusable_ids": [],
   "variants_not_compiled": {},
   "variant_ERR": {},
   "entered_by_level": {
    "FS": {},
    "WS": {},
    "RI": {},
    "U": {},
    "ND": {}
   },
   "marker_violations": 0,
   "surfaced": 0,
   "x_throw_changed_not_entered": 0,
   "x_throw_same_x_ret_changed": 0
  },
  "TF": {
   "n": 246,
   "exclusions": {},
   "ND_by_reason": {},
   "ND_throw_swallowed": 0,
   "ND_swallow_risk": 0,
   "malformed_ids": [],
   "no_record_ids": [],
   "first_order_unusable_ids": [],
   "variants_not_compiled": {},
   "variant_ERR": {},
   "entered_by_level": {
    "FS": {
     "False": 5,
     "True": 169
    },
    "WS": {
     "True": 3
    },
    "RI": {
     "True": 5
    },
    "U": {
     "False": 64
    },
    "ND": {}
   },
   "marker_violations": 0,
   "surfaced": 151,
   "x_throw_changed_not_entered": 0,
   "x_throw_same_x_ret_changed": 3
  }
 }
}
```

## Quality checks

```
{
 "per_run": {
  "D1-test": {
   "scored_rows": 356,
   "marker_violations": 0,
   "surfaced": 272,
   "technical_ND": 0,
   "malformed": 0,
   "technical_ND_share": 0.0,
   "passes": true
  },
  "F1": {
   "scored_rows": 155,
   "marker_violations": 0,
   "surfaced": 142,
   "technical_ND": 0,
   "malformed": 0,
   "technical_ND_share": 0.0,
   "passes": true
  },
  "F2": {
   "scored_rows": 417,
   "marker_violations": 0,
   "surfaced": 213,
   "technical_ND": 17,
   "malformed": 0,
   "technical_ND_share": 0.0408,
   "passes": true
  },
  "CTRL": {
   "scored_rows": 246,
   "marker_violations": 0,
   "surfaced": 151,
   "technical_ND": 0,
   "malformed": 0,
   "technical_ND_share": 0.0,
   "passes": true
  }
 },
 "raw_ledger_gate": {
  "runs": {
   "WDP_D1_TEST": {
    "ledger": "C:\\Users\\huzai\\Downloads\\Fast\\Advance AI\\Phase 3 and 4\\results\\extension\\wdp\\WDP_D1_TEST\\ledger.jsonl",
    "records": 369,
    "instances": 369,
    "surfaced": 285,
    "marker_violations": [],
    "missing": [],
    "duplicated": [],
    "extra": [],
    "unreadable_lines": 0,
    "passes": true
   },
   "WDP_CONF_F1": {
    "ledger": "C:\\Users\\huzai\\Downloads\\Fast\\Advance AI\\Phase 3 and 4\\results\\extension\\wdp\\WDP_CONF_F1\\ledger.jsonl",
    "records": 160,
    "instances": 160,
    "surfaced": 143,
    "marker_violations": [],
    "missing": [],
    "duplicated": [],
    "extra": [],
    "unreadable_lines": 0,
    "passes": true
   },
   "WDP_CONF_F2": {
    "ledger": "C:\\Users\\huzai\\Downloads\\Fast\\Advance AI\\Phase 3 and 4\\results\\extension\\wdp\\WDP_CONF_F2\\ledger.jsonl",
    "records": 428,
    "instances": 428,
    "surfaced": 223,
    "marker_violations": [],
    "missing": [],
    "duplicated": [],
    "extra": [],
    "unreadable_lines": 0,
    "passes": true
   },
   "WDP_CONF_CTRL": {
    "ledger": "C:\\Users\\huzai\\Downloads\\Fast\\Advance AI\\Phase 3 and 4\\results\\extension\\wdp\\WDP_CONF_CTRL\\ledger.jsonl",
    "records": 246,
    "instances": 246,
    "surfaced": 151,
    "marker_violations": [],
    "missing": [],
    "duplicated": [],
    "extra": [],
    "unreadable_lines": 0,
    "passes": true
   }
  },
  "passes": true
 },
 "populations_match_brief": {
  "CONF-all": {
   "instances": [
    572,
    572
   ],
   "PF": [
    55,
    55
   ],
   "bugs_with_PF": [
    21,
    21
   ]
  },
  "CONF-votes": {
   "instances": [
    561,
    561
   ],
   "PF": [
    54,
    54
   ]
  },
  "PILOT-all": {
   "instances": [
    356,
    356
   ],
   "PF": [
    60,
    60
   ],
   "bugs_with_PF": [
    22,
    22
   ]
  },
  "PILOT-votes": {
   "instances": [
    177,
    177
   ],
   "PF": [
    60,
    60
   ]
  },
  "CTRL": {
   "instances": [
    246,
    246
   ]
  }
 },
 "populations_ok": true,
 "registered_rows": {
  "KUU": {
   "TPR": [
    1.0,
    1.0
   ],
   "TNR": [
    0.3156,
    0.3156
   ],
   "BA": [
    0.6578,
    0.6578
   ],
   "PF_lost": [
    0,
    0.0
   ],
   "bugs_lost": [
    0,
    0
   ]
  },
  "KUU+CD": {
   "TPR": [
    0.9815,
    0.9815
   ],
   "TNR": [
    0.43,
    0.43
   ],
   "BA": [
    0.7057,
    0.7057
   ],
   "PF_lost": [
    1,
    1.0
   ],
   "bugs_lost": [
    1,
    1
   ]
  },
  "2-of-3": {
   "TPR": [
    0.8704,
    0.8704
   ],
   "TNR": [
    0.5207,
    0.5207
   ],
   "BA": [
    0.6955,
    0.6955
   ],
   "PF_lost": [
    7,
    7.0
   ],
   "bugs_lost": [
    4,
    4
   ]
  }
 },
 "registered_rows_ok": true,
 "ladder_reportable": true
}
```
