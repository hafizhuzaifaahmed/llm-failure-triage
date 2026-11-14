"""D-104: E9b (Sonnet on D2) is configured as pre-registered and cannot reach the API without the authors' go."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "frontier"))

import e9b  # noqa: E402
from triage import frontier  # noqa: E402


def test_config_is_the_preregistered_design():
    e = json.loads(e9b.EXP.read_text(encoding="utf-8"))
    assert e["dataset"] == "D2" and e["split"] == "test" and e["prompt_set"] == "local_m1b"
    assert e["model"] == frontier.MODEL == "claude-sonnet-5-5"
    assert {c["arm"]: c["levels"] for c in e["conditions"]} == {"J1": ["S1"], "DEB": ["S1"]}
    assert e["replicates"] == 1 and all("replicates" not in c for c in e["conditions"])
    assert e["sample_file"] == "data/processed/sample_D2_test_E9B_scored.json"


def test_cap_and_own_call_log():
    assert e9b.CAP_USD == 11.0 < 12.0                       # under the authors' Console limit
    assert e9b.LOG_DIR != frontier.LOG_DIR                    # E9's spend and answers are not counted or replayed
    assert e9b.GO.parent == e9b.RUN and e9b.GO.name == "AUTHORS_KEY_SET"


def test_scope_allows_e9b():
    s = json.loads((ROOT / "configs" / "local_scope.json").read_text(encoding="utf-8"))
    assert "E9B_SONNET55_D2" in s["allowed_experiments"] and "D2" in s["allowed_datasets"]


def test_key_file_is_ignored():
    import e9
    assert subprocess.run(["git", "check-ignore", "-q", str(e9.ENV_FILE)], cwd=ROOT, stdin=subprocess.DEVNULL,
                          capture_output=True).returncode == 0


def test_run_refuses_without_the_key_or_the_authors_go_file(monkeypatch, tmp_path):
    import anthropic
    import e9
    monkeypatch.setattr(e9, "ENV_FILE", tmp_path / "no.env")
    monkeypatch.setattr(e9b, "GO", tmp_path / "missing")
    monkeypatch.setattr(anthropic, "Anthropic", lambda *a, **k: pytest.fail("test constructed an API client"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        e9b.cmd_run(None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "placeholder-for-the-test")
    with pytest.raises(SystemExit):
        e9b.cmd_run(None)
