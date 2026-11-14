"""Follow-up of D-82 (D2), declared before computing: selective triage against keep-all (zero calls, exploratory).

For each arm (J1, SC, DEB) at the threshold tuned on the development pilot (exploratory_d82.json, D2:tau), the
selective rule "discard only a TF said with confidence >= tau" is compared with keep-all on D1-test S1, judge M1:
paired ΔF1 with the committed bug-level bootstrap, PF tests lost per replicate (of the PF instances in the set), and
the share of failures the rule discards as a confident TF. The arm's own MCC (with its CI) is reported separately;
no MCC difference against keep-all is reported, because keep-all's MCC is 0 by definition (D-82 correction).
Uses exploratory_d82's own rule functions, so the rule is identical.

    python scripts/analysis/selective_vs_ka.py   -> results/heldout/analysis_final/D1_M1/tables/selective_vs_ka.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import exploratory_d82 as x  # noqa: E402
from triage import analysis, config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

OUT = ROOT / "results" / "heldout" / "analysis_final" / "D1_M1" / "tables" / "selective_vs_ka.json"


def main():
    tau = json.loads((ROOT / "results" / "heldout" / "analysis_final" / "D1_M1" / "tables" / "exploratory_d82.json")
                     .read_text(encoding="utf-8"))["D2"]["tau"]
    samp = json.loads((config.PROCESSED / "sample_D1_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    lab_all = {l["instance_id"]: l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl")}
    labels = [lab_all[i] for i in keep if i in lab_all]
    excl = analysis.abort_exclusions(read_jsonl(x.RUN / "leakage_rejections.jsonl"))
    s1_drop = excl.get(("S1", "full"), set())
    allr = list(read_jsonl(x.RUN / "decisions.jsonl"))
    decs = [d for d in allr if d["level"] == "S1" and (d.get("variant") or "full") == "full" and d["arm"] in ("J1", "SC", "DEB")]
    ka = [d for d in allr if d["arm"] == "KA"]
    sel = [{**d, "variant": "sel", "label_raw": x.selective(d, tau[d["arm"]])} for d in decs]
    ex = dict(excl)
    ex[("S1", "sel")] = s1_drop
    ev = analysis.Evaluation(decs + sel + ka, labels, samp["tf_weights"], exclusions=ex)
    out = {"what": "selective triage vs keep-all (D-82 follow-up, exploratory)", "tau": tau, "arms": {}}
    for arm in ("J1", "SC", "DEB"):
        c = f"{arm}|S1|sel"
        s = ev.summary(c)
        k = ev.baseline_summary("KA")
        f = vars(ev.contrast(f"{c} - KA", [c], ["KA"], "f1"))
        ds = [d for d in sel if d["arm"] == arm and d["instance_id"] in ev.lab]
        out["arms"][arm] = {"tau": tau[arm], "f1": s["f1"], "ka_f1": k["f1"],
                            "delta_f1_vs_ka": f["delta"], "delta_f1_vs_ka_ci95": f["ci95"], "p_f1": f["p"],
                            "pf_lost": s["pf_lost"], "pf_in_set": s["TP"] + s["FN"],
                            "share_discarded": sum(d["label_raw"] == x.TF for d in ds) / len(ds),
                            "mcc": s["mcc"], "mcc_ci95": s["mcc_ci95"], "n_decisions": len(ds)}
        a = out["arms"][arm]
        print(arm, round(a["f1"], 3), "dF1", round(a["delta_f1_vs_ka"], 3), [round(v, 3) for v in a["delta_f1_vs_ka_ci95"]],
              "lost", round(a["pf_lost"], 2), "of", a["pf_in_set"], "discarded", round(a["share_discarded"], 3),
              "MCC", round(a["mcc"], 3), [round(v, 3) for v in a["mcc_ci95"]])
    dump_json(OUT, out)


if __name__ == "__main__":
    main()
