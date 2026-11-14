# Program Fault or Test Fault? LLM Triage of Failing Generated Unit Tests and a Registered Test of Mutation Evidence

Code, data and paper for the study by Hafiz Huzaifa Ahmed and Saad Ilyas (Department of Artificial Intelligence &
Data Science, School of Computing, FAST-NUCES). A failing LLM-generated unit test is judged program fault (PF) or test
fault (TF) by local open-weight LLM judges (one-shot judge, self-consistency, a token-matched arm and an adversarial
debate) and scored against labels from executing each test on the buggy and the fixed Defects4J version. A later study,
registered on OSF (`kp79c`), tests whether re-running a failing test on single-edit variants of the method under test
identifies the faulty side. All models ran locally through Ollama: **zero API cost**.

Repository: <https://github.com/hafizhuzaifaahmed/llm-failure-triage>. Dataset: Defects4J 3.0.1,
<https://github.com/rjust/defects4j> (tag v3.0.1).

## Final submission (Phase 4)

| File | What it is |
|---|---|
| `phase4_v2/PHASE4_FINAL_PAPER.pdf` (`.tex`) | the final paper, IEEE format |
| `phase4_v2/PHASE4_FINAL_SUPPLEMENT.pdf` (`.tex`) | supplementary material (extended results, registration, traceability) |
| `phase4_v2/DEFENSE_DECK_FINAL.pptx` | the defence presentation, with speaker notes |
| `phase4_v2/figures/fig_final_architecture.drawio` | editable architecture diagram |
| `phase4_v2/README.md` | how the paper, supplement, figures and deck are built; every number comes from committed results |
| `phase4_v2/FINAL_VERIFICATION_REPORT.md` | what was checked before submission |

Earlier versions are kept for provenance: `paper/` (the first Phase 4 paper and deck) and `phase4_v2/*_v2.*`.

Licences: code MIT (`LICENSE`); data, see `DATA_LICENSE.md`. Cite with `CITATION.cff`. Model weights are not
included. The paid-API configuration of the original design was withdrawn before any call (`configs/WITHDRAWN.md`).

## Layout

```
src/triage/            the pipeline: frame, generation, execution, labelling, evidence packages, arms, local LLM client,
                       leakage guard, metrics, bootstrap/Holm statistics, analysis, figures
src/java/              JUnit single-method runner (fresh JVM per run)
scripts/               one CLI per stage; scripts/local/ (Ollama sessions), scripts/wsl/ (Defects4J side),
                       scripts/analysis/ (post hoc and exploratory analyses), scripts/paper/ (numbers map, PDFs),
                       scripts/audit/ (label-audit kit), scripts/planning/ (projections; nothing run)
configs/               local_models.FROZEN.json (the frozen protocol), experiments/, scope, the 35b profile
prompts/               prompt sets; the frozen set is local_m1b
data/                  processed instances and samples, ground-truth store (labels), raw call logs
results/               runs_local/<experiment>/ decisions; heldout/analysis_final/ (all reported results);
                       revision/ (review-response analyses and local runs, D-112 onward, post hoc or exploratory)
paper/                 first Phase 4 paper (Springer Nature LaTeX); generated/ holds the resolved numbers
phase4_v2/             final paper and supplement (IEEE), defence deck, figures and their build scripts
docs/                  decisions (DECISIONS.md), deviations, progress, audit kit, paper support documents
tests/                 unit tests (pytest)
```

## Reproduce

**1. Re-derive every reported number without any model call** (Python 3.14 with `env/requirements*.txt`):

```bash
python -m pytest
```

```bash
python scripts/analyze.py --runs results/runs_local/LOCAL_HO_E1E3_M1 results/runs_local/LOCAL_HO_E4_M1 --dataset D1 --split test --out results/heldout/analysis_final/D1_M1
```

The full list of analysis commands (D2, M2, R3, exploratory) is in `results/heldout/analysis_final/MANIFEST.json`;
re-running them reproduces the committed outputs byte for byte (checked under D-79). Then rebuild the numbers map
and the paper:

```bash
python scripts/paper/build_numbers.py --check
```

```bash
cd paper && latexmk -pdf PHASE4_RESEARCH_PAPER.tex
```

**2. Re-run the experiments** (Windows 11, NVIDIA GPU with 12 GB, Ollama 0.40.13, WSL2 Ubuntu 22.04 with OpenJDK 11
and Defects4J 3.0.1): pull the three models at the digests in `configs/local_models.FROZEN.json`, start the frozen
server (`scripts/local/start_ollama_server.ps1`), pass `python scripts/local/session_check.py --start`, then follow
`docs/local_models/HELDOUT_SESSION_PLAN.md` and `docs/local_models/ZERO_COST_REPRODUCIBILITY_PLAN.md`. Calls are seeded
and logged; repeated judgements were byte-identical in the non-determinism check, but a re-run on other hardware or
drivers is a new run, not a replay.

**3. Large files.** Raw model-call logs (`data/raw/llm_calls_*`) and inference-server logs (`logs/`) are not in this
public repository: single files exceed GitHub's 100 MB limit (the largest is 367 MB). Every parsed decision and every
analysis output is included, so everything in step 1 runs without them, except the cost/latency table
(`scripts/analysis/cost_latency_s1.py`), which reads the raw call log. Commit hashes cited in the papers and the
decision log refer to the authors' development history; `docs/DEVELOPMENT_HISTORY.txt` lists those commits.
