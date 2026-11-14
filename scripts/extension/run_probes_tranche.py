"""Run counterfactual program probes on a sealed tranche (D-138). WSL entry point.

The D-134 driver with its four inputs as arguments, so that a new tranche never touches the original study's files.
It imports the unchanged engine (`src/triage_ext`) and reads the same buggy-version allow-list of fields.

    wsl -d Ubuntu-22.04 -- bash scripts/wsl/run.sh scripts/extension/run_probes_tranche.py --run CFP_CONFIRM
        --instances <instances.jsonl> --frame configs/extension/confirm_frame.jsonl
        --exec-dir <executions dir> --cand-dir <candidates dir>
"""
import argparse
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage_ext import mutate, probe  # noqa: E402

ALLOWED_METHOD_FIELDS = ("method", "source_class", "compile_b", "runs_b")   # buggy-version side only


def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_execution(exec_dir, candidate_id):
    raw = json.loads((exec_dir / f"{candidate_id}.json").read_text(encoding="utf-8"))
    return {"focal_id": raw["focal_id"],
            "methods": [{k: m.get(k) for k in ALLOWED_METHOD_FIELDS} for m in raw["methods"]]}


def passing_siblings(exec_dir, cand_dir, focal_ids):
    out = defaultdict(list)
    for f in sorted(exec_dir.glob("*.json")):
        ex = load_execution(exec_dir, f.stem)
        if ex["focal_id"] not in focal_ids:
            continue
        cand = json.loads((cand_dir / f"{f.stem}.json").read_text(encoding="utf-8"))
        for m in ex["methods"]:
            runs = m.get("runs_b") or []
            if m.get("compile_b") and runs and all(r.get("outcome") == "pass" for r in runs):
                out[ex["focal_id"]].append({"package": cand["package"], "class_name": cand["class_name"],
                                            "method": m["method"], "source_class": m["source_class"]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--instances", required=True)
    ap.add_argument("--frame", required=True)
    ap.add_argument("--exec-dir", required=True)
    ap.add_argument("--cand-dir", required=True)
    a = ap.parse_args()
    exec_dir, cand_dir = Path(a.exec_dir), Path(a.cand_dir)
    out_dir = ROOT / "results" / "extension" / "probes" / a.run
    out_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = out_dir / "ledger.jsonl"
    done = {r["instance_id"] for r in read_jsonl(ledger_path)} if ledger_path.exists() else set()
    insts = read_jsonl(Path(a.instances))
    frame = {r["focal_id"]: r for r in read_jsonl(Path(a.frame))}
    by_focal = defaultdict(list)
    for r in insts:
        by_focal[r["focal_id"]].append(r)
    focal_ids = sorted(by_focal)
    siblings = passing_siblings(exec_dir, cand_dir, set(focal_ids))
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = None
    (out_dir / "run_meta.json").write_text(json.dumps({
        "decision": "D-134, D-135, D-138", "run": a.run, "commit": commit, "instances_file": a.instances,
        "frame_file": a.frame, "exec_dir": a.exec_dir, "cand_dir": a.cand_dir,
        "utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "focal_methods": len(focal_ids),
        "instances": len(insts), "max_mutants": mutate.MAX_MUTANTS, "callee_depth": probe.CALLEE_DEPTH,
        "probe_timeout_s": probe.PROBE_TIMEOUT_S, "max_siblings": probe.MAX_SIBLINGS, "workers": probe.WORKERS,
        "operators": ["ROR", "AOR", "COR", "LVR", "NEG", "STD"]}, indent=1))
    t_all = time.time()
    with open(ledger_path, "a", encoding="utf-8") as out:
        for n, fid in enumerate(focal_ids, 1):
            todo = [r for r in by_focal[fid] if r["instance_id"] not in done]
            if not todo:
                continue
            t0 = time.time()
            first = todo[0]
            fp = probe.FocalProbe(fid, first["bug_name"], frame[fid]["file"], first["impl"], first["focal_class"])
            for r in todo:
                ex = load_execution(exec_dir, r["candidate_id"])
                m = next(x for x in ex["methods"] if x["method"] == r["method"])
                cand = json.loads((cand_dir / f"{r['candidate_id']}.json").read_text(encoding="utf-8"))
                rec = fp.probe(r, m["source_class"], cand["package"], cand["class_name"], dict(m["runs_b"][0]),
                               list(siblings.get(fid, [])))
                rec["n_siblings_available"] = len(siblings.get(fid, []))
                out.write(json.dumps(rec) + "\n")
                out.flush()
            fp.cleanup()
            print(f"[{n}/{len(focal_ids)}] {fid[:70]} instances={len(todo)} compiled={len(fp.overlays)}/"
                  f"{len(fp.mutants)} excl={fp.exclusion} {time.time() - t0:.0f}s total={time.time() - t_all:.0f}s",
                  flush=True)
    print("done", round(time.time() - t_all), "s")


if __name__ == "__main__":
    main()
