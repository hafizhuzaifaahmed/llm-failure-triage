"""D-70 presentation: per-project F1 is undefined (NaN) for a project with no PF in the scored set -- never 0 --
while a project with PF on which an arm scores 0 keeps its 0. The same rule feeds the Wilcoxon inputs; the
figure labels rows with their counts and lists no-PF projects in a footnote. Synthetic data."""
import math

from triage import figures, stats
from triage.analysis import Evaluation
from triage.metrics import PF, TF

# P_ok: PF and TF; P_zero: PF that every arm misses; P_nopf: TF only, and arm A predicts PF on it once
LABELS = ([{"instance_id": f"ok{n}", "label": l, "bug_name": "Bok", "project": "P_ok"} for n, l in enumerate("PTT")]
          + [{"instance_id": f"z{n}", "label": l, "bug_name": "Bz", "project": "P_zero"} for n, l in enumerate("PT")]
          + [{"instance_id": f"n{n}", "label": "TF", "bug_name": "Bn", "project": "P_nopf"} for n in range(2)])
for l in LABELS:
    l["label"] = {"P": "PF", "T": "TF"}.get(l["label"], l["label"])


def dec(iid, arm, lab, rep=0):
    return {"instance_id": iid, "arm": arm, "level": "S1", "variant": "full", "replicate": rep, "label_raw": lab,
            "cost": {}}


def decisions():
    out = []
    for arm in ("J1", "SC"):
        for rep in range(2):
            out += [dec("ok0", arm, PF, rep), dec("ok1", arm, TF, rep), dec("ok2", arm, TF, rep),
                    dec("z0", arm, TF, rep), dec("z1", arm, TF, rep),
                    dec("n0", arm, PF if (arm == "J1" and rep == 0) else TF, rep), dec("n1", arm, TF, rep)]
    return out


def test_no_pf_project_is_undefined_and_zero_stays_zero():
    ev = Evaluation(decisions(), LABELS)
    j1, sc = ev.per_project_f1("J1|S1"), ev.per_project_f1("SC|S1")
    assert math.isnan(j1["P_nopf"]) and math.isnan(sc["P_nopf"])        # J1 has an FP there: still undefined
    assert j1["P_zero"] == 0.0 and sc["P_zero"] == 0.0                  # PF present, all missed: a real 0
    assert j1["P_ok"] == 1.0
    assert ev.project_counts() == {"P_nopf": {"PF": 0, "TF": 2}, "P_ok": {"PF": 1, "TF": 2},
                                   "P_zero": {"PF": 1, "TF": 1}}


def test_wilcoxon_uses_only_projects_with_pf_and_reports_how_many_enter():
    a = {"P1": 0.5, "P2": 0.4, "P3": 0.3, "P4": float("nan"), "P5": 0.2}
    b = {"P1": 0.2, "P2": 0.4, "P3": 0.1, "P4": 0.0, "P5": 0.1}
    r = stats.wilcoxon_projects(a, b)
    assert r["n_projects"] == 4                  # P4 (undefined on one side) does not enter
    assert r["n_projects_nonzero"] == 3          # P2's zero difference is discarded by zero_method="wilcox"


def test_figure_rows_carry_counts_and_no_pf_projects_go_to_the_footnote():
    per = {"J1|S1": {"P_ok": 1.0, "P_zero": 0.0, "P_nopf": float("nan")},
           "SC|S1": {"P_ok": 0.5, "P_zero": 0.0, "P_nopf": float("nan")}}
    counts = {"P_ok": {"PF": 1, "TF": 2}, "P_zero": {"PF": 1, "TF": 1}, "P_nopf": {"PF": 0, "TF": 2}}
    rows, labels, no_pf = figures.per_project_layout(per, counts)
    assert rows == ["P_zero", "P_ok"] and labels == ["P_zero (PF 1 / TF 1)", "P_ok (PF 1 / TF 2)"]
    assert no_pf == ["P_nopf (TF 2)"]


def test_figure_renders_with_caption(tmp_path):
    per = {"J1|S1": {"P_ok": 1.0, "P_zero": 0.0, "P_nopf": float("nan")}}
    counts = {"P_ok": {"PF": 1, "TF": 2}, "P_zero": {"PF": 1, "TF": 1}, "P_nopf": {"PF": 0, "TF": 2}}
    figures.per_project(per, tmp_path / "pp", counts=counts, unscored=["Closure", "JxPath"])
    assert (tmp_path / "pp.pdf").stat().st_size > 0 and (tmp_path / "pp.png").stat().st_size > 0


def test_single_instance_rows_are_named():
    counts = {"P_ok": {"PF": 8, "TF": 3}, "Mockito": {"PF": 1, "TF": 1}, "P_one_tf": {"PF": 4, "TF": 1},
              "P_nopf": {"PF": 0, "TF": 2}}
    assert figures.single_instance_rows(["P_ok", "Mockito", "P_one_tf"], counts) == ["Mockito", "P_one_tf"]


def test_footnote_sits_below_the_axis_label(tmp_path):
    """The footnote is anchored to the x-label: its top is below the label's bottom with a gap (rendered check)."""
    per = {"J1|S1": {"P_ok": 1.0, "P_zero": 0.0, "P_nopf": float("nan")}}
    counts = {"P_ok": {"PF": 1, "TF": 2}, "P_zero": {"PF": 1, "TF": 1}, "P_nopf": {"PF": 0, "TF": 2}}
    fig, ax, note = figures.per_project(per, tmp_path / "pp", counts=counts, unscored=["Closure"], _return=True)
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    canvas = FigureCanvasAgg(fig)              # the figure was closed after saving
    canvas.draw()
    r = canvas.get_renderer()
    label, foot = ax.xaxis.label.get_window_extent(r), note.get_window_extent(r)
    assert foot.y1 < label.y0 - 8 * fig.dpi / 72     # >= 8 pt clear (the old axes-anchored layout left 3.5 pt)
