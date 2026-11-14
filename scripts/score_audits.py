"""Score the completed human audits: rater agreement (Cohen's kappa) and agreement with the automatic label.

    python scripts/score_audits.py labels|specs
"""
import argparse
import json

from _common import config
from triage import audit
from triage.io_utils import dump_json

D = config.ROOT / "docs" / "audits"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["labels", "specs"])
    a = ap.parse_args()
    if a.which == "labels":
        r = audit.score_label_audit(D / "label_audit_rater_A.csv", D / "label_audit_rater_B.csv",
                                    config.GT_STORE / "audit" / "label_audit_key.csv")
    else:
        r = audit.score_spec_audit(D / "spec_audit_rater_A.csv", D / "spec_audit_rater_B.csv")
    dump_json(config.RESULTS / "audit" / f"{a.which}_audit_scores.json", r)
    print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
