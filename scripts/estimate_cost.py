"""Cost estimates from configs/providers.json. Nothing here is a result; it sizes the approval request.

    python scripts/estimate_cost.py --scope pilot [--max-instances 150] [--json out.json]
    python scripts/estimate_cost.py --scope full

Two numbers per component:
  expected      pinned provider's rate; input tokens = chars/3.5; output = typical length (assumption)
  conservative  highest rate of ANY listed endpoint; input = chars/2.5; output = the hard max_tokens cap;
                +10% retry allowance (failed attempts that may have been charged)
Pilot input sizes are measured from the real dev-split contexts and prompts; the parts that do not exist
yet (failing test and failure evidence) use a fixed stub whose size is stated below.
OpenRouter's 5.5% credit-purchase fee is applied to the credit top-up, not to API spend.
"""
import argparse
import json
import math
import statistics
from pathlib import Path

from _common import config, load_contexts
from triage.context_builder import build_package
from triage.generation import generation_prompt
from triage.llm import ceiling_rate, load_providers, pinned_rate
from triage.prompts import PromptSet
from triage.spec_inference import spec_context

PROV = load_providers()
M1, M2, G = (config.MODELS[k]["id"] for k in ("M1", "M2", "G"))
EXPECTED_CPT, CONSERVATIVE_CPT, RETRY = 3.5, 2.5, 0.10
STUB_TEST = "@Test\npublic void testCase() {\n" + "    Foo f = new Foo(\"value\", 42);\n" * 20 + "    assertEquals(\"expected\", f.bar());\n}"
STUB_MESSAGE = "expected:<[expected value of moderate length]> but was:<[actual value of moderate length]>"
STUB_FRAMES = [{"method": f"org.example.pkg.Klass.method{i}", "location": f"Klass.java:{100 + i}", "in_test": False}
               for i in range(10)]


def stub_instance(ctx):
    return {"instance_id": "stub", "focal_id": ctx["focal_id"], "focal_class": ctx["focal_class"],
            "focal_method_name": ctx["focal_method_name"],
            "test": {"method_source": STUB_TEST, "imports": ["org.junit.Test", "static org.junit.Assert.*"], "fixtures": ""},
            "failure": {"outcome_type": "assertion_failure", "exception_class": "org.junit.ComparisonFailure",
                        "message": STUB_MESSAGE, "failing_test_line": 22, "failing_test_line_text": "assertEquals(...)",
                        "frames": STUB_FRAMES},
            "sig": ctx["sig"], "doc": ctx["doc"], "impl": ctx["impl_B"],
            "spec": {k: "x" * 300 for k in ("purpose", "preconditions", "postconditions", "exceptions", "edge_cases")}}


def row(name, model, calls, chars_in, out_typ, out_max):
    p, c = pinned_rate(model, PROV), ceiling_rate(model, PROV)
    exp_in, con_in = chars_in / EXPECTED_CPT, chars_in / CONSERVATIVE_CPT
    expected = calls * (exp_in * p["input_per_m"] + out_typ * p["output_per_m"]) / 1e6
    conservative = calls * (con_in * c["input_per_m"] + out_max * c["output_per_m"]) / 1e6 * (1 + RETRY)
    return {"component": name, "model": model, "provider": PROV["models"][model]["pinned_provider"],
            "calls": calls, "input_tokens_per_call_expected": round(exp_in), "input_tokens_per_call_conservative": round(con_in),
            "output_tokens_per_call_expected": out_typ, "output_tokens_cap": out_max,
            "pinned_rate_in_out": [p["input_per_m"], p["output_per_m"]],
            "ceiling_rate_in_out": [c["input_per_m"], c["output_per_m"]],
            "expected_usd": expected, "conservative_usd": conservative}


def pilot(max_instances: int):
    ctxs = list(load_contexts("dev").values())
    prompts = PromptSet.named("v0")
    gen_chars = statistics.mean(len(generation_prompt(c, prompts, 0)) for c in ctxs)
    spec_chars = statistics.mean(len(prompts.render("spec_inferencer", method=c["focal_method_name"],
                                                    context=spec_context(c))) for c in ctxs)
    specp_chars = statistics.mean(len(prompts.render("spec_inferencer_from_body", method=c["focal_method_name"],
                                                     context=spec_context(c, True))) for c in ctxs)
    pkg = statistics.mean(len(build_package(stub_instance(c), "S1").text) for c in ctxs)
    judge = len(prompts.templates["judge"]) + pkg
    adv1 = len(prompts.templates["advocate_p_r1"]) + pkg
    arg = 1100   # chars of one forwarded argument (<= 150 words), assumption
    adv2 = len(prompts.templates["advocate_r2"]) + pkg + 2 * arg
    adj = len(prompts.templates["adjudicator"]) + pkg + 4 * arg
    n, F = max_instances, len(ctxs)
    deb_chars_per_inst = 2 * adv1 + 2 * adv2 + adj
    judge_s2 = judge + 5 * 300  # S2 adds the [Spec] section (<= 400 tokens); 300 chars/field assumed
    rows = [
        row("P0  C4 test generation (39 dev focal methods x 3 generations)", G, F * 3, gen_chars, 2500, 4096),
        row("P1  S2 spec inference (1 per dev focal method, T=0)", M1, F, spec_chars, 300, config.MAX_SPEC_TOKENS + 112),
        row(f"P2  Pilot J1 at S1 (<= {n} instances, 1 rep)", M1, n, judge, 200, config.MAX_OUTPUT_TOKENS),
        row(f"P3  Pilot SC at S1 (5 samples x <= {n})", M1, 5 * n, judge, 200, config.MAX_OUTPUT_TOKENS),
        row(f"P4  Pilot DEB at S1 (5 calls x <= {n})", M1, 5 * n, deb_chars_per_inst / 5, 260, config.MAX_OUTPUT_TOKENS),
        row(f"P5  Prompt dev, J1 prompt: <= 5 rounds x J1 on <= {n}", M1, 5 * n, judge, 200, config.MAX_OUTPUT_TOKENS),
        row(f"P6  Prompt dev, advocates+adjudicator: <= 5 rounds x DEB on <= {n}", M1, 5 * 5 * n,
            deb_chars_per_inst / 5, 260, config.MAX_OUTPUT_TOKENS),
        row(f"P7  Prompt dev, Spec Inferencer: <= 5 rounds x 39 specs", M1, 5 * F, spec_chars, 300,
            config.MAX_SPEC_TOKENS + 112),
        row(f"P8  Prompt dev, Spec Inferencer scoring: <= 5 rounds x J1@S2 on <= {n}", M1, 5 * n, judge_s2, 200,
            config.MAX_OUTPUT_TOKENS),
        row(f"P9  R4 paraphrase validity check: 2 paraphrases x J1 on <= {n}", M1, 2 * n, judge, 200,
            config.MAX_OUTPUT_TOKENS),
    ]
    basis = {"dev_focal_methods": F, "mean_generation_prompt_chars": round(gen_chars),
             "mean_S1_package_chars_with_stub": round(pkg), "stub_test_chars": len(STUB_TEST),
             "forwarded_argument_chars_assumed": arg, "max_judged_instances": n}
    return rows, basis


def full():
    # Phase 2 Table 16 call plan; mean sizes from the Phase 2 illustration until the pilot measures them.
    jin, jout = 3000 * EXPECTED_CPT, 350
    plan = [("E1-E3 factorial (D1-test)", M1, 720 * 3 * 11 * 3), ("SC-T at S1 (k_T=7)", M1, 720 * 7 * 3),
            ("D2 factorial", M1, 300 * 33), ("E4 ablations", M1, 720 * 28), ("E5 D3", M1, 200 * 11 * 3),
            ("E5 paraphrases", M1, 720 * 2), ("Spec inferencer + pilot", M1, 4600), ("E5 M2", M2, 1020 * 11)]
    rows = [row(n, m, c, jin, jout, config.MAX_OUTPUT_TOKENS) for n, m, c in plan]
    rows += [row("Generation D1", G, 234 * 3, 9000, 2500, 4096), row("Generation D2", G, 195 * 2 * 3, 9000, 2500, 4096),
             row("Generation D3", G, 60 * 3, 9000, 2500, 4096)]
    return rows, {"note": "Phase 2 planning sizes; superseded by pilot measurements (gate P4)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["pilot", "full"], default="pilot")
    ap.add_argument("--max-instances", type=int, default=150)
    ap.add_argument("--json")
    a = ap.parse_args()
    rows, basis = pilot(a.max_instances) if a.scope == "pilot" else full()
    print(f"{'component':78s} {'model':32s} {'calls':>6s} {'in exp':>7s} {'out exp':>7s} {'exp $':>8s} {'cons $':>8s}")
    for r in rows:
        print(f"{r['component'][:78]:78s} {r['model']:32s} {r['calls']:6d} {r['input_tokens_per_call_expected']:7d} "
              f"{r['output_tokens_per_call_expected']:7d} {r['expected_usd']:8.2f} {r['conservative_usd']:8.2f}")
    e, c = sum(r["expected_usd"] for r in rows), sum(r["conservative_usd"] for r in rows)
    calls = sum(r["calls"] for r in rows)
    ceiling = math.ceil(c)
    print(f"{'TOTAL':78s} {'':32s} {calls:6d} {'':7s} {'':7s} {e:8.2f} {c:8.2f}")
    print(f"proposed hard API-spend ceiling: ${ceiling}  (credit top-up incl. 5.5% fee: ${ceiling * (1 + PROV['credit_purchase_fee']):.2f})")
    print("basis:", json.dumps(basis))
    if a.json:
        Path(a.json).write_text(json.dumps({"scope": a.scope, "rows": rows, "basis": basis, "expected_usd": e,
                                            "conservative_usd": c, "calls": calls, "proposed_ceiling_usd": ceiling,
                                            "credit_topup_usd": ceiling * (1 + PROV["credit_purchase_fee"])}, indent=2))


if __name__ == "__main__":
    main()
