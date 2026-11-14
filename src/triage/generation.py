"""Test generation by model G from the BUGGY focal method (Phase 2 C4), following the prompt format of [12].

Three independent generations per focal method at temperature 0.7 (sample_index = generation number).
The assembled class gets a unique name so it never collides with a developer test, and a fixed block
of common imports (JDK collections/IO, JUnit 4) as in [12], to avoid spurious compile failures.
"""
from __future__ import annotations

import re

from . import config, javasrc
from .io_utils import sha256_text
from .llm import LLMClient
from .prompts import PromptSet

COMMON_IMPORTS = [
    "import static org.junit.Assert.*;", "import org.junit.*;", "import java.util.*;", "import java.io.*;",
    "import java.math.*;",
]
_CODE = re.compile(r"```(?:java)?\s*\n(.*?)```", re.S)


def test_class_name(ctx: dict, gen: int) -> str:
    return f"{ctx['class_simple']}_{ctx['focal_method_name']}_TriageGen{gen}Test"


def generation_prompt(ctx: dict, prompts: PromptSet, gen: int) -> str:
    sig = ctx["sig"]["focal_signature"]
    params = sig[sig.index("(") + 1: sig.rindex(")")] if "(" in sig else ""
    names = [p.strip().split()[-1] for p in params.split(",") if p.strip()]
    types = [" ".join(p.strip().split()[:-1]).replace("final ", "") for p in params.split(",") if p.strip()]
    ret = sig[: sig.index("(")].split()[-2] if "(" in sig and len(sig[: sig.index("(")].split()) > 1 else ""
    return prompts.render(
        "generator", focal_method=ctx["impl_B"], full_signature=f"{ctx['focal_class']}#{sig}",
        method_name=ctx["focal_method_name"], param_names=", ".join(names) or "(none)",
        param_types=", ".join(types) or "(none)", return_type=ret or "(constructor)",
        class_name=ctx["focal_class"], constructors="\n".join(ctx["sig"]["constructors"]) or "(none)",
        other_methods="\n".join(ctx["sig"]["methods"][:60]) or "(none)",
        test_class=test_class_name(ctx, gen), package=ctx["package"])


def assemble(raw_text: str, ctx: dict, gen: int) -> dict | None:
    """Extract the Java test class from the model output and normalise package, class name and imports."""
    blocks = _CODE.findall(raw_text) or ([raw_text] if "@Test" in raw_text else [])
    code = max(blocks, key=lambda b: b.count("@Test"), default="")
    if "@Test" not in code:
        return None
    name = test_class_name(ctx, gen)
    found = javasrc.top_level_class_name(code)
    if found:
        code = re.sub(rf"\b{re.escape(found)}\b", name, code)
    else:
        code = f"public class {name} {{\n{code}\n}}"
    code = re.sub(r"^\s*package\s+[\w.]+\s*;\s*", "", code, flags=re.M)
    existing = set(javasrc.import_lines(code))
    focal_imports = [f"import {i};" for i in ctx.get("imports", []) if not i.startswith("static ")]
    extra = [i for i in COMMON_IMPORTS + focal_imports if i not in existing]
    body = re.sub(r"^\s*import\s+[^;]+;\s*$", "", code, flags=re.M).strip()
    header = (f"package {ctx['package']};\n\n" if ctx["package"] else "") + "\n".join(sorted(existing | set(extra)))
    src = f"{header}\n\n{body}\n"
    return {"package": ctx["package"], "class_name": name, "source": src,
            "n_tests": len(re.findall(r"@Test\b", src))}


def generate(ctx: dict, client: LLMClient, prompts: PromptSet, model_id: str, gen: int) -> dict:
    prompt = generation_prompt(ctx, prompts, gen)
    res = client.complete(role="generator", model_id=model_id, messages=[{"role": "user", "content": prompt}],
                          sample_index=gen, temperature=config.GENERATION_TEMPERATURE, top_p=1.0,
                          max_tokens=4096, json_mode=False, tag=f"G|{ctx['focal_id']}",
                          meta={"focal_id": ctx["focal_id"]})
    cand = assemble(res.text, ctx, gen)
    cid = sha256_text(f"{ctx['focal_id']}|{gen}|{res.key}")[:20]
    return {"candidate_id": cid, "focal_id": ctx["focal_id"], "generation": gen, "call_key": res.key,
            "model_returned": res.model_returned, "assembled": cand is not None, **(cand or {})}
