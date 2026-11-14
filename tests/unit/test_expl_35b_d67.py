"""D-67/D-76: the exploratory qwen3.5:35b runs on its own server (own port, flash attention off) with its own
server-log, call-log and session-log directories, only for EXPL_35B_D1TEST, within a time box; primary experiments
and the frozen server are unchanged. Fakes only: no server is started and no model is loaded."""
import copy
import inspect
import json
import sys
import threading
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "local"))

import _common  # noqa: E402
import run_experiment  # noqa: E402
from triage import expl_profile, ollama, ollama_server, scope  # noqa: E402

P = expl_profile.load()


@pytest.fixture(autouse=True)
def no_sampler(monkeypatch):
    monkeypatch.setattr(ollama.VramSampler, "get", classmethod(lambda cls: None))


def write_profile(tmp_path, **change):
    p = copy.deepcopy(json.loads(expl_profile.PROFILE_FILE.read_text(encoding="utf-8")))
    for k, v in change.items():
        if k == "overrides":
            p["server_env_overrides"] = v
        else:
            p[k] = v
    f = tmp_path / "prof.json"
    f.write_text(json.dumps(p), encoding="utf-8")
    return f


# ---- the profile ---------------------------------------------------------------------------------------------
def test_server_env_is_the_frozen_env_with_only_port_and_flash_attention_changed():
    frozen = ollama_server.base_env()
    env = expl_profile.server_env(P)
    assert {k for k in env if env[k] != frozen.get(k)} == {"OLLAMA_HOST", "OLLAMA_FLASH_ATTENTION"}
    assert env["OLLAMA_FLASH_ATTENTION"] == "0" and frozen["OLLAMA_FLASH_ATTENTION"] == "1"
    assert env["OLLAMA_HOST"] == "127.0.0.1:11435" and frozen["OLLAMA_HOST"] == "127.0.0.1:11434"
    assert P["base_url"] == "http://127.0.0.1:11435"


def test_profile_never_shares_the_frozen_log_directories():
    assert expl_profile.resolve(P["call_log_dir"]) != ollama.LOCAL_CALL_LOG_DIR
    assert expl_profile.resolve(P["server_log_dir"]) != ollama_server.LOG_DIR
    assert P["session_log"] != "logs/sessions.jsonl"
    assert expl_profile.resolve(P["feasibility_dir"]) != (ROOT / "results" / "dev" / "feasibility").resolve()


@pytest.mark.parametrize("change", [
    {"overrides": {"OLLAMA_HOST": "127.0.0.1:11435", "OLLAMA_FLASH_ATTENTION": "0", "OLLAMA_KV_CACHE_TYPE": "q8_0"}},
    {"overrides": {"OLLAMA_HOST": "127.0.0.1:11435", "OLLAMA_FLASH_ATTENTION": "1"}},
    {"overrides": {"OLLAMA_HOST": "127.0.0.1:11434", "OLLAMA_FLASH_ATTENTION": "0"}, "base_url": "http://127.0.0.1:11434"},
    {"call_log_dir": "data/raw/llm_calls_local"},
    {"server_log_dir": "logs/ollama_server"},
])
def test_a_profile_that_drifts_is_refused(tmp_path, change):
    with pytest.raises(expl_profile.ProfileError):
        expl_profile.load(write_profile(tmp_path, **change))


def test_only_the_exploratory_experiment_gets_the_profile():
    assert expl_profile.for_experiment("EXPL_35B_D1TEST")["model_tag"] == "qwen3.5:35b"
    for name in ("LOCAL_HO_E1E3_M1", "LOCAL_HO_E4_M1", "LOCAL_HO_E5R1_D2", "LOCAL_HO_E5R3_M2", "LOCAL_HO_E5R3_M2_D2"):
        assert expl_profile.for_experiment(name) is None


def test_deadline_is_2026_11_10_end_of_day_local():
    assert expl_profile.deadline(P) == datetime(2026, 11, 10, 23, 59)
    assert not expl_profile.past_deadline(P, datetime(2026, 11, 10, 23, 58))
    assert expl_profile.past_deadline(P, datetime(2026, 11, 10, 23, 59))


# ---- client and backend ------------------------------------------------------------------------------------
def test_profile_client_talks_to_the_35b_server_and_logs_to_its_own_directory():
    c = _common.make_client(local=True, profile=P)
    assert c.backend.api.base == "http://127.0.0.1:11435" and c.backend.api.timeout_s == 900
    assert c.log_dir == expl_profile.resolve("data/raw/llm_calls_local_35b")
    assert c.backend.spec("qwen3.5:35b")["digest"].startswith("72aac7c2")
    assert c.backend.routing("qwen3.5:35b")["digest"].startswith("72aac7c2")
    c.scope.check_model("qwen3.5:35b", c.routing_for("qwen3.5:35b"), local=True)
    with pytest.raises(ollama.UnknownLocalModel):         # the profile backend knows no primary model
        c.backend.spec("qwen3.5:9b")


def test_primary_client_cannot_reach_the_35b():
    c = _common.make_client(local=True)
    assert c.backend.api.base == "http://127.0.0.1:11434" and c.log_dir == ollama.LOCAL_CALL_LOG_DIR
    with pytest.raises(ollama.UnknownLocalModel):
        c.backend.spec("qwen3.5:35b")


def test_scope_lists_the_35b_and_still_refuses_d3():
    sc = scope.require(ollama.LOCAL_SCOPE_FILE)
    sc.check_experiment("EXPL_35B_D1TEST")
    assert "qwen3.5:35b" in sc.allowed_models
    with pytest.raises(scope.ScopeViolation):
        sc.check_dataset("D3", "(test)")


# ---- launcher ------------------------------------------------------------------------------------------------
class FakeRun:
    returncode, stderr, stdout = 0, "", ""


def test_start_profile_writes_its_env_into_its_own_log_dir(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(ollama_server.subprocess, "run", lambda *a, **k: calls.append(a) or FakeRun())
    monkeypatch.setattr(ollama_server, "is_up", lambda url=ollama_server.DEFAULT_URL: url.endswith(":11435"))
    p = {**P, "server_log_dir": str(tmp_path / "srv35b")}
    env = ollama_server.start_profile(p, tag="t")
    cmd = (tmp_path / "srv35b" / "launch_server.cmd").read_text(encoding="utf-8")
    assert 'set "OLLAMA_FLASH_ATTENTION=0"' in cmd and 'set "OLLAMA_HOST=127.0.0.1:11435"' in cmd
    assert 'set "OLLAMA_KV_CACHE_TYPE=f16"' in cmd and 'set "OLLAMA_NUM_PARALLEL=1"' in cmd
    assert str(tmp_path / "srv35b") in cmd and env == expl_profile.server_env(P) and len(calls) == 1


def test_start_profile_refuses_while_the_frozen_server_is_up(monkeypatch, tmp_path):
    monkeypatch.setattr(ollama_server, "is_up", lambda url=ollama_server.DEFAULT_URL: True)
    monkeypatch.setattr(ollama_server.subprocess, "run", lambda *a, **k: pytest.fail("must not launch"))
    with pytest.raises(RuntimeError, match="frozen server"):
        ollama_server.start_profile({**P, "server_log_dir": str(tmp_path)})


def test_frozen_launcher_defaults_are_unchanged():
    sig = inspect.signature(ollama_server.start).parameters
    assert sig["log_dir"].default == ollama_server.LOG_DIR and sig["url"].default == "http://127.0.0.1:11434"
    assert sig["env"].default is None
    assert inspect.signature(ollama_server.stop).parameters["url"].default == "http://127.0.0.1:11434"


# ---- entry point -----------------------------------------------------------------------------------------------
@pytest.fixture
def captured(monkeypatch):
    seen = {}
    # These tests describe behaviour before the D-67 time box closes; pin that instead of reading the wall clock,
    # which passed the deadline on 2026-11-11 (the deadline itself is tested on fixed datetimes above).
    monkeypatch.setattr(expl_profile, "past_deadline", lambda p, now=None: False)
    monkeypatch.setattr(run_experiment, "make_client", lambda *a, **k: seen.setdefault("profile", k.get("profile")))
    monkeypatch.setattr(run_experiment, "execute", lambda exp, client, run_dir, *a: seen.update(exp=exp, run_dir=run_dir))
    return seen


def test_only_arm_runs_one_pass_with_the_profile(captured):
    run_experiment.main(["configs/experiments/EXPL_35B_D1TEST.json", "--only-arm", "DEB", "--workers", "1"])
    assert [c["arm"] for c in captured["exp"]["conditions"]] == ["DEB"]
    assert captured["profile"]["base_url"].endswith(":11435")
    assert captured["run_dir"].name == "EXPL_35B_D1TEST"


def test_primary_experiment_gets_no_profile(captured):
    run_experiment.main(["configs/experiments/LOCAL_HO_E5R3_M2.json"])
    assert captured["profile"] is None and len(captured["exp"]["conditions"]) == 3


def test_entry_point_refuses_after_the_deadline(captured, monkeypatch):
    monkeypatch.setattr(expl_profile, "past_deadline", lambda p, now=None: True)
    with pytest.raises(SystemExit, match="deadline"):
        run_experiment.main(["configs/experiments/EXPL_35B_D1TEST.json", "--only-arm", "J1"])
    assert "exp" not in captured


def test_unknown_arm_is_refused(captured):
    with pytest.raises(SystemExit):
        run_experiment.main(["configs/experiments/EXPL_35B_D1TEST.json", "--only-arm", "SC-T"])


# ---- time box --------------------------------------------------------------------------------------------------
def test_watchdog_creates_stop_at_the_deadline(monkeypatch, tmp_path):
    import run_expl_35b
    stop = tmp_path / "STOP"
    monkeypatch.setattr(run_expl_35b, "STOP_FILE", stop)
    assert run_expl_35b.watchdog(P, threading.Event(), now=lambda: datetime(2026, 11, 11, 0, 0), poll_s=0)
    assert stop.read_text(encoding="utf-8").startswith(run_expl_35b.DEADLINE_MARK)


def test_watchdog_before_the_deadline_never_stops(monkeypatch, tmp_path):
    import run_expl_35b
    stop = tmp_path / "STOP"
    monkeypatch.setattr(run_expl_35b, "STOP_FILE", stop)
    evt = threading.Event()
    evt.set()
    assert not run_expl_35b.watchdog(P, evt, now=lambda: datetime(2026, 11, 4), poll_s=0)
    assert not stop.exists()


def test_feasibility_refuses_a_model_the_profile_does_not_serve(monkeypatch):
    import feasibility
    monkeypatch.setattr(sys, "argv", ["feasibility.py", "--model", "qwen3.5:9b", "--role", "judge",
                                      "--profile", "configs/expl_35b.json"])
    with pytest.raises(SystemExit, match="serves qwen3.5:35b"):
        feasibility.main()


def test_arm_passes_are_j1_then_deb_then_sc():
    assert P["arm_passes"] == ["J1", "DEB", "SC"]
    exp = json.loads((ROOT / "configs" / "experiments" / "EXPL_35B_D1TEST.json").read_text(encoding="utf-8"))
    assert [c["arm"] for c in exp["conditions"]] == ["J1", "DEB", "SC"] and exp["model_tag"] == P["model_tag"]


# ---- D-76 fix: the 35b's session records go to its own log ------------------------------------------------
REAL_EXECUTE = run_experiment.execute


class _Stop(Exception):
    pass


def _gate_kwargs(monkeypatch, exp):
    import triage.sessions as sessions
    seen = {}

    def fake(api, model_id, spec, **kw):
        seen.update(model=model_id, **kw)
        raise _Stop

    monkeypatch.setattr(sessions, "g_session_start", fake)

    class B:
        api = object()

        def spec(self, m):
            return {"digest": "x"}

    class C:
        scope, backend = None, B()

    monkeypatch.setattr(run_experiment, "Runner", lambda *a, **k: pytest.fail("must stop at the session gate"))
    with pytest.raises(_Stop):
        REAL_EXECUTE(exp, C(), ROOT / "results" / "smoke" / "never_written")
    return seen


def test_35b_session_gate_writes_to_the_profile_session_log(monkeypatch, captured):
    run_experiment.main(["configs/experiments/EXPL_35B_D1TEST.json", "--only-arm", "J1"])
    exp = captured["exp"]
    assert exp["session_log"] == "logs/sessions_35b.jsonl"
    seen = _gate_kwargs(monkeypatch, exp)
    assert seen["model"] == "qwen3.5:35b" and seen["log"] == ROOT / "logs" / "sessions_35b.jsonl"


def test_primary_session_gate_keeps_the_frozen_session_log(monkeypatch):
    exp = json.loads((ROOT / "configs" / "experiments" / "EXPL_35B_D1TEST.json").read_text(encoding="utf-8"))
    assert "session_log" not in exp
    assert "log" not in _gate_kwargs(monkeypatch, exp)       # g_session_start's default: logs/sessions.jsonl


# ---- D-78: RAM gate waived for the 35b only, replaced by the safety rule ------------------------------------------
import urllib.error  # noqa: E402

from triage import llm, sessions  # noqa: E402


def mon(tmp_path, free=8.0):
    return expl_profile.SafetyMonitor(P["safety"], stop_file=tmp_path / "STOP", events=tmp_path / "ev.jsonl",
                                      ram=lambda: {"free_gib": free})


def test_safety_rule_values_are_the_authors():
    s = P["safety"]
    assert (s["min_available_gib"], s["ram_check_every_calls"], s["latency_window_calls"], s["max_median_latency_s"]) \
        == (0.5, 25, 50, 10.0)
    assert P["ram_gate"]["waived"] and P["label"] == "EXPLORATORY"
    joined = " ".join(P["differences_from_M1"]).lower()
    for k in ("flash attention off", "shared gpu memory", "ram gate is waived", "~3b active"):
        assert k in joined


def test_ram_is_checked_every_25_calls_and_aborts_below_half_a_gib(tmp_path):
    m = mon(tmp_path, free=0.4)
    for _ in range(24):
        m.record(3.0)
    assert not m.aborted and not (tmp_path / "STOP").exists()
    m.record(3.0)
    assert "available RAM 0.40" in m.aborted
    assert (tmp_path / "STOP").read_text(encoding="utf-8").startswith(expl_profile.SAFETY_MARK)


def test_ram_at_or_above_half_a_gib_continues(tmp_path):
    m = mon(tmp_path, free=0.5)
    for _ in range(100):
        m.record(3.0)
    assert not m.aborted


def test_median_latency_of_the_last_50_calls_above_10_s_aborts(tmp_path):
    m = mon(tmp_path)
    for _ in range(49):
        m.record(11.0)
    assert not m.aborted                          # fewer than 50 calls: no median yet
    m.record(11.0)
    assert "median latency" in m.aborted


def test_slow_calls_that_keep_the_median_under_10_s_continue(tmp_path):
    m = mon(tmp_path)
    for i in range(200):
        m.record(30.0 if i % 3 == 0 else 3.3)
    assert not m.aborted


class FakeAPI:
    def __init__(self, exc=None):
        self.exc, self.n = exc, 0

    def chat(self, body):
        self.n += 1
        if self.exc:
            raise self.exc
        return {"message": {"content": "{}"}, "prompt_eval_count": 10, "eval_count": 2, "done_reason": "stop"}

    def ps(self):
        return {}

    def tags(self):
        return {"qwen3.5:35b": {"digest": P["model_spec"]["digest"]}}


def call(b):
    return b.call("qwen3.5:35b", [{"role": "user", "content": "x"}], 0.7, 1.0, 64, False, None, seed=1, role="")


@pytest.mark.parametrize("exc", [urllib.error.URLError("connection refused"), TimeoutError("timed out after 900 s"),
                                 urllib.error.HTTPError("u", 500, "llama runner process has terminated", {}, None)])
def test_server_crash_or_hang_aborts_without_retry(tmp_path, exc):
    api = FakeAPI(exc)
    b = expl_profile.safe_backend(P, api=api, monitor=mon(tmp_path), telemetry=False, verify_digests=False)
    with pytest.raises(llm.StopRequested, match=expl_profile.SAFETY_MARK):
        call(b)
    assert api.n == 1 and b.monitor.aborted.startswith("server crash or hang")
    with pytest.raises(llm.StopRequested):        # nothing further is sent
        call(b)
    assert api.n == 1


def test_a_client_error_is_not_a_crash(tmp_path):
    b = expl_profile.safe_backend(P, api=FakeAPI(urllib.error.HTTPError("u", 400, "bad", {}, None)),
                                  monitor=mon(tmp_path), telemetry=False, verify_digests=False)
    with pytest.raises(llm.AttemptError):
        call(b)
    assert not b.monitor.aborted and not (tmp_path / "STOP").exists()


def test_a_normal_call_is_recorded(tmp_path):
    b = expl_profile.safe_backend(P, api=FakeAPI(), monitor=mon(tmp_path), telemetry=False, verify_digests=False)
    assert call(b)["text"] == "{}" and b.monitor.calls == 1


def test_profile_client_uses_the_safety_backend():
    c = _common.make_client(local=True, profile=P)
    assert isinstance(c.backend.monitor, expl_profile.SafetyMonitor)


def _gate(monkeypatch, tmp_path, free, **kw):
    monkeypatch.setattr(sessions.hwinfo, "ram", lambda: {"free_gib": free, "total_gib": 31.4})
    monkeypatch.setattr(sessions.hwinfo, "gpu", lambda: {})

    class A:
        def chat(self, body):
            return {"message": {"content": "OK"}}

        def tags(self):
            return {"m": {"digest": "d"}}

        def version(self):
            return "0.40.13"

    return sessions.g_session_start(A(), "m", {"digest": "d"}, log=tmp_path / "s.jsonl", **kw)


def test_primary_gate_still_requires_4_gib(monkeypatch, tmp_path):
    with pytest.raises(sessions.SessionPreconditionFailed, match="< 4.0 GiB"):
        _gate(monkeypatch, tmp_path, 2.56)


def test_35b_gate_uses_half_a_gib(monkeypatch, tmp_path):
    assert _gate(monkeypatch, tmp_path, 2.56, min_available_gib=0.5)["ok"]
    with pytest.raises(sessions.SessionPreconditionFailed):
        _gate(monkeypatch, tmp_path, 0.4, min_available_gib=0.5)


def test_only_the_35b_experiment_carries_the_waiver_and_labels(monkeypatch, captured):
    run_experiment.main(["configs/experiments/LOCAL_HO_E5R3_M2.json"])          # execute is still the fake here
    assert "ram_gate_min_gib" not in captured["exp"] and "label" not in captured["exp"]
    run_experiment.main(["configs/experiments/EXPL_35B_D1TEST.json", "--only-arm", "J1"])
    exp = captured["exp"]
    assert exp["ram_gate_min_gib"] == 0.5 and exp["label"] == "EXPLORATORY" and len(exp["differences_from_M1"]) == 4
    assert _gate_kwargs(monkeypatch, exp)["min_available_gib"] == 0.5     # real execute, stopped at the gate


def test_finish_removes_only_tool_created_stop_files():
    import run_expl_35b
    assert f"{expl_profile.SAFETY_MARK}: x".startswith(run_expl_35b.TOOL_MARKS)
    assert f"{run_expl_35b.DEADLINE_MARK} y".startswith(run_expl_35b.TOOL_MARKS)
    assert not "stop (authors)".startswith(run_expl_35b.TOOL_MARKS)
