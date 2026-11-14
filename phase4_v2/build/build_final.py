"""Build the final paper and its supplement (run from the repository root).

  python phase4_v2/build/build_final.py            # LaTeX only
  python phase4_v2/build/build_final.py --all      # also regenerate figures, architecture and supplement source

The two documents cross-reference each other through the xr package. xr would also import the other
document's \\bibcite entries, which clash with each document's own numbered references, so each document reads a
filtered copy of the other's .aux that holds only \\newlabel lines (*_labels.aux).
"""
import os
import subprocess
import sys

ROOT = os.getcwd()
HERE = os.path.join(ROOT, "phase4_v2")
DOCS = ["PHASE4_FINAL_PAPER", "PHASE4_FINAL_SUPPLEMENT"]


def run(cmd, cwd=HERE):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode


def filter_aux(doc):
    src = os.path.join(HERE, doc + ".aux")
    if not os.path.exists(src):
        return
    with open(src, encoding="utf-8", errors="replace") as f:
        lines = [ln for ln in f if ln.startswith("\\newlabel")]
    with open(os.path.join(HERE, doc + "_labels.aux"), "w", encoding="utf-8") as f:
        f.writelines(lines)


def latex_round():
    for d in DOCS:
        run(["pdflatex", "-interaction=nonstopmode", d + ".tex"])
        filter_aux(d)


if __name__ == "__main__":
    if "--all" in sys.argv:
        for script in ("make_figures_final.py", "make_architecture.py", "make_supplement.py"):
            subprocess.run([sys.executable, "-I", os.path.join(HERE, "build", script)], cwd=ROOT, check=True)
    latex_round()
    for d in DOCS:
        run(["bibtex", d])
    for _ in range(3):
        latex_round()
    for d in DOCS:
        log = open(os.path.join(HERE, d + ".log"), encoding="utf-8", errors="replace").read()
        bad = [ln for ln in log.splitlines() if ln.startswith("!") or "undefined" in ln.lower()
               and "Font shape" not in ln or "multiply defined" in ln]
        print(d, "warnings/errors:", len(bad))
        for ln in bad[:15]:
            print("   ", ln)
