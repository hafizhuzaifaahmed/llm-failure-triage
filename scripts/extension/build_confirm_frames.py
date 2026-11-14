"""Sampling frames for the fresh-fault confirmation of CFP (D-138). WSL entry point; no model call, no test run.

    wsl -d Ubuntu-22.04 -- bash scripts/wsl/run.sh scripts/extension/build_confirm_frames.py

Three tranches, all restricted to held-out projects and to bugs the original study never generated a test for:

  F1    methods of the original frame that the per-project cap of 25 left out
  F2    fix-changed public/protected methods present in both versions whose only exclusion from the original frame
        was "no bug-triggering test invokes it by name"; at most MAX_F2_PER_BUG per bug, by a seeded sample
  CTRL  one method per bug that the fix did NOT change: same class as a tranche method, public or protected, body
        identical in the buggy and the fixed version, not named like any fix-changed method of that bug, and with at
        least MIN_CONTROL_MUTANTS first-order mutants; among those, the one whose mutant count is closest to that of
        the bug's first tranche method (ties broken by name)

The fixed version is read here, as in the original frame construction: this is offline frame building, not triage.
Writes configs/extension/confirm_frame.jsonl and confirm_frame_summary.json.
"""
import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import javasrc  # noqa: E402
from triage.execution import WORK  # noqa: E402
from triage_ext import mutate  # noqa: E402

SEED = 20261111
DEV_PROJECTS = {"Cli", "Gson", "Jsoup"}
MAX_F2_PER_BUG = 3
MIN_CONTROL_MUTANTS = 5
GENERATIONS = {"F1": 6, "F2": 3, "CTRL": 3}
ACCESS = re.compile(r"\b(public|protected)\b")
OUT = ROOT / "configs" / "extension"


def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def norm(text):
    return re.sub(r"\s+", " ", text).strip()


def control_for(bug_rows, changed_names):
    """Best-matched unchanged method for one bug, or (None, reason)."""
    project, bug = bug_rows[0]["bug_name"].rsplit("_", 1)
    wb, wf = WORK / f"{project}_{bug}" / "b", WORK / f"{project}_{bug}" / "f"
    reasons = Counter()
    for row in sorted(bug_rows, key=lambda r: r["focal_id"]):
        pb, pf = wb / row["file"], wf / row["file"]
        if not (pb.exists() and pf.exists()):
            reasons["file_missing"] += 1
            continue
        sb, sf = pb.read_text(errors="replace"), pf.read_text(errors="replace")
        simple = row["class"].split(".")[-1].split("$")[-1]
        try:
            mb = [m for m in javasrc.members(sb, simple) if m.kind == "method"]
            mf = {(m.name, norm(javasrc.signature_of(m))): m for m in javasrc.members(sf, simple) if m.kind == "method"}
            focal = next((m for m in javasrc.find_methods(sb, simple, row["method"])), None)
        except (ValueError, IndexError):
            reasons["unparsable"] += 1
            continue
        target = len(mutate.all_mutants(focal.text(sb))) if focal else 0
        best = None
        for m in mb:
            head = m.header.split("(")[0]
            text = m.text(sb)
            if m.name in changed_names or not ACCESS.search(head) or "{" not in text or re.search(r"\babstract\b|\bnative\b", head):
                continue
            twin = mf.get((m.name, norm(javasrc.signature_of(m))))
            if twin is None or norm(twin.text(sf)) != norm(text):
                continue                                  # changed, or absent, in the fixed version
            n = len(mutate.all_mutants(text))
            if n < MIN_CONTROL_MUTANTS:
                continue
            try:
                ptypes = javasrc.param_types(m)
            except ValueError:
                continue
            key = (abs(n - target), m.name, ",".join(ptypes))
            if best is None or key < best[0]:
                best = (key, m, n, ptypes, target, row)
        if best:
            _, m, n, ptypes, target, row = best
            sig = javasrc.signature_of(m)
            inside = sig[sig.index("(") + 1: sig.rindex(")")]
            before = sig[: sig.index("(")].split()
            ret = before[-2] if len(before) > 1 else ""
            return {"bug_name": row["bug_name"], "project": row["project"], "bug": row["bug"], "class": row["class"],
                    "file": row["file"], "method": m.name, "param_types": ptypes, "signature": sig,
                    "qualified": f"{row['class']}:{m.name}:[{inside}]:{ret}", "is_constructor": False,
                    "focal_id": f"{row['bug_name']}::{row['class']}::{m.name}({','.join(ptypes)})",
                    "control_mutants": n, "matched_to": row["focal_id"], "matched_mutants": target}, None
        reasons["no_eligible_method"] += 1
    return None, dict(reasons)


def main():
    cands = [c for c in read_jsonl(ROOT / "data" / "interim" / "frame_candidates.jsonl") if "focal_id" in c]
    used_bugs = {r["bug_name"] for r in read_jsonl(ROOT / "data" / "processed" / "frame_d1.jsonl")}
    held = [c for c in cands if c["project"] not in DEV_PROJECTS and c["bug_name"] not in used_bugs]
    f1 = sorted((c for c in held if c.get("in_frame")), key=lambda c: c["focal_id"])
    f1_bugs = {c["bug_name"] for c in f1}
    pool = defaultdict(list)
    for c in held:
        if c.get("exclusion_reasons") == ["not_invoked"] and c["bug_name"] not in f1_bugs:
            pool[c["bug_name"]].append(c)
    f2 = []
    for bug in sorted(pool):
        rows = sorted(pool[bug], key=lambda c: c["focal_id"])
        if len(rows) > MAX_F2_PER_BUG:
            rng = random.Random(int(hashlib.sha256(f"{SEED}|{bug}".encode()).hexdigest()[:16], 16))
            rows = sorted(rng.sample(rows, MAX_F2_PER_BUG), key=lambda c: c["focal_id"])
        f2 += rows
    changed = defaultdict(set)
    for c in cands:
        changed[c["bug_name"]].add(c["method"])
    by_bug = defaultdict(list)
    for tr, rows in (("F1", f1), ("F2", f2)):
        for c in rows:
            by_bug[c["bug_name"]].append(c)
    out, ctrl_fail = [], {}
    for tr, rows in (("F1", f1), ("F2", f2)):
        for c in rows:
            out.append({**c, "tranche": tr, "generations": GENERATIONS[tr], "split": "confirm"})
    for bug in sorted(by_bug):
        rec, why = control_for(by_bug[bug], changed[bug])
        if rec:
            out.append({**rec, "tranche": "CTRL", "generations": GENERATIONS["CTRL"], "split": "confirm"})
        else:
            ctrl_fail[bug] = why
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "confirm_frame.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    summ = {"decision": "D-138", "seed": SEED, "max_f2_per_bug": MAX_F2_PER_BUG,
            "min_control_mutants": MIN_CONTROL_MUTANTS, "generations": GENERATIONS, "tranches": {}}
    for tr in ("F1", "F2", "CTRL"):
        rows = [r for r in out if r["tranche"] == tr]
        per = defaultdict(lambda: [0, set()])
        for r in rows:
            per[r["project"]][0] += 1
            per[r["project"]][1].add(r["bug_name"])
        summ["tranches"][tr] = {"methods": len(rows), "bugs": len({r["bug_name"] for r in rows}),
                                "generation_calls": len(rows) * GENERATIONS[tr],
                                "per_project": {p: {"methods": v[0], "bugs": len(v[1])} for p, v in sorted(per.items())}}
    summ["bugs_total"] = len(by_bug)
    summ["bugs_without_control"] = len(ctrl_fail)
    summ["control_failure_reasons"] = dict(Counter(k for v in ctrl_fail.values() for k in v))
    summ["generation_calls_total"] = sum(t["generation_calls"] for t in summ["tranches"].values())
    (OUT / "confirm_frame_summary.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
