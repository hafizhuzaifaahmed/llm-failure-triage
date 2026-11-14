"""D-132 fully local cascade: the rule and its scoring on synthetic data (no repository votes are read)."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "analysis"))
import revision_local_cascade as lc  # noqa: E402
from triage import revision_metrics as rm  # noqa: E402

PF, TF, INV = rm.PF, rm.TF, rm.INVALID


@pytest.mark.parametrize("votes,think,expected", [
    ([TF, TF, TF], PF, TF),          # unanimous TF discards; the thinking judge is never asked
    ([PF, PF, PF], TF, PF),          # unanimous PF keeps
    ([TF, TF, PF], TF, TF),          # disagreement: thinking label decides
    ([TF, PF, PF], PF, PF),
    ([TF, TF, INV], TF, TF),         # an invalid vote is a disagreement
    ([TF, TF, None], TF, TF),        # a missing vote is a disagreement
    ([TF, TF, PF], INV, PF),         # invalid / capped thinking answer keeps
    ([TF, TF, PF], None, PF),        # missing thinking answer keeps
])
def test_rule(votes, think, expected):
    assert lc.local_cascade(votes, think) == expected


def test_tier1_matches_the_d105_cascade():
    import cascade
    for vs in ([TF] * 3, [PF] * 3, [TF, PF, TF], [TF, TF, INV], [TF, TF]):
        assert lc.tier1(vs) == cascade.tier1(vs)
        for t in (TF, PF, INV, None):
            assert lc.local_cascade(vs, t) == cascade.cascade(vs, t)


def test_tensor_and_describe_average_replicates():
    ids = ["a", "b", "c", "d"]
    D = SimpleNamespace(bug={"a": "x", "b": "x", "c": "y", "d": "y"}, lab={"a": PF, "b": TF, "c": PF, "d": TF})
    perfect = {i: D.lab[i] for i in ids}
    keep_all = {i: PF for i in ids}
    T = lc.tensor_reps(D, ids, {0: perfect, 1: keep_all})
    assert T.shape == (2, 2, 4)
    assert T[:, 0, :].sum(axis=0).tolist() == [2, 0, 0, 2]      # TP FP FN TN
    assert T[:, 1, :].sum(axis=0).tolist() == [2, 2, 0, 0]
    W = np.ones((5, 2))
    d = lc.describe(D, ids, {0: perfect, 1: keep_all}, W)
    assert d["tpr"] == pytest.approx(1.0) and d["tnr"] == pytest.approx(0.5)
    assert d["pf_lost"] == 0.0 and d["bugs_lost"] == 0.0 and d["replicates"] == 2
