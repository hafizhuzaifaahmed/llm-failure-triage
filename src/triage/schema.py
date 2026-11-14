"""Output schemas (Table 11) and the single deterministic repair parse (Section 3.10).

No extra LLM call is ever made to repair an output. A record that is still invalid after
`parse_output` is marked INVALID; the scorer maps INVALID to TEST_FAULT in the primary analysis.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Optional

from .config import LABELS, REASON_CATEGORIES

EVIDENCE_ID = re.compile(r"\[?([A-Z][A-Za-z]*\d+)\]?")

JUDGE_SCHEMA = {
    "type": "object",
    "required": ["label", "reason_category", "evidence_ids", "summary", "confidence"],
    "properties": {
        "label": {"enum": list(LABELS)},
        "reason_category": {"enum": list(REASON_CATEGORIES)},
        "evidence_ids": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
        "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
    },
}

ADVOCATE_SCHEMA = {
    "type": "object",
    "required": ["position", "argument", "evidence_ids", "concede"],
    "properties": {
        "position": {"enum": list(LABELS)},
        "argument": {"type": "string"},
        "evidence_ids": {"type": "array", "items": {"type": "string"}},
        "concede": {"type": "boolean"},
    },
}

SPEC_KEYS = ("purpose", "preconditions", "postconditions", "exceptions", "edge_cases")


@dataclass
class Parsed:
    ok: bool
    data: dict = field(default_factory=dict)
    repaired: bool = False
    error: Optional[str] = None


def _extract_json_object(text: str) -> Optional[str]:
    """First balanced {...} block, ignoring braces inside strings."""
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        start = text.find("{", start + 1)
    return None


def _repair_text(text: str) -> str:
    """One deterministic repair pass: strip fences, smart quotes, trailing commas, Python literals."""
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.M)
    t = t.replace("“", '"').replace("”", '"').replace("’", "'")
    t = re.sub(r",\s*([}\]])", r"\1", t)
    t = re.sub(r"\bTrue\b", "true", t)
    t = re.sub(r"\bFalse\b", "false", t)
    t = re.sub(r"\bNone\b", "null", t)
    return t


def _normalise_ids(ids) -> list[str]:
    out = []
    for x in ids if isinstance(ids, list) else [ids]:
        for m in EVIDENCE_ID.finditer(str(x)):
            out.append(m.group(1))
    return list(dict.fromkeys(out))


def _validate_judge(d: dict) -> Optional[str]:
    if d.get("label") not in LABELS:
        return f"bad label {d.get('label')!r}"
    if d.get("reason_category") not in REASON_CATEGORIES:
        d["reason_category"] = "OTHER"  # a free-text category is not a validity failure
    d["evidence_ids"] = _normalise_ids(d.get("evidence_ids", []))
    d["summary"] = " ".join(str(d.get("summary", "")).split()[:60])
    try:
        d["confidence"] = max(0, min(100, int(d.get("confidence", 0))))
    except (TypeError, ValueError):
        d["confidence"] = None
    return None


def _validate_advocate(d: dict) -> Optional[str]:
    if d.get("position") not in LABELS:
        return f"bad position {d.get('position')!r}"
    if not isinstance(d.get("argument"), str) or not d["argument"].strip():
        return "empty argument"
    d["evidence_ids"] = _normalise_ids(d.get("evidence_ids", []))
    c = d.get("concede", False)
    d["concede"] = c if isinstance(c, bool) else str(c).lower() == "true"
    return None


def _validate_spec(d: dict) -> Optional[str]:
    missing = [k for k in SPEC_KEYS if k not in d]
    return f"missing {missing}" if missing else None


_VALIDATORS = {"judge": _validate_judge, "advocate": _validate_advocate, "spec": _validate_spec}


def parse_output(text: str, kind: str) -> Parsed:
    validate = _VALIDATORS[kind]
    last = "no JSON object"
    for attempt, candidate in enumerate((text, _repair_text(text))):
        block = _extract_json_object(candidate or "")
        if block is None:
            continue
        try:
            d = json.loads(block)
        except json.JSONDecodeError:
            continue
        if not isinstance(d, dict):
            continue
        # tolerate lower-case labels, a common surface variation
        for k in ("label", "position"):
            if isinstance(d.get(k), str):
                d[k] = d[k].strip().upper().replace(" ", "_")
        err = validate(d)
        if err is None:
            return Parsed(True, d, repaired=attempt == 1)
        last = err
    return Parsed(False, error=last)
