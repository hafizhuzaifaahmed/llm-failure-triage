"""Unit tests for the counterfactual-probe prototype (D-134): mutants, ledger classes, policy rules, boundary."""
import re
from pathlib import Path

import pytest

from triage_ext import ledger, mutate, policy

ROOT = Path(__file__).resolve().parents[2]
METHOD = """public int clamp(int v, int lo) {
    // keep "a < b" in a comment
    String s = "x <= y";
    if (v < lo && lo != 0) {
        count++;
        log(v);
        return lo + 1;
    }
    for (int i = 0; i < 3; i++) { v -= i; }
    return v;
}"""


def ops(ms):
    return {m.operator for m in ms}


def test_operators_present_and_signature_untouched():
    ms = mutate.all_mutants(METHOD)
    assert ops(ms) == {"ROR", "AOR", "COR", "LVR", "NEG", "STD"}
    body = METHOD.index("{")
    assert all(m.start > body for m in ms)                      # nothing before the opening brace is mutated


def test_strings_and_comments_are_never_mutated():
    for m in mutate.all_mutants(METHOD):
        out = m.apply(METHOD)
        assert '// keep "a < b" in a comment' in out
        assert '"x <= y"' in out or m.operator == "STD"          # only deleting the whole statement removes it


def test_each_mutant_is_one_local_change():
    for m in mutate.all_mutants(METHOD):
        out = m.apply(METHOD)
        assert out != METHOD
        assert out[:m.start] == METHOD[:m.start] and out.endswith(METHOD[m.end:])
        assert METHOD[m.start:m.end] == m.original


def test_ror_and_lvr_replacements():
    ms = mutate.all_mutants(METHOD)
    assert {m.replacement for m in ms if m.operator == "ROR" and m.original == "<"} == {"<=", ">"}
    assert {m.replacement for m in ms if m.operator == "LVR" and m.original == "3"} == {"4", "2"}
    assert {m.replacement for m in ms if m.operator == "LVR" and m.original == "0"} == {"1"}


def test_increment_and_compound_tokens_are_not_split():
    ms = mutate.all_mutants(METHOD)
    assert not any(m.original == "+" and METHOD[m.start - 1:m.end + 1] in ("++", "+++") for m in ms)
    assert any(m.original == "-=" and m.replacement == "+=" for m in ms)


def test_statement_deletion_skips_control_transfers_and_for_header():
    std = [m for m in mutate.all_mutants(METHOD) if m.operator == "STD"]
    deleted = {m.original.strip() for m in std}
    assert "count++" in deleted and "log(v)" in deleted
    assert not any(d.startswith("return") for d in deleted)
    assert not any("i < 3" in d and d.startswith("int i") for d in deleted)   # the ';' inside for(...) is not a boundary


def test_negation_wraps_the_whole_condition():
    neg = [m for m in mutate.all_mutants(METHOD) if m.operator == "NEG"]
    assert len(neg) == 1 and neg[0].replacement == "!(v < lo && lo != 0)"


def test_sampling_is_deterministic_and_capped():
    big = "void f() {\n" + "\n".join(f"  a = a + {i};" for i in range(200)) + "\n}"
    a, n = mutate.sample_mutants(big, "X::f")
    b, _ = mutate.sample_mutants(big, "X::f")
    c, _ = mutate.sample_mutants(big, "Y::f")
    assert n > mutate.MAX_MUTANTS and len(a) == mutate.MAX_MUTANTS
    assert [m.mid for m in a] == [m.mid for m in b] and [m.mid for m in a] != [m.mid for m in c]
    order = {m.mid: k for k, m in enumerate(mutate.all_mutants(big))}
    assert [order[m.mid] for m in a] == sorted(order[m.mid] for m in a)      # a subsequence of the full list


BASE = {"outcome": "assertion_failure", "exception": "java.lang.AssertionError", "failing_test_line": 41,
        "message": "expected:<1> but was:<2>"}


@pytest.mark.parametrize("run,rerun,want", [
    ({"outcome": "pass"}, {"outcome": "pass"}, ledger.FLIP),
    ({"outcome": "pass"}, {"outcome": "assertion_failure"}, ledger.ERR),      # a pass that does not repeat
    ({"outcome": "pass"}, None, ledger.ERR),
    ({"outcome": "timeout"}, None, ledger.ERR),
    ({"outcome": "harness_error"}, None, ledger.ERR),
    (dict(BASE), None, ledger.SAME),
    ({**BASE, "message": "expected:<1> but was:<3>"}, None, ledger.SHIFT),    # same signature, other value
    ({**BASE, "failing_test_line": 40}, None, ledger.SHIFT),
    ({**BASE, "outcome": "exception", "exception": "java.lang.NullPointerException"}, None, ledger.SHIFT),
])
def test_classify(run, rerun, want):
    assert ledger.classify(BASE, run, rerun) == want


def test_object_hashes_do_not_count_as_a_shift():
    a = {**BASE, "message": "expected:<Foo@1a2b3c> but was:<Foo@99ffee>"}
    b = {**BASE, "message": "expected:<Foo@777aaa> but was:<Foo@123456>"}
    assert ledger.classify(a, b) == ledger.SAME


def _m(cls, rc=None):
    return {"class": cls, "rc": rc}


def test_summary_flags():
    s = ledger.summarise([_m(ledger.SAME)] * 12)
    assert s["decoupled"] and not s["coupled"] and not s["rcf"]
    s = ledger.summarise([_m(ledger.SAME)] * 9)
    assert not s["decoupled"]                                    # too few mutants: flag undefined, not true
    s = ledger.summarise([_m(ledger.SAME)] * 11 + [_m(ledger.SHIFT)])
    assert s["coupled"] and not s["decoupled"]
    s = ledger.summarise([_m(ledger.SAME)] * 11 + [_m(ledger.FLIP, rc=False)])
    assert s["flip"] and not s["rcf"] and s["flip_without_rcf"]
    s = ledger.summarise([_m(ledger.SAME)] * 11 + [_m(ledger.FLIP, rc=False), _m(ledger.FLIP, rc=True)])
    assert s["rcf"] and not s["flip_without_rcf"] and s["n_rcf"] == 1
    s = ledger.summarise([_m(ledger.ERR)] * 12)
    assert s["flip_fraction"] is None and s["decoupled"]         # all timeouts: nothing changed the failure


def test_policy_rules():
    PF, TF = policy.PF, policy.TF
    rcf = {"rcf": True, "decoupled": False, "excluded": None}
    dec = {"rcf": False, "decoupled": True, "excluded": None}
    none = {"rcf": False, "decoupled": False, "excluded": None}
    excl = {"excluded": "baseline_not_reproduced"}
    assert policy.certified_keep(TF, rcf) == PF and policy.certified_keep(TF, none) == TF
    assert policy.certified_keep(TF, dec) == TF                  # CK never discards
    assert policy.decoupled_discard(PF, dec) == TF and policy.decoupled_discard(PF, none) == PF
    assert policy.decoupled_discard(PF, rcf) == PF               # CD never keeps
    assert policy.combined(TF, rcf) == PF and policy.combined(PF, dec) == TF and policy.combined(PF, none) == PF
    for rule in policy.RULES.values():                           # no usable ledger: the base rule stands
        assert rule(PF, excl) == PF and rule(TF, excl) == TF and rule(PF, None) == PF and rule(TF, None) == TF


def test_engine_has_no_path_to_the_other_version_or_to_labels():
    """Prediction-time boundary: the probe engine and its entry script never name fixed-side or label artefacts."""
    forbidden = [r"runs_f", r"compile_f", r"meta_f", r"ground_truth", r"labels_D", r"classes\.modified",
                 r"tests\.trigger", r"fixed_bodies", r"sigma_F", r"guard_D"]
    for rel in ("src/triage_ext/probe.py", "src/triage_ext/mutate.py", "src/triage_ext/ledger.py",
                "src/triage_ext/policy.py", "scripts/extension/run_probes.py"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        for pat in forbidden:
            assert not re.search(pat, text), f"{rel} mentions {pat}"
    assert 'endswith("/b")' in (ROOT / "src/triage_ext/probe.py").read_text(encoding="utf-8")


CLASS = """package p;
public class Box {
    private int n;
    /** focal */
    public int size() {
        return clamp(n) + helper();
    }
    private int clamp(int v) { return v < 0 ? 0 : deep(v); }
    private int clamp(long v) { return 1; }
    private int helper() { if (n > 3) { return 1; } return 0; }
    private int deep(int v) { return v + 1; }
    private int deeper() { return far(); }
    private int far() { return 9; }
    public int unrelated() { return n * 2; }
}
"""


def test_callee_regions_are_same_class_callees_to_depth_two():
    from triage_ext import probe
    s = CLASS.index("public int size()")
    e = CLASS.index("}", s) + 1
    regs = probe.callee_regions(CLASS, "p.Box", (s, e))
    assert [(r["name"], r["tier"]) for r in regs] == [("clamp", 1), ("clamp", 1), ("helper", 1), ("deep", 2)]
    assert all(r["end"] <= s or r["start"] >= e for r in regs)          # never overlaps the focal method
    assert probe.callee_regions(CLASS, "p.Missing", (s, e)) == []       # unknown class: focal-only scope
