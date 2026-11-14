"""Held-out projection under the authors' D-58 budget and the D-59 scope as amended by D-66/D-67 (time budget only).

    python scripts/local/project_d59.py [--done results/heldout/progress_hours.json]

Budget (D-58, corrected by D-62): ~13-15 running hours per day in two sessions x the D-31 duty factor 0.80, compute ends
2026-11-12 23:59.
Scope (D-66, restoring what D-59 cut once the real D1-test size was known): Tier 1 at 3 replicates plus separate SC-T
calls at k_T = 5 (S1), E4 at its planned 1 replicate, then D2 (generate, execute, judge at 1 replicate), then Tier 3
(E5-R3 with M2, S1, 1 replicate, on D1-test AND D2; still subject to the D-61 time check after Tier 2), then the
exploratory qwen3.5:35b (D-67: flash attention off, separate server, run last; its cost is unknown until its feasibility
probes run, so the projection reports the hours left for it rather than a cost).
GPU seconds per arm are the measured dev costs from project_heldout.py; WSL execution wall time is scaled from the dev
execution (27 bugs in 0.13 h with 6 workers) with a 3x margin for uncached checkouts. Sizes are the D-31 planning values
until the real D1-test sample exists (--n-d1). Phases already finished are excluded with --completed. The D-61
conditional Tier 3 (E5-R3 with M2, D1-test and D2 under D-66, 1 replicate) is projected after D2; it runs iff it fits
in the time remaining after Tier 2 (time only, never results). The D2 build is engineering time that overlaps Tier 1 (no GPU);
it is reported but not counted, while a D2 shake-down contingency on held-out mutants is counted.
Writes results/heldout/projection_latest.json and a timestamped copy.
"""
import argparse
import json
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from triage import config  # noqa: E402
from triage.io_utils import dump_json  # noqa: E402
from project_heldout import N_D1, N_D2, N_METHODS, N_MUTANTS, calls, per_arm  # noqa: E402

DEADLINE = datetime(2026, 11, 12, 23, 59)
HOURS_PER_DAY = (13.0, 15.0)
DUTY = 0.80                                    # D-31 duty factor, applied per D-62
D2_BUILD_ENGINEERING_H = 8.0                   # estimate: code + unit tests against fakes, overlapping Tier 1
D2_SHAKEDOWN_H = 2.0                           # contingency: first held-out mutant batch + D-entry defect fixes
REPS_T1 = 3                                    # D-66 (D-59 had cut it to 2)
DEV_EXEC_H_PER_BUG = 0.1314 / 27              # dev: 27 bugs in 0.1314 h wall with 6 workers
EXEC_MARGIN = 3.0
N_D1_BUGS_EST = 140                            # planning guess for 195 held-out methods (dev: 39 methods / 27 bugs)


def parse_completed(s: str) -> set[str]:
    """Comma-separated phase names; a comma inside parentheses belongs to the name ('Tier 2 (E4, 1 rep as planned)')."""
    return {c.strip() for c in re.split(r",(?![^()]*\))", s) if c.strip()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-d1", type=int, default=N_D1, help="actual D1-test sample size once known")
    ap.add_argument("--completed", default="", help="comma-separated finished phases, e.g. 'steps 0-5,Tier 1 (D1)'")
    a = ap.parse_args()
    C = calls()
    m1, m2 = per_arm("GATE_M1b", C), per_arm("CHECK_M2", C)
    gen = statistics.mean(r["latency_s"] for r in C.values() if r["role"] == "generator")
    spec = statistics.mean(r["latency_s"] for r in C.values() if r["role"] == "spec_inferencer")
    inst1 = m1["J1"] + m1["SC"] + m1["DEB"]
    h = lambda s: s / 3600
    e4 = m1["DEB"] * 2 + inst1 + (m1["J1"] + m1["DEB"]) + m1["J1"]
    exec_h = lambda bugs: bugs * DEV_EXEC_H_PER_BUG * EXEC_MARGIN
    plan = {
        "steps 0-5": {"1 repair context imports (WSL)": 0.2,
                      "2 G generation D1 (195 x 3)": h(N_METHODS * config.GENERATIONS_PER_FOCAL * gen),
                      "3 WSL execution + labelling D1 (wall)": exec_h(N_D1_BUGS_EST),
                      "4 dataset + sample": 0.1,
                      "5 S2 specs (M1)": h(N_METHODS * spec)},
        "Tier 1 (D1)": {f"E1-E3 D1-test (3 levels x {REPS_T1} reps)": h(a.n_d1 * 3 * REPS_T1 * inst1),
                        f"SC-T S1 at k_T = 5 ({REPS_T1} reps, D-66)": h(a.n_d1 * REPS_T1 * m1["SC"])},
        "Tier 2 (E4, 1 rep as planned)": {"E4 ablations S1": h(a.n_d1 * e4), "S2' specs (A5b)": h(N_METHODS * spec)},
        "D2": {"contexts from mutant versions (WSL, wall)": exec_h(N_MUTANTS) / 2,
               "S2 specs per D2 unit (M1)": h(N_MUTANTS * spec),
               "G generation (284 x 3)": h(N_MUTANTS * config.GENERATIONS_PER_FOCAL * gen),
               "WSL execution + labelling (wall)": exec_h(N_MUTANTS),
               "E1-E3 D2 (3 levels x 1 rep)": h(N_D2 * 3 * inst1),
               "shake-down contingency (held-out mutants)": D2_SHAKEDOWN_H},
    }
    m2_inst = m2["J1"] + m2["SC"] + m2["DEB"]
    tier3 = {"E5-R3 M2 S1 D1-test (1 rep)": h(a.n_d1 * m2_inst), "E5-R3 M2 S1 D2 (1 rep, D-66)": h(N_D2 * m2_inst)}
    completed = parse_completed(a.completed)
    unknown = completed - set(plan)
    if unknown:
        raise SystemExit(f"unknown phases {unknown}; known: {list(plan)}")
    plan = {k: v for k, v in plan.items() if k not in completed}
    now = datetime.now()
    days = (DEADLINE - now).total_seconds() / 86400
    avail = {"low_13h_per_day": days * HOURS_PER_DAY[0] * DUTY, "high_15h_per_day": days * HOURS_PER_DAY[1] * DUTY}
    totals = {k: sum(v.values()) for k, v in plan.items()}
    need = sum(totals.values())
    cum, order = 0.0, []
    for k, t in totals.items():
        cum += t
        order.append({"phase": k, "hours": t, "cumulative": cum, "fits_low": cum <= avail["low_13h_per_day"]})
    t3 = sum(tier3.values())
    d61 = {"rule": "D-61 as extended by D-66: after Tier 2, run Tier 3 (D1-test + D2, 1 rep) after D2 iff remaining "
                   "time >= D2 + Tier 3; time only",
           "tier3_hours": t3, "need_with_tier3": need + t3,
           "fits_low": need + t3 <= avail["low_13h_per_day"], "fits_high": need + t3 <= avail["high_15h_per_day"],
           "binding": "Tier 1 (D1)" not in plan and "Tier 2 (E4, 1 rep as planned)" not in plan}
    out = {"computed_local": now.isoformat(timespec="minutes"), "deadline": DEADLINE.isoformat(timespec="minutes"),
           "days_remaining": days, "available_hours": avail, "plan": plan, "phase_totals": totals,
           "cumulative": order, "completed_phases": sorted(completed), "remaining_need_hours": need,
           "duty_factor": DUTY, "d2_build_engineering_h_not_counted": D2_BUILD_ENGINEERING_H, "tier3_D61": d61,
           "margin_hours": {k: v - need for k, v in avail.items()},
           "exploratory_35b_D67": {"cost": "unknown until its feasibility probes run (never loaded under the frozen env)",
                                   "hours_left_after_primary_incl_tier3": {k: v - need - t3 for k, v in avail.items()},
                                   "order": "J1 all instances, then DEB, then SC; D1-test S1, 1 rep; runs last"},
           "basis": {"M1_gpu_s_per_instance_S1": m1, "G_s_per_generation": gen, "spec_s_per_method": spec,
                     "exec_h_per_bug_dev": DEV_EXEC_H_PER_BUG, "exec_margin": EXEC_MARGIN,
                     "sizes": {"D1_test": a.n_d1, "D2": N_D2, "methods": N_METHODS, "mutants": N_MUTANTS,
                               "D1_bugs_estimate": N_D1_BUGS_EST},
                     "notes": ["S0/S2 costed like S1 (measured at S1 on dev)",
                               "D2 build is engineering time overlapping Tier 1 (no GPU, no session time); reported, not counted",
                               "session_check overhead (~2 min/session) not included"]}}
    dump_json(config.ROOT / "results" / "heldout" / "projection_latest.json", out)
    dump_json(config.ROOT / "results" / "heldout" / f"projection_{now:%Y%m%d_%H%M}.json", out)
    print(f"days {days:.2f} | available x{DUTY} {avail['low_13h_per_day']:.1f}-{avail['high_15h_per_day']:.1f} h | "
          f"need {need:.1f} h | D2 build {D2_BUILD_ENGINEERING_H:.0f} h engineering (not counted)")
    for o in order:
        print(f"  {o['phase']:32s} {o['hours']:6.1f} h  cum {o['cumulative']:6.1f}  fits(low) {o['fits_low']}")
        for k, v in plan[o["phase"]].items():
            print(f"      {k:44s} {v:6.2f}")
    print(f"  D-61/D-66 Tier 3 (D1-test + D2, M2, 1 rep) {t3:.1f} h -> need {need + t3:.1f} h; fits low {d61['fits_low']} "
          f"high {d61['fits_high']} (binding only after Tier 2: {d61['binding']})")
    left = out["exploratory_35b_D67"]["hours_left_after_primary_incl_tier3"]
    print(f"  D-67 exploratory 35b: cost unknown; hours left after everything above "
          f"{left['low_13h_per_day']:.1f}-{left['high_15h_per_day']:.1f}")


if __name__ == "__main__":
    main()
