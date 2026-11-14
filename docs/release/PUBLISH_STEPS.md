# Publishing the code and data (steps for the authors)

Nothing here has been done; every step is yours. Nothing is pushed by the assistant.

**Status (2026-11-04, commit `fb6cc1f`).** Staged locally with `python scripts/release/stage_release.py`:
4,658 files, 494 MB in `dist/release/github/`, secrets scan clean. Two files exceed GitHub's limit and go to Zenodo only
(`dist/release/zenodo_extra_files.txt`, with SHA-256): `data/raw/llm_calls_local/qwen3.5_9b.jsonl` (367 MB) and
`logs/ollama_server/server_20261102_220520_heldout_s3.log` (139 MB). Re-stage after any later commit. Still open before
publishing, all yours:

- The label audit is not finished (both human sheets are blank). The export currently contains
  `docs/audits/kit/CALIBRATION_KEY.md` and `data/ground_truth_store/audit/label_audit_key.csv` (the automatic label of every
  audit item). Decide whether to hold them back until the audit is scored. The LLM rater's sheet is not in the export (it is
  sealed outside the repository; only its SHA-256 is committed in `docs/audits/kit/LLM_RATER_SEAL.json`).
- `results/quarantine_d87/` (17 unplanned phi4 calls, D-87) is in the export for audit; keep or drop it as you prefer, it is
  used by no analysis.
- Send the GitHub URL and the Zenodo DOI; they are then filled into `CITATION.cff`, `README.md` and the paper's Data and
  Code availability statements, and recorded as a D-entry.

## 0. Decide before you publish

- [ ] Licences: MIT for code (`LICENSE`), CC BY 4.0 proposed for the study's data (`DATA_LICENSE.md`). Change them now if needed.
- [ ] Remove anything you do not want public (e.g. `docs/audits/kit/CALIBRATION_KEY.md` until the audit is finished, rater sheets with names).
- [ ] Commit, then stage: `python scripts/release/stage_release.py` (GitHub folder) — it refuses to stage if it finds anything that looks like an API key or private key.

## 1. GitHub

1. Create an **empty** repository on github.com (no README, licence or .gitignore, so the first push does not conflict), e.g. `<your-account>/llm-failure-triage`. Public or private, your choice; Zenodo needs it public at release time.
2. In a terminal:

```bash
cd "dist/release/github"
```

```bash
git init -b main && git add -A && git commit -m "Code and data for the LLM failure-triage study"
```

```bash
git remote add origin https://github.com/<your-account>/llm-failure-triage.git
```

```bash
git push -u origin main
```

3. Check on github.com that `LICENSE`, `README.md` and `CITATION.cff` are recognised (the "Cite this repository" box appears).

## 2. Zenodo DOI

1. Sign in at zenodo.org with GitHub; under **GitHub** in your account settings, switch the repository **on**.
2. On GitHub, create a **release** (tag `v1.0.0`). Zenodo archives it and mints a DOI within minutes; the badge and DOI appear on the Zenodo record.
3. Files over GitHub's limit are listed in `dist/release/zenodo_extra_files.txt` (with sha256). Build the full archive with `python scripts/release/stage_release.py --zenodo` and upload `dist/release/zenodo_<commit>.zip` to the **same Zenodo record** as an additional file ("New version" → add file), or as a separate dataset record that links to the software record.
4. Fill the Zenodo metadata: authors and affiliations, the title, licence, keywords, and "is supplement to" the paper once it has a DOI.

## 3. Close the loop

- [ ] `CITATION.cff`: add `repository-code`, `doi`, `date-released`.
- [ ] Paper: replace the TODOs in Data availability and Code availability with the GitHub URL and the Zenodo DOI; rebuild (`python scripts/paper/build_numbers.py && cd paper && latexmk -pdf PHASE4_RESEARCH_PAPER.tex`).
- [ ] Record the release (URL, DOI, commit) as a D-entry.
