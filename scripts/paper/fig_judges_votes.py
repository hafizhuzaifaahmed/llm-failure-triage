"""Figure for the slides and Appendix D: F1 with bug-level 95% CIs by judge and arm, and the three-family votes.

Data: results/e6b/analysis/e6b_d1test.json (family_check: M1, M2, E6b on the common D1-test S1 instances) and
results/e8/analysis/e8_d1test.json (VOTE3, VOTE5 on the same instances). No new statistic is computed here.
Arm colours are the paper's validated palette (src/triage/figures.py); marker shape is the secondary encoding because
DEB's aqua is below 3:1 contrast on the surface, and DEB and the votes carry direct value labels.

    python scripts/paper/fig_judges_votes.py   -> paper/figures/fig_judges_votes_D1.pdf and .png
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage.figures import ARM_COLOR, INK, INK2, plt  # noqa: E402

E6B = ROOT / "results" / "e6b" / "analysis" / "e6b_d1test.json"
E8 = ROOT / "results" / "e8" / "analysis" / "e8_d1test.json"
OUT = ROOT / "paper" / "figures" / "fig_judges_votes_D1"
JUDGES = (("M1", "M1 Qwen3.5 9B"), ("M2", "M2 Gemma 4 12B"), ("E6B", "E6b Ministral 3 14B"))
ARMS = (("J1", "o"), ("SC", "s"), ("DEB", "D"))


def main():
    fam = json.loads(E6B.read_text(encoding="utf-8"))["family_check"]
    e8 = json.loads(E8.read_text(encoding="utf-8"))
    rows = []                                    # (label, f1, ci, colour, marker, direct_label)
    for key, name in JUDGES:
        for arm, mk in ARMS:
            s = fam["summary"][key][arm]
            rows.append((f"{name} · {arm}", s["f1"], s["f1_ci95"], ARM_COLOR[arm], mk, arm == "DEB"))
    for v, label in (("VOTE3|S1", "VOTE3 (1 + 1 + 1 calls)"), ("VOTE5|S1", "VOTE5 (2 + 2 + 1 calls)")):
        s = e8["summary"][v]
        rows.append((label, s["f1"], s["f1_ci95"], INK, "^", True))
    ka = e8["ka_f1"]

    fig, ax = plt.subplots(figsize=(3.45, 3.3))
    ys = list(range(len(rows)))[::-1]
    for y, (label, f1, ci, col, mk, lab) in zip(ys, rows):
        ax.plot(ci, [y, y], color=col, lw=2, solid_capstyle="round", zorder=2)
        ax.plot([f1], [y], marker=mk, ms=6.5, color=col, mec="#fcfcfb", mew=1.2, zorder=3)
        if lab:
            ax.annotate(f"{f1:.2f}", (ci[1], y), xytext=(4, 0), textcoords="offset points", va="center",
                        fontsize=6.5, color=INK2)
    for b in (3, 6, 9):                            # separators between judge groups and the votes
        ax.axhline(len(rows) - b - 0.5, color="#e4e3df", lw=0.8, zorder=1)
    ax.axvline(ka, color=INK2, lw=0.8, ls=(0, (3, 2)), zorder=1)
    ax.annotate("keep-all", (ka, len(rows) - 0.4), xytext=(2, 0), textcoords="offset points", fontsize=6.5,
                color=INK2, va="bottom")
    ax.set_yticks(ys, [r[0] for r in rows])
    ax.set_xlim(0.2, 0.9)
    ax.set_ylim(-0.7, len(rows) - 0.1)
    ax.set_xlabel("F1 (PF = positive class), bug-level 95% CI")
    ax.grid(axis="y", visible=False)
    handles = [plt.Line2D([], [], marker=mk, ls="", color=ARM_COLOR[a], label=a) for a, mk in ARMS]
    handles.append(plt.Line2D([], [], marker="^", ls="", color=INK, label="vote"))
    ax.legend(handles=handles, loc="upper right", bbox_to_anchor=(1.0, 0.985), frameon=False, ncol=2,
              handletextpad=0.3, columnspacing=0.8)
    ax.set_title(f"D1-test, S1: {fam['n_instances']} instances, {fam['n_bugs']} bugs", loc="left", color=INK)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT.with_suffix(".pdf"))
    fig.savefig(OUT.with_suffix(".png"), dpi=200)
    print("wrote", OUT.with_suffix(".pdf"), OUT.with_suffix(".png"))


if __name__ == "__main__":
    main()
