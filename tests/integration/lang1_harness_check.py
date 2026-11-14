"""Integration check of execution + labelling on real Defects4J Lang-1 B/F (run inside WSL, stdlib only).

    python3 tests/integration/lang1_harness_check.py

Uses the hand-written fixture tests/fixtures/lang1/HarnessFixtureTest.java. Output goes to
tests/integration/output/ — it is pipeline-validation evidence, never research data.
"""
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import execution, labeling  # noqa: E402

EXPECTED = {"expectPF": "PF", "expectTF": "TF", "expectPass": "PASS", "expectMisguided": "MISGUIDED",
            "expectAmb": "AMB", "expectTimeout": "TIMEOUT", "expectFlaky": "FLAKY"}


def main():
    for f in Path(tempfile.gettempdir()).glob("triage-fixture-*"):
        f.unlink()
    t0 = time.time()
    mb = execution.prepare_version("Lang", "1", "b")
    mf = execution.prepare_version("Lang", "1", "f")
    src = (ROOT / "tests/fixtures/lang1/HarnessFixtureTest.java").read_text()
    rec = execution.execute_candidate({"candidate_id": "fixture-lang1", "package": "org.apache.commons.lang3.math",
                                       "class_name": "HarnessFixtureTest", "source": src}, mb, mf)
    results, ok = {}, True
    for m in rec["methods"]:
        lab = labeling.label(m)
        results[m["method"]] = lab
        exp = EXPECTED.get(m["method"])
        status = "OK " if lab["label"] == exp else "BAD"
        ok &= lab["label"] == exp
        print(f"{status} {m['method']:16s} expected={exp:9s} got={lab['label']:9s} sigma_B={lab.get('sigma_B')} sigma_F={lab.get('sigma_F')}")
    nc = rec["compilation"]["nc_both"]
    print(f"{'OK ' if nc == ['expectNC'] else 'BAD'} pruned non-compiling: {nc}")
    ok &= nc == ["expectNC"]
    out = ROOT / "tests/integration/output"
    out.mkdir(parents=True, exist_ok=True)
    (out / "lang1_harness_check.json").write_text(json.dumps({"labels": results, "execution": rec,
                                                               "wall_s": round(time.time() - t0, 1),
                                                               "passed": bool(ok)}, indent=2))
    print(f"wall {time.time() - t0:.1f}s ->", "PASSED" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
