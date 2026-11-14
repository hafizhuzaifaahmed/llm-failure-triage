"""D-86: the dev-gate script applies the D-70 leakage-abort exclusions, and E6b selection halts on a harness error
instead of moving to the next candidate. Uses the committed frozen gate runs; no server, no model."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "local"))

import e6b  # noqa: E402


@pytest.mark.parametrize("run,extra", [("GATE_M1b", ["--required", "a,b,c,d"]),
                                       ("CHECK_M2", ["--required", "a,b", "--baselines-from", "results/dev/GATE_M1b"])])
def test_gates_on_a_run_with_leakage_aborts_reproduce_the_committed_verdicts(tmp_path, run, extra):
    src = ROOT / "results" / "dev" / run
    assert (src / "leakage_rejections.jsonl").read_text(encoding="utf-8").strip()     # the case that used to crash
    for f in ("decisions.jsonl", "leakage_rejections.jsonl"):
        shutil.copy2(src / f, tmp_path / f)
    r = subprocess.run([sys.executable, "scripts/local/dev_gates.py", "--run", str(tmp_path), *extra], cwd=ROOT,
                       stdin=subprocess.DEVNULL, capture_output=True, text=True, env={**__import__("os").environ, "PYTHONPATH": "src"})
    assert r.returncode == 0, r.stderr[-800:]
    new = json.loads((tmp_path / "dev_gates.json").read_text(encoding="utf-8"))
    old = json.loads((src / "dev_gates.json").read_text(encoding="utf-8"))
    for g in "abcd":
        assert new[f"G_{g}"] == old[f"G_{g}"]
    assert new["G_a_valid_rate"] == old["G_a_valid_rate"] and new["G_b_citations"] == old["G_b_citations"]
    assert new["leakage_aborts"]


def _selection(tmp_path, monkeypatch, tried, results):
    sel = tmp_path / "selection.json"
    if tried:
        sel.write_text(json.dumps({"order": [], "tried": tried}), encoding="utf-8")
    monkeypatch.setattr(e6b, "SELECTION", sel)
    calls = []

    def fake(tag, prior=None):
        calls.append((tag, prior))
        return results[tag]
    monkeypatch.setattr(e6b, "try_candidate", fake)
    return sel, calls


def test_select_halts_on_a_harness_error_and_does_not_try_the_next_candidate(tmp_path, monkeypatch):
    order = e6b.load()["candidate_order"]
    res = {order[0]: {"tag": order[0], "step1_passes": True, "harness_error": True, "selected": False}}
    sel, calls = _selection(tmp_path, monkeypatch, [], res)
    with pytest.raises(SystemExit):
        e6b.cmd_select(None)
    assert [c[0] for c in calls] == [order[0]]
    assert "selected" not in json.loads(sel.read_text(encoding="utf-8"))


def test_select_resumes_a_harness_error_candidate_with_its_prior_record(tmp_path, monkeypatch):
    order = e6b.load()["candidate_order"]
    prior = {"tag": order[0], "step1_passes": True, "harness_error": True, "spec": {"digest": "d"}}
    res = {order[0]: {"tag": order[0], "step1_passes": True, "selected": True}}
    sel, calls = _selection(tmp_path, monkeypatch, [prior], res)
    e6b.cmd_select(None)
    assert calls == [(order[0], prior)]
    assert json.loads(sel.read_text(encoding="utf-8"))["selected"] == order[0]
