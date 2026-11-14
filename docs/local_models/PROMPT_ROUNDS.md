# Prompt development rounds (D-33) — dev pilot only, M1 = qwen3.5:9b

Each round's prompt set is committed before it is run. Selection (D-33): per family, the highest dev F1 among
versions with < 2% invalid; within 0.005 F1, the shorter prompt. Stop at 5 rounds or when a round improves
neither J1 nor DEB dev F1 by more than 0.02. Dev pilot: 63 instances, 1 leakage-rejected → 62 judged, 54 non-AMB
(20 PF, 34 TF). Numbers are dev-pilot diagnostics, not results.

## Round 0 — `prompts/dev/v0` (as written in Phase 2)
| Condition | Valid | PF F1 | P | R | MCC | TP/FP/FN/TN |
|---|---|---|---|---|---|---|
| J1 S1 | 100% | 0.231 | 0.50 | 0.15 | 0.10 | 3/3/17/31 |
| J1 S2 | 100% | 0.077 | 0.17 | 0.05 | −0.15 | 1/5/19/29 |
| DEB S1 | 99.6% | 0.188 | 0.25 | 0.15 | −0.13 | 3/9/17/25 |
Trigger: (ii) — every arm ≥ 98% valid. **Failure mode visible in the confusion matrix:** recall 0.15 — the judge
labels almost every failure TEST_FAULT (17/20 PF missed, typically at confidence 95–100). The judge prompt defines
TEST_FAULT by three concrete sub-cases and PROGRAM_FAULT by none; most misses are tests whose expectation
contradicts the buggy version's own documentation, which the judge treats as authoritative.
Runaway (D-39): 1 of 270 DEB calls; 0 of 108 J1 calls. Evidence: `results/dev/PROMPTDEV_v0/round_eval.json`.

## Round 1 — `prompts/dev/v1`
Change (judge + adjudicator, identical text): both labels defined symmetrically with concrete sub-cases; "Do not
presume that the implementation is correct, nor that its documentation is complete or up to date. Decide which
side is more likely wrong from all the evidence; do not default to either label." No base-rate information, no
project- or instance-specific content. Advocate and spec-inferencer prompts unchanged.
Result:
| Condition | Valid | PF F1 | P | R | MCC | TP/FP/FN/TN |
|---|---|---|---|---|---|---|
| J1 S1 | 98.1% | 0.286 | 0.33 | 0.25 | −0.05 | 5/10/15/24 |
| J1 S2 | 100% | 0.300 | 0.30 | 0.30 | −0.11 | 6/14/14/20 |
| DEB S1 | 100% | 0.171 | 0.20 | 0.15 | −0.22 | 3/12/17/22 |
J1 improved by > 0.02 (S1 +0.055, S2 +0.223) → continue. Runaway: 1 of 54 J1|S1 calls. MCC ≤ 0 everywhere: the
judge does not separate the classes. Remaining errors are dominated by instances where the failing expectation
contradicts B's documentation (Gson_4 PF) or the test expects behaviour B never had (TF judged PF).

## Round 2 — `prompts/dev/v2`
Change (judge + adjudicator, identical text): a two-question check — (1) is the test's input and call sequence allowed
by [Sig]/[Doc]? If not, test at fault; (2) if allowed, is the observed result in [F] what the method's documented or
evident purpose implies? If not, program at fault. Generic; no instance content.
Result:
| Condition | Valid | PF F1 | P | R | MCC | TP/FP/FN/TN |
|---|---|---|---|---|---|---|
| J1 S1 | 96.3% | 0.250 | 0.25 | 0.25 | −0.19 | 5/15/15/19 |
| J1 S2 | 100% | 0.167 | 0.19 | 0.15 | −0.25 | 3/13/17/21 |
| DEB S1 | 100% | 0.171 | 0.20 | 0.15 | −0.22 | 3/12/17/22 |
Neither J1 nor DEB improved by > 0.02 → **stop** (D-33). Runaway: 2 of 54 J1|S1 calls (v2 is ≥ 2% invalid).

## Selection → frozen set `prompts/frozen/local_m1` (set hash `30412c95…4c47`, MANIFEST.json)
- Judge prompt: **v1** (J1|S1 F1 0.286 at 1.9% invalid; J1|S2 0.300) over v0 (0.231 / 0.077); v2 excluded (3.7% invalid).
- Debate prompts (advocates, rebuttal, adjudicator): **v0** (DEB|S1 F1 0.188) over v1 = v2 = 0.171.
- Spec inferencer, generator: v0 (unchanged; specs 39/39 valid).
Three rounds were run for both families (v0, v1, v2), so their revision counts are equal.

## Correction (D-47) — validity counted over all 62 judged instances
J1|S1 invalid: v0 0/62 · v1 3/62 (4.8%) · v2 2/62 (3.2%); DEB v0 1/310, v1 0, v2 0; J1|S2 0 everywhere.
Hence only v0 qualifies for the judge prompt under "< 2% invalid"; `prompts/frozen/local_m1` (judge v1) is
superseded. Round 1's J1 validity (95.2%) should have triggered a format-only revision; round 2 (v2) was a
substantive one by mistake and is reported as run.

## M1 gate on `local_m1` — `results/dev/GATE_M1/dev_gates.json`
G-a fails (J1 95.2%, SC 97.4%, DEB 99.7%; all invalid outputs are runaways), G-b passes, G-c passes (0.286),
G-d fails (J1 0.286 vs R0 0.642 / KA 0.553). k_T = 7.

## Round 3 — `prompts/dev/v3` (M1 fallback step 1: format-only, because validity fails)
Change (judge only): two short format examples, one per label, and "Keep the summary to one or two short sentences
and end the JSON object immediately after the confidence value." Everything else = v1.
Result (validity over all 62 judged):
| Condition | Valid | PF F1 | P | R | MCC | TP/FP/FN/TN |
|---|---|---|---|---|---|---|
| J1 S1 | 100% | 0.350 | 0.35 | 0.35 | −0.03 | 7/13/13/21 |
| J1 S2 | 100% | 0.368 | 0.39 | 0.35 | 0.03 | 7/11/13/23 |
| DEB S1 | 100% | 0.171 | 0.20 | 0.15 | −0.22 | 3/12/17/22 (prompts = v1, unchanged) |
J1 improved by > 0.02 → continue; one round left in the budget (5).

## Round 4 — `prompts/dev/v4` (last round; substantive, both families)
Change: the same sentence added to the judge (base v3) and the adjudicator (base v0, the best DEB version):
"Use the failure evidence [F]: note whether the failure was raised by the test's own assertion or by an exception
inside the program under test (see the stack frames), and whether the program was given input and a call sequence
its interface accepts." Advocates = v0.
Result:
| Condition | Valid | PF F1 | P | R | MCC | TP/FP/FN/TN |
|---|---|---|---|---|---|---|
| J1 S1 | 100% | 0.182 | 0.23 | 0.15 | −0.16 | 3/10/17/24 |
| J1 S2 | 100% | 0.389 | 0.44 | 0.35 | 0.09 | 7/9/13/25 |
| DEB S1 | 100% | 0.267 | 0.40 | 0.20 | 0.03 | 4/6/16/28 |
Five rounds used → stop.

## Final selection → `prompts/frozen/local_m1b` (set hash `c6a83d89…9a58`; supersedes `local_m1`)
- Judge prompt (scored by J1|S1): **v3** (0.350, 0/62 invalid) — v0 0.231, v1 0.286 (excluded, 4.8% invalid),
  v2 0.250 (excluded, 3.2%), v4 0.182.
- DEB prompts (scored by DEB|S1): **v4** (0.267) — v0 0.188, v1 = v2 = v3 0.171.
- Spec inferencer, generator: v0.
Five rounds for both families (v0–v4).
