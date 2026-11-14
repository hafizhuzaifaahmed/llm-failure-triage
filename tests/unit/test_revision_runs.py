"""D-123 driver: profile relocation and the option wrapper (no server, no call)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "local"))
import revision_runs as rr  # noqa: E402


def test_profile_moves_only_port_logs_and_named_spec_fields():
    base = json.loads((ROOT / "configs" / "kuu_m1.json").read_text(encoding="utf-8"))
    p = rr.profile_for({"member": "M1"})
    assert p["model_spec"] == base["model_spec"] and p["model_tag"] == base["model_tag"]
    assert p["base_url"].endswith(":11441") and p["server_env_overrides"] == {"OLLAMA_HOST": "127.0.0.1:11441"}
    assert p["call_log_dir"] != base["call_log_dir"] and p["safety"]["max_median_latency_s"] == base["safety"]["max_median_latency_s"]
    q = rr.profile_for({"member": "M1", "spec_patch": {"think": True, "num_ctx": 16384}, "max_median_latency_s": 99})
    assert q["model_spec"]["think"] is True and q["model_spec"]["num_ctx"] == 16384
    assert q["model_spec"]["digest"] == base["model_spec"]["digest"] and q["safety"]["max_median_latency_s"] == 99
    assert base["safety"]["max_median_latency_s"] != 99            # the committed profile is not modified


def test_wrapper_sets_only_named_options():
    seen = {}

    class C:
        scope = "s"

        def complete(self, **kw):
            seen.update(kw)
            return "ok"
    w = rr.Wrapped(C(), temperature=0.0)
    assert w.complete(role="judge", temperature=0.7, max_tokens=512) == "ok"
    assert seen["temperature"] == 0.0 and seen["max_tokens"] == 512 and w.scope == "s"
    rr.Wrapped(C()).complete(temperature=0.7, max_tokens=512)
    assert seen["temperature"] == 0.7
