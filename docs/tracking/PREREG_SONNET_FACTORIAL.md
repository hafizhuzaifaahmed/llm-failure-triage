# DRAFT preregistration: specification × architecture factorial with a judge that passes its gate (journal follow-up)

**Status: draft for the authors. Nothing has been called, registered or paid.** The Anthropic key used for E9/E9b is being
revoked; a new key, a spending limit set in the Console and the authors' written approval are needed before any call.
This draft answers review item A6 (the RQ2/RQ3 nulls come from M1, a judge that failed its own development gate G-d).
Internal provenance: D-128. A git commit is not an external timestamp; if the authors want this preregistered, the
document is uploaded to OSF (or AsPredicted) **before** any call (see `OSF_PREREG_RQ4_OUTLINE.md` for the RQ4 one).

## 1. Question and hypotheses
With a judge that passes the development gate, does the specification level or the triage architecture change
classification quality on held-out real faults?

| ID | Contrast (paired, same instances) | Primary metric | Direction tested |
|---|---|---|---|
| F-H2a | S1 − S0 on methods with Javadoc, averaged over J1, SC, DEB | balanced accuracy | two-sided |
| F-H2b | S2 − S1, averaged over arms | balanced accuracy | two-sided |
| F-H3a | DEB − SC at S1 | balanced accuracy | two-sided |
| F-H3b | SC − J1 at S1 | balanced accuracy | two-sided |

Balanced accuracy is primary (prevalence-independent; review item B1); F1, MCC, TPR, TNR are secondary and reported.
One Holm family of the four. α = 0.05. Equivalence margin ±0.05 on the 90% CI, as in the primary study.

## 2. Judge and gate (run first; decides whether the factorial runs)
- Judge: Claude Sonnet 5.5 (`claude-sonnet-5-5`) through the Message Batches API, default sampling, thinking off, the
  frozen `local_m1b` prompts and evidence packages unchanged.
- Gate, on the development pilot (63 instances, 3 projects), at S1: G-a validity ≥ 98%, G-b citation, and G-d (J1 F1 above
  both trivial baselines). **If G-d fails, the factorial does not run** and the failure is reported; no prompt change.

## 3. Design
- Data: D1-test, the same 177 scored instances (60 PF, 117 TF), leakage aborts as in D-70.
- Cells: S0/S1/S2 × J1/SC (five samples)/DEB (five calls) × three replicates. The E9 decisions (S1 J1 replicate 0, S1
  DEB replicates 0–2) are reused, so new spend covers the remaining cells.
- Statistics: bug-level cluster bootstrap, 10,000 resamples, committed seed; paired contrasts; replicate means;
  a two-level (bugs × replicates) bootstrap reported beside it (D-106).
- Exclusions: invalid outputs scored TF (primary) and excluded (sensitivity); AMB excluded.
- Stopping: a hard spending cap in code and in the Console; a canary batch of 3 first; no retry of a failed batch
  beyond the API's own; any refusal or error rate > 2% stops the run.

## 4. Cost (measured basis vs estimate) — `results/planning/sonnet_factorial_estimate.json`
| | US$ |
|---|---|
| **Measured** E9 cost per decision at S1: J1 / DEB | 0.00417 / 0.02331 |
| **Measured** already spent on reusable E9 cells | 13.11 |
| Estimated full factorial (SC = 5 × J1; S0/S2 scaled by M1's token ratios 0.87–1.10) | 76.21 |
| Estimated dev-gate check (63 instances, J1 + SC + DEB) | 3.05 |
| **Estimated new spend** | **66.14** |
| With a 30% margin (suggested Console limit) | 85.99 |

Prices are those embedded in the logged E9 costs (batch pricing on the run date) and must be re-verified before any
call. Wall time: E9's 2,832 calls completed in nine batches within a day.

## 5. What would be claimed
Only what the four tests show, for this judge, on this data. A null with a gate-passing judge is evidence about the
factors for that judge; it does not transfer to other judges. Memorisation remains a threat for a frontier model on
Defects4J (E9b's D2 check is cited, not re-run).

## 6. Author decisions needed
1. Approve the spend ceiling (suggested US$ 86) and create a new key with a Console limit.
2. Decide whether to register externally (OSF) before the calls.
3. Confirm balanced accuracy as the primary metric (the primary study used F1).
