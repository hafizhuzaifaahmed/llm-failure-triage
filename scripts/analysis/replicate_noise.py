"""Replicate noise (D-94; zero calls): M1's run-to-run spread at S1, set beside the single-replicate cross-model
differences. Exploratory and descriptive; defined before M1's per-replicate values were computed.

Per arm (J1, SC, SC-T, DEB at S1, and SC3 = the first three of each SC decision's five votes), on the 177-instance D1-test
set (D-70 leakage aborts dropped): F1 and MCC of each of M1's three replicates scored separately, their range
(max - min), sample SD (ddof 1) and the mean absolute difference over the three replicate pairs.

Cross-model differences (each a single replicate, already committed): M2 - M1, E6b - M1 (J1, SC, DEB; family check
of e6b_d1test.json), 35B - M1 (J1, DEB; E6a), and the pre-registered E8 contrasts VOTE3 - SC3, VOTE5 - SC,
VOTE5 - DEB (e8_d1test.json); M1's value is its three-replicate mean on the same instances.
Rule fixed before computing: a difference is "beyond M1's run-to-run spread" when |Δ| exceeds the range of M1's
replicates for that arm (for the votes: the range of the M1 arm compared), otherwise "within it". No test.

    python scripts/analysis/replicate_noise.py   -> results/heldout/analysis_final/D1_M1/tables/replicate_noise.json
"""
import itertools
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import analysis, arms, config, stats  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

RUN = ROOT / "results" / "runs_local" / "LOCAL_HO_E1E3_M1"
E6B = ROOT / "results" / "e6b" / "analysis" / "e6b_d1test.json"
E6A = ROOT / "results" / "expl_35b" / "analysis" / "e6a_j1_deb" / "expl_35b_vs_m1_m2.json"
E8 = ROOT / "results" / "e8" / "analysis" / "e8_d1test.json"
OUT = ROOT / "results" / "heldout" / "analysis_final" / "D1_M1" / "tables" / "replicate_noise.json"
ARMS = ("J1", "SC", "SC-T", "DEB", "SC3")
METRICS = ("f1", "mcc")


def main():
    allr = list(read_jsonl(RUN / "decisions.jsonl"))
    decs = [d for d in allr if d.get("level") == "S1" and (d.get("variant") or "full") == "full"
            and d["arm"] in ("J1", "SC", "SC-T", "DEB")]
    decs += [{**d, "arm": "SC3", "label_raw": arms.aggregate_votes(d["votes"][:3], 3)["label_raw"]}
             for d in decs if d["arm"] == "SC"]
    samp = json.loads((config.PROCESSED / "sample_D1_test.json").read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    labels = [l for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl") if l["instance_id"] in keep]
    ev = analysis.Evaluation(decs, labels, samp["tf_weights"],
                             exclusions=analysis.abort_exclusions(read_jsonl(RUN / "leakage_rejections.jsonl")))
    conds = [f"{a}|S1" for a in ARMS]
    evr = ev._restricted(ev.comparison_set(conds))
    noise = {}
    for a, c in zip(ARMS, conds):
        reps = sorted({d["replicate"] for d in evr.by_cond[c]})
        row = {"n_instances": len(evr.lab), "replicates": reps}
        T = evr.tensor(c)                        # [bug, replicate, count]; replicates in sorted order
        for m in METRICS:
            v = [stats.point_estimate(T[:, i:i + 1, :], m) for i in range(len(reps))]
            row[m] = {"per_replicate": v, "mean": statistics.mean(v), "range": max(v) - min(v),
                      "sd": statistics.stdev(v),
                      "mean_abs_pair_diff": statistics.mean(abs(x - y) for x, y in itertools.combinations(v, 2))}
        noise[a] = row

    e6b = json.loads(E6B.read_text(encoding="utf-8"))["family_check"]
    e6a = json.loads(E6A.read_text(encoding="utf-8"))
    e8 = json.loads(E8.read_text(encoding="utf-8"))
    cross = []

    def add(name, arm_for_noise, metric, delta):
        rng = noise[arm_for_noise][metric]["range"]
        cross.append({"comparison": name, "metric": metric, "delta": delta, "m1_arm": arm_for_noise,
                      "m1_range": rng, "m1_sd": noise[arm_for_noise][metric]["sd"],
                      "abs_delta_over_range": abs(delta) / rng if rng else None,
                      "beyond_m1_spread": abs(delta) > rng})

    for m in METRICS:
        for arm in ("J1", "SC", "DEB"):
            for model in ("M2", "E6B"):
                add(f"{arm}: {model} - M1", arm, m, e6b["summary"][model][arm][m] - e6b["summary"]["M1"][arm][m])
        for arm in ("J1", "DEB"):
            add(f"{arm}: 35B - M1", arm, m, e6a["summary"]["35B"][arm][m] - e6a["summary"]["M1"][arm][m])
        for name, a, b, arm in (("VOTE3 - SC3", "VOTE3|S1", "SC3|S1", "SC3"), ("VOTE5 - SC", "VOTE5|S1", "SC|S1", "SC"),
                                ("VOTE5 - DEB", "VOTE5|S1", "DEB|S1", "DEB")):
            add(name, arm, m, e8["summary"][a][m] - e8["summary"][b][m])
    out = {"what": "M1 replicate noise vs single-replicate cross-model differences (D-94, exploratory, descriptive)",
           "dataset": "D1", "split": "test", "level": "S1", "n_instances": len(evr.lab), "n_bugs": len(evr.bugs),
           "rule": "beyond M1's run-to-run spread iff |delta| > range of M1's three replicates for that arm",
           "noise": noise, "cross_model": cross,
           "summary": {m: {"beyond": sum(1 for c in cross if c["metric"] == m and c["beyond_m1_spread"]),
                           "of": sum(1 for c in cross if c["metric"] == m)} for m in METRICS}}
    dump_json(OUT, out)
    for a in ARMS:
        f = noise[a]["f1"]
        print(f"{a}: F1 reps {[round(x, 3) for x in f['per_replicate']]} range {f['range']:.3f} sd {f['sd']:.3f} "
              f"MAD {f['mean_abs_pair_diff']:.3f}; MCC range {noise[a]['mcc']['range']:.3f}")
    for c in cross:
        print(f"  {c['comparison']} {c['metric']}: {c['delta']:+.3f} vs range {c['m1_range']:.3f} -> "
              f"{'beyond' if c['beyond_m1_spread'] else 'within'}")


if __name__ == "__main__":
    main()
