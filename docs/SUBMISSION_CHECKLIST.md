# Submission checklist (due 15 Nov 2026)

All paths are under `C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4\`. Before submitting, rebuild everything
from the latest commit, so the files below match each other:

```
python scripts/paper/build_numbers.py --check
cd paper && latexmk -pdf PHASE4_RESEARCH_PAPER.tex && cd ..
python scripts/paper/render_phase3_pdf.py
python scripts/paper/build_deck.py --render
python scripts/paper/bundle_latex.py
python -m pytest -q tests
```

## Files to submit

| Deliverable | What the brief asks for | File |
|---|---|---|
| Phase 3 | Implementation and experimental evaluation | `docs\PHASE3_IMPLEMENTATION_AND_EXPERIMENTAL_REPORT.pdf` |
| Phase 3 | Reproducible code | the public GitHub repository (URL pending; see `docs\release\RELEASE_STEPS.md`) |
| Phase 4 | Research paper (PDF) | `paper\PHASE4_RESEARCH_PAPER.pdf` |
| Phase 4 | Editable LaTeX source | `paper\PHASE4_LATEX_SOURCE.zip` (compiles standalone; text identical to the PDF) |
| Defense | Slide deck | `paper\DEFENSE_DECK.pptx` (preview: `paper\DEFENSE_DECK_contact_sheet.png`) |
| Defense (for you, not to submit) | The hardest questions with answers | `docs\paper\DEFENSE_QA.md` |
| Defense (for you) | The independent mock review and how each objection is answered | `docs\paper\MOCK_REVIEW.md` |

## Remaining author items, in plain words

1. **Instructor feedback.**
   - What to write: what the instructor said about your Phase 2 presentation, and what you changed because of it (or
     that no change was asked for).
   - Where it goes: the red TODO in the paper's "Changes after Phase 2" paragraph, and the Phase 3 report's
     "Feedback" item.
   - Where to record it: `docs\tracking\INSTRUCTOR_FEEDBACK_REGISTER.md`.
2. **Declarations.** Confirm or correct three lines in the paper's Declarations:
   - no external funding;
   - no competing interests;
   - the acknowledgement of Atif Saeed (extend it if you like).
3. **Label audit — done (D-108).** Both sheets are scored; κ is in the paper, the report, the Q&A and the deck. The
   audit material ships with the release.
4. **GitHub and Zenodo (after your instructor approves).** The URL and DOI stay as TODOs until then. Follow
   `docs\release\RELEASE_STEPS.md`:
   - reserve the DOI;
   - create the empty public repository `llm-failure-triage` and send me its URL;
   - sign in when Git Credential Manager asks during the push;
   - publish on Zenodo.

   I then fill the URL and DOI in the paper, the report and `CITATION.cff`.
5. **API key — do this now.** E9b finished on 9 Nov (US$ 7.65 spent). Revoke the Anthropic key in the Console
   (Settings → API keys) and delete `env\.env`. Nothing else needs it.
6. **Deck check.** The deck was rewritten in plain English (22 main slides, 2 statistics backups, 29 question
   backups; 155 entrance effects). Open `paper\DEFENSE_DECK.pptx` in PowerPoint and click through it once in Slide
   Show. Automated checks confirmed PowerPoint reads every animation, but not that it plays. Read
   `docs\paper\STUDY_GUIDE.md` before the defense: it explains every decision in plain words.
7. **Page count — done.** The main text, through the Conclusion, is 12 pages (22 in all), within the brief's
   "typically 8–12", after adding RQ4, KUU-NG and the trade-off figure. The trade-off figure replaced the E1 bar chart,
   which moved to Appendix B with the E2 table; the base-paper summary table and the E5 robustness table are there too.
   The new title is "Program Fault or Test Fault? Evaluating and Improving LLM Triage of Generated Unit Tests".
8. **E7b.** Choose: keep GitBug-Java as future work (the default, D-103), or run it reframed as a generalisation
   check.
9. **Optional learned baseline (queue item 5) — not run.** A logistic regression on failure features, trained on the
   development split, would answer "does an LLM beat a simple trained classifier?". It needs its own pre-registration
   before any fit; say if you want it.
