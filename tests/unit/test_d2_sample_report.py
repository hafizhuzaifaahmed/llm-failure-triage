"""D-64 report (scripts/analysis/d2_sample_report.py) on synthetic labels: no held-out data is read."""
import importlib.util
from pathlib import Path

from triage.dataset import allocate

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("d2_sample_report", ROOT / "scripts" / "analysis" / "d2_sample_report.py")
rep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rep)


def _labels():
    out, i = [], 0
    # project P: bug P_1 dominates; project Q: one bug
    for proj, bug, cls, n in [("P", "P_1", "PF", 70), ("P", "P_1", "TF", 200), ("P", "P_2", "PF", 10),
                              ("P", "P_2", "TF", 60), ("Q", "Q_1", "PF", 30), ("Q", "Q_1", "TF", 150),
                              ("Q", "Q_1", "AMB", 9)]:
        for _ in range(n):
            out.append({"instance_id": f"i{i:04d}", "focal_id": f"{bug}::m{i % 7}#m{i % 3}", "project": proj,
                        "bug_name": bug, "label": cls, "split": "test"})
            i += 1
    return out


def test_capped_report():
    labels = _labels()
    samp = allocate(labels, mode="proportional", seed=20261009, cap=300)
    assert samp["capped"]
    out = rep.report(labels, samp, n_units_total=50)
    b, j, c = out["before_cap"], out["judged_sample"], out["clustering"]
    assert b["labelled_instances"] == {"PF": 110, "TF": 410, "AMB": 9}
    assert b["c9_sample_size_uncapped"] == 110 + 220 + 9
    assert j["n"] == 300 == len(samp["instance_ids"])
    assert 1.95 <= j["realised_tf_per_pf"] <= 2.05
    assert sum(j["by_class"].values()) == 300
    assert c["largest_base_bug"] in {"P_1", "Q_1"}
    assert abs(c["largest_base_bug_share"] - c["largest_base_bug_instances"] / 300) < 1e-12


def test_uncapped_report_uses_all():
    labels = [l for l in _labels() if l["project"] == "Q"]
    samp = allocate(labels, mode="proportional", seed=20261009, cap=300)
    assert not samp["capped"]
    out = rep.report(labels, samp, n_units_total=10)
    assert out["judged_sample"]["n"] == out["before_cap"]["c9_sample_size_uncapped"] == 30 + 60 + 9
    assert out["judged_sample"]["realised_tf_per_pf"] == 2.0
    assert out["clustering"]["largest_base_bug_share"] == 1.0
