"""Render the confirmation's statistical report from the frozen analysis output (D-143). No number is typed by hand.

    python scripts/extension/confirm_report.py --analysis results/extension/confirm/confirm_analysis_CFP_CONF_ALL.json
        -> docs/research_extension/generated/confirm_report.md

Reading rules are the registration's (OSF kp79c; OSF_PREREGISTRATION_CFP.md, "Inference criteria" and the power
classification): C1 is adequately powered, so "not supported" counts against the claim; C2, C3 and C4 are
underpowered, so "not supported" is inconclusive, except that C2 counts against the claim if significant in the
opposite direction or if its interval lies wholly below the pilot's estimate. Secondary analyses, the control group
and anything else are labelled as such and never read as confirmatory.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PILOT_C2 = 0.189          # pilot estimate of C2 (D-137), the registration's reference for the C2 reading rule
POWERED = {"C1"}
PLANNING_MIN_BUGS = 30    # lower end of the registration's planning range for bugs with a PF test
TEXT = {"C1": "P(flip | PF) − P(flip | TF)", "C2": "P(decoupled | TF) − P(decoupled | PF)",
        "C3": "balanced accuracy of KUU + CD − KUU", "C4": "PF tests lost by 2-of-3 + CK − 2-of-3"}
EXPECT = {"C1": +1, "C2": +1, "C3": +1, "C4": -1}


def f(x, n=3):
    return "n/a" if x is None else f"{x:.{n}f}"


def ci(c, n=3):
    return "n/a" if not c else f"[{c[0]:.{n}f}, {c[1]:.{n}f}]"


def reading(h, r):
    if r["supported"]:
        return "**supported**"
    opposite = r["p_holm"] < 0.05 and (r["difference"] > 0) != (EXPECT[h] > 0)
    if opposite:
        return "**not supported: significant in the opposite direction** (counts against the method)"
    if h in POWERED:
        return "**not supported** (adequately powered: counts against the method)"
    if h == "C2" and r["ci95"] and r["ci95"][1] < PILOT_C2:
        return "**not supported; interval wholly below the pilot estimate** (counts against the method)"
    return "**not supported: inconclusive** (underpowered by the registered planning)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--secondary", nargs="*", default=[], help="NAME=<analysis json> for secondary analysis 7")
    ap.add_argument("--out", default=str(ROOT / "docs" / "research_extension" / "generated" / "confirm_report.md"))
    a = ap.parse_args()
    d = json.loads(Path(a.analysis).read_text(encoding="utf-8"))
    reg = json.loads((ROOT / "configs" / "extension" / "osf_registration.json").read_text(encoding="utf-8"))
    dry = d.get("status", "").startswith("DRY RUN")
    L = [f"# CFP confirmation: statistical report{' (DRY RUN ON PILOT DATA, NOT A RESULT)' if dry else ''}", "",
         f"Generated from `{Path(a.analysis).as_posix()}` by `scripts/extension/confirm_report.py`; do not edit.",
         f"Registration: OSF {reg['osf_id']} ({reg['url']}), {reg['registered_utc']}; governing text: "
         f"{reg.get('governing_text', 'the registered document')}. Template-field reconciliation: {reg.get('reconciliation', 'n/a')}.",
         f"Analysis status: {d['status']}. Bootstrap: {d['resamples']} bug-level resamples, seed {d['seed']}.", ""]
    p = d["population"]
    L += ["## Population (F1 and F2)", "", "| Quantity | Value |", "|---|---|",
          f"| Scored failing tests | {p['instances']} ({p['PF']} PF, {p['TF']} TF) |",
          f"| Bugs; bugs with a PF test | {p['bugs']}; {p['bugs_with_PF']} |",
          f"| Excluded by the engine (kept with all flags false) | {p['excluded_by_engine']} |", ""]
    L += ["## Registered family (one Holm family, α = 0.05)", "",
          "| Hypothesis | Quantity | Estimate | 95% CI | p | p (Holm) | Reading |", "|---|---|---|---|---|---|---|"]
    for h in ("C1", "C2", "C3", "C4"):
        r = d["family"].get(h)
        if r is None:
            L.append(f"| {h} | {TEXT[h]} | not computed | | | | {d.get('family_note', '')} |")
            continue
        extra = f" ({r['PF_flagged']}/{r['PF']} PF, {r['TF_flagged']}/{r['TF']} TF)" if "PF_flagged" in r else ""
        L.append(f"| {h} | {TEXT[h]}{extra} | {r['difference']:+.3f} | {ci(r['ci95'])} | {r['p']:.4f} | {r['p_holm']:.4f} | {reading(h, r)} |")
    L += ["", "C1 is adequately powered by the registered planning; C2, C3 and C4 are underpowered, so a non-supported "
              "result for them is inconclusive unless it meets a counting-against rule stated in the registration.", ""]
    if p["bugs_with_PF"] < PLANNING_MIN_BUGS:
        L += [f"**Planning range not met (D-145).** {p['bugs_with_PF']} bugs carry a PF test; the registration expected "
              f"{PLANNING_MIN_BUGS} to 50 and classified C1 as adequately powered from a simulation at {PLANNING_MIN_BUGS} or "
              "more. The registered readings above are applied unchanged, but the reading of a non-supported C1 as "
              "evidence against the claim rests on a planning assumption that this sample does not meet.", ""]
    if d.get("rules"):
        r = d["rules"]
        L += [f"## Decision rules (reported, not tested; {r['instances_with_three_votes']} tests with three votes, {r['PF']} PF)", "",
              "| Rule | TPR | TNR | Balanced accuracy | PF tests lost | Bugs lost / bugs with PF | 95% upper bound on bug-loss rate |",
              "|---|---|---|---|---|---|---|"]
        for name, v in r.items():
            if isinstance(v, dict):
                L.append(f"| {name} | {f(v['TPR'])} | {f(v['TNR'])} | {f(v['BA'])} | {v['PF_lost']:.0f} | "
                         f"{v['bugs_lost']} / {v['bugs_with_PF']} | {f(v['upper95_bug_loss_rate'])} |")
        L.append("")
    c = d.get("control")
    L += ["## Control group (reported, not tested)", ""]
    if c:
        L += ["| Quantity | Value |", "|---|---|",
              f"| Control failing tests | {c['instances']} ({c['TF']} TF, {c['PF']} PF; {c['bugs']} bugs) |",
              f"| Flip rate among control TF [95% CI] | {f(c['flip_rate_TF'])} {ci(c['flip_rate_TF_ci95'])} |",
              f"| Decoupled rate among control TF | {f(c['decoupled_rate_TF'])} |",
              f"| Flip rate among F1/F2 TF | {f(c['flip_rate_TF_in_F1F2'])} |",
              f"| Flip rate among F1/F2 PF | {f(c['flip_rate_PF_in_F1F2'])} |", "",
              "A control method is one the fix did not change; it is not claimed to be free of defects "
              "(`CONTROL_GROUP.md`). Control tests labelled PF reveal the fault through a method the fix did not change.", ""]
    else:
        L += ["Not available.", ""]
    L += ["## Secondary analyses (stated in advance; none replaces a primary result)", "",
          "| Analysis | Estimate | 95% CI | PF flagged | TF flagged |", "|---|---|---|---|---|"]
    for name, v in d["secondary"].items():
        if "difference" in v:
            L.append(f"| {name} | {v['difference']:+.3f} | {ci(v['ci95'])} | {v['PF_flagged']}/{v['PF']} | {v['TF_flagged']}/{v['TF']} |")
    lopo = d["secondary"].get("leave_one_project_out") or {}
    if lopo:
        c1 = [v["C1"] for v in lopo.values()]
        c2 = [v["C2"] for v in lopo.values()]
        L += ["", f"Leave one project out ({len(lopo)} projects): C1 from {min(c1):+.3f} to {max(c1):+.3f}; "
                  f"C2 from {min(c2):+.3f} to {max(c2):+.3f}."]
    per_frame = [(n, json.loads(Path(s).read_text(encoding="utf-8"))) for n, s in (x.split("=", 1) for x in a.secondary)]
    if per_frame:
        L += ["", "**F1 and F2 separately** (secondary analysis 7: the same frozen script on each frame's rows; the "
                  "Holm adjustment inside each run is not a test of the registered family):", "",
              "| Frame | Scored tests (PF / TF) | Bugs with PF | C1 [95% CI] | C2 [95% CI] | C3 [95% CI] | C4 [95% CI] |",
              "|---|---|---|---|---|---|---|"]
        for n, s in per_frame:
            q, fam = s["population"], s["family"]
            cells = [f"{fam[h]['difference']:+.3f} {ci(fam[h]['ci95'])}" if fam.get(h) else "n/a" for h in ("C1", "C2", "C3", "C4")]
            L.append(f"| {n} | {q['instances']} ({q['PF']} / {q['TF']}) | {q['bugs_with_PF']} | " + " | ".join(cells) + " |")
    L += ["", "## What would count against the method (the registration's list, evaluated item by item)", ""]
    fam = d["family"]
    c1 = fam.get("C1")
    L.append(f"1. *C1 not supported:* {'yes' if c1 and not c1['supported'] else 'no'}"
             f"{' (see the D-145 note on the planning range)' if p['bugs_with_PF'] < PLANNING_MIN_BUGS else ''}.")
    c2 = fam.get("C2")
    if c2:
        opp = c2["p_holm"] < 0.05 and c2["difference"] < 0
        below = bool(c2["ci95"]) and c2["ci95"][1] < PILOT_C2
        L.append(f"2. *C2 significant in the opposite direction, or its interval wholly below the pilot's estimate "
                 f"({PILOT_C2}):* {'yes' if opp or below else 'no'} (interval {ci(c2['ci95'])}).")
    rules = d.get("rules") or {}
    pairs = [("KUU+CD", "KUU"), ("2-of-3+CK", "2-of-3"), ("KUU+CK+CD", "KUU"), ("2-of-3+CK+CD", "2-of-3"), ("keep-all+CD", None)]
    parts, worse = [], False
    for rule, base in pairs:
        if rule in rules and (base is None or base in rules):
            b = 0 if base is None else rules[base]["bugs_lost"]       # keep-all discards nothing, so it loses no bug
            delta = rules[rule]["bugs_lost"] - b
            worse |= delta > 1
            parts.append(f"{rule} {rules[rule]['bugs_lost']} vs {base or 'keep-all'} {b} ({delta:+d})")
    L.append(f"3. *CD or CK raising the bugs lost above its base rule by more than one bug:* {'yes' if worse else 'no'}"
             f" ({'; '.join(parts)}).")
    if c:
        L.append(f"4. *A flip rate among control failures close to the flip rate among bug-revealing tests:* control TF "
                 f"{f(c['flip_rate_TF'])} {ci(c['flip_rate_TF_ci95'])} against F1/F2 PF {f(c['flip_rate_PF_in_F1F2'])}. "
                 "The registration sets no numeric threshold for 'close'; the PF rate lies inside the control "
                 f"interval: {'yes' if c['flip_rate_TF_ci95'] and c['flip_rate_TF_ci95'][0] <= c['flip_rate_PF_in_F1F2'] <= c['flip_rate_TF_ci95'][1] else 'no'}.")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(out)


if __name__ == "__main__":
    main()
