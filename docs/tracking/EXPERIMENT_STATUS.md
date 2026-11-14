# Experiment status

Legend: **planned** (Phase 2) · **implemented** (code + tests) · **executed** (real run) · **analysed** ·
**verified** · **blocked** (named blocker).
As of 2026-10-30 (corrective pass): **no experiment has been executed with a real model; no research result exists.**

## Data pipeline

| Stage | Status | Evidence / blocker |
|---|---|---|
| D1 frame reconstruction + split | executed, verified | 312 → 234 methods; `data/processed/split_manifest.json` |
| C3 context extraction (B only) | executed | 234/234 contexts |
| C4 test generation (G) | implemented · **blocked** | needs key + approved pilot ceiling |
| C5–C7 compile + dual execution | implemented · verified on fixtures | Lang-1 integration PASSED (re-run in this pass after a stale-metadata fix) |
| C8 labelling + leakage guard file | implemented · verified | unit tests; guard written by `build_dataset.py` |
| C9 sampling | implemented · verified on synthetic | primary = within-project 1:2 (pre-existing reading); X-07 proportional alternative generated but **pending review, not applied**; pilot cap 150 |
| S2 spec inference | implemented · **blocked** | needs key |
| D2 seeded faults (Major) | executed locally (195/195 methods, final) | 148 methods with ≥ 1 verified mutant, 284 verified mutants; `data/processed/d2_summary.json` |
| Label audit (100) / spec audit (60) | sheet generator + scoring implemented · **sheets not generated** | need real instances / specs |
| D3 GitBug-Java | planned · **blocked** | Docker unavailable (X-05) |

## Safety mechanisms

| Mechanism | Status |
|---|---|
| Leakage guard on the live entry point | implemented · verified end to end (unit + mock e2e: 0 leaks in 12,330 prompts) |
| Budget guard, unknown-price error, attempt journal, possibly-charged accounting | implemented · verified (10 unit tests) |
| Provider pinning, provider-reported cost per call | implemented · **pin pending approval** |
| Replay mode (recompute from log, no key, no calls) | implemented · verified |
| No-mock check of research locations | implemented · CLEAN |

## Pilot gates (development split) — all **blocked** pending approval

P1 PF yield ≥ 3% · P2 0.2 ≤ J1 F1 ≤ 0.9 · P3 invalid < 2% per arm · P4 tokens → k_T · P5 label-audit agreement.

## Experiments

| ID | Status |
|---|---|
| E1–E3 | implemented (`E1E3_main.json`) · blocked (k_T needs P4) |
| E2 GLMM | implemented, validated on simulation (VB intervals under-cover → bootstrap CIs, X-06) · **not executed** |
| E4 ablations | implemented (`E4_ablations.json`) · blocked |
| E5-R1 D2 | mutants being built locally; generation + judging blocked |
| E5-R2 D3 | blocked (Docker) |
| E5-R3 M2 | implemented (`E5_R3_M2.json`) · blocked |
| E5-R4 paraphrases | to be written after the J1 prompt is final, before the freeze (pilot step P9 checks validity) |
| E5-R5 per-project / Wilcoxon / LOPO | implemented in `analyze.py` |

## Software validation (not research evidence)
62 unit tests pass · Lang-1 integration PASSED · mock e2e 3,424 decisions / 0 errors · contamination check CLEAN.
