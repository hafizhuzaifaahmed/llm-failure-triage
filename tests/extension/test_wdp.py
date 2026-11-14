"""Unit tests for whole-method dependence probes (WDP; OPUS_EXECUTION_BRIEF.md version 2, section 3.2, T1 to T10)."""
import importlib.util
import itertools
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from triage_dep import interventions as iv
from triage_dep import levels as lv
from triage_dep import screen

ROOT = Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---- T1 boundary ------------------------------------------------------------------------------------------------
def test_t1_wdp_has_no_path_to_the_other_version_labels_developer_tests_or_votes():
    forbidden = [r"\bruns_f\b", r"\bcompile_f\b", r"\bmeta_f\b", r"ground_truth", r"labels_D", r"labels_", r"label_side",
                 r"classes\.modified", r"tests\.trigger", r"dir\.src\.tests", r"fixed_bodies", r"sigma_F", r"guard_D",
                 r"/f\b['\"]", r"decisions\.jsonl", r"LOCAL_CONF_VOTE", r"revision_common", r"label_raw",
                 r"\bvotes\b", r"GT_STORE"]
    files = sorted((ROOT / "src" / "triage_dep").glob("*.py")) + [ROOT / "scripts/extension/run_wdp_tranche.py"]
    assert len(files) == 6
    for f in files:
        text = f.read_text(encoding="utf-8")
        for pat in forbidden:
            assert not re.search(pat, text), f"{f.name} mentions {pat}"
    eng = (ROOT / "src/triage_dep/wdp.py").read_text(encoding="utf-8")
    assert "load_meta" in eng and "meta_b" not in eng       # checkout access only through the engine's whitelist


# ---- T2 variants -------------------------------------------------------------------------------------------------
X_THROW_SPEC = ('{ try { java.lang.String __wdp_m = java.lang.System.getenv("WDP_MARKER"); if (__wdp_m != null) { new '
                'java.io.File(__wdp_m).createNewFile(); } } catch (java.lang.Throwable __wdp_t) { } throw new '
                'java.lang.Error("__WDP__"); }')


@pytest.mark.parametrize("decl,rt,bodies", [
    ("void", "void", ["{ }"]),
    ("boolean", "boolean", ["{ return false; }", "{ return true; }"]),
    *[(t, t, ["{ return 0; }", "{ return 1; }"]) for t in ("byte", "short", "int", "long", "float", "double")],
    ("char", "char", ["{ return ' '; }", "{ return 'A'; }"]),
    ("String", "String", ['{ return ""; }', '{ return "A"; }']),
    ("java.lang.String", "java.lang.String", ['{ return ""; }', '{ return "A"; }']),
    ("Object", "Object", ["{ return null; }"]),
    ("int[]", "int[]", ["{ return null; }"]),
    ("List<String>", "List<String>", ["{ return null; }"]),
    ("Map<K, V[]>", "Map<K, V[]>", ["{ return null; }"]),
    ("Integer", "Integer", ["{ return null; }"]),
])
def test_t2_variants_follow_the_table(decl, rt, bodies):
    text = f"public {decl} m(int a) {{\n    return x;\n}}"
    assert iv.return_type(text) == rt
    vs = iv.variants(text)
    assert vs[0] == {"id": "X-THROW", "body": X_THROW_SPEC}
    assert [v["body"] for v in vs[1:]] == bodies
    assert [v["id"] for v in vs] == ["X-THROW"] + [f"X-RET-{k}" for k in range(1, len(bodies) + 1)]
    assert len(vs) <= 3
    assert iv.variants(text) == vs                                      # ids and bodies stable


def test_t2_x_throw_body_is_the_spec_string_byte_for_byte():
    spec = (ROOT / "docs/research_extension/TECHNICAL_METHOD_SPEC.md").read_text(encoding="utf-8")
    block = re.search(r"```java\r?\n(.*?)\r?\n```", spec, re.S).group(1)
    assert iv.X_THROW_BODY == block == X_THROW_SPEC


@pytest.mark.parametrize("header,rt", [
    ("@Override\n  public static final synchronized int m()", "int"),
    ("@SuppressWarnings({\"unchecked\", \"rawtypes\"}) protected <T extends Comparable<? super T>> T m(T a)", "T"),
    ("public <K, V> java.util.Map<K, java.util.List<V>> m()", "java.util.Map<K, java.util.List<V>>"),
    ("/** doc */ private @Deprecated String m()", "String"),
    ("public Foo(int x)", None),                                        # constructor: no declared type
    ("int m", None),                                                    # no parameter list
])
def test_t2_return_type_parsing(header, rt):
    assert iv.return_type(header + " { return null; }") == rt


def test_t2_unparseable_header_gets_x_throw_only():
    assert [v["id"] for v in iv.variants("public Foo(int x) { this.x = x; }")] == ["X-THROW"]


# ---- T3 apply ----------------------------------------------------------------------------------------------------
CASES = [
    "public int m(int a) {\n  if (a > 0) { while (true) { a--; } }\n  return a;\n}",
    'public String m() {\n  String s = "}{";\n  char c = \'}\';\n  char d = \'{\';\n  return s + "{";\n}',
    "public int m() {\n  // } a closing brace in a comment\n  /* { another } */\n  return 1;\n}",
    "public void m() throws java.io.IOException, IllegalStateException {\n  throw new java.io.IOException(\"x\");\n}",
    '@SuppressWarnings(value = {"unchecked"})\n@Foo(bar = @Baz({1, 2}))\npublic void m() {\n  run();\n}',
    "public <T extends Comparable<? super T>> java.util.List<T> m(java.util.Map<String, T[]> a) {\n  return null;\n}",
    "public int[] m() {\r\n  int[] a = {1, 2};\r\n  return a;\r\n}",
]


@pytest.mark.parametrize("text", CASES)
def test_t3_apply_replaces_exactly_the_body(text):
    open_at = iv._open_brace(text)
    sig = text[:open_at]
    for v in iv.variants(text):
        out = iv.apply(text, v["body"])
        assert out.startswith(sig)                                      # signature byte-identical
        assert out[len(sig):] == v["body"]                              # exactly one body, nothing left over
        depth = 0
        for t in iv.tokenize(out[len(sig):]):
            if t.kind == "op" and t.text in "{}":
                depth += 1 if t.text == "{" else -1
        assert depth == 0


def test_t3_apply_keeps_text_after_the_body_and_crlf():
    text = "public int m() {\r\n  return 1;\r\n}\r\n"
    out = iv.apply(text, "{ }")
    assert out == "public int m() { }\r\n"


def test_t3_apply_refuses_a_method_without_body():
    with pytest.raises(ValueError):
        iv.apply("abstract int m();", "{ }")


# ---- T4 to T6 levels and certificates (spec version 4) ----------------------------------------------------------
CLS = {"SAME": "SAME", "CHANGED": "SHIFT", "ERR": "ERR", "NA": None, "BOGUS": "WEIRD"}


def rec(excluded=None, xt="SAME", entered=False, swallow=False, xr=(), surfaced=False):
    variants = [{"id": "X-THROW", "compiled": xt != "NA", "class": CLS[xt]}] + \
               [{"id": f"X-RET-{k}", "compiled": True, "class": CLS[c]} for k, c in enumerate(xr, 1)]
    return {"excluded": excluded, "variants": variants, "entered": entered, "swallow_risk": swallow,
            "surfaced": surfaced}


FO_COUPLED = {"excluded": None, "coupled": True, "n_compiled": 20}
FO_NOT = {"excluded": None, "coupled": False, "n_compiled": 20}


@pytest.mark.parametrize("r,fo,want", [
    (None, FO_COUPLED, ("ND", "excluded:no_record")),                                        # 1 (before FS)
    (None, FO_NOT, ("ND", "excluded:no_record")),
    ("junk", FO_COUPLED, ("ND", "malformed:bad_shape")),                                     # 2 (before FS)
    (rec(xr=("BOGUS",)), FO_COUPLED, ("ND", "malformed:unknown_class")),
    (rec(xt="SAME", entered=None), FO_NOT, ("ND", "malformed:entered_missing")),
    (rec(xt="CHANGED", entered=False, surfaced=True, xr=("SAME",)), FO_NOT, ("ND", "malformed:marker_inconsistent")),
    (rec(swallow=None), FO_NOT, ("ND", "malformed:swallow_risk_missing")),
    (rec(), FO_COUPLED, ("FS", None)),                                                       # 3
    (rec(excluded="baseline_not_reproduced", xt="NA", entered=None, surfaced=None), FO_COUPLED, ("FS", None)),
    (rec(excluded="baseline_not_reproduced", xt="NA", entered=None, surfaced=None), FO_NOT,
     ("ND", "excluded:baseline_not_reproduced")),                                            # 4
    (rec(), None, ("ND", "first_order_unusable")),                                           # 5
    (rec(), {"excluded": "test_compile_failed"}, ("ND", "first_order_unusable")),
    (rec(xt="ERR"), FO_NOT, ("ND", "x_throw_err")),                                          # 6
    (rec(xt="NA", entered=None, surfaced=None), FO_NOT, ("ND", "x_throw_na")),
    (rec(xt="SAME", xr=("SAME", "ERR")), FO_NOT, ("ND", "x_ret_err")),                       # 7
    (rec(xt="SAME", xr=("SAME", "CHANGED")), FO_NOT, ("WS", None)),                          # 8
    (rec(xt="CHANGED", entered=True, xr=("SAME",)), FO_NOT, ("RI", None)),                   # 9
    (rec(xt="CHANGED", entered=True, xr=()), FO_NOT, ("ND", "no_x_ret")),                    # 10
    (rec(xt="SAME", entered=True, xr=("SAME",)), FO_NOT, ("ND", "throw_swallowed")),         # 11
    (rec(xt="SAME", entered=False, swallow=True, xr=("SAME",)), FO_NOT, ("ND", "swallow_risk")),   # 12
    (rec(xt="SAME", entered=False, xr=("SAME", "SAME")), FO_NOT, ("U", None)),               # 13
])
def test_t4_one_case_per_row(r, fo, want):
    assert lv.level(r, fo) == want


XR_CLASSES = [()] + [(a,) for a in ("SAME", "CHANGED", "ERR", "BOGUS")] + \
    list(itertools.product(("SAME", "CHANGED", "ERR"), repeat=2))
ENUM = list(itertools.product((None, "test_compile_failed", "MISSING"), ("SAME", "CHANGED", "ERR", "NA", "BOGUS"),
                              (True, False, None, "yes"), (True, False, None), XR_CLASSES, (True, False, None),
                              ("coupled", "silent", "none")))
FO_OF = {"coupled": FO_COUPLED, "silent": FO_NOT, "none": None}


def test_t4_level_is_total_and_fails_closed_over_the_enumeration():
    seen = set()
    for excluded, xt, entered, swallow, xr, surfaced, fo in ENUM:
        r = None if excluded == "MISSING" else rec(excluded, xt, entered, swallow, xr, surfaced)
        out = lv.level(r, FO_OF[fo])
        assert out == lv.level(r, FO_OF[fo])
        lvl, reason = out
        assert lvl in {"FS", "ND", "WS", "RI", "U"} and ((reason is not None) == (lvl == "ND"))
        if r is None:                                     # spec v4 row 1 precedes the validity rules
            assert out == ("ND", "excluded:no_record")
        elif xt == "BOGUS" or "BOGUS" in xr:
            assert out == ("ND", "malformed:unknown_class")
        seen.add(lvl)
    assert seen == {"FS", "ND", "WS", "RI", "U"}


def test_t5_u_only_by_row13_positive_match():
    for excluded, xt, entered, swallow, xr, surfaced, fo in ENUM:
        r = None if excluded == "MISSING" else rec(excluded, xt, entered, swallow, xr, surfaced)
        lvl, _ = lv.level(r, FO_OF[fo])
        row13 = (fo == "silent" and excluded is None and xt == "SAME" and entered is False and swallow is False
                 and surfaced is False and all(c == "SAME" for c in xr))
        assert (lvl == "U") == row13, (excluded, xt, entered, swallow, xr, surfaced, fo)


# ---- T18 regression: one test per case of the authors' review table (brief 12) ---------------------------------
def _good(**over):
    r = {"instance_id": "i", "excluded": None, "entered": False, "surfaced": False, "swallow_risk": False,
         "variants": [{"id": "X-THROW", "compiled": True, "class": "SAME"},
                      {"id": "X-RET-1", "compiled": True, "class": "SAME"}]}
    r.update(over)
    return r


SILENT = {"excluded": None, "coupled": False}
COUPLED = {"excluded": None, "coupled": True}
T18 = {
    "uncompiled_xret_with_unknown_class": (
        _good(variants=[{"id": "X-THROW", "compiled": True, "class": "SAME"},
                        {"id": "X-RET-1", "compiled": False, "class": "BOGUS"}]), SILENT,
        ("ND", "malformed:unknown_class")),
    "no_record_first_order_coupled": (None, COUPLED, ("ND", "excluded:no_record")),
    "entered_missing_first_order_coupled": (_good(entered=None), COUPLED, ("ND", "malformed:entered_missing")),
    "uncompiled_xret_with_shift": (
        _good(variants=[{"id": "X-THROW", "compiled": True, "class": "SAME"},
                        {"id": "X-RET-1", "compiled": False, "class": "SHIFT"}]), SILENT,
        ("ND", "malformed:uncompiled_with_class")),
    "compiled_as_string_false": (
        _good(variants=[{"id": "X-THROW", "compiled": True, "class": "SAME"},
                        {"id": "X-RET-1", "compiled": "false", "class": "SHIFT"}]), SILENT,
        ("ND", "malformed:bad_shape")),
    "two_x_throw_variants": (
        _good(variants=[{"id": "X-THROW", "compiled": True, "class": "SAME"},
                        {"id": "X-THROW", "compiled": True, "class": "SHIFT"}]), SILENT,
        ("ND", "malformed:variant_ids")),
    "unexpected_variant_id": (
        _good(variants=[{"id": "X-THROW", "compiled": True, "class": "SAME"},
                        {"id": "ZZZ", "compiled": True, "class": "SAME"}]), SILENT,
        ("ND", "malformed:variant_ids")),
    "first_order_summary_missing": (_good(), None, ("ND", "first_order_unusable")),
    "first_order_summary_excluded": (_good(), {"excluded": "baseline_not_reproduced"}, ("ND", "first_order_unusable")),
    "first_order_coupled_string_false": (_good(), {"excluded": None, "coupled": "False"},
                                         ("ND", "first_order_unusable")),
    "surfaced_string_true_entered_false": (_good(surfaced="true"), SILENT, ("ND", "malformed:surfaced_missing")),
    "compiled_xret_with_null_class": (
        _good(variants=[{"id": "X-THROW", "compiled": True, "class": "SAME"},
                        {"id": "X-RET-1", "compiled": True, "class": None}]), SILENT,
        ("ND", "malformed:compiled_not_run")),
}


@pytest.mark.parametrize("name", sorted(T18))
def test_t18_review_case(name):
    r, s, want = T18[name]
    assert lv.level(r, s) == want
    assert lv.level(_good(), SILENT) == ("U", None)          # the same record, made valid, is U: the case is real


# ---- T19, T20 necessary conditions on raw inputs; never raises ---------------------------------------------------
# Written from spec section 2.4 "Necessary conditions, stated on the raw inputs", without any helper of levels.py.
_KNOWN = ("SAME", "SHIFT", "FLIP", "ERR")


def _raw_shape_ok(r):
    if not isinstance(r, dict):
        return False
    ex = r.get("excluded")
    if not (ex is None or (isinstance(ex, str) and ex != "")):
        return False
    vs = r.get("variants")
    if not isinstance(vs, list) or not all(isinstance(v, dict) for v in vs):
        return False
    if not all(isinstance(v.get("id"), str) and isinstance(v.get("compiled"), bool) for v in vs):
        return False
    if any(v.get("class") is not None and v.get("class") not in _KNOWN for v in vs):
        return False
    if any(v.get("compiled") is False and v.get("class") is not None for v in vs):
        return False
    return True


def _raw_valid_nonexcluded(r):
    if not _raw_shape_ok(r) or r.get("excluded") is not None:
        return False
    vs = r["variants"]
    ids = [v["id"] for v in vs]
    others = [i for i in ids if i != "X-THROW"]
    if ids.count("X-THROW") != 1 or len(others) > 2 or len(set(others)) != len(others) \
            or not all(i in ("X-RET-1", "X-RET-2") for i in others):
        return False
    if any(v["compiled"] is True and v.get("class") is None for v in vs):
        return False
    return isinstance(r.get("swallow_risk"), bool)


def _silent(s):
    return isinstance(s, dict) and s.get("excluded") is None and s.get("coupled") is False


def _check_necessary(r, s, lvl):
    if lvl == "U":
        assert _raw_valid_nonexcluded(r) and _silent(s)
        xt = [v for v in r["variants"] if v["id"] == "X-THROW"]
        assert len(xt) == 1 and xt[0]["compiled"] is True and xt[0]["class"] == "SAME"
        assert all((v["compiled"] is True and v["class"] == "SAME") or (v["compiled"] is False and v.get("class") is None)
                   for v in r["variants"] if v["id"] != "X-THROW")
        assert r.get("entered") is False and r.get("surfaced") is False and r.get("swallow_risk") is False
    elif lvl == "RI":
        assert _raw_valid_nonexcluded(r) and _silent(s)
        xt = [v for v in r["variants"] if v["id"] == "X-THROW"]
        assert len(xt) == 1 and xt[0]["compiled"] is True and xt[0]["class"] in ("SHIFT", "FLIP")
        rets = [v for v in r["variants"] if v["id"] != "X-THROW"]
        assert any(v["compiled"] is True for v in rets)
        assert all((v["compiled"] is True and v["class"] == "SAME") or (v["compiled"] is False and v.get("class") is None)
                   for v in rets)
        assert isinstance(r.get("entered"), bool) and isinstance(r.get("surfaced"), bool)
    elif lvl == "WS":
        assert _raw_valid_nonexcluded(r) and _silent(s)
        assert any(v["id"] != "X-THROW" and v["compiled"] is True and v["class"] in ("SHIFT", "FLIP")
                   for v in r["variants"])
    elif lvl == "FS":
        assert _raw_shape_ok(r) and isinstance(s, dict) and s.get("coupled") is True
        if r.get("excluded") is None:
            assert _raw_valid_nonexcluded(r)


def _check_any(r, s):
    out = lv.level(r, s)                                       # T20: must not raise
    assert isinstance(out, tuple) and len(out) == 2
    lvl, reason = out
    assert lvl in ("FS", "ND", "WS", "RI", "U")
    assert (lvl == "ND") == (isinstance(reason, str) and reason != "")
    if lvl != "ND":
        assert reason is None
    _check_necessary(r, s, lvl)
    return lvl


_COMPILED = (True, False, "false", None)
_CLASSES = ("SAME", "SHIFT", "FLIP", "ERR", None, "BOGUS")
_TRI = (True, False, None, "true")


def _enum_inputs():
    """Brief 12.3 (a): record present / absent / non-dict; excluded variants; X-THROW absent / once / twice;
    zero to two further variants; entered, surfaced, swallow_risk and first-order summary over their ranges.
    Factors are crossed in blocks so the case count stays bounded while every value of every factor appears with
    every value of the level-relevant factors."""
    fos = [None, {"excluded": "x"}, {"excluded": None, "coupled": True}, {"excluded": None, "coupled": False},
           {"excluded": None, "coupled": None}, {"excluded": None, "coupled": "False"}, ["not", "a", "dict"]]
    yield None, None
    yield "junk", {"excluded": None, "coupled": True}
    yield ["junk"], {"excluded": None, "coupled": False}
    variant = [{"id": i, "compiled": c, "class": k} for i in ("X-THROW", "X-RET-1", "X-RET-2", "ZZZ")
               for c in _COMPILED for k in _CLASSES]
    xthrows = [[]] + [[v] for v in variant if v["id"] == "X-THROW"] + \
        [[{"id": "X-THROW", "compiled": True, "class": "SAME"}, {"id": "X-THROW", "compiled": c, "class": k}]
         for c in _COMPILED for k in _CLASSES]
    others = [[]] + [[v] for v in variant if v["id"] != "X-THROW"] + \
        [[{"id": "X-RET-1", "compiled": True, "class": "SAME"}, v] for v in variant if v["id"] != "X-THROW"] + \
        [[{"id": "X-RET-1", "compiled": True, "class": "SAME"}, {"id": "X-RET-1", "compiled": True, "class": "SAME"}]]
    singles = [o for o in others if len(o) <= 1]
    pairs = [o for o in others if len(o) == 2]
    flags = ((False, False, False), (True, True, False), (True, False, False), (False, False, True),
             (None, None, False), ("true", False, False), (False, "true", False), (False, True, False),
             (False, False, None))
    for ex in (None, "baseline_not_reproduced", "", 7):        # every X-THROW form x every single further variant
        for xt in xthrows:
            for ot in singles:
                for fo in fos:
                    yield ({"excluded": ex, "variants": xt + ot, "entered": False, "surfaced": False,
                            "swallow_risk": False}, fo)
    rep_xt = [[{"id": "X-THROW", "compiled": True, "class": k}] for k in ("SAME", "SHIFT", "ERR")] + [[]]
    for xt in rep_xt:                                          # two further variants x the flag patterns
        for ot in pairs + singles:
            for e, su, sw in flags:
                for fo in fos:
                    yield ({"excluded": None, "variants": xt + ot, "entered": e, "surfaced": su,
                            "swallow_risk": sw}, fo)
    base = {"excluded": None, "variants": [{"id": "X-THROW", "compiled": True, "class": "SAME"}]}
    for e in _TRI:                                             # the three flags over their full ranges
        for su in _TRI:
            for sw in (True, False, None):
                for fo in fos:
                    yield {**base, "entered": e, "surfaced": su, "swallow_risk": sw}, fo


def test_t19_t20_enumeration():
    n, levels_seen = 0, set()
    for r, s in _enum_inputs():
        levels_seen.add(_check_any(r, s))
        n += 1
    assert n > 50_000 and levels_seen == {"FS", "ND", "WS", "RI", "U"}


def _junk(rng, depth=0):
    k = rng.randrange(9 if depth < 3 else 6)
    if k == 0:
        return None
    if k == 1:
        return rng.choice([True, False])
    if k == 2:
        return rng.choice([0, 1, -1, 2.5, 10**12])
    if k == 3:
        return rng.choice(["", "SAME", "SHIFT", "FLIP", "ERR", "BOGUS", "X-THROW", "X-RET-1", "X-RET-2", "ZZZ",
                           "true", "false", "False", "baseline_not_reproduced"])
    if k == 4:
        return rng.choice(["SAME", "SHIFT", "FLIP", "ERR", None])
    if k == 5:
        return rng.choice([True, False, None, "true"])
    if k in (6, 7):
        return [_junk(rng, depth + 1) for _ in range(rng.randrange(4))]
    return {rng.choice(["id", "compiled", "class", "excluded", "entered", "x"]): _junk(rng, depth + 1)
            for _ in range(rng.randrange(4))}


def _fuzz_record(rng):
    if rng.random() < 0.05:
        return _junk(rng)
    nv = rng.randrange(5)
    vs = []
    for _ in range(nv):
        v = {"id": rng.choice(["X-THROW", "X-THROW", "X-RET-1", "X-RET-2", "ZZZ", 3, None]),
             "compiled": rng.choice([True, True, False, "false", None, 1]),
             "class": rng.choice(["SAME", "SAME", "SHIFT", "FLIP", "ERR", None, "BOGUS", 0, ["SAME"]])}
        if rng.random() < 0.1:
            v[rng.choice(["id", "compiled", "class"])] = _junk(rng)
        if rng.random() < 0.05:
            v.pop(rng.choice(["id", "compiled", "class"]))
        vs.append(v)
    r = {"excluded": rng.choice([None, None, None, "x", "", 0, False]),
         "variants": vs if rng.random() > 0.03 else _junk(rng),
         "entered": rng.choice([True, False, None, "true", 0]), "surfaced": rng.choice([True, False, None, "true"]),
         "swallow_risk": rng.choice([True, False, False, None, "false"])}
    for k in list(r):
        if rng.random() < 0.03:
            r.pop(k)
    return r


def _fuzz_summary(rng):
    k = rng.random()
    if k < 0.1:
        return _junk(rng)
    return {"excluded": rng.choice([None, None, None, "x", ""]),
            "coupled": rng.choice([True, False, False, None, "False", "True", 0, 1])}


def _fuzz_near_valid(rng):
    """A valid record (so that U, RI and WS are reachable), then zero to three random corruptions."""
    vs = [{"id": "X-THROW", "compiled": True, "class": rng.choice(["SAME", "SAME", "SHIFT", "FLIP", "ERR"])}]
    for vid in rng.sample(["X-RET-1", "X-RET-2"], rng.randrange(3)):
        comp = rng.random() < 0.85
        vs.append({"id": vid, "compiled": comp,
                   "class": rng.choice(["SAME", "SAME", "SAME", "SHIFT", "FLIP", "ERR"]) if comp else None})
    entered = rng.random() < 0.5
    r = {"excluded": None, "variants": vs, "entered": entered,
         "surfaced": entered and rng.random() < 0.5, "swallow_risk": rng.random() < 0.1}
    for _ in range(rng.choice([0, 0, 1, 1, 2, 3])):
        m = rng.randrange(9)
        cur = r.get("variants")
        live = [x for x in cur if isinstance(x, dict)] if isinstance(cur, list) else []
        v = rng.choice(live) if live else None
        if m == 0 and v is not None:
            v["class"] = _junk(rng)                                  # junk class, compiled or not
        elif m == 1 and v is not None:
            v["compiled"] = _junk(rng)
        elif m == 2 and v is not None:
            v["compiled"], v["class"] = False, rng.choice(["SAME", "SHIFT", "BOGUS"])   # class on uncompiled
        elif m == 3 and isinstance(cur, list):
            cur.append({"id": rng.choice(["X-THROW", "X-RET-1", "ZZZ"]), "compiled": rng.choice([True, False]),
                                  "class": rng.choice(["SAME", "SHIFT", None])})          # duplicate / unexpected id
        elif m == 4:
            r[rng.choice(["entered", "surfaced", "swallow_risk"])] = _junk(rng)
        elif m == 5:
            r.pop(rng.choice(list(r)))
        elif m == 6:
            r["excluded"] = _junk(rng)
        elif m == 7 and v is not None:
            v.pop(rng.choice(list(v)))
        elif m == 8:
            r["surfaced"], r["entered"] = True, rng.choice([False, None, "true"])        # marker inconsistent
    return r


def test_t19_t20_seeded_fuzz():
    """Two seeded streams of 120,000 cases each: arbitrary JSON-like records, and corrupted near-valid records.
    Every case is checked against the necessary conditions; the run must show all five levels so that the U, RI
    and WS conditions are exercised rather than vacuously true."""
    import random
    rng = random.Random(20261114)
    seen, n = set(), 0
    for _ in range(120_000):
        seen.add(_check_any(_fuzz_record(rng), _fuzz_summary(rng)))
        seen.add(_check_any(_fuzz_near_valid(rng), _fuzz_summary(rng)))
        n += 2
    assert n >= 200_000 and seen == {"FS", "ND", "WS", "RI", "U"}


# ---- T21 development-ledger regression ----------------------------------------------------------------------------
def test_t21_dev_ledger_levels_unchanged_from_1b8e667(tmp_path):
    led_p = ROOT / "results/extension/wdp/WDP_D1_DEV/ledger.jsonl"
    fo_p = ROOT / "results/extension/probes/CFP_D1_DEV2/ledger.jsonl"
    if not led_p.exists():
        pytest.skip("WDP_D1_DEV ledger absent")
    old_src = subprocess.run(["git", "show", "1b8e667:src/triage_dep/levels.py"], cwd=ROOT, capture_output=True,
                             text=True, encoding="utf-8", stdin=subprocess.DEVNULL)
    if old_src.returncode != 0:
        pytest.skip("git history unavailable")
    pkg = tmp_path / "triage_dep_old"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "interventions.py").write_text((ROOT / "src/triage_dep/interventions.py").read_text(encoding="utf-8"),
                                          encoding="utf-8")
    (pkg / "levels.py").write_text(old_src.stdout, encoding="utf-8")
    sys.path.insert(0, str(tmp_path))
    try:
        import importlib
        old = importlib.import_module("triage_dep_old.levels")
    finally:
        sys.path.remove(str(tmp_path))
    recs = [json.loads(l) for l in led_p.read_text(encoding="utf-8").splitlines() if l.strip()]
    fo = {json.loads(l)["instance_id"]: json.loads(l)["summary"]
          for l in fo_p.read_text(encoding="utf-8").splitlines() if l.strip()}
    assert len(recs) == 118
    new = {r["instance_id"]: lv.level(r, fo.get(r["instance_id"])) for r in recs}
    prev = {r["instance_id"]: old.level(r, fo.get(r["instance_id"])) for r in recs}
    assert new == prev
    from collections import Counter
    assert Counter(l for l, _ in new.values()) == {"FS": 83, "U": 16, "WS": 14, "RI": 5}
    assert all(lv.malformed(r) is None for r in recs)


def test_t6_certificates():
    PF, TF = lv.PF, lv.TF
    for lvl in ("FS", "ND", "WS", "RI", "U"):
        assert lv.cd_u(TF, lvl) == TF and lv.cd_ur(TF, lvl) == TF            # never PF for a TF base
        assert lv.cd_u(PF, lvl) == (TF if lvl == "U" else PF)
        assert lv.cd_ur(PF, lvl) == (TF if lvl in ("U", "RI") else PF)
    assert lv.cd_u(PF, "ND") == PF and lv.cd_ur(PF, "ND") == PF


# ---- T7 screen ---------------------------------------------------------------------------------------------------
def wrap(body):
    return f"package p;\nimport org.junit.*;\npublic class T {{\n  @Test public void t() throws Exception {{\n{body}\n  }}\n}}\n"


POSITIVE = [
    "try { f(); } catch (Throwable t) { }",
    "try { f(); } catch (final Error e) { }",
    "try { f(); } catch (java.lang.Throwable t) { }",
    "try { f(); } catch (IOException | Error e) { }",
    "assertThrows(Error.class, () -> f());",
    "Assert.assertThrows(Throwable.class, () -> f());",
    "expectThrows(Throwable.class, () -> f());",
    "thrown.expect(Throwable.class);",
]
NEGATIVE = [
    "try { f(); } catch (AssertionError e) { }",
    "try { f(); } catch (Exception e) { }",
    "try { f(); } catch (MyError e) { }",
    "MyError e = new MyError();",
    "assertThrows(IllegalStateException.class, () -> f());",
    "thrown.expect(RuntimeException.class);",
]


@pytest.mark.parametrize("body", POSITIVE)
def test_t7_screen_fires(body):
    assert screen.swallow_risk(wrap(body))


@pytest.mark.parametrize("ann", ["@Test(expected = Throwable.class)", "@Test(expected=java.lang.Error.class)",
                                 "@Test(timeout = 100, expected = Error.class)"])
def test_t7_screen_fires_on_expected_annotation(ann):
    src = f"package p;\npublic class T {{\n  {ann}\n  public void t() {{ f(); }}\n}}\n"
    assert screen.swallow_risk(src)


@pytest.mark.parametrize("body", NEGATIVE)
def test_t7_screen_negatives(body):
    assert not screen.swallow_risk(wrap(body))


def test_t7_throws_throwable_in_a_signature_does_not_fire():
    src = "package p;\npublic class T {\n  @Test public void t() throws Throwable { f(); }\n}\n"
    assert not screen.swallow_risk(src)
    assert not screen.swallow_risk("public class T { @Test(expected = IllegalStateException.class) public void t() {} }")


@pytest.mark.parametrize("construct", POSITIVE + ["@Test(expected = Throwable.class)",
                                                  "@Test(expected=java.lang.Error.class)"])
def test_t7_constructs_inside_comments_and_strings_do_not_fire(construct):
    esc = construct.replace("\\", "\\\\").replace('"', '\\"')
    for body in (f"// {construct}", f"/* {construct} */", f"/** {construct} */", f'String s = "{esc}";'):
        assert not screen.swallow_risk(wrap(body)), body


# ---- T8 run_test_env equals the engine's run_test without extra env ----------------------------------------------
def test_t8_run_test_env_matches_engine_run_test(monkeypatch):
    from triage_dep import wdp
    from triage_ext import probe
    calls = []

    class P:
        returncode = 1
        stdout = ("noise\n<<<TRIAGE-RESULT>>>\noutcome=assertion_failure\nexception=java.lang.AssertionError\n"
                  "message=expected:<1> but was:<2>\ntrace=at p.T.t(T.java:12)\n<<<END-TRIAGE-RESULT>>>\n")

    def fake_run(cmd, **kw):
        calls.append((list(cmd), dict(kw)))
        return P()
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(probe, "ensure_runner", lambda: Path("/runner"))
    monkeypatch.setattr(wdp, "ensure_runner", lambda: Path("/runner"))
    meta = {"workdir": "/w/b", "cp.test": "/w/b/classes:/lib.jar"}
    a = probe.run_test("p.T", "t", "/front", meta, timeout=10)
    b = wdp.run_test_env("p.T", "t", "/front", meta, timeout=10, extra_env={})
    c = wdp.run_test_env("p.T", "t", "/front", meta, timeout=10)
    assert calls[0] == calls[1] == calls[2]
    for r in (a, b, c):
        r.pop("duration_s")
    assert a == b == c and a["failing_test_line"] == 12
    wdp.run_test_env("p.T", "t", "/front", meta, timeout=10, extra_env={"WDP_MARKER": "/m"})
    assert calls[3][1]["env"] == {**calls[0][1]["env"], "WDP_MARKER": "/m"} and calls[3][0] == calls[0][0]


def test_t8_timeout_record_matches(monkeypatch):
    from triage_dep import wdp
    from triage_ext import probe

    def boom(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, kw["timeout"])
    monkeypatch.setattr(subprocess, "run", boom)
    monkeypatch.setattr(probe, "ensure_runner", lambda: Path("/runner"))
    monkeypatch.setattr(wdp, "ensure_runner", lambda: Path("/runner"))
    meta = {"workdir": "/w/b", "cp.test": "/c"}
    assert probe.run_test("p.T", "t", "/f", meta, 10) == wdp.run_test_env("p.T", "t", "/f", meta, 10, {})


# ---- T14 driver approval gate (temporary git repository; the real approval file is never touched) -----------------
def _g(repo, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c",
                           "commit.gpgsign=false", *args], cwd=repo, capture_output=True, text=True, stdin=subprocess.DEVNULL,
                          check=True).stdout.strip()


@pytest.fixture
def gate(tmp_path, monkeypatch):
    drv = _load("run_wdp_tranche_t14", "scripts/extension/run_wdp_tranche.py")
    repo = tmp_path / "repo"
    (repo / "configs" / "extension").mkdir(parents=True)
    manifest = repo / "configs" / "extension" / "wdp_frozen.json"
    manifest.write_text('{"decision": "D-148"}\n', encoding="utf-8", newline="\n")
    _g(repo, "init", "-q")
    _g(repo, "add", "-A")
    _g(repo, "commit", "-q", "-m", "freeze")
    freeze_id = _g(repo, "rev-parse", "HEAD")
    (repo / "later.txt").write_text("x", encoding="utf-8")
    _g(repo, "add", "-A")
    _g(repo, "commit", "-q", "-m", "later")
    side = _g(repo, "commit-tree", _g(repo, "rev-parse", "HEAD^{tree}"), "-m", "not an ancestor")
    monkeypatch.setattr(drv, "ROOT", repo)
    monkeypatch.setattr(drv.FREEZE, "check", lambda: [])
    approval = tmp_path / "approval.json"
    return drv, repo, approval, freeze_id, side


def _args(drv, run, **over):
    b = dict(drv.RUNS[run])
    b.update(over)
    return (run, b["instances"], b["frame"], b["exec_dir"], b["cand_dir"], b["split"])


def _refused(drv, approval, args, needle):
    with pytest.raises(drv.Refused) as e:
        drv.authorize(*args, approval=approval)
    assert needle in str(e.value), str(e.value)
    return str(e.value)


def test_t14_refusals_without_approval(gate):
    drv, repo, approval, freeze_id, side = gate
    for run in drv.EVALUATION_RUNS:
        _refused(drv, approval, _args(drv, run), "is absent")
    assert drv.authorize(*_args(drv, "WDP_D1_DEV"), approval=approval)["approved_freeze_commit"] is None
    _refused(drv, approval, _args(drv, "WDP_D1_DEV", split="test"), "inputs not those bound")
    _refused(drv, approval, ("WDP_OTHER", "a", "b", "c", "d", None), "unknown run name")
    assert sorted(drv.RUNS) == sorted(["WDP_D1_DEV", *drv.EVALUATION_RUNS]) and len(drv.RUNS) == 5


def test_t14_refusals_with_a_bad_approval_file(gate, monkeypatch):
    drv, repo, approval, freeze_id, side = gate
    run = _args(drv, "WDP_CONF_F1")
    approval.write_text("not json", encoding="utf-8")
    _refused(drv, approval, run, "unreadable or not JSON")
    approval.write_text(json.dumps(["x"]), encoding="utf-8")
    _refused(drv, approval, run, "full 40-hex")
    approval.write_text(json.dumps({"freeze_commit": freeze_id[:12]}), encoding="utf-8")
    _refused(drv, approval, run, "full 40-hex")
    approval.write_text(json.dumps({"freeze_commit": "0" * 40}), encoding="utf-8")
    _refused(drv, approval, run, "does not exist")
    approval.write_text(json.dumps({"freeze_commit": side}), encoding="utf-8")
    _refused(drv, approval, run, "not an ancestor")
    approval.write_text(json.dumps({"freeze_commit": freeze_id}), encoding="utf-8")
    monkeypatch.setattr(drv.FREEZE, "check", lambda: ["file changed: src/triage_dep/levels.py"])
    _refused(drv, approval, run, "frozen-file check failed")
    monkeypatch.setattr(drv.FREEZE, "check", lambda: [])
    (repo / "configs/extension/wdp_frozen.json").write_text('{"decision": "other"}\n', encoding="utf-8")
    _refused(drv, approval, run, "differs from the approved commit's manifest")
    (repo / "configs/extension/wdp_frozen.json").write_text('{"decision": "D-148"}\n', encoding="utf-8",
                                                           newline="\n")
    _refused(drv, approval, _args(drv, "WDP_D1_DEV"), "engineering run is closed")
    _refused(drv, approval, ("WDP_OTHER", "a", "b", "c", "d", None), "unknown run name")
    _refused(drv, approval, _args(drv, "WDP_CONF_F1", instances=drv.RUNS["WDP_CONF_F2"]["instances"]),
             "inputs not those bound")
    _refused(drv, approval, _args(drv, "WDP_D1_TEST", split="dev"), "inputs not those bound")

    def no_git(*a, **k):
        raise OSError("git not found")
    monkeypatch.setattr(subprocess, "run", no_git)
    _refused(drv, approval, run, "git unavailable")


def test_t14_accepts_the_correct_case_and_stops_before_reading_instances(gate, monkeypatch):
    drv, repo, approval, freeze_id, side = gate
    approval.write_text(json.dumps({"freeze_commit": freeze_id, "approved_by": "authors"}), encoding="utf-8")
    for run in drv.EVALUATION_RUNS:
        prov = drv.authorize(*_args(drv, run), approval=approval)
        assert prov["approved_freeze_commit"] == freeze_id
        assert prov["execution_commit"] == _g(repo, "rev-parse", "HEAD") != freeze_id
        assert prov["frozen_check"]["status"] == "passed" and len(prov["frozen_check"]["manifest_sha256"]) == 64
        assert isinstance(prov["worktree_dirty_paths"], list)

    class Stop(Exception):
        pass

    def stop(p):
        raise Stop(str(p))
    monkeypatch.setattr(drv, "APPROVAL", approval)
    monkeypatch.setattr(drv, "read_jsonl", stop)
    b = drv.RUNS["WDP_CONF_CTRL"]
    monkeypatch.setattr(sys, "argv", ["x", "--run", "WDP_CONF_CTRL", "--instances", b["instances"], "--frame",
                                      b["frame"], "--exec-dir", b["exec_dir"], "--cand-dir", b["cand_dir"]])
    with pytest.raises(Stop) as e:
        drv.main()
    assert "instances_D1C_CTRL" in str(e.value)
    assert not (repo / "results").exists()                        # nothing created before the instances are read


def test_t14_main_exits_non_zero_before_reading_or_creating_anything(gate, monkeypatch):
    drv, repo, approval, freeze_id, side = gate
    monkeypatch.setattr(drv, "APPROVAL", approval)
    for run in drv.EVALUATION_RUNS:
        b = drv.RUNS[run]
        argv = ["x", "--run", run, "--instances", b["instances"], "--frame", b["frame"], "--exec-dir",
                b["exec_dir"], "--cand-dir", b["cand_dir"]] + (["--split", b["split"]] if b["split"] else [])
        monkeypatch.setattr(sys, "argv", argv)
        with pytest.raises(SystemExit) as e:
            drv.main()
        assert "refused" in str(e.value.code)
    assert not (repo / "results").exists()


def test_t17_no_run_approval_file_exists():
    assert not (ROOT / "configs/extension/wdp_run_approval.json").exists()


def test_freeze_check_is_one_implementation_imported_by_the_driver():
    drv = _load("run_wdp_tranche_t14b", "scripts/extension/run_wdp_tranche.py")
    text = (ROOT / "scripts/extension/run_wdp_tranche.py").read_text(encoding="utf-8")
    assert "FREEZE.check()" in text and "def check" not in text
    assert drv.FREEZE.__file__.endswith("freeze_wdp.py")


# ---- T9 analysis on a synthetic fixture -------------------------------------------------------------------------
def _wrec(i, xt, entered, xr, swallow=False, excluded=None, surfaced=False):
    r = rec(excluded, xt, entered, swallow, xr)
    r.update({"instance_id": i, "surfaced": surfaced, "seconds": 2.0,
              "baseline": None if excluded == "test_compile_failed" else {"outcome": "assertion_failure"}})
    for v in r["variants"]:
        v["outcome"] = "assertion_failure" if v["class"] else None
    return r


def _fixture():
    an = _load("wdp_analysis", "scripts/extension/wdp_analysis.py")
    # bug A: PF test a1 is level U (lost under CD-U); TF a2 is U. bug B: PF b1 WS, TF b2 U, TF b3 ND throw_swallowed.
    # bug C: PF c1 FS, TF c2 RI, TF c3 ND excluded. bug D: TF d1 U, TF d2 ND swallow_risk.
    spec = [  # id, bug, project, label, wdp record, fo summary (decoupled?)
        ("a1", "Math_59", "Math", "PF", _wrec("a1", "SAME", False, ("SAME",)), {"coupled": False, "decoupled": True, "n_compiled": 12}),
        ("a2", "Math_59", "Math", "TF", _wrec("a2", "SAME", False, ("SAME",)), {"coupled": False, "decoupled": True, "n_compiled": 12}),
        ("b1", "Lang_1", "Lang", "PF", _wrec("b1", "SAME", True, ("CHANGED",)), {"coupled": False, "decoupled": False, "n_compiled": 3}),
        ("b2", "Lang_1", "Lang", "TF", _wrec("b2", "SAME", False, ()), {"coupled": False, "decoupled": False, "n_compiled": 3}),
        ("b3", "Lang_1", "Lang", "TF", _wrec("b3", "SAME", True, ("SAME",)), {"coupled": False, "decoupled": False, "n_compiled": 30}),
        ("c1", "Codec_2", "Codec", "PF", _wrec("c1", "CHANGED", True, ("CHANGED",), surfaced=True), {"coupled": True, "decoupled": False, "n_compiled": 30}),
        ("c2", "Codec_2", "Codec", "TF", _wrec("c2", "CHANGED", True, ("SAME",), surfaced=True), {"coupled": False, "decoupled": True, "n_compiled": 30}),
        ("c3", "Codec_2", "Codec", "TF", _wrec("c3", "NA", None, (), excluded="test_compile_failed"), None),
        ("d1", "JacksonCore_1", "JacksonCore", "TF", _wrec("d1", "SAME", False, ("SAME", "SAME")), {"coupled": False, "decoupled": True, "n_compiled": 15}),
        ("d2", "JacksonCore_1", "JacksonCore", "TF", _wrec("d2", "SAME", False, ("SAME",), swallow=True), {"coupled": False, "decoupled": True, "n_compiled": 15}),
    ]
    labels, wled, fled = [], {}, {}
    for i, bug, proj, lab, w, s in spec:
        labels.append({"instance_id": i, "bug_name": bug, "project": proj, "label": lab})
        wled[i] = w
        if s is not None:
            fled[i] = {"summary": {"excluded": None, **s}, "seconds": 10.0}
    f1 = an.make_rows("F1", [l for l in labels if l["instance_id"][0] in "ab"], wled, fled)
    f2 = an.make_rows("F2", [l for l in labels if l["instance_id"][0] in "cd"], wled, fled)
    pilot = an.make_rows("D1-test", [{**l, "instance_id": "p" + l["instance_id"]} for l in labels],
                         {"p" + k: {**v, "instance_id": "p" + k} for k, v in wled.items()},
                         {"p" + k: v for k, v in fled.items()})
    ctrl = an.make_rows("CTRL", [{"instance_id": "x1", "bug_name": "Lang_1", "project": "Lang", "label": "TF"}],
                        {"x1": _wrec("x1", "SAME", False, ("SAME",))},
                        {"x1": {"summary": {"excluded": None, "coupled": False, "decoupled": False, "n_compiled": 12}}})
    ids = [r["id"] for r in f1 + f2]
    kuu = {i: "PROGRAM_FAULT" for i in ids}
    kuu["c2"] = "TEST_FAULT"                                            # KUU already discards one TF
    conf = {"ids": ids, "KUU": dict(kuu), "2-of-3": {i: "TEST_FAULT" for i in ids}}
    pids = ["p" + i for i in ids]
    pil = {"ids": pids, "KUU": {"p" + k: v for k, v in kuu.items()}, "2-of-3": {i: "PROGRAM_FAULT" for i in pids}}
    return an, {"F1": f1, "F2": f2, "D1-test": pilot, "CTRL": ctrl}, conf, pil


def test_t9_levels_rules_lost_bug_and_nd_reasons():
    an, frames, conf, pil = _fixture()
    out = an.analyse(frames, conf, pil, seed=20261113)
    lev = {r["id"]: (r["level"], r["reason"]) for r in frames["F1"] + frames["F2"]}
    assert lev == {"a1": ("U", None), "a2": ("U", None), "b1": ("WS", None), "b2": ("U", None),
                   "b3": ("ND", "throw_swallowed"), "c1": ("FS", None), "c2": ("RI", None),
                   "c3": ("ND", "excluded:test_compile_failed"), "d1": ("U", None), "d2": ("ND", "swallow_risk")}
    assert out["populations"]["CONF-all"] == {"instances": 10, "PF": 3, "TF": 7, "bugs": 4, "bugs_with_PF": 3}
    p = out["primary"]
    assert p["bugs_lost_KUU"] == [] and p["bugs_lost_KUU_CDU"] == ["Math_59"]
    assert p["additional_bugs_lost"] == ["Math_59"] and p["safety_holds"] is False
    # TNR: KUU discards c2 only (1/7); KUU + CD-U discards a2, b2, c2, d1 (4/7)
    assert p["paired"]["TNR"]["difference"] == round(4 / 7 - 1 / 7, 4)
    assert p["criterion"]["result"] == "NOT MET" and p["criterion"]["math59_decoupled_pf_levels"] == ["U"]
    rules = out["secondary"]["6_rules"]["CONF-votes"]
    assert rules["KUU"]["TNR"] == round(1 / 7, 4) and rules["KUU"]["bugs_lost"] == 0
    assert rules["KUU+CD-U"]["bugs_lost_names"] == ["Math_59"] and rules["KUU+CD-U"]["PF_lost"] == 1
    assert rules["KUU+CD"]["bugs_lost_names"] == ["Math_59"]           # a1 is registered-decoupled
    assert rules["KUU+CD-UR"]["TNR"] == round(4 / 7, 4)                # c2 (RI) was already discarded by KUU
    assert rules["2-of-3"]["bugs_lost"] == 3 and rules["keep-all"]["TPR"] == 1.0
    assert rules["keep-all+CD-U"]["TNR"] == round(3 / 7, 4)
    from scipy import stats as sps
    assert rules["KUU+CD-U"]["upper95_bug_loss_rate"] == round(float(sps.beta.ppf(0.95, 2, 2)), 4)
    diag = out["secondary"]["12_diagnostics"]
    assert diag["F1"]["TF"]["ND_throw_swallowed"] == 1 and diag["F2"]["TF"]["ND_swallow_risk"] == 1
    assert diag["F2"]["TF"]["exclusions"] == {"test_compile_failed": 1}
    assert diag["F1"]["PF"]["x_throw_same_x_ret_changed"] == 1
    lad = out["secondary"]["4_ladder"]["by_dataset"]["CONF"]
    assert lad["TF"] == {"n": 7, "FS": 0, "WS": 0, "RI": 1, "U": 3, "ND": 3,
                         "ND_by_reason": {"excluded:test_compile_failed": 1, "swallow_risk": 1, "throw_swallowed": 1}}
    assert out["secondary"]["4_ladder"]["registered_decoupled"]["CONF"]["TF"]["U"] == 2
    assert out["secondary"]["5_low_mutant_stratum"]["CONF"]["PF"]["WS"] == 1
    pre = out["secondary"]["8_prefilter"]["CONF-votes"]
    assert pre["level_U"] == 4 and pre["level_U_already_discarded_by_KUU"] == 0 and pre["judge_calls_avoided"] == 12
    u3 = out["secondary"]["3_level_U_by_label"]["CONF-all"]["U"]
    assert (u3["TF_flagged"], u3["TF"], u3["PF_flagged"], u3["PF"]) == (3, 7, 1, 3)
    assert u3["difference_TF_minus_PF"] == round(3 / 7 - 1 / 3, 4)
    assert out["secondary"]["10_control"]["TF"]["U"] == 1
    q = out["quality_checks"]["per_run"]["F2"]
    assert q["marker_violations"] == 0 and q["technical_ND"] == 1 and q["passes"] is False   # 1 of 5 > 5%
    assert "pooled_bound" not in out
    assert out["secondary"]["11_cost"]["F2"]["executions_mean"] == round((3 + 3 + 0 + 4 + 3) / 5, 3)


def test_t9_bootstrap_is_deterministic_under_the_seed():
    an, frames, conf, pil = _fixture()
    a = an.analyse(frames, json.loads(json.dumps(conf)), json.loads(json.dumps(pil)), seed=20261113)
    b = an.analyse(frames, json.loads(json.dumps(conf)), json.loads(json.dumps(pil)), seed=20261113)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    ci = a["primary"]["paired"]["TNR"]["ci95"]
    assert ci[0] <= a["primary"]["paired"]["TNR"]["difference"] <= ci[1]


def test_t9_marker_violation_and_met_criterion():
    an, frames, conf, pil = _fixture()
    for r in frames["F1"]:                                              # make Math_59's PF test WS: safety holds
        if r["id"] == "a1":
            r["level"] = "WS"
    frames["F2"][0]["surfaced"], frames["F2"][0]["entered"] = True, False
    out = an.analyse(frames, conf, pil, seed=20261113)
    assert out["primary"]["safety_holds"] is True
    assert out["quality_checks"]["per_run"]["F2"]["marker_violations"] == 1
    crit = out["primary"]["criterion"]
    assert crit["i_safety"] and crit["iii_math59_decoupled_pf_not_U"]
    assert crit["result"] == ("MET" if crit["ii_ci_lower_above_0"] else "NOT MET")


def test_t9_report_renders(tmp_path):
    an, frames, conf, pil = _fixture()
    out = an.analyse(frames, conf, pil, seed=20261113)
    rep = _load("wdp_report", "scripts/extension/wdp_report.py")
    text = rep.render(json.loads(json.dumps(out)))
    assert text.splitlines()[0] == ("Status: exploratory; protocol frozen internally in Git before the run; not "
                                    "externally preregistered; designed after the confirmation outcomes were known.")
    assert "no entry observed and throw-invariant" in text and "Primary criterion: NOT MET" in text
    for banned in ("confirmatory", "validated", "held-out", "unreachable"):
        assert banned not in text.lower()


# ---- freeze manifest (present only after P3) ---------------------------------------------------------------------
def test_wdp_freeze_manifest_matches_when_present():
    fz = _load("freeze_wdp", "scripts/extension/freeze_wdp.py")
    if not fz.MANIFEST.exists():
        pytest.skip("wdp_frozen.json not written yet")
    doc = json.loads(fz.MANIFEST.read_text(encoding="utf-8"))
    assert {f: fz.content_hash(f) for f in doc["files"]} == doc["files"]
    assert fz.parameters() == doc["parameters"]
    assert set(fz.FILES) == set(doc["files"])


# ---- T15 raw-ledger gate: aborts before any label is read -------------------------------------------------------
def _write_jsonl(p, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8", newline="\n")


def _gate_tree(tmp_path, an, ledger_rows_for):
    """A miniature repository: instances files and WDP ledgers of the four evaluation runs (two instances each)."""
    for run, (fr, inst_file, split) in an.EVALUATION_LEDGERS.items():
        ids = [f"{run}-a", f"{run}-b"]
        _write_jsonl(tmp_path / inst_file, [{"instance_id": i, "split": split or "test"} for i in ids]
                     + ([{"instance_id": f"{run}-dev", "split": "dev"}] if split else []))
        rows = ledger_rows_for(run, ids)
        _write_jsonl(tmp_path / "results/extension/wdp" / run / "ledger.jsonl", rows)


def _ok(i):
    return {"instance_id": i, "surfaced": True, "entered": True}


def _run_main_expect_abort(an, tmp_path, monkeypatch):
    def labels_read(*a, **k):
        raise AssertionError("labels or votes were read before the gate")
    monkeypatch.setattr(an, "ROOT", tmp_path)
    monkeypatch.setattr(an, "load_frames", labels_read)
    monkeypatch.setattr(an, "load_conf_bases", labels_read)
    monkeypatch.setattr(an, "load_pilot_bases", labels_read)
    out = tmp_path / "results/extension/wdp/wdp_analysis.json"
    monkeypatch.setattr(sys, "argv", ["x", "--out", str(out)])
    with pytest.raises(SystemExit) as e:
        an.main()
    assert e.value.code not in (0, None)
    assert not out.exists()
    return json.loads((tmp_path / "results/extension/wdp/wdp_analysis_ABORTED.json").read_text(encoding="utf-8"))


def test_t15_marker_violation_only_in_an_amb_record_aborts(tmp_path, monkeypatch):
    an = _load("wdp_analysis_t15a", "scripts/extension/wdp_analysis.py")

    def rows(run, ids):
        r = [_ok(i) for i in ids]
        if run == "WDP_CONF_F2":
            r[1] = {"instance_id": ids[1], "surfaced": True, "entered": False}     # the AMB-labelled test
        return r
    _gate_tree(tmp_path, an, rows)
    # this record would never reach a scored row: it is labelled AMB
    labels = [{"instance_id": "WDP_CONF_F2-a", "bug_name": "B_1", "project": "B", "label": "TF"},
              {"instance_id": "WDP_CONF_F2-b", "bug_name": "B_1", "project": "B", "label": "AMB"}]
    led = {r["instance_id"]: {**r, "variants": [], "excluded": None, "swallow_risk": False}
           for r in rows("WDP_CONF_F2", ["WDP_CONF_F2-a", "WDP_CONF_F2-b"])}
    scored = an.make_rows("F2", labels, led, {})
    assert [r["id"] for r in scored] == ["WDP_CONF_F2-a"] and not any(r["surfaced"] and not r["entered"]
                                                                       for r in scored)
    doc = _run_main_expect_abort(an, tmp_path, monkeypatch)
    assert doc["failed_runs"] == ["WDP_CONF_F2"]
    assert doc["runs"]["WDP_CONF_F2"]["marker_violations"] == ["WDP_CONF_F2-b"]
    assert all(doc["runs"][r]["passes"] for r in ("WDP_D1_TEST", "WDP_CONF_F1", "WDP_CONF_CTRL"))


def test_t15_missing_or_duplicated_instance_aborts(tmp_path, monkeypatch):
    an = _load("wdp_analysis_t15b", "scripts/extension/wdp_analysis.py")

    def rows(run, ids):
        if run == "WDP_D1_TEST":
            return [_ok(ids[0])]                                       # one instance missing
        if run == "WDP_CONF_CTRL":
            return [_ok(ids[0]), _ok(ids[1]), _ok(ids[1])]             # one instance duplicated
        return [_ok(i) for i in ids]
    _gate_tree(tmp_path, an, rows)
    doc = _run_main_expect_abort(an, tmp_path, monkeypatch)
    assert doc["failed_runs"] == ["WDP_D1_TEST", "WDP_CONF_CTRL"]
    assert doc["runs"]["WDP_D1_TEST"]["missing"] == ["WDP_D1_TEST-b"]
    assert doc["runs"]["WDP_CONF_CTRL"]["duplicated"] == ["WDP_CONF_CTRL-b"]
    assert doc["runs"]["WDP_D1_TEST"]["records"] == 1 and doc["runs"]["WDP_D1_TEST"]["instances"] == 2


def test_t15_a_complete_consistent_set_passes_the_gate(tmp_path, monkeypatch):
    an = _load("wdp_analysis_t15c", "scripts/extension/wdp_analysis.py")
    _gate_tree(tmp_path, an, lambda run, ids: [_ok(i) for i in ids])
    monkeypatch.setattr(an, "ROOT", tmp_path)
    gate = an.raw_ledger_gate(tmp_path / "out")
    assert gate["passes"] and not (tmp_path / "out" / "wdp_analysis_ABORTED.json").exists()
    assert gate["runs"]["WDP_D1_TEST"]["instances"] == 2                 # the dev instance is not counted


# ---- T16 leave-one-project-out for U and U or RI ----------------------------------------------------------------
def test_t16_leave_one_project_out_level_contrasts():
    an, frames, conf, pil = _fixture()
    out = an.analyse(frames, conf, pil, seed=20261113)
    lp = out["secondary"]["9_heterogeneity"]["leave_one_project_out_levels"]
    want = {  # project left out -> (U: TF flagged, TF, PF flagged, PF), (U or RI: same)
        "Math": ((2, 6, 0, 2), (3, 6, 0, 2)),
        "Lang": ((2, 5, 1, 2), (3, 5, 1, 2)),
        "Codec": ((3, 5, 1, 2), (3, 5, 1, 2)),
        "JacksonCore": ((2, 5, 1, 3), (3, 5, 1, 3)),
    }
    assert set(lp) == set(want)
    for p, (u, ur) in want.items():
        for key, (a, n, b, m) in (("U", u), ("U_or_RI", ur)):
            c = lp[p][key]
            assert (c["TF_flagged"], c["TF"], c["PF_flagged"], c["PF"]) == (a, n, b, m), (p, key, c)
            assert c["difference_TF_minus_PF"] == round(a / n - b / m, 4)
    rep = _load("wdp_report_t16", "scripts/extension/wdp_report.py")
    assert "CONF-all without Math: U TF 2/6, PF 0/2" in rep.render(json.loads(json.dumps(out)))


def test_t16_project_whose_removal_leaves_one_label_is_skipped():
    an = _load("wdp_analysis_t16", "scripts/extension/wdp_analysis.py")
    rows = [{"project": "A", "y": 1, "level": "U"}, {"project": "B", "y": 0, "level": "U"},
            {"project": "B", "y": 1, "level": "WS"}]
    assert set(an.lopo_levels(rows)) == {"A"}                           # removing B leaves only a PF test
