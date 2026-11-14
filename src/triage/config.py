"""Fixed protocol constants. Every value here is a Phase 2 [DES] decision unless marked otherwise.

Changing anything in this file after the prompt freeze invalidates the frozen protocol hash
(see `triage.freeze`). Deviations must be logged in docs/tracking/EXPERIMENT_DEVIATIONS.md.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"                      # immutable: generated tests, execution logs, model responses
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
GT_STORE = DATA / "ground_truth_store"  # labels; never read by any judging module
LEAKAGE_GUARD = DATA / "leakage_guard"  # per-instance forbidden strings; read only by the pre-call check
EXTERNAL = DATA / "external"
RESULTS = ROOT / "results"
PROMPTS = ROOT / "prompts"
LOGS = ROOT / "logs"

# --- seeds (Section 3.2, 3.3) -------------------------------------------------------------
SEED_SPLIT = 20261007          # project-level dev/test draw
SEED_FRAME_CAP = 20261008      # 25-per-project cap
SEED_TF_SAMPLE = 20261009      # 1:2 PF:TF stratified sampling
SEED_ARGUMENT_ORDER = 20261010 # adjudicator argument-order randomisation
SEED_BOOTSTRAP = 20261011
SEED_MUTANTS = 20261012

# --- dataset ------------------------------------------------------------------------------
D4J_PROJECTS = [
    "Chart", "Cli", "Closure", "Codec", "Collections", "Compress", "Csv", "Gson",
    "JacksonCore", "JacksonDatabind", "JacksonXml", "Jsoup", "JxPath", "Lang", "Math",
    "Mockito", "Time",
]
N_DEV_PROJECTS = 3
MAX_FOCAL_PER_PROJECT = 25
GENERATIONS_PER_FOCAL = 3
GENERATION_TEMPERATURE = 0.7
MAX_MUTANTS_PER_FOCAL = 2
MUTATION_OPERATORS = ["AOR", "LOR", "SOR", "COR", "ROR", "ORU", "LVR", "STD"]
D3_MAX_BUGS = 60
PF_TO_TF_RATIO = 2              # keep all PF, sample 2 TF per PF, stratified by project

# --- execution (C5-C7) --------------------------------------------------------------------
RUNS_PER_VERSION = 3
TEST_TIMEOUT_S = 30
MAX_COMPILE_PRUNE_PASSES = 3
ENV_RERUNS = 1

# --- preprocessing (Table 7) --------------------------------------------------------------
MAX_STACK_FRAMES = 25
NEVER_TRUNCATED_FRAMES = 10
MAX_MESSAGE_CHARS = 500
MAX_JAVADOC_TOKENS = 600
MAX_SPEC_TOKENS = 400
MAX_PACKAGE_TOKENS = 6000
# D-35: package/Javadoc/spec caps are "model tokenizer" tokens; the local tokenizers measure 2.37-2.9 chars/token
# on packages (2.37 on the densest synthetic probe, D-36), so one conservative estimate keeps every judge's real count under the cap (byte-identical packages).
CHARS_PER_TOKEN_ESTIMATE = 2.2
MAX_ARGUMENT_WORDS = 150
MAX_CALL_SITES = 5
CALL_SITE_CONTEXT_LINES = 5

# --- decoding and budget (Sections 3.8, 4.5) ----------------------------------------------
TEMPERATURE = 0.7
TOP_P = 1.0
MAX_INPUT_TOKENS = 8192
MAX_OUTPUT_TOKENS = 512
SPEC_TEMPERATURE = 0.0
SC_SAMPLES = 5
DEB_CALLS = 5
REPLICATES = 3

# --- prompt optimisation (Section 3.9) ----------------------------------------------------
MAX_PROMPT_REVISIONS = 5
MAX_INVALID_RATE = 0.02

# --- statistics (Section 5.2) -------------------------------------------------------------
BOOTSTRAP_RESAMPLES = 10_000
SESOI_F1 = 0.05
ALPHA = 0.05
EQUIVALENCE_CI = 0.90

LABELS = ("PROGRAM_FAULT", "TEST_FAULT")
REASON_CATEGORIES = (
    "WRONG_EXPECTED_VALUE",
    "INVALID_SETUP_OR_API_MISUSE",
    "SPEC_VIOLATED_BY_PROGRAM",
    "UNEXPECTED_EXCEPTION_IN_PROGRAM",
    "OTHER",
)

# --- models (Section 3.8). Exact strings are logged per call; these are the requested ids. --
MODELS = {
    "M1": {"provider": "openrouter", "id": "deepseek/deepseek-chat-v3-0324"},
    "M2": {"provider": "openrouter", "id": "qwen/qwen3-235b-a22b-2507"},
    "G": {"provider": "openrouter", "id": "openai/gpt-4.1"},
}
