"""D-90: E8 uses fresh J1-prompt calls at replicate indices no committed run used; the votes are formed offline with
the committed SC aggregation rule. Fakes only: no server, no model."""
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

from triage import arms, expl_profile, scope  # noqa: E402
from triage.io_utils import read_jsonl  # noqa: E402
from triage.runner import Runner  # noqa: E402

EXP = ROOT / "configs" / "experiments"
NAMES = ("LOCAL_HO_E8_VOTE_M1", "LOCAL_HO_E8_VOTE_M2", "LOCAL_HO_E8_VOTE_E6B")


def test_runner_uses_the_named_replicate_indices(tmp_path, monkeypatch):
    seen = []
    r = Runner(tmp_path, None, None, "m", require_guard=False, workers=1)
    monkeypatch.setattr(r, "one", lambda inst, arm, level, variant, rep, k: seen.append(rep) or
                        {"instance_id": inst["instance_id"], "arm": arm, "level": level, "variant": variant,
                         "model": "m", "replicate": rep, "label_raw": "TEST_FAULT"})
    insts = [{"instance_id": "a"}, {"instance_id": "b"}]
    r.run(insts, [{"arm": "J1", "levels": ["S1"], "replicate_indices": [10, 11, 12]}], 3)
    assert sorted(seen) == [10, 10, 11, 11, 12, 12]
    seen.clear()
    r2 = Runner(tmp_path / "x", None, None, "m", require_guard=False, workers=1)
    monkeypatch.setattr(r2, "one", lambda inst, arm, level, variant, rep, k: seen.append(rep) or
                        {"instance_id": inst["instance_id"], "arm": arm, "level": level, "variant": variant,
                         "model": "m", "replicate": rep, "label_raw": "TEST_FAULT"})
    r2.run(insts, [{"arm": "J1", "levels": ["S1"]}], 3)
    assert sorted(seen) == [0, 0, 1, 1, 2, 2]                  # unchanged without the field


def test_e8_indices_are_used_by_no_committed_j1_run():
    used = set()
    for run in ("LOCAL_HO_E1E3_M1", "LOCAL_HO_E5R3_M2", "LOCAL_HO_E6B_D1TEST"):
        used |= {d["replicate"] for d in read_jsonl(ROOT / "results" / "runs_local" / run / "decisions.jsonl")
                 if d["arm"] == "J1"}
    for n in NAMES:
        e = json.loads((EXP / f"{n}.json").read_text(encoding="utf-8"))
        (c,) = e["conditions"]
        assert c["arm"] == "J1" and c["levels"] == ["S1"] and e["prompt_set"] == "local_m1b" and e["split"] == "test"
        assert not set(c["replicate_indices"]) & used and min(c["replicate_indices"]) >= 10
        # the J1 call key uses sample_index = replicate * 1000 (arms.j1_arm); SC uses replicate*1000 + j with j < 5
        assert all(i * 1000 > 2 * 1000 + 4 for i in c["replicate_indices"])


def test_vote_members_match_the_pre_registration():
    import e8_analysis as a
    assert sum(len(v) for v in a.VOTE3.values()) == 3 and all(len(v) == 1 for v in a.VOTE3.values())
    assert [len(a.VOTE5[m]) for m in ("M1", "M2", "E6B")] == [2, 2, 1]
    assert not set(a.VOTE3["M1"]) & set(a.VOTE5["M1"])          # VOTE3 and VOTE5 use separate calls
    for m, n in (("M1", "LOCAL_HO_E8_VOTE_M1"), ("M2", "LOCAL_HO_E8_VOTE_M2"), ("E6B", "LOCAL_HO_E8_VOTE_E6B")):
        idx = json.loads((EXP / f"{n}.json").read_text(encoding="utf-8"))["conditions"][0]["replicate_indices"]
        assert sorted(a.VOTE3[m] + a.VOTE5[m]) == idx


def test_scope_and_the_e6b_gate():
    sc = scope.load(scope.LOCAL_SCOPE_FILE)
    for n in NAMES:
        sc.check_experiment(n)
    p = json.loads(expl_profile.E6B_PROFILE_FILE.read_text(encoding="utf-8"))
    assert "LOCAL_HO_E8_VOTE_E6B" in p["experiments"] and "LOCAL_HO_E8_VOTE_E6B" in p["selection_gated"]["experiments"]
    assert expl_profile.for_experiment("LOCAL_HO_E8_VOTE_M1") is None       # M1/M2 batches run on the frozen server
    assert json.loads((EXP / "LOCAL_HO_E8_VOTE_E6B.json").read_text(encoding="utf-8"))["model_tag"] == "{profile}"


def test_majority_rule_is_the_committed_sc_rule():
    PF, TF, INV = "PROGRAM_FAULT", "TEST_FAULT", "INVALID"
    assert arms.aggregate_votes([PF, PF, TF], 3)["label_raw"] == PF
    assert arms.aggregate_votes([PF, INV, TF], 3)["label_raw"] == TF            # valid tie -> TF, as SC
    assert arms.aggregate_votes([PF, PF, TF, TF, PF], 5)["label_raw"] == PF


def test_analysis_runs_on_stand_in_vote_runs(tmp_path, monkeypatch):
    """Code path only: committed J1 decisions re-indexed as the vote replicates (no E8 output exists yet)."""
    import e8_analysis as a
    runs = tmp_path / "runs"
    src = ROOT / "results" / "runs_local"
    shutil.copytree(src / a.M1_RUN, runs / a.M1_RUN)
    plan = {"LOCAL_HO_E8_VOTE_M1": ("LOCAL_HO_E1E3_M1", {0: 10, 1: 11, 2: 12}),
            "LOCAL_HO_E8_VOTE_M2": ("LOCAL_HO_E5R3_M2", {0: 10}),
            "LOCAL_HO_E8_VOTE_E6B": ("LOCAL_HO_E6B_D1TEST", {0: 10})}
    for name, (frm, remap) in plan.items():
        (runs / name).mkdir(parents=True)
        rows = []
        for d in read_jsonl(src / frm / "decisions.jsonl"):
            if d["arm"] == "J1" and d["level"] == "S1" and d["replicate"] in remap:
                rows.append({**d, "replicate": remap[d["replicate"]]})
                if name != "LOCAL_HO_E8_VOTE_M1":              # second/third index for the stand-ins
                    rows.append({**d, "replicate": 11})
                    if name == "LOCAL_HO_E8_VOTE_M2":
                        rows.append({**d, "replicate": 12})
        (runs / name / "decisions.jsonl").write_text("".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")
        shutil.copy2(src / frm / "leakage_rejections.jsonl", runs / name / "leakage_rejections.jsonl")
    monkeypatch.setattr(a, "RUNS", runs)
    monkeypatch.setattr(a, "OUT", tmp_path / "e8.json")
    a.main()
    out = json.loads((tmp_path / "e8.json").read_text(encoding="utf-8"))
    assert set(out["hypotheses"]) == {"H8-1", "H8-2", "H8-3"} and out["n_instances"] > 150
    assert all(v["p_holm"] >= v["p"] for v in out["hypotheses"].values())
