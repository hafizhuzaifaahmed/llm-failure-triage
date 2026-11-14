"""D-51 audit item 2: the label mapping end to end — PROGRAM_FAULT is scored as the positive class PF, the
decision -> label-store join is by instance_id only, AMB is excluded, and an INVALID output counts as TF."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from triage import analysis  # noqa: E402

LABELS = [{"instance_id": i, "label": lab, "bug_name": b, "project": b[0], "split": "dev"}
          for i, lab, b in (("a", "PF", "B1"), ("b", "PF", "B2"), ("c", "TF", "B1"), ("d", "TF", "B3"),
                            ("e", "AMB", "B2"), ("f", "TF", "B3"))]


def dec(iid, label):
    return {"instance_id": iid, "arm": "J1", "level": "S1", "variant": "full", "replicate": 0, "label_raw": label}


def test_program_fault_is_the_positive_class_and_join_is_by_instance_id():
    decisions = [dec("a", "PROGRAM_FAULT"),   # PF  -> TP
                 dec("b", "TEST_FAULT"),      # PF  -> FN
                 dec("c", "PROGRAM_FAULT"),   # TF  -> FP
                 dec("d", "TEST_FAULT"),      # TF  -> TN
                 dec("e", "PROGRAM_FAULT"),   # AMB -> excluded
                 dec("f", "INVALID"),         # TF, invalid counted as TF -> TN
                 dec("zz", "PROGRAM_FAULT")]  # not in the label store -> never joined
    s = analysis.Evaluation(decisions, LABELS).summary("J1|S1")
    assert (s["TP"], s["FN"], s["FP"], s["TN"]) == (1, 1, 1, 2)
    assert s["n_instances"] == 5


def test_swapping_labels_swaps_the_confusion_matrix():
    decisions = [dec("a", "TEST_FAULT"), dec("b", "TEST_FAULT"), dec("c", "PROGRAM_FAULT"), dec("d", "PROGRAM_FAULT"),
                 dec("f", "PROGRAM_FAULT")]
    s = analysis.Evaluation(decisions, LABELS).summary("J1|S1")
    assert (s["TP"], s["FN"], s["FP"], s["TN"]) == (0, 2, 3, 0)
