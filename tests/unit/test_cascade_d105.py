"""D-105: the cascade rule and the error-diversity analysis, exercised on synthetic logs only (no real output read)."""
import importlib.util
import json
import random
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


cas = load("cascade_mod", "scripts/analysis/cascade.py")
div = load("diversity_mod", "scripts/analysis/error_diversity.py")
TF, PF = cas.TF, cas.PF


def test_tier1_unanimity_decides_and_disagreement_escalates():
    assert cas.tier1([TF, TF, TF]) == TF and cas.tier1([PF, PF, PF]) == PF
    assert cas.tier1([TF, TF, PF]) is None and cas.tier1([TF, TF, "INVALID"]) is None and cas.tier1([TF, TF]) is None


def test_escalation_uses_sonnet_and_keeps_when_it_is_missing_or_invalid():
    assert cas.cascade([TF, PF, TF], TF) == TF and cas.cascade([TF, PF, TF], PF) == PF
    assert cas.cascade([TF, PF, TF], None) == PF and cas.cascade([TF, PF, TF], "INVALID") == PF
    assert cas.cascade([TF, TF, TF], PF) == TF                     # tier 1 is never overridden


def test_kuu_is_unchanged():
    assert cas.kuu([TF, TF, TF]) == TF and cas.kuu([TF, TF, PF]) == PF and cas.kuu([TF, TF, None]) == PF


def _write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


@pytest.fixture
def world(tmp_path, monkeypatch):
    rnd = random.Random(1)
    ids = [f"i{k}" for k in range(60)]
    lab = {i: ("PF" if k % 3 == 0 else "TF") for k, i in enumerate(ids)}
    proc, gt, runs, front = tmp_path / "proc", tmp_path / "gt", tmp_path / "runs", tmp_path / "front"
    for ds in ("D1", "D2"):
        (proc).mkdir(exist_ok=True)
        (proc / f"sample_{ds}_test.json").write_text(json.dumps({"instance_ids": ids, "tf_weights": None}))
        _write(gt / f"labels_{ds}.jsonl", [{"instance_id": i, "label": lab[i], "bug_name": f"b{k // 3}",
                                             "project": "P"} for k, i in enumerate(ids)])

    def vote(i, acc):
        right = PF if lab[i] == "PF" else TF
        return right if rnd.random() < acc else (TF if right == PF else PF)

    def dec(arm, rep, i, label, **kw):
        return {"instance_id": i, "arm": arm, "level": "S1", "variant": "full", "replicate": rep, "label_raw": label, **kw}

    for plan in (cas.PLAN["d1"], cas.PLAN["d2"]):
        for m, run in plan["members"].items():
            _write(runs / run / "decisions.jsonl", [dec("J1", plan["vote_rep"], i, vote(i, 0.7)) for i in ids])
        rows = [dec("DEB", 0, i, vote(i, 0.7), agreement={}) for i in ids] + [dec("KA", 0, i, PF) for i in ids]
        _write(runs / plan["m1_run"] / "decisions.jsonl", rows)
        reps = 3 if plan["dataset"] == "D1" else 1
        _write(front / plan["frontier_run"] / "decisions.jsonl",
               [dec("DEB", r, i, vote(i, 0.85), agreement={}, cost={"cost_usd": 0.02, "calls": 5}) for r in range(reps) for i in ids]
               + [dec("J1", 0, i, vote(i, 0.8), cost={"cost_usd": 0.004, "calls": 1}) for i in ids])
    for plan in div.PLAN.values():
        for m, run in plan["sc"].items():
            p = runs / run / "decisions.jsonl"
            old = p.read_text(encoding="utf-8") if p.exists() else ""
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(old + "".join(json.dumps(dec("SC", 0, i, PF, votes=[vote(i, 0.7) for _ in range(5)])) + "\n"
                                       for i in ids), encoding="utf-8")
    for mod in (cas, div):
        monkeypatch.setattr(mod, "RUNS", runs)
        monkeypatch.setattr(mod.config, "PROCESSED", proc)
        monkeypatch.setattr(mod.config, "GT_STORE", gt)
    monkeypatch.setattr(cas, "FRONT", front)
    monkeypatch.setattr(cas, "OUT", tmp_path / "out")
    monkeypatch.setattr(div, "OUT", tmp_path / "out" / "div.json")
    return tmp_path


@pytest.mark.parametrize("which", ["d1", "d2"])
def test_cascade_runs_end_to_end_on_synthetic_logs(world, monkeypatch, which):
    monkeypatch.setattr("sys.argv", ["cascade.py", which])
    cas.main()
    out = json.loads((world / "out" / cas.PLAN[which]["out"]).read_text())
    assert set(out["hypotheses"]) == {"H12-1", "H12-2"}
    assert 0 <= out["escalation"]["share_escalated"] <= 1
    assert out["sonnet_deb_replicates"] == (3 if which == "d1" else 1)
    if which == "d1":
        assert all(h["supported"] is None for h in out["hypotheses"].values())


def test_error_diversity_runs_end_to_end_on_synthetic_logs(world):
    div.main()
    out = json.loads((world / "out" / "div.json").read_text())
    assert set(out["D1"]["within_family"]) == {"M1", "M2", "E6B"} and set(out["D2"]["within_family"]) == {"M1", "M2"}
    assert out["D2"]["kuu_loss"]["observed"] >= 0 and "difference_ci95" in out["D2"]["comparison"]
