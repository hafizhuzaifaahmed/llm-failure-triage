"""Pilot (D1-test) comparison and frame-overlap checks; read-only."""
import json, sys, glob, os
from collections import Counter
from pathlib import Path
ROOT = Path(sys.argv[1])
def rj(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
gt = None
for cand in glob.glob(str(ROOT / "data" / "ground_truth_store" / "**" / "labels_D1.jsonl"), recursive=True):
    gt = cand
print("labels file:", gt)
lab = {l["instance_id"]: l for l in rj(gt)}
led = {r["instance_id"]: r for r in rj(ROOT / "results/extension/probes/CFP_D1_TEST/ledger.jsonl")}
T = [(lab[i], led[i]["summary"]) for i in led if i in lab and lab[i]["label"] in ("PF", "TF") and lab[i].get("split") == "test"]
print("pilot scored:", len(T), Counter(l["label"] for l, s in T))
print("pilot by project: proj n PF flipPF decPF | TF flipTF decTF")
for p in sorted({l["project"] for l, s in T}):
    pf = [s for l, s in T if l["project"] == p and l["label"] == "PF"]; tf = [s for l, s in T if l["project"] == p and l["label"] == "TF"]
    print("  ", p, len(pf) + len(tf), len(pf), sum(bool(s.get("flip")) for s in pf), sum(bool(s.get("decoupled")) for s in pf), "|", len(tf), sum(bool(s.get("flip")) for s in tf), sum(bool(s.get("decoupled")) for s in tf))
print("pilot ncomp<10 & no flip/shift: PF", sum(1 for l, s in T if l["label"] == "PF" and (s.get("n_compiled") or 0) < 10 and not s.get("coupled")), "TF", sum(1 for l, s in T if l["label"] == "TF" and (s.get("n_compiled") or 0) < 10 and not s.get("coupled")))
# overlap of confirmation bugs with any bug the original study generated for
orig_bugs = {l["bug_name"] for l in lab.values()}
conf = set()
for t, ds in (("F1", "D1C_F1"), ("F2", "D1C_F2"), ("CTRL", "D1C_CTRL")):
    conf |= {l["bug_name"] for l in rj(ROOT / f"data/extension/confirm/{t}/labels_{ds}.jsonl")}
frame = rj(ROOT / "configs/extension/confirm_frame.jsonl")
fb = {r["focal_id"].split("::")[0] for r in frame}
print("original-study labelled bugs:", len(orig_bugs), "; confirmation labelled bugs:", len(conf), "; overlap:", len(orig_bugs & conf), "; frame bugs:", len(fb), "overlap with original labelled:", len(fb & orig_bugs))
print("frame tranche rows:", Counter(r["tranche"] for r in frame), "projects in frame:", sorted({b.rsplit('_', 1)[0] for b in fb}))
print("original splits by project:", {s: sorted({l['project'] for l in lab.values() if l.get('split') == s}) for s in {l.get('split') for l in lab.values()}})
