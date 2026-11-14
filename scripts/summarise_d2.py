"""Summarise data/processed/d2_mutants.jsonl -> data/processed/d2_summary.json (and print it)."""
import collections
import json

from _common import config
from triage.io_utils import dump_json, read_jsonl


def main():
    rs = list(read_jsonl(config.PROCESSED / "d2_mutants.jsonl"))
    frame_test = [r for r in read_jsonl(config.PROCESSED / "frame_d1.jsonl") if r["split"] == "test"]
    placed = [r for r in rs if r.get("placeable_focal") is not None]
    s = {
        "held_out_focal_methods": len(frame_test), "processed": len(rs),
        "status": dict(collections.Counter(r["status"] for r in rs)),
        "focal_methods_with_verified_mutant": sum(bool(r.get("chosen")) for r in rs),
        "verified_mutants": sum(len(r.get("chosen", [])) for r in rs),
        "attempt_verdicts": dict(collections.Counter(a["verdict"] for r in rs for a in r.get("attempts", []))),
        "verified_by_operator": dict(collections.Counter(c["operator"] for r in rs for c in r.get("chosen", []))),
        "placement_rate_all_focal_mutants": (sum(r["placeable_focal"] for r in placed) /
                                             max(1, sum(r["n_mutants_focal"] for r in placed))),
        "verified_by_project": dict(collections.Counter(r["focal_id"].split("_")[0] for r in rs for _ in r.get("chosen", []))),
        "errors": [{"focal_id": r["focal_id"], "error": r.get("error", "")[-200:]} for r in rs if r["status"] == "ERROR"],
    }
    dump_json(config.PROCESSED / "d2_summary.json", s)
    print(json.dumps(s, indent=1))


if __name__ == "__main__":
    main()
