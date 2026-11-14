"""P1/A2: recompute labels for a seeded sample of 60 instances from raw execution records.

Independent implementation (imports no project module). Rule as registered
(OSF_PREREGISTRATION_CFP.md, hypotheses + data collection step 3):
  - three runs per version (runs_b = buggy, runs_f = developer-fixed);
  - excluded: non-compiling on either version, timeout, environment/harness error, flaky
    (the three runs on one version do not agree);
  - signature = (outcome type, exception class, failing test line);
  - PF: fails on B (deterministic) and passes on F (deterministic);
  - TF: fails on both with identical signatures;
  - AMB: fails on both with different signatures;
  - passes on B: not a failing test (would not be in the labels file).
Usage: python a2_labels.py <repo root> <out json>
"""
import json, random, sys
from pathlib import Path

root = Path(sys.argv[1]); out = Path(sys.argv[2])
SEED = 20261113
FAIL = {"assertion_failure", "exception"}


def sig(r):
    if r["outcome"] == "pass":
        return ("pass", None, None)
    return (r["outcome"], r["exception"] or None, r["failing_test_line"])


def side_state(runs):
    if len(runs) != 3:
        return ("EXCLUDED", f"{len(runs)} runs, expected 3")
    oc = {r["outcome"] for r in runs}
    if "timeout" in oc:
        return ("EXCLUDED", "timeout")
    if oc - FAIL - {"pass"}:
        return ("EXCLUDED", "environment: " + ",".join(sorted(oc - FAIL - {"pass"})))
    sigs = {sig(r) for r in runs}
    if len(sigs) != 1:
        return ("EXCLUDED", "flaky: " + repr(sorted(sigs, key=repr)))
    return ("OK", sigs.pop())


def label(m):
    if not (m["compile_b"] and m["compile_f"]):
        return "EXCLUDED", "non-compiling", None, None
    sb, b = side_state(m["runs_b"]); sf, f = side_state(m["runs_f"])
    if sb != "OK":
        return "EXCLUDED", "B " + b, None, None
    if sf != "OK":
        return "EXCLUDED", "F " + f, b, None
    if b[0] == "pass":
        return "NOT_FAILING", "passes on B", b, f
    if f[0] == "pass":
        return "PF", "", b, f
    return ("TF" if b == f else "AMB"), "", b, f


def load(p):
    with open(p, encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


results = []
for T in ("F1", "F2", "CTRL"):
    d = root / "data/extension/confirm" / T
    labs = {l["instance_id"]: l for l in load(d / f"labels_D1C_{T}.jsonl")}
    ins = {i["instance_id"]: i for i in load(d / f"instances_D1C_{T}.jsonl")}
    ids = sorted(labs)
    sample = random.Random(SEED).sample(ids, 20)
    for iid in sample:
        L = labs[iid]; I = ins[iid]
        assert I["candidate_id"] == L["candidate_id"], iid
        e = json.load(open(d / "executions" / f"{L['candidate_id']}.json", encoding="utf-8"))
        ms = [m for m in e["methods"] if m["method"] == I["method"]]
        if len(ms) != 1:
            mine, why, b, f = "NO_UNIQUE_METHOD", f"{len(ms)} methods named {I['method']}", None, None
        else:
            mine, why, b, f = label(ms[0])
        ok = mine == L["label"]
        # also compare stored signatures where both exist
        sig_ok = None
        if b is not None and f is not None:
            sig_ok = (list(b) == L["sigma_B"]) and (list(f) == L["sigma_F"])
        results.append(dict(tranche=T, instance_id=iid, candidate_id=L["candidate_id"], method=I["method"],
                            stored=L["label"], recomputed=mine, note=why, match=ok, sigma_match=sig_ok,
                            runs_b=None if ok else ms[0]["runs_b"] if ms else None,
                            runs_f=None if ok else ms[0]["runs_f"] if ms else None))

n_ok = sum(r["match"] for r in results)
print(f"A2: {n_ok} of {len(results)} recomputed labels equal the stored labels")
for T in ("F1", "F2", "CTRL"):
    rs = [r for r in results if r["tranche"] == T]
    from collections import Counter
    print(f"  {T}: {sum(r['match'] for r in rs)}/{len(rs)} match; stored {dict(Counter(r['stored'] for r in rs))};"
          f" sigma_B/sigma_F equal to stored: {sum(1 for r in rs if r['sigma_match'])}/{len(rs)}")
for r in results:
    if not r["match"] or r["sigma_match"] is False:
        print("MISMATCH", json.dumps({k: v for k, v in r.items()}, default=str)[:3000])
print("sampled ids:", {T: [r["instance_id"] for r in results if r["tranche"] == T] for T in ("F1", "F2", "CTRL")})
json.dump(results, open(out, "w", encoding="utf-8"), indent=1)
