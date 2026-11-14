"""G-selection criterion 3 (reported, not gating under D-22): focal-method line/branch coverage on F of the
passing generated tests, per candidate class. Runs in WSL (Defects4J). Dev split only.

    wsl -d Ubuntu-22.04 -- bash scripts/wsl/run.sh scripts/local/dev_coverage.py --model gemma4:26b
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from triage import config, execution, frame, javasrc, labeling  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402


def slug(m):
    return m.replace("/", "__").replace(":", "_")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    a = ap.parse_args()
    sl = slug(a.model)
    fr = {r["focal_id"]: r for r in read_jsonl(config.PROCESSED / "frame_d1.jsonl")}
    rows = []
    for cp in sorted((config.INTERIM / f"candidates_{sl}").glob("*.json")):
        c = json.loads(cp.read_text())
        ep = config.RAW / f"executions_{sl}" / f"{c['candidate_id']}.json"
        rec = fr.get(c["focal_id"])
        if not ep.exists() or not rec or rec["split"] != "dev":
            continue
        ex = json.loads(ep.read_text())
        passing = [m["method"] for m in ex["methods"] if labeling.label(m)["label"] in ("PF", "PASS")]
        if not passing:
            continue
        src = javasrc.remove_members(ex.get("final_source") or c["source"],
                                     {m.name for m in javasrc.test_methods(c["source"])} - set(passing))
        meta_f = execution.prepare_version(rec["project"], rec["bug"], "f")
        f_src = (Path(meta_f["workdir"]) / rec["file"]).read_text(errors="replace")
        m = frame.locate_method(f_src, frame.parse_qualified(rec["qualified"]))
        if m is None:
            continue
        lo, hi = f_src.count("\n", 0, m.start) + 1, f_src.count("\n", 0, m.end) + 1
        cov = execution.focal_coverage(meta_f, src, c["package"], c["class_name"],
                                       rec["class"].split("$")[0], rec["file"], lo, hi, c["candidate_id"])
        rows.append({"candidate_id": c["candidate_id"], "focal_id": c["focal_id"], "passing_methods": len(passing), **cov})
        print(c["candidate_id"], cov.get("status"), cov.get("line_rate"), cov.get("branch_rate"), flush=True)
    ok = [r for r in rows if r.get("status") == "ok"]
    summ = {"classes_measured": len(ok), "classes_failed": len(rows) - len(ok),
            "mean_line_rate": statistics.mean(r["line_rate"] for r in ok if r["line_rate"] is not None) if ok else None,
            "mean_branch_rate": statistics.mean(r["branch_rate"] for r in ok if r["branch_rate"] is not None)
            if any(r["branch_rate"] is not None for r in ok) else None}
    dump_json(config.ROOT / "results" / "dev" / f"coverage_{sl}.json", {"model": a.model, "rows": rows, "summary": summ})
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
