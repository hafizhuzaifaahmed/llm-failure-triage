"""Fixed synthetic probe set for feasibility, server-setting measurement and session checks.

Every probe is built from invented Java classes defined here — no Defects4J code, no dev or held-out instance —
so measuring with probes cannot leak data or tune anything (MODEL_SELECTION_PROTOCOL Step 1). The set is
deterministic: same list, same order, same text on every machine.
"""
from __future__ import annotations

import json
import random

from . import config
from .context_builder import build_package
from .io_utils import sha256_text
from .preprocess import cap_words
from .prompts import PromptSet

_CLASSES = [
    ("org.synth.Thermo", "Thermo", "convert", "public double convert(double value, String unit)",
     "Converts a temperature to Kelvin. Unit is one of C, F or K; other units raise IllegalArgumentException."),
    ("org.synth.Ledger", "Ledger", "balance", "public long balance(String account)",
     "Returns the balance of an account in cents; unknown accounts raise NoSuchElementException."),
    ("org.synth.Slugger", "Slugger", "slug", "public String slug(String title)",
     "Lower-cases the title, replaces runs of non-alphanumeric characters with one hyphen, trims hyphens."),
    ("org.synth.Window", "Window", "average", "public double average(int[] values, int k)",
     "Average of the last k values; k larger than the array length uses all values; empty input returns 0."),
]


def _instance(cls_idx: int, size: str, rng: random.Random) -> dict:
    fq, simple, meth, sig, doc = _CLASSES[cls_idx]
    n_methods = {"small": 3, "typical": 25, "large": 900}[size]   # large reaches the package cap
    n_test_lines = {"small": 4, "typical": 18, "large": 60}[size]
    body = "\n".join(f"  {simple} o{i} = new {simple}();\n  assertEquals({rng.randint(1, 999)}, o{i}.{meth}(null));"
                     for i in range(n_test_lines // 2))
    frames = [{"method": f"{fq}.{meth}", "location": f"{simple}.java:{40 + i}", "in_test": False}
              for i in range(min(12, 3 + n_methods // 10))]
    return {
        "instance_id": f"probe-{cls_idx}-{size}", "focal_id": f"PROBE::{fq}::{meth}", "focal_class": fq,
        "focal_method_name": meth,
        "test": {"method_source": f"@Test\npublic void probe() {{\n{body}\n}}", "imports": ["org.junit.Test"],
                 "fixtures": ""},
        "failure": {"outcome_type": rng.choice(["assertion_failure", "exception"]),
                    "exception_class": rng.choice(["java.lang.AssertionError", "java.lang.IllegalArgumentException"]),
                    "message": f"expected:<{rng.randint(1, 99)}> but was:<{rng.randint(100, 199)}>",
                    "failing_test_line": 3, "failing_test_line_text": "assertEquals(...)", "frames": frames},
        "sig": {"focal_signature": sig, "class_declaration": f"public class {simple}",
                "constructors": [f"public {simple}()"],
                "methods": [f"public int helper{i}(String s{i}, int k{i})" for i in range(n_methods)],
                "type_signatures": []},
        "doc": {"method_javadoc": f"/** {doc} */" * (1 if size != "large" else 12), "class_javadoc": ""},
        "spec": {k: f"synthetic {k} for {meth}" for k in ("purpose", "preconditions", "postconditions",
                                                          "exceptions", "edge_cases")},
        "impl": f"{sig} {{ return 0; }}",
    }


def judge_probes(prompts: PromptSet | None = None) -> list[dict]:
    """20 judge-shaped prompts: 6 small, 8 typical, 4 large (near the package cap), 2 adjudicator-shaped."""
    prompts = prompts or PromptSet.named("v0")
    rng = random.Random(20261101)
    out = []
    plan = [("small", 6), ("typical", 8), ("large", 4)]
    k = 0
    for size, n in plan:
        for j in range(n):
            inst = _instance(k % len(_CLASSES), size, rng)
            pkg = build_package(inst, "S2" if j % 2 else "S1")
            out.append({"id": f"J{k:02d}-{size}", "role": "judge", "text": prompts.render("judge", package=pkg.text)})
            k += 1
    for j, size in enumerate(("typical", "large")):   # A1 = the largest prompt the study can produce
        inst = _instance(j, size, rng)
        pkg = build_package(inst, "S1")
        arg = ("Position: PROGRAM_FAULT. Concedes: false. Cited: F2, Doc1.\n" + cap_words("The documented contract "
               "states the behaviour the failure violates. " * 14))      # a full 150-word statement, as forwarded
        blocks = "\n\n".join(f"--- Analyst {n} ---\nFirst statement:\n{arg}\nSecond statement:\n{arg}" for n in "XY")
        out.append({"id": f"A{j}-adjudicator", "role": "adjudicator",
                    "text": prompts.render("adjudicator", package=pkg.text, arguments=blocks)})
    return out


def generator_probes(prompts: PromptSet | None = None, n: int = 20) -> list[dict]:
    prompts = prompts or PromptSet.named("v0")
    out = []
    for i in range(n):
        fq, simple, meth, sig, doc = _CLASSES[i % len(_CLASSES)]
        ctx = {"impl_B": f"/** {doc} */\n{sig} {{\n    // synthetic implementation {i}\n    throw new UnsupportedOperationException();\n}}",
               "focal_class": fq, "focal_method_name": meth, "class_simple": simple, "package": "org.synth",
               "sig": {"focal_signature": sig, "constructors": [f"public {simple}()"], "methods": []}}
        from .generation import generation_prompt
        out.append({"id": f"G{i:02d}", "role": "generator", "text": generation_prompt(ctx, prompts, i % 3)})
    return out


def session_probes() -> list[dict]:
    """The 3 fixed probes run at the start of every session (small, typical, large)."""
    p = judge_probes()
    return [p[0], p[6], p[14]]


def probe_set_hash() -> str:
    return sha256_text(json.dumps([(p["id"], p["text"]) for p in judge_probes() + generator_probes()]))
