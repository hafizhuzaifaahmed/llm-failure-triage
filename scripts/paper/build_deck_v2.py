"""Build paper/DEFENSE_DECK_v2.pptx (P7a) as a copy of the original deck's template, following
docs/research_extension/DEFENCE_DECK_RESTRUCTURE.md: 18 main slides and 12 backup slides.

The original deck is opened read-only; its slides are dropped from the in-memory copy and new slides are built on
its Blank layout in the same palette. Every number is resolved through build_numbers_v2.py from a committed
result file (no number is typed here). No WDP result appears: slide 16 is the designed, not-run extension.

    python scripts/paper/build_deck_v2.py
"""
import importlib.util
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "paper" / "DEFENSE_DECK.pptx"
DST = ROOT / "paper" / "DEFENSE_DECK_v2.pptx"
_spec = importlib.util.spec_from_file_location("bn2", ROOT / "scripts" / "paper" / "build_numbers_v2.py")
bn2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bn2)

INK, MUTED, RULE = RGBColor(0x1B, 0x26, 0x3B), RGBColor(0x5F, 0x6B, 0x7A), RGBColor(0xD9, 0xDE, 0xE5)
TEAL, RED, SLATE = RGBColor(0x0B, 0x8A, 0x7D), RGBColor(0xC2, 0x41, 0x3B), RGBColor(0x34, 0x49, 0x5E)
AMBER = RGBColor(0xB2, 0x6B, 0x00)
TAGS = {"registered": TEAL, "exploratory": AMBER, "designed, not run": RED, "original study": SLATE, "": MUTED}
WDP_STATUS = ("Exploratory. Protocol frozen internally in Git before the run. Not externally preregistered. "
              "Designed after the confirmation outcomes were known.")
USED = {}


def N(key):
    """A number from a committed file, formatted for slides (Unicode minus)."""
    v = bn2.resolve(key, "md")
    USED[key] = v
    return v


def text(slide, x, y, w, h, s, size=16, bold=False, color=INK):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    lines = s if isinstance(s, list) else [s]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = color
        p.space_after = Pt(6)
    return tb


def table(slide, x, y, w, rows, size=12, col_w=None):
    h = Inches(0.36 * len(rows))
    t = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), h).table
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = t.cell(r, c)
            cell.text = str(val)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(size)
                p.font.bold = r == 0
    if col_w:
        for c, cw in enumerate(col_w):
            t.columns[c].width = Inches(cw)
    return t


def slide(prs, n, title, message, tag="", backup=False):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    text(s, 0.4, 0.15, 9.5, 0.4, "Ahmed & Ilyas · FAST-NUCES · LLM failure triage and a registered test of mutation "
         f"evidence · OSF {N('osf:osf_id')}", 10, color=MUTED)
    text(s, 12.4, 0.15, 0.8, 0.4, ("B" if backup else "") + str(n), 10, color=MUTED)
    text(s, 0.4, 0.55, 10.5, 0.6, title, 26, True)
    text(s, 0.4, 1.2, 12.3, 0.8, message, 16, color=SLATE)
    if tag:
        box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10.9), Inches(0.6), Inches(2.1), Inches(0.45))
        box.fill.solid()
        box.fill.fore_color.rgb = TAGS[tag]
        box.line.fill.background()
        box.text_frame.text = tag
        box.text_frame.paragraphs[0].font.size = Pt(12)
        box.text_frame.paragraphs[0].font.bold = True
        box.text_frame.paragraphs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    line = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.4), Inches(1.98), Inches(12.5), Emu(12000))
    line.fill.solid()
    line.fill.fore_color.rgb = RULE
    line.line.fill.background()
    return s


def build():
    prs = Presentation(str(SRC))
    sld = prs.slides._sldIdLst
    for sid in list(sld):                                   # drop the original slides from the in-memory copy
        prs.part.drop_rel(sid.rId)
        sld.remove(sid)

    # 1 Title
    s = slide(prs, 1, "Program fault or test fault?",
              "LLM triage of failing generated unit tests, and a registered test of mutation evidence")
    text(s, 0.4, 2.4, 12, 2.5, ["Hafiz Huzaifa Ahmed · Saad Ilyas — FAST-NUCES Islamabad",
                                f"Registered confirmation: OSF {N('osf:osf_id')} ({N('osf:registered_utc')})",
                                "Analysis commit 3b017f2; frozen engine eb2d231"], 18)
    # 2 Problem
    s = slide(prs, 2, "The problem",
              "A failing generated test is either the only evidence of a bug or noise; repair-first tools destroy "
              "the first kind", "original study")
    text(s, 0.4, 2.3, 12.3, 4, ["Generators run their own tests; most failures are wrong tests, a few reveal a real bug.",
                                "Repairing every failing assertion to the observed value, or deleting the test, hides "
                                "the bug when the program is the one that is wrong.",
                                "Question: for each failing generated test, is the test wrong (TF) or has it found a "
                                "program fault (PF)?"], 18)
    # 3 Ground truth
    s = slide(prs, 3, "What “ground truth” means here",
              "Labels come from executions, not from opinions", "original study")
    table(s, 0.6, 2.4, 12, [["Label", "Rule (Defects4J buggy B and fixed F versions)"],
                            ["PF (program fault)", "fails on B, passes on F"],
                            ["TF (test fault)", "fails on B and on F with an identical failure"],
                            ["AMB", "anything else; excluded from scoring"]], 16)
    text(s, 0.6, 4.4, 12, 1.4, "TF means “fails identically on the fixed version”: a test revealing a second real "
         "fault is labelled TF. No independent audit of TF labels exists for the confirmation.", 14, color=MUTED)
    # 4 Study 1
    s = slide(prs, 4, "Study 1: how good are LLM judges?",
              "Judged against execution labels; no confirmatory test survived Holm correction", "original study")
    table(s, 0.6, 2.4, 9, [["Arm (D1-test, M1, S1)", "F1", "MCC"],
                           ["keep-all", N("d1:KA:f1"), N("d1:KA:mcc")],
                           ["one-shot judge (J1)", N("d1:J1|S1:f1"), N("d1:J1|S1:mcc")],
                           ["self-consistency (SC)", N("d1:SC|S1:f1"), N("d1:SC|S1:mcc")],
                           ["debate (DEB)", N("d1:DEB|S1:f1"), N("d1:DEB|S1:mcc")]], 16)
    text(s, 0.6, 4.6, 12, 1.2, f"Single-judge arms lost about half of the {N('sum:prevalence:PF')} bug-revealing "
         f"tests (DEB lost {N('d1:DEB|S1:pf_lost@0')}).", 16)
    # 5 One curve
    s = slide(prs, 5, "Judge-only rules sit on one curve",
              "Voting, unanimity, debate and escalation are operating points; KUU is the keep-heavy end — the "
              "baseline", "original study")
    s.shapes.add_picture(str(ROOT / "paper" / "figures" / "fig_tradeoff_rates.png"), Inches(2.2), Inches(2.1),
                         height=Inches(4.6))
    text(s, 0.4, 6.75, 12.4, 0.5, f"KUU on D2: lost {N('kuu2:summary:KUU|S1:pf_lost@0')} of "
         f"{N('kuu2:pf_prevalence:PF')} bug-revealing tests; debate lost {N('kuu2:summary:DEB|S1:pf_lost@0')}. "
         "KUU is a baseline, not a method.", 13, color=MUTED)
    # 6 Idea
    s = slide(prs, 6, "Idea: ask the program, not another judge",
              "Run the failing test on single-edit variants of the method under test")
    text(s, 0.4, 2.3, 12.3, 4.2, [
        f"Up to {N('cfz:parameters:max_mutants_per_focal')} first-order mutants of the method under test (ROR, AOR, "
        "COR, LVR, NEG, STD); each run classified FLIP / SHIFT / SAME / ERR.",
        "flip: some edit makes the test pass (and it passes again on a re-run).",
        f"decoupled: at least {N('cfz:parameters:min_compiled_mutants_for_decoupling')} mutants compiled and no edit "
        "changes the failure at all.",
        "The executions are those of mutation-based fault localization (MUSE, Metallaxis) and unified debugging "
        "(ProFL); the question is different: they assume the failing test is right, we ask whether it is."], 17)
    # 7 Pilot
    s = slide(prs, 7, "Pilot",
              f"Flip {N('pil:flags:flip:rate_PF')} vs {N('pil:flags:flip:rate_TF')}; decoupled "
              f"{N('pil:flags:decoupled:TF_flagged')} of {N('pil:flags:decoupled:n_flagged')} wrong; "
              f"{N('pil:scored:bugs_with_PF')} bugs, labels known", "exploratory")
    table(s, 0.6, 2.4, 10, [["Pilot (D1-test)", "PF", "TF"],
                            ["tests", N("pil:scored:PF"), N("pil:scored:TF")],
                            ["with a flip", N("pil:flags:flip:PF_flagged"), N("pil:flags:flip:TF_flagged")],
                            ["decoupled", N("pil:flags:decoupled:PF_flagged"), N("pil:flags:decoupled:TF_flagged")]],
          16)
    text(s, 0.6, 4.3, 12, 1.0, f"Flip difference {N('pil:flags:flip:diff_PF_minus_TF@signed')} "
         f"{N('pil:flags:flip:diff_ci95')} — EXPLORATORY: labels known when the rules were written.", 18, True, AMBER)
    # 8 Why not stop
    s = slide(prs, 8, "Why we did not stop there", "A pilot is not evidence")
    text(s, 0.4, 2.3, 12.3, 3.5, ["The labels were known when the rules were written.",
                                  f"Only {N('pil:scored:bugs_with_PF')} bugs carried a bug-revealing test.",
                                  "One design amendment (callee mutants) was made after the first look.",
                                  "So we froze the engine and registered the claim before any new test existed."], 18)
    # 9 Design
    s = slide(prs, 9, "The registered confirmation: design",
              "Hypotheses C1–C4 in one Holm family; frames F1, F2 and a control group; frozen engine", "registered")
    table(s, 0.6, 2.3, 12, [["Step (UTC, 13 Nov 2026)", "Time", "Commit"],
                            ["registration", N("osf:registered_utc"), "OSF " + N("osf:osf_id")],
                            ["labels committed", N("atx:t labels"), "1a58e54"],
                            ["first probe run", N("atx:t probe"), "—"],
                            ["probe ledgers committed", N("atx:t ledger"), "b332305"],
                            ["first judge vote", N("atx:t vote"), "—"],
                            ["analysis committed", N("atx:t analysis"), "3b017f2"]], 14)
    text(s, 0.6, 5.1, 12, 1.5, ["C1 flip rate PF − TF · C2 decoupled rate TF − PF · C3 KUU + CD vs KUU (balanced "
                                "accuracy) · C4 2-of-3 + CK vs 2-of-3 (PF lost)",
                                "A commit time shows the order of recording, not when a file was read."], 14, color=MUTED)
    # 10 Population
    s = slide(prs, 10, "Population",
              f"{N('cman:generation_calls_total')} generation calls → {N('cc:population:instances')} scored failing "
              f"tests ({N('cc:population:PF')} PF, {N('cc:population:TF')} TF), {N('cc:population:bugs')} bugs, "
              f"{N('cc:population:bugs_with_PF')} with a PF test", "registered")
    table(s, 0.6, 2.3, 12, [["Tranche", "Calls", "Failing", "PF", "TF", "AMB"],
                            ["F1", N("cman:tranches:F1:generation_calls"), N("dsf1:instances"), N("dsf1:labels:PF"),
                             N("dsf1:labels:TF"), N("dsf1:labels:AMB")],
                            ["F2", N("cman:tranches:F2:generation_calls"), N("dsf2:instances"), N("dsf2:labels:PF"),
                             N("dsf2:labels:TF"), N("dsf2:labels:AMB")],
                            ["CTRL", N("cman:tranches:CTRL:generation_calls"), N("dsct:instances"), N("cc:control:PF"),
                             N("dsct:labels:TF"), "—"]], 15)
    text(s, 0.6, 4.4, 12, 1.4, f"Shortfall: {N('cc:population:bugs_with_PF')} bugs with a PF test against a planned "
         f"{N('atx:plan lo')}–{N('atx:plan hi')} (D-145). {N('cc:population:bugs')} of {N('atx:frame bugs')} frame bugs "
         "produced a scored failing test.", 18, True, RED)
    # 11 C1
    s = slide(prs, 11, "Result 1: flip did not replicate",
              f"C1 {N('cc:family:C1:difference@signed')} {N('cc:family:C1:ci95')}, Holm p "
              f"{N('cc:family:C1:p_holm@4')}; the pilot's {N('pil:flags:flip:diff_PF_minus_TF')} is excluded",
              "registered")
    cd = CategoryChartData()
    cd.categories = ["bug-revealing (PF)", "wrong (TF)", "control failures"]
    cd.add_series("flip rate", (float(bn2.raw("dv:flip rate pf")), float(bn2.raw("dv:flip rate tf")),
                                float(bn2.raw("cc:control:flip_rate_TF"))))
    ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(2.2), Inches(7.5), Inches(4.4),
                            cd).chart
    ch.has_legend = False
    pl = ch.plots[0]
    pl.has_data_labels = True
    pl.data_labels.number_format = "0.000"
    pl.data_labels.number_format_is_linked = False
    pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    ch.value_axis.maximum_scale = 0.5
    text(s, 8.4, 2.3, 4.6, 4.4, [f"Control interval {N('cc:control:flip_rate_TF_ci95')}.",
                                 f"Half the pilot's effect ({N('dv:pilot half@3')}) is not excluded.",
                                 "“Did not replicate” — not proof of no effect.",
                                 f"D-145: {N('cc:population:bugs_with_PF')} bugs, planned "
                                 f"{N('atx:plan lo')}–{N('atx:plan hi')}.",
                                 "A flip is a mutation outcome, not a repair."], 15)
    # 12 C2
    s = slide(prs, 12, "Result 2: decoupling held, with limits",
              f"Pooled {N('cc:family:C2:difference@signed')} {N('cc:family:C2:ci95')}, Holm p "
              f"{N('cc:family:C2:p_holm@4')}; {N('cc:family:C2:TF_flagged')} of {N('dv:dec flagged')} flagged tests "
              "are wrong", "registered")
    table(s, 0.6, 2.3, 9, [["C2", "Estimate", "95% CI"],
                           ["pooled (registered)", N("cc:family:C2:difference@signed"), N("cc:family:C2:ci95")],
                           ["F1 (registered secondary)", N("cf1:family:C2:difference@signed"),
                            N("cf1:family:C2:ci95@ci2")],
                           ["F2 (registered secondary)", N("cf2:family:C2:difference@signed"),
                            N("cf2:family:C2:ci95@ci2")]], 16)
    text(s, 0.6, 4.2, 12, 1.5, "Not reproduced in F1. Per-frame limits to two decimals: bootstrap limits carry "
         "Monte Carlo error.", 16, color=MUTED)
    # 13 Where it holds
    s = slide(prs, 13, "Where it holds",
              f"{N('arow:jackson dec tf')} of {N('cc:family:C2:TF_flagged')} decoupled wrong tests are in two "
              f"projects; without them {N('atx:noJ est@signed')} {N('atx:noJ ci')}", "exploratory")
    table(s, 0.6, 2.3, 12, [["Subset (exploratory)", "C2", "95% CI"],
                            ["all", N("cc:family:C2:difference@signed"), N("cc:family:C2:ci95")],
                            ["without JacksonDatabind", N("atx:noJDB est@signed"), N("atx:noJDB ci")],
                            ["without both Jackson projects", N("atx:noJ est@signed"), N("atx:noJ ci")],
                            ["resampling projects (indicative)", "", N("atx:projboot ci")]], 15)
    text(s, 0.6, 4.5, 12, 1.6, [f"Wrong tests decoupled: F1 {N('dv:f1 dec tf rate@3')}, F2 {N('dv:f2 dec tf rate@3')}.",
                                "Mostly exceptions raised outside the method under test. Precision transferred; "
                                "yield did not."], 15)
    # 14 Rules
    s = slide(prs, 14, "Rules: inconclusive",
              f"C3 Holm p {N('cc:family:C3:p_holm@4')}; C4 Holm p {N('cc:family:C4:p_holm@4')}; keep certificate: "
              "no support", "registered")
    rows = [["Rule", "TPR", "TNR", "Bugs lost", "Bound", "Bal. acc."]]
    for r in ("KUU", "KUU+CD", "2-of-3", "2-of-3+CK"):
        rows.append([r + (" (baseline)" if r == "KUU" else ""), N(f"cc:rules:{r}:TPR@3"), N(f"cc:rules:{r}:TNR@3"),
                     f"{N(f'cc:rules:{r}:bugs_lost')} / {N(f'cc:rules:{r}:bugs_with_PF')}",
                     N(f"cc:rules:{r}:upper95_bug_loss_rate@3"), N(f"cc:rules:{r}:BA@3")])
    table(s, 0.6, 2.3, 12, rows, 15)
    text(s, 0.6, 4.3, 12, 1.4, f"rcf (keep certificate) set for {N('cc:secondary:rcf_in_place_of_flip:PF_flagged')} "
         f"of {N('cc:population:PF')} PF and {N('cc:secondary:rcf_in_place_of_flip:TF_flagged')} of "
         f"{N('cc:population:TF')} TF tests. KUU + CD lost one bug (Math_59).", 15)
    # 15 Surviving signal
    s = slide(prs, 15, "What the surviving signal is",
              "Both lost bugs are edits the operators could not make", "exploratory")
    text(s, 0.4, 2.3, 12.3, 4, [
        f"Math_59 — FastMath.max(float,float), assertion failure: exactly {N('arow:math59 ncomp')} compiled mutants, "
        "all silent.",
        "Codec_13 (pilot) — a replaced call: no operator touches it.",
        f"The ten-mutant minimum shields {N('atx:minshield pf')} bug-revealing tests (and {N('atx:minshield tf')} wrong "
        "ones) that no mutant changes.",
        "The flag conflates “does not depend on this method” with “our edits could not reach it”."], 17)
    # 16 Extension (designed, not run)
    s = slide(prs, 16, "Planned: a direct dependence test",
              "Replace the whole method: is it entered, and does the failure change at all?", "designed, not run")
    text(s, 0.4, 2.3, 12.3, 2.6, [
        "Design only: a body that records entry and throws, and fixed-return bodies; a ladder from first-order "
        "sensitive to “no entry observed, throw-invariant” — never “unreachable”.",
        "Protocol and implementation committed before any evaluation run. Not yet evaluated: no result is shown."], 17)
    text(s, 0.4, 5.0, 12.3, 1.2, WDP_STATUS, 16, True, RED)
    # 17 Claims
    s = slide(prs, 17, "What we claim, and what we do not", "")
    text(s, 0.4, 1.4, 6.1, 5.6, ["We claim"] + [
        "• an execution-grounded measurement of LLM triage with lost bugs as an outcome;",
        "• a registered result that a test-passing single edit is not evidence that the test is right;",
        f"• a registered result that a failure no single edit changes was a wrong test in "
        f"{N('cc:family:C2:TF_flagged')} of {N('dv:dec flagged')} cases, in one sampling frame and mostly two projects;",
        f"• a base rate: a single small edit makes a failing generated test pass for {N('cc:control:flip_rate_TF@3')} "
        f"(control), {N('cc:control:flip_rate_TF_in_F1F2@3')} (wrong) and {N('cc:control:flip_rate_PF_in_F1F2@3')} "
        "(right) of failures, whoever is at fault."], 14)
    text(s, 6.8, 1.4, 6.1, 5.6, ["We do not claim"] + [
        "• a new triage method, or that the certificates are safe;",
        "• that the decoupling effect generalises across frames or projects;",
        "• that C3 is significant or that the keep certificate works;",
        "• that the control methods are correct;",
        "• novelty of the mechanism: the executions are those of MUSE, Metallaxis and ProFL;",
        "• that the exploratory extension is preregistered or confirmed."], 14)
    # 18 Limitations
    s = slide(prs, 18, "Limitations and next steps", "")
    text(s, 0.4, 1.5, 12.3, 5, [
        f"One benchmark, one generator; {N('cc:population:bugs_with_PF')} bugs with a bug-revealing test; no label "
        "audit; e-Otter++ not reproduced.",
        "Intervals resample bugs, not projects; percentile intervals with few clusters are approximate.",
        "Next: a fresh registered test of the dependence check on tests from a second generator; an LLM-patch arm "
        "without an issue report; an independent label audit."], 18)

    # Backups
    s = slide(prs, 1, "Registration details", f"OSF {N('osf:osf_id')}, {N('osf:registered_utc')}", "registered", True)
    text(s, 0.4, 2.3, 12.3, 4.5, [
        "Governs: the attached document and the frozen code it contains; template fields were reworded at deposit and "
        "their reconciliation is pending.",
        f"One Holm family C1–C4, α 0.05; bug-level bootstrap, {N('cc:resamples')} resamples, seed {N('cc:seed')}.",
        "Counting against the method: (1) C1 not supported — yes; (2) C2 reversed or below the pilot — no; (3) a "
        "certificate losing more than one extra bug — no; (4) control flip rate close to the PF rate — no numeric "
        "threshold; the PF rate lies inside the control interval (a reading)."], 16)
    s = slide(prs, 2, "Power planning and the realized sample", "Was it underpowered?", "registered", True)
    text(s, 0.4, 2.3, 12.3, 4, [
        f"Planned {N('atx:plan lo')}–{N('atx:plan hi')} bugs with a PF test; realized {N('cc:population:bugs_with_PF')} "
        "(D-145).",
        f"C1's interval half-width {N('dv:c1 halfwidth@3')} equals the planned width at {N('atx:plan lo')} bugs; it "
        "excludes the pilot's estimate and includes half of it.",
        "C2–C4 are further below plan than registered; their non-support (C3, C4) is inconclusive."], 17)
    s = slide(prs, 3, "Control group", "Is the control defect-free? No.", "registered", True)
    text(s, 0.4, 2.3, 12.3, 4, [
        "One method per bug in the same class that the fix did not change (public or protected, identical in both "
        "versions, matched on mutant count).",
        f"{N('cc:control:instances')} failures, all TF, from {N('cc:control:bugs')} bugs; flip "
        f"{N('cc:control:flip_rate_TF@3')} {N('cc:control:flip_rate_TF_ci95')}; decoupled "
        f"{N('cc:control:decoupled_rate_TF@3')}.",
        "It answers one question: how often a flip occurs away from the repaired method."], 17)
    s = slide(prs, 4, "Registered secondary analyses", "None replaces a primary result", "registered", True)
    rows = [["Analysis", "Estimate", "95% CI", "PF", "TF"]]
    for k, lab in (("rcf_in_place_of_flip", "rcf for flip"), ("guarded_decoupling", "guarded decoupling"),
                   ("clean_operator_flip", "clean-operator flip"), ("focal_body_only_flip", "focal-body-only flip"),
                   ("shared_flip", "shared flip")):
        rows.append([lab, N(f"cc:secondary:{k}:difference@signed"), N(f"cc:secondary:{k}:ci95"),
                     N(f"cc:secondary:{k}:PF_flagged"), N(f"cc:secondary:{k}:TF_flagged")])
    table(s, 0.6, 2.3, 12, rows, 14)
    s = slide(prs, 5, "Frames F1 and F2", "Why do the frames differ?", "exploratory", True)
    text(s, 0.4, 2.3, 12.3, 4, [
        "F1: the original frame's methods of unseen bugs. F2: fix-changed methods no bug-triggering test calls by name.",
        f"F1 wrong tests: {N('dv:f1 tf assert share@pct0')} assertion failures. F2 wrong tests: "
        f"{N('dv:f2 tf exc share@pct0')} exceptions.",
        f"An exception-outside-the-method rule would discard {N('atx:stack pf')} PF and {N('atx:stack tf')} TF tests; "
        f"the flag discards {N('cc:family:C2:PF_flagged')} and {N('cc:family:C2:TF_flagged')}."], 17)
    s = slide(prs, 6, "Positioning", "How is this different from X?", "", True)
    table(s, 0.4, 2.2, 12.5, [["Work", "Variants", "Failing test assumed", "Inference"],
                              ["MUSE", "first-order mutants", "right", "where the fault is"],
                              ["Metallaxis", "first-order mutants", "verdict taken as given", "where the fault is"],
                              ["ProFL", "repair-tool patches", "the suite is the oracle", "where the fault is"],
                              ["e-Otter++ (not reproduced)", "LLM patches from the issue", "should fail on old code",
                               "which candidate to return"],
                              ["Pseudo-tested methods", "whole-body replacement", "— (passing suites)",
                               "does the suite notice"],
                              ["This study", "first-order mutants", "in question", "which side is at fault"]], 13)
    s = slide(prs, 7, "Independent audit", "Can we trust the numbers?", "", True)
    text(s, 0.4, 2.3, 12.3, 4, [
        "Every registered count, estimate, interval, p-value, Holm step, rule row and bound recomputed from raw "
        "records with independent code: no discrepancy; registered intervals reproduced exactly with the registered "
        "seed.",
        f"Labels recomputed from raw runs: {N('atx:labels recomputed')} of {N('atx:a6 records')}. Ledger flags: "
        f"{N('atx:a6 mismatches')} mismatches. Concatenation sources: {N('atx:a7 sources')} matched. Sealing checks: "
        f"{N('atx:a8 pass')} passed.",
        "Blinding: verified by inspection and a source scan; three scan patterns were ineffective."], 16)
    s = slide(prs, 8, "Stage B", "Why not put the probe report in the judge's prompt?", "designed, not run", True)
    text(s, 0.4, 2.3, 12.3, 3, ["Designed before the confirmation outcomes; pre-specified, unregistered, not run.",
                                "Two of the report's three lines describe flips, which carried no signal; the third "
                                "restates a rule that costs nothing to apply outside the model."], 17)
    s = slide(prs, 9, "An e-Otter++-style baseline", "Why no patch baseline?", "designed, not run", True)
    text(s, 0.4, 2.3, 12.3, 4, ["e-Otter++ needs an issue report and LLM patches written without seeing the tests; "
                                "this setting has no report.",
                                "A fair version: patches from documentation and signature only, a frozen generator, "
                                "a repair prompt developed on the development projects, the same tests and labels.",
                                "Not run before the deadline; listed as future work."], 17)
    s = slide(prs, 10, "Evidence status", "Confirmatory vs exploratory", "", True)
    table(s, 0.4, 2.2, 12.5, [["Result", "Status"],
                              ["Measurement RQ1–RQ3", "confirmatory family of the original study"],
                              ["RQ4, KUU", "fixed in advance on D2; KUU is a baseline"],
                              ["C1–C4, rule table, control, registered secondaries", "confirmatory, registered (OSF "
                               + N("osf:osf_id") + ")"],
                              ["Pilot; audit analyses", "exploratory"],
                              ["Stage B", "designed before the outcomes; pre-specified, unregistered, not run"],
                              ["Whole-method dependence probes", "exploratory; frozen internally in Git; not externally "
                               "preregistered; designed after the outcomes; not evaluated"]], 13)
    s = slide(prs, 11, "Cost", "Practicality", "", True)
    text(s, 0.4, 2.3, 12.3, 3, ["Probes: CPU only, no model; one fresh JVM per mutant run.",
                                "Votes: three local judges, one call each, on the study GPU.",
                                "Per-test seconds are in the committed run logs; not restated here."], 17)
    s = slide(prs, 12, "Per project", "Leave-one-project-out (registered) and the pilot's concentration", "", True)
    lopo = bn2.raw("cc:secondary:leave_one_project_out")
    rows = [["Left out (registered)", "C1", "C2"]] + [
        [p, N(f"cc:secondary:leave_one_project_out:{p}:C1@signed"), N(f"cc:secondary:leave_one_project_out:{p}:C2@signed")]
        for p in sorted(lopo)]
    table(s, 0.4, 2.1, 7.2, rows, 11)
    text(s, 7.9, 2.2, 5.0, 4, [f"Pilot (exploratory): {N('atx:pilot chart flip')} of {N('pil:flags:flip:PF_flagged')} "
                               f"flipping PF tests were in Chart ({N('atx:pilot chart flip')} of "
                               f"{N('atx:pilot chart pf')}); Math had {N('atx:pilot math flip')} of "
                               f"{N('atx:pilot math pf')}."], 15)
    prs.save(str(DST))
    print(f"written {DST.relative_to(ROOT)}: {len(prs.slides)} slides, {len(USED)} numbers resolved")


if __name__ == "__main__":
    build()
