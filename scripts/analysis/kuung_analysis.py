"""KUU-NG (D-109): keep unless unanimous with a panel that contains no generator-family judge. Zero model calls.
Committed before any KUU-NG call.

Panel: M1 (Qwen 3.5 9B), E6b (Ministral 3 14B) and the fourth-family judge selected by `scripts/local/kuung.py`
(phi4, else llama3.1); fresh J1 calls at S1, replicate index 30, runs LOCAL_HO_KUUNG_{D1,D2}_{M1,E6B,NG}.
Rule (KUU, D-95, unchanged): discard (TEST_FAULT) only if all three votes are valid TEST_FAULT; otherwise keep.

Per dataset (D1-test and D2), Holm over the pair, two-sided bug-level bootstrap p (committed seed and B):
  H13-1  ΔF1(KUU-NG − keep-all) > 0, paired;                   supported when p_Holm < alpha and Δ > 0.
  H13-2  bugs lost(KUU-NG) < bugs lost(M1 DEB), paired;       supported when p_Holm < alpha and Δ < 0.
         A bug is lost when it has at least one PF test in the set and none is kept; M1 DEB is the committed run
         (D1: LOCAL_HO_E1E3_M1, three replicates, per-bug loss averaged over replicates; D2: LOCAL_HO_E5R1_D2).
Descriptive: F1, MCC, precision, recall, PF tests lost, bugs lost, share discarded for KUU-NG, the original KUU
(D1: E8 votes, post hoc; D2: KUU runs), the M1+E6b pair from the original votes, keep-all and M1 DEB; MCC(KUU-NG) −
MCC(KUU) paired. D1 note: the KUU rule was derived from the D1 votes, so a D1 test of KUU-NG with fresh calls tests a
new panel on the data the rule came from; D2 is the cleaner test.

    python scripts/analysis/kuung_analysis.py   -> results/kuung/analysis/kuung.json
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

from triage import analysis, config, stats  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

import kuu_analysis as ka  # noqa: E402

OUT = ROOT / "results" / "kuung" / "analysis" / "kuung.json"
TF, PF = ka.TF, ka.PF
PLAN = {
    "D1": {"sample": "sample_D1_test.json", "labels": "labels_D1.jsonl", "deb_run": "LOCAL_HO_E1E3_M1",
           "ng": {"M1": "LOCAL_HO_KUUNG_D1_M1", "E6B": "LOCAL_HO_KUUNG_D1_E6B", "NG": "LOCAL_HO_KUUNG_D1_NG"},
           "orig": ka.PLAN["d1"]},
    "D2": {"sample": "sample_D2_test.json", "labels": "labels_D2.jsonl", "deb_run": "LOCAL_HO_E5R1_D2",
           "ng": {"M1": "LOCAL_HO_KUUNG_D2_M1", "E6B": "LOCAL_HO_KUUNG_D2_E6B", "NG": "LOCAL_HO_KUUNG_D2_NG"},
           "orig": ka.PLAN["d2"]},
}
KEYS = ("f1", "f1_ci95", "mcc", "mcc_ci95", "precision", "recall", "pf_lost")


def unanimous(votes):
    return TF if votes and all(v == TF for v in votes) else PF


def votes_of(runs: dict, rep: int) -> dict:
    out = {}
    for m, r in runs.items():
        for d in read_jsonl(ka.RUNS / r / "decisions.jsonl"):
            if d["arm"] == "J1" and ka.s1(d) and d["replicate"] == rep:
                out.setdefault(d["instance_id"], {})[m] = d["label_raw"]
    return out


def bug_loss_vector(ev, c: str) -> np.ndarray:
    """Per bug: share of replicates in which the bug has a PF test in the set and none kept."""
    T = ev.tensor(c)
    has_pf = (T[:, 0, 0] + T[:, 0, 2]) > 0
    return np.mean([(has_pf & (T[:, r, 0] == 0)).astype(float) for r in range(T.shape[1])], axis=0)


def run(ds):
    plan = PLAN[ds]
    ng = votes_of(plan["ng"], 30)
    orig = votes_of(plan["orig"]["members"], plan["orig"]["replicate"])
    samp = json.loads((config.PROCESSED / plan["sample"]).read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / plan["labels"]) if l["instance_id"] in keep]
    aborted = ka.rejections(plan["deb_run"]).union(*(ka.rejections(r) for r in plan["ng"].values()),
                                                   *(ka.rejections(r) for r in plan["orig"]["members"].values()))
    syn = []
    for i in keep:
        v, o = ng.get(i, {}), orig.get(i, {})
        syn.append({"instance_id": i, "arm": "KUUNG", "level": "S1", "variant": "full", "replicate": 0,
                    "label_raw": unanimous([v.get(m) for m in ("M1", "E6B", "NG")]) if len(v) == 3 else PF})
        syn.append({"instance_id": i, "arm": "KUU", "level": "S1", "variant": "full", "replicate": 0,
                    "label_raw": unanimous([o.get(m) for m in ("M1", "M2", "E6B")]) if len(o) == 3 else PF})
        syn.append({"instance_id": i, "arm": "PAIR_M1_E6B", "level": "S1", "variant": "full", "replicate": 0,
                    "label_raw": unanimous([o.get("M1"), o.get("E6B")])})
    base = [d for d in read_jsonl(ka.RUNS / plan["deb_run"] / "decisions.jsonl")
            if (d["arm"] == "DEB" and ka.s1(d)) or d["arm"] == "KA"]
    ev = analysis.Evaluation(syn + base, labels, samp.get("tf_weights"), exclusions={("S1", "full"): aborted})
    conds = ["KUUNG|S1", "KUU|S1", "PAIR_M1_E6B|S1", "DEB|S1"]
    ids = ev.comparison_set(conds) & {i for i in keep if len(ng.get(i, {})) == 3}
    evr = ev._restricted(ids)
    summ = {}
    for c in conds:
        s = {k: evr.summary(c).get(k) for k in KEYS}
        s["bugs_lost"] = float(bug_loss_vector(evr, c).sum())
        arm = c.split("|")[0]
        rows = [x for x in syn if x["arm"] == arm and x["instance_id"] in evr.lab]
        s["share_discarded"] = sum(x["label_raw"] == TF for x in rows) / len(rows) if rows else None
        summ[c] = s
    summ["KA"] = {k: evr.baseline_summary("KA").get(k) for k in KEYS}
    h1 = evr.contrast(f"H13-1 {ds} KUU-NG - KA", ["KUUNG|S1"], ["KA"], "f1")
    diff = bug_loss_vector(evr, "KUUNG|S1") - bug_loss_vector(evr, "DEB|S1")
    d2 = float(diff.sum())
    boot = evr.W @ diff
    p2 = stats.bootstrap_p_two_sided(boot)
    adj = stats.holm([h1.p, p2])
    hyp = {"H13-1": {"what": "ΔF1(KUU-NG − keep-all) > 0", "delta": h1.delta, "ci95": h1.ci95, "p": h1.p,
                     "p_holm": adj[0], "supported": bool(adj[0] < config.ALPHA and h1.delta > 0)},
           "H13-2": {"what": "bugs lost(KUU-NG) − bugs lost(M1 DEB) < 0, paired", "delta": d2,
                     "ci95": stats.percentile_ci(boot), "p": p2, "p_holm": adj[1],
                     "supported": bool(adj[1] < config.ALPHA and d2 < 0)}}
    sel = json.loads((ROOT / "results" / "kuung" / "selection.json").read_text(encoding="utf-8"))
    return {"dataset": ds, "status": "pre-registered (D-109)" + ("; the KUU rule itself came from D1" if ds == "D1" else ""),
            "fourth_judge": sel.get("selected"), "n_instances": len(ids), "n_bugs": len(evr.bugs),
            "pf_prevalence": analysis.judged_prevalence(labels, sorted(ids)),
            "invalid_or_missing_votes": sum(1 for i in ids for m in ("M1", "E6B", "NG") if ng.get(i, {}).get(m) not in (TF, PF)),
            "summary": summ, "hypotheses": hyp,
            "kuung_minus_kuu_mcc": vars(evr.contrast("KUU-NG - KUU", ["KUUNG|S1"], ["KUU|S1"], "mcc"))}


def main():
    out = {"what": "KUU-NG: a KUU panel with no generator-family judge (D-109)", "decisions": ["D-95", "D-107", "D-109"],
           "D1": run("D1"), "D2": run("D2")}
    dump_json(OUT, out)
    r = lambda v: round(v, 3) if isinstance(v, float) else v
    for ds in ("D2", "D1"):
        o = out[ds]
        print(ds, o["fourth_judge"], "n", o["n_instances"], "bugs", o["n_bugs"], "invalid", o["invalid_or_missing_votes"])
        for c, s in o["summary"].items():
            print(f"  {c}: F1 {r(s['f1'])} MCC {r(s['mcc'])} lost {r(s['pf_lost'])} bugs {r(s.get('bugs_lost'))} discarded {r(s.get('share_discarded'))}")
        for h, v in o["hypotheses"].items():
            print(f"  {h}: {r(v['delta'])} {[r(x) for x in v['ci95']]} p_holm={r(v['p_holm'])} supported={v['supported']}")


if __name__ == "__main__":
    main()
