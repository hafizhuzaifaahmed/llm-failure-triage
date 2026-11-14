"""Build the defense deck, paper/DEFENSE_DECK.pptx, from the rendered deck source and the defense questions.

Inputs, both rendered by scripts/paper/build_numbers.py from docs/paper/NUMBERS_MAP.csv, so the deck cannot disagree
with the paper:
  docs/paper/DEFENSE_DECK.md  - the main slides (headline, text, chart values, speaker notes)
  docs/paper/DEFENSE_QA.md    - one backup slide per question
Charts are native, editable PowerPoint charts. Entrance animations (fade, on click, in story order: bullets one by
one, chart series one by one, diagram parts left to right) and a fade transition are written into each slide's
<p:timing> XML, which python-pptx does not expose. The footer carries the commit hash and its date.

    python scripts/paper/build_numbers.py          # first: render the sources
    python scripts/paper/build_deck.py [--render]  # --render: PowerPoint opens the deck, counts its animations,
                                                   # exports thumbnails and a contact sheet (Windows + PowerPoint)
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_TICK_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
DECK_MD = ROOT / "docs" / "paper" / "DEFENSE_DECK.md"
QA_MD = ROOT / "docs" / "paper" / "DEFENSE_QA.md"
OUT = ROOT / "paper" / "DEFENSE_DECK.pptx"
PREVIEW = ROOT / "paper" / "deck_preview"

# palette: ink for text, slate for the judges' arms, one teal accent for what is ours, one red for lost bugs
INK, MUTED, RULE = RGBColor(0x1B, 0x26, 0x3B), RGBColor(0x5F, 0x6B, 0x7A), RGBColor(0xD9, 0xDE, 0xE5)
SLATE, SLATE_L, GREY = RGBColor(0x34, 0x49, 0x5E), RGBColor(0xA9, 0xB6, 0xC4), RGBColor(0xC4, 0xCA, 0xD1)
TEAL, TEAL_L, RED = RGBColor(0x0B, 0x8A, 0x7D), RGBColor(0xE3, 0xF3, 0xF1), RGBColor(0xC2, 0x41, 0x3B)
PAPER, CARD, DARK = RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0xF3, 0xF5, 0xF8), RGBColor(0x14, 0x1E, 0x30)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT, MONO = "Calibri", "Courier New"
W, H = Inches(13.333), Inches(7.5)
MX = Inches(0.6)                       # side margin
CW = W - 2 * MX                        # content width


# ---------------------------------------------------------------- sources
def parse_deck(text):
    slides, cur, in_notes = {}, None, False
    for line in text.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            slides[cur] = {"notes": []}
            in_notes = False
            continue
        if cur is None:
            continue
        if in_notes:
            if line.strip():
                slides[cur]["notes"].append(line.strip())
            continue
        if line.strip() == "notes:":
            in_notes = True
            continue
        m = re.match(r"^([a-z_]+): ?(.*)$", line)
        if m:
            slides[cur].setdefault(m.group(1), []).append(m.group(2))
    for s in slides.values():
        s["notes"] = " ".join(s["notes"])
    return slides


def parse_qa(text):
    qs = []
    for m in re.finditer(r"^\*\*(\d+)\. (.+?)\*\*\n(.*?)(?=^\*\*\d+\. |^\*AI use|\Z)", text, re.S | re.M):
        clean = lambda t: " ".join(t.replace("`", "").replace("**", "").replace("*", "").split())
        body = []
        for line in m.group(3).splitlines():          # a Markdown table becomes "a: b · c · d;" rows
            st = line.strip()
            if re.fullmatch(r"\|[\s:|-]+\|", st):
                continue
            if st.startswith("|") and st.endswith("|"):
                cells = [c.strip() for c in st.strip("|").split("|")]
                line = f"{cells[0]}: " + " · ".join(cells[1:]) + ";"
            body.append(line)
        qs.append((int(m.group(1)), clean(m.group(2)), clean("\n".join(body))))
    return qs


def num(s):
    s = s.strip().replace("−", "-").replace(",", "").rstrip("%")
    return float(s)


def one(spec, key, i=0):
    return spec[key][i]


def git_stamp():
    try:
        h = subprocess.run(["git", "log", "-1", "--format=%h %cs"], cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL,
                           check=True).stdout.split()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                               capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout.strip()
        return h[0] + ("+" if dirty else ""), h[1]
    except (subprocess.CalledProcessError, IndexError, OSError):
        return "unknown", ""


# ---------------------------------------------------------------- drawing helpers
class Deck:
    def __init__(self, stamp):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, H
        self.blank = self.prs.slide_layouts[6]
        self.stamp = stamp
        self.anims = []        # per slide: list of click steps, each a list of targets
        self.n = 0

    def slide(self, dark=False):
        s = self.prs.slides.add_slide(self.blank)
        self.n += 1
        bg = s.background.fill
        bg.solid()
        bg.fore_color.rgb = DARK if dark else PAPER
        self.anims.append([])
        commit, date = self.stamp
        col = SLATE_L if dark else MUTED
        text(s, MX, H - Inches(0.48), Inches(9), Inches(0.3),
             f"Ahmed & Ilyas · FAST-NUCES · LLM failure triage · commit {commit} · {date}", 10, color=col)
        text(s, W - MX - Inches(1.5), H - Inches(0.48), Inches(1.5), Inches(0.3), str(self.n), 10, color=col,
             align=PP_ALIGN.RIGHT)
        return s

    def click(self, *targets):
        self.anims[-1].append(list(targets))


def text(slide, x, y, w, h, content, size, bold=False, color=INK, align=PP_ALIGN.LEFT, font=FONT,
         anchor=MSO_ANCHOR.TOP, italic=False, space_after=0, name=None):
    """content: a string, or a list of paragraphs; a paragraph is a string or a list of (text, overrides) runs."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    paras = content if isinstance(content, list) else [content]
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        if space_after:
            para.space_after = Pt(space_after)
        runs = p if isinstance(p, list) else [(p, {})]
        for t, o in runs:
            r = para.add_run()
            r.text = t
            f = r.font
            f.name, f.size = o.get("font", font), Pt(o.get("size", size))
            f.bold, f.italic = o.get("bold", bold), o.get("italic", italic)
            f.color.rgb = o.get("color", color)
    return tb


def box(slide, x, y, w, h, fill=CARD, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08, name=None):
    sp = slide.shapes.add_shape(shape, x, y, w, h)
    if name:
        sp.name = name
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sp.adjustments[0] = radius
    sp.fill.solid()
    sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(1.25)
    sp.shadow.inherit = False
    tf = sp.text_frame
    tf.margin_left = tf.margin_right = Inches(0.18)
    tf.margin_top = tf.margin_bottom = Inches(0.12)
    tf.word_wrap = True
    return sp


def fill_text(sp, paras, size, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, space_after=4):
    tf = sp.text_frame
    tf.vertical_anchor = anchor
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        para.space_after = Pt(space_after)
        runs = p if isinstance(p, list) else [(p, {})]
        for t, o in runs:
            r = para.add_run()
            r.text = t
            f = r.font
            f.name, f.size = o.get("font", FONT), Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.color.rgb = o.get("color", color)
    return sp


def disc(slide, x, y, d, label, fill=TEAL, color=WHITE, size=16):
    c = box(slide, x, y, d, d, fill=fill, shape=MSO_SHAPE.OVAL)
    c.text_frame.margin_left = c.text_frame.margin_right = c.text_frame.margin_top = c.text_frame.margin_bottom = 0
    fill_text(c, [label], size, color=color, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    return c


def header(slide, spec, dark=False):
    text(slide, MX, Inches(0.42), CW, Inches(0.32), one(spec, "kicker"), 14, bold=True, color=TEAL)
    text(slide, MX, Inches(0.78), CW, Inches(1.2), one(spec, "title"), 28, bold=True, color=WHITE if dark else INK)


def chart(slide, x, y, w, h, cats, series, fmt="0.000", colors=None, point_colors=None, vmax=None, vmin=None,
          legend=True, label_size=13):
    cd = CategoryChartData()
    cd.categories = cats
    for name, vals in series:
        cd.add_series(name, vals)
    gf = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, w, h, cd)
    ch = gf.chart
    ch.font.name, ch.font.size = FONT, Pt(13)
    ch.font.color.rgb = INK
    ch.has_title = False
    ch.has_legend = legend and len(series) > 1
    if ch.has_legend:
        ch.legend.position = XL_LEGEND_POSITION.TOP
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(13)
    va = ch.value_axis
    lo = min(min(v) for _, v in series)
    va.minimum_scale = vmin if vmin is not None else (0 if lo >= 0 else -0.2)
    if vmax is not None:
        va.maximum_scale = vmax
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = RULE
    va.format.line.fill.background()
    va.tick_labels.font.size = Pt(11)
    va.tick_labels.font.color.rgb = MUTED
    va.tick_labels.number_format = fmt.replace("0.000", "0.0")
    va.tick_labels.number_format_is_linked = False
    ca = ch.category_axis
    ca.tick_labels.font.size = Pt(13)
    ca.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    ca.format.line.color.rgb = GREY
    ca.has_major_gridlines = False
    plot = ch.plots[0]
    plot.gap_width = 70
    plot.overlap = -8 if len(series) > 1 else 0
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format, dl.number_format_is_linked = fmt, False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size = Pt(label_size)
    dl.font.color.rgb = INK
    cols = colors or [SLATE, SLATE_L, TEAL]
    for i, s in enumerate(plot.series):
        s.invert_if_negative = False
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = cols[i % len(cols)]
        if point_colors and i == 0:
            for j, c in enumerate(point_colors):
                pt = s.points[j]
                pt.format.fill.solid()
                pt.format.fill.fore_color.rgb = c
    return gf


def callouts(slide, x, y, w, items, size=17, gap=0.22, h_each=1.0, marker=TEAL):
    shapes = []
    for i, t in enumerate(items):
        yy = y + Inches((h_each + gap) * i)
        b = box(slide, x, yy, w, Inches(h_each), fill=CARD)
        fill_text(b, [t], size, anchor=MSO_ANCHOR.MIDDLE, space_after=0)
        shapes.append(b)
    return shapes


def notes(slide, t):
    slide.notes_slide.notes_text_frame.text = t


# ---------------------------------------------------------------- animation XML
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _effect(ids, spid_xml, node):
    c0, c1, c2 = next(ids), next(ids), next(ids)
    return (f'<p:par><p:cTn id="{c0}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" grpId="0" '
            f'nodeType="{node}"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
            f'<p:set><p:cBhvr><p:cTn id="{c1}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            f'</p:cTn><p:tgtEl>{spid_xml}</p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName>'
            f'</p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>'
            f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{c2}" dur="500"/>'
            f'<p:tgtEl>{spid_xml}</p:tgtEl></p:cBhvr></p:animEffect></p:childTnLst></p:cTn></p:par>')


def _target(t):
    kind, shape = t[0], t[1]
    sid = shape.shape_id
    if kind == "para":
        return f'<p:spTgt spid="{sid}"><p:txEl><p:pRg st="{t[2]}" end="{t[2]}"/></p:txEl></p:spTgt>'
    if kind == "grid":
        return (f'<p:spTgt spid="{sid}"><p:graphicEl><a:chart seriesIdx="-3" categoryIdx="-3" bldStep="gridLegend"/>'
                f'</p:graphicEl></p:spTgt>')
    if kind == "series":
        return (f'<p:spTgt spid="{sid}"><p:graphicEl><a:chart seriesIdx="{t[2]}" categoryIdx="-4" bldStep="series"/>'
                f'</p:graphicEl></p:spTgt>')
    return f'<p:spTgt spid="{sid}"/>'


def write_timing(slide, steps):
    sld = slide._element
    for old in sld.findall(qn("p:transition")) + sld.findall(qn("p:timing")):
        sld.remove(old)
    trans = etree.fromstring(f'<p:transition xmlns:p="{P}" spd="med"><p:fade/></p:transition>')
    anchor = sld.find(qn("p:clrMapOvr"))
    anchor.addnext(trans)
    if not steps:
        return 0
    ids = iter(range(3, 100000))
    pars, builds, n = [], {}, 0
    for step in steps:
        c_outer, c_inner = next(ids), next(ids)
        inner = "".join(_effect(ids, _target(t), "clickEffect" if i == 0 else "withEffect") for i, t in enumerate(step))
        pars.append(f'<p:par><p:cTn id="{c_outer}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>'
                    f'<p:childTnLst><p:par><p:cTn id="{c_inner}" fill="hold"><p:stCondLst><p:cond delay="0"/>'
                    f'</p:stCondLst><p:childTnLst>{inner}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
        for t in step:
            n += 1
            sid = t[1].shape_id
            if t[0] in ("grid", "series"):
                builds[sid] = (f'<p:bldGraphic spid="{sid}" grpId="0"><p:bldSub><a:bldChart bld="series"/></p:bldSub>'
                               f'</p:bldGraphic>')
            elif t[0] == "para":
                builds[sid] = f'<p:bldP spid="{sid}" grpId="0" build="p"/>'
            elif t[1].shape_type is not None and t[1].has_text_frame:
                is_box = t[1]._element.tag == qn("p:sp") and t[1]._element.find(qn("p:nvSpPr")).find(
                    qn("p:cNvSpPr")).get("txBox") == "1"
                builds.setdefault(sid, f'<p:bldP spid="{sid}" grpId="0"{"" if is_box else " animBg=\"1\""}/>')
    xml = (f'<p:timing xmlns:p="{P}" xmlns:a="{A}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" '
           f'nodeType="tmRoot"><p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" '
           f'nodeType="mainSeq"><p:childTnLst>{"".join(pars)}</p:childTnLst></p:cTn><p:prevCondLst>'
           f'<p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst>'
           f'<p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
           f'</p:childTnLst></p:cTn></p:par></p:tnLst><p:bldLst>{"".join(builds.values())}</p:bldLst></p:timing>')
    trans.addnext(etree.fromstring(xml))
    return n


def chart_steps(d, gf, n_series):
    d.click(("grid", gf), ("series", gf, 0))
    for i in range(1, n_series):
        d.click(("series", gf, i))


# ---------------------------------------------------------------- slides
# Layout grid (inches): headline 0.42-1.95; content 2.15-5.85; "Why we did this" strip 6.0-6.75; footer 7.02.
CONTENT_TOP, CONTENT_BOTTOM = 2.15, 5.85


def why_box(d, s, sp):
    """The plain-English reason for the slide, last on click."""
    if "why" not in sp:
        return
    b = box(s, MX, Inches(6.0), CW, Inches(0.72), fill=TEAL_L)
    fill_text(b, [[("Why we did this   ", {"bold": True, "color": TEAL}), (one(sp, "why"), {})]], 16,
              anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    d.click(("sp", b))


def stat_block(s, x, y, w, sp, color=TEAL, size=50, label_size=17):
    """The slide's one key number, with its label under it."""
    st = one(sp, "stat")
    size = size if len(st) <= 7 else min(size, 40) if len(st) <= 10 else min(size, 32)   # one line, never wrapped
    a = text(s, x, Inches(y), w, Inches(1.0), st, size, bold=True, color=color)
    b = text(s, x, Inches(y + 1.05), w, Inches(2.4), one(sp, "statlabel"), label_size, color=INK)
    return a, b


def stat_band(d, s, sp, y, h=0.85, color=TEAL):
    """The key number as a full-width band: number left, label right."""
    band = box(s, MX, Inches(y), CW, Inches(h), fill=CARD)
    num_ = text(s, MX + Inches(0.25), Inches(y), Inches(3.2), Inches(h), one(sp, "stat"), 34, bold=True, color=color,
                anchor=MSO_ANCHOR.MIDDLE)
    lab = text(s, MX + Inches(3.5), Inches(y), CW - Inches(3.75), Inches(h), one(sp, "statlabel"), 17,
               anchor=MSO_ANCHOR.MIDDLE)
    d.click(("sp", band), ("sp", num_), ("sp", lab))


def s_title(d, sp):
    s = d.slide(dark=True)
    text(s, MX, Inches(1.35), CW, Inches(0.4), one(sp, "kicker"), 16, bold=True, color=TEAL)
    text(s, MX, Inches(1.85), Inches(11.2), Inches(2.0), one(sp, "title"), 46, bold=True, color=WHITE)
    text(s, MX, Inches(3.95), Inches(11.2), Inches(0.9), one(sp, "subtitle"), 22, color=SLATE_L)
    text(s, MX, Inches(5.3), CW, Inches(0.45), one(sp, "authors"), 22, bold=True, color=WHITE)
    text(s, MX, Inches(5.8), CW, Inches(0.4), one(sp, "affiliation"), 16, color=SLATE_L)
    notes(s, sp["notes"])


def s_hook(d, sp):
    s = d.slide()
    header(s, sp)
    code = box(s, MX, Inches(2.15), Inches(7.6), Inches(1.3), fill=DARK)
    fill_text(code, [[(c, {"font": MONO, "color": WHITE if not c.lstrip().startswith("//") else SLATE_L})]
                     for c in sp["code"]], 15, space_after=2, anchor=MSO_ANCHOR.MIDDLE)
    fail = box(s, MX, Inches(3.55), Inches(7.6), Inches(1.0), fill=RGBColor(0xFB, 0xEC, 0xEB))
    fill_text(fail, [[("Fails on the buggy version: ", {"bold": True, "color": RED}), (one(sp, "failure"), {})]], 15,
              anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    verdict = box(s, MX, Inches(4.65), Inches(7.6), Inches(1.15), fill=TEAL_L)
    fill_text(verdict, [[("It found a bug. ", {"bold": True, "color": TEAL}), (one(sp, "verdict"), {})]], 15,
              anchor=MSO_ANCHOR.MIDDLE, space_after=0)
    big, lab = stat_block(s, Inches(8.75), 2.4, Inches(3.95), sp, color=RED, size=60, label_size=18)
    d.click(("sp", code))
    d.click(("sp", fail))
    d.click(("sp", verdict))
    d.click(("sp", big), ("sp", lab))
    why_box(d, s, sp)
    notes(s, sp["notes"])


def s_problem(d, sp):
    s = d.slide()
    header(s, sp)
    a, b = stat_block(s, MX, 2.3, Inches(4.5), sp, size=60)
    d.click(("sp", a), ("sp", b))
    bl = box(s, Inches(5.7), Inches(2.15), Inches(7.0), Inches(3.7), fill=CARD)
    fill_text(bl, [[("•  ", {"color": TEAL, "bold": True}), (t, {})] for t in sp["bullet"]], 19, space_after=14,
              anchor=MSO_ANCHOR.MIDDLE)
    for i in range(len(sp["bullet"])):
        d.click(("para", bl, i))
    why_box(d, s, sp)
    notes(s, sp["notes"])


def s_glossary(d, sp):
    s = d.slide()
    header(s, sp)
    rows = [[c.strip() for c in t.split("|", 1)] for t in sp["term"]]
    gt = s.shapes.add_table(len(rows), 2, MX, Inches(2.1), CW, Inches(3.75))
    t = gt.table
    t.columns[0].width, t.columns[1].width = Inches(3.9), CW - Inches(3.9)
    for i, (term, meaning) in enumerate(rows):
        for j, v in enumerate((term, meaning)):
            c = t.cell(i, j)
            c.text = ""
            c.fill.solid()
            c.fill.fore_color.rgb = CARD if i % 2 == 0 else PAPER
            r = c.text_frame.paragraphs[0].add_run()
            r.text = v
            r.font.name, r.font.size, r.font.bold = FONT, Pt(14), j == 0
            r.font.color.rgb = TEAL if j == 0 else INK
            c.margin_left = c.margin_right = Inches(0.1)
            c.margin_top = c.margin_bottom = Inches(0.02)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
    d.click(("sp", gt))
    why_box(d, s, sp)
    notes(s, sp["notes"])


def s_gap(d, sp):
    s = d.slide()
    header(s, sp)
    n = len(sp["card"])
    gap = Inches(0.25)
    cw = (CW - gap * (n - 1)) / n
    for i, c in enumerate(sp["card"]):
        head, body, rq = [x.strip() for x in c.split("|")]
        x = MX + (cw + gap) * i
        ours = i == n - 1 and n == 4
        b = box(s, x, Inches(2.15), cw, Inches(3.7), fill=TEAL_L if ours else CARD)
        rq_id, _, rq_text = rq.partition(" ")
        fill_text(b, [[(head, {"bold": True, "size": 19, "color": TEAL if ours else INK})], [(body, {"color": MUTED})],
                      [(" ", {"size": 4})], [("Question " + rq_id[2:] + ":  ", {"bold": True, "color": TEAL}),
                                             (rq_text, {"bold": True})]], 15, space_after=8)
        b.text_frame.margin_top = Inches(0.7)
        dot = disc(s, x + Inches(0.18), Inches(2.3), Inches(0.48), str(i + 1), fill=TEAL if ours else SLATE)
        d.click(("sp", b), ("sp", dot))
    why_box(d, s, sp)
    notes(s, sp["notes"])


def s_framework(d, sp):
    s = d.slide()
    header(s, sp)
    steps = sp["step"]
    n = len(steps)
    aw = Inches(0.32)
    bw = (CW - aw * (n - 1) - Inches(0.08) * 2 * (n - 1)) / n
    y = Inches(2.2)
    for i, st in enumerate(steps):
        head, sub = [x.strip() for x in st.split("|")]
        x = MX + (bw + aw + Inches(0.16)) * i
        ours = i in (2, 3)
        b = box(s, x, y, bw, Inches(1.7), fill=TEAL if ours else CARD)
        fill_text(b, [[(head, {"bold": True, "size": 17})], [(sub, {"size": 14})]], 14,
                  color=WHITE if ours else INK, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, space_after=4)
        tgt = [("sp", b)]
        if i < n - 1:
            ar = box(s, x + bw + Inches(0.08), y + Inches(0.67), aw, Inches(0.35), fill=GREY, shape=MSO_SHAPE.RIGHT_ARROW)
            tgt.append(("sp", ar))
        d.click(*tgt)
    brace = text(s, MX + (bw + aw + Inches(0.16)) * 2, y + Inches(1.8), bw * 2 + aw + Inches(0.16), Inches(0.4),
                 "no model and no person decides a label", 14, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
    d.anims[-1][3].append(("sp", brace))
    stat_band(d, s, sp, 4.95, h=0.9)
    why_box(d, s, sp)
    notes(s, sp["notes"])


def s_arms(d, sp):
    s = d.slide()
    header(s, sp)
    n = len(sp["arm"])
    gap = Inches(0.24)
    cw = (CW - gap * (n - 1)) / n
    for i, a in enumerate(sp["arm"]):
        name, desc, budget = [x.strip() for x in a.split("|")]
        x = MX + (cw + gap) * i
        b = box(s, x, Inches(2.15), cw, Inches(1.75), fill=CARD)
        fill_text(b, [[(name, {"bold": True, "size": 20, "color": SLATE})], [(desc, {})],
                      [(budget, {"bold": True, "color": TEAL})]], 15, space_after=6)
        d.click(("sp", b))
    lines = box(s, MX, Inches(4.0), CW, Inches(0.85), fill=PAPER, line=RULE)
    fill_text(lines, [[("Baselines  ", {"bold": True, "color": TEAL}), (one(sp, "baseline"), {})],
                      [(one(sp, "levels").split(":", 1)[0] + ":  ", {"bold": True, "color": TEAL}),
                       (one(sp, "levels").split(":", 1)[1].strip(), {})]],
              16, anchor=MSO_ANCHOR.MIDDLE, space_after=4)
    d.click(("para", lines, 0))
    d.click(("para", lines, 1))
    stat_band(d, s, sp, 4.98, h=0.85)
    why_box(d, s, sp)
    notes(s, sp["notes"])


def _series(sp):
    out = []
    for c in sp["chart"]:
        name, vals = c.split("|", 1)
        out.append((name.strip(), [num(v) for v in vals.split(",")]))
    return out


def s_chart(d, sp, colors, point_colors=None, fmt="0.000", vmax=1.0, cap=None, legend=True, stat_color=TEAL):
    """Chart on the left, the slide's one key number on the right, the reason underneath."""
    s = d.slide()
    header(s, sp)
    cats = [c.strip() for c in one(sp, "cats").split(",")]
    series = _series(sp)
    y = Inches(CONTENT_TOP)
    if cap:
        text(s, MX, y, Inches(7.9), Inches(0.35), cap, 15, bold=True, color=MUTED)
        y += Inches(0.35)
    gf = chart(s, MX, y, Inches(7.9), Inches(CONTENT_BOTTOM) - y, cats, series, fmt=fmt, colors=colors,
               point_colors=point_colors, vmax=vmax, legend=legend)
    chart_steps(d, gf, len(series))
    a, b = stat_block(s, Inches(8.85), 2.35, Inches(3.88), sp, color=stat_color)
    d.click(("sp", a), ("sp", b))
    why_box(d, s, sp)
    notes(s, sp["notes"])


def s_image(d, sp):
    """A figure on the left (fade in), the key number on the right."""
    s = d.slide()
    header(s, sp)
    pic = s.shapes.add_picture(str(ROOT / one(sp, "image")), MX, Inches(2.1), height=Inches(3.8))
    d.click(("sp", pic))
    a, b = stat_block(s, Inches(8.9), 2.3, Inches(3.83), sp, size=44, label_size=16)
    d.click(("sp", a), ("sp", b))
    why_box(d, s, sp)
    notes(s, sp["notes"])


def s_kuu(d, sp):
    s = d.slide()
    header(s, sp)
    jy = [Inches(2.2 + 0.9 * i) for i in range(3)]
    js = []
    for y, j in zip(jy, sp["judge"]):
        b = box(s, MX, y, Inches(3.4), Inches(0.75), fill=CARD)
        fill_text(b, [j], 18, bold=True, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, space_after=0)
        js.append(("sp", b))
    d.click(*js)
    a1 = box(s, Inches(4.2), Inches(3.15), Inches(0.75), Inches(0.5), fill=GREY, shape=MSO_SHAPE.RIGHT_ARROW)
    rule = box(s, Inches(5.15), Inches(2.6), Inches(3.0), Inches(1.6), fill=SLATE)
    fill_text(rule, [one(sp, "rule")], 20, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
    d.click(("sp", a1), ("sp", rule))
    a2 = box(s, Inches(8.35), Inches(2.55), Inches(0.75), Inches(0.5), fill=GREY, shape=MSO_SHAPE.RIGHT_ARROW)
    yes = box(s, Inches(9.3), Inches(2.2), Inches(3.4), Inches(1.15), fill=CARD, line=GREY)
    fill_text(yes, [[("Yes  ", {"bold": True, "color": MUTED}), (one(sp, "yes"), {"bold": True})]], 22,
              anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
    a3 = box(s, Inches(8.35), Inches(3.8), Inches(0.75), Inches(0.5), fill=TEAL, shape=MSO_SHAPE.RIGHT_ARROW)
    no = box(s, Inches(9.3), Inches(3.5), Inches(3.4), Inches(1.15), fill=TEAL)
    fill_text(no, [[("No  ", {"bold": True, "color": TEAL_L}), (one(sp, "no"), {"bold": True})]], 19, color=WHITE,
              anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
    d.click(("sp", a2), ("sp", yes))
    d.click(("sp", a3), ("sp", no))
    pr = box(s, MX, Inches(4.9), CW, Inches(0.55), fill=TEAL_L)
    fill_text(pr, [one(sp, "property")], 18, bold=True, color=TEAL, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER,
              space_after=0)
    d.click(("sp", pr))
    if "origin" in sp:
        og = text(s, MX, Inches(5.5), CW, Inches(0.4), one(sp, "origin"), 14, italic=True, color=MUTED,
                  align=PP_ALIGN.CENTER)
        d.click(("sp", og))
    why_box(d, s, sp)
    notes(s, sp["notes"])


def s_cascade(d, sp):
    """Two-tier cascade diagram: three local votes -> unanimity check -> discard / keep / escalate -> frontier judge."""
    s = d.slide()
    header(s, sp)
    js = []
    for k, j in enumerate(sp["judge"]):
        b = box(s, MX, Inches(2.15 + 0.78 * k), Inches(2.9), Inches(0.66), fill=CARD)
        fill_text(b, [j], 16, bold=True, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, space_after=0)
        js.append(("sp", b))
    d.click(*js)
    a1 = box(s, Inches(3.65), Inches(2.95), Inches(0.6), Inches(0.42), fill=GREY, shape=MSO_SHAPE.RIGHT_ARROW)
    rule = box(s, Inches(4.4), Inches(2.55), Inches(2.5), Inches(1.2), fill=SLATE)
    fill_text(rule, [one(sp, "rule")], 18, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER)
    d.click(("sp", a1), ("sp", rule))
    outs = []
    for k, (key, fill, col) in enumerate((("discard", CARD, INK), ("keep", TEAL_L, TEAL), ("escalate", SLATE, WHITE))):
        y = Inches(2.15 + 0.8 * k)
        ar = box(s, Inches(7.05), y + Inches(0.17), Inches(0.5), Inches(0.36), fill=GREY, shape=MSO_SHAPE.RIGHT_ARROW)
        b = box(s, Inches(7.7), y, Inches(2.6), Inches(0.7), fill=fill, line=GREY if fill == CARD else None)
        fill_text(b, [one(sp, key)], 15, bold=True, color=col, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER,
                  space_after=0)
        outs.append((ar, b))
    d.click(("sp", outs[0][0]), ("sp", outs[0][1]), ("sp", outs[1][0]), ("sp", outs[1][1]))
    a3 = box(s, Inches(10.4), Inches(3.92), Inches(0.42), Inches(0.36), fill=TEAL, shape=MSO_SHAPE.RIGHT_ARROW)
    fr = box(s, Inches(10.9), Inches(3.4), Inches(1.83), Inches(1.15), fill=TEAL)
    fill_text(fr, [one(sp, "frontier")], 14, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER,
              space_after=0)
    d.click(("sp", outs[2][0]), ("sp", outs[2][1]), ("sp", a3), ("sp", fr))
    stat_band(d, s, sp, 4.65, h=0.8)
    if "origin" in sp:
        og = text(s, MX, Inches(5.5), CW, Inches(0.4), one(sp, "origin"), 14, italic=True, color=MUTED,
                  align=PP_ALIGN.CENTER)
        d.click(("sp", og))
    why_box(d, s, sp)
    notes(s, sp["notes"])


def s_base(d, sp):
    s = d.slide()
    header(s, sp)
    rows = [[c.strip() for c in r.split("|")] for r in sp["row"]]
    tw = Inches(7.9)
    gt = s.shapes.add_table(len(rows) + 1, 3, MX, Inches(2.15), tw, Inches(3.7))
    t = gt.table
    for j, wdt in enumerate((1.9, 2.6, 3.4)):
        t.columns[j].width = Inches(wdt)
    for i, r in enumerate([["", "Earlier papers", "This study"]] + rows):
        for j, v in enumerate(r):
            c = t.cell(i, j)
            c.text = ""
            c.fill.solid()
            c.fill.fore_color.rgb = SLATE if i == 0 else (CARD if i % 2 else PAPER)
            p = c.text_frame.paragraphs[0]
            run = p.add_run()
            run.text = v
            run.font.name, run.font.size = FONT, Pt(15)
            run.font.bold = i == 0 or j == 0
            run.font.color.rgb = WHITE if i == 0 else (TEAL if j == 2 else INK)
            c.margin_left = c.margin_right = Inches(0.1)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
    d.click(("sp", gt))
    ag = box(s, Inches(8.8), Inches(2.15), Inches(3.93), Inches(3.7), fill=TEAL_L)
    fill_text(ag, [[("Where the designs meet, we agree", {"bold": True, "color": TEAL})]] +
              [[("•  ", {"color": TEAL, "bold": True}), (a, {})] for a in sp["agree"]], 16, space_after=10)
    for i in range(1, len(sp["agree"]) + 1):
        d.click(("para", ag, i))
    d.anims[-1][1].insert(0, ("para", ag, 0))
    why_box(d, s, sp)
    notes(s, sp["notes"])


def s_threats(d, sp):
    s = d.slide()
    header(s, sp)
    rows = [[c.strip() for c in r.split("|")] for r in sp["threat"]]
    step = (CONTENT_BOTTOM - CONTENT_TOP) / len(rows)
    for i, (name, what) in enumerate(rows):
        y = Inches(CONTENT_TOP + step * i)
        b = box(s, MX, y, CW, Inches(step - 0.08), fill=CARD)
        fill_text(b, [[(name + "   ", {"bold": True, "color": SLATE}), (what, {})]], 16, anchor=MSO_ANCHOR.MIDDLE,
                  space_after=0)
        d.click(("sp", b))
    why_box(d, s, sp)
    notes(s, sp["notes"])


def s_contrib(d, sp):
    s = d.slide()
    header(s, sp)
    cw, gap = Inches(3.85), Inches(0.33)
    for i, c in enumerate(sp["contrib"]):
        head, body = [x.strip() for x in c.split("|")]
        x = MX + (cw + gap) * i
        b = box(s, x, Inches(2.15), cw, Inches(3.7), fill=TEAL_L if i == 1 else CARD)
        fill_text(b, [[(head, {"bold": True, "size": 21, "color": TEAL if i == 1 else SLATE})], [(body, {})]], 16,
                  space_after=10)
        b.text_frame.margin_top = Inches(0.8)
        dot = disc(s, x + Inches(0.18), Inches(2.3), Inches(0.5), str(i + 1), fill=TEAL if i == 1 else SLATE)
        d.click(("sp", b), ("sp", dot))
    why_box(d, s, sp)
    notes(s, sp["notes"])


def s_takeaways(d, sp):
    s = d.slide(dark=True)
    text(s, MX, Inches(0.42), CW, Inches(0.32), one(sp, "kicker"), 14, bold=True, color=TEAL)
    text(s, MX, Inches(0.78), CW, Inches(1.2), one(sp, "title"), 30, bold=True, color=WHITE)
    for i, t in enumerate(sp["take"]):
        y = Inches(2.35 + 1.0 * i)
        dot = disc(s, MX, y, Inches(0.62), str(i + 1), size=18)
        tx = text(s, MX + Inches(0.95), y, Inches(11), Inches(0.62), t, 22, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
        d.click(("sp", dot), ("sp", tx))
    notes(s, sp["notes"])


def s_divider(d, title, sub):
    s = d.slide(dark=True)
    text(s, MX, Inches(2.6), CW, Inches(1.0), title, 40, bold=True, color=WHITE)
    text(s, MX, Inches(3.7), CW, Inches(0.8), sub, 20, color=SLATE_L)
    notes(s, "Backup slides follow: first the statistics behind the main slides, then one slide per question in "
             "DEFENSE_QA. Jump to the number the panel asks about.")


def s_stats(d, sp):
    """Backup: the tests, intervals and corrections that the plain-English main slides leave out."""
    s = d.slide()
    text(s, MX, Inches(0.42), CW, Inches(0.32), one(sp, "kicker"), 14, bold=True, color=TEAL)
    text(s, MX, Inches(0.78), CW, Inches(1.2), one(sp, "title"), 26, bold=True)
    b = box(s, MX, Inches(2.1), CW, Inches(4.6), fill=CARD)
    fill_text(b, [[("•  ", {"color": TEAL, "bold": True}), (t, {})] for t in sp["line"]], 17, space_after=10)
    notes(s, sp["notes"])


def s_backup(d, n, q, a):
    s = d.slide()
    text(s, MX, Inches(0.42), CW, Inches(0.32), f"Backup · question {n}", 14, bold=True, color=TEAL)
    text(s, MX, Inches(0.78), CW, Inches(1.3), q, 26, bold=True)
    size = 22 if len(a) < 380 else 20 if len(a) < 560 else 19 if len(a) < 900 else 18 if len(a) < 1200 else 16
    b = box(s, MX, Inches(2.3), CW, Inches(4.35), fill=CARD)
    fill_text(b, [a], size, space_after=0)
    first = re.split(r"(?<=[.!?])\s", a, maxsplit=1)[0]
    notes(s, f"Lead with: {first} Then give the number on the slide, and point to the paper if pressed for detail.")


def build(render=False):
    sp = parse_deck(DECK_MD.read_text(encoding="utf-8"))
    qa = parse_qa(QA_MD.read_text(encoding="utf-8"))
    d = Deck(git_stamp())
    # story order: lost bugs -> truth -> the judges barely help -> why -> our rule -> proof -> limits -> takeaways
    s_title(d, sp["title"])
    s_hook(d, sp["hook"])
    s_problem(d, sp["problem"])
    s_glossary(d, sp["glossary"])
    s_gap(d, sp["gap"])
    s_framework(d, sp["framework"])
    s_arms(d, sp["arms"])
    s_chart(d, sp["f1"], colors=[SLATE, SLATE_L])
    s_chart(d, sp["evidence"], colors=[SLATE, SLATE_L])
    s_chart(d, sp["debate"], colors=[SLATE], point_colors=[GREY, GREY, RED, SLATE], vmax=0.25,
            cap=one(sp["debate"], "chart").split("|")[0].strip(), legend=False, stat_color=RED)
    s_chart(d, sp["thinking"], colors=[SLATE], point_colors=[GREY, GREY, RED, TEAL], vmax=1.0,
            cap=one(sp["thinking"], "chart").split("|")[0].strip(), legend=False)   # D-130/D-131
    s_chart(d, sp["ceiling"], colors=[SLATE_L, SLATE])
    s_chart(d, sp["cost"], colors=[SLATE], point_colors=[GREY, RED, RED, TEAL], fmt="0", vmax=None,
            cap=one(sp["cost"], "chart").split("|")[0].strip(), legend=False)
    s_kuu(d, sp["kuu"])
    s_chart(d, sp["kuu_d2"], colors=[SLATE], point_colors=[RED, TEAL], fmt="0", vmax=None,
            cap=one(sp["kuu_d2"], "chart").split("|")[0].strip(), legend=False)
    s_image(d, sp["tradeoff"])
    s_chart(d, sp["kuung"], colors=[SLATE], point_colors=[RED, TEAL, TEAL], fmt="0", vmax=None,
            cap=one(sp["kuung"], "chart").split("|")[0].strip(), legend=False)
    s_cascade(d, sp["cascade"])
    s_chart(d, sp["cascade_d2"], colors=[SLATE, SLATE_L], point_colors=None)
    s_base(d, sp["base"])
    s_threats(d, sp["threats"])
    s_contrib(d, sp["contributions"])
    s_takeaways(d, sp["takeaways"])
    n_main = d.n
    stats = [k for k in sp if k.startswith("stats_")]
    s_divider(d, "Backup: statistics and the hardest questions",
              f"{len(stats)} statistics slides, then {len(qa)} questions from DEFENSE_QA, in its order")
    for k in stats:
        s_stats(d, sp[k])
    for n, q, a in qa:
        s_backup(d, n, q, a)
    effects = [write_timing(slide, steps) for slide, steps in zip(d.prs.slides, d.anims)]
    print("on-click steps written per slide:", [len(st) for st in d.anims])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    d.prs.save(OUT)
    print(f"{OUT.name}: {d.n} slides ({n_main} main, {d.n - n_main} backup and divider), "
          f"{sum(effects)} entrance effects; commit {d.stamp[0]}")
    (OUT.with_suffix(".effects.txt")).write_text("\n".join(str(e) for e in effects) + "\n", encoding="utf-8")
    if render:
        render_preview(effects)


RENDER_PS = r"""
$ErrorActionPreference = "Stop"
$pp = New-Object -ComObject PowerPoint.Application
try {
  $pres = $pp.Presentations.Open("__DECK__", $true, $false, $false)
  $counts = @()
  foreach ($s in $pres.Slides) { $counts += $s.TimeLine.MainSequence.Count }
  "EFFECTS " + ($counts -join ",")
  foreach ($s in $pres.Slides) { $s.Export(("__OUT__\slide-{0:D2}.png" -f $s.SlideIndex), "PNG", 1600, 900) }
  $pres.Close()
} finally { $pp.Quit() }
"""


def render_preview(expected):
    import shutil
    from PIL import Image, ImageDraw, ImageFont
    if PREVIEW.exists():
        shutil.rmtree(PREVIEW)
    PREVIEW.mkdir(parents=True)
    ps = PREVIEW / "_render.ps1"
    ps.write_text(RENDER_PS.replace("__DECK__", str(OUT)).replace("__OUT__", str(PREVIEW)), encoding="utf-8")
    r = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps)], capture_output=True, text=True)
    ps.unlink()
    if r.returncode:
        sys.exit("PowerPoint render failed:\n" + r.stdout + r.stderr)
    got = [int(x) for x in re.search(r"EFFECTS (.*)", r.stdout).group(1).split(",")]
    print("PowerPoint opened the deck; effects per slide as PowerPoint reads them:", got)
    if got != expected:
        sys.exit(f"animation mismatch: wrote {expected}, PowerPoint reads {got}")
    # A scripted slide show cannot verify playback here: under automation PowerPoint's own reference file also
    # reports 0 clicks and does not advance. Parsing every written effect (above) is the automated check.
    pngs = sorted(PREVIEW.glob("slide-*.png"))
    cols, tw, th, pad = 4, 400, 225, 28
    rows = -(-len(pngs) // cols)
    sheet = Image.new("RGB", (cols * (tw + 12) + 12, rows * (th + pad + 12) + 12), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    for i, p in enumerate(pngs):
        im = Image.open(p).convert("RGB").resize((tw, th))
        x, y = 12 + (i % cols) * (tw + 12), 12 + (i // cols) * (th + pad + 12)
        sheet.paste(im, (x, y + pad))
        draw.rectangle([x, y + pad, x + tw - 1, y + pad + th - 1], outline=(200, 200, 200))
        draw.text((x, y + 4), f"{i + 1}", fill=(30, 30, 30), font=font)
    sheet.save(ROOT / "paper" / "DEFENSE_DECK_contact_sheet.png")
    print(f"thumbnails in {PREVIEW.relative_to(ROOT)}; contact sheet paper/DEFENSE_DECK_contact_sheet.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", action="store_true")
    build(ap.parse_args().render)
