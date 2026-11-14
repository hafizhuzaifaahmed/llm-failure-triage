# Authors' acceptance of the P1 replication (recorded 2026-11-13)

`P1_SUMMARY.md` reports `P1 RESULT: FAIL` and is left as written. `P1_ADJUDICATION.md` explains the failure.
The authors' decision, quoted verbatim from their message of 2026-11-13 in the working session:

> P1 is accepted as passed after adjudication, for the scope of checks A1–A5.
>
> The initial FAIL remains recorded in `P1_SUMMARY.md`. The adjudication establishes that the two per-frame C1
> interval differences arose from bootstrap seed variation, not a registered-result discrepancy: the
> registered-seed intervals reproduce exactly in independent code. The audit's overstated tolerance statement has
> been corrected. The full 834-label recomputation, leakage-refusal verification, and A5 checks also pass.
>
> Proceed in the existing Opus session with P2 and, only if all implementation tests and dev-run acceptance
> criteria pass, P3 to create the local freeze commit. Do not start another Opus session or introduce concurrent
> writers.
>
> At P3b, return the freeze commit hash, manifest, test results, dev-run summary, changed-file list, and
> deviations for my review. Also report the status of the three audit items not independently replicated by P1:
> ledger flags against mutant records, concatenation hashes, and sealing chronology.
>
> This approval does not authorize D1_TEST or any confirmation-tranche WDP run. Those remain blocked until I
> explicitly approve the reviewed freeze commit. Keep the registered experiment, OSF kp79c, and all frozen paths
> untouched.

Scope of this acceptance: checks A1–A5 only. It does not approve any retrospective evaluation run
(`WDP_D1_TEST`, `WDP_CONF_F1`, `WDP_CONF_F2`, `WDP_CONF_CTRL`); `configs/extension/wdp_run_approval.json` must not
exist until the authors approve the reviewed freeze commit.
