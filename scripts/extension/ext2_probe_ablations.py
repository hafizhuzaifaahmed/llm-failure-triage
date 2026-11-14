"""EXT-2 (D-136; exploratory): mechanism ablations recomputed from a CFP ledger. Zero executions, zero model calls.

    python scripts/extension/ext2_probe_ablations.py --run CFP_D1_TEST --split test
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage.io_utils import read_jsonl  # noqa: E402
from triage_ext import ledger as lg  # noqa: E402

OPS = ("ROR", "AOR", "COR", "LVR", "NEG", "STD")


def rates(ids, y, flag):
    v = np.array([1.0 if flag[i] else 0.0 for i in ids])
    pf, tf = v[y == 1], v[y == 0]
    return {"PF": [int(pf.sum()), int(len(pf))], "TF": [int(tf.sum()), int(len(tf))],
            "rate_PF": round(float(pf.mean()), 3) if len(pf) else None,
            "rate_TF": round(float(tf.mean()), 3) if len(tf) else None}


def auroc(score, y):
    pos, neg = score[y == 1], score[y == 0]
    if not len(pos) or not len(neg):
        return None
    return round(float(((pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum())
                       / (len(pos) * len(neg))), 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--split", required=True, choices=["dev", "test"])
    a = ap.parse_args()
    led = {r["instance_id"]: r for r in read_jsonl(ROOT / "results" / "extension" / "probes" / a.run / "ledger.jsonl")}
    labels = {l["instance_id"]: l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl") if l["split"] == a.split}
    inst = {r["instance_id"]: r for r in read_jsonl(config.PROCESSED / "instances_D1.jsonl") if r["split"] == a.split}
    ids = [i for i, l in labels.items() if l["label"] in ("PF", "TF") and i in led and not led[i]["summary"].get("excluded")]
    y = np.array([1 if labels[i]["label"] == "PF" else 0 for i in ids])
    out = {"decision": "D-136", "run": a.run, "split": a.split, "instances": len(ids), "PF": int(y.sum())}

    # (a) scope
    out["scope"] = {}
    for name, key in (("focal_plus_callees", "summary"), ("focal_body_only", "summary_focal_only")):
        out["scope"][name] = {f: rates(ids, y, {i: led[i][key][f] for i in ids})
                              for f in ("flip", "rcf", "decoupled", "coupled")}
        out["scope"][name]["usable_10plus"] = int(sum(1 for i in ids if led[i][key]["n_compiled"] >= lg.MIN_MUTANTS))

    # (b) sibling filter
    flips = [m for i in ids for m in led[i]["mutants"] if m["class"] == lg.FLIP]
    out["sibling_filter"] = {"flip_mutant_runs": len(flips),
                             "regression_consistent": sum(1 for m in flips if m.get("rc")),
                             "vacuous": sum(1 for m in flips if m.get("rc_vacuous"))}

    # (c) operators
    def flip_with(keep):
        return {i: any(m["class"] == lg.FLIP and m["operator"] in keep for m in led[i]["mutants"]) for i in ids}

    out["operators"] = {"all": rates(ids, y, flip_with(set(OPS)))}
    for op in OPS:
        out["operators"][f"without_{op}"] = rates(ids, y, flip_with(set(OPS) - {op}))
        out["operators"][f"only_{op}"] = rates(ids, y, flip_with({op}))

    # (d) failure type
    out["failure_type"] = {}
    for ft in ("assertion_failure", "exception"):
        sel = np.array([inst[i]["covariates"]["failure_type"] == ft for i in ids])
        sub = [i for i, s in zip(ids, sel) if s]
        ys = y[sel]
        ff = [led[i]["summary"]["flip_fraction"] for i in sub]
        ok = np.array([f is not None for f in ff], dtype=bool)
        out["failure_type"][ft] = {
            "flip": rates(sub, ys, {i: led[i]["summary"]["flip"] for i in sub}),
            "decoupled": rates(sub, ys, {i: led[i]["summary"]["decoupled"] for i in sub}),
            "auroc_flip_fraction": auroc(np.array([f for f in ff if f is not None], dtype=float), ys[ok]) if ok.any() else None}
    ft_score = np.array([1.0 if inst[i]["covariates"]["failure_type"] == "exception" else 0.0 for i in ids])
    out["auroc_failure_type_alone"] = auroc(ft_score, y)

    # (e) bug level
    by_bug = defaultdict(lambda: {"pf": 0, "pf_flip": 0, "tf": 0, "tf_flip": 0})
    for i, yy in zip(ids, y):
        b = by_bug[labels[i]["bug_name"]]
        fl = led[i]["summary"]["flip"]
        if yy:
            b["pf"] += 1
            b["pf_flip"] += int(fl)
        else:
            b["tf"] += 1
            b["tf_flip"] += int(fl)
    pf_bugs = [b for b in by_bug.values() if b["pf"]]
    tf_only = [b for b in by_bug.values() if not b["pf"]]
    out["bug_level"] = {"bugs_with_PF": len(pf_bugs),
                        "of_which_some_PF_test_flips": sum(1 for b in pf_bugs if b["pf_flip"]),
                        "TF_only_bugs": len(tf_only), "of_which_any_flip": sum(1 for b in tf_only if b["tf_flip"])}

    # (f) shared flips
    flipped_by = defaultdict(set)
    for i in ids:
        for m in led[i]["mutants"]:
            if m["class"] == lg.FLIP:
                flipped_by[(led[i]["focal_id"], m["mid"])].add(i)
    shared = {i: any(len(flipped_by[(led[i]["focal_id"], m["mid"])]) >= 2
                     for m in led[i]["mutants"] if m["class"] == lg.FLIP) for i in ids}
    out["shared_flip"] = rates(ids, y, shared)

    # (g) cost
    secs = np.array([r["seconds"] for r in led.values()])
    out["cost"] = {"instances": int(len(secs)), "seconds_total": round(float(secs.sum()), 1),
                   "seconds_median": round(float(np.median(secs)), 2),
                   "seconds_p90": round(float(np.percentile(secs, 90)), 2),
                   "note": "per-instance probe time; focal-method mutant compilation is in the run log"}
    dest = ROOT / "results" / "extension" / f"ext2_probe_ablations_{a.run}.json"
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
