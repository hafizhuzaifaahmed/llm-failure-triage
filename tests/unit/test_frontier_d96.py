"""D-96 (E9): the Message Batches frontier client against a fake API. No network, no key, nothing billed."""
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "frontier"))

from triage import frontier  # noqa: E402
from triage.io_utils import read_jsonl  # noqa: E402
from triage.llm import DeferredCall, StopRequested  # noqa: E402
from triage.runner import Runner  # noqa: E402
from triage.schema import parse_output  # noqa: E402

GOOD = '{"label": "PROGRAM_FAULT", "reason_category": "OTHER", "evidence_ids": [], "summary": "s", "confidence": 70}'


class Usage:
    def __init__(self, i, o):
        self.d = {"input_tokens": i, "output_tokens": o}

    def model_dump(self):
        return dict(self.d)


class FakeBatches:
    def __init__(self, responder):
        self.created, self.responder = [], responder

    def create(self, requests):
        self.created.append(list(requests))
        return NS(id=f"b{len(self.created)}", processing_status="in_progress")

    def retrieve(self, bid):
        return NS(id=bid, processing_status="ended")

    def results(self, bid):
        return [self.responder(r) for r in self.created[int(bid[1:]) - 1]]


def api(responder):
    return NS(messages=NS(batches=FakeBatches(responder)))


def ok(text=GOOD, stop="end_turn"):
    def r(req):
        msg = NS(content=[NS(type="text", text=text)], usage=Usage(1000, 50), stop_reason=stop,
                 model=frontier.MODEL, id="msg_1", stop_details=None)
        return NS(custom_id=req["custom_id"], result=NS(type="succeeded", message=msg))
    return r


def failing(kind="expired"):
    return lambda req: NS(custom_id=req["custom_id"], result=NS(type=kind, error=None))


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(frontier, "STOP_FILE", tmp_path / "STOP")
    return frontier.FrontierClient(log_dir=tmp_path / "log")


def ask(c, text="hello", role="judge"):
    return c.complete(role=role, model_id=frontier.MODEL, messages=[{"role": "user", "content": text}], max_tokens=512)


def test_params_follow_the_sonnet55_settings_and_send_no_sampling_fields():
    p = frontier.build_params({"role": "judge", "json_mode": True, "max_tokens": 512,
                               "messages": [{"role": "user", "content": "x"}]})
    assert p["model"] == "claude-sonnet-5-5" and p["max_tokens"] == 512
    assert p["thinking"] == {"type": "between_tools"} and p["output_config"]["effort"] == "high"
    assert not {"temperature", "top_p", "top_k", "fallbacks", "tools", "tool_choice"} & set(p)
    s = p["output_config"]["format"]["schema"]
    assert p["output_config"]["format"]["type"] == "json_schema" and s["additionalProperties"] is False
    assert "minimum" not in s["properties"]["confidence"] and set(s["required"]) >= {"label", "confidence"}
    a = frontier.build_params({"role": "advocate_p_r1", "json_mode": True, "max_tokens": 512,
                               "messages": [{"role": "user", "content": "x"}]})
    assert "position" in a["output_config"]["format"]["schema"]["properties"]


def test_collect_then_replay(client, tmp_path):
    with pytest.raises(DeferredCall):
        ask(client)
    assert len(client.pending) == 1
    res = frontier.submit_pending(client, api(ok()), tmp_path / "state.jsonl", sleep=lambda s: None)
    assert res["succeeded"] == 1 and not client.pending
    r = ask(client)
    assert r.cached and r.text == GOOD
    fresh = frontier.FrontierClient(log_dir=tmp_path / "log")      # a new pass reads the log
    assert ask(fresh).text == GOOD
    rec = next(read_jsonl(client.log_path))
    assert rec["cost_usd"] == pytest.approx((1000 * 1.0 + 50 * 5.0) / 1e6) and rec["label"] == frontier.LABEL


def test_cap_refuses_before_any_batch_is_created(client, tmp_path):
    with pytest.raises(DeferredCall):
        ask(client, "x" * 30000)
    fake = api(ok())
    with pytest.raises(frontier.CapExceeded):
        frontier.submit_pending(client, fake, tmp_path / "s.jsonl", cap=0.001, sleep=lambda s: None)
    assert fake.messages.batches.created == []


def test_spend_counts_toward_the_next_preflight(client, tmp_path):
    with pytest.raises(DeferredCall):
        ask(client, "a")
    frontier.submit_pending(client, api(ok()), tmp_path / "s.jsonl", sleep=lambda s: None)
    with pytest.raises(DeferredCall):
        ask(client, "b")
    pf = frontier.preflight(client, list(client.pending.values()), cap=frontier.CAP_USD)
    assert pf["spent_usd"] == pytest.approx(0.00125) and pf["allowed"]
    assert frontier.preflight(client, list(client.pending.values()), cap=0.00125)["allowed"] is False


def test_refusal_is_logged_and_scores_invalid(client, tmp_path):
    with pytest.raises(DeferredCall):
        ask(client)
    res = frontier.submit_pending(client, api(ok(text="", stop="refusal")), tmp_path / "s.jsonl", sleep=lambda s: None)
    assert res["refusal"] == 1
    r = ask(client)
    assert r.finish_reason == "refusal" and not parse_output(r.text, "judge").ok


def test_malformed_reply_scores_invalid(client, tmp_path):
    with pytest.raises(DeferredCall):
        ask(client)
    frontier.submit_pending(client, api(ok(text="not json")), tmp_path / "s.jsonl", sleep=lambda s: None)
    assert not parse_output(ask(client).text, "judge").ok


def test_expired_is_resubmitted_once_then_invalid(client, tmp_path):
    st = tmp_path / "s.jsonl"
    with pytest.raises(DeferredCall):
        ask(client)
    r1 = frontier.submit_pending(client, api(failing("expired")), st, sleep=lambda s: None)
    assert r1["expired"] == 1 and r1["invalid_after_failures"] == 0
    with pytest.raises(DeferredCall):                                # not in the log: queued again
        ask(client)
    r2 = frontier.submit_pending(client, api(failing("expired")), st, sleep=lambda s: None)
    assert r2["invalid_after_failures"] == 1
    r = ask(client)
    assert r.finish_reason == "error:expired" and r.text == ""


def test_partial_results_leave_the_rest_pending_for_the_next_pass(client, tmp_path):
    for t in ("a", "b"):
        with pytest.raises(DeferredCall):
            ask(client, t)
    half = lambda req: (ok()(req) if req["params"]["messages"][0]["content"] == "a" else failing("errored")(req))
    res = frontier.submit_pending(client, api(half), tmp_path / "s.jsonl", sleep=lambda s: None)
    assert res["succeeded"] == 1 and res["errored"] == 1
    assert ask(client, "a").text == GOOD
    with pytest.raises(DeferredCall):
        ask(client, "b")


def test_stop_file_blocks_queueing(client, tmp_path):
    (tmp_path / "STOP").write_text("stop", encoding="utf-8")
    with pytest.raises(StopRequested):
        ask(client)


def test_runner_skips_deferred_tasks_without_logging_an_error(tmp_path, monkeypatch):
    r = Runner(tmp_path, None, None, "m", require_guard=False, workers=1)

    def one(inst, arm, level, variant, rep, k):
        raise DeferredCall("k")
    monkeypatch.setattr(r, "one", one)
    r.run([{"instance_id": "a"}, {"instance_id": "b"}], [{"arm": "J1", "levels": ["S1"]}], 1)
    assert r.deferred == 2 and not (tmp_path / "errors.jsonl").exists() and not (tmp_path / "decisions.jsonl").exists()


def test_run_refuses_without_the_key_or_the_authors_go_file(monkeypatch, tmp_path):
    """Never reaches the API: the real env/.env and go-file are replaced by missing paths (D-97)."""
    import anthropic
    import e9
    monkeypatch.setattr(e9, "ENV_FILE", tmp_path / "no.env")
    monkeypatch.setattr(e9, "GO", tmp_path / "missing")
    monkeypatch.setattr(anthropic, "Anthropic", lambda *a, **k: pytest.fail("test constructed an API client"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        e9.cmd_run(None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "placeholder-for-the-test")
    with pytest.raises(SystemExit):
        e9.cmd_run(None)


def test_key_is_loaded_only_from_the_ignored_env_file():
    import subprocess
    import e9
    assert e9.ENV_FILE == ROOT / "env" / ".env"
    r = subprocess.run(["git", "check-ignore", "-q", str(e9.ENV_FILE)], cwd=ROOT)
    assert r.returncode == 0                                       # git-ignored
    assert frontier.CAP_USD == 14.0


def test_d99_a_queue_that_does_not_fit_is_sent_as_the_largest_fitting_chunk(client, tmp_path):
    for t in ("a", "b", "c"):
        with pytest.raises(DeferredCall):
            ask(client, t * 900)
    one = frontier.worst_case_usd(next(iter(client.pending.values())))
    fake = api(ok())
    res = frontier.submit_pending(client, fake, tmp_path / "s.jsonl", cap=one * 2.5, sleep=lambda s: None)
    assert len(fake.messages.batches.created[0]) == 2 and res["succeeded"] == 2 and len(client.pending) == 1
    pf = [r for r in read_jsonl(tmp_path / "s.jsonl") if r["event"] == "preflight"][0]
    assert pf["chunked"] and pf["queued"] == 3


def test_d99_an_unfinished_batch_is_collected_before_anything_new_is_sent(client, tmp_path):
    st = tmp_path / "s.jsonl"
    with pytest.raises(DeferredCall):
        ask(client, "x")
    fake = api(ok())
    from anthropic.types.messages.batch_create_params import Request
    key = next(iter(client.pending))
    fake.messages.batches.created.append([Request(custom_id=key, params={"messages": [{"role": "user", "content": "x"}]})])
    from triage.io_utils import append_jsonl
    append_jsonl(st, {"event": "created", "batch_id": "b1", "requests": 1, "keys": [key]})    # the process died here
    assert frontier.unfinished_batches(st)
    out = frontier.resume(client, fake, st, sleep=lambda s: None)
    assert out[0]["succeeded"] == 1 and not frontier.unfinished_batches(st) and len(fake.messages.batches.created) == 1
    assert ask(client, "x").text == GOOD
