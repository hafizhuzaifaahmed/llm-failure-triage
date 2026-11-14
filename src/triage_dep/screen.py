"""Static screen for constructs that can intercept a Throwable or an Error (WDP spec version 2, section 2.3).

Pure text, stdlib only. The test class source is tokenised with the engine's tokenizer; comments, string literals
and char literals are dropped before any construct is looked for, so the same words inside them never count.

`swallow_risk` is true if any of:
  1. a `catch` clause whose parameter types include Throwable or Error (simple or java.lang.-qualified, with or
     without `final`, including inside a multi-catch);
  2. `expected = Throwable.class` or `expected = Error.class` inside an annotation's arguments;
  3. `assertThrows(`, `expectThrows(` or `.expect(` whose first argument is `Throwable.class` or `Error.class`.
AssertionError, Exception and a `throws Throwable` clause do not set it.
"""
from __future__ import annotations

from triage_ext.mutate import tokenize

INTERCEPTING = {"Throwable", "Error", "java.lang.Throwable", "java.lang.Error"}
_DROP = ("ws", "comment", "str", "chr")


def _code_tokens(src: str) -> list:
    return [t for t in tokenize(src) if t.kind not in _DROP]


def _matching(toks: list, i: int) -> int:
    """Index of the ')' matching the '(' at toks[i]; len(toks) if unbalanced."""
    depth = 0
    for k in range(i, len(toks)):
        if toks[k].text == "(":
            depth += 1
        elif toks[k].text == ")":
            depth -= 1
            if depth == 0:
                return k
    return len(toks)


def _qualified_names(toks: list) -> list[str]:
    """Dotted identifier chains in a token run, e.g. ['final', 'java.lang.Error', 'e']."""
    out, k = [], 0
    while k < len(toks):
        if toks[k].kind == "id":
            name = toks[k].text
            k += 1
            while k + 1 < len(toks) and toks[k].text == "." and toks[k + 1].kind == "id":
                name += "." + toks[k + 1].text
                k += 2
            out.append(name)
        else:
            k += 1
    return out


def _is_class_literal(toks: list) -> bool:
    """True if the token run is exactly <Throwable|Error, possibly java.lang.-qualified> . class"""
    if len(toks) < 3 or toks[-1].text != "class" or toks[-2].text != ".":
        return False
    head = toks[:-2]
    names = _qualified_names(head)
    joined = "".join(t.text for t in head)
    return len(names) == 1 and names[0] == joined and joined in INTERCEPTING


def _first_argument(toks: list, open_at: int) -> list:
    """Tokens of the first argument of the call whose '(' is toks[open_at]."""
    depth, out = 0, []
    for k in range(open_at, len(toks)):
        x = toks[k].text
        if x in ("(", "[", "{"):
            depth += 1
            if depth == 1:
                continue
        elif x in (")", "]", "}"):
            depth -= 1
            if depth == 0:
                return out
        elif x == "," and depth == 1:
            return out
        out.append(toks[k])
    return out


def swallow_risk(test_class_source: str) -> bool:
    toks = _code_tokens(test_class_source or "")
    n = len(toks)
    for i, t in enumerate(toks):
        nxt = toks[i + 1].text if i + 1 < n else None
        # 1. catch (... Throwable | Error ... name)
        if t.kind == "id" and t.text == "catch" and nxt == "(":
            end = _matching(toks, i + 1)
            if any(q in INTERCEPTING for q in _qualified_names(toks[i + 2:end])):
                return True
        # 2. @Annotation( ... expected = Throwable.class ... )
        if t.kind == "op" and t.text == "@":
            k = i + 1
            while k < n and (toks[k].kind == "id" or toks[k].text == "."):
                k += 1
            if k < n and toks[k].text == "(":
                end = _matching(toks, k)
                args = toks[k + 1:end]
                for j, a in enumerate(args):
                    if a.kind == "id" and a.text == "expected" and j + 1 < len(args) and args[j + 1].text == "=":
                        val = []
                        for b in args[j + 2:]:
                            if b.text in (",", ")"):
                                break
                            val.append(b)
                        if _is_class_literal(val):
                            return True
        # 3. assertThrows( / expectThrows( / .expect( with a Throwable or Error class literal first
        if t.kind == "id" and nxt == "(" and (t.text in ("assertThrows", "expectThrows")
                                              or (t.text == "expect" and i > 0 and toks[i - 1].text == ".")):
            if _is_class_literal(_first_argument(toks, i + 1)):
                return True
    return False
