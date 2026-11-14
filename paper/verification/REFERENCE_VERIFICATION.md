# Reference verification (2026-10-30)

Method: each DOI resolved through the Crossref REST API (`crossref_check.json`); title, year, venue,
volume/issue/pages and author list compared with `paper/references.bib`. Entries without a DOI were checked
against the primary source named below.

| Key | Phase no. | Check | Result |
|---|---|---|---|
| xie2026maco | [1] | Crossref | match (IST 195, art. 108098, 6 authors) |
| xu2026candor | [2] | Crossref | match (TOSEM, Just Accepted, art. 3803418) |
| liu2026jstestcraft | [3] | Crossref | match |
| gu2026testart | [4] | Crossref | match (8 authors) |
| hayet2025chatassert | [5] | Crossref | match (TSE 51(1) 305–319) |
| taherkhani2026valtest | [6] | Crossref | match (TSE 52(4) 1426–1445) |
| walczak2026context | [7] | Crossref | match (JSS 237, 112834) |
| li2026mitgen | [8] | Crossref | match (TOSEM 35(10), 39 pp.) |
| yaraghi2025target | [9] | Crossref | match (TSE 51(4) 1104–1133) |
| maddila2026agentic | [10] | Crossref | match (TSE 52(8) 2446–2462; 24 authors, cited "et al.") |
| mathews2026validate | [11] | Crossref | match (IEEE Software 43(1) 98–104) |
| zhao2026misguidance | [12] | Crossref | match (PACMSE 3(ISSTA) 2589–2612) |
| zhao2026replication | — | Zenodo API | match (v1.0.0, 2026-07-18) |
| li2026selfrepair | [13] | arXiv abs page | match; comment "Accepted at ASE 2026"; no proceedings DOI yet |
| fu2026javaoracle | [14] | Crossref | match (FSE Companion '26, 1605–1613) |
| barr2015oracle | [15] | Crossref | match |
| just2014defects4j | [16] | Crossref | match |
| herzig2015alarms | [17] | Crossref | match |
| jiang2017alarm | [18] | Crossref | match |
| du2024debate | [19] | carried from Phase 2 (PMLR 235) | no DOI; not re-fetched |
| wang2023selfconsistency | [20] | carried from Phase 2 (ICLR 2023) | no DOI; not re-fetched |
| huang2026ult | [21] | Crossref | match |
| silva2024gitbug | [22] | Crossref | match (MSR 2024, 118–122) |
| dietterich1998tests | [23] | Crossref | match |
| holm1979 | [24] | no DOI (JSTOR) | carried |
| efron1993bootstrap | [25] | book | carried |
| wilcoxon1945 | [26] | Crossref | match (Crossref lists start page 80 only) |
| chicco2020mcc | [27] | Crossref | match |
| saito2015pr | [28] | Crossref | match |
| lakens2017equivalence | [29] | Crossref | match |
| wohlin2012experimentation | [30] | Crossref | match |
| cohen1960kappa | [31] | Crossref | match |
| arcuri2011guide | [32] | Crossref | match |
| defects4j301 | [33] | git tag on disk | tag v3.0.1, commit 6d54320e |
| bates2015lme4 | [34] | Crossref | match |

Open: [19], [20], [24], [25] were not re-fetched in this session (no DOI); they are standard and carried from
the authors' Phase 2 verification. Re-check before final submission if required.
