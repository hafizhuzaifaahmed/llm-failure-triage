"""Light-weight Java source utilities (stdlib only; runs on the WSL execution side).

A masking pass blanks comments, string and char literals while preserving offsets, so brace matching
and member detection work on real Java without a full parser. Coverage is checked by unit tests on
Defects4J-style sources; anything unparsable is reported, never guessed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


def mask(src: str) -> str:
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j == -1 else j
            for k in range(i, j):
                out[k] = " "
            i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j == -1 else j + 2
            for k in range(i, j):
                if src[k] != "\n":
                    out[k] = " "
            i = j
        elif c == '"' and src.startswith('"""', i):
            j = src.find('"""', i + 3)
            j = n if j == -1 else j + 3
            for k in range(i + 1, j - 1):
                if src[k] != "\n":
                    out[k] = " "
            i = j
        elif c in "\"'":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            for k in range(i + 1, min(j, n)):
                out[k] = " "
            i = j + 1
        else:
            i += 1
    return "".join(out)


def matching_brace(masked: str, open_idx: int) -> int:
    depth = 0
    for i in range(open_idx, len(masked)):
        if masked[i] == "{":
            depth += 1
        elif masked[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("unbalanced braces")


@dataclass
class Member:
    kind: str            # method | constructor | field | initializer | type
    name: str
    start: int           # offset of first annotation / modifier (after Javadoc)
    end: int             # offset after closing brace or semicolon
    header: str          # declaration text up to '{' or ';'
    javadoc: str = ""
    annotations: list = field(default_factory=list)
    javadoc_start: Optional[int] = None

    def text(self, src: str) -> str:
        return src[self.start:self.end]


_IDENT = r"[A-Za-z_$][\w$]*"
_METHOD_HDR = re.compile(rf"({_IDENT})\s*\($")


def _class_body_bounds(src: str, masked: str, class_name: Optional[str]) -> tuple[int, int]:
    pat = rf"\b(class|interface|enum)\s+{re.escape(class_name)}\b" if class_name else r"\b(class|interface|enum)\s+" + _IDENT
    m = re.search(pat, masked)
    if not m:
        raise ValueError(f"class {class_name} not found")
    ob = masked.index("{", m.end())
    return ob, matching_brace(masked, ob)


def members(src: str, class_name: Optional[str] = None) -> list[Member]:
    """Direct members of a (top-level or named) class, in source order."""
    masked = mask(src)
    ob, cb = _class_body_bounds(src, masked, class_name)
    out, i = [], ob + 1
    prev_end = ob + 1
    while i < cb:
        while i < cb and masked[i] in " \t\r\n;":
            i += 1
        if i >= cb:
            break
        # declaration runs until the first top-level '{' or ';'
        j, paren = i, 0
        while j < cb:
            ch = masked[j]
            if ch == "(":
                paren += 1
            elif ch == ")":
                paren -= 1
            elif paren == 0 and ch in "{;=":
                break
            j += 1
        if j >= cb:
            break
        header = src[i:j].strip()
        hm = masked[i:j]
        if masked[j] == "=":  # field with initializer: skip to ';' at depth 0
            k, depth = j, 0
            while k < cb:
                if masked[k] in "({[":
                    depth += 1
                elif masked[k] in ")}]":
                    depth -= 1
                elif masked[k] == ";" and depth == 0:
                    break
                k += 1
            end = k + 1
            name = re.findall(_IDENT, hm.split("=")[0])[-1] if re.findall(_IDENT, hm) else "?"
            kind = "field"
        elif masked[j] == ";":
            end = j + 1
            hdr_core = re.sub(r"@\w+(\([^)]*\))?", "", hm)
            if "(" in hdr_core:  # abstract / interface method
                kind = "method"
                name = re.search(rf"({_IDENT})\s*\(", hdr_core).group(1)
            else:
                kind, name = "field", (re.findall(_IDENT, hdr_core) or ["?"])[-1]
        else:
            end = matching_brace(masked, j) + 1
            hdr_core = re.sub(r"@\w+(\.\w+)*(\([^)]*\))?", " ", hm)
            if re.search(r"\b(class|interface|enum)\b", hdr_core):
                kind = "type"
                name = re.search(rf"\b(?:class|interface|enum)\s+({_IDENT})", hdr_core).group(1)
            elif "(" in hdr_core:
                pre = hdr_core[: hdr_core.index("(")].split()
                name = pre[-1] if pre else "?"
                rest = [w for w in pre[:-1] if w not in ("public", "protected", "private", "static", "final",
                                                         "synchronized", "abstract", "native", "strictfp")]
                kind = "constructor" if not rest or (len(rest) == 1 and rest[0].startswith("<")) else "method"
            else:
                kind, name = "initializer", "<init-block>"
        annotations = re.findall(r"@(\w+)", re.sub(r"\(.*", "", hm.split("(")[0]) if kind in ("method", "constructor") else hm)
        # Javadoc immediately preceding
        # Javadoc can only sit between the previous member and this one; searching the whole prefix
        # made this quadratic-to-cubic on very large classes (Closure).
        before = src[prev_end:i]
        jd = ""
        jd_start = None
        k = before.rfind("/**")
        if k != -1:
            mjd = re.match(r"/\*\*.*?\*/\s*$", before[k:], re.S)
            if mjd:
                jd = mjd.group(0).strip()
                jd_start = prev_end + k
        out.append(Member(kind, name, i, end, header, jd, annotations, jd_start))
        i = end
        prev_end = end
    return out


def package_of(src: str) -> str:
    m = re.search(r"^\s*package\s+([\w.]+)\s*;", mask(src), re.M)
    return m.group(1) if m else ""


def imports_of(src: str) -> list[str]:
    """Imported names; a static import keeps its `static ` prefix (D-42: dropping it turned
    `import static a.B.C;` into the uncompilable `import a.B.C;` in assembled tests)."""
    return [("static " if st else "") + name
            for st, name in re.findall(r"^\s*import\s+(static\s+)?([\w.*]+)\s*;", src, re.M)]


def import_lines(src: str) -> list[str]:
    return [m.group(0).strip() for m in re.finditer(r"^\s*import\s+[^;]+;", src, re.M)]


def top_level_class_name(src: str) -> Optional[str]:
    m = re.search(r"\b(?:public\s+)?(?:final\s+|abstract\s+)*class\s+(" + _IDENT + ")", mask(src))
    return m.group(1) if m else None


def is_test_method(m: Member) -> bool:
    return m.kind == "method" and "Test" in m.annotations


def test_methods(src: str) -> list[Member]:
    return [m for m in members(src, top_level_class_name(src)) if is_test_method(m)]


def fixtures_of(src: str) -> str:
    """Fields, set-up/tear-down and helper methods of a test class (everything that is not a @Test)."""
    cls = top_level_class_name(src)
    parts = [m.text(src).strip() for m in members(src, cls) if not is_test_method(m)]
    return "\n".join(parts)


def remove_members(src: str, names: set[str]) -> str:
    """Remove @Test methods by name (with their Javadoc) — used for compile pruning."""
    cls = top_level_class_name(src)
    ms = [m for m in members(src, cls) if is_test_method(m) and m.name in names]
    for m in sorted(ms, key=lambda x: x.start, reverse=True):
        s = m.javadoc_start if m.javadoc_start is not None else m.start
        src = src[:s] + src[m.end:]
    return src


def keep_only_test(src: str, keep: str) -> str:
    names = {m.name for m in test_methods(src)} - {keep}
    return remove_members(src, names)


def member_at_line(src: str, line: int) -> Optional[Member]:
    off = sum(len(l) + 1 for l in src.split("\n")[: line - 1])
    for m in members(src, top_level_class_name(src)):
        if m.start <= off < m.end:
            return m
    return None


def signature_of(m: Member) -> str:
    h = re.sub(r"\s+", " ", m.header)
    h = re.sub(r"@\w+(\([^)]*\))?\s*", "", h)
    return h.strip()


def is_private(m: Member) -> bool:
    return re.search(r"\bprivate\b", m.header) is not None


def class_declaration(src: str, class_name: str) -> str:
    masked = mask(src)
    m = re.search(rf"[^;{{}}]*\b(class|interface|enum)\s+{re.escape(class_name)}\b[^{{]*", masked)
    if not m:
        return ""
    text = src[m.start():m.end()]
    text = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
    return re.sub(r"\s+", " ", text).strip()


def class_javadoc(src: str, class_name: str) -> str:
    masked = mask(src)
    m = re.search(rf"\b(class|interface|enum)\s+{re.escape(class_name)}\b", masked)
    if not m:
        return ""
    before = src[: m.start()]
    jd = re.search(r"/\*\*(.*?)\*/[^/]*$", before, re.S)
    return jd.group(0).strip() if jd else ""


def find_methods(src: str, class_name: str, name: str) -> list[Member]:
    return [m for m in members(src, class_name) if m.kind in ("method", "constructor") and m.name == name]


def param_types(m: Member) -> list[str]:
    h = signature_of(m)
    inside = h[h.index("(") + 1: h.rindex(")")]
    out, depth, cur = [], 0, ""
    for ch in inside:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    types = []
    for p in out:
        p = re.sub(r"\bfinal\b|@\w+", "", p).strip()
        types.append(p.rsplit(None, 1)[0] if " " in p else p)
    return types


def call_sites(sources: dict[str, str], method_name: str, exclude_file: Optional[str] = None,
               max_sites: int = 5, context: int = 5) -> list[dict]:
    """Up to `max_sites` call sites of `method_name` in main code, +/- `context` lines each.

    sources: path -> text of main (non-test) source files of B. Order is by path then line (deterministic).
    """
    sites = []
    pat = re.compile(rf"(?<![\w$])\.?{re.escape(method_name)}\s*\(")
    for path in sorted(sources):
        src = sources[path]
        masked = mask(src)
        lines = src.split("\n")
        for m in pat.finditer(masked):
            ln = masked.count("\n", 0, m.start())
            line_txt = masked.split("\n")[ln]
            if re.search(rf"\b(public|protected|private|static)\b[^=;]*\b{re.escape(method_name)}\s*\(", line_txt):
                continue  # a declaration, not a call
            lo, hi = max(0, ln - context), min(len(lines), ln + context + 1)
            sites.append({"path": path, "line": ln + 1, "snippet": "\n".join(lines[lo:hi]),
                          "lines": list(range(lo + 1, hi + 1))})
            if len(sites) >= max_sites:
                return sites
    return sites
