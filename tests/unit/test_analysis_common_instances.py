"""D-70: every comparison uses the same instances. Aborts are keyed by (level, variant): a Tier 1 abort removes the
instance from every E1-E3 arm at that level; a Tier 2 abort (S2', A1, A2, noF, impl) only from that ablation. A
level-free baseline is evaluated on the set of what it is compared with; an ablation is compared with its parent on
the intersection; a contrast with an unexplained gap is refused. Synthetic data."""
import json

import pytest

from triage import stats
from triage.analysis import Evaluation, UnequalInstanceSets, abort_exclusions, confirmatory
from triage.metrics import PF, TF

LABELS = [{"instance_id": f"i{n}", "label": lab, "bug_name": f"B{n % 5}", "project": f"P{n % 2}"}
          for n, lab in enumerate(["PF", "TF", "TF", "PF", "TF", "PF", "TF", "TF", "PF", "TF"])]
IDS = [l["instance_id"] for l in LABELS]
TRUTH = {l["instance_id"]: (PF if l["label"] == "PF" else TF) for l in LABELS}
E1E3 = [f"{a}|{lv}" for a in ("J1", "SC", "DEB") for lv in ("S0", "S1", "S2")] + ["SC-T|S1"]


def dec(iid, arm, level, rep, lab, variant="full"):
    return {"instance_id": iid, "arm": arm, "level": level, "variant": variant, "replicate": rep, "label_raw": lab,
            "cost": {}, "agreement": {"vote_share_pf": 1.0 if lab == PF else 0.0, "k": 5,
                                      "sided_with_last_presented": None, "no_evidence_cited": False}}


def guess(iid, arm, lv, rep):
    flip = (sum(map(ord, iid + arm + lv)) + rep) % 4 == 0
    return (TF if TRUTH[iid] == PF else PF) if flip else TRUTH[iid]


def decisions(skip=()):
    out = []
    for iid in IDS:
        out.append(dec(iid, "R0", None, 0, PF if iid in ("i0", "i1", "i5") else TF))
        out.append(dec(iid, "DA", None, 0, TF))
        for cond in E1E3:
            arm, lv = cond.split("|")
            if (iid, lv, "full") in skip:
                continue
            for rep in range(3):
                out.append(dec(iid, arm, lv, rep, guess(iid, arm, lv, rep)))
        for arm, lv, var in (("J1", "S1", "noF"), ("A1", "S1", "full"), ("J1", "S2", "specprime")):
            if (iid, lv, arm if arm == "A1" else var) not in skip:
                out.append(dec(iid, arm, lv, 0, guess(iid, arm + var, lv, 0), variant=var))
    return out


def rej(iid, arm, level, variant):
    return [{"instance_id": iid, "arm": arm, "level": level, "variant": variant, "replicate": str(r), "reason": "x"}
            for r in range(2)]


TIER1 = rej("i3", "J1", "S1", "full") + rej("i3", "DEB", "S1", "full")
TIER1_SKIP = {("i3", "S1", "full")}
TIER2 = rej("i5", "J1", "S2", "specprime") + rej("i6", "J1", "S1", "noF") + rej("i7", "A1", "S1", "full")
TIER2_SKIP = {("i5", "S2", "specprime"), ("i6", "S1", "noF"), ("i7", "S1", "A1")}


def test_abort_exclusions_are_keyed_by_level_and_variant():
    assert abort_exclusions(TIER1) == {("S1", "full"): {"i3"}}
    assert abort_exclusions(TIER2) == {("S2", "specprime"): {"i5"}, ("S1", "noF"): {"i6"}, ("S1", "A1"): {"i7"}}
    assert abort_exclusions([]) == {}


def test_tier1_abort_leaves_every_e1e3_arm_at_that_level_only():
    ev = Evaluation(decisions(TIER1_SKIP), LABELS, exclusions=abort_exclusions(TIER1))
    for c in ("J1|S1", "SC|S1", "DEB|S1", "SC-T|S1"):
        assert {d["instance_id"] for d in ev.by_cond[c]} == set(IDS) - {"i3"}
    assert {d["instance_id"] for d in ev.by_cond["J1|S0"]} == set(IDS)
    assert {d["instance_id"] for d in ev.by_cond["J1|S1|noF"]} == set(IDS)    # its own set; i3 not aborted there
    assert ev.exclusion_counts()["S1|full"] == {"instances": 1, "PF": 1, "TF": 0}


def test_baseline_and_cross_level_contrasts_use_the_common_set():
    ev = Evaluation(decisions(TIER1_SKIP), LABELS, exclusions=abort_exclusions(TIER1))
    same = ev._restricted(set(IDS) - {"i3"})
    k = ev.contrast("H1", ["J1|S1"], ["R0"])
    assert k.estimate_b == pytest.approx(stats.point_estimate(same.tensor("R0"), "f1"))
    assert k.estimate_a == pytest.approx(stats.point_estimate(same.tensor("J1|S1"), "f1"))
    k0 = ev.contrast("S0 vs R0", ["J1|S0"], ["R0"])                    # S0 untouched: all instances
    assert k0.estimate_b == pytest.approx(stats.point_estimate(ev._restricted(set(IDS)).tensor("R0"), "f1"))
    assert k.estimate_b != pytest.approx(k0.estimate_b)                # i3 (a PF that R0 misses) really left
    x = ev.contrast("S1 vs S0", ["J1|S1"], ["J1|S0"])
    assert x.estimate_b == pytest.approx(stats.point_estimate(same.tensor("J1|S0"), "f1"))
    assert ev.baseline_summary("R0", "S1")["n_instances"] == 9


def test_ablation_is_compared_with_its_parent_on_the_intersection():
    ev = Evaluation(decisions(TIER1_SKIP | TIER2_SKIP), LABELS,
                    exclusions=abort_exclusions(TIER1 + TIER2))
    k = ev.contrast("noF", ["J1|S1|noF"], ["J1|S1"])
    both = ev._restricted(set(IDS) - {"i3", "i6"})                     # Tier 1 abort AND the ablation's own
    assert k.estimate_b == pytest.approx(stats.point_estimate(both.tensor("J1|S1"), "f1"))
    k2 = ev.contrast("specprime", ["J1|S2|specprime"], ["J1|S2"])
    assert k2.estimate_b == pytest.approx(stats.point_estimate(ev._restricted(set(IDS) - {"i5"}).tensor("J1|S2"), "f1"))
    assert {d["instance_id"] for d in ev.by_cond["A1|S1"]} == set(IDS) - {"i7"}


def same(a, b) -> bool:   # NaN-aware equality (DA has no precision)
    return json.dumps(a, sort_keys=True, default=float) == json.dumps(b, sort_keys=True, default=float)


def test_tier2_aborts_leave_every_e1e3_set_and_result_unchanged():
    base = Evaluation(decisions(TIER1_SKIP), LABELS, exclusions=abort_exclusions(TIER1))
    more = Evaluation(decisions(TIER1_SKIP | TIER2_SKIP), LABELS, exclusions=abort_exclusions(TIER1 + TIER2))
    for c in E1E3:
        assert base.allowed(c) == more.allowed(c)
        assert {d["instance_id"] for d in base.by_cond[c]} == {d["instance_id"] for d in more.by_cond[c]}
        assert same(base.summary(c), more.summary(c))
    for c in ("R0", "DA"):
        assert same(base.baseline_summary(c), more.baseline_summary(c))
    jd = set(IDS) - {"i9"}
    cb, cm = confirmatory(base, jd), confirmatory(more, jd)
    assert [c["name"] for c in cb["f1"]] == ["H1", "H2a", "H2b", "H3a", "H3b"]
    assert same(cb, cm)


def test_unexplained_gap_is_refused():
    ev = Evaluation(decisions({("i5", "S1", "full")}), LABELS, exclusions={})   # missing without an abort record
    with pytest.raises(UnequalInstanceSets):
        ev.contrast("H1", ["J1|S1"], ["R0"])
    decs = [d for d in decisions() if not (d["instance_id"] == "i6" and d["arm"] == "J1" and d["level"] == "S1"
                                           and d["replicate"] == 2 and d["variant"] == "full")]
    with pytest.raises(UnequalInstanceSets):                           # a missing replicate is a gap too
        Evaluation(decs, LABELS).contrast("S1 vs S0", ["J1|S1"], ["J1|S0"])
