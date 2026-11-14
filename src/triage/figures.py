"""Paper figures from analysis outputs. Static, light mode, print-first (Springer two-column width).

Colour by job (validated with the dataviz validator, light surface, --pairs all):
  identity  J1 #2a78d6 (blue), SC #eb6834 (orange), DEB #1baf7a (aqua; <3:1 contrast, so always labelled)
  SC-T      SC's orange + hatch texture (it is an SC variant; texture is the secondary encoding)
  baselines DA/KA/R0 in neutral greys with distinct hatches (they are references, not series)
  ordinal   S0/S1/S2 = blue ramp steps 250/450/650
Every figure states its data source in the caption file; a SMOKE watermark is stamped on any figure built
from mock or synthetic data so it can never be mistaken for a result.
"""
from __future__ import annotations

import math
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ARM_COLOR = {"J1": "#2a78d6", "SC": "#eb6834", "SC-T": "#eb6834", "DEB": "#1baf7a",
             "A1": "#1baf7a", "A2": "#1baf7a", "R0": "#8a8984", "DA": "#c3c2b7", "KA": "#a3a29b"}
ARM_HATCH = {"SC-T": "///", "A1": "\\\\", "A2": "xx", "R0": "", "DA": "..", "KA": "++"}
LEVEL_COLOR = {"S0": "#86b6ef", "S1": "#2a78d6", "S2": "#104281"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.family": "serif", "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5, "axes.edgecolor": INK2,
    "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "savefig.dpi": 300, "savefig.bbox": "tight", "pdf.fonttype": 42,
})


def _arm(cond: str) -> str:
    return cond.split("|")[0]


STAMP = None   # e.g. "preliminary, Tier 1 only": printed on every figure saved while set (analyze.py --status)


def _save(fig, out: Path, smoke: bool):
    if STAMP and not smoke:
        fig.text(0.0, 1.07, STAMP.upper(), ha="left", va="bottom", fontsize=7, color="#b03a2e",   # above all axes
                 transform=fig.transFigure)
    if smoke:
        fig.text(0.5, 0.5, "SMOKE TEST — MOCK DATA — NOT A RESULT", ha="center", va="center", fontsize=14,
                 color="#d03b3b", alpha=0.35, rotation=20, transform=fig.transFigure)
    out.parent.mkdir(parents=True, exist_ok=True)
    # D-70: no embedded timestamp, so a re-run writes byte-identical files (PNG carries none by default)
    fig.savefig(out.with_suffix(".pdf"), metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(out.with_suffix(".png"), metadata={"Software": None})
    plt.close(fig)


def _err(s: dict, m: str):
    lo, hi = s[f"{m}_ci95"]
    v = s[m]
    return [[max(0, v - lo)], [max(0, hi - v)]]


def prf_bars(summaries: list[dict], out: Path, smoke=False, title="Triage performance at S1 (PF = positive class)"):
    """E1: precision, recall, F1 and MCC per method with 95% bug-level cluster-bootstrap CIs. MCC sits beside F1
    because F1 alone hides chance level (keep-all has F1 0.55 at MCC 0 on a 1:2 sample; D-51)."""
    metrics = [("precision", "Precision"), ("recall", "Recall"), ("f1", "F1"), ("mcc", "MCC")]
    fig, axes = plt.subplots(1, 4, figsize=(9.0, 2.6))
    for ax, (m, lab) in zip(axes, metrics):
        for i, s in enumerate(summaries):
            a = _arm(s["condition"])
            v = 0 if (isinstance(s[m], float) and math.isnan(s[m])) else s[m]
            ax.bar(i, v, width=0.72, color=ARM_COLOR.get(a, INK2), hatch=ARM_HATCH.get(a, ""),
                   edgecolor="white", linewidth=0.8)
            if not (isinstance(s[m], float) and math.isnan(s[m])):
                ax.errorbar(i, v, yerr=_err(s, m), fmt="none", ecolor=INK, elinewidth=0.8, capsize=2)
        # values live in the results table; bars carry only CIs (no number on every mark)
        ax.set_xticks(range(len(summaries)), [_arm(s["condition"]) for s in summaries], rotation=45, ha="right")
        ax.set_title(lab)
        ax.set_ylim((-1.05, 1.05) if m == "mcc" else (0, 1.1))
        if m == "mcc":
            ax.axhline(0, color=INK2, linewidth=0.6)
    axes[0].set_ylabel("Score (mean of replicates)")
    fig.suptitle(title, y=1.02, fontsize=9)
    _save(fig, out, smoke)


def spec_levels(table: dict, out: Path, metric="f1", smoke=False):
    """E2: metric by specification level for each architecture (grouped bars, ordinal colour)."""
    arms = [a for a in ("J1", "SC", "DEB") if any(f"{a}|{lv}" in table for lv in ("S0", "S1", "S2"))]
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    w = 0.26
    for j, lv in enumerate(("S0", "S1", "S2")):
        for i, a in enumerate(arms):
            s = table.get(f"{a}|{lv}")
            if not s:
                continue
            x = i + (j - 1) * w
            ax.bar(x, s[metric], width=w - 0.03, color=LEVEL_COLOR[lv], edgecolor="white", linewidth=0.8,
                   label=lv if i == 0 else None)
            ax.errorbar(x, s[metric], yerr=_err(s, metric), fmt="none", ecolor=INK, elinewidth=0.8, capsize=1.5)
    ax.set_xticks(range(len(arms)), arms)
    ax.set_ylabel(metric.upper() if metric == "f1" else metric.capitalize())
    ax.set_ylim(0, 1.05)
    ax.legend(title="Specification", frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.18))
    _save(fig, out, smoke)


def pareto(summaries: list[dict], out: Path, smoke=False):
    """E3: F1 against consumed tokens per instance (cost-performance)."""
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    pts = []
    for s in summaries:
        if "consumed_tokens_per_instance" not in s or _arm(s["condition"]) not in ("J1", "SC", "SC-T", "DEB"):
            continue
        a = _arm(s["condition"])
        x, y = s["consumed_tokens_per_instance"] / 1000, s["f1"]
        lo, hi = s["f1_ci95"]
        ax.errorbar(x, y, yerr=[[y - lo], [hi - y]], fmt="o", ms=6, color=ARM_COLOR.get(a, INK2),
                    mec="white", mew=1.2, elinewidth=0.8, capsize=2)
        pts.append((x, y, s["condition"].replace("|", " ")))
    # D-79: arms at near-equal token cost (SC, SC-T, DEB) used to print their labels on top of each other; labels
    # now sit in a column right of the points, spaced at least `gap` apart, joined to their point by a thin leader
    xmax = max((p[0] for p in pts), default=1.0)
    gap, placed = 0.075, []
    for x, y, name in sorted(pts, key=lambda p: -p[1]):
        ly = y
        near = [py for px, py in placed if abs(px - x) < 1.5]
        while any(abs(ly - py) < gap for py in near):
            ly -= 0.01
        placed.append((x, ly))
        ax.annotate(name, (x, y), xytext=(x + 0.35, ly), textcoords="data", fontsize=6.5, color=INK,
                    va="center", arrowprops={"arrowstyle": "-", "color": INK2, "lw": 0.5, "shrinkA": 0, "shrinkB": 3})
    ax.set_xlim(right=xmax + 2.4)
    ax.set_xlabel("Consumed tokens per instance (thousands)")
    ax.set_ylabel("F1")
    ax.set_ylim(0, 1.05)
    _save(fig, out, smoke)


def forest(contrasts: list[dict], out: Path, xlabel="Δ F1 (A − B), 95% CI", smoke=False, sesoi=0.05):
    """Confirmatory contrasts or ablations: point estimate and CI, with the ±SESOI band."""
    fig, ax = plt.subplots(figsize=(3.4, 0.35 * len(contrasts) + 0.8))
    ax.axvspan(-sesoi, sesoi, color="#f0efec", zorder=0)
    ax.axvline(0, color=INK2, lw=0.8)
    for i, c in enumerate(contrasts):
        y = len(contrasts) - 1 - i
        lo, hi = c["ci95"]
        ax.plot([lo, hi], [y, y], color=INK, lw=1.2)
        ax.plot(c["delta"], y, "o", color="#2a78d6", ms=5, mec="white", mew=1)
        ax.text(1.02, y, f"{c['delta']:+.3f}", transform=ax.get_yaxis_transform(), va="center", fontsize=6.5)
    ax.set_yticks(range(len(contrasts)), [c["name"] for c in contrasts][::-1])
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    _save(fig, out, smoke)


def confusion_grid(summaries: list[dict], out: Path, smoke=False):
    n = len(summaries)
    cols = min(4, n)
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(1.75 * cols, 1.7 * rows), squeeze=False)
    for ax in axes.flat:
        ax.axis("off")
    for ax, s in zip(axes.flat, summaries):
        m = np.array([[s["TP"], s["FN"]], [s["FP"], s["TN"]]])
        tot = m.sum() or 1
        ax.imshow(m / tot, cmap=matplotlib.colors.LinearSegmentedColormap.from_list("b", ["#f7f9fc", "#2a78d6"]),
                  vmin=0, vmax=1)
        for (r, c), v in np.ndenumerate(m):
            ax.text(c, r, f"{v:.0f}", ha="center", va="center", fontsize=7,
                    color="white" if v / tot > 0.5 else INK)
        ax.set_xticks([0, 1], ["pred PF", "pred TF"], fontsize=6)
        ax.set_yticks([0, 1], ["PF", "TF"], fontsize=6)
        ax.set_title(s["condition"].replace("|", " "), fontsize=7)
        ax.axis("on")
        ax.grid(False)
    _save(fig, out, smoke)


def project_order(per_proj: dict[str, dict]) -> list[str]:
    """Projects by mean F1 over arms; ties broken by name, projects with no F1 last (D-70: no set order)."""
    def key(p):
        v = [d[p] for d in per_proj.values() if p in d and not math.isnan(d[p])]
        return (not v, float(np.mean(v)) if v else 0.0, p)
    return sorted({p for d in per_proj.values() for p in d}, key=key)


def per_project_layout(per_proj: dict[str, dict], counts: dict | None = None):
    """Rows (projects with PF, in project_order), their labels "P (PF n / TF m)", and the no-PF projects,
    whose F1 is undefined and which are listed in a footnote instead of plotted (D-70)."""
    counts = counts or {}
    no_pf = sorted(p for p in counts if counts[p]["PF"] == 0)
    rows = [p for p in project_order(per_proj) if p not in no_pf]
    labels = [f"{p} (PF {counts[p]['PF']} / TF {counts[p]['TF']})" if p in counts else p for p in rows]
    return rows, labels, [f"{p} (TF {counts[p]['TF']})" for p in no_pf]


def single_instance_rows(rows: list[str], counts: dict) -> list[str]:
    """Plotted projects whose F1 turns on a single PF or a single TF instance."""
    return [p for p in rows if p in counts and min(counts[p]["PF"], counts[p]["TF"]) <= 1]


def per_project(per_proj: dict[str, dict], out: Path, smoke=False, counts: dict | None = None,
                unscored: list | None = None, _return: bool = False):
    """R5: per-project F1 for each arm (dot plot; projects sorted by mean, ties by name). A 0 is a real 0 on a
    project with PF; projects without PF (F1 undefined) and projects without scored instances are footnoted."""
    projects, labels, no_pf = per_project_layout(per_proj, counts)
    fig, ax = plt.subplots(figsize=(3.4, 0.22 * len(projects) + 0.8))
    for k, (cond, d) in enumerate(per_proj.items()):
        a = _arm(cond)
        ps = [p for p in projects if p in d]     # plotted in the fixed order, not the dict's (D-70)
        ys = [projects.index(p) + (k - 1) * 0.18 for p in ps]
        ax.plot([d[p] for p in ps], ys, "o", ms=4, color=ARM_COLOR.get(a, INK2), mec="white", mew=0.8, label=cond)
    ax.set_yticks(range(len(projects)), labels)
    ax.set_xlabel("F1")
    ax.set_xlim(-0.02, 1)
    ax.legend(frameon=False, fontsize=6.5, loc="lower right")
    notes = []
    single = single_instance_rows(projects, counts or {})
    if single:
        notes.append("Decided by a single PF or TF instance: "
                     + ", ".join(f"{p} (PF {counts[p]['PF']} / TF {counts[p]['TF']})".replace(" ", "\u00a0")
                                 for p in single) + ".")
    if no_pf:
        nb = [x.replace(" ", "\u00a0") for x in no_pf]          # keep "Name (TF n)" on one line
        notes.append("No PF in the scored set (F1 undefined, not plotted): " + ", ".join(nb) + ".")
    if unscored:
        notes.append("Held-out projects with no scored instances: " + ", ".join(sorted(unscored)) + ".")
    note = None
    if notes:   # anchored to the bottom of the x-label (x at the axes' left), so it can never ride up into it
        note = ax.annotate("\n".join(textwrap.fill(n, 70) for n in notes), xy=(0, 0),
                           xycoords=("axes fraction", ax.xaxis.label), xytext=(-60, -10), textcoords="offset points",
                           ha="left", va="top", fontsize=6.5, color=INK2)
    _save(fig, out, smoke)
    if _return:
        return fig, ax, note
