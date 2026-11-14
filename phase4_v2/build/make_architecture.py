"""As-implemented research architecture, drawn from ONE specification and written two ways:

  phase4_v2/figures/fig_final_architecture.drawio  editable in diagrams.net (draw.io)
  phase4_v2/figures/fig_final_architecture.tex     TikZ source; compiled to .pdf (vector) for the paper and to
                                                    .png (pdftoppm) for the deck
Run from the repository root:  python phase4_v2/build/make_architecture.py
Neither diagrams.net nor Graphviz is installed on the build machine, so the rendered figure comes from the TikZ
output of this same specification; the .drawio file carries the same nodes, shapes, positions and connections.

Visual language (as an architect would draw it): two grouped panels (the original study; the later studies),
numbered stages, a database symbol for the benchmark, stacked cards for the triage arms, a separate ground-truth
channel, chevrons for the sequence of later studies, colour by evidence status, neutral arrows.
"""
import html
import os
import subprocess

OUT = os.path.join(os.getcwd(), "phase4_v2", "figures")
NAME = "fig_final_architecture"

C = {  # name: (fill, border, text) -- gray-and-white theme; status is carried by fill shade and line style
    "ink": ("3A3A3A", "3A3A3A", "FFFFFF"),
    "stage": ("FFFFFF", "3A3A3A", "1B1B1B"),
    "data": ("EFEFEF", "3A3A3A", "1B1B1B"),
    "gt": ("E2E2E2", "3A3A3A", "1B1B1B"),
    "notrun": ("FFFFFF", "9A9A9A", "6E6E6E"),
    "rule": ("EDEDED", "5A5A5A", "1B1B1B"),
    "expl": ("FFFFFF", "5A5A5A", "1B1B1B"),
    "reg": ("D4D4D4", "3A3A3A", "1B1B1B"),
    "panelA": ("F7F7F7", "CFCFCF", "333333"),
    "panelB": ("FBFBFB", "D9D9D9", "333333"),
    "arrow": ("4A4A4A", "4A4A4A", "4A4A4A"),
}
DASH = {"notrun": "dash pattern=on 1pt off 1.6pt", "expl": "dash pattern=on 4pt off 2pt"}
DRAWIO_DASH = {"notrun": "dashed=1;dashPattern=1 2;", "expl": "dashed=1;dashPattern=4 2;"}

# panels: (x0, y0, x1, y1, colour, title)
PANELS = [(-0.25, 1.8, 19.25, -3.15, "panelA", "Original study \\textendash{} the approved Phase 2 design, as executed"),
          (-0.25, -3.5, 19.25, -5.85, "panelB", "Later studies \\textendash{} added after Phase 2, in the order they were run")]

# nodes: id -> (shape, x, y, w, h, colour, name, detail, badge)
X = [1.25, 4.425, 7.725, 11.025, 14.325, 17.625]
BW, BH = 2.75, 1.45
N = {
    "data": ("cyl", X[0], 0.0, 2.5, 1.75, "data", "Defects4J 3.0.1", "D1 real faults\\\\D2 seeded faults", None),
    "gen": ("box", X[1], 0.0, BW, BH, "stage", "Test generation", "Gemma 4 26B", "1"),
    "exec": ("box", X[2], 0.0, BW, BH, "stage", "Dual execution", "buggy \\,\\textbar\\, fixed, 3 runs", "2"),
    "ctx": ("box", X[3], 0.0, BW, BH, "stage", "Evidence package", "S0 \\,\\textbar\\, S1 \\,\\textbar\\, S2", "3"),
    "arms": ("stack", X[4], 0.0, BW, BH, "stage", "Triage arms", "J1 \\textperiodcentered{} SC \\textperiodcentered{} DEB", "4"),
    "eval": ("box", X[5], 0.0, BW, BH, "stage", "Evaluation", "F1 \\textperiodcentered{} MCC \\textperiodcentered{} bugs lost", "5"),
    "gt": ("box", X[2], -2.3, BW, 1.05, "gt", "Execution labels", "PF / TF, sealed", None),
    "d3": ("cyl", X[0], -2.3, 2.3, 1.25, "notrun", "GitBug-Java", "D3 \\textendash{} not run", None),
    "kuu": ("chev0", 2.425, -4.8, 4.85, 1.05, "rule", "Judge-only rules", "KUU baseline (RQ4)", None),
    "cfp": ("chev", 7.175, -4.8, 4.85, 1.05, "expl", "Mutation probes", "pilot, exploratory", None),
    "conf": ("chev", 11.925, -4.8, 4.85, 1.05, "reg", "Registered confirmation", "OSF kp79c, C1\\textendash{}C4", None),
    "wdp": ("chev", 16.675, -4.8, 4.85, 1.05, "expl", "Whole-method probes", "exploratory, retrospective", None),
}
# edges: (from anchor, to anchor, route, style)
E = [("data.east", "gen.west", "--", "main"), ("gen.east", "exec.west", "--", "main"),
     ("exec.east", "ctx.west", "--", "main"), ("ctx.east", "arms.west", "--", "main"),
     ("[xshift=6pt]arms.east", "eval.west", "--", "main"),
     ("exec.south", "gt.north", "--", "gt"), ("gt.east", "eval.south", "-|", "gt"),
     ("d3.north", "data.south", "--", "notrun")]
GT_NOTE = (13.4, -2.0, "ground-truth channel \\textendash{} no LLM sees it")
LEGEND = [("data", "executed"), ("gt", "ground truth / registered"), ("rule", "fixed in advance"),
          ("expl", "exploratory"), ("notrun", "planned, not run")]
LEGEND_Y = -6.3


def tikz():
    L = [r"\documentclass[tikz,border=4pt]{standalone}", r"\usepackage[T1]{fontenc}", r"\usepackage{helvet}",
         r"\usepackage{textcomp}", r"\renewcommand{\familydefault}{\sfdefault}",
         r"\usetikzlibrary{arrows.meta,shapes.geometric,shapes.symbols,shadows,calc}", r"\begin{document}",
         r"\begin{tikzpicture}[>={Latex[length=2.4mm,width=1.8mm]},"
         r"lbl/.style={align=center,execute at begin node={\hyphenpenalty=10000\relax}}]"]
    for k, (f, b, t) in C.items():
        L.append(rf"\definecolor{{f{k}}}{{HTML}}{{{f}}}\definecolor{{b{k}}}{{HTML}}{{{b}}}\definecolor{{t{k}}}{{HTML}}{{{t}}}")
    for x0, y0, x1, y1, col, title in PANELS:
        L.append(rf"\draw[fill=f{col},draw=b{col},line width=0.7pt,rounded corners=6pt] ({x0},{y0}) rectangle ({x1},{y1});")
        L.append(rf"\node[anchor=north west,font=\footnotesize\bfseries,text=t{col}] at ({x0 + 0.2},{y0 - 0.12}) {{{title}}};")
    for nid, (shape, x, y, w, h, col, name, detail, badge) in N.items():
        body = rf"{{\footnotesize\bfseries {name}}}\\[1pt]{{\scriptsize\color{{black!65}} {detail}}}"
        dash = DASH[col] + "," if col in DASH else ""
        common =rf"draw=b{col},fill=f{col},text=t{col},line width=0.9pt,{dash}lbl,text width={w - 0.12}cm"
        if shape == "cyl":
            L.append(rf"\node[{common},cylinder,shape border rotate=90,aspect=0.16,minimum width={w}cm,"
                     rf"minimum height={h}cm,inner sep=2pt] ({nid}) at ({x},{y}) {{{body}}};")
        elif shape == "stack":
            L.append(rf"\node[{common},rounded corners=3pt,minimum width={w}cm,minimum height={h}cm,inner sep=3pt,"
                     rf"double copy shadow={{shadow xshift=3pt,shadow yshift=3pt,fill=white,draw=b{col},line width=0.7pt}}]"
                     rf" ({nid}) at ({x},{y}) {{{body}}};")
        elif shape.startswith("chev"):
            frm = "nowhere" if shape == "chev0" else "west"
            L.append(rf"\node[{common},signal,signal to=east,signal from={frm},signal pointer angle=120,"
                     rf"minimum width={w}cm,minimum height={h}cm,inner sep=2pt] ({nid}) at ({x},{y}) {{{body}}};")
        else:
            L.append(rf"\node[{common},rounded corners=3pt,minimum width={w}cm,minimum height={h}cm,inner sep=3pt]"
                     rf" ({nid}) at ({x},{y}) {{{body}}};")
        if badge:
            L.append(rf"\node[circle,fill=fink,text=white,font=\scriptsize\bfseries,inner sep=0pt,minimum size=0.42cm]"
                     rf" at ({nid}.north west) {{{badge}}};")
    for a, b, route, st in E:
        if st == "main":
            sty = r"->,draw=farrow,line width=1.1pt"
        elif st == "gt":
            sty = r"->,draw=bgt,line width=1.1pt,rounded corners=5pt"
        else:
            sty = r"->,draw=bnotrun,line width=0.9pt,dash pattern=on 1.5pt off 1.5pt"
        L.append(rf"\draw[{sty}] ({a}) {route} ({b});")
    L.append(rf"\node[font=\scriptsize\itshape,text=bgt!80!black,fill=fpanelA,inner sep=1pt] at ({GT_NOTE[0]},{GT_NOTE[1]}) {{{GT_NOTE[2]}}};")
    # legend: each item starts a fixed gap after the measured end of the previous label (even spacing)
    L.append(rf"\coordinate (lg0) at (-0.6,{LEGEND_Y});")
    for i, (col, lab) in enumerate(LEGEND, start=1):
        dash = "," + DASH[col] if col in DASH else ""
        L.append(rf"\draw[fill=f{col},draw=b{col},line width=0.8pt{dash},rounded corners=1.5pt] "
                 rf"($(lg{i - 1}.east)+(0.6,-0.13)$) rectangle ++(0.45,0.26);")
        L.append(rf"\node[anchor=west,font=\scriptsize,text=black!75,inner sep=0pt] (lg{i}) at "
                 rf"($(lg{i - 1}.east)+(1.15,0)$) {{{lab}}};")
    L += [r"\end{tikzpicture}", r"\end{document}"]
    return "\n".join(L) + "\n"


def drawio():
    s = 40.0
    ox, oy = 0.6 * s, 1.8 * s

    def px(x, y):
        return ox + x * s, oy - y * s

    def plain(t):
        return (t.replace("\\textendash{}", "–").replace("\\,\\textbar\\,", " | ")
                .replace("\\textperiodcentered{}", "·").replace("\\\\", ", "))

    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    for i, (x0, y0, x1, y1, col, title) in enumerate(PANELS):
        f, b, t = C[col]
        X0, Y0 = px(x0, y0)
        X1, Y1 = px(x1, y1)
        cells.append(f'<mxCell id="p{i}" value="{html.escape(plain(title))}" style="rounded=1;arcSize=3;whiteSpace=wrap;'
                     f'html=1;fillColor=#{f};strokeColor=#{b};fontColor=#{t};fontStyle=1;fontSize=11;verticalAlign=top;'
                     f'align=left;spacingLeft=8;spacingTop=2;" vertex="1" parent="1"><mxGeometry x="{X0:.0f}" '
                     f'y="{Y0:.0f}" width="{X1 - X0:.0f}" height="{Y1 - Y0:.0f}" as="geometry"/></mxCell>')
    shape_style = {"cyl": "shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=7;",
                   "stack": "rounded=1;arcSize=6;shadow=1;", "box": "rounded=1;arcSize=6;",
                   "chev0": "shape=step;perimeter=stepPerimeter;fixedSize=1;size=14;",
                   "chev": "shape=step;perimeter=stepPerimeter;fixedSize=1;size=14;"}
    for nid, (shape, x, y, w, h, col, name, detail, badge) in N.items():
        f, b, t = C[col]
        cx, cy = px(x, y)
        label = html.escape(f"<b>{html.escape(name)}</b><br><font color=\"#555555\" style=\"font-size:9px\">"
                            f"{html.escape(plain(detail))}</font>")
        dash = DRAWIO_DASH.get(col, "")
        cells.append(f'<mxCell id="{nid}" value="{label}" style="{shape_style[shape]}whiteSpace=wrap;html=1;'
                     f'fillColor=#{f};strokeColor=#{b};fontColor=#{t};fontSize=11;strokeWidth=1.5;{dash}" vertex="1" '
                     f'parent="1"><mxGeometry x="{cx - w * s / 2:.0f}" y="{cy - h * s / 2:.0f}" width="{w * s:.0f}" '
                     f'height="{h * s:.0f}" as="geometry"/></mxCell>')
        if badge:
            cells.append(f'<mxCell id="b{nid}" value="{badge}" style="ellipse;whiteSpace=wrap;html=1;fillColor=#3A3A3A;'
                         f'strokeColor=none;fontColor=#FFFFFF;fontStyle=1;fontSize=9;" vertex="1" parent="1">'
                         f'<mxGeometry x="{cx - w * s / 2 - 8:.0f}" y="{cy - h * s / 2 - 8:.0f}" width="17" height="17" '
                         f'as="geometry"/></mxCell>')
    side = {"east": (1, 0.5), "west": (0, 0.5), "north": (0.5, 0), "south": (0.5, 1)}
    for i, (a, b, route, st) in enumerate(E):
        sa, aa = a.split("]")[-1].split(".")
        sb, ab = b.split(".")
        col = {"main": "4A4A4A", "gt": "3A3A3A", "notrun": "9A9A9A"}[st]
        dash = "dashed=1;" if st == "notrun" else ""
        (ex, ey), (nx, ny) = side[aa], side[ab]
        cells.append(f'<mxCell id="e{i}" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#{col};'
                     f'strokeWidth=1.5;{dash}endArrow=block;endFill=1;exitX={ex};exitY={ey};entryX={nx};entryY={ny};" '
                     f'edge="1" parent="1" source="{sa}" target="{sb}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    gx, gy = px(GT_NOTE[0], GT_NOTE[1])
    cells.append(f'<mxCell id="gtn" value="{html.escape(plain(GT_NOTE[2]))}" style="text;html=1;fontStyle=2;fontSize=9;'
                 f'fontColor=#555555;align=center;" vertex="1" parent="1"><mxGeometry x="{gx - 110:.0f}" y="{gy - 9:.0f}" '
                 f'width="220" height="18" as="geometry"/></mxCell>')
    x = 0.0
    for i, (col, lab) in enumerate(LEGEND):
        f, b, _t = C[col]
        lx, ly = px(x, LEGEND_Y)
        cells.append(f'<mxCell id="l{i}" value="{html.escape(lab)}" style="rounded=1;html=1;fillColor=#{f};'
                     f'strokeColor=#{b};{DRAWIO_DASH.get(col, "")}align=left;spacingLeft=6;fontSize=9;" '
                     f'vertex="1" parent="1"><mxGeometry x="{lx:.0f}" y="{ly - 7:.0f}" width="130" height="14" '
                     f'as="geometry"/></mxCell>')
        x += 1.0 + 0.16 * len(lab)
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
