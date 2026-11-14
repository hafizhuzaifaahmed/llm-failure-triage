"""Score the two-rater label audit (D-82): rater agreement and agreement with the execution label. No model call.

Inputs: the raters' sheets (`docs/audits/kit/label_audit_rater_{A,B}.csv`, decision PF / TF / AMB), the hidden key
(`data/ground_truth_store/audit/label_audit_key.csv`: audit_id -> instance_id, execution label) and, optionally, a
consensus sheet written after the raters discuss their disagreements (`docs/audits/kit/label_audit_consensus.csv`,
columns audit_id, decision). Without it, the consensus is the shared decision where the raters agree and UNRESOLVED
where they do not.

Reported:
  - Cohen's kappa between the raters over PF / TF / AMB, with a 95% bootstrap CI resampled by bug (seed 20261011);
  - consensus vs execution label: agreement, Cohen's kappa (PF / TF items only), the 3 x 2 confusion matrix;
  - a mismatch-category table: every consensus label that differs from the execution label, by direction and by the
    instance's failure type (assertion failure vs exception).

    python scripts/analysis/label_audit.py [--a ... --b ... --consensus ...]   -> results/audit/label_audit_scores.json
"""
import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

KIT = ROOT / "docs" / "audits" / "kit"
CATS = ("PF", "TF", "AMB")


def kappa(a: list[str], b: list[str], cats=CATS) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[c] * cb[c] for c in cats) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def bootstrap_kappa(a, b, clusters, B=2000, seed=20261011, cats=CATS):
    rng = np.random.default_rng(seed)
    ids = sorted(set(clusters))
    idx = {c: [k for k, x in enumerate(clusters) if x == c] for c in ids}
    vals = []
    for _ in range(B):
        pick = [k for c in rng.choice(ids, size=len(ids), replace=True) for k in idx[c]]
        vals.append(kappa([a[k] for k in pick], [b[k] for k in pick], cats))
    v = np.array([x for x in vals if not np.isnan(x)])
    return [float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975))] if len(v) else [float("nan")] * 2


def read_sheet(path: Path, col="decision") -> dict:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return {r["audit_id"]: r[col].strip().upper() for r in csv.DictReader(fh)}


def score(a: dict, b: dict, key: dict, meta: dict, consensus: dict | None = None) -> dict:
    ids = sorted(i for i in key if a.get(i) in CATS and b.get(i) in CATS)
    missing = sorted(i for i in key if i not in ids)
    ra, rb = [a[i] for i in ids], [b[i] for i in ids]
    bugs = [meta[key[i]["instance_id"]]["bug_name"] for i in ids]
    cons = {i: (consensus.get(i) if consensus and consensus.get(i) in CATS else (a[i] if a[i] == b[i] else "UNRESOLVED")) for i in ids}
    res = [i for i in ids if cons[i] in CATS]
    exe = [key[i]["auto_label"] for i in res]
    cl = [cons[i] for i in res]
    pf_tf = [k for k, c in enumerate(cl) if c in ("PF", "TF")]
    conf = {c: {e: sum(1 for x, y in zip(cl, exe) if x == c and y == e) for e in ("PF", "TF")} for c in CATS}
    mism = Counter()
    for i in res:
        if cons[i] != key[i]["auto_label"]:
            ft = meta[key[i]["instance_id"]]["covariates"]["failure_type"]
            mism[(f"execution {key[i]['auto_label']} -> raters {cons[i]}", ft)] += 1
    return {
        "n_items": len(key), "n_scored": len(ids), "missing_or_invalid": missing,
        "raters": {"agreement": float(np.mean([x == y for x, y in zip(ra, rb)])) if ids else None,
                   "kappa": kappa(ra, rb), "kappa_ci95_bug_bootstrap": bootstrap_kappa(ra, rb, bugs),
                   "decisions_A": dict(Counter(ra)), "decisions_B": dict(Counter(rb))},
        "consensus_vs_execution": {
            "n_resolved": len(res), "unresolved": sum(1 for i in ids if cons[i] == "UNRESOLVED"),
            "consensus_source": "consensus sheet" if consensus else "rater agreement only",
            "agreement": float(np.mean([x == y for x, y in zip(cl, exe)])) if res else None,
            "kappa_pf_tf": kappa([cl[k] for k in pf_tf], [exe[k] for k in pf_tf], ("PF", "TF")),
            "consensus_amb": sum(1 for c in cl if c == "AMB"),
            "confusion_consensus_by_execution": conf},
        "mismatch_categories": [{"direction": d, "failure_type": f, "count": n} for (d, f), n in sorted(mism.items())],
    }


def llm_secondary(a: dict, b: dict, c: dict, key: dict, meta: dict, consensus: dict | None) -> dict:
    """D-84 secondary statistics: agreement and Cohen's kappa of each human rater and of the human consensus against
    the LLM rater C (never replaces a human rating or the execution label)."""
    ids = sorted(i for i in key if a.get(i) in CATS and b.get(i) in CATS and c.get(i) in CATS)
    bugs = [meta[key[i]["instance_id"]]["bug_name"] for i in ids]
    cons = {i: (consensus.get(i) if consensus and consensus.get(i) in CATS else (a[i] if a[i] == b[i] else None))
            for i in ids}
    out = {"n_scored": len(ids), "decisions_C": dict(Counter(c[i] for i in ids))}
    for name, other in (("A_vs_C", a), ("B_vs_C", b)):
        x, y = [other[i] for i in ids], [c[i] for i in ids]
        out[name] = {"agreement": float(np.mean([p == q for p, q in zip(x, y)])), "kappa": kappa(x, y),
                     "kappa_ci95_bug_bootstrap": bootstrap_kappa(x, y, bugs)}
    res = [i for i in ids if cons[i] in CATS]
    x, y = [cons[i] for i in res], [c[i] for i in res]
    out["consensus_vs_C"] = {"n": len(res), "agreement": float(np.mean([p == q for p, q in zip(x, y)])) if res else None,
                             "kappa": kappa(x, y)}
    exe = [key[i]["auto_label"] for i in ids]
    yc = [c[i] for i in ids]
    out["C_vs_execution"] = {"agreement": float(np.mean([p == q for p, q in zip(yc, exe)])),
                             "kappa_pf_tf": kappa([p for p, q in zip(yc, exe) if p in ("PF", "TF")],
                                                  [q for p, q in zip(yc, exe) if p in ("PF", "TF")], ("PF", "TF"))}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default=str(KIT / "label_audit_rater_A.csv"))
    ap.add_argument("--b", default=str(KIT / "label_audit_rater_B.csv"))
    ap.add_argument("--c", default=str(KIT / "llm_rater" / "unsealed" / "label_audit_rater_C.csv"),
                    help="the unsealed LLM rater sheet (D-84); scored only if present")
    ap.add_argument("--consensus", default=str(KIT / "label_audit_consensus.csv"))
    ap.add_argument("--out", default=str(config.RESULTS / "audit" / "label_audit_scores.json"))
    x = ap.parse_args()
    with open(config.GT_STORE / "audit" / "label_audit_key.csv", newline="", encoding="utf-8-sig") as fh:
        key = {r["audit_id"]: r for r in csv.DictReader(fh)}
    meta = {i["instance_id"]: i for i in read_jsonl(config.PROCESSED / "instances_D1.jsonl")}
    a, b = read_sheet(Path(x.a)), read_sheet(Path(x.b))
    cons = read_sheet(Path(x.consensus)) if Path(x.consensus).exists() else None
    r = score(a, b, key, meta, cons)
    if r["n_scored"] == 0:
        raise SystemExit("no rated items yet (decision column empty)")
    if Path(x.c).exists():
        r["llm_rater_secondary_D84"] = llm_secondary(a, b, read_sheet(Path(x.c)), key, meta, cons)
    dump_json(Path(x.out), r)
    print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
