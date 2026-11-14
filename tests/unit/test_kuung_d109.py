"""D-109: KUU-NG is configured as pre-registered (panel, replicate index, profiles, rule) before any call."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
sys.path.insert(0, str(ROOT / "scripts" / "local"))


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


an = load("kuung_analysis", "scripts/analysis/kuung_analysis.py")


def test_rule_is_kuu():
    TF, PF = an.TF, an.PF
    assert an.unanimous([TF, TF, TF]) == TF
    assert an.unanimous([TF, TF, PF]) == PF and an.unanimous([TF, TF, None]) == PF and an.unanimous([]) == PF


def test_configs_fresh_replicate_and_panel():
    from triage import expl_profile
    for ds in ("D1", "D2"):
        for who in ("M1", "E6B", "NG"):
            name = f"LOCAL_HO_KUUNG_{ds}_{who}"
            cfg = json.loads((ROOT / "configs" / "experiments" / f"{name}.json").read_text(encoding="utf-8"))
            assert cfg["conditions"] == [{"arm": "J1", "levels": ["S1"], "replicate_indices": [30]}]
            assert cfg["dataset"] == ds and cfg["prompt_set"] == "local_m1b"
            assert expl_profile.for_experiment(name) is not None
            assert an.PLAN[ds]["ng"][who] == name
    p = json.loads((ROOT / "configs" / "kuung.json").read_text(encoding="utf-8"))
    assert p["candidate_order"] == ["phi4:14b-q4_K_M", "llama3.1:8b-instruct-q4_K_M"]
    assert p["base_url"].endswith(":11439") and set(p["server_env_overrides"]) == {"OLLAMA_HOST"}
    assert p["selection_gated"]["experiments"] == ["LOCAL_HO_KUUNG_D1_NG", "LOCAL_HO_KUUNG_D2_NG"]
    for f in ("configs/kuu_m1.json", "configs/e6b.json", "configs/kuung.json"):
        expl_profile.load(ROOT / f)


def test_no_generator_family_in_the_panel():
    frozen = json.loads((ROOT / "configs" / "local_models.FROZEN.json").read_text(encoding="utf-8"))
    p = json.loads((ROOT / "configs" / "kuung.json").read_text(encoding="utf-8"))
    assert all(not t.startswith("gemma") for t in p["candidate_order"])
    assert "gemma" not in json.loads((ROOT / "configs" / "e6b.json").read_text(encoding="utf-8"))["model_tag"]


def test_replicate_30_unused_by_committed_runs():
    for f in (ROOT / "configs" / "experiments").glob("*.json"):
        if "KUUNG" in f.name:
            continue
        cfg = json.loads(f.read_text(encoding="utf-8"))
        for c in cfg.get("conditions", []):
            assert 30 not in c.get("replicate_indices", []), f.name
