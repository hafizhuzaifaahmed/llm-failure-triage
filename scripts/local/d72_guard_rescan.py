"""D-72 re-scan: every package the runs logged (decisions and leakage aborts), rebuilt as the runner builds it and
judged by the guard before D-72 and by the guard now. Reads instance_id/arm/level/variant of each logged tuple, the
instances and the guard -- strings only, never a label, decision or verdict.

    python scripts/local/d72_guard_rescan.py   -> results/heldout/d72_guard_rescan.json
"""
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src")]

from _common import config  # noqa: E402
from triage.context_builder import GENERIC_PATTERNS  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402
from triage.runner import Runner, load_specs  # noqa: E402
from triage.spec_inference import SPEC_CACHE  # noqa: E402

RUNS = sorted([p for p in (ROOT / "results" / "runs_local").iterdir() if p.is_dir()]
              + [p for p in (ROOT / "results" / "dev").iterdir() if (p / "decisions.jsonl").exists()])


def pre_d72(package_text, guard=None, extra_lines=None):
    """The guard as it was before D-72."""
    guard = guard or {}
    hits = []
    for bid in guard.get("bug_ids", []):
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(bid)}(?![0-9])", package_text):
            hits.append(bid)
    low = package_text.lower()
    for s in list(guard.get("code_lines", [])) + list(guard.get("paths", [])) + list(extra_lines or []):
        s = (s or "").strip()
        if len(s) >= 6 and s.lower() in low:
            hits.append(s)
    for pat in GENERIC_PATTERNS:
        hits += re.findall(pat, package_text)
    return hits


def tuples(run: Path):
    out = set()
    for name in ("decisions.jsonl", "leakage_rejections.jsonl"):
        f = run / name
        if not f.exists():
            continue
        for r in read_jsonl(f):
            if r.get("level"):
                var = r.get("variant") or "full"
                out.add((r["instance_id"], r["level"], var, name == "leakage_rejections.jsonl"))
    return out


def main():
    insts = {i["instance_id"]: i for i in read_jsonl(config.PROCESSED / "instances_D1.jsonl")}
    guard = {g["instance_id"]: g for g in read_jsonl(config.LEAKAGE_GUARD / "guard_D1.jsonl")}
    runner = Runner(ROOT / "results" / "_tmp_unused", None, None, None, load_specs(SPEC_CACHE / "S2__qwen3.5_9b.jsonl"),
                    load_specs(SPEC_CACHE / "S2prime__qwen3.5_9b.jsonl"), forbidden=guard)
    out = {"fields_read": ["instance_id", "arm", "level", "variant"], "runs": {}, "changed": []}
    for run in RUNS:
        tally = Counter()
        cells = {}
        for iid, lv, var, aborted in tuples(run):
            cells[(iid, lv, var)] = cells.get((iid, lv, var), False) or aborted
        for (iid, lv, var), aborted in sorted(cells.items()):
            inst = insts[iid]
            pkg, new = runner.package_for(inst, lv, var)
            body = inst.get("impl", "")
            body = body[body.find("{") + 1:] if "{" in body else ""
            extra = [] if var == "impl" else [l.strip() for l in body.split("\n") if len(l.strip()) >= 25]
            old = pre_d72(pkg.text, guard.get(iid), extra)
            tally["packages"] += 1
            tally["identical" if old == new else "changed"] += 1
            tally["aborted_before"] += bool(old)
            tally["aborted_now"] += bool(new)
            if old != new:
                out["changed"].append({"run": run.name, "instance_id": iid, "bug": inst.get("bug_name"), "level": lv,
                                       "variant": var, "logged_as_abort": aborted, "hits_before": old, "hits_now": new})
        out["runs"][run.name] = dict(tally)
    out["packages"] = sum(t["packages"] for t in out["runs"].values())
    out["changed_count"] = len(out["changed"])
    dump_json(ROOT / "results" / "heldout" / "d72_guard_rescan.json", out)
    print(f"packages {out['packages']} | changed {out['changed_count']}")
    for k, v in out["runs"].items():
        print(f"  {k:22s} {v}")
    for c in out["changed"]:
        print("  CHANGED", c["run"], c["bug"], c["instance_id"][:8], c["level"], c["variant"], c["hits_before"], "->", c["hits_now"])


if __name__ == "__main__":
    main()
