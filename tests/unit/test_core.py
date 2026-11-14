"""Unit tests for schema parsing, preprocessing, labelling, context building, arms, metrics and stats.

All LLM behaviour here comes from MockBackend: these tests validate the software, not the research.
"""
import json
import math
import random

import numpy as np
import pytest

from triage import arms, config, context_builder, labeling, metrics, preprocess, schema, stats
from triage.llm import LLMClient, MockBackend
from triage.prompts import PromptSet


# ---------------------------------------------------------------- schema
def test_parse_valid_judge():
    p = schema.parse_output('{"label":"PROGRAM_FAULT","reason_category":"SPEC_VIOLATED_BY_PROGRAM",'
                            '"evidence_ids":["F2","[Doc1]"],"summary":"x","confidence":80}', "judge")
    assert p.ok and not p.repaired and p.data["evidence_ids"] == ["F2", "Doc1"]


def test_parse_repairs_fence_and_trailing_comma():
    p = schema.parse_output('```json\n{"label":"test_fault","reason_category":"OTHER","evidence_ids":["T3"],'
                            '"summary":"s","confidence":50,}\n```', "judge")
    assert p.ok and p.data["label"] == "TEST_FAULT"


def test_parse_invalid_label():
    assert not schema.parse_output('{"label":"MAYBE","reason_category":"OTHER","evidence_ids":[],'
                                   '"summary":"","confidence":1}', "judge").ok
    assert not schema.parse_output("no json here", "judge").ok


def test_summary_capped_at_60_words():
    p = schema.parse_output(json.dumps({"label": "TEST_FAULT", "reason_category": "OTHER", "evidence_ids": [],
                                        "summary": "w " * 100, "confidence": 3}), "judge")
    assert len(p.data["summary"].split()) == 60


# ---------------------------------------------------------------- preprocess
TRACE = """java.lang.NumberFormatException: For input string: "80000000" at 2024-01-01T10:00:00Z
\tat java.lang.NumberFormatException.forInputString(NumberFormatException.java:65)
\tat java.lang.Integer.parseInt(Integer.java:583)
\tat org.apache.commons.lang3.math.NumberUtils.createInteger(NumberUtils.java:684)
\tat org.apache.commons.lang3.math.NumberUtils.createNumber(NumberUtils.java:474)
\tat org.apache.commons.lang3.math.GenTest.t1(GenTest.java:12)
\tat sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
\tat org.junit.runners.model.FrameworkMethod$1.runReflectiveCall(FrameworkMethod.java:50)
"""


def test_stack_normalisation_keeps_project_frames_and_scrubs():
    n = preprocess.normalise_stack_trace(TRACE, ["org.apache.commons.lang3"], "org.apache.commons.lang3.math.GenTest")
    methods = [f["method"] for f in n["frames"]]
    assert methods == ["org.apache.commons.lang3.math.NumberUtils.createInteger",
                       "org.apache.commons.lang3.math.NumberUtils.createNumber",
                       "org.apache.commons.lang3.math.GenTest.t1"]
    assert "<TIMESTAMP>" in n["rendered"] and "framework frames omitted" in n["rendered"]
    assert preprocess.deepest_project_frame(n["frames"], "org.apache.commons.lang3.math.NumberUtils") == "focal"


def test_normalise_body_ignores_comments_and_names():
    a = "@Test public void a() { // x\n assertEquals(1, f()); }"
    b = "@Test public void b() {\n /* y */ assertEquals(1,   f()); }"
    assert preprocess.normalise_test_body(a) == preprocess.normalise_test_body(b)


# ---------------------------------------------------------------- labelling
def _runs(outcome, exc=None, line=None, n=3):
    return [{"outcome": outcome, "exception": exc or "", "failing_test_line": line} for _ in range(n)]


@pytest.mark.parametrize("rb,rf,expected", [
    (_runs("exception", "java.lang.NumberFormatException", 12), _runs("pass"), "PF"),
    (_runs("assertion_failure", "java.lang.AssertionError", 9), _runs("assertion_failure", "java.lang.AssertionError", 9), "TF"),
    (_runs("exception", "java.lang.NumberFormatException", 12), _runs("assertion_failure", "java.lang.AssertionError", 13), "AMB"),
    (_runs("pass"), _runs("pass"), "PASS"),
    (_runs("pass"), _runs("exception", "java.lang.NullPointerException", 4), "MISGUIDED"),
    (_runs("pass")[:2] + _runs("assertion_failure", "java.lang.AssertionError", 3, 1), _runs("pass"), "FLAKY"),
    (_runs("timeout"), _runs("pass"), "TIMEOUT"),
    (_runs("harness_error"), _runs("pass"), "ENV"),
])
def test_label_rules(rb, rf, expected):
    assert labeling.label({"compile_b": True, "compile_f": True, "runs_b": rb, "runs_f": rf})["label"] == expected


def test_label_nc_and_same_exception_different_line_is_amb():
    assert labeling.label({"compile_b": True, "compile_f": False})["label"] == "NC"
    rb = _runs("exception", "java.lang.IllegalStateException", 10)
    rf = _runs("exception", "java.lang.IllegalStateException", 11)
    assert labeling.label({"compile_b": True, "compile_f": True, "runs_b": rb, "runs_f": rf})["label"] == "AMB"


# ---------------------------------------------------------------- context builder
def make_instance(**over):
    inst = {
        "instance_id": "i1", "bug_id": "Lang_1", "label": "PF", "outcomes_F": ["pass"],
        "focal_class": "org.x.NumberUtils", "focal_method_name": "createNumber",
        "test": {"method_source": "@Test\npublic void t1() {\n  assertEquals(5L, NumberUtils.createNumber(\"0x80000000\"));\n}",
                 "imports": ["org.junit.Test"], "fixtures": ""},
        "failure": {"outcome_type": "exception", "exception_class": "java.lang.NumberFormatException",
                    "message": "For input string: \"80000000\"", "failing_test_line": 3,
                    "failing_test_line_text": "assertEquals(5L, NumberUtils.createNumber(\"0x80000000\"));",
                    "frames": [{"method": "org.x.NumberUtils.createNumber", "location": "NumberUtils.java:474", "in_test": False}]},
        "sig": {"focal_signature": "public static Number createNumber(String str) throws NumberFormatException",
                "class_declaration": "public class NumberUtils", "constructors": ["public NumberUtils()"],
                "methods": [f"public static int m{i}()" for i in range(3)], "type_signatures": []},
        "doc": {"method_javadoc": "/** Turns a string into a Number. <p>Hex is supported.</p> */", "class_javadoc": ""},
        "spec": {k: f"{k} text" for k in schema.SPEC_KEYS},
        "impl": "{ return Integer.valueOf(str); }",
    }
    inst.update(over)
    return inst


def test_levels_are_nested_and_labels_never_leak():
    inst = make_instance()
    p0, p1, p2 = (context_builder.build_package(inst, lv) for lv in ("S0", "S1", "S2"))
    assert "[Doc1]" not in p0.text and "[Doc1]" in p1.text and "[Spec1]" in p2.text
    assert "[Spec1]" not in p1.text
    for p in (p0, p1, p2):
        assert "Lang_1" not in p.text and "outcomes_F" not in p.text and "Impl1" not in p.text
        assert p.text.startswith("=== [T] Failing test ===")
    # test, failure and interface sections are byte-identical across levels
    head = lambda t: t.split("=== [Doc]")[0].rstrip()
    assert head(p0.text) == head(p1.text) == head(p2.text)


def test_ablation_variants():
    inst = make_instance()
    a4 = context_builder.build_package(inst, "S1", include_failure=False)
    a5 = context_builder.build_package(inst, "S1", include_impl=True)
    assert "[F1]" not in a4.text and a4.variant == "noF"
    assert "[Impl1]" in a5.text and a5.variant == "impl"


def test_truncation_drops_interface_first():
    inst = make_instance()
    inst["sig"]["methods"] = [f"public static int method{i}(String a, String b, String c)" for i in range(4000)]
    p = context_builder.build_package(inst, "S0")
    assert p.truncated["interface_items_dropped"] > 0 and p.approx_tokens <= config.MAX_PACKAGE_TOKENS
    assert "[T3]" in p.text and "[F2]" in p.text and "[Sig1]" in p.text


def test_leakage_check_flags_bug_ids_and_forbidden():
    guard = {"bug_ids": ["Lang_1"], "code_lines": ["return Integer.valueOf(str)"]}
    assert context_builder.leakage_check("see Lang-1b and the buggy version here", guard)
    assert context_builder.leakage_check("x = return Integer.valueOf(str);", guard)
    assert context_builder.leakage_check("clean text", guard) == []


def test_judge_view_strips_labels():
    v = context_builder.judge_view(make_instance())
    assert "label" not in v and "bug_id" not in v and "outcomes_F" not in v


# ---------------------------------------------------------------- arms with the mock backend
PROMPTS = PromptSet(config.PROMPTS / "dev" / "v0")


def responder(model, messages):
    text = messages[0]["content"]
    if "Analyst P" in text or "Analyst T" in text or "You are an analyst" in text:
        pos = "PROGRAM_FAULT" if "Analyst P" in text else "TEST_FAULT"
        return json.dumps({"position": pos, "argument": "because [F2]", "evidence_ids": ["F2"], "concede": False})
    if "adjudicator" in text:
        return json.dumps({"label": "PROGRAM_FAULT", "reason_category": "SPEC_VIOLATED_BY_PROGRAM",
                           "evidence_ids": ["F2", "Z99"], "summary": "s", "confidence": 70})
    # judge: alternate deterministic answers by a hash of the full prompt and sample counter
    h = random.Random(len(text) + responder.counter).random()
    responder.counter += 1
    if h < 0.1:
        return "garbage"
    return json.dumps({"label": "PROGRAM_FAULT" if h < 0.6 else "TEST_FAULT", "reason_category": "OTHER",
                       "evidence_ids": ["T3"], "summary": "s", "confidence": 60})


responder.counter = 0


@pytest.fixture()
def client(tmp_path):
    return LLMClient(MockBackend(responder), log_dir=tmp_path)


def test_policy_and_rule_arms():
    assert arms.policy_arm("i", "DA")["label_raw"] == arms.TF
    assert arms.policy_arm("i", "KA")["label_raw"] == arms.PF
    r = arms.r0_arm(make_instance())
    assert r["label_raw"] == arms.PF and r["features"]["deepest_project_frame"] == "focal"
    inst = make_instance()
    inst["failure"]["outcome_type"] = "assertion_failure"
    assert arms.r0_arm(inst)["label_raw"] == arms.TF


def test_sc_uses_five_calls_and_vote_share(client):
    pkg = context_builder.build_package(make_instance(), "S1")
    r = arms.sc_arm("i1", pkg, client, PROMPTS, "m", k=5)
    assert r["cost"]["calls"] == 5 and len(r["votes"]) == 5
    assert r["agreement"]["vote_share_pf"] == r["agreement"]["n_pf"] / 5


def test_aggregation_ties_and_thresholds():
    PFv, TFv, INV = arms.PF, arms.TF, arms.INVALID
    assert arms.aggregate_votes([PFv, PFv, TFv, TFv, INV], 5)["label_raw"] == TFv  # 2-2 tie -> TF
    assert arms.aggregate_votes([PFv, PFv, TFv, TFv, TFv], 5, threshold=2 / 5)["label_raw"] == PFv
    assert arms.aggregate_votes([PFv, PFv, PFv, TFv, TFv], 5, threshold=4 / 5)["label_raw"] == TFv
    assert arms.aggregate_votes([INV] * 5, 5)["label_raw"] == INV


def test_debate_five_calls_and_isolation(client):
    pkg = context_builder.build_package(make_instance(), "S1")
    r = arms.deb_arm("i1", pkg, client, PROMPTS, "m", replicate=0)
    assert r["cost"]["calls"] == 5 and r["label_raw"] == arms.PF
    assert r["invalid_evidence_ids"] == ["Z99"] and r["evidence_ids"] == ["F2"]
    log = [json.loads(l) for f in client.log_dir.glob("*.jsonl") if not f.name.startswith("_") for l in open(f)]
    r1 = [x for x in log if x["role"] in ("advocate_p_r1", "advocate_t_r1")]
    assert len(r1) == 2 and all("opposing" not in x["messages"][0]["content"] for x in r1)
    adj = next(x for x in log if x["role"] == "adjudicator")["messages"][0]["content"]
    assert "Analyst X" in adj and "Analyst Y" in adj and "Analyst P" not in adj and "Analyst T" not in adj


def test_ablation_a1_hides_opponent(client):
    pkg = context_builder.build_package(make_instance(), "S1")
    arms.deb_arm("i2", pkg, client, PROMPTS, "m", variant="A1")
    log = [json.loads(l) for f in client.log_dir.glob("*.jsonl") if not f.name.startswith("_") for l in open(f)]
    r2 = [x for x in log if x["role"] in ("r2_a", "r2_b") and x["tag"].startswith("A1")]
    assert len(r2) == 2 and all("opposing analyst" not in x["messages"][0]["content"] for x in r2)


def test_cache_prevents_duplicate_calls(client):
    pkg = context_builder.build_package(make_instance(), "S0")
    a = arms.j1_arm("i3", pkg, client, PROMPTS, "m")
    b = arms.j1_arm("i3", pkg, client, PROMPTS, "m")
    assert b["cost"]["cached_calls"] == 1 and a["label_raw"] == b["label_raw"]


# ---------------------------------------------------------------- metrics
def test_metrics_known_values():
    y = ["PROGRAM_FAULT"] * 4 + ["TEST_FAULT"] * 6
    p = ["PROGRAM_FAULT"] * 3 + ["TEST_FAULT"] + ["PROGRAM_FAULT"] * 2 + ["TEST_FAULT"] * 4
    m = metrics.classification_metrics(y, p)
    assert m["TP"] == 3 and m["FP"] == 2 and m["FN"] == 1 and m["TN"] == 4
    assert m["precision"] == pytest.approx(0.6) and m["recall"] == pytest.approx(0.75)
    assert m["f1"] == pytest.approx(2 * 0.6 * 0.75 / 1.35)
    assert m["mcc"] == pytest.approx((3 * 4 - 2 * 1) / math.sqrt(5 * 4 * 6 * 5))


def test_keep_all_f1_matches_formula():
    prev = 1 / 3
    y = ["PROGRAM_FAULT"] * 10 + ["TEST_FAULT"] * 20
    m = metrics.classification_metrics(y, ["PROGRAM_FAULT"] * 30)
    assert m["f1"] == pytest.approx(2 * prev / (1 + prev)) and m["recall"] == 1


def test_prevalence_adjusted_precision_and_retention():
    y = ["PROGRAM_FAULT", "TEST_FAULT", "TEST_FAULT"]
    p = ["PROGRAM_FAULT", "PROGRAM_FAULT", "TEST_FAULT"]
    assert metrics.prevalence_adjusted_precision(y, p, [1, 3, 3]) == pytest.approx(1 / 4)
    assert metrics.bug_level_retention(["b1", "b1", "b2"], ["PROGRAM_FAULT", "PROGRAM_FAULT", "PROGRAM_FAULT"],
                                       ["TEST_FAULT", "PROGRAM_FAULT", "TEST_FAULT"]) == 0.5


def test_average_precision_perfect_ranking():
    assert metrics.average_precision(["PROGRAM_FAULT", "TEST_FAULT"], [0.8, 0.2]) == pytest.approx(1.0)


# ---------------------------------------------------------------- stats
def test_holm_matches_reference():
    assert stats.holm([0.01, 0.04, 0.03, 0.005]) == pytest.approx([0.03, 0.06, 0.06, 0.02])


def test_bootstrap_identical_conditions_give_zero_delta():
    rng = np.random.default_rng(0)
    T = rng.integers(0, 4, size=(50, 3, 4)).astype(float)
    W = stats.bootstrap_weights(50, B=500)
    c = stats.paired_contrast("same", T, T.copy(), "f1", W)
    assert c.delta == 0 and c.ci95 == (0.0, 0.0) and c.p == 1.0


def test_bootstrap_detects_large_difference_and_decision_rule():
    n = 80
    Ta = np.zeros((n, 1, 4)); Tb = np.zeros((n, 1, 4))
    Ta[:, 0] = [3, 1, 1, 5]   # strong arm
    Tb[:, 0] = [1, 3, 3, 3]   # weak arm
    W = stats.bootstrap_weights(n, B=1000)
    c = stats.paired_contrast("ab", Ta, Tb, "f1", W)
    c.p_holm = c.p
    assert c.delta > 0.3 and c.p < 0.01 and stats.decide(c) == "effect demonstrated"


def test_point_estimate_matches_metrics():
    T = np.array([[[3, 2, 1, 4]]], dtype=float)
    assert stats.point_estimate(T, "f1") == pytest.approx(6 / 9)


def test_mcnemar_and_kappa():
    r = stats.mcnemar_exact([True] * 10 + [False] * 2, [False] * 10 + [True] * 2)
    assert r["a_only"] == 10 and r["b_only"] == 2 and r["p"] < 0.05
    assert stats.cohen_kappa(["PF", "TF", "PF", "TF"], ["PF", "TF", "PF", "TF"]) == 1.0
