"""E9 frontier reference judge (D-92, D-96): Claude Sonnet 5.5 through the Message Batches API, under a hard cap.

Labelled everywhere "frontier reference point, not a protocol replication". The arms are the committed J1 and DEB code
unchanged; this module only changes how a call is answered.

Collect, then replay. `FrontierClient.complete` answers a call from the frontier call log when its key is there (the
same request key as every local run). When it is not, the request is recorded as pending and `DeferredCall` is raised;
the runner skips that task and keeps going, so one pass of the runner collects every call that is ready (J1 calls,
then DEB's round-1 advocates, rebuttals, adjudicator in later passes). `submit_pending` sends the pending calls as one
batch, writes every answer to the call log in the same record format the local runs use, and the next pass replays
them. Nothing is reused from any local log.

Cap (three layers, D-92): (1) before a batch is created, its worst case (every request at a conservative token count
of its real prompt, plus its full max_tokens of output, at batch rates) is added to the spend so far, and the batch is
not created if the total would exceed the cap; (2) spend is recomputed from the logged `usage` of every answered call
before each batch; (3) the Console spend limit, set by the authors. No API key is ever written anywhere: the SDK reads
ANTHROPIC_API_KEY from the authors' shell.

Request settings (D-92, from the Sonnet 5.5 documentation): thinking {"type": "between_tools"} (thinking off; no tools
are sent), output_config.effort "high", output_config.format = the frozen JSON schema of the role (additionalProperties
false added and numeric bounds left to the committed validator, as structured outputs require), max_tokens as frozen,
no temperature / top_p / top_k (a 400 on this model), no seed, no server-side fallback (the Batches API rejects it and a
fallback would change the judge). A refusal is logged with finish_reason "refusal" and scores INVALID (TF, primary
policy). An errored or expired request is resubmitted once in the next batch; a second failure is logged as INVALID.
"""
from __future__ import annotations

import copy
import json
import math
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from . import config
from .io_utils import append_jsonl, dump_json, read_jsonl, sha256_text
from .llm import CallResult, DeferredCall, STOP_FILE, StopRequested, _slug, request_key

MODEL = "claude-sonnet-5-5"
LABEL = "frontier reference point, not a protocol replication"
CAP_USD = 14.00                                       # D-97: under the authors' US$ 15 Console limit (was 8.00, D-92)
BATCH_PRICE = {"input": 1.00, "output": 5.00}          # USD per million tokens, Batch API (frontier_cost_estimate.json)
CHARS_PER_TOKEN_FLOOR = 1.5                           # conservative: below every density measured on these prompts
MAX_FAILURES = 2                                      # an errored/expired request is resubmitted once
LOG_DIR = config.ROOT / "data" / "raw" / "llm_calls_frontier"


class CapExceeded(RuntimeError):
    pass


def frontier_schema(schema: dict) -> dict:
    """The frozen schema in the form structured outputs accept: closed objects, no numeric bounds (the committed
    validator in triage.schema still enforces them on the reply)."""
    s = copy.deepcopy(schema)
    s["additionalProperties"] = False
    for v in s["properties"].values():
        v.pop("minimum", None)
        v.pop("maximum", None)
    return s


def schema_for(role: str) -> Optional[dict]:
    from .ollama import schema_for_role
    s = schema_for_role(role)
    return frontier_schema(s) if s else None


def build_params(req: dict) -> dict:
    """Message Batches `params` for one pending request (no sampling fields, no seed, no fallback)."""
    params = {"model": MODEL, "max_tokens": req["max_tokens"], "messages": req["messages"],
              "thinking": {"type": "between_tools"}, "output_config": {"effort": "high"}}
    schema = schema_for(req["role"]) if req["json_mode"] else None
    if schema is not None:
        params["output_config"]["format"] = {"type": "json_schema", "schema": schema}
    return params


def worst_case_usd(req: dict) -> float:
    chars = sum(len(m["content"]) for m in req["messages"]) + 400       # schema and framing allowance
    tin = math.ceil(chars / CHARS_PER_TOKEN_FLOOR)
    return (tin * BATCH_PRICE["input"] + req["max_tokens"] * BATCH_PRICE["output"]) / 1e6


def usage_usd(usage: dict) -> float:
    tin = (usage.get("input_tokens") or 0) + (usage.get("cache_creation_input_tokens") or 0) \
        + (usage.get("cache_read_input_tokens") or 0)
    return (tin * BATCH_PRICE["input"] + (usage.get("output_tokens") or 0) * BATCH_PRICE["output"]) / 1e6


class FrontierClient:
    """Drop-in for LLMClient in the runner: answers from the frontier call log or defers."""

    name = "frontier_batch"

    def __init__(self, log_dir: Path = LOG_DIR, scope=None):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.scope = scope
        self.pending: dict[str, dict] = {}
        self._cache: dict[str, dict] = {}
        self._lock = threading.RLock()
        for r in read_jsonl(self.log_path):
            self._cache[r["key"]] = r

    @property
    def log_path(self) -> Path:
        return self.log_dir / f"{_slug(MODEL)}.jsonl"

    def complete(self, *, role: str, model_id: str, messages: list[dict], sample_index: int = 0,
                 temperature: float = config.TEMPERATURE, top_p: float = config.TOP_P,
                 max_tokens: int = config.MAX_OUTPUT_TOKENS, json_mode: bool = True, tag: str = "",
                 meta: Optional[dict] = None) -> CallResult:
        if model_id != MODEL:
            raise ValueError(f"the frontier client serves {MODEL} only, not {model_id}")
        key = request_key(model_id, messages, temperature, top_p, max_tokens, sample_index, tag, None)
        with self._lock:
            r = self._cache.get(key)
            if r is not None:
                return CallResult(key, r["text"], r["input_tokens"], r["output_tokens"], r["latency_s"], r["cost_usd"],
                                  True, model_id, r["model_returned"], r["finish_reason"])
            if STOP_FILE.exists():
                raise StopRequested(f"stop file {STOP_FILE} present; not queueing {role} call {key[:12]}")
            self.pending[key] = {"key": key, "role": role, "messages": messages, "max_tokens": max_tokens,
                                 "json_mode": json_mode, "temperature": temperature, "top_p": top_p,
                                 "sample_index": sample_index, "tag": tag, "meta": meta or {}}
        raise DeferredCall(key)

    def spend_usd(self) -> float:
        return sum(r.get("cost_usd") or 0.0 for r in read_jsonl(self.log_path))

    def failures(self) -> dict[str, int]:
        f = self.log_dir / "_failures.jsonl"
        out: dict[str, int] = {}
        for r in read_jsonl(f):
            out[r["key"]] = out.get(r["key"], 0) + 1
        return out


def preflight(client: FrontierClient, reqs: list[dict], cap: float = CAP_USD) -> dict:
    spent = client.spend_usd()
    worst = sum(worst_case_usd(r) for r in reqs)
    return {"requests": len(reqs), "spent_usd": spent, "worst_case_usd": worst, "cap_usd": cap,
            "allowed": spent + worst <= cap}


def submit_pending(client: FrontierClient, api, state_file: Path, cap: float = CAP_USD, poll_s: float = 60.0,
                   sleep: Callable[[float], None] = time.sleep, limit: Optional[int] = None) -> dict:
    """One batch for the pending calls: pre-flight, create, poll, log every answer. `api` is an anthropic.Anthropic."""
    reqs = sorted(client.pending.values(), key=lambda r: r["key"])[:limit]
    if not reqs:
        return {"requests": 0}
    # D-99: when the whole queue's worst case does not fit, send the largest prefix that does (the rest stays queued
    # for the next pass); the cap holds for every batch either way, since spend only grows by actual usage
    spent, fit, acc = client.spend_usd(), 0, 0.0
    for r in reqs:
        acc += worst_case_usd(r)
        if spent + acc > cap:
            break
        fit += 1
    pf = {**preflight(client, reqs[:fit] or reqs[:1], cap), "queued": len(reqs), "chunked": fit < len(reqs)}
    append_jsonl(state_file, {"event": "preflight", "utc": _utc(), **pf})
    if fit == 0:
        raise CapExceeded(f"spent ${spent:.4f} + the worst case of a single request > cap ${cap:.2f}; batch not created")
    reqs = reqs[:fit]
    if STOP_FILE.exists():
        raise StopRequested("stop file present; batch not created")
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    batch = api.messages.batches.create(requests=[
        Request(custom_id=r["key"], params=MessageCreateParamsNonStreaming(**build_params(r))) for r in reqs])
    append_jsonl(state_file, {"event": "created", "utc": _utc(), "batch_id": batch.id, "requests": len(reqs),
                              "keys": [r["key"] for r in reqs]})
    return collect(client, api, batch.id, reqs, state_file, poll_s, sleep)


def unfinished_batches(state_file: Path) -> list[dict]:
    """D-99: batches created but never collected (the process stopped while one was in flight)."""
    rows = list(read_jsonl(state_file))
    ended = {r["batch_id"] for r in rows if r.get("event") == "ended"}
    return [r for r in rows if r.get("event") == "created" and r["batch_id"] not in ended]


def resume(client: FrontierClient, api, state_file: Path, poll_s: float = 60.0,
           sleep: Callable[[float], None] = time.sleep) -> list[dict]:
    """Collect every unfinished batch before anything new is sent, so an answer already billed is never re-requested.
    The request details come from the pending queue the latest pass rebuilt (same keys)."""
    out = []
    for b in unfinished_batches(state_file):
        reqs = [client.pending[k] for k in b.get("keys", []) if k in client.pending]
        if not reqs:                                       # older record without keys: map every pending request
            reqs = list(client.pending.values())
        append_jsonl(state_file, {"event": "resumed", "utc": _utc(), "batch_id": b["batch_id"]})
        out.append(collect(client, api, b["batch_id"], reqs, state_file, poll_s, sleep))
    return out


def collect(client: FrontierClient, api, batch_id: str, reqs: list[dict], state_file: Path, poll_s: float,
            sleep: Callable[[float], None]) -> dict:
    class _B:
        id = batch_id
    batch = _B()
    t0 = time.time()
    while True:
        b = api.messages.batches.retrieve(batch.id)
        if b.processing_status == "ended":
            break
        sleep(poll_s)
    by_key = {r["key"]: r for r in reqs}
    counts = {"succeeded": 0, "refusal": 0, "errored": 0, "expired": 0, "canceled": 0, "invalid_after_failures": 0,
              "unmatched": 0}
    fails = client.failures()
    for res in api.messages.batches.results(batch.id):
        req = by_key.get(res.custom_id)
        if req is None:                                    # D-99: answered elsewhere already, or not rebuilt this pass
            counts["unmatched"] += 1
            continue
        kind = res.result.type
        if kind == "succeeded":
            msg = res.result.message
            usage = msg.usage.model_dump() if hasattr(msg.usage, "model_dump") else dict(msg.usage)
            text = "".join(getattr(blk, "text", "") for blk in msg.content if getattr(blk, "type", "") == "text")
            refusal = msg.stop_reason == "refusal"
            counts["refusal" if refusal else "succeeded"] += 1
            sd = getattr(msg, "stop_details", None)
            _log(client, req, text, usage, msg.stop_reason, msg.model, msg.id, batch.id, time.time() - t0,
                 stop_details=(sd.model_dump() if hasattr(sd, "model_dump") else sd))
        else:
            counts[kind] = counts.get(kind, 0) + 1
            err = getattr(res.result, "error", None)
            append_jsonl(client.log_dir / "_failures.jsonl", {"key": req["key"], "kind": kind, "batch_id": batch.id,
                                                              "error": str(err)[:300] if err else None, "utc": _utc()})
            if fails.get(req["key"], 0) + 1 >= MAX_FAILURES:       # second failure: scored INVALID, not resubmitted
                counts["invalid_after_failures"] += 1
                _log(client, req, "", {"input_tokens": 0, "output_tokens": 0}, f"error:{kind}", MODEL, None, batch.id,
                     time.time() - t0)
    client.pending = {k: v for k, v in client.pending.items() if k not in by_key}
    out = {"event": "ended", "utc": _utc(), "batch_id": batch.id, "wall_s": round(time.time() - t0, 1), **counts,
           "spent_usd": client.spend_usd()}
    append_jsonl(state_file, out)
    return out


def _log(client: FrontierClient, req: dict, text: str, usage: dict, stop_reason: str, model_returned: str,
         message_id: Optional[str], batch_id: str, latency: float, stop_details=None) -> None:
    rec = {"key": req["key"], "role": req["role"], "model_requested": MODEL, "model_returned": model_returned,
           "provider": "anthropic", "routing": None, "generation_id": message_id, "backend": "anthropic_batch",
           "batch_id": batch_id, "messages_sha256": sha256_text(json.dumps(req["messages"], ensure_ascii=False)),
           "messages": req["messages"], "temperature": req["temperature"], "top_p": req["top_p"],
           "max_tokens": req["max_tokens"], "sample_index": req["sample_index"], "tag": req["tag"],
           "request_params": {k: v for k, v in build_params(req).items() if k != "messages"},
           "text": text, "finish_reason": stop_reason, "stop_details": stop_details,
           "input_tokens": int(usage.get("input_tokens") or 0), "output_tokens": int(usage.get("output_tokens") or 0),
           "usage": usage, "latency_s": round(latency, 3), "cost_usd": usage_usd(usage), "cost_source": "batch_usage",
           "label": LABEL, "utc": _utc(), "meta": req["meta"]}
    with client._lock:
        append_jsonl(client.log_path, rec)
        client._cache[req["key"]] = rec


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def dump_state(path: Path, obj: dict) -> None:
    dump_json(path, obj)
