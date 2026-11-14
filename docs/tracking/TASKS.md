# Tasks

`[x]` done and verified · `[~]` implemented, awaiting real data · `[ ]` open · `[!]` blocked

## Phase 3
- [x] Workspace audit (`INITIAL_AUDIT.md`)
- [x] Project structure, tracking documents, traceability matrix
- [!] Instructor feedback register — needs the authors' record of the feedback
- [x] D1 frame reconstruction + 25/project cap + 3/14 project split (312 → 234 methods)
- [x] B-side context extraction for all 234 focal methods
- [~] Test generation with G (code ready; needs API key + budget)
- [x] Execution harness (compile on B/F, prune, 3 fresh-JVM runs, timeout) — verified on Lang-1
- [x] Ground-truth labeller — verified (unit + Lang-1)
- [~] Dataset build: label store, instances, exclusions, 1:2 sampling + weights
- [ ] Label audit sheet generator (100 dev labels, two raters) and κ report
- [ ] Spec leakage audit sheet (60 specs) and κ report
- [x] Evidence packages S0/S1/S2 + leakage checks
- [~] Spec Inferencer (S2, S2′)
- [x] Arms DA, KA, R0, J1, SC, SC-T, DEB; ablations A1, A2, A3, A4, A5a, A5b
- [x] Budget-guarded resumable LLM client; concurrent runner
- [ ] Prompt development (≤5 rounds/prompt, dev split) and freeze with MANIFEST.json
- [ ] J1 prompt paraphrases ×2 (R4) — written on dev split before freeze
- [!] Pilot gates P1–P5 — need generation
- [!] E1–E3 main factorial (3 levels × 3 arms × 3 reps + SC-T)
- [!] E4 ablations
- [!] D3 GitBug-Java — Docker unavailable
- [!] E5 M2 cross-model
- [x] Analysis pipeline, tables, figures (validated on mock data)
- [ ] Phase 3 report final (results sections)

- [x] Leakage guard on live path; budget journal; provider pins; scope lock (dev-only pilot)
- [x] GLMM implemented + simulation-validated (not run on real data)
- [x] D2 mutant build (local)
- [ ] X-07 sampling decision (pending author review)

## Phase 4
- [x] Springer Nature template (official v3.1 ZIP) installed; manuscript compiles (17 pp. with placeholders)
- [x] Title, abstract skeleton, keywords, Introduction, Related Work, Methodology, Experimental Setup, threats, declarations
- [x] Bibliography: 36 entries, DOIs checked against Crossref; every entry cited, every citation resolved
- [x] Author emails / corresponding author (Hafiz Huzaifa Ahmed, corresponding; Saad Ilyas)
- [ ] Results, comparison (quantitative), ablation, discussion, conclusion, abstract numbers — after experiments
- [ ] Final visual inspection of the PDF
