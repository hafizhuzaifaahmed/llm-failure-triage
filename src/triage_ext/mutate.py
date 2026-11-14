"""First-order mutants of a Java method body (D-134). Pure text, deterministic, stdlib only.

The operator set is fixed: ROR, AOR, COR, LVR (integer and boolean literals), NEG (if-condition negation) and STD
(single-statement deletion). Mutants are generated without parsing types, so some will not compile; the probe engine
discards those. Nothing here reads a label, a fixed version or a test.
"""
from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass

MAX_MUTANTS = 80

_OPS = [">>>=", "<<=", ">>=", ">>>", "->", "::", "++", "--", "&&", "||", "==", "!=", "<=", ">=", "+=", "-=", "*=",
        "/=", "%=", "&=", "|=", "^=", "<<", ">>"]
_TOKEN = re.compile(
    r"(?P<comment>//[^\n]*|/\*.*?\*/)"
    r"|(?P<str>\"(?:\\.|[^\"\\\n])*\")"
    r"|(?P<chr>'(?:\\.|[^'\\\n])+')"
    r"|(?P<num>\b(?:0[xX][0-9a-fA-F_]+[lL]?|\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?[fFdDlL]?)\b)"
    r"|(?P<id>[A-Za-z_$][\w$]*)"
    r"|(?P<op>" + "|".join(re.escape(o) for o in _OPS) + r"|[-+*/%<>=!&|^~?:;,.(){}\[\]@])"
    r"|(?P<ws>\s+)"
    r"|(?P<other>.)", re.S)

ROR = {"<": ["<=", ">"], "<=": ["<", ">="], ">": [">=", "<"], ">=": [">", "<="], "==": ["!="], "!=": ["=="]}
AOR = {"+": ["-"], "-": ["+"], "*": ["/"], "/": ["*"], "%": ["*"], "+=": ["-="], "-=": ["+="]}
COR = {"&&": ["||"], "||": ["&&"]}
_NO_DELETE = {"return", "throw", "break", "continue", "case", "default", "else", "do", "try", "finally", "catch"}


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class Mutant:
    mid: str          # stable id: operator, offset and replacement
    operator: str
    start: int        # offsets into the method text
    end: int
    original: str
    replacement: str
    line: int         # 1-based line inside the method text

    def apply(self, text: str) -> str:
        return text[:self.start] + self.replacement + text[self.end:]


def tokenize(text: str) -> list[Token]:
    return [Token(m.lastgroup, m.group(), m.start(), m.end()) for m in _TOKEN.finditer(text)]


def _body_start(text: str) -> int:
    """Offset just after the method's opening brace; mutants never touch the signature."""
    depth = 0
    for t in tokenize(text):
        if t.kind != "op":
            continue
        if t.text == "(":
            depth += 1
        elif t.text == ")":
            depth -= 1
        elif t.text == "{" and depth == 0:
            return t.end
    return len(text)


def _mk(op: str, text: str, start: int, end: int, rep: str) -> Mutant:
    return Mutant(f"{op}:{start}:{hashlib.sha1(rep.encode()).hexdigest()[:6]}", op, start, end, text[start:end], rep,
                  text.count("\n", 0, start) + 1)


def _int_replacements(lit: str) -> list[str]:
    core = lit.rstrip("lL")
    suffix = lit[len(core):]
    if not re.fullmatch(r"\d+", core):
        return []
    n = int(core)
    reps = [1] if n == 0 else ([0] if n == 1 else [n + 1, n - 1])
    return [f"{r}{suffix}" for r in reps]


def all_mutants(method_text: str) -> list[Mutant]:
    """Every first-order mutant of the body, in source order. No cap, no sampling."""
    lo = _body_start(method_text)
    toks = [t for t in tokenize(method_text) if t.kind not in ("ws", "comment")]
    out: list[Mutant] = []
    depth = 0                                   # parenthesis depth, to skip the ';' inside for(...)
    stmt_start = None                           # offset of the first token of the current statement
    for k, t in enumerate(toks):
        if t.start < lo:
            continue
        if stmt_start is None and not (t.kind == "op" and t.text in "{};"):
            stmt_start = t.start
        if t.kind == "op":
            if t.text == "(":
                depth += 1
            elif t.text == ")":
                depth -= 1
            for name, table in (("ROR", ROR), ("AOR", AOR), ("COR", COR)):
                for rep in table.get(t.text, []):
                    out.append(_mk(name, method_text, t.start, t.end, rep))
            if t.text in "{}" and depth == 0:
                stmt_start = None
            elif t.text == ";" and depth == 0:
                if stmt_start is not None:
                    first = method_text[stmt_start:t.start].split(None, 1)[0] if method_text[stmt_start:t.start].strip() else ""
                    head = re.match(r"[A-Za-z_]+", first)
                    if not (head and head.group() in _NO_DELETE):
                        out.append(_mk("STD", method_text, stmt_start, t.start, ""))
                stmt_start = None
        elif t.kind == "num":
            for rep in _int_replacements(t.text):
                out.append(_mk("LVR", method_text, t.start, t.end, rep))
        elif t.kind == "id":
            if t.text in ("true", "false"):
                out.append(_mk("LVR", method_text, t.start, t.end, "false" if t.text == "true" else "true"))
            elif t.text == "if" and k + 1 < len(toks) and toks[k + 1].text == "(":
                d, close = 0, None
                for u in toks[k + 1:]:
                    if u.kind == "op" and u.text == "(":
                        d += 1
                    elif u.kind == "op" and u.text == ")":
                        d -= 1
                        if d == 0:
                            close = u
                            break
                if close is not None:
                    s, e = toks[k + 1].end, close.start
                    out.append(_mk("NEG", method_text, s, e, f"!({method_text[s:e]})"))
    seen, uniq = set(), []
    for m in out:
        if m.mid not in seen and m.apply(method_text) != method_text:
            seen.add(m.mid)
            uniq.append(m)
    return uniq


def sample_mutants(method_text: str, focal_id: str, cap: int = MAX_MUTANTS) -> tuple[list[Mutant], int]:
    """At most `cap` mutants, chosen by a shuffle seeded from the focal id. Returns (chosen, number generated)."""
    ms = all_mutants(method_text)
    if len(ms) <= cap:
        return ms, len(ms)
    rng = random.Random(int(hashlib.sha256(focal_id.encode()).hexdigest()[:16], 16))
    idx = sorted(rng.sample(range(len(ms)), cap))
    return [ms[i] for i in idx], len(ms)
