"""Deterministic pseudo-random responses for --mock runs. Outputs are meaningless by construction and are
written only under results/smoke/; they validate plumbing, never research questions."""
from __future__ import annotations

import hashlib
import json


def _u(text: str, salt: str) -> float:
    return int(hashlib.sha256((salt + text).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def responder(model: str, messages: list[dict]) -> str:
    text = messages[0]["content"]
    u = _u(text, model)
    if "describe the intended behaviour" in text:
        return json.dumps({"purpose": "mock", "preconditions": "mock", "postconditions": "mock",
                           "exceptions": "mock", "edge_cases": "mock"})
    if "unit tests in java" in text:
        return "```java\npublic class X {\n  @org.junit.Test public void t() { org.junit.Assert.assertTrue(true); }\n}\n```"
    if '"position"' in text and "adjudicator" not in text:
        pos = "PROGRAM_FAULT" if ("Analyst P" in text or (u < 0.5 and "Analyst T" not in text)) else "TEST_FAULT"
        return json.dumps({"position": pos, "argument": "mock argument citing [F2]", "evidence_ids": ["F2"],
                           "concede": u < 0.1})
    if u < 0.01:
        return "not json"
    return json.dumps({"label": "PROGRAM_FAULT" if u < 0.45 else "TEST_FAULT", "reason_category": "OTHER",
                       "evidence_ids": ["T1", "F2"], "summary": "mock", "confidence": int(u * 100)})
