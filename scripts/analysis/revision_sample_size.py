"""WP1.8 (D-119; planning guidance, not a power guarantee; zero calls): bugs needed for a minimum detectable dF1 of
0.10, 0.08 and 0.05 at 80% power, from Table C1's bug-level bootstrap SE, assuming SE scales as 1/sqrt(bugs):
n(MDE) = n0 * ((z_{1-a/2} + z_{0.8}) * SE0 / MDE)^2, at a = 0.05 and at the Holm a for five tests (0.01).

    python scripts/analysis/revision_sample_size.py  -> results/revision/wp18_sample_size.json
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import revision_common as rc  # noqa: E402
from triage.io_utils import dump_json  # noqa: E402

SRC = rc.ROOT / "results" / "heldout" / "analysis_final" / "D1_M1" / "tables" / "mde_sensitivity.json"
OUT = rc.OUT / "wp18_sample_size.json"
MDES = (0.10, 0.08, 0.05)


def required(n0, se0, mde, z_a, z_b):
    return n0 * ((z_a + z_b) * se0 / mde) ** 2


def main():
    t = json.loads(SRC.read_text(encoding="utf-8"))
    za, zh, zb = t["z_alpha_005"], t["z_alpha_holm_min"], t["z_power"]
    res = {"what": "sample-size planning (D-119): planning guidance, not a power guarantee", "decisions": ["D-112", "D-119"],
           "source": "Table C1 (mde_sensitivity.json, D-80)", "power": t["power"],
           "assumptions": ["the bootstrap SE scales as 1/sqrt(number of bugs) (same tests per bug, same PF prevalence and "
                           "between-bug variance as the held-out split)", "normal approximation to the bootstrap distribution",
                           "the same paired design, judge and replicate count", "no allowance for drop-out or leakage aborts"],
           "tests": {}}
    for row in t["tests"]:
        n0, se0 = row["n_bugs"], row["se_bootstrap"]
        r = {"n0_bugs": n0, "n0_instances": row["n_instances"], "se0": se0, "observed_delta": row["delta"],
             "mde_now_alpha_005": row["mde_alpha_005"], "by_mde": {}}
        for m in MDES:
            n5, nh = required(n0, se0, m, za, zb), required(n0, se0, m, zh, zb)
            r["by_mde"][f"{m:.2f}"] = {"bugs_alpha_005": math.ceil(n5), "multiplier_alpha_005": n5 / n0,
                                        "bugs_alpha_holm_001": math.ceil(nh), "multiplier_alpha_holm_001": nh / n0}
        res["tests"][row["name"]] = r
    h = res["tests"]
    res["reviewer_check"] = {"claim": "about 4x the bugs for an MDE of 0.08 (H3a/H2a)",
                             "H3a_multiplier_0.08": h["H3a"]["by_mde"]["0.08"]["multiplier_alpha_005"],
                             "H2a_multiplier_0.08": h["H2a"]["by_mde"]["0.08"]["multiplier_alpha_005"],
                             "H3a_multiplier_0.08_holm": h["H3a"]["by_mde"]["0.08"]["multiplier_alpha_holm_001"],
                             "H2a_multiplier_0.08_holm": h["H2a"]["by_mde"]["0.08"]["multiplier_alpha_holm_001"]}
    dump_json(OUT, res)
    for name, r in res["tests"].items():
        print(name, "n0", r["n0_bugs"], "SE", round(r["se0"], 4),
              {m: (v["bugs_alpha_005"], round(v["multiplier_alpha_005"], 2), v["bugs_alpha_holm_001"]) for m, v in r["by_mde"].items()})
    print(res["reviewer_check"])


if __name__ == "__main__":
    main()
