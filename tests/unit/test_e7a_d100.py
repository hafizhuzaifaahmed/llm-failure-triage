"""D-100: E7a second generator. Fakes and committed data only: no server, no model, no WSL."""
import copy
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "local"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

from triage import expl_profile, scope  # noqa: E402
from triage.io_utils import read_jsonl  # noqa: E402

P = json.loads(expl_profile.E7A_PROFILE_FILE.read_text(encoding="utf-8"))


def test_profile_is_a_frozen_settings_server_on_its_own_port(tmp_path):
    p = expl_profile.load(expl_profile.E7A_PROFILE_FILE)
    assert p["kind"] == "e7a" and set(p["server_env_overrides"]) == {"OLLAMA_HOST"} and p["base_url"].endswith(":11438")
    bad = copy.deepcopy(P)
    bad["server_env_overrides"]["OLLAMA_KV_CACHE_TYPE"] = "q8_0"
    f = tmp_path / "e7a.json"
    f.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(expl_profile.ProfileError):
        expl_profile.load(f)


def test_candidates_are_outside_every_judge_family_in_the_pre_registered_order():
    assert P["candidate_order"] == ["phi4:14b-q4_K_M", "llama3.1:8b-instruct-q4_K_M"]
    for t in P["candidate_order"]:
        assert not any(f in t for f in ("qwen", "gemma", "mistral", "ministral"))
    assert P["feasibility_dir"] == "results/dev/feasibility"     # where select_g.py reads Step 1


def test_driver_uses_g_prompt_set_and_g_style_directories():
    import e7a
    assert e7a.PROMPT_SET == "v0" and e7a.DATASET == "D1G2"
    c, e = e7a.dirs("phi4:14b-q4_K_M")
    assert c.name == "candidates_phi4_14b-q4_K_M" and e.name == "executions_phi4_14b-q4_K_M"


def test_experiment_and_scope():
    e = json.loads((ROOT / "configs" / "experiments" / "LOCAL_HO_E7A_M1.json").read_text(encoding="utf-8"))
    assert e["dataset"] == "D1G2" and e["model"] == "M1" and e["prompt_set"] == "local_m1b" and e["replicates"] == 1
    assert {"arm": "J1", "levels": ["S1"], "variant": "noF"} in e["conditions"]
    assert {c["arm"] for c in e["conditions"]} == {"DA", "KA", "R0", "J1", "SC", "DEB"}
    sc = scope.load(scope.LOCAL_SCOPE_FILE)
    sc.check_experiment("LOCAL_HO_E7A_M1")
    sc.check_dataset("D1G2")
    for t in P["candidate_order"]:
        sc.check_model(t, {"digest": "d" * 64}, local=True)


def test_analysis_runs_on_a_stand_in_corpus(tmp_path, monkeypatch):
    """Code path only: D1's committed M1 decisions (E1-E3 + the noF ablation) stand in for the D1G2 run."""
    import e7a_analysis as a
    run = tmp_path / "run"
    run.mkdir()
    src = ROOT / "results" / "runs_local"
    rows = [d for d in read_jsonl(src / "LOCAL_HO_E1E3_M1" / "decisions.jsonl")
            if d["arm"] in ("KA", "R0", "DA") or (d.get("level") == "S1" and (d.get("variant") or "full") == "full"
                                                  and d["arm"] in ("J1", "SC", "DEB") and d["replicate"] == 0)]
    rows += [d for d in read_jsonl(src / "LOCAL_HO_E4_M1" / "decisions.jsonl") if d["arm"] == "J1" and d.get("variant") == "noF"]
    (run / "decisions.jsonl").write_text("".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")
    shutil.copy2(src / "LOCAL_HO_E1E3_M1" / "leakage_rejections.jsonl", run / "leakage_rejections.jsonl")
    sel = ROOT / "results" / "e7a" / "selection.json"
    made = not sel.exists()
    if made:
        sel.parent.mkdir(parents=True, exist_ok=True)
        sel.write_text(json.dumps({"selected": None}), encoding="utf-8")
    try:
        monkeypatch.setattr(a, "DATASET", "D1")
        monkeypatch.setattr(a, "RUN", run)
        monkeypatch.setattr(a, "OUT", tmp_path / "out.json")
        a.main()
    finally:
        if made:
            sel.unlink()
    out = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert set(out["hypotheses"]) == {"H7-1", "H7-2"} and out["n_instances"] > 150
    assert all(h["p_holm"] >= h["p"] for h in out["hypotheses"].values())
