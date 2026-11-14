# OSF-ready outline: one consolidated RQ4 replication on fresh data (journal follow-up)

**Status: outline for the authors; not registered, not published.** Answers review item G1: D-82 to D-111 are a chain
of follow-ups, each chosen after earlier results; the decision log is internal provenance (git commits), not an
external, time-stamped preregistration. For the journal version, RQ4 is re-tested once, on data no analysis has touched,
with every hypothesis in one document and one Holm family, registered on OSF before any call. Nothing below is run until
the authors register it.

## 1. Title and authors
"Keep unless unanimous and disagreement escalation for LLM failure triage: a preregistered replication." Authors: TBD.

## 2. Data (fresh; none of it judged or analysed before registration)
- **Primary:** real faults from the 78 focal methods excluded by the per-project cap (Lang 26, Math 44, Mockito 8;
  `data/processed/split_manifest.json`), plus any further frame methods made available by lifting the cap, generated
  with the frozen generator G, executed and labelled with the unchanged buggy/fixed rule. Labels computed and sealed
  before any judge call.
- **Secondary (if available):** bugs fixed after every judge's release date (release-date evidence recorded per model).
- Unit of analysis: bugs (cluster bootstrap), with tests nested in bugs.
- Sample-size target from `results/revision/wp18_sample_size.json`: ≥ 257 bugs for an MDE of 0.08 on a DEB−SC-type
  contrast; RQ4's contrasts are on PF tests lost and bugs lost, so the binding constraint is the number of bugs with a PF
  test (state the target and the stopping rule; no optional stopping).

## 3. Hypotheses (one Holm family, α = 0.05)
| ID | Hypothesis | Metric | Test |
|---|---|---|---|
| R-1 | KUU loses fewer bug-revealing tests than M1 DEB | PF tests lost | paired bug bootstrap, one-sided |
| R-2 | KUU loses fewer bugs (no PF test kept) than M1 DEB | bugs lost | as above |
| R-3 | KUU-NG loses fewer bugs than M1 DEB | bugs lost | as above |
| R-4 | KUU removes more test faults than keep-all | TNR (> 0) | bootstrap CI excludes 0 |
| R-5 | The cascade's balanced accuracy exceeds KUU's | balanced accuracy | paired, one-sided |
| R-6 | Cascade non-inferior to frontier DEB on every instance at −0.05 | balanced accuracy | one-sided, margin |
Balanced accuracy and rate metrics are used instead of F1 (prevalence-independent). Exploratory, labelled so and outside
the family: AUROC/AUPRC, top-10/20/30% inspection with bug-level recall, k-of-3 curves, the learned vote stacker
trained on the original D1-test and frozen before registration.

## 4. Rules fixed in advance
KUU: discard only on three valid TF votes (M1, M2, E6b); missing or invalid = keep. KUU-NG: M1, E6b, Llama 3.1 8B.
Cascade: disagreement → frontier DEB; missing frontier answer = keep. Frozen prompts, decoding and seeds rule.
Invalid-output coding stated per rule (primary arms TF; panels keep) with a sensitivity analysis.

## 5. Exclusions
Leakage-guard aborts excluded from every rule at that level (D-70 rule), counted and characterised by label and by
matched string kind (D-121 template). AMB excluded; sensitivity with AMB as PF/TF.

## 6. Analysis plan
Bug-level cluster bootstrap, 10,000 resamples, seed fixed in the registration; Holm over R-1…R-6; effect sizes with
95% CIs; no subgroup analysis is confirmatory.

## 7. Deviations policy
Any deviation is written in the decision log with a timestamp and reported in the paper with its reason.

## 8. Author actions before registration
Create the OSF project; upload this document, the frozen config hash, the generator and judge digests, the sealed
label hash; record the registration DOI in the paper. None of these has been done.
