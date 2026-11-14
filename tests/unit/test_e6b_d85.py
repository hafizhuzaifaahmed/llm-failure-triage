"""D-82/D-85: the E6b third-family judge runs on its own server under the frozen settings (only the port differs), only
for its two experiments, with its own logs; a model without a thinking channel gets no `think` field while the frozen
models' requests are unchanged. Fakes only: no server is started and no model is loaded."""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "local"))

import e6b  # noqa: E402
from triage import expl_profile, ollama, scope  # noqa: E402

E6B = json.loads(expl_profile.E6B_PROFILE_FILE.read_text(encoding="utf-8"))


def write(tmp_path, **change):
    p = copy.deepcopy(E6B)
    p.update(change)
    f = tmp_path / "e6b.json"
    f.write_text(json.dumps(p), encoding="utf-8")
    return f


def test_profile_loads_and_keeps_the_frozen_server_settings():
    p = expl_profile.load(expl_profile.E6B_PROFILE_FILE)
    assert p["kind"] == "e6b" and set(p["server_env_overrides"]) == {"OLLAMA_HOST"}
    env = expl_profile.server_env(p)
    from triage.ollama_server import base_env
    frozen = base_env()
    assert {k: v for k, v in env.items() if k != "OLLAMA_HOST"} == {k: v for k, v in frozen.items() if k != "OLLAMA_HOST"}
    assert env["OLLAMA_HOST"].endswith(":11436")


@pytest.mark.parametrize("bad", [{"OLLAMA_HOST": "127.0.0.1:11436", "OLLAMA_FLASH_ATTENTION": "0"},
                                 {"OLLAMA_HOST": "127.0.0.1:11436", "OLLAMA_KV_CACHE_TYPE": "q8_0"},
                                 {"OLLAMA_HOST": "127.0.0.1:11434"}])
def test_profile_refuses_any_other_setting_or_the_frozen_port(tmp_path, bad):
    with pytest.raises(expl_profile.ProfileError):
        expl_profile.load(write(tmp_path, server_env_overrides=bad))


def test_profile_refuses_the_frozen_log_directories(tmp_path):
    with pytest.raises(expl_profile.ProfileError):
        expl_profile.load(write(tmp_path, call_log_dir="data/raw/llm_calls_local"))


def test_each_experiment_finds_its_own_profile_and_primary_runs_none():
    assert expl_profile.for_experiment("LOCAL_HO_E6B_D1TEST")["kind"] == "e6b"
    assert expl_profile.for_experiment("LOCAL_DEV_E6B_CHECK")["kind"] == "e6b"
    assert expl_profile.for_experiment("EXPL_35B_D1TEST")["model_tag"] == "qwen3.5:35b"
    for name in ("LOCAL_HO_E1E3_M1", "LOCAL_HO_E5R3_M2", "LOCAL_HO_E4_M1"):
        assert expl_profile.for_experiment(name) is None


def test_candidate_order_is_the_pre_registered_one():
    assert E6B["candidate_order"] == ["ministral-3:14b-instruct-2512-q4_K_M", "phi4:14b-q4_K_M",
                                      "mistral-nemo:12b-instruct-2407-q4_K_M", "llama3.1:8b-instruct-q4_K_M"]


def test_scope_admits_the_e6b_experiments_and_candidates_only():
    sc = scope.load(scope.LOCAL_SCOPE_FILE)
    for name in E6B["experiments"]:
        sc.check_experiment(name)
    for tag in E6B["candidate_order"]:
        sc.check_model(tag, {"digest": "d" * 64}, local=True)
    with pytest.raises(scope.ScopeViolation):
        sc.check_experiment("LOCAL_HO_E8_VOTE")       # only the three named E8 batches are in scope (D-90)


class FakeAPI:
    def __init__(self, caps):
        self.caps, self.bodies = caps, []

    def tags(self):
        return {"m:x": {"digest": "d" * 64, "size": 10}}

    def show(self, tag):
        return {"parameters": "top_k 40\nrepeat_penalty 1.1", "capabilities": self.caps,
                "details": {"family": "fam", "quantization_level": "Q4_K_M", "parameter_size": "14B", "format": "gguf"}}

    def chat(self, body):
        self.bodies.append(body)
        return {"message": {"content": '{"label": "TEST_FAULT"}'}, "prompt_eval_count": 10, "eval_count": 5,
                "done_reason": "stop"}


def test_spec_records_no_think_for_a_model_without_a_thinking_channel():
    assert e6b.spec_from_server(FakeAPI(["completion"]), "m:x")["think"] is None
    assert e6b.spec_from_server(FakeAPI(["completion", "thinking"]), "m:x")["think"] is False
    s = e6b.spec_from_server(FakeAPI(["completion"]), "m:x")
    assert s["top_k"] == 40 and s["repeat_penalty"] == 1.1 and s["num_ctx"] == 8192 and s["require_gpu_resident"]


@pytest.mark.parametrize("think,expect_field", [(None, False), (False, True)])
def test_backend_omits_think_only_when_the_spec_says_none(think, expect_field):
    api = FakeAPI(["completion"])
    spec = {"digest": "d" * 64, "num_ctx": 8192, "think": think, "keep_alive": "30m", "top_k": 40}
    b = ollama.OllamaBackend({"base_url": "http://x", "models": {"m:x": spec}}, api=api, verify_digests=False)
    b.call("m:x", [{"role": "user", "content": "hi"}], 0.7, 1.0, 64, False, b.routing("m:x"), seed=1, role="judge")
    assert ("think" in api.bodies[-1]) is expect_field
    if expect_field:
        assert api.bodies[-1]["think"] is False


def test_runner_fills_the_candidate_into_the_experiment(tmp_path, monkeypatch):
    import run_experiment
    prof = copy.deepcopy(E6B)
    prof.update(model_tag="phi4:14b-q4_K_M", model_spec={"digest": "d" * 64, "num_ctx": 8192, "think": None})
    prof["safety"]["max_median_latency_s"] = 9.0
    seen = {}
    prof.pop("selection_gated", None)                  # the dev check is not selection-gated anyway
    monkeypatch.setattr(expl_profile, "for_experiment", lambda name, path=None: prof)
    monkeypatch.setattr(run_experiment, "make_client", lambda *a, **k: "client")
    monkeypatch.setattr(run_experiment, "execute", lambda exp, client, run_dir, *a, **k: seen.update(exp=exp, run_dir=run_dir))
    run_experiment.main([str(ROOT / "configs" / "experiments" / "LOCAL_DEV_E6B_CHECK.json")])
    assert seen["exp"]["model_tag"] == "phi4:14b-q4_K_M"
    assert seen["run_dir"].name == "CHECK_E6B_phi4_14b-q4_K_M" or "phi4" in seen["run_dir"].name
    assert seen["exp"]["decisions"] == ["D-82", "D-83", "D-85", "D-90", "D-95", "D-109"] and seen["exp"]["ram_gate_min_gib"] == 4.0


def test_runner_refuses_an_unregistered_candidate(monkeypatch):
    import run_experiment
    prof = copy.deepcopy(E6B)
    prof.update(model_tag=None, model_spec=None)       # not registered (the live profile may hold a candidate)
    monkeypatch.setattr(expl_profile, "for_experiment", lambda name, path=None: prof)
    _no_server(monkeypatch, run_experiment)
    with pytest.raises(SystemExit):
        run_experiment.main([str(ROOT / "configs" / "experiments" / "LOCAL_HO_E6B_D1TEST.json")])


def _no_server(monkeypatch, run_experiment):
    """D-87: a test of the runner must never reach a client or a server, whatever the live profile holds."""
    def boom(*a, **k):
        raise AssertionError("test reached a model client")
    monkeypatch.setattr(run_experiment, "make_client", boom)
    monkeypatch.setattr(run_experiment, "execute", boom)


@pytest.mark.parametrize("selected,refused", [(None, True), ("phi4:14b-q4_K_M", True),
                                              ("ministral-3:14b-instruct-2512-q4_K_M", False)])
def test_heldout_runs_only_for_the_selected_candidate(tmp_path, monkeypatch, selected, refused):
    import run_experiment
    prof = copy.deepcopy(E6B)
    prof.update(model_tag="ministral-3:14b-instruct-2512-q4_K_M", model_spec={"digest": "d" * 64, "think": None})
    sel = tmp_path / "selection.json"
    sel.write_text(json.dumps({"selected": selected}), encoding="utf-8")
    prof["selection_gated"] = {"experiments": ["LOCAL_HO_E6B_D1TEST"], "selection_file": str(sel)}
    monkeypatch.setattr(expl_profile, "for_experiment", lambda name, path=None: prof)
    monkeypatch.setattr(expl_profile, "resolve", lambda rel: Path(rel))
    reached = {}
    monkeypatch.setattr(run_experiment, "make_client", lambda *a, **k: "client")
    monkeypatch.setattr(run_experiment, "execute", lambda exp, *a, **k: reached.update(tag=exp["model_tag"]))
    ho = str(ROOT / "configs" / "experiments" / "LOCAL_HO_E6B_D1TEST.json")
    if refused:
        with pytest.raises(SystemExit):
            run_experiment.main([ho])
        assert not reached
    else:
        run_experiment.main([ho])
        assert reached["tag"] == "ministral-3:14b-instruct-2512-q4_K_M"


def test_live_profile_is_selection_gated_and_logs_safety_events_apart():
    assert E6B["selection_gated"]["experiments"] == ["LOCAL_HO_E6B_D1TEST", "LOCAL_HO_E8_VOTE_E6B", "LOCAL_HO_KUU_D2_E6B",
                                                     "LOCAL_HO_KUUNG_D1_E6B", "LOCAL_HO_KUUNG_D2_E6B"]
    assert E6B["selection_gated"]["selection_file"] == "results/e6b/selection.json"
    b = expl_profile.safe_backend(E6B if E6B.get("model_spec") else {**E6B, "model_tag": "m:x",
                                  "model_spec": {"digest": "d" * 64, "num_ctx": 8192, "think": None}}, api=FakeAPI([]),
                                  verify_digests=False)
    assert b.monitor.events == expl_profile.resolve("results/e6b/safety_events.jsonl")
    assert b.monitor.events != expl_profile.SAFETY_EVENTS
