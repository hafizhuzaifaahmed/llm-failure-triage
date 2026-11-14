# Current architecture and data flow (as implemented at `5138443`)

Reconstructed from code, not from the slides. File names are relative to the repository root.

## 1. Pipeline

```
 Defects4J 3.0.1 (WSL)                         Windows side (Python 3.14, Ollama 0.40.13)
 ─────────────────────                         ─────────────────────────────────────────
 frame.py / build_frame.py                     generation.py / generate_tests.py
   312 focal methods → cap 25/project            G (gemma4:26b) × 3 generations per focal method,
   → 234 methods, dev/test split                 prompt sees the BUGGY context
          │                                                │
          ▼                                                ▼
 execution.py / run_execution.py  ◄──────── data/interim/candidates_gemma4_26b/<id>.json
   checkout B and F once per bug                 {package, class_name, source, generation}
   prune non-compiling @Test methods (≤3 passes)
   each surviving method alone in its own class copy
   3 runs on B, 3 runs on F, fresh JVM, 30 s timeout
          │
          ▼
 data/raw/executions_gemma4_26b/<id>.json   (compile_b/f, runs_b, runs_f, source_class)
          │
          ├──► labeling.py ──► data/ground_truth_store/labels_D1.jsonl      ◄── GROUND-TRUTH CHANNEL
          │      PF / TF / AMB / excluded                                        (never read by a judge module)
          │
          └──► dataset.py ──► data/processed/instances_D1.jsonl
                 failure view built from runs_b[0] only:
                 exception class, message, expected/actual, failing test line, frames
                          │
                          ▼
                 context_builder.py  (judge_view whitelist → evidence package with ids
                                      [T..] [F1..] [Sig..] [Doc..] [Spec..]; S0 ⊂ S1 ⊂ S2)
                          │
                 leakage guard (data/leakage_guard/guard_D*.jsonl): bug ids, fixed-only lines,
                 focal-body lines, paths → abort the call on a match
                          │
                          ▼
                 arms.py + runner.py + ollama.py / frontier.py
                   DA, KA, R0 (no call) · J1 (1 call) · SC (5) · SC-T (k_T) · DEB (5 calls)
                          │
                          ▼
                 results/runs_local/<RUN>/decisions.jsonl   (label_raw, confidence, cited ids, cost)
                          │
                          ▼
                 analysis.py / metrics.py / stats.py  ──► results/heldout/analysis_final/…
                 (labels join here, bug-level cluster bootstrap, Holm)
                          │
                          ▼
                 scripts/paper/build_numbers.py ──► docs/paper/NUMBERS_MAP.csv ──► paper/generated/numbers.tex
```

## 2. What each method observes, computes and costs

| Method | Observes | Computes | Output | Calls per failure | Where |
|---|---|---|---|---|---|
| DA / KA | nothing | constant | TF / PF | 0 | `arms.py` |
| R0 | failure type, deepest project frame | PF iff not an assertion failure and deepest project frame is in main code | label | 0 | `arms.py` |
| J1 | evidence package at level s | one neutral judgement | label, confidence, cited ids | 1 | `arms.py` |
| SC | same | majority of 5 samples, tie → TF; PF vote share kept as score | label, score | 5 | `arms.py` |
| SC-T | same | majority of k_T = 5 samples (token-matched to DEB on dev) | label | 5 | `arms.py` |
| DEB | same | two advocates, one rebuttal round, adjudicator | label, confidence | 5 | `arms.py`, paper Alg. 1 |
| Thinking J1 | same package | one call, thinking on, 16,384 context, 8,192 output cap | label | 1 (≈70 s) | `scripts/local/revision_runs.py` |
| KUU | J1 votes of M1, M2, M3 | discard iff all three valid votes are TF; invalid vote keeps | label | 3 (8.0 GPU-s on D2) | `scripts/analysis/kuu_analysis.py`, `revision_common.unanimous` |
| KUU-NG | J1 votes of M1, M3, NG | same rule, no generator-family judge | label | 3 | `kuung_analysis.py` |
| Cascade | KUU votes, then Sonnet DEB on any disagreement | unanimous votes decide; else frontier label; invalid keeps | label | 3 + 5 on ≈50% | `cascade.py` |
| Fully local cascade | KUU votes, then thinking M1 J1 | as cascade with a local Tier 2 | label | 3 + 1 on ≈50% | `revision_local_cascade.py` |
| k-of-n, stacker, risk threshold | logged votes and confidences | post hoc rules | label / score | 0 new | `revision_k_of_n.py`, `revision_learned.py`, `revision_risk.py` |

**Every method above reads the same static evidence package.** None executes anything at decision time. The only
execution evidence a judge ever sees is the single failing run on the buggy version (`runs_b[0]`).

## 3. Where a bug-revealing test can be lost

| Stage | Loss mechanism | Who has authority | Measured? |
|---|---|---|---|
| Generation | the generator, shown buggy code, writes a test that asserts the buggy behaviour (misguided: 102 of 2,909) | generator | yes (`dataset_summary_D1.json`) |
| Compile pruning | a bug-revealing method that does not compile on one version is NC (518) | harness | counted, not analysed |
| Labelling | a test exposing a real fault the developer's patch does not touch fails on both versions and is labelled TF | label rule | audit only: both mismatches in the 71-item audit are of this kind |
| **Triage** | a judge says TF | **the judge / policy** | yes: the paper's main outcome |
| Repair or deletion after triage | a discarded test is rewritten to the observed value or dropped | repair stage | **not implemented, not measured** |

The study measures the fourth row only. What happens to the suite afterwards (how many bugs still have a kept
revealing test once repair runs) is outside the implemented pipeline.

## 4. Runtime assumptions

- Prediction-time inputs: failing test source, one failing run on B, signature, Javadoc of B, optional inferred spec.
  The buggy focal body exists in every instance record (`impl`) but is shown only in ablation A5.
- Not available to a judge by construction: fixed version, patch, developer tests, bug id, labels.
- Developer tests are withheld because Defects4J's buggy checkout contains the bug-triggering tests; showing them
  would leak the fix.
- One laptop GPU; a local judge call is 1.7 s (J1) to ≈70 s (thinking). A fresh-JVM test run in WSL is on the order
  of a second; a single-file `javac` against a compiled checkout is a few seconds.
