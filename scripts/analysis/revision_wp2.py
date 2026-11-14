"""Analysis of the WP2 local runs (D-124 to D-127; exploratory) and the judge gate table (WP2.5). Zero calls.

  gates   every local judge's development-gate outcome (committed gate files)
  tf296   D-124: merge checks, then M1 J1, KUU and KUU-NG on the 60 PF + all judged TF of D1-test (natural prevalence)
  greedy  D-125: M1 J1 at temperature 0 vs the frozen 0.7
  think   D-126: probe summary; the held-out thinking run if it exists
  deb8    D-127: eight DEB replicates (3 committed + 5 new), per-replicate rates and their spread
A part whose run is missing or incomplete is reported as such, never filled in.

    python scripts/analysis/revision_wp2.py  -> results/revision/wp2_local_runs.json
"""
import ast
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import revision_common as rc  # noqa: E402
from triage import config, stats  # noqa: E402
from triage import revision_metrics as rm  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

OUT = rc.OUT / "wp2_local_runs.json"
REV = rc.OUT / "runs"
DEV = rc.ROOT / "results" / "dev"
GATES = {"M1 (Qwen3.5 9B)": DEV / "GATE_M1b", "M2 (Gemma 4 12B)": DEV / "CHECK_M2",
         "E6b (Ministral 3 14B)": DEV / "CHECK_E6B_ministral-3_14b-instruct-2512-q4_K_M",
         "NG (Llama 3.1 8B)": DEV / "CHECK_KUUNG_llama3.1_8b-instruct-q4_K_M"}
PROFILES = {"M1": "configs/kuu_m1.json", "M2": "configs/kuu_m2.json", "E6B": "configs/e6b.json", "NG": "configs/kuung.json"}
COMMITTED = {"M1": [("LOCAL_HO_E8_VOTE_M1", 10), ("LOCAL_HO_KUUNG_D1_M1", 30)], "M2": [("LOCAL_HO_E8_VOTE_M2", 10)],
             "E6B": [("LOCAL_HO_E8_VOTE_E6B", 10), ("LOCAL_HO_KUUNG_D1_E6B", 30)], "NG": [("LOCAL_HO_KUUNG_D1_NG", 30)]}
DEB_TABLE_TOKENS_KEY = "DEB|S1"


def _cost(d):
    c = d.get("cost")
    return (ast.literal_eval(c) if isinstance(c, str) else c) or {}


def s1(d):
    return d.get("level") == "S1" and (d.get("variant") or "full") == "full"


def gates():
    out = {}
    for name, d in GATES.items():
        g = json.loads((d / "dev_gates.json").read_text(encoding="utf-8"))
        det = g.get("G_d_detail") or {}
        out[name] = {"G_a": g.get("G_a"), "G_b": g.get("G_b"), "G_c": g.get("G_c"), "G_d": g.get("G_d"),
                     "J1_f1_dev": det.get("J1_f1"), "R0_f1_dev": det.get("R0_f1"), "KA_f1_dev": det.get("KA_f1"),
                     "source": d.relative_to(rc.ROOT).as_posix()}
    out["Claude Sonnet 5.5"] = {"G_a": None, "G_b": None, "G_c": None, "G_d": None,
                                "note": "frontier reference point (E9/E9b); no development gate was run"}
    out["Qwen3.5 35B (exploratory)"] = {"G_a": None, "G_b": None, "G_c": None, "G_d": None,
                                        "note": "exploratory judge (E6a); not gated"}
    return out


def rates_ci(lab, bug, ids, pred):
    bugs = sorted({bug[i] for i in ids})
    bi = {b: n for n, b in enumerate(bugs)}
    T = np.zeros((len(bugs), 1, 4))
    for i in ids:
        t, k = lab[i] == rc.PF, pred[i] == rc.PF
        T[bi[bug[i]], 0, 0 if (t and k) else 2 if t else 1 if k else 3] += 1
    W = stats.bootstrap_weights(len(bugs))
    pt, bs = rm.rates_point(T), rm.rates_bootstrap(T, W)
    tot = T.sum(axis=0)[0]
    tp, fp = tot[0], tot[1]
    return {**pt, "tpr_ci95": rc.ci(bs["tpr"]), "tnr_ci95": rc.ci(bs["tnr"]), "ba_ci95": rc.ci(bs["ba"]),
            "precision": tp / (tp + fp) if tp + fp else float("nan"),
            "false_alarms_per_kept_pf": fp / tp if tp else float("nan"),
            "TP": float(tp), "FP": float(fp), "FN": float(tot[2]), "TN": float(tot[3]), "n": len(ids),
            "mcc": stats.point_estimate(T, "mcc"), "f1": stats.point_estimate(T, "f1")}


def tf296():
    D = rc.build("D1")
    runs = {m: REV / f"REV_TF176_{m}" for m in PROFILES}
    missing = [m for m, r in runs.items() if not (r / "decisions.jsonl").exists()]
    if missing:
        return {"status": f"not available: runs missing for {missing}"}
    samp176 = json.loads((config.PROCESSED / "sample_D1_test_TF176.json").read_text(encoding="utf-8"))["instance_ids"]
    labels = {l["instance_id"]: l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl")}
    checks, votes_new, aborted_new = {}, {}, set()
    frozen = json.loads((rc.ROOT / "configs" / "local_models.FROZEN.json").read_text(encoding="utf-8"))
    for m, r in runs.items():
        e = json.loads((r / "experiment.json").read_text(encoding="utf-8"))
        prof = json.loads((rc.ROOT / PROFILES[m]).read_text(encoding="utf-8"))
        ds = [d for d in read_jsonl(r / "decisions.jsonl") if d["arm"] == "J1" and s1(d)]
        ids = [d["instance_id"] for d in ds]
        rej = {x["instance_id"] for x in read_jsonl(r / "leakage_rejections.jsonl")} if (r / "leakage_rejections.jsonl").exists() else set()
        aborted_new |= rej
        errs = list(read_jsonl(r / "errors.jsonl")) if (r / "errors.jsonl").exists() else []
        com_hash = {json.loads((rc.RUNS / c / "experiment.json").read_text(encoding="utf-8"))["prompt_set_hash"]
                    for c, _ in COMMITTED[m]}
        checks[m] = {"decisions": len(ds), "duplicates": len(ids) - len(set(ids)), "aborted": len(rej), "errors": len(errs),
                     "invalid": sum(d["label_raw"] == rc.INV for d in ds),
                     "missing": len(set(samp176) - set(ids) - rej),
                     "overlap_with_judged_sample": len(set(ids) & set(D.sample["instance_ids"])),
                     "prompt_set_hash_matches_committed": com_hash == {e["prompt_set_hash"]},
                     "digest_matches_profile": e["model_spec"]["digest"] == prof["model_spec"]["digest"],
                     "decoding_frozen": e.get("temperature") is None and e.get("max_tokens") is None and not e.get("spec_patch"),
                     "replicate_indices": sorted({d["replicate"] for d in ds}),
                     "frozen_config_sha256_matches": e.get("frozen_config_sha256") is not None}
        for d in ds:
            votes_new.setdefault(d["instance_id"], {})[m] = d["label_raw"]
    ok = all(c["duplicates"] == 0 and c["overlap_with_judged_sample"] == 0 and c["prompt_set_hash_matches_committed"]
             and c["digest_matches_profile"] and c["decoding_frozen"] for c in checks.values())
    if not ok:
        return {"status": "merge checks failed; not merged", "checks": checks}
    new_ids = sorted(i for i in samp176 if i not in aborted_new and len(votes_new.get(i, {})) == 4)
    old_ids = D.ids                                           # D-110 common set: 60 PF + 117 TF
    lab = {**{i: D.lab[i] for i in old_ids}, **{i: rc.TF for i in new_ids}}
    bug = {**{i: D.bug[i] for i in old_ids}, **{i: labels[i]["bug_name"] for i in new_ids}}
    kv = {**{i: D.kuu_votes[i] for i in old_ids}, **{i: votes_new[i] for i in new_ids}}
    nv = {**{i: D.ng_votes[i] for i in old_ids}, **{i: {"M1": votes_new[i]["M1"], "E6B": votes_new[i]["E6B"],
                                                         "NG": votes_new[i]["NG"]} for i in new_ids}}
    rules = {"M1 J1": lambda i: rc.TF if kv[i].get("M1") in (rc.TF, rc.INV) else rc.PF,
             "KUU": lambda i: rm.k_of_n([kv[i].get(m) for m in ("M1", "M2", "E6B")], 3),
             "KUU-NG": lambda i: rm.k_of_n([nv[i].get(m) for m in ("M1", "E6B", "NG")], 3),
             "2-of-3 (KUU panel)": lambda i: rm.k_of_n([kv[i].get(m) for m in ("M1", "M2", "E6B")], 2),
             "Keep all": lambda i: rc.PF}
    full = sorted(lab)
    tf_old = [i for i in old_ids if lab[i] == rc.TF]
    res = {"status": "merged", "checks": checks, "n_pf": sum(lab[i] == rc.PF for i in full),
           "n_tf_total_labelled": 296, "n_tf_judged": len(tf_old) + len(new_ids),
           "tf_not_covered": 296 - len(tf_old) - len(new_ids),
           "natural_prevalence_claim": (296 - len(tf_old) - len(new_ids)) == 0,
           "note": ("TF of the original sample use the committed votes (E8 replicate 10; KUU-NG replicate 30); the 176 "
                    "use replicate 40; same prompts, digests and decoding (checked). 3 TF of the 120 were aborted by "
                    "the leakage guard in committed runs, so 'all 296' is reached only if they are counted as not judged."),
           "rules": {}}
    for name, f in rules.items():
        pred = {i: f(i) for i in full}
        res["rules"][name] = {"all": rates_ci(lab, bug, full, pred),
                              "tnr_original_sample": float(np.mean([pred[i] == rc.TF for i in tf_old])),
                              "tnr_new_176": float(np.mean([pred[i] == rc.TF for i in new_ids])) if new_ids else None}
    return res


def arm_rates(D, decisions, arm):
    by = {}
    for d in decisions:
        if d["arm"] == arm and s1(d) and d["instance_id"] in set(D.ids):
            by.setdefault(d["replicate"], {})[d["instance_id"]] = d
    per = {}
    for r, dd in sorted(by.items()):
        if set(dd) != set(D.ids):
            per[r] = {"status": f"incomplete: {len(dd)} of {len(D.ids)}"}
            continue
        pred = {i: (rc.PF if dd[i]["label_raw"] == rc.PF else rc.TF) for i in D.ids}
        x = rates_ci(D.lab, D.bug, D.ids, pred)
        x["invalid"] = sum(dd[i]["label_raw"] == rc.INV for i in D.ids)
        c = [_cost(dd[i]) for i in D.ids]
        x["consumed_tokens_per_instance"] = float(np.mean([y.get("input_tokens", 0) + y.get("output_tokens", 0) for y in c]))
        x["output_tokens_per_instance"] = float(np.mean([y.get("output_tokens", 0) for y in c]))
        x["latency_s_per_instance"] = float(np.mean([y.get("latency_s", 0) for y in c]))
        per[r] = x
    return per


def greedy(D, m1):
    f = REV / "REV_J1_T0_M1" / "decisions.jsonl"
    if not f.exists():
        return {"status": "not available"}
    return {"temperature_0": arm_rates(D, list(read_jsonl(f)), "J1"), "temperature_0.7_committed": arm_rates(D, m1, "J1")}


def think(D, m1):
    out = {}
    pf = REV / "REV_THINK_PROBE_M1" / "decisions.jsonl"
    if pf.exists():
        ds = list(read_jsonl(pf))
        logs = [json.loads(l) for l in open(rc.ROOT / "data/raw/llm_calls_local_revision/qwen3.5_9b.jsonl", encoding="utf-8")
                if json.loads(l).get("max_tokens") == 8192] if (rc.ROOT / "data/raw/llm_calls_local_revision/qwen3.5_9b.jsonl").exists() else []
        out["probe"] = {"decisions": len(ds), "labels": [d["label_raw"] for d in ds],
                        "latency_s": [_cost(d).get("latency_s") for d in ds],
                        "output_tokens": [_cost(d).get("output_tokens") for d in ds],
                        "input_tokens": [_cost(d).get("input_tokens") for d in ds],
                        "thinking_chars": [(x.get("local") or {}).get("thinking_chars") for x in logs],
                        "done_reason": [(x.get("local") or {}).get("done_reason") for x in logs],
                        "peak_vram_mib": [(x.get("local") or {}).get("peak_vram_mib") for x in logs],
                        "gpu_resident": [(x.get("local") or {}).get("gpu_resident") for x in logs],
                        "eval_count": [(x.get("local") or {}).get("eval_count") for x in logs]}
    hf = REV / "REV_THINK_M1" / "decisions.jsonl"
    if hf.exists():
        x = arm_rates(D, list(read_jsonl(hf)), "J1")
        T = {r["condition"]: r for r in __import__("csv").DictReader(open(rc.ROOT / "results/heldout/analysis_final/D1_M1/tables/conditions.csv", encoding="utf-8"))}
        out["heldout"] = x
        out["deb_consumed_tokens_per_instance_table"] = float(T["DEB|S1"]["consumed_tokens_per_instance"])
        out["comparators"] = {"DEB": arm_rates(D, m1, "DEB"), "SC-T": arm_rates(D, m1, "SC-T")}
        for r, v in x.items():
            if "consumed_tokens_per_instance" in v:
                v["ratio_to_deb_tokens"] = v["consumed_tokens_per_instance"] / out["deb_consumed_tokens_per_instance_table"]
                v["approximately_token_matched"] = abs(v["ratio_to_deb_tokens"] - 1) <= 0.20
    else:
        out["heldout"] = {"status": "not run"}
    return out


def deb8(D, m1):
    f = REV / "REV_DEB5_M1" / "decisions.jsonl"
    old = arm_rates(D, m1, "DEB")
    new = arm_rates(D, list(read_jsonl(f)), "DEB") if f.exists() else {}
    allr = {**{f"committed_{r}": v for r, v in old.items()}, **{f"new_{r}": v for r, v in new.items()}}
    ok = {k: v for k, v in allr.items() if "f1" in v}
    summ = {}
    for m in ("f1", "mcc", "ba", "tpr", "tnr"):
        vals = [v[m] for v in ok.values()]
        summ[m] = {"values": vals, "min": min(vals), "max": max(vals), "range": max(vals) - min(vals),
                   "sd": float(np.std(vals, ddof=1)) if len(vals) > 1 else None, "median": float(np.median(vals)),
                   "mean": float(np.mean(vals))}
    return {"n_replicates": len(ok), "new_complete": sum(1 for k in ok if k.startswith("new_")),
            "per_replicate": allr, "spread": summ}


def main():
    D = rc.build("D1")
    m1 = list(read_jsonl(rc.RUNS / "LOCAL_HO_E1E3_M1" / "decisions.jsonl"))
    res = {"what": "WP2 local runs (D-124 to D-127, exploratory) and the judge gate table", "decisions": ["D-123", "D-124",
           "D-125", "D-126", "D-127"], "gates": gates(), "tf296": tf296(), "greedy": greedy(D, m1), "think": think(D, m1),
           "deb8": deb8(D, m1)}
    dump_json(OUT, res)
    print(json.dumps(res["gates"], indent=0)[:600])
    t = res["tf296"]
    print("tf296", t.get("status"), {k: v for k, v in t.items() if k in ("n_pf", "n_tf_judged", "tf_not_covered")})
    for k, v in (t.get("checks") or {}).items():
        print("  ", k, v)
    for name, r in (t.get("rules") or {}).items():
        a = r["all"]
        print(f"  {name:20s} TPR {a['tpr']:.3f} TNR {a['tnr']:.3f} {np.round(a['tnr_ci95'], 3)} BA {a['ba']:.3f} prec {a['precision']:.3f} "
              f"FA/PF {a['false_alarms_per_kept_pf']:.2f} | TNR orig {r['tnr_original_sample']:.3f} new {r['tnr_new_176']}")
    for part in ("greedy",):
        for k, v in res[part].items():
            if isinstance(v, dict):
                for r, x in v.items():
                    if "f1" in x:
                        print(part, k, r, {m: round(x[m], 3) for m in ("tpr", "tnr", "ba", "f1", "mcc")}, "inv", x["invalid"])
    print("think", json.dumps(res["think"].get("probe"), indent=0)[:800])
    d = res["deb8"]
    print("deb8", d["n_replicates"], {m: (round(s["range"], 3), round(s["sd"] or 0, 3), round(s["median"], 3)) for m, s in d["spread"].items()})


if __name__ == "__main__":
    main()
