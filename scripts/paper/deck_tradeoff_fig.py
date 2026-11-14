"""Deck version of the trade-off figure (D-110): seeded bugs (D2) only, plain-English labels, slide-sized fonts.

Reads results/pareto/pareto.json, the same file the paper's figure and the numbers map read, and writes
paper/figures/deck_tradeoff.png. Presentation only: no number is computed here.
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "results" / "pareto" / "pareto.json"
OUT = ROOT / "paper" / "figures" / "deck_tradeoff.png"

RED, SLATE, TEAL, GREY = "#C2413B", "#34495E", "#0B8A7D", "#7A8694"
GROUP = {"J1|S1": "single", "SC|S1": "single", "DEB|S1": "single", "TAU|S1": "tuned", "KUU|S1": "ours",
         "KUUNG|S1": "ours", "CAS|S1": "ours", "J1|S1|SON": "frontier", "DEB|S1|SON": "frontier", "KA": "base"}
NAME = {"J1|S1": "One judge", "SC|S1": "Majority of five", "DEB|S1": "Debate", "CAS|S1": "Our rule + escalation",
        "J1|S1|SON": "Frontier AI, one judge", "DEB|S1|SON": "Frontier AI, debate", "KUU|S1": "Our rule",
        "KUUNG|S1": "Our rule without Gemma", "TAU|S1": "Debate, only if\n100% sure (tuned)", "KA": "Keep\neverything"}
MAIN = {"J1|S1": (8, 4, "left"), "SC|S1": (-8, -10, "right"), "DEB|S1": (8, -8, "left"),
        "CAS|S1": (-10, 10, "right"), "DEB|S1|SON": (8, -10, "left"), "J1|S1|SON": (9, 0, "left")}
INSET = {"KUU|S1": (3.0, 8.6), "KUUNG|S1": (9.0, -1.0), "TAU|S1": (16.0, 7.4), "KA": (-1.2, 2.4)}


def main():
    pts = json.loads(SRC.read_text(encoding="utf-8"))["D2"]["points"]
    fig, ax = plt.subplots(figsize=(8.4, 4.6), dpi=200)
    ins = ax.inset_axes([0.07, 0.43, 0.48, 0.53])
    for c, g in GROUP.items():
        p = pts[c]
        x, y = 100 * p["share_discarded"], 100 * p["share_pf_lost"]
        col = {"single": RED, "tuned": GREY, "ours": TEAL, "frontier": SLATE, "base": GREY}[g]
        mk = {"single": "o", "tuned": "o", "ours": "D", "frontier": "s", "base": "o"}[g]
        for a, s in ((ax, 80), (ins, 90)):
            a.scatter(x, y, s=s, marker=mk, facecolors="none" if g == "tuned" else col, edgecolors=col,
                      linewidths=2, zorder=3)
        if c in MAIN:
            dx, dy, ha = MAIN[c]
            ax.annotate(NAME[c], (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=12, color=col, ha=ha,
                        va="center", fontweight="bold" if g == "ours" else "normal")
        if c in INSET:
            ins.annotate(NAME[c], (x, y), xytext=INSET[c], textcoords="data", fontsize=11, color=col, va="center",
                         fontweight="bold" if g == "ours" else "normal",
                         arrowprops=None if c in ("KA", "KUUNG|S1") else dict(arrowstyle="-", color=col, lw=1, shrinkA=2, shrinkB=5))
    ins.set_xlim(-1.5, 27)
    ins.set_ylim(-2, 12)
    ins.tick_params(labelsize=9)
    ins.grid(alpha=0.3)
    ins.set_facecolor("#FAFBFC")
    ins.set_title("Low-loss corner, enlarged", fontsize=10, color=GREY, loc="left")
    ax.indicate_inset_zoom(ins, edgecolor="#A9B6C4", lw=1)
    ax.set_xlim(-2, 62)
    ax.set_ylim(-2, 47)
    ax.set_xlabel("Failing tests thrown away (%): the work saved", fontsize=13)
    ax.set_ylabel("Bug-finding tests lost (%)", fontsize=13)
    ax.tick_params(labelsize=11)
    ax.grid(alpha=0.3)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200)
    print(OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
