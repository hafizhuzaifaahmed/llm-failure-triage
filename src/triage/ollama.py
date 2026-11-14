"""Local open-weight backend (Ollama) — code changes 1, 2, 4, 5, 6 and 7 of
docs/local_models/UPDATED_MODEL_CONFIG_PROPOSAL.md §5.

1 OllamaBackend      POST /api/chat with explicit options (num_ctx, num_predict, temperature, top_p, top_k, min_p,
                     seed), top-level `think`, and a JSON-schema `format` chosen by call role.
2 digest pin         the live manifest digest (/api/tags) must equal the configured one, checked on first use of a
                     model and every PIN_EVERY calls; mismatch -> DigestMismatch (run stops).
4 context guard      (D-35) pre-call: refused only when overflow is certain (chars / MAX_CHARS_PER_TOKEN +
                     num_predict > num_ctx); post-call: `truncation_suspected` -> ContextOverflow. Ollama truncates an
                     oversized prompt to about num_ctx/2 and says nothing, so a truncated prompt looks SHORT.
5 thinking guard     think=false; any non-empty message.thinking -> the answer is withheld (text "") so it parses as
                     INVALID, and the call is flagged; thinking text is logged verbatim.
6 VRAM telemetry     one `nvidia-smi -lms 200` stream per process -> peak VRAM and max GPU temperature per call;
                     /api/ps after each call -> size, size_vram, context_length; judges must stay 100% GPU-resident.
7 GPU-time ledger    total_duration per call (seconds) instead of USD; USD cost is 0 by construction.
"""
from __future__ import annotations

import json
import math
import subprocess
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path
from typing import Optional

from . import config
from .io_utils import read_jsonl
from .schema import ADVOCATE_SCHEMA, JUDGE_SCHEMA, SPEC_KEYS

LOCAL_MODELS_FILE = config.ROOT / "configs" / "local_models.json"
LOCAL_SCOPE_FILE = config.ROOT / "configs" / "local_scope.json"
LOCAL_CALL_LOG_DIR = config.RAW / "llm_calls_local"
PIN_EVERY = 200

SPEC_SCHEMA = {"type": "object", "required": list(SPEC_KEYS),
               "properties": {k: {"type": "string"} for k in SPEC_KEYS}}
JUDGE_ROLES = {"judge", "adjudicator", "probe_judge"}
ADVOCATE_ROLES = {"advocate_p_r1", "advocate_t_r1", "debater_neutral_r1", "r2_a", "r2_b"}
SPEC_ROLES = {"spec_inferencer", "spec_inferencer_from_body"}


class DigestMismatch(RuntimeError):
    pass


MAX_CHARS_PER_TOKEN = 6.0     # pre-call "certain overflow" bound; Gemma packs up to ~4.5 chars/token on prose (D-41)
TRUNCATION_BAND = (-8, 64)    # Ollama (both runners) cuts any overflowing prompt to num_ctx/2 + 2..3 tokens (D-41)
BAND_FATAL_CHARS_PER_TOKEN = 4.5   # D-68: a band hit is fatal only above this density (was 3.3, D-41)
# D-68 amendment: lowest chars/token ever measured per model (probes and logged calls), rounded down
MIN_CHARS_PER_TOKEN = {"qwen3.5:9b": 2.372,          # results/dev/feasibility/qwen3.5_9b.D35.json
                       "qwen3.5:9b-q8_0": 2.453,     # results/dev/feasibility/qwen3.5_9b-q8_0.json
                       "gemma4:12b": 2.314,          # results/dev/feasibility/gemma4_12b.json
                       "gemma4:26b": 3.376}          # held-out generator call, session 1 (probes: 3.899)


def min_chars_per_token(model: Optional[str]) -> float:
    """A model never measured (or not named) gets the lowest density of any measured model."""
    return MIN_CHARS_PER_TOKEN.get(model or "", min(MIN_CHARS_PER_TOKEN.values()))


def truncation_check(chars: int, prompt_tokens: int, num_ctx: int, max_tokens: int, model: Optional[str] = None) -> str:
    """D-35/D-41/D-68. "fatal" when the reported prompt length cannot be the whole prompt (or leaves no room to
    answer): near the limit; or at Ollama's truncation length (measured 4,098-4,099 at num_ctx 8192 on every
    overflow, both runners, three models) when the prompt could really be too long: more than 4.5 chars per
    reported token, or chars / (the model's lowest measured density) >= num_ctx - max_tokens (D-68 amendment:
    even at that density the prompt would not fit). A band hit at normal density is a full-length prompt that
    happens to sit in the band: "band_hit_density_normal" (accepted, logged). Anything else: "ok"."""
    if prompt_tokens <= 0:
        return "fatal" if chars > 0 else "ok"
    if prompt_tokens >= num_ctx - max_tokens:
        return "fatal"
    lo, hi = num_ctx // 2 + TRUNCATION_BAND[0], num_ctx // 2 + TRUNCATION_BAND[1]
    if lo <= prompt_tokens <= hi:
        if (chars / prompt_tokens > BAND_FATAL_CHARS_PER_TOKEN
                or chars / min_chars_per_token(model) >= num_ctx - max_tokens):
            return "fatal"
        return "band_hit_density_normal"
    return "ok"


def truncation_suspected(chars: int, prompt_tokens: int, num_ctx: int, max_tokens: int,
                         model: Optional[str] = None) -> bool:
    return truncation_check(chars, prompt_tokens, num_ctx, max_tokens, model) == "fatal"


class ContextOverflow(RuntimeError):
    pass


class ResidencyLost(RuntimeError):
    """A model required to be 100% GPU-resident was partly offloaded during a call: stop the session."""


class UnknownLocalModel(RuntimeError):
    pass


def schema_for_role(role: str) -> Optional[dict]:
    if role in JUDGE_ROLES:
        return JUDGE_SCHEMA_JSON
    if role in ADVOCATE_ROLES:
        return ADVOCATE_SCHEMA_JSON
    if role in SPEC_ROLES:
        return SPEC_SCHEMA
    return None


def _jsonschema(s: dict) -> dict:
    """The project schemas use bare enums; Ollama's grammar wants explicit types."""
    out = {"type": "object", "required": s["required"], "properties": {}}
    for k, v in s["properties"].items():
        v = dict(v)
        if "enum" in v and "type" not in v:
            v["type"] = "string"
        out["properties"][k] = v
    return out


JUDGE_SCHEMA_JSON = _jsonschema(JUDGE_SCHEMA)
ADVOCATE_SCHEMA_JSON = _jsonschema(ADVOCATE_SCHEMA)


FROZEN_MODELS_FILE = config.ROOT / "configs" / "local_models.FROZEN.json"


def load_local_models(path: Path | None = None) -> dict:
    """After Step 6 the frozen file is authoritative: digests, sampling options and roles come from it."""
    if path is None:
        path = FROZEN_MODELS_FILE if FROZEN_MODELS_FILE.exists() else LOCAL_MODELS_FILE
    return json.loads(Path(path).read_text(encoding="utf-8"))


SAMPLING_EXTRAS = ("top_k", "min_p", "presence_penalty", "frequency_penalty", "repeat_penalty", "repeat_last_n")


def model_options(spec: dict) -> dict:
    """Sampling options other than temperature/top_p (fixed by Phase 2), sent explicitly on every request so that
    neither the Modelfile nor an Ollama default can change them silently (D-34)."""
    return {k: spec[k] for k in SAMPLING_EXTRAS if spec.get(k) is not None}


def derive_seed(key: str) -> int:
    return int(key[:8], 16) % 2_147_483_647


class OllamaAPI:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout_s: int = 900):
        self.base = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def _req(self, path: str, body: Optional[dict] = None, timeout: Optional[int] = None) -> dict:
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(self.base + path, data=data,
                                     headers={"Content-Type": "application/json"},
                                     method="POST" if body is not None else "GET")
        with urllib.request.urlopen(req, timeout=timeout or self.timeout_s) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def version(self) -> str:
        return self._req("/api/version")["version"]

    def tags(self) -> dict:
        return {m["name"]: m for m in self._req("/api/tags").get("models", [])}

    def show(self, model: str) -> dict:
        return self._req("/api/show", {"model": model})

    def ps(self) -> dict:
        return {m["name"]: m for m in self._req("/api/ps").get("models", [])}

    def chat(self, body: dict) -> dict:
        return self._req("/api/chat", body)

    def unload(self, model: str) -> None:
        self._req("/api/generate", {"model": model, "keep_alive": 0}, timeout=120)


class VramSampler:
    """Single background `nvidia-smi` stream (200 ms) shared by all calls in the process."""

    _instance = None
    _lock = threading.Lock()

    def __init__(self, interval_ms: int = 200):
        self.samples: deque = deque(maxlen=200_000)
        self.ok = True
        try:
            self.proc = subprocess.Popen(
                ["nvidia-smi", "--query-gpu=memory.used,temperature.gpu", "--format=csv,noheader,nounits",
                 f"-lms", str(interval_ms)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except (OSError, FileNotFoundError):
            self.ok = False
            return
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            try:
                mem, temp = (float(x) for x in line.strip().split(","))
                self.samples.append((time.time(), mem, temp))
            except ValueError:
                continue

    @classmethod
    def get(cls) -> "VramSampler":
        with cls._lock:
            if cls._instance is None:
                cls._instance = VramSampler()
            return cls._instance

    def window(self, t0: float, t1: float) -> dict:
        w = [s for s in list(self.samples) if t0 - 0.25 <= s[0] <= t1 + 0.25]
        if not w:
            return {"peak_vram_mib": None, "max_gpu_temp_c": None, "samples": 0}
        return {"peak_vram_mib": max(s[1] for s in w), "max_gpu_temp_c": max(s[2] for s in w), "samples": len(w)}


class OllamaBackend:
    """One HTTP attempt per call (retries owned by LLMClient). Model specs come from configs/local_models.json."""

    name = "ollama"

    def __init__(self, models_cfg: Optional[dict] = None, api: Optional[OllamaAPI] = None,
                 telemetry: bool = True, verify_digests: bool = True):
        self.cfg = models_cfg if models_cfg is not None else load_local_models()
        self.api = api or OllamaAPI(self.cfg.get("base_url", "http://127.0.0.1:11434"))
        self.telemetry = telemetry
        self.sampler = VramSampler.get() if telemetry else None
        self.verify_digests = verify_digests
        self._pinned_ok: dict[str, int] = {}
        self._lock = threading.Lock()

    # -- model specification -------------------------------------------------------------
    def spec(self, model_id: str) -> dict:
        m = self.cfg["models"].get(model_id)
        if not m:
            raise UnknownLocalModel(f"{model_id} is not in {LOCAL_MODELS_FILE.name}")
        return m

    def routing(self, model_id: str) -> dict:
        """What identifies a request beyond the prompt: weights digest and every decoding option."""
        m = self.spec(model_id)
        return {"engine": "ollama", "digest": m.get("digest"), "num_ctx": m["num_ctx"], "think": m.get("think", False),
                "quantization": m.get("quantization"), **model_options(m)}

    def check_digest(self, model_id: str) -> None:
        if not self.verify_digests:
            return
        with self._lock:
            n = self._pinned_ok.get(model_id)
            if n is not None and n % PIN_EVERY:
                self._pinned_ok[model_id] = n + 1
                return
        want = self.spec(model_id).get("digest")
        live = self.api.tags().get(model_id, {}).get("digest")
        if not want or not live or live != want:
            raise DigestMismatch(f"{model_id}: live digest {live!r} != configured {want!r}")
        with self._lock:
            self._pinned_ok[model_id] = (n or 0) + 1

    # -- the call -----------------------------------------------------------------------
    def call(self, model_id, messages, temperature, top_p, max_tokens, json_mode, routing, *, seed=None,
             role="", **_):
        from .llm import AttemptError
        m = self.spec(model_id)
        num_ctx = int(m["num_ctx"])
        chars = sum(len(x["content"]) for x in messages)
        min_in = math.ceil(chars / MAX_CHARS_PER_TOKEN)
        if min_in + max_tokens > num_ctx:
            raise ContextOverflow(f"{model_id}: at least {min_in} input + {max_tokens} output > num_ctx {num_ctx}")
        self.check_digest(model_id)
        options = {"num_ctx": num_ctx, "num_predict": max_tokens, "temperature": temperature, "top_p": top_p}
        options.update(model_options(m))
        if seed is not None:
            options["seed"] = int(seed)
        body = {"model": model_id, "messages": messages, "stream": False, "options": options,
                "think": m.get("think", False), "keep_alive": m.get("keep_alive", "30m")}
        if body["think"] is None:   # D-85: a model with no thinking channel gets no `think` field (frozen specs say False)
            del body["think"]
        schema = schema_for_role(role) if json_mode else None
        if schema is not None:
            body["format"] = schema
        t0 = time.time()
        try:
            out = self.api.chat(body)
        except urllib.error.HTTPError as e:
            raise AttemptError(f"HTTP {e.code}: {e.read()[:300]!r}", possibly_charged=False,
                               retryable=e.code >= 500, status=e.code)
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            raise AttemptError(f"{type(e).__name__}: {e}", possibly_charged=False, retryable=True)
        t1 = time.time()
        msg = out.get("message") or {}
        thinking = msg.get("thinking") or ""
        content = msg.get("content") or ""
        p_eval = int(out.get("prompt_eval_count") or 0)
        p_cached = int(out.get("prompt_eval_cached_count") or 0)   # D-37: a SUBSET of prompt_eval_count, never added
        e_count = int(out.get("eval_count") or 0)
        ps = {}
        try:
            ps = self.api.ps().get(model_id, {})
        except Exception:
            pass
        size, size_vram = ps.get("size"), ps.get("size_vram")
        resident = bool(size) and size_vram is not None and size_vram >= size
        tele = self.sampler.window(t0, t1) if self.sampler else {}
        local = {
            "prompt_eval_count": p_eval, "prompt_eval_cached_count": p_cached, "eval_count": e_count,
            "total_duration_ns": out.get("total_duration"), "load_duration_ns": out.get("load_duration"),
            "prompt_eval_duration_ns": out.get("prompt_eval_duration"), "eval_duration_ns": out.get("eval_duration"),
            "done_reason": out.get("done_reason"), "thinking": thinking, "thinking_chars": len(thinking),
            "thinking_violation": bool(thinking.strip()) and not m.get("think", False),
            "options": options, "think": body.get("think"), "format_role": role if schema is not None else None,
            "ps_size": size, "ps_size_vram": size_vram, "ps_context_length": ps.get("context_length"),
            "cpu_offload_bytes": (size - size_vram) if size and size_vram is not None else None,
            "gpu_resident": resident, "require_gpu_resident": bool(m.get("require_gpu_resident", False)),
            "digest": m.get("digest"), "gpu_seconds": (out.get("total_duration") or 0) / 1e9, **tele,
            "prompt_chars": chars,
            "truncation_check": truncation_check(chars, p_eval, num_ctx, max_tokens, model_id),
        }
        local["possibly_truncated"] = local["truncation_check"] == "fatal"
        text = "" if local["thinking_violation"] else content
        return {"text": text, "finish_reason": out.get("done_reason", ""), "input_tokens": p_eval,
                "output_tokens": e_count, "cost_usd": None, "cost_details": None, "model_returned": out.get("model", model_id),
                "provider": "ollama-local", "generation_id": None, "local": local}


def local_ledger(log_dir: Path = LOCAL_CALL_LOG_DIR) -> dict:
    calls = gpu = 0.0
    flags = {"thinking_violation": 0, "possibly_truncated": 0, "not_resident": 0}
    for f in Path(log_dir).glob("*.jsonl"):
        if f.name.startswith("_"):
            continue
        for r in read_jsonl(f):
            loc = r.get("local") or {}
            calls += 1
            gpu += loc.get("gpu_seconds") or 0.0
            flags["thinking_violation"] += bool(loc.get("thinking_violation"))
            flags["possibly_truncated"] += bool(loc.get("possibly_truncated"))
            flags["not_resident"] += bool(loc.get("require_gpu_resident")) and not loc.get("gpu_resident")
    return {"calls": int(calls), "gpu_hours": gpu / 3600, "usd": 0.0, **flags}
