"""D-68: a hit in D-41's truncation band is fatal only above 4.5 chars per reported token; below that it is accepted
and logged as "band hit, density normal". The six records are the Tier 1 session-1 DEB adjudicator calls, reduced to
their metadata (prompt chars, reported prompt tokens, num_ctx, max_tokens); no prompt or verdict text is used."""
import json

import pytest

from triage import ollama
from triage.io_utils import read_jsonl
from triage.ollama import ContextOverflow, truncation_check, truncation_suspected

from test_ollama_local import STATE, TAG, local, server  # noqa: F401  (fixtures)

SESSION1_SIX = [(16681, 4125), (17333, 4098), (16515, 4100), (16556, 4117), (17392, 4109), (17381, 4160)]


@pytest.mark.parametrize("chars,reported", SESSION1_SIX)
def test_session1_band_hits_are_accepted(chars, reported):
    assert 4.0 < chars / reported < 4.3
    assert truncation_check(chars, reported, 8192, 512) == "band_hit_density_normal"
    assert not truncation_suspected(chars, reported, 8192, 512)


def test_true_overflow_is_still_fatal():
    # 7,700 real tokens at 2.56 chars/token (a qwen package density; NOT the lowest measured, see D-68) -> 19,712 chars
    assert truncation_check(19712, 4098, 8192, 512) == "fatal"
    assert truncation_suspected(19712, 4098, 8192, 512)
    # the 4.5 bound, on a model whose lowest measured density keeps the per-model bound out of the way (amendment)
    assert truncation_check(int(4.5 * 4098) + 1, 4098, 8192, 512, "gemma4:26b") == "fatal"            # just above 4.5
    assert truncation_check(int(4.5 * 4098), 4098, 8192, 512, "gemma4:26b") == "band_hit_density_normal"  # 4.5 is not


def test_other_d35_d41_checks_unchanged():
    assert truncation_check(10000, 7700, 8192, 512) == "fatal"      # near-limit: no room left to answer
    assert truncation_check(100, 0, 8192, 512) == "fatal"           # zero reported tokens for a non-empty prompt
    assert truncation_check(0, 0, 8192, 512) == "ok"
    assert truncation_check(16000, 4000, 8192, 512) == "ok"         # outside the band: density is not judged
    assert truncation_check(21000, 4200, 8192, 512) == "ok"
    for chars, rep in [(18000, 4098), (16000, 4100)]:              # were fatal under D-41's 3.3 bound
        assert truncation_check(chars, rep, 8192, 512, "qwen3.5:9b") == "band_hit_density_normal"
    assert ollama.MAX_CHARS_PER_TOKEN == 6.0 and ollama.TRUNCATION_BAND == (-8, 64)


def test_band_hit_is_accepted_and_logged_live_and_from_the_log(local):  # noqa: F811
    make, tmp = local
    STATE.prompt_eval = 4109
    msg = [{"role": "user", "content": "z" * 17392}]
    r = make().complete(role="adjudicator", model_id=TAG, messages=msg)
    assert not r.cached
    rec = list(read_jsonl(tmp / "calls" / "fakejudge_9b.jsonl"))[-1]
    assert rec["local"]["truncation_check"] == "band_hit_density_normal" and not rec["local"]["possibly_truncated"]
    n = len(STATE.requests)
    r2 = make().complete(role="adjudicator", model_id=TAG, messages=msg)      # resume: served from the log
    assert r2.cached and len(STATE.requests) == n
    events = [json.loads(l) for l in (tmp / "calls" / "_journal.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(e.get("event") == "band_hit_density_normal" for e in events)


def test_logged_session1_style_flag_is_cleared_on_resume(local):  # noqa: F811
    """A call flagged under D-41 (possibly_truncated true, ContextOverflow raised) is re-judged on resume."""
    make, tmp = local
    STATE.prompt_eval = 4098
    msg = [{"role": "user", "content": "q" * 17333}]
    make().complete(role="adjudicator", model_id=TAG, messages=msg)
    f = tmp / "calls" / "fakejudge_9b.jsonl"
    rows = list(read_jsonl(f))
    rows[-1]["local"]["possibly_truncated"] = True          # as written under the D-41 rule
    rows[-1]["local"].pop("truncation_check", None)
    f.write_text("".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")
    n = len(STATE.requests)
    r = make().complete(role="adjudicator", model_id=TAG, messages=msg)
    assert r.cached and len(STATE.requests) == n


def test_true_overflow_is_fatal_through_the_client(local):  # noqa: F811
    make, _ = local
    STATE.prompt_eval = 4098
    with pytest.raises(ContextOverflow):
        make().complete(role="judge", model_id=TAG, messages=[{"role": "user", "content": "y" * 19712}])
