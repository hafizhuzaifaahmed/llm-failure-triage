# Phase 4 `_v2` manuscript and defence deck

Revised manuscript and defence deck after the CFP confirmation (OSF kp79c) and its independent audit. They are
**copies**: the submitted originals in `paper/` are unchanged.

| File | What it is |
|---|---|
| `PHASE4_RESEARCH_PAPER_v2.tex`, `.pdf` | the revised manuscript (33 pages) |
| `DEFENSE_DECK_v2.pptx` | the revised defence deck (18 main and 12 backup slides) |
| `references_v2.bib` | the original bibliography plus the entries added for the revision |
| `generated/numbers_v2.tex` | every number the manuscript prints, as `\V{key}` macros |
| `NUMBERS_MAP_v2.csv` | each number with its source file and the field or pattern it was read from |
| `generated/qualitative.tex`, `figures/`, `sn-jnl.cls`, `sn-mathphys-num.bst` | byte-for-byte copies of the assets the manuscript needs, so that it builds here on its own |
| `build/` | the build scripts for this folder |

## Build

From the repository root:

```
python phase4_v2/build/make_paper_v2.py        # .tex and .bib, from the original manuscript and bibliography (read only)
python phase4_v2/build/build_numbers_v2.py     # numbers_v2.tex and NUMBERS_MAP_v2.csv, from committed result files
python phase4_v2/build/build_deck_v2.py        # the deck, from the original deck's template (read only)
cd phase4_v2 && latexmk -pdf PHASE4_RESEARCH_PAPER_v2.tex
```

Every output, including LaTeX's auxiliary files, is written inside this folder. The scripts only read from
`paper/`, `scripts/paper/build_numbers.py` and the committed result files.

## Why this folder exists

The `_v2` files were first written under `paper/` and `docs/paper/` (commits `516ef6a` to `6e190c8`). Both are
immutable paths of the registered confirmation's gate (`scripts/extension/confirm_gate.py`,
`check_nothing_frozen_changed`), which compares them with `master` and does not inspect commit history. The gate
test failed while the files were there. They were moved here (decision D-150), and the gate passes again; the gate
itself was not changed. A folder under `deliverables/` was considered first and not used: `.gitignore` ignores
`deliverables/` as a whole (it holds packaged zip bundles), so tracked sources there would have needed a forced add
and any new file would have been silently untracked.

## Status of the content

- The registered confirmation is printed as registered. The audit's qualifiers, the literature positioning and the
  limitations follow `docs/research_extension/PUBLICATION_STRATEGY.md`.
- **Whole-method dependence probes (WDP) are reported as an exploratory, retrospective result** (paper Section 10,
  Table 12; deck slide 16): protocol frozen internally in Git before the runs (`08ec9af`), not externally
  preregistered, designed after the confirmation outcomes were known. Every WDP number comes from
  `results/extension/wdp/wdp_analysis.json`. The only interpretation review is the Claude Opus 5.5 review
  (`docs/research_extension/WDP_INTERPRETATION_REVIEW.md`); the Fable 5.2 review was waived by the authors (D-152).
  The text reports an exploratory result; it does not claim that WDP is validated, safe, generalisable or externally
  confirmed.

## Known limitations

1. The manuscript source keeps a comment line from its earlier location: `%% Rebuild: … (in paper/)`. It is not
   printed. It was kept so that the source stays byte-identical to the reviewed version; the build instructions
   above are the current ones.
2. The scripts' generated header comments and the numbers map's "where used" column still name the earlier paths
   (`scripts/paper/…`, `docs/paper/…`, `paper/…`), for the same reason.
3. The earlier copies of the build scripts remain in `scripts/paper/` (`make_paper_v2.py`, `paper_v2_text.py`,
   `build_numbers_v2.py`, `build_deck_v2.py`). **Do not run them**: they write into `paper/` and `docs/paper/` and
   would make the gate fail again. They were left unchanged on instruction; removing them needs the authors'
   approval.
4. Submission tasks for the authors: the AI-use declaration (it must cover both Claude Opus 5.5 and Claude
   Fable 5.2, worded to the target venue's policy), eight `[TODO]` placeholders, and a visual check of the deck
   in PowerPoint.

## Final paper, supplement and deck (D-153)

| File | What it is |
|---|---|
| `PHASE4_FINAL_PAPER.tex`, `.pdf` | the final submission paper (IEEE journal format, Phase 4 section order, 10 pages with references) |
| `PHASE4_FINAL_SUPPLEMENT.tex`, `.pdf` | the `_v2` appendices plus the full registered-confirmation report (generated, IEEE format, tables S1...) |
| `DEFENSE_DECK_FINAL.pptx` | the integrated defence deck (25 main + 12 backup slides, speaker notes on all) |
| `figures/fig_final_*` | as-implemented architecture (`.drawio` editable, TikZ, PDF, PNG) and two charts with their data CSVs |
| `SUBMISSION_REQUIREMENTS_AUDIT.md`, `PHASE2_TO_PHASE3_TRACEABILITY.md` | the audit written before any edit |
| `MANUSCRIPT_REVISION_LOG.md`, `PRESENTATION_STORYBOARD.md`, `FINAL_VERIFICATION_REPORT.md` | what changed, the deck's story, and what was verified |

Build, from the repository root:

```
python phase4_v2/build/make_figures_final.py     # charts from the frozen JSON
python phase4_v2/build/make_architecture.py      # architecture: .drawio + TikZ -> PDF/PNG (needs pdflatex, pdftoppm)
python phase4_v2/build/make_supplement.py        # supplement source from the _v2 appendices (read only)
python phase4_v2/build/build_final.py            # LaTeX for paper and supplement (xr cross-references)
python phase4_v2/build/build_deck_final.py       # the deck (python-pptx)
python phase4_v2/build/audit_final_numbers.py    # independent check of headline numbers against the frozen JSON
```

The final paper and deck read every number from `generated/numbers_v2.tex`, the same file as the `_v2` manuscript.
Public repository: https://github.com/hafizhuzaifaahmed/llm-failure-triage (a clean snapshot; see `FINAL_VERIFICATION_REPORT.md`, section 7).
