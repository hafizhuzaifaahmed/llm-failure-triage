"""Runtime profiles for models outside the frozen config: the exploratory qwen3.5:35b (D-67, configs/expl_35b.json)
and the E6b third-family judge (D-82, configs/e6b.json).

A profile names the experiments it serves; any other experiment gets None and runs exactly as before. It carries a
separate server (own port), its own server-log, call-log and session-log directories, the model spec (never in the
frozen config) and the compute deadline. The server env is the frozen env with only the overrides the profile's kind
allows, checked here so a profile cannot drift into other settings: kind "expl_35b" (the default) must turn flash
attention off (D-67); kind "e6b" may change only the port, so it runs under the frozen server settings (D-82).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import config

PROFILE_FILE = config.ROOT / "configs" / "expl_35b.json"
E6B_PROFILE_FILE = config.ROOT / "configs" / "e6b.json"
KUU_PROFILE_FILES = (config.ROOT / "configs" / "kuu_m1.json", config.ROOT / "configs" / "kuu_m2.json")
E7A_PROFILE_FILE = config.ROOT / "configs" / "e7a.json"            # D-100: the second generator
KUUNG_PROFILE_FILE = config.ROOT / "configs" / "kuung.json"        # D-109: the KUU-NG fourth-family judge
PROFILE_FILES = (PROFILE_FILE, E6B_PROFILE_FILE, *KUU_PROFILE_FILES, E7A_PROFILE_FILE, KUUNG_PROFILE_FILE)
ALLOWED_OVERRIDES = {"OLLAMA_HOST", "OLLAMA_FLASH_ATTENTION"}
FROZEN_FILE = config.ROOT / "configs" / "local_models.FROZEN.json"


class ProfileError(RuntimeError):
    pass


def load(path: Path = PROFILE_FILE) -> dict:
    p = json.loads(Path(path).read_text(encoding="utf-8"))
    bad = set(p["server_env_overrides"]) - ALLOWED_OVERRIDES
    if bad:
        raise ProfileError(f"profile overrides more than D-67 allows: {sorted(bad)}")
    kind = p.get("kind", "expl_35b")
    if kind == "expl_35b" and p["server_env_overrides"].get("OLLAMA_FLASH_ATTENTION") != "0":
        raise ProfileError("D-67: the exploratory server runs with flash attention off")
    if kind in ("e6b", "frozen_copy", "e7a") and set(p["server_env_overrides"]) != {"OLLAMA_HOST"}:
        raise ProfileError("D-82/D-95: this server changes only its port; every other setting is the frozen server env")
    if kind == "frozen_copy":                      # D-95: a frozen model on its own server and logs, spec unchanged
        frozen = json.loads(FROZEN_FILE.read_text(encoding="utf-8"))["models"]
        if p.get("model_spec") != frozen.get(p.get("model_tag")):
            raise ProfileError(f"D-95: {p.get('model_tag')!r} must carry its frozen spec exactly")
    if kind not in ("expl_35b", "e6b", "frozen_copy", "e7a"):
        raise ProfileError(f"unknown profile kind {kind!r}")
    host = p["server_env_overrides"].get("OLLAMA_HOST", "")
    if host.endswith(":11434") or not p["base_url"].endswith(host.split(":")[-1]):
        raise ProfileError(f"profile port must differ from the frozen 11434 and match base_url ({host}, {p['base_url']})")
    from .ollama import LOCAL_CALL_LOG_DIR
    from .ollama_server import LOG_DIR
    if resolve(p["call_log_dir"]) == LOCAL_CALL_LOG_DIR or resolve(p["server_log_dir"]) == LOG_DIR:
        raise ProfileError("profile must not share the frozen call-log or server-log directory")
    return p


def resolve(rel: str) -> Path:
    return (config.ROOT / rel).resolve()


def for_experiment(name: str, path: Optional[Path] = None) -> Optional[dict]:
    """The profile serving this experiment, or None (every primary experiment). With `path`, only that file."""
    for f in ((path,) if path is not None else PROFILE_FILES):
        if Path(f).exists():
            p = load(f)
            if name in p["experiments"]:
                return p
    return None


def models_cfg(p: dict) -> dict:
    """OllamaBackend configuration: the profile's one model and its own server URL (nothing from the frozen file)."""
    return {"base_url": p["base_url"], "models": {p["model_tag"]: p["model_spec"]}}


def server_env(p: dict) -> dict:
    from .ollama_server import base_env
    return {**base_env(), **p["server_env_overrides"]}


def deadline(p: dict) -> datetime:
    return datetime.fromisoformat(p["deadline_local"])


def past_deadline(p: dict, now: Optional[datetime] = None) -> bool:
    return (now or datetime.now()) >= deadline(p)


# ---- D-78: replacement safety rule for the exploratory run ------------------------------------------------------
SAFETY_MARK = "D-78 safety abort"


def STOP_FILE_PATH() -> Path:
    from .llm import STOP_FILE
    return Path(STOP_FILE)
SAFETY_EVENTS = config.ROOT / "results" / "expl_35b" / "safety_events.jsonl"


class SafetyMonitor:
    """Abort (STOP file with a marker, no retry) if available RAM < min at any check (every N calls), if the median
    latency of the last W calls exceeds the limit, or on a server crash or hang."""

    def __init__(self, safety: dict, stop_file: Optional[Path] = None, events: Path = SAFETY_EVENTS, ram=None):
        from . import hwinfo
        from .llm import STOP_FILE
        self.s, self.stop_file, self.events = safety, Path(stop_file or STOP_FILE), Path(events)
        self.ram = ram or hwinfo.ram
        self.calls, self.latencies, self.aborted = 0, [], None
        import threading
        self._lock = threading.Lock()

    def _event(self, kind: str, **kw):
        import time
        from .io_utils import append_jsonl
        append_jsonl(self.events, {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": kind,
                                   "calls": self.calls, **kw})

    def abort(self, reason: str):
        if self.aborted:
            return
        self.aborted = reason
        self.stop_file.parent.mkdir(parents=True, exist_ok=True)
        self.stop_file.write_text(f"{SAFETY_MARK}: {reason}\n", encoding="utf-8")
        self._event("abort", reason=reason)

    def record(self, latency_s: float):
        import statistics
        with self._lock:
            self.calls += 1
            self.latencies.append(latency_s)
            w = self.s["latency_window_calls"]
            if self.calls % self.s["ram_check_every_calls"] == 0:
                free = self.ram().get("free_gib") or 0.0
                self._event("ram_check", available_gib=round(free, 3))
                if free < self.s["min_available_gib"]:
                    self.abort(f"available RAM {free:.2f} GiB < {self.s['min_available_gib']} GiB")
            if len(self.latencies) >= w:
                med = statistics.median(self.latencies[-w:])
                if med > self.s["max_median_latency_s"]:
                    self.abort(f"median latency of the last {w} calls {med:.1f} s > {self.s['max_median_latency_s']} s")


def safe_backend(p: dict, api=None, monitor: Optional[SafetyMonitor] = None, **kw):
    """OllamaBackend for the profile's model, wrapped by the D-78 safety rule."""
    import time
    from .llm import AttemptError, StopRequested
    from .ollama import OllamaAPI, OllamaBackend

    class SafeOllamaBackend(OllamaBackend):
        def call(self, *a, **k):
            if self.monitor.aborted:
                raise StopRequested(f"{SAFETY_MARK}: {self.monitor.aborted}")
            t0 = time.time()
            try:
                out = super().call(*a, **k)
            except AttemptError as e:
                if e.status is None or e.status >= 500:      # connection lost, timeout (900 s), runner crash
                    self.monitor.abort(f"server crash or hang: {str(e)[:200]}")
                    raise StopRequested(f"{SAFETY_MARK}: {self.monitor.aborted}")
                raise
            self.monitor.record(time.time() - t0)
            return out

    b = SafeOllamaBackend(models_cfg(p), api=api or OllamaAPI(p["base_url"], timeout_s=p["first_response_timeout_s"]), **kw)
    events = resolve(p["safety_events"]) if p.get("safety_events") else SAFETY_EVENTS   # D-87: per-profile log
    b.monitor = monitor or SafetyMonitor(p["safety"], events=events)
    return b
