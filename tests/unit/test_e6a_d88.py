"""D-88: E6a completes the 35b in two server starts, each below the 871 calls after which it slowed (D-78).
Fakes only: no server is started and no model is loaded."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "local"))

import run_expl_35b as r  # noqa: E402
from triage import expl_profile  # noqa: E402
from triage.io_utils import read_jsonl  # noqa: E402

RUN = ROOT / "results" / "runs_local" / "EXPL_35B_D1TEST"
CALLS_PER_DECISION = 5                          # SC k = 5; DEB 5 calls (2 rounds x 2 advocates + judge)


def remaining():
    samp = json.loads((ROOT / "data" / "processed" / "sample_D1_test.json").read_text(encoding="utf-8"))
    done = {}
    for d in read_jsonl(RUN / "decisions.jsonl"):
        done.setdefault(d["arm"], set()).add(d["instance_id"])
    n = len(samp["instance_ids"])
    return {a: n - len(done.get(a, ())) for a in ("DEB", "SC")}


def test_each_server_start_stays_below_the_d78_slowdown():
    left = remaining()                           # includes the leakage-aborted instances (they cost no call)
    s1 = left["DEB"] + dict(r.E6A_PLAN[1])["SC"]
    s2 = left["SC"] - dict(r.E6A_PLAN[1])["SC"]
    assert r.E6A_CALL_CAP < 871
    assert s1 * CALLS_PER_DECISION <= r.E6A_CALL_CAP and s2 * CALLS_PER_DECISION <= r.E6A_CALL_CAP
    assert [a for a, _ in r.E6A_PLAN[1]] == ["DEB", "SC"] and [a for a, _ in r.E6A_PLAN[2]] == ["SC"]


@pytest.mark.parametrize("recorded,session", [({}, 2), ({"1": {}}, 1), ({"1": {}, "2": {}}, 2)])
def test_sessions_run_in_order_and_once(monkeypatch, recorded, session):
    monkeypatch.setattr(r, "outcome", lambda: {"feasibility_ok": True, "e6a": recorded})
    monkeypatch.setattr(expl_profile, "past_deadline", lambda p, now=None: False)
    started = []
    monkeypatch.setattr(r.ollama_server, "start_profile", lambda *a, **k: started.append(1))
    with pytest.raises(SystemExit):
        r.cmd_e6a(expl_profile.load(), session)
    assert not started


def test_e6a_refuses_past_the_deadline(monkeypatch):
    monkeypatch.setattr(r, "outcome", lambda: {"feasibility_ok": True})
    monkeypatch.setattr(expl_profile, "past_deadline", lambda p, now=None: True)
    monkeypatch.setattr(r.ollama_server, "start_profile", lambda *a, **k: pytest.fail("server started"))
    with pytest.raises(SystemExit):
        r.cmd_e6a(expl_profile.load(), 1)
