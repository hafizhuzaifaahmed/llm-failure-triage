"""Integration tests for whole-method dependence probes (WDP; OPUS_EXECUTION_BRIEF.md version 2, T11 to T13).

T11 is an end-to-end toy fixture, independent of Defects4J, that needs a JDK and the JUnit jar (run inside WSL).
T12 checks marker consistency on the WDP_D1_DEV ledger. T13 re-runs 30 seeded dev instances and compares levels;
it needs the Defects4J checkouts and is opt-in (environment variable WDP_RUN_T13=1) because it runs real probes.
"""
import importlib.util
import json
import os
import random
import shutil
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DEV_LEDGER = ROOT / "results" / "extension" / "wdp" / "WDP_D1_DEV" / "ledger.jsonl"
FO_DEV_LEDGER = ROOT / "results" / "extension" / "probes" / "CFP_D1_DEV2" / "ledger.jsonl"
SEED = 20261113


def _read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _java_available():
    if os.name == "nt" or not shutil.which("javac") or not shutil.which("java"):
        return False
    from triage.execution import JUNIT_JAR
    return JUNIT_JAR.exists()


# ---- T11 toy end-to-end ------------------------------------------------------------------------------------------
PROGRAM = """package toy;

public class Calc {
    public int add(int a, int b) {
        return a + b;
    }
}
"""
METHOD = """public int add(int a, int b) {
        return a + b;
    }"""

TESTS = {   # class name -> (test body, expected level, expected reason, expected entered)
    "TA": ("org.junit.Assert.assertEquals(1, 2);\n        new Calc().add(1, 1);", "U", None, False),
    "TB": ("try { new Calc().add(1, 1); } catch (Throwable t) { }\n        org.junit.Assert.assertEquals(1, 2);",
           "ND", "throw_swallowed", True),
    "TC": ("Thread th = new Thread(new Runnable() { public void run() { new Calc().add(1, 1); } });\n"
           "        th.start();\n        th.join();\n        org.junit.Assert.assertEquals(1, 2);",
           "ND", "throw_swallowed", True),
    "TD": ("new Calc().add(1, 1);\n        org.junit.Assert.assertEquals(1, 2);", "RI", None, True),
    "TE": ("org.junit.Assert.assertEquals(5, new Calc().add(2, 2));", "WS", None, True),
}


def _test_source(cls, body):
    return (f"package toy;\n\nimport org.junit.Test;\n\npublic class {cls} {{\n    @Test\n"
            f"    public void t() throws Exception {{\n        {body}\n    }}\n}}\n")


@pytest.mark.skipif(not _java_available(), reason="needs a JDK and the JUnit jar (run inside WSL)")
def test_t11_toy_fixture_end_to_end(tmp_path):
    from triage.execution import _javac
    from triage_dep import levels, wdp
    work = tmp_path / "b"
    (work / "src" / "toy").mkdir(parents=True)
    (work / "src" / "toy" / "Calc.java").write_text(PROGRAM, encoding="utf-8")
    (work / "classes").mkdir()
    import subprocess
    subprocess.run(["javac", "-d", str(work / "classes"), str(work / "src" / "toy" / "Calc.java")], check=True)
    meta = {"workdir": str(work), "cp.test": str(work / "classes"), "dir.src.classes": "src"}
    probe = wdp.WdpProbe("TOY::toy.Calc::add(int,int)", "Toy_1", "src/toy/Calc.java", METHOD, meta=meta)
    try:
        assert probe.exclusion is None
        assert probe.return_type == "int"
        assert [v["id"] for v in probe.variants] == ["X-THROW", "X-RET-1", "X-RET-2"]
        assert all(v["compiled"] for v in probe.variants)
        for cls, (body, want_level, want_reason, want_entered) in TESTS.items():
            src = _test_source(cls, body)
            tdir = tmp_path / "stored" / cls
            assert not _javac(src, "toy", cls, meta, tdir)
            stored = wdp.run_test_env(f"toy.{cls}", "t", f"{tdir / 'classes'}", meta, timeout=30)
            assert stored["outcome"] != "pass"
            rec = probe.probe({"instance_id": cls, "method": "t"}, src, "toy", cls, stored)
            assert rec["excluded"] is None, (cls, rec)
            assert rec["entered"] is want_entered, (cls, rec)
            if rec["surfaced"]:
                assert rec["entered"] is True                          # marker consistency
            silent = {"excluded": None, "coupled": False}      # spec v4: the toy has no first-order run;
            assert levels.level(rec, silent) == (want_level, want_reason), (cls, rec)   # a SILENT one is supplied
        assert rec["surfaced"] is True                                 # TE: the probe's own Error reached the runner
    finally:
        probe.cleanup()
    assert not probe.dir.exists()


# ---- T12 marker consistency on the engineering run --------------------------------------------------------------
@pytest.mark.skipif(not DEV_LEDGER.exists(), reason="WDP_D1_DEV has not been run")
def test_t12_marker_consistency_on_the_dev_run():
    spec = importlib.util.spec_from_file_location("wdp_analysis_t12", ROOT / "scripts/extension/wdp_analysis.py")
    an = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(an)
    dev_ids = [r["instance_id"] for r in _read_jsonl(ROOT / "data/processed/instances_D1.jsonl") if r["split"] == "dev"]
    chk = an.raw_ledger_check(DEV_LEDGER, dev_ids)                      # every raw record, no label read
    assert chk["passes"] and chk["records"] == chk["instances"] == 118, chk
    assert chk["surfaced"] > 0 and chk["marker_violations"] == []
    recs = _read_jsonl(DEV_LEDGER)
    assert len(recs) == 118
    surfaced = [r for r in recs if r.get("surfaced") is True]
    violations = [r["instance_id"] for r in surfaced if r.get("entered") is not True]
    assert not violations, violations
    assert surfaced, "no record has surfaced = true: the check is vacuous (stop condition 3)"


# ---- T13 re-run of 30 seeded dev instances ------------------------------------------------------------------------
@pytest.mark.skipif(os.environ.get("WDP_RUN_T13") != "1" or not DEV_LEDGER.exists() or not _java_available(),
                    reason="opt-in (WDP_RUN_T13=1), needs WDP_D1_DEV and the Defects4J checkouts (WSL)")
def test_t13_seeded_rerun_reproduces_levels():
    from triage_dep import levels
    spec = importlib.util.spec_from_file_location("run_wdp_tranche", ROOT / "scripts/extension/run_wdp_tranche.py")
    drv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(drv)
    insts = [r for r in _read_jsonl(ROOT / "data/processed/instances_D1.jsonl") if r["split"] == "dev"]
    frame = {r["focal_id"]: r for r in _read_jsonl(ROOT / "data/processed/frame_d1.jsonl")}
    ids = random.Random(SEED).sample(sorted(r["instance_id"] for r in insts), 30)
    chosen = [r for r in insts if r["instance_id"] in set(ids)]
    by_focal = defaultdict(list)
    for r in chosen:
        by_focal[r["focal_id"]].append(r)
    orig = {r["instance_id"]: r for r in _read_jsonl(DEV_LEDGER)}
    fo = {r["instance_id"]: r["summary"] for r in _read_jsonl(FO_DEV_LEDGER)}
    exec_dir, cand_dir = ROOT / "data/raw/executions_gemma4_26b", ROOT / "data/interim/candidates_gemma4_26b"
    diffs = []
    for fid in sorted(by_focal):
        for rec in drv.probe_focal(fid, by_focal[fid], frame, exec_dir, cand_dir):
            i = rec["instance_id"]
            a, b = levels.level(orig[i], fo.get(i)), levels.level(rec, fo.get(i))
            if a != b:
                diffs.append((i, a, b))
    out = ROOT / "results" / "extension" / "wdp" / "WDP_D1_DEV" / "t13_rerun.json"
    out.write_text(json.dumps({"seed": SEED, "instances": sorted(ids), "differences": diffs}, indent=1),
                   encoding="utf-8", newline="\n")
    assert len(chosen) == 30 and not diffs, diffs
