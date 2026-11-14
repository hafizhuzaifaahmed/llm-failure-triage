"""Research methodology architecture (draw.io), built from one specification and exported by draw.io itself.

Run from the repository root:
    python phase4_v2/methodology_architecture/build_methodology_architecture.py

Writes, in this folder:
    research_methodology_architecture.drawio   editable diagrams.net source (native mxGraph XML, html labels)
    research_methodology_architecture.svg      exported by diagrams.net's own renderer (Graph.getSvg)
    research_methodology_architecture.pdf      that SVG printed to PDF by headless Chrome (vector, one page)
    research_methodology_architecture.png      that SVG rasterised at 2x by headless Chrome

draw.io Desktop is not installed on the build machine, so the exports are produced by loading the official
diagrams.net viewer engine (https://viewer.diagrams.net/js/viewer-static.min.js) in headless Chrome and calling its
getSvg() on the .drawio file. Only the viewer script is fetched; the diagram never leaves the machine.

Every number shown is read from phase4_v2/generated/numbers_v2.tex, the file the paper prints from.
Visual language: white background, black text, Arial, sharp rectangles, thin black orthogonal connectors; line style
and grey fill carry methodological meaning (see the legend). No colour, gradients, shadows or icons.
"""
import html
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
NAME = "research_methodology_architecture"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W, H = 2300, 1700

# ------------------------------------------------------------------ numbers (single source shared with the paper)
_NUM = {}
for m in re.finditer(r"\\csname V@(.+?)\\endcsname\{(.*)\}\s*$",
                     open(os.path.join(ROOT, "phase4_v2", "generated", "numbers_v2.tex"), encoding="utf-8").read(), re.M):
    _NUM[m.group(1)] = m.group(2)


def V(key):
    v = _NUM[key]
    v = v.replace(r"\textminus{}", "\u2212").replace(r"\%", "%").replace(r"\,", "\u2009").replace("{}", "")
    if "\\" in v:
        raise ValueError(key + ": " + v)
    return v


# ------------------------------------------------------------------ styles
BASE = "html=1;whiteSpace=wrap;fontFamily=Arial;fontColor=#000000;rounded=0;shadow=0;glass=0;"
LEFT = "align=left;verticalAlign=middle;spacingLeft=6;spacingRight=4;fontSize=11;"
S = {
    "title": BASE + "text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=16;fontStyle=1;",
    "section": BASE + "fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1;align=left;verticalAlign=top;spacingLeft=8;"
               "spacingTop=4;fontSize=13;fontStyle=1;",
    "sealed": BASE + "fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2.5;align=left;verticalAlign=top;spacingLeft=8;"
              "spacingTop=4;fontSize=13;fontStyle=1;",
    "proc": BASE + "fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1;" + LEFT,
    "proctop": BASE + "fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1;align=left;verticalAlign=top;spacingLeft=6;"
               "spacingTop=2;spacingRight=4;fontSize=11;",
    "procc": BASE + "fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1;align=center;verticalAlign=middle;fontSize=11;",
    "llm": BASE + "fillColor=#D9D9D9;strokeColor=#000000;strokeWidth=1;" + LEFT,
    "llmc": BASE + "fillColor=#D9D9D9;strokeColor=#000000;strokeWidth=1;align=center;verticalAlign=middle;fontSize=11;",
    "data": BASE + "shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=9;fillColor=#FFFFFF;strokeColor=#000000;"
            "strokeWidth=1;align=center;verticalAlign=middle;fontSize=11;",
    "gtbox": BASE + "fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2.5;" + LEFT,
    "factor": BASE + "fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1;dashed=1;dashPattern=6 3;" + LEFT,
    "control": BASE + "fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1;dashed=1;dashPattern=1 2;" + LEFT,
    "withheld": BASE + "fillColor=#F0F0F0;strokeColor=#000000;strokeWidth=1;" + LEFT,
    "confirm": BASE + "fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.75;" + LEFT,
    "explore": BASE + "fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1;dashed=1;dashPattern=8 3 2 3;" + LEFT,
    "group": BASE + "fillColor=none;strokeColor=#000000;strokeWidth=1;align=center;verticalAlign=top;spacingTop=3;"
             "fontSize=11;fontStyle=1;",
    "groupx": BASE + "fillColor=none;strokeColor=#000000;strokeWidth=1.75;align=center;verticalAlign=top;spacingTop=3;"
              "fontSize=11;fontStyle=1;",
    "note": BASE + "text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=10;fontStyle=2;",
    "notec": BASE + "text;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=10;fontStyle=2;",
    "leg": BASE + "text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;",
    "legh": BASE + "text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=11;fontStyle=1;",
}
EDGE = ("rounded=0;html=1;fontFamily=Arial;fontSize=10;fontColor=#000000;strokeColor=#000000;endArrow=block;"
        "endFill=1;endSize=6;labelBackgroundColor=#FFFFFF;")
E_STYLE = {
    "flow": EDGE + "edgeStyle=orthogonalEdgeStyle;strokeWidth=1;",
    "straight": EDGE + "edgeStyle=none;strokeWidth=1;",
    "gt": EDGE + "edgeStyle=orthogonalEdgeStyle;strokeWidth=2;dashed=1;dashPattern=8 4;",
    "ids": EDGE + "edgeStyle=orthogonalEdgeStyle;strokeWidth=1;dashed=1;dashPattern=1 2;",
}

CELLS = []
_ids = set()


def esc(t):
    return html.escape(t, quote=True)


def box(cid, x, y, w, h, style, label=""):
    assert cid not in _ids, cid
    _ids.add(cid)
    CELLS.append(f'<mxCell id="{cid}" value="{esc(label)}" style="{S[style]}" vertex="1" parent="1">'
                 f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')


def edge(cid, src, tgt, kind="flow", label="", exit=None, entry=None, points=None):
    assert cid not in _ids, cid
    _ids.add(cid)
    st = E_STYLE[kind]
    if exit:
        st += f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
    if entry:
        st += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
    pts = ""
    if points:
        pts = '<Array as="points">' + "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in points) + "</Array>"
    CELLS.append(f'<mxCell id="{cid}" value="{esc(label)}" style="{st}" edge="1" parent="1" source="{src}" '
                 f'target="{tgt}"><mxGeometry relative="1" as="geometry">{pts}</mxGeometry></mxCell>')


def free_edge(cid, x1, y1, x2, y2, kind):
    """A connector without endpoint shapes (used for the legend)."""
    _ids.add(cid)
    st = E_STYLE[kind].replace("edgeStyle=orthogonalEdgeStyle;", "")
    CELLS.append(f'<mxCell id="{cid}" value="" style="{st}" edge="1" parent="1"><mxGeometry relative="1" '
                 f'as="geometry"><mxPoint x="{x1}" y="{y1}" as="sourcePoint"/><mxPoint x="{x2}" y="{y2}" '
                 f'as="targetPoint"/></mxGeometry></mxCell>')


def B(t):
    return "<b>" + t + "</b>"


BR = "<br>"

# ================================================================== title
box("title", 20, 12, 1700, 30, "title",
    "Research methodology architecture: LLM triage of failing generated unit tests (program fault vs test fault)")

# ================================================================== A  datasets and partitioning   x 20-320
box("secA", 20, 55, 300, 590, "section", "A  Datasets and project-level partitioning")
box("d1", 32, 92, 276, 112, "data",
    B("D1 \u00b7 Defects4J 3.0.1") + " (real faults)" + BR + "17 projects; frame " + V("split:frame_methods")
    + " methods / " + V("split:frame_bugs") + " defects" + BR + "cap 25 per project \u2192 " + V("split:sampled_methods")
    + " methods / " + V("split:sampled_bugs") + " defects")
box("split", 32, 226, 276, 46, "procc", B("Project-level split") + BR + "seeded draw, made before any test generation")
box("dev", 176, 296, 132, 128, "proc",
    B("Development") + BR + "3 projects" + BR + "(Cli, Gson, Jsoup)" + BR + V("der:dev methods") + " methods" + BR
    + "prompt rounds, pilot, gates, k<sub>T</sub>")
box("test", 32, 296, 132, 128, "proc",
    B("Held-out test") + BR + V("der:n test projects") + " projects" + BR + V("der:test methods") + " methods" + BR
    + "every reported D1 result")
box("d2", 32, 448, 276, 120, "data",
    B("D2 \u00b7 Seeded faults") + " (contamination control)" + BR + "F = fixed version; B = F + one killed Major" + BR
    + "mutant inside a held-out focal method" + BR + "(\u2264 2 per method) \u00b7 "
    + V("d2rep:before_cap:d2_units_total") + " mutants")
box("noteA", 32, 580, 276, 54, "note", "Development projects serve prompt development, the pilot and the "
    "development gates only; they never enter held-out evaluation.")
edge("eA1", "d1", "split")
edge("eA2", "split", "dev", exit=(0.76, 1), entry=(0.5, 0))
edge("eA3", "split", "test", exit=(0.24, 1), entry=(0.5, 0))
edge("eA4", "test", "d2", exit=(0.3, 1), entry=(0.1435, 0))

# ================================================================== C  generation and dual execution   x 340-670
box("secC", 340, 55, 330, 590, "section", "C  Test generation and dual execution")
box("env", 352, 92, 306, 88, "control",
    B("Execution environment (controlled)") + BR + "WSL2 Ubuntu 22.04.5 \u00b7 OpenJDK 11.0.32" + BR
    + "Defects4J v3.0.1 \u00b7 recorded environment manifest" + BR + "TZ America/Los_Angeles \u00b7 locale en_US")
box("checkout", 352, 198, 306, 50, "proc", B("Checkout") + " buggy (B) and fixed (F) version of every focal method")
box("gen", 352, 266, 306, 76, "llm",
    B("Test generation") + " \u00b7 generator G" + BR + "Gemma 4 26B-A4B (local, Q4_K_M)" + BR
    + "3 generations per focal method from the buggy context, T = 0.7")
box("compile", 352, 360, 306, 50, "proc", B("Compile") + " each test class against B and F; prune non-compiling "
    "methods (\u2264 3 passes)")
box("exec", 352, 428, 306, 62, "proc", B("Dual execution") + BR + "each test method 3\u00d7 on B and 3\u00d7 on F; "
    "fresh JVM per run; 30 s timeout")
box("frec", 352, 508, 306, 56, "proc", B("Failure record") + ": outcome, exception, message, failing test line, "
    "stack trace (every run)")
edge("eC0a", "dev", "checkout", exit=(1, 0.3), entry=(0, 0.5), points=[(330, 334), (330, 223)])
edge("eC0b", "test", "checkout", exit=(0.75, 1), entry=(0, 0.5), points=[(131, 436), (330, 436), (330, 223)])
edge("eC0c", "d2", "checkout", exit=(1, 0.5), entry=(0, 0.5), points=[(330, 508), (330, 223)])
edge("eC1", "checkout", "gen")
edge("eC2", "gen", "compile")
edge("eC3", "compile", "exec")
edge("eC4", "exec", "frec")

# ================================================================== D  preprocessing   x 690-1010
box("secD", 690, 55, 320, 590, "section", "D  Preprocessing and evidence construction")
steps = [
    ("p1", 48, "1  Parse generated test classes; drop unparsable classes"),
    ("p2", 48, "2  De-duplicate test bodies (normalised-body hash within each focal method)"),
    ("p3", 48, "3  Exclude FLAKY, TIMEOUT, ENV and NC outcomes (ENV re-run once)"),
    ("p4", 62, "4  Stack traces: keep project and test frames (\u2264 25), collapse framework frames; scrub paths, "
               "object hashes, timestamps"),
    ("p5", 62, "5  Length limits: message \u2264 500 chars; Javadoc \u2264 600, specification \u2264 400, package "
               "\u2264 6,000 tokens"),
    ("p6", 62, "6  Leakage guard: block any call whose package contains bug ids, fixed-only lines, focal-body lines "
               "or paths"),
    ("p7", 62, B("7  Context builder") + " (deterministic, no LLM): evidence package whose items carry citable ids"),
]
y = 92
for sid, h, lab in steps:
    box(sid, 702, y, 296, h, "proc", lab)
    y += h + 16
for a, b in zip([s[0] for s in steps][:-1], [s[0] for s in steps][1:]):
    edge("e" + a + b, a, b)
edge("eCD", "frec", "p1", exit=(1, 0.5), entry=(0, 0.5), points=[(680, 536), (680, 116)])

# ================================================================== E  evidence and specification   x 1030-1360
box("secE", 1030, 55, 330, 590, "section", "E  Evidence package and specification availability")
box("s2", 1042, 92, 306, 300, "proctop",
    B("S2") + " = S1 + [Spec] inferred specification" + BR + "once per focal method, T = 0, from signature, Javadoc, "
    "call sites and sibling documentation; fix-changed lines removed")
box("s1", 1054, 168, 282, 214, "proctop", B("S1") + " = S0 + [Doc] Javadoc of the buggy version")
box("s0", 1066, 196, 258, 176, "proc",
    B("S0") + BR + "[T] test code and fixtures" + BR + "[F1] outcome, exception class" + BR
    + "[F2] message with expected / actual values" + BR + "[F3] failing test line" + BR
    + "[F4\u2026] normalised stack frames" + BR + "[Sig] signature, class and type interfaces")
box("e2tag", 1042, 404, 306, 46, "factor", B("Manipulated factor (E2)") + ": S0 / S1 / S2; only the "
    "specification section changes")
box("e4tag", 1042, 460, 306, 62, "factor", B("Ablated inputs (E4)") + ": A4 removes [F]; A5a adds the buggy "
    "focal body; A5b body-derived specification")
box("hidden", 1042, 534, 306, 98, "withheld",
    B("Withheld from every triage method") + BR + "focal method body \u00b7 fixed version \u00b7 patch" + BR
    + "developer tests \u00b7 bug identifiers" + BR + "PF / TF labels")
edge("eDE", "p7", "s2", exit=(1, 0.5), entry=(0, 0.75), points=[(1020, 549), (1020, 317)])

# ================================================================== F  triage methods   x 1380-1940
box("secF", 1380, 55, 560, 590, "section", "F  Triage methods")
box("grpB", 1390, 84, 136, 276, "group", "Non-LLM baselines")
box("da", 1398, 110, 120, 58, "proc", B("DA") + " discard-all" + BR + "TF for every failure; 0 calls")
box("ka", 1398, 176, 120, 58, "proc", B("KA") + " keep-all" + BR + "PF for every failure; 0 calls")
box("r0", 1398, 242, 120, 110, "proc", B("R0") + " rule" + BR + "PF iff not an assertion failure and the deepest "
    "project frame is in main code; 0 calls")
box("grpS", 1534, 84, 148, 276, "group", "Single-agent LLM")
box("j1", 1542, 110, 132, 58, "llm", B("J1") + " one-shot judge" + BR + "1 call")
box("sc", 1542, 176, 132, 58, "llm", B("SC") + " self-consistency" + BR + "5 samples, majority; tie \u2192 TF")
box("sct", 1542, 242, 132, 110, "llm", B("SC-T") + " token-matched" + BR + "k<sub>T</sub> = "
    + V("frozen:decoding:k_T") + " samples: smallest odd k reaching DEB's consumed tokens on development data")
box("deb", 1690, 84, 240, 300, "groupx", "DEB \u00b7 proposed adversarial debate \u00b7 5 calls")
box("r1lab", 1698, 106, 224, 18, "notec", "Round 1: independent arguments")
box("advp", 1698, 126, 100, 54, "llmc", B("Advocate-P") + BR + "program-fault case")
box("advt", 1822, 126, 100, 54, "llmc", B("Advocate-T") + BR + "test-fault case")
box("rebp", 1698, 212, 100, 62, "llmc", B("Rebuttal-P") + BR + "round 2: answers Advocate-T")
box("rebt", 1822, 212, 100, 62, "llmc", B("Rebuttal-T") + BR + "round 2: answers Advocate-P")
box("adj", 1698, 294, 224, 80, "llmc", B("Adjudicator") + BR + "reads all four arguments, anonymised "
    "(Analyst X / Y), in seeded random order; decides from cited evidence ids")
edge("ed1", "advp", "rebp")
edge("ed2", "advt", "rebt")
edge("ed3", "advp", "rebt", kind="straight", exit=(1, 1), entry=(0, 0))
edge("ed4", "advt", "rebp", kind="straight", exit=(0, 1), entry=(1, 0))
edge("ed5", "rebp", "adj", entry=(0.25, 0))
edge("ed6", "rebt", "adj", entry=(0.75, 0))
box("ctrl", 1390, 404, 540, 118, "control",
    B("Controlled across all LLM arms") + BR + "same judge M1: Qwen3.5 9B (local, Ollama " + V("frozen:runtime:version")
    + ") \u00b7 temperature " + V("frozen:frozen_models:M1:temperature:judges@1") + ", top-p "
    + V("frozen:frozen_models:M1:top_p@1") + BR + "context 8,192 tokens \u00b7 \u2264 "
    + V("frozen:frozen_models:M1:num_predict:judge_roles") + " output tokens per call \u00b7 per-call seed \u00b7 "
    "thinking disabled" + BR + "prompts frozen after 5 development rounds, before any held-out call \u00b7 "
    + V("frozen:decoding:replicates") + " replicates (E1\u2013E3)")
box("budget", 1390, 534, 540, 100, "factor",
    B("Equal allocated budget (E3)") + BR + "SC and DEB: 5 calls \u00d7 \u2264 512 output tokens each" + BR
    + "J1: 1 call (low-budget reference) \u00b7 SC-T: matches DEB's consumed tokens" + BR + "baselines: 0 calls")
edge("eEF1", "s2", "grpB", exit=(1, 0.75), entry=(0, 0.8),
     points=[(1370, 317), (1370, 305)])
edge("eEF2", "s2", "grpS", exit=(1, 0.06), entry=(0.5, 0),
     points=[(1368, 110), (1368, 47), (1608, 47)])
edge("eEF3", "s2", "deb", exit=(1, 0.06), entry=(0.5, 0), points=[(1368, 110), (1368, 47), (1810, 47)])
box("evnote", 1612, 29, 420, 16, "note", "same evidence package (level under test) to every LLM arm")

# ================================================================== G  prediction interface   x 1960-2280
box("secG", 1960, 55, 320, 590, "section", "G  Common prediction interface")
box("out", 1972, 92, 296, 254, "proc",
    B("Output record") + " (fixed JSON schema, every arm)" + BR + "label: PROGRAM_FAULT | TEST_FAULT" + BR
    + "reason_category" + BR + "evidence_ids (cited package items)" + BR + "summary" + BR
    + "confidence 0\u2013100 (descriptive only)" + BR + "SC: PF vote share" + BR
    + "DEB: round positions, concessions, position bias" + BR + "cost log: calls, tokens, latency")
box("parse", 1972, 362, 296, 78, "proc", "One deterministic repair parse; an output still invalid is scored TF "
    "(sensitivity analysis: excluded). Baselines emit the label field only.")
edge("eFG1", "deb", "out", exit=(1, 0.5), entry=(0, 0.55), points=[(1950, 234), (1950, 232)])
edge("eFG2", "grpB", "out", exit=(0.5, 1), entry=(0, 0.88), points=[(1458, 392), (1950, 392), (1950, 316)])
edge("eFG3", "grpS", "out", exit=(0.5, 1), entry=(0, 0.88), points=[(1608, 392), (1950, 392), (1950, 316)])
edge("eFG4", "out", "parse")

# ================================================================== B  sealed ground truth   x 340-1010, y 665-925
box("secB", 340, 665, 670, 262, "sealed",
    "B  Sealed ground-truth channel: derived from execution only; no triage method can read it")
box("sig", 352, 700, 196, 120, "gtbox", B("Failure signature") + BR + "\u03c3(t, V) = (outcome type, exception "
    "class, failing test line); deterministic over 3 runs")
box("rule", 560, 700, 214, 120, "gtbox",
    B("PF") + ": fails on B, passes on F" + BR + B("TF") + ": fails on B and F, \u03c3<sub>B</sub> = \u03c3<sub>F</sub>"
    + BR + B("AMB") + ": both fail, \u03c3<sub>B</sub> \u2260 \u03c3<sub>F</sub> (sensitivity only)" + BR
    + B("Excluded") + ": FLAKY, TIMEOUT, ENV, NC" + BR + "passes on B: not a triage instance")
box("samp", 786, 700, 212, 120, "gtbox",
    B("Evaluation sample") + BR + "all PF; 2 TF per PF over the split, project-stratified (IPW weights)" + BR + "D1-test: "
    + V("sum:prevalence:judged_sample_prevalence_by_dataset:D1:PF") + " PF / "
    + V("sum:prevalence:judged_sample_prevalence_by_dataset:D1:TF") + " TF / "
    + V("sum:prevalence:judged_sample_prevalence_by_dataset:D1:AMB") + " AMB \u2192 "
    + V("sum:leakage_abort_exclusions:n_per_level:S1") + " scored at S1" + BR + "D2: "
    + V("d2rep:judged_sample:cap") + " judged, " + V("d2:DEB|S1:n_instances") + " scored")
box("store", 352, 838, 646, 74, "gtbox",
    B("Sealed label store") + ": written before any judge runs; not readable by any judging module; joined to "
    "predictions only at evaluation")
edge("eB0", "frec", "sig", label="outcomes of every run on B and F", exit=(0.5, 1), entry=(0, 0.5),
     points=[(505, 655), (333, 655), (333, 760)])
edge("eB1", "sig", "rule")
edge("eB2", "rule", "samp")
edge("eB3", "rule", "store", exit=(0.5, 1), entry=(0.5, 0))
edge("eB4", "samp", "p7", kind="ids", label="instance ids only", exit=(1, 0.5), entry=(0.5, 1),
     points=[(1020, 760), (1020, 655), (850, 655)])

# ================================================================== H  evaluation   x 1380-2280, y 665-925
box("secH", 1380, 665, 900, 262, "section", "H  Evaluation against the sealed labels")
box("score", 1392, 700, 190, 212, "proc",
    B("Scoring") + BR + "unit: one failing test" + BR + "metrics per replicate, averaged over replicates" + BR
    + "resampling unit: bug" + BR + "AMB and leakage-aborted instances excluded")
box("metrics", 1594, 700, 330, 212, "proc",
    B("Metrics") + BR + "precision, recall, F1 of the PF class \u00b7 FPR, FNR \u00b7 MCC" + BR
    + "TPR, TNR, balanced accuracy \u00b7 confusion matrix" + BR + "PF tests lost \u00b7 bug-level retention" + BR
    + "precision at the natural prevalence (IPW)" + BR + "PR-AUC of the SC vote share \u00b7 invalid-output rate"
    + BR + "calls, tokens, latency \u00b7 \u0394F1 per 1,000 tokens vs J1" + BR + "FP / FN error analysis")
box("stats", 1936, 700, 332, 212, "proc",
    B("Statistics") + BR + "bug-level cluster bootstrap, " + V("cc:resamples") + " resamples, paired" + BR
    + "Holm over H1\u2013H3b (F1); recall, precision: secondary family" + BR
    + "equivalence: 90% CI within \u00b10.05 F1" + BR
    + "sensitivity: McNemar exact, per-project Wilcoxon, leave-one-project-out" + BR
    + "E2 only: logistic mixed model (exploratory)")
edge("eGH", "parse", "score", label="predictions", exit=(0.5, 1), entry=(0, 0.2), points=[(2120, 655), (1370, 655), (1370, 742)])
edge("eBH", "store", "score", kind="gt", label="sealed labels (evaluation only)", exit=(1, 0.5), entry=(0, 0.82))
edge("eH1", "score", "metrics")
edge("eH2", "metrics", "stats")

# ================================================================== I  experimental design   x 20-760, y 945-1560
box("secI", 20, 945, 740, 615, "section", "I  Experimental design")
box("e1", 32, 982, 716, 62, "confirm",
    B("E1 \u00b7 Baselines and arms") + ": DA, KA, R0, J1, SC, SC-T, DEB at S1 \u00b7 D1-test \u00b7 judge M1 \u00b7 3 "
    "replicates \u2192 " + B("H1") + " J1 vs R0")
box("e2", 32, 1054, 716, 62, "confirm",
    B("E2 \u00b7 Specification availability") + ": S0 / S1 / S2 \u00d7 J1, SC, DEB \u00b7 D1-test \u00b7 3 replicates "
    "\u2192 " + B("H2a") + " S1 vs S0 (methods with Javadoc), " + B("H2b") + " S2 vs S1")
box("e3", 32, 1126, 716, 62, "confirm",
    B("E3 \u00b7 Equal-budget architectures") + ": J1, SC, SC-T, DEB at S1 with cost and latency \u2192 "
    + B("H3a") + " DEB vs SC, " + B("H3b") + " SC vs J1")
box("e4", 32, 1198, 716, 152, "explore",
    B("E4 \u00b7 Ablations") + " (one replicate; each against its parent arm on identical instances)" + BR
    + "A1  DEB without argument exchange in round 2" + BR + "A2  DEB with neutral instead of adversarial debaters"
    + BR + "A3  SC decision threshold v \u2265 2/5 and v \u2265 4/5 (re-analysis, no calls)" + BR
    + "A4  failure evidence [F] removed (J1, SC, DEB)" + BR
    + "A5a buggy focal body shown (J1, DEB) \u00b7 A5b body-derived specification (J1 at S2)")
box("e5", 32, 1360, 716, 130, "explore",
    B("E5 \u00b7 Robustness") + " (one replicate)" + BR + "D2 seeded faults: all arms and specification levels, judge M1"
    + BR + "second judge M2, Gemma 4 12B: J1, SC, DEB at S1 on D1-test and D2" + BR
    + "per-project F1, Wilcoxon over projects, leave-one-project-out" + BR
    + "further judges: Qwen3.5 35B, Ministral 3 14B (M3), three-family vote; frontier reference Claude Sonnet 5.5")
box("noteI", 32, 1500, 716, 46, "note",
    "Confirmatory family: H1, H2a, H2b, H3a, H3b (Holm). Configuration, prompts and decoding frozen in one file before "
    "any held-out call. E2, E3 and E4 vary only the components tagged in sections E and F.")

# ================================================================== J  supplementary analyses   x 780-1520
box("secJ", 780, 945, 740, 615, "section", "J  Supplementary analyses, grouped by evidential status")
box("kuu", 792, 982, 716, 132, "proc",
    B("Judge-only rules (RQ4)") + " \u00b7 hypotheses fixed in advance in the decision log, tested on D2; post hoc on D1"
    + BR + "KUU (baseline): one J1 vote from each of three families, M1 Qwen3.5 9B, M2 Gemma 4 12B, M3 Ministral 3 "
    "14B; discard only on unanimous TF; an invalid vote keeps the test" + BR
    + "cascade: disagreements escalated to a frontier judge's DEB \u00b7 KUU-NG: Llama 3.1 8B replaces M2")
box("pilot", 792, 1126, 716, 112, "explore",
    B("Mutation probes, pilot") + " \u00b7 exploratory (D1-test, labels known)" + BR
    + "up to " + V("cfz:parameters:max_mutants_per_focal") + " first-order mutants of the method under test and its "
    "same-class callees (ROR, AOR, COR, LVR, NEG, STD); each run FLIP, SHIFT, SAME or ERR" + BR
    + "flip: some mutant makes the test pass \u00b7 decoupled: \u2265 "
    + V("cfz:parameters:min_compiled_mutants_for_decoupling") + " mutants compiled, none changes the failure")
box("conf", 792, 1250, 716, 160, "confirm",
    B("Registered confirmation, OSF " + V("osf:osf_id")) + " \u00b7 confirmatory, registered before its data existed"
    + BR + "fresh failing tests from bugs never used before: frames F1, F2 and control group CTRL" + BR
    + "C1  flip rate, PF \u2212 TF \u00b7 C2  decoupled rate, TF \u2212 PF" + BR
    + "C3  balanced accuracy, KUU + decoupled-discard \u2212 KUU" + BR
    + "C4  PF tests lost, 2-of-3 vote + keep certificate \u2212 2-of-3 vote" + BR
    + "one Holm family, \u03b1 = 0.05 \u00b7 bug-level bootstrap \u00b7 exact bound on bug loss")
box("wdp", 792, 1422, 716, 86, "explore",
    B("Whole-method dependence probes") + " \u00b7 exploratory, retrospective, not externally preregistered" + BR
    + "method body replaced by entry-recording throwing and fixed-return bodies; level U = no entry observed and "
    "throw-invariant; rule KUU + CD-U")
box("noteJ", 792, 1516, 716, 34, "note", "Probes execute the buggy version only; they use no LLM, no labels and no "
    "fixed version.")

# ================================================================== K  research questions and findings   x 1540-2280
box("secK", 1540, 945, 740, 615, "section", "K  Research questions, hypotheses and findings")
rq = [
    ("rq1", 62, B("RQ1 \u00b7 Accuracy and tests lost") + " (H1): inconclusive after Holm; best arm DEB F1 "
     + V("d1:DEB|S1:f1") + " vs keep-all " + V("d1:KA:f1") + ", MCC " + V("d1:DEB|S1:mcc") + "; DEB discards "
     + V("d1:DEB|S1:pf_lost@0") + " of " + V("sum:prevalence:PF") + " bug-revealing tests"),
    ("rq2", 46, B("RQ2 \u00b7 Specification effect") + " (H2a, H2b): no detectable gain from Javadoc or an "
     "inferred specification; both inconclusive"),
    ("rq3", 46, B("RQ3 \u00b7 Architecture effect") + " (H3a, H3b): DEB \u2212 SC " + V("conf:f1:H3a:delta")
     + " F1, Holm p " + V("conf:f1:H3a:p_holm") + "; SC \u2212 J1 " + V("conf:f1:H3b:delta") + "; inconclusive"),
    ("rq4", 46, B("RQ4 \u00b7 Judge-only rules") + ": one trade-off curve; KUU lost "
     + V("kuu2:summary:KUU|S1:pf_lost@0") + " of " + V("kuu2:pf_prevalence:PF") + " bug-revealing tests on D2 vs DEB's "
     + V("kuu2:summary:DEB|S1:pf_lost@0") + "; MCC below DEB"),
    ("rq5", 62, B("RQ5 \u00b7 Mutation outcomes") + " (C1, C2): C1 not supported ("
     + V("cc:family:C1:difference@signed") + " " + V("cc:family:C1:ci95") + "); C2 supported ("
     + V("cc:family:C2:difference@signed") + " " + V("cc:family:C2:ci95") + ", Holm p " + V("cc:family:C2:p_holm@4")
     + "), in one frame and mostly two projects"),
    ("rq6", 46, B("RQ6 \u00b7 Certificate rules") + " (C3, C4): both inconclusive; KUU + decoupled-discard lost "
     "one bug"),
    ("rqx", 46, B("Exploratory") + ": whole-method check raised TNR by " + V("wdp:primary:paired:TNR:difference@signed")
     + " " + V("wdp:primary:paired:TNR:ci95") + " over KUU, no bug lost; retrospective, concentrated"),
    ("eff", 46, B("Efficiency") + ": DEB " + V("d1:DEB|S1:consumed_tokens_per_instance@0") + " vs SC "
     + V("d1:SC|S1:consumed_tokens_per_instance@0") + " tokens per failure; " + V("d1:DEB|S1:latency_s_per_instance@1")
     + " s vs " + V("d1:SC|S1:latency_s_per_instance@1") + " s latency (sequential calls)"),
    ("lim", 62, B("Limitations") + ": one benchmark, language and generator; small local judges below their "
     "development gate; " + V("pil:scored:bugs_with_PF") + " and " + V("cc:population:bugs_with_PF")
     + " bugs with a bug-revealing test (D1-test, confirmation)"),
]
y = 982
for rid, h, lab in rq:
    box(rid, 1552, y, 716, h, "proc", lab)
    y += h + 10
edge("eHK", "stats", "rq1", label="results", exit=(0.5, 1), entry=(0.5, 0), points=[(2102, 936), (1910, 936)])
edge("eJK", "secJ", "secK", exit=(1, 0.5), entry=(0, 0.5))

# ================================================================== legend
LY = 1578
box("legend", 20, LY, 2260, 100, "section", "")
box("lgt", 32, LY + 6, 80, 20, "legh", "Legend")
items = [
    ("proc", "deterministic step, non-LLM component"), ("llm", "LLM call"), ("data", "dataset"),
    ("gtbox", "sealed ground truth"), ("factor", "manipulated factor"), ("control", "controlled setting"),
    ("withheld", "information withheld from triage"), ("confirm", "confirmatory analysis"),
    ("explore", "exploratory analysis"),
]
x = 32
for i, (st, lab) in enumerate(items):
    box(f"lg{i}", x, LY + 32, 34, 22, st)
    w = int(6.3 * len(lab)) + 10
    box(f"lgl{i}", x + 40, LY + 32, w, 22, "leg", lab)
    x += 40 + w + 22
for j, (kind, lab) in enumerate([("flow", "data and evidence flow"), ("gt", "sealed labels, used only at evaluation"),
                                 ("ids", "instance ids only (no labels)")]):
    sx = 32 + j * 360
    free_edge(f"le{j}", sx, LY + 78, sx + 56, LY + 78, kind)
    box(f"lt{j}", sx + 64, LY + 67, 280, 22, "leg", lab)


def drawio_xml():
    return ('<mxfile host="diagrams.net" type="device"><diagram id="methodology" name="Methodology architecture">'
            f'<mxGraphModel dx="{W}" dy="{H}" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
            f'fold="1" page="1" pageScale="1" pageWidth="{W}" pageHeight="{H}" math="0" shadow="0" background="#FFFFFF">'
            '<root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(CELLS) +
            "</root></mxGraphModel></diagram></mxfile>\n")


RENDER = """<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;background:#fff}</style></head><body>
<div id="host"></div><textarea id="out"></textarea>
<script id="src" type="application/json">%s</script>
<script src="https://viewer.diagrams.net/js/viewer-static.min.js"></script>
<script>
window.addEventListener('load', function () {
  try {
    var xml = JSON.parse(document.getElementById('src').textContent);
    var host = document.getElementById('host');
    host.setAttribute('data-mxgraph', JSON.stringify({xml: xml, toolbar: '', nav: false, resize: false, border: 0}));
    GraphViewer.createViewerForElement(host, function (viewer) {
      var svg = viewer.graph.getSvg('#ffffff', 1, 16, true, null, true, true, null, null, false);
      document.getElementById('out').textContent = mxUtils.getXml(svg);
    });
  } catch (e) { document.getElementById('out').textContent = 'ERROR ' + e; }
});
</script></body></html>
"""

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
@page { size: %dpx %dpx; margin: 0 } html, body { margin: 0; padding: 0; background: #fff }
img { display: block; width: %dpx; height: %dpx }
</style></head><body><img src="%s"></body></html>
"""


def chrome(args):
    prof = os.path.join(os.environ.get("TEMP", HERE), "drawio-export-chrome-profile")
    return subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars",
                           "--user-data-dir=" + prof] + args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=240)


def main():
    xml = drawio_xml()
    with open(os.path.join(HERE, NAME + ".drawio"), "w", encoding="utf-8", newline="\n") as f:
        f.write(xml)
    render = os.path.join(HERE, "_render.html")
    with open(render, "w", encoding="utf-8") as f:
        f.write(RENDER % json.dumps(xml).replace("</", "<\\/"))
    r = chrome(["--virtual-time-budget=60000", "--dump-dom", "file:///" + render.replace("\\", "/")])
    m = re.search(r'<textarea id="out">(.*?)</textarea>', r.stdout, re.S)
    if not m or not m.group(1).strip() or m.group(1).startswith("ERROR"):
        raise SystemExit("draw.io export failed: " + (m.group(1)[:300] if m else r.stdout[-500:]))
    svg = html.unescape(m.group(1))
    if not svg.startswith("<?xml"):
        svg = '<?xml version="1.0" encoding="UTF-8"?>\n' + svg
    with open(os.path.join(HERE, NAME + ".svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    sw = int(float(re.search(r'width="([\d.]+)px"', svg).group(1)))
    sh = int(float(re.search(r'height="([\d.]+)px"', svg).group(1)))
    page = os.path.join(HERE, "_page.html")
    with open(page, "w", encoding="utf-8") as f:
        f.write(PAGE % (sw, sh, sw, sh, NAME + ".svg"))
    url = "file:///" + page.replace("\\", "/")
    chrome(["--no-pdf-header-footer", "--virtual-time-budget=20000",
            "--print-to-pdf=" + os.path.join(HERE, NAME + ".pdf"), url])
    chrome(["--virtual-time-budget=20000", f"--window-size={sw},{sh}", "--force-device-scale-factor=2",
            "--screenshot=" + os.path.join(HERE, NAME + ".png"), url])
    for tmp in (render, page):
        os.remove(tmp)
    print("wrote .drawio, .svg (%dx%d), .pdf, .png" % (sw, sh))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
