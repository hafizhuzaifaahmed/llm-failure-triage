"""Leakage-guard aborts of one run, by instance: which (arm, level, variant) tuples were aborted, and every string the
guard matched, with its length and where the guard got it. Rebuilds the packages exactly as the runner does; reads
the run's leakage_rejections.jsonl, never decisions or verdicts. Reporting only -- the guard is not changed.

  python scripts/analysis/leakage_abort_report.py results/runs_local/LOCAL_HO_E1E3_M1
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import config  # noqa: E402,F401
from triage.context_builder import GENERIC_PATTERNS, leakage_check  # noqa: E402
from triage.io_utils import read_jsonl  # noqa: E402
from triage.runner import Runner, load_specs  # noqa: E402
from triage.spec_inference import SPEC_CACHE  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def source_of(hit: str, guard: dict, extra: list[str]) -> str:
    if hit in guard.get("bug_ids", []):
        return "guard bug id"
    if hit in [s.strip() for s in guard.get("code_lines", [])]:
        return "guard fixed-only line"
    if hit in [s.strip() for s in guard.get("paths", [])]:
        return "guard path"
    if hit in extra:
        return "focal-body line (runner)"
    if any(re.fullmatch(p, hit) for p in GENERIC_PATTERNS):
        return "generic pattern"
    return "unknown"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    a = ap.parse_args(argv)
    exp = json.loads((a.run_dir / "experiment.json").read_text(encoding="utf-8"))
    exp = exp.get("experiment", exp)
    ds = exp.get("dataset", "D1")
    rej = list(read_jsonl(a.run_dir / "leakage_rejections.jsonl"))
    tuples = defaultdict(set)
    for r in rej:
        tuples[r["instance_id"]].add((r["arm"], r["level"], r["variant"], str(r["replicate"])))
    insts = {i["instance_id"]: i for i in read_jsonl(config.PROCESSED / f"instances_{ds}.jsonl") if i["instance_id"] in tuples}
    guard = {g["instance_id"]: g for g in read_jsonl(config.LEAKAGE_GUARD / f"guard_{ds}.jsonl") if g["instance_id"] in tuples}
    specs = load_specs(SPEC_CACHE / "S2__qwen3.5_9b.jsonl")
    specs_p = load_specs(SPEC_CACHE / "S2prime__qwen3.5_9b.jsonl")
    runner = Runner(ROOT / "results" / "_tmp_unused", None, None, None, specs, specs_p, forbidden=guard)
    out = {"run": str(a.run_dir), "unique_aborted_tuples": sum(len(v) for v in tuples.values()), "instances": []}
    for iid in sorted(tuples):
        inst, g = insts[iid], guard[iid]
        cells = sorted({(arm, lvl, var) for arm, lvl, var, _ in tuples[iid]})
        levels = sorted({lvl for _, lvl, _ in cells})
        per_level = {}
        for lvl in levels:
            var = next(v for _, l, v in cells if l == lvl)
            pkg, hits = runner.package_for(inst, lvl, var)
            body = inst.get("impl", "")
            body = body[body.find("{") + 1:] if "{" in body else ""
            extra = [l.strip() for l in body.split("\n") if len(l.strip()) >= 25]
            assert hits == leakage_check(pkg.text, g, extra, exempt_body=inst.get("impl") if var == "impl" else None)
            per_level[lvl] = [{"string": h, "length": len(h), "source": source_of(h, g, extra)} for h in dict.fromkeys(hits)]
        out["instances"].append({
            "instance_id": iid, "project": inst.get("project"), "bug_name": inst.get("bug_name"),
            "aborted_tuples": len(tuples[iid]),
            "aborted_levels": levels,
            "aborted_arms_by_level": {lvl: sorted({arm for arm, l, _ in cells if l == lvl}) for lvl in levels},
            "matches_by_level": per_level,
        })
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
