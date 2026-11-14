# Selected method: counterfactual program probes (CFP)

Specification of the method as implemented in `src/triage_ext/` at the commit that ran the pilot.
Decision entries: D-134 (design), D-135 (scope amendment).

## 1. Problem definition

**Objects.** A buggy program version `P`, a method under test `m` in class `C` of `P` (the method the test was
generated for), and a generated test `t` that fails deterministically on `P` with failure `φ₀ = (σ₀, μ₀)`:
signature `σ₀` = (outcome type, exception class, failing test line) and normalised message `μ₀`.

**Decision.** `d(t) ∈ {keep, discard}`; an abstaining variant returns `defer`. `keep` means the failure is treated as
a program fault (PF); `discard` means the test is treated as wrong (TF).

**Prediction-time information `I(t)`.** The source of `t`; the stored runs of `t` on `P`; a compiled checkout of `P`;
the other generated tests of `m` with their stored runs on `P`; and, for the rules that use a judge, the study's
evidence package. Explicitly excluded: the fixed version, the patch, which classes the fix modified, the
bug-triggering tests, developer tests, bug identifiers, labels.

**Offline-only information.** The execution label `y(t) ∈ {PF, TF, AMB}` from running `t` on the fixed version. It
joins the data in the analysis script and nowhere earlier.

**Loss.** Asymmetric and stated at two levels. Test level: `L = c_FN · 1[y = PF, d = discard] + c_FP · 1[y = TF, d = keep]`
with `c_FN ≫ c_FP`. Bug level: a bug is *lost* when it has at least one PF test and none is kept. No value of
`c_FN / c_FP` is assumed; results are reported as (TPR, TNR) pairs, PF tests lost and bugs lost, so a reader can apply
their own ratio.

## 2. The counterfactual set

Let `R(m)` be the *region*: the body of `m` plus the bodies of methods of `C` that `m` calls by simple name,
transitively to depth 2 (`probe.callee_regions`; syntactic, overloads included).

`M(m)` is a set of first-order mutants of `R(m)` produced by a fixed operator set:

| Operator | Edit |
|---|---|
| ROR | `<`→{`<=`,`>`}, `<=`→{`<`,`>=`}, `>`→{`>=`,`<`}, `>=`→{`>`,`<=`}, `==`↔`!=` |
| AOR | `+`↔`-`, `*`↔`/`, `%`→`*`, `+=`↔`-=` |
| COR | `&&`↔`||` |
| LVR | `0`→`1`, `1`→`0`, `n`→{`n+1`,`n−1`}, `true`↔`false` |
| NEG | `if (c)` → `if (!(c))` |
| STD | delete one statement that is not a control transfer |

At most `K = 80` mutants per focal method: mutants of `m`'s own body first (a seeded sample if more than 80), the
remaining room filled by a seeded sample of callee mutants. Seeds derive from the focal identifier, so `M(m)` is a
function of the source text alone. Mutants that do not compile are dropped; `M_c(m)` are the compiled ones.

## 3. Observation

For each `p ∈ M_c(m)`, run `t` once on `P[p]` (the checkout with `p`'s class files ahead of it on the classpath) in a
fresh JVM with a 10 s limit, giving `φ_p`. A pass is re-run once.

```
class(p, t) = FLIP   if t passes on P[p] twice
              SHIFT  if t fails with σ_p ≠ σ₀ or μ_p ≠ μ₀
              SAME   if t fails with (σ_p, μ_p) = (σ₀, μ₀)
              ERR    timeout, harness error, or a pass that did not repeat
```

For a FLIP mutant `p`, let `S(m)` be up to 30 sibling tests (other generated tests of `m` that passed on every
stored run on `P`; seeded choice). `p` is **regression-consistent** when no sibling fails on `P[p]`.

## 4. Evidence ledger (one record per failing test)

```
E(t) = { n_compiled, n_flip, n_shift, n_same, n_err, n_rcf,
         flip             = n_flip > 0
         rcf              = some FLIP mutant is regression-consistent
         flip_without_rcf = flip and not rcf
         coupled          = n_flip + n_shift > 0
         decoupled        = n_compiled ≥ 10 and n_flip + n_shift = 0
         flip_fraction, coupled_fraction,
         per-mutant entries: operator, line, tier, region, class, outcome, sibling counts }
```

Exclusions (no ledger evidence; the base rule decides): focal method not located in the source, focal class does not
recompile alone, test does not compile alone, stored failure not reproduced under the identity overlay.

## 5. Why the observables should carry information

**H-reach (for `flip`).** Competent-programmer hypothesis: a real fault lies a small syntactic distance from the
correct program. If `t` is right (PF), the set of programs on which `t` passes contains the correct program, which is
near `P`, so a first-order mutant that passes `t` is more likely to exist than when `t` is wrong (TF), where the
programs satisfying `t` have no reason to be near `P`. Prediction: `P(flip | PF) > P(flip | TF)`.
*Known ways to fail:* fixes that add code are not first-order reachable; an off-by-one expectation in a wrong test
can be satisfied by an off-by-one mutant.

**H-dep (for `decoupled`).** If no edit of `R(m)` changes the failure in any way, the failure is determined before or
outside the code under test (set-up error, API misuse, an assertion on something `m` does not compute).
Prediction: `P(decoupled | TF) > P(decoupled | PF)`.
*Known way to fail:* the fault sits outside `R(m)` (another class, a constructor, a static initialiser).

**H-sib (for the regression filter).** A flip that breaks sibling tests satisfies `t` at the expense of behaviour
other tests rely on, which favours TF. *Known way to fail:* siblings generated from buggy code can assert the buggy
behaviour, and then the true fix breaks them.

## 6. Decision rules

Let `b(t) ∈ {keep, discard}` be any base rule (keep-all, KUU, a judge).

```
CK    (certified keep)      d = keep     if E(t).rcf        else b(t)
CD    (decoupled discard)   d = discard  if E(t).decoupled  else b(t)
CK+CD                       d = keep if rcf;  discard if decoupled;  else b(t)
```

`rcf` and `decoupled` are mutually exclusive (a flip is a coupling). An excluded instance always gets `b(t)`.
The rules have no fitted parameter: `K = 80`, the depth 2, the 10-mutant minimum and the timeouts were set before any
held-out probe was run.

## 7. Algorithm

```
procedure PROBE_FOCAL(P, m):                       # once per focal method
    src ← source of C in P;  span ← unique occurrence of m's text in src        # else exclude
    identity ← compile(src)                        # else exclude
    M ← sample(mutants(body(m)), K) ⊕ sample(mutants(callees(m, depth 2)), K − |·|)
    for p in M in parallel:  overlay[p] ← compile(src with p applied)           # drop on failure

procedure PROBE_TEST(t):                           # once per failing test of m
    compile t alone against P                      # else exclude
    φ₀ ← run(t, identity);  require signature(φ₀) = stored signature           # else exclude
    for p in overlays in parallel:
        φ ← run(t, overlay[p]);  if pass: φ' ← run again
        record class(p, t)
    for p with class FLIP:
        run each sibling in S(m) on overlay[p];  rc[p] ← none failed
    return summarise(records)                      # the ledger E(t)

procedure DECIDE(t, rule, b):  return rule(b(t), E(t))
```

Stopping conditions: every loop is bounded (`K` mutants, 30 siblings, one re-run). No agent loop exists.

## 8. Cost

Per focal method: `|M| ≤ 80` single-file compilations. Per failing test: 1 + `|M_c|` + (flips) JVM starts, plus up to
30 sibling runs per flip. No model call, no token, nothing leaves the machine. Measured wall time is in
`CONTRIBUTION_EVALUATION.md`. Cost grows linearly in the number of failing tests and is independent of prevalence.

## 9. Validity safeguards

| Risk | Safeguard |
|---|---|
| Fixed-version leakage | The engine reads three whitelisted metadata keys of the buggy checkout and refuses a work directory that is not `…/b`; a unit test scans the engine for every fixed-side or label name |
| Label leakage | Labels are opened only by `scripts/extension/ext1_probe_analysis.py` |
| Self-confirming evidence | No LLM takes part; the test's own expectation is never edited; mutants are generated from the program text alone |
| Contamination of the checkout | Mutants live in a scratch directory and reach the JVM through the classpath; the checkout is not written |
| Dependence between tests of one bug | All intervals resample bugs |
| Tuning to held-out labels | Operator set, cap, thresholds and rules were committed before the held-out run; the one amendment (D-135) was made on a label-free quantity and is disclosed with the dev counts |

## 10. Ablations that isolate the mechanism

| Ablation | Question |
|---|---|
| Focal body only vs focal body + callees | Does the wider region matter? (both summaries are in every ledger record) |
| `flip` vs `rcf` | Does the sibling filter add or remove information? |
| Operator family left out | Which edits produce the signal? |
| Random label permutation within bug | Is the flip difference larger than chance structure? |
| Probe flags vs the cheap failure features (assertion/exception, deepest frame) | Is the signal more than failure type? |
| Probe report in the judge's package vs the same judge without it, equal calls | Evidence or reasoning? (N3; needs local calls) |

## 11. Baseline compatibility

Nothing in the primary pipeline is changed. Base-rule predictions are read from the committed decisions through
`scripts/analysis/revision_common.build`, so KUU, KUU-NG, debate, the thinking judge, the 2-of-3 vote and the frontier
judge are evaluated on the same instances with the same bootstrap as in the paper.
