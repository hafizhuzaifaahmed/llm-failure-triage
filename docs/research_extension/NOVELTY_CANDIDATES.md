# Novelty candidates

Ten candidates across architecture, method, data and evaluation. Names are working labels. Scores were assigned
before any held-out probe result was read; the development-split engineering pilot (D-135) had been seen.

## Rubric

Each criterion is scored 1–5. Weighted total = Σ weight × score, maximum 5.

| Criterion | Weight | 5 means |
|---|---|---|
| Originality after the literature check | 0.22 | no direct prior work found after documented search |
| Technical depth | 0.18 | a mechanism with a stated assumption that can fail, not a configuration |
| Importance of the question | 0.12 | addresses the top-ranked bottleneck (B1) |
| Developer value if it works | 0.10 | changes what a developer must inspect or what bugs survive |
| Empirical testability | 0.12 | a falsifiable prediction on available labels |
| Reproducibility | 0.08 | deterministic, no paid or closed component |
| Feasibility here | 0.10 | runnable on this machine and data within the session or a few days |
| Venue fit | 0.08 | matches what ICSE/FSE/ASE/ISSTA/TOSEM publish as a technical contribution |

Originality and depth carry 40% together; feasibility 10%.

## Records

### N1. Counterfactual program probes (CFP)
- **Problem.** A failing run shows that test and program disagree, not which is wrong. Target: a triage stage inside
  a test generator or a CI bot, working on the buggy program only.
- **Mechanism.** Run the failing test against first-order mutants of the method under test and of the same-class
  methods it calls. Under the competent-programmer hypothesis a real fault is a small edit away from correct code,
  so if the test is right some small edit should make it pass (FLIP). If no edit changes the failure at all, the
  failure does not depend on the method (decoupled). The outcome pattern is evidence about fault side.
- **New element.** Uses the fault-localization observable of MUSE for a different inference. KUU and the cascade
  add opinions about one run; CFP adds runs. No LLM, no fixed version.
- **Overlap risk.** MUSE/Metallaxis (same observable, assumes the test is right), OASIs (mutation on oracles with a
  human), APR overfitting literature (a plausible edit is not a correct one).
- **Needs.** Mutant generator, overlay compile-and-run engine, evidence ledger, policy rules. Days of engineering.
- **Evaluation.** Rates of FLIP and decoupling under each label; certificate rules beside base rules on TPR, TNR,
  bugs lost; ablation of scope and regression filter; cost in CPU-seconds. Baselines: keep-all, KUU, KUU-NG, debate,
  thinking judge, frontier judge, the failure-feature classifier.
- **Success.** P(FLIP | PF) − P(FLIP | TF) > 0 with a bug-level interval excluding 0, and a certificate rule above
  the local frontier.
- **Failure modes.** Fix not reachable by one edit (many Defects4J fixes add code); wrong-oracle tests flipped by
  coincidence; sibling tests that assert buggy behaviour; tiny methods with no mutants.
- **Type.** Method. **Feasible:** yes, today.

### N2. Evidence-gathering triage agent
- **Mechanism.** An LLM chooses diagnostic actions (capture values, run test variants, inspect call sites, run
  probes) under a budget, then decides PF / TF / defer.
- **New element.** Adaptive choice of evidence. **Overlap.** LogicHunter, FalseCrashReducer, AutoSD in other tasks.
- **Risk.** With 9–14 B judges that fail their gate, a tool-use loop is the least reliable component; any gain is
  confounded with tokens and wall time unless the tools are first shown to carry information without the agent.
- **Type.** Architecture. **Feasible:** 1–2 weeks (J-F4). Depends on N1-style tools existing and being informative.

### N3. Probe report as judge evidence (fixed, not adaptive)
- **Mechanism.** Add a compact, deterministic probe report to the evidence package ("line 6: `<` → `<=` makes the
  test pass; 11 of 11 sibling tests still pass") and re-run the same one-shot judge.
- **New element.** Tests whether execution evidence helps a judge at a matched call budget, separating evidence
  from reasoning (GAP B1 vs B4). **Type.** Supporting method/ablation. **Feasible:** yes, local calls only.

### N4. Risk-controlled discard with bug-level calibration
- **Mechanism.** Choose a discard threshold so that the share of bugs losing every revealing test is ≤ α with
  confidence 1−δ, with bugs as exchangeable units.
- **Overlap.** Neyman–Pearson classification; Learn-then-Test; Trust or Escalate; REAG. **Gap.** The bug-level loss.
- **Risk.** 22 bugs certify nothing below ≈13%. **Type.** Method (statistical). **Feasible:** computable, not useful yet.

### N5. Masked oracle re-derivation
- **Mechanism.** Hide both the expected and the observed value; ask independent models what the call should return
  from the documentation; compare with each side.
- **Overlap.** TOGA-style spec-derived oracles, CANDOR, Doc2OracLL, differential prompting. **Repository evidence
  against.** Javadoc gave no benefit; cross-generation agreement AUROC 0.513; 15–21% of derived specs keep the defect.
- **Type.** Method. **Feasible:** yes, but capped by weak judges.

### N6. Abductive joint triage over all failures of a method
- **Mechanism.** Treat the failing tests of one method together: prefer the explanation "one small program fault"
  when a single edit flips several failures, and "several wrong tests" otherwise.
- **New element.** Parsimony across tests. **Overlap.** CodeT's dual agreement; MUSE aggregation. Builds on N1's
  ledger. **Type.** Method extension of N1. **Feasible:** zero extra execution once N1 exists; small samples.

### N7. Fresh sealed real-fault benchmark with a cause taxonomy
- **Mechanism.** Generate for the 78 capped-out methods and more generations per method; label by execution; add an
  independently audited taxonomy (wrong expectation, harness, second real fault, unresolved).
- **Overlap.** Zhao et al.'s four labels; no public failing-test set. **Type.** Dataset. **Feasible:** generation
  3–4 h of GPU plus hours of execution; the audit needs external raters (author approval).

### N8. End-to-end outcome inside repair-first generation
- **Mechanism.** After triage, run a repair stage on discarded tests; count bugs with a revealing test surviving and
  tests a developer must read. **Overlap.** Mathews and Nagappan (bugs lost), Meta (workload). **Type.** Evaluation.
  **Feasible:** about a week (J-F5).

### N9. Post-cutoff or renamed-identifier contamination control
- **Mechanism.** Bugs fixed after every judge's release, or behaviour-preserving renaming. **Overlap.** Ramos et al.
  on memorisation; GitBug-Java, GHRB. **Type.** Evaluation/data. **Feasible:** days; needs a benchmark newer than 2026 models.

### N10. Privacy-aware local/hybrid triage as a systems trade-off
- **Mechanism.** Report bug retention against data egress, latency and cost. **Overlap.** FrugalGPT, routing work;
  the paper already reports these numbers. **Type.** Evaluation framing. **Feasible:** zero new work; no new result.

## Scores

| Candidate | Orig. | Depth | Import. | Dev value | Testable | Reprod. | Feasible | Venue | **Total** |
|---|---|---|---|---|---|---|---|---|---|
| N1 Counterfactual program probes | 5 | 4 | 5 | 3 | 5 | 5 | 5 | 4 | **4.54** |
| N6 Abductive joint triage (on N1) | 4 | 4 | 4 | 3 | 3 | 5 | 4 | 4 | 3.86 |
| N3 Probe report as judge evidence | 3 | 3 | 5 | 3 | 5 | 4 | 4 | 4 | 3.74 |
| N2 Evidence-gathering agent | 4 | 4 | 5 | 4 | 3 | 2 | 2 | 4 | 3.64 |
| N7 Fresh benchmark with taxonomy | 3 | 2 | 4 | 4 | 4 | 5 | 3 | 4 | 3.40 |
| N8 End-to-end repair-first outcome | 3 | 2 | 4 | 5 | 4 | 4 | 2 | 4 | 3.32 |
| N4 Risk-controlled discard | 2 | 4 | 3 | 3 | 3 | 5 | 4 | 3 | 3.22 |
| N5 Masked oracle re-derivation | 2 | 3 | 3 | 3 | 4 | 3 | 4 | 3 | 3.00 |
| N9 Contamination control | 2 | 2 | 3 | 2 | 4 | 4 | 2 | 3 | 2.60 |
| N10 Privacy trade-off framing | 1 | 1 | 2 | 3 | 3 | 5 | 5 | 2 | 2.36 |

Totals were computed by script from the weights above, not by hand.

Why the leading scores are what they are:

- **N1 originality 5:** no work found that uses mutant outcomes to decide fault side. **Depth 4, not 5:** the
  mechanism is one assumption (reachability by a small edit) plus an execution engine; it is not a learning method.
  **Developer value 3:** it can only help where the method under test has mutable logic and the fix is small.
- **N2 feasibility 2, reproducibility 2:** needs tool-use from judges that fail a simple gate; outcomes depend on
  model sampling. Its originality is 4 rather than 5 because agentic oracles exist in neighbouring tasks.
- **N4 originality 2:** the i.i.d. core is Neyman–Pearson classification and calibrated judge cascades are published.
- **N7 depth 2:** valuable and necessary, but a data contribution; it supports whichever method is confirmed.
