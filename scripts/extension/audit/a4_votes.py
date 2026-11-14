"""P1/A4: tests without judge votes, per judge, and what the leakage-guard file says about them.

Imports no project module. Read-only.
Usage: python a4_votes.py <repo root>
"""
import json, sys
from collections import Counter
from pathlib import Path

root = Path(sys.argv[1])
JUDGES = ("M1", "M2", "E6B")


def load(p):
    with open(p, encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


all_missing = {}
for T in ("F1", "F2"):
    d = root / "data/extension/confirm" / T
    labs = {l["instance_id"]: l for l in load(d / f"labels_D1C_{T}.jsonl") if l["label"] in ("PF", "TF")}
    miss = {}
    for J in JUDGES:
        rows = load(d / "votes" / f"LOCAL_CONF_VOTE_{J}_{T}" / "decisions.jsonl")
        sel = [r for r in rows if r.get("replicate") == 80 and r.get("arm") == "J1" and r.get("level") == "S1"]
        voted = {r["instance_id"] for r in sel}
        dup = [k for k, v in Counter(r["instance_id"] for r in sel).items() if v > 1]
        miss[J] = sorted(set(labs) - voted)
        print(f"{T} {J}: decisions rows {len(rows)}, selected {len(sel)}, distinct ids {len(voted)}, duplicates {len(dup)},"
              f" voted ids not in PF/TF labels {len(voted - set(labs))}; scored ids without vote {len(miss[J])}")
    same = all(miss[J] == miss[JUDGES[0]] for J in JUDGES)
    print(f"{T}: missing sets identical across judges: {same}")
    m = miss[JUDGES[0]]
    for iid in m:
        all_missing[iid] = (T, labs[iid]["label"], labs[iid]["bug_name"])

    # guard file structure
    guard = load(d / f"guard_D1C_{T}.jsonl")
    kc = Counter(); [kc.update(g.keys()) for g in guard]
    gid = Counter(g.get("instance_id") for g in guard)
    print(f"{T} guard file: {len(guard)} records; key counts {dict(kc)}; distinct instance ids {len(gid)};"
          f" scored ids with a guard record {sum(1 for i in labs if i in gid)}/{len(labs)}")
    refusal_like = [k for k in kc if any(s in k.lower() for s in ("refus", "block", "leak", "hit", "match", "status", "flag"))]
    print(f"{T} guard keys that could mark a refusal: {refusal_like or 'none'}")
    by = {}
    for g in guard:
        by.setdefault(g.get("instance_id"), []).append(g)
    for iid in m:
        recs = by.get(iid, [])
        print(f"   missing {iid} {labs[iid]['label']} {labs[iid]['bug_name']}: guard records {len(recs)}; "
              + "; ".join(json.dumps(r)[:400] for r in recs))

# Supplementary: the guard_D1C file holds guard INPUTS (forbidden strings), not outcomes. The per-judge
# votes/<run>/leakage_rejections.jsonl files (found by searching for the ids) are inspected here as-is.
print("== supplementary: votes/<run>/leakage_rejections.jsonl")
for T in ("F1", "F2"):
    d = root / "data/extension/confirm" / T
    for J in JUDGES:
        p = d / "votes" / f"LOCAL_CONF_VOTE_{J}_{T}" / "leakage_rejections.jsonl"
        if not p.exists():
            print(f"{T} {J}: no leakage_rejections.jsonl"); continue
        recs = load(p)
        kc = Counter(); [kc.update(r.keys()) for r in recs]
        ids = {r.get("instance_id") for r in recs}
        miss_T = {i for i, v in all_missing.items() if v[0] == T}
        print(f"{T} {J}: {len(recs)} records, keys {dict(kc)}; ids equal to the no-vote set: {ids == miss_T}"
              f" (in file not missing: {sorted(ids - miss_T)}, missing not in file: {sorted(miss_T - ids)})")
        if J == "M1":
            for r in recs:
                print("    ", json.dumps({k: (v if len(json.dumps(v)) < 200 else str(v)[:200] + '...') for k, v in r.items()}))

c = Counter((v[0], v[1]) for v in all_missing.values())
print(f"TOTAL missing (identical-across-judges sets): {len(all_missing)}; by tranche/label {dict(c)};"
      f" TF {sum(1 for v in all_missing.values() if v[1]=='TF')} PF {sum(1 for v in all_missing.values() if v[1]=='PF')}")
