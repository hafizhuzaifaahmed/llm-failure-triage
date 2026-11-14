"""Scope lock: the dev pilot cannot touch held-out data, unapproved experiments/models, or fallback providers."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import run_experiment  # noqa: E402
from test_guard_and_budget import MSG, PROVIDERS, SCOPE, FakePaid, _instance, _setup  # noqa: E402
from triage import llm, scope  # noqa: E402
from triage.io_utils import write_jsonl  # noqa: E402
from triage.llm import LLMClient  # noqa: E402

PILOT = json.loads((ROOT / "configs" / "budget.pilot.PROPOSED.json").read_text())


@pytest.fixture()
def paid(tmp_path, monkeypatch):
    b = tmp_path / "budget.json"
    b.write_text(json.dumps(SCOPE | {"approved_usd": 1.0}))
    monkeypatch.setattr(llm, "BUDGET_FILE", b)
    monkeypatch.setenv("TRIAGE_ALLOW_PAID", "1")
    return tmp_path


def client(tmp, backend, providers=PROVIDERS):
    return LLMClient(backend, log_dir=tmp / "calls", providers=providers, sleep=lambda s: None)


def test_proposed_pilot_budget_is_dev_only_and_16_dollars():
    assert PILOT["approved_usd"] == 16 and PILOT["allowed_splits"] == ["dev"]
    assert PILOT["allowed_experiments"] == ["PILOT_dev"] and PILOT["require_pinned_no_fallback"] is True
    assert set(PILOT["allowed_models"]) == {"deepseek/deepseek-chat-v3-0324", "openai/gpt-4.1"}   # no M2
    providers = json.loads((ROOT / "configs" / "providers.json").read_text())
    for m in PILOT["allowed_models"]:
        r = providers["models"][m]["routing"]
        assert r["allow_fallbacks"] is False and len(r["only"]) == 1


def test_scope_requires_all_fields(tmp_path):
    p = tmp_path / "b.json"
    p.write_text(json.dumps({"approved_usd": 16}))
    with pytest.raises(scope.ScopeViolation):
        scope.load(p)


def test_held_out_items_are_refused():
    s = scope.Scope(16, "dev_pilot", ["dev"], ["PILOT_dev"], ["known/model"])
    with pytest.raises(scope.ScopeViolation):
        s.check_items([{"focal_id": "Lang_1::x", "split": "test"}], "focal method")
    with pytest.raises(scope.ScopeViolation):
        s.check_split(None)
    assert s.check_items([{"focal_id": "Cli_1::x", "split": "dev"}], "focal method") == 1


def test_unapproved_model_is_refused_before_sending(paid):
    be = FakePaid([0.01])
    other = {"models": {**PROVIDERS["models"], "other/model": PROVIDERS["models"]["known/model"]}}
    with pytest.raises(scope.ScopeViolation):
        client(paid, be, other).complete(role="r", model_id="other/model", messages=MSG)
    assert be.calls == 0


def test_fallback_routing_is_refused(paid):
    loose = {"models": {"known/model": {**PROVIDERS["models"]["known/model"],
                                        "routing": {"only": ["p"], "allow_fallbacks": True}}}}
    be = FakePaid([0.01])
    with pytest.raises(scope.ScopeViolation):
        client(paid, be, loose).complete(role="r", model_id="known/model", messages=MSG)
    assert be.calls == 0


def test_provider_mismatch_stops_and_is_counted(paid):
    class OtherHost(FakePaid):
        def call(self, *a, **k):
            out = super().call(*a, **k)
            return {**out, "provider": "SomeOtherHost"}
    c = client(paid, OtherHost([0.003]))
    with pytest.raises(llm.ProviderMismatch):
        c.complete(role="r", model_id="known/model", messages=MSG)
    assert llm.ledger(paid / "calls")["completed_usd"] == pytest.approx(0.003)   # logged and counted


def test_paid_run_refuses_unapproved_experiment_and_test_split(paid):
    exp = _setup(paid)                              # name "t", split "dev"
    c = client(paid, FakePaid([]))
    with pytest.raises(scope.ScopeViolation):
        run_experiment.execute(exp, c, paid / "run", workers=1)
    exp["name"] = "PILOT_dev"
    test_inst = _instance("heldout") | {"split": "test"}
    write_jsonl(paid / "instances.jsonl", [test_inst])
    (paid / "sample.json").write_text(json.dumps({"instance_ids": ["heldout"]}))
    with pytest.raises(SystemExit):                 # split mismatch with the experiment
        run_experiment.execute(exp, c, paid / "run", workers=1)
    exp["split"] = "test"
    with pytest.raises(scope.ScopeViolation):       # held-out split outside the approved scope
        run_experiment.execute(exp, c, paid / "run", workers=1)
