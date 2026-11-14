"""Evaluation-sample allocation (Phase 2 C9) and the zero-PF-project effect (decision D-16)."""
import pytest

from triage import dataset


def labels(spec):
    out = []
    for proj, (pf, tf, amb) in spec.items():
        for c, n in (("PF", pf), ("TF", tf), ("AMB", amb)):
            out += [{"instance_id": f"{proj}-{c}-{i:03d}", "project": proj, "label": c} for i in range(n)]
    return out


EXAMPLE = {"A": (10, 100, 1), "B": (0, 40, 0), "C": (2, 60, 0)}


def test_per_project_mode_drops_zero_pf_project():
    s = dataset.allocate(labels(EXAMPLE), mode="per_project")
    pp = s["per_project"]
    assert (pp["A"]["TF_sampled"], pp["B"]["TF_sampled"], pp["C"]["TF_sampled"]) == (20, 0, 4)
    assert s["projects_dropped"] == ["B"]


def test_proportional_mode_keeps_every_project_and_global_ratio():
    s = dataset.allocate(labels(EXAMPLE), mode="proportional")
    pp = s["per_project"]
    assert sum(p["TF_sampled"] for p in pp.values()) == 2 * 12                    # global 1:2
    assert (pp["A"]["TF_sampled"], pp["B"]["TF_sampled"], pp["C"]["TF_sampled"]) == (12, 5, 7)
    assert s["projects_dropped"] == []
    a_tf = [i for i in s["instance_ids"] if i.startswith("A-TF")]
    assert s["tf_weights"][a_tf[0]] == pytest.approx(100 / 12)
    assert sum(1 for i in s["instance_ids"] if "-PF-" in i) == 12 and sum(1 for i in s["instance_ids"] if "AMB" in i) == 1


def test_allocation_is_seeded_and_deterministic():
    a = dataset.allocate(labels(EXAMPLE), mode="proportional")
    b = dataset.allocate(list(reversed(labels(EXAMPLE))), mode="proportional")
    assert a["instance_ids"] == b["instance_ids"]


def test_pilot_cap_bounds_the_judged_set():
    s = dataset.allocate(labels({"A": (100, 500, 10), "B": (20, 300, 0)}), cap=150)
    assert s["capped"] and len(s["instance_ids"]) <= 150
    n_pf = sum("-PF-" in i for i in s["instance_ids"])
    n_tf = sum("-TF-" in i for i in s["instance_ids"])
    assert abs(n_tf / n_pf - 2.0) < 0.1                                            # ratio preserved


def test_default_is_the_pre_x07_reading():
    """X-07 is pending: the default must remain the within-project reading."""
    assert dataset.allocate(labels(EXAMPLE))["mode"] == "per_project"
