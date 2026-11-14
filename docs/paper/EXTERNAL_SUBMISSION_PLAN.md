<!-- generated from docs/paper/src/EXTERNAL_SUBMISSION_PLAN.src.md by scripts/paper/build_numbers.py; every number is in docs/paper/NUMBERS_MAP.csv -->
# External submission plan — post-15-November upgrades (proposals only; nothing run)

Recorded 2026-11-03 under D-80. **Nothing in this document has been run, and none of it can change the course
submission or any committed result.** Each experiment needs the authors' approval, its own D-entry (draft below) and
its own scope entry (`configs/local_scope.json`) before any call. API cost of every proposal: **zero** (local Ollama
only). GPU time comes from `scripts/planning/project_external.py` (`results/planning/external_projection.json`), which
uses measured per-call and per-instance times from the committed call logs and includes the duty factor
0.80 (D-62). Session shapes: night 8–10 h, day
5 h. All proposals run on D1-test at S1 under the frozen protocol (frozen prompts, decoding,
seeds, sampling, analysis code; `configs/local_models.FROZEN.json` unchanged); a new model enters through its own
profile, as the 35b did (D-67, D-76).

Power context (D-80 sensitivity analysis): at this sample size the minimum detectable ΔF1 at 80% power and α = 0.05 is
0.165 for DEB vs SC and 0.272 for J1 vs R0. A second judge on the same
193 instances cannot detect smaller architecture differences; E6–E8 are robustness and
replication checks, not new confirmatory tests of small effects.

## E6 — E6a: stronger-judge evidence (exploratory 35b); E6b: a third model family

**E6a: complete the exploratory 35b (SC, and DEB for the instances not reached).** 970
calls at the measured 5.5 s per call →
**1.8 GPU-h**, one day session. The 35b slowed after
871 DEB calls (D-78), so the run is split into
2 sessions, each restarting the 35b server and staying below that
count. It keeps the 35b's exploratory status and its differences from M1's conditions (D-78).

**E6b: a third model family** (neither Qwen nor Gemma). Purpose (reframed by the authors, 3 Nov): a third family for
E8's vote and for the family-affinity check of M2, which shares the generator's family; it is **not** the
stronger-judge evidence, which is E6a (the 35b) and E9 (frontier reference point, not approved). Selected on
the development split only by `docs/local_models/MODEL_SELECTION_PROTOCOL.md` Step 1 (fully GPU-resident at the
frozen context in 12 GB, schema-valid, thinking controllable) and the dev gates G-a/G-b; then J1/SC/DEB at S1, one
replicate. Costed at M1's measured time (23.4 s per
instance): **2.0 GPU-h** including the dev gate, one day session.

*Stopping rule, fixed in advance in the version-controlled decision log (both; the parameters are the D-78 rule's, scaled to each model):* stop the run, with no retry and no setting change, on any of: available RAM below
the model's gate at a check every 25 calls; median latency of the last 50 calls above 3× the model's feasibility
median; a server crash or a request with no response within 900 s; the session's time box. Report what completed.

*Hypotheses (written before any run):*
- **H6-1** (replication of H3a): with the new judge, ΔF1(DEB − SC) at S1 > 0.
- **H6-2**: with the new judge, MCC(DEB|S1) > 0 (95% bug-level CI excludes 0).
- Analysis: the committed `analyze.py` and R3 script, bug-level bootstrap, Holm over H6-1 and H6-2; M1 remains the
  confirmatory judge of the paper.

*D-entry draft (E6):* "E6 approved by the authors on <date>: <E6a | E6b with model tag and digest>, D1-test, S1,
J1/SC/DEB, 1 replicate, frozen prompts and decoding, own profile and log directories, stopping rule as above;
hypotheses H6-1 and H6-2 fixed now, before any call; nothing feeds back into M1's results."

## E7 — a second generator, or a contamination check

**E7a: second generator** from a third family (neither Qwen nor Gemma), selected on the dev split by the D-22 criteria;
585 generations at G's measured
16.6 s each plus re-judging with M1 →
**4.9 GPU-h** (judged size assumed equal to D1-test; execution runs on
CPU), one day session at the limit or one night session.

**E7b: GitBug-Java** (D3 of the Phase 2 design), up to 60 post-cutoff bugs →
**1.5 GPU-h**. Blocked: build reproduction needs Docker (X-05), which the host
does not have.

*Hypotheses (written before any run):*
- **H7-1** (E7a): removing the failure evidence lowers F1 for J1 on the new generator's tests (replicates A4).
- **H7-2** (E7a): MCC(DEB|S1) > 0 on the new generator's tests.
- **H7-3** (E7b, contamination diagnostic): MCC(DEB|S1) on GitBug-Java is not lower than on D1-test by more than the
  D1-test MDE; a larger drop would suggest the D1 result benefits from memorised Defects4J content.

*D-entry draft (E7):* "E7a/E7b approved on <date>; generator <tag, digest> selected on dev by D-22; labelling,
sampling (D-53, D-64 rules) and analysis unchanged; hypotheses H7-1 to H7-3 fixed before any generation."

## E8 — a JSTestCraft-style three-LLM vote under the equal budget

**VOTE3:** one J1-style call each from three families (M1, M2, and the E6b judge), majority vote. Its budget-matched
comparator **SC3** (majority of the first three SC samples) needs **no new calls** — it re-reads committed SC samples.
**VOTE5:** five calls split 2 + 2 + 1 across the three families, against SC and DEB at five calls.
**1.4 GPU-h** for both (the third judge costed at M1's J1 time; models
swap once per batch), one day session. This is a re-implementation in the spirit of JSTestCraft's vote, not their code.

*Hypotheses (written before any run):*
- **H8-1**: ΔF1(VOTE3 − SC3) > 0 at S1 (does family diversity beat repeated sampling at three calls?).
- **H8-2**: ΔF1(VOTE5 − SC) > 0 at S1, five calls each.
- **H8-3**: ΔF1(VOTE5 − DEB) ≠ 0 at S1, five calls each.
- Holm over H8-1 to H8-3. M2 shares the generator's family; the vote's self-preference risk is reported.

*D-entry draft (E8):* "E8 approved on <date>; VOTE3/VOTE5 defined as above with tie rule TF (as SC); SC3 from committed
SC samples; frozen J1 prompt for every family; hypotheses H8-1 to H8-3 fixed before any call."

## Order and total

Suggested order: E6b (needed by E8) → E8 → E6a → E7a; E7b only if Docker becomes available. Totals per proposal, all
zero API cost:

| Proposal | GPU-h | Fits one day session |
|---|---|---|
| E6a complete 35b | 1.8 | True |
| E6b second-family judge | 2.0 | True |
| E7a second generator | 4.9 | True |
| E7b GitBug-Java (blocked) | 1.5 | True |
| E8 three-LLM vote | 1.4 | True |
