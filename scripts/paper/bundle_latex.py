"""Bundle the paper's editable LaTeX source (the Phase 4 brief asks for the PDF and its source) into one zip that compiles
on its own, e.g. on Overleaf or with `latexmk -pdf PHASE4_RESEARCH_PAPER.tex`.

    python scripts/paper/build_numbers.py && python scripts/paper/bundle_latex.py   -> paper/PHASE4_LATEX_SOURCE.zip

Included: the .tex, the bibliography and its style, the class, the generated number definitions, every figure and table
file the .tex references. Build byproducts (.aux, .log, ...) are left out.
"""
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper"
TEX = PAPER / "PHASE4_RESEARCH_PAPER.tex"
OUT = PAPER / "PHASE4_LATEX_SOURCE.zip"


def referenced(tex: str) -> set[str]:
    out = set()
    for cmd in ("includegraphics", "input", "include", "bibliography", "bibliographystyle", "documentclass"):
        for m in re.finditer(r"\\" + cmd + r"(?:\[[^\]]*\])?\{([^}]+)\}", tex):
            for name in m.group(1).split(","):
                out.add((cmd, name.strip()))
    return out


def resolve(cmd: str, name: str) -> list[Path]:
    exts = {"includegraphics": ["", ".pdf", ".png"], "input": ["", ".tex"], "include": [".tex"],
            "bibliography": [".bib"], "bibliographystyle": [".bst"], "documentclass": [".cls"]}[cmd]
    for e in exts:
        for base in (PAPER, PAPER / "bst"):
            p = base / (name + e)
            if p.is_file():
                return [p]
    return []


def main():
    tex = TEX.read_text(encoding="utf-8")
    files, missing = {TEX}, []
    for cmd, name in sorted(referenced(tex)):
        found = resolve(cmd, name)
        if found:
            files.update(found)
        elif cmd not in ("documentclass", "bibliographystyle") and name not in ("glyphtounicode",):  # TeX system file
            missing.append(f"\\{cmd}{{{name}}}")
    if missing:
        raise SystemExit("referenced but not found: " + ", ".join(missing))
    opts = re.search(r"\\documentclass\[([^\]]*)\]", tex)
    for o in (opts.group(1).split(",") if opts else []):       # sn-jnl names its .bst as a class option
        if (PAPER / f"{o.strip()}.bst").is_file():
            files.add(PAPER / f"{o.strip()}.bst")
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):
            z.write(p, p.relative_to(PAPER).as_posix())
    print(f"{OUT.relative_to(ROOT)}: {len(files)} files")
    for p in sorted(files):
        print("  ", p.relative_to(PAPER).as_posix())


if __name__ == "__main__":
    main()
