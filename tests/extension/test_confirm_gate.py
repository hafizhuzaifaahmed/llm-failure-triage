"""Readiness gate and gated generation driver for the CFP confirmation (D-140)."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "extension"))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "extension" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


gate = _load("confirm_gate")
gen = _load("confirm_generate")


def _reg(tmp_path, **over):
    rec = {"osf_id": "abc12", "url": "https://osf.io/abc12", "registered_utc": "2026-11-12T00:00:00Z",
           "registration_doc_sha256": gate.content_hash(gate.PREREG), "recorded_in_decision": "D-141", **over}
    p = tmp_path / "osf_registration.json"
    p.write_text(json.dumps(rec), encoding="utf-8")
    return p


def test_registration_must_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "REGISTRATION", tmp_path / "absent.json")
    ok, why = gate.check_registration()
    assert not ok and "absent" in why


def test_registration_must_be_complete_and_match_the_repository_text(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "REGISTRATION", _reg(tmp_path))
    assert gate.check_registration()[0]
    monkeypatch.setattr(gate, "REGISTRATION", _reg(tmp_path, registration_doc_sha256="0" * 64))
    assert not gate.check_registration()[0]                       # registered text differs from the repository's
    monkeypatch.setattr(gate, "REGISTRATION", _reg(tmp_path, osf_id=""))
    assert not gate.check_registration()[0]                       # no identifier recorded


def test_manifest_hashes_and_frozen_components_hold_now():
    ok, why = gate.check_manifest_and_hashes()
    assert ok, why
    ok, why = gate.check_nothing_frozen_changed()
    assert ok, why


def test_offline_evaluation_can_never_be_ready():
    rep = gate.evaluate(offline=True)
    assert rep["ready"] is False
    assert [c["ok"] for c in rep["checks"] if c["check"][0] in "23"] == [None, None]


def test_every_check_must_pass(monkeypatch):
    for failing in ("check_registration", "check_no_desktop_server", "check_frozen_server",
                    "check_manifest_and_hashes", "check_nothing_frozen_changed"):
        for name in ("check_registration", "check_no_desktop_server", "check_frozen_server",
                     "check_manifest_and_hashes", "check_nothing_frozen_changed"):
            monkeypatch.setattr(gate, name, (lambda: (False, "x")) if name == failing else (lambda: (True, "ok")))
        assert gate.evaluate()["ready"] is False, failing
    for name in ("check_registration", "check_no_desktop_server", "check_frozen_server",
                 "check_manifest_and_hashes", "check_nothing_frozen_changed"):
        monkeypatch.setattr(gate, name, lambda: (True, "ok"))
    assert gate.evaluate()["ready"] is True


def test_generation_is_refused_when_the_gate_fails(monkeypatch):
    monkeypatch.setattr(gate, "evaluate", lambda offline=False: {"ready": False, "checks": [
        {"check": "1 OSF registration", "ok": False, "detail": "absent"}]})
    with pytest.raises(SystemExit) as e:
        gen.main(["--tranche", "F1"])
    assert "NOT READY" in str(e.value)


def test_a_real_run_cannot_be_limited_to_part_of_a_tranche(monkeypatch):
    monkeypatch.setattr(gate, "evaluate", lambda offline=False: {"ready": True, "checks": []})
    with pytest.raises(SystemExit) as e:
        gen.main(["--tranche", "F1", "--limit", "2"])
    assert "whole" in str(e.value)


def test_scope_lock_only_gained_entries():
    old = json.loads(subprocess.run(["git", "show", "master:configs/local_scope.json"], cwd=ROOT, capture_output=True,
                                    text=True, encoding="utf-8", stdin=subprocess.DEVNULL).stdout)
    new = json.loads((ROOT / "configs" / "local_scope.json").read_text(encoding="utf-8"))
    assert new["allowed_splits"] == old["allowed_splits"] and new["allowed_models"] == old["allowed_models"]
    for k in ("allowed_datasets", "allowed_experiments"):
        assert new[k][: len(old[k])] == old[k]
    assert set(new["allowed_datasets"]) - set(old["allowed_datasets"]) == {"D1C_F1", "D1C_F2", "D1C_CTRL"}
    assert all(x.startswith("LOCAL_CONF_VOTE_") for x in set(new["allowed_experiments"]) - set(old["allowed_experiments"]))
    assert new["_status"].startswith(old["_status"])


def test_tranche_contexts_are_separate_and_complete():
    man = json.loads((ROOT / "configs" / "extension" / "confirm_dataset_manifest.json").read_text(encoding="utf-8"))
    assert {t: v["contexts"] for t, v in man["tranches"].items()} == {"F1": 62, "F2": 371, "CTRL": 246}
    assert man["generation_calls_total"] == 2223
    study = {p.name for p in (ROOT / "data" / "interim" / "context").glob("*.json")}
    for tr in ("F1", "F2", "CTRL"):
        files = list((ROOT / "data" / "extension" / "confirm" / tr / "context").glob("*.json"))
        assert len(files) == man["tranches"][tr]["contexts"]
        assert not ({f.name for f in files} & study)              # no focal method of the study is reused
        c = json.loads(files[0].read_text(encoding="utf-8"))
        assert c["tranche"] == tr and c["split"] == "test" and "_label_side" not in c and "fixed_body" not in c
