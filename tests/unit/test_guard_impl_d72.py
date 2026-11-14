"""D-72: in ablation A5a (impl) the F-only-line check runs against the package with B's verbatim body removed, since
an F-only line can be a substring of a B line (Lang_36: F adds "if (chars[i] == '.') {", B has
"} else if (chars[i] == '.') {"). Bug ids, paths and generic patterns are still checked on the whole package, and
every non-impl guard result is byte-identical to the pre-D-72 rule."""
import re
import tempfile
from pathlib import Path

import pytest

from triage.context_builder import GENERIC_PATTERNS, leakage_check
from triage.runner import Runner

from test_core import make_instance as _make_instance

SPEC = {"purpose": "p", "preconditions": "", "postconditions": "", "exceptions": "", "edge_cases": ""}


def make_instance(**over):
    return _make_instance(focal_id="f1", **over)


B_BODY = ("{\n    for (int i = 0; i < sz; i++) {\n        if (chars[i] >= '0' && chars[i] <= '9') {\n"
          "            foundDigit = true;\n        } else if (chars[i] == '.') {\n            hasDecPoint = true;\n"
          "        }\n    }\n    return foundDigit && !hasExp;\n}")
F_ONLY = "if (chars[i] == '.') {"
GUARD = {"bug_ids": ["Lang_36", "Lang-36"], "code_lines": [F_ONLY, "// single trailing decimal point after non-exponent is ok"],
         "paths": ["triage_work"]}


def pre_d72(package_text, guard=None, extra_lines=None):
    """The guard as it was before D-72 (reference for the byte-identical check)."""
    guard = guard or {}
    hits = []
    for bid in guard.get("bug_ids", []):
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(bid)}(?![0-9])", package_text):
            hits.append(bid)
    low = package_text.lower()
    for s in list(guard.get("code_lines", [])) + list(guard.get("paths", [])) + list(extra_lines or []):
        s = (s or "").strip()
        if len(s) >= 6 and s.lower() in low:
            hits.append(s)
    for pat in GENERIC_PATTERNS:
        hits += re.findall(pat, package_text)
    return hits


def runner(guard):
    return Runner(Path(tempfile.mkdtemp()), None, None, None, {"f1": SPEC}, {"f1": SPEC}, forbidden={"i1": guard})


def test_lang36_pair_is_accepted_for_impl():
    inst = make_instance(impl=B_BODY)
    pkg, hits = runner(GUARD).package_for(inst, "S1", "impl")
    assert "[Impl1] " + B_BODY in pkg.text
    assert hits == []
    assert pre_d72(pkg.text, GUARD) == [F_ONLY]                 # the defect: B's own line fired


def test_real_f_only_leak_outside_the_body_is_still_blocked():
    test_src = "@Test\npublic void t() {\n  // " + F_ONLY + "\n  assertTrue(NumberUtils.isNumber(\"1.\"));\n}"
    inst = make_instance(impl=B_BODY, test={"method_source": test_src, "imports": [], "fixtures": ""})
    _, hits = runner(GUARD).package_for(inst, "S1", "impl")
    assert hits == [F_ONLY]


def test_b_body_is_still_checked_for_bug_ids_paths_and_generic_patterns():
    body = B_BODY.replace("return", "// Lang_36 triage_work Math_90b fixed_version\n    return")
    _, hits = runner(GUARD).package_for(make_instance(impl=body), "S1", "impl")
    assert hits == ["Lang_36", "triage_work", "fixed_version", "Lang_36", "Math_90b"]   # guard, then generic patterns


def test_exempt_body_only_narrows_code_lines():
    text = "=== [Impl] ===\n[Impl1] " + B_BODY + "\nsee " + F_ONLY
    assert leakage_check(text, GUARD, exempt_body=B_BODY) == [F_ONLY]       # the copy outside the body
    assert leakage_check(text, GUARD) == pre_d72(text, GUARD)


@pytest.mark.parametrize("variant", ["full", "noF", "specprime"])
@pytest.mark.parametrize("level", ["S0", "S1", "S2"])
def test_non_impl_variants_are_byte_identical(level, variant):
    for impl in (B_BODY, "{ return Integer.valueOf(str); }", ""):
        for guard in (GUARD, {"code_lines": ["return foundDigit && !hasExp;"]}, {}):
            inst = make_instance(impl=impl)
            r = runner(guard)
            pkg, hits = r.package_for(inst, level, variant)
            body = impl[impl.find("{") + 1:] if "{" in impl else ""
            extra = [l.strip() for l in body.split("\n") if len(l.strip()) >= 25]
            assert hits == pre_d72(pkg.text, guard, extra)
