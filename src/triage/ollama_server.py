"""Start/stop the Windows Ollama server with an explicit environment (never the tray app, which auto-updates)."""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

from . import config

OLLAMA_EXE = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
SERVER_ENV_FILE = config.ROOT / "configs" / "local_server_env.json"
LOG_DIR = config.ROOT / "logs" / "ollama_server"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
DEFAULT_URL = "http://127.0.0.1:11434"


def base_env() -> dict:
    return dict(json.loads(SERVER_ENV_FILE.read_text(encoding="utf-8"))["env"])


def is_up(url: str = DEFAULT_URL) -> bool:
    try:
        with urllib.request.urlopen(url + "/api/version", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def stop(url: str = DEFAULT_URL) -> None:
    for name in ("ollama app.exe", "ollama.exe"):
        subprocess.run(["taskkill", "/IM", name, "/F", "/T"], capture_output=True, creationflags=NO_WINDOW)
    for _ in range(30):
        if not is_up(url):
            return
        time.sleep(1)
    raise RuntimeError("Ollama server did not stop")


def start(overrides: dict | None = None, tag: str = "", env: dict | None = None, log_dir: Path = LOG_DIR,
          url: str = DEFAULT_URL) -> dict:
    """Start `ollama serve` with base env + overrides, outside this process's job object; return the env used.

    A tool-shell reset once killed a server started as our child (Windows job objects, breakaway not allowed),
    so the server is launched by the WMI service (Win32_Process.Create) through a generated .cmd that sets the
    environment explicitly and redirects the log; ShowWindow = 0 keeps it hidden.
    `env`, `log_dir` and `url` are given only by start_profile (D-67); the frozen server uses the defaults.
    """
    env = env if env is not None else {**base_env(), **(overrides or {})}
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    log = log_dir / f"server_{stamp}{('_' + tag) if tag else ''}.log"
    cmd = log_dir / "launch_server.cmd"
    lines = ["@echo off"] + [f'set "{k}={v}"' for k, v in env.items()] + [f'"{OLLAMA_EXE}" serve > "{log}" 2>&1']
    cmd.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    ps = ("$si = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ShowWindow=[uint16]0}; "
          f"$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments "
          f"@{{CommandLine='cmd.exe /c \"{cmd}\"'; ProcessStartupInformation=$si}}; exit $r.ReturnValue")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True,
                       creationflags=NO_WINDOW)
    if r.returncode != 0:
        raise RuntimeError(f"Win32_Process.Create failed ({r.returncode}): {r.stderr[:300]}")
    for _ in range(60):
        if is_up(url):
            return env
        time.sleep(1)
    raise RuntimeError("Ollama server did not come up")


def restart(overrides: dict | None = None, tag: str = "") -> dict:
    stop()
    return start(overrides, tag)


def start_profile(profile: dict, tag: str = "") -> dict:
    """D-67: the exploratory server -- the frozen env plus the profile's two overrides (own port, flash attention
    off), its own log directory and URL. The frozen server must be stopped first (one GPU)."""
    from . import expl_profile
    if is_up(DEFAULT_URL):
        raise RuntimeError("the frozen server is still up on 11434; stop it before starting the exploratory server")
    return start(tag=tag, env=expl_profile.server_env(profile), log_dir=expl_profile.resolve(profile["server_log_dir"]),
                 url=profile["base_url"])
