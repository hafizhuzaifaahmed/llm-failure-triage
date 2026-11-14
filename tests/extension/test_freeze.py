"""The frozen CFP configuration (D-138) must not drift: every hashed file and every engine parameter is checked."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "configs" / "extension" / "cfp_frozen.json"

spec = importlib.util.spec_from_file_location("freeze_cfp", ROOT / "scripts" / "extension" / "freeze_cfp.py")
freeze = importlib.util.module_from_spec(spec)
spec.loader.exec_module(freeze)


@pytest.fixture(scope="module")
def doc():
    assert MANIFEST.exists(), "the freeze manifest is missing"
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_every_frozen_file_is_unchanged(doc):
    changed = [f for f, h in doc["files"].items() if freeze.content_hash(f) != h]
    assert not changed, f"frozen files changed (a deviation must be entered in DECISIONS.md first): {changed}"


def test_every_engine_parameter_is_unchanged(doc):
    assert freeze.parameters() == doc["parameters"]


def test_manifest_covers_engine_driver_analysis_and_frame(doc):
    for needed in ("src/triage_ext/mutate.py", "src/triage_ext/probe.py", "src/triage_ext/ledger.py",
                   "src/triage_ext/policy.py", "scripts/extension/run_probes_tranche.py",
                   "scripts/extension/confirm_analysis.py", "configs/extension/confirm_frame.jsonl"):
        assert needed in doc["files"]


def test_hash_ignores_line_endings(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_bytes(b"x\r\ny\r\n")
    (tmp_path / "b.txt").write_bytes(b"x\ny\n")
    monkeypatch.setattr(freeze, "ROOT", tmp_path)
    assert freeze.content_hash("a.txt") == freeze.content_hash("b.txt")


def test_tranche_driver_reads_only_the_buggy_side():
    import re
    text = (ROOT / "scripts" / "extension" / "run_probes_tranche.py").read_text(encoding="utf-8")
    for pat in (r"\bruns_f\b", r"\bcompile_f\b", r"\bmeta_f\b", r"ground_truth", r"labels_D", r"fixed_bodies"):
        assert not re.search(pat, text), pat
