"""Shared loader for the review-response analyses (D-112 to D-121). Zero model calls; reads committed decisions only.

`build(ds)` reconstructs, on D-110's common instance set (the same construction as `pareto.py`, checked against
`results/pareto/pareto.json`), every rule's per-instance prediction per replicate, a PF score per rule where one is
defined (D-114), the raw panel votes, M1's SC samples and M1's DEB label and confidence. Nothing is written.
"""
import ast
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import analysis, arms, config, stats  # noqa: E402
from triage import revision_metrics as rm  # noqa: E402
from triage.io_utils import read_jsonl  # noqa: E402
from triage.metrics import score_label  # noqa: E402

RUNS, FRONT = ROOT / "results" / "runs_local", ROOT / "results" / "runs_frontier"
OUT = ROOT / "results" / "revision"
TF, PF, INV = rm.TF, rm.PF, rm.INVALID
PLAN = {
    "D1": {"sample": "sample_D1_test.json", "labels": "labels_D1.jsonl", "m1": "LOCAL_HO_E1E3_M1", "m2": "LOCAL_HO_E5R3_M2",
           "kuu": ({"M1": "LOCAL_HO_E8_VOTE_M1", "M2": "LOCAL_HO_E8_VOTE_M2", "E6B": "LOCAL_HO_E8_VOTE_E6B"}, 10),
           "ng": ({"M1": "LOCAL_HO_KUUNG_D1_M1", "E6B": "LOCAL_HO_KUUNG_D1_E6B", "NG": "LOCAL_HO_KUUNG_D1_NG"}, 30),
           "frontier": "E9_SONNET55_D1TEST", "instances": "instances_D1.jsonl"},
    "D2": {"sample": "sample_D2_test.json", "labels": "labels_D2.jsonl", "m1": "LOCAL_HO_E5R1_D2", "m2": "LOCAL_HO_E5R3_M2_D2",
           "kuu": ({"M1": "LOCAL_HO_KUU_D2_M1", "M2": "LOCAL_HO_KUU_D2_M2", "E6B": "LOCAL_HO_KUU_D2_E6B"}, 20),
           "ng": ({"M1": "LOCAL_HO_KUUNG_D2_M1", "E6B": "LOCAL_HO_KUUNG_D2_E6B", "NG": "LOCAL_HO_KUUNG_D2_NG"}, 30),
           "frontier": "E9B_SONNET55_D2", "instances": "instances_D2.jsonl"},
}
PAIRS = {"P_M1_E6B": ("M1", "E6B"), "P_M1_M2": ("M1", "M2"), "P_M2_E6B": ("M2", "E6B")}
NAMES = {"KA": "Keep all", "DA": "Discard all", "R0": "Rule R0", "J1|S1": "M1 one judge (J1)",
         "SC|S1": "M1 self-consistency (SC)", "SC-T|S1": "M1 SC-T", "DEB|S1": "M1 debate (DEB)",
         "TAU|S1": "M1 DEB, confidence 100 (tuned)", "KUU|S1": "KUU", "KUUNG|S1": "KUU-NG",
         "P_M1_E6B|S1": "KUU pair M1+E6b", "P_M1_M2|S1": "KUU pair M1+M2", "P_M2_E6B|S1": "KUU pair M2+E6b",
         "MAJ3|S1": "Cross-family 2-of-3 (D-106)", "VOTE3|S1": "E8 VOTE3 (SC aggregation)", "CAS|S1": "Cascade",
         "J1|S1|SON": "Sonnet J1", "DEB|S1|SON": "Sonnet DEB"}


def _cost(d):
    c = d.get("cost")
    if isinstance(c, str):
        c = ast.literal_eval(c)
    return c or {}


def s1(d):
    return d.get("level") == "S1" and (d.get("variant") or "full") == "full"


def rejections(run):
    f = RUNS / run / "leakage_rejections.jsonl"
    return {r["instance_id"] for r in read_jsonl(f) if r.get("level") == "S1"} if f.exists() else set()


def unanimous(vs):
    return TF if vs and all(v == TF for v in vs) else PF


def panel_votes(runs, rep):
    v = {}
    for m, r in runs.items():
        for d in read_jsonl(RUNS / r / "decisions.jsonl"):
            if d["arm"] == "J1" and s1(d) and d["replicate"] == rep:
                v.setdefault(d["instance_id"], {})[m] = d["label_raw"]
    return v


class Data:
    """Per-dataset view. preds[cond][rep][id] = label_raw; scores[cond][rep][id] = PF score (higher = PF)."""

    def __init__(self, ds):
        self.ds = ds
        self.preds, self.scores = {}, {}

    # count tensor of a condition on the common set (primary coding: INVALID -> TF unless policy says otherwise)
    def tensor(self, cond, policy="as_TF", ids=None):
        ids = self.ids if ids is None else ids
        idset = set(ids)
        bugs = sorted({self.bug[i] for i in ids})
        reps = sorted(self.preds[cond])
        rows = []
        for r in reps:
            for i, lab in self.preds[cond][r].items():
                if i not in idset:
                    continue
                if policy == "as_PF" and lab == INV:
                    y = PF
                else:
                    y = score_label(lab, "as_TF")
                rows.append({"bug_id": self.bug[i], "replicate": r, "y_true": self.lab[i], "y_pred": y})
        return stats.count_tensor(rows, bugs, reps)

    def weights_W(self, ids=None, seed=config.SEED_BOOTSTRAP):
        ids = self.ids if ids is None else ids
        bugs = sorted({self.bug[i] for i in ids})
        return bugs, stats.bootstrap_weights(len(bugs), seed=seed)


def build(ds):
    plan = PLAN[ds]
    samp = json.loads((config.PROCESSED / plan["sample"]).read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels_all = list(read_jsonl(config.GT_STORE / plan["labels"]))
    labels = [l for l in labels_all if l["instance_id"] in keep]
    m1 = list(read_jsonl(RUNS / plan["m1"] / "decisions.jsonl"))
    syn = []

    def add(i, arm, rep, lab):
        syn.append({"instance_id": i, "arm": arm, "level": "S1", "variant": "full", "replicate": rep, "label_raw": lab,
                    "agreement": {}})
    for d in m1:
        if d["arm"] == "DEB" and s1(d):
            conf = d.get("confidence")
            add(d["instance_id"], "TAU", d["replicate"],
                TF if d["label_raw"] == TF and conf is not None and float(conf) >= 100 else PF)
    kv = panel_votes(*plan["kuu"])
    nv = panel_votes(*plan["ng"])
    front = [d for d in read_jsonl(FRONT / plan["frontier"] / "decisions.jsonl") if s1(d)]
    son = {}
    for d in front:
        son.setdefault((d["arm"], d["replicate"]), {})[d["instance_id"]] = d
    deb_reps = sorted(r for a, r in son if a == "DEB")
    for i in keep:
        v = kv.get(i, {})
        if len(v) == 3:
            vs = [v.get(m) for m in ("M1", "M2", "E6B")]
            add(i, "KUU", 0, unanimous(vs))
            for name, (a, b) in PAIRS.items():
                add(i, name, 0, unanimous([v.get(a), v.get(b)]))
            add(i, "MAJ3", 0, rm.k_of_n(vs, 2))
            add(i, "VOTE3", 0, arms.aggregate_votes(vs, 3)["label_raw"])      # E8 rule: majority of valid, tie -> TF
            esc = not (all(x == TF for x in vs) or all(x == PF for x in vs))
            for k, r in enumerate(deb_reps):
                e = son[("DEB", r)].get(i)
                add(i, "CAS", k, vs[0] if not esc else (e["label_raw"] if e and e["label_raw"] in (TF, PF) else PF))
        n = nv.get(i, {})
        if len(n) == 3:
            add(i, "KUUNG", 0, unanimous([n.get(m) for m in ("M1", "E6B", "NG")]))
    for (arm, r), dd in son.items():
        for i, d in dd.items():
            syn.append({**d, "variant": "SON"})
    base = [d for d in m1 if (d["arm"] in ("J1", "SC", "DEB", "SC-T") and s1(d)) or d["arm"] in ("KA", "DA", "R0")]
    aborted = rejections(plan["m1"]).union(*(rejections(r) for r in plan["kuu"][0].values()),
                                           *(rejections(r) for r in plan["ng"][0].values()))
    ev = analysis.Evaluation(syn + base, labels, samp.get("tf_weights"),
                             exclusions={("S1", "full"): aborted, ("S1", "SON"): aborted})
    # D-110's common set: exactly pareto.py's condition list
    pconds = ["J1|S1", "SC|S1", "DEB|S1", "TAU|S1", "KUU|S1", "P_M1_E6B|S1", "P_M1_M2|S1", "P_M2_E6B|S1", "KUUNG|S1",
              "CAS|S1", "J1|S1|SON", "DEB|S1|SON"]
    pconds = [c for c in pconds if ev.by_cond.get(c)]
    ids = sorted(ev.comparison_set(pconds))
    D = Data(ds)
    D.ids, D.plan, D.sample = ids, plan, samp
    D.lab = {i: ev.lab[i] for i in ids}
    D.bug = {i: ev.meta[i]["bug_name"] for i in ids}
    D.project = {i: ev.meta[i]["project"] for i in ids}
    tfw = samp.get("tf_weights") or {}
    D.w = {i: (1.0 if D.lab[i] == PF else float(tfw.get(i, 1.0))) for i in ids}
    D.labels_all = labels_all
    D.aborted = aborted
    idset = set(ids)
    for c, ds_ in ev.by_cond.items():
        for d in ds_:
            if d["instance_id"] in idset:
                D.preds.setdefault(c, {}).setdefault(d["replicate"], {})[d["instance_id"]] = d["label_raw"]
    # SC-T may not cover the set; drop any condition with a gap rather than score it on fewer instances
    for c in list(D.preds):
        reps = D.preds[c]
        if any(set(m) != idset for m in reps.values()):
            D.preds.pop(c)
    # scores (D-114)
    D.kuu_votes = {i: kv[i] for i in ids if i in kv}
    D.ng_votes = {i: nv[i] for i in ids if i in nv}
    D.scores["KUU|S1"] = {0: {i: rm.keep_score([kv[i].get(m) for m in ("M1", "M2", "E6B")]) for i in ids}}
    D.scores["KUUNG|S1"] = {0: {i: rm.keep_score([nv[i].get(m) for m in ("M1", "E6B", "NG")]) for i in ids}}
    for name, (a, b) in PAIRS.items():
        D.scores[f"{name}|S1"] = {0: {i: rm.keep_score([kv[i].get(a), kv[i].get(b)], n=2) for i in ids}}
    D.scores["MAJ3|S1"] = D.scores["KUU|S1"]
    D.m1deb, D.sc_votes = {}, {}
    for d in m1:
        if not s1(d) or d["instance_id"] not in idset:
            continue
        i, r = d["instance_id"], d["replicate"]
        if d["arm"] in ("J1", "DEB"):
            D.scores.setdefault(f"{d['arm']}|S1", {}).setdefault(r, {})[i] = rm.pf_score(d["label_raw"], d.get("confidence"))
            if d["arm"] == "DEB":
                D.m1deb.setdefault(r, {})[i] = (d["label_raw"], d.get("confidence"))
        elif d["arm"] == "SC":
            D.scores.setdefault("SC|S1", {}).setdefault(r, {})[i] = float(d["agreement"]["vote_share_pf"])
            D.sc_votes.setdefault("M1", {}).setdefault(r, {})[i] = list(d.get("votes") or [])
        elif d["arm"] == "R0":
            pass
    for d in base:
        if d["arm"] == "R0" and d["instance_id"] in idset:
            D.scores.setdefault("R0", {}).setdefault(d["replicate"], {})[d["instance_id"]] = 1.0 if d["label_raw"] == PF else 0.0
    D.scores["KA"] = {0: {i: 0.5 for i in ids}}
    for (arm, r), dd in son.items():
        D.scores.setdefault(f"{arm}|S1|SON", {})[r] = {i: rm.pf_score(dd[i]["label_raw"], dd[i].get("confidence"))
                                                      for i in ids if i in dd}
    m2f = RUNS / plan["m2"] / "decisions.jsonl"
    if m2f.exists():
        for d in read_jsonl(m2f):
            if d["arm"] == "SC" and s1(d) and d["instance_id"] in idset:
                D.sc_votes.setdefault("M2", {}).setdefault(d["replicate"], {})[d["instance_id"]] = list(d.get("votes") or [])
    D.instances = {x["instance_id"]: x for x in read_jsonl(config.PROCESSED / plan["instances"]) if x["instance_id"] in idset}
    D.pareto_n = json.loads((ROOT / "results" / "pareto" / "pareto.json").read_text(encoding="utf-8"))[ds]["n_instances"]
    assert len(ids) == D.pareto_n, f"{ds}: common set {len(ids)} differs from D-110's {D.pareto_n}"
    return D


def population_prevalence(D):
    """PF / (PF + TF) over every labelled instance of the dataset's held-out split (AMB excluded)."""
    ls = [l for l in D.labels_all if l.get("split", "test") == "test" and l["label"] in ("PF", "TF")]
    return sum(l["label"] == "PF" for l in ls) / len(ls), len(ls)


def ci(samples, level=0.95):
    return list(stats.percentile_ci(np.asarray(samples, dtype=float), level))
