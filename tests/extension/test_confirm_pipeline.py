"""Confirmation pipeline after generation (D-142): execution, labelling, votes and concatenation drivers.

Everything here runs offline on the Windows side: no model call, no test execution, no confirmation data.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "extension"))

import confirm_lib as L  # noqa: E402
import confirm_pipeline as P  # noqa: E402
from triage import config  # noqa: E402

VALID = ROOT / "results" / "extension" / "validation"


# ---- concatenation ---------------------------------------------------------------------------------------------
def _write(p: Path, recs: list[dict], crlf: bool = False):
    nl = "\r\n" if crlf else "\n"
    p.write_bytes("".join(json.dumps(r) + nl for r in recs).encode("utf-8"))
    return p


def _part(tmp, name, ids, focal="F::a", crlf=False, votes=True, extra_ledger=()):
    d = tmp / name
    d.mkdir()
    inst = [{"instance_id": i, "focal_id": f"{focal}{i}"} for i in ids]
    part = {"tranche": name, "instances": _write(d / "i.jsonl", inst, crlf),
            "labels": _write(d / "l.jsonl", [{"instance_id": i, "label": "TF"} for i in ids], crlf),
            "ledger": _write(d / "g.jsonl", [{"instance_id": i, "summary": {}} for i in list(ids) + list(extra_ledger)], crlf),
            "votes": {}}
    if votes:
        for m in L.VOTE_MODELS:
            part["votes"][m] = _write(d / f"v_{m}.jsonl", [{"instance_id": i, "replicate": r, "label_raw": "TEST_FAULT"}
                                                           for i in ids for r in (L.VOTE_REPLICATE, 3)])
    return part


def test_concatenation_copies_lines_and_counts(tmp_path):
    parts = [_part(tmp_path, "F1", ["a", "b"], crlf=True), _part(tmp_path, "F2", ["c"]),
             _part(tmp_path, "CTRL", ["d", "e"], votes=False)]
    man = L.concatenate(parts, tmp_path / "out_ledger", tmp_path / "out", frame=None)
    led = L.raw_lines(tmp_path / "out_ledger" / "ledger.jsonl")
    assert [json.loads(x)["instance_id"] for x in led] == ["a", "b", "c", "d", "e"]
    src = L.raw_lines(parts[0]["ledger"]) + L.raw_lines(parts[1]["ledger"]) + L.raw_lines(parts[2]["ledger"])
    assert led == src                                                  # byte-identical lines, CRLF normalised
    assert b"\r" not in (tmp_path / "out_ledger" / "ledger.jsonl").read_bytes()
    votes = L.read_jsonl(tmp_path / "out" / "votes" / "M1" / "decisions.jsonl")
    assert len(votes) == 3 and {v["replicate"] for v in votes} == {L.VOTE_REPLICATE}   # other replicates dropped
    assert man["counts"]["CTRL"] == {"instances": 2, "ledger": 2, "labels": 2}
    assert all(len(s["sha256"]) == 64 for s in man["sources"])
    assert (tmp_path / "out" / "concat_manifest.json").exists()


def test_concatenation_refuses_overwrite(tmp_path):
    parts = [_part(tmp_path, "F1", ["a"])]
    L.concatenate(parts, tmp_path / "ol", tmp_path / "o", frame=None)
    with pytest.raises(SystemExit, match="overwrite"):
        L.concatenate(parts, tmp_path / "ol", tmp_path / "o", frame=None)


def test_concatenation_refuses_duplicate_ids_across_tranches(tmp_path):
    parts = [_part(tmp_path, "F1", ["a", "b"]), _part(tmp_path, "F2", ["b"])]
    with pytest.raises(SystemExit, match="duplicate"):
        L.concatenate(parts, tmp_path / "ol", tmp_path / "o", frame=None)


def test_concatenation_refuses_orphan_ledger_records(tmp_path):
    parts = [_part(tmp_path, "F1", ["a"], extra_ledger=["zz"])]
    with pytest.raises(SystemExit, match="no instance"):
        L.concatenate(parts, tmp_path / "ol", tmp_path / "o", frame=None)


def test_concatenation_refuses_instances_of_another_tranche(tmp_path):
    parts = [_part(tmp_path, "F1", ["a"])]
    with pytest.raises(SystemExit, match="another tranche"):
        L.concatenate(parts, tmp_path / "ol", tmp_path / "o", frame={"F::aa": "F2"})


# ---- labelling -------------------------------------------------------------------------------------------------
def test_redirected_stores_restore_config_even_on_error(tmp_path):
    before = (config.GT_STORE, config.LEAKAGE_GUARD, config.PROCESSED)
    with pytest.raises(RuntimeError):
        with L.redirected_stores(tmp_path):
            assert config.GT_STORE == config.PROCESSED == tmp_path
            raise RuntimeError("boom")
    assert (config.GT_STORE, config.LEAKAGE_GUARD, config.PROCESSED) == before


def test_build_dataset_reproduces_study_records_for_one_focal_method(tmp_path):
    focal = L.read_jsonl(P.STUDY["labels"])[0]["focal_id"]
    execs = tmp_path / "ex"
    cands = tmp_path / "ca"
    execs.mkdir()
    cands.mkdir()
    for p in P.D1_EXECS.glob("*.json"):
        if json.loads(p.read_text())["focal_id"] == focal:
            (execs / p.name).write_bytes(p.read_bytes())
            (cands / p.name).write_bytes((P.D1_CANDS / p.name).read_bytes())
    L.build_dataset("D1", execs, cands, P._study_contexts(), P._study_fixed(), tmp_path / "out")
    built = {r["instance_id"]: r for r in L.read_jsonl(tmp_path / "out" / "labels_D1.jsonl")}
    study = {r["instance_id"]: r for r in L.read_jsonl(P.STUDY["labels"]) if r["focal_id"] == focal}
    assert built and built == study
    assert not (config.GT_STORE / "labels_D1.jsonl").samefile(tmp_path / "out" / "labels_D1.jsonl")


def test_label_tranche_refuses_to_overwrite(tmp_path, monkeypatch):
    real = L.paths("F1")
    fake = {**real, "labels": tmp_path / "labels.jsonl"}
    fake["labels"].write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(L, "paths", lambda tr: fake)
    with pytest.raises(SystemExit, match="written once"):
        L.label_tranche("F1")


# ---- execution -------------------------------------------------------------------------------------------------
def test_group_candidates_skips_unassembled_and_already_executed(tmp_path):
    c, o = tmp_path / "c", tmp_path / "o"
    c.mkdir()
    o.mkdir()
    for cid, ok in (("x1", True), ("x2", False), ("x3", True)):
        (c / f"{cid}.json").write_text(json.dumps({"candidate_id": cid, "assembled": ok,
                                                   "focal_id": "Lang_7::A::f()"}), encoding="utf-8")
    (o / "x3.json").write_text("{}", encoding="utf-8")
    g = L.group_candidates(c, o)
    assert list(g) == [("Lang", "7")] and [x["candidate_id"] for x in g[("Lang", "7")]] == ["x1"]


def test_execution_scope_rejects_methods_of_other_tranches():
    some_f2 = next(iter(L.contexts("F2")))
    with pytest.raises(SystemExit, match="not methods of tranche F1"):
        L.check_execution_scope("F1", {("X", "1"): [{"focal_id": some_f2}]})
    one_f1 = next(iter(L.contexts("F1")))
    L.check_execution_scope("F1", {("X", "1"): [{"focal_id": one_f1}]})          # no exception


# ---- votes -----------------------------------------------------------------------------------------------------
def test_vote_replicate_is_unused_by_every_committed_run():
    used = set()
    for f in list((ROOT / "results" / "runs_local").glob("*/decisions.jsonl")) + \
            list((ROOT / "results" / "revision" / "runs").glob("*/decisions.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                used.add(json.loads(line).get("replicate"))
    assert L.VOTE_REPLICATE not in used


def test_vote_configs_match_the_registration():
    for tr in L.JUDGED:
        for m in L.VOTE_MODELS:
            name = L.vote_run_name(tr, m)
            exp = json.loads((L.EXP_DIR / f"{name}.json").read_text(encoding="utf-8"))
            assert exp["name"] == exp["run_label"] == name
            assert exp["conditions"] == [{"arm": "J1", "levels": ["S1"], "replicate_indices": [L.VOTE_REPLICATE]}]
            assert exp["prompt_set"] == "local_m1b" and exp["split"] == "test" and exp["replicates"] == 1
            assert exp["dataset"] == L.paths(tr)["tag"]
            assert exp["instances_file"].startswith(f"data/extension/confirm/{tr}/")
            assert exp["guard_file"].startswith(f"data/extension/confirm/{tr}/")
            assert (exp.get("model") == m) if m != "M3" else exp["model_tag"].startswith("ministral-3:14b")
    scope = json.loads((ROOT / "configs" / "local_scope.json").read_text(encoding="utf-8"))
    names = [L.vote_run_name(tr, m) for tr in L.JUDGED for m in L.VOTE_MODELS]
    assert set(names) <= set(scope["allowed_experiments"])


def test_m3_profile_copy_changes_only_routing_of_logs_and_experiments():
    from triage import expl_profile
    from triage.ollama import LOCAL_CALL_LOG_DIR
    orig = json.loads(L.E6B_PROFILE.read_text(encoding="utf-8"))
    copy = expl_profile.load(L.CONF_E6B_PROFILE)                           # passes the study's own profile checks
    changed = {k for k in set(orig) | set(copy) if orig.get(k) != copy.get(k)}
    assert changed == {"_status", "experiments", "call_log_dir", "session_log", "safety_events", "selection_gated"}
    assert copy["model_tag"] == orig["model_tag"] and copy["model_spec"] == orig["model_spec"]
    assert expl_profile.resolve(copy["call_log_dir"]) != LOCAL_CALL_LOG_DIR
    assert copy["call_log_dir"].startswith("data/extension/confirm/")


def test_replay_client_can_never_make_a_call(tmp_path):
    from triage.llm import NotInLog
    c = L.vote_client("M1", tmp_path, replay=True)
    with pytest.raises(NotInLog):
        c.backend.call("qwen3.5:9b", [{"role": "user", "content": "x"}], 0.7, 1.0, 16, True, None)


# ---- the real steps refuse while the gate is closed -----------------------------------------------------------
@pytest.mark.parametrize("argv", [["execute", "--tranche", "F1"], ["label", "--tranche", "F2"], ["concat"],
                                  ["vote", "--tranche", "F1", "--model", "M1"],
                                  ["vote", "--tranche", "F2", "--model", "M3"]])
def test_real_steps_refuse_without_registration(argv):
    if (ROOT / "configs" / "extension" / "osf_registration.json").exists():
        pytest.skip("a registration is recorded; this test covers the unregistered state")
    with pytest.raises(SystemExit, match="REFUSED"):
        P.main(argv)


def test_control_group_cannot_be_judged():
    with pytest.raises(SystemExit):
        P.main(["vote", "--tranche", "CTRL", "--model", "M1"])          # argparse rejects CTRL


def test_vote_refuses_unsealed_labels(monkeypatch, tmp_path):
    monkeypatch.setattr(P, "_require", lambda checks: None)
    fake = {**L.paths("F1"), "labels": tmp_path / "labels.jsonl", "instances": tmp_path / "i.jsonl",
            "guard": tmp_path / "g.jsonl"}
    for k in ("labels", "instances", "guard"):
        fake[k].write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(L, "paths", lambda tr: fake)
    with pytest.raises(SystemExit, match="sealed"):
        P.main(["vote", "--tranche", "F1", "--model", "M1"])


# ---- the drivers are outside the frozen engine -----------------------------------------------------------------
def test_new_drivers_do_not_touch_frozen_or_study_paths():
    changed = subprocess.run(["git", "diff", "--name-only", "eb2d231", "--", "src/triage_ext"], cwd=ROOT,
                             capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout.split()
    assert changed == []
    for rel in ("scripts/extension/confirm_lib.py", "scripts/extension/confirm_pipeline.py"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "triage_ext" not in text                                   # the drivers never import the engine


# ---- recorded reproductions of the original data ---------------------------------------------------------------
@pytest.mark.parametrize("name", ["validate_labels_D1", "validate_votes_E8", "validate_concat_pilot"])
def test_recorded_reproductions_are_exact(name):
    rep = json.loads((VALID / f"{name}.json").read_text(encoding="utf-8"))
    assert rep["exact"] is True


def test_execution_reproduction_differs_only_at_the_time_limit():
    rep = json.loads((VALID / "validate_execution_D1.json").read_text(encoding="utf-8"))
    assert rep["records_compared"] == rep["compilation_identical"] == 702
    assert rep["methods_compared"] == 2909 and rep["label_mismatches"] <= 2
    assert all("TIMEOUT" in (m["stored"], m["reexecuted"]) for m in rep["mismatches"])
    alone = json.loads((VALID / "validate_execution_timing_cases.json").read_text(encoding="utf-8"))
    flipped = {(m["candidate_id"], m["method"]) for m in rep["mismatches"]}
    assert all(c["stored"] == c["alone"] for c in alone["cases"] if (c["candidate_id"], c["method"]) in flipped)
    assert all("TIMEOUT" in (c["stored"], c["alone"]) for c in alone["cases"] if c["stored"] != c["alone"])


def test_near_time_limit_counts_by_label(tmp_path):
    rec = {"methods": [{"compile_b": True, "compile_f": True, "method": "t",
                        "runs_b": [{"outcome": "exception", "exception": "E", "failing_test_line": 3, "duration_s": 0.1}] * 3,
                        "runs_f": [{"outcome": "exception", "exception": "E", "failing_test_line": 3, "duration_s": 25.0}] * 3},
                       {"compile_b": True, "compile_f": True, "method": "u",
                        "runs_b": [{"outcome": "pass", "duration_s": 0.1}] * 3,
                        "runs_f": [{"outcome": "pass", "duration_s": 0.1}] * 3}]}
    (tmp_path / "x.json").write_text(json.dumps(rec), encoding="utf-8")
    assert L.near_time_limit(tmp_path) == {"threshold_s": 20.0, "methods_by_label": {"TF": 1}}


def test_report_reading_rules(tmp_path):
    import confirm_report as R
    base = {"difference": 0.1, "ci95": [-0.05, 0.25], "p": 0.2, "p_holm": 0.6, "supported": False}
    assert "counts against" in R.reading("C1", base)                       # powered: a null counts against
    assert "inconclusive" in R.reading("C3", base)                         # underpowered: a null is inconclusive
    assert "wholly below" in R.reading("C2", {**base, "ci95": [0.0, 0.15]})  # below the pilot estimate 0.189
    assert "opposite" in R.reading("C4", {**base, "difference": 3.0, "p_holm": 0.01})
    assert R.reading("C1", {**base, "supported": True}) == "**supported**"
    out = tmp_path / "r.md"
    rc = subprocess.run([sys.executable, str(ROOT / "scripts" / "extension" / "confirm_report.py"), "--analysis",
                         str(ROOT / "results" / "extension" / "dryrun" / "confirm_analysis_dryrun_on_pilot.json"),
                         "--out", str(out)], cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    assert rc.returncode == 0 and "DRY RUN ON PILOT DATA" in out.read_text(encoding="utf-8")
