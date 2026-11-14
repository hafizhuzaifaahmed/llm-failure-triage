"""Every number in the paper and the Phase 3 report, resolved from a committed file (write-up phase).

The manuscript writes a value as \\V{key} and the Phase 3 report source as {{key}}; nothing numeric about the results
is typed by hand. This script resolves each key that is actually used, from the file its prefix names, and writes

    paper/generated/numbers.tex                         \\V{key} -> value
    docs/paper/NUMBERS_MAP.csv                          claim, value, source file, field, category, where used
    docs/PHASE3_IMPLEMENTATION_AND_EXPERIMENTAL_REPORT.md   rendered from docs/phase3/PHASE3_REPORT.src.md
    paper/figures/<name>                                copies of the committed analysis figures used

A key is `prefix:field:field...[@format]`. CSV prefixes take `row:column`; JSON prefixes take a path, where a list is
indexed by position or by an item's name/term/condition. Unknown keys stop the build. It reads only; it computes no
statistic (the "der" keys are labelled arithmetic on two resolved values, with the formula in the map).

    python scripts/paper/build_numbers.py           # build
    python scripts/paper/build_numbers.py --check   # also list bare numerals left in the manuscript prose
"""
import argparse
import csv
import json
import math
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AF = "results/heldout/analysis_final"
TEX = ROOT / "paper" / "PHASE4_RESEARCH_PAPER.tex"
MD_SRC = ROOT / "docs" / "phase3" / "PHASE3_REPORT.src.md"
MD_OUT = ROOT / "docs" / "PHASE3_IMPLEMENTATION_AND_EXPERIMENTAL_REPORT.md"
# D-80: further Markdown documents rendered the same way (source -> output)
MD_DOCS = {MD_SRC: MD_OUT,
           ROOT / "docs" / "paper" / "src" / "EXTERNAL_SUBMISSION_PLAN.src.md": ROOT / "docs" / "paper" / "EXTERNAL_SUBMISSION_PLAN.md",
           ROOT / "docs" / "paper" / "src" / "REVISION_REPORT_D80.src.md": ROOT / "docs" / "paper" / "REVISION_REPORT_D80.md",
           ROOT / "docs" / "paper" / "src" / "REVISION_REPORT_D81.src.md": ROOT / "docs" / "paper" / "REVISION_REPORT_D81.md",
           ROOT / "docs" / "paper" / "src" / "SESSION_CHECKLISTS.src.md": ROOT / "docs" / "paper" / "SESSION_CHECKLISTS.md",
           ROOT / "docs" / "paper" / "src" / "DEFENSE_QA.src.md": ROOT / "docs" / "paper" / "DEFENSE_QA.md",
           ROOT / "docs" / "paper" / "src" / "E9_FRONTIER_JUDGE_DRAFT.src.md": ROOT / "docs" / "paper" / "E9_FRONTIER_JUDGE_DRAFT.md",
           ROOT / "docs" / "paper" / "src" / "PRESENTATION_OUTLINE.src.md": ROOT / "docs" / "paper" / "PRESENTATION_OUTLINE.md",
           ROOT / "docs" / "paper" / "src" / "DEFENSE_DECK.src.md": ROOT / "docs" / "paper" / "DEFENSE_DECK.md",
           ROOT / "docs" / "paper" / "src" / "STUDY_GUIDE.src.md": ROOT / "docs" / "paper" / "STUDY_GUIDE.md"}
OUT_TEX = ROOT / "paper" / "generated" / "numbers.tex"
OUT_MAP = ROOT / "docs" / "paper" / "NUMBERS_MAP.csv"

# prefix -> (file, kind, category, description)
SOURCES = {
    "d1": (f"{AF}/D1_M1/tables/conditions.csv", "csv", "result", "D1-test, judge M1"),
    "d2": (f"{AF}/D2_M1/tables/conditions.csv", "csv", "result", "D2 seeded faults, judge M1"),
    "d1m2": (f"{AF}/D1_M2/tables/conditions.csv", "csv", "result", "D1-test, judge M2"),
    "d2m2": (f"{AF}/D2_M2/tables/conditions.csv", "csv", "result", "D2 seeded faults, judge M2"),
    "conf": (f"{AF}/D1_M1/tables/confirmatory.json", "json", "result", "D1-test M1 confirmatory family (Holm)"),
    "conf2": (f"{AF}/D2_M1/tables/confirmatory.json", "json", "result", "D2 M1 confirmatory contrasts (not confirmatory on D2)"),
    "abl": (f"{AF}/D1_M1/tables/ablations.json", "json", "result", "D1-test M1 ablation vs parent"),
    "sum": (f"{AF}/D1_M1/analysis_summary.json", "json", "result", "D1-test M1 analysis summary"),
    "sum2": (f"{AF}/D2_M1/analysis_summary.json", "json", "result", "D2 M1 analysis summary"),
    "sum1m2": (f"{AF}/D1_M2/analysis_summary.json", "json", "result", "D1-test M2 analysis summary"),
    "sum2m2": (f"{AF}/D2_M2/analysis_summary.json", "json", "result", "D2 M2 analysis summary"),
    "r3": (f"{AF}/R3/r3_model_robustness.json", "json", "result", "R3 M1 vs M2 on shared instances"),
    "glmmb": (f"{AF}/D1_M1/tables/glmm_e2_bootstrap.json", "json", "result", "E2 GLMM odds ratios with bug-level cluster-bootstrap intervals (D-79)"),
    "mde": (f"{AF}/D1_M1/tables/mde_sensitivity.json", "json", "result (post hoc sensitivity)",
            "minimum detectable ΔF1 at 80% power, bug-level bootstrap SE (D-80)"),
    "cost": (f"{AF}/D1_M1/tables/cost_latency_s1.json", "json", "result", "cost and latency per arm from the call log (D-80)"),
    "xd": (f"{AF}/D1_M1/tables/exploratory_d82.json", "json", "result (exploratory, D-82)",
           "exploratory analyses D1-D4 declared in D-82"),
    "fcost": ("results/planning/frontier_cost_estimate.json", "json", "planning (estimate, nothing called)",
              "frontier-judge cost estimate (D-82)"),
    "sel": (f"{AF}/D1_M1/tables/selective_vs_ka.json", "json", "result (exploratory, D-82)",
            "selective triage vs keep-all (D-82 follow-up)"),
    "zhao": (f"{AF}/zhao_replication.json", "json", "result (replication check)",
             "Zhao et al. effective-test share from our records"),
    "proj": ("results/planning/external_projection.json", "json", "planning (proposal, not a result)",
             "GPU-time projection for proposals E6-E8 (D-80)"),
    "x35": ("results/expl_35b/analysis/expl_35b_vs_m1_m2.json", "json", "result (exploratory)",
            "EXPLORATORY qwen3.5:35b vs M1/M2"),
    "e6a": ("results/expl_35b/analysis/e6a_j1_deb/expl_35b_vs_m1_m2.json", "json", "result (exploratory)",
            "EXPLORATORY qwen3.5:35b vs M1/M2, DEB completed (E6a, D-89)"),
    "e6b": ("results/e6b/analysis/e6b_d1test.json", "json", "result (robustness, D-82)",
            "E6b third-family judge ministral-3:14b on D1-test (H6-1..H6-3)"),
    "e8": ("results/e8/analysis/e8_d1test.json", "json", "result (D-82/D-90)",
           "E8 three-family vote on D1-test (H8-1..H8-3, Holm)"),
    "gtr": ("results/heldout/generation_truncation.json", "json", "setup (zero-call check, D-91)",
            "generations lost to length (truncation check)"),
    "q87": ("results/quarantine_d87/summary.json", "json", "disclosure (D-87)",
            "unplanned calls quarantined unread (counts only)"),
    "x35o": ("results/expl_35b/outcome.json", "json", "result (exploratory)", "35b run outcome record (D-78, D-89)"),
    "aud": ("data/ground_truth_store/audit/audit_sample_summary.json", "json", "setup", "label-audit sample counts (D-45)"),
    "e9": ("results/e9/analysis/e9_d1test.json", "json", "result (frontier reference point, D-92/D-97)",
           "E9 Claude Sonnet 5.5, frontier reference point, not a protocol replication"),
    "kuu1": ("results/kuu/analysis/kuu_d1_posthoc.json", "json", "result (post hoc, development evidence, D-95)",
             "KUU on D1-test from the E8 calls"),
    "kuu2": ("results/kuu/analysis/kuu_d2.json", "json", "result (confirmatory, D-95)", "KUU on D2 with fresh calls"),
    "e9b": ("results/e9b/analysis/e9b_d2.json", "json", "result (frontier reference point, memorisation check, D-104)",
            "E9b Claude Sonnet 5.5 on D2, frontier reference point, not a protocol replication"),
    "ed": ("results/kuu/analysis/error_diversity.json", "json", "result (pre-specified exploratory, D-105)",
           "error diversity behind KUU (D1 post hoc, D2 pre-registered)"),
    "cas1": ("results/cascade/analysis/cascade_d1_posthoc.json", "json", "result (post hoc, development evidence, D-105)",
             "KUU with disagreement escalation, cascade on D1-test"),
    "cas2": ("results/cascade/analysis/cascade_d2.json", "json", "result (confirmatory, D-105)",
             "KUU with disagreement escalation, cascade on D2"),
    "rv": (f"{AF}/D1_M1/tables/review_sensitivity.json", "json", "result (post hoc sensitivity, D-106)",
           "sensitivity analyses requested by the mock reviews"),
    "loo": ("results/kuu/analysis/kuu_loo.json", "json", "result (post hoc sensitivity, D-107)",
            "leave-one-judge-out sensitivity for KUU"),
    "aud2": ("results/audit/label_audit_scores.json", "json", "result (label audit, D-82/D-84/D-108)",
             "two-rater label audit scores"),
    "kuung": ("results/kuung/analysis/kuung.json", "json", "result (fixed in advance, D-109; D1 status as for KUU)",
              "KUU-NG, a KUU panel with no generator-family judge (H13-1, H13-2)"),
    "kuungm": ("results/kuung/analysis/kuung_members.json", "json", "result (post hoc, descriptive, D-111)",
               "KUU and KUU-NG member vote rates"),
    "kuungsel": ("results/kuung/selection.json", "json", "setup (development split, D-109)",
                 "KUU-NG fourth-judge selection"),
    "pareto": ("results/pareto/pareto.json", "json", "result (post hoc, descriptive, D-110)",
               "discard-loss trade-off of every rule"),
    "e7a": ("results/e7a/selection.json", "json", "setup (development split, D-100/D-102)",
            "E7a second-generator selection on dev (D-22); E7a not run"),
    "rn": (f"{AF}/D1_M1/tables/replicate_noise.json", "json", "result (exploratory, D-94)",
           "M1 replicate noise vs single-replicate cross-model differences"),
    "seal": ("docs/audits/kit/LLM_RATER_SEAL.json", "json", "setup", "blind LLM rater seal (D-84)"),
    # review-response pass (D-112 onward): every value post hoc or exploratory, none confirmatory
    "rv11": ("results/revision/wp11_rates.json", "json", "result (post hoc, descriptive, D-113)",
             "prevalence-independent rates of every rule"),
    "rv13": ("results/revision/wp13_ranking.json", "json", "result (post hoc, descriptive, D-114)",
             "triage as ranking: AUROC, AUPRC, top-k inspection"),
    "rv14": ("results/revision/wp14_learned.json", "json", "result (exploratory, D-115)",
             "trained baselines, leave-one-project-out"),
    "rv15": ("results/revision/wp15_k_of_n.json", "json", "result (post hoc, descriptive, D-116)", "k-of-3 discard rules"),
    "rv16": ("results/revision/wp16_risk.json", "json", "result (exploratory, D-117)", "risk-targeted discard threshold"),
    "rv17": ("results/revision/wp17_cross_gen.json", "json", "result (exploratory, D-118)",
             "cross-generation consensus signal"),
    "rv18": ("results/revision/wp18_sample_size.json", "json", "planning (guidance, not a power guarantee, D-119)",
             "bugs needed for a given MDE"),
    "rv19": ("results/revision/wp19_integrity.json", "json", "result (sensitivity, D-120)",
             "integrity checks and GEE sensitivity"),
    "rv110": ("results/revision/wp110_wp111.json", "json", "result (post hoc, D-121)",
              "leakage-guard selection effect and label-noise sensitivity"),
    "rv2": ("results/revision/wp2_local_runs.json", "json", "result (exploratory, D-124 to D-127)",
            "WP2 local runs and the judge gate table"),
    "cfgt0": ("configs/revision/REV_J1_T0_M1.json", "json", "setup (D-125)", "greedy J1 run configuration"),
    "cfgth": ("configs/revision/REV_THINK_M1.json", "json", "setup (D-126)", "thinking J1 run configuration"),
    "tf176": ("data/processed/sample_D1_test_TF176.json", "json", "setup (D-124)", "the D1-test TF never judged before"),
    "sfc": ("results/planning/sonnet_factorial_estimate.json", "json", "planning (estimate, nothing called, D-128)",
            "Sonnet factorial cost estimate"),
    "tk": ("results/revision/think_followup.json", "json", "result (gate check; D2 confirmation committed before the calls; D1 replicates exploratory, D-130)",
            "thinking-judge follow-up: gate, D2 HT-1/HT-2, D1 replicates, cap sensitivity, tokens"),
    "lc": ("results/revision/local_cascade.json", "json", "result (post hoc, D-132; to be confirmed on fresh data)",
           "fully local cascade: KUU unanimity, disagreements to the thinking-enabled M1 J1"),
    # setup facts: committed files outside the two analysis directories (flagged in the map)
    "split": ("data/processed/split_manifest.json", "json", "setup", "D1 frame and project split"),
    "ds1": ("data/processed/dataset_summary_D1.json", "json", "setup", "D1 execution and labelling summary"),
    "ds2": ("data/processed/dataset_summary_D2.json", "json", "setup", "D2 execution and labelling summary"),
    "d2rep": ("results/heldout/d2_sample_report.json", "json", "setup", "D2 sample report (D-64)"),
    "frozen": ("configs/local_models.FROZEN.json", "json", "setup", "frozen model configuration (D-57)"),
    "devgate": ("results/dev/GATE_M1b/dev_gates.json", "json", "setup (development split)", "M1 development gate"),
    "gsel": ("results/dev/g_selection_gemma4_26b.json", "json", "setup (development split)", "generator selection"),
    "nondet": ("results/dev/nondeterminism.json", "json", "setup (development split)", "non-determinism check"),
    "d2ab": ("results/heldout/d2_abort_vs_mutant.json", "json", "setup", "D2 leakage aborts vs the mutant record (D-70 note)"),
}

# labelled arithmetic on resolved values (formula recorded); never a new statistic
DERIVED = {
    "der:d1 DEB-KA f1": (lambda v: v("d1:DEB|S1:f1") - v("d1:KA:f1"), "d1:DEB|S1:f1 - d1:KA:f1"),
    "der:d1 DEB-R0 f1": (lambda v: v("d1:DEB|S1:f1") - v("d1:R0:f1"), "d1:DEB|S1:f1 - d1:R0:f1"),
    "der:d1 DEB-R0 mcc": (lambda v: v("d1:DEB|S1:mcc") - v("d1:R0:mcc"), "d1:DEB|S1:mcc - d1:R0:mcc"),
    "der:d1 DEB-J1 f1": (lambda v: v("d1:DEB|S1:f1") - v("d1:J1|S1:f1"), "d1:DEB|S1:f1 - d1:J1|S1:f1"),
    "der:d1 DEB-R0 f1 rel": (lambda v: (v("d1:DEB|S1:f1") - v("d1:R0:f1")) / v("d1:R0:f1"),
                             "(d1:DEB|S1:f1 - d1:R0:f1) / d1:R0:f1"),
    "der:d1 DEB-SC f1 rel": (lambda v: (v("d1:DEB|S1:f1") - v("d1:SC|S1:f1")) / v("d1:SC|S1:f1"),
                             "(d1:DEB|S1:f1 - d1:SC|S1:f1) / d1:SC|S1:f1"),
    "der:d1 DEB-J1 f1 rel": (lambda v: (v("d1:DEB|S1:f1") - v("d1:J1|S1:f1")) / v("d1:J1|S1:f1"),
                             "(d1:DEB|S1:f1 - d1:J1|S1:f1) / d1:J1|S1:f1"),
    "der:d1 DEB-KA f1 rel": (lambda v: (v("d1:DEB|S1:f1") - v("d1:KA:f1")) / v("d1:KA:f1"),
                             "(d1:DEB|S1:f1 - d1:KA:f1) / d1:KA:f1"),
    "der:d1 best S1 LLM - KA f1": (lambda v: max(v(f"d1:{a}|S1:f1") for a in ("J1", "SC", "SC-T", "DEB")) - v("d1:KA:f1"),
                                   "max(d1:J1|S1:f1, d1:SC|S1:f1, d1:SC-T|S1:f1, d1:DEB|S1:f1) - d1:KA:f1"),
    "der:d1 best S1 LLM is DEB": (lambda v: "DEB" if max(("J1", "SC", "SC-T", "DEB"), key=lambda a: v(f"d1:{a}|S1:f1")) == "DEB" else "not DEB",
                                  "argmax over S1 LLM arms of d1:<arm>|S1:f1"),
    "der:mde all below": (lambda v: "yes" if all(t["abs_delta_over_mde_005"] < 1 for t in v("mde:tests")) else "no",
                          "all(mde:tests:*:abs_delta_over_mde_005 < 1)"),
    "der:d2 SC-DEB f1": (lambda v: v("d2:SC|S1:f1") - v("d2:DEB|S1:f1"), "d2:SC|S1:f1 - d2:DEB|S1:f1"),
    "der:d2 DEB-KA f1": (lambda v: v("d2:DEB|S1:f1") - v("d2:KA:f1"), "d2:DEB|S1:f1 - d2:KA:f1"),
    "der:d1 J1 S1-S0 f1": (lambda v: v("d1:J1|S1:f1") - v("d1:J1|S0:f1"), "d1:J1|S1:f1 - d1:J1|S0:f1"),
    "der:d1 SC S1-S0 f1": (lambda v: v("d1:SC|S1:f1") - v("d1:SC|S0:f1"), "d1:SC|S1:f1 - d1:SC|S0:f1"),
    "der:d1 DEB S1-S0 f1": (lambda v: v("d1:DEB|S1:f1") - v("d1:DEB|S0:f1"), "d1:DEB|S1:f1 - d1:DEB|S0:f1"),
    "der:d1 test TF labelled": (lambda v: sum(p["TF_total"] for p in v("ds1:sample:test:per_project").values()),
                                "sum over projects of ds1:sample:test:per_project:*:TF_total"),
    "der:d1 test PF labelled": (lambda v: sum(p["PF"] for p in v("ds1:sample:test:per_project").values()),
                                "sum over projects of ds1:sample:test:per_project:*:PF"),
    "der:d1 test AMB labelled": (lambda v: sum(p["AMB"] for p in v("ds1:sample:test:per_project").values()),
                                 "sum over projects of ds1:sample:test:per_project:*:AMB"),
    "der:d2 aborted instances": (lambda v: len({x["instance_id"] for x in v("d2ab")}),
                                 "number of distinct instance_id in d2ab"),
    "der:d2 aborts mutated line": (lambda v: len({x["instance_id"] for x in v("d2ab") if x["matched_is"] == "the mutated line"}),
                                   "distinct instance_id in d2ab with matched_is == 'the mutated line'"),
    "der:dev methods": (lambda v: sum(v(f"split:per_project:{p}:sampled") for p in v("split:dev_projects")),
                        "sum of split:per_project:<dev project>:sampled"),
    "der:test methods": (lambda v: sum(v(f"split:per_project:{p}:sampled") for p in v("split:test_projects")),
                         "sum of split:per_project:<test project>:sampled"),
    "der:n test projects": (lambda v: len(v("split:test_projects")), "len(split:test_projects)"),
    # review-response pass (D-113 to D-127)
    "der:inv keep max dBA": (lambda v: max(abs(s["invalid_as_keep"]["ba"] - s["primary_invalid_as_TF"]["ba"])
                                           for ds in ("D1", "D2") for s in v(f"rv11:{ds}:invalid_sensitivity").values()),
                             "max over D1, D2 and arms of |rv11:<ds>:invalid_sensitivity:<arm>:invalid_as_keep:ba - "
                             "...:primary_invalid_as_TF:ba|"),
    "der:tf176 n": (lambda v: len(v("tf176:instance_ids")), "len(tf176:instance_ids)"),
    "der:holm families": (lambda v: len(v("rv19:holm")), "len(rv19:holm)"),
    "der:holm all match": (lambda v: "all" if all(f["matches"] for f in v("rv19:holm")) else "not all",
                           "all(rv19:holm:*:matches)"),
    "der:local judges failing G-d": (lambda v: sum(1 for g in v("rv2:gates").values() if g.get("G_d") is False),
                                     "count of rv2:gates:* with G_d == false"),
    "der:local judges gated": (lambda v: sum(1 for g in v("rv2:gates").values() if g.get("G_d") is not None),
                               "count of rv2:gates:* with a G_d outcome"),
    "der:d2 guard pf share": (lambda v: v("rv110:guard:D2:aborted_by_label:PF") / v("rv110:guard:D2:aborted_at_S1_any_run"),
                              "rv110:guard:D2:aborted_by_label:PF / rv110:guard:D2:aborted_at_S1_any_run"),
}

GATE_JUDGES = {"M1": "M1 (Qwen3.5 9B)", "M2": "M2 (Gemma 4 12B)", "M3": "E6b (Ministral 3 14B)", "NG": "NG (Llama 3.1 8B)"}
for _short, _name in GATE_JUDGES.items():          # D-127: development-gate outcome per local judge, as pass/fail text
    for _g in ("G_a", "G_b", "G_c", "G_d"):
        DERIVED[f"der:gate {_short} {_g}"] = (
            (lambda v, n=_name, g=_g: "pass" if v(f"rv2:gates:{n}")[g] else "fail"),
            f"'pass' if rv2:gates:{_name}:{_g} else 'fail'")

# numbers taken from the cited papers (marked * in the manuscript); value as printed there, verified source
LIT = "docs/source_documents/AdvancedAI_Phase1_LiteratureReview (1).pdf"
P2 = "docs/source_documents/phase2/Phase_2_assignment/Phase2_Research_Methodology_Design.pdf"
CITED = {
    "cit:jstestcraft recall": ("68.75", "liu2026jstestcraft, as quoted in", LIT),
    "cit:jstestcraft audit n": ("296", "liu2026jstestcraft, as quoted in", LIT),
    "cit:jstestcraft pass": ("60.9", "liu2026jstestcraft, as quoted in", LIT),
    "cit:jstestcraft branch": ("47.3", "liu2026jstestcraft, as quoted in", LIT),
    "cit:javaoracle precision": ("0.889", "fu2026javaoracle, as quoted in", LIT),
    "cit:javaoracle tp before": ("14.33", "fu2026javaoracle, as quoted in", LIT),
    "cit:javaoracle tp after": ("5.33", "fu2026javaoracle, as quoted in", LIT),
    "cit:maco line": ("84.4", "xie2026maco, as quoted in", LIT),
    "cit:maco branch": ("79.2", "xie2026maco, as quoted in", LIT),
    "cit:testart pass": ("78.55", "gu2026testart, as quoted in", LIT),
    "cit:walczak docstring": ("19.67", "walczak2026context, as quoted in", LIT),
    "cit:target em": ("66.1", "yaraghi2025target, as quoted in", LIT),
    "cit:maddila solve": ("42.3", "maddila2026agentic, as quoted in", LIT),
    "cit:candor lo": ("0.894", "xu2026candor, as quoted in", LIT),
    "cit:candor hi": ("0.930", "xu2026candor, as quoted in", LIT),
    "cit:mitgen ours": ("0.66", "li2026mitgen, as quoted in", LIT),
    "cit:mitgen base": ("0.31", "li2026mitgen, as quoted in", LIT),
    "cit:valtest": ("29", "taherkhani2026valtest, as quoted in", LIT),
    "cit:chatassert": ("15", "hayet2025chatassert, as quoted in", LIT),
    "cit:maco methods": ("41", "xie2026maco, as quoted in", LIT),
    "cit:jstestcraft repos": ("20", "liu2026jstestcraft, as quoted in", LIT),
    "cit:walczak methods": ("12", "walczak2026context, as quoted in", LIT),
    "cit:zhao lo": ("2.09", "zhao2026misguidance, as quoted in", P2),
    "cit:zhao hi": ("4.54", "zhao2026misguidance, as quoted in", P2),
}

_cache = {}


def _load(prefix):
    if prefix not in _cache:
        path, kind, *_ = SOURCES[prefix]
        f = ROOT / path
        if kind == "csv":
            _cache[prefix] = {r[next(iter(r))]: r for r in csv.DictReader(open(f, encoding="utf-8"))}
        else:
            _cache[prefix] = json.loads(f.read_text(encoding="utf-8").replace("NaN", "null"))
    return _cache[prefix]


def _norm(s):
    return str(s).replace("\u2212", "-").replace(" ", "")


def _step(node, part):
    if isinstance(node, dict):
        if part in node:
            return node[part]
        for k in node:
            if _norm(k) == _norm(part):
                return node[k]
        raise KeyError(part)
    if isinstance(node, list) and "~" in part:          # name~metric, e.g. H1~precision in the secondary family
        name, metric = part.split("~", 1)
        for x in node:
            if isinstance(x, dict) and _norm(x.get("name", "")) == _norm(name) and x.get("metric") == metric:
                return x
        raise KeyError(part)
    if isinstance(node, list):
        if part.isdigit() and int(part) < len(node) and not (node and isinstance(node[0], dict)
                                                             and any(_norm(x.get("name", x.get("term", ""))) == part
                                                                     for x in node)):
            return node[int(part)]
        for x in node:
            if isinstance(x, dict) and any(_norm(x.get(f, "")) == _norm(part) for f in ("name", "term", "condition")):
                return x
        raise KeyError(part)
    raise KeyError(part)


def raw(key):
    """The stored value for a key (no formatting)."""
    if key in DERIVED:
        return DERIVED[key][0](raw)
    if key in CITED:
        return CITED[key][0]
    prefix, *path = key.split(":")
    node = _load(prefix)
    for part in path:
        node = _step(node, part)
    if isinstance(node, str) and SOURCES[prefix][1] == "csv":
        try:
            return float(node)
        except ValueError:
            return node
    return node


def fmt(v, key, f, target):
    minus = "\\textminus{}" if target == "tex" else "\u2212"
    pct = "\\%" if target == "tex" else "%"
    last = key.split(":")[-1]

    def num(x, d, signed=False):
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return "n/a"
        s = f"{abs(x):,.{d}f}"
        sign = minus if x < 0 and float(s.replace(",", "")) != 0 else ("+" if signed and x > 0 else "")
        return sign + s

    if f is None:
        if last in ("ci95", "ci90") or last.endswith("_ci95") or "ci95_" in last:
            f = "ci"
        elif last == "delta" or last.endswith("_minus") or (key.startswith("der:") and "-" in key):
            f = "signed"
        elif last in ("p", "p_holm"):
            f = "p"
    if isinstance(v, str) and f not in ("ci", "ci2", "ci0"):
        return v.replace("%", pct).replace("_", "\\_" if target == "tex" else "_") if target == "tex" else v
    if f in ("ci", "ci2", "ci0"):
        lo, hi = (v if isinstance(v, list) else [float(x) for x in v.strip("[]").split(",")])
        d = {"ci2": 2, "ci0": 0}.get(f, 3)
        return f"[{num(lo, d)}, {num(hi, d)}]"
    if isinstance(v, bool) or isinstance(v, (list, dict)):
        return str(v)
    if f == "p":
        lt = "\\textless{}" if target == "tex" else "<"          # a bare < is set as ¡ in the paper's text font
        return f"{minus if v < 0 else ''}{lt}0.001" if v < 0.001 else num(v, 3)
    if f == "signed":
        return num(v, 3, signed=True)
    if f == "abs":
        return num(abs(v), 3)
    if f == "spct":
        return num(100 * v, 1, signed=True) + pct
    if f in ("pct", "pct0", "pct1", "pct2"):
        d = {"pct": 1, "pct0": 0, "pct1": 1, "pct2": 2}[f]
        return num(100 * v, d) + pct
    if f in ("0", "1", "2", "3", "4"):
        return num(v, int(f))
    if f == "int" or (isinstance(v, (int, float)) and float(v).is_integer() and f is None):
        return num(v, 0)
    return num(v, 3)


def resolve(key_fmt, target):
    key, _, f = key_fmt.partition("@")
    return fmt(raw(key), key, f or None, target)


def source_of(key):
    if key in DERIVED:
        return "(derived)", DERIVED[key][1], "derived from resolved values"
    if key in CITED:
        _, who, where = CITED[key]
        return where, f"{who} this file", "taken from paper (*)"
    prefix, *path = key.split(":")
    path_file, _, cat, desc = SOURCES[prefix]
    field = ("row=" + path[0] + "; column=" + ":".join(path[1:])) if SOURCES[prefix][1] == "csv" else ".".join(path)
    return path_file, field, cat


def claim_of(key):
    if key in DERIVED:
        return f"derived: {key[4:]}"
    if key in CITED:
        return f"published figure: {key[4:]}"
    prefix, *path = key.split(":")
    return f"{SOURCES[prefix][3]}: {' / '.join(path)}"


TEX_KEY = re.compile(r"\\V\{([^{}]+)\}")
MD_KEY = re.compile(r"\{\{([^{}]+)\}\}")
FIGURES = {  # copied from the committed analysis outputs into paper/figures/
    "fig_e1_prf_D1.pdf": f"{AF}/D1_M1/figures/fig_e1_prf.pdf",
    "fig_confirmatory_D1.pdf": f"{AF}/D1_M1/figures/fig_confirmatory_forest.pdf",
    "fig_e2_spec_f1_D1.pdf": f"{AF}/D1_M1/figures/fig_e2_spec_f1.pdf",
    "fig_e4_ablations_D1.pdf": f"{AF}/D1_M1/figures/fig_e4_ablations.pdf",
    "fig_e3_pareto_D1.pdf": f"{AF}/D1_M1/figures/fig_e3_pareto.pdf",
    "fig_r5_per_project_D1.pdf": f"{AF}/D1_M1/figures/fig_r5_per_project.pdf",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    used = {}   # key@fmt -> [where]
    texts = {TEX: TEX.read_text(encoding="utf-8")}
    for src in MD_DOCS:
        if src.exists():
            texts[src] = src.read_text(encoding="utf-8")
    for f, t in texts.items():
        rx = TEX_KEY if f.suffix == ".tex" else MD_KEY
        for i, line in enumerate(t.splitlines(), 1):
            if f.suffix == ".tex" and line.lstrip().startswith("%"):
                continue
            for m in rx.finditer(line):
                used.setdefault(m.group(1), []).append(f"{f.relative_to(ROOT).as_posix()}:{i}")
    errors, rows, defs = [], [], []
    for kf in sorted(used):
        try:
            val_tex, val_md = resolve(kf, "tex"), resolve(kf, "md")
        except (KeyError, TypeError, ValueError, IndexError) as e:
            errors.append(f"{kf}: {type(e).__name__} {e}")
            continue
        key = kf.partition("@")[0]
        src, field, cat = source_of(key)
        rows.append({"key": kf, "claim": claim_of(key), "value": val_md, "source_file": src, "field": field,
                     "category": cat, "used_in": " ".join(used[kf])})
        defs.append(f"\\expandafter\\def\\csname V@{kf}\\endcsname{{{val_tex}}}")
    if errors:
        print("UNRESOLVED KEYS:\n  " + "\n  ".join(errors))
        sys.exit(1)
    OUT_TEX.parent.mkdir(parents=True, exist_ok=True)
    OUT_TEX.write_text("% generated by scripts/paper/build_numbers.py -- do not edit; every value is in "
                       "docs/paper/NUMBERS_MAP.csv\n\\makeatletter\n" + "\n".join(defs) + "\n\\makeatother\n",
                       encoding="utf-8")
    OUT_MAP.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_MAP, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for src, dst in MD_DOCS.items():
        if src in texts:
            body = MD_KEY.sub(lambda m: resolve(m.group(1), "md"), texts[src])
            dst.write_text(f"<!-- generated from {src.relative_to(ROOT).as_posix()} by scripts/paper/build_numbers.py; "
                           "every number is in docs/paper/NUMBERS_MAP.csv -->\n" + body, encoding="utf-8")
    for dst, src in FIGURES.items():
        shutil.copyfile(ROOT / src, ROOT / "paper" / "figures" / dst)
    cats = {}
    for r in rows:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    print(f"{len(rows)} values resolved -> {OUT_TEX.relative_to(ROOT)}, {OUT_MAP.relative_to(ROOT)}; by category {cats}")
    if a.check:
        check(texts[TEX])
        check_cited({k.partition("@")[0] for k in used if k.startswith("cit:")})


def check_cited(keys):
    """Each published figure used must appear verbatim in the source document it is attributed to."""
    import subprocess
    texts = {}
    bad = []
    for k in sorted(keys):
        val, _, src = CITED[k]
        if src not in texts:
            texts[src] = subprocess.run(["pdftotext", "-layout", str(ROOT / src), "-"], capture_output=True,
                                        text=True, encoding="utf-8", errors="replace").stdout
        if not re.search(rf"(?<![\d.]){re.escape(val)}(?![\d])", texts[src]):
            bad.append(f"{k} = {val} not found in {src}")
    print(f"\ncited figures checked against their source: {len(keys) - len(bad)}/{len(keys)} found"
          + ("".join(f"\n  MISSING {b}" for b in bad)))


def check(tex):
    """Bare numerals in the manuscript prose (outside \\V, citations, refs, labels, comments, the preamble)."""
    body = tex.split("\\begin{document}", 1)[1]
    body = re.sub(r"(?<!\\)%.*", "", body)
    body = re.sub(r"\\(V|cite|ref|label|includegraphics|eqref|bibliography|begin|end)(\[[^\]]*\])?\{[^{}]*\}", " ", body)
    hits = []
    for i, line in enumerate(body.splitlines(), 1):
        for m in re.finditer(r"(?<![A-Za-z0-9_\\@.{-])\d+(?:[.,]\d+)*", line):
            hits.append((i, m.group(0), line.strip()[:110]))
    print(f"\n{len(hits)} bare numerals in the manuscript body (review: identifiers, years, versions, design constants):")
    for i, n, l in hits:
        print(f"  body+{i}: {n:>8}  | {l}")


if __name__ == "__main__":
    main()
