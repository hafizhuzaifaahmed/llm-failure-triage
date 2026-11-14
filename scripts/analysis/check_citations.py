"""Every in-text citation must exist in the bibliography and every bibliography entry must be cited."""
import re
import sys
from pathlib import Path

paper = Path(__file__).resolve().parents[2] / "paper"
tex = (paper / "PHASE4_RESEARCH_PAPER.tex").read_text(encoding="utf-8")
bib = (paper / "references.bib").read_text(encoding="utf-8")
cited = {k.strip() for g in re.findall(r"\\cite[pt]?\{([^}]*)\}", tex) for k in g.split(",")}
keys = set(re.findall(r"^@\w+\{(\w+),", bib, re.M))
print("uncited bibliography entries:", sorted(keys - cited))
print("citations missing from bibliography:", sorted(cited - keys))
sys.exit(1 if (keys - cited) or (cited - keys) else 0)
