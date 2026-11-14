"""Render the Phase 3 report (generated Markdown) to PDF for submission (write-up phase, D-79).

No Markdown library or pandoc is installed, so this converts the small Markdown subset the report uses (headings,
paragraphs, bullet lists, pipe tables, bold, inline code, links, escaped asterisks) to HTML, shows linked PNG figures
inline, and prints the page with headless Microsoft Edge. It reads the generated report only; every number in it
already comes from docs/paper/NUMBERS_MAP.csv.

    python scripts/paper/render_phase3_pdf.py   -> docs/PHASE3_IMPLEMENTATION_AND_EXPERIMENTAL_REPORT.pdf
"""
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "docs" / "PHASE3_IMPLEMENTATION_AND_EXPERIMENTAL_REPORT.md"
HTML = ROOT / "docs" / "phase3" / "PHASE3_REPORT.html"
PDF = ROOT / "docs" / "PHASE3_IMPLEMENTATION_AND_EXPERIMENTAL_REPORT.pdf"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")

CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: 'Georgia', 'Times New Roman', serif; font-size: 10pt; line-height: 1.38; color: #1a1a1a; }
h1 { font-size: 17pt; margin: 0 0 4pt; } h2 { font-size: 13pt; margin: 16pt 0 5pt; border-bottom: 1px solid #bbb; }
h3 { font-size: 11pt; margin: 12pt 0 4pt; }
p { margin: 4pt 0 6pt; } ul { margin: 3pt 0 6pt 16pt; padding: 0; } li { margin: 1pt 0; }
code { font-family: Consolas, monospace; font-size: 8.6pt; background: #f2f2f2; padding: 0 2px; }
table { border-collapse: collapse; margin: 6pt 0 10pt; font-size: 8.4pt; width: 100%; page-break-inside: avoid; }
th, td { border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; padding: 2.5pt 4pt; text-align: left; vertical-align: top; }
th { background: #f0f0f0; } a { color: #1a4f8a; text-decoration: none; }
figure { margin: 6pt 0 10pt; page-break-inside: avoid; } figure img { max-width: 100%; max-height: 82mm; }
figcaption { font-size: 8.4pt; color: #444; }
"""


def inline(t, base):
    t = html.escape(t, quote=False).replace("\\*", "&#42;")
    t = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)

    def link(m):
        text, target = m.group(1), m.group(2)
        if target.lower().endswith(".png"):
            src = (base / target).resolve().as_uri()
            return f"<figure><img src=\"{src}\"><figcaption>{text} — <code>{target.replace('../', '')}</code></figcaption></figure>"
        return f"<a href=\"{target}\">{text}</a>"
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, t)
    return re.sub(r"</figure>\s*,\s*", "</figure>", t)          # the Markdown list separates figure links by commas


def convert(md: str, base: Path) -> str:
    out, lines, i = [], [l for l in md.splitlines() if not l.startswith("<!--")], 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,3}) (.*)", ln)
        if m:
            n = len(m.group(1))
            out.append(f"<h{n}>{inline(m.group(2), base)}</h{n}>")
            i += 1
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], [r for r in rows[1:] if not all(re.fullmatch(r":?-+:?", c) for c in r)]
            out.append("<table><tr>" + "".join(f"<th>{inline(c, base)}</th>" for c in head) + "</tr>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c, base)}</td>" for c in r) + "</tr>" for r in body)
                       + "</table>")
        elif re.match(r"^\s*- ", ln):
            items = []
            while i < len(lines) and (re.match(r"^\s*- ", lines[i]) or (lines[i].startswith("  ") and items)):
                if re.match(r"^\s*- ", lines[i]):
                    items.append(re.sub(r"^\s*- ", "", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x, base)}</li>" for x in items) + "</ul>")
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,3} |\||\s*- )", lines[i]):
                para.append(lines[i].strip())
                i += 1
            out.append(f"<p>{inline(' '.join(para), base)}</p>")
    return "\n".join(out)


def main():
    body = convert(MD.read_text(encoding="utf-8"), MD.parent)
    HTML.write_text(f"<!doctype html><html><head><meta charset='utf-8'><title>Phase 3 report</title><style>{CSS}</style>"
                    f"</head><body>{body}</body></html>", encoding="utf-8")
    r = subprocess.run([str(EDGE), "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={PDF}", HTML.resolve().as_uri()], capture_output=True, text=True, timeout=180)
    if not PDF.exists():
        sys.exit(f"Edge did not write the PDF: {r.stderr[-800:]}")
    print(PDF, PDF.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
