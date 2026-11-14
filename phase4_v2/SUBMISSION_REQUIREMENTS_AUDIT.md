# Submission requirements audit (Phase 3 and Phase 4)

Status: initial audit 2026-11-14, against `phase4_v2/PHASE4_RESEARCH_PAPER_v2.tex` / `.pdf` (34 pages) and
`phase4_v2/DEFENSE_DECK_v2.pptx` (30 slides) at commit `27a767b`. The final state after revision is in
`FINAL_VERIFICATION_REPORT.md`. Assignment texts: `Phase 03 - Implementation.pdf`,
`Phase_04_-_Research_Paper_Writing.pdf` (both read in full).

Legend: **Met** · **Partly met** · **Not met** · **Author input required**.

## A. Phase 3 — implementation and experimental evaluation

| # | Requirement | V2 state | Verdict | Action |
|---|---|---|---|---|
| 3.1 | Implement the Phase 2 methodology; incorporate the instructor's feedback; document changes | DEB, all baselines and the full factorial are implemented and run; changes documented (Appendix A of V2). Instructor feedback: **not recorded anywhere**; V2 carries a `[TODO]` | Partly met / **Author input required** | Keep an explicit author placeholder; do not invent feedback |
| 3.2 | Dataset, preprocessing, splits, implementation details | Present (Sec. 4) | Met | Add a population-flow table and a reproducibility table |
| 3.3 | Baselines with all essential metrics | DA, KA, R0, J1, SC, SC-T, DEB with F1, MCC, P, R, P_adj, lost, invalid | Met | Keep every baseline |
| 3.4 | Graphs and visualisations | 9 figures; the architecture figure is the Phase 2 *design* diagram (shows D3 as if part of the pipeline) | Partly met | New as-implemented architecture; new charts for the registered confirmation and WDP |
| 3.5 | Comparison with existing research; limitations of fairness | Present but scattered between Sec. 6 and Appendix B | Partly met | One dedicated section with summary table, quantitative table, fairness |
| 3.6 | Ablation studies | A1–A5 reported (exploratory, 1 rep) | Met | Add a per-ablation table: parent, change, tests, result, reading |
| 3.7 | Results analysis and discussion vs Phase 1–2 gaps | Present ("Were the gaps and objectives met?") | Met | Keep; add objective-level verdicts |

## B. Phase 4 — paper components

| # | Requirement | V2 state | Verdict | Action |
|---|---|---|---|---|
| 4.1 | One coherent story; every claim supported | Supported, but the story splits into a measurement study and a confirmation study with the methodology of the second one placed after the ablation | Partly met | Restructure so the story runs problem → design → measurement → why confirmation → confirmation → exploratory extension |
| 4.2 | Required sections **in the given order** (1 Title … 15 Appendix) | Order broken: Sections 8–10 (probes, registered confirmation, surviving signal) sit between *Ablation* (7) and *Discussion* (11); the probe methodology is not in *Proposed Methodology* | **Not met** | Move probe/confirmation design into Methodology and Setup, their results into Results |
| 4.3 | Dedicated comparison with base papers (summary table, quantitative table with *, methodological comparison, improvement analysis, fairness) | All five elements exist, but the tables live in Appendix B | Partly met | Bring both tables into the main section |
| 4.4 | Architecture diagram, results tables, performance graphs, ablation results, qualitative examples; high resolution, numbered, cited | Architecture is a raster PNG of the Phase 2 design; qualitative examples in appendix | Partly met | Vector, as-implemented architecture with editable source |
| 4.5 | Ablation, discussion, limitations, failure cases; gaps met? | Present | Met | Keep |
| 4.6 | References: consistent style, recent, every citation listed and vice versa | 55 bib entries, 53 distinct keys cited, Springer `sn-mathphys-num` | Unverified | Run a cite/bib cross-check on the final source |
| 4.7 | Recognised template; original; AI use declared | Springer Nature `sn-jnl` (iicol); AI declaration names Claude Opus 5.5 only and carries a `[TODO]`; the Fable 5.2 review (attempted, stopped at the usage limit, then waived, D-152) is not mentioned | Partly met | Accurate AI declaration covering both |
| 4.8 | Reproducibility: source, splits, hyperparameters, hardware, software, seeds, code link | All present except the public repository URL / DOI (`[TODO]`) | Partly met / **Author input required** | Keep the placeholder for the URL |
| S1 | Title: problem, approach, domain | "Program Fault or Test Fault? LLM Triage of Failing Generated Unit Tests and a Registered Test of Mutation Evidence" | Met | Keep |
| S1 | Authors, affiliation, contact email | Present | Met | — |
| S2 | Abstract: one paragraph, 150–250 words, actual numbers | ≈ 280 words (291 tokens incl. heading); numbers present | **Not met** (length) | Rewrite to ≤ 250 words |
| S3 | 4–6 keywords | 7 keywords | **Not met** | Reduce to six |
| S4 | Introduction with contributions as a short bulleted list and an outline | Present; contribution bullets are long paragraphs | Partly met | Shorten bullets |
| S5 | Related work by theme with summary table | Present (two tables) | Met | Merge into one summary table + positioning table |
| S6 | Methodology: formulation, architecture diagram, modules, maths, objective, pseudocode, changes after Phase 2 feedback | All present except the Phase 2 feedback paragraph (TODO) and the probe method (placed later) | Partly met | Add a change table; move the probe method here |
| S7 | Experimental setup | Present | Met | — |
| S8 | Results with statistical evidence | Present | Met | — |
| S9 | Comparison section | Present (thin in main text) | Partly met | see 4.3 |
| S10 | Ablation section | Present | Met | — |
| S11 | Discussion incl. threats to validity; gaps met | Present | Met | Add E5-R4 and spec-audit omissions to threats |
| S12 | Conclusion, no new information | V2 conclusion lists future work only; no new numbers beyond results | Met | — |
| S13 | Declarations: data and code availability, COI, funding, AI use | Present with 6 `[TODO]` items | **Author input required** | Resolve only what has a source |
| S14 | Complete reference list | Present | Unverified | cross-check |
| S15 | Appendix (optional) | 8 appendices (A–H), 15 pages | Met | Move to supplementary |
| Style | Formal, third person, no exaggeration | First-person plural ("we") throughout | **Not met** | Write the final paper in the third person, as the brief asks |
| Pages | "Keep within the page limit of the chosen template (typically 8–12 pages for journals)" | 34 pages; main text to the conclusion ends on p. 18 | **Not met** | Concise main paper (≤ 12 pages of text before references) + a separate supplementary document |

## C. Scientific-integrity findings (beyond the brief)

| # | Finding | Severity | Action |
|---|---|---|---|
| I-1 | E5-R4 (prompt paraphrases) was never run and V1/V2 never mention it | Moderate (silent omission of a planned experiment) | Disclose in the change table and threats |
| I-2 | The Phase 2 S2 specification-leakage audit (60 items) was not carried out and is not mentioned | Moderate | Disclose |
| I-3 | Label audit 71 vs planned 100 items (dev split had only 21 PF) | Low (disclosed numbers, not the shortfall reason) | State the reason |
| I-4 | "about 257 bugs rather than 60": the 60 is the number of bug clusters in the scored D1-test sample (bootstrap unit), while only 22 bugs carry a bug-revealing test; a reader can confuse the two | Low | Say "60 bug clusters (22 with a bug-revealing test)" |
| I-5 | PPT1 calls KUU "our rule" and treats it as the method; PPT2 corrected this | Moderate for the deck | Final deck: KUU is a baseline; DEB is the original proposed framework |
| I-6 | PPT2 has **no speaker notes** on any of its 30 slides; PPT1 has notes on all 65 | High for the defence | Write notes for every slide |
| I-7 | PPT2 compresses the whole original study (methodology, E1–E5) into two slides; the approved Phase 2 design (DEB, S0–S2, equal budget) is barely shown | High for the defence story | Rebuild Acts 2–4 |
| I-8 | The architecture figure is the Phase 2 design, not what ran (D3 appears) | Moderate | As-implemented diagram distinguishing executed, later and not-run paths |
| I-9 | Headline numbers (C1–C4, WDP, H1–H3b, E1) re-read from the frozen JSON with an independent script: **all match** the V2 macros | — | Keep the single numbers source (`numbers_v2.tex`) |
| I-10 | Citation cross-check of V2: every cited key has a bib entry; three bib entries are never cited (`qwen35_35b`, `saito2015pr`, `wohlin2012experimentation`) and so are not printed by BibTeX | Low | Cite or drop in the final bibliography |

## D. Author inputs that block full compliance (nothing will be invented)

1. The instructor's verbal feedback on the Phase 2 presentation, and what changed because of it (or a statement that no change was requested).
2. Funding statement (V2 suggests "no external funding" — unconfirmed).
3. Conflict-of-interest statement (V2 suggests "no competing interests" — unconfirmed).
4. Public repository URL and archived artefact DOI.
5. Acknowledgements wording (V2 thanks the instructor — unconfirmed).
6. Confirmation that the AI-use declaration matches the institution's policy.
7. Target page limit: this audit assumes the journal guidance (8–12 pages); if the instructor counts appendices, the supplementary document must be submitted separately.
