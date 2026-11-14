"""Shared CLI helpers: path setup, client construction, context loading."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage.io_utils import read_jsonl  # noqa: E402,F401


def local_model(role: str) -> str:
    """Ollama tag assigned to a study role (G, M1, M2) in configs/local_models.json."""
    from triage.ollama import load_local_models
    return load_local_models()["roles"][role]


def make_client(mock: bool = False, replay: bool = False, local: bool = False, profile: dict | None = None):
    """Mock -> results/smoke/llm_calls (never research data). Replay -> serve only from the call log, no key,
    no network, error on any unlogged request. Real -> OpenRouter with the provider pin and rates from
    configs/providers.json; refuses without a key, TRIAGE_ALLOW_PAID=1 and configs/budget.json."""
    from triage.llm import LLMClient, MockBackend, OpenRouterBackend, ReplayBackend
    if mock:
        from triage.mock_responder import responder
        return LLMClient(MockBackend(responder), log_dir=config.ROOT / "results" / "smoke" / "llm_calls")
    if replay:
        return LLMClient(ReplayBackend())
    if local and profile is not None:   # D-67: exploratory model on its own server and call log
        from triage import expl_profile
        from triage.ollama import OllamaAPI, OllamaBackend
        api = OllamaAPI(profile["base_url"], timeout_s=profile["first_response_timeout_s"])
        return LLMClient(expl_profile.safe_backend(profile, api=api),     # D-78 safety rule
                         log_dir=expl_profile.resolve(profile["call_log_dir"]))
    if local:
        from triage.ollama import LOCAL_CALL_LOG_DIR, OllamaBackend
        return LLMClient(OllamaBackend(), log_dir=LOCAL_CALL_LOG_DIR)
    return LLMClient(OpenRouterBackend())


def load_contexts(split=None):
    out = {}
    for p in sorted((config.INTERIM / "context").glob("*.json")):
        c = json.loads(p.read_text(encoding="utf-8"))
        if split is None or c["split"] == split:
            out[c["focal_id"]] = c
    return out
