# Reproducibility guide

## 1. Environment

**Execution side (Linux).** Ubuntu 22.04.5 under WSL2, OpenJDK 11.0.32, Perl 5.34, Defects4J 3.0.1
(tag `v3.0.1`, commit `6d54320e0db5a357f9ab38a8e4d2e5aead7e1c09`), Python 3.10 stdlib only. Exact values:
`env/environment_manifest.json` (re-record with `scripts/wsl/record_env.sh`). A reference `env/Dockerfile`
rebuilds the same stack where Docker exists (not used for our runs, deviation X-04).

Defects4J install (once):
```bash
git clone --branch v3.0.1 https://github.com/rjust/defects4j.git ~/experiment/defects4j
```
```bash
cd ~/experiment/defects4j && cpanm --installdeps . && ./init.sh
```
Environment variables read by the code: `D4J_HOME`, `TRIAGE_PERL5LIB`, `TRIAGE_WORK` (defaults in `scripts/wsl/run.sh`).

**Judging/analysis side.** Python 3.14.4 with `env/requirements.txt`:
```bash
python -m pip install -r env/requirements.txt
```

**External data.** Zhao et al. replication package, commit `751f9f4153fce0d55c111602a27e19009dec0721`
(identical to Zenodo v1.0.0, DOI 10.5281/zenodo.21428153):
```bash
git clone https://github.com/drixs2050/EvalAndMitigate.git data/external/EvalAndMitigate
```

## 2. Fixed randomness

All seeds are in `src/triage/config.py`: project split 20261007, per-project cap 20261008, TF sampling
20261009, adjudicator argument order 20261010 (derived per instance and replicate), bootstrap 20261011,
mutant selection 20261012. LLM sampling is stochastic by design (T = 0.7); replicates and the call log make
any run auditable and resumable, and the released call log reproduces every decision exactly.

## 3. Models and decoding

Requested model ids and roles: `configs` → `src/triage/config.py: MODELS`. Each call record stores the
requested id, the returned id, the serving provider, the full prompt, decoding parameters, token counts,
latency and cost (`data/raw/llm_calls/*.jsonl`). Judges: T = 0.7, top-p 1.0, ≤ 512 output tokens,
≤ 8,192 input tokens. Spec Inferencer: T = 0, ≤ 400-token specification. Generator: T = 0.7, 3 generations.

## 4. Prompts

Development prompts: `prompts/dev/v0/`. The frozen set used for held-out runs is copied to
`prompts/frozen/<name>/` with `MANIFEST.json` (SHA-256 per file and a set hash), and each run writes the
hashes it used into `results/runs/<run>/experiment.json`.

## 5. Order of execution

See the pipeline table in `README.md`. Every stage is idempotent: re-running skips finished work.

## 6. What a reader can verify without paying

- `python -m pytest` — 62 unit tests.
- `python scripts/analysis/check_no_mock.py` — confirms no mock/synthetic output in research locations.
- `tests/integration/lang1_harness_check.py` (WSL) — labelling on real Defects4J B/F.
- `scripts/smoke_test.py` + `scripts/analyze.py --smoke` — full plumbing on mock data.
- Once the call log is released (it is **not yet** — no real run has happened),
  `python scripts/run_experiment.py <config> --replay` recomputes every decision from the logged responses with
  no API key and no network access; any request that is not in the log stops with `NotInLog` instead of
  calling a model. Re-running the models themselves is a new, paid and stochastic experiment.
