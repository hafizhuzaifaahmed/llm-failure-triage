"""Verify that no research-result location contains mock or synthetic output.

    python scripts/analysis/check_no_mock.py

Research locations: results/ (except results/smoke/), data/raw/, data/processed/, data/ground_truth_store/,
data/leakage_guard/, paper/ (figures, tables, tex). Markers: the mock backend name, "mock:" model strings,
the smoke watermark, synthetic instance ids, mock call logs. Exit 1 on any hit.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCATIONS = ["results", "data/raw", "data/processed", "data/ground_truth_store", "data/leakage_guard", "paper"]
EXCLUDE = [ROOT / "results" / "smoke"]
MARKERS = [re.compile(p) for p in (r'"backend":\s*"mock"', r'"model_returned":\s*"mock:', r"SMOKE TEST",
                                   r"MOCK DATA", r'"instance_id":\s*"syn\d{3}"', r"mock-model")]
TEXT_SUFFIXES = {".json", ".jsonl", ".csv", ".tex", ".txt", ".md", ".bbl", ".svg"}


def main():
    hits, scanned = [], 0
    for loc in LOCATIONS:
        base = ROOT / loc
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or any(ex in p.parents for ex in EXCLUDE):
                continue
            if p.name.endswith(".mock.jsonl"):
                hits.append((p, "mock call log"))
                continue
            if p.suffix.lower() not in TEXT_SUFFIXES or p.stat().st_size > 50_000_000:
                continue
            scanned += 1
            text = p.read_text(encoding="utf-8", errors="ignore")
            for m in MARKERS:
                if m.search(text):
                    hits.append((p, m.pattern))
                    break
    # figures: a smoke figure would carry the watermark text in its PDF stream
    for p in (ROOT / "paper").rglob("*.pdf"):
        if b"SMOKE TEST" in p.read_bytes():
            hits.append((p, "smoke watermark in PDF"))
    print(f"scanned {scanned} text files in {', '.join(LOCATIONS)} (excluding results/smoke)")
    for p, why in hits:
        print(f"  HIT {p.relative_to(ROOT)}: {why}")
    print("CLEAN" if not hits else f"{len(hits)} contaminated file(s)")
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
