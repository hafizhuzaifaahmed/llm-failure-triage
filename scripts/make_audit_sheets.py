"""Generate the blinded human-audit sheets once real data exist (no LLM, no cost).

    python scripts/make_audit_sheets.py labels    # needs data/ground_truth_store/labels_D1.jsonl (dev split)
    python scripts/make_audit_sheets.py specs     # needs data/processed/specs/S2__<M1>.jsonl (test split)
    python scripts/make_audit_sheets.py templates # header-only templates (available now)
"""
import argparse
import json

from _common import config, load_contexts
from triage import audit
from triage.io_utils import read_jsonl

OUT = config.ROOT / "docs" / "audits"


def fix_diffs() -> dict:
    out = {}
    for d in (config.EXTERNAL / "EvalAndMitigate" / "data" / "d4j2_fix_info").iterdir():
        info = json.loads((d / "buggy_fix_info.json").read_text(encoding="utf-8", errors="replace"))
        out[d.name] = "\n".join(ch.get("diff", "") for ch in info.get("fixing_changes", []))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["labels", "specs", "templates"])
    a = ap.parse_args()
    if a.which == "templates":
        audit._write_csv(OUT / "TEMPLATE_label_audit.csv", [{k: "" for k in (
            "audit_id", "project", "focal_method", "test_method", "failure_on_buggy_version", "fix_patch", "decision", "notes")}])
        audit._write_csv(OUT / "TEMPLATE_spec_audit.csv", [{k: "" for k in (
            "audit_id", "project", "focal_signature", "inferred_specification", "fix_patch", "classification", "notes")}])
        print("templates written to", OUT)
        return
    if a.which == "labels":
        labels = list(read_jsonl(config.GT_STORE / "labels_D1.jsonl"))
        if not labels:
            raise SystemExit("no labels yet: run generation + execution + build_dataset first")
        inst = {i["instance_id"]: i for i in read_jsonl(config.PROCESSED / "instances_D1.jsonl")}
        print(audit.make_label_audit(labels, inst, fix_diffs(), OUT))
    else:
        spec_file = config.PROCESSED / "specs" / f"S2__{config.MODELS['M1']['id'].replace('/', '__')}.jsonl"
        specs = list(read_jsonl(spec_file))
        if not specs:
            raise SystemExit(f"no specifications yet ({spec_file})")
        print(audit.make_spec_audit(specs, load_contexts(), fix_diffs(), OUT))


if __name__ == "__main__":
    main()
