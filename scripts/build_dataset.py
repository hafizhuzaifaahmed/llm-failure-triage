"""Stages C8-C9 — label, preprocess, de-duplicate and sample. Windows side.

    python scripts/build_dataset.py --dataset D1
"""
import argparse
import json
from pathlib import Path

from _common import config, load_contexts
from triage import dataset, scope
from triage.io_utils import dump_json, read_jsonl


PRIMARY_MODE = {"dev": "per_project", "test": "proportional"}   # X-07, D-53


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="D1")
    ap.add_argument("--candidates", default=str(config.INTERIM / "candidates"))
    ap.add_argument("--executions", default=str(config.RAW / "executions"))
    ap.add_argument("--splits", default="dev,test")
    a = ap.parse_args()
    splits = a.splits.split(",")
    sc = scope.load(scope.LOCAL_SCOPE_FILE)          # held-out lock: under the local scope only its splits
    if sc is not None:
        for s in splits:
            sc.check_split(s, "(dataset build)")
        sc.check_dataset(a.dataset, "(dataset build)")
    cands = {}
    for p in Path(a.candidates).glob("*.json"):
        c = json.loads(p.read_text())
        cands[c["candidate_id"]] = c
    execs = [json.loads(p.read_text()) for p in sorted(Path(a.executions).glob("*.json"))]
    ctxs = {k: v for k, v in load_contexts().items() if v["split"] in splits}
    if sc is not None:
        scope.check_focal_ids_local([e["focal_id"] for e in execs], "dataset build")
    fixed = {r["focal_id"]: r.get("fixed_body") for r in read_jsonl(config.GT_STORE / "fixed_bodies.jsonl")}
    counts = dataset.build(a.dataset, execs, cands, ctxs, fixed)
    # X-07 decided (D-53): D1-test uses the overall/proportional reading (1:2 over the split, TF draw stratified
    # by project); dev keeps the within-project reading its pilot was run on (selection only). The other reading
    # is written for each split as a named alternative so the choice can be scored side by side.
    samp = {s: dataset.sample(a.dataset, s, mode=PRIMARY_MODE[s]) for s in splits}
    for s in splits:
        alt = "per_project" if PRIMARY_MODE[s] == "proportional" else "proportional"
        samp[f"{s}_alternative_{alt}"] = dataset.sample(a.dataset, s, mode=alt, suffix=f"_alternative_{alt}")
    samp["dev_pilot"] = dataset.sample(a.dataset, "dev", mode="per_project", cap=150, suffix="_pilot")
    counts["sample"] = {s: {"n": len(v["instance_ids"]), "capped": v["capped"], "projects_dropped": v["projects_dropped"],
                            "per_project": v["per_project"]} for s, v in samp.items()}
    dump_json(config.PROCESSED / f"dataset_summary_{a.dataset}.json", counts)
    print(json.dumps({k: counts[k] for k in ("labels", "exclusions", "executed_methods")}, indent=1))


if __name__ == "__main__":
    main()
