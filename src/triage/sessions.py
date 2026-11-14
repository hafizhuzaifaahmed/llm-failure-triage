"""Per-session preconditions for local generation (D-40).

The Step 1 RAM rule measures the host, not the model, so it is checked at the start of every G generation
session instead of once: G is loaded with a tiny request, then the live digest must match the configured one,
`message.thinking` must be empty, and available system RAM must be >= G_MIN_AVAILABLE_GIB. Every check is
appended to logs/sessions.jsonl (event `g_session_start`); a failed check raises and nothing is generated.
"""
from __future__ import annotations

import time
from pathlib import Path

from . import config, hwinfo
from .io_utils import append_jsonl

SESSIONS_LOG = config.ROOT / "logs" / "sessions.jsonl"
G_MIN_AVAILABLE_GIB = 4.0


class SessionPreconditionFailed(RuntimeError):
    pass


def g_session_start(api, model_id: str, spec: dict, log: Path = SESSIONS_LOG,
                    min_available_gib: float = G_MIN_AVAILABLE_GIB) -> dict:
    """`min_available_gib` differs from G_MIN_AVAILABLE_GIB only for the exploratory 35b (D-78)."""
    from .ollama import model_options
    body = {"model": model_id, "messages": [{"role": "user", "content": "Reply with OK."}], "stream": False,
            "think": spec.get("think", False), "keep_alive": spec.get("keep_alive", "30m"),
            "options": {"num_ctx": int(spec.get("num_ctx", 8192)), "num_predict": 8, "temperature": 0.0,
                        "seed": 1, **model_options(spec)}}
    out = api.chat(body)
    live = api.tags().get(model_id, {}).get("digest")
    ram = hwinfo.ram()
    rec = {"event": "g_session_start", "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "model": model_id, "digest_live": live, "digest_config": spec.get("digest"),
           "ollama_version": api.version(), "available_ram_gib": ram.get("free_gib"),
           "total_ram_gib": ram.get("total_gib"), "min_available_gib": min_available_gib,
           "thinking_empty": not ((out.get("message") or {}).get("thinking") or "").strip(),
           "gpu": hwinfo.gpu(), "problems": []}
    if live != spec.get("digest"):
        rec["problems"].append(f"digest {live} != configured {spec.get('digest')}")
    if not rec["thinking_empty"]:
        rec["problems"].append("thinking output with think=false")
    if (ram.get("free_gib") or 0) < min_available_gib:
        rec["problems"].append(f"available RAM {ram.get('free_gib'):.2f} GiB < {min_available_gib} GiB with G loaded "
                               "(D-40): close other applications and start the session again")
    rec["ok"] = not rec["problems"]
    append_jsonl(log, rec)
    if not rec["ok"]:
        raise SessionPreconditionFailed("; ".join(rec["problems"]))
    return rec


def g_session_end(model_id: str, generations: int, log: Path = SESSIONS_LOG) -> None:
    append_jsonl(log, {"event": "g_session_end", "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "model": model_id, "generations_this_session": generations,
                       "available_ram_gib": hwinfo.ram().get("free_gib"), "gpu": hwinfo.gpu()})
