# Unresolved source details

This file covers the methodology architecture diagram. It lists two kinds of item:

- places where the planned and the executed method differ;
- details the diagram could not verify from the repository.

In every case the diagram shows the **executed** state, or leaves the detail out. Nothing here was resolved by assumption.

## A. Planned versus executed (documented deviations)

| # | Topic | Planned | Executed (shown in the diagram) | Record |
|---|---|---|---|---|
| 1 | Execution environment | Docker image with a digest | WSL2 Ubuntu 22.04.5 with a recorded environment manifest. Reproducibility rests on the manifest, not on an image digest. | paper Table III; supplement X-04 |
| 2 | AMB instances | — | The paper uses AMB "only in a sensitivity analysis" and excludes it from primary scoring. The diagram says "sensitivity only" in section B and "AMB excluded" in section H's scoring box. Whether AMB is out of *every* secondary analysis, or only the primary one, is not stated per analysis. | paper §III-C |
| 3 | E5-R4 prompt paraphrases | Robustness to paraphrased prompts | Not run. Left out of E5; no prompt-sensitivity claim is made. | paper Table III; D-59, D-61 |
| 4 | E5-R2 third benchmark | A third dataset | Not run. Left out of the diagram entirely, as the task required. | paper Table III; X-05 |
| 5 | S2 leakage audit | Manual audit of 60 inferred specifications | Not carried out. Fix-changed lines are removed mechanically, but whether an S2 text restates the fixed behaviour was never audited. The diagram shows only the mechanical removal. | paper Table III |
| 6 | Mixed model | GLMM with lme4 | statsmodels variational Bayes, with bug-level bootstrap intervals; exploratory only. The diagram says "logistic mixed model (exploratory)" and names no library. | paper Table III; supplement X-02 / X-06 |
| 7 | Label audit | 100 instances (50 PF, 50 TF) | 71 instances; all 21 development PF. It is not drawn as a pipeline step, because it audits the labels rather than producing them. | paper Table III; D-82, D-108 |
| 8 | Frame size | Zhao et al.: 318 methods / 233 defects | Re-running their selection rule gives 312 / 220. The diagram shows 312 / 220. | paper Table III; X-03 |
| 9 | 1:2 PF:TF sampling | "stratified by project" (wording ambiguous) | The ratio applies over the split, project-stratified, with IPW weights (D-53). This audit corrected the diagram from "1:2 by project" to match. The development split kept the within-project reading. | D-53; X-07 |
| 10 | Development gate | J1 F1 above both trivial baselines | M1 failed the gate (J1 F1 0.35 vs R0 0.64) and was kept under the fixed fallback ladder. The diagram's limitations line says "small local judges below their development gate". | paper Table III; D-48 to D-52 |

## B. Details not verifiable, or deliberately simplified

1. **Experiment links as tags, not arrows.** E2, E3 and E4 are shown as tagged boxes in sections E and F, not as connectors from section I. This keeps the diagram readable; the I-section note states the mapping.
2. **PR-AUC.** The source computes it only for the SC vote share. Other arms emit a descriptive confidence that is not used as a score, so the diagram lists PR-AUC only for SC.
3. **"Flip" definition shortened.** The paper also requires the test to pass again on a re-run. The diagram's "some mutant makes the test pass" leaves out that re-run condition for space.
4. **Debate argument length.** `config.py` sets `MAX_ARGUMENT_WORDS = 150`. The paper does not state it, so the diagram leaves it out. The summary-field word limit in the output schema was also not verified and is not shown.
5. **Call-site limits for S2.** `MAX_CALL_SITES = 5` and `CALL_SITE_CONTEXT_LINES = 5` are in `config.py`. They are left out for space; the diagram says only "call sites".
6. **Superseded model identifiers in `config.py`.** The `MODELS` dictionary still names the API models from the original plan. The executed models come from `configs/local_models.FROZEN.json` (D-57), and the diagram shows those.
7. **Mutation operators.** `config.py` lists eight Major operators for D2 (`MUTATION_OPERATORS`). The diagram says only "one killed Major mutant" and does not list them. The probe operators (ROR, AOR, COR, LVR, NEG, STD) are a separate engine, as stated in the paper.

## C. Tooling note

- **Exports.** draw.io Desktop is not installed, so the exports come from the official diagrams.net viewer engine running in headless Chrome. They are genuine diagrams.net renders, but not output of the desktop app's own export command.
- **Arial on other machines.** A machine without Arial may substitute another font when it opens the `.drawio` file. The PDF, SVG and PNG keep the rendered layout.
