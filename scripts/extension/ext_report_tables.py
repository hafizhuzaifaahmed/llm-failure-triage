"""Render the CFP result tables as Markdown from the EXT-1 and EXT-2 JSON outputs (no number is typed by hand).

    python scripts/extension/ext_report_tables.py --run CFP_D1_TEST  -> docs/research_extension/generated/cfp_tables_<run>.md
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def f3(x):
    return "n/a" if x is None else f"{x:.3f}"


def ci(c):
    return "n/a" if not c else f"[{c[0]:.3f}, {c[1]:.3f}]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    e1 = json.loads((ROOT / "results" / "extension" / f"ext1_probe_analysis_{a.run}.json").read_text(encoding="utf-8"))
    e2 = json.loads((ROOT / "results" / "extension" / f"ext2_probe_ablations_{a.run}.json").read_text(encoding="utf-8"))
    L = [f"# CFP result tables, run `{a.run}` (generated; do not edit)", "",
         f"Source: `results/extension/ext1_probe_analysis_{a.run}.json`, `results/extension/ext2_probe_ablations_{a.run}.json`.",
         "Intervals: bug-level cluster bootstrap, 10,000 resamples. PF = program fault (bug-revealing), TF = test fault.", ""]
    s = e1["scored"]
    L += ["## T1. Instances", "", "| Quantity | Value |", "|---|---|",
          f"| Labelled instances with a ledger record | {e1['instances_labelled'] - e1['instances_without_ledger']} of {e1['instances_labelled']} |",
          f"| Scored (PF or TF, not excluded) | {s['instances']} ({s['PF']} PF, {s['TF']} TF) |",
          f"| Bugs; bugs with a PF test | {s['bugs']}; {s['bugs_with_PF']} |",
          f"| Compiled mutants per instance: min / q1 / median / q3 / max | {' / '.join(str(x) for x in e1['n_compiled_quartiles'])} |"]
    for lab, d in sorted(e1["by_label_status"].items()):
        L.append(f"| {lab}: status counts | {', '.join(f'{k} {v}' for k, v in sorted(d.items()))} |")
    L += ["", "## T2. Probe flags by execution label", "",
          "| Flag | PF flagged | TF flagged | Rate PF | Rate TF | Difference [95% CI] | Likelihood ratio | PF share among flagged (overall) |",
          "|---|---|---|---|---|---|---|---|"]
    for f, v in e1["flags"].items():
        L.append(f"| {f} | {v['PF_flagged']} of {s['PF']} | {v['TF_flagged']} of {s['TF']} | {f3(v['rate_PF'])} | {f3(v['rate_TF'])} | "
                 f"{f3(v['diff_PF_minus_TF'])} {ci(v['diff_ci95'])} | {v['LR'] if v['LR'] is not None else 'n/a'} | "
                 f"{f3(v['PF_share_among_flagged'])} ({f3(v['PF_share_overall'])}) |")
    L += ["", f"HP-1 (regression-consistent flip, as fixed in D-134): {'supported' if e1['HP1_rcf_supported'] else 'not supported'}. "
              f"HP-2 (decoupling): {'supported' if e1['HP2_decoupled_supported'] else 'not supported'}.",
          f"AUROC of the flip fraction: {f3(e1['auroc_flip_fraction'])}; of the coupled fraction: {f3(e1['auroc_coupled_fraction'])}.",
          f"AMB instances (n = {e1['AMB']['n']}): flip {e1['AMB']['flip']}, rcf {e1['AMB']['rcf']}, decoupled {e1['AMB']['decoupled']}.", ""]
    if "policies" in e1:
        p = e1["policies"]
        L += [f"## T3. Certificate rules beside their base rules ({p['set']}, {p['instances']} instances, {p['PF']} PF)", "",
              "| Rule | TPR | TNR | Balanced accuracy | PF tests lost | Bugs lost | Δ balanced accuracy [95% CI] | Δ TPR [95% CI] | Δ TNR [95% CI] | Δ bugs lost [95% CI] |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for base, r in p["rules"].items():
            b = r["base"]
            L.append(f"| **{base}** | {f3(b['TPR'])} | {f3(b['TNR'])} | {f3(b['BA'])} | {b['PF_lost']:.1f} | {b['bugs_lost']:.1f} | — | — | — | — |")
            for rule, v in r.items():
                if rule == "base":
                    continue
                d, c = v["delta_vs_base"], v["delta_ci95"]
                L.append(f"| {base} + {rule} | {f3(v['TPR'])} | {f3(v['TNR'])} | {f3(v['BA'])} | {v['PF_lost']:.1f} | {v['bugs_lost']:.1f} | "
                         f"{d['BA']:+.3f} {ci(c['BA'])} | {d['TPR']:+.3f} {ci(c['TPR'])} | {d['TNR']:+.3f} {ci(c['TNR'])} | "
                         f"{d['bugs_lost']:+.1f} {ci(c['bugs_lost'])} |")
        L.append("")
    L += ["## T4. Ablations (EXT-2)", "", "| Ablation | Setting | PF flipped | TF flipped | Rate PF | Rate TF |", "|---|---|---|---|---|---|"]
    for name, v in e2["scope"].items():
        fl = v["flip"]
        L.append(f"| Region | {name} (≥10 mutants: {v['usable_10plus']} instances) | {fl['PF'][0]} of {fl['PF'][1]} | {fl['TF'][0]} of {fl['TF'][1]} | {f3(fl['rate_PF'])} | {f3(fl['rate_TF'])} |")
    for name, v in e2["operators"].items():
        L.append(f"| Operators | {name} | {v['PF'][0]} of {v['PF'][1]} | {v['TF'][0]} of {v['TF'][1]} | {f3(v['rate_PF'])} | {f3(v['rate_TF'])} |")
    for ft, v in e2["failure_type"].items():
        fl = v["flip"]
        L.append(f"| Failure type | {ft} (AUROC of flip fraction {f3(v['auroc_flip_fraction'])}) | {fl['PF'][0]} of {fl['PF'][1]} | {fl['TF'][0]} of {fl['TF'][1]} | {f3(fl['rate_PF'])} | {f3(fl['rate_TF'])} |")
    sh = e2["shared_flip"]
    L.append(f"| Shared flip | flipped by a mutant that flips another failing test of the method | {sh['PF'][0]} of {sh['PF'][1]} | {sh['TF'][0]} of {sh['TF'][1]} | {f3(sh['rate_PF'])} | {f3(sh['rate_TF'])} |")
    L += ["", "| Further quantity | Value |", "|---|---|"]
    for name, v in e2["scope"].items():
        for flag in ("rcf", "decoupled"):
            x = v[flag]
            L.append(f"| {flag}, {name}: PF / TF | {x['PF'][0]} of {x['PF'][1]} / {x['TF'][0]} of {x['TF'][1]} |")
    for ft, v in e2["failure_type"].items():
        x = v["decoupled"]
        L.append(f"| decoupled within {ft}: PF / TF | {x['PF'][0]} of {x['PF'][1]} / {x['TF'][0]} of {x['TF'][1]} |")
    sf, bl, co = e2["sibling_filter"], e2["bug_level"], e2["cost"]
    L += [f"| AUROC of failure type alone (exception = 1) | {f3(e2['auroc_failure_type_alone'])} |",
          f"| Flip mutant runs; regression-consistent; vacuous (no sibling) | {sf['flip_mutant_runs']}; {sf['regression_consistent']}; {sf['vacuous']} |",
          f"| Bugs with a PF test; of which some PF test flips | {bl['bugs_with_PF']}; {bl['of_which_some_PF_test_flips']} |",
          f"| TF-only bugs; of which any test flips | {bl['TF_only_bugs']}; {bl['of_which_any_flip']} |",
          f"| Probe seconds per instance: median / 90th percentile / total over {co['instances']} | {co['seconds_median']} / {co['seconds_p90']} / {co['seconds_total']} |", ""]
    dest = ROOT / "docs" / "research_extension" / "generated" / f"cfp_tables_{a.run}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(L), encoding="utf-8", newline="\n")
    print(dest)


if __name__ == "__main__":
    main()
