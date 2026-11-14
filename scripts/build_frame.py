"""Stage 3a — reconstruct the D1 frame, apply the 25/project cap and the 3/14 project split (run in WSL).

    wsl -d Ubuntu-22.04 -- bash scripts/wsl/run.sh scripts/build_frame.py --workers 8

Outputs
  data/interim/frame_candidates.jsonl   every candidate focal method with its keep/exclude reasons
  data/processed/frame_d1.jsonl         the capped, split frame
  data/processed/split_manifest.json    dev/test projects, seeds, counts
  data/interim/context/<focal>.json     B-side context for each frame method (C3)
  data/ground_truth_store/fixed_bodies.jsonl  fixed bodies (label side; leakage audit only)
"""
import argparse
import json
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from triage import config, frame  # noqa: E402
from triage.io_utils import append_jsonl, dump_json, read_jsonl, sha256_text, write_jsonl  # noqa: E402


def _screen(bug_name):
    try:
        return bug_name, frame.screen_bug(bug_name), None
    except Exception as e:  # recorded, never silently dropped
        return bug_name, [], f"{type(e).__name__}: {e}\n{traceback.format_exc()[-800:]}"


def _context(rec):
    info = json.loads((frame.FIX_INFO / rec["bug_name"] / "buggy_fix_info.json").read_text())
    try:
        return rec, frame.extract_context(rec, info), None
    except Exception as e:
        return rec, None, f"{type(e).__name__}: {e}\n{traceback.format_exc()[-800:]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--projects", nargs="*", default=config.D4J_PROJECTS)
    ap.add_argument("--skip-context", action="store_true")
    a = ap.parse_args()

    cand_path = config.INTERIM / "frame_candidates.jsonl"
    err_path = config.INTERIM / "frame_errors.jsonl"
    done = {r["bug_name"] for r in read_jsonl(cand_path)} | {r["bug_name"] for r in read_jsonl(err_path)}
    todo = []
    for p in a.projects:
        for b in frame.active_bugs(p):
            name = f"{p}_{b}"
            if (frame.FIX_INFO / name / "buggy_fix_info.json").exists() and name not in done:
                todo.append(name)
    no_info = [f"{p}_{b}" for p in a.projects for b in frame.active_bugs(p)
               if not (frame.FIX_INFO / f"{p}_{b}" / "buggy_fix_info.json").exists()]
    print(f"screening {len(todo)} bugs ({len(done)} already done; {len(no_info)} active bugs lack fix info)")
    t0 = time.time()
    with ProcessPoolExecutor(a.workers) as ex:
        futs = [ex.submit(_screen, b) for b in todo]
        for i, f in enumerate(as_completed(futs), 1):
            name, recs, err = f.result()
            if err:
                append_jsonl(err_path, {"bug_name": name, "error": err})
            elif not recs:
                append_jsonl(cand_path, {"bug_name": name, "no_candidates": True})
            for r in recs:
                append_jsonl(cand_path, r)
            if i % 25 == 0:
                print(f"  {i}/{len(todo)}  {time.time() - t0:.0f}s", flush=True)

    cands = [r for r in read_jsonl(cand_path) if not r.get("no_candidates")]
    in_frame = [r for r in cands if r["in_frame"]]
    sampled, split = frame.apply_cap_and_split(in_frame)
    write_jsonl(config.PROCESSED / "frame_d1.jsonl", sampled)
    summary = {
        **split, "active_bugs_without_fix_info": no_info,
        "candidates": len(cands), "frame_methods": len(in_frame),
        "frame_bugs": len({r["bug_name"] for r in in_frame}),
        "reference_frame_zhao": {"methods": 318, "bugs": 233},
        "sampled_methods": len(sampled), "sampled_bugs": len({r["bug_name"] for r in sampled}),
        "per_project": {p: {"frame": sum(r["project"] == p for r in in_frame),
                            "sampled": sum(r["project"] == p for r in sampled),
                            "split": "dev" if p in split["dev_projects"] else "test"} for p in config.D4J_PROJECTS},
        "screen_errors": sum(1 for _ in read_jsonl(err_path)),
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    dump_json(config.PROCESSED / "split_manifest.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "per_project"}, indent=1))

    if a.skip_context:
        return
    ctx_dir = config.INTERIM / "context"
    todo = [r for r in sampled if not (ctx_dir / f"{sha256_text(r['focal_id'])[:16]}.json").exists()]
    print(f"extracting context for {len(todo)} focal methods")
    with ProcessPoolExecutor(a.workers) as ex:
        for f in as_completed([ex.submit(_context, r) for r in todo]):
            rec, ctx, err = f.result()
            if err:
                append_jsonl(config.INTERIM / "context_errors.jsonl", {"focal_id": rec["focal_id"], "error": err})
                continue
            label_side = ctx.pop("_label_side")
            append_jsonl(config.GT_STORE / "fixed_bodies.jsonl", {"focal_id": rec["focal_id"], **label_side})
            dump_json(ctx_dir / f"{sha256_text(rec['focal_id'])[:16]}.json", {**ctx, "split": rec["split"],
                                                                             "project": rec["project"],
                                                                             "bug_name": rec["bug_name"]})
    print("done", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
