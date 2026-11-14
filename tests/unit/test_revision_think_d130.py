"""D-130 thinking-judge follow-up: sign conventions and scoring of scripts/analysis/revision_think.py on synthetic data."""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "analysis"))
import revision_think as rt  # noqa: E402
from triage import revision_metrics as rm  # noqa: E402

PF, TF, INV = rm.PF, rm.TF, rm.INVALID


def fake_dataset(n_bugs=12):
    """Each bug: two PF tests and two TF tests."""
    bug, lab, ids = {}, {}, []
    for b in range(n_bugs):
        for k, y in enumerate((PF, PF, TF, TF)):
            i = f"b{b}-{k}"
            ids.append(i)
            bug[i], lab[i] = f"bug{b}", y
    return SimpleNamespace(ids=ids, bug=bug, lab=lab)


def test_identical_arms_give_zero_and_unsupported():
    D = fake_dataset()
    pred = {i: (PF if n % 3 else TF) for n, i in enumerate(D.ids)}
    h = rt.hypotheses(D, D.ids, pred, dict(pred))
    assert h["HT-1"]["delta"] == pytest.approx(0.0) and h["HT-2"]["delta"] == 0.0
    assert not h["HT-1"]["supported"] and not h["HT-2"]["supported"]
    assert h["n_bugs"] == 12 and h["n_instances"] == 48


def test_signs_better_thinking_supported():
    """Thinking perfect, DEB discards every PF and keeps every TF: dMCC > 0 and dPF-lost < 0, both supported."""
    D = fake_dataset()
    think = {i: D.lab[i] for i in D.ids}
    deb = {i: (TF if D.lab[i] == PF else PF) for i in D.ids}
    h = rt.hypotheses(D, D.ids, think, deb)
    assert h["HT-1"]["delta"] > 0 and h["HT-1"]["supported"]
    assert h["HT-2"]["delta"] == -24.0 and h["HT-2"]["pf_lost_thinking"] == 0.0 and h["HT-2"]["supported"]
    assert h["HT-1"]["p_holm"] >= h["HT-1"]["p"]


def test_signs_worse_thinking_never_supported():
    D = fake_dataset()
    think = {i: (TF if D.lab[i] == PF else PF) for i in D.ids}
    deb = {i: D.lab[i] for i in D.ids}
    h = rt.hypotheses(D, D.ids, think, deb)
    assert h["HT-1"]["delta"] < 0 and not h["HT-1"]["supported"]
    assert h["HT-2"]["delta"] > 0 and not h["HT-2"]["supported"]


def test_think_pred_policies_change_only_capped():
    run = {"a": {"label": INV, "capped": True}, "b": {"label": INV, "capped": False}, "c": {"label": PF, "capped": False}}
    ids = list(run)
    assert rt.think_pred(run, ids, "as_TF") == {"a": TF, "b": TF, "c": PF}
    assert rt.think_pred(run, ids, "keep") == {"a": PF, "b": TF, "c": PF}
    assert rt.think_pred(run, ids, "exclude") == {"a": None, "b": TF, "c": PF}


def test_tensor_skips_excluded_and_counts_cells():
    D = fake_dataset(2)
    pred = {i: PF for i in D.ids}
    pred[D.ids[0]] = None                                  # excluded PF of bug0
    pred[D.ids[2]] = TF                                    # TN of bug0
    T, bugs = rt.tensor(D, D.ids, pred)
    assert bugs == ["bug0", "bug1"]
    assert T[0, 0].tolist() == [1, 1, 0, 1]                # TP, FP, FN, TN
    assert T[1, 0].tolist() == [2, 2, 0, 0]
