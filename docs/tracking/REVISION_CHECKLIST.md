# Revision checklist (review response pass, started 2026-11-09)

Rows map to `REVIEWER_RESPONSE_MATRIX.md`. Each analysis has a dated DECISIONS entry committed before it runs.

## Phase 0 — audit and tracking
- [x] Repository state: HEAD 27c6b25, clean tree (live server log only); counts verified (matrix header)
- [x] Generators vs judges verified (one generator, G; judges M1, M2, E6b, NG, 35B, Sonnet)
- [x] Tracking files created (this file, the matrix)
- [x] Compute estimate (below)

### Compute estimate (from logged latencies, 2026-11-09; deadline 2026-11-12 23:59, D-58)
| Run | Calls | Measured basis | Estimate |
|---|---|---|---|
| WP2.1 176 TF × M1, M2, E6b, NG (J1, S1) | 704 | J1 mean 2.07 / 2.10 / 3.35 / 1.35 s per call | ~26 min + 4 server starts ≈ 35 min |
| WP2.2 M1 J1 temperature 0 | 189 | 1.9 s | ~6 min |
| WP2.3 M1 thinking J1 | 189 | unknown; a 3-instance probe on dev fixes it | 4–6 h if ~6k thinking tokens at ~70 tok/s |
| WP2.4 M1 DEB × 5 new replicates | 945 decisions, 4,725 calls | 13.3 s per DEB instance | ~3.5 h |
Disk: 349 GB free; call logs add < 1 GB. RAM 31.4 GiB total, 15.4 available; the D-109 stopping rule (RAM < 4.0 GiB at a 25-call
check, median of the last 50 calls > 3 × Step 1 median, crash or 900 s hang, deadline) stays armed unchanged; no retry.
GPU: RTX 5070 Ti Laptop, 12,227 MiB; models stay fully GPU-resident as in their profiles. WP2.3 needs a larger context than
the frozen 8,192 (see D-entry) and runs only if the model stays GPU-resident with ≥ 0.5 GiB free VRAM.

## Phase 1 — zero-call analyses
- [x] WP1.1 prevalence-independent metrics (+ invalid-as-keep sensitivity, false alarms per kept PF)
- [x] WP1.2 common-scale trade-off figure
- [x] WP1.3 ranking, AUROC/AUPRC, top-k test and bug recall, reweighting
- [x] WP1.4 LOPO logistic stacker and non-LLM classifier; D1→D2 transfer
- [x] WP1.5 k-of-3 curves
- [x] WP1.6 risk-targeted threshold (conformal check)
- [x] WP1.7 cross-generation consensus
- [x] WP1.8 sample-size planning
- [x] WP1.9 statistical integrity checks; mixed-model reassessment
- [x] WP1.10 leakage-guard selection effect (D2)
- [x] WP1.11 label-noise sensitivity
- [x] Unit tests for every new metric

## Phase 2 — local runs
- [x] WP2.1 complete held-out TF judging
- [x] WP2.2 greedy J1
- [x] WP2.3 thinking J1 — done (D-129): BA 0.771, not token-matched (0.74×)
- [x] WP2.4 five DEB replicates — done (D-129)
- [x] WP2.5 judge gate table

## Phase 3 — plans only (no paid call, no registration, no recruitment)
- [x] Sonnet factorial preregistration draft + cost estimate
- [x] OSF-ready RQ4 replication outline
- [x] JOURNAL_FOLLOWUP_PLAN.md

## Manuscript structure recommendation (M11; no file split, no radical restructure)
**Recommendation: keep one paper for the 15 November submission; split only for the journal version, after the RQ4
replication.** Reasons: (1) the evaluation (RQ1–RQ3) and the method (RQ4) answer one problem, bug-revealing tests being
discarded, and the method's motivation is the evaluation's finding that single judges lose about half of them;
(2) as it stands RQ4 rests on tests fixed only in the repository and chosen after earlier results, which is too thin
for a stand-alone method paper; (3) the evaluation alone, with a weak judge and inconclusive confirmatory tests, would
lose its most useful finding. For the journal: paper A, an execution-grounded benchmark and evaluation of LLM failure
triage (RQ1–RQ3 with a gate-passing judge, `PREREG_SONNET_FACTORIAL.md`); paper B, KUU and escalation with the
externally registered replication (`OSF_PREREG_RQ4_OUTLINE.md`). What was done now: the main text names the core problem
first (unchanged introduction) and the Discussion states the one-problem rationale; the draft before this pass is
recoverable at commit 27c6b25. The authors decide.

## Page budget (author decision)
The main text now ends on p13 (p12 before this pass): Figure 3 (rates) stands beside Figure 2 until the authors choose one, as asked; moving the unchosen one to Appendix G recovers most of the page. Four main-text tables (E3, confirmatory, quantitative comparison, ablations) moved to Appendix B to make room; the main text keeps each section's key values and points to the tables, which hold the full rows. The authors may prefer to move a figure instead.

## GPU time used
WP2.1 1,597 s (M1 358, M2 430, E6b 573, NG 236); WP2.2 414 s; probe 193 s; WP2.4 12,274 s; WP2.3 13,184 s: about 7.6 h of run wall time, no run interrupted, no stopping-rule trip.

## Phase 4/5 — documents, verification, commits
- [x] Manuscript cleanup M1–M13
- [x] Numbers map, paper, report, study guide, deck backup slide
- [x] Full test suite, numbers check, rebuilds, visual inspection
- [x] Final report

## Pass 2 (authors' decisions of 2026-11-10; GPU work by 2026-11-12 23:59)
Author decisions applied: one paper now (split is a journal decision); the rates figure becomes the main-text trade-off
figure and the discarded-vs-lost figure moves to Appendix G; main text back to p12; the thinking result is tested like
KUU (D2 confirmation with hypotheses committed in the decision log before the calls, D1 replicates); Sonnet, OSF and raters
stay plans; authors fill the TODOs and click through the deck. No push.

### WP1 — thinking-judge follow-up (local GPU)
- [x] 1. GPU estimate from the first thinking run's logs, recorded (and run order 2 → 3 → 4 if anything must be cut) — D-130: 69.4 s/instance, ≈ 14.5 h in all; the dev run took 3,785 s for 62 calls (61.0 s/call, measured)
- [x] 2. Development gate: thinking M1 J1 on the 63-instance dev pilot; G-a…G-d as originally applied — **FAILED** (`results/revision/runs/REV_THINK_DEV_M1/dev_gates.json`): G-a 96.8% valid < 98% (2 of 62 calls cut off by the output cap); G-b pass; G-c pass; G-d J1 F1 0.312 < R0 0.642 (thinking-disabled M1 was 0.350). Thinking M1 fails the same gate M1 failed. A gate check, not a research result; D2 and the D1 replicates run as D-130 fixed.
- [x] 3. D2 confirmation: HT-1 (ΔMCC vs M1 DEB > 0) and HT-2 (fewer PF lost than M1 DEB), one Holm family, committed before any D2 call
- [x] 4. D1 replicates: two more runs, three in all, beside DEB's eight-run spread
  - **Paused 2026-11-10 at the authors' request** (manual `logs/STOP`, not a safety stop): REV_THINK_D1R2_M1 has 76 of
    193 decisions, REV_THINK_D1R3_M1 not started; `finish` restored the frozen server (session check exit 0). To resume:
    delete `logs/STOP`, then `revision_runs.py begin`, `run REV_THINK_D1R2_M1 REV_THINK_D1R3_M1`, `finish`; the runner
    skips decisions already written. GPU deadline 2026-11-12 23:59.
  - **Resumed 2026-11-10 20:45 local** (`logs/runs/revision_batch4.log`; 117 to go, 76 already done). The laptop lost
    mains power and slept (no reboot: last boot 2026-11-03); the processes resumed on wake. One call spanned the sleep
    (key `8df2d8dd…`, 5,820 s wall time, `finish_reason` stop, 3,326 output tokens, under the cap): its seeded output
    is unaffected, so it stands. The D-109 rule uses the median latency over a window, so one long call did not trip it;
    nothing was relaxed. GPU-time figures for this run are wall time and include the sleep.
- [x] 5. Output-cap sensitivity (capped as TF / as keep / excluded) for every thinking run
- [x] 6. Token figure explained (prompt + eval counts incl. thinking; not token-matched)

### WP2 — claim wording (after WP1; rule fixed in D-130 before the D2 result)
- [x] 7. Branch chosen by the rule (A; D-131); each affected sentence quoted with its replacement below, before editing
- [x] 8. Contributions' findings bullet scoped to thinking-disabled small judges (both branches)

**WP2 drafts, written 2026-11-10 while REV_THINK_D2_M1 was running and before any of its decisions were read.**
Numbers in ⟨…⟩ are filled from `results/revision/think_followup.json` through the numbers map; the wording is fixed here.
The development gate had already failed (item 2), and both branches say so where the thinking result appears.

*Both branches (scope the planned-arm findings to thinking disabled):*
- **Abstract.** Old: "…were judged by a local 9B model under a one-shot judge, five-sample self-consistency and a
  five-call debate, against keep-all, discard-all and rule-based baselines at three specification levels."
  New: "…were judged by a local 9B model, with its thinking mode disabled, under a one-shot judge, five-sample
  self-consistency and a five-call debate, against keep-all, discard-all and rule-based baselines at three specification
  levels."
- **Contributions, findings bullet.** Old: "\emph{Findings:} with small judges the failure evidence, not the
  specification or the architecture, carries the signal; equal-budget debate does not beat self-consistency; a frontier
  reference judge is far more accurate and run-to-run stable."
  New: "\emph{Findings:} for small judges with thinking disabled, the failure evidence, not the specification or the
  architecture, carries the signal and equal-budget debate does not beat self-consistency; a frontier reference judge is
  far more accurate and run-to-run stable."
- **Conclusion, first sentence.** Old: "Against execution-based buggy/fixed labels, the best arm, DEB, reached F1 …"
  New: "Against execution-based buggy/fixed labels and with thinking disabled, the best planned arm, DEB, reached F1 …"
- **Threats (Deviations), last thinking sentence.** Old: "All planned arms ran with thinking disabled; with thinking
  enabled, one exploratory run of the same 9B judge reached balanced accuracy ⟨0.771⟩ and lost ⟨7⟩ of ⟨60⟩
  bug-revealing tests on fewer tokens than debate (Appendix G), so the architecture and specification results describe
  thinking-disabled judges only."
  New (branch A): "All planned arms ran with thinking disabled, so the architecture and specification results describe
  thinking-disabled judges only; the thinking-enabled judge still failed the development gate (F1 ⟨…⟩ against R0's
  ⟨…⟩) and was not token-matched to debate (Appendix G)."
  New (branch B): "All planned arms ran with thinking disabled, so the architecture and specification results describe
  thinking-disabled judges only. With thinking enabled the same 9B judge reached balanced accuracy ⟨min⟩–⟨max⟩ over
  three D1-test runs (exploratory; found on these data) but failed the development gate (F1 ⟨…⟩ against R0's ⟨…⟩), and
  on D2 the hypotheses committed before its calls ⟨were not both supported: HT-1 …, HT-2 …⟩ (Appendix G); it was not
  token-matched to debate."

*Branch A only (HT-1 and HT-2 both supported after Holm):*
- **Abstract, new sentence after the Holm sentence:** "With its thinking mode enabled, the same 9B judge outperformed
  every planned arm: found on the real faults and confirmed on seeded faults with hypotheses committed in the decision
  log before the calls (MCC ⟨…⟩ against debate's ⟨…⟩; ⟨…⟩ against ⟨…⟩ bug-revealing tests lost)."
- **Discussion, new paragraph "Test-time reasoning versus orchestration.":** one judge that reasons before it answers
  beat five-call debate and self-consistency at lower token use, so for small judges the gain RQ3 looked for in
  orchestration came instead from reasoning inside one call; it still failed its development gate, so it is not shown
  to be good enough to replace keep-all on its own.
- **RQ4, one sentence:** whether KUU adds protection beyond the thinking judge, from `kuu_vs_thinking` (PF tests the
  thinking judge loses that KUU keeps, and the reverse).

*Branch B only (either hypothesis unsupported):*
- **Discussion, one sentence in "Debate and Javadoc: inconclusive.":** "Thinking-enabled M1 did better than every
  planned arm on D1-test (balanced accuracy ⟨min⟩–⟨max⟩ over three runs) but this was found on those data and was not
  confirmed on D2 (Appendix G), so it is exploratory."
- No abstract sentence.

**WP2 final text (branch A), recorded 2026-11-10 after the D2 result (D-131) and before the paper was edited.**
Rule outcome: HT-1 (ΔMCC +0.267, 95% CI [0.146, 0.391], p_Holm 0.0004) and HT-2 (8 vs 56 PF tests lost, Δ −48,
[−65, −32], p_Holm 0.0004) are both supported, so branch A applies. The "both branches" scoping edits above are used
exactly as drafted. Three changes from the branch-A draft, each made because a check of the draft against the results
showed it would say more than the data do:
- *"every planned arm" → "every planned arm run with that judge".* The second judge M2 (12B, the generator's family)
  reached debate MCC 0.571 on D1-test, above thinking M1's 0.513, so the unscoped phrase is false. Against M1's own
  planned arms it holds on both sets (D2 MCC 0.659 vs J1 0.301, SC 0.383, DEB 0.392, DEB at S2 0.463; D1 0.513 vs a
  best of 0.311, DEB at S0), and the D1 claim is re-checked against the three-run range when the replicates finish.
- *Abstract placement:* the sentence goes after "Single-judge arms discarded about half of the bug-revealing tests."
  rather than straight after the Holm sentence, so that the ablation sentence's "every arm" still means the planned arms.
  It adds the gate failure in one clause, because a reader of the abstract alone would otherwise take the judge as
  validated.
- *Conclusion:* the rule names the abstract; the Conclusion mirrors it in one sentence so the two do not disagree.

Final sentences (old → new; ⟨…⟩ are `\V{tk:…}` keys):
- **Abstract**, scoping: as drafted above. New sentence after "…Single-judge arms discarded about half of the
  bug-revealing tests.": "With its thinking mode enabled, the same 9B judge did better than every planned arm run with
  it: found on the real faults and confirmed on seeded faults with hypotheses committed in the decision log before the
  calls (MCC ⟨0.659⟩ against debate's ⟨0.392⟩; ⟨8⟩ against ⟨56⟩ bug-revealing tests lost), though it failed the
  development gate it was held to."
- **Contributions, findings bullet**: as drafted above.
- **RQ4**, new sentence after the KUU/TAU sentence ("…KUU reaches that point with no tuning."): "Against the
  thinking-enabled judge (Appendix G), KUU still adds protection: of D2's bug-revealing tests, ⟨6⟩ lost by that judge
  are kept by KUU and ⟨2⟩ the reverse, at a cost of removing ⟨27%⟩ of test faults against its ⟨67%⟩."
- **Discussion**, new paragraph after "Debate and Javadoc: inconclusive.": "\paragraph{Test-time reasoning versus
  orchestration.} With thinking enabled, one M1 call beat M1's five-call debate on D2 (ΔMCC ⟨+0.267⟩ ⟨[0.146, 0.391]⟩,
  p_Holm ⟨0.0004⟩; ⟨8⟩ against ⟨56⟩ bug-revealing tests lost, whichever way the ⟨9⟩ outputs cut off by the cap are
  scored) and every planned M1 arm on D1-test in each of three runs (balanced accuracy ⟨min⟩–⟨max⟩), on fewer tokens
  per instance than debate (⟨mean⟩ against ⟨9,188⟩; not token-matched). For small judges, then, the gain RQ3 looked
  for in orchestration came instead from reasoning inside one call. It is not a validated judge: it failed its
  development gate (F1 ⟨0.312⟩ against R0's ⟨0.642⟩ on ⟨55⟩ pilot instances), the 12B M2's debate scored higher on
  D1-test (MCC ⟨0.571⟩ against a three-run mean of ⟨…⟩), and it lost more bug-revealing tests than KUU, so it is a
  stronger classifier, not a safety rule (Table G-think)."
- **Threats (Deviations)**: old as quoted above; new = the branch-A draft, filled: "All planned arms ran with thinking
  disabled, so the architecture and specification results describe thinking-disabled judges only; the
  thinking-enabled judge still failed the development gate (F1 ⟨0.312⟩ against R0's ⟨0.642⟩) and was not token-matched
  to debate (Appendix G)."
- **Conclusion**: first sentence scoped as drafted; new second sentence after "…the failure evidence carried the
  signal.": "With thinking enabled, the same judge did better than all of its planned arms, confirmed on D2 (MCC ⟨0.659⟩
  against debate's ⟨0.392⟩), though it failed its development gate."

**Correction after the D1 replicates (2026-11-11, D-131 (3)).** Every thinking run is above every planned M1 arm (BA 0.771–0.817, MCC 0.513–0.601 against DEB's eight-run maxima 0.710 and 0.433), so the scoped claims stand. One Discussion clause changes: old "the 12B M2's debate scored higher on D1-test (MCC ⟨0.571⟩ against a three-run mean of ⟨0.556⟩)" → new "the 12B M2's debate scored about as high on D1-test (MCC ⟨0.571⟩ against ⟨0.513⟩–⟨0.601⟩ over three runs)", because one run exceeded it; the same change in report §7c and Q&A 30.

### WP3 — page budget and documents
- [x] 9. Rates figure in the main text, discarded-vs-lost figure to Appendix G; main text ends p12 (checked in the built PDF) — 26 pp; Conclusion, Acknowledgements and the start of the Declarations on p12; "Improvement analysis" and "Rates, ranking and trained baselines" moved verbatim to Appendix B with pointers; Table G8 on p23
- [x] 10. Phase 3 report: WP1 results (§7c)
- [x] 11. Study guide: thinking-judge decision entry (five-part format) (entry 28)
- [x] 12. Deck: trade-off slide figure choice recorded; backup Q&A "Why not just let one judge think?"; numbers changed only where they change — the rates figure reads clearly at slide size, so the trade-off slide (15) uses it, with the thinking point; Q&A 30 is backup slide 56; the only other change is the thinking line and notes of backup slide 26

### WP4 — independent check and finish
- [x] 13. Read-only subagent check (a)–(e); findings fixed or recorded
  Independent read-only check, 2026-11-11 (a fresh agent given only the built PDF, NUMBERS_MAP and `results/`).
  *(a) numbers in abstract/intro/contributions/conclusion:* ~40 checked against map and source, no mismatch. Notes:
  the Conclusion's "best planned arm" is best at S1 only (DEB at S0 has F1 0.550) → "at S1" added. The map's source path
  for `tk:d2:descriptive:ThinkingM1J1` drops the spaces of the JSON key "Thinking M1 J1" (the resolver ignores spaces);
  values are right, recorded, not changed.
  *(b) claims vs the thinking results:* "better than every planned arm run with it" verified at every level on both sets.
  Fixed: three unscoped claims ("DEB at S2 is the best D2 cell", "DEB has the highest MCC in all four dataset–judge
  combinations", "Single-judge arms discard about half…") now say thinking-disabled; the G-a failure (96.8% valid) now
  stands beside G-d in the Discussion and threats; "8 against 56 … whichever way the capped outputs are scored" now says
  the verdict holds (the counts move to 5 vs 56 / 5 vs 55); the traceability row for the local runs reads X/F, since the
  D2 confirmation is a fixed-in-advance family; abstract and Conclusion say the D2 confirmation was against debate.
  Recorded, not changed: 0.3125 prints as 0.312 under the formatter's round-half-even rule used for every number.
  *(c) "pre-registered" for decision-log items:* five in the paper (fallback ladder, E6b/E8 hypotheses, E6b candidates,
  E9b D2 reads, Table E2 header) → "fixed in advance"; the numbers-map category label too. Not changed, for the authors:
  the deck says "five pre-registered tests" (main slide, kicker area of the results slide) and "a frozen, pre-registered
  plan" (backup); the authors' rule limits deck edits to changed numbers, so these are listed in the final report.
  *(d) decision ids in main-text prose:* none on pp1–12; D-84/D-108 appear in the AI-use declaration (back matter), kept.
  *(e) course leftovers:* five "Phase 2" uses (sample rule, model replacement, yield floor, Appendix A title, Appendix B
  fairness) → "the original design". Left for the authors: the instructor-feedback TODO and the Acknowledgements TODO.
  "Comparison with Base Papers" / "ten base papers" read as rubric phrasing; kept, since the section is required.
- [x] 14. Unit tests (incl. output-cap scoring variants), numbers check, full suite, full rebuild, every changed page and slide looked at — 346 passed (three D-67 tests now pin the clock); `--check` 24/24; paper, report PDF, LaTeX bundle, study guide, deck rebuilt; pp. 1, 11–13, 23 and slides 15, 26, 56 looked at
- [x] 15. Logical commits referencing decisions; no push

## Pass 3 (authors' decisions of 2026-11-11; last pass before the 15 Nov submission)
Zero model calls; no push, no deletion; frozen and confirmatory outputs untouched. Anything computed on D2 now is post hoc.

### WP1 — fully local cascade (post hoc, zero calls)
- [x] 1. Decision entry fixing the one rule committed before computing — D-132, commit `abf0e8b` (with the script and its unit tests, before any vote was read)
- [x] 2. F1, MCC, BA, TPR, TNR, PF lost, bugs lost, share discarded beside KUU, thinking J1, Sonnet cascade, Sonnet DEB;
      D1-test per thinking run and range — `results/revision/local_cascade.json`. D2: fully local BA 0.765, MCC 0.593,
      F1 0.841, 6 PF lost, 0 bugs lost, 27% discarded; thinking alone 0.810 / 0.659 / 0.864, 8, 2; Sonnet cascade
      0.826 / 0.666 / 0.863, 15, 2; local − Sonnet cascade ΔBA −0.061 [−0.124, −0.004], ΔMCC −0.073 [−0.186, 0.034].
      D1-test: fully local BA 0.740–0.770, MCC 0.471–0.528, 1–3 PF lost over the three runs; Sonnet cascade 0.810 / 0.595,
      10.3 lost. No confirmed claim is undercut (H12-1 is cascade vs KUU; non-inferiority to Sonnet was never shown).
- [x] 3. Appendix G table and one RQ4 sentence (post hoc; journal confirmation); main text still ends p12 — Table G9
      (p23); sentence "Fully local (post hoc)." ends the RQ4 escalation paragraph; journal row J-L1; Conclusion and
      Acknowledgements on p12 (Declarations moved to p13), no other wording shortened
- [x] 4. Any cascade / local-first sentence the result contradicts quoted with the number and scoped. Contradicted
      (by the thinking judge, D-131, and the fully local cascade, D-132; both local): (i) DEFENSE_QA Q28 "No local rule
      reaches that region on its own." and (ii) STUDY_GUIDE decision 22 "The cascade reaches the frontier AI's region;
      no local rule does on its own." — on D2 the thinking judge discards 32% and loses 8, the fully local cascade 27%
      and 6, beside the Sonnet cascade's 38% and 15 and Sonnet DEB's 42% and 13. Both now say "no thinking-disabled
      local rule" and name the two local points. Checked and NOT contradicted (they describe the Sonnet cascade only):
      paper §3 "local-first: only escalated failures leave the machine"; RQ4 "the other half of the failures never
      left the machine" and "Escalation thus recovers most of the frontier judge's accuracy, not all of it, while
      keeping half of the evidence local"; Conclusion "with half of the failures kept local"; deck notes "the other
      half never left the machine". The fully local cascade loses accuracy against the Sonnet cascade (ΔBA −0.061), so
      "escalation recovers most of the frontier judge's accuracy" still holds.

### WP2 — one story across paper, deck and study guide
- [x] 5. Terminology: "fixed in advance in the version-controlled decision log", never "pre-registered" (unless quoting
      the course design); every change listed below
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "with hypotheses committed in the decision log before the calls (MCC" → "with hypotheses fixed in advance in the version-controlled decision log (MCC"
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "Tested once on seeded faults with hypotheses fixed before its calls," → "Tested once on seeded faults with hypotheses fixed in advance,"
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "its hypotheses were committed to the repository before any of their calls, which is internal provenance, not an external preregistration" → "its hypotheses were fixed in advance in the version-controlled decision log before any of their calls, which is internal provenance, not an external preregistration"
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "tested on D2 with hypotheses fixed before its calls," → "tested on D2 with hypotheses fixed in advance,"
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "The cascade and its hypotheses were committed to the repository before any frontier call on D2," → "The cascade and its hypotheses were fixed in advance in the version-controlled decision log before any frontier call on D2,"
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "was selected by pre-specified criteria:" → "was selected by criteria fixed in advance:"
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "A hypothesis described as fixed in advance was written into the repository's decision log before its calls;" → "A hypothesis described as fixed in advance was written into the version-controlled decision log before its calls;"
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "tested once on unseen D2 with its hypotheses fixed before the calls." → "tested once on unseen D2 with its hypotheses fixed in advance."
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "both hypotheses fixed before its calls are supported" → "both hypotheses fixed in advance are supported"
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "the pre-set criterion is not met" → "the criterion fixed in advance is not met" (×2)
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "(pre-set rule)" → "(rule fixed in advance)"
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "All were written into the repository's decision log (D-106) before they were computed," → "All were fixed in advance in the version-controlled decision log (D-106) before they were computed,"
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "Every analysis here was written into the repository's decision log before it was computed" → "Every analysis here was fixed in advance in the version-controlled decision log before it was computed"
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "whose hypotheses were committed in the decision log before its calls;" → "whose hypotheses were fixed in advance in the version-controlled decision log;"
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "and the wording rule for this paper were committed in the decision log before the calls." → "and the wording rule for this paper were fixed in advance in the version-controlled decision log."
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "One rule, fixed in the decision log before it was computed;" → "One rule, fixed in advance in the version-controlled decision log;"
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "F fixed in the decision log before its calls (not externally registered)" → "F fixed in advance in the version-controlled decision log (not externally registered)"
  - `docs/phase3/PHASE3_REPORT.src.md`: "(D-109; committed before any call)" → "(D-109; fixed in advance)"
  - `docs/phase3/PHASE3_REPORT.src.md`: "Each was written into `docs/tracking/DECISIONS.md` before it was computed" → "Each was fixed in advance in the version-controlled decision log (`docs/tracking/DECISIONS.md`) before it was computed"
  - `docs/phase3/PHASE3_REPORT.src.md`: "with two hypotheses committed in the decision log before" → "with two hypotheses fixed in advance in the version-controlled decision log, before"
  - `docs/paper/src/STUDY_GUIDE.src.md`: "**None of the five pre-registered tests reached significance.**" → "**None of the five tests fixed in advance reached significance.**"
  - `docs/paper/src/STUDY_GUIDE.src.md`: "Re-running the pre-registered tests on MCC" → "Re-running the tests fixed in advance on MCC"
  - `docs/paper/src/STUDY_GUIDE.src.md`: "F1 stayed the registered primary metric" → "F1 stayed the primary metric fixed in advance"
  - `docs/paper/src/STUDY_GUIDE.src.md`: "fixed in advance on D2 (committed to our repository, not registered externally)" → "fixed in advance in the version-controlled decision log on D2 (not registered externally)"
  - `docs/paper/src/STUDY_GUIDE.src.md`: "Each RQ4 test was committed before the calls it uses," → "Each RQ4 test was fixed in advance in the version-controlled decision log before the calls it uses,"
  - `docs/paper/src/STUDY_GUIDE.src.md`: "two hypotheses written into the decision log before any D2 call" → "two hypotheses fixed in advance in the version-controlled decision log before any D2 call"
  - `docs/paper/src/STUDY_GUIDE.src.md`: "| **Pre-registered** | Written down before the data were seen. Here: committed to our repository first (internal), not registered externally. |" → "| **Fixed in advance** | Written into the version-controlled decision log (`docs/tracking/DECISIONS.md`, git history) before the data were seen: internal provenance, not an external registration, so we never call it pre-registered. |"
  - `docs/paper/src/DEFENSE_QA.src.md`: "F1 is kept because the design pre-registered it." → "F1 is kept because the original design fixed it in advance."
  - `docs/paper/src/DEFENSE_QA.src.md`: "its tests were committed to the repository before any of their calls (D-95, D-105, D-109)," → "its tests were fixed in advance in the version-controlled decision log before any of their calls (D-95, D-105, D-109),"
  - `docs/paper/src/DEFENSE_QA.src.md`: "with hypotheses written into the decision log before the calls (D-130, D-131)." → "with hypotheses fixed in advance in the version-controlled decision log (D-130, D-131)."
  - `docs/paper/src/DEFENSE_DECK.src.md`: "term: Pre-registered / fixed in advance | the plan and its tests written down before the data were looked at; for our rule, committed to our own repository, not an external registry" → "term: Fixed in advance | the plan and its tests written into our version-controlled decision log before the data were looked at; internal provenance, not an external registry"
  - `docs/paper/src/DEFENSE_DECK.src.md`: "every test for it was written down and committed before the data it uses were collected." → "every test for it was fixed in advance in the version-controlled decision log before the data it uses were collected."
  - `docs/paper/src/DEFENSE_DECK.src.md`: "None of our five pre-registered tests was significant;" → "None of our five tests fixed in advance was significant;"
  - `docs/paper/src/DEFENSE_DECK.src.md`: "a frozen, pre-registered plan;" → "a frozen plan, fixed in advance in the version-controlled decision log;"
  - `docs/paper/src/DEFENSE_DECK.src.md`: "title: The tests on seeded bugs, fixed before their calls," → "title: The tests on seeded bugs, fixed in advance,"
  - `docs/paper/src/DEFENSE_DECK.src.md`: "All six were committed to our repository before the calls they use," → "All six were fixed in advance in the version-controlled decision log before the calls they use,"
  - `docs/paper/src/DEFENSE_DECK.src.md`: "tested with two hypotheses committed before its calls" → "tested with two hypotheses fixed in advance"
  - `paper/PHASE4_RESEARCH_PAPER.tex`: "were fixed in D-105 and committed before any E9b call;" → "were fixed in advance in the version-controlled decision log (D-105) before any E9b call;"
  - `docs/phase3/PHASE3_REPORT.src.md`: "Its tests were committed to the repository before any of their calls" → "Its tests were fixed in advance in the version-controlled decision log before any of their calls"
  - `docs/phase3/PHASE3_REPORT.src.md`: "*Error diversity, pre-specified.*" → "*Error diversity, fixed in advance.*"
  - `docs/phase3/PHASE3_REPORT.src.md`: "the pre-set criterion is not met" → "the criterion fixed in advance is not met"
  - `docs/paper/src/STUDY_GUIDE.src.md`: "it passed the pre-set bars on the development split" → "it passed the bars fixed in advance on the development split"
  - `docs/paper/src/STUDY_GUIDE.src.md`: "the choice followed the pre-set bars." → "the choice followed the bars fixed in advance."
  - `docs/paper/src/STUDY_GUIDE.src.md`: "| A pre-set pass/fail check a model must meet on the dev split. |" → "| A pass/fail check, fixed in advance, that a model must meet on the dev split. |"
  - `docs/paper/src/DEFENSE_DECK.src.md`: "No; it was committed before the frontier AI saw a single seeded bug." → "No; it was fixed in advance in the version-controlled decision log before the frontier AI saw a single seeded bug."
  - `docs/paper/src/SESSION_CHECKLISTS.src.md`: "candidates in the pre-registered D-82 order" → "candidates in the D-82 order, fixed in advance in the version-controlled decision log"
  - `docs/paper/src/EXTERNAL_SUBMISSION_PLAN.src.md`: "*Pre-registered stopping rule (both;" → "*Stopping rule, fixed in advance in the version-controlled decision log (both;"
  - Kept on purpose: disclaimers that name what the provenance is NOT ("not an external, time-stamped preregistration", "not an external registration", "not externally registered"), plans for a future external registration ("externally registered replication", OSF), and DEFENSE_QA's "registered" for a model candidate registered in the run profile (no hypothesis).
- [x] 6. Deck: thinking slide after the debate slide; findings and takeaways slides updated; backup 56 kept; local
      cascade one-line note — new slide 11 "Letting one judge reason first helped more than debate or voting, but it
      still fails its quality gate" (key number 0.659 vs 0.392, Why box); slide 22 findings card and slide 23 takeaway 4
      rewritten; slide 19 (cascade on unseen bugs) carries the fully local line; slide 21 small-judges limit scoped to
      thinking off; slide 12 notes and slide 8 notes adjusted; Q&A 30 is now backup slide 57
- [x] 7. Study guide: Part 1 story, thinking decision in five parts, glossary "thinking mode" — the thinking decision is
      entry 28 (the prompt's "decision 24" is the rates entry), already five-part; entry 27 gained its Rejected part;
      new five-part entry 29 for D-132; Part 1 findings 1 and 4 scoped to thinking off, finding 6 and the fully local
      bullet added

### WP3 — defense preparation
- [x] 8. Eight questions in DEFENSE_QA and the study guide, two to four sentences, each claim cited — DEFENSE_QA 31–38
      (backup slides 58–65) and study guide Part 2b, same text; Q1's reason is recorded in
      `docs/local_models/METHODOLOGY_CHANGE_IMPACT.md` L-8 and the selection protocol, not in the decision log (said so);
      Q4 and Q6 report untested work, now journal rows J-T1 and J-T2
- [x] 9. `docs/paper/SUBMISSION_TODO.md` with every author TODO (file and line or slide), unfilled — 10 TODOs (8 paper,
      2 report), the deck click-through, and three things that are not author TODOs

### WP4 — check and freeze
- [x] 10. Read-only subagent check of paper, deck, study guide, numbers map; findings fixed or recorded
  Fresh read-only agent, 2026-11-11, given the built paper, the deck (text and notes), the study guide and the numbers map.
  *(a) numbers:* ~135 checked; none differs from NUMBERS_MAP. Fixed: guide Part 1 finding 4 said "real bugs" for
  bug-revealing tests; deck slide 13 title said the three-family vote beat "any one" judge (M2 alone lost fewer, D1 post
  hoc) → "than our main judge's debate or voting"; Q&A 2 said H6-2 was the only later hypothesis supported → lists every
  later one (H6-2, H10, H12-1, H13, HT) and says most are sanity or safety checks; Q&A 32 / guide Q2 gate difference
  now says it is paired on the instances both scored (−0.315, not 0.312 − 0.642).
  *(b) stronger than the paper:* fixed — slide 11 kicker and slide 22 findings card now say "confirmed against debate"
  (the comparison with voting is descriptive, matching the paper's "did better than every planned arm") and slide 22
  carries the gate failure; guide finding 6 adds "confirmed against debate; not token-matched"; Q&A 23 "confirmatory"
  → "a test fixed in advance (status F, not part of the original confirmatory family)"; Q&A 1 "evidence findings,
  which hold within each judge" → measured for M1 with thinking off; "any three families that disagree supply the veto"
  (slide 17 notes, guide entry 21) → "the panel without it kept the protection too"; Q&A 27 "the protection comes from"
  → "is consistent with"; "no AI can have memorised" (slide 4, slide 12, guide finding 5, entry 11) → "seen as bugs",
  with the original-code caveat; slide 12 title "the small judge is the limit, not the method" → "points to … as the
  limit", notes "the method works" → "debate can help"; slide 9 notes and guide finding 3 regain "exploratory, one
  replicate" and only the one-shot and voting judges fall to chance; guide header no longer says every decision came
  before the data (KUU and D-132 are post hoc); slide 15 kicker "Proof" → "Tested"; slide 17 Llama miss rate marked
  post hoc. Recorded, not changed: slide 10 title "Debate is no better than majority voting" matches the paper's own
  contribution bullet ("does not beat") and is not contradicted by the thinking judge.
  *(c) "pre-registered":* none claimed anywhere; the paper's three and the glossary's one are disclaimers.
  *(d) unscoped "best judge" / "the judges":* fixed — slide 2 statlabel and notes, slide 8 title, callout and notes,
  slide 16 notes now say thinking off; takeaway 4 carries "one model so far, and it still failed its gate". Already
  scoped (OK): slide 55, guide findings 1 and 4, slide 22, guide entry 28.
- [x] 11. Numbers check, full suite, full rebuild, every changed page and slide looked at, clean-tree deck — 1,522 values,
      `--check` 24/24; 356 tests pass (10 new for D-132); paper 26 pp, main text ends p12 (Declarations from p13); report
      PDF, LaTeX bundle, guide, Q&A and deck rebuilt; pages 1, 10, 12, 23 and slides 2, 8, 11, 12, 13, 19, 21, 22, 23,
      58, 62, 65 looked at; deck rebuilt on a clean tree
- [x] 12. Logical commits; local annotated tag `submission-rc1`; no push
