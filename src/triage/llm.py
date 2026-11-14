"""LLM access with a content-addressed call log, a write-ahead attempt journal, a hard spending guard,
provider pinning and a mock backend.

What the design guarantees, and what it does not
- A request key covers model, provider routing, messages, decoding and an explicit `sample_index`;
  independent samples (SC votes, replicates) get distinct keys and are never collapsed.
- A completed call is appended (fsync) to data/raw/llm_calls/<model>.jsonl. On resume, a key that is in
  the log is served from it and is NOT sent again.
- Before every HTTP attempt a journal entry is written (data/raw/llm_calls/_journal.jsonl) with a
  conservative maximum cost. If the process dies after the provider accepted the request but before the
  response was logged, that attempt is left without a terminal entry ("orphan"). Its response is lost,
  so a resumed run will send the request again and may be charged twice for it. The guard therefore counts
  every orphan, and every attempt that failed after it may have reached the provider (timeouts, 5xx,
  dropped connections), at its maximum cost. Duplicate charges are thus possible but bounded and counted;
  they are not claimed to be impossible.
- Unknown prices are a hard error. The cost stored for a call is the provider-reported `usage.cost`
  (`cost_source = "provider"`); only if the response lacks it is the pinned rate used (`"computed"`).
- Paid calls require OPENROUTER_API_KEY, TRIAGE_ALLOW_PAID=1 and configs/budget.json with an approved
  ceiling. API keys are read from the environment only and never logged.
"""
from __future__ import annotations

import json
import math
import os
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from . import config
from .io_utils import append_jsonl, read_jsonl, sha256_text

CALL_LOG_DIR = config.RAW / "llm_calls"
BUDGET_FILE = config.ROOT / "configs" / "budget.json"
PROVIDERS_FILE = config.ROOT / "configs" / "providers.json"
CONSERVATIVE_CHARS_PER_TOKEN = 2.5   # reservation only; measured code/English text is ~3.5-4 chars/token
MAX_ATTEMPTS = 4
STOP_FILE = config.ROOT / "logs" / "STOP"   # D-58: present -> no new model call is started


class BudgetExceeded(RuntimeError):
    pass


class StopRequested(RuntimeError):
    """The authors asked the session to stop (D-58): the call in flight finished, no new call is started. Calls
    already made are in the call log, so re-running the same command resumes without repeating them."""


class DeferredCall(RuntimeError):
    """D-96 (E9): the call is not answered yet; it was queued for the next batch and the task is left for a later pass."""


class PaidCallsNotApproved(RuntimeError):
    pass


class UnknownPrice(RuntimeError):
    pass


class ProviderMismatch(RuntimeError):
    """The call was served by a provider other than the pinned one. The call is logged and its cost counted,
    then the run must stop (no fallback providers are permitted)."""


class AttemptError(RuntimeError):
    """One HTTP attempt failed. `possibly_charged` is False only when the provider certainly rejected it."""

    def __init__(self, msg: str, possibly_charged: bool, retryable: bool, status: Optional[int] = None):
        super().__init__(msg)
        self.possibly_charged, self.retryable, self.status = possibly_charged, retryable, status


@dataclass
class CallResult:
    key: str
    text: str
    input_tokens: int
    output_tokens: int
    latency_s: float
    cost_usd: float
    cached: bool
    model_requested: str
    model_returned: str
    finish_reason: str


def _slug(model_id: str) -> str:
    return model_id.replace("/", "__").replace(":", "_")


def request_key(model_id: str, messages: list[dict], temperature: float, top_p: float,
                max_tokens: int, sample_index: int, tag: str = "", routing: Optional[dict] = None) -> str:
    payload = {"m": model_id, "msg": messages, "t": temperature, "p": top_p, "mx": max_tokens,
               "i": sample_index, "tag": tag}
    if routing:
        payload["route"] = routing
    return sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def load_providers() -> dict:
    if not PROVIDERS_FILE.exists():
        raise UnknownPrice(f"{PROVIDERS_FILE} is missing")
    return json.loads(PROVIDERS_FILE.read_text(encoding="utf-8"))


def pinned_rate(model_id: str, providers: Optional[dict] = None) -> dict:
    p = (providers or load_providers())["models"].get(model_id)
    if not p:
        raise UnknownPrice(f"no price configured for {model_id}")
    return p["endpoints"][p["pinned_provider"]]


def ceiling_rate(model_id: str, providers: Optional[dict] = None) -> dict:
    """Highest input and output rate over every listed endpoint: used for reservations."""
    p = (providers or load_providers())["models"].get(model_id)
    if not p:
        raise UnknownPrice(f"no price configured for {model_id}")
    eps = p["endpoints"].values()
    return {"input_per_m": max(e["input_per_m"] for e in eps), "output_per_m": max(e["output_per_m"] for e in eps)}


def max_call_cost(model_id: str, messages: list[dict], max_tokens: int, providers: Optional[dict] = None) -> float:
    r = ceiling_rate(model_id, providers)
    n_in = math.ceil(sum(len(m["content"]) for m in messages) / CONSERVATIVE_CHARS_PER_TOKEN) + 16
    return n_in / 1e6 * r["input_per_m"] + max_tokens / 1e6 * r["output_per_m"]


def ledger(log_dir: Path = CALL_LOG_DIR) -> dict:
    """Spend accounting from the call log and the journal.

    completed_usd  provider-reported (or computed) cost of logged calls
    at_risk_usd    reservations of orphaned attempts and failed attempts that may have been charged
    """
    log_dir = Path(log_dir)
    completed = 0.0
    if log_dir.exists():
        for f in log_dir.glob("*.jsonl"):
            if f.name.startswith("_"):
                continue
            for r in read_jsonl(f):
                completed += float(r.get("cost_usd") or 0.0)
    attempts, terminal = {}, {}
    for e in read_jsonl(log_dir / "_journal.jsonl"):
        if e["event"] == "attempt":
            attempts[e["attempt_id"]] = e
        else:
            terminal[e["attempt_id"]] = e
    orphans = [a for k, a in attempts.items() if k not in terminal]
    risky = [attempts[k] for k, t in terminal.items() if t["event"] == "failed" and t.get("possibly_charged")
             and k in attempts]
    at_risk = sum(a["reserve_usd"] for a in orphans + risky)
    return {"completed_usd": completed, "at_risk_usd": at_risk, "orphan_attempts": len(orphans),
            "possibly_charged_failures": len(risky), "attempts": len(attempts),
            "orphans": [{"key": a["key"], "model": a["model"], "utc": a["utc"]} for a in orphans]}


class Backend:
    name = "abstract"

    def call(self, model_id: str, messages: list[dict], temperature: float, top_p: float,
             max_tokens: int, json_mode: bool, routing: Optional[dict], **kw) -> dict:
        raise NotImplementedError


class OpenRouterBackend(Backend):
    """One HTTP attempt per call() — retries are owned by LLMClient so that each attempt is journalled."""

    name = "openrouter"
    url = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key_env: str = "OPENROUTER_API_KEY", timeout_s: int = 180):
        self.api_key = os.environ.get(api_key_env)
        if not self.api_key:
            raise PaidCallsNotApproved(f"environment variable {api_key_env} is not set")
        self.timeout_s = timeout_s

    def call(self, model_id, messages, temperature, top_p, max_tokens, json_mode, routing, **kw):
        body = {"model": model_id, "messages": messages, "temperature": temperature, "top_p": top_p,
                "max_tokens": max_tokens}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        if routing:
            body["provider"] = routing
        req = urllib.request.Request(self.url, data=json.dumps(body).encode("utf-8"), headers={
            "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                out = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # 4xx other than 408/429 = rejected before inference; 408/429/5xx may or may not have run
            certain_reject = 400 <= e.code < 500 and e.code not in (408, 429)
            raise AttemptError(f"HTTP {e.code}: {e.read()[:300]!r}", possibly_charged=not certain_reject,
                               retryable=e.code in (408, 429) or e.code >= 500, status=e.code)
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            raise AttemptError(f"{type(e).__name__}: {e}", possibly_charged=True, retryable=True)
        if "choices" not in out or not out["choices"]:
            raise AttemptError(f"no choices: {str(out)[:300]}", possibly_charged=True, retryable=True)
        ch = out["choices"][0]
        u = out.get("usage") or {}
        return {
            "text": ch["message"].get("content") or "", "finish_reason": ch.get("finish_reason", ""),
            "input_tokens": int(u.get("prompt_tokens", 0)), "output_tokens": int(u.get("completion_tokens", 0)),
            "cost_usd": u.get("cost"), "cost_details": u.get("cost_details"),
            "model_returned": out.get("model", model_id), "provider": out.get("provider"),
            "generation_id": out.get("id"),
        }


class NotInLog(RuntimeError):
    pass


class ReplayBackend(Backend):
    """Offline replay of a released call log: any request not already logged is an error, never a call.
    Lets third parties recompute every decision without an API key and without spending anything."""

    name = "replay"

    def call(self, model_id, messages, temperature, top_p, max_tokens, json_mode, routing, **kw):
        raise NotInLog(f"request for {model_id} is not in the call log (replay mode makes no network calls)")


class MockBackend(Backend):
    """Deterministic offline backend for pipeline tests. Its outputs are never research data."""

    name = "mock"

    def __init__(self, responder: Callable[[str, list[dict]], str]):
        self.responder = responder

    def call(self, model_id, messages, temperature, top_p, max_tokens, json_mode, routing, **kw):
        text = self.responder(model_id, messages)
        n_in = sum(len(m["content"]) for m in messages) // 4
        return {"text": text, "finish_reason": "stop", "input_tokens": n_in, "output_tokens": len(text) // 4,
                "cost_usd": 0.0, "cost_details": None, "model_returned": f"mock:{model_id}", "provider": "mock",
                "generation_id": None}


class LLMClient:
    def __init__(self, backend: Backend, log_dir: Path = CALL_LOG_DIR, enforce_budget: bool = True,
                 providers: Optional[dict] = None, sleep: Callable[[float], None] = time.sleep):
        self.backend = backend
        self.log_dir = Path(log_dir)
        self.journal = self.log_dir / "_journal.jsonl"
        self.mock = backend.name == "mock"
        self.local = backend.name == "ollama"
        self.enforce_budget = enforce_budget and backend.name not in ("mock", "replay", "ollama")
        self.providers = providers if providers is not None else (None if (self.mock or self.local) else load_providers())
        self.scope = None
        self.sleep = sleep
        self._cache: dict[str, dict] = {}
        self._loaded: set[str] = set()
        self._lock = threading.RLock()
        self.reserved_in_flight = 0.0
        if self.enforce_budget:
            if os.environ.get("TRIAGE_ALLOW_PAID") != "1":
                raise PaidCallsNotApproved("set TRIAGE_ALLOW_PAID=1 only after the budget is approved")
            if not BUDGET_FILE.exists():
                raise PaidCallsNotApproved(f"{BUDGET_FILE} with an approved ceiling is required")
            b = json.loads(BUDGET_FILE.read_text())
            self.ceiling = float(b["approved_usd"])
            if self.ceiling <= 0:
                raise PaidCallsNotApproved("approved_usd must be > 0")
            from . import scope as scope_mod
            self.scope = scope_mod.require(BUDGET_FILE)
            led = ledger(self.log_dir)
            self.committed = led["completed_usd"] + led["at_risk_usd"]
            if led["orphan_attempts"]:
                print(f"WARNING: {led['orphan_attempts']} orphaned attempts from a previous run are counted at "
                      f"their maximum cost (${led['at_risk_usd']:.4f})", flush=True)

        if self.local:
            from . import scope as scope_mod
            from .ollama import LOCAL_SCOPE_FILE
            self.scope = scope_mod.require(LOCAL_SCOPE_FILE)

    # -- helpers ---------------------------------------------------------------------------
    def routing_for(self, model_id: str) -> Optional[dict]:
        if self.local:
            return self.backend.routing(model_id)
        if self.mock or not self.providers:
            return None
        m = self.providers["models"].get(model_id)
        if not m:
            raise UnknownPrice(f"no provider/price configured for {model_id}")
        return m["routing"]

    def _log_path(self, model_id: str) -> Path:
        return self.log_dir / f"{_slug(model_id)}{'.mock' if self.mock else ''}.jsonl"

    def _load(self, model_id: str) -> None:
        p = self._log_path(model_id)
        if str(p) in self._loaded:
            return
        for r in read_jsonl(p):
            self._cache[r["key"]] = r
        self._loaded.add(str(p))

    def _journal(self, event: dict) -> None:
        append_jsonl(self.journal, {**event, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})

    def _reserve(self, amount: float) -> None:
        if self.enforce_budget and self.committed + self.reserved_in_flight + amount > self.ceiling:
            raise BudgetExceeded(f"committed ${self.committed:.4f} + in-flight ${self.reserved_in_flight:.4f} "
                                 f"+ this call up to ${amount:.4f} > ceiling ${self.ceiling:.2f}")
        self.reserved_in_flight += amount

    # -- main entry ------------------------------------------------------------------------
    def complete(self, *, role: str, model_id: str, messages: list[dict], sample_index: int = 0,
                 temperature: float = config.TEMPERATURE, top_p: float = config.TOP_P,
                 max_tokens: int = config.MAX_OUTPUT_TOKENS, json_mode: bool = True,
                 tag: str = "", meta: Optional[dict] = None) -> CallResult:
        routing = self.routing_for(model_id)
        if self.scope is not None:
            self.scope.check_model(model_id, routing, local=self.local)   # approved model (+ pin rules)
        key = request_key(model_id, messages, temperature, top_p, max_tokens, sample_index, tag, routing)
        with self._lock:
            self._load(model_id)
            if key in self._cache:
                r = self._cache[key]
                loc = r.get("local") or {}
                if loc:   # re-judged with the CURRENT rule from the logged counts, not the stored flag (D-41)
                    from .ollama import ContextOverflow, truncation_check
                    chars = loc.get("prompt_chars", sum(len(m["content"]) for m in r.get("messages", messages)))
                    num_ctx = int((loc.get("options") or {}).get("num_ctx", config.MAX_INPUT_TOKENS))
                    verdict = truncation_check(chars, int(loc.get("prompt_eval_count") or 0), num_ctx, r["max_tokens"],
                                               r.get("model_requested", model_id))
                    if verdict == "fatal":
                        raise ContextOverflow(f"logged call {key[:12]} was possibly truncated")
                    if verdict == "band_hit_density_normal":   # D-68: accepted, logged
                        self._journal({"event": "band_hit_density_normal", "key": key, "source": "log",
                                       "prompt_chars": chars, "prompt_eval_count": loc.get("prompt_eval_count")})
                return CallResult(key, r["text"], r["input_tokens"], r["output_tokens"], r["latency_s"],
                                  r["cost_usd"], True, model_id, r["model_returned"], r["finish_reason"])
        if STOP_FILE.exists():
            raise StopRequested(f"stop file {STOP_FILE} present; not starting {role} call {key[:12]}")
        if self.backend.name == "replay":
            raise NotInLog(f"{role} request for {model_id} (key {key[:12]}) is not in the call log")
        reserve = 0.0 if (self.mock or self.local) else max_call_cost(model_id, messages, max_tokens, self.providers)
        seed = int(key[:8], 16) % 2_147_483_647
        last_err = None
        for attempt in range(MAX_ATTEMPTS):
            aid = uuid.uuid4().hex
            with self._lock:
                self._reserve(reserve)
                self._journal({"event": "attempt", "attempt_id": aid, "key": key, "model": model_id,
                               "attempt": attempt, "reserve_usd": reserve})
            t0 = time.time()
            try:
                out = self.backend.call(model_id, messages, temperature, top_p, max_tokens, json_mode, routing,
                                        seed=seed, role=role)
            except AttemptError as e:
                with self._lock:
                    self.reserved_in_flight -= reserve
                    if e.possibly_charged and self.enforce_budget:
                        self.committed += reserve   # counted at maximum cost; never reconciled downward
                    self._journal({"event": "failed", "attempt_id": aid, "error": str(e)[:500],
                                   "status": e.status, "possibly_charged": e.possibly_charged})
                last_err = e
                if not e.retryable:
                    raise
                self.sleep(2.0 * 2 ** attempt)
                continue
            latency = time.time() - t0
            if out["cost_usd"] is not None:
                cost, source = float(out["cost_usd"]), "provider"
            elif self.mock or self.local:
                cost, source = 0.0, ("mock" if self.mock else "local")
            else:
                r = pinned_rate(model_id, self.providers)
                cost = out["input_tokens"] / 1e6 * r["input_per_m"] + out["output_tokens"] / 1e6 * r["output_per_m"]
                source = "computed"
            rec = {
                "key": key, "role": role, "model_requested": model_id, "model_returned": out["model_returned"],
                "provider": out.get("provider"), "routing": routing, "generation_id": out.get("generation_id"),
                "backend": self.backend.name, "messages_sha256": sha256_text(json.dumps(messages, ensure_ascii=False)),
                "messages": messages, "temperature": temperature, "top_p": top_p, "max_tokens": max_tokens,
                "sample_index": sample_index, "tag": tag, "text": out["text"], "finish_reason": out["finish_reason"],
                "input_tokens": out["input_tokens"], "output_tokens": out["output_tokens"],
                "latency_s": round(latency, 3), "cost_usd": cost, "cost_source": source,
                "cost_details": out.get("cost_details"), "attempts": attempt + 1, "seed": seed,
                "local": out.get("local"),
                "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "meta": meta or {},
            }
            with self._lock:
                append_jsonl(self._log_path(model_id), rec)
                self._journal({"event": "done", "attempt_id": aid, "cost_usd": cost})
                self._cache[key] = rec
                self.reserved_in_flight -= reserve
                if self.enforce_budget:
                    self.committed += cost
            loc = out.get("local") or {}
            if loc.get("truncation_check") == "band_hit_density_normal":   # D-68: accepted, logged
                with self._lock:
                    self._journal({"event": "band_hit_density_normal", "key": key, "source": "live",
                                   "prompt_chars": loc.get("prompt_chars"), "prompt_eval_count": loc.get("prompt_eval_count")})
            if loc.get("possibly_truncated"):
                from .ollama import ContextOverflow
                raise ContextOverflow(f"{model_id}: prompt {loc['prompt_eval_count']} (cached {loc['prompt_eval_cached_count']}) "
                                      f"tokens may have been truncated at num_ctx (call logged and flagged)")
            if loc.get("require_gpu_resident") and not loc.get("gpu_resident"):
                from .ollama import ResidencyLost
                raise ResidencyLost(f"{model_id} not 100% GPU-resident (size {loc.get('ps_size')}, "
                                    f"vram {loc.get('ps_size_vram')}); stop the session")
            if self.enforce_budget:
                pinned = self.providers["models"][model_id]["pinned_provider"]
                served = out.get("provider")
                if not served or str(served).lower() != pinned.lower():
                    raise ProviderMismatch(f"{model_id} served by {served!r}, pinned {pinned!r}; stopping (call logged, "
                                           f"cost ${cost:.6f} counted)")
            return CallResult(key, out["text"], out["input_tokens"], out["output_tokens"], latency, cost,
                              False, model_id, out["model_returned"], out["finish_reason"])
        raise last_err


def result_cost_dict(results: list[CallResult]) -> dict:
    return {
        "calls": len(results),
        "input_tokens": sum(r.input_tokens for r in results),
        "output_tokens": sum(r.output_tokens for r in results),
        "latency_s": round(sum(r.latency_s for r in results), 3),
        "cost_usd": round(sum(r.cost_usd for r in results), 6),
        "cached_calls": sum(r.cached for r in results),
        "call_keys": [r.key for r in results],
    }
