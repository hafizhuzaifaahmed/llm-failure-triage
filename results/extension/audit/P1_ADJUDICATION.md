# Adjudication of the P1 replication result (lead research model, 2026-11-13)

`P1_SUMMARY.md` (Opus) reports `P1 RESULT: FAIL` and is left unchanged. This file does not override it. Whether P1
counts as passed for the freeze (brief step P3, stop condition 1) is the authors' decision.

## What failed

One tolerance check in A1: two per-frame C1 bootstrap upper limits from the audit's own different-seed bootstrap
differ from the registered secondary files in the second decimal.

| Limit | Audit script (seed 777) | Registered (seed 20261011) |
|---|---|---|
| F1 C1 upper | 0.2698 | 0.2786 |
| F2 C1 upper | 0.4078 | 0.4133 |

Every count, label, point estimate, rule-table entry, Holm value and exact bound matched.

## Check run in response (read-only)

`docs/research_extension/audit_scripts/audit_seedcheck.py`, output in `FABLE_seedcheck.txt`: the registered seed's
random stream generated independently of the project's code (`numpy.random.default_rng(20261011).multinomial`,
bugs in sorted order), then 20 other seeds.

| Interval | Independent code, registered seed | Registered file | Range of the upper limit over 20 other seeds |
|---|---|---|---|
| Pooled C1 | [−0.1372, 0.2735] | [−0.1372, 0.2735] | 0.268–0.283 (sd 0.004) |
| Pooled C2 | [0.1140, 0.3723] | [0.1140, 0.3723] | 0.369–0.377 (sd 0.002) |
| F1 C1 | [−0.3229, 0.2786] | [−0.3229, 0.2786] | 0.251–0.276 (sd 0.007) |
| F1 C2 | [−0.0833, 0.1563] | [−0.0833, 0.1563] | 0.153–0.160 (sd 0.002) |
| F2 C1 | [−0.1257, 0.4133] | [−0.1257, 0.4133] | 0.403–0.427 (sd 0.006) |
| F2 C2 | [0.1738, 0.4682] | [0.1738, 0.4682] | 0.464–0.472 (sd 0.002) |

## Finding

1. The registered intervals are reproduced exactly. The mismatch is bootstrap seed variation.
2. The fault was a sentence in `CONFIRMATION_INDEPENDENT_AUDIT.md` (row 16) that overstated how closely the
   audit's different-seed intervals agree. It has been corrected, and rows 22 and 23 and section 9 were added.
3. The A4 expectation pointed at the guard input file; refusals are recorded in
   `votes/<run>/leakage_rejections.jsonl`, where Opus found all 11.
4. A2 follow-up: the fresh label rule applied to every labelled instance
   (`audit_scripts/audit_labels_full.py`, output `FABLE_A2_labels_full.txt`): 834 of 834 labels and stored
   signatures equal (55 PF, 763 TF, 16 AMB).

## Recommendation to the authors

Accept P1 as passed with the corrections above. No registered number, label or reading changes. Consequence for
the paper: per-frame interval limits are printed to two decimals with a note on Monte Carlo error.

Not checked by P1 and still resting on the lead model's own checks: ledger flags against mutant records (audit
row 4), concatenation hashes (row 5), chronology (row 18).
