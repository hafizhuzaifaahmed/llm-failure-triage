# Submission TODOs (authors only)

Every author TODO left before the 15 November 2026 submission, found by searching the sources, the generated
documents and the deck on 2026-11-11 (pass 3). None is filled here: each needs the authors' own information or decision.
Line numbers are in the **source** file; edit the source, then rebuild (`python scripts/paper/build_numbers.py`, then the
build commands in `docs/SUBMISSION_CHECKLIST.md`). Generated files (`docs/PHASE3_IMPLEMENTATION_AND_EXPERIMENTAL_REPORT.md`,
the PDFs) are overwritten by the rebuild.

## In the paper (`paper/PHASE4_RESEARCH_PAPER.tex`; red in the built PDF)

| # | Source line | Page in the PDF | What is there now | Input needed |
|---|---|---|---|---|
| 1 | 206 (§3, Experiments paragraph) | 7 | `\TODO{public repository URL and archived artefact DOI.}` | a URL (GitHub) and a DOI (Zenodo), available only after the release in `docs/release/PUBLISH_STEPS.md` |
| 2 | 328 (Acknowledgements) | 12 | `\TODO{authors to confirm or extend.}` after the thanks to the course instructor | a decision: confirm the sentence, or extend the thanks (people, institutions, compute) |
| 3 | 333 (Declarations: Funding) | 13 | `\TODO{authors to confirm: no external funding was received.}` | a factual confirmation, or the funder and grant number |
| 4 | 334 (Declarations: Conflict of interest) | 13 | `\TODO{authors to confirm: the authors declare no competing interests.}` | a factual confirmation, or the interests to declare |
| 5 | 335 (Declarations: Data availability) | 13 | `\TODO{archive location and DOI.}` | the archive (e.g. Zenodo) record and its DOI, same release as item 1 |
| 6 | 336 (Declarations: Code availability) | 13 | `\TODO{public URL.}` | the public repository URL, same as item 1 |
| 7 | 337 (Declarations: Use of AI-assisted tools) | 13 | `\TODO{authors to confirm wording against institutional policy.}` | a check of the paragraph against the university's / venue's AI-use policy, and any wording it requires |
| 8 | 372 (Appendix A, "Instructor feedback on Phase 2") | 14 | `\TODO{the instructor's verbal feedback on the Phase~2 presentation is not recorded ...}` | the instructor's feedback and what changed because of it, or a statement that no change was requested; also add it to `docs/tracking/INSTRUCTOR_FEEDBACK_REGISTER.md` |

The `\TODO` macro is defined on line 31; once every item is filled, a search for `\TODO{` in the `.tex` should find only
that definition.

## In the Phase 3 report (`docs/phase3/PHASE3_REPORT.src.md`)

| # | Source line | Line in the generated report | What is there now | Input needed |
|---|---|---|---|---|
| 9 | 40 ("Changes to the Phase 2 methodology") | 41 | `**TODO (authors):** state the feedback and what changed, or that no change was requested.` | the same instructor feedback as item 8 |
| 10 | 474 (reproduction steps) | 475 | `**TODO (authors):** public repository URL.` | the same URL as item 1 |

## In the deck (`paper/DEFENSE_DECK.pptx`)

No TODO text is on any slide or in any speaker note (checked slide by slide on 2026-11-11). What remains is manual:

| # | Where | Input needed |
|---|---|---|
| 11 | all 65 slides (23 main, then backup) | the authors click through the deck in PowerPoint: animations play in story order, the speaker notes read as intended, and slide 11 (thinking result), 19 (cascade with the fully local note) and 22–23 (findings, takeaways) say what the presenter will say |

## Not author TODOs, listed so nobody hunts for them

- `docs/paper/src/SESSION_CHECKLISTS.src.md` line 80, "TODO (authors): decide whether a paid frontier judge is in scope
  at all": a planning note from before E9; the authors decided it then (D-92 recorded it, D-96 approved E9, D-97 amended its design), so it needs no input for submission.
- `docs/paper/MOCK_REVIEW*.md`: quotations of earlier review rounds that mention TODOs; historical records, not edited.
- Plans that are not TODOs: the Sonnet factorial, OSF registration and recruiting independent raters stay plans
  (`docs/tracking/JOURNAL_FOLLOWUP_PLAN.md`); nothing here asks for them before submission.
