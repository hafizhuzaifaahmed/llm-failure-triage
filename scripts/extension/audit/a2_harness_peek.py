"""P1/A2 exploration: what a run carrying rerun_of_harness_error looks like (read-only)."""
import json, glob, sys
from collections import Counter
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
shown = 0
pat = Counter()
for T in ("F2", "CTRL"):
    for f in sorted(glob.glob(str(root / "data/extension/confirm" / T / "executions" / "*.json"))):
        e = json.load(open(f, encoding="utf-8"))
        for m in e["methods"]:
            for side in ("runs_b", "runs_f"):
                rs = m[side]
                if any("rerun_of_harness_error" in r for r in rs):
                    pat[(T, side, tuple(r["outcome"] for r in rs), tuple(r.get("rerun_of_harness_error") for r in rs))] += 1
                    if shown < 2:
                        shown += 1
                        print(T, Path(f).name, m["method"], side)
                        for r in rs:
                            print("   ", {k: (v[:120] if isinstance(v, str) else v) for k, v in r.items()})
for k, v in pat.most_common(15):
    print(v, k)
