"""Final defence deck: one research story built from the _v2 science and the original deck's storytelling.

Run from the repository root:  python phase4_v2/build/build_deck_final.py
Writes phase4_v2/DEFENSE_DECK_FINAL.pptx. Every number is read from phase4_v2/generated/numbers_v2.tex, the same
file the final paper prints from, so the deck and the paper cannot disagree. Charts are native PowerPoint charts
or native shapes positioned from those numbers; the only pictures are the architecture diagram (rendered from its
editable source, figures/fig_final_architecture.drawio / .tex) and the post hoc trade-off figure of the paper.
No stock or generated imagery is used.
"""
import os
import re

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = os.getcwd()
HERE = os.path.join(ROOT, "phase4_v2")
OUT = os.path.join(HERE, "DEFENSE_DECK_FINAL.pptx")

# ---------------------------------------------------------------- numbers (single source shared with the paper)
_NUM = {}
for m in re.finditer(r"\\csname V@(.+?)\\endcsname\{(.*)\}\s*$",
                     open(os.path.join(HERE, "generated", "numbers_v2.tex"), encoding="utf-8").read(), re.M):
    _NUM[m.group(1)] = m.group(2)


def V(key):
    if key not in _NUM:
        raise KeyError("number not in numbers_v2.tex: " + key)
    v = _NUM[key]
    v = v.replace(r"\textminus{}", "−").replace(r"\%", "%").replace(r"\,", " ").replace("~", " ")
    v = v.replace(r"\textless", "<").replace(r"\textgreater", ">").replace("{}", "")
    if "\\" in v:
        raise ValueError("untranslated LaTeX in " + key + ": " + v)
    return v


def F(key):
    """Numeric value of a macro (for positioning shapes and charts)."""
    return float(V(key).replace("−", "-").replace(",", "").replace("+", "").replace("%", ""))


def CI(key):
    lo, hi = V(key).strip("[]").split(",")
    return float(lo.replace("−", "-")), float(hi.replace("−", "-"))


# ---------------------------------------------------------------- design system
INK, MUTED, FAINT = "1B1B1B", "55544F", "8A8984"
NAVY, NAVY2 = "17213A", "26324F"
BLUE, VIOLET, ORANGE, GREEN, GREY = "2A78D6", "6250D6", "EB6834", "1BAF7A", "8A8984"
TINT = {BLUE: "EAF2FC", VIOLET: "F0EEFC", ORANGE: "FDEEE7", GREEN: "E6F6EF", GREY: "F3F3F1"}
HEAD, BODY = "Cambria", "Calibri"
STATUS = {  # text, colour
    "original": ("ORIGINAL STUDY · APPROVED DESIGN", BLUE),
    "confirmatory": ("ORIGINAL STUDY · CONFIRMATORY FAMILY", BLUE),
    "exploratory": ("EXPLORATORY", ORANGE),
    "registered": ("REGISTERED · OSF " + V("osf:osf_id"), GREEN),
    "advance": ("FIXED IN ADVANCE · NOT EXTERNALLY REGISTERED", VIOLET),
    "posthoc": ("POST HOC · DESCRIPTIVE", ORANGE),
    "wdp": ("EXPLORATORY · RETROSPECTIVE · NOT PREREGISTERED", ORANGE),
    "notrun": ("PLANNED, NOT RUN", GREY),
}

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
SW = 13.333
COUNTER = {"n": 0}


def rgb(h):
    return RGBColor.from_string(h)


def _font(run, size, color, bold=False, italic=False, face=BODY):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = face
    run.font.color.rgb = rgb(color)


def text(slide, x, y, w, h, content, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT, face=BODY,
         anchor=MSO_ANCHOR.TOP, italic=False, name=None, spacing=4):
    """content: str, or list of paragraphs; a paragraph is str or list of (text, {opts}) runs."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    paras = content if isinstance(content, list) else [content]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(spacing)
        runs = para if isinstance(para, list) else [(para, {})]
        for t, o in runs:
            r = p.add_run()
            r.text = t
            _font(r, o.get("size", size), o.get("color", color), o.get("bold", bold), o.get("italic", italic),
                  o.get("face", face))
    return tb


def bullets(slide, x, y, w, h, items, size=16, color=INK, gap=8):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(Emu(Inches(0.25))))
        pPr.set("indent", str(-Emu(Inches(0.25))))
        bu = pPr.makeelement(qn("a:buChar"), {"char": "•"})
        pPr.append(bu)
        runs = it if isinstance(it, list) else [(it, {})]
        for t, o in runs:
            r = p.add_run()
            r.text = t
            _font(r, o.get("size", size), o.get("color", color), o.get("bold", False), o.get("italic", False))
    return tb


def box(slide, x, y, w, h, fill, line=None, content=None, size=14, color=INK, bold=False, align=PP_ALIGN.CENTER,
        dash=None, radius=0.08, anchor=MSO_ANCHOR.MIDDLE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, name=None, lw=1.25):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        s.name = name
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    if fill:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(lw)
        if dash:
            s.line.dash_style = dash
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    tf = s.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.1)
    tf.margin_top = tf.margin_bottom = Inches(0.05)
    tf.vertical_anchor = anchor
    if content is not None:
        paras = content if isinstance(content, list) else [content]
        for i, para in enumerate(paras):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            runs = para if isinstance(para, list) else [(para, {})]
            for t, o in runs:
                r = p.add_run()
                r.text = t
                _font(r, o.get("size", size), o.get("color", color), o.get("bold", bold), o.get("italic", False))
    return s


def arrow(slide, x1, y1, x2, y2, color=MUTED, width=1.75, dash=None):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(width)
    if dash:
        c.line.dash_style = dash
    ln = c.line._get_or_add_ln()
    ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    return c


def line(slide, x1, y1, x2, y2, color=FAINT, width=1.0, dash=None):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = rgb(color)
    c.line.width = Pt(width)
    if dash:
        c.line.dash_style = dash
    return c


def picture(slide, path, x, y, w=None, h=None, alt=""):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    p = slide.shapes.add_picture(path, Inches(x), Inches(y), **kw)
    p._element.nvPicPr.cNvPr.set("descr", alt)
    return p


def notes(slide, t):
    slide.notes_slide.notes_text_frame.text = t.strip()


def new_slide(title, status=None, act=None, dark=False, backup=None):
    COUNTER["n"] += 1
    s = prs.slides.add_slide(BLANK)
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = rgb(NAVY if dark else "FFFFFF")
    tc = "FFFFFF" if dark else INK
    if title:
        text(s, 0.6, 0.42, 10.0 if status else 12.1, 1.05, title, size=28, color=tc, bold=True, face=HEAD,
             anchor=MSO_ANCHOR.TOP, name="Title")
    if act:
        text(s, 0.6, 0.16, 8, 0.25, act.upper(), size=11, color=FAINT if not dark else "B8BCC8", bold=True)
    if status:
        lab, col = STATUS[status]
        box(s, 10.75, 0.2, 2.05, 0.66, TINT[col], col, lab, size=10, color=col, bold=True, radius=0.3,
            name="Evidence status")
    foot = ("Backup " + backup + "  ·  " if backup else "") + "Ahmed & Ilyas · FAST-NUCES Islamabad"
    text(s, 0.6, 7.05, 8, 0.25, foot, size=10, color="B8BCC8" if dark else FAINT)
    text(s, 12.2, 7.05, 0.55, 0.25, str(COUNTER["n"]), size=10, color="B8BCC8" if dark else FAINT, align=PP_ALIGN.RIGHT)
    return s


def forest(slide, x, y, w, rows, xmin, xmax, ticks, row_h=0.42, label_w=2.6, title=None):
    """Dot-and-whisker from numbers: rows = [(label, est, lo, hi, colour, hollow)]."""
    px0, pw = x + label_w, w - label_w - 0.7
    if title:
        text(slide, x, y - 0.42, w, 0.35, title, size=13, color=INK, bold=True)

    def X(v):
        return px0 + (v - xmin) / (xmax - xmin) * pw
    yb = y + row_h * len(rows)
    for t in ticks:
        line(slide, X(t), y - 0.05, X(t), yb, color="E4E3DF" if t != 0 else MUTED, width=0.75 if t != 0 else 1.25)
        text(slide, X(t) - 0.4, yb + 0.05, 0.8, 0.25, ("%+.2f" % t).replace("-", "−") if t else "0",
             size=11, color=MUTED, align=PP_ALIGN.CENTER)
    for i, (lab, est, lo, hi, col, hollow) in enumerate(rows):
        cy = y + row_h * i + row_h / 2
        text(slide, x, cy - 0.15, label_w - 0.1, 0.3, lab, size=12, color=INK, anchor=MSO_ANCHOR.MIDDLE)
        line(slide, X(lo), cy, X(hi), cy, color=col, width=3)
        d = 0.16
        dot = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(X(est) - d / 2), Inches(cy - d / 2), Inches(d), Inches(d))
        dot.fill.solid()
        dot.fill.fore_color.rgb = rgb("FFFFFF" if hollow else col)
        dot.line.color.rgb = rgb(col)
        dot.line.width = Pt(2)
        dot.shadow.inherit = False
        text(slide, X(hi) + 0.08, cy - 0.14, 0.75, 0.28, ("%+.3f" % est).replace("-", "−"), size=11, color=INK)
    return yb


def bar_chart(slide, x, y, w, h, cats, series, colors, number_format="0", max_v=None, horizontal=True,
              legend=False, gap=60, label_size=12):
    cd = CategoryChartData()
    cd.categories = cats
    for name, vals in series:
        cd.add_series(name, vals)
    kind = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
    gf = slide.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    ch = gf.chart
    ch.has_title = False
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.TOP
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(12)
        ch.legend.font.name = BODY
    ch.font.name = BODY
    ch.font.size = Pt(12)
    ch.font.color.rgb = rgb(MUTED)
    plot = ch.plots[0]
    plot.gap_width = gap
    plot.overlap = -10 if len(series) > 1 else 0
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format = number_format
    dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size = Pt(label_size)
    dl.font.color.rgb = rgb(INK)
    for s, c in zip(plot.series, colors):
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = rgb(c)
    va = ch.value_axis
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb("E4E3DF")
    va.format.line.fill.background()
    va.tick_labels.font.size = Pt(11)
    if max_v is not None:
        va.maximum_scale = max_v
        va.minimum_scale = 0
    ca = ch.category_axis
    ca.tick_labels.font.size = Pt(12)
    ca.tick_labels.font.color.rgb = rgb(INK)
    ca.format.line.color.rgb = rgb(MUTED)
    if horizontal:
        ca.reverse_order = True
    return gf


ARCH_PNG = os.path.join(HERE, "figures", "fig_final_architecture.png")
TRADE_PNG = os.path.join(HERE, "figures", "fig_tradeoff_rates.png")

# =============================================================== ACT 1 - THE PROBLEM
s = new_slide(None, dark=True)
text(s, 0.9, 1.35, 11.5, 0.4, "ADVANCED ARTIFICIAL INTELLIGENCE · PHASE 3 AND 4 DEFENCE", size=13, color="B8BCC8", bold=True)
text(s, 0.9, 1.9, 11.6, 1.9, "Program fault or test fault?", size=48, color="FFFFFF", bold=True, face=HEAD)
text(s, 0.9, 2.95, 11.6, 1.2, "LLM triage of failing generated unit tests, and a registered test of mutation evidence",
     size=24, color="DCE3F0", face=HEAD)
text(s, 0.9, 4.6, 11.0, 0.9, [[("Hafiz Huzaifa Ahmed · Saad Ilyas", {"bold": True, "color": "FFFFFF", "size": 18})],
                              [("Department of Artificial Intelligence & Data Science, School of Computing, FAST-NUCES", {"color": "B8BCC8", "size": 15})]])
text(s, 0.9, 5.85, 11.6, 0.6, "Registered confirmation: OSF " + V("osf:osf_id") + " (" + V("osf:registered_utc") +
     ")  ·  every number from committed analysis outputs", size=13, color="B8BCC8")
notes(s, """
Good morning. When a language model writes a unit test and the test fails, one of two things is true: either the test is wrong, or the program has a bug. We asked whether an AI judge can tell which, and we checked its answers against the truth that comes from running the code.

The talk has two halves. The first half is the study we proposed in Phase 2 and ran in Phase 3: how accurate are LLM judges, does documentation help them, and is multi-agent debate worth its cost. The second half is what those results led us to: a registered confirmation of a mutation-based signal, and one exploratory follow-up. I will tell you, slide by slide, which result is confirmatory, which is registered, and which is exploratory.

Transition: let me start with one concrete failing test.
""")

s = new_slide("A failing test can be the only evidence of a bug", "original", act="Act 1 · The problem")
box(s, 0.6, 1.75, 5.9, 1.75, "F7F7F5", "D9D8D3", [
    [("Generated test for JFreeChart  ", {"bold": True, "size": 15}), ("DefaultKeyedValues.removeValue", {"size": 14, "face": "Consolas"})],
    [("1. add keys A and B", {"size": 15})],
    [("2. removeValue(\"B\")", {"size": 15})],
    [("3. expect one item to remain", {"size": 15})]], align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
box(s, 7.0, 1.75, 2.75, 1.0, TINT[ORANGE], ORANGE, [[("Buggy version", {"bold": True})], [("fails: 2 items remain", {})]], size=14)
box(s, 10.05, 1.75, 2.7, 1.0, TINT[GREEN], GREEN, [[("Fixed version", {"bold": True})], [("same test passes", {})]], size=14)
arrow(s, 9.75, 2.25, 10.05, 2.25)
text(s, 7.0, 3.0, 5.75, 1.1, "Execution label: PROGRAM FAULT. The test is right; the program is wrong.", size=15, color=INK, bold=True)
box(s, 0.6, 4.5, 12.15, 1.55, TINT[ORANGE], None, [
    [("What a repair-first generator does: ", {"bold": True, "size": 17}),
     ("rewrite the failing assertion to the observed value (expect 2) or delete the test. ", {"size": 17}),
     ("The only evidence of the bug disappears.", {"size": 17, "bold": True, "color": "B5441A"})]],
    align=PP_ALIGN.LEFT)
text(s, 0.6, 6.3, 12.1, 0.5, "TestART, ChatAssert and TaRGET all repair toward the observed behaviour; they presume the program is correct.",
     size=13, color=MUTED, italic=True)
notes(s, """
This is a real test from our data, for JFreeChart (Defects4J bug Chart 18). The test adds two keys, removes one, and expects one item to remain. On the buggy version it fails, because the method leaves two items. On the developer's fixed version the same test passes. So the test was right and the program was wrong: a program fault.

Now think about what most LLM test generators do with a failing test. TestART rewrites the assertion to whatever the program returned. ChatAssert and TaRGET also repair toward the observed behaviour. All of them assume the test is wrong. Here that would turn a bug-revealing test into one that asserts the bug.

Emphasise: a failing test is not necessarily a wrong test. That single sentence is the whole motivation.

Transition: how often does this happen? Rarely, and that is exactly why it is hard.
""")

s = new_slide("Bug-revealing failures are needles in a haystack", "original", act="Act 1 · The problem")
text(s, 0.6, 1.95, 4.1, 1.0, V("cit:zhao lo") + "–" + V("cit:zhao hi") + "%", size=40, color=BLUE, bold=True, face=HEAD)
text(s, 0.6, 3.0, 3.9, 1.3, "of tests generated from buggy Defects4J code reveal the bug (Zhao et al., six models; published figure)", size=14, color=MUTED)
text(s, 4.9, 1.8, 3.6, 1.2, V("zhao:subsets:all_D1:share_effective_pct@2") + "%", size=54, color=BLUE, bold=True, face=HEAD)
text(s, 4.9, 3.0, 3.6, 1.3, "of the " + V("ds1:executed_methods") + " test methods our generator wrote reveal the bug (measured here)", size=14, color=MUTED)
text(s, 9.0, 1.8, 3.8, 1.2, V("der:d1 test PF labelled") + " : " + V("der:d1 test TF labelled"), size=54, color=ORANGE, bold=True, face=HEAD)
text(s, 9.0, 3.0, 3.8, 1.3, "bug-revealing vs wrong failing tests on the held-out split", size=14, color=MUTED)
box(s, 0.6, 4.75, 12.15, 1.45, "F7F7F5", None, [[
    ("Why this matters: ", {"bold": True, "size": 17}),
    ("a filter can look accurate while throwing away most of the few bug-revealing tests. So this study counts ", {"size": 17}),
    ("lost bug-revealing tests and lost bugs", {"bold": True, "size": 17}),
    (" as outcomes, not only accuracy.", {"size": 17})]], align=PP_ALIGN.LEFT)
notes(s, """
Bug-revealing failures are rare. Zhao et al. found that only about two to four and a half percent of tests generated from buggy Defects4J code fail on the buggy version and pass on the fixed one. Our own generator gives 1.94 percent, inside their range. On our held-out split, 60 failing tests are bug-revealing and 296 are wrong tests.

So triage is a needle-in-a-haystack problem. If you keep everything you drown in false alarms; if you discard everything you lose every bug. That is why the paper reports lost bug-revealing tests and lost bugs next to F1.

Plain-language point: accuracy alone flatters a filter that says "wrong test" every time, because that is right more than 80 percent of the time here.

Transition: what did earlier work leave open?
""")

# =============================================================== ACT 2 - GAPS AND QUESTIONS
s = new_slide("Three gaps carried forward from the literature review", "original", act="Act 2 · Research gap and objectives")
gaps = [("G1", "Ground truth", "Triage accuracy has been reported as a precision or a small manual audit, never against buggy/fixed ground truth on repository-level Java, and never as lost bug-revealing tests."),
        ("G2", "Specification", "Triage errors are blamed on missing documentation, but no study varies the specification given to the judge while keeping the failing test fixed."),
        ("G3", "Equal budget", "Multi-agent gains are reported without matching the budget; self-consistency, the natural equal-cost comparator, has not been applied to triage.")]
for i, (g, head, body) in enumerate(gaps):
    x = 0.6 + i * 4.1
    box(s, x, 1.8, 3.85, 4.6, TINT[BLUE], None, None)
    text(s, x + 0.25, 2.0, 3.4, 0.8, g, size=36, color=BLUE, bold=True, face=HEAD)
    text(s, x + 0.25, 2.85, 3.4, 0.5, head, size=19, color=INK, bold=True)
    text(s, x + 0.25, 3.45, 3.35, 2.9, body, size=15, color=INK)
text(s, 0.6, 6.55, 12.1, 0.4, "JSTestCraft (vote, audited recall), JavaOracle (debate, precision), Meta (rules) are the closest triage studies.", size=13, color=MUTED, italic=True)
notes(s, """
Our Phase 1 review left three gaps, and the Phase 2 design addressed each one.

G1: nobody had scored LLM triage against the truth that comes from running a test on the buggy and the fixed program. JSTestCraft estimated recall from a manual audit; JavaOracle reported precision only.

G2: papers blame triage errors on missing documentation, but no one had varied the documentation while holding the test and its label fixed.

G3: multi-agent systems are compared with single agents that get fewer calls. The fair comparator is self-consistency: the same model sampled the same number of times.

Transition: each gap became one research question.
""")

s = new_slide("Three approved questions, and three the results led to", "original", act="Act 2 · Research gap and objectives")
rqs = [("RQ1", "G1", "How accurate is LLM triage against buggy/fixed labels, and how many bug-revealing tests does it keep vs discard-all and a rule?", "H1", BLUE),
       ("RQ2", "G2", "Does Javadoc (S1) or an inferred specification (S2) change precision and recall?", "H2a, H2b", BLUE),
       ("RQ3", "G3", "At an equal budget, does debate beat self-consistency, and both a one-shot judge?", "H3a, H3b", BLUE),
       ("RQ4", "later", "How far do judge-only rules go; what is the strongest keep-heavy baseline?", "fixed in advance", VIOLET),
       ("RQ5", "later", "Do single-edit mutation outcomes separate bug-revealing from wrong tests?", "registered C1, C2", GREEN),
       ("RQ6", "later", "Do rules built on them improve a base rule without losing bugs?", "registered C3, C4", GREEN)]
text(s, 0.6, 1.62, 6, 0.35, "Approved Phase 2 design (one Holm family of five)", size=13, color=BLUE, bold=True)
text(s, 0.6, 4.25, 8, 0.35, "Added after RQ1–RQ3, each with its own evidence status", size=13, color=VIOLET, bold=True)
for i, (rq, g, q, h, col) in enumerate(rqs):
    y = 2.0 + i * 0.77 + (0.33 if i >= 3 else 0)
    box(s, 0.6, y, 1.0, 0.62, col, None, rq, size=16, color="FFFFFF", bold=True)
    text(s, 1.8, y + 0.04, 8.4, 0.62, q, size=15, color=INK, anchor=MSO_ANCHOR.MIDDLE)
    box(s, 10.4, y + 0.08, 2.35, 0.46, TINT[col], col, h, size=12, color=col, bold=True, radius=0.3)
notes(s, """
The approved design had three questions, one per gap, with five confirmatory hypotheses tested as one Holm-corrected family.

RQ1 is accuracy against ground truth. RQ2 is the specification factor: S0 is signature only, S1 adds Javadoc, S2 adds an inferred specification. RQ3 is debate against self-consistency at the same five calls.

The bottom three came later, and I want to be clear about that. RQ4 grew out of the RQ1 results; its hypotheses were written into our decision log before their data, which is internal provenance, not a public registration. RQ5 and RQ6 were registered on OSF before any of their data existed.

Transition: before any judge, we need the truth. Here is how we got it.
""")

# =============================================================== ACT 3 - METHODOLOGY
s = new_slide("Ground truth comes from running the code, not from an opinion", "original", act="Act 3 · Proposed methodology")
hdr = ["On buggy version", "On fixed version", "Label", "Use"]
rows = [("fails", "passes", "PF · program fault", "positive class", GREEN),
        ("fails", "fails identically", "TF · test fault", "negative class", ORANGE),
        ("fails", "fails differently", "AMB", "sensitivity only", GREY),
        ("flaky, timeout, env., no compile", "—", "excluded", "—", GREY)]
xs, ws = [0.6, 3.75, 6.9, 9.95], [3.0, 3.0, 2.9, 2.8]
for j, hname in enumerate(hdr):
    text(s, xs[j] + 0.1, 1.75, ws[j], 0.35, hname, size=14, color=MUTED, bold=True)
for i, (b, f, lab, use, col) in enumerate(rows):
    y = 2.2 + i * 0.72
    for j, val in enumerate([b, f]):
        box(s, xs[j], y, ws[j], 0.58, "F7F7F5", None, val, size=15, align=PP_ALIGN.LEFT)
    box(s, xs[2], y, ws[2], 0.58, TINT[col], col, lab, size=15, bold=True, color=INK, align=PP_ALIGN.LEFT)
    box(s, xs[3], y, ws[3], 0.58, None, None, use, size=15, color=MUTED, align=PP_ALIGN.LEFT)
bullets(s, 0.6, 5.3, 12.1, 1.5, [
    "Each test compiled against both versions and run 3 times on each, every run in a fresh JVM; deterministic outcomes only.",
    "Labels are computed before any judge runs and stored where no judge can read them: no LLM and no person in the labelling.",
    [("Caveat: ", {"bold": True}), ("the fixed version is an operational reference, not proof of correctness; a test revealing a second fault is labelled TF.", {})]],
    size=15)
notes(s, """
This is the ground-truth rule from Phase 2, implemented unchanged. A failing test that passes on the developer's fixed version is a program fault: the fix changed exactly the code the test was complaining about. A test that fails the same way on the fixed version is a test fault. Failing differently on both is ambiguous, and we keep it out of the main analysis.

Every test runs three times on each version in a fresh JVM, and flaky or timed-out tests are excluded. The labels are written before any judge runs and are stored where the judging code cannot read them, so there is no circular scoring.

Limitation to acknowledge if asked: the fixed version is a reference, not proof that the program is now correct. A test that reveals a different, unfixed bug fails on both versions and is labelled a test fault. Our two-rater audit agreed with the execution label 97 percent of the time on the development split.

Transition: this rule sits inside a nine-stage pipeline.
""")

s = new_slide("The pipeline as executed, including what did not run", None, act="Act 3 · Proposed methodology")
picture(s, ARCH_PNG, 1.2, 1.5, w=10.95, alt="As-implemented research architecture: the approved Phase 2 pipeline (executed), the ground-truth channel, later investigations, and planned components that were not run.")
text(s, 0.6, 6.45, 12.1, 0.45, "Also planned and not run: prompt paraphrases (E5-R4) and the audit of inferred specifications. Editable source: figures/fig_final_architecture.drawio",
     size=13, color=MUTED, italic=True)
notes(s, """
This is the architecture as it actually ran, drawn from an editable diagram source. Read the top row left to right.

The blue row is the approved Phase 2 design: Defects4J real and seeded faults, test generation with Gemma 4 26B from the buggy code, running every test on both versions, an evidence package that varies only the specification, the triage arms with the 9B Qwen judge, and evaluation.

The green path is the ground truth: it leaves at execution and joins only at evaluation; no model ever sees it.

The violet row was added later, in the order we ran it: judge-only rules, then mutation probes, then the registered confirmation, then the whole-method check.

Be explicit about the grey box: GitBug-Java (D3) was planned but not run, because its build reproduction needs Docker. The prompt-paraphrase robustness test was also not run, and the planned audit of inferred specifications was not done, as the line under the diagram says. We do not claim anything that would need them.

Transition: the one factor we manipulate inside the evidence is the specification.
""")

s = new_slide("Same evidence, three specification levels", "original", act="Act 3 · Proposed methodology")
lv = [("S0", "signature, test code, failure (message, failing line, stack frames)", 12.1),
      ("S1", "S0 + Javadoc of the buggy version", 9.6),
      ("S2", "S1 + specification inferred once per method (fix lines removed)", 7.1)]
for i, (lab, desc, w) in enumerate(reversed(lv)):
    pass
box(s, 0.6, 1.75, 12.15, 3.75, TINT[BLUE], BLUE, None)
box(s, 0.9, 2.55, 11.55, 2.75, "FFFFFF", BLUE, None)
box(s, 1.2, 3.35, 10.95, 1.75, TINT[BLUE], BLUE, None)
text(s, 0.85, 1.85, 11.6, 0.6, [[("S2  ", {"bold": True, "color": BLUE, "size": 20}), ("adds a specification inferred once per focal method from signature, Javadoc and call sites, with lines changed by the fix removed", {"size": 15})]])
text(s, 1.15, 2.65, 11.1, 0.6, [[("S1  ", {"bold": True, "color": BLUE, "size": 20}), ("adds the Javadoc of the buggy version", {"size": 15})]])
text(s, 1.45, 3.45, 10.5, 1.6, [[("S0  ", {"bold": True, "color": BLUE, "size": 20}), ("test lines [T], failure [F1–F4]: outcome, message with expected/actual values, failing line, stack frames; interface signatures [Sig]", {"size": 15})],
                                 [("Never shown: the focal implementation, the fixed version, the patch, developer tests, bug ids.", {"size": 14, "italic": True, "color": MUTED})]])
bullets(s, 0.6, 5.75, 12.1, 1.1, ["The test, its failure and its label stay fixed; only the specification section changes, so any difference is attributable to it.",
                                  "A leakage guard blocks a call whose package contains a forbidden string (bug id, fixed-only line, focal-body line)."], size=15)
notes(s, """
The evidence package is the same for every arm. Every item has an identifier the judge must cite, for example F2 is the failure message with the expected and actual values.

The three levels are nested. S0 gives the test, the failure and the signatures. S1 adds the Javadoc of the buggy version. S2 adds a specification that a model inferred once per method, with any line the fix changed removed.

Because the test and its label do not change, any change in accuracy across levels comes from the specification. A leakage guard checks every package and blocks a call if it would leak the fix or the bug id.

Transition: now the arms that read this package, including our proposed debate.
""")

s = new_slide("Proposed framework: adversarial debate at an equal budget of five calls", "original", act="Act 3 · Proposed methodology")
box(s, 0.6, 1.85, 2.4, 1.0, "F7F7F5", "D9D8D3", "Evidence package", size=15, bold=True)
box(s, 3.6, 1.6, 2.7, 0.8, TINT[GREEN], GREEN, "Advocate P · round 1", size=14, bold=True)
box(s, 3.6, 2.6, 2.7, 0.8, TINT[ORANGE], ORANGE, "Advocate T · round 1", size=14, bold=True)
box(s, 6.9, 1.6, 2.6, 0.8, TINT[GREEN], GREEN, "P rebuts T · round 2", size=14)
box(s, 6.9, 2.6, 2.6, 0.8, TINT[ORANGE], ORANGE, "T rebuts P · round 2", size=14)
box(s, 10.1, 1.85, 2.65, 1.3, TINT[BLUE], BLUE, [[("Adjudicator", {"bold": True})], [("anonymised, random order; cites evidence ids", {"size": 12})]], size=14)
arrow(s, 3.0, 2.35, 3.6, 2.0); arrow(s, 3.0, 2.35, 3.6, 3.0)
arrow(s, 6.3, 2.0, 6.9, 2.0); arrow(s, 6.3, 3.0, 6.9, 3.0)
line(s, 6.3, 2.0, 6.9, 3.0, color=FAINT, dash=MSO_LINE_DASH_STYLE.DASH); line(s, 6.3, 3.0, 6.9, 2.0, color=FAINT, dash=MSO_LINE_DASH_STYLE.DASH)
arrow(s, 9.5, 2.0, 10.1, 2.35); arrow(s, 9.5, 3.0, 10.1, 2.75)
text(s, 0.6, 3.65, 12, 0.35, "Compared at the same model, decoding and evidence:", size=15, color=INK, bold=True)
arms = [("DA", "0", "discard every failing test"), ("KA", "0", "keep every failing test"), ("R0", "0", "rule on failure type and deepest frame"),
        ("J1", "1", "one neutral judgement"), ("SC", "5", "majority of 5 samples (self-consistency)"),
        ("SC-T", "5", "token-matched self-consistency"), ("DEB", "5", "the debate above")]
for i, (a, c, d) in enumerate(arms):
    col, row = i % 2, i // 2
    x, y = 0.6 + col * 6.15, 4.15 + row * 0.62
    box(s, x, y, 0.95, 0.5, BLUE if a == "DEB" else "F7F7F5", None, a, size=14, bold=True, color="FFFFFF" if a == "DEB" else INK)
    text(s, x + 1.1, y + 0.08, 4.9, 0.4, [[(c + " calls  ", {"bold": True, "color": MUTED}), (d, {})]], size=14)
notes(s, """
This is the framework we proposed in Phase 2. Two advocates argue opposite sides. Advocate P argues that the program is at fault; Advocate T argues that the test is wrong. In round 1 they argue independently, so neither copies the other. In round 2 each rebuts the other. Then an adjudicator decides, seeing the arguments anonymised as Analyst X and Y in a random order, and must cite evidence identifiers. That is exactly five calls.

Why adversarial roles? Repair-first tools carry a prior that the test is wrong. Assigning one advocate to the program-fault side forces that case to be argued for every failure.

The key design choice is the budget: self-consistency also gets five calls of the same model, and SC-T matches the tokens debate consumes. So if debate wins, it is the method, not more compute. J1 shows what any extra budget buys. DA, KA and R0 are the zero-cost baselines.

Transition: that was the plan. Here is what changed when we implemented it.
""")

# =============================================================== ACT 4 - IMPLEMENTATION AND EXPERIMENTS
s = new_slide("Implementation: what changed from the approved plan, and why", "original", act="Act 4 · Implementation and experiments")
chg = [("API judges (DeepSeek-V3, Qwen3) and GPT-4.1 generator", "local open-weight models: Gemma 4 26B generator, Qwen3.5 9B judge M1, Gemma 4 12B M2", "zero API spend (authors, D-21)"),
       ("Zhao et al.'s frame, 318 methods / 233 defects", "frame rebuilt by re-running their rule: " + V("split:frame_methods") + " / " + V("split:frame_bugs") + "; " + V("split:sampled_methods") + " after the cap", "their final list is not distributed"),
       ("Docker image", "WSL2 with a recorded environment manifest", "Docker unavailable"),
       ("D3 GitBug-Java; prompt paraphrases (E5-R4)", "not run", "Docker needed; Tier 3 cut for time"),
       ("Judge passes its development gate", "M1 failed it (F1 " + V("devgate:G_d_detail:J1_f1") + " vs R0 " + V("devgate:G_d_detail:R0_f1") + "); kept under the fixed fallback rule", "no pipeline defect found (D-48–D-52)")]
for j, hname in enumerate(["Phase 2 plan", "Executed", "Reason"]):
    text(s, [0.6, 4.6, 9.4][j], 1.65, [3.8, 4.6, 3.35][j], 0.35, hname, size=14, color=MUTED, bold=True)
for i, (a, b, c) in enumerate(chg):
    y = 2.05 + i * 0.86
    box(s, 0.6, y, 3.85, 0.76, "F7F7F5", None, a, size=13, align=PP_ALIGN.LEFT)
    box(s, 4.6, y, 4.65, 0.76, TINT[GREY if "not run" == b else BLUE], None, b, size=13, align=PP_ALIGN.LEFT,
        color=MUTED if b == "not run" else INK, bold=(b == "not run"))
    box(s, 9.4, y, 3.35, 0.76, None, None, c, size=13, color=MUTED, align=PP_ALIGN.LEFT)
text(s, 0.6, 6.45, 12.1, 0.45, "No question, hypothesis, endpoint or decision rule changed. The instructor gave no comments on the Phase 2 presentation, so nothing changed for feedback.",
     size=13, color=MUTED, italic=True)
notes(s, """
Implementation followed the approved design, with five changes that I want to state openly.

First, models: we planned API models and moved to locally served open-weight models, so the study cost nothing in API fees. The consequence is smaller judges, so our results describe locally deployable models.

Second, the sampling frame: Zhao et al. do not distribute their final method list, so we re-ran their selection rule: 312 methods instead of 318.

Third, Docker was not available, so we ran under WSL2 with a recorded environment manifest. For the same reason the external benchmark D3 was not run, and the prompt-paraphrase experiment was dropped with Tier 3 for time.

Fourth, and most important: our main judge failed its own development gate: on the pilot its F1 did not beat the rule baseline. The fallback ladder was fixed in advance; an audit found no pipeline defect; we kept the judge and report the failure. So null results describe a weak judge, not the methods in general.

If asked about instructor feedback: the instructor gave no comments on our Phase 2 presentation, so every change on this slide has a technical or design reason.

Transition: here is how the data flowed.
""")

s = new_slide("From " + V("split:sampled_methods") + " focal methods to " + V("sum:leakage_abort_exclusions:n_per_level:S1") + " judged failures", "original", act="Act 4 · Implementation and experiments")
flow = [(V("split:sampled_methods"), "focal methods (" + V("split:sampled_bugs") + " defects, 17 projects)"),
        (V("ds1:executed_methods"), "generated test methods executed on both versions"),
        (V("der:d1 test PF labelled") + " PF / " + V("der:d1 test TF labelled") + " TF", "labelled failures on the held-out split (" + V("der:n test projects") + " projects)"),
        (V("sum:prevalence:judged_sample_prevalence_by_dataset:D1:PF") + " + " + V("sum:prevalence:judged_sample_prevalence_by_dataset:D1:TF"), "judged sample: every PF, TF sampled 1:2 by project"),
        (V("sum:leakage_abort_exclusions:n_per_level:S1"), "scored at S1 after " + V("sum:leakage_abort_exclusions:counts_labelled:S1|full:instances") + " leakage aborts")]
for i, (num, lab) in enumerate(flow):
    y = 1.75 + i * 0.95
    w = 4.4 - i * 0.4
    box(s, 0.6, y, w, 0.78, BLUE if i == 4 else TINT[BLUE], None, num, size=22, bold=True, color="FFFFFF" if i == 4 else BLUE)
    text(s, 0.6 + w + 0.25, y + 0.05, 8.6 - (0.6 + w + 0.25), 0.7, lab, size=15, color=INK, anchor=MSO_ANCHOR.MIDDLE)
box(s, 9.0, 1.75, 3.75, 2.25, TINT[BLUE], None, [[("D2 seeded faults", {"bold": True, "size": 16})],
    [(V("d2rep:before_cap:d2_units_total") + " killed mutants, " + V("d2:DEB|S1:n_instances") + " scored", {"size": 14})],
    [("contamination control: new faults in the same methods", {"size": 13, "color": MUTED})]], align=PP_ALIGN.LEFT)
notes(s, """
The funnel. 234 focal methods after the per-project cap, from 167 defects. The generator wrote 2,909 test methods that we executed on both versions. On the held-out split that gave 60 bug-revealing and 296 wrong failing tests. We kept every bug-revealing test and sampled the wrong tests two to one, stratified by project, and stored inverse-probability weights. Four instances were blocked by the leakage guard, leaving 177 scored failures.

Say the honest number: the 60 bug-revealing tests come from only 22 bugs, so bug-level claims rest on 22 clusters.

D2 is the contamination control: one mutant inside a held-out method's fixed version. The model cannot have memorised these faults.

Transition: first result.
""")

s = new_slide("E1: the best judge barely beats keeping every failing test, and still loses half the bugs", "confirmatory", act="Act 4 · Implementation and experiments")
text(s, 0.6, 1.75, 3.3, 1.0, V("d1:DEB|S1:f1"), size=50, color=BLUE, bold=True, face=HEAD)
text(s, 0.6, 2.75, 3.3, 0.6, "F1 of debate (best arm)", size=14, color=MUTED)
text(s, 0.6, 3.35, 3.3, 1.0, V("d1:KA:f1"), size=50, color=MUTED, bold=True, face=HEAD)
text(s, 0.6, 4.35, 3.3, 0.6, "F1 of keeping everything", size=14, color=MUTED)
text(s, 0.6, 5.05, 3.4, 1.5, [[("MCC " + V("d1:DEB|S1:mcc") + " " + V("d1:DEB|S1:mcc_ci95"), {"bold": True, "size": 16})],
                              [("vs 0 for keep-all: a weak but real signal", {"size": 14, "color": MUTED})]])
cats = ["Discard-all", "Rule R0", "Self-consistency", "Token-matched SC", "One-shot J1", "Debate", "Keep-all"]
vals = [F("d1:DA:pf_lost"), F("d1:R0:pf_lost"), F("d1:SC|S1:pf_lost@1"), F("d1:SC-T|S1:pf_lost@1"), F("d1:J1|S1:pf_lost@1"), F("d1:DEB|S1:pf_lost@1"), F("d1:KA:pf_lost")]
text(s, 4.4, 1.62, 8.3, 0.35, "Bug-revealing tests lost, of " + V("sum:prevalence:PF") + " (mean of 3 replicates)", size=14, color=INK, bold=True)
bar_chart(s, 4.3, 1.95, 8.45, 4.8, cats, [("PF tests lost", vals)], [ORANGE], number_format="0.0", max_v=66)
notes(s, """
On F1, the best arm, debate, reaches 0.511. Keeping every failing test reaches 0.506. On F1 alone the judges look useless, which is why we report MCC: keep-all scores exactly zero on MCC, and debate 0.267 with an interval that excludes zero. So there is a signal, but a weak one.

The chart is the cost that matters to a developer: out of 60 bug-revealing tests, discard-all loses all 60, the rule loses 45, self-consistency 36, debate 30. Every LLM arm throws away about half of the real bug evidence.

H1, the one-shot judge against the rule, was inconclusive after Holm correction (p 0.233).

Transition: did documentation or debate help?
""")

s = new_slide("E2 and E3: no detectable gain from documentation or from debate", "confirmatory", act="Act 4 · Implementation and experiments")
hyp = [("H1", "J1 vs rule R0", "H1"), ("H2a", "Javadoc: S1 vs S0", "H2a"), ("H2b", "Inferred spec: S2 vs S1", "H2b"),
       ("H3a", "Debate vs self-consistency (5 calls each)", "H3a"), ("H3b", "Self-consistency vs one-shot", "H3b")]
for j, hname in enumerate(["", "Contrast", "ΔF1", "95% CI", "p (Holm)", "Verdict"]):
    text(s, [0.6, 1.5, 6.3, 7.6, 9.6, 10.95][j], 1.7, 2.5, 0.35, hname, size=14, color=MUTED, bold=True)
for i, (h, c, k) in enumerate(hyp):
    y = 2.1 + i * 0.66
    box(s, 0.6, y, 0.75, 0.52, BLUE, None, h, size=14, bold=True, color="FFFFFF")
    text(s, 1.5, y + 0.11, 4.7, 0.4, c, size=15)
    text(s, 6.3, y + 0.11, 1.2, 0.4, V("conf:f1:" + k + ":delta"), size=15, bold=True)
    text(s, 7.6, y + 0.11, 2.0, 0.4, V("conf:f1:" + k + ":ci95"), size=15)
    text(s, 9.6, y + 0.11, 1.2, 0.4, V("conf:f1:" + k + ":p_holm"), size=15)
    box(s, 10.95, y + 0.04, 1.8, 0.44, TINT[GREY], GREY, "inconclusive", size=13, color=MUTED, radius=0.3)
bullets(s, 0.6, 5.55, 12.1, 1.3, [
    "No hypothesis supported after Holm, and none shown equivalent: “not significant” is not “no effect”.",
    "Debate used about the same tokens as self-consistency but took longer (" + V("d1:DEB|S1:latency_s_per_instance@1") + " s vs " + V("d1:SC|S1:latency_s_per_instance@1") + " s per failure): its calls are sequential."], size=15)
notes(s, """
This is the whole confirmatory family of the approved design. All five are inconclusive after Holm correction.

Javadoc: adding it slightly lowered F1, about minus 0.05, significant before correction but not after. The inferred specification did not help either. Debate beat self-consistency by 0.074 in F1, consistent in direction but far from significant; and five samples of one judge were no better than one.

How to say this carefully: inconclusive is not the same as no effect. At this sample size the smallest F1 difference we could reliably detect is around 0.17 for debate versus self-consistency, and every observed difference is smaller. And remember the judge failed its own gate. So these nulls describe a weak 9B judge, not debate or documentation in general.

Transition: so what is the judge actually using? The ablations answer that.
""")

s = new_slide("E4: the judge reads the failure message; debate components add nothing", "exploratory", act="Act 4 · Implementation and experiments")
abl = [("A1 no argument exchange (DEB)", "abl:A1|S1-DEB|S1"), ("A2 neutral debaters (DEB)", "abl:A2|S1-DEB|S1"),
       ("A4 no failure evidence (J1)", "abl:J1|S1|noF-J1|S1"), ("A4 no failure evidence (SC)", "abl:SC|S1|noF-SC|S1"),
       ("A4 no failure evidence (DEB)", "abl:DEB|S1|noF-DEB|S1"), ("A5a buggy body shown (J1)", "abl:J1|S1|impl-J1|S1"),
       ("A5a buggy body shown (DEB)", "abl:DEB|S1|impl-DEB|S1"), ("A5b body-derived spec (J1, S2)", "abl:J1|S2|specprime-J1|S2")]
rows = []
for lab, k in abl:
    lo, hi = CI(k + ":ci95")
    rows.append((lab, F(k + ":delta"), lo, hi,
                 ORANGE if "A4" in lab else BLUE, "A4" not in lab))
text(s, 0.6, 1.62, 9, 0.35, "ΔF1 of each ablation against its parent arm (95% CI, one replicate)", size=14, bold=True)
forest(s, 0.6, 2.1, 8.6, rows, -0.6, 0.3, [-0.6, -0.4, -0.2, 0, 0.2], row_h=0.53, label_w=3.4)
box(s, 9.55, 2.1, 3.2, 4.25, TINT[ORANGE], None, [
    [("Failure evidence (A4)", {"bold": True, "size": 16})],
    [("is the only component whose removal clearly hurts: one-shot and self-consistency fall to chance (MCC " + V("d1:J1|S1|noF:mcc") + ", " + V("d1:SC|S1|noF:mcc") + ").", {"size": 14})],
    [("", {"size": 6})],
    [("Exchange and adversarial roles (A1, A2) ", {"bold": True, "size": 14}), ("did not help: the small debate advantage is not explained by argument.", {"size": 14})]],
    align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
notes(s, """
Each ablation removes one component and compares with its parent on the same failures. They are exploratory: one replicate, no multiplicity correction.

The orange rows are the striking ones. Remove the failure section, meaning the message with expected and actual values, the failing line and the stack trace, and the one-shot and self-consistency judges drop to chance. So the judge's signal comes from the execution evidence. That also argues against the judge simply recalling a memorised benchmark.

The debate components did nothing measurable: no exchange and no adversarial roles both left F1 slightly higher, with intervals spanning zero. So we cannot credit adversarial argument for the small debate advantage.

Do not overclaim: running an ablation does not prove a component contributes; here only A4 shows a clear effect.

Transition: does any of this hold elsewhere?
""")

s = new_slide("E5 robustness: what was run, and what was not", None, act="Act 4 · Implementation and experiments")
cards = [("R1 · D2 seeded faults", "run", "Every arm again beats the rule on MCC; debate highest (MCC " + V("d2:DEB|S1:mcc") + "). F1 is not comparable across datasets: prevalence differs.", BLUE),
         ("R3 · second judge M2 (12B)", "run", "Better than M1 in every arm (DEB +" + V("r3:D1:m2_minus_m1:DEB:f1:delta").lstrip("+") + " F1 on D1-test), but it shares the generator's family.", BLUE),
         ("R5 · per project, LOPO", "run", "No single project drives a confirmatory verdict.", BLUE),
         ("Frontier reference", "run", "Claude Sonnet 5.5 debate F1 " + V("e9:summary:DEB|S1|SON:f1") + " on D1-test: the task is learnable; small judges are the limit.", VIOLET),
         ("R2 · D3 GitBug-Java", "not run", "Build reproduction needs Docker; no external-benchmark claim.", GREY),
         ("R4 · prompt paraphrases", "not run", "Dropped with Tier 3 for time; no prompt-sensitivity claim.", GREY)]
for i, (head, st, body, col) in enumerate(cards):
    c, r = i % 3, i // 3
    x, y = 0.6 + c * 4.1, 1.75 + r * 2.55
    box(s, x, y, 3.85, 2.3, TINT[col], col if st == "not run" else None, None,
        dash=MSO_LINE_DASH_STYLE.ROUND_DOT if st == "not run" else None)
    text(s, x + 0.2, y + 0.15, 3.45, 0.4, head, size=16, bold=True, color=MUTED if st == "not run" else INK)
    text(s, x + 0.2, y + 0.6, 3.45, 0.3, st.upper(), size=11, bold=True, color=col if col != BLUE else BLUE)
    text(s, x + 0.2, y + 0.95, 3.45, 1.3, body, size=14, color=MUTED if st == "not run" else INK)
notes(s, """
Robustness, E5, had five planned parts. Three ran. On seeded faults every arm again beats the rule baseline and debate has the highest MCC. The second judge, 12B, was better than our 9B in every arm, but it is from the same family as the generator, so self-preference cannot be ruled out. Per-project analysis shows no single project drives a verdict.

As a reference point, not as our method, we also ran Claude Sonnet 5.5: its debate reached F1 0.823. That tells us the task is learnable and that the small judge is the bottleneck.

Two parts did not run, and we say so: GitBug-Java needed Docker, and the prompt-paraphrase test was cut for time. So we make no external-benchmark or prompt-sensitivity claim.

Transition: the results raised a practical question: if judges lose half the bugs, can a rule lose fewer?
""")

s = new_slide("How this study compares with the closest triage work", "original", act="Act 4 \u00b7 Implementation and experiments")
props = ["Triage decision evaluated", "Recall measured", "Buggy/fixed ground truth", "Specification varied", "Budget-matched arms"]
studies = [("JSTestCraft", ["yes", "partly", "no", "no", "no"], "recall " + V("cit:jstestcraft recall") + "%*"),
           ("JavaOracle", ["partly", "no", "no", "no", "no"], "precision " + V("cit:javaoracle precision") + "*"),
           ("VALTEST", ["partly", "yes", "no", "no", "n/a"], "validity +" + V("cit:valtest") + "%*"),
           ("Maddila et al.", ["partly", "no", "no", "no", "n/a"], "solve " + V("cit:maddila solve") + "%*"),
           ("Zhao et al.", ["no", "no", "yes", "partly", "n/a"], V("cit:zhao lo") + "\u2013" + V("cit:zhao hi") + "% effective*"),
           ("This study", ["yes", "yes", "yes", "yes", "yes"], "F1 " + V("d1:DEB|S1:f1") + ", MCC " + V("d1:DEB|S1:mcc"))]
xs = [0.6, 2.75, 4.35, 5.95, 7.55, 9.15]
for j, hname in enumerate(["Study"] + props):
    text(s, xs[j], 1.65, 2.0 if j == 0 else 1.45, 0.6, hname, size=12, color=MUTED, bold=True)
text(s, 10.85, 1.65, 1.9, 0.6, "Reported figure", size=12, color=MUTED, bold=True)
mark = {"yes": ("\u2713", "138A60"), "partly": ("\u25d0", ORANGE), "no": ("\u2013", FAINT), "n/a": ("n/a", FAINT)}
for i, (name, vals, fig) in enumerate(studies):
    y = 2.4 + i * 0.62
    me = name == "This study"
    box(s, 0.6, y, 12.15, 0.52, TINT[BLUE] if me else ("F7F7F5" if i % 2 == 0 else None), None, None)
    text(s, 0.75, y + 0.11, 2.2, 0.35, name, size=14, bold=True)
    for j, v in enumerate(vals):
        sym, col = mark[v]
        text(s, xs[j + 1] + 0.5, y + 0.06, 0.8, 0.4, sym, size=18 if v != "n/a" else 12, color=col, bold=True)
    text(s, 10.85, y + 0.12, 1.9, 0.35, fig, size=11, color=INK if me else MUTED)
text(s, 0.6, 6.25, 12.1, 0.6, "✓ yes  ◐ partly  – no.   * published figures from other languages, data, label sources and models: context, not targets. "
     "No improvement over a base paper can be computed; the fair comparison is against re-implemented arms on identical failures (backup B9).",
     size=13, color=MUTED, italic=True)
notes(s, """
This slide answers: what is new compared with the closest work? Read across the columns. JSTestCraft evaluates its triage vote but estimates recall from a small manual audit. JavaOracle reports precision only. VALTEST measures validity against reference solutions. Meta's pipeline triages with rules but does not evaluate the triage. Zhao et al. use buggy/fixed versions but have no triage step.

This study is the only one that does all five: it evaluates the triage decision, measures recall, scores against buggy/fixed ground truth, varies the specification, and matches the budgets.

Be careful with the right-hand column: the starred numbers come from other languages, datasets, label sources and much larger models, so they are context, not targets. We cannot claim an improvement over any of them; backup B9 compares our re-implemented baselines on identical failures.

Transition: the results raised a practical question: if judges lose half the bugs, can a rule lose fewer?
""")

# =============================================================== ACT 5 - FINDINGS AND EXTENSIONS
s = new_slide("RQ4: judge-only rules trade lost bugs against removed wrong tests", "advance", act="Act 5 · Findings and research extensions")
pic = picture(s, TRADE_PNG, 1.85, 1.5, w=9.6, alt="Post hoc trade-off plot: PF-loss rate against TF-removal rate for every rule on D1-test and D2.")
pic.crop_bottom = 0.1
pic.height = int(pic.height * (1 - 0.1))
box(s, 0.6, 5.85, 5.95, 1.05, TINT[VIOLET], None, [
    [("Keep unless unanimous (KUU): ", {"bold": True, "size": 14}),
     ("discard only if three model families all say “test fault”. On D2 it lost ", {"size": 14}),
     (V("kuu2:summary:KUU|S1:pf_lost@0") + " of " + V("kuu2:pf_prevalence:PF"), {"bold": True, "size": 14}),
     (" bug-revealing tests; debate lost " + V("kuu2:summary:DEB|S1:pf_lost@0") + ".", {"size": 14})]], align=PP_ALIGN.LEFT)
box(s, 6.8, 5.85, 5.95, 1.05, "F7F7F5", None, [
    [("A baseline, not a method: ", {"bold": True, "size": 14}),
     ("its MCC (" + V("kuu2:summary:KUU|S1:mcc") + ") is below debate's (" + V("kuu2:summary:DEB|S1:mcc") + "); it keeps bugs by keeping almost everything.", {"size": 14})]],
    align=PP_ALIGN.LEFT)
notes(s, """
Read the plot: across is the share of bug-revealing tests a rule loses, up is the share of wrong tests it removes. Top left is best. Every rule we tried, voting, debate, unanimity, escalation, sits on roughly one curve.

Keep unless unanimous asks one judge from each of three model families and discards a test only if all three say the test is wrong. On the seeded faults, with hypotheses fixed in advance in our decision log, it lost 4 of 154 bug-revealing tests where debate lost 56.

But be honest about what that means: its MCC is lower than debate's, because it keeps bugs by keeping almost everything. Multi-judge voting and unanimity are established ideas. So KUU is our baseline, the keep-heavy end of the curve, not a new method. This corrects how our first deck presented it.

Transition: judges alone move along this curve. Could the program itself tell us which side is wrong?
""")

s = new_slide("A new idea: ask the program, not another judge", "exploratory", act="Act 5 · Findings and research extensions")
box(s, 0.6, 1.8, 2.8, 1.2, "F7F7F5", "D9D8D3", [[("Failing test t", {"bold": True})], [("on the buggy method m", {"size": 13})]], size=15)
box(s, 4.0, 1.6, 3.6, 1.6, TINT[VIOLET], VIOLET, [[("Up to " + V("cfz:parameters:max_mutants_per_focal") + " single-edit mutants", {"bold": True})],
                                                    [("of m and its same-class callees (ROR, AOR, COR, LVR, NEG, STD)", {"size": 13})]], size=15)
arrow(s, 3.4, 2.4, 4.0, 2.4)
outs = [("FLIP", "the test now passes (twice)"), ("SHIFT", "it fails differently"), ("SAME", "same failure")]
for i, (o, d) in enumerate(outs):
    box(s, 8.3, 1.55 + i * 0.6, 1.2, 0.5, VIOLET, None, o, size=13, bold=True, color="FFFFFF")
    text(s, 9.65, 1.63 + i * 0.6, 3.1, 0.4, d, size=14)
arrow(s, 7.6, 2.4, 8.3, 2.4)
box(s, 0.6, 3.75, 5.9, 2.4, TINT[GREEN], None, [[("Flip", {"bold": True, "size": 18})],
    [("Some edit makes the test pass. Hypothesis: a bug-revealing test should flip more often, because fixing the bug makes it pass.", {"size": 15})]],
    align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
box(s, 6.85, 3.75, 5.9, 2.4, TINT[ORANGE], None, [[("Decoupled", {"bold": True, "size": 18})],
    [("At least " + V("cfz:parameters:min_compiled_mutants_for_decoupling") + " mutants compiled and none changed the failure. Hypothesis: a wrong test does not depend on the method at all.", {"size": 15})]],
    align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP)
text(s, 0.6, 6.35, 12.1, 0.5, "The probe reads only the buggy version: no model, no labels, no fixed version, no developer tests.", size=14, color=MUTED, italic=True)
notes(s, """
Here is the idea. Instead of asking another model, ask the program. Take the failing test and run it on many small, single-edit variants of the method under test: flip a comparison, change an arithmetic operator, and so on. Each run either flips (the test now passes), shifts (fails differently), or stays the same.

Two signals follow. A flip: some edit makes the test pass. Our hypothesis was that bug-revealing tests flip more, because a fix makes them pass. Decoupled: ten or more mutants compiled and none changed the failure. Our hypothesis was that wrong tests often do not depend on the method at all.

The mechanism is not new: mutation-based fault localisation runs exactly these executions, but it assumes the failing test is right. We ask the question it presupposes.

Note: this uses no model and never sees the fixed version or the labels.

Transition: the first look was very promising.
""")

s = new_slide("The pilot looked strong, but a pilot is not evidence", "exploratory", act="Act 5 · Findings and research extensions")
text(s, 0.6, 1.8, 5.6, 1.1, V("pil:flags:flip:diff_PF_minus_TF@signed"), size=60, color=ORANGE, bold=True, face=HEAD)
text(s, 0.6, 3.0, 5.6, 1.0, "difference in flip rate, bug-revealing minus wrong tests, " + V("pil:flags:flip:diff_ci95") + " (pilot, D1-test)", size=15, color=MUTED)
text(s, 0.6, 4.0, 5.6, 1.0, V("pil:flags:decoupled:TF_flagged") + " of " + V("pil:flags:decoupled:n_flagged"), size=44, color=ORANGE, bold=True, face=HEAD)
text(s, 0.6, 4.95, 5.6, 0.8, "decoupled tests were wrong tests", size=15, color=MUTED)
box(s, 6.7, 1.8, 6.05, 3.6, "F7F7F5", None, None)
text(s, 6.95, 1.95, 5.6, 0.45, "Why we did not stop there", size=18, bold=True)
bullets(s, 6.95, 2.55, 5.6, 2.8, ["The labels were known when the rules were written.",
                                   "Only " + V("pil:scored:bugs_with_PF") + " bugs carried a bug-revealing test.",
                                   "One design change (callee mutants) came after the first look.",
                                   [("So the claim was registered on OSF before any new data existed.", {"bold": True})]], size=15)
box(s, 6.7, 5.65, 6.05, 0.8, TINT[GREEN], GREEN, "OSF " + V("osf:osf_id") + " · " + V("osf:registered_utc") + " · frozen engine and analysis", size=14, color="138A60", bold=True)
notes(s, """
On our held-out split the pilot looked excellent: bug-revealing tests flipped far more often than wrong tests, a difference of 0.511, and 61 of 62 decoupled tests were wrong tests.

But this is exactly the situation in which a result is least trustworthy. We knew the labels when we wrote the rules. Only 22 bugs carried a bug-revealing test. And we amended the design once after looking. A pilot like this can produce a large effect by chance and by our own choices.

So instead of reporting it as a finding, we froze the probe engine and the analysis, and registered the hypotheses on OSF before generating any new test. This is the turning point of the talk.

Transition: here is what the registered test found.
""")

s = new_slide("Registered result: the flip did not replicate; decoupling held, with limits", "registered", act="Act 5 · Findings and research extensions")
p_c1 = CI("pil:flags:flip:diff_ci95")
c1 = CI("cc:family:C1:ci95"); c2 = CI("cc:family:C2:ci95")
f1c2 = CI("cf1:family:C2:ci95@ci2"); f2c2 = CI("cf2:family:C2:ci95@ci2")
def sv(k):
    v = V(k); return float(v.replace("−", "-").replace("+", ""))
rows1 = [("Pilot (exploratory)", sv("pil:flags:flip:diff_PF_minus_TF@signed"), p_c1[0], p_c1[1], ORANGE, True),
         ("Registered, pooled", sv("cc:family:C1:difference@signed"), c1[0], c1[1], GREEN, False)]
rows2 = [("Registered, pooled", sv("cc:family:C2:difference@signed"), c2[0], c2[1], GREEN, False),
         ("  frame F1", sv("cf1:family:C2:difference@signed"), f1c2[0], f1c2[1], GREEN, True),
         ("  frame F2", sv("cf2:family:C2:difference@signed"), f2c2[0], f2c2[1], GREEN, True)]
forest(s, 0.6, 2.15, 6.1, rows1, -0.3, 0.8, [-0.2, 0, 0.2, 0.4, 0.6], row_h=0.55, label_w=2.2, title="C1 · flip rate, PF minus TF")
forest(s, 0.6, 4.55, 6.1, rows2, -0.3, 0.8, [-0.2, 0, 0.2, 0.4, 0.6], row_h=0.5, label_w=2.2, title="C2 · decoupled rate, TF minus PF")
box(s, 7.2, 1.75, 5.55, 1.55, "F7F7F5", None, [[(V("cc:population:instances") + " fresh failing tests · " + V("cc:population:bugs") + " unseen bugs", {"bold": True, "size": 15})],
    [("only " + V("cc:population:bugs_with_PF") + " bugs carry a bug-revealing test (plan: " + V("atx:plan lo") + "–" + V("atx:plan hi") + ")", {"size": 14, "color": MUTED})]], align=PP_ALIGN.LEFT)
box(s, 7.2, 3.5, 5.55, 1.45, TINT[GREY], None, [[("C1 not supported", {"bold": True, "size": 15})],
    [("Holm p " + V("cc:family:C1:p_holm@4") + ". A passing edit is not evidence the test is right; control failures flip at " + V("cc:control:flip_rate_TF@3") + ".", {"size": 14})]], align=PP_ALIGN.LEFT)
box(s, 7.2, 5.15, 5.55, 1.65, TINT[GREEN], None, [[("C2 supported, Holm p " + V("cc:family:C2:p_holm@4"), {"bold": True, "size": 15})],
    [(V("cc:family:C2:TF_flagged") + " of " + V("dv:dec flagged") + " decoupled tests are wrong, but not reproduced in F1; " + V("arow:jackson dec tf") + " of " + V("cc:family:C2:TF_flagged") + " lie in two Jackson projects.", {"size": 14})]], align=PP_ALIGN.LEFT)
notes(s, """
This is the registered result, printed as registered. 572 fresh failing tests from 104 bugs the original study never touched. One shortfall to say upfront: only 21 bugs carry a bug-revealing test, against a plan of 30 to 50.

C1, the flip: not supported. The difference is +0.028 with an interval from minus 0.137 to 0.274. It excludes the pilot's 0.511. A single edit makes a failing test pass about equally often whichever side is at fault; even control failures on methods the fix did not touch flip 22 percent of the time. Careful wording: it did not replicate; a small positive effect is not excluded.

C2, decoupling: supported, Holm p 0.0024, and 135 of 136 decoupled tests were wrong. But two limits. The registered per-frame analysis shows it in frame F2 and not in F1. And 117 of the 135 come from two Jackson projects; without them the estimate is +0.041 with an interval crossing zero, which is exploratory. So the flag is precise where it fires, but how often it fires does not transfer.

Transition: did rules built on these signals help?
""")

s = new_slide("Probe-based rules were inconclusive, and one lost a bug", "registered", act="Act 5 · Findings and research extensions")
for j, hname in enumerate(["Rule", "TPR (bugs kept)", "TNR (wrong removed)", "Bugs lost"]):
    text(s, [0.6, 4.6, 7.0, 9.6][j], 1.7, 2.6, 0.35, hname, size=14, color=MUTED, bold=True)
rr = [("KUU (baseline)", "KUU"), ("KUU + decoupled-discard (C3)", "KUU+CD"), ("2-of-3 vote", "2-of-3"), ("2-of-3 + keep certificate (C4)", "2-of-3+CK")]
for i, (lab, k) in enumerate(rr):
    y = 2.1 + i * 0.68
    box(s, 0.6, y, 3.85, 0.55, TINT[VIOLET] if k == "KUU" else "F7F7F5", None, lab, size=14, align=PP_ALIGN.LEFT, bold=(k == "KUU"))
    text(s, 4.6, y + 0.12, 2.2, 0.4, V("cc:rules:" + k + ":TPR@3"), size=16)
    text(s, 7.0, y + 0.12, 2.2, 0.4, V("cc:rules:" + k + ":TNR@3"), size=16)
    text(s, 9.6, y + 0.12, 3, 0.4, V("cc:rules:" + k + ":bugs_lost") + " of " + V("cc:rules:" + k + ":bugs_with_PF"), size=16,
         bold=V("cc:rules:" + k + ":bugs_lost") != "0", color="B5441A" if V("cc:rules:" + k + ":bugs_lost") != "0" else INK)
bullets(s, 0.6, 5.0, 12.1, 1.8, [
    [("C3 ", {"bold": True}), ("(KUU + CD vs KUU, balanced accuracy): " + V("cc:family:C3:difference@signed") + ", Holm p " + V("cc:family:C3:p_holm@4") + ": inconclusive; it lost one bug (Math_59).", {})],
    [("C4 ", {"bold": True}), ("(keep certificate): Holm p " + V("cc:family:C4:p_holm@4") + ": inconclusive; its evidence was set for " + V("cc:secondary:rcf_in_place_of_flip:PF_flagged") + " of " + V("cc:population:PF") + " bug-revealing tests.", {})],
    "Both were underpowered by the registered planning, so neither is evidence against the rule either."], size=15)
notes(s, """
The registered rules. The table leads with what a developer cares about: share of bug-revealing tests kept, share of wrong tests removed, and bugs lost entirely.

Adding the decoupled-discard certificate to KUU removed more wrong tests, from about 0.32 to 0.43, but lost one bug, Math 59, and C3 was not significant after Holm, p 0.14. The keep certificate, C4, had almost nothing to work with: its evidence fired for 4 of 55 bug-revealing tests. Both were underpowered by our own planning, so we call them inconclusive, not failures.

Transition: why was Math 59 lost? That question leads to the last, exploratory analysis.
""")

s = new_slide("What survived is a dependence check, and it is exploratory", "wdp", act="Act 5 · Findings and research extensions")
w_r = ["KUU", "KUU+CD", "KUU+CD-U"]
bar_chart(s, 0.6, 1.95, 6.3, 4.4, ["KUU (baseline)", "KUU + CD (registered)", "KUU + CD-U (WDP)"],
          [("TPR: bug-revealing tests kept", [F("wdp:secondary:6_rules:CONF-votes:" + k + ":TPR@3") for k in w_r]),
           ("TNR: wrong tests removed", [F("wdp:secondary:6_rules:CONF-votes:" + k + ":TNR@3") for k in w_r])],
          [BLUE, ORANGE], number_format="0.000", max_v=1.15, horizontal=False, legend=True, gap=80, label_size=12)
text(s, 0.6, 6.4, 6.3, 0.4, "Bugs lost: 0, 1, 0 of " + V("wdp:populations:CONF-votes:bugs_with_PF") + " · " + V("wdp:populations:CONF-votes:instances") + " confirmation tests with three votes", size=13, color=MUTED)
bullets(s, 7.3, 1.85, 5.45, 4.9, [
    [("Replace the whole method: ", {"bold": True}), ("is it entered, and does the failure change at all?", {})],
    [("TNR +" + V("wdp:primary:paired:TNR:difference@signed").lstrip("+") + " " + V("wdp:primary:paired:TNR:ci95") + " over KUU, ", {"bold": True}), ("no bug-revealing test or bug lost", {})],
    "No bug-revealing test at level U: " + V("wdp:secondary:3_level_U_by_label:CONF-all:U:PF_flagged") + " of " + V("wdp:secondary:3_level_U_by_label:CONF-all:U:PF") + " (pilot " + V("wdp:secondary:3_level_U_by_label:PILOT-all:U:PF_flagged") + " of " + V("wdp:secondary:3_level_U_by_label:PILOT-all:U:PF") + ")",
    "Bound on extra bug loss " + V("wdp:pooled_bound:upper95@3") + ": optimistic, the rule was designed after seeing the lost bugs",
    "Concentrated in F2 and two Jackson projects (without them +" + V("wdp:secondary:9_heterogeneity:without_Jackson:primary:paired:TNR:difference@signed").lstrip("+") + ")",
    "Mostly an entry check (" + V("wdp:secondary:4_ladder:registered_decoupled:CONF:TF:U") + " of " + V("wdp:secondary:4_ladder:registered_decoupled:CONF:TF:n") + "), not a mutation effect"], size=14, gap=7)
notes(s, """
Both lost bugs, Math 59 in the confirmation and Codec 13 in the pilot, were faults no single edit could touch, so every mutant was silent even though the failure plainly depended on the method. That suggested asking the underlying question directly: replace the whole method, and check whether it is entered at all.

Read the status tag first: exploratory, retrospective, protocol frozen in Git before the runs, not externally preregistered, and designed after the confirmation outcomes were known.

On the 561 confirmation tests with three votes, discarding level-U failures beside KUU removed 0.104 more of the wrong tests, interval 0.037 to 0.201, with no bug-revealing test lost; no bug-revealing test reached level U. But: the 0.067 bound is optimistic because the rule was designed knowing those bugs; the gain is concentrated in F2 and two Jackson projects; and 112 of the 135 decoupled wrong tests are level U, which means most of the signal is simply "the method is never entered", an entry check, not a mutation effect.

If questioned: we do not claim WDP is validated or safe. It needs a fresh registered test.

Transition: let me pull this together.
""")

# =============================================================== ACT 6 - CONCLUSION
s = new_slide("What the evidence supports, and what it does not", None, act="Act 6 · Conclusion")
box(s, 0.6, 1.7, 5.95, 5.1, TINT[GREEN], None, None)
box(s, 6.8, 1.7, 5.95, 5.1, "F7F7F5", None, None)
text(s, 0.85, 1.85, 5.5, 0.45, "Supported", size=20, bold=True, color="138A60")
text(s, 7.05, 1.85, 5.5, 0.45, "Not claimed", size=20, bold=True, color=MUTED)
bullets(s, 0.85, 2.45, 5.5, 4.3, [
    "An execution-grounded measurement of LLM triage, with lost tests and lost bugs as outcomes",
    "Small judges carry a weak signal that comes from the failure evidence",
    "Judge-only rules lie on one trade-off curve; KUU is its keep-heavy baseline",
    "Registered: a test-passing edit is not evidence the test is right",
    "Registered, with limits: a failure no edit changes is mostly a wrong test"], size=15)
bullets(s, 7.05, 2.45, 5.5, 4.3, [
    "A new triage method, or that KUU or any certificate is safe",
    "That debate or documentation does not help (inconclusive is not “no effect”)",
    "That the decoupling rate transfers across frames or projects",
    "That WDP is validated: it is exploratory and retrospective",
    "Generalisation beyond Defects4J, Java, one generator and small local judges"], size=15)
notes(s, """
This is the slide to remember. On the left is what our evidence supports. We built and ran an execution-grounded measurement of LLM triage that counts lost bugs. Small judges carry a weak signal, and it comes from the failure message. Rules made only of judges trade lost bugs against removed wrong tests on one curve. And from the registered study: a passing edit is not evidence that a test is right, while a failure no edit changes is mostly a wrong test, with the frame and project limits.

On the right is what we do not claim. We do not claim a new method. We do not claim debate or Javadoc are useless: our tests were inconclusive. We do not claim the decoupling rate transfers, or that the whole-method check is validated. And we do not generalise beyond one benchmark, one language and one generator.

Transition: did we meet the gaps we set out to close?
""")

s = new_slide("Gaps and objectives: measured as designed, answers mostly inconclusive", None, act="Act 6 · Conclusion")
go = [("G1 · O1, O2", "Measured against execution labels; H1 inconclusive; about half of bug-revealing tests lost by every judge", "met (measurement)", BLUE),
      ("G2 · O3", "Specification varied with test and label fixed; no detectable gain for these judges", "met (inconclusive)", BLUE),
      ("G3 · O4", "Equal-budget comparison run; debate advantage small and not significant", "met (inconclusive)", BLUE),
      ("O5 robustness", "D2 and a second judge run; D3 and prompt paraphrases not run", "partly met", ORANGE),
      ("RQ5 · registered", "Flip did not replicate; decoupling held pooled, not in frame F1", "answered", GREEN),
      ("RQ6 · registered", "Both certificate rules inconclusive; one lost a bug", "inconclusive", GREY)]
for i, (g, d, v, col) in enumerate(go):
    y = 1.75 + i * 0.82
    box(s, 0.6, y, 2.5, 0.66, TINT[col], None, g, size=14, bold=True)
    text(s, 3.3, y + 0.08, 7.0, 0.6, d, size=15, anchor=MSO_ANCHOR.MIDDLE)
    box(s, 10.5, y + 0.1, 2.25, 0.46, TINT[col], col, v, size=12, bold=True, color=col if col != GREY else MUTED, radius=0.3)
notes(s, """
Against the Phase 2 objectives. G1, G2 and G3 were each measured exactly as designed. The answers are mostly inconclusive at this sample size, and we report that rather than forcing a positive story. The robustness objective was only partly met, because two planned parts did not run. The two registered questions are answered: the flip did not replicate, decoupling held with limits, and the rules were inconclusive.

Transition: what we would do next.
""")

s = new_slide("Limitations, next steps, and the take-away", None, act="Act 6 · Conclusion", dark=True)
text(s, 0.6, 1.7, 5.9, 0.45, "Limitations", size=20, bold=True, color="FFFFFF")
bullets(s, 0.6, 2.25, 5.9, 3.6, ["One benchmark, one language, one generator, small local judges",
                                 "Only " + V("cc:population:bugs_with_PF") + " bugs with a bug-revealing test in the confirmation",
                                 "Every local judge failed its development gate",
                                 "No independent audit of the confirmation's labels"], size=15, color="DCE3F0")
text(s, 6.9, 1.7, 5.9, 0.45, "Next steps", size=20, bold=True, color="FFFFFF")
bullets(s, 6.9, 2.25, 5.85, 3.6, ["A fresh registered test of the dependence check on unseen tests",
                                  "A second generator and an external benchmark",
                                  "An independent audit of the labels",
                                  "A patch-based comparison where an issue report exists"], size=15, color="DCE3F0")
box(s, 0.6, 5.55, 12.15, 1.15, NAVY2, None, [[("Take-away: ", {"bold": True, "color": "FFFFFF", "size": 18}),
    ("a failing generated test is not necessarily a wrong test. Do not keep it because some edit makes it pass; a failure that never depends on the method under test is the signal worth confirming next.", {"color": "DCE3F0", "size": 17})]],
    align=PP_ALIGN.LEFT)
text(s, 0.6, 6.75, 12.1, 0.3, "Thank you · Questions   |   Code and data: github.com/hafizhuzaifaahmed/llm-failure-triage   |   Dataset: github.com/rjust/defects4j (v3.0.1)", size=13, color="B8BCC8", bold=True)
notes(s, """
Limitations, briefly: one benchmark, one language, one generator, small local judges; only 21 bugs with a bug-revealing test in the confirmation; every local judge failed its development gate; and no independent audit of the confirmation labels.

Next steps follow directly: a fresh registered test of the whole-method dependence check on tests that no probe or judge has seen; a second generator and an external benchmark; an independent label audit; and a patch-based comparison in a setting with issue reports.

The take-away in one sentence: a failing generated test is not necessarily a wrong test. Do not keep a test because some edit makes it pass; whether the failure depends on the method under test at all is the signal worth confirming next.

Thank you. We are happy to take questions; the backup slides cover registration, power, the control group, the frames, the judges, the statistics, the label audit, the base-paper comparison and evidence status.
""")

# =============================================================== BACKUP
def backup(title, status, label):
    return new_slide(title, status, act="Backup", backup=label)


s = backup("Registration details", "registered", "B1")
bullets(s, 0.6, 1.8, 12.1, 5, [
    "OSF " + V("osf:osf_id") + ", registered " + V("osf:registered_utc") + ", before any confirmation test was generated.",
    "Governing text: the attached document and the frozen code it contains; the template fields were reworded at deposit and their reconciliation is pending.",
    "One Holm family C1–C4, α = 0.05; bug-level cluster bootstrap, " + V("cc:resamples") + " resamples, seed " + V("cc:seed@id") + ".",
    "Sealing order recorded by commits: labels (1a58e54) → probe ledgers (b332305) → judge votes → analysis (3b017f2).",
    "Registered: hypotheses, bugs-lost outcome with exact bounds, a control group, secondary analyses, a counting-against list."], size=18, gap=12)
notes(s, "If asked what was registered and when: OSF kp79c, before any confirmation test existed. The commit order shows labels and probe ledgers were sealed before votes and analysis. Acknowledge that the OSF template fields were reworded at deposit; the attached frozen bundle is what governs.")

s = backup("Was the confirmation underpowered?", "registered", "B2")
bullets(s, 0.6, 1.8, 12.1, 5, [
    "Planned " + V("atx:plan lo") + "–" + V("atx:plan hi") + " bugs with a bug-revealing test; realised " + V("cc:population:bugs_with_PF") + " (decision D-145, before any hypothesis was computed).",
    "C1 was classified as adequately powered at " + V("atx:plan lo") + "+ bugs; its realised interval half-width equals the planned width, so the shortfall did not widen it.",
    "C2–C4 were classified underpowered in advance: their nulls are inconclusive unless a registered counting-against rule applies.",
    "Reading of C1 as evidence against the method rests on a planning assumption this sample does not meet: stated beside C1 in the paper."], size=18, gap=12)
notes(s, "Be direct: 21 bugs, not 30 to 50. The registered reading is applied unchanged, with the qualifier. C1's interval is as narrow as planned, which is why it still excludes the pilot effect.")

s = backup("Control group: methods the fix did not change", "registered", "B3")
bullets(s, 0.6, 1.8, 12.1, 5, [
    "One method per bug in the same class, unchanged by the fix, public or protected, matched on mutant count.",
    V("cc:control:instances") + " failures from " + V("cc:control:bugs") + " bugs, all labelled TF.",
    "Flip rate " + V("cc:control:flip_rate_TF@3") + " " + V("cc:control:flip_rate_TF_ci95") + ": the same as wrong and bug-revealing tests.",
    "These methods are not known to be defect-free: they sit in classes that needed a fix."], size=18, gap=12)
notes(s, "The control shows that flipping is common even for failures on methods the fix never touched, which is why a flip is not evidence the test is right.")

s = backup("Registered secondary analyses", "registered", "B4")
for j, hname in enumerate(["Analysis", "Estimate", "95% CI"]):
    text(s, [0.6, 6.0, 8.0][j], 1.75, 3, 0.35, hname, size=14, color=MUTED, bold=True)
sec = [("Keep evidence (rcf) in place of flip", "rcf_in_place_of_flip"), ("Guarded decoupling", "guarded_decoupling"),
       ("Clean-operator flip", "clean_operator_flip"), ("Focal-body-only flip", "focal_body_only_flip"), ("Shared flip", "shared_flip")]
for i, (lab, k) in enumerate(sec):
    y = 2.2 + i * 0.62
    text(s, 0.6, y, 5.3, 0.4, lab, size=16)
    text(s, 6.0, y, 1.8, 0.4, V("cc:secondary:" + k + ":difference@signed"), size=16, bold=True)
    text(s, 8.0, y, 3, 0.4, V("cc:secondary:" + k + ":ci95"), size=16)
text(s, 0.6, 5.6, 12, 0.6, "None replaces a primary result.", size=15, color=MUTED, italic=True)
notes(s, "Registered secondary analyses, reported not tested. None changes a primary reading.")

s = backup("Where decoupling holds: frames and projects", "exploratory", "B5")
bullets(s, 0.6, 1.8, 12.1, 5, [
    "F1: the original frame's methods of unseen bugs; F2: fix-changed methods that no bug-triggering test calls by name.",
    "C2 in F1 " + V("cf1:family:C2:difference@signed") + " " + V("cf1:family:C2:ci95@ci2") + "; in F2 " + V("cf2:family:C2:difference@signed") + " " + V("cf2:family:C2:ci95@ci2") + " (registered secondary).",
    V("arow:jackson dec tf") + " of " + V("cc:family:C2:TF_flagged") + " decoupled wrong tests are in JacksonDatabind and JacksonCore; without both: " + V("atx:noJ est@signed") + " " + V("atx:noJ ci") + ".",
    "Decoupling lives where an exception is raised outside the method under test.",
    "Precision transferred; how often the flag fires did not."], size=18, gap=12)
notes(s, "Exploratory, chosen after the outcomes. The effect is real in the pooled registered analysis, but it is carried by F2 and two projects.")

s = backup("Thinking-enabled judge and the frontier reference", "advance", "B6")
bullets(s, 0.6, 1.8, 12.1, 5, [
    "With thinking enabled, one M1 call beat M1's five-call debate on D2: ΔMCC " + V("tk:d2:confirmatory:HT-1:delta") + " " + V("tk:d2:confirmatory:HT-1:ci95") + ", Holm p " + V("tk:d2:confirmatory:HT-1:p_holm") + " (fixed in advance).",
    "It still failed its development gate, so it is a stronger classifier, not a validated judge.",
    "Claude Sonnet 5.5 (reference only): debate F1 " + V("e9:summary:DEB|S1|SON:f1") + " on D1-test; escalating KUU disagreements to it raised MCC to " + V("cas2:summary:CAS|S1:mcc") + ".",
    "Escalation did not show non-inferiority to Sonnet on every instance."], size=18, gap=12)
notes(s, "For small judges, reasoning inside one call did what extra calls were meant to do. The frontier model shows the task is learnable; it is a reference, not our method.")

s = backup("Statistics and reproducibility", "original", "B7")
bullets(s, 0.6, 1.8, 12.1, 5, [
    "Bug-level cluster bootstrap, 10,000 resamples, paired; two-sided bootstrap p; Holm within each confirmatory family.",
    "Equivalence only when the 90% CI lies within ±0.05 F1; non-significance is never read as equivalence.",
    "Decoding: temperature " + V("frozen:frozen_models:M1:temperature:judges@1") + ", top-p " + V("frozen:frozen_models:M1:top_p@1") + ", " + V("frozen:frozen_models:M1:num_predict:judge_roles") + " output tokens, per-call seed, thinking off; 3 replicates for E1–E3.",
    "Ollama " + V("frozen:runtime:version") + " on one " + V("frozen:hardware:name") + "; WSL2 Ubuntu 22.04, OpenJDK 11, Defects4J 3.0.1.",
    "Configuration, prompts and digests frozen in one file before any held-out call; every number in the paper and deck generated from committed outputs.",
    "Code and data: github.com/hafizhuzaifaahmed/llm-failure-triage; dataset: github.com/rjust/defects4j (v3.0.1)."], size=18, gap=12)
notes(s, "Everything needed to reproduce: the frozen configuration file, the decision log and the build scripts that regenerate every number.")

s = backup("Can the labels be trusted?", "original", "B8")
bullets(s, 0.6, 1.8, 12.1, 5, [
    "Two-rater blind audit of " + V("aud:n_items") + " development instances: κ " + V("aud2:raters:kappa") + "; consensus matches the execution label on " + V("aud2:consensus_vs_execution:agreement@pct1") + ".",
    "Planned 100 items; the development split has only " + V("aud:labels:PF") + " PF instances.",
    "The raters are the authors and saw the fix; no independent audit of the confirmation labels exists.",
    "Blind spot: a test revealing a second real fault fails on both versions and is labelled TF."], size=18, gap=12)
notes(s, "If a reviewer pushes on construct validity, concede the blind spot and the author-rater limitation; the next step is an independent audit.")

s = backup("Comparison with base papers", "original", "B9")
for j, hname in enumerate(["Method", "Source", "Recall", "F1", "MCC"]):
    text(s, [0.6, 4.2, 7.9, 9.4, 10.9][j], 1.75, 3.5, 0.35, hname, size=14, color=MUTED, bold=True)
qrows = [("JSTestCraft vote", "published* (JS, audit)", V("cit:jstestcraft recall") + "%*", "n/r", "n/r"),
         ("JavaOracle debate", "published* (precision " + V("cit:javaoracle precision") + "*)", "n/r", "n/r", "n/r"),
         ("Rule R0", "re-implemented", V("d1:R0:recall"), V("d1:R0:f1"), V("d1:R0:mcc")),
         ("Three-family vote", "re-implemented, local", V("e8:summary:VOTE3|S1:recall"), V("e8:summary:VOTE3|S1:f1"), V("e8:summary:VOTE3|S1:mcc")),
         ("Debate (DEB)", "this study", V("d1:DEB|S1:recall"), V("d1:DEB|S1:f1"), V("d1:DEB|S1:mcc"))]
for i, r in enumerate(qrows):
    y = 2.2 + i * 0.6
    for j, val in enumerate(r):
        text(s, [0.6, 4.2, 7.9, 9.4, 10.9][j], y, [3.5, 3.6, 1.4, 1.4, 1.4][j], 0.45, val, size=15, bold=(j == 0))
text(s, 0.6, 5.5, 12.1, 1.0, "* published figures from other languages, data, label sources and much larger models: context, not targets. No improvement over a base paper can be computed on comparable data.", size=14, color=MUTED, italic=True)
notes(s, "Be careful: the starred numbers are other papers' figures in other settings. The fair comparison is against the re-implemented arms on identical failures.")

s = backup("Evidence status of every result", None, "B10")
es = [("RQ1–RQ3 (H1–H3b)", "confirmatory family of the approved design; protocol frozen before held-out calls", BLUE),
      ("E4, E5", "exploratory / robustness", ORANGE),
      ("RQ4: KUU, cascade", "fixed in advance in the decision log on D2; post hoc on D1; KUU is a baseline", VIOLET),
      ("Probe pilot", "exploratory (labels known)", ORANGE),
      ("C1–C4, rules, control", "confirmatory, registered (OSF " + V("osf:osf_id") + ")", GREEN),
      ("WDP", "exploratory; retrospective; frozen internally in Git before the runs; not externally preregistered; designed after the confirmation outcomes were known", ORANGE)]
for i, (r, st, col) in enumerate(es):
    y = 1.75 + i * 0.82
    box(s, 0.6, y, 3.4, 0.68, TINT[col], None, r, size=14, bold=True)
    text(s, 4.2, y + 0.06, 8.5, 0.66, st, size=15, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "Use this if anyone asks how strong a given result is. Fixed in advance in our Git decision log is internal provenance, not a public preregistration; only C1 to C4 are registered.")

s = backup("Independent audit and use of AI tools", None, "B11")
bullets(s, 0.6, 1.8, 12.1, 5, [
    "A read-only audit (Claude Fable 5.2) recomputed every registered count, estimate, interval, p-value, Holm step, rule row and bound from raw records with independent code: no discrepancy.",
    "Claude Opus 5.5 implemented the pipeline, ran the analyses, built figures and this deck, and drafted text, under the authors' direction.",
    "A Fable 5.2 review of the WDP interpretation was started, stopped at the usage limit with no output, and waived by the authors (D-152).",
    "The open-weight models and Claude Sonnet 5.5 are experimental subjects, not authoring tools; the authors take responsibility for every claim."], size=18, gap=12)
notes(s, "State AI use plainly. The only interpretation review of WDP on record is by Opus 5.5.")

s = backup("Likely questions", None, "B12")
qa = [("Is KUU your method?", "No. It is a baseline: unanimity voting already exists. Our original proposed framework was the debate."),
      ("Did debate fail?", "Inconclusive, not failed: the study could detect only differences around " + V("mde:tests:H3a:mde_alpha_005@2") + " F1, with a judge below its own gate."),
      ("Why trust a fixed version as truth?", "It is an operational reference; the audit agreed 97% on development data; second-fault tests are a known blind spot."),
      ("Is WDP safe to deploy?", "No claim: exploratory, retrospective, concentrated in two projects; it needs a fresh registered test.")]
for i, (q, a) in enumerate(qa):
    y = 1.75 + i * 1.25
    text(s, 0.6, y, 12.1, 0.4, q, size=17, bold=True, color=BLUE)
    text(s, 0.6, y + 0.45, 12.1, 0.7, a, size=15)
notes(s, "Short answers to the four questions we expect. Keep each answer to one or two sentences and point to the relevant backup slide.")

prs.save(OUT)
print("wrote", OUT, "slides:", len(prs.slides))
