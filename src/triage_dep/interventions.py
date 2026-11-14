"""Whole-body replacements of the method under test (WDP, TECHNICAL_METHOD_SPEC.md version 2, section 2.1).

Pure text, deterministic, stdlib only. The signature of the method is never touched: everything from the body's
opening brace to its matching closing brace is replaced by one new body. Nothing here reads a label, a fixed
version or a test.
"""
from __future__ import annotations

import hashlib
import json

from triage_ext.mutate import _body_start, tokenize

X_THROW_ID = "X-THROW"
# Exactly the text of spec section 2.1 (one line in the source).
X_THROW_BODY = ('{ try { java.lang.String __wdp_m = java.lang.System.getenv("WDP_MARKER"); if (__wdp_m != null) '
                '{ new java.io.File(__wdp_m).createNewFile(); } } catch (java.lang.Throwable __wdp_t) { } '
                'throw new java.lang.Error("__WDP__"); }')

NUMERIC = ("byte", "short", "int", "long", "float", "double")
# Declared return type -> X-RET bodies, in order (spec section 2.1). Anything not listed: { return null; }.
X_RET_TABLE = {
    "void": ["{ }"],
    "boolean": ["{ return false; }", "{ return true; }"],
    **{t: ["{ return 0; }", "{ return 1; }"] for t in NUMERIC},
    "char": ["{ return ' '; }", "{ return 'A'; }"],
    "String": ['{ return ""; }', '{ return "A"; }'],
    "java.lang.String": ['{ return ""; }', '{ return "A"; }'],
}
X_RET_OTHER = ["{ return null; }"]
MAX_VARIANTS = 3

MODIFIERS = {"public", "protected", "private", "static", "final", "synchronized", "abstract", "native", "strictfp",
             "default"}


def variant_table_sha256() -> str:
    """Hash of the variant table, written into each run's metadata."""
    doc = {"x_throw": X_THROW_BODY, "x_ret": X_RET_TABLE, "x_ret_other": X_RET_OTHER, "max_variants": MAX_VARIANTS}
    return hashlib.sha256(json.dumps(doc, sort_keys=True).encode("utf-8")).hexdigest()


def body_sha(body: str) -> str:
    return hashlib.sha1(body.encode("utf-8")).hexdigest()[:12]


def _code(tokens):
    return [t for t in tokens if t.kind not in ("ws", "comment")]


def _open_brace(method_text: str) -> int:
    """Offset of the body's opening brace; ValueError if the text has no body."""
    s = _body_start(method_text)
    if s == 0 or method_text[s - 1] != "{":
        raise ValueError("method text has no body")
    return s - 1


def _close_brace(method_text: str, open_at: int) -> int:
    """Offset of the brace that closes the body opened at `open_at` (braces in literals and comments ignored)."""
    depth = 0
    for t in tokenize(method_text[open_at:]):
        if t.kind != "op":
            continue
        if t.text == "{":
            depth += 1
        elif t.text == "}":
            depth -= 1
            if depth == 0:
                return open_at + t.start
    raise ValueError("unbalanced method body")


def return_type(method_text: str) -> str | None:
    """Declared return type of the method, or None if the header cannot be parsed (brief section 3.1)."""
    try:
        open_at = _open_brace(method_text)
    except ValueError:
        return None
    header = method_text[:open_at]
    toks = _code(tokenize(header))
    i, n = 0, len(toks)
    while i < n:
        t = toks[i]
        if t.kind == "op" and t.text == "@":                       # annotation: @Name(.Name)* [ ( ... ) ]
            i += 1
            if i < n and toks[i].kind == "id" and toks[i].text == "interface":
                return None
            while i < n and toks[i].kind == "id":
                i += 1
                if i < n and toks[i].text == "." and i + 1 < n and toks[i + 1].kind == "id":
                    i += 1
                    continue
                break
            if i < n and toks[i].text == "(":
                depth = 0
                while i < n:
                    if toks[i].text == "(":
                        depth += 1
                    elif toks[i].text == ")":
                        depth -= 1
                        if depth == 0:
                            i += 1
                            break
                    i += 1
                else:
                    return None
            continue
        if t.kind == "id" and t.text in MODIFIERS:
            i += 1
            continue
        break
    if i < n and toks[i].text == "<":                              # leading type-parameter list
        depth = 0
        while i < n:
            x = toks[i].text
            if x == "<":
                depth += 1
            elif x in (">", ">>", ">>>"):
                depth -= len(x)
            i += 1
            if depth == 0:
                break
            if depth < 0:
                return None
        if depth != 0:
            return None
    paren = next((k for k in range(i, n) if toks[k].kind == "op" and toks[k].text == "("), None)
    if paren is None or paren - 1 <= i or toks[paren - 1].kind != "id":
        return None
    type_toks = toks[i:paren - 1]
    if not type_toks:
        return None
    out = type_toks[0].text
    for a, b in zip(type_toks, type_toks[1:]):
        out += (" " if header[a.end:b.start] else "") + b.text
    return out


def variants(method_text: str) -> list[dict]:
    """[{id, body}]: X-THROW first, then the X-RET bodies of the declared return type; at most three."""
    out = [{"id": X_THROW_ID, "body": X_THROW_BODY}]
    rt = return_type(method_text)
    if rt is None:
        return out
    bodies = X_RET_TABLE.get(rt, X_RET_OTHER)
    out += [{"id": f"X-RET-{k}", "body": b} for k, b in enumerate(bodies, 1)]
    return out[:MAX_VARIANTS]


def apply(method_text: str, body: str) -> str:
    """The method text with its whole body replaced by `body`; the signature is byte-identical."""
    open_at = _open_brace(method_text)
    close_at = _close_brace(method_text, open_at)
    return method_text[:open_at] + body + method_text[close_at + 1:]
