"""As-implemented research architecture, from ONE node/edge specification, written two ways:

  phase4_v2/figures/fig_final_architecture.drawio  editable in diagrams.net (draw.io)
  phase4_v2/figures/fig_final_architecture.tex     TikZ source; compiled to .pdf (vector) for the paper,
                                                    and to .png (pdftoppm) for the deck
Run from the repository root:  python phase4_v2/build/make_architecture.py
Neither diagrams.net nor Graphviz is installed on the build machine, so the rendered figure comes from the
TikZ output of this same specification; the .drawio file carries identical nodes, positions and edges.

Kept deliberately simple: one left-to-right pipeline, the ground-truth path beneath it, and one row for the
investigations added after the Phase 2 design. Each box has a bold name and one short detail line.
Styles: done = executed part of the approved Phase 2 design; gt = ground-truth channel (no LLM);
ext = executed later investigation (not in the Phase 2 design); notrun = planned in Phase 2, not run.
"""
import html
import os
import subprocess

OUT = os.path.join(os.getcwd(), "phase4_v2", "figures")
NAME = "fig_final_architecture"

STYLE = {  # fill, border, dash, text
    "done": ("EAF2FC", "2A78D6", None, "0B0B0B"),
    "gt": ("E6F6EF", "1BAF7A", None, "0B0B0B"),
    "ext": ("F0EEFC", "6250D6", "dashed", "0B0B0B"),
    "notrun": ("F7F7F5", "8A8984", "dotted", "5F5E5A"),
}
W, H, GAP = 2.75, 1.0, 0.35
COL = [W / 2 + i * (W + GAP) for i in range(6)]
# id: (x_cm, y_cm, w_cm, h_cm, style, name, detail)
N = {
    "data": (COL[0], 0, W, H, "done", "Defects4J 3.0.1", "D1 real, D2 seeded"),
    "gen": (COL[1], 0, W, H, "done", "Test generation", "Gemma 4 26B (local)"),
    "run": (COL[2], 0, W, H, "done", "Run each test", "buggy and fixed"),
    "ctx": (COL[3], 0, W, H, "done", "Evidence package", "S0 / S1 / S2"),
    "arms": (COL[4], 0, W, H, "done", "Triage arms", "J1, SC, DEB"),
    "eval": (COL[5], 0, W, H, "done", "Evaluation", "F1, MCC, bugs lost"),
    "d3": (COL[0], -1.8, W, 0.8, "notrun", "D3 GitBug-Java", "planned, not run"),
    "label": (COL[2], -1.8, W, 0.8, "gt", "Execution labels", "PF / TF, no LLM"),
    "rules": (2.05, -4.2, 4.1, 0.85, "ext", "Judge-only rules", "KUU baseline (RQ4)"),
    "cfp": (6.8, -4.2, 4.1, 0.85, "ext", "Mutation probes", "exploratory pilot"),
    "conf": (11.55, -4.2, 4.1, 0.85, "ext", "Registered confirmation", "OSF kp79c, C1--C4"),
    "wdp": (16.3, -4.2, 4.1, 0.85, "ext", "Whole-method probes", "exploratory, retrospective"),
}
# (from, to, style, from_side, to_side)
E = [
    ("data", "gen", "done", "E", "W"), ("gen", "run", "done", "E", "W"), ("run", "ctx", "done", "E", "W"),
    ("ctx", "arms", "done", "E", "W"), ("arms", "eval", "done", "E", "W"),
    ("d3", "data", "notrun", "N", "S"),
    ("run", "label", "gt", "S", "N"), ("label", "eval", "gt", "E", "S"),
    ("rules", "cfp", "ext", "E", "W"), ("cfp", "conf", "ext", "E", "W"), ("conf", "wdp", "ext", "E", "W"),
]
RIGHT = COL[5] + W / 2
TOP_TITLE = (0.85, "Original study: the approved Phase 2 design, as executed")
BAND = (-2.85, "Later investigations, added after the Phase 2 design (in the order run)")
LEGEND_Y = -5.2
LEGEND = [("done", "executed (Phase 2 design)"), ("gt", "ground truth, no LLM"),
          ("ext", "later investigation"), ("notrun", "planned, not run")]


def anchor(nid, side):
    x, y, w, h = N[nid][:4]
    return {"N": (x, y + h / 2), "S": (x, y - h / 2), "E": (x + w / 2, y), "W": (x - w / 2, y)}[side]


def path(a, b, sa, sb):
    (x1, y1), (x2, y2) = anchor(a, sa), anchor(b, sb)
    if sa in "EW" and sb in "NS":
        return [(x1, y1), (x2, y1), (x2, y2)]
    return [(x1, y1), (x2, y2)]


def tikz():
    L = [r"\documentclass[tikz,border=3pt]{standalone}", r"\usepackage[T1]{fontenc}", r"\usepackage{helvet}",
         r"\renewcommand{\familydefault}{\sfdefault}", r"\usetikzlibrary{arrows.meta}", r"\begin{document}",
         r"\begin{tikzpicture}[>={Stealth[length=2.2mm]}]"]
    for k, (fill, border, _d, text) in STYLE.items():
        L.append(rf"\definecolor{{f{k}}}{{HTML}}{{{fill}}}\definecolor{{b{k}}}{{HTML}}{{{border}}}"
                 rf"\definecolor{{t{k}}}{{HTML}}{{{text}}}")
    L.append(rf"\node[anchor=west,font=\footnotesize\bfseries,text=black!70] at (0,{TOP_TITLE[0]}) {{{TOP_TITLE[1]}}};")
    L.append(rf"\draw[densely dashed,black!35] (0,{BAND[0]}) -- ({RIGHT},{BAND[0]});")
    L.append(rf"\node[anchor=west,font=\footnotesize\bfseries,text=black!70] at (0,{BAND[0] - 0.4}) {{{BAND[1]}}};")
    for nid, (x, y, w, h, st, name, detail) in N.items():
        dash = STYLE[st][2] or "solid"
        L.append(rf"\node[draw=b{st},fill=f{st},text=t{st},{dash},line width=0.9pt,rounded corners=3pt,"
                 rf"minimum width={w}cm,minimum height={h}cm,text width={w - 0.2}cm,align=center,inner sep=2pt,"
                 r"execute at begin node={\hyphenpenalty=10000\relax}] "
                 rf"({nid}) at ({x},{y}) {{{{\footnotesize\bfseries {name}}}\\[1pt]{{\scriptsize {detail}}}}};")
    for a, b, st, sa, sb in E:
        dash = STYLE[st][2] or "solid"
        side = {"N": "north", "S": "south", "E": "east", "W": "west"}
        op = "-|" if (sa in "EW" and sb in "NS") else "--"   # attach to the drawn box edges, whatever their height
        pts = f"({a}.{side[sa]}) {op} ({b}.{side[sb]})"
        L.append(rf"\draw[->,draw=b{st},{dash},line width=0.9pt] {pts};")
    for i, (st, lab) in enumerate(LEGEND):
        x = i * 4.45
        dash = STYLE[st][2] or "solid"
        L.append(rf"\node[draw=b{st},fill=f{st},{dash},line width=0.9pt,minimum width=0.55cm,minimum height=0.3cm]"
                 rf" at ({x + 0.28},{LEGEND_Y}) {{}};")
        L.append(rf"\node[anchor=west,font=\scriptsize] at ({x + 0.65},{LEGEND_Y}) {{{lab}}};")
    L += [r"\end{tikzpicture}", r"\end{document}"]
    return "\n".join(L) + "\n"


def drawio():
    s = 40  # px per cm
    ox, oy = 0.5 * s, 1.5 * s

    def px(x, y):
        return ox + x * s, oy - y * s

    rel = {"N": (0.5, 0), "S": (0.5, 1), "E": (1, 0.5), "W": (0, 0.5)}
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    for nid, (x, y, w, h, st, name, detail) in N.items():
        fill, border, dash, text = STYLE[st]
        cx, cy = px(x, y)
        label = html.escape("<b>" + html.escape(name) + "</b><br><font style=\"font-size:9px\">"
                            + html.escape(detail.replace("--", "–")) + "</font>")
        dstyle = "dashed=1;" if dash == "dashed" else ("dashed=1;dashPattern=1 2;" if dash == "dotted" else "")
        cells.append(f'<mxCell id="{nid}" value="{label}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#{fill};'
                     f'strokeColor=#{border};fontColor=#{text};fontSize=11;{dstyle}" vertex="1" parent="1">'
                     f'<mxGeometry x="{cx - w * s / 2:.0f}" y="{cy - h * s / 2:.0f}" width="{w * s:.0f}" '
                     f'height="{h * s:.0f}" as="geometry"/></mxCell>')
    for i, (a, b, st, sa, sb) in enumerate(E):
        _f, border, dash, _t = STYLE[st]
        (ex, ey), (nx, ny) = rel[sa], rel[sb]
        cells.append(f'<mxCell id="e{i}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#{border};'
                     f'{"dashed=1;" if dash else ""}endArrow=block;endFill=1;exitX={ex};exitY={ey};entryX={nx};'
                     f'entryY={ny};" edge="1" parent="1" source="{a}" target="{b}"><mxGeometry relative="1" '
                     f'as="geometry"/></mxCell>')
    for j, (y, label) in enumerate([TOP_TITLE, (BAND[0] - 0.4, BAND[1])]):
        cx, cy = px(0, y)
        cells.append(f'<mxCell id="t{j}" value="{html.escape(label)}" style="text;html=1;fontStyle=1;align=left;'
                     f'verticalAlign=middle;fontColor=#555555;" vertex="1" parent="1"><mxGeometry x="{cx:.0f}" '
                     f'y="{cy - 10:.0f}" width="560" height="20" as="geometry"/></mxCell>')
    x1, y1 = px(0, BAND[0])
    x2, _ = px(RIGHT, BAND[0])
    cells.append(f'<mxCell id="band" style="endArrow=none;html=1;dashed=1;strokeColor=#AAAAAA;" edge="1" parent="1">'
                 f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x1:.0f}" y="{y1:.0f}" as="sourcePoint"/>'
                 f'<mxPoint x="{x2:.0f}" y="{y1:.0f}" as="targetPoint"/></mxGeometry></mxCell>')
    for i, (st, lab) in enumerate(LEGEND):
        fill, border, dash, _t = STYLE[st]
        cx, cy = px(i * 4.45, LEGEND_Y)
        cells.append(f'<mxCell id="l{i}" value="{html.escape(lab)}" style="rounded=0;html=1;fillColor=#{fill};'
                     f'strokeColor=#{border};{"dashed=1;" if dash else ""}align=left;spacingLeft=6;fontSize=10;" '
                     f'vertex="1" parent="1"><mxGeometry x="{cx:.0f}" y="{cy - 8:.0f}" width="170" height="16" '
                     f'as="geometry"/></mxCell>')
    return ('<mxfile host="generated" type="device"><diagram id="arch" name="As-implemented architecture">'
            '<mxGraphModel grid="1" gridSize="10" page="1" pageWidth="1169" pageHeight="827"><root>'
            + "".join(cells) + "</root></mxGraphModel></diagram></mxfile>\n")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8", newline="\n") as f:
        f.write(tikz())
    with open(os.path.join(OUT, NAME + ".drawio"), "w", encoding="utf-8", newline="\n") as f:
        f.write(drawio())
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", NAME + ".tex"], cwd=OUT, check=True,
                   stdout=subprocess.DEVNULL)
    subprocess.run(["pdftoppm", "-png", "-r", "220", "-singlefile", NAME + ".pdf", NAME], cwd=OUT, check=True)
    for ext in (".aux", ".log"):
        p = os.path.join(OUT, NAME + ext)
        if os.path.exists(p):
            os.remove(p)
    print("wrote", NAME, ".tex/.drawio/.pdf/.png")
