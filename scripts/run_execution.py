"""Stages C5-C7 — compile and dual-execute candidate tests (WSL side, stdlib only).

    wsl -d Ubuntu-22.04 -- bash scripts/wsl/run.sh scripts/run_execution.py --workers 6
Raw records are written once to data/raw/executions/<candidate_id>.json and never overwritten.
"""
import argparse
import json
import sys
import time
import traceback
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from triage import config, execution, scope  # noqa: E402
from triage.io_utils import append_jsonl, write_immutable  # noqa: E402
from triage.llm import STOP_FILE  # noqa: E402


def _bug_job(project, bug, cands):
    out = []
    try:
        mb = execution.prepare_version(project, bug, "b")
        mf = execution.prepare_version(project, bug, "f")
    except Exception as e:
        return [(c["candidate_id"], None, f"prepare failed: {e}") for c in cands]
    for c in cands:
        try:
            rec = execution.execute_candidate(c, mb, mf)
            rec["focal_id"] = c["focal_id"]
            rec["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            out.append((c["candidate_id"], rec, None))
        except Exception as e:
            out.append((c["candidate_id"], None, f"{type(e).__name__}: {e}\n{traceback.format_exc()[-800:]}"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--candidates", default=str(config.INTERIM / "candidates"))
    ap.add_argument("--out", default=str(config.RAW / "executions"))
    a = ap.parse_args()
    out = Path(a.out)
    groups = defaultdict(list)
    for p in sorted(Path(a.candidates).glob("*.json")):
        c = json.loads(p.read_text())
        if not c.get("assembled") or (out / f"{c['candidate_id']}.json").exists():
            continue
        proj, bug = c["focal_id"].split("::")[0].rsplit("_", 1)
        groups[(proj, bug)].append(c)
    # held-out lock in code: refuse to execute anything outside the local scope's splits
    scope.check_focal_ids_local([c["focal_id"] for cs in groups.values() for c in cs], "execution")
    print(f"{sum(map(len, groups.values()))} candidates over {len(groups)} bugs", flush=True)
    execution.ensure_runner()
    with ProcessPoolExecutor(a.workers) as ex:
        futs = [ex.submit(_bug_job, p, b, cs) for (p, b), cs in sorted(groups.items())]
        for i, f in enumerate(as_completed(futs), 1):
            if f.cancelled():
                continue
            for cid, rec, err in f.result():
                if err:
                    append_jsonl(out.parent / "execution_errors.jsonl", {"candidate_id": cid, "error": err})
                else:
                    write_immutable(out / f"{cid}.json", json.dumps(rec, indent=1, sort_keys=True))
            print(f"  bugs {i}/{len(futs)}", flush=True)
            if STOP_FILE.exists():   # D-58: let running bug jobs finish, start no new one; re-run resumes
                print("STOPPED ON REQUEST (D-58): stop file present; finishing running bug jobs", flush=True)
                for f2 in futs:
                    f2.cancel()


if __name__ == "__main__":
    main()
