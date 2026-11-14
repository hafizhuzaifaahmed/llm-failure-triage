"""Simplified research methodology architecture (draw.io), A3 landscape, black and white.

Run from the repository root:
    python phase4_v2/methodology_architecture_simple/build_methodology_architecture_simple.py

Writes, in this folder:
    research_methodology_architecture_simple.drawio   editable diagrams.net source (native mxGraph XML)
    research_methodology_architecture_simple.svg      rendered by diagrams.net's own engine (Graph.getSvg)
    research_methodology_architecture_simple.pdf      that SVG on one A3 landscape page (420 x 297 mm), vector
    research_methodology_architecture_simple.png      that SVG rasterised at 2x

The canvas is draw.io's own A3 landscape page (1654 x 1169 units; 1 unit = 0.254 mm = 0.72 pt), so a 16-unit
font prints at 11.5 pt on A3. No text in the figure is smaller than 16 units.

draw.io Desktop is not installed on the build machine, so the exports load the official diagrams.net viewer engine
(https://viewer.diagrams.net/js/viewer-static.min.js) in headless Chrome. Only the viewer script is fetched.
Details too fine for the figure are recorded in architecture_content_audit.md, not squeezed into boxes.
"""
import html
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "research_methodology_architecture_simple"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W, H = 1654, 1169          # draw.io A3 landscape
FS = 16                    # body text (11.5 pt on A3)
FH = 17                    # headers

BASE = "html=1;whiteSpace=wrap;fontFamily=Arial;fontColor=#000000;rounded=0;shadow=0;glass=0;"
S = {
    "bg": "rounded=0;html=1;fillColor=#FFFFFF;strokeColor=none;locked=1;",
    "title": BASE + "text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=22;fontStyle=1;",
    "stage": BASE + f"fillColor=#F2F2F2;strokeColor=#000000;strokeWidth=1;align=center;verticalAlign=top;"
                    f"spacingTop=6;fontSize={FH};fontStyle=1;",
    "gt": BASE + f"fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2.5;align=left;verticalAlign=top;"
                 f"spacingTop=6;spacingLeft=248;fontSize={FH};",
    "key": BASE + "fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=2.5;",
    "strip": BASE + f"fillColor=#F2F2F2;strokeColor=#000000;strokeWidth=1;align=left;verticalAlign=top;"
                    f"spacingTop=6;spacingLeft=12;fontSize={FH};fontStyle=1;",
    "box": BASE + f"fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1;align=center;verticalAlign=middle;"
                  f"spacing=4;fontSize={FS};",
    "boxx": BASE + f"fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1;dashed=1;dashPattern=6 4;align=center;"
                   f"verticalAlign=middle;spacing=4;fontSize={FS};",
    "data": BASE + f"shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=8;fillColor=#FFFFFF;strokeColor=#000000;"
                   f"strokeWidth=1;align=center;verticalAlign=middle;fontSize={FS};",
    "text": BASE + f"text;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize={FS};",
    "textl": BASE + f"text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize={FS};",
    "label": BASE + f"text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize={FS};fontStyle=1;",
}
EDGE = ("rounded=0;html=1;fontFamily=Arial;fontColor=#000000;strokeColor=#000000;endArrow=block;endFill=1;"
        "endSize=7;edgeStyle=orthogonalEdgeStyle;")
E_STYLE = {
    "flow": EDGE + "strokeWidth=1.25;",
    "gt": EDGE + "strokeWidth=2.5;dashed=1;dashPattern=8 5;",
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


def edge(cid, src, tgt, kind="flow", exit=None, entry=None, points=None):
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
    CELLS.append(f'<mxCell id="{cid}" value="" style="{st}" edge="1" parent="1" source="{src}" target="{tgt}">'
                 f'<mxGeometry relative="1" as="geometry">{pts}</mxGeometry></mxCell>')


def free_edge(cid, x1, y1, x2, y2, kind):
    _ids.add(cid)
    st = E_STYLE[kind].replace("edgeStyle=orthogonalEdgeStyle;", "")
    CELLS.append(f'<mxCell id="{cid}" value="" style="{st}" edge="1" parent="1"><mxGeometry relative="1" '
                 f'as="geometry"><mxPoint x="{x1}" y="{y1}" as="sourcePoint"/><mxPoint x="{x2}" y="{y2}" '
                 f'as="targetPoint"/></mxGeometry></mxCell>')


def L(title, *rest):
    """Bold title line plus at most a few short plain lines."""
    return "<br>".join(["<b>" + title + "</b>"] + list(rest))


# ------------------------------------------------------------------ page
box("bg", 0, 0, W, H, "bg")
box("title", 28, 18, 1500, 36, "title",
    "Research methodology architecture: LLM triage of failing generated unit tests "
    "(program fault vs test fault)")

TOP, BOT = 72, 600                      # main workflow band
HDR = 52                                # header band inside a stage
IY = TOP + HDR + 4                      # first inner box
GAP = 26
stages = [("s1", 28, 206, "Datasets and partitioning"),
          ("s2", 260, 206, "Test generation and execution"),
          ("s3", 492, 232, "Preprocessing and evidence"),
          ("s4", 750, 446, "Triage methods"),
          ("s5", 1222, 178, "Prediction interface"),
          ("s6", 1426, 200, "Evaluation")]
X = {}
for sid, x, w, title in stages:
    box(sid, x, TOP, w, BOT - TOP, "stage", title)
    X[sid] = (x, w)


def inner(sid):
    x, w = X[sid]
    return x + 12, w - 24


# ------------------------------------------------------------------ 1  datasets and partitioning
ix, iw = inner("s1")
box("d1", ix, IY, iw, 108, "data", L("D1 \u00b7 Defects4J 3.0.1", "real faults", "17 projects"))
box("split", ix, IY + 132, iw, 96, "box", L("Project-level split", "development: 3 projects", "held-out: 14 projects"))
box("d2", ix, IY + 252, iw, 108, "data", L("D2 \u00b7 Seeded faults", "contamination control", "mutants in held-out methods"))
box("n1", ix, IY + 372, iw, 92, "text", "<i>Development projects: prompt design, calibration and pilot only</i>")
edge("e11", "d1", "split")
edge("e12", "split", "d2")

# ------------------------------------------------------------------ 2  test generation and execution
ix, iw = inner("s2")
box("gen", ix, IY, iw, 92, "box", L("Test generation", "Gemma 4 26B-A4B", "3 per method, T = 0.7"))
box("comp", ix, IY + 108, iw, 92, "box", L("Compilation", "against buggy (B)", "and fixed (F) versions"))
box("exec", ix, IY + 216, iw, 92, "box", L("Execution", "3 runs each on B and F", "fresh JVM, 30 s timeout"))
box("fev", ix, IY + 324, iw, 92, "box", L("Failure evidence", "outcome, message,", "stack trace"))
box("n2", ix, IY + 422, iw, 48, "text", "<i>Ubuntu 22.04.5 (WSL2), OpenJDK 11</i>")
edge("e21", "gen", "comp")
edge("e22", "comp", "exec")
edge("e23", "exec", "fev")
edge("e12x", "s1", "gen", exit=(1, (IY + 46 - TOP) / (BOT - TOP)), entry=(0, 0.5))

# ------------------------------------------------------------------ 3  preprocessing and evidence
ix, iw = inner("s3")
box("filt", ix, IY, iw, 92, "box", L("Filtering", "flaky, timeout, environment", "and duplicate tests removed"))
box("norm", ix, IY + 108, iw, 92, "box", L("Normalisation", "stack traces,", "length limits"))
box("leak", ix, IY + 216, iw, 92, "box", L("Leakage guard", "blocks bug ids, fix text", "and focal-method body"))
box("pkg", ix, IY + 324, iw, 140, "box",
    L("Evidence package", "S0: test, failure, signature", "S1: S0 + Javadoc", "S2: S1 + inferred spec"))
edge("e31", "filt", "norm")
edge("e32", "norm", "leak")
edge("e33", "leak", "pkg")
gx2 = X["s2"][0] + X["s2"][1] + GAP // 2
edge("e23x", "fev", "filt", exit=(1, 0.5), entry=(0, 0.5), points=[(gx2, IY + 370), (gx2, IY + 46)])

# ------------------------------------------------------------------ 4  triage methods
ix, iw = inner("s4")
box("fa", ix, IY, iw, 70, "box", L("Non-LLM baselines", "DA discard-all \u00b7 KA keep-all \u00b7 R0 failure-type rule"))
box("fb", ix, IY + 86, iw, 70, "box", L("Single-agent LLM", "J1 one call \u00b7 SC majority of 5 \u00b7 SC-T token-matched"))
DY = IY + 172
box("deblab", ix, DY, iw, 26, "label", "DEB \u00b7 proposed adversarial debate (5 calls)")
cw, cg = 118, 34
ry = DY + 32
box("advp", ix, ry, cw, 54, "box", L("Advocate-P", "program fault"))
box("advt", ix, ry + 66, cw, 54, "box", L("Advocate-T", "test fault"))
box("rebp", ix + cw + cg, ry, cw, 54, "box", L("Rebuttal-P", "round 2"))
box("rebt", ix + cw + cg, ry + 66, cw, 54, "box", L("Rebuttal-T", "round 2"))
ax = ix + 2 * (cw + cg)
box("adj", ax, ry, ix + iw - ax, 120, "box", L("Adjudicator", "reads all four", "arguments,", "anonymised"))
box("debn", ix, ry + 126, iw, 30, "text", "<i>Round 2: each side rebuts the other's round-1 argument</i>")
edge("ed1", "advp", "rebp")
edge("ed2", "advt", "rebt")
edge("ed3", "rebp", "adj", exit=(1, 0.5), entry=(0, 0.225))
edge("ed4", "rebt", "adj", exit=(1, 0.5), entry=(0, 0.775))
box("ctrl", ix, BOT - 96, iw, 84, "box",
    "Same judge M1 (Qwen3.5 9B), decoding and evidence<br>"
    "<b>Equal budget</b>: SC and DEB 5 calls of \u2264 512 tokens<br>SC-T matches DEB's consumed tokens")
gx3 = X["s3"][0] + X["s3"][1] + GAP // 2
for i, tgt in enumerate(("fa", "fb", "advp", "advt")):
    edge(f"e34{i}", "pkg", tgt, exit=(1, 0.5), entry=(0, 0.5), points=[(gx3, IY + 394)])

# ------------------------------------------------------------------ 5  prediction interface
ix, iw = inner("s5")
box("out", ix, IY, iw, 160, "box", L("Structured output", "PROGRAM_FAULT", "or TEST_FAULT", "reason, cited", "evidence ids"))
box("val", ix, BOT - 128, iw, 116, "box", L("Validation", "one repair parse;", "invalid output", "scored TF"))
edge("e51", "out", "val")
gx4 = X["s4"][0] + X["s4"][1] + GAP // 2
for i, src in enumerate(("fa", "fb", "adj")):
    edge(f"e45{i}", src, "out", exit=(1, 0.5), entry=(0, 0.5), points=[(gx4, IY + 80)])

# ------------------------------------------------------------------ 6  evaluation
ix, iw = inner("s6")
box("m1", ix, IY, iw, 92, "box", L("Classification", "Precision, Recall, F1", "FPR, FNR, MCC"))
box("m2", ix, IY + 108, iw, 92, "box", L("Error and retention", "PF tests lost,", "FP / FN analysis"))
box("m3", ix, IY + 216, iw, 100, "box", L("Statistics and cost", "bug-level bootstrap,", "Holm correction;", "calls, tokens, latency"))
box("score", ix, BOT - 128, iw, 116, "box", L("Scoring", "predictions joined", "to sealed labels"))
edge("e56", "val", "score")
edge("e6u", "score", "m3")

# ------------------------------------------------------------------ sealed ground-truth channel
GT0, GT1 = 626, 790
gx, gw = X["s2"][0], X["s6"][0] + X["s6"][1] - X["s2"][0]
box("gtc", gx, GT0, gw, GT1 - GT0, "gt",
    "<b>Sealed ground-truth channel</b>: labels are never visible to any LLM or triage method; "
    "they are used only at evaluation")
by = GT0 + 46
box("g1", X["s2"][0] + 12, by, X["s2"][1] - 24, 100, "box", L("Execution outcomes", "every run on B and F"))
box("g2", 520, by, 330, 100, "box",
    L("Ground-truth classification", "PF: fails on B, passes on F", "TF: fails on B and F, same signature"))
box("g3", 900, by, 330, 100, "box",
    L("Sealed PF / TF labels", "stored where no method can read them;", "sample: all PF, 2 TF per PF"))
edge("eg0", "s2", "g1", exit=(0.5, 1), entry=(0.5, 0))
edge("eg1", "g1", "g2")
edge("eg2", "g2", "g3")
sx6 = X["s6"][0] + X["s6"][1] // 2
edge("eg3", "g3", "score", kind="gt", exit=(1, 0.5), entry=(0.5, 1), points=[(sx6, by + 50)])

# ------------------------------------------------------------------ experimental conditions and additional analyses
ST0, ST1 = 814, 1010
box("strip", 28, ST0, W - 56, ST1 - ST0, "strip", "Experimental Conditions and Additional Analyses")
cells = [
    ("c1", "box", L("Specification availability", "S0 / S1 / S2 (E2)")),
    ("c2", "box", L("Arm and budget comparison", "all arms (E1); equal budget (E3)")),
    ("c3", "boxx", L("Ablation studies", "debate, evidence and input", "variants (E4)")),
    ("c4", "boxx", L("Robustness", "D2, second judge, per-project", "analysis (E5)")),
    ("c5", "box", L("Registered confirmation", "mutation-probe hypotheses", "C1\u2013C4 (OSF kp79c)")),
    ("c6", "boxx", L("Supplementary investigations", "judge-only rules (KUU),", "mutation and whole-method probes")),
]
cw2, cg2 = 252, 12
for i, (cid, st, lab) in enumerate(cells):
    box(cid, 40 + i * (cw2 + cg2), ST0 + 44, cw2, 96, st, lab)
box("sn", 40, ST0 + 148, W - 80, 40, "textl",
    "<i>Solid border: confirmatory (hypotheses H1\u2013H3b and C1\u2013C4, Holm-corrected). "
    "Dashed border: exploratory or supplementary. Probes execute the buggy version only, without LLMs or labels.</i>")

# ------------------------------------------------------------------ analytical objectives and key
box("obj", 28, 1024, W - 56, 32, "textl",
    "<b>Analytical objectives:</b>  accuracy and test loss  |  specification effect  |  architecture effect  |  "
    "efficiency  |  robustness  |  judge-only and probe-based rules")
KY = 1094
free_edge("k1", 40, KY, 100, KY, "flow")
box("k1t", 108, KY - 14, 170, 28, "textl", "workflow data")
free_edge("k2", 290, KY, 390, KY, "gt")
box("k2t", 398, KY - 14, 300, 28, "textl", "sealed labels, used only at evaluation")
box("k3", 710, KY - 13, 44, 26, "stage")
box("k3t", 762, KY - 14, 150, 28, "textl", "workflow stage")
box("k4", 930, KY - 13, 44, 26, "key")
box("k4t", 982, KY - 14, 210, 28, "textl", "ground-truth channel")
box("k5", 1210, KY - 13, 44, 26, "boxx")
box("k5t", 1262, KY - 14, 330, 28, "textl", "exploratory or supplementary analysis")


# ------------------------------------------------------------------ output
def drawio_xml():
    return ('<mxfile host="diagrams.net" type="device"><diagram id="methodology-simple" name="Methodology architecture">'
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
      var svg = viewer.graph.getSvg('#ffffff', 1, 0, true, null, true, true, null, null, false);
      document.getElementById('out').textContent = mxUtils.getXml(svg);
    });
  } catch (e) { document.getElementById('out').textContent = 'ERROR ' + e; }
});
</script></body></html>
"""

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
@page { size: 420mm 297mm; margin: 0 } html, body { margin: 0; padding: 0; background: #fff }
img { display: block; width: 420mm; height: 297mm }
</style></head><body><img src="%s"></body></html>
"""
PNGPAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html, body { margin: 0; padding: 0; background: #fff } img { display: block; width: %dpx; height: %dpx }
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
        f.write(PAGE % (NAME + ".svg"))
    chrome(["--no-pdf-header-footer", "--virtual-time-budget=20000",
            "--print-to-pdf=" + os.path.join(HERE, NAME + ".pdf"), "file:///" + page.replace("\\", "/")])
    with open(page, "w", encoding="utf-8") as f:
        f.write(PNGPAGE % (sw, sh, NAME + ".svg"))
    chrome(["--virtual-time-budget=20000", f"--window-size={sw},{sh}", "--force-device-scale-factor=2",
            "--screenshot=" + os.path.join(HERE, NAME + ".png"), "file:///" + page.replace("\\", "/")])
    for tmp in (render, page):
        os.remove(tmp)
    print("wrote .drawio, .svg (%dx%d), .pdf (A3 landscape), .png" % (sw, sh))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
