"""Session start/end check (D-28). Must pass before any run after the freeze.

    python scripts/local/session_check.py --start [--frozen configs/local_models.FROZEN.json]
    python scripts/local/session_check.py --end

--start: 3 fixed synthetic probe calls with each judge (M1, M2); verifies Ollama version, model digests, num_ctx
(context_length 8192), 100% GPU residency for judges, valid JSON, empty thinking; logs GPU temperature, driver and
Ollama version. Any mismatch with the frozen (or, pre-freeze, the working) config -> exit 1.
--end: closes the session record with calls completed (local call log), median latency and GPU temperature range.
Both append to logs/sessions.jsonl.
"""
import argparse
import re
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config, hwinfo, probes  # noqa: E402
from triage.io_utils import append_jsonl, read_jsonl  # noqa: E402
from triage.ollama import LOCAL_CALL_LOG_DIR, OllamaAPI, model_options, schema_for_role  # noqa: E402
from triage.schema import parse_output  # noqa: E402

LOG = config.ROOT / "logs" / "sessions.jsonl"
SERVER_LOGS = config.ROOT / "logs" / "ollama_server"


def llamacpp_offload() -> dict | None:
    """D-38: for the llamacpp runner /api/ps misreports size, so residency is read from the server log: the first
    'offloaded X/Y layers to GPU' after the most recent 'starting llama-server' (the model just loaded)."""
    logs = sorted(SERVER_LOGS.glob("server_*.log"), key=lambda f: f.stat().st_mtime)
    if not logs:
        return None
    lines = logs[-1].read_text(encoding="utf-8", errors="replace").splitlines()
    starts = [i for i, ln in enumerate(lines) if "starting llama-server" in ln]
    if not starts:
        return None
    for ln in lines[starts[-1]:]:
        m = re.search(r"offloaded (\d+)/(\d+) layers to GPU", ln)
        if m:
            return {"offloaded": int(m.group(1)), "total": int(m.group(2)), "log": logs[-1].name}
    return None


def count_calls():
    n, lat = 0, []
    for f in Path(LOCAL_CALL_LOG_DIR).glob("*.jsonl"):
        if f.name.startswith("_"):
            continue
        for r in read_jsonl(f):
            n += 1
            lat.append(r.get("latency_s") or 0)
    return n, lat


def start(cfg_path: Path):
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    api = OllamaAPI()
    rec = {"event": "start", "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "config": str(cfg_path),
           "frozen": bool(cfg.get("frozen")), "ollama_version": api.version(), "gpu": hwinfo.gpu(), "ram": hwinfo.ram(),
           "problems": [], "probes": []}
    want_ver = cfg.get("runtime", {}).get("version")
    if want_ver and rec["ollama_version"] != want_ver:
        rec["problems"].append(f"Ollama version {rec['ollama_version']} != frozen {want_ver}")
    want_driver = cfg.get("hardware", {}).get("driver")
    if want_driver and rec["gpu"].get("driver") != want_driver:
        rec["problems"].append(f"driver {rec['gpu'].get('driver')} != frozen {want_driver}")
    tags = api.tags()
    for role in ("M1", "M2"):
        tag = cfg["roles"].get(role)
        if not tag:
            continue
        spec = cfg["models"].get(tag, {})
        live = tags.get(tag, {}).get("digest")
        if live != spec.get("digest"):
            rec["problems"].append(f"{role} {tag}: digest {live} != {spec.get('digest')}")
            continue
        for p in probes.session_probes():
            body = {"model": tag, "messages": [{"role": "user", "content": p["text"]}], "stream": False,
                    "think": spec.get("think", False), "format": schema_for_role(p["role"]),
                    "options": {"num_ctx": spec.get("num_ctx", 8192), "num_predict": config.MAX_OUTPUT_TOKENS,
                                "temperature": 0.0, "top_p": 1.0, "seed": 1, **model_options(spec)}}
            t0 = time.time()
            out = api.chat(body)
            msg = out.get("message") or {}
            ps = api.ps().get(tag, {})
            row = {"role": role, "model": tag, "probe": p["id"], "wall_s": time.time() - t0,
                   "valid": parse_output(msg.get("content") or "", "judge").ok,
                   "thinking_empty": not (msg.get("thinking") or "").strip(),
                   "context_length": ps.get("context_length"),
                   "runner": ps.get("runner"),
                   "resident": bool(ps.get("size")) and (ps.get("size_vram") or 0) >= ps["size"]}
            if ps.get("runner") == "llamacpp":          # D-38: /api/ps is not evidence for this runner
                off = llamacpp_offload()
                row["offload"] = off
                row["resident"] = bool(off) and off["offloaded"] == off["total"]
            rec["probes"].append(row)
            for k, ok in (("valid", row["valid"]), ("thinking_empty", row["thinking_empty"]),
                          ("context_length", row["context_length"] == spec.get("num_ctx", 8192)),
                          ("resident", row["resident"] or not spec.get("require_gpu_resident"))):
                if not ok:
                    rec["problems"].append(f"{role} {p['id']}: {k} check failed ({row})")
    n, _ = count_calls()
    rec["calls_in_log_at_start"] = n
    rec["ok"] = not rec["problems"]
    append_jsonl(LOG, rec)
    print(json.dumps({"ok": rec["ok"], "problems": rec["problems"], "ollama": rec["ollama_version"],
                      "driver": rec["gpu"].get("driver"), "gpu_temp_c": rec["gpu"].get("temp_c")}, indent=1))
    sys.exit(0 if rec["ok"] else 1)


def end():
    starts = [r for r in read_jsonl(LOG) if r["event"] == "start"]
    s = starts[-1] if starts else {}
    n, lat = count_calls()
    new = lat[s.get("calls_in_log_at_start", 0):]
    rec = {"event": "end", "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "session_start": s.get("utc"),
           "calls_completed": n - s.get("calls_in_log_at_start", 0),
           "median_latency_s": statistics.median(new) if new else None, "gpu_end": hwinfo.gpu()}
    temps = [s.get("gpu", {}).get("temp_c"), rec["gpu_end"].get("temp_c")]
    rec["gpu_temp_range_c"] = [min(t for t in temps if t is not None), max(t for t in temps if t is not None)]
    append_jsonl(LOG, rec)
    print(json.dumps(rec, indent=1))


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--start", action="store_true")
    g.add_argument("--end", action="store_true")
    ap.add_argument("--frozen", default=None)
    a = ap.parse_args()
    if a.start:
        frozen = config.ROOT / "configs" / "local_models.FROZEN.json"
        start(Path(a.frozen) if a.frozen else (frozen if frozen.exists() else config.ROOT / "configs" / "local_models.json"))
    else:
        end()


if __name__ == "__main__":
    main()
