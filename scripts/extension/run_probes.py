"""Run counterfactual program probes (D-134) for the failing instances of one split. WSL entry point.

    wsl -d Ubuntu-22.04 -- bash scripts/wsl/run.sh scripts/extension/run_probes.py --split dev --run CFP_D1_DEV

Reads, per instance: the instance record (test, focal id, focal body), the frame's focal file, the candidate's
package and class, and the stored buggy-version runs of the candidate's methods. The execution record is reduced to
an allow-list of fields the moment it is loaded. Appends one ledger record per instance to
results/extension/probes/<run>/ledger.jsonl and can be resumed.
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
EXEC_DIR = ROOT / "data" / "raw" / "executions_gemma4_26b"
CAND_DIR = ROOT / "data" / "interim" / "candidates_gemma4_26b"


def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_execution(candidate_id):
    """Buggy-version view of one execution record: allow-listed fields only."""
    raw = json.loads((EXEC_DIR / f"{candidate_id}.json").read_text(encoding="utf-8"))
    return {"focal_id": raw["focal_id"],
            "methods": [{k: m.get(k) for k in ALLOWED_METHOD_FIELDS} for m in raw["methods"]]}


def passing_siblings(focal_ids):
    """focal_id -> tests of that focal method that compiled and passed on every stored buggy-version run."""
    out = defaultdict(list)
    for f in sorted(EXEC_DIR.glob("*.json")):
        cid = f.stem
        ex = load_execution(cid)
        if ex["focal_id"] not in focal_ids:
            continue
        cand = json.loads((CAND_DIR / f"{cid}.json").read_text(encoding="utf-8"))
        for m in ex["methods"]:
            runs = m.get("runs_b") or []
            if m.get("compile_b") and runs and all(r.get("outcome") == "pass" for r in runs):
                out[ex["focal_id"]].append({"package": cand["package"], "class_name": cand["class_name"],
                                            "method": m["method"], "source_class": m["source_class"]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["dev", "test"])
    ap.add_argument("--run", required=True)
    ap.add_argument("--limit-focal", type=int, default=None, help="engineering smoke test only")
    a = ap.parse_args()
    out_dir = ROOT / "results" / "extension" / "probes" / a.run
    out_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = out_dir / "ledger.jsonl"
    done = {r["instance_id"] for r in read_jsonl(ledger_path)} if ledger_path.exists() else set()

    insts = [r for r in read_jsonl(ROOT / "data" / "processed" / "instances_D1.jsonl") if r["split"] == a.split]
    frame = {r["focal_id"]: r for r in read_jsonl(ROOT / "data" / "processed" / "frame_d1.jsonl")}
    by_focal = defaultdict(list)
    for r in insts:
        by_focal[r["focal_id"]].append(r)
    focal_ids = sorted(by_focal)[: a.limit_focal] if a.limit_focal else sorted(by_focal)
    siblings = passing_siblings(set(focal_ids))
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = None
    (out_dir / "run_meta.json").write_text(json.dumps({
        "decision": "D-134, D-135", "callee_depth": probe.CALLEE_DEPTH, "run": a.run, "dataset": "D1", "split": a.split, "commit": commit,
        "utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "focal_methods": len(focal_ids),
        "instances": sum(len(by_focal[f]) for f in focal_ids), "max_mutants": mutate.MAX_MUTANTS,
        "probe_timeout_s": probe.PROBE_TIMEOUT_S, "max_siblings": probe.MAX_SIBLINGS, "workers": probe.WORKERS,
        "operators": ["ROR", "AOR", "COR", "LVR", "NEG", "STD"], "limit_focal": a.limit_focal}, indent=1))

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
                ex = load_execution(r["candidate_id"])
                m = next(x for x in ex["methods"] if x["method"] == r["method"])
                cand = json.loads((CAND_DIR / f"{r['candidate_id']}.json").read_text(encoding="utf-8"))
                stored = dict(m["runs_b"][0])
                rec = fp.probe(r, m["source_class"], cand["package"], cand["class_name"], stored,
                               [s for s in siblings.get(fid, [])])
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
