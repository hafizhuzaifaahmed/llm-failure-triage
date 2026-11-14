# Initial Audit — Phase 3 and Phase 4

Date of audit: 2026-10-30. Auditor: Claude Opus 5.5 (implementation assistant).
Everything below was checked against files, tools or live endpoints on this date.

## 1. What already exists

| Item | Location | Status |
|---|---|---|
| Phase 1 literature review (approved) | `docs/source_documents/AdvancedAI_Phase1_LiteratureReview (1).pdf`; editable copy in `../Assignment-1/` | Read in full |
| Phase 2 methodology (approved) + architecture diagram | `docs/source_documents/phase2/Phase_2_assignment/`; editable `.docx` in `../Phase 2/` | Read in full, including Appendix A prompt skeletons |
| Phase 3 / Phase 4 assignment briefs | `docs/source_documents/` | Read in full |
| Rubric | Google Classroom screenshots (category names and maxima only) | No expanded level descriptors found anywhere in the workspace |
| Working directory `Phase 3 and 4/` | — | **Was empty.** No Phase 3 code, data or results existed. |
| `../experiment/` | Harness for an *earlier, superseded* topic ("coordination residual", pre-registration drafts in `../superseded_drafts/`) | Not reused as research code; only its Defects4J install is reused |
| Defects4J 3.0.1 under WSL2 Ubuntu 22.04 | `~/experiment/defects4j` inside WSL (tag `v3.0.1`, commit `6d54320e`) | **Working.** 17 projects, 854 active bugs (counts verified per project). Earlier verification (2026-09-13) showed Lang-1 trigger test fails on 1b and passes on 1f. |
| Java | OpenJDK 11.0.32 (WSL) | Matches Defects4J 3.x requirement |
| Zhao et al. [12] replication package | `data/external/EvalAndMitigate` (GitHub commit `751f9f4`, identical to Zenodo v1.0.0, DOI 10.5281/zenodo.21428153) | Cloned. Contains fix metadata for 835 bug versions and the selection *procedure*, **but not the final list of 318 focal methods** (`data/prompts/*` is not committed). The frame must be reconstructed by re-running their documented rule. |

## 2. What has already been implemented

Nothing for this research topic. No generated tests, executions, labels, prompts or model outputs exist.

## 3. Experimental evidence that already exists

**None.** There are no research observations of any kind. Any number in the final paper must come from runs made after this audit.

## 4. What is missing for Phase 3

Everything from Stage 3 onward of the execution prompt: dataset frame, test generation, dual execution, labelling, evidence packages, all arms, all experiments, statistics, figures, report. This turn implements the infrastructure; experiments need the items in §7.

## 5. What can be prepared now for Phase 4

Title, authors, Introduction, Related Work (from Phase 1), Methodology and Experimental Setup (from Phase 2 + the implementation), threats to validity, declarations. Results, Comparison (quantitative part), Ablation and the abstract's numbers must wait for real runs.

## 6. Instructor feedback

**Not available.** Searched the whole `Advance AI/` tree for feedback, comments, slides and presentation notes (file names and contents): nothing found. The Phase 3 brief states feedback was given verbally in class. No methodological change is claimed as feedback-driven until the authors supply it (see `INSTRUCTOR_FEEDBACK_REGISTER.md`).

## 7. Model APIs and spending allowance

| Role | Phase 2 spec | Availability on 2026-10-30 | Price (per 1M tokens, in/out) |
|---|---|---|---|
| M1 | version-pinned DeepSeek-V3-family chat | **DeepSeek's own API no longer serves V3** (only `deepseek-flash` = V4.1-Flash and `deepseek-v4-pro`). V3 snapshots remain available via OpenRouter: `deepseek/deepseek-chat-v3-0324` | $0.29 / $1.14 (OpenRouter list) |
| M2 | version-pinned Qwen3-family instruct | OpenRouter `qwen/qwen3-235b-a22b-2507` | $0.09 / $0.55 |
| G | GPT-4.1 | OpenRouter / OpenAI `gpt-4.1` (2025-04-14 snapshot). **OpenAI announced API removal on 2027-01-14**; Azure removal 2026-11-04. Usable for this study's window. | $2.00 / $8.00 |

- **No API key** for OpenRouter, DeepSeek, OpenAI or Qwen/DashScope is configured in the environment.
- **No approved spending allowance** is recorded anywhere in the workspace. (An older `spend_model.py` mentions a "$50 pilot" for the superseded topic; it is not treated as approval for this study.)
- Using OpenRouter instead of the DeepSeek first-party API is a *provider* change, not a model change. It still needs your confirmation because the Phase 2 text implies the vendor API.

## 8. Genuine blockers

1. **API key + spending approval** (blocks test generation, so blocks every experiment).
2. **Instructor feedback content** (blocks the feedback register and the "changes after feedback" paper subsection; nothing else).
3. **Author emails / corresponding author** (blocks the final title block only).
4. **lme4 is unavailable** (no R on the machine). GLMM will be fitted with Python `statsmodels` (BinomialBayesMixedGLM) unless R is installed — recorded as a deviation.

Non-blockers resolved during the audit: Defects4J works; Java 11 present; network reaches GitHub, OpenRouter and Zenodo; MiKTeX `pdflatex`/`latexmk` present for the paper.
