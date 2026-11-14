# Project fact base (research-extension workstream)

Status: verified against the checkout on 2026-11-11. Every row names the file or command it was read from.
Nothing here changes the primary study. Branch `research-extension`, cut from `master` at `5138443`.

## 1. Repository state and the commit discrepancy

| Fact | Value | Source |
|---|---|---|
| Working copy | `C:\Users\huzai\Downloads\Fast\Advance AI\Phase 3 and 4`, branch `master`, clean tree | `git status`, `git branch -a` |
| HEAD at start | `5138443` "Deck rebuilt on a clean tree (footer stamp 0c16659)"; 297 commits | `git log --oneline` |
| Deck stamp `0c16659` | The parent of HEAD ("Pass 3 rebuild"). All 65 slides carry it in the footer. The deck was built on the clean tree at `0c16659` and committed as `5138443`, so stamp and HEAD differ by design | `git log`; text extracted from `paper/DEFENSE_DECK.pptx` |
| Notes commit `3f320fa` | "Pass 2 checklist complete (D-130, D-131)", 12 commits before `0c16659`. It is an ancestor of HEAD, so the revision notes describe an older snapshot of the same line of history | `git log --oneline` |
| Resolution | Neither attachment describes the current checkout exactly. `5138443` is authoritative; it contains pass 3 (D-132, fully local cascade), which the pass-2 notes predate | — |
| Repository instructions | No `CLAUDE.md` or `AGENTS.md` in the repo. Rules live in `README.md`, `docs/tracking/DECISIONS.md` (133 rows, D-01 to D-132), `docs/local_models/*.md` | `ls`, `grep -c` |
| Unit tests at baseline | 356 passed (79 s) | `python -m pytest -q` on `5138443` |

### Materials that could not be read

- **`Pasted markdown(20261111-052523).md`** (prior research/revision notes) is not in the repository, `Downloads`, `Desktop`
  or `Documents` (searched by name and by modification date). Its content was not substituted. The repository's own
  record of the same passes was read instead: `docs/tracking/REVISION_CHECKLIST.md`, `REVIEWER_RESPONSE_MATRIX.md`,
  `JOURNAL_FOLLOWUP_PLAN.md`, `docs/paper/MOCK_REVIEW.md` and the decision log.
- **An external-style reviewer report** as a separate file was not found. The two mock-review rounds
  (`docs/paper/MOCK_REVIEW_round1_raw.md`, `_round2_raw.md`) and the response matrix are what the repository holds.

## 2. What the study is

Title: "Program Fault or Test Fault? Evaluating and Improving LLM Triage of Generated Unit Tests"
(`paper/PHASE4_RESEARCH_PAPER.tex`, 26 pp, main text ends p. 12). Authors Hafiz Huzaifa Ahmed and Saad Ilyas.

A failing LLM-generated JUnit test is classified **program fault (PF)**, meaning the test is right and the program is
wrong, or **test fault (TF)**. Labels come from execution only: PF = fails deterministically on the buggy version and
passes on the developer-fixed version; TF = fails on both with identical failure signatures; AMB = fails on both with
different signatures (excluded from the primary analysis). Source: `src/triage/labeling.py`, paper Table 2.

## 3. Data (verified counts)

| Set | What | Counts | Source |
|---|---|---|---|
| Frame | Defects4J 3.0.1, selection rule of Zhao et al. re-run | 1,758 candidates → 312 focal methods / 220 defects; per-project cap of 25 → **234 methods / 167 defects**; 78 methods excluded by the cap | `data/processed/split_manifest.json`, `frame_d1.jsonl` |
| Split | Seeded draw before generation | dev: 3 projects (Cli, Gson, Jsoup), 39 methods; held-out: 14 projects, 195 methods | `split_manifest.json` |
| Generation | Gemma 4 26B, 3 generations per focal method, buggy context | 2,909 test methods executed; 2,284 pass on B; 102 misguided; 518 NC | `dataset_summary_D1.json` |
| D1 labels | Real faults | 81 PF, 385 TF, 21 AMB | `labels_D1.jsonl` |
| D1-dev | | 21 PF, 89 TF, 8 AMB; 16 bugs, **5 bugs with a PF test** | computed from `labels_D1.jsonl` |
| D1-test | | 60 PF, 296 TF, 13 AMB; 76 bugs, **22 bugs with a PF test**, 95 focal methods, 11 projects with instances | same |
| D1-test judged sample | all PF, TF sampled 1:2 | 60 PF + 120 TF + 13 AMB = 193; 177 scored at S1 after 4 leakage aborts | `sample_D1_test.json`, paper §4 |
| D2 | One killed Major mutant inside a held-out focal method of the fixed version | 284 mutants → 468 PF, 349 TF, 65 AMB; judged sample 300, 270 scored, 64 bugs | `labels_D2.jsonl`, `sample_D2_test.json` |
| D3 (GitBug-Java) | Not run (no Docker; 2023 bugs predate every 2026 model anyway) | — | D-101, D-103 |

The bug is the independent unit. The paper's "60" is PF *tests*; they sit in 22 bugs. Any bug-level claim on D1-test
rests on 22 clusters.

## 4. Models and runtime

| Role | Model | Notes | Source |
|---|---|---|---|
| Generator G | `gemma4:26b` (Q4_K_M) | passed generator criteria on dev | `configs/local_models.FROZEN.json` |
| Judge M1 | `qwen3.5:9b` | primary; fails development gate G-d (F1 0.350 vs R0 0.642) | same; paper Table G6 |
| Judge M2 | `gemma4:12b` | shares G's family; fails G-d | same |
| Judge M3 ("E6b") | `ministral-3:14b` | third family; fails G-d | D-82 to D-85 |
| Judge NG | `llama3.1:8b` | fourth family (KUU-NG); fails G-d | D-109 |
| Exploratory | `qwen3.5:35b` | run last, never fed back | D-67 |
| Frontier reference | Claude Sonnet 5.5 (API, E9/E9b) | key since revoked; not gated | D-92 to D-104 |
| Runtime | Ollama 0.40.13, RTX 5070 Ti Laptop 12 GB, 31 GB RAM; WSL2 Ubuntu 22.04, OpenJDK 11, Defects4J 3.0.1 | | paper §4; checked 2026-11-11 |

Decoding for planned arms: temperature 0.7, top-p 1.0, 8,192 context, 512 output tokens, thinking disabled, seeded.

## 5. Resources checked on 2026-11-11

- GPU idle (312 MiB of 12,227 MiB used). 31.4 GB RAM, 317 GB free on `C:`.
- Ollama models present: `gemma4:26b`, `gemma4:12b`, `qwen3.5:9b`, `qwen3.5:9b-q8_0`, `qwen3.5:35b`,
  `ministral-3:14b`, `llama3.1:8b`, `mistral-nemo:12b`, `phi4:14b` (from `/api/tags`).
- **Side effect to disclose:** running `ollama list` during this check auto-started the default Ollama desktop server
  on port 11434. The study's runs use the frozen server started by `scripts/local/start_ollama_server.ps1`. No model
  was loaded and no call was made. Stopping the process was blocked by the session's permission mode, so it is still
  running; it must be stopped before any study session.
- WSL: `~/triage_work` holds 834 checkout directories (55 GB), Major is installed, 24 logical cores, 897 GB free.
  Execution-side experiments are therefore feasible without new downloads.

## 6. Standing rules found in the repository

1. A rule is written into `docs/tracking/DECISIONS.md` and committed before the result it governs.
2. Frozen: `configs/local_models.FROZEN.json`, prompts `prompts/frozen/local_m1b`, the label store, every committed run.
3. Never run tests or heavy CPU work while G generates (D-64). Never load the 35B model on the study server (D-60).
4. No paid API calls, external raters or OSF registration without the authors (decision of 2026-11-10, D-130).
5. Commits carry no AI attribution; push only when asked.
6. Numbers reach the paper only through `scripts/paper/build_numbers.py` and `docs/paper/NUMBERS_MAP.csv` (1,522 values).
