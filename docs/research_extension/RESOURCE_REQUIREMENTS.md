# Resource requirements: fresh-fault confirmation of CFP

Prepared 2026-11-11 under D-138. **Nothing here has been started.** Figures marked *measured* come from this
repository's own logs; figures marked *estimate* are extrapolations and say from what.

## 1. What would be generated

Frames are fixed in `configs/extension/confirm_frame.jsonl` (hash in `configs/extension/cfp_frozen.json`).
All bugs are in held-out projects and none was ever generated for by the original study.

| Tranche | Rule | Methods | Bugs | Generations per method | Generation calls |
|---|---|---|---|---|---|
| F1 | Original-frame methods the per-project cap left out, in unseen bugs | 62 | 53 (Math 33, Lang 18, Mockito 2) | 6 | 372 |
| F2 | Fix-changed public/protected methods present in both versions that no bug-triggering test invokes by name; at most 3 per bug | 371 | 269 (13 projects; JacksonDatabind 80, Closure 55, Math 39) | 3 | 1,113 |
| CTRL | One method per bug that the fix did not change, matched on mutant count (control group) | 246 | 246 (76 bugs have no eligible method) | 3 | 738 |
| **Total** | | **679** | **322** | | **2,223** |

Why the frame was widened: the 78 capped-out methods contain only 53 unseen bugs, all in three projects. In the
original data 27 of 167 bugs had a bug-revealing test and that count saturated across generations (19, 26, 27 after
one, two, three), so extra generations add tests, not bugs. More bugs are the only way to more evidence.

## 2. Generator

| Item | Value | Source |
|---|---|---|
| Model | `gemma4:26b` (Gemma 4 26B-A4B), 25.2B parameters, Q4_K_M, digest `001e5dafc3c7…` | `configs/local_models.FROZEN.json` |
| Runtime | Ollama 0.40.13, bundled llama.cpp runner, frozen server (`scripts/local/start_ollama_server.ps1`) | same |
| Server settings | context 8,192; one model loaded; one parallel request; flash attention on; KV cache f16; keep-alive 30 min | `server_env` in the frozen config |
| Decoding | temperature 0.7, top-p 1.0, top-k 64, min-p 0, at most 4,096 output tokens, thinking off, one seed per call | generator call log |
| Prompt | `local_m1b` set, generator template `8b08a25d…`, buggy method body and class signature | frozen config |
| Generation index | 0–5 for F1, 0–2 for F2 and CTRL (the sample index, as in the study) | `src/triage/generation.py` |

Unchanged from the original study. Nothing is pulled, updated or re-quantised.

## 3. Hardware and server

| Item | Requirement | Measured on this machine |
|---|---|---|
| GPU | 12 GB class | RTX 5070 Ti Laptop, 12,227 MiB; generator peak VRAM 10,810 MiB, about 0.3 GB of the model on the CPU side |
| RAM | 32 GB | 31.4 GB; the generator's mixture-of-experts layers use host RAM |
| CPU | any; execution and probes use 6 to 12 processes | 24 logical cores in WSL |
| Constraint | no test execution or other heavy CPU work while the generator is loaded (D-64) | generation and execution must run in sequence, not together |
| Constraint | the default Ollama desktop server that `ollama list` started on 2026-11-11 must be stopped before the frozen server starts | still running at the time of writing |

## 4. Time

| Step | Basis | Estimate |
|---|---|---|
| Tranche tooling (context extraction for 679 methods, a dataset tag, guard, scope entry, smoke test) | engineering; follows the pattern of the second-generator experiment (D-100) | 0.5–1 day of work, no GPU |
| **Generation**, 2,223 calls | *measured:* 14.9 s mean per call on D1 (702 calls, 2.91 h), 17.9 s on D2 (852 calls, 4.24 h) | **9.2–11.1 h of GPU**, in two or three sessions |
| Compile 322 bugs × 2 versions and execute 2,223 test classes, 3 runs per version | *measured:* 585 classes over 140 bugs in 23.6 min with 6 workers, compilation included | **1.5–3 h** (*estimate*; this tranche is heavier in Closure, JacksonDatabind and Mockito, which build slowly) |
| Labelling, dataset build, leakage guard | deterministic | minutes |
| **Probes** on about 1,530 failing tests | *measured:* 3.3 s per failing test all-in on D1-test (369 in 1,228 s); failing tests per generation 0.69 on D1 (487 of 702) | **1.5–2.5 h** of CPU (*estimate*) |
| Judge votes for hypotheses C3 and C4 (three one-shot judges on about 1,025 F1/F2 failures) | *measured:* 8.0 GPU-seconds per failure for the three-judge panel on D2 | **about 2.3 h of GPU** plus three model loads |
| Analysis | scripted | minutes |
| **Total machine time** | | **about 15–19 h**, of which 11.5–13.5 h GPU |

A realistic schedule is three working days: tooling and smoke test; generation overnight in two sessions; execution,
probes, votes and analysis.

## 5. Storage

| Item | Basis | Estimate |
|---|---|---|
| Candidates, execution records, generator call log | *measured:* 4.8 + 19.7 + 10.1 kB per generation | about 80 MB |
| Generation contexts | *measured:* 26 kB per method | about 18 MB |
| Probe ledgers | *measured:* about 10 kB per failing test | about 15 MB |
| Judge call logs and decisions | from the study's logs | under 100 MB |
| Repository growth | | **about 0.2 GB** |
| WSL: compiled classes for 322 already checked-out bugs | *measured:* compiled checkouts range from 40 MB (Lang, Math) to 375 MB (Mockito) per version | **under 15 GB** (*estimate*); 897 GB free |
| WSL probe scratch | removed per focal method | under 1 GB transient |

No download is needed: all 322 bugs are already checked out in `~/triage_work` (uncompiled).

## 6. What the confirmation can and cannot show

| Quantity | Value | Kind |
|---|---|---|
| Unseen bugs | 322 | exact |
| Bugs expected to yield a bug-revealing test | **about 30–50** | *estimate:* 16% of bugs did in the original frame (27 of 167), 15% in Math, Lang and Mockito (8 of 55); the F2 rule has never been run, so 8–16% is assumed there |
| Bug-revealing tests expected | roughly 100–200 | *estimate* from 81 in 702 generations |
| Bound on the bug-loss rate if a rule loses no bug | 9.5% at 30 bugs, 5.7% at 51 | exact binomial, 95% one-sided |
| Earlier target of 60 such bugs | **not reachable** from Defects4J under either frame rule with three generations | stated so the registration does not promise it |

The design is therefore fixed in advance (every frame row, a fixed number of generations) with no stopping rule that
looks at counts. If the yield in F2 is near the low end, hypotheses C1 and C2 (rates) remain testable; C3 and C4
(rules) will have wide intervals. The registration says this.

## 6a. Planning for 30, 40 and 50 bugs (added 2026-11-12, D-140 and D-141)

Full table: `generated/power_planning.md` (planning simulation on pilot data; not a result).

| Hypothesis | Supported at the strictest Holm step if only half the pilot effect holds, at 30 / 40 / 50 bugs | Classification |
|---|---|---|
| C1 flip rate | 0.830 / 0.927 / 0.988 | adequately powered |
| C2 decoupled rate | 0.362 / 0.500 / 0.552 | underpowered (adequate only at the full pilot effect: 0.963 / 0.998 / 1.000) |
| C3 KUU + CD | 0.058 / 0.087 / 0.098 | underpowered |
| C4 2-of-3 + CK | 0.128 / 0.175 / 0.362 | underpowered |

One-sided 95% upper bound on a rule's bug-loss rate with 0 / 1 / 2 bugs lost: 30 bugs 0.095 / 0.149 / 0.195;
40 bugs 0.072 / 0.113 / 0.149; 50 bugs 0.058 / 0.091 / 0.121.

Consequence: the confirmation can settle C1. For C2 to C4 a non-supported result will be inconclusive. No stopping
rule depends on outcomes; the frame and generation counts are fixed.

## 7. Stage B (probe report shown to the judge), separate from the confirmation

| Arm set | Calls | Basis | Estimate |
|---|---|---|---|
| M1 one-shot, thinking off: 3 evidence conditions × 177 instances × 3 replicates | 1,593 | *measured:* 1.7 s median per one-shot call | about 45 min of GPU |
| M1 one-shot, thinking on: 3 conditions × 177 × 1 | 531 | *measured:* about 70 s per call (D-131) | about 10.3 h of GPU |

Details and the budget-matching rule are in `STAGE_B_PLAN.md`.

## 8. Cost in money and data egress

None. No paid API, nothing leaves the machine. External registration on OSF is free but is an external action.

## 9. Decisions needed from the authors before anything starts

| # | Decision | Default if approved as proposed |
|---|---|---|
| 1 | Approve the widened frame (F2) and the control group as defined | 2,223 generations |
| 2 | Approve about 11.5–13.5 h of GPU time and 3–5.5 h of execution and probe time on the study machine | three sessions |
| 3 | Approve adding one dataset tag and the new run names to `configs/local_scope.json` (the study's own lock; every earlier extension did this through a decision entry) | one entry, D-139 |
| 4 | Register the preregistration externally (OSF) before the first generation call, or keep it as a committed, hashed internal record | not registered until you say so |
| 5 | Approve the three-judge votes for C3 and C4 (2.3 h GPU). Without them the family is C1 and C2 only | include |
| 6 | Stage B: run after the confirmation, before it, or not yet | after |
| 7 | Stop the default Ollama desktop server (I could not: blocked by the session's permissions) | you |
