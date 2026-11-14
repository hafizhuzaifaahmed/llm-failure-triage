"""D-115 feature encoding (no study data)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "analysis"))
import revision_learned as rl  # noqa: E402


def test_exception_families():
    assert rl.exc_family("java.lang.AssertionError") == "assertion"
    assert rl.exc_family("org.junit.ComparisonFailure") == "assertion"
    assert rl.exc_family("java.lang.NumberFormatException") == "IllegalArgumentException"
    assert rl.exc_family("java.lang.ArrayIndexOutOfBoundsException") == "IndexOutOfBounds"
    assert rl.exc_family("com.x.CustomException") == "other"
    assert rl.exc_family(None) == "other"


def test_vote_values_invalid_is_neutral():
    assert rl.vote_value(rl.rc.PF) == 1.0 and rl.vote_value(rl.rc.TF) == 0.0
    assert rl.vote_value(rl.rc.INV) == 0.5 and rl.vote_value(None) == 0.5
