# Execution brief for Claude Opus 5.5

Version 4, 2026-11-14 (section 12 is the latest addendum and is authoritative where it differs from earlier
sections). Written by the lead research model after the audit and the design phase; amended on the
authors' **conditional approval** of 2026-11-13 (section 10); amended again on their **review of freeze commit
`3c59196`** (section 11, which is authoritative wherever it differs from sections 1 to 10).
Opus implements and runs exactly what is written here and makes no scientific-design decision. Where the brief is
silent or something does not work as described: stop, record what was found, and ask.

Read first, in this order: this file; `TECHNICAL_METHOD_SPEC.md` (version 2); `CONFIRMATION_INDEPENDENT_AUDIT.md`
§1, §7, §8; `RESEARCH_STATE_2026-11-13.md`. You do not need the rest of the repository history.

## 0. Standing rules

1. Never edit, re-run into, or overwrite: any path in `configs/extension/cfp_frozen.json`; anything under
   `data/extension/confirm/`, `results/extension/confirm/`, `results/extension/probes/`;
   `docs/research_extension/OSF_PREREGISTRATION_CFP.md`, `STAGE_B_PLAN.md`, `generated/confirm_report.md`.
2. No external registration, deposit, account or amendment of any kind (OSF, AsPredicted, journal registry, or any
   other platform) before 16 November 2026, and none afterwards without the authors' explicit approval. Leave
   OSF kp79c and `OSF_RECONCILIATION.md` alone.
3. No model call of any kind. No Stage B. Do not start, stop or query Ollama. Never run `ollama list` or
   `ollama ps`.
4. No push. Commit locally only, with no AI attribution or co-author line (authors' standing rule).
5. Preserve each file's line endings. Use scratch `.py` files rather than shell heredocs for Python with quotes.
6. Do not change a method, threshold, sample, outcome or exclusion rule to improve a result. A necessary deviation
   is written into `docs/tracking/DECISIONS.md` **before** the affected result is computed, and is reported.
   The method criteria are never weakened and the analysis is never changed to obtain a better result.
7. Every WDP result is **exploratory**. Its runs on existing data are **retrospective evaluation runs**. The words
   "confirmatory", "preregistered", "registered", "validated" and "held-out" are never applied to them. The
   phrase to use is: "exploratory; protocol frozen internally in Git before the run; not externally preregistered;
   designed after the confirmation outcomes were known".
8. **Approval gate.** `WDP_D1_TEST` and the three `WDP_CONF_*` runs must not be started until the authors have
   reviewed the freeze commit and approved it in writing. Until then the only WDP run allowed is `WDP_D1_DEV`.
9. **Manuscript first.** If WDP work threatens completion of the `_v2` manuscript by 15 November, stop WDP, report
   it in the paper as future work (design only), and finish the manuscript.

## 1. What is being built and why this and not something else

**Primary technical contribution:** whole-method dependence probes (WDP) and the certificate CD-U
(`TECHNICAL_METHOD_SPEC.md`).

Why it was chosen over the alternatives (`UPDATED_NOVELTY_AND_CONTRIBUTION_ASSESSMENT.md` §5):

- The confirmation removed the flip observable. Only decoupling survived, so the extension must stand on it.
  Stage B and a learned score both lean on flip evidence.
- Both bugs the decoupling certificate has ever lost are operator gaps, not independent failures. WDP replaces the
  whole method and has no tuned parameter.
- It decides the 102 tests the ten-mutant minimum leaves undecided.
- No model calls, minutes of CPU, so it is the only candidate that can be completed and checked before the
  deadline without displacing the manuscript.

**Fallback:** if a stop condition in section 6 fires, or rule 0.9 applies, there is no new method and WDP is
future work. If the runs complete and pass their quality checks but the primary criterion is not met, there is no
new method either, and the descriptive ladder is still reported (authors' decision of 2026-11-13).

**Not to be done:** Stage B (any arm); an e-Otter++-style patch arm; any new generation; any judge call.

## 2. Experiment definition

### 2.1 Runs and datasets

One deterministic procedure, no randomised arms. One engineering run and four retrospective evaluation runs:

| Run name | Kind | Tests | Instances file | Frame | Executions | Candidates | First-order ledger used for `fo_changed` |
|---|---|---|---|---|---|---|---|
| `WDP_D1_DEV` | engineering only | 118 | `data/processed/instances_D1.jsonl`, split `dev` | `data/processed/frame_d1.jsonl` | `data/raw/executions_gemma4_26b` | `data/interim/candidates_gemma4_26b` | `results/extension/probes/CFP_D1_DEV2/ledger.jsonl` |
| `WDP_D1_TEST` | retrospective evaluation (gated, rule 0.8) | 369 | same file, split `test` | same | same | same | `.../CFP_D1_TEST/ledger.jsonl` |
| `WDP_CONF_F1` | retrospective evaluation (gated) | 160 | `data/extension/confirm/F1/instances_D1C_F1.jsonl` | `configs/extension/confirm_frame.jsonl` | `data/extension/confirm/F1/executions` | `data/extension/confirm/F1/candidates` | `.../CFP_CONF_F1/ledger.jsonl` |
| `WDP_CONF_F2` | retrospective evaluation (gated) | 428 | `.../F2/instances_D1C_F2.jsonl` | same | `.../F2/executions` | `.../F2/candidates` | `.../CFP_CONF_F2/ledger.jsonl` |
| `WDP_CONF_CTRL` | retrospective evaluation (gated) | 246 | `.../CTRL/instances_D1C_CTRL.jsonl` | same | `.../CTRL/executions` | `.../CTRL/candidates` | `.../CFP_CONF_CTRL/ledger.jsonl` |

Outputs go to `results/extension/wdp/<RUN>/ledger.jsonl` and `run_meta.json`. A run is resumable by instance id
and is never restarted from scratch once it has records, unless the authors say so.

### 2.2 Immutable baselines and the matched comparison population

All rules are computed on the same tests with the same stored votes; nothing is re-judged.

| Population | Definition | Size |
|---|---|---|
| CONF-all | F1 and F2 instances labelled PF or TF | 572 (55 PF, 21 PF-bearing bugs) |
| CONF-votes | CONF-all with three votes at replicate 80, arm J1, level S1 (`data/extension/confirm/{F1,F2}/votes/LOCAL_CONF_VOTE_{M1,M2,E6B}_{F1,F2}/decisions.jsonl`) | 561 (54 PF) |
| PILOT-all | D1 test split, labelled PF or TF (`data/ground_truth_store/labels_D1.jsonl`) | 356 (60 PF, 22 PF-bearing bugs) |
| PILOT-votes | the D-110 common set, with KUU and 2-of-3 loaded exactly as `scripts/extension/ext1_probe_analysis.py` loads them (`revision_common`, `d.preds["KUU|S1"][0]`) | 177 (60 PF) |
| CTRL | control failures | 246 (all TF) |

| Rule | Definition | Role |
|---|---|---|
| KUU | discard only if all three valid votes say test fault (`rm.k_of_n(votes, 3)`) | **the baseline to beat**: the original paper's rule, the only rule with no lost bug in the confirmation |
| 2-of-3 | discard if at least two valid votes say test fault | second baseline |
| keep-all | keep everything | reference |
| KUU + CD | registered certificate (`policy.decoupled_discard`) | the registered extension, for comparison |
| KUU + CD-U | **primary** | new |
| KUU + CD-UR, 2-of-3 + CD-U, keep-all + CD-U | secondary | new |

Why KUU is the strongest relevant comparator: the practical requirement stated by the authors is to lose no
bug-revealing test's bug, and on the confirmation tests KUU is the only stored rule that loses none (TPR 1.000,
TNR 0.316). The cascade and the thinking judge of the original paper were not run on the confirmation tests, and
running them would need new model calls; their published values come from another sample and are context only.

### 2.3 Splits, grouping, leakage prevention

- No parameter is fitted, so there is no training split. `WDP_D1_DEV` is used to debug the engine and for nothing
  else; no dev figure appears in the paper except the disclosure that the run happened.
- The unit of resampling is the bug. Pilot and confirmation share no bug (verified: 0 of 322).
- The WDP package cannot read labels, the fixed version, `label_side/`, developer tests or judge decisions
  (section 3, test T1). Labels and votes are read only by the analysis script.
- The implementation, the variant table, the level function, the screen, the analysis script, the method
  specification and this brief are hashed and committed before any retrospective evaluation run (step P3), and
  that commit is approved by the authors before any such run (step P3b).

### 2.4 Outcomes

**Primary outcome (one):** on CONF-votes, ΔTNR = TNR(KUU + CD-U) − TNR(KUU), paired, with a bug-level bootstrap
95% interval.

**Safety constraint:** on CONF-votes, bugs lost by KUU + CD-U must equal bugs lost by KUU (zero). A bug is lost when
it has a PF test and none is kept.

**Primary criterion.** MET if and only if all three hold: (i) the safety constraint; (ii) the lower limit of the
interval for ΔTNR is above 0; (iii) the decoupled PF test of `Math_59` is not level U.
Otherwise NOT MET. There is no third category and no p-value.

**Secondary outcomes** (all descriptive, intervals without tests):

1. The same contrast on PILOT-votes, and whether KUU + CD-U loses any bug KUU keeps there; the level of the
   decoupled PF test of `Codec_13`.
2. KUU + CD-U against KUU + CD (registered): ΔTNR, ΔPF tests lost, Δbugs lost, paired.
3. P(U | TF) − P(U | PF), and the same for U ∪ RI, on CONF-all and PILOT-all.
4. The ladder: counts of FS, WS, RI, U and ND (by reason code) by label, by dataset, by frame, by project, and
   inside the registered `decoupled` set.
5. The low-mutant stratum (fewer than ten compiled first-order mutants and no FLIP or SHIFT): levels by label.
6. Rule table for every rule in 2.2: TPR, TNR, balanced accuracy, PF tests lost, bugs lost with their names, exact
   one-sided 95% upper bound on the bug-loss rate, tests kept, share of kept tests that are PF.
7. Inspection workload: wrong tests kept per bug-revealing test kept, at the labelled prevalence and at 5%
   prevalence, the latter as (1 − π)(1 − TNR) / (π · TPR) with π = 0.05, stated as an assumption.
8. Pre-filter effect: share of tests at level U (three judge calls avoided each), and how many of them KUU already
   discards.
9. Heterogeneity: outcome 3 and the primary contrast for F1 and F2 separately, without the two Jackson projects,
   and leave-one-project-out.
10. Control group: level distribution.
11. Cost: seconds and executions per test, beside the first-order ledger's `seconds`.
12. Diagnostics, by label: exclusions; ND by reason code, with `throw_swallowed` and `swallow_risk` shown
    separately (these two are the cost of the conservative handling: tests that would have been level U without
    it); variants that did not compile; ERR counts; `entered` by level; marker-consistency violations
    (`surfaced` and not `entered`); records with `x_throw` CHANGED and `entered` false; records with `x_throw`
    SAME and an `X-RET` variant CHANGED.

No ranking method is proposed, so AUROC and top-k are not outcomes.

### 2.5 Statistical procedure

- Bug-level cluster bootstrap, 10,000 resamples, seed **20261113**, identical resamples for both sides of a paired
  difference, percentile intervals; implemented in the new analysis script without importing
  `confirm_analysis.py` (it may import `triage.stats`).
- Exact one-sided 95% Clopper–Pearson bounds for bug-loss rates.
- **Multiplicity:** one primary criterion; everything else is descriptive and labelled so. No Holm family, no
  "supported / not supported" wording (that vocabulary belongs to the registered analysis).
- Missing data: an instance without three votes is excluded from rule tables only; an instance the WDP engine
  excludes is level ND (or FS if the first-order ledger says so) and stays in every denominator.
- If and only if the criterion is MET on CONF-votes and KUU + CD-U loses no additional bug on PILOT-votes, also
  report the pooled bound: additional bugs lost 0 of 43 PF-bearing bugs, one-sided 95% upper bound
  1 − 0.05^(1/43) = 0.067, **with the sentence that the rule was designed with knowledge of these bugs, so the
  bound is optimistic and is not a guarantee.**

### 2.6 Models, prompts, decoding

None. No generation, no judge call. Votes are read from committed files (confirmation: replicate 80; pilot: as
loaded by `ext1_probe_analysis.py`). Model names appear in the report only to identify the stored votes
(M1 Qwen3.5 9B, M2 Gemma 4 12B, M3 Ministral 3 14B).

## 3. Implementation

### 3.1 Files to create (and only these, plus tests and outputs)

| Path | Content |
|---|---|
| `src/triage_dep/__init__.py` | empty |
| `src/triage_dep/interventions.py` | pure text: `return_type(method_text)`, `variants(method_text) -> [{id, body}]`, `apply(method_text, body) -> str`, following spec §2.1. The `X-THROW` body is the exact string of spec §2.1. Uses `triage_ext.mutate.tokenize` and `_body_start` by import |
| `src/triage_dep/screen.py` | pure text: `swallow_risk(test_class_source) -> bool` (spec §2.3), on the source with comments and string and char literals removed (use `triage_ext.mutate.tokenize` token kinds) |
| `src/triage_dep/wdp.py` | engine: class `WdpProbe(focal_id, bug_name, rel_file, impl, meta=None)` (an injected `meta` is for the toy fixture only) with `probe(inst, test_src, pkg, cls, stored_run)`; imports `load_meta, read_source, locate, compile_overlay, SOURCE_LEVELS, SCRATCH` from `triage_ext.probe`, `_javac` and the names `run_test` itself uses from `triage.execution`, and `classify, signature, message_digest` from `triage_ext.ledger`. Its own `run_test_env(fqcn, method, cp_front, meta, timeout, extra_env)`: a copy of `triage_ext.probe.run_test` that differs only in merging `extra_env` into the subprocess environment. Baseline run 30 s, variant runs 10 s, a pass is re-run once, same exclusion names as the engine. Marker path: `<per-test scratch dir>/marker_<variant>_<n>`; must not exist before the run; `entered` = it exists after the first `X-THROW` run. Scratch directory `SCRATCH / "wdp" / <sha1(focal_id)[:16]>`, removed per method |
| `src/triage_dep/levels.py` | pure: `level(wdp_record, first_order_summary) -> (level, nd_reason)` (spec §2.4, first match wins), `cd_u`, `cd_ur` (spec §2.5) |
| `scripts/extension/run_wdp_tranche.py` | WSL entry point; arguments `--run --instances --frame --exec-dir --cand-dir [--split]`; the same allow-list of execution fields as `run_probes_tranche.py`; writes `results/extension/wdp/<run>/`. **It refuses any run name other than `WDP_D1_DEV` unless the file `configs/extension/wdp_run_approval.json` exists** and names the freeze commit; that file is created only after the authors' approval (step P3b) |
| `scripts/extension/wdp_analysis.py` | sections 2.4 and 2.5; writes `results/extension/wdp/wdp_analysis.json` |
| `scripts/extension/wdp_report.py` | renders `docs/research_extension/generated/wdp_report.md` from the JSON; the first line states the status sentence of rule 0.7 |
| `scripts/extension/freeze_wdp.py` | writes `configs/extension/wdp_frozen.json`: sha256 (CRLF normalised to LF) of the code files above, of `TECHNICAL_METHOD_SPEC.md` and of this brief, with a UTC time |
| `tests/extension/test_wdp.py`, `tests/extension/test_wdp_integration.py` | section 3.2 |

Return type parsing: take the method header (text before the body's opening brace), drop annotations, modifiers
(`public protected private static final synchronized abstract native strictfp default`) and a leading type-parameter
list `<…>`; the declared type is everything between that point and the method-name token that precedes the
parameter list. If parsing fails, the method gets `X-THROW` only and the record carries `return_type: null`.

### 3.2 Tests (T1–T10 must pass before the dev run; T11–T13 before step P3)

| ID | Test |
|---|---|
| T1 | Boundary: scan `src/triage_dep/*.py` and `run_wdp_tranche.py` for any reference to the fixed checkout, `label_side`, label files, `meta_f`, developer-test metadata or judge decisions; mirror `tests/extension/test_boundary.py` |
| T2 | `variants()` for each row of the spec's table: `void`, `boolean`, each numeric primitive, `char`, `String`, `java.lang.String`, `Object`, `int[]`, `List<String>`, `Map<K, V[]>`, boxed `Integer`; ids stable; at most three; the `X-THROW` body equals the spec's string byte for byte |
| T3 | `apply()`: signature byte-identical; exactly one body; correct on nested braces, braces inside string and char literals and comments, `throws` clauses, annotations with arguments, generic methods, CRLF text |
| T4 | `level()`: one case per row of spec §2.4, in order, and an exhaustive enumeration of excluded × `x_throw` × `entered` × `swallow_risk` × `X-RET` classes × `fo_changed` asserting a single level from {FS, ND, WS, RI, U} and, for ND, a single reason code |
| T5 | **U is never returned when `entered` is true, when `swallow_risk` is true, or when `entered` is null** (property over the same enumeration) |
| T6 | `cd_u`, `cd_ur`: act only at the stated levels; never return PROGRAM_FAULT for a TEST_FAULT base; never act at ND |
| T7 | `swallow_risk`: true for `catch (Throwable t)`, `catch (final Error e)`, `catch (java.lang.Throwable t)`, `catch (IOException \| Error e)`, `@Test(expected = Throwable.class)`, `@Test(expected=java.lang.Error.class)`, `assertThrows(Error.class, …)`, `expectThrows(Throwable.class, …)`, `thrown.expect(Throwable.class)`; false for `catch (AssertionError e)`, `catch (Exception e)`, `throws Throwable` in a signature, `MyError`, and for each positive construct placed inside a comment or a string literal |
| T8 | `run_test_env` with an empty `extra_env` builds the same command and environment as `triage_ext.probe.run_test` (compare by patching `subprocess.run`) |
| T9 | Analysis script on a synthetic fixture with known counts reproduces them, including a lost bug, ND reasons and the paired bootstrap's determinism under the seed |
| T10 | `tests/extension/test_freeze.py` and the whole existing extension test directory still pass |
| T11 (WSL) | End-to-end toy fixture, independent of Defects4J: a small class with one method and five JUnit tests, compiled into a temporary directory and probed through `WdpProbe` with an injected `meta`. Expected: (a) fails before calling the method → **U**, `entered` false; (b) calls the method inside `try { … } catch (Throwable t) { }`, then fails on an unrelated assertion → **ND `throw_swallowed`**, `entered` true; (c) calls the method on a new thread, joins, then fails on an unrelated assertion → **ND `throw_swallowed`**, `entered` true; (d) calls the method, ignores the result, fails on an unrelated assertion → **RI**, `entered` true; (e) asserts a wrong value on the method's result → **WS** (first-order summary absent), `entered` true |
| T12 (WSL, after the dev run) | Marker consistency on `WDP_D1_DEV`: zero records with `surfaced` true and `entered` false; and at least one record with `surfaced` true (otherwise the check is vacuous: stop) |
| T13 (WSL, after the dev run) | re-run 30 seeded dev instances (seed 20261113): identical levels and reason codes |

### 3.3 Commands

```bash
# tests (Windows side)
python -m pytest tests/extension -q

# engineering run (WSL; nothing else heavy running)
MSYS_NO_PATHCONV=1 wsl -d Ubuntu-22.04 --cd "/mnt/c/Users/huzai/Downloads/Fast/Advance AI/Phase 3 and 4" -- bash scripts/wsl/run.sh scripts/extension/run_wdp_tranche.py --run WDP_D1_DEV --split dev --instances data/processed/instances_D1.jsonl --frame data/processed/frame_d1.jsonl --exec-dir data/raw/executions_gemma4_26b --cand-dir data/interim/candidates_gemma4_26b

python scripts/extension/freeze_wdp.py

# ONLY after the authors approve the freeze commit (rule 0.8): the four retrospective evaluation runs, same form,
# with WDP_D1_TEST (--split test), WDP_CONF_F1, WDP_CONF_F2, WDP_CONF_CTRL and the paths of section 2.1; then
python scripts/extension/wdp_analysis.py --out results/extension/wdp/wdp_analysis.json
python scripts/extension/wdp_report.py
```

The exact WSL quoting is the one recorded for the confirmation probes (D-145 and
`results/extension/confirm_logs/probes.log`); reuse it. Run pipeline git checks with
`GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=true` (D-144).

## 4. Order of work and critical path

| Step | Task | Depends on | Who | Wall-clock (estimate) | CPU / GPU / calls / disk | Earliest safe start |
|---|---|---|---|---|---|---|
| P1 | Audit replication A1–A5 (`CONFIRMATION_INDEPENDENT_AUDIT.md` §8); outputs under `results/extension/audit/`, scripts under `scripts/extension/audit/` | approved 2026-11-13 | Opus | 1–1.5 h | CPU, seconds; 0 calls; < 5 MB | now |
| P2 | Implement section 3.1; tests T1–T11; `WDP_D1_DEV`; T12, T13 | approved 2026-11-13, after the lead model's review of the version 2 amendments | Opus | 3–5 h, of which the dev run a few minutes | WSL, 12 JVMs; no GPU; 0 calls | after the amendments |
| P2a | Three read-only checks that P1 did not replicate, written to `results/extension/audit/A6_A8.md` with scripts under `scripts/extension/audit/`: **A6** ledger flags recomputed from each record's mutant list for the 834 confirmation ledger records (audit row 4); **A7** sha256 of the 15 sources in `data/extension/confirm/ALL/concat_manifest.json` (row 5); **A8** sealing chronology from `git log` and the run logs: labels commit before the first probe, ledger commit before the first vote call, label and ledger files unchanged since their sealing commits (row 18). Status only; a mismatch is reported, not fixed, and blocks P3 | P1 accepted | Opus | 20 min | CPU, seconds | with P2 |
| P3 | **Freeze:** decision entry D-147 (text in section 9), `freeze_wdp.py`, one commit holding the eight design documents, the audit scripts and outputs (including the adjudication and the authors' acceptance record), the code, the tests, `wdp_frozen.json` and the dev ledger. **Return to the authors for review (step P3b): the commit hash, the freeze manifest, the test results, the dev-run summary, the list of changed files, every deviation, and the status of A6–A8.** | P1 accepted, P2 green, P2a clean | Opus | 20 min | — | after P1 and P2 |
| P3b | **Authors review and approve the freeze commit.** On approval only: create `configs/extension/wdp_run_approval.json` (`{"freeze_commit": …, "approved_by": "authors", "date": …, "source": "<where the approval was given>"}`), add one line to D-147, commit | P3 | authors, then Opus | — | — | — |
| P3c | **Hardening and re-freeze** (section 11): driver checks, raw-ledger marker check, complete leave-one-project-out, fail-closed levels, tests, new manifest, a new local freeze commit on top of `3c59196` (which is preserved, never amended or rebased). Return the new hash and the review package of section 11.7 | authors' review of `3c59196`, 2026-11-13 | Opus | 1–2 h | CPU; WSL for T11, T13 | now |
| P4 | Retrospective evaluation runs `WDP_D1_TEST`, `WDP_CONF_F1`, `WDP_CONF_F2`, `WDP_CONF_CTRL`; commit the four ledgers **before** the analysis is run | **P3b on the P3c commit** (the authors' explicit approval of the reviewed re-freeze commit) | Opus | under 30 min (the first-order probes took 42 min for 834 tests with up to 80 variants; WDP has at most 3) | WSL CPU; no GPU; 0 calls; < 20 MB | after P3b |
| P5 | `wdp_analysis.py`, `wdp_report.py`; commit | P4 | Opus | 30 min | seconds | after P4 |
| P6 | Hand back to the lead model for interpretation: this brief, `wdp_report.md`, `wdp_analysis.json`, the four `run_meta.json`, the list of changed files, any deviation. Nothing else | P5 | Fable | 1 h | — | after P5 |
| P7a | `_v2` manuscript and deck: registered confirmation, independent audit, limitations, positioning (section 8) | P1 PASS | Opus | 6–9 h | — | **after P1; does not wait for WDP** |
| P7b | WDP subsection and slide in the `_v2` files | P6 | Opus | 1–2 h | — | after P6 |
| O1 | Jackknife intervals (audit A3) as an appendix table | P1 | Opus | 30 min | — | optional |
| O2 | A figure of the ladder (stacked bars by label and frame) | P5 | Opus | 45 min | — | optional |

Priorities and cut-off (rule 0.9): P7a has priority over everything after P3. **Default cut-off: if P6 is not
complete by 2026-11-14 20:00 (+05:00), P7b is replaced by a short "designed, not run / not yet evaluated"
paragraph and WDP is listed as future work.** The authors may move the cut-off; Opus may not.

Local Gemma/Ollama time: none. Fable time: the review of the amendments (done with this version) and P6.

## 5. Acceptance criteria and quality checks

| Step | Accepted when |
|---|---|
| P1 | `results/extension/audit/P1_SUMMARY.md` begins `P1 RESULT: PASS`; **or** it begins `P1 RESULT: FAIL`, the failure is adjudicated in `results/extension/audit/P1_ADJUDICATION.md`, and the authors' written acceptance is recorded in `results/extension/audit/P1_AUTHOR_ACCEPTANCE.md`. Otherwise stop. (Actual outcome, 2026-11-13: the second case. The summary is never edited to read PASS.) |
| P2 | T1–T13 pass; on `WDP_D1_DEV`: engine exclusions ≤ those of `CFP_D1_DEV2` for the same instances plus 2; `X-THROW` compiled for every method whose identity overlay compiled; no record with a missing class or a missing `entered` where `x_throw` is not NA |
| P3 | `wdp_frozen.json` committed; `git status` clean; commit hash written into the decision log and returned to the authors; **no file under `results/extension/wdp/` other than `WDP_D1_DEV/`** |
| P3b | `wdp_run_approval.json` names the P3 commit and the approval's source |
| P4 | each ledger has one record per instance of its instances file; `run_meta.json` names the P3 commit; the frozen hashes still match after the runs |
| P5 | the report's population counts equal section 2.2; the registered rows (KUU, KUU + CD, 2-of-3) equal `confirm_report.md` to four decimals |

**Quality checks for reporting the ladder** (all must hold on each retrospective evaluation run; if they do, the
descriptive ladder is reported even when the primary criterion is NOT MET): P4 and P5 accepted; no stop condition
of section 6 fired; zero marker-consistency violations; ND for technical reasons (`excluded:*`, `x_throw_err`,
`x_throw_na`, `x_ret_err`, `no_x_ret`) at most 5% of instances.

## 6. Stop conditions (stop, write down what happened, ask the authors)

1. Any audit check of P1 fails.
2. Any frozen hash changes, or `test_freeze.py` fails, at any time.
3. On `WDP_D1_DEV`: more than 5% of instances excluded for `baseline_not_reproduced`; or `X-THROW` fails to compile
   for any method whose identity overlay compiled; or T12 or T13 fails; or T12 is vacuous.
4. The dev run suggests a change to the variant table, the screen, the level function or a certificate. That is a
   design decision: do not make it. Report the evidence.
5. In any retrospective evaluation run: a marker-consistency violation; or ND for technical reasons above 5%.
   (`throw_swallowed` and `swallow_risk` are not technical reasons and are not capped; they are reported.)
6. A retrospective evaluation run has to be restarted after it produced records.
7. Anything would require reading a label, a fixed version or a vote inside the engine.
8. Any attempt, by any path, to start a retrospective evaluation run before P3b.

## 7. Interpretation rules (fixed before the run)

| Outcome on CONF-votes | What may be written | What may not |
|---|---|---|
| **Criterion MET**, and no additional bug lost on PILOT-votes | "In an exploratory, retrospective evaluation, discarding failures for which no entry into the method under test was observed and which were throw-invariant removed x% more wrong tests than KUU with no additional bug lost on 21 (and 22) bugs with a bug-revealing test, at no model cost." Give TPR, TNR, bugs lost, the bound of §2.5 with its caveat | "validated", "safe", "guarantee", "confirms", "held-out", "unreachable", any comparison with published numbers from other samples |
| Criterion MET on CONF-votes, a bug lost on PILOT-votes | report both; the certificate is **not** recommended; the ladder is a descriptive result | selecting the favourable dataset |
| **NOT MET because a bug is lost** or `Math_59` is level U | "the refinement did not remove the certificate's bug loss"; no method; the ladder is reported if the quality checks hold | any redefinition of the level function, screen or variants after the fact |
| **NOT MET because ΔTNR's interval includes 0**, safety held | "no bug lost in this sample and no measurable benefit over KUU"; report the pre-filter share, the cost, and how many tests the conservative handling moved from U to ND | calling it an improvement; relaxing the conservative handling |
| Whatever the criterion, quality checks passed | the ladder (how the registered `decoupled` set splits into U, RI, WS and ND by reason, and where the PF tests sit), by frame and project | — |

Level U is always described as an operational observation: "no entry observed and throw-invariant". It is never
described as proof that the test cannot reach the method.

If level U accounts for most of the registered decoupled wrong tests, the paper says so plainly: the part of CFP
that survived confirmation is then largely an entry check obtainable with one extra execution per test. If it
accounts for few, the paper says that instead. Neither is to be softened.

Status labels for the paper:

| Result | Label |
|---|---|
| C1–C4, rule table, control, registered secondaries | confirmatory, registered (OSF kp79c) |
| `STAGE_B_PLAN.md` | designed before the confirmation outcomes; unregistered; not run |
| Audit §3–§6 analyses | exploratory |
| Everything from WDP | exploratory; retrospective; internally frozen before its run; not externally preregistered; designed after the outcomes |

## 8. Manuscript and deck (P7)

- Do not edit `paper/PHASE4_RESEARCH_PAPER.tex` or `paper/DEFENSE_DECK.pptx`. Build
  `paper/PHASE4_RESEARCH_PAPER_v2.tex` and `paper/DEFENSE_DECK_v2.pptx` as copies and edit only those.
- Order of content (authors' priorities): (1) the registered confirmation, printed as registered; (2) the
  independent audit's qualifiers (audit §7, all eleven); (3) limitations and threats; (4) positioning and the
  claims to abandon; (5) WDP, **only after P6**, and then with the full status sentence.
- If the primary criterion is NOT MET and the quality checks passed, the `_v2` paper still contains the
  descriptive ladder (one table, one paragraph) and states the criterion's outcome in the same paragraph.
- Every new number enters through the repository's numbers map (`scripts/paper/build_numbers.py`) from
  `confirm_analysis_CFP_CONF_ALL.json`, the two secondary JSON files, `results/extension/audit/*` and
  `wdp_analysis.json`; no hand-typed figure.
- Follow `PUBLICATION_STRATEGY.md` for the text and `DEFENCE_DECK_RESTRUCTURE.md` for the slides, including their
  lists of statements that must not appear.

## 9. Decision entry to add at P3 (append to `docs/tracking/DECISIONS.md`; fill the bracketed values)

> **D-147 | 2026-11-[dd] | Whole-method dependence probes (WDP): exploratory extension, protocol frozen
> internally before its retrospective evaluation runs; not externally preregistered.** *Basis:* independent audit
> of the confirmation (`CONFIRMATION_INDEPENDENT_AUDIT.md`). *Replication P1 (A1–A5):*
> `results/extension/audit/P1_SUMMARY.md` reported FAIL on one tolerance check (two per-frame C1 bootstrap upper
> limits differed in the second decimal from the registered files); adjudicated in `P1_ADJUDICATION.md` as
> bootstrap seed variation (the registered-seed intervals reproduce exactly in independent code) and an overstated
> sentence in the audit, since corrected; all 834 labels recomputed from raw runs; **accepted as passed by the
> authors on 2026-11-13 for the scope A1–A5** (`P1_AUTHOR_ACCEPTANCE.md`); the summary is left as written.
> *Further read-only checks A6–A8* (ledger flags, concatenation hashes, sealing chronology): [result].
> *Audit findings:* registered results reproduce; C1 not replicated; C2 supported pooled and carried by F2 and two projects; both
> bugs ever lost by the decoupling certificate are operator gaps. *Authors' conditional approval, 2026-11-13:*
> audit replication; amendment of level U before implementation; implementation, engineering run and freeze; no
> retrospective evaluation run before the authors approve the freeze commit; `_v2` manuscript and deck; no
> external registration, no Stage B, no model call. *Design:* `TECHNICAL_METHOD_SPEC.md` version 2 and
> `OPUS_EXECUTION_BRIEF.md` version 2 (hashes in `configs/extension/wdp_frozen.json`): three whole-body
> replacements of the method under test, the throw variant writing an entry marker; a static screen for constructs
> that intercept a `Throwable` or `Error`; levels FS / WS / RI / U / ND with reason codes; level U an operational
> observation (no entry observed, throw-invariant), never assigned when entry was recorded or the screen fires;
> certificate CD-U; primary outcome ΔTNR of KUU + CD-U over KUU on the 561 confirmation tests with votes, safety
> constraint no additional bug lost, criterion as written in the brief §2.4; bug-level bootstrap, seed 20261113.
> *Status:* exploratory; designed after the pilot's and the confirmation's labels and probe outcomes were known; no
> model call; no change to any registered result or frozen file. *External registration:* none, by the authors'
> instruction; none to be made before 2026-11-16, and none afterwards without their approval. *Engineering run:*
> `WDP_D1_DEV` ([n] instances, [n] excluded; marker consistency [n] violations of [n] surfaced throws), used for
> debugging only. *Frozen at commit:* [hash], returned to the authors; retrospective evaluation runs await their
> approval. Stage B not run (`STAGE_B_FINAL_PROTOCOL.md`).

## 10. Amendments in version 2 and what the conditional approval covers

| # | Authors' condition (2026-11-13) | Where it is implemented |
|---|---|---|
| 1 | Proceed with P1; outputs outside frozen paths | section 4, P1 |
| 2 | Resolve the `catch (Throwable)` / `catch (Error)` ambiguity in level U: conservative handling with tests, **and** U defined as an operational observation | spec §2.1 (entry marker), §2.3 (`entered`, `swallow_risk`), §2.4 rows 8–10, §5 invariants 7–9, §6; this brief §3.1, tests T4, T5, T7, T11, T12, stop conditions 3 and 5, section 7 |
| 3 | "held-out runs" → "retrospective evaluation runs" | throughout; rule 0.7 bans the old term for WDP |
| 4 | Opus may implement, run the dev split, pass tests, freeze, and return the commit hash | P2, P3 |
| 5 | No `D1_TEST` or confirmation tranche run before the freeze is reviewed and approved | rule 0.8, P3b, the driver's refusal (section 3.1), stop condition 8 |
| 6 | `_v2` copies; confirmation, audit and limitations first; WDP only after run and interpretation review; ladder retained if quality checks pass | sections 5 and 8, P7a, P7b |
| 7 | No change to OSF kp79c, no external registration, no Stage B, no model call | rules 0.2, 0.3 |
| — | Manuscript has priority if WDP threatens the deadline; criteria never weakened | rules 0.6, 0.9; cut-off in section 4 |
| — | Second message, 2026-11-13: P1 accepted as passed after adjudication, scope A1–A5; continue in the **existing** Opus session, no second session and no concurrent writer; P3 only if all implementation tests and dev-run criteria pass; at P3b return hash, manifest, tests, dev summary, changed files, deviations and the status of the three audit items P1 did not replicate; evaluation runs still blocked | section 5 (P1 row), steps P2a and P3, section 9 |

## 11. Version 3 addendum: hardening after the authors' review of `3c59196` (authoritative where it differs)

The authors accepted the engineering work and A6–A8, asked that `3c59196` be preserved as the original
implementation snapshot, and required the items below **before** they are asked for final P4 approval.
Nothing here changes an intervention variant, the classification of a variant's outcome, the screen, a certificate,
the primary outcome, the safety constraint, the criterion or an acceptance threshold.

### 11.1 Driver `scripts/extension/run_wdp_tranche.py`

| # | Requirement |
|---|---|
| 1 | Run names are exactly five. **Without** `configs/extension/wdp_run_approval.json`: only `WDP_D1_DEV` (with `--split dev`) may run. **With** it: only `WDP_D1_TEST`, `WDP_CONF_F1`, `WDP_CONF_F2`, `WDP_CONF_CTRL` may run; `WDP_D1_DEV` and every other name are refused |
| 2 | Each run name is bound to its inputs (section 2.1): the instances file, frame, executions and candidates directories and, for `WDP_D1_TEST`, `--split test`. Any other combination is refused |
| 3 | The approval file must be a JSON object whose `freeze_commit` is a full 40-character hexadecimal commit id |
| 4 | That commit must exist (`git cat-file -e <id>^{commit}`) and must be an ancestor of, or equal to, the current HEAD (`git merge-base --is-ancestor <id> HEAD`) |
| 5 | The frozen-file check is run automatically: the same function that `freeze_wdp.py --check` uses (one implementation, imported, not copied) must report every hashed file and parameter equal to `configs/extension/wdp_frozen.json` |
| 6 | `configs/extension/wdp_frozen.json` in the working tree must be byte-identical (after CRLF→LF) to `git show <id>:configs/extension/wdp_frozen.json`, so that the approval refers to this manifest and no other |
| 7 | Any failure of 3 to 6, an unreadable approval file, or git being unavailable is a refusal with a message naming the failed check; the driver exits non-zero **before** reading an instance or creating a directory. It fails closed |
| 8 | `run_meta.json` records, separately: `approved_freeze_commit` (from the approval file), `execution_commit` (HEAD when the run starts), `frozen_check` ("passed", with the manifest's sha256), and `worktree_dirty_paths` (the output of `git status --porcelain`, expected empty apart from the run's own output directory) |

The driver never creates, edits or deletes the approval file. Only the authors' explicit approval of the reviewed
re-freeze commit allows that file to be created (step P3b).

### 11.2 Marker consistency over every raw ledger record

`wdp_analysis.py` gains a first step that runs before any label or vote is read:

1. For each of the four retrospective ledgers, load **every** record (PF, TF, AMB and any other).
2. Completeness: the set of record ids must equal the set of instance ids of that run's instances file, one record
   each.
3. Marker consistency: zero records with `surfaced` true and `entered` not true.
4. If 2 or 3 fails: write `results/extension/wdp/wdp_analysis_ABORTED.json` (which check failed, the offending
   ids, the run names), print the same, exit non-zero, and write **no** `wdp_analysis.json`. This is stop
   condition 5; it is reported to the authors and nothing is repaired.

The quality-check block reports these counts over all raw records, by run, beside the counts over scored rows.
The same check is exposed as a function so that it can be run on a single ledger (it is run on `WDP_D1_DEV` at
P3c and reported).

### 11.3 Leave-one-project-out, completed

Secondary outcome 9 is computed in full. For each project of CONF-all whose removal leaves at least one PF and
one TF test, report on the remaining tests: P(U | TF) − P(U | PF) and P(U ∪ RI | TF) − P(U ∪ RI | PF) as point
estimates with the four counts behind each (as the registered leave-one-project-out reports its contrasts), beside
the ΔTNR and additional bugs lost already computed on CONF-votes. No interval and no test: descriptive.

### 11.4 Level function

Implement spec version 3 §2.3 (record validity) and §2.4 (rows 2, 2b, 10, 11). `level()` never raises. Malformed
or inconsistent records are ND with a `malformed:` code, are counted as technical ND (they count toward the 5%
cap of section 5), and are listed by id in the diagnostics. The analysis must also not crash on a missing WDP
record inside `level()`; completeness is enforced by 11.2 instead.

### 11.5 Files that may and may not change at P3c

| May change | Must not change (if you believe one must, stop and report) |
|---|---|
| `src/triage_dep/levels.py`; `scripts/extension/run_wdp_tranche.py`, `wdp_analysis.py`, `wdp_report.py`, `freeze_wdp.py`; `tests/extension/test_wdp.py`, `test_wdp_integration.py`; `configs/extension/wdp_frozen.json`; `docs/tracking/DECISIONS.md` (one new entry, D-148) | `src/triage_dep/wdp.py`, `interventions.py`, `screen.py` (the engine: the development ledger was produced by them and stays valid only if they are byte-identical); `results/extension/wdp/WDP_D1_DEV/ledger.jsonl` and `run_meta.json`; everything in rule 0.1; `tests/extension/test_cfp.py` |

`TECHNICAL_METHOD_SPEC.md`, `CONFIRMATION_INDEPENDENT_AUDIT.md` and this brief were amended by the lead model before
P3c started; commit them as they are, and hash the specification and the brief as they are.

### 11.6 Tests and checks to add, and to re-run

| ID | Test |
|---|---|
| T4, T5 (revised) | the enumeration now includes a missing `entered`, a missing `swallow_risk`, an unknown class, a missing record and `surfaced` true with `entered` false; `level()` never raises; every malformed input is ND with a `malformed:` code; U only for row 10's exact conditions |
| T14 | driver, in a temporary git repository or with git patched: refuses when the approval file is absent (four names), is not JSON, lacks a 40-hex id, names a commit that does not exist, names a commit that is not an ancestor of HEAD, when a frozen hash differs, when the manifest differs from the approved commit's manifest, when a run name is not one of the four, when `WDP_D1_DEV` is requested after approval, and when a run name is paired with another run's inputs; accepts the correct case up to the point where it would read instances (stop the test there); `run_meta` carries both commits |
| T15 | analysis aborts, writes the ABORTED file and no result, on a synthetic ledger whose only violation is in an AMB record; and on a ledger with a missing or duplicated instance |
| T16 | leave-one-project-out for U and U ∪ RI on a synthetic fixture with known counts |
| T17 | the real approval file does not exist (kept from version 2) |
| re-run | every test of section 3.2; T11 and T13 in WSL; T12 over **all** 118 raw records of `WDP_D1_DEV`; `freeze_wdp.py --check`; `tests/extension/test_freeze.py` |

A demonstration to include in the report: the real driver invoked once for each of the four evaluation run names
**without** an approval file, showing the refusal message and that `results/extension/wdp/` still holds only
`WDP_D1_DEV/`.

### 11.7 Re-freeze and what to return

1. Engine files unchanged: show that `git diff 3c59196 --stat -- src/triage_dep/wdp.py src/triage_dep/interventions.py
   src/triage_dep/screen.py results/extension/wdp/WDP_D1_DEV/ledger.jsonl` is empty.
2. Append decision entry **D-148** (text below), run `freeze_wdp.py`, make **one new local commit** on top of
   `3c59196`. No amend, no rebase, no push, no AI attribution. `git status --short` clean afterwards.
3. Return: the new commit hash; the full new manifest; test results by id with counts; the quality-check outputs
   (raw-ledger marker check on the development ledger, the four refusal messages, freeze check, engine-unchanged
   diff); every deviation; the complete changed-file list (`git show --name-status`); and the sha256 and git blob
   ids of `wdp.py`, `levels.py`, `interventions.py` and `screen.py` at the new commit, so the authors can inspect
   those four source files independently.

> **D-148 | 2026-11-[dd] | WDP hardened and re-frozen after the authors' review of freeze commit `3c59196`; no
> retrospective evaluation run exists.** *Review decision (authors, 2026-11-13):* engineering work and audit
> checks A6–A8 accepted; `3c59196` preserved as the original implementation snapshot; final approval of the
> evaluation runs withheld until the following are done. *Done:* the driver now verifies, before any retrospective
> evaluation run, that the approval file names a full commit id that exists and is an ancestor of HEAD, that every
> frozen hash matches, and that the manifest equals the approved commit's manifest; it accepts only the four
> evaluation run names with their own inputs after approval and only the development run before it; it records the
> approved freeze commit and the execution commit separately. The analysis checks marker consistency and
> completeness over every raw ledger record, AMB included, before reading a label, and stops without a result on a
> violation. Leave-one-project-out is computed for the level-U and U-or-RI contrasts. The level function follows
> specification version 3: malformed or inconsistent records are ND with a `malformed:` code, level U is assigned
> by positive match only, and the function never raises. *Unchanged:* intervention variants, outcome
> classification, screen, certificates, primary outcome, safety constraint, criterion, thresholds; the engine files
> are byte-identical to `3c59196` and the development ledger was not re-run ([n] records, [n] malformed, [n] marker
> violations over all raw records). *Tests:* [counts]. *Status:* exploratory; internally frozen; not externally
> preregistered. The approval file does not exist; `WDP_D1_TEST` and the `WDP_CONF_*` runs remain blocked until the
> authors explicitly approve this commit.

### 11.8 Manuscript and deck `_v2` (P7a): start after the P3c report, in the same session

Authorised by the authors on 2026-11-13. One writer: do P3c first, hand back its report, then P7a. If a P4
instruction arrives while P7a is in progress, finish the current file edit, do P4 and P5, then return to P7a.

- Work **only** on copies: `paper/PHASE4_RESEARCH_PAPER_v2.tex` and `paper/DEFENSE_DECK_v2.pptx` (and any `_v2`
  generated numbers, tables or figures they need). `paper/PHASE4_RESEARCH_PAPER.tex`, `paper/DEFENSE_DECK.pptx`,
  `paper/references.bib` and every existing generated file stay byte-identical; new references go into a `_v2`
  bibliography copy.
- Content, in priority order: the registered confirmation printed as registered; the independent audit's
  qualifiers (`CONFIRMATION_INDEPENDENT_AUDIT.md` §7 and §9, all twelve corrections, and rows 24 to 27); the
  literature review and positioning (`UPDATED_NOVELTY_AND_CONTRIBUTION_ASSESSMENT.md` §1–§4 and §7, with
  read-depth honesty: cite only what the assessment marks as read, and mark preprints as preprints); limitations
  and threats (`PUBLICATION_STRATEGY.md` §8); the claims to abandon (assessment §3; strategy §10).
- **No WDP experimental result** in either file until P6 is complete. Until then WDP appears only as a designed
  extension under the full status sentence. If the cut-off of section 4 passes, it is presented as future work.
- Every number comes through the numbers map from committed result files; none is typed by hand. If the build
  tooling for the numbers map or LaTeX is unavailable, say so and stop that part; do not hand-type as a workaround.
- Commit `_v2` work in its own commits, separate from any freeze or run commit.

## 12. Version 4 addendum: level-function defects found in the authors' review of `1b8e667` (authoritative where it differs)

**The authors did not approve `1b8e667`.** They found two defects in `src/triage_dep/levels.py`. Both reproduce, and
six further malformed inputs of the same kind receive level U or FS (table below; reproduced by the lead model on
the frozen code). `TECHNICAL_METHOD_SPEC.md` is amended to version 4 (sections 2.3, 2.4, 5 item 4, 12): validity
first, a strict record schema, a three-state first-order observable, and tests that assert necessary conditions
on raw inputs. This step is **P3d**. `3c59196` and `1b8e667` are preserved; nothing is amended or rebased.

| Case (frozen code at `1b8e667`) | Got | Must be |
|---|---|---|
| X-THROW SAME, `entered` false, an **uncompiled** X-RET carrying class `BOGUS` (authors' case) | U | ND `malformed:unknown_class` |
| no WDP record, first-order coupled (authors' case) | FS | ND `excluded:no_record` |
| `entered` missing, first-order coupled (authors' case) | FS | ND `malformed:entered_missing` |
| an uncompiled X-RET carrying class SHIFT | U | ND `malformed:uncompiled_with_class` |
| `compiled` given as the string `"false"`, class SHIFT | WS | ND `malformed:bad_shape` |
| two X-THROW variants, the second SHIFT | U | ND `malformed:variant_ids` |
| a variant with id `ZZZ` | U | ND `malformed:variant_ids` (or `uncompiled_with_class` if rule 3 applies first) |
| first-order summary missing | U | ND `first_order_unusable` |
| first-order summary excluded | U | ND `first_order_unusable` |
| first-order `coupled` is the string `"False"` | FS | ND `first_order_unusable` |
| `surfaced` is the string `"true"`, `entered` false | U | ND `malformed:surfaced_missing` |
| a compiled X-RET with a null class | ND `malformed:unclassifiable` | ND `malformed:compiled_not_run` |

### 12.1 What changes, and only this

| May change | Must not change (if you believe one must, stop and report) |
|---|---|
| `src/triage_dep/levels.py`; `tests/extension/test_wdp.py` (and `test_wdp_integration.py` only if a level code it asserts was renamed); `configs/extension/wdp_frozen.json`; `docs/tracking/DECISIONS.md` (one new entry, D-149) | `src/triage_dep/wdp.py`, `interventions.py`, `screen.py`; `scripts/extension/run_wdp_tranche.py`, `freeze_wdp.py`; the development ledger; every `_v2` paper and deck file; everything in rule 0.1 |

`scripts/extension/wdp_analysis.py` and `wdp_report.py` may change **only** as far as the new reason codes require:
`first_order_unusable` and every `malformed:*` code count as technical ND and are listed by id in the diagnostics.
If they need no change, do not touch them. The specification and this brief were amended by the lead model before
P3d started; hash them as they are.

### 12.2 `levels.py`

Implement spec version 4 §2.3 (the three-state `fo`, the nine validity rules in their order, with their scope) and
§2.4 (rows 1 to 14 in that order). Requirements beyond the table:

1. `level()` never raises on any input, including non-dict records, non-list `variants`, non-dict variants and
   non-dict first-order summaries.
2. Every comparison that decides a level is exact (`is True`, `is False`, `==` on a known string); no truthiness
   test on a field read from a record.
3. The X-RET classes used by the level rows come only from variants that passed validity; uncompiled variants
   never contribute a class.
4. `cd_u` and `cd_ur` are unchanged.

### 12.3 Tests (in `tests/extension/test_wdp.py`)

| ID | Test |
|---|---|
| T18 | one regression test per row of the table above (twelve cases), asserting the "must be" level and code |
| T19 | **necessary conditions on raw inputs**, written without calling any helper of `levels.py` other than `level()` and without an oracle of the table: for every generated input, if the level is U then all conditions listed for U in spec §2.4 hold on the raw record and raw first-order summary; likewise RI, WS and FS. Inputs: (a) an enumeration over record present / absent / non-dict; `excluded` null / string / empty string / non-string; X-THROW absent / once / twice, compiled true / false / `"false"` / null, class each of SAME, SHIFT, FLIP, ERR, null, `BOGUS`; zero to two further variants with ids from `X-RET-1`, `X-RET-2`, `ZZZ`, a repeated id, each with the same compiled and class ranges; `entered` and `surfaced` each true / false / null / `"true"`; `swallow_risk` true / false / null; first-order summary absent / excluded / `coupled` true / false / null / `"False"` / non-dict. (b) a seeded random fuzz (seed 20261114, at least 200,000 cases) of arbitrary JSON-like records and summaries, including nested junk |
| T20 | `level()` never raises over (a) and (b), and always returns a level in {FS, ND, WS, RI, U} with a reason code if and only if the level is ND |
| T21 | development ledger regression: with `results/extension/probes/CFP_D1_DEV2/ledger.jsonl` as first-order input, the 118 records of `WDP_D1_DEV` give exactly FS 83, U 16, WS 14, RI 5, ND 0, and the per-instance levels are identical to those computed by the `1b8e667` version of `levels.py` (load that version from `git show 1b8e667:src/triage_dep/levels.py` into a temporary module for the comparison). The fix must not move any valid record |
| T4, T5 | revise to the new row order and codes; keep them, but T19 is the test that carries the safety property |
| re-run | the whole `tests/extension` directory; `freeze_wdp.py --check`; `tests/extension/test_freeze.py`; the raw-ledger check on the development ledger. T11 and T13 in WSL need not be re-run if `wdp.py`, `interventions.py` and `screen.py` are byte-identical to `1b8e667`; show that diff |

### 12.4 Re-freeze and what to return

1. Show `git diff 1b8e667 --stat -- src/triage_dep/wdp.py src/triage_dep/interventions.py src/triage_dep/screen.py
   scripts/extension/run_wdp_tranche.py scripts/extension/freeze_wdp.py results/extension/wdp/WDP_D1_DEV/` is empty,
   and that no `_v2` paper or deck file and no original paper file changed.
2. Append decision entry **D-149** (text below), run `freeze_wdp.py --refreeze D-149`, make **one new local commit**.
   No amend, no rebase, no push, no AI attribution. `git status --short` clean afterwards.
3. Return, for the authors' review: the new commit hash; the full new manifest; the complete `levels.py` as
   committed, with its sha256 and git blob id; the regression tests T18 to T21 (names and what each asserts) with
   their results; the counts for the whole test directory; every deviation; and the complete changed-file list.

> **D-149 | 2026-11-[dd] | WDP level function corrected and re-frozen after the authors' review of `1b8e667`,
> which they did not approve; no retrospective evaluation run exists.** *Defects found by the authors in
> `src/triage_dep/levels.py` at `1b8e667`:* (1) an uncompiled variant carrying an unknown class escaped validation
> and the record could receive level U; (2) first-order coupling was checked before record validity, so a missing
> or malformed record could receive level FS. *Further cases of the same kind found on reproduction:* a class on an
> uncompiled variant, a duplicate or unexpected variant id, a `compiled` or `surfaced` field of the wrong type, and
> a missing or excluded first-order summary read as "no edit changed the failure". *Correction (specification
> version 4):* validity is checked first; nine validity rules over every variant; the first-order observable has
> three states and an unusable one is ND; levels U, RI, WS and FS are assigned only from a present, valid record;
> tests assert necessary conditions on raw inputs over an enumeration and a seeded fuzz, with one regression test
> per defect. *Unchanged:* intervention variants, outcome classification, screen, certificates, primary outcome,
> safety constraint, criterion, thresholds, engine files, driver; the development ledger's 118 levels are identical
> before and after ([counts]). *Tests:* [counts]. *Status:* exploratory; internally frozen; not externally
> preregistered. `3c59196` and `1b8e667` are preserved as snapshots. The approval file does not exist;
> `WDP_D1_TEST` and the `WDP_CONF_*` runs remain blocked until the authors explicitly approve this commit.

### 12.5 Paper and deck while this is open

The `_v2` WDP paragraph and deck slide 16 stay as unevaluated-extension placeholders. If the corrected
implementation has not passed the authors' review by the cut-off of section 4 (2026-11-14 20:00 +05:00), WDP is
presented as future work. Submission tasks that remain the authors': the AI-use declaration (it must cover both
Claude Opus 5.5 and Claude Fable 5.2, worded to the target venue's policy), the eight TODO placeholders, and a
visual check of the deck.
