"""A6 (P2a, read-only): recompute the summary flags of the 834 confirmation ledger records from their mutant lists.

Independent of triage_ext.ledger: the rules are re-stated here. Prints one line per tranche and every mismatch.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MIN = 10


def recompute(mutants):
    n = len(mutants)
    fl = sum(1 for m in mutants if m["class"] == "FLIP")
    sh = sum(1 for m in mutants if m["class"] == "SHIFT")
    return {"n_compiled": n, "n_flip": fl, "n_shift": sh, "flip": fl > 0,
            "rcf": any(m["class"] == "FLIP" and m.get("rc") is True for m in mutants),
            "decoupled": n >= MIN and fl == 0 and sh == 0}


def main():
    total, bad, skipped = 0, [], 0
    for tr in ("F1", "F2", "CTRL"):
        recs = [json.loads(l) for l in open(ROOT / f"results/extension/probes/CFP_CONF_{tr}/ledger.jsonl",
                                            encoding="utf-8") if l.strip()]
        nb = 0
        for r in recs:
            total += 1
            s = r["summary"]
            if s.get("excluded"):
                skipped += 1
                continue
            mine = recompute(r["mutants"])
            for k, v in mine.items():
                if s.get(k) != v:
                    bad.append((tr, r["instance_id"], k, s.get(k), v))
                    nb += 1
        print(f"{tr}: {len(recs)} records, mismatches {nb}")
    print(f"A6 total records {total}; excluded (no summary flags) {skipped}; mismatches {len(bad)}")
    for b in bad:
        print("MISMATCH", *b)


if __name__ == "__main__":
    main()
