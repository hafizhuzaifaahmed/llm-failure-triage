"""Create paper/PHASE4_RESEARCH_PAPER_v2.tex from the current manuscript (P7a; the original is never written).

Each edit replaces one exactly-matched passage of the original text (an edit whose anchor is missing or not unique
stops the script), so the `_v2` file is reproducible from the committed original and this script.

    python scripts/paper/make_paper_v2.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "paper" / "PHASE4_RESEARCH_PAPER.tex"
DST = ROOT / "paper" / "PHASE4_RESEARCH_PAPER_v2.tex"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paper_v2_text import EDITS, NEW_BIB  # noqa: E402


def main():
    text = SRC.read_text(encoding="utf-8").replace("\r\n", "\n")
    for n, edit in enumerate(EDITS, 1):
        kind, old, new = edit if len(edit) == 3 else ("SUB", *edit)
        if kind == "SUB":
            c = text.count(old)
            if c != 1:
                sys.exit(f"edit {n}: anchor found {c} times: {old[:80]!r}")
            text = text.replace(old, new)
            continue
        lines = text.split("\n")
        hits = [i for i, l in enumerate(lines) if l.startswith(old)]
        if len(hits) != 1:
            sys.exit(f"edit {n}: line prefix found {len(hits)} times: {old[:80]!r}")
        i = hits[0]
        if kind == "LINE":                      # replace the whole line
            lines[i] = new
        elif kind == "APPEND":                  # keep the line, add text after it
            lines[i] = lines[i] + "\n\n" + new
        elif kind == "BEFORE":                  # add text before the line
            lines[i] = new + "\n\n" + lines[i]
        else:
            sys.exit(f"edit {n}: unknown kind {kind}")
        text = "\n".join(lines)
    DST.write_text(text, encoding="utf-8", newline="\n")
    bib = (ROOT / "paper" / "references.bib").read_text(encoding="utf-8").replace("\r\n", "\n")
    (ROOT / "paper" / "references_v2.bib").write_text(bib.rstrip("\n") + "\n\n" + NEW_BIB.strip("\n") + "\n",
                                                      encoding="utf-8", newline="\n")
    print(f"written {DST.relative_to(ROOT)} ({len(EDITS)} edits) and paper/references_v2.bib")


if __name__ == "__main__":
    main()
