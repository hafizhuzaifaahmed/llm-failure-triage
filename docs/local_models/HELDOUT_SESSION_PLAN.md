# Held-out run — session plan (approved D-58, scope D-59 as amended by D-66/D-67)

Approved 2026-11-01 (D-58). Compute ends **2026-11-12 23:59**; 13–15 Nov are analysis and writing. Budget: ~13–15
running hours per day in two sessions (night 8–10 h, day ≈ 5 h), × 0.8 duty (D-62). Projection with the real D1-test size
(193) under D-66 (`results/heldout/projection_latest.json`): need **60.5 h** incl. Tier 3 of **113.6–131.1 h**; 53–71 h left
for the 35b (cost unknown until feasibility). Re-projected after each tier and reported; anything
that will not fit → stop and ask the authors, nothing is cut unilaterally.

## Scope (D-59, amended by D-66/D-67 once the real D1-test size was known)
- Tier 1 E1–E3 at **3 replicates** plus **SC-T** (S1, k_T = 5, independent samples, 3 replicates; "SC-T uses the SC
  configuration at k_T = 5"). E4 at its planned 1 replicate. D2 judging at its planned 1 replicate.
- Tier 3 / E5-R3 with M2 (S1, 1 rep) on D1-test **and** D2, after D2, iff the D-61 time check after Tier 2 holds.
- Exploratory qwen3.5:35b (D-67): last, separate server with flash attention off, own sessions; feasibility probes first,
  dropped with no further change if it crashes; J1 → DEB → SC passes; then restart the frozen server + session_check.
- No extra generations or other enlargement of D1-test (60 PF / 193 is reported as a limitation).

## Every session
0. In the shell that runs the Python entry points: `. scripts\local\session_env.ps1` (PowerShell) or `source scripts/local/session_env.sh` (Git Bash) — sets `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` (D-73). WSL stages get `PYTHONUTF8=1` from `scripts/wsl/run.sh`. Client only; the Ollama server env is unchanged.
1. **resume**: server up via `src/triage/ollama_server.py` (WMI launcher, frozen env). Never update Ollama, drivers or models.
2. `python scripts/local/session_check.py --start` must pass (frozen version/driver/digests, probes, residency) →
   logged in `logs/sessions.jsonl`. Any problem → stop.
3. Generation sessions: the D-40 RAM precondition (≥ 4 GiB available after G loads) runs automatically.
4. Continue the next step's command; runs are idempotent (call log + decisions).
5. **stop**: create `logs/STOP`. The LLM client starts no new call (the call in flight finishes), WSL execution
   starts no new bug job; the process exits cleanly. Then `session_check.py --end`, commit, update PROGRESS.md,
   remove `logs/STOP` at the next resume.
6. Never G generation concurrently with WSL Defects4J. Judge runs use `--workers 1`.

## Order
| # | Step | Command / config | Est. |
|---|---|---|---|
| 0 | Activate held-out scope | `configs/local_scope.json` (done 2026-11-01; `results/heldout/scope_activation_check.json`) | — |
| 1 | Repair held-out context imports (D-42) | WSL `repair_context_imports.py --split test` | 0.2 h |
| 2 | G generation, 195 × 3 (RAM precondition) | `generate_tests.py --split test --local` | 2.1 h |
| 3 | WSL execution (G unloaded) + labelling | `run_execution.py --candidates data/interim/candidates_gemma4_26b …` | ≈ 2 h wall |
| 4 | D1-test dataset, overall/proportional sample (D-53) + leakage guard; **re-project with the real size** | `build_dataset.py --splits dev,test …` | minutes |
| 5 | S2 specs (M1) | `infer_specs.py --split test --local` | 0.2 h |
| 6 | **Tier 1** E1–E3, 3 replicates + SC-T (D-66) | `run_experiment.py configs/experiments/LOCAL_HO_E1E3_M1.json --workers 1` | 23.1 h |
| 7 | **Tier 2** E4 ablations (+ S2′ specs) | `infer_specs.py --split test --prime --local`; `LOCAL_HO_E4_M1.json` | 24.6 h |
| 8 | **D2**: contexts, generate, specs, execute, dataset (cap 300, D-64), judge E1–E3 (1 rep) | `scripts/d2_pipeline.py …`; `LOCAL_HO_E5R1_D2.json` (added to the scope then) | 22.7 h |
| 8b | **Tier 3** (D-61 check after Tier 2) | `LOCAL_HO_E5R3_M2.json`, `LOCAL_HO_E5R3_M2_D2.json` | 7.9 h |
| 8c | **Exploratory 35b** (D-67), separate server, FA off | feasibility probes, then `EXPL_35B_D1TEST.json` J1 → DEB → SC | unknown |
| 9 | Analysis (F1 with MCC beside it everywhere; DEB vs SC as the token-matched check) | `analyze.py` | — |
