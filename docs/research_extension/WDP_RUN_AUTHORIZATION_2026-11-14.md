# Authors' approval of the WDP freeze and of the four retrospective evaluation runs (recorded 2026-11-14)

Decision entry: D-151 in `docs/tracking/DECISIONS.md`. Approval file: `configs/extension/wdp_run_approval.json`.
The authors' decision, quoted verbatim from their message of 2026-11-14 in the working session:

> My decision: Approve 08ec9af. Approve the four-run window in principle, but not D-151 verbatim.
>
> 1. Freeze approval — APPROVED
> Based on the review evidence provided, 08ec9af satisfies the conditions for freeze approval.
>
> The important evidence is:
> - Both original defects and all eight additional malformed-input cases produce ND (not determined).
> - All 12 review cases have regression coverage.
> - T19/T20 cover necessary conditions, including 240,000 fuzzed cases.
> - T21 confirms the 118 existing development levels remain unchanged.
> - The selected 38 tests pass, with zero independent-checker violations.
> I authorize treating 08ec9af as the frozen code version for the retrospective evaluation.
>
> 2. D-151 — APPROVED WITH REQUIRED CORRECTIONS
> There is one important governance distinction in the draft.
>
> D-67 should not be listed as an exception. Its time box governs model experiments through run_experiment.py. The
> four WDP runs do not make model calls and do not use that mechanism.
>
> The actual exception required is to D-58's general compute deadline.
>
> Before committing D-151, make these corrections:
> 1. Describe the exception as applying to D-58 only. Explicitly state that D-67 and all model-experiment deadlines
>    remain unchanged.
> 2. Include the complete manifest hash rather than the abbreviated bae8ad9a….
> 3. Specify exactly one invocation per evaluation run, with no retries.
> 4. Preserve partial outputs and mark any run unfinished at 18:00 as incomplete. Do not include incomplete runs in
>    the analysis.
> 5. Record the 13 November confirmation execution transparently as a historical governance issue, without
>    presenting D-151 as retroactive authorization.
>
> 3. Authorized execution sequence
> Once the corrected D-151 and approval file are committed:
>
> | Step | Authorization |
> |---|---|
> | Freeze 08ec9af | Approved |
> | Record D-151 | Approved with corrections |
> | Four WDP runs | Approved within revised window |
> | Retry failed runs | Not authorized |
> | Frozen analysis | After run ledgers are committed |
> | Interpretation review | Before 20:00, 14 November |
>
> The 18:00 deadline remains unchanged.
>
> Final decision: The code freeze is approved. The four retrospective evaluations are authorized subject to the
> D-151 corrections above. Do not modify the frozen code, profiles, or historical experiment records.
>
> No evaluation runs have been authorized to start before the corrected decision record and approval file are
> committed.

## How each correction is implemented in D-151

| Correction | In D-151 |
|---|---|
| 1. D-58 only; D-67 and model-experiment deadlines unchanged | "Exception: to D-58's general compute deadline only … D-67 is not excepted … remain unchanged, and no profile file is edited" |
| 2. Complete manifest hash | `bae8ad9a4d3ddbbf0f0149dd97e8c3f59aaa16f3dd9441d4fb47491cc2bb06cd`, and the full freeze commit id |
| 3. One invocation per run, no retries | "exactly one invocation … per evaluation run; no retry and no resumption" |
| 4. Partial outputs preserved; unfinished at 18:00 marked incomplete; not analysed | stated; plus the consequence under the frozen code: the analysis requires all four ledgers to be complete, so an incomplete run means the frozen analysis is not run at all, and no subset is analysed without a further decision |
| 5. 13 November confirmation as a historical governance issue, not retroactive authorisation | stated in its own clause |

Also recorded in D-151: the correction to D-149's summary (eight further cases, not six; the omitted
`coupled`-as-string case).
