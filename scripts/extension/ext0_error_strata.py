"""EXT-0 (D-133; exploratory; zero model calls): where do the strongest logged judges err?

Counts, per failure stratum, how many PF tests each rule keeps and how many TF tests it removes, on D-110's common
sets. Reads committed decisions and the instance records only; writes results/extension/ext0_error_strata.json.

    python scripts/extension/ext0_error_strata.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
import revision_common as rc  # noqa: E402
from triage.io_utils import read_jsonl  # noqa: E402

OUT = ROOT / "results" / "extension" / "ext0_error_strata.json"
THINK = {"D1": "REV_THINK_M1", "D2": "REV_THINK_D2_M1"}
RULES = ["DEB|S1", "KUU|S1", "DEB|S1|SON"]


def strata(ds):
    plan = rc.PLAN[ds]
    return {r["instance_id"]: f"{r['covariates']['failure_type']}/{r['covariates']['deepest_frame']}"
            for r in read_jsonl(ROOT / "data" / "processed" / plan["instances"])}


def think_votes(ds):
    f = ROOT / "results" / "revision" / "runs" / THINK[ds] / "decisions.jsonl"
    return {d["instance_id"]: d["label_raw"] for d in read_jsonl(f) if d["arm"] == "J1" and rc.s1(d)}


def main():
    out = {"decision": "D-133", "status": "exploratory, descriptive, zero calls", "datasets": {}}
    for ds in ("D1", "D2"):
        d = rc.build(ds)
        st = strata(ds)
        tv = think_votes(ds)
        table = defaultdict(lambda: defaultdict(lambda: {"pf": 0, "tf": 0, "pf_kept": 0.0, "tf_removed": 0.0}))
        for i in d.ids:
            s, y = st[i], d.lab[i]
            for cond in RULES + ["THINK"]:
                if cond == "THINK":
                    preds = [tv[i]] if i in tv else []
                else:
                    preds = [d.preds[cond][r][i] for r in sorted(d.preds[cond]) if i in d.preds[cond][r]]
                if not preds:
                    continue
                cell = table[s][cond]
                kept = sum(1 for p in preds if p == rc.PF) / len(preds)      # invalid scores TF (primary coding)
                if y == rc.PF:
                    cell["pf"] += 1
                    cell["pf_kept"] += kept
                else:
                    cell["tf"] += 1
                    cell["tf_removed"] += 1 - kept
        out["datasets"][ds] = {s: {c: {k: round(v, 2) for k, v in cell.items()} for c, cell in rules.items()}
                               for s, rules in sorted(table.items())}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    for ds, t in out["datasets"].items():
        print(ds)
        for s, rules in t.items():
            print(" ", s, {c: f"PF {v['pf_kept']}/{v['pf']} TF {v['tf_removed']}/{v['tf']}" for c, v in rules.items()})


if __name__ == "__main__":
    main()
