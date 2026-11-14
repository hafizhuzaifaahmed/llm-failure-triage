# Presentation storyboard: `DEFENSE_DECK_FINAL.pptx`

Built by `build/build_deck_final.py` (python-pptx; native shapes and charts; speaker notes on every slide).
25 main slides and 12 backup slides, 16:9. Every number is read from `generated/numbers_v2.tex`, the file the final
paper prints from, so the deck and the paper cannot disagree. The two earlier decks are unchanged:
`paper/DEFENSE_DECK.pptx` (PPT1, 65 slides, storytelling reference) and `phase4_v2/DEFENSE_DECK_v2.pptx` (PPT2,
30 slides, science reference, no speaker notes).

## What was taken from each earlier deck

| From PPT1 (storytelling) | From PPT2 (science) | New in the final deck |
|---|---|---|
| Concrete opening example (here: the Chart_18 `removeValue` test from the qualitative examples) | Registered confirmation slides and their status tags | Approved Phase 2 design shown as the proposed method (DEB diagram, S0–S2, equal budget) |
| Needle-in-a-haystack framing | KUU as a baseline, not a method | Implementation-changes slide (models, frame, WSL2, gate failure, D3 and R4 not run) |
| Gradual build-up of the method | C1–C4 readings, frames, Jackson concentration | Data-flow funnel; E2/E3 hypothesis table; E4 ablation forest; E5 run/not-run cards |
| Conversational speaker notes with "transition" lines | WDP slide with its full exploratory status | "Supported vs not claimed" slide; gaps-and-objectives verdict slide |

Corrected from PPT1: PPT1 called KUU "our rule". The final deck calls it a baseline and names DEB as the framework
proposed in Phase 2. No slide is more optimistic than the paper.

## Main slides

| # | Act | Assertion title | Status tag | Visual |
|---|---|---|---|---|
| 1 | — | Program fault or test fault? | — | title (dark) |
| 2 | 1 Problem | A failing test can be the only evidence of a bug | original | worked example, buggy/fixed outcome, repair consequence |
| 3 | 1 | Bug-revealing failures are needles in a haystack | original | three stat callouts |
| 4 | 2 Gap | Three gaps carried forward from the literature review | original | G1–G3 cards |
| 5 | 2 | Three approved questions, and three the results led to | original | RQ ladder with status pills |
| 6 | 3 Method | Ground truth comes from running the code, not from an opinion | original | labelling-rule grid |
| 7 | 3 | The pipeline as executed, including what did not run | — | simple as-implemented architecture, full width (from `.drawio`/TikZ source) |
| 8 | 3 | Same evidence, three specification levels | original | nested S0/S1/S2 boxes |
| 9 | 3 | Proposed framework: adversarial debate at an equal budget of five calls | original | DEB flow + arm grid |
| 10 | 4 Implementation | Implementation: what changed from the approved plan, and why | original | plan / executed / reason table |
| 11 | 4 | From 234 focal methods to 177 judged failures | original | funnel + D2 card |
| 12 | 4 | E1: the best judge barely beats keeping every failing test, and still loses half the bugs | confirmatory | stat callouts + native bar chart (PF lost) |
| 13 | 4 | E2 and E3: no detectable gain from documentation or from debate | confirmatory | H1–H3b table |
| 14 | 4 | E4: the judge reads the failure message; debate components add nothing | exploratory | native-shape forest of ΔF1 with CIs |
| 15 | 4 | E5 robustness: what was run, and what was not | — | six cards, not-run ones dotted grey |
| 16 | 4 | How this study compares with the closest triage work | original | comparison grid (five design properties, reported figures marked *) |
| 17 | 5 Findings | RQ4: judge-only rules trade lost bugs against removed wrong tests | fixed in advance | trade-off figure (post hoc) + KUU baseline cards |
| 18 | 5 | A new idea: ask the program, not another judge | exploratory | probe mechanism diagram |
| 19 | 5 | The pilot looked strong, but a pilot is not evidence | exploratory | pilot stats + why-register panel |
| 20 | 5 | Registered result: the flip did not replicate; decoupling held, with limits | registered | two native-shape forests (C1, C2 by frame) |
| 21 | 5 | Probe-based rules were inconclusive, and one lost a bug | registered | rules table (TPR, TNR, bugs lost) |
| 22 | 5 | What survived is a dependence check, and it is exploratory | exploratory · retrospective · not preregistered | native clustered column chart + qualifiers |
| 23 | 6 Conclusion | What the evidence supports, and what it does not | — | two columns |
| 24 | 6 | Gaps and objectives: measured as designed, answers mostly inconclusive | — | verdict rows |
| 25 | 6 | Limitations, next steps, and the take-away | — | dark close, Q&A, code and dataset links |

## Backup slides

B1 registration details · B2 power planning vs realised sample · B3 control group · B4 registered secondary analyses ·
B5 frames and projects · B6 thinking-enabled judge and frontier reference · B7 statistics and reproducibility ·
B8 label trust · B9 base-paper comparison · B10 evidence status · B11 independent audit and AI use · B12 likely
questions.

## Timing

About 20 minutes for the 25 main slides (≈ 50 s each; slides 12, 20 and 22 deserve the most time), leaving the
backups for questions. If the slot is 10 minutes, present 1–3, 5, 7, 9, 12, 13, 16, 17, 19, 20, 22, 23, 25.

## Design

White content slides, navy title and closing slides; Cambria headings, Calibri body. One colour per evidence class,
used the same way in the paper's Fig. 1: blue (original approved design), green (ground truth / registered), violet
(later investigations), orange (exploratory; wrong tests), grey (not run). Every result slide carries an
evidence-status tag in the top-right corner. No stock or generated imagery.

Round 2 (authors, 2026-11-14): title slide shows "Department of Artificial Intelligence & Data Science, School of Computing, FAST-NUCES"; slide 10 states that the instructor gave no comments on Phase 2; the comparison slide (16) is in the main sequence; the closing slide and backup B7 carry the repository and dataset links; the architecture slide uses the simplified diagram.
