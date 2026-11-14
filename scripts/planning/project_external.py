"""GPU-time projection for the post-submission proposals E6-E8 (D-80; proposals only, nothing is run).

Every input is a measured quantity from committed files: per-instance wall time of J1 / SC / DEB at S1 from the call
logs (cost_latency_s1.json for M1; conditions.csv for M2), per-call latency of the exploratory 35b and of the generator G
from their call logs, and the D1-test judged size. A judge that has not been run is costed at M1's measured per-instance
time (labelled as an assumption). Hours include the D-31 duty factor 0.80 (D-62) and are compared with the authors'
session shapes: a night session of 8-10 h and a day session of 5 h.

    python scripts/planning/project_external.py   -> results/planning/external_projection.json
"""
import csv
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AF = ROOT / "results" / "heldout" / "analysis_final"
OUT = ROOT / "results" / "planning" / "external_projection.json"
DUTY = 0.80
NIGHT_H, NIGHT_H_MIN, DAY_H = 10.0, 8.0, 5.0


def jl(p):
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            yield json.loads(line)


def main():
    cl = json.loads((AF / "D1_M1" / "tables" / "cost_latency_s1.json").read_text(encoding="utf-8"))
    m1 = {a: cl["arms"][a]["wall_s_mean"] for a in ("J1", "SC", "DEB")}
    m2 = {r["condition"].split("|")[0]: float(r["latency_s_per_instance"])
          for r in csv.DictReader(open(AF / "D1_M2" / "tables" / "conditions.csv", encoding="utf-8"))}
    samp = json.loads((ROOT / "data" / "processed" / "sample_D1_test.json").read_text(encoding="utf-8"))
    n_judged = len(samp["instance_ids"])
    # exploratory 35b: per-call latency while healthy (J1 pass, and the DEB pass before the D-78 slowdown)
    c35 = list(jl(ROOT / "data" / "raw" / "llm_calls_local_35b" / "qwen3.5_35b.jsonl"))
    lat35 = [float(c["latency_s"]) for c in c35]
    j1_35 = statistics.median(lat35[:n_judged - 4])          # J1: one call per decided instance (4 aborts)
    deb_calls = lat35[n_judged - 4:]
    # healthy DEB phase: before the first 50-call window whose median exceeds the 10 s D-78 limit
    first_bad = next((i for i in range(len(deb_calls) - 49) if statistics.median(deb_calls[i:i + 50]) > 10.0), len(deb_calls))
    deb_35 = statistics.median(deb_calls[:first_bad])
    outcome = json.loads((ROOT / "results" / "expl_35b" / "outcome.json").read_text(encoding="utf-8"))
    deb_done = outcome["decisions_by_arm"]["DEB"]
    gen = [float(c["latency_s"]) for c in jl(ROOT / "data" / "raw" / "llm_calls_local" / "gemma4_26b.jsonl")
           if c.get("role") == "generator"]
    gen_mean = statistics.mean(gen)
    n_focal_test = 195                                      # held-out focal methods (split manifest), 3 generations each
    split = json.loads((ROOT / "data" / "processed" / "split_manifest.json").read_text(encoding="utf-8"))
    n_focal_test = sum(split["per_project"][p]["sampled"] for p in split["test_projects"])

    def h(seconds):
        return seconds / 3600 / DUTY

    props = {}
    # E6a: complete the 35b (SC at S1; DEB for the instances the D-78 stop did not reach), sessions capped below the
    # call count at which the 35b slowed (first_bad DEB calls into its pass)
    sc_calls = 5 * (n_judged - 4)
    deb_rest_calls = 5 * (n_judged - 4 - deb_done)
    props["E6a_35b_complete"] = {"calls": sc_calls + deb_rest_calls, "sec_per_call_measured": deb_35,
                                 "gpu_h": h((sc_calls + deb_rest_calls) * deb_35),
                                 "calls_before_slowdown_measured": first_bad,
                                 "sessions_needed_at_cap": math.ceil((sc_calls + deb_rest_calls) / first_bad)}
    # E6b: second judge outside the Gemma family, J1/SC/DEB at S1, one replicate; dev Step 1 + gate on the 55-instance pilot
    per_inst = m1["J1"] + m1["SC"] + m1["DEB"]
    props["E6b_second_family_judge"] = {"per_instance_s_assumed_M1": per_inst, "gpu_h_heldout": h(n_judged * per_inst),
                                        "gpu_h_dev_gate": h(55 * per_inst), "note": "costed at M1's measured time"}
    # E7a: second generator (3 generations per held-out focal method) + re-judging J1/SC/DEB at S1 with M1
    gens = 3 * n_focal_test
    props["E7a_second_generator"] = {"generations": gens, "sec_per_generation_G_measured": gen_mean,
                                     "gpu_h_generation": h(gens * gen_mean),
                                     "gpu_h_judging_same_size": h(n_judged * per_inst),
                                     "note": "judged size assumed equal to D1-test; execution runs on CPU (WSL)"}
    # E7b: GitBug-Java, up to 60 bugs (Phase 2 D3), one focal method each, 3 generations, judged size assumed 60
    props["E7b_gitbug_java"] = {"generations": 180, "gpu_h_generation": h(180 * gen_mean), "gpu_h_judging": h(60 * per_inst),
                                "blocker": "needs Docker for build reproduction (X-05)"}
    # E8: three-family vote, one J1-style call each from M1, M2 and the E6b judge, plus a five-call (2+2+1) variant
    v3 = m1["J1"] + m2["J1"] + m1["J1"]
    v5 = 2 * m1["J1"] + 2 * m2["J1"] + m1["J1"]
    props["E8_three_llm_vote"] = {"per_instance_s_vote3": v3, "per_instance_s_vote5": v5,
                                  "gpu_h_vote3": h(n_judged * v3), "gpu_h_vote5": h(n_judged * v5),
                                  "note": "third judge costed at M1's J1 time; models swap once per batch (MAX_LOADED 1)"}
    for p in props.values():
        tot = sum(v for k, v in p.items() if k.startswith("gpu_h"))
        p["gpu_h_total"] = tot
        p["fits_one_day_session"] = tot <= DAY_H
        p["fits_one_night_session"] = tot <= NIGHT_H_MIN
    out = {"what": "GPU-time projection for proposals E6-E8 (D-80); nothing is run", "duty_factor": DUTY,
           "sessions_h": {"night": [NIGHT_H_MIN, NIGHT_H], "day": DAY_H}, "n_judged_d1_test": n_judged,
           "n_focal_test": n_focal_test, "measured": {"m1_wall_s_mean": m1, "m2_latency_s_per_instance": m2,
                                                      "q35_j1_s_per_call_median": j1_35, "q35_deb_s_per_call_median_healthy": deb_35,
                                                      "q35_deb_decided": deb_done, "g_s_per_generation_mean": gen_mean},
           "api_cost_usd": 0.0, "proposals": props}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for k, v in props.items():
        print(k, round(v["gpu_h_total"], 2), "h", "day" if v["fits_one_day_session"] else ("night" if v["fits_one_night_session"] else "multi"))


if __name__ == "__main__":
    main()
