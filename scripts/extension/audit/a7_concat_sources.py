"""A7 (P2a, read-only): sha256 of each source listed in data/extension/confirm/ALL/concat_manifest.json.

Both the raw-byte hash and the hash with CRLF normalised to LF are computed; a source matches if either equals the
recorded value, and the line reports which.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def main():
    man = json.loads((ROOT / "data/extension/confirm/ALL/concat_manifest.json").read_text(encoding="utf-8"))
    bad = 0
    for s in man["sources"]:
        data = (ROOT / s["path"]).read_bytes()
        raw = hashlib.sha256(data).hexdigest()
        lf = hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()
        how = "raw" if raw == s["sha256"] else ("LF-normalised" if lf == s["sha256"] else None)
        bad += how is None
        print(f"{'OK ' if how else 'BAD'} {s['tranche']:5} {s['kind']:12} {s['path']} ({how or 'no match'})")
    print(f"A7 sources {len(man['sources'])}; mismatches {bad}")


if __name__ == "__main__":
    main()
