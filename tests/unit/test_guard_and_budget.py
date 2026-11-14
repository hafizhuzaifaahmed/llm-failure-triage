"""Leakage guard (end to end through the live entry point) and budget/recovery behaviour of the LLM client.
All model behaviour here is a mock or a fake backend: no network, no cost."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import run_experiment  # noqa: E402
from triage import config, context_builder, dataset, llm  # noqa: E402
from triage.io_utils import read_jsonl, write_jsonl  # noqa: E402
from triage.llm import AttemptError, BudgetExceeded, LLMClient, MockBackend, UnknownPrice  # noqa: E402
from triage.runner import Runner  # noqa: E402

FIXED_ONLY = "if (hexDigits > 8) { return createLong(str); }"


def _instance(iid, message="expected:<1> but was:<2>", test_extra=""):
    return {
        "instance_id": iid, "focal_id": "Cli_7::f", "project": "Cli", "bug_name": "Cli_7", "split": "dev",
        "focal_class": "org.x.Foo", "focal_method_name": "bar",
        "test": {"method_source": f"@Test\npublic void t() {{\n  assertEquals(1, new Foo().bar());{test_extra}\n}}",
                 "imports": [], "fixtures": ""},
        "failure": {"outcome_type": "assertion_failure", "exception_class": "java.lang.AssertionError",
                    "message": message, "failing_test_line": 3, "failing_test_line_text": "assertEquals(...)",
                    "frames": []},
        "sig": {"focal_signature": "public int bar()", "class_declaration": "public class Foo",
                "constructors": [], "methods": [], "type_signatures": []},
        "doc": {"method_javadoc": "/** doc */", "class_javadoc": ""},
        "impl": "public int bar() {\n  return 2;\n}", "covariates": {"javadoc_present": True},
    }


class Recorder:
    def __init__(self):
        self.prompts = []

    def __call__(self, model, messages):
        self.prompts.append(messages[0]["content"])
        if '"position"' in messages[0]["content"] and "adjudicator" not in messages[0]["content"]:
            return json.dumps({"position": "TEST_FAULT", "argument": "x", "evidence_ids": ["F2"], "concede": False})
        return json.dumps({"label": "TEST_FAULT", "reason_category": "OTHER", "evidence_ids": ["F2"],
                           "summary": "s", "confidence": 50})


def _setup(tmp_path, with_guard=True):
    clean = _instance("clean")
    bug_id = _instance("bugid", message="see Cli_7 for details")          # short id: was unchecked before
    fixed = _instance("fixedline", test_extra=f"\n  // {FIXED_ONLY}")   # fixed-only code in the package
    insts = [clean, bug_id, fixed]
    write_jsonl(tmp_path / "instances.jsonl", insts)
    (tmp_path / "sample.json").write_text(json.dumps({"instance_ids": [i["instance_id"] for i in insts]}))
    fixed_body = "public int bar() {\n  " + FIXED_ONLY + "\n  return 2;\n}"
    if with_guard:
        write_jsonl(tmp_path / "guard.jsonl",
                    [dataset.guard_record(i["instance_id"], "Cli_7", fixed_body, i["impl"]) for i in insts])
    exp = {"name": "t", "dataset": "D1", "split": "dev", "model": "M1", "prompt_set": "v0", "replicates": 1,
           "instances_file": str(tmp_path / "instances.jsonl"), "sample_file": str(tmp_path / "sample.json"),
           "guard_file": str(tmp_path / "guard.jsonl"), "specs_file": str(tmp_path / "none.jsonl"),
           "specs_prime_file": str(tmp_path / "none.jsonl"),
           "conditions": [{"arm": "J1", "levels": ["S1"]}, {"arm": "DEB", "levels": ["S1"]}]}
    return exp


def test_guard_rejects_bug_ids_and_fixed_lines_before_any_call(tmp_path):
    exp = _setup(tmp_path)
    rec = Recorder()
    client = LLMClient(MockBackend(rec), log_dir=tmp_path / "calls")
    run_experiment.execute(exp, client, tmp_path / "run", workers=2)
    decisions = list(read_jsonl(tmp_path / "run" / "decisions.jsonl"))
    rejected = list(read_jsonl(tmp_path / "run" / "leakage_rejections.jsonl"))
    assert {d["instance_id"] for d in decisions} == {"clean"}
    assert {r["instance_id"] for r in rejected} == {"bugid", "fixedline"} and len(rejected) == 4
    assert len(rec.prompts) == 1 + 5                      # J1 + DEB for the clean instance only
    assert not any("Cli_7" in p or FIXED_ONLY in p for p in rec.prompts)


def test_real_run_refuses_without_guard_file(tmp_path):
    exp = _setup(tmp_path, with_guard=False)
    client = LLMClient(MockBackend(Recorder()), log_dir=tmp_path / "calls")
    with pytest.raises(SystemExit):
        run_experiment.execute(exp, client, tmp_path / "run", workers=1)


def test_runner_rejects_instance_without_guard_entry(tmp_path):
    rec = Recorder()
    from triage.prompts import PromptSet
    r = Runner(tmp_path / "run", LLMClient(MockBackend(rec), log_dir=tmp_path / "c"), PromptSet.named("v0"),
               "m", forbidden={}, require_guard=True)
    r.run([_instance("clean")], [{"arm": "J1", "levels": ["S0"]}], 1)
    assert rec.prompts == [] and len(list(read_jsonl(tmp_path / "run" / "leakage_rejections.jsonl"))) == 1


def test_leakage_check_short_ids_and_generic_patterns():
    g = dataset.guard_record("i", "Csv_3", None, "")
    assert context_builder.leakage_check("value Csv_3 here", g) == ["Csv_3", "Csv_3"]
    assert context_builder.leakage_check("see Math-12b", {}) == ["Math-12b"]
    assert context_builder.leakage_check("clean package text", g) == []


# ------------------------------------------------------------------ budget and recovery
PROVIDERS = {"models": {"known/model": {"pinned_provider": "P", "routing": {"only": ["p"], "allow_fallbacks": False},
                                        "endpoints": {"P": {"input_per_m": 1.0, "output_per_m": 2.0},
                                                      "Q": {"input_per_m": 3.0, "output_per_m": 4.0}}}}}


class FakePaid(llm.Backend):
    name = "fake"

    def __init__(self, script):
        self.script, self.calls = list(script), 0

    def call(self, model_id, messages, temperature, top_p, max_tokens, json_mode, routing, **kw):
        self.calls += 1
        step = self.script.pop(0)
        if isinstance(step, Exception):
            raise step
        return {"text": "{}", "finish_reason": "stop", "input_tokens": 100, "output_tokens": 50,
                "cost_usd": step, "cost_details": None, "model_returned": model_id, "provider": "P",
                "generation_id": "gen-1"}


SCOPE = {"scope": "dev_pilot", "allowed_splits": ["dev"], "allowed_experiments": ["PILOT_dev"],
         "allowed_models": ["known/model"], "require_pinned_no_fallback": True}


@pytest.fixture()
def paid_env(tmp_path, monkeypatch):
    b = tmp_path / "budget.json"
    b.write_text(json.dumps(SCOPE | {"approved_usd": 1.0}))
    monkeypatch.setattr(llm, "BUDGET_FILE", b)
    monkeypatch.setenv("TRIAGE_ALLOW_PAID", "1")
    return tmp_path


def _client(tmp, backend, ceiling=None):
    if ceiling is not None:
        (tmp / "budget.json").write_text(json.dumps(SCOPE | {"approved_usd": ceiling}))
    return LLMClient(backend, log_dir=tmp / "calls", providers=PROVIDERS, sleep=lambda s: None)


MSG = [{"role": "user", "content": "x" * 250}]


def test_unknown_price_is_a_hard_error(paid_env):
    be = FakePaid([0.01])
    with pytest.raises(UnknownPrice):
        _client(paid_env, be).complete(role="r", model_id="unknown/model", messages=MSG)
    assert be.calls == 0


def test_provider_cost_preserved_and_computed_fallback(paid_env):
    c = _client(paid_env, FakePaid([0.0123, None]))
    c.complete(role="r", model_id="known/model", messages=MSG, sample_index=0)
    c.complete(role="r", model_id="known/model", messages=MSG, sample_index=1)
    recs = list(read_jsonl(paid_env / "calls" / "known__model.jsonl"))
    assert recs[0]["cost_usd"] == 0.0123 and recs[0]["cost_source"] == "provider" and recs[0]["generation_id"]
    assert recs[1]["cost_source"] == "computed" and recs[1]["cost_usd"] == pytest.approx(100e-6 * 1 + 50e-6 * 2)
    assert recs[0]["routing"] == {"only": ["p"], "allow_fallbacks": False}


def test_ceiling_blocks_before_sending(paid_env):
    be = FakePaid([0.01])
    with pytest.raises(BudgetExceeded):
        _client(paid_env, be, ceiling=1e-6).complete(role="r", model_id="known/model", messages=MSG)
    assert be.calls == 0


def test_timeout_is_counted_as_possibly_charged(paid_env):
    be = FakePaid([AttemptError("timeout", possibly_charged=True, retryable=True), 0.002])
    c = _client(paid_env, be)
    c.complete(role="r", model_id="known/model", messages=MSG)
    led = llm.ledger(paid_env / "calls")
    reserve = llm.max_call_cost("known/model", MSG, config.MAX_OUTPUT_TOKENS, PROVIDERS)
    assert be.calls == 2 and led["possibly_charged_failures"] == 1
    assert led["at_risk_usd"] == pytest.approx(reserve) and led["completed_usd"] == pytest.approx(0.002)
    assert c.committed == pytest.approx(reserve + 0.002)


def test_rejected_request_is_not_counted(paid_env):
    be = FakePaid([AttemptError("HTTP 401", possibly_charged=False, retryable=False, status=401)])
    with pytest.raises(AttemptError):
        _client(paid_env, be).complete(role="r", model_id="known/model", messages=MSG)
    assert llm.ledger(paid_env / "calls")["at_risk_usd"] == 0


def test_orphaned_attempt_is_counted_on_restart(paid_env):
    j = paid_env / "calls" / "_journal.jsonl"
    j.parent.mkdir(parents=True)
    j.write_text(json.dumps({"event": "attempt", "attempt_id": "a1", "key": "k", "model": "known/model",
                             "attempt": 0, "reserve_usd": 0.4, "utc": "t"}) + "\n")
    c = _client(paid_env, FakePaid([]))
    assert c.committed == pytest.approx(0.4)
    assert llm.ledger(paid_env / "calls")["orphan_attempts"] == 1


def test_completed_call_is_served_from_log_on_resume(paid_env):
    be1 = FakePaid([0.01])
    _client(paid_env, be1).complete(role="r", model_id="known/model", messages=MSG)
    be2 = FakePaid([])
    r = _client(paid_env, be2).complete(role="r", model_id="known/model", messages=MSG)
    assert r.cached and be2.calls == 0


def test_replay_serves_logged_calls_and_never_sends(paid_env, monkeypatch):
    _client(paid_env, FakePaid([0.01])).complete(role="r", model_id="known/model", messages=MSG)
    monkeypatch.delenv("TRIAGE_ALLOW_PAID")                     # replay needs no paid-call approval
    rp = LLMClient(llm.ReplayBackend(), log_dir=paid_env / "calls", providers=PROVIDERS)
    assert rp.complete(role="r", model_id="known/model", messages=MSG).cached
    with pytest.raises(llm.NotInLog):
        rp.complete(role="r", model_id="known/model", messages=MSG, sample_index=9)
    assert llm.ledger(paid_env / "calls")["attempts"] == 1       # replay journalled no attempt


def test_reservation_uses_highest_endpoint_rate():
    cost = llm.max_call_cost("known/model", MSG, 512, PROVIDERS)
    assert cost == pytest.approx((100 + 16) / 1e6 * 3.0 + 512 / 1e6 * 4.0)
