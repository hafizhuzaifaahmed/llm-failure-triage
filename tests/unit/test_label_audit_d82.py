"""D-82 label-audit scoring on synthetic sheets (no real rater data exists yet)."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("label_audit", ROOT / "scripts" / "analysis" / "label_audit.py")
la = importlib.util.module_from_spec(spec)
spec.loader.exec_module(la)


def setup():
    key = {f"LA{k:03d}": {"audit_id": f"LA{k:03d}", "instance_id": f"i{k}", "auto_label": "PF" if k < 4 else "TF"} for k in range(10)}
    meta = {f"i{k}": {"bug_name": f"B{k % 5}", "covariates": {"failure_type": "assertion_failure" if k % 2 else "exception"}}
            for k in range(10)}
    return key, meta


def test_kappa_perfect_and_chance():
    assert la.kappa(["PF", "TF", "AMB"], ["PF", "TF", "AMB"]) == 1.0
    assert la.kappa(["PF", "PF", "TF", "TF"], ["PF", "TF", "PF", "TF"]) == pytest.approx(0.0)


def test_kappa_known_value():
    # 2x2: agreement 0.8, both raters 50/50 -> pe 0.5 -> kappa 0.6
    a = ["PF"] * 5 + ["TF"] * 5
    b = ["PF"] * 4 + ["TF"] + ["PF"] + ["TF"] * 4
    assert la.kappa(a, b, ("PF", "TF")) == pytest.approx(0.6)


def test_consensus_defaults_to_agreement_and_counts_unresolved():
    key, meta = setup()
    a = {i: k["auto_label"] for i, k in key.items()}
    b = dict(a, LA001="TF", LA005="AMB")
    r = la.score(a, b, key, meta)
    assert r["n_scored"] == 10 and r["consensus_vs_execution"]["unresolved"] == 2
    assert r["consensus_vs_execution"]["agreement"] == 1.0          # the 8 agreed items all match execution
    lo, hi = r["raters"]["kappa_ci95_bug_bootstrap"]
    assert lo <= r["raters"]["kappa"] <= hi


def test_consensus_sheet_and_mismatch_table():
    key, meta = setup()
    a = {i: k["auto_label"] for i, k in key.items()}
    b = dict(a, LA001="TF")
    cons = dict(a, LA001="TF", LA006="AMB")
    r = la.score(a, b, key, meta, cons)
    c = r["consensus_vs_execution"]
    assert c["unresolved"] == 0 and c["consensus_amb"] == 1
    assert c["confusion_consensus_by_execution"]["TF"]["PF"] == 1
    dirs = {m["direction"]: m["count"] for m in r["mismatch_categories"]}
    assert dirs == {"execution PF -> raters TF": 1, "execution TF -> raters AMB": 1}


def test_blank_decisions_are_reported_not_scored():
    key, meta = setup()
    a = {i: k["auto_label"] for i, k in key.items()}
    b = dict(a, LA009="")
    r = la.score(a, b, key, meta)
    assert r["n_scored"] == 9 and r["missing_or_invalid"] == ["LA009"]
