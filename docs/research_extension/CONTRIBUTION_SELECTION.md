# Contribution selection

> **Note added after full-text verification (2026-11-11):** reason 2 below ("no direct prior work") is narrowed in
> `NOVELTY_COLLISION_CHECK.md` section E. Patch-based validation of failing tests exists (e-Otter++); the remaining
> claim is about model-free first-order mutants, no bug report, a fault-side verdict, and decoupling as evidence.
> The selection stands; the novelty gate is "narrowed and passed", not "passed".

Decided before the held-out probe results were read (the development engineering pilot, D-135, had been seen).
The outcome of the evaluation is in `CONTRIBUTION_EVALUATION.md` and may overturn this choice.

## Primary: counterfactual program probes (N1)

**Claim to be tested.** Executing a failing generated test against small, systematic edits of the buggy program
yields evidence about which side is at fault, without the fixed version and without an LLM.

**Why this one.**

1. It attacks the top-ranked bottleneck (GAP B1): every existing rule re-reads one failing run.
2. It is the only candidate for which the documented search found no direct prior work (collision check, C3). Its
   nearest ancestor, mutation-based fault localization, uses the same observable for a different inference and
   assumes away the question asked here.
3. Its power does not come from the judge. Every local judge in the study is below its development gate; a
   contribution that depends on them inherits that weakness, and one that depends on a paid frontier model cannot be
   run under the authors' current approvals.
4. It is falsifiable on existing labels with outcomes nobody has computed, deterministic, and costs seconds of CPU
   per failure.
5. It makes a prediction that can fail in an informative way: if real faults are not reachable by small edits, or
   wrong tests are flipped as easily as right ones, the rates will show it.

**What it is not.** Not a classifier and not a guarantee. A flip is a plausible patch, and plausible patches overfit.
The contribution is the measured evidential value of two observables (a reachable passing state; a failure no edit
can move) and the rules built on them.

## Supporting, tightly coupled: probe evidence shown to the judge (N3)

The same ledger, rendered as a short report inside the evidence package, with the same one-shot judge at the same
call budget. It answers the question the existing data cannot: is the judge short of evidence or short of reasoning?
It shares the mechanism, the engine and the ledger; it adds one evidence section and one ablation arm. It needs local
model calls only and is planned, not run, in this pass (see `EXPERIMENT_BLUEPRINT.md`).

N6 (joint abduction over the failures of one method) is recorded as the natural next step on the same ledger, not as
a second supporting contribution.

## Fallback: fresh sealed benchmark with a cause taxonomy and the end-to-end outcome (N7 + N8)

If the probes carry no usable signal on held-out real faults, the strongest paper this project can become is a
measurement paper: execution-grounded triage on a larger, fresh real-fault set (the 78 capped-out methods, more
generations per method), an independently audited taxonomy that separates wrong expectations from second real faults,
and bugs-still-detected after a repair stage. That fallback is also the confirmation set the primary contribution
needs, so the generation work is not wasted either way.

## Rejected, with reasons

| Candidate | Reason |
|---|---|
| N2 Evidence-gathering agent | Deferred, not rejected on principle. An agent is only as good as its tools; N1 builds and measures the tools first. With sub-gate local judges, a tool-use loop would add variance and token cost that no matched-budget comparison on 22 bugs could separate from a real effect |
| N4 Risk-controlled discard | The i.i.d. core is Neyman–Pearson classification; calibrated judge cascades are published (Trust or Escalate, REAG); 22 bugs certify nothing below about 13%. Kept as a reporting practice (bug-level bounds), not as a contribution |
| N5 Masked oracle re-derivation | The repository's own evidence is against it (specifications gave no benefit; agreement among generations uninformative on real faults), and spec-derived oracles are a crowded line of work |
| N9, N10 | Controls and framing. Necessary for a submission, not contributions |
| Keeping KUU and the cascade as the method | Collides with published three-family judging and escalation; on the paper's own rates it is an operating point |

## Gates the primary contribution must pass

| Gate | Criterion | Where checked |
|---|---|---|
| Novelty | No prior work that uses mutant or patch reachability to decide test-versus-program blame | `NOVELTY_COLLISION_CHECK.md` (passed on the searches run; full-text check of two preprints outstanding) |
| Feasibility | Engine reproduces stored failures and completes a split within the session | D-134 Stage 1 (passed: dev split in 346 s, no exclusion) |
| Signal | HP-1 or HP-2 holds on D1-test | `CONTRIBUTION_EVALUATION.md` |
| Usefulness | A certificate rule improves a base rule on balanced accuracy without losing bugs | `CONTRIBUTION_EVALUATION.md` |
| Confirmation | The same rules, unchanged, on fresh real faults | not possible in this pass; `DATASET_EXPANSION_PLAN.md` |
