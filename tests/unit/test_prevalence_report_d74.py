"""D-74: every analysis output states the PF prevalence of the scored set, KA's F1 at that prevalence, F1 with MCC and
the prevalence-adjusted precision beside it, and that F1 is not comparable between D1 and D2. Synthetic data."""
import math

import pytest

from triage.analysis import F1_NOT_COMPARABLE, Evaluation, judged_prevalence, prevalence_report
from triage.metrics import PF, TF

LABELS = [{"instance_id": f"i{n}", "label": lab, "bug_name": f"B{n % 4}", "project": "P"}
          for n, lab in enumerate(["PF", "PF", "PF", "PF", "TF", "TF", "TF", "AMB", "PF", "TF"])]


def dec(iid, arm, level, lab):
    return {"instance_id": iid, "arm": arm, "level": level, "variant": "full" if level else None, "replicate": 0,
            "label_raw": lab, "cost": {}, "agreement": {}}


def decisions():
    out = []
    for l in LABELS:
        out.append(dec(l["instance_id"], "KA", None, PF))
        out.append(dec(l["instance_id"], "J1", "S1", PF if l["label"] == "PF" or l["instance_id"] == "i4" else TF))
    return out


def report(exclusions=None, weights=None):
    ev = Evaluation(decisions(), LABELS, weights or {}, exclusions=exclusions)
    summ = {"KA": ev.baseline_summary("KA"), "J1|S1": ev.summary("J1|S1")}
    return prevalence_report(ev, summ, "D2", {"D1": {"pf_prevalence": 0.31}})


def test_ka_f1_is_reported_at_this_datasets_prevalence():
    r = report()
    assert (r["PF"], r["TF"]) == (5, 4)                       # AMB excluded
    p = 5 / 9
    assert r["pf_prevalence"] == pytest.approx(p) and r["tf_per_pf"] == pytest.approx(0.8)
    assert r["ka_f1"] == pytest.approx(2 * p / (1 + p)) == pytest.approx(r["ka_f1_expected_2p_over_1_plus_p"])


def test_prevalence_follows_the_primary_level_set_after_an_abort():
    r = report(exclusions={("S1", "full"): {"i0"}})
    assert (r["PF"], r["TF"]) == (4, 4)
    assert r["ka_f1"] == pytest.approx(2 * 0.5 / 1.5)


def test_every_condition_carries_f1_mcc_and_prevalence_adjusted_precision():
    r = report(weights={"i4": 2.0, "i5": 2.0, "i6": 2.0, "i9": 2.0})
    rows = {x["condition"]: x for x in r["conditions"]}
    assert set(rows) == {"KA", "J1|S1"}
    for x in rows.values():
        assert list(x)[2:5] == ["f1", "mcc", "precision"] and not math.isnan(x["precision_prev_adj"])
    assert rows["J1|S1"]["precision"] == pytest.approx(5 / 6)
    assert rows["J1|S1"]["precision_prev_adj"] == pytest.approx(5 / 7)   # the one FP counts twice (TF weight 2)
    assert math.isnan(rows["KA"]["mcc"]) or rows["KA"]["mcc"] == 0      # constant predictor: MCC undefined/zero


def test_the_output_says_f1_is_not_comparable_between_d1_and_d2():
    r = report()
    assert r["note"] == F1_NOT_COMPARABLE and "not comparable between D1 and D2" in r["note"]
    assert r["judged_sample_prevalence_by_dataset"] == {"D1": {"pf_prevalence": 0.31}}


def test_judged_prevalence_reads_labels_of_the_sample_only():
    p = judged_prevalence(LABELS, ["i0", "i4", "i7", "i8"])
    assert p == {"PF": 2, "TF": 1, "AMB": 1, "pf_prevalence": pytest.approx(2 / 3), "tf_per_pf": 0.5}


def test_summary_puts_mcc_beside_f1():
    ev = Evaluation(decisions(), LABELS)
    keys = list(ev.summary("J1|S1"))
    assert keys[keys.index("f1_ci95") + 1] == "mcc"
