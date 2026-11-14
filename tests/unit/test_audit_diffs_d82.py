"""D-82 protocol note: packet diffs are standard unified diffs, buggy -> fixed."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("diffs", ROOT / "scripts" / "audit" / "diffs.py")
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)

SRC = """diff --git a/src/X.java b/src/X.java
index 1111111..2222222 100644
--- a/src/X.java
+++ b/src/X.java
@@ -10,4 +10,5 @@ class X {
     int a = 1;
-    int b = fixed();
+    int b = buggy();
+    int c = extra();
     return a;
 }"""


def test_reversal_swaps_sides_headers_and_index():
    out = d.reverse_unified_diff(SRC)
    lines = out.splitlines()
    assert lines[1] == "index 2222222..1111111 100644"
    assert lines[2] == "--- a/src/X.java" and lines[3] == "+++ b/src/X.java"
    assert lines[4] == "@@ -10,5 +10,4 @@ class X {"
    assert lines[5:9] == ["     int a = 1;", "-    int b = buggy();", "-    int c = extra();", "+    int b = fixed();"]
    old, new = d.sides(SRC)
    rold, rnew = d.sides(out)
    assert (rold, rnew) == (new, old)


def test_minus_lines_precede_plus_lines_in_every_block():
    out = d.reverse_unified_diff(SRC)
    signs = "".join(ln[0] for ln in out.splitlines()[5:] if ln and ln[0] in "+-")
    assert signs == "--+"


def test_no_newline_marker_stays_with_its_line():
    src = SRC + "\n" + d.NOEOL
    out = d.reverse_unified_diff(src)
    assert out.splitlines()[-1] == d.NOEOL


@pytest.mark.skipif(not (ROOT / "data" / "external" / "EvalAndMitigate").exists(), reason="replication package absent")
def test_every_packaged_fix_reverses_exactly():
    base = ROOT / "data" / "external" / "EvalAndMitigate" / "data" / "d4j2_fix_info"
    n = 0
    for p in base.glob("*/buggy_fix_info.json"):
        info = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        for ch in info.get("fixing_changes", []):
            src = ch.get("diff", "")
            if not src:
                continue
            out = d.reverse_unified_diff(src)
            o, nw = d.sides(src)
            assert d.sides(out) == (nw, o), p
            for blk in _blocks(out):
                assert blk == "".join(sorted(blk, key=lambda c: c != "-")), p   # '-' before '+'
            n += 1
    assert n > 100


def _blocks(diff):
    cur, out = "", []
    for ln in diff.splitlines():
        if ln and ln[0] in "+-" and not ln.startswith(("--- ", "+++ ")):
            cur += ln[0]
        elif cur:
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out


def test_blank_line_between_joined_diffs_is_kept():
    out = d.reverse_unified_diff(SRC + "\n\n" + SRC)
    assert "" in out.splitlines() and out.count("index 2222222..1111111") == 2
