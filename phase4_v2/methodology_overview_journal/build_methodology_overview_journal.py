"""Research methodology overview for a journal page (double-column width, ~180 mm), black and white.

Run from the repository root:
    python phase4_v2/methodology_overview_journal/build_methodology_overview_journal.py

Writes, in this folder:
    research_methodology_overview_journal.drawio   editable diagrams.net source (native shapes and connectors)
    research_methodology_overview_journal.svg      vector, rendered by diagrams.net's own engine (Graph.getSvg)
    research_methodology_overview_journal.pdf      vector, one page at the final printed size
    research_methodology_overview_journal.png      600 dpi raster at the final printed size

Designed at its final size: 1 drawing unit = 1 CSS px = 0.2646 mm, so the 680-unit canvas prints 180 mm wide,
11-unit body text prints at 8.25 pt and 12-unit stage labels at 9 pt. Every label line is measured with the
Arial font metrics before export; the build stops if any line would overflow or wrap inside its box.

draw.io Desktop is not installed on the build machine, so the exports load the official diagrams.net viewer
engine (https://viewer.diagrams.net/js/viewer-static.min.js) in headless Chrome; only that script is fetched.
"""
import html
import json
import os
import re
import subprocess
import sys

from PIL import ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "research_methodology_overview_journal"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
W, H = 680, 418                 # 180 mm x 110.6 mm
FB, FH = 11, 12                 # body 8.25 pt, stage labels 9 pt
PAD = 3                         # inner text spacing used in the box styles
FONTS = {(s, k): ImageFont.truetype(f, s) for s in (FB, FH)
         for k, f in (("r", "arial.ttf"), ("b", "arialbd.ttf"), ("i", "ariali.ttf"))}

LINE = "strokeColor=#000000;"
BASE = "html=1;whiteSpace=wrap;fontFamily=Arial;fontColor=#000000;rounded=0;shadow=0;glass=0;"
S = {
    "bg": "rounded=0;html=1;fillColor=#FFFFFF;strokeColor=none;locked=1;",
    "stage": BASE + LINE + f"fillColor=#F3F3F3;strokeWidth=0.8;align=center;verticalAlign=top;spacingTop=3;"
                           f"fontSize={FH};fontStyle=1;",
    "gt": BASE + LINE + f"fillColor=#FFFFFF;strokeWidth=1.6;align=left;verticalAlign=top;spacingTop=4;"
                        f"spacingLeft=196;fontSize={FH};fontStyle=1;",
    "box": BASE + LINE + f"fillColor=#FFFFFF;strokeWidth=0.8;align=center;verticalAlign=middle;spacing={PAD};"
                         f"fontSize={FB};",
    "frame": BASE + LINE + f"fillColor=#FFFFFF;strokeWidth=0.8;align=center;verticalAlign=top;spacingTop=1;"
                           f"fontSize={FB};",
    "data": BASE + LINE + f"shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=5;fillColor=#FFFFFF;"
                          f"strokeWidth=0.8;align=center;verticalAlign=middle;spacing={PAD};fontSize={FB};",
    "note": BASE + f"text;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;spacing={PAD};"
                   f"fontSize={FB};",
}
EDGE = ("rounded=0;html=1;strokeColor=#000000;endArrow=block;endFill=1;endSize=4;startSize=4;"
        "edgeStyle=orthogonalEdgeStyle;")
E_STYLE = {
    "flow": EDGE + "strokeWidth=0.9;",
    "straight": EDGE.replace("edgeStyle=orthogonalEdgeStyle;", "edgeStyle=none;") + "strokeWidth=0.9;",
    "gt": EDGE + "strokeWidth=1.4;dashed=1;dashPattern=4 3;",
}

CELLS, _ids, PROBLEMS = [], set(), []


def label(lines):
    """lines: list of (kind, text) with kind r / b / i; returns draw.io html."""
    out = []
    for kind, text in lines:
        t = html.escape(text, quote=False)
        out.append({"r": t, "b": f"<b>{t}</b>", "i": f"<i>{t}</i>"}[kind])
    return "<br>".join(out)


def check(cid, w, lines, size=FB, extra=0):
    room = w - 2 * PAD - 2 - extra
    for kind, text in lines:
        need = FONTS[(size, kind)].getlength(text)
        if need > room:
            PROBLEMS.append(f"{cid}: '{text}' needs {need:.0f} > {room:.0f}")


def box(cid, x, y, w, h, style, lines=(), size=FB, extra=0):
    assert cid not in _ids, cid
    _ids.add(cid)
    lines = list(lines)
    if lines and style not in ("stage", "gt", "frame"):
        check(cid, w, lines, size, extra)
        need_h = len(lines) * size * 1.2 + 2 * PAD - 2
        if need_h > h:
            PROBLEMS.append(f"{cid}: {len(lines)} lines need {need_h:.0f} px height > {h}")
    value = label(lines) if lines else ""
    CELLS.append(f'<mxCell id="{cid}" value="{html.escape(value, quote=True)}" style="{S[style]}" vertex="1" '
                 f'parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')


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


def stage(cid, x, w, title):
    check(cid, w, [("b", t) for t in title.split("\n")], FH)
    box(cid, x, TOP, w, BOT - TOP, "stage")
    CELLS[-1] = CELLS[-1].replace('value=""', f'value="{html.escape("<br>".join(title.split(chr(10))), quote=True)}"')


box("bg", 0, 0, W, H, "bg")
TOP, BOT, Y0 = 2, 312, 44       # stage band; first inner row
X1, W1 = 2, 186                 # data and execution
X2, W2 = 200, 120               # evidence preparation
X3, W3 = 332, 206               # triage methods
X4, W4 = 550, 128               # prediction and evaluation
stage("st1", X1, W1, "Data and execution")
stage("st2", X2, W2, "Evidence\npreparation")
stage("st3", X3, W3, "Triage methods")
stage("st4", X4, W4, "Prediction and\nevaluation")

# ------------------------------------------------------------------ 1 data and execution
# D2 is built from the held-out split (one killed mutant inside a held-out focal method; Paper l.211,
# src/triage/d2.py), so it hangs off the split, not off D1 directly.
full = W1 - 16
cx, cw, cg, cw2 = X1 + 8, 82, 13, 75             # split column, gap, D2 column (cw + cg + cw2 = full)
box("d1", cx, Y0, full, 40, "data", [("b", "D1 \u00b7 Defects4J 3.0.1"), ("r", "real faults")])
R2 = Y0 + 50
box("split", cx, R2, cw, 85, "box", [("b", "Project split"), ("r", "dev: 3 projects"), ("r", "(prompts,"),
                                     ("r", "thresholds)"), ("r", "held-out: 14")])
box("d2", cx + cw + cg, R2, cw2, 85, "data", [("b", "D2"), ("r", "seeded faults"), ("r", "held-out only"),
                                             ("r", "contamination"), ("r", "control")])
box("gen", cx, R2 + 95, full, 32, "box", [("b", "Unit-test generation"), ("r", "Gemma 4 26B-A4B")])
box("exe", cx, R2 + 137, full, 32, "box", [("b", "Compile and execute"), ("r", "on buggy (B) and fixed (F)")])
box("fev", cx, R2 + 179, full, 32, "box", [("b", "Failure evidence"), ("r", "outcome, message, stack trace")])
edge("a1", "d1", "split", exit=((cw / 2) / full, 1), entry=(0.5, 0))
edge("a1b", "split", "d2", exit=(1, 0.5), entry=(0, 0.5))
edge("a2", "split", "gen", exit=(0.5, 1), entry=((cw / 2) / full, 0))
edge("a3", "d2", "gen", exit=(0.5, 1), entry=((cw + cg + cw2 / 2) / full, 0))
edge("a4", "gen", "exe")
edge("a5", "exe", "fev")

# ------------------------------------------------------------------ 2 evidence preparation
ex, ew = X2 + 8, W2 - 16
box("prep", ex, Y0, ew, 70, "box", [("b", "Preprocessing"), ("r", "test filtering"),
                                    ("r", "trace normalisation"), ("r", "leakage guard")])
box("pkg", ex, Y0 + 86, ew, 70, "box", [("b", "Evidence package"), ("r", "S0 / S1 / S2"),
                                        ("r", "specification levels")])
box("wh", ex, Y0 + 168, ew, 62, "note", [("i", "Withheld from all"), ("i", "methods: fixed"),
                                         ("i", "version, patch,"), ("i", "labels")])
edge("b1", "prep", "pkg")
gx12 = X1 + W1 + 6
edge("b0", "fev", "prep", exit=(1, 0.5), entry=(0, 0.5), points=[(gx12, R2 + 195), (gx12, Y0 + 35)])

# ------------------------------------------------------------------ 3 triage methods
tx, tw = X3 + 8, W3 - 16
box("fa", tx, Y0, tw, 34, "box", [("b", "Non-LLM baselines"), ("r", "DA \u00b7 KA \u00b7 R0")])
box("fb", tx, Y0 + 42, tw, 34, "box", [("b", "Single-agent LLM"), ("r", "J1 \u00b7 SC \u00b7 SC-T")])
FY = Y0 + 84
box("deb", tx, FY, tw, 132, "frame", [])
CELLS[-1] = CELLS[-1].replace('value=""', 'value="' + html.escape("<b>DEB: proposed adversarial debate</b>",
                                                                   quote=True) + '"')
check("deb", tw, [("b", "DEB: proposed adversarial debate")])
bw = (tw - 12 - 14) // 2
box("advp", tx + 6, FY + 22, bw, 22, "box", [("r", "Advocate-P")])
box("advt", tx + 6 + bw + 14, FY + 22, bw, 22, "box", [("r", "Advocate-T")])
box("rebp", tx + 6, FY + 68, bw, 22, "box", [("r", "Rebuttal-P")])
box("rebt", tx + 6 + bw + 14, FY + 68, bw, 22, "box", [("r", "Rebuttal-T")])
aw = 110
box("adj", tx + (tw - aw) // 2, FY + 104, aw, 22, "box", [("r", "Adjudicator")])
edge("x1", "advp", "rebt", kind="straight", exit=(0.5, 1), entry=(0.5, 0))
edge("x2", "advt", "rebp", kind="straight", exit=(0.5, 1), entry=(0.5, 0))
edge("x3", "rebp", "adj", exit=(0.5, 1), entry=(0.15, 0))
edge("x4", "rebt", "adj", exit=(0.5, 1), entry=(0.85, 0))
box("bud", X3 + 3, FY + 136, W3 - 6, 46, "note", [("i", "Shared judge model: M1 (Qwen3.5 9B)"),
                                          ("i", "Equal budget: SC and DEB 5 calls,"),
                                          ("i", "SC-T matched to DEB tokens")])
gx23 = X2 + W2 + 6
for i, t in enumerate(("fa", "fb", "deb")):
    edge(f"c{i}", "pkg", t, exit=(1, 0.5), entry=(0, 0.5), points=[(gx23, Y0 + 121)])

# ------------------------------------------------------------------ 4 prediction and evaluation
px, pw = X4 + 8, W4 - 16
box("out", px, Y0, pw, 62, "box", [("b", "Common output"), ("r", "PROGRAM_FAULT /"), ("r", "TEST_FAULT"),
                                   ("r", "cited evidence ids")])
box("ev", px, BOT - 90, pw, 80, "box", [("b", "Evaluation"), ("r", "vs sealed labels:"), ("r", "classification"),
                                        ("r", "error and retention"), ("r", "efficiency")])
edge("d0", "out", "ev")
gx34 = X3 + W3 + 6
for i, s in enumerate(("fa", "fb", "deb")):
    edge(f"e{i}", s, "out", exit=(1, 0.5), entry=(0, 0.5), points=[(gx34, Y0 + 31)])

# ------------------------------------------------------------------ independent ground-truth pathway
G0, G1 = 322, 416
box("gtc", 2, G0, W - 4, G1 - G0, "gt")
CELLS[-1] = CELLS[-1].replace('value=""', 'value="Independent ground-truth pathway"')
gy, gh = G0 + 28, 60
g1x, g1w = cx, full
box("g1", g1x, gy, g1w, gh, "box", [("b", "Execution outcomes"), ("r", "every run on B and F")])
box("g2", 198, gy, 222, gh, "box", [("b", "PF / TF classification"), ("r", "PF: fails on B, passes on F"),
                                    ("r", "TF: fails on B and F, same failure signature"),
                                    ("r", "Other outcomes: excluded")])
box("g3", 438, gy, 150, gh, "box", [("b", "Sealed labels"), ("r", "never exposed to any triage"),
                                    ("r", "method or LLM judge")])
edge("h0", "st1", "g1", exit=(0.5, 1), entry=(0.5, 0))
edge("h1", "g1", "g2")
edge("h2", "g2", "g3")
evx = px + pw / 2
edge("h3", "g3", "ev", kind="gt", exit=(1, 0.5), entry=(0.5, 1), points=[(evx, gy + gh / 2)])


# ------------------------------------------------------------------ output
def drawio_xml():
    return ('<mxfile host="diagrams.net" type="device"><diagram id="methodology-overview" name="Methodology overview">'
            f'<mxGraphModel dx="{W}" dy="{H}" grid="0" gridSize="5" guides="1" tooltips="1" connect="1" arrows="1" '
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
    if PROBLEMS:
        raise SystemExit("label fit check failed:\n  " + "\n  ".join(PROBLEMS))
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
    chrome(["--virtual-time-budget=20000", f"--window-size={sw},{sh}", "--force-device-scale-factor=6.25",
            "--screenshot=" + os.path.join(HERE, NAME + ".png"), url])
    for tmp in (render, page):
        os.remove(tmp)
    print("wrote .drawio, .svg (%dx%d px = %.1f x %.1f mm), .pdf, .png (600 dpi)"
          % (sw, sh, sw * 25.4 / 96, sh * 25.4 / 96))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
