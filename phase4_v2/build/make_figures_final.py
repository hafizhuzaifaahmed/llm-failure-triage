"""Figures for the final manuscript and deck, drawn only from committed, frozen analysis outputs.

Run from the repository root:  python phase4_v2/build/make_figures_final.py
Reads (never writes):
  results/extension/ext1_probe_analysis_CFP_D1_TEST.json        pilot (exploratory)
  results/extension/confirm/confirm_analysis_CFP_CONF_ALL.json  registered family (OSF kp79c)
  results/extension/confirm/confirm_analysis_CFP_CONF_F1_secondary.json, ..._F2_secondary.json
  results/extension/wdp/wdp_analysis.json                         WDP (exploratory, retrospective)
Writes phase4_v2/figures/fig_final_*.{pdf,png} and a CSV of every plotted value beside each figure.
No number is typed by hand: every plotted value is read from the files above.
"""
import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.getcwd()
OUT = os.path.join(ROOT, "phase4_v2", "figures")
BLUE, ORANGE, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "pdf.fonttype": 42, "savefig.dpi": 300,
})


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def save(fig, name, rows, header):
    fig.savefig(os.path.join(OUT, name + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(OUT, name + ".png"), bbox_inches="tight", dpi=220)
    with open(os.path.join(OUT, name + "_data.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    plt.close(fig)


def confirmation_figure():
    pilot = load("results/extension/ext1_probe_analysis_CFP_D1_TEST.json")["flags"]
    allf = load("results/extension/confirm/confirm_analysis_CFP_CONF_ALL.json")["family"]
    f1 = load("results/extension/confirm/confirm_analysis_CFP_CONF_F1_secondary.json")["family"]
    f2 = load("results/extension/confirm/confirm_analysis_CFP_CONF_F2_secondary.json")["family"]

    # Pilot C2 is stored as decoupled rate PF minus TF; C2 is TF minus PF, so the sign and the interval flip.
    dec = pilot["decoupled"]
    p_c2 = -dec["diff_PF_minus_TF"]
    p_c2_ci = [-dec["diff_ci95"][1], -dec["diff_ci95"][0]]

    panels = [
        ("C1: flip rate, PF minus TF", [
            ("Pilot (exploratory)", pilot["flip"]["diff_PF_minus_TF"], pilot["flip"]["diff_ci95"], "pilot"),
            ("Registered, pooled", allf["C1"]["difference"], allf["C1"]["ci95"], "reg"),
            ("  frame F1 (secondary)", f1["C1"]["difference"], f1["C1"]["ci95"], "frame"),
            ("  frame F2 (secondary)", f2["C1"]["difference"], f2["C1"]["ci95"], "frame"),
        ]),
        ("C2: decoupled rate, TF minus PF", [
            ("Pilot (exploratory)", p_c2, p_c2_ci, "pilot"),
            ("Registered, pooled", allf["C2"]["difference"], allf["C2"]["ci95"], "reg"),
            ("  frame F1 (secondary)", f1["C2"]["difference"], f1["C2"]["ci95"], "frame"),
            ("  frame F2 (secondary)", f2["C2"]["difference"], f2["C2"]["ci95"], "frame"),
        ]),
    ]
    style = {"pilot": dict(color=ORANGE, marker="D", mfc="white"),
             "reg": dict(color=BLUE, marker="o", mfc=BLUE),
             "frame": dict(color=BLUE, marker="o", mfc="white")}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.2), sharey=True)
    rows = []
    for ax, (title, items) in zip(axes, panels):
        for i, (lab, est, ci, kind) in enumerate(items):
            y = len(items) - 1 - i
            ax.plot(ci, [y, y], color=style[kind]["color"], lw=2, solid_capstyle="round")
            ax.plot([est], [y], linestyle="none", markersize=6, markeredgewidth=1.5,
                    markeredgecolor=style[kind]["color"], marker=style[kind]["marker"],
                    markerfacecolor=style[kind]["mfc"])
            ax.annotate(f"{est:+.3f}".replace("-", "−"), (ci[1], y), xytext=(4, 0), textcoords="offset points",
                        va="center", fontsize=7, color=INK)
            rows.append([title, lab.strip(), round(est, 4), round(ci[0], 4), round(ci[1], 4)])
        ax.axvline(0, color=MUTED, lw=0.8)
        ax.set_yticks(range(len(items)))
        ax.set_yticklabels([it[0] for it in reversed(items)])
        ax.set_xlim(-0.45, 1.0)
        ax.set_title(title, fontsize=8, color=INK, loc="left")
        ax.set_xlabel("difference in rates (95% bug-level CI)")
        ax.grid(axis="x", color=GRID, lw=0.6)
    fig.tight_layout()
    save(fig, "fig_final_confirmation", rows, ["panel", "row", "estimate", "ci_low", "ci_high"])


def wdp_figure():
    w = load("results/extension/wdp/wdp_analysis.json")
    rules = w["secondary"]["6_rules"]["CONF-votes"]
    names = ["KUU", "KUU+CD", "KUU+CD-U"]
    short = {"KUU": "KUU\nbaseline", "KUU+CD": "KUU + CD\nregistered", "KUU+CD-U": "KUU + CD-U\nWDP (exploratory)"}
    labels = [short[n] + f"\nbugs lost {rules[n]['bugs_lost']} of {rules[n]['bugs_with_PF']}" for n in names]
    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    rows = []
    width = 0.36
    for i, n in enumerate(names):
        r = rules[n]
        for j, (metric, col) in enumerate((("TPR", BLUE), ("TNR", ORANGE))):
            x = i + (j - 0.5) * (width + 0.03)
            ax.bar(x, r[metric], width=width, color=col, edgecolor="white", linewidth=1)
            ax.text(x, r[metric] + 0.02, f"{r[metric]:.3f}", ha="center", fontsize=6.5, color=INK)
        rows.append([n, r["TPR"], r["TNR"], r["PF_lost"], r["bugs_lost"], r["bugs_with_PF"],
                     r["upper95_bug_loss_rate"]])
    ax.set_xticks(range(3))
    ax.set_xticklabels(labels, fontsize=6.5)
    ax.set_ylim(0, 1.12)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.tick_params(axis="x", length=0, pad=3)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="TPR (bug-revealing tests kept)"),
                       Patch(color=ORANGE, label="TNR (wrong tests removed)")],
              fontsize=6.5, frameon=False, loc="upper left", bbox_to_anchor=(0, 1.2), ncol=1)
    fig.tight_layout()
    save(fig, "fig_final_wdp", rows,
         ["rule", "TPR", "TNR", "PF_lost", "bugs_lost", "bugs_with_PF", "upper95_bug_loss_rate"])


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    confirmation_figure()
    wdp_figure()
    print("wrote fig_final_confirmation and fig_final_wdp to", OUT)
