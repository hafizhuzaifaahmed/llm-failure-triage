"""Idempotency proof on a real dev run (D-28). Run after a run was hard-killed and resumed to completion.

    python scripts/local/verify_idempotency.py --run results/dev/PROMPTDEV_v0 --config configs/experiments/LOCAL_DEV_M1_PROMPTDEV.json --prompt-set v0

Checks: (1) no request key appears twice in the local call log (each request answered once, across the kill);
(2) the run's decisions are complete and unique per (instance, arm, level, variant, replicate);
(3) rebuilding every decision into a fresh folder with the local client makes ZERO new model calls (all served
from the log) and reproduces the decisions exactly (label, evidence ids, agreement, call keys).
Writes <run>/idempotency.json.
"""
import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from triage.io_utils import dump_json, read_jsonl  # noqa: E402
from triage.ollama import LOCAL_CALL_LOG_DIR  # noqa: E402

KEEP = ("instance_id", "arm", "level", "variant", "replicate", "label_raw", "evidence_ids", "invalid_evidence_ids",
        "reason_category", "agreement", "votes")


def call_keys():
    keys = []
    for f in Path(LOCAL_CALL_LOG_DIR).glob("*.jsonl"):
        if not f.name.startswith("_"):
            keys += [r["key"] for r in read_jsonl(f)]
    return keys


def canon(d):
    out = {k: d.get(k) for k in KEEP}
    out["call_keys"] = (d.get("cost") or {}).get("call_keys")
    return json.dumps(out, sort_keys=True)


def ident(d):
    return (d["instance_id"], d["arm"], d.get("level"), d.get("variant"), d.get("replicate"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--prompt-set", required=True)
    a = ap.parse_args()
    import run_experiment
    from _common import make_client
    run = Path(a.run)
    keys = call_keys()
    dup = [k for k, n in Counter(keys).items() if n > 1]
    decs = list(read_jsonl(run / "decisions.jsonl"))
    ids = Counter(ident(d) for d in decs)
    res = {"run": str(run), "call_log_lines": len(keys), "duplicate_request_keys": len(dup),
           "decisions": len(decs), "duplicate_decisions": sum(n > 1 for n in ids.values())}
    exp = json.loads(Path(a.config).read_text())
    exp = {k: (v.replace("<set>", a.prompt_set) if isinstance(v, str) else v) for k, v in exp.items()}
    rebuild = run.parent / f"_rebuild_{run.name}"
    if rebuild.exists():
        shutil.rmtree(rebuild)
    run_experiment.execute(exp, make_client(local=True), rebuild, workers=2)
    after = call_keys()
    redecs = list(read_jsonl(rebuild / "decisions.jsonl"))
    a_map = {ident(d): canon(d) for d in decs}
    b_map = {ident(d): canon(d) for d in redecs}
    res.update({"new_model_calls_during_rebuild": len(after) - len(keys), "rebuilt_decisions": len(redecs),
                "identical_decisions": sum(a_map.get(k) == v for k, v in b_map.items()),
                "missing_or_extra": len(set(a_map) ^ set(b_map))})
    res["passes"] = (res["duplicate_request_keys"] == 0 and res["duplicate_decisions"] == 0
                     and res["new_model_calls_during_rebuild"] == 0 and res["missing_or_extra"] == 0
                     and res["identical_decisions"] == len(decs))
    shutil.rmtree(rebuild, ignore_errors=True)
    dump_json(run / "idempotency.json", res)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
