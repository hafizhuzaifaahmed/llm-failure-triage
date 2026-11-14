# Reviewer response matrix (revision pass after the external-style review, started 2026-11-09)

Every major issue, minor issue and proposed upgrade of the review, and every manuscript-cleanup item, has one row.
Disposition: **do now** (this pass, before the 15 Nov 2026 submission), **journal follow-up** (needs new data, independent
raters, external preregistration, paid models or a new system; protocol in `JOURNAL_FOLLOWUP_PLAN.md`), **blocked** (exact
blocker stated), **not applicable** (reason stated). Status is updated as work lands; nothing is removed because it is
deferred. Governing decision entries are in `DECISIONS.md` (D-112 onward).

Repository state verified at the start of the pass (2026-11-09, HEAD `27c6b25`, clean tree apart from the live server log):
frame 312 methods / 220 bugs; per-project cap 25 leaves 234 methods / 167 bugs, so **78 methods** are excluded (Lang 26,
Math 44, Mockito 8, all held-out projects); D1-test labelled **60 PF / 296 TF / 13 AMB**; judged sample 60 PF / **120 TF** /
13 AMB, so **176 TF** were never judged; D1-test scored set at S1 177 instances; D2 judged sample 300 (159 PF / 119 TF /
22 AMB), scored 270; D2 leakage aborts 8, of which 5 matched the mutated line. Generator: G = Gemma 4 26B (the only
generator; E7a's phi4 and llama3.1 failed generator selection, D-102). Judges: M1 Qwen3.5 9B, M2 Gemma 4 12B, E6b Ministral 3
14B, NG Llama 3.1 8B, the exploratory Qwen3.5 35B, and the frontier reference Claude Sonnet 5.5. Adding a judge is never
adding a generator.

## A. Statistical power and dataset coverage

| ID | Reviewer concern | Evidence in this repository | Disposition | Data / resources | Planned method | Destination | Status |
|---|---|---|---|---|---|---|---|
| A1 | Judge all 296 held-out TF failures, not only the sampled 120 | `sample_D1_test.json` holds 120 of 296 TF; instances and contexts exist for all 296 (`instances_D1.jsonl`, `data/interim/context`) | do now (WP2.1) | local GPU ~35 min; frozen prompts | J1 at S1 from M1, M2, E6b, NG on the 176 unjudged TF; merge after ID/prompt/setting checks | `results/revision/wp21/`, App. G | **done (WP2.1)**: 173 of 176 judged by 4 judges (3 leakage-guard aborts, identical for all); merge checks pass; 290 of 296 TF judged in all, so natural-prevalence coverage is NOT claimed; App. G Table G7(a), D-124 |
| A2 | Lift the 25-per-project cap; investigate the 78 excluded methods | `split_manifest.json`: Lang 51→25, Math 69→25, Mockito 33→25 | journal follow-up (generation) + do now (characterise) | G generation, WSL Defects4J execution, labelling: new data, several days | now: describe the 78 (project, bug count) from the frame; later: generate, execute, label, judge with frozen protocol | `JOURNAL_FOLLOWUP_PLAN.md` J-A2; App. G | **characterised; generation is journal follow-up** (J-A2): the 78 are Lang 26, Math 44, Mockito 8; no tests exist for them |
| A3 | Generate more tests per method | 3 generations per method (D-22 design) | journal follow-up | G generation + execution | k > 3 generations, same frame; report per-method PF yield | J-A3 | **journal follow-up** (J-A3) |
| A4 | Add a genuinely second **test generator** (not a judge); judge-selection gates may be wrong for a generator | E7a: phi4 14B and llama3.1 8B failed D-22 generator gates C1/C2 on dev (D-100, D-102); no second corpus exists | journal follow-up | a stronger generator (local or API), new gates suited to "tests that fail in useful ways" | write generator gates on PF yield and failure diversity rather than C1/C2 assertion validity; preregister | J-A4 | **journal follow-up** (J-A4); E7a's two candidates failed the generator gates (D-102) |
| A5 | Sample size for H3a/H2a, MDE 0.08, ~4x bugs | Table C1 (`mde_sensitivity.json`): bug-level bootstrap SE per test | do now (WP1.8) | zero calls | n_req = n0 · (SE0·(z₀.₉₇₅+z₀.₈) / MDE)², SE ∝ 1/√bugs | `results/revision/wp18_sample_size.json`, App. G | **done (WP1.8)**: MDE 0.08 needs 257 bugs for H3a (4.27×; 6.35× at Holm α), only 33 for H2a: the 4× holds for H3a, not H2a; D-122 |
| A6 | Re-run the S × architecture factorial with a judge that passes its gate | every local judge failed G-d (WP2.5); Sonnet's E9 was a reference point, no gate | journal follow-up (paid) | Sonnet 5.5 API, new key, author approval | preregistered E2/E3 factorial, 3 replicates; cost from logged E9/E9b usage | `docs/tracking/PREREG_SONNET_FACTORIAL.md`, J-A6 | **journal follow-up (paid)**: `PREREG_SONNET_FACTORIAL.md`, new spend ≈ US$ 66 (estimate); author approval and a new key needed; D-128 |

## B. Metrics and practical value

| ID | Reviewer concern | Evidence | Disposition | Data | Method | Destination | Status |
|---|---|---|---|---|---|---|---|
| B1 | Report TPR, TNR, balanced accuracy; reduce dependence on the 1:2 mix | only F1/MCC/P/R/FPR reported; D1 PF prevalence 0.339, D2 0.570 | do now (WP1.1) | committed decisions | per rule and dataset with bug-level 10,000-resample CIs; Sonnet E9 vs E9b on TPR/TNR/BA | `results/revision/wp11_prevalence_free.json`, App. G | **done (WP1.1)**: App. G Table G1; KUU BA 0.594/0.621 below M1 DEB 0.632/0.697; Sonnet D1 − D2 BA not distinguishable; D-122 |
| B2 | Common-scale PF-loss vs TF-removal plot | Fig. 2 (`fig_pareto`) plots share discarded vs share lost | do now (WP1.2) | as B1 | x = 1 − TPR, y = TNR, same axes for D1 and D2; Fig. 2 kept until authors choose | `paper/figures/fig_tradeoff_rates.pdf` | **done (WP1.2)**: Fig. 3 beside Fig. 2 (authors choose) |
| B3 | Triage as ranking: AUROC/AUPRC, top 10/20/30% inspection, bug-level recall | SC PR-AUC only | do now (WP1.3) | committed votes and confidences | scores with verified direction; test-level and bug-level recall@k with exact expectation over random tie-breaking; D1 reweighted with the sampling weights | `results/revision/wp13_ranking.json`, App. G | **done (WP1.3)**: App. G Table G2; bug-level recall reported separately; D1 reweighted |
| B4 | Compare KUU with a learned LR stacker and a non-LLM feature classifier | none; R0 is the only non-LLM rule | do now (WP1.4) | instance covariates + KUU votes | leave-one-project-out LR; D1→D2 transfer, exploratory | `results/revision/wp14_learned.json`, App. G | **done (WP1.4)**: App. G Table G3; LOPO, D1→D2 transfer (exploratory) |
| B5 | Compare all k-of-3 thresholds | D-106 has KUU and 2-of-3 majority on D2 only | do now (WP1.5) | committed votes | k = 1,2,3 for KUU, KUU-NG panels and within-model triples (SC samples) | `results/revision/wp15_k_of_n.json` | **done (WP1.5)**: App. G Table G4 |
| B6 | Conformal risk control, with accurate assumptions | none | do now (WP1.6), exploratory | KUU/KUU-NG votes + M1 DEB confidence | CRC bound calibrated on D1 PF, evaluated on D2; assumptions checked; called a heuristic if they fail | `results/revision/wp16_risk_threshold.json`, App. G | **done as a heuristic (WP1.6)**: two CRC conditions fail; KUU-NG threshold exceeds α on D2 (0.065 > 0.05); App. G Table G5 |
| B7 | Practical value: KUU-NG removes 7%; KUU/cascade 7–13%; +0.029 F1; precision 0.065 at 5% (≈14 false alarms per bug) | `kuung.json`, `pareto.json`, `review_sensitivity.json` | do now (WP1.1/1.3) | as B1 | recompute each with its denominator; false alarms per kept PF at natural, 5% and 2% prevalence; top-k developer view; conservative wording | paper RQ4, App. G, matrix note | **done**: all four figures reproduce from raw outputs (7.0%, 13.0%, +0.029, 0.065 → 14.3 false alarms per kept PF); cascade discards 37.8%, so '7–13%' is KUU-NG to KUU; Discussion 'Practical value of KUU is limited'; conclusion tempered |

## C. Fresh real-fault confirmation and leakage

| ID | Reviewer concern | Evidence | Disposition | Data | Method | Destination | Status |
|---|---|---|---|---|---|---|---|
| C1 | Confirm on the 78 cap-excluded methods | the 78 are in `frame_d1.jsonl`; no tests generated for them | journal follow-up | new generation and execution (as A2) | KUU and cascade preregistered on the new corpus | J-C1 | **journal follow-up** (J-C1) |
| C2 | Bugs fixed after the models' release dates | GitBug-Java 2023 bugs predate 2026 models (D-103) | journal follow-up | a post-cutoff benchmark with release-date evidence | select bugs fixed after each model's documented release date | J-C2 | **journal follow-up** (J-C2) |
| C3 | Behaviour-preserving identifier renaming as a memorisation check | not done | journal follow-up | renaming tool, re-execution to prove behaviour preserved, new calls | rename in focal class and tests; re-label; re-judge | J-C3 | **journal follow-up** (J-C3) |
| C4 | D2 single-line mutants may be identifiable; not sufficient real-fault confirmation | E9b caveat already in App. E | do now (text) | none | state plainly in threats and RQ4 | paper threats | **done**: threats (Internal) and App. G |
| C5 | Quantify the leakage guard's selection effect (5 of 8 aborts caught the mutated line) | `d2_abort_vs_mutant.json`, leakage rejections | do now (WP1.10) | zero calls | labels, projects and prevalence of aborted vs scored D2 instances; no aborted item restored | `results/revision/wp110_guard_selection.json`, App. G | **done (WP1.10)**: 8 of 300 judged D2 aborted, 5 PF all on the injected line, 3 TF; prevalence 0.572→0.570; no item restored; threats + App. G |

## D. Label validity and audit

| ID | Reviewer concern | Evidence | Disposition | Data | Method | Destination | Status |
|---|---|---|---|---|---|---|---|
| D1 | Audit held-out items with raters who are not authors and do not see the fix or the label | D-108 audit: authors, saw the fix, dev split only | journal follow-up | independent raters (recruitment needs author approval) | blind packets without fix/label/model output | J-D1 | **journal follow-up** (J-D1): needs independent raters (author approval) |
| D2 | Blind raters to fixed-version outcomes and model judgments | as D1 | journal follow-up | as D1 | packet builder strips fix, F-outcome, judgments | J-D1 | **journal follow-up** (J-D1) |
| D3 | Oversample TF assertion failures; the blind spot (a test exposing a different real bug fails on both versions → TF) | rule in Table 2; D-108 mismatches were 2 execution-TF judged PF | journal follow-up + do now (text) | raters | stratified sample over-weighting TF assertion failures | J-D3; threats | **journal follow-up** (J-D3) + **done (text)**: blind spot stated in threats |
| D4 | Audit taxonomy (wrong expectation / environment / patch-unrelated real fault / unresolved); no post hoc change to the label rule | none | journal follow-up (taxonomy drafted now) | raters | taxonomy fixed before rating | J-D3 | **journal follow-up** (taxonomy drafted in J-D1/J-D3); label rule unchanged |
| D5 | How plausible label noise moves TPR/TNR/BA, ranking metrics and conclusions | none | do now as a zero-call sensitivity (WP1.11), audit-calibrated version is follow-up | committed decisions | flip a share q of TF assertion-failure labels to PF (q from 0 to 0.10) and recompute | `results/revision/wp111_label_noise.json`, App. G | **done as a zero-call noise model (WP1.11)**: order of rules unchanged up to q = 0.10 (max BA shift 0.043); audit-calibrated version is follow-up |

## E. Judge configuration and repeatability

| ID | Reviewer concern | Evidence | Disposition | Data | Method | Destination | Status |
|---|---|---|---|---|---|---|---|
| E1 | One-shot J1 at temperature 0 | J1 ran at the frozen temperature 0.7 | do now (WP2.2) | local GPU ~6 min | M1, S1, temp 0, otherwise frozen | `results/revision/wp22/` | **done (WP2.2)**: App. G Table G7(b); D-125 |
| E2 | Thinking-enabled one-shot judge at DEB's token budget | thinking disabled in the frozen config | do now (WP2.3) if the runtime allows | local GPU 4–6 h (probe first) | M1 think=true, one call; token match only if measurable | `results/revision/wp23/` | **done (WP2.3), not token-matched**: one run, BA 0.771, MCC 0.513, 7 of 60 PF lost, 0.74× DEB's tokens; 10 calls hit the output cap; qualifies the abstract/conclusion wording about arms (authors decide); D-129 |
| E3 | At least five debate replicates (0.221 F1 range over three) | `replicate_noise.json`: DEB 0.525/0.614/0.393 | do now (WP2.4) | local GPU ~3.5 h | five new DEB replicates at fresh indices | `results/revision/wp24/` | **done (WP2.4)**: 8 runs, F1 0.393–0.614 (range 0.221 unchanged, SD 0.076), BA 0.546–0.710; D-129 |
| E4 | Record gate failures; weak-judge nulls are not evidence about the method | M1 and M2 fail G-d; E6b, NG gates G-a/G-b only | do now (WP2.5) | committed gate files | table of every judge's gate outcome; wording in RQ2/RQ3 | App. G, threats | **done (WP2.5)**: all 4 local judges failed G-d (App. G Table G6); wording in setup, Discussion, threats |

## F. Baselines and method upgrades

| ID | Reviewer concern | Evidence | Disposition | Data | Method | Destination | Status |
|---|---|---|---|---|---|---|---|
| F1 | A learned non-LLM baseline inspired by CI alarm triage | R0 only | do now (WP1.4b) | covariates | LOPO logistic regression, no LLM votes | as B4 | **done**: as B4 (features-only model) |
| F2 | Cross-generation agreement as a zero-call signal and its incremental value | three generations per method, linked by focal_id + generation | do now (WP1.7) | buggy-version executions only | agreement of another generation on the same violated expectation; standalone and as a WP1.4 feature | `results/revision/wp17_cross_generation.json` | **done (WP1.7)**: AUROC 0.513 on D1 (no signal), 0.708 on D2; no incremental value in WP1.4 |
| F3 | Ranking and risk-controlled thresholds | as B3, B6 | do now | as B3, B6 | as B3, B6 | as B3, B6 | **done**: as B3, B6 |
| F4 | Agentic evidence-gathering judge (run variants, print values, inspect call sites) vs the fixed package at matched budget | not built | journal follow-up | new system: sandboxed tool execution | budget-matched comparison, preregistered | J-F4 | **journal follow-up** (J-F4) |
| F5 | End-to-end repair-first outcome: bugs still detected after triage and repair | not measured | journal follow-up | repair generator + re-execution | count bugs with ≥1 PF test surviving triage and repair | J-F5 | **journal follow-up** (J-F5) |

## G. Research-process concerns

| ID | Reviewer concern | Evidence | Disposition | Data | Method | Destination | Status |
|---|---|---|---|---|---|---|---|
| G1 | D-82…D-111 are sequential follow-ups selected after earlier results; consolidate RQ4 into one fresh-data OSF-preregistered replication with one Holm family | DECISIONS D-82…D-111 | journal follow-up (outline now) | fresh data, OSF account (author action) | one document: hypotheses, outcomes, exclusions, analysis, full Holm family | `docs/tracking/OSF_PREREG_RQ4_OUTLINE.md`, J-G1 | **journal follow-up (outline done)**: `OSF_PREREG_RQ4_OUTLINE.md`; paper now says 'fixed in the repository, not externally registered' |
| G2 | Separate confirmatory, exploratory and post hoc claims; new analyses do not confirm old hypotheses | statuses exist per decision | do now | none | label every new result exploratory/post hoc; artifact traceability table | paper App. H, threats | **done**: statuses in App. H; 'pre-registered' removed for RQ4 in paper, report, QA, deck, guide |

## M. Manuscript cleanup register

| ID | Item | Disposition | Status |
|---|---|---|---|
| M1 | Remove "approved Phase 2 design" from the Figure 1 caption | do now | **done** |
| M2 | Remove the "Changes after Phase 2" paragraph | do now (its TODO is not an author TODO the prompt lists to keep; the instructor-feedback TODO moves to the acknowledgements TODO list, not dropped) | **done** (its instructor-feedback TODO kept, moved to App. A) |
| M3 | Replace "Two independent mock reviews of this manuscript asked for…" with neutral wording; git log ≠ external registration | do now | **done** |
| M4 | Keep author TODOs (instructor feedback, repository URL, DOI, declarations); invent nothing | do now (verify) | **done**: all 8 author TODOs present, none filled |
| M5 | Move D-xx / E-xx / H-xx identifiers out of main prose into a traceability appendix | do now (main text; appendices keep them) | **done for main prose** (D-, H6–H13, E6b–E9b removed; M3/NG names; App. H maps them); H1–H3b and E1–E5 kept because the paper defines them |
| M6 | Table 7: add E8 VOTE3 as a measured three-family vote; label published figures as external | do now | **done**: VOTE3 row (same 177 instances); published rows labelled 'published elsewhere*' |
| M7 | Invalid outputs = TF in primary arms but keep in KUU: explain; sensitivity | do now (WP1.1 sensitivity) | **done**: explained in Method; sensitivity max ΔBA 0.008 |
| M8 | Report the leakage guard's selection effect on D2 | do now (WP1.10) | **done**: Setup/threats + App. G |
| M9 | statsmodels variational-Bayes mixed model under-covered: reassess | do now (WP1.9): R/lme4 not installed; frequentist GEE sensitivity, VB model de-emphasised | **done**: VB de-emphasised; GEE sensitivity (R not installed) |
| M10 | Local-first rationale: privacy/data governance; no "free GPU" claim | do now | **done**: privacy/data-governance sentence; local compute stated as not priced |
| M11 | Reorganise around discarded bug-revealing tests; one paper or two? recommendation | do now (recommendation + plan; no split without authors) | **done (recommendation)**: one paper now, split for the journal after the RQ4 replication (REVISION_CHECKLIST.md); no split made |
| M12 | Small KUU F1 gain and false-alarm burden limit practical claims | do now | **done**: Discussion paragraph + conclusion |
| M13 | Threats: weak judge, sample size, D1/D2 prevalence, mutant selection, leakage guard, label blind spot, sequential follow-ups | do now | **done**: threats updated (all seven named) |

## P2. Pass 2 (authors' decisions, 2026-11-10)

| ID | Item | Disposition | Status |
|---|---|---|---|
| P2-1 | Thinking-judge GPU estimate and run order (WP1.1) | do now | done (D-130: 61.0 s/call measured) |
| P2-2 | Thinking M1 on the development gate (WP1.2) | do now | done — gate FAILED (G-a 96.8%, G-d F1 0.312 vs R0 0.642), recorded |
| P2-3 | D2 confirmation HT-1/HT-2, committed before the calls (WP1.3) | do now | done — HT-1 and HT-2 supported, p_Holm 0.0004 (D-131) |
| P2-4 | Two more D1 thinking runs (WP1.4) | do now | done — BA 0.771–0.817 over three runs (D-131 (3)) |
| P2-5 | Output-cap sensitivity (WP1.5) | do now | done — verdict unchanged under keep/exclude (D-131) |
| P2-6 | Token figure explained, not token-matched (WP1.6) | do now | done — 6,753 vs 9,188 tokens/instance, not token-matched |
| P2-7 | Claim wording by the fixed rule (WP2) | do now | done — branch A; text quoted in REVISION_CHECKLIST.md |
| P2-8 | Rates figure main, old figure to App. G, main text p12 (WP3.7) | do now | done — main text ends p12 |
| P2-9 | Report, study guide, deck updates (WP3.8–3.10) | do now | done — report §7c, guide entry 28, Q&A 30, deck slides 15/26/56 |
| P2-10 | Independent read-only check (WP4.11) | do now | done — findings fixed or recorded in REVISION_CHECKLIST.md item 13 |
| P2-11 | One paper now; split after RQ4 replication | author decision, recorded in JOURNAL_FOLLOWUP_PLAN.md | recorded (J-M11) |

## P3. Pass 3 (authors' decisions, 2026-11-11; last pass before the 15 Nov 2026 submission; zero model calls)

| ID | Item | Disposition | Status |
|---|---|---|---|
| P3-1 | Fully local cascade (Tier 2 = logged thinking M1 J1), post hoc, D2 and D1-test, one rule fixed before computing | do now (zero calls) | done — D-132; D2 BA 0.765, 6 PF lost, 0 bugs lost |
| P3-2 | Report it beside KUU, thinking J1, Sonnet cascade, Sonnet DEB; Appendix G table + one RQ4 sentence; journal confirmation | do now + journal follow-up | done — Table G9, RQ4 sentence, J-L1 |
| P3-3 | Scope any cascade / local-first sentence the result contradicts | do now | done — two sentences scoped (Q&A 28, guide decision 22); paper's cascade sentences hold |
| P3-4 | One wording for hypotheses fixed in the decision log, across paper, report, guide (incl. glossary), deck | do now | done — 47 changes, listed in REVISION_CHECKLIST.md |
| P3-5 | Deck main story: thinking slide after debate; findings and takeaways slides; local-cascade note | do now | done — slides 11, 19, 21, 22, 23 |
| P3-6 | Study guide Part 1, the thinking decision in five parts, glossary "thinking mode" | do now | done — Part 1, entries 27–29, glossary |
| P3-7 | Eight new defense questions in DEFENSE_QA and the study guide, cited | do now | done — DEFENSE_QA 31–38, guide Part 2b |
| P3-8 | `docs/paper/SUBMISSION_TODO.md`: every author TODO with file and line | do now | done — docs/paper/SUBMISSION_TODO.md |
| P3-9 | Independent read-only consistency check of paper, deck, guide and numbers map | do now | done — findings fixed or recorded in REVISION_CHECKLIST.md item 10 |
| P3-10 | Numbers check, tests, full rebuild, clean-tree deck, commits, local tag `submission-rc1` (no push) | do now | done — tag submission-rc1 (local, not pushed) |
