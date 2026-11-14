# Publication figure: content audit

**Figure.** `research_methodology_overview_journal.drawio`, with exports `.pdf` / `.svg` (vector) and `.png` (600 dpi). The generator is `build_methodology_overview_journal.py`; run it from the repository root.

**Earlier versions left unchanged:**
- `../methodology_architecture/` (detailed);
- `../methodology_architecture_simple/` (A3).

**What was not touched:** the manuscript (`PHASE4_FINAL_PAPER.tex` and its supplement) was not edited, and no Git commit was made.

**References used in this audit:**
- **Paper** = `phase4_v2/PHASE4_FINAL_PAPER.tex`. Line numbers are from the current file. Section numbers follow the IEEE build: §III Proposed Methodology, §IV Experimental Setup, §V Results, §VII Ablation Study.
- **Supp** = `phase4_v2/PHASE4_FINAL_SUPPLEMENT.tex`.
- Code and configuration paths are relative to the repository root.

## 1. Format and size

| Property | Value | How checked |
|---|---|---|
| Final width | 179.9 mm (680 drawing units at 96 units/inch), double-column | PDF page box read with pypdf |
| Final height | 107.9 mm | PDF page box |
| Body text | 11 units = **8.25 pt** at final size | style constants; designed at final size, not scaled down |
| Stage labels | 12 units = **9 pt** bold | style constants |
| Smallest text anywhere | 8.25 pt | every label uses `FB` or `FH` |
| Label fit | every line measured with Arial metrics (PIL) against its box width before export; the build stops on any overflow | `check()` in the generator; the final build reports no problems |
| Line weights | boxes 0.8 units (0.6 pt), arrows 0.9 (0.68 pt), ground-truth frame 1.6 (1.2 pt) | all above the usual 0.25 pt journal minimum |
| Colours | `#000000`, `#FFFFFF`, `#F3F3F3` (stage shading) only | style constants |
| Vector output | PDF is one page with selectable text; SVG is diagrams.net's own render | pypdf text extraction; SVG source |
| Raster | PNG at 6.25× (600 dpi at final size), 4250 × 2550 px | export command |

**Inspection at publication size.** The PDF was rasterised at 120 dpi, close to its on-screen printed size, and inspected whole. It was also checked at 300 dpi for detail. Three revision passes fixed:
- a ground-truth heading that touched the box below it;
- an arrow in the ground-truth row too short to read;
- a two-line stage heading crowding its first box;
- the "D2" label clipping the cylinder top.

**Editor check (14 Nov 2026).** The file was opened in the diagrams.net editor (app.diagrams.net) at 100 % zoom, which on screen is approximately the printed size. It showed one page, "Methodology overview", and 28 native text labels; reading the editor's DOM confirmed each label's text. The editor draws in its own dark theme; the file's page background is white.

**Exports.** draw.io Desktop is not installed, so the exports come from the official diagrams.net viewer engine (`viewer-static.min.js`, `Graph.getSvg`) in headless Chrome.

## 2. What the figure shows, and its sources

| Stage | Element in the figure | Source |
|---|---|---|
| Data and execution | D1, Defects4J 3.0.1, real faults | Paper l.211 (Data and splits); `src/triage/config.py` `D4J_PROJECTS` |
| | D2, seeded faults, contamination control | Paper l.211, Table `tab:flow`; `src/triage/d2.py` |
| | Project split: dev 3, test 14 projects | Paper l.211; config `N_DEV_PROJECTS`, `SEED_SPLIT` |
| | Unit-test generation with Gemma 4 26B-A4B | Paper l.230, l.232; `configs/local_models.FROZEN.json` role G |
| | Compile and execute on buggy (B) and fixed (F) | Paper §III-C (l.133) |
| | Failure evidence: outcome, message, stack trace | Paper §III-D (l.138) |
| Evidence preparation | Preprocessing: test filtering, trace normalisation, leakage guard | Paper §III-C/D (l.133, l.138); `src/triage/preprocess.py` |
| | Evidence package; S0 / S1 / S2 specification levels | Paper §III-D (l.138); `src/triage/context_builder.py` |
| | Withheld from all methods: fixed version, patch, labels | Paper §III-D (l.138, last sentence) |
| Triage methods | Non-LLM baselines DA, KA, R0 | Paper Table `tab:arms` (l.144) |
| | Single-agent LLM J1, SC, SC-T | Paper Table `tab:arms` |
| | DEB: Advocate-P and Advocate-T → cross-rebuttal (Rebuttal-P, Rebuttal-T) → Adjudicator | Paper Algorithm `alg:deb` (l.162), §III-E (l.141) |
| | One evidence package feeds all three families (one fan-out connector) | Paper §III-E (l.141): "same model, decoding parameters and evidence package" |
| | Annotation: one judge model M1 (Qwen3.5 9B); equal budget, SC and DEB 5 calls; SC-T matched to DEB tokens | Paper l.232, Table `tab:arms`; FROZEN `decoding` |
| Prediction and evaluation | Common output: PROGRAM_FAULT / TEST_FAULT, cited evidence ids | Paper l.174; `src/triage/schema.py` |
| | Evaluation against sealed labels: classification, error and retention, efficiency | Paper §III-A (l.116–121), l.236 (Statistics) |
| Ground-truth pathway | Execution outcomes → PF / TF classification → sealed labels → evaluation (dashed, the only outgoing link) | Paper §III-C (l.133) |
| | PF: fails on B, passes on F. TF: fails on B and F with the same failure signature | Paper §III-C (l.133), exact rule |
| | "never exposed to any triage method or LLM judge" | Paper §III-C (l.133): labels "stored where no judging module can read them"; §III-D (l.138) |

**Not in the figure:**
- no numerical result;
- no GitBug-Java, D3 or project-stage terminology;
- no figure title (the caption carries it).

A text search of the `.drawio` file finds none of "GitBug", "D3" or "Phase".

## 3. Details removed from the figure, and where they remain documented

Every item removed from the earlier A3 version, or never shown, is still in the manuscript or its supplement.

| Removed detail | Where it remains |
|---|---|
| E1–E5 configurations (arms, levels, datasets, replicates) | Paper §IV "Experiments" paragraph (l.234); results tables `tab:e1` (l.262), Supp `tab:e2` (l.159), `tab:e3` (l.122), `tab:robust` (l.177) |
| Hypotheses H1–H3b and their tests | Paper §I research questions; Supp `tab:conf` (l.103), `fig:forest` (l.143); Paper `tab:status` (l.239) |
| Ablations A1–A5b (E4) | Paper §VII Ablation Study (l.419), Table `tab:abl` (l.423); Supp `fig:abl` (l.149) |
| Robustness (D2, second judge M2, per-project, further judges, frontier reference) | Paper §V `sec:robust` (l.282); Supp `tab:robust` (l.177), `fig:perproject` (l.216), App. `app:post` (l.320) |
| Registered confirmation C1–C4 (OSF kp79c) | Paper §V `sec:confirm` (l.294), Table `tab:family` (l.300), `fig:confirm` (l.322); Supp App. `app:confirmfull` (l.821), `app:registration` (l.781) |
| Mutation probes (operators, FLIP / SHIFT / SAME / ERR, decoupling rule) | Paper §III-F `sec:probes` (l.181); Supp App. `app:confirmfull`; `configs/extension/cfp_frozen.json` |
| Judge-only KUU, cascade, KUU-NG | Paper §III-F (l.179), Table `tab:rules` (l.328); Supp App. `app:cascade` (l.419) |
| Whole-method probes (WDP) | Paper §III-F (l.183), §V `sec:surviving` (l.343), Table `tab:wdp` (l.349); `configs/extension/wdp_frozen.json` |
| Evidential status of each result | Paper Table `tab:status` (l.239) |
| Statistical procedures (bootstrap, Holm, equivalence, McNemar, Wilcoxon, LOPO, mixed model) | Paper §IV "Statistics" (l.236); Supp App. `app:review` (l.503), l.258 (mixed model) |
| Individual metrics (precision, recall, F1, FPR, FNR, MCC, TPR, TNR, balanced accuracy, IPW precision) | Paper §III-A (l.116–121), l.230 (IPW) |
| Execution controls (3 runs per version, fresh JVM, 30 s timeout) | Paper §III-C (l.133); config `RUNS_PER_VERSION`, `TEST_TIMEOUT_S` |
| Environment (Ubuntu 22.04.5 under WSL2, OpenJDK 11) | Paper l.232; Supp X-04 (l.78) |
| Generation settings (3 generations per method, T = 0.7, buggy context) | Paper l.230 |
| Failure signature σ, AMB rule, excluded outcomes | Paper §III-C (l.133) |
| Evaluation sample (all PF, 2 TF per PF, project-stratified, IPW) | Paper l.230; DECISIONS D-53 |
| Population counts (frame, sampled methods, judged and scored instances) | Paper Table `tab:flow` (l.214), Table III `tab:changes` (l.187) |
| Specification inference (T = 0, inputs, fix-line removal) | Paper §III-D (l.138) |
| Invalid-output handling (one repair parse, scored TF, excluded in sensitivity) | Paper l.174 |
| Decoding (temperature, top-p, context, output cap, seed, thinking off), prompt freeze | Paper l.232; FROZEN |
| Seeded adjudicator order, anonymised sides, citation of evidence ids | Paper §III-E (l.141), Algorithm `alg:deb` |
| Deviations from the planned design | Paper Table III `tab:changes` (l.187); Supp App. `app:deviations` (l.70) |
| Numerical findings | Paper §V and its tables; Supp App. `app:extra` |

## 4. Accuracy decisions

1. **D2 hangs off the project split (corrected in the QA review, §4a).** D2 mutants are seeded only into held-out focal methods (Paper l.211), so the split feeds D2, and both D1 (both splits) and D2 feed generation.
2. **Cross-rebuttal is drawn as crossing arrows.** Advocate-P → Rebuttal-T and Advocate-T → Rebuttal-P show what each rebuttal answers. Algorithm 1 also passes each side its own round-1 argument; that same-side input is not drawn, to keep the mechanism readable. It stays in Algorithm 1.
3. **The ground-truth pathway links to Evaluation only.** In the pipeline, the label-based evaluation sample decides which instances are judged, and only their ids cross. That link is deliberately not drawn, so no connector runs from labels toward a triage input. It is documented in the Paper (l.230) and D-53.
4. **"Test filtering" is a summary.** It covers parsing, de-duplication and the removal of flaky, timeout, environment and non-compiling outcomes, all in Paper §III-C/D.
5. **"Efficiency" covers calls, tokens and latency per instance.** Source: Supp `tab:e3`.

## 4a. Final QA review (14 Nov 2026)

The overall structure, layout and the ground-truth pathway were approved and are unchanged. Only corrections required by an actual issue were made. The reviewed pre-QA files are kept in `pre_qa_review/`.

| # | Check | Result | Action |
|---|---|---|---|
| 1 | Project split annotation | The old "dev 3 · test 14" did not state the development purpose. | **Corrected.** Now reads "dev: 3 projects (prompts, thresholds) / held-out: 14", using Paper l.211's terms and its rule that every prompt and threshold was chosen on the development split only. |
| 2 | "One judge model M1" | Paper §III-E (l.141): all LLM arms use the same model. "Shared judge model: M1" is accurate for the main comparison; E5's second judge M2 is shared across arms in its own runs. | **Changed** to "Shared judge model: M1 (Qwen3.5 9B)". The borderless note now spans the stage's inner width so the line fits. |
| 3 | PF / TF and B / F | Matches Paper §III-C (l.133): PF fails on P_B and passes on P_F; TF fails on both with σ_B = σ_F. For D2, B is the mutant version and F the fixed version (`src/triage/d2.py`), which is consistent with "buggy (B)". | Passed, no change. |
| 4 | D1 and D2 pathways | **Issue.** The figure showed D2 feeding generation independently of the split. D2 is built inside held-out focal methods (Paper l.211; `d2.py` traces each D2 item to its test-split focal method), then reuses the D1 pipeline unchanged: generation, dual execution, labelling and evidence preparation. | **Corrected.** D1 → project split → D2 (held-out); both the split and D2 feed generation. The shared downstream path was already correct. |
| 5 | Equal-budget description | "SC and DEB 5 calls" matches Table `tab:arms` and the allocated budget of 5 calls × ≤ 512 output tokens. "SC-T matched to DEB tokens" matches SC-T = smallest odd k reaching DEB's consumed tokens. J1 is correctly not described as budget-matched. | Passed, no change. |
| 6 | Connections | Checked in the `.drawio` XML. `fa`, `fb` and `deb` → `out` only. The sealed labels (`g3`) have exactly one outgoing edge, dashed, to `ev`. No edge leaves the ground-truth pathway toward any method. | Passed. |
| 7 | PDF at publication size | One page, 179.9 × 107.9 mm (pypdf). Checked at 120 dpi (near actual size) and 300 dpi: no clipping, every connector visible, spacing even. The label-fit check passed at 8.25 pt minimum. | Passed after the corrections. |
| 8 | Abbreviations | Defined in the figure: B, F, D1/D2 (named), M1 (named). **Not defined:** PF, TF, S0/S1/S2 contents, DA, KA, R0, J1, SC, SC-T, the P/T suffixes, LLM. | **Caption updated** below. The figure was not crowded further. |

The editor check after QA loaded one page, "Methodology overview", with 28 native labels, including the corrected split and judge texts.

## 4b. Final clarifications and freeze (14 Nov 2026)

**Status: FINAL. Frozen as the publication version.** The pre-clarification files are kept in `pre_final_clarifications/`.

| Change | Text added | Source | Fit |
|---|---|---|---|
| D2 derivation | "held-out only" (fifth line of the D2 cylinder; the existing split → D2 connector is kept) | Paper l.211: one killed mutant "inside a held-out focal method"; `src/triage/d2.py` | The exact phrase "held-out projects only" needs two lines (81 px against about 69 px of room in the 75-unit D2 column). With six lines the first stage could not keep readable spacing at a fixed figure size, so the single-line form was used. The connector from "held-out: 14" in the split box makes the project scope explicit. |
| PF / TF rule | "Other outcomes: excluded" (fourth line) | Paper §III-C (l.133): non-deterministic, timed-out, environment and non-compiling outcomes are excluded. AMB (both fail, different signatures) is excluded from the primary analysis and used only in a sensitivity analysis. | Fits on one line (129 px against 214 px of room). |

**Geometry needed for the two lines**, with no change to typography (8.25 / 9 pt), styling, connectors, width or architecture:
- **First stage:** inner gaps 12 → 10 units; generation, execution and failure-evidence boxes 34 → 32 units; split box and D2 cylinder 72 → 85 units. The stage outline and every other stage are unchanged.
- **Ground-truth row:** boxes 50 → 60 units, so the figure is 2.6 mm taller: **179.9 × 110.6 mm** (was 107.9 mm). The width stays at double column.

**Verification:**
- One-page PDF, 179.9 × 110.7 mm, vector text containing both new lines.
- Inspected at 120 dpi (near actual size) and 300 dpi: no clipping, every connector visible, even spacing.
- The label-fit check passed.
- In the diagrams.net editor: one page, 28 native labels, both new lines present.
- PNG 4250 × 2613 px (600 dpi).

**Checksums of the frozen files (SHA-256):**
- `.drawio` f3b945fb8bfe50f1362e02bdcf637bb4f10b5d077ec00cf9743ea66f3c62cf4b
- `.pdf` ef97e3b4372100cd64f78f4c3accd26d9047face16969262e0b45106de95862d
- `.svg` 4bd2b80267040beece66b8f7d025b464f821cbe96169103a4a8184284b492696
- `.png` 4384f91c6bc9daefa6f4dfd93bf7755b19aefb0f45461fa65a5fd6f62065a691

**Caption note.** The caption below already says D2 is derived from the held-out projects. To match the new PF/TF line, its ground-truth sentence can end with: "other outcomes are excluded (ambiguous outcomes are used only in a sensitivity analysis)".

## 5. Recommended caption with abbreviations (not inserted; the manuscript was not edited)

> **Figure X. Overview of the experimental methodology for LLM-based triage of failing generated unit tests.** The workflow covers dataset preparation, test generation and dual execution on the buggy (B) and fixed (F) program versions, evidence construction, and comparison of non-LLM baselines, single-agent large language model (LLM) approaches and the proposed adversarial debate (DEB) method. D2 is derived from the held-out projects of D1 and follows the same generation, execution and evidence-preparation pipeline. All approaches produce predictions through a common interface. Ground-truth labels are derived independently from execution: program fault (PF), failing on B and passing on F; test fault (TF), failing on B and F with the same failure signature. They are withheld from all triage methods and used exclusively for evaluation (dashed arrow). Specification availability is varied across three levels: S0, test code, failure evidence and signatures; S1, S0 plus the Javadoc of the buggy version; S2, S1 plus an inferred specification. Computational budgets are controlled. DA, discard-all; KA, keep-all; R0, rule-based baseline; J1, one-shot LLM judge; SC, self-consistency (majority of five samples); SC-T, self-consistency matched to DEB's consumed tokens; Advocate-P/-T and Rebuttal-P/-T, debaters arguing for a program fault and a test fault, respectively; M1, shared judge model.

**Two wording corrections to the supplied caption:**
- "Specification availability (S0–S2) and computational budgets are controlled experimental conditions" → specification availability is *varied* (it is the manipulated factor in E2), while budgets are *controlled*.
- "the proposed adversarial debate (DEB) method" is kept.

### Earlier caption draft (superseded)

> Research methodology overview. Generated unit tests for D1 (Defects4J 3.0.1, real faults) and D2 (seeded faults) are executed on the buggy (B) and fixed (F) versions. A deterministic preparation step builds one evidence package per failure, at specification level S0, S1 or S2. Three families of triage methods receive the same package: non-LLM baselines, single-agent LLM judges and the proposed adversarial debate (DEB). All methods emit the same structured output. Ground-truth labels are derived from execution alone, sealed, and joined to predictions only at evaluation (dashed arrow); no triage method or LLM judge can read them.

## 6. Suggested experimental-design table (not inserted)

If the manuscript needs a single place for the conditions removed from the figure, this table matches Paper l.234 and `tab:status`:

| Exp. | Run (Paper l.234) | Data | Judge | Replicates | Tested / status |
|---|---|---|---|---|---|
| E1–E3 | every arm at S0–S2 (SC-T at S1) | D1-test | M1 | 3 | E1: H1 (J1 vs R0, S1); E2: H2a, H2b (specification level); E3: H3a, H3b (equal budget). Confirmatory, Holm (`tab:status`) |
| E4 | ablations A1–A5 against the parent arm (A5b at S2, `tab:abl`) | D1-test | M1 | 1 | exploratory |
| E5 | D2 with M1; second judge M2 on D1-test and D2 (`tab:robust`) | D2, D1-test | M1, M2 | 1 | exploratory (robustness) |
| Confirmation | mutation-probe hypotheses C1–C4 | bugs never used before: frames F1, F2, control CTRL | — | — | confirmatory, registered (OSF kp79c), one Holm family |
