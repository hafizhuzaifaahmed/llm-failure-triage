"""D-102: select_g counts a class with unbalanced braces instead of crashing."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("select_g", ROOT / "scripts" / "local" / "select_g.py")
sg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sg)

GOOD = """package p;
import org.junit.Test;
public class ATest {
    @Test public void a() { int x = 1; }
    @Test public void b() { int y = 2; }
}
"""
BAD = """package p;
import org.junit.Test;
public class ATest {
    @Test public void a() { int x = 1; }
    @Test public void b() { if (true) { int y = 2; }
"""


def test_parseable_class_counts_its_methods():
    n, bodies = sg.generated_methods({"source": GOOD, "n_tests": 2})
    assert n == 2 and len(bodies) == 2


def test_unbalanced_class_counts_as_generated_not_parsed():
    n, bodies = sg.generated_methods({"source": BAD, "n_tests": 2})
    assert n == 2 and bodies is None


def test_unbalanced_class_without_count_is_zero():
    assert sg.generated_methods({"source": BAD}) == (0, None)
