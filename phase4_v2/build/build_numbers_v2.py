"""Numbers for the `_v2` manuscript (paper/PHASE4_RESEARCH_PAPER_v2.tex), resolved from committed files.

A parallel build, so that no tracked file of the original build changes: it imports `build_numbers.py` unchanged
(its sources, formats and derived values), adds the sources of the registered confirmation, the pilot probe analysis
and the independent audit, and writes

    paper/generated/numbers_v2.tex        \\V{key} -> value, for the _v2 manuscript only
    docs/paper/NUMBERS_MAP_v2.csv          key, value, source file, field or pattern, category, where used

Key kinds, beyond those of build_numbers.py:
    <json prefix>:path        the confirmation, pilot and dataset JSON files listed in NEW_SOURCES
    atx:<name>                a value read by a fixed regular expression from a committed audit or report text file
                              (TXT below; the pattern is written into the map)
    arow:<name>               a count over results/extension/audit/rows.json (the audit's per-test table)
    dv:<name>                 arithmetic on resolved values (formula in the map); computes no statistic

    python scripts/paper/build_numbers_v2.py
"""
import csv
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # repository root: inputs are read here, never written
HERE = Path(__file__).resolve().parents[1]   # phase4_v2: every output is written here
_spec = importlib.util.spec_from_file_location("build_numbers", ROOT / "scripts" / "paper" / "build_numbers.py")
bn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bn)

TEX = HERE / "PHASE4_RESEARCH_PAPER_v2.tex"
OUT_TEX = HERE / "generated" / "numbers_v2.tex"
OUT_MAP = HERE / "NUMBERS_MAP_v2.csv"
CONF = "results/extension/confirm"
AUD = "results/extension/audit"

NEW_SOURCES = {
    "cc": (f"{CONF}/confirm_analysis_CFP_CONF_ALL.json", "json", "confirmatory, registered (OSF kp79c)",
           "registered confirmation, F1+F2 and control"),
    "cf1": (f"{CONF}/confirm_analysis_CFP_CONF_F1_secondary.json", "json", "registered secondary analysis 7",
            "confirmation, frame F1 alone"),
    "cf2": (f"{CONF}/confirm_analysis_CFP_CONF_F2_secondary.json", "json", "registered secondary analysis 7",
            "confirmation, frame F2 alone"),
    "pil": ("results/extension/ext1_probe_analysis_CFP_D1_TEST.json", "json", "exploratory (pilot)",
            "pilot probe analysis, D1-test"),
    "osf": ("configs/extension/osf_registration.json", "json", "registration record", "OSF registration record"),
    "cman": ("configs/extension/confirm_dataset_manifest.json", "json", "registered data", "generation manifest"),
    "dsf1": ("data/extension/confirm/F1/dataset_summary_D1C_F1.json", "json", "registered data", "F1 dataset summary"),
    "dsf2": ("data/extension/confirm/F2/dataset_summary_D1C_F2.json", "json", "registered data", "F2 dataset summary"),
    "dsct": ("data/extension/confirm/CTRL/dataset_summary_D1C_CTRL.json", "json", "registered data",
             "control dataset summary"),
    "cfz": ("configs/extension/cfp_frozen.json", "json", "frozen engine parameters (D-138)",
            "frozen CFP engine configuration"),
    "wdp": ("results/extension/wdp/wdp_analysis.json", "json",
            "exploratory, retrospective (WDP, D-151); not externally preregistered",
            "frozen WDP analysis of the four retrospective runs"),
}
bn.SOURCES.update(NEW_SOURCES)

_N = r"([-+]?\d+(?:\.\d+)?)"
TXT = {   # name -> (file, regex, group or tuple of groups, category)
    "noJ est": (f"{AUD}/A1_robustness.txt", r"without both Jackson projects: " + _N, 1, "exploratory (audit)"),
    "noJ ci": (f"{AUD}/A1_robustness.txt", r"without both Jackson projects: \S+ \(\[" + _N + ", " + _N, (1, 2),
               "exploratory (audit)"),
    "noJ n": (f"{AUD}/A1_robustness.txt", r"without both Jackson projects:.*? n (\d+) PF", 1, "exploratory (audit)"),
    "noJ pf": (f"{AUD}/A1_robustness.txt", r"without both Jackson projects:.*? PF (\d+) decTF", 1, "exploratory (audit)"),
    "noJ dectf": (f"{AUD}/A1_robustness.txt", r"without both Jackson projects:.*? decTF (\d+)", 1, "exploratory (audit)"),
    "noJDB est": (f"{AUD}/A1_robustness.txt", r"without JacksonDatabind: " + _N, 1, "exploratory (audit)"),
    "noJDB ci": (f"{AUD}/A1_robustness.txt", r"without JacksonDatabind: \S+ \(\[" + _N + ", " + _N, (1, 2),
                 "exploratory (audit)"),
    "projboot ci": (f"{AUD}/A1_robustness.txt", r"cluster bootstrap \((\d+) projects\): \(\[" + _N + ", " + _N, (2, 3),
                    "exploratory (audit)"),
    "projboot n": (f"{AUD}/A1_robustness.txt", r"cluster bootstrap \((\d+) projects\)", 1, "exploratory (audit)"),
    "mh": (f"{AUD}/A1_robustness.txt", r"\(MH weights\) risk difference: " + _N, 1, "exploratory (audit)"),
    "top bugs n": (f"{AUD}/A1_robustness.txt", r"tests in the (\d+) bugs with most decoupled TF", 1, "exploratory (audit)"),
    "top bugs dec": (f"{AUD}/A1_robustness.txt", r"bugs with most decoupled TF: (\d+) of", 1, "exploratory (audit)"),
    "nomut pf": (f"{AUD}/A1_robustness.txt", r"flip \| ncomp>=1: PF (\d+)/\d+", 1, "exploratory (audit)"),
    "nomut pfn": (f"{AUD}/A1_robustness.txt", r"flip \| ncomp>=1: PF \d+/(\d+)", 1, "exploratory (audit)"),
    "nomut tf": (f"{AUD}/A1_robustness.txt", r"flip \| ncomp>=1: PF \d+/\d+ TF (\d+)/\d+", 1, "exploratory (audit)"),
    "nomut tfn": (f"{AUD}/A1_robustness.txt", r"flip \| ncomp>=1: PF \d+/\d+ TF \d+/(\d+)", 1, "exploratory (audit)"),
    "nomut f1 pf": (f"{AUD}/A1_robustness.txt", r"\n\s+F1 PF (\d+)/\d+", 1, "exploratory (audit)"),
    "nomut f1 pfn": (f"{AUD}/A1_robustness.txt", r"\n\s+F1 PF \d+/(\d+)", 1, "exploratory (audit)"),
    "nomut f1 tf": (f"{AUD}/A1_robustness.txt", r"\n\s+F1 PF \d+/\d+ TF (\d+)/\d+", 1, "exploratory (audit)"),
    "nomut f1 tfn": (f"{AUD}/A1_robustness.txt", r"\n\s+F1 PF \d+/\d+ TF \d+/(\d+)", 1, "exploratory (audit)"),
    "buglevel pf": (f"{AUD}/A1_robustness.txt", r"with a flipping PF test (\d+)/\d+", 1, "exploratory (audit)"),
    "buglevel tf": (f"{AUD}/A1_robustness.txt", r"bugs with only TF having any flip (\d+)/\d+", 1, "exploratory (audit)"),
    "buglevel tfn": (f"{AUD}/A1_robustness.txt", r"bugs with only TF having any flip \d+/(\d+)", 1, "exploratory (audit)"),
    "auroc flip": (f"{AUD}/A1_robustness.txt", r"flip_fraction: " + _N, 1, "exploratory (audit)"),
    "auroc votes": (f"{AUD}/A1_robustness.txt", r"AUROC #PF votes: " + _N, 1, "exploratory (audit)"),
    "auroc votes dec": (f"{AUD}/A1_robustness.txt", r"decoupled forced to bottom: " + _N, 1, "exploratory (audit)"),
    "dec unanimous": (f"{AUD}/A1_robustness.txt", r"#TF-votes Counter\(\{3: (\d+)", 1, "exploratory (audit)"),
    "stack pf": (f"{AUD}/A1_robustness.txt", r"deepest frame not focal\]: PF flagged (\d+)/", 1, "exploratory (audit)"),
    "stack tf": (f"{AUD}/A1_robustness.txt", r"deepest frame not focal\]: PF flagged \d+/\d+, TF flagged (\d+)/", 1,
                 "exploratory (audit)"),
    "minshield tf": (f"{AUD}/A1_robustness.txt", r"no flip/shift\): (\d+) PF same", 1, "exploratory (audit)"),
    "minshield pf": (f"{AUD}/A1_robustness.txt", r"no flip/shift\): \d+ PF same: (\d+)", 1, "exploratory (audit)"),
    "het ci": (f"{AUD}/A1_recompute.txt", r"heterogeneity C2: F2-F1 CI95 \[" + _N + ", " + _N, (1, 2),
               "exploratory (audit)"),
    "elig pf": (f"{AUD}/A1_recompute.txt", r"F1\+F2: n=572.*?eligible\(>=10 compiled\) PF (\d+)/", 1, "exploratory (audit)"),
    "elig tf": (f"{AUD}/A1_recompute.txt", r"F1\+F2: n=572.*?eligible\(>=10 compiled\) PF \d+/\d+ TF (\d+)/", 1,
                "exploratory (audit)"),
    "elig est": (f"{AUD}/A1_recompute.txt", r"F1\+F2: n=572.*?C2\|eligible \(" + _N, 1, "exploratory (audit)"),
    "elig ci": (f"{AUD}/A1_recompute.txt", r"F1\+F2: n=572.*?C2\|eligible \(\S+ \[" + _N + ", " + _N, (1, 2),
                "exploratory (audit)"),
    "jk c1 ci": (f"{AUD}/A3_jackknife.txt", r"C1:.*?normal 95% \[" + _N + ", " + _N, (1, 2), "exploratory (audit)"),
    "jk c2 ci": (f"{AUD}/A3_jackknife.txt", r"C2:.*?normal 95% \[" + _N + ", " + _N, (1, 2), "exploratory (audit)"),
    "seed sd f1": (f"{AUD}/FABLE_seedcheck.txt", r"F1 C1:.*?sd upper " + _N, 1, "exploratory (audit)"),
    "seed sd f2": (f"{AUD}/FABLE_seedcheck.txt", r"F2 C1:.*?sd upper " + _N, 1, "exploratory (audit)"),
    "pilot chart pf": (f"{AUD}/A1_pilot.txt", r"\n\s+Chart \d+ (\d+) \d+", 1, "exploratory (audit, pilot)"),
    "pilot chart flip": (f"{AUD}/A1_pilot.txt", r"\n\s+Chart \d+ \d+ (\d+)", 1, "exploratory (audit, pilot)"),
    "pilot math pf": (f"{AUD}/A1_pilot.txt", r"\n\s+Math \d+ (\d+) \d+", 1, "exploratory (audit, pilot)"),
    "pilot math flip": (f"{AUD}/A1_pilot.txt", r"\n\s+Math \d+ \d+ (\d+)", 1, "exploratory (audit, pilot)"),
    "frame bugs": (f"{AUD}/A1_pilot.txt", r"frame bugs: (\d+)", 1, "registered data (audit recount)"),
    "orig bugs": (f"{AUD}/A1_pilot.txt", r"original-study labelled bugs: (\d+)", 1, "registered data (audit recount)"),
    "bug overlap": (f"{AUD}/A1_pilot.txt", r"overlap with original labelled: (\d+)", 1, "registered data (audit recount)"),
    "plan lo": ("docs/research_extension/generated/confirm_report.md", r"the registration expected (\d+) to (\d+)", 1,
                "registration (planning range)"),
    "plan hi": ("docs/research_extension/generated/confirm_report.md", r"the registration expected (\d+) to (\d+)", 2,
                "registration (planning range)"),
    "t labels": (f"{AUD}/A6_A8.md", r"labels commit (\d\d:\d\d:\d\d)", 1, "sealing (A8)"),
    "t probe": (f"{AUD}/A6_A8.md", r"first probe start (\d\d:\d\d:\d\d)", 1, "sealing (A8)"),
    "t ledger": (f"{AUD}/A6_A8.md", r"ledger commit (\d\d:\d\d:\d\d)", 1, "sealing (A8)"),
    "t vote": (f"{AUD}/A6_A8.md", r"first vote start (\d\d:\d\d:\d\d)", 1, "sealing (A8)"),
    "t analysis": (f"{AUD}/A6_A8.md", r"analysis commit\s+(\d\d:\d\d:\d\d)", 1, "sealing (A8)"),
    "a6 records": (f"{AUD}/A6_A8.md", r"A6 (\d+) mismatches of (\d+) records", 2, "audit check A6"),
    "a6 mismatches": (f"{AUD}/A6_A8.md", r"A6 (\d+) mismatches of (\d+) records", 1, "audit check A6"),
    "a7 sources": (f"{AUD}/A6_A8.md", r"A7 (\d+) of (\d+) sources", 2, "audit check A7"),
    "a8 pass": (f"{AUD}/A6_A8.md", r"A8 (\d+) of (\d+) checks pass", 1, "audit check A8"),
    "labels recomputed": (f"{AUD}/FABLE_A2_labels_full.txt", r"(\d+) of (\d+)", 1, "audit check A2"),
}
for _ft in ("assertion", "focal", "main", "test"):
    _pat = {"assertion": r"ALL \('assertion_failure', 'test'\)", "focal": r"ALL \('exception', 'focal'\)",
            "main": r"ALL \('exception', 'main'\)", "test": r"ALL \('exception', 'test'\)"}[_ft]
    for _k, _g in (("pf", 1), ("pfdec", 2), ("tf", 3), ("tfdec", 4)):
        TXT[f"ft {_ft} {_k}"] = (f"{AUD}/A1_recompute.txt", _pat + r" PF n/dec (\d+)/(\d+)\s+TF n/dec (\d+)/(\d+)", _g,
                                 "exploratory (audit)")
for _k, _g in (("pf", 1), ("pfdec", 2), ("tf", 3), ("tfdec", 4)):     # assertion failures with no test frame
    TXT[f"ft assertnone {_k}"] = (f"{AUD}/A1_recompute.txt",
                                  r"ALL \('assertion_failure', 'none'\) PF n/dec (\d+)/(\d+)\s+TF n/dec (\d+)/(\d+)", _g,
                                  "exploratory (audit)")

_rows_cache = {}


def _rows():
    if "r" not in _rows_cache:
        _rows_cache["r"] = [r for r in json.loads((ROOT / AUD / "rows.json").read_text(encoding="utf-8"))
                            if r["tr"] in ("F1", "F2") and r["label"] in ("PF", "TF")]
    return _rows_cache["r"]


def _jk(r):
    return r["proj"].startswith("Jackson")


AROW = {   # name -> (predicate over a scored F1/F2 row, description)
    "jackson tf": (lambda r: _jk(r) and r["label"] == "TF", "TF tests in JacksonDatabind or JacksonCore"),
    "jackson pf": (lambda r: _jk(r) and r["label"] == "PF", "PF tests in JacksonDatabind or JacksonCore"),
    "jackson dec tf": (lambda r: _jk(r) and r["label"] == "TF" and r["dec"], "decoupled TF in the two Jackson projects"),
    "lang57 pf": (lambda r: r["bug"] == "Lang_57" and r["label"] == "PF", "PF tests of Lang_57"),
    "lang57 pf nomut": (lambda r: r["bug"] == "Lang_57" and r["label"] == "PF" and r["ncomp"] == 0,
                        "PF tests of Lang_57 with no compiled mutant"),
    "math59 dec pf": (lambda r: r["bug"] == "Math_59" and r["label"] == "PF" and r["dec"], "decoupled PF of Math_59"),
    "math59 ncomp": (None, "compiled mutants of the decoupled PF test of Math_59"),
    "f1 tf assert": (lambda r: r["tr"] == "F1" and r["label"] == "TF" and r["ft"] == "assertion_failure",
                     "F1 TF assertion failures"),
    "f1 tf": (lambda r: r["tr"] == "F1" and r["label"] == "TF", "F1 TF tests"),
    "f2 tf exc": (lambda r: r["tr"] == "F2" and r["label"] == "TF" and r["ft"] == "exception", "F2 TF exceptions"),
    "f2 tf": (lambda r: r["tr"] == "F2" and r["label"] == "TF", "F2 TF tests"),
    "few pf": (lambda r: r["label"] == "PF" and r["ncomp"] < 10, "PF tests with fewer than ten compiled mutants"),
    "few tf": (lambda r: r["label"] == "TF" and r["ncomp"] < 10, "TF tests with fewer than ten compiled mutants"),
    "few all": (lambda r: r["ncomp"] < 10, "tests with fewer than ten compiled mutants"),
}


def arow(name):
    if name == "math59 ncomp":
        return next(r["ncomp"] for r in _rows() if r["bug"] == "Math_59" and r["label"] == "PF" and r["dec"])
    return sum(1 for r in _rows() if AROW[name][0](r))


def txt(name):
    f, rx, g, _ = TXT[name]
    m = re.search(rx, (ROOT / f).read_text(encoding="utf-8-sig"), re.S)
    if not m:
        raise KeyError(f"pattern for {name!r} not found in {f}")
    conv = (lambda s: float(s) if re.fullmatch(r"[-+]?\d+\.\d+", s) else (int(s) if s.lstrip("+-").isdigit() else s))
    return [conv(m.group(i)) for i in g] if isinstance(g, tuple) else conv(m.group(g))


def R(k):
    return raw(k)


DV = {   # name -> (function, formula)
    "pilot half": (lambda: R("pil:flags:flip:diff_PF_minus_TF") / 2, "pilot C1 estimate / 2"),
    "pilot c2": (lambda: -R("pil:flags:decoupled:diff_PF_minus_TF"), "pilot decoupled rate TF minus PF"),
    "c1 halfwidth": (lambda: (R("cc:family:C1:ci95")[1] - R("cc:family:C1:ci95")[0]) / 2, "half-width of C1 interval"),
    "voteless": (lambda: R("cc:population:instances") - R("cc:rules:instances_with_three_votes"),
                 "scored tests minus tests with three votes"),
    "voteless pf": (lambda: R("cc:population:PF") - R("cc:rules:PF"), "PF minus PF with three votes"),
    "voteless tf": (lambda: (R("cc:population:instances") - R("cc:rules:instances_with_three_votes"))
                    - (R("cc:population:PF") - R("cc:rules:PF")), "voteless minus voteless PF"),
    "dec flagged": (lambda: R("cc:family:C2:TF_flagged") + R("cc:family:C2:PF_flagged"), "decoupled TF + PF"),
    "jackson dec share": (lambda: arow("jackson dec tf"), "same as arow jackson dec tf"),
    "nomut pf rate": (lambda: txt("nomut pf") / txt("nomut pfn"), "PF flipping / PF with a mutant"),
    "nomut tf rate": (lambda: txt("nomut tf") / txt("nomut tfn"), "TF flipping / TF with a mutant"),
    "nomut f1 pf rate": (lambda: txt("nomut f1 pf") / txt("nomut f1 pfn"), "F1 PF flipping / with a mutant"),
    "nomut f1 tf rate": (lambda: txt("nomut f1 tf") / txt("nomut f1 tfn"), "F1 TF flipping / with a mutant"),
    "f1 dec tf rate": (lambda: R("cf1:family:C2:TF_flagged") / R("cf1:family:C2:TF"), "F1 decoupled TF share"),
    "f2 dec tf rate": (lambda: R("cf2:family:C2:TF_flagged") / R("cf2:family:C2:TF"), "F2 decoupled TF share"),
    "lang57 share": (lambda: arow("lang57 pf") / R("cc:population:PF"), "Lang_57 PF / all PF"),
    "f1 tf assert share": (lambda: arow("f1 tf assert") / arow("f1 tf"), "F1 TF assertion failures / F1 TF"),
    "f2 tf exc share": (lambda: arow("f2 tf exc") / arow("f2 tf"), "F2 TF exceptions / F2 TF"),
    "cd added": (lambda: R("cc:family:C2:TF_flagged") - txt("dec unanimous"),
                 "decoupled TF minus those already unanimous TF (all 135 decoupled TF have three votes)"),
    "ft assert pf": (lambda: txt("ft assertion pf") + txt("ft assertnone pf"), "assertion failures, any frame"),
    "ft assert pfdec": (lambda: txt("ft assertion pfdec") + txt("ft assertnone pfdec"), "same, decoupled"),
    "ft assert tf": (lambda: txt("ft assertion tf") + txt("ft assertnone tf"), "same, TF"),
    "ft assert tfdec": (lambda: txt("ft assertion tfdec") + txt("ft assertnone tfdec"), "same, TF decoupled"),
    "kuu cd dtnr": (lambda: R("cc:rules:KUU+CD:TNR") - R("cc:rules:KUU:TNR"), "TNR(KUU+CD) - TNR(KUU)"),
    "lopo c1 min": (lambda: min(v["C1"] for v in R("cc:secondary:leave_one_project_out").values()),
                    "minimum C1 over the registered leave-one-project-out rows"),
    "lopo c1 max": (lambda: max(v["C1"] for v in R("cc:secondary:leave_one_project_out").values()),
                    "maximum C1 over the registered leave-one-project-out rows"),
    "lopo c2 min": (lambda: min(v["C2"] for v in R("cc:secondary:leave_one_project_out").values()),
                    "minimum C2 over the registered leave-one-project-out rows"),
    "lopo c2 max": (lambda: max(v["C2"] for v in R("cc:secondary:leave_one_project_out").values()),
                    "maximum C2 over the registered leave-one-project-out rows"),
    "lopo projects": (lambda: len(R("cc:secondary:leave_one_project_out")), "projects in the registered LOPO rows"),
    "flip rate pf": (lambda: R("cc:family:C1:PF_flagged") / R("cc:family:C1:PF"), "flipping PF / PF"),
    "flip rate tf": (lambda: R("cc:family:C1:TF_flagged") / R("cc:family:C1:TF"), "flipping TF / TF"),
    "pilot dec pf": (lambda: R("pil:flags:decoupled:PF_flagged"), "decoupled PF in the pilot"),
    "rcf rate pf": (lambda: R("cc:secondary:rcf_in_place_of_flip:PF_flagged") / R("cc:population:PF"), "rcf PF / PF"),
    "rcf rate tf": (lambda: R("cc:secondary:rcf_in_place_of_flip:TF_flagged") / R("cc:population:TF"), "rcf TF / TF"),
    "scored labelled pf tests share": (lambda: R("cc:population:bugs") / txt("frame bugs"), "bugs scored / frame bugs"),
}


DV.update({   # WDP (D-151): category labels read from the frozen analysis, not numbers
    "wdp math59 level": (lambda: "/".join(R("wdp:primary:criterion:math59_decoupled_pf_levels")),
                         "level of Math_59's decoupled bug-revealing test"),
    "wdp codec13 level": (lambda: "/".join(R("wdp:secondary:1_pilot:codec13_decoupled_pf_levels")),
                          "level of Codec_13's decoupled bug-revealing test (pilot)"),
})


def raw(key):
    kind, _, name = key.partition(":")
    if kind == "atx":
        return txt(name)
    if kind == "arow":
        return arow(name)
    if kind == "dv":
        return DV[name][0]()
    return bn.raw(key)


def resolve(key_fmt, target):
    key, _, f = key_fmt.partition("@")
    v = raw(key)
    if isinstance(v, list) and f in ("", None):
        f = "ci"
    if f == "id":                                   # an identifier (e.g. a seed): digits only, no grouping
        return str(int(v))
    return bn.fmt(v, key, f or None, target)


def source_of(key):
    kind, _, name = key.partition(":")
    if kind == "atx":
        f, rx, g, cat = TXT[name]
        return f, f"regex {rx} group {g}", cat
    if kind == "arow":
        return f"{AUD}/rows.json", f"count: {AROW[name][1]} (F1+F2, PF/TF rows)", "exploratory (audit)"
    if kind == "dv":
        return "(derived)", DV[name][1], "derived from resolved values"
    return bn.source_of(key)


def main():
    text = TEX.read_text(encoding="utf-8")
    used = {}
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("%"):
            continue
        for m in bn.TEX_KEY.finditer(line):
            used.setdefault(m.group(1), []).append(f"paper/{TEX.name}:{i}")
    errors, rows, defs = [], [], []
    for kf in sorted(used):
        try:
            val_tex, val_md = resolve(kf, "tex"), resolve(kf, "md")
        except (KeyError, TypeError, ValueError, IndexError, StopIteration) as e:
            errors.append(f"{kf}: {type(e).__name__} {e}")
            continue
        key = kf.partition("@")[0]
        src, field, cat = source_of(key)
        rows.append({"key": kf, "value": val_md, "source_file": src, "field": field, "category": cat,
                     "used_in": " ".join(used[kf])})
        defs.append(f"\\expandafter\\def\\csname V@{kf}\\endcsname{{{val_tex}}}")
    if errors:
        print("UNRESOLVED KEYS:\n  " + "\n  ".join(errors))
        sys.exit(1)
    OUT_TEX.write_text("% generated by scripts/paper/build_numbers_v2.py -- do not edit; every value is in "
                       "docs/paper/NUMBERS_MAP_v2.csv\n\\makeatletter\n" + "\n".join(defs) + "\n\\makeatother\n",
                       encoding="utf-8", newline="\n")
    with open(OUT_MAP, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    cats = {}
    for r in rows:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    print(f"{len(rows)} values resolved -> {OUT_TEX.relative_to(ROOT)}, {OUT_MAP.relative_to(ROOT)}; by category {cats}")


if __name__ == "__main__":
    main()
