"""Label-audit kit (D-82): blind packets, rubric, calibration set and per-rater CSVs. No model call, nothing scored.

Each packet item shows only what a rater needs to judge the execution label: the generated test, the failure on the
BUGGY version, the focal method's Javadoc and the developer's fix as a diff. It never shows the execution label, the
outcome on the fixed version or any LLM output.

Patch direction: the fix diffs in Zhao et al.'s replication package (`d4j2_fix_info`) are stored fixed -> buggy (as
Defects4J's own patches are); `scripts/audit/diffs.py` reverses them into standard unified diffs, buggy -> fixed
("-" buggy lines before "+" fixed lines in each block, a/ b/ headers), so every packet reads as the developer's fix.

    python scripts/audit/build_label_audit_kit.py
      -> docs/audits/kit/{LABEL_AUDIT_RUBRIC.md, packets_rater_A.pdf, packets_rater_B.pdf,
                          label_audit_rater_A.csv, label_audit_rater_B.csv, calibration_rater_A.csv, calibration_rater_B.csv,
                          CALIBRATION_KEY.md (open only after calibration)}
         data/ground_truth_store/audit/packet_orders.json (per-rater order; the audit key stays where it was)
"""
import csv
import html
import json
import random
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "audit"))
from diffs import reverse_unified_diff  # noqa: E402  standard buggy -> fixed unified diff (D-82 note)

KIT = ROOT / "docs" / "audits" / "kit"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
ORDER_SEEDS = {"A": 20261104, "B": 20261105, "C": 20261107}   # C: the blind LLM rater (D-84)
FIX = config.EXTERNAL / "EvalAndMitigate" / "data" / "d4j2_fix_info"

# Rubric explanations, written by reading each seeded example (execution label shown for the examples only)
EXPLAIN = {
    "1733bd6292c2dcae": "PF. The test asks for the paint of a value below the lower bound. The buggy method computes the grey level from the raw value, which goes negative, so <code>new Color</code> throws. The fix computes it from the clamped value <code>v</code>; the same test passes on the fixed version.",
    "21059fffb913ee70": "PF. Cloning a series throws <code>Requires start &lt;= end</code> because the buggy <code>clone()</code> calls <code>createCopy(0, getItemCount() - 1)</code>, which fails on an empty series. The fix restores <code>super.clone()</code> with a deep copy, and the test passes.",
    "36a710bbde166f3d": "TF. The test expects one item in <code>createCopy(1, 1)</code> and gets none. The fix only resets <code>minY</code>/<code>maxY</code> in the copy; it does not touch how items are copied, and the test fails the same way on the fixed version. The expectation, not the fault, is wrong.",
    "3c5ee66a61f6efb2": "TF. The test adds 8,760 hours to 2023-01-01T00:00Z and expects the year to be 2024. That instant is still 31 December 2023 in a time zone west of UTC, and Defects4J runs its tests in America/Los_Angeles; the fix (dropping the <code>amount != 0</code> guards) is unrelated. The expectation depends on the time zone.",
    "f3e565ad421854ff": "AMB (a genuine mixed case). On the buggy version <code>getHeaderMap()</code> throws a NullPointerException when no header is defined; the fix makes it return <code>null</code> instead. The failure is caused by the faulty code, but the test's own expectation (an empty map) contradicts the fixed behaviour too, so it fails on both versions in different places.",
    "e62205a7d8001b4d": "Execution label AMB, but a careful rater decides TF. 0000123 in octal is 83, so the expected value 9 is wrong whatever the fault; the fixed version fails as well, with a different signature, which is why the rule says AMB. Use AMB only when the evidence genuinely cannot decide.",
}


def patch(bug: str) -> str:
    p = FIX / bug / "buggy_fix_info.json"
    if not p.exists():
        return "(patch unavailable)"
    info = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    return reverse_unified_diff("\n".join(ch.get("diff", "") for ch in info.get("fixing_changes", [])))


def item_html(tag: str, inst: dict) -> str:
    f = inst["failure"]
    fail = (f"{f['outcome_type']} {f.get('exception_class') or ''}: {f.get('message') or ''}\n"
            f"failing line: {f.get('failing_test_line_text')}\n{f.get('rendered_trace', '')}")
    doc = (inst.get("doc") or {}).get("method_javadoc") or "(no Javadoc)"
    e = html.escape
    return (f"<section class='item'><h3>{e(tag)} &mdash; {e(inst['project'])}, <code>{e(inst['focal_class'])}.{e(inst['focal_method_name'])}</code></h3>"
            f"<h4>Generated test</h4><pre>{e(inst['test']['method_source'])}</pre>"
            f"<h4>Failure on the buggy version</h4><pre>{e(fail)}</pre>"
            f"<h4>Javadoc of the focal method (buggy version)</h4><pre>{e(doc)}</pre>"
            f"<h4>Developer's fix (buggy &rarr; fixed)</h4><pre class='diff'>{e(patch(inst['bug_name']))}</pre>"
            f"<p class='answer'>Your decision: &#9744; PF &nbsp; &#9744; TF &nbsp; &#9744; AMB &nbsp;&nbsp; confidence 1 / 2 / 3 &nbsp;&nbsp; notes: ____________</p></section>")


RUBRIC_MD = """# Label-audit rubric (both raters, independently)

**Question.** For each failing generated test, decide what caused the failure on the **buggy** version, using only the
packet: the test, the failure on the buggy version, the focal method's Javadoc and the developer's fix (shown buggy →
fixed). The execution label and any model output are hidden. Do not confer until both sheets are complete.

| Decision | Use it when |
|---|---|
| **PF** (program fault) | The test's expectation matches the intended behaviour (as the fix and the Javadoc show it), and the failure on the buggy version comes from the code the fix changes. The same test would pass once the fix is applied. |
| **TF** (test fault) | The test fails for a reason the fix does not address: a wrong expected value, invalid set-up, API misuse, or a dependence on the environment (time zone, locale, ordering). It would fail on the fixed version as well. |
| **AMB** (ambiguous) | The evidence cannot decide, or both are true: the faulty code causes the failure and the test's own expectation contradicts the fixed behaviour. Explain in the notes. Use it sparingly. |

Also record a **confidence** (1 = guess, 2 = fairly sure, 3 = certain) and, for anything not obvious, a short note.

## Worked examples (from the held-out split, not part of the audit; execution label shown)

{examples}

## Procedure

1. Read this rubric. 2. Do the 10 **calibration** items alone (`calibration_rater_X.csv`). Then compare your sheet
with the other rater's and discuss your disagreements using this rubric only. Open `CALIBRATION_KEY.md` only after
that discussion, and do not change the rubric or any judgement to match it. 3. Do the 71 **audit** items
(`label_audit_rater_X.csv`) alone, in the packet order, without conferring. 4. Return the CSV. Scoring:
`python scripts/analysis/label_audit.py`.
"""


def main(raters=("A", "B")):
    KIT.mkdir(parents=True, exist_ok=True)
    inst = {i["instance_id"]: i for i in read_jsonl(config.PROCESSED / "instances_D1.jsonl")}
    key = list(csv.DictReader(open(config.GT_STORE / "audit" / "label_audit_key.csv", encoding="utf-8-sig")))
    sel = json.loads((config.GT_STORE / "audit" / "audit_examples_selection.json").read_text(encoding="utf-8"))
    lab = {l["instance_id"]: l["label"] for l in read_jsonl(config.GT_STORE / "labels_D1.jsonl")}

    # rubric with worked examples
    ex_md = []
    for c in ("PF", "TF", "AMB"):
        for iid in sel["rubric"][c]:
            i = inst[iid]
            f = i["failure"]
            ex_md += [f"### {c}: {i['bug_name']}, `{i['focal_class'].split('.')[-1]}.{i['focal_method_name']}`", "",
                      f"- Failure on the buggy version: `{f['exception_class']}` — `{(f.get('message') or '')[:140]}` at "
                      f"`{(f.get('failing_test_line_text') or '').strip()[:140]}`",
                      "- " + re.sub(r"</?code>", "`", EXPLAIN[iid]).replace("&lt;", "<").replace("&gt;", ">"), ""]
    rubric = RUBRIC_MD.replace("{examples}", "\n".join(ex_md))
    (KIT / "LABEL_AUDIT_RUBRIC.md").write_text(rubric, encoding="utf-8")

    calib_ids = [i for c in ("PF", "TF", "AMB") for i in sel["calibration"][c]]
    rng = random.Random(20261106)
    rng.shuffle(calib_ids)
    calib = [(f"CAL{k:02d}", iid) for k, iid in enumerate(calib_ids, 1)]
    (KIT / "CALIBRATION_KEY.md").write_text(
        "# Calibration key — open only after both raters have finished the 10 calibration items\n\n"
        "| Item | Execution label |\n|---|---|\n" + "\n".join(f"| {cid} | {lab[iid]} |" for cid, iid in calib) + "\n",
        encoding="utf-8")

    op = config.GT_STORE / "audit" / "packet_orders.json"
    orders = json.loads(op.read_text(encoding="utf-8"))["orders"] if op.exists() else {}
    css = ("@page{size:A4;margin:14mm 13mm}body{font-family:Georgia,serif;font-size:9.5pt;line-height:1.35}"
           "h1{font-size:15pt}h2{font-size:12.5pt;border-bottom:1px solid #999;margin-top:14pt}h3{font-size:10.5pt;margin:0 0 3pt}"
           "h4{font-size:8.6pt;margin:6pt 0 2pt;color:#333;text-transform:uppercase;letter-spacing:.03em}"
           "pre{font-family:Consolas,monospace;font-size:7.6pt;background:#f4f4f4;padding:4pt;white-space:pre-wrap;word-break:break-all;margin:0}"
           ".item{page-break-before:always}.answer{border:1px solid #888;padding:4pt;margin-top:6pt}"
           "table{border-collapse:collapse;font-size:8.6pt}td,th{border:1px solid #bbb;padding:2pt 5pt;vertical-align:top}")
    sys.path.insert(0, str(ROOT / "scripts" / "paper"))
    from render_phase3_pdf import convert          # the same small Markdown converter as the Phase 3 report
    rub_html = convert(rubric, KIT)
    for rater in raters:
        seed = ORDER_SEEDS[rater]
        r = random.Random(seed)
        audit = [(row["audit_id"], row["instance_id"]) for row in key]
        r.shuffle(audit)
        orders[rater] = [a for a, _ in audit]
        parts = [f"<h1>Label audit — rater {rater}</h1><p>Blind packet: no execution label, no fixed-version outcome, "
                 f"no model output. {len(calib)} calibration items, then {len(audit)} audit items in your order.</p>", rub_html,
                 "<h2 style='page-break-before:always'>Part 1 — calibration (10 items)</h2>"]
        parts += [item_html(cid, inst[iid]) for cid, iid in calib]
        parts += ["<h2 style='page-break-before:always'>Part 2 — audit (71 items)</h2>"]
        parts += [item_html(f"{n:02d}. {aid}", inst[iid]) for n, (aid, iid) in enumerate(audit, 1)]
        page = KIT / f"packets_rater_{rater}.html"
        page.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{''.join(parts)}</body></html>",
                        encoding="utf-8")
        pdf = KIT / f"packets_rater_{rater}.pdf"
        subprocess.run([str(EDGE), "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={pdf}", page.resolve().as_uri()],
                       capture_output=True, timeout=300)
        page.unlink()
        cols = ["order", "audit_id", "decision", "confidence", "notes"]
        with open(KIT / f"label_audit_rater_{rater}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows({"order": n, "audit_id": aid, "decision": "", "confidence": "", "notes": ""} for n, (aid, _) in enumerate(audit, 1))
        with open(KIT / f"calibration_rater_{rater}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["item", "decision", "confidence", "notes"])
            w.writeheader()
            w.writerows({"item": cid, "decision": "", "confidence": "", "notes": ""} for cid, _ in calib)
        print(rater, pdf, pdf.exists() and pdf.stat().st_size)
    dump_json(config.GT_STORE / "audit" / "packet_orders.json",
              {"seeds": ORDER_SEEDS, "orders": orders, "calibration": [{"item": c, "instance_id": i} for c, i in calib],
               "patch_direction": "standard unified diff buggy -> fixed (scripts/audit/diffs.py; source diffs are fixed -> buggy)"})


if __name__ == "__main__":
    main(tuple(sys.argv[1:]) or ("A", "B"))   # e.g. `... build_label_audit_kit.py C` builds only rater C
