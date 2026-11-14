"""D-65: a generated class whose braces do not balance (truncated model output) is a class-level compile failure
(NC_CLASS), not an execution error. Synthetic source; javac is never reached."""
from pathlib import Path

from triage import execution

TRUNCATED = """package p;
import org.junit.Test;
public class TruncTest {
    @Test public void a() { int x = 1; }
    @Test public void b() {
        Object o = new Object() {
            @Override public String toString() {
"""


def test_truncated_class_is_class_error(monkeypatch, tmp_path):
    def no_javac(*a, **k):
        raise AssertionError("javac must not be called for an unparseable class")
    monkeypatch.setattr(execution, "_javac", no_javac)
    comp = execution.compile_on_both(TRUNCATED, "p", "TruncTest", {}, {}, Path(tmp_path))
    assert comp["compiled"] == [] and comp["nc_one_version"] == []
    assert comp["nc_both"] == []
    assert comp["class_error"].startswith("unparseable class")
    assert comp["passes"] == 0
