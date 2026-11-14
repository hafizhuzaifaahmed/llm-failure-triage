"""Re-execute named stored D1 test classes alone (one worker) and report their labels (D-142 validation follow-up).

    wsl -d Ubuntu-22.04 -- bash scripts/wsl/run.sh scripts/extension/validate_timing_cases.py <candidate_id> ...

Used only to check whether a label difference in the full re-execution comes from wall-clock load. Writes under
results/extension/validation/exec_D1_alone/ and compares with the stored records; no confirmation data.
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import confirm_lib as L  # noqa: E402
from triage import labeling  # noqa: E402

ROOT = L.ROOT
D1_CANDS = ROOT / "data" / "interim" / "candidates_gemma4_26b"
D1_EXECS = ROOT / "data" / "raw" / "executions_gemma4_26b"
OUT = ROOT / "results" / "extension" / "validation" / "exec_D1_alone"


def main(ids):
    cands = OUT / "candidates"
    execs = OUT / "executions"
    if OUT.exists():
        shutil.rmtree(OUT)
    cands.mkdir(parents=True)
    for cid in ids:
        shutil.copy2(D1_CANDS / f"{cid}.json", cands / f"{cid}.json")
    run = L.execute(cands, execs, workers=1)
    rep = {"run": run, "cases": []}
    for cid in ids:
        new = json.loads((execs / f"{cid}.json").read_text())
        old = json.loads((D1_EXECS / f"{cid}.json").read_text())
        om = {m["method"]: m for m in old["methods"]}
        for m in new["methods"]:
            o = om[m["method"]]
            rep["cases"].append({"candidate_id": cid, "method": m["method"], "stored": labeling.label(o)["label"],
                                 "alone": labeling.label(m)["label"],
                                 "stored_f_seconds": [r.get("duration_s") for r in o.get("runs_f") or []],
                                 "alone_f_seconds": [r.get("duration_s") for r in m.get("runs_f") or []]})
    rep["label_mismatches"] = sum(1 for c in rep["cases"] if c["stored"] != c["alone"])
    (ROOT / "results" / "extension" / "validation" / "validate_execution_timing_cases.json").write_text(
        json.dumps(rep, indent=1), encoding="utf-8", newline="\n")
    shutil.rmtree(OUT)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
