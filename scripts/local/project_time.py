"""Step 1b — GPU-time projection per tier and the D-25 cut order (D-27 caching, D-31 time available).

    python scripts/local/project_time.py

Inputs (all measured on synthetic probes): results/dev/feasibility/<M1>.json, <M2>.json, <G>.json and
results/dev/server_settings.json. Writes results/dev/projection_1b.json and prints a per-tier table.
"""
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage.io_utils import dump_json  # noqa: E402
from triage.ollama import load_local_models  # noqa: E402

FEAS = config.ROOT / "results" / "dev" / "feasibility"
DEADLINE = datetime(2026, 11, 13, 23, 59)
DUTY = 0.80
N_D1, N_D2, K_T = 720, 300, 7                    # Phase 2 planning sizes until measured (D-31)
PKG_CHARS, ARG_CHARS = 4643, 1100                # measured mean S1 package chars (estimate_cost basis); forwarded arg


def slug(m):
    return m.replace("/", "__").replace(":", "_")


def load(m):
    p = FEAS / f"{slug(m)}.json"
    return json.loads(p.read_text()) if p.exists() else None


def per_call_model(feas, speedup):
    s = feas["summary"]
    cpt = s["median_chars_per_token"]
    out_tok = statistics.mean(r["eval_count"] for r in feas["probes"])
    pre, gen = s["median_prefill_tps"], s["median_gen_tps"]
    cache = feas.get("sc_prefix_caching") or []
    # D-27: fraction of the prompt that is actually prefilled on samples 2..5 of the same prompt
    if len(cache) >= 2 and cache[0]["prompt_eval_count"]:
        # D-37: prompt_eval_count includes the cached prefix; the refilled part is the uncached remainder
        rep = statistics.mean((c["prompt_eval_count"] or 0) - (c["prompt_eval_cached_count"] or 0) for c in cache[1:])
        refill = rep / cache[0]["prompt_eval_count"]
    else:
        refill = 1.0

    def t(prompt_chars, n=1, same_prompt=False):
        tok = prompt_chars / cpt
        first = tok / pre + out_tok / gen
        rest = (tok * refill) / pre + out_tok / gen
        return (first + (n - 1) * (rest if same_prompt else first)) / speedup
    return t, {"chars_per_token": cpt, "mean_out_tokens": out_tok, "prefill_tps": pre, "gen_tps": gen,
               "sc_refill_fraction": refill, "parallel_speedup": speedup}


def factorial_hours(t, n_inst, levels, reps, k_t, sct_levels):
    judge = 800 + PKG_CHARS
    j1 = t(judge)
    sc = t(judge, 5, same_prompt=True)
    deb = 2 * t(900 + PKG_CHARS) + 2 * t(1300 + PKG_CHARS + 2 * ARG_CHARS) + t(1400 + PKG_CHARS + 4 * ARG_CHARS)
    sct = t(judge, k_t, same_prompt=True)
    per_inst_level = j1 + sc + deb
    return (n_inst * levels * reps * per_inst_level + n_inst * len(sct_levels) * reps * sct) / 3600


def main():
    cfg = load_local_models()
    roles = cfg["roles"]
    fm1, fm2, fg = load(roles["M1"]), load(roles["M2"]), load(roles["G"])
    ss = json.loads((config.ROOT / "results" / "dev" / "server_settings.json").read_text())
    p1 = next(r for r in ss["results"] if r.get("parallel") == 1 and r.get("flash_attention") == ss["choice"]["OLLAMA_FLASH_ATTENTION"])
    speedup = ss["choice"]["calls_per_hour"] / p1["calls_per_hour"]
    t1, basis1 = per_call_model(fm1, speedup)
    t2, basis2 = per_call_model(fm2, speedup) if fm2 else (None, None)
    now = datetime.now()
    avail = (DEADLINE - now).total_seconds() / 3600 * DUTY

    # G generation for held-out D1 focal methods and D2 mutants (sequential; never concurrent with WSL)
    gs = fg["summary"]
    g_out = statistics.mean(r["eval_count"] for r in fg["probes"])
    g_call = (2700 / gs["median_chars_per_token"]) / gs["median_prefill_tps"] + g_out / gs["median_gen_tps"]
    n_gen = (195 + 284) * config.GENERATIONS_PER_FOCAL
    gen_h = n_gen * g_call / 3600
    spec_h = 234 * t1(2000) / 3600

    def tiers(reps, d2_tier1, sct_levels):
        tier1 = factorial_hours(t1, N_D1, 3, reps, K_T, sct_levels) + spec_h + gen_h
        d2 = factorial_hours(t1, N_D2, 3, 1, K_T, [])
        judge = 800 + PKG_CHARS
        tier2 = N_D1 * 28 * t1(judge) / 3600                     # E4: A1 5 + A2 5 + A4 11 + A5 7 calls, 1 rep
        tier3 = ((N_D1 + N_D2) * 11 * t2(judge) / 3600 if t2 else float("nan")) + N_D1 * 2 * t1(judge) / 3600
        # tier3 = E5-R3 (M2, 1 rep, D1-test + D2) + R4 paraphrases (J1 x 2); D3 is blocked (Docker) -> 0
        if d2_tier1:
            tier1 += d2
        else:
            tier2 += d2
        return {"tier1_h": tier1, "tier2_h": tier2, "tier3_h": tier3}

    # Phase 2 already runs SC-T at S1 only (configs/experiments/E1E3_main.json), so step (d) changes nothing;
    # it is listed to show the full pre-registered order was applied.
    steps = [("as planned (parallel per D-24)", 3, True, ["S1"]),
             ("(b) replicates 3 -> 2", 2, True, ["S1"]),
             ("(c) + D2 to Tier 2", 2, False, ["S1"]),
             ("(d) + SC-T at S1 only (no-op)", 2, False, ["S1"])]
    table = []
    for name, reps, d2t1, sct in steps:
        r = tiers(reps, d2t1, sct)
        r.update(step=name, fits_tier1=r["tier1_h"] <= avail)
        table.append(r)
    first_fit = next((r["step"] for r in table if r["fits_tier1"]), None)
    out = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "available_gpu_hours": avail,
           "deadline_local": DEADLINE.isoformat(), "duty": DUTY, "basis_M1": basis1, "basis_M2": basis2,
           "g_seconds_per_generation": g_call, "g_generations": n_gen, "g_hours": gen_h, "spec_hours": spec_h,
           "planning_sizes": {"D1_test": N_D1, "D2": N_D2, "k_T": K_T}, "cut_order": table,
           "first_step_where_tier1_fits": first_fit, "decision": "proceed" if first_fit else "STOP: report to authors"}
    dump_json(config.ROOT / "results" / "dev" / "projection_1b.json", out)
    print(f"available GPU hours (to {DEADLINE:%Y-%m-%d %H:%M}, x{DUTY}): {avail:.1f}")
    print(f"{'step':34s} {'tier1 h':>8s} {'tier2 h':>8s} {'tier3 h':>8s} fits")
    for r in table:
        print(f"{r['step']:34s} {r['tier1_h']:8.1f} {r['tier2_h']:8.1f} {r['tier3_h']:8.1f} {r['fits_tier1']}")
    print("decision:", out["decision"], "| first fitting step:", first_fit)


if __name__ == "__main__":
    main()
