# Final verification report

Date: 2026-11-14. Branch `research-extension`. Two rounds: D-153 (restructuring to the Phase 4 brief) and D-154
(authors' instructions: IEEE format, affiliation, declarations, links, simplified diagram, comparison table, public
repository). No experiment, model call, run, dataset change or frozen-file edit was made.

Verdicts: **Complete** · **Partially complete** · **Not complete**.

## 1. Deliverables

| Deliverable | File(s) | Built from |
|---|---|---|
| Final paper (PDF + LaTeX), IEEE | `PHASE4_FINAL_PAPER.pdf`, `.tex`, `.bbl` | hand-maintained source; numbers from `generated/numbers_v2.tex` |
| Supplementary material, IEEE | `PHASE4_FINAL_SUPPLEMENT.pdf`, `.tex`, `.bbl` | `build/make_supplement.py` (from the `_v2` appendices, read only) |
| Defence deck | `DEFENSE_DECK_FINAL.pptx` (25 main + 12 backup, notes on all 37) | `build/build_deck_final.py` |
| Architecture diagram | `figures/fig_final_architecture.drawio` (editable), `.tex`, `.pdf`, `.png` | `build/make_architecture.py` |
| Charts | `figures/fig_final_confirmation.*`, `figures/fig_final_wdp.*` with `_data.csv` | `build/make_figures_final.py` (frozen JSON) |
| Build and audit | `build/build_final.py`, `build/audit_final_numbers.py` | — |
| Documents | `SUBMISSION_REQUIREMENTS_AUDIT.md` (pre-edit audit), `PHASE2_TO_PHASE3_TRACEABILITY.md`, `MANUSCRIPT_REVISION_LOG.md`, `PRESENTATION_STORYBOARD.md`, this file | — |
| Public repository | <https://github.com/hafizhuzaifaahmed/llm-failure-triage> | clean snapshot of this commit (section 7) |

Kept unchanged: V1 paper and deck (`paper/`), the `_v2` paper and deck, the Phase 2 submission, every result, ledger,
configuration and earlier decision record.

## 2. Manuscript checks

| Check | Result | Verdict |
|---|---|---|
| Template | IEEE journal (`IEEEtran`), IEEE reference style | Complete |
| Sections 1–15 in order | Title/authors, Abstract, Index Terms, I Introduction, II Related Work, III Proposed Methodology, IV Experimental Setup, V Results and Analysis, VI Comparison with Base Papers, VII Ablation Study, VIII Discussion, IX Conclusion and Future Work, Data and Code Availability, References; appendices in the supplement | Complete |
| Page limit (8–12 pp.) | 10 pages including references; text ends on p. 9 | Complete |
| Abstract 150–250 words, five components, numbers | 249 words | Complete |
| Keywords 4–6 | 6 | Complete |
| Authors and affiliation | names only, no e-mails; "Department of Artificial Intelligence & Data Science, School of Computing, FAST-NUCES" | Complete |
| Related-work comparison table | Table I | Complete |
| Methodology incl. architecture, maths, pseudocode, changes after Phase 2 | §III, Fig. 1, Eqs. (1)–(2), Algorithm 1, Table III (changes, cited from §III-B and §V-C); the separate changes subsection was removed at the authors' instruction (D-156) | Complete |
| Setup incl. dataset link, splits, hyperparameters, hardware, seeds | §IV with the Defects4J link, Table IV | Complete |
| Results with statistics; negative and inconclusive results visible | §V | Complete |
| Base-paper comparison (summary, quantitative with *, methodological, improvement, fairness) | §VI, Tables X–XI | Complete |
| Ablation | §VII, Table XII | Complete |
| Registered vs exploratory distinguished | Table V and a status statement at every exploratory or registered result | Complete |
| Declarations | Data and Code Availability (repository, dataset, registration); funding, conflicts, acknowledgements, author contributions and the AI-tool declaration removed at the authors' instruction (D-155) | Complete as instructed (the Phase 4 brief lists conflict-of-interest, funding and AI-tool statements; the authors chose to omit them) |
| Third person, no placeholders | no `[TODO]` or `[AUTHOR INPUT]` remains | Complete |

## 3. Numerical checks

`build/audit_final_numbers.py` reads the frozen JSON directly, not the number build: **24 of 24** headline values
appear in the paper text (C1 +0.028 [−0.137, 0.274]; C2 +0.243 [0.114, 0.372], Holm p 0.0024; C3 Holm p 0.1422; C4
Holm p 1.0000; 572 tests, 104 bugs, 21 with a bug-revealing test; WDP +0.104 [0.037, 0.201], 0 of 55 at level U,
bound 0.067; H1–H3b deltas and Holm p). The deck shows the same values (C1/C2 intervals as plotted shapes). Paper,
supplement and deck read one numbers file; no unresolved macro (`??`) in either PDF; the deck builder raises on any
untranslated LaTeX. Chart values (`*_data.csv`) equal the paper's macros. Speaker-note numbers were checked against
the macros. Verdict: Complete.

## 4. References

Every key cited in the paper and the supplement has a bibliography entry, and every printed reference is cited
(scripted check). No reference was added; the bibliography is `_v2`'s (Crossref-checked in
`paper/verification/REFERENCE_VERIFICATION.md`, additions full-text checked in
`docs/research_extension/LITERATURE_VERIFICATION_FULLTEXT.md`). No new DOI lookup was made. Verdict: Complete.

## 5. PDF checks

Both documents build with no LaTeX error, no undefined reference or citation and no multiply-defined label. The
paper has no overfull box; the supplement keeps small overfull boxes inherited from the `_v2` tables. Every page of
both PDFs was rendered and inspected; nothing is clipped. Verdict: Complete.

## 6. PowerPoint checks

Opened read-only in PowerPoint and exported all 37 slides; the OOXML validator passes. Every slide was rendered and
inspected; overlaps found on slides 3, 11, 12, 16, 17, 21 and B6 were fixed and re-rendered. Speaker notes on all
slides. Slide 7 shows the simplified diagram; slide 16 is the comparison with the closest work; the closing slide and
backup B7 carry the repository and dataset links. Verdict: Complete.

## 7. Repository checks

| Check | Result |
|---|---|
| Local history | commits added on `research-extension`; no amend, rebase or reset |
| Frozen evidence; confirmation gate | unchanged; `pytest -k confirm_gate`: 9 passed |
| Public repository | a clean snapshot (one commit) of this tree, without `logs/` and `data/raw/llm_calls_*`: the full history cannot be pushed because it holds files up to 367 MB, above GitHub's 100 MB limit. The course assignment briefs (`docs/source_documents/Phase 03 …`, `Phase_04 …`) are not published. `docs/DEVELOPMENT_HISTORY.txt` lists the development commits cited in the papers |
| Secrets | the published tree was scanned for API-key patterns before the push |

## 8. Compliance summary

| Area | Verdict |
|---|---|
| Phase 3 compliance (7 requirements) | Complete; requirement 1's feedback part is answered by the authors' statement that no comments were given |
| Phase 4 compliance | Complete, with the authors' choice to omit funding, conflict-of-interest and AI-tool statements |
| Phase 2 → implementation alignment | Complete (`PHASE2_TO_PHASE3_TRACEABILITY.md`); D3, E5-R4 and the S2 audit not run and disclosed |
| Scientific corrections | Complete (`MANUSCRIPT_REVISION_LOG.md`) |

## 9. Remaining author actions

1. Rehearse with the speaker notes in `DEFENSE_DECK_FINAL.pptx` and pick the talk length (the storyboard gives a
   10-minute cut).
2. Optional: the OSF registration's template fields were reworded at deposit; the paper and supplement disclose this
   and state that the attached frozen bundle governs.
