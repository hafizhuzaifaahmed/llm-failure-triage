"""D2 seeded faults for held-out focal methods (run in WSL, no LLM, no cost).

    wsl -d Ubuntu-22.04 -- bash scripts/wsl/run.sh scripts/build_d2.py --workers 4 [--limit N] [--bugs Lang_1 ...]

Output: data/processed/d2_mutants.jsonl (one record per focal method: counts, kill statuses, every attempted
mutant with its verdict, and the verified mutants with their exact source edit and mutated focal body).
"""
import argparse
import json
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from triage import config, frame, mutants  # noqa: E402
from triage.io_utils import append_jsonl, read_jsonl  # noqa: E402

OUT = config.PROCESSED / "d2_mutants.jsonl"


def _bug_job(recs):
    """All focal methods of ONE bug, sequentially: they share the bug's F checkout, which must never be
    prepared by two processes at once (a race corrupted a Closure build in the first full run)."""
    out = []
    for rec in recs:
        info = json.loads((frame.FIX_INFO / rec["bug_name"] / "buggy_fix_info.json").read_text())
        t0 = time.time()
        try:
            r = mutants.build_for_focal(rec, None, info)
        except Exception as e:
            r = {"focal_id": rec["focal_id"], "status": "ERROR", "error": f"{type(e).__name__}: {e}",
                 "trace": traceback.format_exc()[-800:]}
        r["wall_s"] = round(time.time() - t0, 1)
        out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--bugs", nargs="*")
    a = ap.parse_args()
    done = {r["focal_id"] for r in read_jsonl(OUT)}
    frame_rows = [r for r in read_jsonl(config.PROCESSED / "frame_d1.jsonl") if r["split"] == "test"]
    todo = [r for r in frame_rows if r["focal_id"] not in done and (not a.bugs or r["bug_name"] in a.bugs)]
    todo = todo[: a.limit] if a.limit else todo
    groups = {}
    for r in todo:
        groups.setdefault(r["bug_name"], []).append(r)
    print(f"{len(todo)} held-out focal methods in {len(groups)} bugs to process ({len(done)} done)", flush=True)
    i = 0
    with ProcessPoolExecutor(a.workers) as ex:
        for f in as_completed([ex.submit(_bug_job, g) for g in groups.values()]):
            for r in f.result():
                i += 1
                append_jsonl(OUT, r)
                print(f"  {i}/{len(todo)} {r['focal_id'][:70]} -> {r['status']} "
                      f"({len(r.get('chosen', []))} verified, {r.get('wall_s')}s)", flush=True)


if __name__ == "__main__":
    main()
