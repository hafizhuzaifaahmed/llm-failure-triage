"""Render docs/research_extension/generated/wdp_report.md from results/extension/wdp/wdp_analysis.json (WDP; D-147).

    python scripts/extension/wdp_report.py [--in <analysis.json>] [--out <report.md>]

The first line states the status sentence of OPUS_EXECUTION_BRIEF.md rule 0.7. Every number comes from the JSON.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATUS_LINE = ("Status: exploratory; protocol frozen internally in Git before the run; not externally preregistered; "
               "designed after the confirmation outcomes were known.")
LEVELS = ("FS", "WS", "RI", "U", "ND")


def _fmt(x):
    if x is None:
        return "n/a"
    if isinstance(x, float):
        return f"{x:.4f}"
    if isinstance(x, list):
        return "[" + ", ".join(_fmt(v) for v in x) + "]"
    return str(x)


def ladder_table(title: str, groups: dict) -> list[str]:
    lines = [f"#### {title}", "", "| group | label | n | " + " | ".join(LEVELS) + " | ND by reason |",
             "|---|---|---|" + "---|" * len(LEVELS) + "---|"]
    for g, lad in groups.items():
        for lab in ("PF", "TF"):
            d = lad.get(lab, {})
            if not d.get("n"):
                continue
            reasons = ", ".join(f"{k} {v}" for k, v in d["ND_by_reason"].items()) or "-"
            lines.append(f"| {g} | {lab} | {d['n']} | " + " | ".join(str(d[k]) for k in LEVELS) + f" | {reasons} |")
    return lines + [""]


def render(a: dict) -> str:
    L = [STATUS_LINE, "", "# Whole-method dependence probes (WDP): retrospective evaluation report", "",
         f"Level U means: {a['level_U_means']} (an operational observation, not a proof that the test cannot "
         "reach the method). Model calls: 0. Bootstrap: bug-level, "
         f"{a['resamples']} resamples, seed {a['seed']}, percentile intervals.", "", "## Populations", "",
         "| population | instances | PF | TF | bugs | bugs with PF |", "|---|---|---|---|---|---|"]
    for k, v in a["populations"].items():
        L.append(f"| {k} | {v['instances']} | {v['PF']} | {v['TF']} | {v['bugs']} | {v['bugs_with_PF']} |")
    p = a["primary"]
    c = p["criterion"]
    t = p["paired"]["TNR"]
    L += ["", "## Primary outcome (CONF-votes)", "",
          f"dTNR = TNR(KUU + CD-U) - TNR(KUU) = {_fmt(t['difference'])}, 95% interval {_fmt(t['ci95'])}.", "",
          f"- (i) safety (KUU + CD-U loses exactly the bugs KUU loses): {c['i_safety']} "
          f"(KUU loses {len(p['bugs_lost_KUU'])}; additional: {', '.join(p['additional_bugs_lost']) or 'none'})",
          f"- (ii) interval lower limit above 0: {c['ii_ci_lower_above_0']}",
          f"- (iii) the decoupled PF test of Math_59 is not level U: {c['iii_math59_decoupled_pf_not_U']} "
          f"(levels: {', '.join(c['math59_decoupled_pf_levels']) or 'none found'})", "",
          f"**Primary criterion: {c['result']}.**", ""]
    if c.get("note"):
        L += [f"Note: {c['note']}.", ""]
    if a.get("pooled_bound"):
        pb = a["pooled_bound"]
        L += [f"Pooled bound: additional bugs lost 0 of {pb['bugs_with_PF']} PF-bearing bugs, one-sided 95% upper "
              f"bound {_fmt(pb['upper95'])}; {pb['caveat']}.", ""]
    s = a["secondary"]
    L += ["## Secondary outcomes (descriptive)", "", "### 1. Pilot (PILOT-votes)", "",
          f"dTNR {_fmt(s['1_pilot']['paired']['TNR']['difference'])}, interval "
          f"{_fmt(s['1_pilot']['paired']['TNR']['ci95'])}; additional bugs lost: "
          f"{', '.join(s['1_pilot']['additional_bugs_lost']) or 'none'}; level of the decoupled PF test of Codec_13: "
          f"{', '.join(s['1_pilot']['codec13_decoupled_pf_levels']) or 'none found'}.", "",
          "### 2. KUU + CD-U against KUU + CD (CONF-votes)", ""]
    for k, v in s["2_CDU_vs_CD"].items():
        L.append(f"- {k}: {_fmt(v['difference'])} {_fmt(v['ci95'])}")
    L += ["", "### 3. P(U | TF) - P(U | PF)", ""]
    for pop, d in s["3_level_U_by_label"].items():
        for k, v in d.items():
            L.append(f"- {pop}, {k}: TF {v['TF_flagged']}/{v['TF']}, PF {v['PF_flagged']}/{v['PF']}, difference "
                     f"{_fmt(v['difference_TF_minus_PF'])} {_fmt(v['ci95'])}")
    L += ["", "### 4. The ladder", ""]
    lad = s["4_ladder"]
    L += ladder_table("By dataset", lad["by_dataset"])
    L += ladder_table("By frame", lad["by_frame"])
    L += ladder_table("By project", lad["by_project"])
    L += ladder_table("Inside the registered decoupled set", lad["registered_decoupled"])
    L += ["### 5. Low-mutant stratum", ""] + ladder_table("Fewer than ten compiled first-order mutants, no FLIP or "
                                                        "SHIFT", s["5_low_mutant_stratum"])
    L += ["### 6-7. Rule tables", ""]
    cols = ("TPR", "TNR", "BA", "PF_lost", "bugs_lost", "upper95_bug_loss_rate", "tests_kept", "PF_share_of_kept",
            "wrong_kept_per_PF_kept_labelled", "wrong_kept_per_PF_kept_at_5pct")
    for pop, tab in s["6_rules"].items():
        L += [f"#### {pop} ({tab['instances']} tests, {tab['PF']} PF, {tab['bugs_with_PF']} bugs with PF)", "",
              "| rule | " + " | ".join(cols) + " | bugs lost |", "|---|" + "---|" * (len(cols) + 1)]
        for name, row in tab.items():
            if isinstance(row, dict):
                L.append(f"| {name} | " + " | ".join(_fmt(row[k]) for k in cols) + " | "
                         f"{', '.join(row['bugs_lost_names']) or '-'} |")
        L.append("")
    L += ["The 5% column assumes a prevalence of 0.05: (1 - pi)(1 - TNR) / (pi * TPR).", "",
          "### 8. Pre-filter", ""]
    for k, v in s["8_prefilter"].items():
        L.append(f"- {k}: " + ", ".join(f"{a_} {_fmt(b)}" for a_, b in v.items()))
    L += ["", "### 9. Heterogeneity", ""]
    for k, v in s["9_heterogeneity"].items():
        if k == "leave_one_project_out":
            for proj, d in v.items():
                L.append(f"- without {proj}: dTNR {_fmt(d['dTNR'])}, additional bugs lost "
                         f"{', '.join(d['additional_bugs_lost']) or 'none'}")
        elif k == "leave_one_project_out_levels":
            for proj, d in v.items():
                L.append(f"- CONF-all without {proj}: " + "; ".join(
                    f"{name} TF {c['TF_flagged']}/{c['TF']}, PF {c['PF_flagged']}/{c['PF']}, difference "
                    f"{_fmt(c['difference_TF_minus_PF'])}" for name, c in d.items()))
        else:
            pr = v.get("primary")
            L.append(f"- {k}: {v['instances']} tests, {v['PF']} PF" + (
                f"; dTNR {_fmt(pr['paired']['TNR']['difference'])} {_fmt(pr['paired']['TNR']['ci95'])}, "
                f"additional bugs lost {', '.join(pr['additional_bugs_lost']) or 'none'}" if pr else ""))
    L += ["", "### 10. Control group", ""] + ladder_table("CTRL", {"CTRL": s["10_control"]})
    L += ["### 11. Cost", "", "| frame | tests | seconds mean | executions mean | first-order seconds mean |",
          "|---|---|---|---|---|"]
    for fr, v in s["11_cost"].items():
        L.append(f"| {fr} | {v['tests']} | {_fmt(v['seconds_mean'])} | {_fmt(v['executions_mean'])} | "
                 f"{_fmt(v['first_order_seconds_mean'])} |")
    L += ["", "### 12. Diagnostics", "", "```", json.dumps(s["12_diagnostics"], indent=1), "```", "",
          "## Quality checks", "", "```", json.dumps(a["quality_checks"], indent=1), "```", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=str(ROOT / "results" / "extension" / "wdp" / "wdp_analysis.json"))
    ap.add_argument("--out", default=str(ROOT / "docs" / "research_extension" / "generated" / "wdp_report.md"))
    a = ap.parse_args()
    text = render(json.loads(Path(a.inp).read_text(encoding="utf-8")))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(text, encoding="utf-8", newline="\n")
    print("written", a.out)


if __name__ == "__main__":
    main()
