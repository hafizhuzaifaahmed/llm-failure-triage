"""WP1.7 (D-118; exploratory; zero calls): cross-generation consensus as a buggy-version-only PF signal.

For an instance i (focal method f, generation g), another generation g' != g of f *agrees* when one of its test methods
compiled on P_B and failed deterministically on all three P_B runs with the same outcome type and exception class as i,
and either (assertion failures with parsed values) the same expected and actual values, or (exceptions) the same top
project frame below the test. Only `compile_b` and `runs_b` are read; never `runs_f`, `compile_f`, labels or instance
membership. Parsing uses the pipeline's own `dataset._failure_view`, so values are read exactly as in the packages.

    python scripts/analysis/revision_cross_gen.py  -> results/revision/wp17_cross_gen.json
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import revision_common as rc  # noqa: E402
from triage import config, dataset, labeling  # noqa: E402
from triage import revision_metrics as rm  # noqa: E402
from triage.io_utils import dump_json  # noqa: E402

OUT = rc.OUT / "wp17_cross_gen.json"
DIRS = {"D1": ("candidates_gemma4_26b", "executions_gemma4_26b"),
        "D2": ("candidates_gemma4_26b_D2", "executions_gemma4_26b_D2")}


def _b_failures(ds):
    """focal_id -> generation -> list of buggy-version failure signatures of every deterministic P_B failure."""
    cdir, edir = (config.ROOT / "data" / "interim" / DIRS[ds][0]), (config.ROOT / "data" / "raw" / DIRS[ds][1])
    out = defaultdict(lambda: defaultdict(list))
    stats_ = {"candidates": 0, "methods": 0, "compiled_b": 0, "det_fail_b": 0, "missing_candidate": 0}
    for f in sorted(edir.glob("*.json")):
        ex = json.loads(f.read_text(encoding="utf-8"))
        cf = cdir / f.name
        if not cf.exists():
            stats_["missing_candidate"] += 1
            continue
        cand = json.loads(cf.read_text(encoding="utf-8"))
        stats_["candidates"] += 1
        fqcn = f"{cand['package']}.{cand['class_name']}"
        for m in ex["methods"]:
            stats_["methods"] += 1
            if not m.get("compile_b"):
                continue
            stats_["compiled_b"] += 1
            sig = labeling._deterministic(m["runs_b"])
            if sig is None or sig[0] == "pass":
                continue
            stats_["det_fail_b"] += 1
            fv = dataset._failure_view(m["runs_b"][0], fqcn, cand["source"], cand["package"])
            out[ex["focal_id"]][str(cand["generation"])].append(_key(fv, m["method"]))
    return out, stats_


def _top_main_frame(frames):
    for fr in frames:
        if not fr.get("in_test"):
            return f"{fr['method']}({fr['location']})"
    return None


def _key(fv, method):
    return {"method": method, "outcome": fv["outcome_type"], "exception": fv["exception_class"],
            "expected": fv["expected"], "actual": fv["actual"], "frame": _top_main_frame(fv["frames"])}


def comparable(k):
    if k["outcome"] == "assertion_failure":
        return k["expected"] is not None and k["actual"] is not None
    return k["frame"] is not None


def agrees(a, b):
    if a["outcome"] != b["outcome"] or a["exception"] != b["exception"]:
        return False
    if a["outcome"] == "assertion_failure":
        return a["expected"] is not None and a["expected"] == b["expected"] and a["actual"] == b["actual"]
    return a["frame"] is not None and a["frame"] == b["frame"]


def signal(D, bfail):
    """instance_id -> (cg count 0..2, comparable flag). The instance's own key is rebuilt from its P_B failure."""
    out = {}
    for i in D.ids:
        x = D.instances[i]
        f = x["failure"]
        k = {"outcome": f["outcome_type"], "exception": f["exception_class"], "expected": f["expected"],
             "actual": f["actual"], "frame": _top_main_frame(f["frames"])}
        g = str(x["generation"])
        others = {gg: keys for gg, keys in bfail.get(x["focal_id"], {}).items() if gg != g}
        n = sum(1 for keys in others.values() if any(agrees(k, o) for o in keys))
        out[i] = (n, comparable(k), len(others))
    return out


def run(ds):
    D = rc.build(ds)
    bfail, st = _b_failures(ds)
    sig = signal(D, bfail)
    bugs, W = D.weights_W()
    bi = {b: n for n, b in enumerate(bugs)}
    ids = D.ids
    y = [D.lab[i] for i in ids]
    cg = [sig[i][0] for i in ids]
    comp = [sig[i][1] for i in ids]
    T = np.zeros((len(bugs), 1, 4))
    for i, c in zip(ids, cg):
        t, p = D.lab[i] == rc.PF, c > 0
        T[bi[D.bug[i]], 0, 0 if (t and p) else 2 if t else 1 if p else 3] += 1
    pt, bs = rm.rates_point(T), rm.rates_bootstrap(T, W)
    pf = [c for c, t in zip(cg, y) if t == rc.PF]
    tf = [c for c, t in zip(cg, y) if t == rc.TF]
    bug_index = np.array([bi[D.bug[i]] for i in ids])
    auc_s = rm.auroc_bootstrap(y, cg, bug_index, W)
    return {"dataset": ds, "n_instances": len(ids), "execution_records": st,
            "linkage": {"instances_with_other_generations": sum(1 for i in ids if sig[i][2] > 0),
                        "instances_with_two_other_generations": sum(1 for i in ids if sig[i][2] == 2),
                        "note": "other generations = generations of the same focal method with >= 1 deterministic "
                                "P_B failure; a generation with none contributes no evidence"},
            "comparable_share": float(np.mean(comp)),
            "comparable_share_by_class": {"PF": float(np.mean([c for c, t in zip(comp, y) if t == rc.PF])),
                                          "TF": float(np.mean([c for c, t in zip(comp, y) if t == rc.TF]))},
            "cg_positive_rate": {"PF": float(np.mean([c > 0 for c in pf])), "TF": float(np.mean([c > 0 for c in tf]))},
            "cg_distribution": {"PF": {str(v): pf.count(v) for v in (0, 1, 2)}, "TF": {str(v): tf.count(v) for v in (0, 1, 2)}},
            "auroc_cg": rm.auroc(y, cg), "auroc_cg_ci95": rc.ci(auc_s),
            "keep_iff_cg": {**pt, "tpr_ci95": rc.ci(bs["tpr"]), "tnr_ci95": rc.ci(bs["tnr"]), "ba_ci95": rc.ci(bs["ba"])},
            "per_instance": {i: {"cg": sig[i][0], "comparable": sig[i][1]} for i in ids}}


def main():
    res = {"what": "cross-generation consensus, buggy-version information only (D-118, exploratory)",
           "decisions": ["D-112", "D-118"], "D1": run("D1"), "D2": run("D2")}
    dump_json(OUT, res)
    for ds in ("D1", "D2"):
        r = res[ds]
        print(ds, r["n_instances"], r["execution_records"], r["linkage"], "comparable", round(r["comparable_share"], 3),
              r["comparable_share_by_class"])
        print("  cg>0 rate", r["cg_positive_rate"], "dist", r["cg_distribution"], "AUROC", round(r["auroc_cg"], 3),
              np.round(r["auroc_cg_ci95"], 3))
        k = r["keep_iff_cg"]
        print(f"  keep iff cg>0: TPR {k['tpr']:.3f} TNR {k['tnr']:.3f} BA {k['ba']:.3f} {np.round(k['ba_ci95'], 3)}")


if __name__ == "__main__":
    main()
