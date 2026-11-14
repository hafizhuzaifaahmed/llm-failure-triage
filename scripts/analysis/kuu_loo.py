"""Leave-one-judge-out sensitivity for KUU (D-107, post hoc). Zero model calls; committed before computing.

Question: is KUU's protection mostly M2 (Gemma 4 12B, the generator's family, miss rate on PF 0.065 on D2 and 0.017 on
D1) vetoing discards? For each judge pair, discard only when both of its valid votes say TEST_FAULT (pair unanimity),
from the same committed votes KUU uses: D2 the KUU runs (replicate 20), D1 the E8 VOTE3 calls (replicate 10, post hoc
there as KUU is). Reported beside full KUU and M1 DEB: F1, MCC, precision, recall, PF tests lost, bugs with no PF test
kept, share discarded, and MCC(pair) − MCC(KUU) paired with a bug-level 95% CI. The key row is M1+E6b (no M2).
Descriptive; no hypothesis, no Holm family.

    python scripts/analysis/kuu_loo.py   -> results/kuu/analysis/kuu_loo.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

from triage import analysis, config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

import kuu_analysis as ka  # noqa: E402  (the committed KUU plan, rule and helpers)

OUT = ROOT / "results" / "kuu" / "analysis" / "kuu_loo.json"
TF, PF = ka.TF, ka.PF
PAIRS = {"M1+E6B": ("M1", "E6B"), "M1+M2": ("M1", "M2"), "M2+E6B": ("M2", "E6B")}
KEYS = ("f1", "f1_ci95", "mcc", "mcc_ci95", "precision", "recall", "pf_lost")


def unanimous(votes):
    return TF if votes and all(v == TF for v in votes) else PF


def run(which):
    plan = ka.PLAN[which]
    votes = {}
    for m, r in plan["members"].items():
        for d in read_jsonl(ka.RUNS / r / "decisions.jsonl"):
            if d["arm"] == "J1" and ka.s1(d) and d["replicate"] == plan["replicate"]:
                votes.setdefault(d["instance_id"], {})[m] = d["label_raw"]
    samp = json.loads((config.PROCESSED / plan["sample"]).read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / plan["labels"]) if l["instance_id"] in keep]
    aborted = ka.rejections(plan["baseline_run"]).union(*(ka.rejections(r) for r in plan["members"].values()))
    syn = []
    for i, v in votes.items():
        if i not in keep:
            continue
        syn.append({"instance_id": i, "arm": "KUU", "level": "S1", "variant": "full", "replicate": 0,
                    "label_raw": unanimous([v.get(m) for m in plan["members"]])})
        for name, (a, b) in PAIRS.items():
            syn.append({"instance_id": i, "arm": name.replace("+", "_"), "level": "S1", "variant": "full",
                        "replicate": 0, "label_raw": unanimous([v.get(a), v.get(b)])})
    base = [d for d in read_jsonl(ka.RUNS / plan["baseline_run"] / "decisions.jsonl") if d["arm"] == "DEB" and ka.s1(d)]
    ev = analysis.Evaluation(syn + base, labels, samp.get("tf_weights"), exclusions={("S1", "full"): aborted})
    conds = ["KUU|S1"] + [f"{n.replace('+', '_')}|S1" for n in PAIRS] + ["DEB|S1"]
    ids = ev.comparison_set(conds)
    evr = ev._restricted(ids)
    summ = {}
    for c in conds:
        s = {k: evr.summary(c).get(k) for k in KEYS}
        s["bugs_with_no_pf_kept"] = ka.lost_bugs(evr, c)
        arm = c.split("|")[0]
        rows = [x for x in syn if x["arm"] == arm and x["instance_id"] in evr.lab]
        s["share_discarded"] = (sum(x["label_raw"] == TF for x in rows) / len(rows)) if rows else None
        summ[c] = s
    diffs = {c: vars(evr.contrast(f"{c} - KUU", [c], ["KUU|S1"], "mcc")) for c in conds[1:4]}
    return {"dataset": plan["dataset"], "status": "post hoc sensitivity (D-107)" + (
                "; D1 is development evidence (KUU itself is post hoc there)" if plan["dataset"] == "D1" else ""),
            "n_instances": len(ids), "n_bugs": len(evr.bugs), "summary": summ, "pair_minus_kuu_mcc": diffs}


def main():
    out = {"what": "leave-one-judge-out sensitivity for KUU (D-107)", "decisions": ["D-95", "D-107"],
           "D2": run("d2"), "D1": run("d1")}
    dump_json(OUT, out)
    r = lambda v: round(v, 3) if isinstance(v, float) else v
    for ds in ("D2", "D1"):
        print(ds, "n", out[ds]["n_instances"])
        for c, s in out[ds]["summary"].items():
            print(f"  {c}: F1 {r(s['f1'])} MCC {r(s['mcc'])} P {r(s['precision'])} R {r(s['recall'])} "
                  f"lost {r(s['pf_lost'])} bugs {r(s['bugs_with_no_pf_kept'])} discarded {r(s['share_discarded'])}")


if __name__ == "__main__":
    main()
