"""Analysis of decision records against the label store (Phase 2 Section 5). Evaluation is the ONLY place
where predictions and ground-truth labels meet.

Produces condition tables with bug-level cluster-bootstrap CIs, the five confirmatory contrasts (Holm),
the secondary precision/recall family, SC-T check, efficiency, A3 re-analysis, sensitivity analyses
(invalid excluded; AMB as PF; AMB as TF), McNemar, per-project Wilcoxon and leave-one-project-out.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import numpy as np

from . import arms as arms_mod
from . import config, stats
from .io_utils import read_jsonl
from .metrics import PF, TF, average_precision, bug_level_retention, score_label

ARM_ORDER = ["DA", "KA", "R0", "J1", "SC", "SC-T", "DEB", "A1", "A2"]
BASELINES = ("DA", "KA", "R0")
PRIMARY_LEVEL = "S1"      # the E1 level: level-free baselines are tabulated on its instance set (D-70)


class UnequalInstanceSets(ValueError):
    """A comparison whose conditions do not cover the same instances and replicates (D-70)."""


def exclusion_key(arm: str, level: Optional[str], variant: Optional[str]) -> tuple:
    """D-70 (amended): aborts are keyed by (level, variant). A1/A2 are ablation conditions keyed as their own
    variants, so a Tier 2 abort never touches the E1-E3 (`full`) sets; the A3 re-scoring follows SC `full`."""
    v = variant or "full"
    if arm in ("A1", "A2"):
        v = arm
    elif v.startswith("A3"):
        v = "full"
    return (level, v)


def abort_exclusions(rejections) -> dict[tuple, set]:
    """D-70: (level, variant) -> instances the leakage guard aborted there (any replicate)."""
    out: dict[tuple, set] = defaultdict(set)
    for r in rejections:
        if r.get("level"):
            out[exclusion_key(r["arm"], r["level"], r.get("variant"))].add(r["instance_id"])
    return dict(out)


def cond_level(cond: str) -> Optional[str]:
    return cond.split("|")[1] if "|" in cond else None


def cond_key(cond: str) -> tuple:
    parts = cond.split("|")
    if len(parts) == 1:
        return (None, "full")
    return exclusion_key(parts[0], parts[1], parts[2] if len(parts) > 2 else None)


def cond_name(d: dict) -> str:
    if d["arm"] in ("DA", "KA", "R0"):
        return d["arm"]
    v = d.get("variant") or "full"
    return f"{d['arm']}|{d['level']}" + ("" if v == "full" else f"|{v}")


class Evaluation:
    def __init__(self, decisions: list[dict], labels: list[dict], weights: Optional[dict] = None,
                 amb_policy: str = "exclude", invalid_policy: str = "as_TF", restrict: Optional[set] = None,
                 exclusions: Optional[dict] = None):
        self.lab = {}
        for l in labels:
            if l["label"] == "AMB":
                if amb_policy == "exclude":
                    continue
                self.lab[l["instance_id"]] = PF if amb_policy == "as_PF" else TF
            else:
                self.lab[l["instance_id"]] = PF if l["label"] == "PF" else TF
        if restrict is not None:
            self.lab = {k: v for k, v in self.lab.items() if k in restrict}
        self.meta = {l["instance_id"]: l for l in labels}
        self.weights = weights or {}
        self.invalid_policy = invalid_policy
        self.exclusions = {k: set(v) for k, v in (exclusions or {}).items()}
        self.by_cond: dict[str, list[dict]] = defaultdict(list)
        for d in decisions:
            # D-70: an instance aborted at (level, variant) leaves every arm there
            key = exclusion_key(d["arm"], d.get("level"), d.get("variant"))
            if d["instance_id"] in self.lab and d["instance_id"] not in self.exclusions.get(key, ()):
                self.by_cond[cond_name(d)].append(d)
        self.bugs = sorted({self.meta[i]["bug_name"] for i in self.lab})
        self.W = stats.bootstrap_weights(len(self.bugs)) if self.bugs else None

    def allowed(self, cond: str) -> set:
        """Instances a condition may be scored on: the labelled set minus its (level, variant) aborts (D-70)."""
        return set(self.lab) - self.exclusions.get(cond_key(cond), set())

    def exclusion_counts(self) -> dict:
        out = {}
        for (lv, var), ids in sorted(self.exclusions.items()):
            labelled = [i for i in ids if i in self.meta]
            lv = f"{lv}|{var}"
            out[lv] = {"instances": len(labelled),
                       "PF": sum(self.meta[i]["label"] == "PF" for i in labelled),
                       "TF": sum(self.meta[i]["label"] == "TF" for i in labelled)}
            amb = sum(self.meta[i]["label"] == "AMB" for i in labelled)
            if amb:
                out[lv]["AMB"] = amb
        return out

    def comparison_set(self, conds: list[str], restrict: Optional[set] = None) -> set:
        """The common instance set of a comparison; refuses unexplained gaps (missing instance or replicate)."""
        ids = set(self.lab) if restrict is None else set(self.lab) & set(restrict)
        for c in conds:
            ids &= self.allowed(c)
        for c in conds:
            reps: dict[str, set] = defaultdict(set)
            for d in self.by_cond.get(c, []):
                reps[d["instance_id"]].add(d["replicate"])
            want = set().union(*reps.values()) if reps else set()
            gaps = sorted(i for i in ids if reps.get(i) != want)
            if gaps:
                raise UnequalInstanceSets(f"{c}: {len(gaps)} instance(s) of the comparison set lack a decision or "
                                          f"replicate without a leakage abort (e.g. {gaps[:3]})")
        return ids

    def baseline_summary(self, cond: str, level: str = PRIMARY_LEVEL) -> dict:
        """A level-free baseline scored on the instance set of `level` (D-70)."""
        s = self._restricted(self.allowed(f"X|{level}")).summary(cond)
        s["instance_set"] = level
        return s

    def rows(self, cond: str, policy: Optional[str] = None) -> list[dict]:
        pol = policy or self.invalid_policy
        out = []
        for d in self.by_cond.get(cond, []):
            out.append({"instance_id": d["instance_id"], "bug_id": self.meta[d["instance_id"]]["bug_name"],
                        "project": self.meta[d["instance_id"]]["project"], "replicate": d["replicate"],
                        "y_true": self.lab[d["instance_id"]], "y_pred": score_label(d["label_raw"], pol)})
        return out

    def tensor(self, cond: str, reps: Optional[list[int]] = None, policy: Optional[str] = None) -> np.ndarray:
        rows = self.rows(cond, policy)
        reps = reps or sorted({r["replicate"] for r in rows}) or [0]
        return stats.count_tensor(rows, self.bugs, reps)

    def summary(self, cond: str) -> dict:
        T = self.tensor(cond)
        out = {"condition": cond, "n_instances": len({r["instance_id"] for r in self.rows(cond)}),
               "replicates": T.shape[1]}
        for m in ("f1", "mcc", "precision", "recall", "fpr"):   # D-74: MCC beside F1 in every table
            out[m] = stats.point_estimate(T, m)
            out[f"{m}_ci95"] = stats.percentile_ci(stats.bootstrap_metric(T, m, self.W))
        tot = T.sum(axis=0).mean(axis=0)
        out.update(TP=tot[0], FP=tot[1], FN=tot[2], TN=tot[3], pf_lost=tot[2])
        out["fnr"] = tot[2] / (tot[0] + tot[2]) if tot[0] + tot[2] else math.nan
        ds = self.by_cond[cond]
        rep_vals, ret_vals = [], []
        for rep in sorted({d["replicate"] for d in ds}):
            rs = [d for d in ds if d["replicate"] == rep]
            y = [self.lab[d["instance_id"]] for d in rs]
            p = [score_label(d["label_raw"], self.invalid_policy) for d in rs]
            w = [1.0 if t == PF else self.weights.get(d["instance_id"], 1.0) for t, d in zip(y, rs)]
            tp = sum(wi for t, q, wi in zip(y, p, w) if t == PF and q == PF)
            fp = sum(wi for t, q, wi in zip(y, p, w) if t == TF and q == PF)
            rep_vals.append(tp / (tp + fp) if tp + fp else math.nan)
            ret_vals.append(bug_level_retention([self.meta[d["instance_id"]]["bug_name"] for d in rs], y, p))
        out["precision_prev_adj"] = float(np.nanmean(rep_vals)) if rep_vals else math.nan
        out["bug_retention"] = float(np.nanmean(ret_vals)) if ret_vals else math.nan
        out["invalid_rate"] = float(np.mean([d["label_raw"] == arms_mod.INVALID for d in ds])) if ds else math.nan
        c = [d.get("cost", {}) for d in ds]
        if c and c[0]:
            out["calls_per_instance"] = float(np.mean([x.get("calls", 0) for x in c]))
            out["input_tokens_per_instance"] = float(np.mean([x.get("input_tokens", 0) for x in c]))
            out["output_tokens_per_instance"] = float(np.mean([x.get("output_tokens", 0) for x in c]))
            out["consumed_tokens_per_instance"] = out["input_tokens_per_instance"] + out["output_tokens_per_instance"]
            out["latency_s_per_instance"] = float(np.mean([x.get("latency_s", 0) for x in c]))
            out["cost_usd_per_instance"] = float(np.mean([x.get("cost_usd", 0) for x in c]))
        if cond.startswith("SC|") or cond.startswith("SC-T|"):
            aps = []
            for rep in sorted({d["replicate"] for d in ds}):
                rs = [d for d in ds if d["replicate"] == rep]
                aps.append(average_precision([self.lab[d["instance_id"]] for d in rs],
                                             [d["agreement"]["vote_share_pf"] for d in rs]))
            out["pr_auc_vote_share"] = float(np.nanmean(aps))
        if any(d["arm"] in ("DEB", "A1", "A2") for d in ds):
            sw = [d["agreement"].get("sided_with_last_presented") for d in ds]
            sw = [x for x in sw if x is not None]
            out["position_bias_rate"] = float(np.mean(sw)) if sw else math.nan
            out["no_evidence_rate"] = float(np.mean([bool(d["agreement"].get("no_evidence_cited")) for d in ds]))
        return out

    # ---- contrasts
    def contrast(self, name: str, a: list[str], b: list[str], metric: str = "f1",
                 restrict: Optional[set] = None) -> stats.Contrast:
        """Delta = mean_over(a) - mean_over(b), each list averaged (arm-averaged contrasts for H2a/H2b)."""
        ev = self._restricted(self.comparison_set(a + b, restrict))   # D-70: same instances for every side

        def boot(cs):
            return np.mean([stats.bootstrap_metric(ev.tensor(c), metric, ev.W) for c in cs], axis=0)

        def point(cs):
            return float(np.mean([stats.point_estimate(ev.tensor(c), metric) for c in cs]))

        d = boot(a) - boot(b)
        pa, pb = point(a), point(b)
        return stats.Contrast(name, metric, pa, pb, pa - pb, stats.percentile_ci(d, .95), stats.percentile_ci(d, .90),
                              stats.bootstrap_p_two_sided(d))

    def _restricted(self, ids: set) -> "Evaluation":
        e = Evaluation.__new__(Evaluation)
        e.lab = {k: v for k, v in self.lab.items() if k in ids}
        e.meta, e.weights, e.invalid_policy = self.meta, self.weights, self.invalid_policy
        e.exclusions = self.exclusions
        e.by_cond = {k: [d for d in v if d["instance_id"] in e.lab] for k, v in self.by_cond.items()}
        e.bugs = sorted({self.meta[i]["bug_name"] for i in e.lab})
        e.W = stats.bootstrap_weights(len(e.bugs))
        return e

    def majority_correct(self, cond: str) -> dict:
        votes = defaultdict(list)
        for r in self.rows(cond):
            votes[r["instance_id"]].append(r["y_pred"] == r["y_true"])
        return {i: sum(v) * 2 > len(v) for i, v in votes.items()}

    def per_project_f1(self, cond: str) -> dict:
        out = {}
        for p in sorted({self.meta[i]["project"] for i in self.lab}):
            rows = [r for r in self.rows(cond) if r["project"] == p]
            bugs = sorted({r["bug_id"] for r in rows})
            if not bugs:
                continue
            if not any(r["y_true"] == PF for r in rows):
                out[p] = math.nan     # D-70: no PF in the scored set -> F1 undefined, never 0
                continue
            T = stats.count_tensor(rows, bugs, sorted({r["replicate"] for r in rows}))
            out[p] = stats.point_estimate(T, "f1")
        return out

    def project_counts(self) -> dict:
        """Scored instances per project and class (labels the per-project figure)."""
        out: dict[str, dict] = {}
        for i, y in self.lab.items():
            c = out.setdefault(self.meta[i]["project"], {"PF": 0, "TF": 0})
            c["PF" if y == PF else "TF"] += 1
        return dict(sorted(out.items()))

    def lopo(self, a: list[str], b: list[str]) -> dict:
        out = {}
        for p in sorted({self.meta[i]["project"] for i in self.lab}):
            ids = {i for i in self.lab if self.meta[i]["project"] != p}
            e = self._restricted(ids)
            out[p] = float(np.mean([stats.point_estimate(e.tensor(c), "f1") for c in a])
                           - np.mean([stats.point_estimate(e.tensor(c), "f1") for c in b]))
        return out


F1_NOT_COMPARABLE = ("F1 is not comparable between D1 and D2: the PF prevalence of the judged sets differs, and F1 "
                     "moves with prevalence (KA, which always answers PF, scores F1 = 2p/(1+p) at PF prevalence p). "
                     "Compare arms within a dataset; across datasets read MCC and the prevalence-adjusted precision.")


def judged_prevalence(labels: list[dict], instance_ids) -> dict:
    """Class counts and PF prevalence of a judged sample, AMB excluded (reads labels only, never decisions)."""
    keep = set(instance_ids)
    c = defaultdict(int)
    for l in labels:
        if l["instance_id"] in keep:
            c[l["label"]] += 1
    pf, tf = c["PF"], c["TF"]
    return {"PF": pf, "TF": tf, "AMB": c["AMB"], "pf_prevalence": pf / (pf + tf) if pf + tf else math.nan,
            "tf_per_pf": tf / pf if pf else math.nan}


def prevalence_report(ev: "Evaluation", summ: dict, dataset: str, prevalences: Optional[dict] = None) -> dict:
    """D-74: KA's F1 at this dataset's PF prevalence, and F1 with MCC and the prevalence-adjusted precision beside it
    for every condition, so F1 is never read across datasets whose prevalences differ. The prevalence is that of
    the primary level's instance set (D-70), the set the baselines are scored on."""
    ids = ev.allowed(f"X|{PRIMARY_LEVEL}")
    pf = sum(ev.lab[i] == PF for i in ids)
    tf = len(ids) - pf
    p = pf / (pf + tf) if pf + tf else math.nan
    ka = summ.get("KA") or {}
    return {"dataset": dataset, "scored_set": f"{PRIMARY_LEVEL} instance set (D-70), AMB excluded",
            "PF": pf, "TF": tf, "pf_prevalence": p, "tf_per_pf": tf / pf if pf else math.nan,
            "ka_f1": ka.get("f1", math.nan), "ka_f1_expected_2p_over_1_plus_p": 2 * p / (1 + p) if pf else math.nan,
            "ka_mcc": ka.get("mcc", math.nan), "ka_precision_prev_adj": ka.get("precision_prev_adj", math.nan),
            "judged_sample_prevalence_by_dataset": prevalences or {},
            "note": F1_NOT_COMPARABLE,
            "conditions": [{"condition": c, "n_instances": s.get("n_instances"), "f1": s.get("f1"),
                            "mcc": s.get("mcc"), "precision": s.get("precision"),
                            "precision_prev_adj": s.get("precision_prev_adj"), "recall": s.get("recall")}
                           for c, s in summ.items()]}


def a3_reanalysis(decisions: list[dict], level: str = "S1") -> list[dict]:
    """A3: rescore SC with PF thresholds v >= 2/5 and v >= 4/5 (no new calls)."""
    out = []
    for d in decisions:
        if d["arm"] == "SC" and d.get("level") == level and (d.get("variant") or "full") == "full":
            for thr, tag in ((2 / 5, "v>=2/5"), (4 / 5, "v>=4/5")):
                agg = arms_mod.aggregate_votes(d["votes"], d["agreement"]["k"], threshold=thr)
                out.append({**d, "arm": "SC", "variant": f"A3 {tag}", "label_raw": agg["label_raw"]})
    return out


CONFIRMATORY = [
    ("H1", ["J1|S1"], ["R0"], None),
    ("H2a", ["J1|S1", "SC|S1", "DEB|S1"], ["J1|S0", "SC|S0", "DEB|S0"], "javadoc"),
    ("H2b", ["J1|S2", "SC|S2", "DEB|S2"], ["J1|S1", "SC|S1", "DEB|S1"], None),
    ("H3a", ["DEB|S1"], ["SC|S1"], None),
    ("H3b", ["SC|S1"], ["J1|S1"], None),
]


def confirmatory(ev: Evaluation, javadoc_ids: set) -> dict:
    fam = {}
    for metric in ("f1", "recall", "precision"):
        cs = []
        for name, a, b, sub in CONFIRMATORY:
            if not all(ev.by_cond.get(c) for c in a + b):
                continue
            cs.append(ev.contrast(name, a, b, metric, restrict=javadoc_ids if sub == "javadoc" else None))
        if metric == "f1":
            adj = stats.holm([c.p for c in cs])
        else:
            fam.setdefault("_secondary", []).extend(cs)
            continue
        for c, p in zip(cs, adj):
            c.p_holm = p
            c.conclusion = stats.decide(c)
        fam["f1"] = cs
    sec = fam.pop("_secondary", [])
    if sec:
        adj = stats.holm([c.p for c in sec])
        for c, p in zip(sec, adj):
            c.p_holm = p
            c.conclusion = stats.decide(c)
    fam["secondary"] = sec
    return {k: [asdict(c) for c in v] for k, v in fam.items()}
