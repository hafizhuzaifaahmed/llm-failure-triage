# Execution readiness: CFP confirmation

State on 2026-11-12. **Generation has not started and cannot start**: the readiness gate refuses it.
Authors' decisions: D-140. This file is the checklist the authors asked for before any experiment begins.

## 1. The five preconditions

Checked in code by `python scripts/extension/confirm_gate.py`; the generation driver calls the same checks and has
no override.

| # | Precondition | Status now | Who acts |
|---|---|---|---|
| 1 | OSF registration deposited, identifier and timestamp recorded, registered text identical to the repository's | **Open.** Text is final; nothing is deposited | authors (deposit), then the record command in section 3 |
| 2 | Default desktop Ollama server stopped | **Met when checked on 2026-11-12** (no `ollama app.exe` process). Re-checked at every start | — |
| 3 | Frozen study server answers with Ollama 0.40.13 and the frozen generator digest | **Open.** No server was running when checked; it is started only for a session | authors or the session start script; verified by the gate and by `session_check.py --start` |
| 4 | Dataset manifest and configuration hashes validate | **Met.** 8 frozen files and 11 parameters verified; 679 generation inputs match the manifest | — |
| 5 | No frozen experimental component changed | **Met.** Paper, prompts, frozen model config, study data and results, study source identical to `master`; engine identical to `eb2d231`; the scope lock only gained entries | — |

Current gate output: `NOT READY: generation is refused` (checks 1 and 3).

## 2. What exists

| Item | Where | State |
|---|---|---|
| Frame: F1 62 methods / 53 bugs, F2 371 / 269, Control 246 / 246 | `configs/extension/confirm_frame.jsonl` | frozen by hash |
| Generation inputs: one context per method, none missing | `data/extension/confirm/{F1,F2,CTRL}/context/` | hashed in `configs/extension/confirm_dataset_manifest.json` |
| Label-side bodies (for labelling and the leakage guard only) | `data/extension/confirm/<tranche>/label_side/` | separate from generation inputs |
| Dataset tags and run identifiers | `configs/extension/confirm_runs.json` | `D1C_F1`, `D1C_F2`, `D1C_CTRL`; one run name per stage and tranche |
| Scope lock | `configs/local_scope.json` | three dataset tags and six vote run names added; splits and models unchanged |
| Readiness gate | `scripts/extension/confirm_gate.py` | 9 tests |
| Gated generation driver | `scripts/extension/confirm_generate.py` | writes only under `data/extension/confirm/<tranche>/`; its mock mode was run once (no model call, output under `results/smoke/`) |
| Probe driver and analysis | `scripts/extension/run_probes_tranche.py`, `confirm_analysis.py` | frozen by hash |
| Planning simulation | `generated/power_planning.md` | C1 adequately powered; C2, C3, C4 underpowered |
| Registration text and deposit bundle | `OSF_PREREGISTRATION_CFP.md`, `osf_deposit/` | final; not deposited |

No earlier experiment's file was modified. New artefacts never enter `data/interim/context`, `data/processed`,
`data/ground_truth_store`, `data/raw/llm_calls_local` or `logs/sessions.jsonl`.

## 3. Steps for the authors

**A. Deposit on OSF** (an account and a login are needed; this cannot be done for you).

1. Create an OSF project and choose *Registrations → New registration → OSF Preregistration*.
2. Paste the sections of `docs/research_extension/OSF_PREREGISTRATION_CFP.md` into the template's fields. Confirm the
   author list. Choose public or embargoed.
3. Attach `docs/research_extension/osf_deposit/cfp_confirmation_frozen_bundle.zip` (registration text, frozen engine
   and scripts, frame, manifests, planning output, `SHA256SUMS.txt`).
4. Submit. Note the registration identifier, its URL and the registration timestamp shown by OSF.
5. **Do not edit the registration text in the repository afterwards**: the gate compares hashes.
   Registration text sha256 at the time of writing: `044cad8fe792ad0a9be823febb8ca525b709bdb13870bb2810bffa1e4a076aa8`.

**B. Record it** (then tell me, or run it yourself):

```bash
python scripts/extension/osf_package.py record --osf-id <id> --url https://osf.io/<id> --utc <YYYY-MM-DDTHH:MM:SSZ> --decision D-142
```

**C. Start a study session.** Make sure the desktop Ollama app is closed, start the frozen server with
`scripts/local/start_ollama_server.ps1`, and run:

```bash
python scripts/local/session_check.py --start
```

```bash
python scripts/extension/confirm_gate.py
```

The gate must print `READY TO GENERATE`. I will report that status before starting anything.

## 4. Run order once the gate passes

| Step | Command or component | Output | Built? |
|---|---|---|---|
| 1 | `confirm_generate.py --tranche F1`, then `F2`, then `CTRL` (GPU; no test execution meanwhile) | candidates and call log per tranche | yes |
| 2 | `confirm_pipeline.py execute --tranche T` (WSL): compile and execute every test on the buggy and fixed versions | execution records per tranche | yes (D-142) |
| 3 | `confirm_pipeline.py label --tranche T`: label by the unchanged rule; build instances and guard; then commit them (sealing) | labels and instances per tranche | yes (D-142) |
| 4 | `run_probes_tranche.py` per tranche | ledgers `CFP_CONF_F1`, `CFP_CONF_F2`, `CFP_CONF_CTRL` | yes (frozen) |
| 5 | `confirm_pipeline.py vote --tranche F1/F2 --model M1/M2/M3`: one-shot votes; the guard is built in step 3 | six vote runs | yes (D-142) |
| 6 | `confirm_pipeline.py concat`: read-only concatenation of the three tranches | `CFP_CONF_ALL` | yes (D-142) |
| 7 | `confirm_analysis.py` | the registered family and secondaries | yes (frozen) |

Steps 2, 3, 5 and 6 reuse the study's own modules through `scripts/extension/confirm_lib.py` and
`confirm_pipeline.py` (D-142). Each was validated against the original stored data before any confirmation data
exist; reports in `results/extension/validation/`:

| Driver | Reproduction | Result |
|---|---|---|
| Labelling | D1 labels, instances, guard and exclusions rebuilt from the stored execution records | byte-identical (487 / 487 / 487 / 3,129 records) |
| Votes | E8's three vote runs replayed from the committed call logs, with a backend that cannot call | 189 of 189 decisions identical for each judge |
| Concatenation | pilot split into three parts by bug, concatenated, analysed by the frozen script | identical to the committed dry run in every section |
| Execution | all 702 stored D1 test classes re-executed in WSL (6 workers), labels compared method by method | compilation identical for 702 of 702; labels identical for 2,907 of 2,909 methods. The 2 differences are one dev-split test (`Cli_8`) whose fixed-version runs take 23–28 s against the 30 s limit and timed out under load; re-run alone they match (TF). A third method of the same class flipped the other way alone (stored TIMEOUT, 25 s alone). No held-out triage instance has a run of 20 s or more |

**Known property of the frozen label rule:** a test whose runs approach the 30 s wall-clock limit can be labelled
differently under different machine load. The labelling driver therefore reports, descriptively, how many methods
have any run of 20 s or more, by label (`near_time_limit` in the tranche summary). Run confirmation execution with
6 workers, as the study did, and with no other heavy work on the machine.

## 5. What is deliberately not done

- No generation, no test execution on new data, no judge call.
- Nothing deposited, published or pushed.
- The paper, the numbers map and the defence deck are unchanged.
- Stage B is deferred; `STAGE_B_PLAN.md` is unchanged.
