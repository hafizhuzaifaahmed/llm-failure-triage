"""D-107: pair unanimity is defined like KUU (all valid TEST_FAULT discards; anything else keeps)."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
spec = importlib.util.spec_from_file_location("kuu_loo", ROOT / "scripts" / "analysis" / "kuu_loo.py")
loo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loo)
TF, PF = loo.TF, loo.PF


def test_pair_unanimity_rule():
    assert loo.unanimous([TF, TF]) == TF
    assert loo.unanimous([TF, PF]) == PF
    assert loo.unanimous([TF, None]) == PF and loo.unanimous([TF, "INVALID"]) == PF
    assert loo.unanimous([TF, TF, TF]) == TF and loo.unanimous([]) == PF


def test_pairs_cover_every_leave_one_out():
    assert set(loo.PAIRS) == {"M1+E6B", "M1+M2", "M2+E6B"}
    assert all(len(set(p)) == 2 for p in loo.PAIRS.values())
