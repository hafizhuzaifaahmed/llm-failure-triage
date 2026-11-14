"""Analysis of whole-method dependence probes (WDP; OPUS_EXECUTION_BRIEF.md version 2, sections 2.2 to 2.5).

    python scripts/extension/wdp_analysis.py --out results/extension/wdp/wdp_analysis.json

Status: exploratory; protocol frozen internally in Git before the run; not externally preregistered; designed after
the confirmation outcomes were known. Labels and stored judge votes are read here and nowhere earlier; nothing is
re-judged and no model is called.

One primary criterion (brief 2.4): on CONF-votes, dTNR = TNR(KUU + CD-U) - TNR(KUU) with a bug-level bootstrap 95%
interval; MET iff (i) KUU + CD-U loses exactly the bugs KUU loses, (ii) the interval's lower limit is above 0, (iii)
the decoupled PF test of Math_59 is not level U. Everything else is descriptive. Level U is reported only as "no
entry observed and throw-invariant".
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import stats  # noqa: E402
from triage_dep import levels as lv  # noqa: E402
from triage_ext import ledger as lg  # noqa: E402
from triage_ext import policy  # noqa: E402

SEED = 20261113
B = 10_000
PI_ASSUMED = 0.05
PF, TF = policy.PF, policy.TF
STATUS = ("exploratory; protocol frozen internally in Git before the run; not externally preregistered; designed "
          "after the confirmation outcomes were known")
U_WORDS = "no entry observed and throw-invariant"
TECHNICAL_ND = ("x_throw_err", "x_throw_na", "x_ret_err", "no_x_ret", "first_order_unusable")   # plus excluded:*, malformed:*
LEVEL_KEYS = ("FS", "WS", "RI", "U", "ND")
EXPECTED_POPULATIONS = {"CONF-all": {"instances": 572, "PF": 55, "bugs_with_PF": 21},
                        "CONF-votes": {"instances": 561, "PF": 54},
                        "PILOT-all": {"instances": 356, "PF": 60, "bugs_with_PF": 22},
                        "PILOT-votes": {"instances": 177, "PF": 60},
                        "CTRL": {"instances": 246}}
REGISTERED_ROWS = ("KUU", "KUU+CD", "2-of-3")

DATASETS = {   # frame -> (WDP run, first-order run, labels file)
    "D1-test": ("WDP_D1_TEST", "CFP_D1_TEST", "data/ground_truth_store/labels_D1.jsonl"),
    "F1": ("WDP_CONF_F1", "CFP_CONF_F1", "data/extension/confirm/F1/labels_D1C_F1.jsonl"),
    "F2": ("WDP_CONF_F2", "CFP_CONF_F2", "data/extension/confirm/F2/labels_D1C_F2.jsonl"),
    "CTRL": ("WDP_CONF_CTRL", "CFP_CONF_CTRL", "data/extension/confirm/CTRL/labels_D1C_CTRL.jsonl"),
}
CONF_VOTES = {fr: {"M1": f"data/extension/confirm/{fr}/votes/LOCAL_CONF_VOTE_M1_{fr}/decisions.jsonl",
                   "M2": f"data/extension/confirm/{fr}/votes/LOCAL_CONF_VOTE_M2_{fr}/decisions.jsonl",
                   "M3": f"data/extension/confirm/{fr}/votes/LOCAL_CONF_VOTE_E6B_{fr}/decisions.jsonl"}
              for fr in ("F1", "F2")}
CONF_REPLICATE = 80


def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# ---------------------------------------------------------------------------------------------------------------
# rows
# ---------------------------------------------------------------------------------------------------------------
def n_executions(rec: dict) -> int:
    """JVM test executions the WDP engine spent on one test (baseline, variant runs, re-runs of a pass)."""
    if rec.get("baseline") is None:
        return 0
    runs = sum(1 for v in rec.get("variants") or [] if v.get("class") is not None)
    reruns = sum(1 for v in rec.get("variants") or [] if v.get("outcome") == "pass")
    return 1 + runs + reruns


def make_rows(frame: str, labels: list, wdp_led: dict, fo_led: dict) -> list:
    """One row per labelled instance (PF or TF) of a frame. Completeness is enforced earlier by the raw-ledger gate;
    a missing record here is level ND excluded:no_record, never an error."""
    rows = []
    for l in labels:
        if l["label"] not in ("PF", "TF"):
            continue
        i = l["instance_id"]
        raw = wdp_led.get(i)
        rec = raw if isinstance(raw, dict) else {"variants": [], "excluded": None}
        fo = fo_led.get(i)
        s = fo["summary"] if fo else None
        level, reason = lv.level(raw, s)
        usable = bool(s) and not s.get("excluded")
        rows.append({"id": i, "bug": l["bug_name"], "project": l["project"], "frame": frame, "label": l["label"],
                     "y": 1 if l["label"] == "PF" else 0, "level": level, "reason": reason, "summary": s,
                     "decoupled": usable and bool(s.get("decoupled")),
                     "low_mutant": usable and s.get("n_compiled", 0) < lg.MIN_MUTANTS and not s.get("coupled"),
                     "x_throw": lv.x_throw(rec), "x_ret": lv.x_ret(rec), "entered": rec.get("entered"),
                     "surfaced": rec.get("surfaced"), "excluded": rec.get("excluded"), "wdp": rec,
                     "seconds": rec.get("seconds"), "executions": n_executions(rec),
                     "fo_seconds": fo.get("seconds") if fo else None})
    return rows


def level_key(r: dict) -> str:
    return r["level"] if r["level"] != "ND" else f"ND:{r['reason']}"


def ladder(rows: list) -> dict:
    out = {"n": len(rows)}
    for lab in ("PF", "TF"):
        sub = [r for r in rows if r["label"] == lab]
        c = Counter(r["level"] for r in sub)
        out[lab] = {"n": len(sub), **{k: c.get(k, 0) for k in LEVEL_KEYS},
                    "ND_by_reason": dict(sorted(Counter(r["reason"] for r in sub if r["level"] == "ND").items()))}
    return out


def by(rows, key):
    g = defaultdict(list)
    for r in rows:
        g[key(r)].append(r)
    return {k: ladder(v) for k, v in sorted(g.items())}


# ---------------------------------------------------------------------------------------------------------------
# rules and metrics
# ---------------------------------------------------------------------------------------------------------------
def cp_upper(k: int, n: int) -> float | None:
    if not n:
        return None
    return round(float(sps.beta.ppf(0.95, k + 1, n - k)), 4) if n > k else 1.0


def rule_keep(rows: list, base: dict, cert=None) -> np.ndarray:
    """1 = keep. base: id -> PF/TF label; cert: None, 'CD', 'CD-U' or 'CD-UR'."""
    out = []
    for r in rows:
        lab = PF if base[r["id"]] == PF else TF
        if cert == "CD":
            lab = policy.decoupled_discard(lab, r["summary"])
        elif cert == "CD-U":
            lab = lv.cd_u(lab, r["level"])
        elif cert == "CD-UR":
            lab = lv.cd_ur(lab, r["level"])
        out.append(1.0 if lab == PF else 0.0)
    return np.array(out)


class Pop:
    """A comparison population: rows, labels, bug index and one set of bootstrap weights (shared by every rule)."""

    def __init__(self, rows: list, seed: int = SEED):
        self.rows = rows
        self.y = np.array([r["y"] for r in rows])
        self.bugs = sorted({r["bug"] for r in rows})
        self.bidx = np.array([self.bugs.index(r["bug"]) for r in rows], dtype=int)
        self.Wb = stats.bootstrap_weights(len(self.bugs), B=B, seed=seed)
        self.W = self.Wb[:, self.bidx] if len(rows) else np.zeros((B, 0))

    def metrics(self, keep: np.ndarray, w=None) -> dict:
        w = np.ones((1, len(self.rows))) if w is None else w
        pf, tf = (self.y == 1), (self.y == 0)
        tpr = (w * pf * keep).sum(-1) / np.maximum((w * pf).sum(-1), 1e-12)
        tnr = (w * tf * (1 - keep)).sum(-1) / np.maximum((w * tf).sum(-1), 1e-12)
        return {"TPR": tpr, "TNR": tnr, "BA": (tpr + tnr) / 2, "PF_lost": (w * pf * (1 - keep)).sum(-1)}

    def bugs_lost(self, keep: np.ndarray) -> list[str]:
        has, kept = np.zeros(len(self.bugs)), np.zeros(len(self.bugs))
        np.add.at(has, self.bidx, (self.y == 1).astype(float))
        np.add.at(kept, self.bidx, ((self.y == 1) * keep).astype(float))
        return [b for b, h, k in zip(self.bugs, has, kept) if h > 0 and k == 0]

    def bug_lost_boot(self, keep: np.ndarray) -> np.ndarray:
        has, kept = np.zeros(len(self.bugs)), np.zeros(len(self.bugs))
        np.add.at(has, self.bidx, (self.y == 1).astype(float))
        np.add.at(kept, self.bidx, ((self.y == 1) * keep).astype(float))
        return self.Wb @ ((has > 0) & (kept == 0)).astype(float)

    def bugs_with_pf(self) -> int:
        return len({r["bug"] for r in self.rows if r["y"] == 1})

    def rule_row(self, keep: np.ndarray) -> dict:
        m = {k: float(v[0]) for k, v in self.metrics(keep).items()}
        lost = self.bugs_lost(keep)
        n_pf_bugs = self.bugs_with_pf()
        kept = int(keep.sum())
        pf_kept = int((keep * (self.y == 1)).sum())
        tf_kept = kept - pf_kept
        tpr, tnr = m["TPR"], m["TNR"]
        return {**{k: round(v, 4) for k, v in m.items()}, "PF_lost": int(round(m["PF_lost"])),
                "bugs_with_PF": n_pf_bugs, "bugs_lost": len(lost), "bugs_lost_names": lost,
                "upper95_bug_loss_rate": cp_upper(len(lost), n_pf_bugs), "tests_kept": kept,
                "PF_share_of_kept": round(pf_kept / kept, 4) if kept else None,
                "wrong_kept_per_PF_kept_labelled": round(tf_kept / pf_kept, 4) if pf_kept else None,
                "wrong_kept_per_PF_kept_at_5pct": (round((1 - PI_ASSUMED) * (1 - tnr) / (PI_ASSUMED * tpr), 4)
                                                   if tpr > 0 else None)}

    def paired(self, keep_a: np.ndarray, keep_b: np.ndarray) -> dict:
        """a minus b, with identical resamples for both sides."""
        pa, pb = self.metrics(keep_a), self.metrics(keep_b)
        ba, bb = self.metrics(keep_a, self.W), self.metrics(keep_b, self.W)
        out = {}
        for k in ("TPR", "TNR", "BA", "PF_lost"):
            lo, hi = stats.percentile_ci(ba[k] - bb[k], 0.95)
            out[k] = {"difference": round(float(pa[k][0] - pb[k][0]), 4), "ci95": [round(lo, 4), round(hi, 4)]}
        lo, hi = stats.percentile_ci(self.bug_lost_boot(keep_a) - self.bug_lost_boot(keep_b), 0.95)
        out["bugs_lost"] = {"difference": len(self.bugs_lost(keep_a)) - len(self.bugs_lost(keep_b)),
                            "ci95": [round(lo, 4), round(hi, 4)]}
        return out

    def rate_contrast(self, flag: np.ndarray) -> dict:
        """P(flag | TF) - P(flag | PF), with a bug-level bootstrap interval."""
        pf, tf = (self.y == 1).astype(float), (self.y == 0).astype(float)

        def rate(w, mask):
            den = (w * mask).sum(-1)
            with np.errstate(invalid="ignore", divide="ignore"):
                return np.where(den > 0, (w * mask * flag).sum(-1) / den, np.nan)
        one = np.ones((1, len(self.rows)))
        point = float((rate(one, tf) - rate(one, pf))[0]) if pf.sum() and tf.sum() else None
        lo, hi = stats.percentile_ci(rate(self.W, tf) - rate(self.W, pf), 0.95)
        return {"TF_flagged": int((flag * tf).sum()), "TF": int(tf.sum()), "PF_flagged": int((flag * pf).sum()),
                "PF": int(pf.sum()), "difference_TF_minus_PF": None if point is None else round(point, 4),
                "ci95": [round(lo, 4), round(hi, 4)]}


def u_contrasts(rows: list, seed: int = SEED) -> dict:
    p = Pop(rows, seed)
    return {"U": p.rate_contrast(np.array([1.0 if r["level"] == "U" else 0.0 for r in rows])),
            "U_or_RI": p.rate_contrast(np.array([1.0 if r["level"] in ("U", "RI") else 0.0 for r in rows]))}


RULES = (("KUU", "KUU", None), ("2-of-3", "2-of-3", None), ("keep-all", "keep-all", None), ("KUU+CD", "KUU", "CD"),
         ("KUU+CD-U", "KUU", "CD-U"), ("KUU+CD-UR", "KUU", "CD-UR"), ("2-of-3+CD-U", "2-of-3", "CD-U"),
         ("keep-all+CD-U", "keep-all", "CD-U"))


def rule_table(pop: Pop, bases: dict) -> dict:
    out = {"instances": len(pop.rows), "PF": int(pop.y.sum()), "bugs": len(pop.bugs), "bugs_with_PF": pop.bugs_with_pf()}
    for name, base, cert in RULES:
        out[name] = pop.rule_row(rule_keep(pop.rows, bases[base], cert))
    return out


def primary_contrast(pop: Pop, bases: dict) -> dict:
    k0 = rule_keep(pop.rows, bases["KUU"])
    k1 = rule_keep(pop.rows, bases["KUU"], "CD-U")
    lost0, lost1 = pop.bugs_lost(k0), pop.bugs_lost(k1)
    return {"contrast": "TNR(KUU + CD-U) - TNR(KUU)", "paired": pop.paired(k1, k0),
            "bugs_lost_KUU": lost0, "bugs_lost_KUU_CDU": lost1,
            "additional_bugs_lost": sorted(set(lost1) - set(lost0)), "safety_holds": set(lost1) == set(lost0)}


def decoupled_pf_levels(rows: list, bug: str) -> list[str]:
    return [r["level"] for r in rows if r["bug"] == bug and r["y"] == 1 and r["decoupled"]]


# ---------------------------------------------------------------------------------------------------------------
# the analysis
# ---------------------------------------------------------------------------------------------------------------
def analyse(frames: dict, conf_bases: dict, pilot_bases: dict, registered: dict | None = None,
            seed: int = SEED, raw_gate: dict | None = None) -> dict:
    """frames: frame -> rows (D1-test, F1, F2, CTRL); conf_bases / pilot_bases: {"ids": [...], "KUU": {id: label},
    "2-of-3": {id: label}} for the instances with three votes; registered: the registered analysis's rule rows."""
    conf_all = frames.get("F1", []) + frames.get("F2", [])
    pilot_all = frames.get("D1-test", [])
    ctrl = frames.get("CTRL", [])
    byid_conf = {r["id"]: r for r in conf_all}
    byid_pilot = {r["id"]: r for r in pilot_all}
    for name, bases, byid in (("CONF-votes", conf_bases, byid_conf), ("PILOT-votes", pilot_bases, byid_pilot)):
        missing = [i for i in bases["ids"] if i not in byid]
        if missing:
            raise ValueError(f"{name}: {len(missing)} voted instances have no row, e.g. {missing[:3]}")
    conf_votes = [byid_conf[i] for i in conf_bases["ids"]]
    pilot_votes = [byid_pilot[i] for i in pilot_bases["ids"]]
    for bases, rows in ((conf_bases, conf_votes), (pilot_bases, pilot_votes)):
        bases["keep-all"] = {r["id"]: PF for r in rows}
    out = {"status": STATUS, "level_U_means": U_WORDS, "seed": seed, "resamples": B, "model_calls": 0}

    def pop_counts(rows):
        return {"instances": len(rows), "PF": sum(r["y"] for r in rows), "TF": sum(1 - r["y"] for r in rows),
                "bugs": len({r["bug"] for r in rows}), "bugs_with_PF": len({r["bug"] for r in rows if r["y"]})}
    pops = {"CONF-all": conf_all, "CONF-votes": conf_votes, "PILOT-all": pilot_all, "PILOT-votes": pilot_votes,
            "CTRL": ctrl}
    out["populations"] = {k: pop_counts(v) for k, v in pops.items()}

    # ---- primary ---------------------------------------------------------------------------------------------
    cpop = Pop(conf_votes, seed)
    prim = primary_contrast(cpop, conf_bases)
    m59 = decoupled_pf_levels(conf_all, "Math_59")
    lo = prim["paired"]["TNR"]["ci95"][0]
    crit = {"i_safety": prim["safety_holds"], "ii_ci_lower_above_0": bool(lo > 0),
            "iii_math59_decoupled_pf_not_U": bool(m59) and "U" not in m59,
            "math59_decoupled_pf_levels": m59}
    crit["result"] = "MET" if (crit["i_safety"] and crit["ii_ci_lower_above_0"]
                               and crit["iii_math59_decoupled_pf_not_U"]) else "NOT MET"
    if not m59:
        crit["note"] = "no decoupled PF test of Math_59 was found, so (iii) could not be established"
    out["primary"] = {**prim, "criterion": crit}

    # ---- secondary 1, 2 --------------------------------------------------------------------------------------
    ppop = Pop(pilot_votes, seed)
    pprim = primary_contrast(ppop, pilot_bases)
    out["secondary"] = {"1_pilot": {**pprim, "codec13_decoupled_pf_levels": decoupled_pf_levels(pilot_all, "Codec_13")}}
    out["secondary"]["2_CDU_vs_CD"] = cpop.paired(rule_keep(conf_votes, conf_bases["KUU"], "CD-U"),
                                                  rule_keep(conf_votes, conf_bases["KUU"], "CD"))
    if crit["result"] == "MET" and not pprim["additional_bugs_lost"]:
        n = cpop.bugs_with_pf() + ppop.bugs_with_pf()
        out["pooled_bound"] = {"additional_bugs_lost": 0, "bugs_with_PF": n,
                               "upper95": round(1 - 0.05 ** (1 / n), 4) if n else None,
                               "caveat": "the rule was designed with knowledge of these bugs, so the bound is "
                                         "optimistic and is not a guarantee"}
    # ---- secondary 3 to 5 ------------------------------------------------------------------------------------
    out["secondary"]["3_level_U_by_label"] = {"CONF-all": u_contrasts(conf_all, seed),
                                              "PILOT-all": u_contrasts(pilot_all, seed)}
    allrows = conf_all + pilot_all + ctrl
    out["secondary"]["4_ladder"] = {
        "by_dataset": {"CONF": ladder(conf_all), "PILOT": ladder(pilot_all), "CTRL": ladder(ctrl)},
        "by_frame": by(allrows, lambda r: r["frame"]),
        "by_project": by(allrows, lambda r: r["project"]),
        "registered_decoupled": {"CONF": ladder([r for r in conf_all if r["decoupled"]]),
                                 "PILOT": ladder([r for r in pilot_all if r["decoupled"]]),
                                 "CTRL": ladder([r for r in ctrl if r["decoupled"]])}}
    out["secondary"]["5_low_mutant_stratum"] = {"CONF": ladder([r for r in conf_all if r["low_mutant"]]),
                                                "PILOT": ladder([r for r in pilot_all if r["low_mutant"]]),
                                                "CTRL": ladder([r for r in ctrl if r["low_mutant"]])}
    # ---- secondary 6, 7: rule tables (workload columns are in each row) -----------------------------------------
    out["secondary"]["6_rules"] = {"CONF-votes": rule_table(cpop, conf_bases),
                                   "PILOT-votes": rule_table(ppop, pilot_bases)}
    # ---- secondary 8: pre-filter -----------------------------------------------------------------------------
    pre = {}
    for name, rows, bases in (("CONF-votes", conf_votes, conf_bases), ("PILOT-votes", pilot_votes, pilot_bases)):
        u = [r for r in rows if r["level"] == "U"]
        pre[name] = {"level_U": len(u), "share_level_U": round(len(u) / len(rows), 4) if rows else None,
                     "judge_calls_avoided": 3 * len(u),
                     "level_U_already_discarded_by_KUU": sum(1 for r in u if bases["KUU"][r["id"]] != PF)}
    for name, rows in (("CONF-all", conf_all), ("PILOT-all", pilot_all), ("CTRL", ctrl)):
        u = sum(1 for r in rows if r["level"] == "U")
        pre[name] = {"level_U": u, "share_level_U": round(u / len(rows), 4) if rows else None}
    out["secondary"]["8_prefilter"] = pre
    # ---- secondary 9: heterogeneity --------------------------------------------------------------------------
    het = {}

    def sub(name, keep_row):
        cv = [r for r in conf_votes if keep_row(r)]
        ca = [r for r in conf_all if keep_row(r)]
        h = {"instances": len(cv), "PF": sum(r["y"] for r in cv)}
        if cv and 0 < h["PF"] < len(cv):
            h["primary"] = primary_contrast(Pop(cv, seed), conf_bases)
        if ca and 0 < sum(r["y"] for r in ca) < len(ca):
            h["level_U_by_label"] = u_contrasts(ca, seed)
        het[name] = h
    sub("F1", lambda r: r["frame"] == "F1")
    sub("F2", lambda r: r["frame"] == "F2")
    sub("without_Jackson", lambda r: not r["project"].startswith("Jackson"))
    lopo = {}
    for p in sorted({r["project"] for r in conf_votes}):
        cv = [r for r in conf_votes if r["project"] != p]
        if not cv or not any(r["y"] for r in cv) or all(r["y"] for r in cv):
            continue
        pp = Pop(cv, seed)
        k0, k1 = rule_keep(cv, conf_bases["KUU"]), rule_keep(cv, conf_bases["KUU"], "CD-U")
        lopo[p] = {"dTNR": round(float(pp.metrics(k1)["TNR"][0] - pp.metrics(k0)["TNR"][0]), 4),
                   "additional_bugs_lost": sorted(set(pp.bugs_lost(k1)) - set(pp.bugs_lost(k0)))}
    het["leave_one_project_out"] = lopo
    het["leave_one_project_out_levels"] = lopo_levels(conf_all)
    out["secondary"]["9_heterogeneity"] = het
    # ---- secondary 10, 11, 12 ----------------------------------------------------------------------------------
    out["secondary"]["10_control"] = ladder(ctrl)
    cost = {}
    for fr, rows in frames.items():
        sec = [r["seconds"] for r in rows if r["seconds"] is not None]
        ex = [r["executions"] for r in rows]
        fos = [r["fo_seconds"] for r in rows if r["fo_seconds"] is not None]
        cost[fr] = {"tests": len(rows), "seconds_mean": round(float(np.mean(sec)), 3) if sec else None,
                    "seconds_total": round(float(np.sum(sec)), 1) if sec else None,
                    "executions_mean": round(float(np.mean(ex)), 3) if ex else None,
                    "first_order_seconds_mean": round(float(np.mean(fos)), 3) if fos else None,
                    "first_order_seconds_total": round(float(np.sum(fos)), 1) if fos else None}
    out["secondary"]["11_cost"] = cost
    out["secondary"]["12_diagnostics"] = {fr: diagnostics(rows) for fr, rows in frames.items()}
    out["quality_checks"] = quality_checks(frames, out, registered, raw_gate)
    return out


def point_contrast(rows: list, flag) -> dict:
    """P(flag | TF) - P(flag | PF) as a point estimate with its four counts (no interval, no test)."""
    tf = [r for r in rows if r["y"] == 0]
    pf = [r for r in rows if r["y"] == 1]
    a, b = sum(1 for r in tf if flag(r)), sum(1 for r in pf if flag(r))
    return {"TF_flagged": a, "TF": len(tf), "PF_flagged": b, "PF": len(pf),
            "difference_TF_minus_PF": round(a / len(tf) - b / len(pf), 4) if tf and pf else None}


def lopo_levels(conf_all: list) -> dict:
    """Brief 11.3: for each project of CONF-all whose removal leaves a PF and a TF test, the level-U and U-or-RI
    contrasts on the remaining tests (descriptive)."""
    out = {}
    for p in sorted({r["project"] for r in conf_all}):
        rest = [r for r in conf_all if r["project"] != p]
        if not any(r["y"] == 1 for r in rest) or not any(r["y"] == 0 for r in rest):
            continue
        out[p] = {"U": point_contrast(rest, lambda r: r["level"] == "U"),
                  "U_or_RI": point_contrast(rest, lambda r: r["level"] in ("U", "RI"))}
    return out


def diagnostics(rows: list) -> dict:
    out = {}
    for lab in ("PF", "TF"):
        sub = [r for r in rows if r["label"] == lab]
        nd = Counter(r["reason"] for r in sub if r["level"] == "ND")
        out[lab] = {
            "n": len(sub),
            "exclusions": dict(sorted(Counter(r["excluded"] for r in sub if r["excluded"]).items())),
            "ND_by_reason": dict(sorted(nd.items())),
            "ND_throw_swallowed": nd.get("throw_swallowed", 0), "ND_swallow_risk": nd.get("swallow_risk", 0),
            "malformed_ids": sorted(r["id"] for r in sub if r["level"] == "ND" and r["reason"].startswith("malformed:")),
            "no_record_ids": sorted(r["id"] for r in sub if r["reason"] == lv.NO_RECORD),
            "first_order_unusable_ids": sorted(r["id"] for r in sub if r["reason"] == "first_order_unusable"),
            "variants_not_compiled": dict(sorted(Counter(str(v.get("id")) for r in sub if not r["excluded"]
                                                         for v in _vs(r) if not v.get("compiled")).items())),
            "variant_ERR": dict(sorted(Counter(str(v.get("id")) for r in sub for v in _vs(r)
                                               if v.get("class") == lg.ERR).items())),
            "entered_by_level": {k: dict(sorted(Counter(str(r["entered"]) for r in sub if r["level"] == k).items()))
                                 for k in LEVEL_KEYS},
            "marker_violations": sum(1 for r in sub if r["surfaced"] is True and r["entered"] is not True),
            "surfaced": sum(1 for r in sub if r["surfaced"] is True),
            "x_throw_changed_not_entered": sum(1 for r in sub if r["x_throw"] == lv.CHANGED and r["entered"] is False),
            "x_throw_same_x_ret_changed": sum(1 for r in sub if r["x_throw"] == lv.SAME and lv.CHANGED in r["x_ret"]),
        }
    return out


def _vs(r: dict) -> list:
    v = r["wdp"].get("variants")
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def technical_nd(r: dict) -> bool:
    return r["level"] == "ND" and (r["reason"].startswith("excluded:") or r["reason"].startswith("malformed:")
                                   or r["reason"] in TECHNICAL_ND)


def quality_checks(frames: dict, out: dict, registered: dict | None, raw_gate: dict | None = None) -> dict:
    q = {"per_run": {}, "raw_ledger_gate": raw_gate}
    for fr, rows in frames.items():
        viol = sum(1 for r in rows if r["surfaced"] is True and r["entered"] is not True)
        tech = sum(1 for r in rows if technical_nd(r))
        q["per_run"][fr] = {"scored_rows": len(rows), "marker_violations": viol,
                            "surfaced": sum(1 for r in rows if r["surfaced"] is True), "technical_ND": tech,
                            "malformed": sum(1 for r in rows if r["level"] == "ND" and r["reason"].startswith("malformed:")), "technical_ND_share": round(tech / len(rows), 4) if rows else None,
                            "passes": viol == 0 and (not rows or tech / len(rows) <= 0.05)}
    q["populations_match_brief"] = {k: {f: (out["populations"][k][f], v) for f, v in exp.items()}
                                    for k, exp in EXPECTED_POPULATIONS.items()}
    q["populations_ok"] = all(a == b for d in q["populations_match_brief"].values() for a, b in d.values())
    if registered is not None:
        mine = out["secondary"]["6_rules"]["CONF-votes"]
        cmp = {}
        for name in REGISTERED_ROWS:
            cmp[name] = {k: (mine[name][k], registered[name][k]) for k in ("TPR", "TNR", "BA", "PF_lost", "bugs_lost")}
        q["registered_rows"] = cmp
        q["registered_rows_ok"] = all(round(float(a), 4) == round(float(b), 4) for d in cmp.values()
                                      for a, b in d.values())
    q["ladder_reportable"] = all(v["passes"] for v in q["per_run"].values()) and q["populations_ok"] and \
        q.get("registered_rows_ok", False)
    return q


# ---------------------------------------------------------------------------------------------------------------
# loading (labels and votes are read here and nowhere earlier)
# ---------------------------------------------------------------------------------------------------------------
def load_frames(split: str = "test") -> dict:
    frames = {}
    for fr, (wrun, frun, lab) in DATASETS.items():
        labels = read_jsonl(ROOT / lab)
        if fr == "D1-test":
            labels = [l for l in labels if l.get("split") == split]
        wled = {r["instance_id"]: r for r in read_jsonl(ROOT / "results" / "extension" / "wdp" / wrun / "ledger.jsonl")}
        fled = {r["instance_id"]: r for r in read_jsonl(ROOT / "results" / "extension" / "probes" / frun / "ledger.jsonl")}
        frames[fr] = make_rows(fr, labels, wled, fled)
    return frames


def load_conf_bases(frames: dict) -> dict:
    from triage import revision_metrics as rm
    votes = {}
    for fr, files in CONF_VOTES.items():
        for model, f in files.items():
            for d in read_jsonl(ROOT / f):
                if d["arm"] == "J1" and d.get("level") == "S1" and (d.get("variant") or "full") == "full" \
                        and d["replicate"] == CONF_REPLICATE:
                    votes.setdefault(d["instance_id"], {})[model] = d["label_raw"]
    ids = [r["id"] for r in frames["F1"] + frames["F2"] if len(votes.get(r["id"], {})) == 3]
    return {"ids": ids,
            "KUU": {i: rm.k_of_n([votes[i].get(m) for m in ("M1", "M2", "M3")], 3) for i in ids},
            "2-of-3": {i: rm.k_of_n([votes[i].get(m) for m in ("M1", "M2", "M3")], 2) for i in ids}}


def load_pilot_bases() -> dict:
    sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
    import revision_common as rc          # exactly as ext1_probe_analysis.py loads the D-110 common set
    d = rc.build("D1")
    ids = list(d.ids)
    return {"ids": ids, "KUU": {i: d.preds["KUU|S1"][0].get(i) for i in ids},
            "2-of-3": {i: d.preds["MAJ3|S1"][0].get(i) for i in ids}}


def raw_ledger_check(ledger_path, instance_ids) -> dict:
    """Spec invariant 8 and brief 11.2 on ONE ledger, over every raw record whatever its label: completeness against
    the run's instance ids (one record each) and marker consistency (surfaced true implies entered true)."""
    ids = []
    violations, unreadable, surfaced = [], 0, 0
    with open(ledger_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except ValueError:
                unreadable += 1
                continue
            if not isinstance(r, dict):
                unreadable += 1
                continue
            ids.append(r.get("instance_id"))
            surfaced += r.get("surfaced") is True
            if r.get("surfaced") is True and r.get("entered") is not True:
                violations.append(r.get("instance_id"))
    c = Counter(ids)
    want = set(instance_ids)
    missing = sorted(want - set(c))
    duplicated = sorted(str(i) for i, n in c.items() if n > 1)
    extra = sorted(str(i) for i in set(c) - want)
    ok = not (missing or duplicated or extra or violations or unreadable)
    return {"ledger": str(ledger_path), "records": len(ids), "instances": len(want),
            "surfaced": surfaced, "marker_violations": sorted(map(str, violations)), "missing": missing,
            "duplicated": duplicated, "extra": extra, "unreadable_lines": unreadable, "passes": ok}


def raw_ledger_gate(out_dir: Path) -> dict:
    """Run raw_ledger_check on the four evaluation ledgers before any label or vote is read. On failure write
    <out_dir>/wdp_analysis_ABORTED.json, print it and exit non-zero."""
    res = {}
    for name, (fr, inst_file, split) in EVALUATION_LEDGERS.items():
        p = ROOT / "results" / "extension" / "wdp" / name / "ledger.jsonl"
        try:
            ids = [r["instance_id"] for r in read_jsonl(ROOT / inst_file) if split is None or r.get("split") == split]
            res[name] = raw_ledger_check(p, ids) if p.exists() else {"ledger": str(p), "passes": False,
                                                                     "error": "ledger missing"}
        except (OSError, ValueError, KeyError) as e:
            res[name] = {"ledger": str(p), "passes": False, "error": repr(e)}
    gate = {"runs": res, "passes": all(v["passes"] for v in res.values())}
    if not gate["passes"]:
        doc = {"status": "ABORTED before any label or vote was read (stop condition 5); nothing repaired",
               "failed_runs": [k for k, v in res.items() if not v["passes"]], **gate}
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "wdp_analysis_ABORTED.json").write_text(json.dumps(doc, indent=1), encoding="utf-8", newline="\n")
        print(json.dumps(doc, indent=1))
        sys.exit(1)
    return gate


EVALUATION_LEDGERS = {   # WDP run -> (frame, instances file, split)
    "WDP_D1_TEST": ("D1-test", "data/processed/instances_D1.jsonl", "test"),
    "WDP_CONF_F1": ("F1", "data/extension/confirm/F1/instances_D1C_F1.jsonl", None),
    "WDP_CONF_F2": ("F2", "data/extension/confirm/F2/instances_D1C_F2.jsonl", None),
    "WDP_CONF_CTRL": ("CTRL", "data/extension/confirm/CTRL/instances_D1C_CTRL.jsonl", None),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results" / "extension" / "wdp" / "wdp_analysis.json"))
    a = ap.parse_args()
    gate = raw_ledger_gate(Path(a.out).parent)          # first step: no label or vote has been read yet
    frames = load_frames()
    reg_path = ROOT / "results" / "extension" / "confirm" / "confirm_analysis_CFP_CONF_ALL.json"
    registered = json.loads(reg_path.read_text(encoding="utf-8"))["rules"] if reg_path.exists() else None
    out = analyse(frames, load_conf_bases(frames), load_pilot_bases(), registered, raw_gate=gate)
    dest = Path(a.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps({"status": out["status"], "populations": out["populations"],
                      "criterion": out["primary"]["criterion"]}, indent=1))


if __name__ == "__main__":
    main()
