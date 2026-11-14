# Proposed architecture: probe-backed triage

The primary pipeline (`CURRENT_ARCHITECTURE.md`) is unchanged. The extension adds one evidence path between
execution and the decision. Implemented components are marked ✔; designed-only components are marked ○.

## 1. Components

```
                       PREDICTION-TIME SIDE                                   │  OFFLINE SIDE
                                                                              │
  failing test t ──┐                                                          │
  buggy checkout P ├─► ✔ Mutant generator ──► M(m)                            │
  focal method m ──┘     src/triage_ext/mutate.py                             │
                              │                                               │
                              ▼                                               │
                     ✔ Probe engine  (WSL, sandboxed scratch dir)             │
                       src/triage_ext/probe.py                                │
                       compile overlays · run t per overlay · run siblings    │
                              │                                               │
                              ▼                                               │
                     ✔ Evidence ledger   results/extension/probes/<run>/      │   label store
                       src/triage_ext/ledger.py   (one JSON record per t)     │   (execution on the
                              │                                               │    fixed version)
              ┌───────────────┼──────────────────┐                            │        │
              ▼               ▼                  ▼                            │        │
   ✔ Certificate rules   ○ Probe report     ○ Probe-selecting agent           │        │
     policy.py             in the judge's     (chooses region, operators,     │        │
     CK · CD · CK+CD       evidence package   depth under a budget)           │        │
              │               │                  │                            │        │
              └───────┬───────┴──────────────────┘                            │        │
                      ▼                                                       │        ▼
              base rule b(t): keep-all · KUU · judge  ──► decision d(t) ──────┼──► ✔ analysis
              (committed decisions, unchanged)                                │    scripts/extension/ext1_…, ext2_…
```

| Component | Responsibility | Input | Output | Failure behaviour | Trust boundary |
|---|---|---|---|---|---|
| Mutant generator ✔ | Enumerate first-order edits of the region | method text, focal id | ordered mutants with stable ids | returns fewer or no mutants; never raises on odd syntax | pure text; reads nothing else |
| Probe engine ✔ | Compile each mutant into an overlay; run the failing test and, for flips, sibling tests | buggy checkout (3 whitelisted metadata keys), test source, stored buggy-side runs | per-mutant outcome classes | excludes the instance (4 named reasons); a timeout or harness error is class ERR | may execute generated code; confined to the WSL work directory; cannot open the fixed checkout or labels |
| Evidence ledger ✔ | Turn outcomes into counts and two flags | per-mutant classes | `summary` (+ focal-only summary) | undefined flags are false, never guessed | data only |
| Certificate rules ✔ | Override a base rule only on a certificate | base label, summary | keep / discard | no usable ledger → base label | pure function |
| Probe report ○ | Render the ledger as evidence items a judge can cite | ledger record | text section `[C1..]` | omitted when excluded | passes the existing leakage guard |
| Probe-selecting agent ○ | Spend a probe budget adaptively | failure, source, ledger so far | next probe | falls back to the fixed schedule | LLM output is a *choice of probe*, never a verdict about evidence |
| Analysis ✔ | Join labels, bootstrap by bug | ledger, label store, committed decisions | JSON results | — | the only component that reads labels |

## 2. Sequence for one failing test

```
generator/CI      probe engine           JVM (fresh per run)         ledger          policy
     │  t, m, P       │                         │                      │               │
     ├───────────────►│ locate m in C           │                      │               │
     │                │ compile identity ──────►│                      │               │
     │                │ compile ≤80 overlays ──►│   (parallel)         │               │
     │                │ run t on identity ─────►│ φ₀                   │               │
     │                │ check φ₀ = stored       │                      │               │
     │                │ run t on each overlay ─►│ φ_p (re-run a pass)  │               │
     │                │ for flips: siblings ───►│ pass / fail          │               │
     │                │ classes ───────────────────────────────────────►│ summary E(t)  │
     │                │                         │                      ├──────────────►│ rule(b(t), E(t))
     │◄───────────────────────────────────────────────────────────────────────────────┤ keep / discard
```

## 3. Interfaces

**Ledger record** (`results/extension/probes/<run>/ledger.jsonl`, one line per failing test):

```json
{
  "instance_id": "4079939b669bba8f",
  "focal_id": "Chart_18::org.jfree.data.DefaultKeyedValues::removeValue(int)",
  "method": "testRemoveValue_LastIndex_NoRebuild",
  "n_generated": 9, "n_generated_callee": 41, "n_sampled": 50, "n_compiled": 44,
  "source_level": null,
  "baseline": {"outcome": "assertion_failure", "exception": "java.lang.AssertionError",
               "failing_test_line": 41, "message_digest": "…"},
  "mutants": [
    {"mid": "ROR:113:a1b2c3", "tier": 0, "region": "<focal>", "operator": "ROR", "line": 4,
     "original": "<", "replacement": "<=", "class": "FLIP", "outcome": "pass",
     "siblings_run": 11, "siblings_failed": 0, "rc": true, "rc_vacuous": false}
  ],
  "excluded": null,
  "summary": {"n_compiled": 44, "n_flip": 1, "n_shift": 12, "n_same": 31, "n_err": 0, "n_rcf": 1,
              "flip": true, "rcf": true, "flip_without_rcf": false, "coupled": true, "decoupled": false,
              "flip_fraction": 0.023, "coupled_fraction": 0.295, "excluded": null},
  "summary_focal_only": {"…": "same fields over tier-0 mutants"},
  "n_siblings_available": 11, "seconds": 3.1
}
```
(The values above illustrate the schema; they are not a result.)

**Run metadata** (`run_meta.json`): decision ids, commit, split, operator list, cap, timeouts, workers, callee depth.

**Policy call:** `policy.RULES[name](base_label, summary) -> "PROGRAM_FAULT" | "TEST_FAULT"`.

**Probe report (designed, ○).** Rendered deterministically from the ledger, at most six lines, each with an id the
judge must cite, placed after the failure section:

```
[C1] 44 single edits of the method under test and its helpers were compiled and the failing test re-run on each.
[C2] 1 edit makes the test pass: line 4, `index < size` -> `index <= size`. 11 of 11 other tests of this method still pass.
[C3] 12 edits change the failure (different value or exception); 31 leave it identical.
```
The report states observations only. It never says which side is at fault.

## 4. Resource and safety limits

| Limit | Value | Where |
|---|---|---|
| Mutants per focal method | 80 | `mutate.MAX_MUTANTS` |
| Callee depth | 2 | `probe.CALLEE_DEPTH` |
| Wall clock per mutant run | 10 s (baseline run 30 s) | `probe.PROBE_TIMEOUT_S` |
| Sibling tests per flip | 30 | `probe.MAX_SIBLINGS` |
| Parallel JVMs | 12 | `PROBE_WORKERS` |
| JVM heap | 1 GB, the study's flags | `triage.execution.JVM_FLAGS` |
| Writes | scratch directory under the WSL work dir, removed per focal method | `probe.SCRATCH` |

The engine never edits the test, never writes into a checkout, and has no loop without a fixed bound.

## 5. What changes for the baselines

Nothing. KUU, KUU-NG, both cascades, the judges and the trivial baselines are read from committed decisions. The
certificate rules wrap them; removing the wrapper returns the published numbers.
