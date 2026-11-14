# Defence deck restructure

Date: 2026-11-13. A plan for the authors to approve; `paper/DEFENSE_DECK.pptx` was not edited. Opus builds the
revised deck as a copy (`paper/DEFENSE_DECK_v2.pptx`) after approval. Numbers come from the numbers map, never
typed by hand.

## 1. The story in four sentences

1. Generated tests fail; the hard question is whether the test or the program is wrong, and we measured how well
   LLM judges answer it against execution ground truth.
2. Judges alone trade lost bugs against kept wrong tests along one curve, so we asked whether *executing* small
   variants of the program adds evidence, and a pilot said yes, strongly.
3. We registered that claim before any data existed and tested it on 104 unseen real bugs: one signal did not
   replicate, the other held with sharp limits.
4. We show what the surviving signal is, where it fails, and what we would and would not tell a practitioner.

The old headline (KUU and the cascade as the method) is removed. KUU appears once, as the baseline.
The deck leads with the confirmation, not the pilot.

## 2. Slide sequence (18 main slides, about 15 minutes)

| # | Slide | One message | Evidence on the slide |
|---|---|---|---|
| 1 | Title | question as title; authors; registration id | OSF kp79c, commit hash |
| 2 | The problem | a failing generated test is either the only evidence of a bug or noise; repair-first tools destroy the first kind | one example pair (a PF and a TF test) |
| 3 | What "ground truth" means here | PF = fails on buggy, passes on fixed; TF = fails identically on both | label rule diagram |
| 4 | Study 1: how good are LLM judges? | existing headline numbers; nothing survived correction | existing main table, reduced |
| 5 | Judge-only rules sit on one curve | voting, unanimity, debate, cascade are operating points; KUU is the keep-heavy end | existing rates figure; KUU marked "baseline" |
| 6 | Idea: ask the program, not another judge | run the failing test on single-edit variants of the method under test; two observables: *flip* and *decoupled* | schematic; "the executions are those of mutation-based fault localization; the question is different" |
| 7 | Pilot (exploratory) | flip 0.667 vs 0.155; decoupled 61 of 62 wrong; 22 bugs, labels known | pilot table with a large "exploratory" tag |
| 8 | Why we did not stop there | labels known, 22 bugs, one design amendment | three bullets; registration timeline |
| 9 | The registered confirmation: design | hypotheses C1–C4, frames F1, F2, control; sealing order with commit hashes; frozen engine | timeline graphic: registration → generation → labels sealed → probes → votes → analysis |
| 10 | Population | 2,223 calls → 572 scored failing tests (55 PF, 517 TF), 104 bugs, 21 with a PF test; planned 30–50 | flow table; the shortfall stated on the slide |
| 11 | **Result 1: flip did not replicate** | +0.028 [−0.137, 0.274]; right tests 25%, wrong tests 23%, control 22% | three bars with intervals; pilot's 0.51 marked as excluded |
| 12 | **Result 2: decoupling held, with limits** | +0.243 [0.114, 0.372], Holm p 0.0024; 135 of 136 flagged tests are wrong | forest plot: pooled, F1 (+0.04), F2 (+0.32) |
| 13 | Where it holds (exploratory) | 117 of 135 in two projects; without them +0.04 [−0.04, 0.11]; mostly exceptions raised outside the method | project bar chart; "exploratory" tag |
| 14 | Rules: inconclusive | KUU 1.000 / 0.316 / 0 bugs lost; KUU + CD 0.982 / 0.430 / 1 lost; Holm p 0.14; keep certificate: no support | rule table with bugs lost and upper bounds |
| 15 | What the surviving signal is | both lost bugs are edits the operators could not make; the ten-mutant minimum shields 19 right tests | two code snippets (`Codec_13`, `Math_59`), one line each |
| 16 | Exploratory extension (only after its run and interpretation review) | replace the whole method: is it entered, and does the failure change at all? ladder U / RI / WS / FS / ND; CD-U result. U is worded "no entry observed, throw-invariant", never "unreachable" | ladder chart; rule row; status sentence in full; shown as a descriptive ladder even if the criterion is not met |
| 17 | What we claim, and what we do not | two columns (section 4) | — |
| 18 | Limitations and next steps | one benchmark, one generator, 21 bugs, no label audit, e-Otter++ not reproduced; next: fresh registered test of the dependence check | list |

If slide 16 has no result by the deadline, replace it with "Planned: a direct dependence test", design only,
clearly marked as not run.

## 3. Backup slides

| # | Slide | Purpose |
|---|---|---|
| B1 | Registration details: what was registered, when, hashes, what counts against the method | "what exactly was preregistered?" |
| B2 | Power planning table and the realized 21 bugs | "was it underpowered?" |
| B3 | Control group: definition, matching, biases | "is the control defect-free?" |
| B4 | Registered secondary analyses | completeness |
| B5 | F1 and F2 definitions and their failure-type mix | "why do the frames differ?" |
| B6 | Positioning table: MUSE, Metallaxis, ProFL, e-Otter++, judge triage, pseudo-tested methods | "how is this different from X?" |
| B7 | Audit summary: what was recomputed and matched | "can we trust the numbers?" |
| B8 | Stage B: designed, not run, why | "why didn't you put the evidence in the prompt?" |
| B9 | e-Otter++-style baseline: why not run, what a fair version needs | "why no patch baseline?" |
| B10 | Evidence-status table for every result | confirmatory vs exploratory |
| B11 | Cost: probes about 3 s of CPU per test, no model; votes about 8 GPU-seconds per test | practicality |
| B12 | Per-project tables for flip and decoupling, pilot and confirmation | detail |

## 4. Claim slide (slide 17), exact content

**We claim**

- an execution-grounded measurement of LLM triage with lost bugs as an outcome;
- a registered result that a test-passing single edit is *not* evidence that the test is right;
- a registered result that a failure no single edit changes was a wrong test in 135 of 136 cases, in one sampling
  frame and mostly two projects;
- a base rate: 22–26% of failing generated tests can be made to pass by one small edit, whoever is at fault.

**We do not claim**

- a new triage method, or that the certificates are safe;
- that the decoupling effect generalises across frames or projects;
- that C3 is significant or that the keep certificate works;
- that the control methods are correct;
- novelty of the mechanism: the executions are those of MUSE, Metallaxis and ProFL;
- that the exploratory extension is preregistered or confirmed.

## 5. Rules for every slide

- Each result slide carries a corner tag: **registered**, **exploratory**, or **designed, not run**.
- The extension's slide carries, in full: "Exploratory. Protocol frozen internally in Git before the run. Not
  externally preregistered. Designed after the confirmation outcomes were known."
- No slide says "significant" for C3, "validated", "safe", "novel", "first" or "state of the art".
- Pooled C2 never appears without F1 and F2 beside it.
- Flip slides always show the control bar.
- Rule tables show bugs lost before balanced accuracy.

## 6. Likely committee questions and short answers

| Question | Answer |
|---|---|
| Your main hypothesis failed. What is the contribution? | The measurement, and a registered answer to a question the pilot got wrong. The field has positive pilot results of exactly this kind; a sealed test that says "no" for one signal and "yes, here, with these limits" for the other is the result |
| Was C1 really adequately powered with 21 bugs? | The classification assumed 30. The interval we got is as narrow as planned for 30 (±0.21), excludes the pilot's 0.51 and includes half of it. We say "did not replicate", not "no effect" |
| Why did the pilot show 0.51? | 22 bugs, labels known when the rules were written, and half of the flipping right tests came from one project that contributes no right test here |
| Is C2 just JacksonDatabind? | Largely: 117 of 135. Without the two Jackson projects the estimate is +0.04 with an interval that includes zero. The flag's precision held everywhere (135 of 136); how often it fires did not |
| Why do F1 and F2 differ? | F2 methods are those no bug-triggering test calls by name. Wrong tests there fail mostly with exceptions raised before or outside the method; in F1 they are 93% wrong assertions. Decoupling lives in the first kind |
| Isn't decoupled just "exception outside the method"? | That stack-trace rule would discard 6 right tests and 160 wrong ones; the flag discards 1 and 135 |
| Is the control group bug-free? | No. It is methods the patch did not change, in classes that needed a patch. It answers one question: how often a flip occurs away from the repaired method |
| C3 has p = 0.047. Why not call it supported? | Four hypotheses, one Holm family, adjusted p 0.14. And the gain came with a lost bug |
| How is this different from ProFL or MUSE? | Same executions. They assume the failing test is right and rank locations; we ask whether it is right |
| And from e-Otter++? | It uses LLM patches written from an issue report to pick among candidate tests, and never calls a test wrong. We have no issue report and we did not reproduce it. Its success and our null for blind edits are consistent |
| Why not put the probe report into the judge's prompt? | Designed before the confirmation, not run: two of its three lines describe flips, which turned out to carry no signal, and the third restates a rule that costs nothing to apply outside the model |
| Is the extension preregistered? | No. Its protocol was committed before it ran, and it was designed after we saw the outcomes. It is exploratory and labelled so |
| Did the models see Defects4J in training? | Probably. The probe uses no model; the judges and the generator may have. Stated as a threat |
| What would you tell a practitioner today? | Do not use "an edit makes it pass" as a reason to keep a test. A failure that does not depend on the method under test is very likely a wrong test, but expect that check to fire unevenly, and budget for an occasional lost bug until it is tested on fresh data |
| What next? | A registered test of the dependence check on tests from a second generator, a label audit, and a fair patch-based baseline |
