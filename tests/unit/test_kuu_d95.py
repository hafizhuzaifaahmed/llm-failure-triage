"""D-95: keep-unless-unanimous cross-family triage (KUU). Fakes and committed data only: no server, no model."""
import copy
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import kuu_analysis as ka  # noqa: E402
from triage import expl_profile, scope  # noqa: E402
from triage.io_utils import read_jsonl  # noqa: E402

TF, PF, INV = "TEST_FAULT", "PROGRAM_FAULT", "INVALID"
EXP = ROOT / "configs" / "experiments"
NAMES = ("LOCAL_HO_KUU_D2_M1", "LOCAL_HO_KUU_D2_M2", "LOCAL_HO_KUU_D2_E6B")


@pytest.mark.parametrize("votes,expect", [([TF, TF, TF], TF), ([TF, TF, PF], PF), ([PF, PF, PF], PF),
                                          ([TF, TF, INV], PF), ([TF, TF, None], PF), ([TF, TF], PF), ([], PF)])
def test_kuu_discards_only_on_three_valid_tf_votes(votes, expect):
    assert ka.kuu(votes) == expect


def test_frozen_copy_profiles_carry_the_frozen_spec_and_only_a_port(tmp_path):
    frozen = json.loads(expl_profile.FROZEN_FILE.read_text(encoding="utf-8"))["models"]
    for f in expl_profile.KUU_PROFILE_FILES:
        p = expl_profile.load(f)
        assert p["kind"] == "frozen_copy" and p["model_spec"] == frozen[p["model_tag"]]
        assert set(p["server_env_overrides"]) == {"OLLAMA_HOST"} and not p["base_url"].endswith(":11434")
        bad = copy.deepcopy(p)
        bad["model_spec"]["top_k"] = 1
        g = tmp_path / "bad.json"
        g.write_text(json.dumps(bad), encoding="utf-8")
        with pytest.raises(expl_profile.ProfileError):
            expl_profile.load(g)
        bad = copy.deepcopy(p)
        bad["server_env_overrides"]["OLLAMA_FLASH_ATTENTION"] = "0"
        g.write_text(json.dumps(bad), encoding="utf-8")
        with pytest.raises(expl_profile.ProfileError):
            expl_profile.load(g)


def test_experiments_use_an_unused_replicate_index_on_d2_s1_j1():
    used = set()
    for run in ("LOCAL_HO_E5R1_D2", "LOCAL_HO_E5R3_M2_D2", "LOCAL_HO_E8_VOTE_M1", "LOCAL_HO_E8_VOTE_M2", "LOCAL_HO_E8_VOTE_E6B",
                "LOCAL_HO_E1E3_M1", "LOCAL_HO_E5R3_M2", "LOCAL_HO_E6B_D1TEST"):
        used |= {d["replicate"] for d in read_jsonl(ROOT / "results" / "runs_local" / run / "decisions.jsonl")}
    for n in NAMES:
        e = json.loads((EXP / f"{n}.json").read_text(encoding="utf-8"))
        (c,) = e["conditions"]
        assert e["dataset"] == "D2" and e["split"] == "test" and e["prompt_set"] == "local_m1b"
        assert c == {"arm": "J1", "levels": ["S1"], "replicate_indices": [20]} and 20 not in used


def test_each_member_finds_its_own_profile_and_scope_admits_it():
    tags = {"LOCAL_HO_KUU_D2_M1": "qwen3.5:9b", "LOCAL_HO_KUU_D2_M2": "gemma4:12b"}
    for n, t in tags.items():
        p = expl_profile.for_experiment(n)
        assert p["kind"] == "frozen_copy" and p["model_tag"] == t
        assert json.loads((EXP / f"{n}.json").read_text(encoding="utf-8"))["model_tag"] == t
    e6 = expl_profile.for_experiment("LOCAL_HO_KUU_D2_E6B")
    assert e6["kind"] == "e6b" and "LOCAL_HO_KUU_D2_E6B" in e6["selection_gated"]["experiments"]
    sc = scope.load(scope.LOCAL_SCOPE_FILE)
    for n in NAMES:
        sc.check_experiment(n)


def test_runner_routes_a_member_to_its_profile_without_reaching_a_client(monkeypatch):
    import run_experiment
    seen = {}
    monkeypatch.setattr(run_experiment, "make_client", lambda *a, **k: seen.update(profile=k.get("profile")) or "c")
    monkeypatch.setattr(run_experiment, "execute", lambda exp, *a, **k: seen.update(exp=exp))
    run_experiment.main([str(EXP / "LOCAL_HO_KUU_D2_M2.json")])
    assert seen["profile"]["model_tag"] == "gemma4:12b" and seen["exp"]["model_tag"] == "gemma4:12b"
    assert seen["exp"]["session_log"] == "logs/sessions_kuu.jsonl" and seen["exp"]["ram_gate_min_gib"] == 4.0


def test_analysis_runs_on_stand_in_d2_members(tmp_path, monkeypatch):
    """Code path only: committed D2 J1 decisions re-indexed as the members (no KUU output exists yet)."""
    runs = tmp_path / "runs"
    src = ROOT / "results" / "runs_local"
    shutil.copytree(src / "LOCAL_HO_E5R1_D2", runs / "LOCAL_HO_E5R1_D2")
    for name, frm in (("LOCAL_HO_KUU_D2_M1", "LOCAL_HO_E5R1_D2"), ("LOCAL_HO_KUU_D2_M2", "LOCAL_HO_E5R3_M2_D2"),
                      ("LOCAL_HO_KUU_D2_E6B", "LOCAL_HO_E5R1_D2")):
        (runs / name).mkdir(parents=True)
        rows = [{**d, "replicate": 20} for d in read_jsonl(src / frm / "decisions.jsonl")
                if d["arm"] == "J1" and d.get("level") == "S1"]
        (runs / name / "decisions.jsonl").write_text("".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")
    monkeypatch.setattr(ka, "RUNS", runs)
    monkeypatch.setattr(ka, "OUT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["kuu_analysis.py", "d2"])
    ka.main()
    out = json.loads((tmp_path / "kuu_d2.json").read_text(encoding="utf-8"))
    assert set(out["hypotheses"]) == {"H10-1", "H10-2"} and out["n_instances"] > 250
    assert all(h["p_holm"] >= h["p"] for h in out["hypotheses"].values())
