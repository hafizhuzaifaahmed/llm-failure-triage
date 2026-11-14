P1 RESULT: FAIL

P1 replication of audit checks A1–A5 (`docs/research_extension/CONFIRMATION_INDEPENDENT_AUDIT.md` §8), run 2026-11-13 at HEAD `3b017f2`, branch `research-extension`. Read-only. No model calls, no git writes.

The FAIL comes from one strict-tolerance miss in A1. Every count and point estimate reproduced exactly. The pooled registered intervals reproduced to the third decimal. Two per-frame C1 bootstrap limits (secondary analysis 7) differ from the registered JSON in the **second** decimal. That contradicts audit matrix row 16 ("all intervals agree to the third decimal") and exceeds the tolerance this task set. Nothing was fixed or reinterpreted. Checks A2–A5 are independent and read-only, so they were run anyway and are reported below.

## Results

| Check | Expected | Observed | Result |
|---|---|---|---|
| A1 counts and point estimates (§§2–5 and `confirm_analysis_CFP_CONF_ALL.json`) | identical | identical for every figure checked: population 572/55/517/104/21; F1 155 (36/119, 28 bugs, 12 PF-bugs), F2 417 (19/398, 76 bugs, 9); AMB 5/11; CTRL 246 TF, 59 bugs; C1 +0.0282, C2 +0.2429, C3 +0.0479, C4 −1; all 7 rule rows (TPR, TNR, BA, PF lost, bugs lost); Clopper–Pearson 0.1329/0.2067/0.3292/0.3844; control 0.2195, 0.187, 0.2263, 0.2545; F1/F2 C1 −0.1223/+0.1248, C2 +0.0394/+0.3191; LOPO ends 0.0876 (JacksonDatabind) / 0.3005 (Lang); all of §3, §4.1–4.3 and §5 counts (rcf 4/55 vs 32/517, 14/42 vs 117/504, 8/21, 41/83, AUROC 0.526/0.772/0.787, MH 0.149, without Jackson +0.041, 92 of 136, 117 of 135, 82/160, 19 PF / 83 TF, the Math_59 detail, the pilot's 20/20 Chart and 0/11 Math, 45/230, and so on) | PASS |
| A1 pooled bootstrap intervals | may differ in 3rd decimal | C1 [−0.1383, 0.2737] vs registered [−0.1372, 0.2735]; C2 [0.1150, 0.3715] vs [0.1140, 0.3723]; C3 [0.0013, 0.0993] vs [0.0008, 0.0991]; control flip [0.1376, 0.3230] vs [0.1370, 0.3208]. All within the 3rd decimal. p-values differ by seed (C1 0.7833 vs 0.7685; C2 0.0002 vs 0.0006; C3 0.0442 vs 0.0474; C4 0.7249 vs 0.7375). Holm by hand from the registered p: 4×0.0006=0.0024, 3×0.0474=0.1422, others capped at 1, identical | PASS |
| A1 per-frame bootstrap intervals (secondary 7, `*_F1/F2_secondary.json`) | may differ in 3rd decimal | **F1 C1 upper 0.2698 vs registered 0.2786 (Δ 0.009); F2 C1 upper 0.4078 vs 0.4133 (Δ 0.0055)**. Within the 3rd decimal: F1 C1 lower −0.3256 vs −0.3229; F1 C2 [−0.0843, 0.1532] vs [−0.0833, 0.1563]; F2 C1 lower −0.1264 vs −0.1257; F2 C2 [0.1704, 0.4699] vs [0.1738, 0.4682] | **FAIL (tolerance)** |
| A2 labels for 60 seeded instances, recomputed from raw runs | 60/60 | **60/60** (F1 20/20: 4 PF, 15 TF, 1 AMB; F2 20/20, all TF; CTRL 20/20, all TF). The recomputed sigma_B and sigma_F equal the stored ones in 60/60 | PASS |
| A3 delete-one-bug jackknife, 104 clusters | computed | C1 +0.0282, SE 0.1159, normal 95% [−0.199, +0.255] (width 0.454) vs bootstrap [−0.137, 0.274] (0.411). C2 +0.2429, SE 0.0683, [+0.109, +0.377] (0.268) vs [0.114, 0.372] (0.258) | computed |
| A4 tests without votes | same 11 for all 3 judges, 2 F1 + 9 F2, 10 TF + 1 PF | identical sets for M1, M2 and E6B: F1 `7b1aea85c0f523f3` (TF, Lang_19) and `fd4951b27a4ba42a` (TF, Lang_51); F2 `0299c576ff1e7d75` (TF, JD_42), `135cd1fa3a3afbae` (**PF**, Compress_35), `1549a0ffb2a33da6`, `2bac2323f936e79e`, `3734ad4b6462e07b` (TF, JD_30), `ab741f1756cc0930`, `ca648e4f6a3eda1c`, `ce706bf0f0e20271` (TF, JD_7), `e4e4847d78dea0a2` (TF, Mockito_29). 10 TF, 1 PF. No duplicate decisions | PASS |
| A4 guard refusal record for each of the 11 | a refusal record | `guard_D1C_<T>.jsonl` has **no refusal or outcome field**. Its only keys are `bug_ids`, `code_lines`, `instance_id` and `paths`, with one record for every instance (160 and 428), so it holds guard inputs, not outcomes. Refusals are recorded in `data/extension/confirm/<T>/votes/LOCAL_CONF_VOTE_<J>_<T>/leakage_rejections.jsonl`: for every judge and frame, the id set equals the no-vote set exactly (2 and 9 records, `reason: "leakage check failed for <id>: [...]"`, replicate 80, J1, S1) | reported (see note) |
| A5 frozen code diff vs `3b017f2`, freeze tests | empty; pass | empty diff (HEAD is `3b017f2`); `tests/extension/test_freeze.py`: 5 passed | PASS |

## Figures that did not match (both values)

1. F1 C1 bootstrap upper limit: audit script 0.2698, registered `confirm_analysis_CFP_CONF_F1_secondary.json` 0.2786.
2. F2 C1 bootstrap upper limit: audit script 0.4078, registered `confirm_analysis_CFP_CONF_F2_secondary.json` 0.4133.
3. Consequently audit matrix row 16 ("all intervals agree to the third decimal") does not hold for these two limits. The point estimates in that row are correct.

No count, label, point estimate, rule-table entry, Holm value or bound failed to match.

## Not verified by P1

- Audit matrix rows 4 (ledger flags recomputed from mutant lists) and 5 (sha256 of the 15 concat sources). The audit scripts print neither figure, and no new check was written for them.
- Rows 18 (sealing chronology) and 21 (a judgement), and row 11 (a code reading).
- The §3 planning half-width comparison (0.204 at 30 bugs). Only the realized half-width was checked, (0.2735+0.1372)/2 = 0.205.
- The A2 sample contains no F2 PF and no CTRL PF (there are none in CTRL). PF coverage is the 4 F1 PF tests only. The A2 rule treats any timeout or harness_error run, or any disagreement among a version's three run signatures, as an exclusion. No sampled labelled instance hit those branches, so that part of the rule was not exercised against the stored labels.

## Files created

- `results/extension/audit/`: `rows.json` (written by `audit_recompute.py`), `A1_recompute.txt`, `A1_robustness.txt`, `A1_pilot.txt`, `A2_labels.txt`, `A2_labels.json`, `A3_jackknife.txt`, `A4_votes.txt`, `A5_gitdiff.txt` (empty), `A5_pytest.txt`, `P1_SUMMARY.md`
- `scripts/extension/audit/`: `a2_explore.py`, `a2_harness_peek.py` (field inspection), `a2_labels.py`, `a3_jackknife.py`, `a4_votes.py`
