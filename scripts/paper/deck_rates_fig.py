"""Deck version of the rates figure (D-113, made the main trade-off figure by the authors' decision in D-130): seeded
bugs (D2) only, plain-English labels, slide-sized fonts.

Reads results/revision/wp11_rates.json (and, if present, results/revision/think_followup.json for the
thinking-judge star), the same files the paper's figure and the numbers map read, and writes
paper/figures/deck_rates.png. Presentation only: no number is computed here.
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "results" / "revision" / "wp11_rates.json"
THINK = ROOT / "results" / "revision" / "think_followup.json"
OUT = ROOT / "paper" / "figures" / "deck_rates.png"

RED, SLATE, TEAL, GREY, PURPLE = "#C2413B", "#34495E", "#0B8A7D", "#7A8694", "#7B3FA0"
GROUP = {"J1|S1": "single", "SC|S1": "single", "DEB|S1": "single", "TAU|S1": "tuned", "KUU|S1": "ours",
         "KUUNG|S1": "ours", "CAS|S1": "ours", "J1|S1|SON": "frontier", "DEB|S1|SON": "frontier", "KA": "base",
         "DA": "base"}
NAME = {"J1|S1": "One judge", "SC|S1": "Majority of five", "DEB|S1": "Debate", "CAS|S1": "Our rule\n+ escalation",
        "J1|S1|SON": "Frontier AI,\none judge", "DEB|S1|SON": "Frontier AI,\ndebate", "KUU|S1": "Our rule",
        "KUUNG|S1": "Our rule\nwithout Gemma", "TAU|S1": "Debate, only if\n100% sure (tuned)",
        "KA": "Keep everything", "DA": "Throw everything away"}
# label offsets in points: (dx, dy, ha)
OFF = {"J1|S1": (10, 0, "left"), "SC|S1": (0, -18, "center"), "DEB|S1": (0, 16, "center"), "TAU|S1": (12, 14, "left"),
       "KUU|S1": (12, -6, "left"), "KUUNG|S1": (12, -12, "left"), "CAS|S1": (-10, 0, "right"),
       "J1|S1|SON": (10, -6, "left"), "DEB|S1|SON": (0, 22, "center"), "KA": (10, 0, "left"), "DA": (-10, 0, "right")}


def thinking_d2():
    if not THINK.exists():
        return None
    d = json.loads(THINK.read_text(encoding="utf-8")).get("d2", {}).get("descriptive", {}).get("Thinking M1 J1")
    if not d:
        return None
    return 100 * (1 - d["tpr"]), 100 * d["tnr"]


def main():
    rules = json.loads(SRC.read_text(encoding="utf-8"))["D2"]["rules"]
    fig, ax = plt.subplots(figsize=(8.4, 4.6), dpi=200)
    for c, g in GROUP.items():
        p = rules[c]
        x, y = 100 * p["pf_loss_rate"], 100 * p["tnr"]
        col = {"single": RED, "tuned": GREY, "ours": TEAL, "frontier": SLATE, "base": GREY}[g]
        mk = {"single": "o", "tuned": "o", "ours": "D", "frontier": "s", "base": "o"}[g]
        ax.scatter(x, y, s=90, marker=mk, facecolors="none" if g == "tuned" else col, edgecolors=col,
                   linewidths=2, zorder=3)
        dx, dy, ha = OFF[c]
        ax.annotate(NAME[c], (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=11, color=col,
                    ha=ha, va="center", fontweight="bold" if g == "ours" else "normal")
    tp = thinking_d2()
    if tp is not None:
        ax.scatter(*tp, s=260, marker="*", color=PURPLE, zorder=4)
        ax.annotate("One judge,\nthinking on", tp, xytext=(4, -14), textcoords="offset points",
                    fontsize=11, color=PURPLE, ha="left", va="top")
    ax.plot([0, 100], [0, 100], ls=":", lw=1, color="#9AA3AD", zorder=1)
    ax.set_xlim(-3, 103)
    ax.set_ylim(-3, 103)
    ax.set_xlabel("Bug-finding tests lost (%)  →  worse", fontsize=12)
    ax.set_ylabel("Wrong tests removed (%)  →  better", fontsize=12)
    ax.grid(alpha=0.25)
    ax.tick_params(labelsize=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT, dpi=200)
    print(OUT)


if __name__ == "__main__":
    main()
