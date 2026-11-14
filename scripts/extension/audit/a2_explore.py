"""P1/A2 exploration: field names and value sets in the confirmation records (read-only)."""
import json, glob, sys
from collections import Counter
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
for T in ("F1", "F2", "CTRL"):
    d = root / "data/extension/confirm" / T
    labs = [json.loads(x) for x in open(d / f"labels_D1C_{T}.jsonl", encoding="utf-8") if x.strip()]
    ins = [json.loads(x) for x in open(d / f"instances_D1C_{T}.jsonl", encoding="utf-8") if x.strip()]
    print(T, "labels", len(labs), Counter(l["label"] for l in labs), "label keys", sorted(labs[0].keys()))
    print("  reasons", Counter(l["reason"] for l in labs))
    print("  instances", len(ins), "keys", sorted(ins[0].keys()))
    print("  instance sample (non-doc fields):", {k: v for k, v in ins[0].items() if k not in ("doc", "source", "context", "test_source")} if len(json.dumps(ins[0])) < 4000 else {k: (v if len(json.dumps(v)) < 300 else "...") for k, v in ins[0].items()})
    oc = Counter(); mkeys = Counter(); rkeys = Counter()
    for f in glob.glob(str(d / "executions" / "*.json")):
        e = json.load(open(f, encoding="utf-8"))
        for m in e["methods"]:
            mkeys.update(m.keys())
            for side in ("runs_b", "runs_f"):
                for r in m.get(side) or []:
                    oc[r["outcome"]] += 1; rkeys.update(r.keys())
    print("  exec method keys", dict(mkeys))
    print("  run keys", dict(rkeys))
    print("  outcomes", dict(oc))
