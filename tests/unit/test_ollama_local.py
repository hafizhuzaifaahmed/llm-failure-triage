"""Local Ollama backend, tested against a fake Ollama HTTP server (no real model, no GPU)."""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from triage import execution, ollama, scope  # noqa: E402
from triage.io_utils import read_jsonl, write_jsonl  # noqa: E402
from triage.llm import LLMClient  # noqa: E402
from triage.ollama import ContextOverflow, DigestMismatch, OllamaAPI, OllamaBackend, ResidencyLost  # noqa: E402
from triage.prompts import PromptSet  # noqa: E402
from triage.runner import Runner, order_tasks  # noqa: E402

TAG = "fakejudge:9b"
DIGEST = "sha256:aaaa"


class State:
    def __init__(self):
        self.reset()

    def reset(self):
        self.requests = []
        self.digest = DIGEST
        self.size, self.size_vram = 100, 100
        self.thinking = ""
        self.prompt_eval = 500
        self.cached = 0
        self.fail_after = None      # raise a 500 after this many /api/chat calls
        self.answered = 0
        self.content = json.dumps({"label": "TEST_FAULT", "reason_category": "OTHER", "evidence_ids": ["F2"],
                                   "summary": "s", "confidence": 50})


STATE = State()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/api/version":
            return self._send({"version": "0.40.13"})
        if self.path == "/api/tags":
            return self._send({"models": [{"name": TAG, "digest": STATE.digest}]})
        if self.path == "/api/ps":
            return self._send({"models": [{"name": TAG, "size": STATE.size, "size_vram": STATE.size_vram,
                                           "context_length": 8192, "digest": STATE.digest}]})
        self._send({}, 404)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/api/chat":
            STATE.requests.append(body)
            if STATE.fail_after is not None and len(STATE.requests) > STATE.fail_after:
                return self._send({"error": "crash"}, 500)
            STATE.answered += 1
            msg = body["messages"][0]["content"]
            content = STATE.content
            if '"position"' in msg and "adjudicator" not in msg:
                content = json.dumps({"position": "TEST_FAULT", "argument": "a", "evidence_ids": ["F2"], "concede": False})
            return self._send({"model": TAG, "message": {"role": "assistant", "content": content, "thinking": STATE.thinking},
                               "done": True, "done_reason": "stop", "prompt_eval_count": STATE.prompt_eval,
                               "prompt_eval_cached_count": STATE.cached, "eval_count": 40, "total_duration": 2_000_000_000,
                               "load_duration": 1, "prompt_eval_duration": 1, "eval_duration": 1})
        if self.path == "/api/show":
            return self._send({"details": {"quantization_level": "Q4_K_M"}})
        self._send({}, 404)


@pytest.fixture(scope="module")
def server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


CFG = {"roles": {"M1": TAG}, "models": {TAG: {"digest": DIGEST, "num_ctx": 8192, "top_k": 20, "min_p": 0.0,
                                               "think": False, "quantization": "Q4_K_M", "require_gpu_resident": True}}}


@pytest.fixture()
def local(tmp_path, monkeypatch, server):
    STATE.reset()
    sc = tmp_path / "local_scope.json"
    sc.write_text(json.dumps({"scope": "local_dev_selection", "allowed_splits": ["dev"],
                              "allowed_experiments": ["LOCAL_DEV"], "allowed_models": [TAG]}))
    monkeypatch.setattr(ollama, "LOCAL_SCOPE_FILE", sc)

    def make():
        return LLMClient(OllamaBackend(CFG, api=OllamaAPI(server), telemetry=False), log_dir=tmp_path / "calls",
                         sleep=lambda s: None)
    return make, tmp_path


MSG = [{"role": "user", "content": "Evidence package text " * 20}]


def test_request_carries_explicit_options_schema_and_think_off(local):
    make, tmp = local
    r = make().complete(role="judge", model_id=TAG, messages=MSG, sample_index=3)
    req = STATE.requests[-1]
    assert req["options"]["num_ctx"] == 8192 and req["options"]["num_predict"] == 512
    assert req["options"]["temperature"] == 0.7 and req["options"]["top_k"] == 20 and "seed" in req["options"]
    assert req["think"] is False and req["format"]["properties"]["label"]["enum"] == ["PROGRAM_FAULT", "TEST_FAULT"]
    rec = list(read_jsonl(tmp / "calls" / "fakejudge_9b.jsonl"))[0]
    assert rec["cost_usd"] == 0 and rec["cost_source"] == "local" and rec["local"]["gpu_resident"]
    assert rec["local"]["eval_count"] == 40 and rec["local"]["gpu_seconds"] == 2.0 and r.output_tokens == 40


def test_generator_role_sends_no_schema(local):
    make, _ = local
    make().complete(role="generator", model_id=TAG, messages=MSG, json_mode=False, max_tokens=4096)
    assert "format" not in STATE.requests[-1]


def test_seed_is_deterministic_per_request_and_differs_across_samples(local):
    make, _ = local
    c = make()
    c.complete(role="judge", model_id=TAG, messages=MSG, sample_index=0)
    c.complete(role="judge", model_id=TAG, messages=MSG, sample_index=1)
    s0, s1 = STATE.requests[-2]["options"]["seed"], STATE.requests[-1]["options"]["seed"]
    assert s0 != s1
    c2 = LLMClient(c.backend, log_dir=c.log_dir.parent / "calls2", sleep=lambda s: None)
    c2.complete(role="judge", model_id=TAG, messages=MSG, sample_index=0)
    assert STATE.requests[-1]["options"]["seed"] == s0


def test_digest_mismatch_stops_before_any_chat(local):
    make, _ = local
    STATE.digest = "sha256:bbbb"
    with pytest.raises(DigestMismatch):
        make().complete(role="judge", model_id=TAG, messages=MSG)
    assert STATE.requests == []


def test_thinking_output_makes_the_answer_invalid_and_is_logged(local):
    make, tmp = local
    STATE.thinking = "let me reason about this"
    r = make().complete(role="judge", model_id=TAG, messages=MSG)
    rec = list(read_jsonl(tmp / "calls" / "fakejudge_9b.jsonl"))[0]
    assert r.text == "" and rec["local"]["thinking_violation"] and rec["local"]["thinking"].startswith("let me")


def test_possible_truncation_is_fatal_now_and_on_resume(local):
    make, _ = local
    STATE.prompt_eval = 7800                # 7800 + 512 > 8192
    with pytest.raises(ContextOverflow):
        make().complete(role="judge", model_id=TAG, messages=MSG)
    n = len(STATE.requests)
    with pytest.raises(ContextOverflow):     # served from the log, still refused
        make().complete(role="judge", model_id=TAG, messages=MSG)
    assert len(STATE.requests) == n


def test_oversized_prompt_refused_before_sending(local):
    make, _ = local
    with pytest.raises(ContextOverflow):     # 60000 / 6.0 + 512 > 8192: cannot fit at any tokenization
        make().complete(role="judge", model_id=TAG, messages=[{"role": "user", "content": "x" * 60000}])
    assert STATE.requests == []


@pytest.mark.parametrize("chars,reported", [(20000, 4098), (19712, 4098), (18500, 4100)])   # > 4.5 chars/token (D-68)
def test_silent_half_context_truncation_is_detected(local, chars, reported):
    """D-35: Ollama cuts an oversized prompt to about num_ctx/2 without saying so; the short count is the tell.
    D-68: (18000, 4098) and (16000, 4100) left this list -- 4.39 / 3.90 chars per token is a normal-density band hit."""
    make, _ = local
    STATE.prompt_eval = reported
    with pytest.raises(ContextOverflow):
        make().complete(role="judge", model_id=TAG, messages=[{"role": "user", "content": "y" * chars}])


def test_untruncated_prompts_are_not_flagged():
    from triage.ollama import truncation_suspected
    assert not truncation_suspected(11500, 4098, 8192, 512)      # a genuine 4k-token package, 2.8 chars/token
    assert not truncation_suspected(16800, 6000, 8192, 512)
    assert not truncation_suspected(2000, 500, 8192, 512)        # short prose, 4.0 chars/token
    assert not truncation_suspected(3516, 778, 8192, 4096)       # D-41: a real gemma4:26b generator prompt, 4.52
    assert truncation_suspected(43840, 4099, 8192, 64)           # D-41: measured gemma overflow (llamacpp runner)
    assert truncation_suspected(21700, 4098, 8192, 512)          # the observed qwen3.5:9b probe J14
    assert truncation_suspected(10000, 7700, 8192, 512)          # no room left to answer


def test_package_cap_and_argument_cap():
    from triage import config
    from triage.preprocess import approx_tokens, cap_words
    assert approx_tokens("a" * 13000) < 6000 < approx_tokens("a" * 13400)                   # 2.2 chars/token estimate (D-36)
    long_arg = " ".join(f"w{i}" for i in range(400))
    assert len(cap_words(long_arg).split()) == config.MAX_ARGUMENT_WORDS + 1   # + the truncation marker
    assert cap_words("short argument") == "short argument"


def test_residency_loss_stops_the_session(local):
    make, _ = local
    STATE.size_vram = 80
    with pytest.raises(ResidencyLost):
        make().complete(role="judge", model_id=TAG, messages=MSG)


def test_local_scope_refuses_unlisted_model_and_missing_digest(local, server):
    make, _ = local
    cfg = {"models": {"other:1b": {"digest": DIGEST, "num_ctx": 8192}, TAG: {"num_ctx": 8192}}}
    c = LLMClient(OllamaBackend(cfg, api=OllamaAPI(server), telemetry=False), log_dir=local[1] / "c3")
    with pytest.raises(scope.ScopeViolation):
        c.complete(role="judge", model_id="other:1b", messages=MSG)
    with pytest.raises(scope.ScopeViolation):
        c.complete(role="judge", model_id=TAG, messages=MSG)   # no pinned digest
    assert STATE.requests == []


def test_local_ledger_counts_gpu_time_not_dollars(local):
    make, tmp = local
    c = make()
    for i in range(3):
        c.complete(role="judge", model_id=TAG, messages=MSG, sample_index=i)
    led = ollama.local_ledger(tmp / "calls")
    assert led["calls"] == 3 and abs(led["gpu_hours"] - 6 / 3600) < 1e-9 and led["usd"] == 0


def _instance(i, split="dev"):
    return {"instance_id": f"i{i}", "focal_id": "Cli_1::f", "project": "Cli", "bug_name": "Cli_1", "split": split,
            "focal_class": "org.x.Foo", "focal_method_name": "bar",
            "test": {"method_source": "@Test\npublic void t() {\n  assertEquals(1, f());\n}", "imports": [], "fixtures": ""},
            "failure": {"outcome_type": "assertion_failure", "exception_class": "java.lang.AssertionError",
                        "message": f"expected:<{i}>", "failing_test_line": 3, "failing_test_line_text": "x", "frames": []},
            "sig": {"focal_signature": "public int bar()", "class_declaration": "public class Foo", "constructors": [],
                    "methods": [], "type_signatures": []},
            "doc": {"method_javadoc": "", "class_javadoc": ""}, "impl": "public int bar() {\n return 1;\n}"}


def test_kill_and_resume_neither_duplicates_nor_loses_calls(local):
    """Idempotency proof: the server crashes mid-run; the resumed run completes every decision and every
    distinct request is answered exactly once (crashed attempts got no answer, so they are not duplicates)."""
    make, tmp = local
    from triage import dataset
    insts = [_instance(i) for i in range(6)]
    guard = {i["instance_id"]: dataset.guard_record(i["instance_id"], "Cli_1", None, i["impl"]) for i in insts}
    conds = [{"arm": "J1", "levels": ["S0"]}, {"arm": "SC", "levels": ["S0"]}]   # 6 x (1 + 5) = 36 calls
    STATE.fail_after = 14
    r1 = Runner(tmp / "run", make(), PromptSet.named("v0"), TAG, forbidden=guard, workers=1)
    r1.run(insts, conds, replicates=1)
    first = list(read_jsonl(tmp / "run" / "decisions.jsonl"))
    assert 0 < len(first) < 12 and STATE.answered == 14
    STATE.fail_after = None
    r2 = Runner(tmp / "run", make(), PromptSet.named("v0"), TAG, forbidden=guard, workers=1)
    r2.run(insts, conds, replicates=1)
    decisions = list(read_jsonl(tmp / "run" / "decisions.jsonl"))
    keys = [(d["instance_id"], d["arm"]) for d in decisions]
    assert len(keys) == 12 and len(set(keys)) == 12                      # nothing lost, nothing duplicated
    logged = list(read_jsonl(tmp / "calls" / "fakejudge_9b.jsonl"))
    assert len(logged) == 36 and len({r["key"] for r in logged}) == 36    # each request logged once
    assert STATE.answered == 36                                          # and answered by the server once


def test_task_order_interleaves_arms_within_instance_batches():
    insts = [{"instance_id": f"i{k}"} for k in range(20)]
    tasks = [(i, arm, "S1", "full", 0, None) for arm in ("J1", "SC", "DEB") for i in insts]   # arm blocks
    out = order_tasks(tasks, batch=4)
    first_batch = out[:12]
    assert len({t[0]["instance_id"] for t in first_batch}) == 4
    assert {t[1] for t in first_batch} == {"J1", "SC", "DEB"}
    assert out == order_tasks(list(reversed(tasks)), batch=4)          # deterministic, input-order independent


def test_cobertura_parser_restricts_to_focal_lines():
    xml = """<coverage><packages><package><classes>
      <class name="org.x.Foo" filename="org/x/Foo.java"><lines>
        <line number="9" hits="1"/>
        <line number="10" hits="2" branch="true" condition-coverage="50% (1/2)"/>
        <line number="11" hits="0"/>
        <line number="30" hits="5"/>
      </lines></class></classes></package></packages></coverage>"""
    r = execution.parse_cobertura(xml, "org.x.Foo", 10, 12)
    assert r["lines_total"] == 2 and r["lines_covered"] == 1 and r["branches_total"] == 2 and r["branch_rate"] == 0.5


def test_local_runs_refuse_held_out_data_through_the_live_entry_point(local):
    """Hard rule: before the authors approve, held-out instances cannot be judged by a local model."""
    import run_experiment
    from triage import dataset
    make, tmp = local
    held = _instance(0, split="test")
    write_jsonl(tmp / "inst.jsonl", [held])
    (tmp / "sample.json").write_text(json.dumps({"instance_ids": [held["instance_id"]]}))
    write_jsonl(tmp / "guard.jsonl", [dataset.guard_record(held["instance_id"], "Cli_1", None, held["impl"])])
    exp = {"name": "LOCAL_DEV", "dataset": "D1", "split": "test", "model": TAG, "prompt_set": "v0", "replicates": 1,
           "instances_file": str(tmp / "inst.jsonl"), "sample_file": str(tmp / "sample.json"),
           "guard_file": str(tmp / "guard.jsonl"), "specs_file": str(tmp / "n.jsonl"),
           "specs_prime_file": str(tmp / "n.jsonl"), "conditions": [{"arm": "J1", "levels": ["S1"]}]}
    with pytest.raises(scope.ScopeViolation):
        run_experiment.execute(exp, make(), tmp / "run", workers=1)
    exp.update(split="dev", name="LOCAL_HELDOUT_RUN")
    held["split"] = "dev"
    write_jsonl(tmp / "inst.jsonl", [held])
    with pytest.raises(scope.ScopeViolation):          # experiment not in the local scope
        run_experiment.execute(exp, make(), tmp / "run", workers=1)
    assert STATE.requests == []
    s = make().scope
    with pytest.raises(scope.ScopeViolation):          # generation/spec entry points use the same check
        s.check_items([{"focal_id": "Lang_1::x", "split": "test"}], "focal method")


def test_cached_prefix_is_not_double_counted(local):
    """D-37: Ollama's prompt_eval_count already includes prompt_eval_cached_count (a repeat of a 5,691-token prompt
    reports 5,691 with 5,687 cached). Summing them would read 11,378 and stop every SC run as 'truncated'."""
    make, tmp = local
    STATE.prompt_eval, STATE.cached = 5691, 5687
    r = make().complete(role="judge", model_id=TAG, messages=[{"role": "user", "content": "z" * 14000}])
    rec = list(read_jsonl(tmp / "calls" / "fakejudge_9b.jsonl"))[-1]
    assert not rec["local"]["possibly_truncated"] and r.input_tokens == 5691


def test_runaway_rate_tracked_per_arm(tmp_path):
    """D-39: the J11 failure mode (INVALID and stopped at num_predict) is counted per arm for G-a."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("dev_gates", ROOT / "scripts" / "local" / "dev_gates.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    good = '{"label": "TEST_FAULT", "reason_category": "wrong_expected_value", "evidence_ids": ["T1"], ' \
           '"summary": "ok", "confidence": 0.7}'
    with open(tmp_path / "m.jsonl", "w", encoding="utf-8") as f:
        for k, text, fr in (("a", good, "stop"), ("b", '{"label": "TEST_FAULT", "summary": "and then', "length"),
                            ("c", "not json", "stop")):
            f.write(json.dumps({"key": k, "role": "judge", "text": text, "finish_reason": fr}) + "\n")
    decs = [{"arm": "J1", "cost": {"call_keys": ["a"]}}, {"arm": "J1", "cost": {"call_keys": ["b"]}},
            {"arm": "SC", "cost": {"call_keys": ["c"]}}]
    out = mod.runaway_counts(decs, log_dir=tmp_path)
    assert out["J1"] == {"calls": 2, "invalid": 1, "invalid_length": 1, "runaway_rate": 0.5}
    assert out["SC"]["invalid"] == 1 and out["SC"]["invalid_length"] == 0


@pytest.mark.parametrize("avail,ok", [(9.0, True), (3.9, False)])
def test_g_session_precondition_ram(server, tmp_path, monkeypatch, avail, ok):
    """D-40: every G session checks available RAM after G loads; below 4 GiB it stops, and either way it logs."""
    from triage import hwinfo, sessions
    STATE.reset()
    monkeypatch.setattr(hwinfo, "ram", lambda: {"free_gib": avail, "total_gib": 31.4})
    monkeypatch.setattr(hwinfo, "gpu", lambda: {})
    log = tmp_path / "sessions.jsonl"
    spec = CFG["models"][TAG]
    if ok:
        rec = sessions.g_session_start(OllamaAPI(server), TAG, spec, log=log)
        assert rec["ok"] and rec["available_ram_gib"] == 9.0
    else:
        with pytest.raises(sessions.SessionPreconditionFailed):
            sessions.g_session_start(OllamaAPI(server), TAG, spec, log=log)
    rows = list(read_jsonl(log))
    assert len(rows) == 1 and rows[0]["event"] == "g_session_start" and rows[0]["ok"] is ok
    assert STATE.requests[-1]["think"] is False and STATE.requests[-1]["options"]["num_ctx"] == 8192


def test_g_session_precondition_digest(server, tmp_path, monkeypatch):
    from triage import hwinfo, sessions
    STATE.reset()
    STATE.digest = "f" * 64
    monkeypatch.setattr(hwinfo, "ram", lambda: {"free_gib": 9.0, "total_gib": 31.4})
    monkeypatch.setattr(hwinfo, "gpu", lambda: {})
    with pytest.raises(sessions.SessionPreconditionFailed, match="digest"):
        sessions.g_session_start(OllamaAPI(server), TAG, CFG["models"][TAG], log=tmp_path / "s.jsonl")


def test_execution_side_lock_refuses_held_out_and_unknown(tmp_path, monkeypatch):
    """The held-out lock also binds WSL execution, which involves no LLM call: test-split or unknown focal
    methods are refused before anything is compiled or run."""
    from triage import config as cfg, scope
    ctx = tmp_path / "context"
    ctx.mkdir()
    (ctx / "a.json").write_text(json.dumps({"focal_id": "Gson_1::A::m", "split": "dev"}))
    (ctx / "b.json").write_text(json.dumps({"focal_id": "Lang_9::B::n", "split": "test"}))
    monkeypatch.setattr(cfg, "INTERIM", tmp_path)
    sc = tmp_path / "local_scope.json"
    sc.write_text(json.dumps({"scope": "local_dev_selection", "allowed_splits": ["dev"],
                              "allowed_experiments": ["X"], "allowed_models": [TAG]}))
    assert scope.check_focal_ids_local(["Gson_1::A::m"], "execution", path=sc) == 1
    for fid in ("Lang_9::B::n", "Never_1::C::o"):
        with pytest.raises(scope.ScopeViolation):
            scope.check_focal_ids_local([fid], "execution", path=sc)


def test_cached_call_is_rejudged_with_the_current_rule(local):
    """D-41: a call flagged by an earlier, wrong rule is served from the log once the current rule clears it."""
    make, tmp = local
    STATE.prompt_eval = 778
    c = make()
    c.complete(role="generator", model_id=TAG, messages=[{"role": "user", "content": "w" * 3516}],
               json_mode=False, max_tokens=4096)
    f = tmp / "calls" / "fakejudge_9b.jsonl"
    rows = list(read_jsonl(f))
    rows[-1]["local"]["possibly_truncated"] = True          # as written by the old D-35 rule
    f.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    n = len(STATE.requests)
    r = make().complete(role="generator", model_id=TAG, messages=[{"role": "user", "content": "w" * 3516}],
                        json_mode=False, max_tokens=4096)
    assert r.cached and len(STATE.requests) == n
