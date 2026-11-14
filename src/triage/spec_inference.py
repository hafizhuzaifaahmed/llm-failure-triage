"""Spec Inferencer (Phase 2 Section 3.6.1). One call per focal method, M1, temperature 0, cached.

Inputs: [Sig], [Doc] (from B), up to five call sites in B's main code (patch lines already removed by
frame.extract_context) and the names + Javadoc of sibling methods. NOT inputs: focal body, failing test,
failure evidence, developer tests, fixed version. The S2' variant (ablation A5b) adds the buggy body.
"""
from __future__ import annotations

import json

from . import config
from .io_utils import append_jsonl, read_jsonl
from .llm import LLMClient
from .preprocess import cap_tokens, strip_html
from .prompts import PromptSet
from .schema import SPEC_KEYS, parse_output

SPEC_CACHE = config.PROCESSED / "specs"


def model_slug(model_id: str) -> str:
    """Filesystem-safe model name (Windows forbids ':')."""
    return model_id.replace("/", "__").replace(":", "_")


def spec_context(ctx: dict, with_body: bool = False) -> str:
    parts = [f"Method signature: {ctx['sig']['focal_signature']}",
             f"Class: {ctx['sig']['class_declaration']}"]
    if ctx["doc"].get("class_javadoc"):
        parts.append("Class documentation:\n" + strip_html(ctx["doc"]["class_javadoc"])[:2000])
    if ctx["doc"].get("method_javadoc"):
        parts.append("Method documentation:\n" + strip_html(ctx["doc"]["method_javadoc"]))
    sib = [f"- {s['name']}: {strip_html(s['javadoc'])[:200]}" if s["javadoc"] else f"- {s['name']}"
           for s in ctx.get("siblings", [])[:30]]
    if sib:
        parts.append("Other methods of the class:\n" + "\n".join(sib))
    for i, s in enumerate(ctx.get("call_sites", [])[: config.MAX_CALL_SITES], 1):
        parts.append(f"Usage {i}:\n{s['snippet']}")
    if with_body:
        parts.append("Implementation:\n" + ctx["impl_B"])
    return "\n\n".join(parts)


def infer(ctx: dict, client: LLMClient, prompts: PromptSet, model_id: str, with_body: bool = False) -> dict:
    variant = "S2prime" if with_body else "S2"
    cache = SPEC_CACHE / f"{variant}__{model_slug(model_id)}.jsonl"
    for r in read_jsonl(cache):
        if r["focal_id"] == ctx["focal_id"]:
            return r
    name = "spec_inferencer_from_body" if with_body else "spec_inferencer"
    text = prompts.render(name, method=ctx["focal_method_name"], context=spec_context(ctx, with_body))
    res = client.complete(role=name, model_id=model_id, messages=[{"role": "user", "content": text}],
                          temperature=config.SPEC_TEMPERATURE, top_p=1.0, max_tokens=config.MAX_SPEC_TOKENS + 112,
                          tag=f"{variant}|{ctx['focal_id']}")
    p = parse_output(res.text, "spec")
    spec, truncated = None, False
    if p.ok:
        spec = {k: (" ".join(map(str, p.data[k])) if isinstance(p.data[k], list) else str(p.data[k])) for k in SPEC_KEYS}
        joined, truncated = cap_tokens(json.dumps(spec), config.MAX_SPEC_TOKENS)
        if truncated:  # shorten the longest fields proportionally
            for k in SPEC_KEYS:
                spec[k], _ = cap_tokens(spec[k], config.MAX_SPEC_TOKENS // len(SPEC_KEYS))
    rec = {"focal_id": ctx["focal_id"], "variant": variant, "model": model_id, "spec": spec, "valid": p.ok,
           "truncated": truncated, "call_key": res.key, "parse_error": p.error}
    append_jsonl(cache, rec)
    return rec
