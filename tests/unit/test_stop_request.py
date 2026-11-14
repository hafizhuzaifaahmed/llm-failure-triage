"""D-58: a stop file makes the client refuse to START a new model call; cached calls still replay, so the same command
resumes after the stop file is removed without repeating a call."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from triage import llm  # noqa: E402
from triage.llm import LLMClient, MockBackend, StopRequested  # noqa: E402

MSG = [{"role": "user", "content": "hello"}]


class Counter:
    def __init__(self):
        self.n = 0

    def __call__(self, model_id, messages):
        self.n += 1
        return '{"label": "TEST_FAULT"}'


def test_stop_file_blocks_new_calls_but_not_cached_ones(tmp_path, monkeypatch):
    stop = tmp_path / "STOP"
    monkeypatch.setattr(llm, "STOP_FILE", stop)
    rec = Counter()
    client = LLMClient(MockBackend(rec), log_dir=tmp_path / "calls")
    client.complete(role="judge", model_id="m", messages=MSG)            # made before the stop
    stop.write_text("")
    with pytest.raises(StopRequested):
        client.complete(role="judge", model_id="m", messages=MSG, sample_index=1)
    assert rec.n == 1
    again = client.complete(role="judge", model_id="m", messages=MSG)    # cached: still served during a stop
    assert again.cached and rec.n == 1
    stop.unlink()                                                        # resume
    client2 = LLMClient(MockBackend(rec), log_dir=tmp_path / "calls")
    client2.complete(role="judge", model_id="m", messages=MSG)
    client2.complete(role="judge", model_id="m", messages=MSG, sample_index=1)
    assert rec.n == 2                                                     # only the call that was never made
