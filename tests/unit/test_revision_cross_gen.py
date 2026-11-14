"""D-118 agreement rule on synthetic failure keys (no study data)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "analysis"))
import revision_cross_gen as cg  # noqa: E402


def k(outcome="assertion_failure", exc="java.lang.AssertionError", exp="1", act="2", frame=None):
    return {"method": "t", "outcome": outcome, "exception": exc, "expected": exp, "actual": act, "frame": frame}


def test_assertion_agreement_needs_same_expected_and_actual():
    assert cg.agrees(k(), k())
    assert not cg.agrees(k(), k(act="3"))
    assert not cg.agrees(k(), k(exp="0"))
    assert not cg.agrees(k(exp=None, act=None), k(exp=None, act=None))      # nothing to compare
    assert not cg.comparable(k(exp=None, act=None))


def test_exception_agreement_needs_same_class_and_frame():
    a = k("exception", "java.lang.NullPointerException", None, None, "org.x.Foo.bar(Foo.java:10)")
    assert cg.agrees(a, dict(a))
    assert not cg.agrees(a, {**a, "frame": "org.x.Foo.baz(Foo.java:12)"})
    assert not cg.agrees(a, {**a, "exception": "java.lang.IllegalStateException"})
    assert not cg.agrees(a, k())                                              # outcome differs
    assert not cg.comparable({**a, "frame": None})


def test_top_main_frame_skips_test_frames():
    frames = [{"method": "org.x.FooTest.t", "location": "FooTest.java:5", "in_test": True},
              {"method": "org.x.Foo.bar", "location": "Foo.java:10", "in_test": False}]
    assert cg._top_main_frame(frames) == "org.x.Foo.bar(Foo.java:10)"
    assert cg._top_main_frame(frames[:1]) is None
