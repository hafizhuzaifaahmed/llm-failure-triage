# Architecture content audit

What this audit covers: `research_methodology_architecture.drawio` and its `.pdf`, `.svg` and `.png` exports.
The generator is `build_methodology_architecture.py`, run from the repository root.

## 1. Source hierarchy

Each claim in the diagram was checked against the most authoritative source available, in this order:

1. **Executed code and frozen configuration.**
   - `src/triage/config.py` holds the protocol constants and seeds.
   - `configs/local_models.FROZEN.json` holds the models, decoding settings and k_T, frozen under D-57.
   - `configs/extension/cfp_frozen.json` freezes the mutation probes.
   - `configs/extension/wdp_frozen.json` freezes the whole-method probes.
   - `configs/extension/osf_registration.json` records the OSF registration.
2. **Generated numbers.** `phase4_v2/generated/numbers_v2.tex` is the single file the paper prints its numbers from. The generator reads every number in the diagram from it at build time through `V(key)`; no number is typed by hand.
3. **Final paper and supplement.**
   - Paper: `phase4_v2/PHASE4_FINAL_PAPER.tex`.
     - Section III (Proposed Methodology), subsections A–F.
     - Section IV (Experimental Setup), including Table III, the changes from the approved design.
     - Section V (Results).
   - Supplement: `phase4_v2/PHASE4_FINAL_SUPPLEMENT.tex`, the deviations list X-01 to X-07.
4. **Decision log.** `docs/tracking/DECISIONS.md`, used only where the paper defers to it (for example D-53 on sampling).

Where two sources disagreed, the executed state won and the planned state went to
`unresolved_source_details.md`.

## 2. Component-to-source checklist

| § | Diagram component | Content shown | Source(s) | Status |
|---|---|---|---|---|
| A | D1 dataset | Defects4J 3.0.1, 17 projects, frame 312 / 220, 25-per-project cap, 234 / 167 sampled | `config.py` (`D4J_PROJECTS` = 17, `MAX_FOCAL_PER_PROJECT` = 25); numbers `split:frame_methods`, `split:frame_bugs`, `split:sampled_methods`, `split:sampled_bugs`; paper Table III | verified |
| A | Project-level split | Seeded draw made before generation | `config.py` `SEED_SPLIT`, `N_DEV_PROJECTS` = 3; paper §IV | verified |
| A | Development / held-out | Development: Cli, Gson, Jsoup, 39 methods. Held-out: 14 projects, 195 methods | numbers `der:dev methods`, `der:n test projects`, `der:test methods`; paper §IV | verified |
| A | D2 seeded faults | B = F + one killed Major mutant inside a held-out focal method, ≤ 2 per method, 284 mutants | `config.py` `MAX_MUTANTS_PER_FOCAL` = 2; `src/triage/d2.py`; number `d2rep:before_cap:d2_units_total`; paper §IV | verified |
| C | Execution environment | WSL2 Ubuntu 22.04.5, OpenJDK 11.0.32, Defects4J 3.0.1, recorded manifest, TZ, locale | paper §IV "Models and hyperparameters"; supplement X-04 | verified (see unresolved item 1) |
| C | Checkout / generation | Generator G = Gemma 4 26B-A4B Q4_K_M; 3 generations per focal method; T = 0.7 | `config.py` `GENERATIONS_PER_FOCAL`, `GENERATION_TEMPERATURE`; `local_models.FROZEN.json` role G; paper §IV | verified |
| C | Compile, dual execution, failure record | ≤ 3 prune passes; 3 runs per version; fresh JVM; 30 s timeout | `config.py` `MAX_COMPILE_PRUNE_PASSES`, `RUNS_PER_VERSION`, `TEST_TIMEOUT_S`; paper §III-C | verified |
| D | Steps 1–7 | Parse, dedup, outcome exclusion (ENV re-run once), stack frames ≤ 25, message ≤ 500 chars, Javadoc ≤ 600 / spec ≤ 400 / package ≤ 6,000 tokens, leakage guard, context builder | `config.py` preprocessing block (`MAX_STACK_FRAMES`, `MAX_MESSAGE_CHARS`, `MAX_*_TOKENS`, `ENV_RERUNS`); `src/triage/preprocess.py`; `src/triage/context_builder.py`; paper §III-D | verified |
| E | S0 / S1 / S2 nesting | Item ids [T], [F1]–[F4…], [Sig], [Doc], [Spec]; S2 inferred once per method at T = 0 with fix-changed lines removed | paper §III-D; `src/triage/spec_inference.py`; `config.py` `SPEC_TEMPERATURE` = 0 | verified |
| E | E2 / E4 factor tags | Only the specification section varies (E2); A4, A5a, A5b inputs (E4) | paper §IV and §VII (Ablation Study) | verified |
| E | Withheld box | Focal body, fixed version, patch, developer tests, bug ids, labels | paper §III-D (last sentence); `config.py` `GT_STORE`, `LEAKAGE_GUARD` | verified |
| F | DA, KA, R0 | Decision rules, 0 calls | paper Table II (`tab:arms`) | verified |
| F | J1, SC, SC-T | 1 call; 5 samples with ties going to TF; k_T = 5 | paper Table II; `local_models.FROZEN.json` `decoding.k_T`, `sc_samples` | verified |
| F | DEB | Two advocates, crossed rebuttals, anonymised adjudicator, seeded order, 5 calls | paper Algorithm 1, §III-E; `config.py` `SEED_ARGUMENT_ORDER`, `DEB_CALLS` | verified |
| F | Controlled settings | M1 Qwen3.5 9B; Ollama 0.40.13; temperature, top-p, 8,192 context, ≤ 512 output tokens; per-call seed; thinking off; 5 prompt rounds; 3 replicates | `local_models.FROZEN.json`; numbers `frozen:*`; paper §IV | verified |
| F | Equal budget (E3) | SC and DEB at 5 × ≤ 512 tokens; J1 as the low-budget reference; SC-T matched on consumed tokens | `config.py` `MAX_OUTPUT_TOKENS`, `SC_SAMPLES`, `DEB_CALLS`; paper §IV | verified |
| G | Output record and parse | JSON schema fields; one deterministic repair; invalid output scored TF, excluded in the sensitivity run | paper §III-E (last paragraph); `src/triage/schema.py`; `config.py` `REASON_CATEGORIES` | verified |
| B | Signature and labelling rule | σ = (outcome, exception class, failing line), deterministic over 3 runs; PF / TF / AMB / excluded | paper §III-C; `src/triage/labeling.py` | verified (see unresolved item 2) |
| B | Evaluation sample | All PF plus 2 TF per PF over the split, project-stratified, with IPW weights; D1-test 60 / 120 / 13 → 177 scored at S1; D2 300 judged, 270 scored | D-53; `config.py` `PF_TO_TF_RATIO`, `SEED_TF_SAMPLE`; numbers `sum:prevalence:*`, `sum:leakage_abort_exclusions:*`, `d2rep:judged_sample:cap`, `d2:DEB\|S1:n_instances` | verified (wording corrected to D-53 during this audit) |
| B | Sealed label store | Written before any judge runs; not readable by any judging module | `config.py` comment on `GT_STORE`; paper §III-C | verified |
| H | Scoring, metrics | Unit of analysis, replicate averaging, bug resampling unit, metric list | paper §III-A, §IV; `src/triage/metrics.py` | verified |
| H | Statistics | 10,000 bug-level cluster-bootstrap resamples; Holm over H1–H3b; ±0.05 equivalence with a 90 % CI; McNemar, Wilcoxon, LOPO; exploratory mixed model | `config.py` statistics block; number `cc:resamples`; paper §IV; supplement X-02 / X-06 | verified (see unresolved item 6) |
| I | E1–E5 | Arms, levels, replicates and hypotheses per experiment | paper §IV, §V, §VII | verified (E5-R2 and E5-R4 left out, see unresolved items 3 and 4) |
| J | KUU, cascade, KUU-NG | Three families, unanimity rule, invalid vote keeps the test | paper §III-F (`sec:probes`); `configs/kuu_*.json`, `configs/kuung.json` | verified |
| J | Mutation probes (pilot) | ≤ 80 mutants; operators; FLIP / SHIFT / SAME / ERR; ≥ 10 compiled for "decoupled" | paper §III-F; `cfp_frozen.json`; numbers `cfz:parameters:*` | verified |
| J | Registered confirmation | OSF kp79c; frames F1, F2, CTRL; C1–C4; one Holm family | `osf_registration.json`; number `osf:osf_id`; paper §V (`sec:confirm`) | verified |
| J | Whole-method probes | Exploratory, retrospective; entry-recording replacement bodies; KUU + CD-U | paper §V (`sec:surviving`); `wdp_frozen.json` | verified |
| K | RQ1–RQ6, Exploratory, Efficiency, Limitations | Every figure | numbers `d1:*`, `conf:f1:*`, `kuu2:*`, `cc:family:*`, `wdp:*`, `pil:*`, `cc:population:*` | verified (generated, not typed) |

## 3. Coverage checklist (task specification)

- [x] Research problem and objective, in the title strip.
- [x] Datasets and partitioning (A), with D1 and D2 only.
- [x] Test generation, compilation and dual execution (C).
- [x] Preprocessing and evidence construction (D).
- [x] Evidence package, specification levels and withheld information (E).
- [x] Baselines, the proposed debate and the comparators (F).
- [x] Common output interface (G).
- [x] Sealed ground-truth channel, kept physically separate from every LLM path (B).
- [x] Evaluation, metrics and statistics (H).
- [x] Experimental design E1–E5 and the hypotheses (I).
- [x] Supplementary analyses grouped by evidential status (J).
- [x] Research questions linked to their findings (K).
- [x] Legend: 9 node styles and 3 connector styles.
- [x] GitBug-Java and D3 are left out entirely.
- [x] No historical project-stage labels ("Phase 2", "Phase 3", "Phase 4", "later additions") anywhere in the diagram.

## 4. Visual language

| Style | Meaning |
|---|---|
| White rectangle, 1 px | deterministic step or non-LLM component |
| Grey (#D9D9D9) rectangle | LLM call |
| Cylinder | dataset |
| 2.5 px rectangle | sealed ground truth |
| Dashed 6-3 | manipulated factor |
| Dotted 1-2 | controlled setting |
| Light grey (#F0F0F0) | information withheld from triage |
| 1.75 px rectangle | confirmatory analysis |
| Dash-dot | exploratory analysis |

Connectors come in three kinds:

- **Solid arrow:** data and evidence flow.
- **Thick dashed arrow:** sealed labels, used only at evaluation.
- **Dotted arrow:** instance ids only, with no labels.

The whole diagram uses Arial, black text on white, sharp corners, no shadows, no gradients and no icons.

## 5. Export and verification method

- **Exports.** draw.io Desktop is not installed on the build machine, so the official diagrams.net viewer engine produces the exports. The steps:
  1. The engine (`viewer-static.min.js`) loads in headless Chrome.
  2. Its `Graph.getSvg()` renders the `.drawio` file as **SVG**.
  3. Chrome prints that SVG to a one-page vector **PDF**.
  4. Chrome rasterises it at 2× for the **PNG** (4588 × 3398).
  Only the viewer script is fetched; the diagram itself is never uploaded.
- **Editor check (14 Nov 2026).** The `.drawio` file was opened in the diagrams.net editor (app.diagrams.net, loaded through a local `#R` URL). It opened as one page, "Methodology architecture", with native, selectable shapes; selecting a step showed its Style, Text and Arrange panels. The editor rendered in its own dark UI theme; the file's page background is white (`background="#FFFFFF"`).
- **Visual QA.** Two passes, each at full page and on zoomed quadrant crops. They checked for connectors crossing titles or boxes, label collisions, clipped text and overflow, and every defect found was fixed in the generator. A third crop check followed the D-53 wording correction to section B.
