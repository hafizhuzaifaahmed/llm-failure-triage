"""Independent numeric audit of the final paper and deck (run from the repository root).

Reads the frozen analysis JSON directly (it does NOT use build_numbers_v2.py or numbers_v2.tex), formats each
headline value the way the paper prints it, and checks that the string occurs in the text of
PHASE4_FINAL_PAPER.pdf (via pdftotext) and in DEFENSE_DECK_FINAL.pptx (via python-pptx).
Writes nothing; prints one line per check and exits non-zero on any miss.
"""
import json
import os
import subprocess
import sys

from pptx import Presentation

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.getcwd()
P4 = os.path.join(ROOT, "phase4_v2")


def j(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def num(x, d=3, signed=False):
    s = f"{x:+.{d}f}" if signed else f"{x:.{d}f}"
    return s.replace("-", "−")


def ci(c, d=3):
    return "[" + num(c[0], d) + ", " + num(c[1], d) + "]"


fam = j("results/extension/confirm/confirm_analysis_CFP_CONF_ALL.json")
F, pop = fam["family"], fam["population"]
w = j("results/extension/wdp/wdp_analysis.json")
conf = {r["name"]: r for r in j("results/heldout/analysis_final/D1_M1/tables/confirmatory.json")["f1"]}
lvl = w["secondary"]["3_level_U_by_label"]["CONF-all"]["U"]

checks = [
    ("C1 estimate", num(F["C1"]["difference"], signed=True)), ("C1 CI", ci(F["C1"]["ci95"])),
    ("C2 estimate", num(F["C2"]["difference"], signed=True)), ("C2 CI", ci(F["C2"]["ci95"])),
    ("C2 Holm p", num(F["C2"]["p_holm"], 4)), ("C3 Holm p", num(F["C3"]["p_holm"], 4)),
    ("C4 Holm p", num(F["C4"]["p_holm"], 4)),
    ("confirmation tests", str(pop["instances"])), ("confirmation bugs", str(pop["bugs"])),
    ("bugs with PF", str(pop["bugs_with_PF"])),
    ("WDP TNR gain", num(w["primary"]["paired"]["TNR"]["difference"], signed=True)),
    ("WDP CI", ci(w["primary"]["paired"]["TNR"]["ci95"])),
    ("WDP bound", num(w["pooled_bound"]["upper95"])),
    ("level U PF", f"{lvl['PF_flagged']} of {lvl['PF']}"),
] + [(h + " Holm p", num(conf[h]["p_holm"])) for h in ("H1", "H2a", "H2b", "H3a", "H3b")] + [
    (h + " delta", num(conf[h]["delta"], signed=True)) for h in ("H1", "H2a", "H2b", "H3a", "H3b")]

pdf = subprocess.run(["pdftotext", "-enc", "UTF-8", os.path.join(P4, "PHASE4_FINAL_PAPER.pdf"), "-"], capture_output=True,
                     text=True, encoding="utf-8").stdout
pdf = " ".join(pdf.replace("-\n", "-").split())
deck = []
for s in Presentation(os.path.join(P4, "DEFENSE_DECK_FINAL.pptx")).slides:
    for sh in s.shapes:
        if sh.has_text_frame:
            deck.append(sh.text_frame.text)
deck = " ".join(" ".join(deck).split())

# The PDF prints U+2212 for minus; pdftotext may return either form.
pdf_n = pdf.replace("-", "−")
miss = 0
for name, val in checks:
    in_pdf = val in pdf_n
    in_deck = val in deck or val.replace("−", "-") in deck
    print(f"{name:20s} {val:22s} paper={'ok' if in_pdf else 'MISSING'}  deck={'ok' if in_deck else '-'}")
    miss += (not in_pdf)
print("paper misses:", miss)
sys.exit(1 if miss else 0)
