# Progress log

## PAUSED 2026-10-30 ~23:35 — resume here
- Awaiting the authors' explicit approval of `docs/PILOT_READINESS_REPORT.md`. **No paid call made; no
  `configs/budget.json` exists.** On approval: create it from `configs/budget.pilot.PROPOSED.json`; the authors
  set `OPENROUTER_API_KEY` themselves.
- X-07 sampling: PENDING author review (primary samples = within-project reading).
- Still open from the authors: instructor feedback text; X-01/D-18 provider-pin approval.
- D2: FINAL, 195/195 processed (148 methods with verified mutants, 284 mutants; Math_15 hit the 2 h analysis limit). ZIP rebuilt.
  `logs/build_d2_part3.log`). If it finished: `python scripts/summarise_d2.py`, update report §3, re-run
  `python scripts/package_project.py`. If it was interrupted: re-run `build_d2.py` (resumes; only Math_15 left).
  Optional later: single-worker retry of Math_16 `FastMath.cosh` (memory-killed).
- Last verified: 70 unit tests pass; Lang-1 integration PASSED; mock e2e clean; check_no_mock CLEAN; paper builds (17 pp).
- Latest ZIP: see newest file in `deliverables/` (rebuilt after D2 finished).

## 2026-10-30 — session 2: corrective verification pass (no paid calls)

Full detail: `docs/PILOT_READINESS_REPORT.md`.
- Leakage guard wired into `run_experiment.execute` and `Runner`; real runs refuse without full guard coverage.
  **Bug fixed:** ids shorter than 6 chars (e.g. `Cli_1`) were never checked.
- LLM client rebuilt: unknown price = hard error; write-ahead attempt journal; possibly-charged/orphaned attempts
  counted at maximum cost; provider-reported cost + generation id stored; provider pinned per model; replay mode.
- Providers verified on OpenRouter (M1 GMICloud fp8, M2 DeepInfra fp8, G OpenAI); 5.5% credit fee confirmed.
- GLMM implemented and validated: VB intervals under-cover (50–70%) → bootstrap intervals (X-06). Not run on real data.
- D2 implemented with Major; **bugs fixed**: offset semantics, CRLF offsets, unsorted seeded order. Full local run started.
- Audit sheet generator + scorer + instructions (sheets need real data).
- Sampling: zero-PF projects analysed; proportional reading adopted pending confirmation (X-07).
- **Bug fixed:** stale compile metadata after a re-checkout broke the Lang-1 integration run; re-run PASSED.
- Paper: data-availability and regeneration claims corrected, MitGen ref fixed, tables restructured; builds clean.
- Pilot estimate: 7,551 calls max, $8.57 expected, $15.91 conservative → requested ceiling $16.00.

## 2026-10-30 — session 1

**Done and verified**
- Read Phase 1, Phase 2 (incl. Appendix A and the architecture diagram), Phase 3 and Phase 4 briefs in full.
- Audit: working folder was empty; Defects4J 3.0.1 in WSL works (17 projects, 854 bugs); no model API key;
  no recorded spending approval; no recorded instructor feedback.
- Model availability: DeepSeek's own API no longer serves V3; V3-0324, Qwen3-235B-2507 and GPT-4.1 are
  available via OpenRouter (GPT-4.1 API removal announced for 2027-01-14).
- Implemented the full pipeline (`src/triage/`, 15 modules) and stage CLIs (`scripts/`).
- 35 unit tests pass. Real-B/F harness check on Lang-1 passes for all seven label rules plus NC pruning.
- Mock end-to-end run (synthetic, watermarked): 3,420 decisions, 0 errors, all tables and figures produced.
- D1 frame reconstructed: 312 focal methods / 220 defects (vs. 318/233 in [12]); capped to 234 / 167;
  split dev = Cli, Gson, Jsoup. Context extracted for all 234.
- Bugs found and fixed during validation: array types in qualified-name parsing; near-cubic Javadoc lookup
  on very large classes (Closure); undefined-metric CI crash; figure label collisions; BibTeX inline comments.
- Cost envelope at current list prices: ≈ $224 for the full Phase 2 programme (≈ $290 with 30% contingency).
- Paper: Springer template installed; manuscript compiles; references verified against Crossref.

**Blocked on the authors**
1. OpenRouter API key + approved spending ceiling (gates everything empirical).
2. Approval of the provider change (X-01).
3. The instructor's feedback on the Phase 2 presentation.
4. Author emails / corresponding author.

**Next (no approval needed)**
- D2 mutant pipeline; label-audit and spec-audit sheet generators; GLMM in `analyze.py`; paraphrase prompts.

**Next (after approval)**
- Dev-split generation (39 focal methods × 3 = 117 GPT-4.1 calls, ≈ $3.4) → execution → pilot gates P1–P5 → prompt freeze →
  test-split generation → main runs in Tier order.
