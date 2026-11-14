# Stop report — M1 fails gate G-d after the fallback ladder (stop point 2)

2026-11-01. Local open-weight models only (Ollama v0.40.13, RTX 5070 Ti Laptop 12 GiB, driver 616.56).
API spend: $0. Held-out instances (14 projects / 195 methods), D2 seeded faults and D3: not read, generated,
executed or judged (scope lock enforced in code at generation, spec inference, execution, dataset build and
context repair; each refusal tested). Nothing is frozen.
All dev numbers below are a **dev pilot**, not results. These open models are **not equivalent** to the
original proprietary-model design.

## Status
G = gemma4:26b is selected (D-44). M2 = gemma4:12b passes its required gates (D-49). M1 = qwen3.5:9b passes
G-a, G-b and G-c after five prompt-development rounds, but **fails G-d**: its dev J1 F1 of 0.350 is below the
rule-based baseline R0 (0.642) and keep-all (0.553). The next larger quantization (q8_0) was worse (J1 0.138,
fails G-c too). Under the protocol (fallback 3) the authors choose how to proceed.

## Steps
| Step | Status | Key numbers | Evidence |
|---|---|---|---|
| 0 Decisions | done | D-21 … D-50 recorded before the steps they govern | `docs/tracking/DECISIONS.md` |
| Install, server | done | v0.40.13, auto-update off; WMI-launched server (D-30, ops) | `configs/local_server_env.json` |
| Code + tests | done | 96 tests pass (fake Ollama server; kill/resume; scope refusals) | `tests/unit/` |
| 1 Feasibility | done | qwen3.5:9b, gemma4:12b, gemma4:26b, qwen3.5:9b-q8_0 pass (D-39 screen, D-40 RAM per session); all judge layers on GPU (D-38, D-46) | `results/dev/feasibility/` |
| D-24 settings | done | NUM_PARALLEL 1, flash attention on: 1,770 calls/h | `results/dev/server_settings.json` |
| 1b Projection | done | Tier 1 62.9 h of 247.7 h available; no cuts | `results/dev/projection_1b.json` |
| 2 G selection | done | gemma4:26b: C1 0.595, C2 0.725, P1 23/459 = 5.0% (after defect fixes D-42/D-43, disclosed) | `results/dev/g_selection_gemma4_26b.json` |
| 3 Dev set | done | 118 instances (PF 21/TF 89/AMB 8); pilot 63; label audit sheets 71 (human task) | `data/processed/`, `docs/audits/` |
| Idempotency | done | hard kill + resume: 0 duplicate requests; rebuild 186/186 identical, 0 new calls | `results/dev/PROMPTDEV_v0/idempotency.json` |
| 4 Prompt rounds | done | 5 rounds; frozen candidate set `local_m1b` (judge v3, DEB v4) | `docs/local_models/PROMPT_ROUNDS.md` |
| 4 M1 gate (Q4_K_M) | **G-d fails** | G-a 100/99.7/100%, G-b pass, G-c 0.350, G-d 0.350 vs R0 0.642 (Δ −0.292, CI −0.507…+0.596); k_T = 5 | `results/dev/GATE_M1b/dev_gates.json` |
| Fallback 2 (q8_0) | **G-c, G-d fail** | J1 0.138, SC 0.074, DEB 0.194 | `results/dev/GATE_M1b_q8/dev_gates.json` |
| 5 M2 check | done | G-a/G-b pass; J1 0.222, DEB 0.267 (reported) | `results/dev/CHECK_M2/dev_gates.json` |
| Non-determinism | done | 0 flips, 100% identical text at T 0 and 0.7 (49) | `results/dev/nondeterminism.json` |
| 6 Freeze | **not done** | waits for the authors' choice | — |

## Dev pilot metrics, M1 = qwen3.5:9b Q4_K_M, prompts `local_m1b` (55 PF/TF instances, 12 bugs)
| Arm | F1 (bug-bootstrap 95% CI) | Precision | Recall | MCC | TP/FP/FN/TN |
|---|---|---|---|---|---|
| DA | 0.000 | — | 0.00 | 0.00 | 0/0/21/34 |
| KA | 0.553 (0.19–0.66) | 0.38 | 1.00 | 0.00 | 21/34/0/0 |
| R0 | 0.642 (0.00–0.77) | 0.53 | 0.81 | 0.36 | 17/15/4/19 |
| J1 | 0.350 (0.18–0.74) | 0.35 | 0.35 | −0.03 | 7/13/13/21 |
| SC | 0.333 (0.00–0.74) | 0.38 | 0.30 | 0.01 | 6/10/14/24 |
| DEB | 0.267 (0.00–0.63) | 0.40 | 0.20 | 0.03 | 4/6/16/28 |

The CIs are very wide (12 bug clusters). 15 of the 21 dev PF instances come from one bug family (Gson JsonWriter),
where the failing test contradicts the buggy version's own Javadoc; judges follow the documentation.

## Defects found and fixed during execution (each before the result it affects; each with a test)
D-35/36/37/41 truncation detection and token accounting · D-42 static imports lost in context extraction ·
D-43 runner lost failing tests on old-JUnit projects · D-47 my round evaluation counted validity on the wrong set.

## Options (protocol fallback 3)
- **(a) Proceed** with M1 = qwen3.5:9b Q4_K_M and `local_m1b`, and report "a local 9B judge does not beat keep-all
  or the rule-based baseline on dev" as a finding for RQ1. The freeze (Step 6) and the held-out plan follow.
- **(b) Switch to Option B**: G = qwen3.5:35b, M1 = gemma4:12b, M2 = qwen3.5:9b. Requires pulling qwen3.5:35b
  (~24 GB), regenerating and relabelling dev, new prompt rounds for gemma4:12b, and the gates again; it is model
  selection on the dev outcome and must be reported as such. On the current prompts gemma4:12b scored J1 0.222
  (below qwen's 0.350).
