"""Run whole-method dependence probes (WDP) on one instance set. WSL entry point.

    wsl -d Ubuntu-22.04 -- bash scripts/wsl/run.sh scripts/extension/run_wdp_tranche.py --run WDP_D1_DEV --split dev
        --instances data/processed/instances_D1.jsonl --frame data/processed/frame_d1.jsonl
        --exec-dir data/raw/executions_gemma4_26b --cand-dir data/interim/candidates_gemma4_26b

Mirrors `run_probes_tranche.py`: the same arguments (plus an optional split filter) and the same buggy-version
allow-list of execution fields. Writes results/extension/wdp/<run>/ledger.jsonl and run_meta.json; resumable by
instance id.

Approval gate (OPUS_EXECUTION_BRIEF.md rule 0.8, sections 3.1 and 11.1). Exactly five run names exist, each bound
to its own inputs. Without configs/extension/wdp_run_approval.json only WDP_D1_DEV (dev split) may run. With it,
only WDP_D1_TEST, WDP_CONF_F1, WDP_CONF_F2 and WDP_CONF_CTRL may run, and only if the file names a full commit id
that exists and is an ancestor of HEAD, every frozen hash matches (the check of freeze_wdp.py, imported), and the
working-tree manifest equals the approved commit's manifest. Any failure, an unreadable approval file or git being
unavailable refuses the run before an instance is read or a directory created. The driver never writes the
approval file.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import freeze_wdp as FREEZE  # noqa: E402  (one implementation of the frozen-file check)
from triage_dep import interventions, wdp  # noqa: E402

ALLOWED_METHOD_FIELDS = ("method", "source_class", "compile_b", "runs_b")   # buggy-version side only
APPROVAL = ROOT / "configs" / "extension" / "wdp_run_approval.json"
MANIFEST_REL = "configs/extension/wdp_frozen.json"
ENGINEERING_RUN = "WDP_D1_DEV"
_D1 = {"instances": "data/processed/instances_D1.jsonl", "frame": "data/processed/frame_d1.jsonl",
       "exec_dir": "data/raw/executions_gemma4_26b", "cand_dir": "data/interim/candidates_gemma4_26b"}


def _conf(t):
    return {"instances": f"data/extension/confirm/{t}/instances_D1C_{t}.jsonl",
            "frame": "configs/extension/confirm_frame.jsonl", "exec_dir": f"data/extension/confirm/{t}/executions",
            "cand_dir": f"data/extension/confirm/{t}/candidates", "split": None}


RUNS = {   # brief section 2.1: each run name bound to its inputs
    "WDP_D1_DEV": {**_D1, "split": "dev"},
    "WDP_D1_TEST": {**_D1, "split": "test"},
    "WDP_CONF_F1": _conf("F1"), "WDP_CONF_F2": _conf("F2"), "WDP_CONF_CTRL": _conf("CTRL"),
}
EVALUATION_RUNS = ("WDP_D1_TEST", "WDP_CONF_F1", "WDP_CONF_F2", "WDP_CONF_CTRL")


class Refused(Exception):
    pass


def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _git(*args) -> subprocess.CompletedProcess:
    """git in the repository; a refusal if git cannot be run at all."""
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    except OSError as e:
        raise Refused(f"git unavailable: {e}")


def _same_path(given, bound) -> bool:
    return (ROOT / given).resolve() == (ROOT / bound).resolve()


def authorize(run: str, instances: str, frame: str, exec_dir: str, cand_dir: str, split,
              approval: Path | None = None) -> dict:
    """The gate. Returns the provenance fields for run_meta.json, or raises Refused naming the failed check.

    Reads nothing but the approval file, the manifest and git; creates nothing."""
    approval = APPROVAL if approval is None else approval
    if run not in RUNS:
        raise Refused(f"run {run!r} refused: unknown run name (allowed: {', '.join(RUNS)})")
    b = RUNS[run]
    given = {"instances": instances, "frame": frame, "exec_dir": exec_dir, "cand_dir": cand_dir}
    wrong = [k for k, v in given.items() if not _same_path(v, b[k])]
    if wrong or split != b["split"]:
        raise Refused(f"run {run!r} refused: inputs not those bound to this run name "
                      f"({', '.join(wrong + (['split'] if split != b['split'] else []))})")
    if not approval.exists():
        if run != ENGINEERING_RUN:
            raise Refused(f"run {run!r} refused: only {ENGINEERING_RUN} may run before the authors approve the "
                          f"freeze commit (approval file {approval.name} is absent)")
        head = _git("rev-parse", "HEAD")
        return {"approved_freeze_commit": None, "execution_commit": head.stdout.strip() or None,
                "frozen_check": "not required (engineering run before approval)",
                "worktree_dirty_paths": _git("status", "--porcelain").stdout.splitlines()}
    if run == ENGINEERING_RUN:
        raise Refused(f"run {run!r} refused: the engineering run is closed once an approval file exists")
    try:
        doc = json.loads(approval.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Refused(f"run {run!r} refused: approval file unreadable or not JSON ({e})")
    cid = doc.get("freeze_commit") if isinstance(doc, dict) else None
    if not isinstance(cid, str) or not re.fullmatch(r"[0-9a-f]{40}", cid):
        raise Refused(f"run {run!r} refused: approval file does not name a full 40-hex freeze commit")
    if _git("cat-file", "-e", f"{cid}^{{commit}}").returncode != 0:
        raise Refused(f"run {run!r} refused: freeze commit {cid} does not exist")
    if _git("merge-base", "--is-ancestor", cid, "HEAD").returncode != 0:
        raise Refused(f"run {run!r} refused: freeze commit {cid} is not an ancestor of HEAD")
    bad = FREEZE.check()
    if bad:
        raise Refused(f"run {run!r} refused: frozen-file check failed: {'; '.join(bad)}")
    shown = _git("show", f"{cid}:{MANIFEST_REL}")
    if shown.returncode != 0:
        raise Refused(f"run {run!r} refused: the freeze commit has no {MANIFEST_REL}")
    here = (ROOT / MANIFEST_REL).read_bytes().replace(b"\r\n", b"\n")
    if here != shown.stdout.replace("\r\n", "\n").encode("utf-8"):
        raise Refused(f"run {run!r} refused: {MANIFEST_REL} differs from the approved commit's manifest")
    head = _git("rev-parse", "HEAD")
    if head.returncode != 0:
        raise Refused(f"run {run!r} refused: cannot read HEAD")
    return {"approved_freeze_commit": cid, "execution_commit": head.stdout.strip(),
            "frozen_check": {"status": "passed", "manifest_sha256": hashlib.sha256(here).hexdigest()},
            "worktree_dirty_paths": _git("status", "--porcelain").stdout.splitlines()}


def load_execution(exec_dir, candidate_id):
    raw = json.loads((exec_dir / f"{candidate_id}.json").read_text(encoding="utf-8"))
    return {"focal_id": raw["focal_id"],
            "methods": [{k: m.get(k) for k in ALLOWED_METHOD_FIELDS} for m in raw["methods"]]}


def probe_focal(fid, todo, frame, exec_dir, cand_dir):
    """Yield one ledger record per instance of `todo` (all instances of focal method `fid`)."""
    first = todo[0]
    wp = wdp.WdpProbe(fid, first["bug_name"], frame[fid]["file"], first["impl"])
    try:
        for r in todo:
            ex = load_execution(exec_dir, r["candidate_id"])
            m = next(x for x in ex["methods"] if x["method"] == r["method"])
            cand = json.loads((cand_dir / f"{r['candidate_id']}.json").read_text(encoding="utf-8"))
            yield wp.probe(r, m["source_class"], cand["package"], cand["class_name"], dict(m["runs_b"][0]))
    finally:
        wp.cleanup()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--instances", required=True)
    ap.add_argument("--frame", required=True)
    ap.add_argument("--exec-dir", required=True)
    ap.add_argument("--cand-dir", required=True)
    ap.add_argument("--split", default=None)
    a = ap.parse_args()
    try:
        prov = authorize(a.run, a.instances, a.frame, a.exec_dir, a.cand_dir, a.split)
    except Refused as e:
        sys.exit(str(e))
    exec_dir, cand_dir = ROOT / a.exec_dir, ROOT / a.cand_dir
    insts = [r for r in read_jsonl(ROOT / a.instances) if a.split is None or r.get("split") == a.split]
    frame = {r["focal_id"]: r for r in read_jsonl(ROOT / a.frame)}
    out_dir = ROOT / "results" / "extension" / "wdp" / a.run
    out_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = out_dir / "ledger.jsonl"
    done = {r["instance_id"] for r in read_jsonl(ledger_path)} if ledger_path.exists() else set()
    by_focal = defaultdict(list)
    for r in insts:
        by_focal[r["focal_id"]].append(r)
    focal_ids = sorted(by_focal)
    meta_path = out_dir / "run_meta.json"
    start = {"utc_start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **prov, "records_before": len(done)}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.setdefault("resumes", []).append(start)
    else:
        meta = {"decision": "D-147, D-148", "status": "exploratory" + ("; engineering run" if a.run == ENGINEERING_RUN
                                                                       else "; retrospective evaluation run"),
                "run": a.run, **prov, "instances_file": a.instances, "split": a.split, "frame_file": a.frame,
                "exec_dir": a.exec_dir, "cand_dir": a.cand_dir, "utc_start": start["utc_start"],
                "focal_methods": len(focal_ids), "instances": len(insts),
                "variant_table_sha256": interventions.variant_table_sha256(),
                "baseline_timeout_s": wdp.BASELINE_TIMEOUT_S, "variant_timeout_s": wdp.VARIANT_TIMEOUT_S,
                "max_variants": interventions.MAX_VARIANTS}
    meta_path.write_text(json.dumps(meta, indent=1), encoding="utf-8", newline="\n")
    t_all = time.time()
    n_written = 0
    with open(ledger_path, "a", encoding="utf-8", newline="\n") as out:
        for n, fid in enumerate(focal_ids, 1):
            todo = [r for r in by_focal[fid] if r["instance_id"] not in done]
            if not todo:
                continue
            t0 = time.time()
            excl = set()
            for rec in probe_focal(fid, todo, frame, exec_dir, cand_dir):
                out.write(json.dumps(rec) + "\n")
                out.flush()
                n_written += 1
                excl.add(rec["excluded"])
            print(f"[{n}/{len(focal_ids)}] {fid[:70]} instances={len(todo)} excl={sorted(map(str, excl))} "
                  f"{time.time() - t0:.0f}s total={time.time() - t_all:.0f}s", flush=True)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.setdefault("completions", []).append({"utc_end": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                               "records_written": n_written,
                                               "wall_seconds": round(time.time() - t_all, 1)})
    meta_path.write_text(json.dumps(meta, indent=1), encoding="utf-8", newline="\n")
    print("done", round(time.time() - t_all), "s")


if __name__ == "__main__":
    main()
