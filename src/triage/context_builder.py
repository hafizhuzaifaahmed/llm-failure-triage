"""Deterministic Context Builder (Phase 2 Section 3.6, Table 8).

Input: one *judge-visible* instance view (see `judge_view`). Output: an evidence package string in which
every item carries a stable identifier, plus metadata (ids present, truncation flags, token estimate).

Identifier scheme (recorded in docs/tracking/DECISIONS.md, D-07):
  [T1]..[Tn]     lines of the failing test method (fixtures/imports are listed under [T0])
  [F1]           outcome type and exception class
  [F2]           exception message (expected/actual values kept)
  [F3]           test line at which the failure surfaced
  [F4]..[Fk]     retained stack frames, top of stack first
  [Sig1]         focal method signature; [Sig2] class declaration; [Sig3].. constructors, methods, types
  [Doc1]         method Javadoc (from B); [Doc2] class Javadoc (from B)
  [Spec1]..[Spec5] inferred specification fields (S2 only)
  [Impl1]        buggy focal body (ablation A5a only)

The builder never sees ground-truth labels: `judge_view` whitelists the fields it may read.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import config
from .preprocess import approx_tokens, cap_tokens, strip_html, truncate_message

SPEC_LEVELS = ("S0", "S1", "S2")

# Fields a judge-side module may read. Anything else in an instance record (labels, F outcomes,
# patch, bug id, developer tests) is dropped before the builder runs.
JUDGE_VISIBLE = {
    "instance_id", "test", "failure", "sig", "doc", "spec", "impl", "focal_class", "focal_method_name",
}
FORBIDDEN_KEYS = {"label", "gt_label", "outcomes_F", "failure_F", "sigma_F", "patch", "fixed_body",
                  "bug_id", "developer_tests", "trigger_tests"}


class LeakageError(RuntimeError):
    pass


def judge_view(instance: dict) -> dict:
    view = {k: v for k, v in instance.items() if k in JUDGE_VISIBLE}
    bad = FORBIDDEN_KEYS & set(view)
    if bad:  # defensive: JUDGE_VISIBLE and FORBIDDEN_KEYS must never overlap
        raise LeakageError(f"forbidden keys in judge view: {bad}")
    return view


@dataclass
class Package:
    text: str
    level: str
    ids: list[str]
    truncated: dict = field(default_factory=dict)
    approx_tokens: int = 0
    has_javadoc: bool = False
    variant: str = "full"


def _section(title: str, items: list[tuple[str, str]]) -> str:
    body = "\n".join(f"[{i}] {t}" for i, t in items)
    return f"=== {title} ===\n{body}" if items else f"=== {title} ===\n(none)"


def build_package(instance: dict, level: str, *, include_failure: bool = True, include_impl: bool = False,
                  spec_override: dict | None = None, max_tokens: int = config.MAX_PACKAGE_TOKENS) -> Package:
    """Build the evidence package for one instance at one specification level.

    include_failure=False  -> ablation A4 (section [F] removed)
    include_impl=True      -> ablation A5a (buggy focal body exposed)
    spec_override          -> ablation A5b (S2' specification inferred from the buggy body)
    """
    if level not in SPEC_LEVELS:
        raise ValueError(level)
    v = judge_view(instance)
    truncated = {"interface_items_dropped": 0, "frames_dropped": 0, "javadoc": False, "spec": False}

    # [T] test
    t = v["test"]
    test_lines = t["method_source"].splitlines()
    t_items = [(f"T{i + 1}", ln.rstrip()) for i, ln in enumerate(test_lines)]
    fixtures = t.get("fixtures", "").strip()
    t_header = []
    if t.get("imports"):
        t_header.append(("T0", "imports: " + "; ".join(t["imports"])))
    if fixtures:
        t_header.append(("T0", "fixtures:\n" + fixtures))

    # [F] failure on B
    f = v["failure"]
    f_items = [
        ("F1", f"outcome={f['outcome_type']}; exception={f.get('exception_class') or 'none'}"),
        ("F2", "message: " + truncate_message(f.get("message") or "")),
        ("F3", f"failing test line: {f.get('failing_test_line_text') or f.get('failing_test_line') or 'unknown'}"),
    ]
    frames = f.get("frames", [])
    frame_items = [(f"F{4 + i}", f"at {fr['method']}({fr['location']})") for i, fr in enumerate(frames)]

    # [Sig] interface
    s = v["sig"]
    sig_core = [("Sig1", s["focal_signature"]), ("Sig2", s["class_declaration"])]
    sig_rest = [(f"Sig{3 + i}", x) for i, x in enumerate(s.get("constructors", []) + s.get("methods", [])
                                                         + s.get("type_signatures", []))]

    # [Doc]
    d = v.get("doc") or {}
    doc_items = []
    if level in ("S1", "S2"):
        for i, key in ((1, "method_javadoc"), (2, "class_javadoc")):
            if d.get(key):
                txt, cut = cap_tokens(strip_html(d[key]), config.MAX_JAVADOC_TOKENS)
                truncated["javadoc"] |= cut
                doc_items.append((f"Doc{i}", txt))

    # [Spec]
    spec_items = []
    spec = spec_override if spec_override is not None else v.get("spec")
    if level == "S2" and spec:
        for i, key in enumerate(("purpose", "preconditions", "postconditions", "exceptions", "edge_cases")):
            val = spec.get(key, "")
            if isinstance(val, list):
                val = "; ".join(map(str, val))
            spec_items.append((f"Spec{i + 1}", f"{key}: {val}"))

    impl_items = [("Impl1", v["impl"])] if include_impl and v.get("impl") else []

    def render(sig_rest_kept, frames_kept):
        parts = [_section("[T] Failing test", t_header + t_items)]
        if include_failure:
            parts.append(_section("[F] Failure evidence (program version under test)", f_items + frames_kept))
        parts.append(_section("[Sig] Interface", sig_core + sig_rest_kept))
        if level in ("S1", "S2"):
            parts.append(_section("[Doc] Documentation", doc_items))
        if level == "S2":
            parts.append(_section("[Spec] Inferred specification", spec_items))
        if impl_items:
            parts.append(_section("[Impl] Implementation of the method under test", impl_items))
        return "\n\n".join(parts)

    # Truncation order (Table 7): interface listing first, then frames beyond the top 10.
    sig_kept, frames_kept = list(sig_rest), list(frame_items)
    text = render(sig_kept, frames_kept)
    while approx_tokens(text) > max_tokens and sig_kept:
        sig_kept.pop()
        truncated["interface_items_dropped"] += 1
        text = render(sig_kept, frames_kept)
    while approx_tokens(text) > max_tokens and len(frames_kept) > config.NEVER_TRUNCATED_FRAMES:
        frames_kept.pop()
        truncated["frames_dropped"] += 1
        text = render(sig_kept, frames_kept)

    ids = re.findall(r"^\[([A-Za-z]+\d+)\]", text, flags=re.M)
    return Package(text=text, level=level, ids=sorted(set(ids)), truncated=truncated,
                   approx_tokens=approx_tokens(text), has_javadoc=bool(d.get("method_javadoc")),
                   variant=("noF" if not include_failure else "") + ("impl" if include_impl else "")
                   + ("specprime" if spec_override is not None else "") or "full")


GENERIC_PATTERNS = (
    r"\b(?:buggy|fixed)[_/ -]?(?:version|dir|checkout)\b",                    # checkout naming
    r"\b(?:Chart|Cli|Closure|Codec|Collections|Compress|Csv|Gson|JacksonCore|JacksonDatabind|JacksonXml|"
    r"Jsoup|JxPath|Lang|Math|Mockito|Time)[_-]\d+[bf]?\b",                      # any Defects4J bug id
)


def leakage_check(package_text: str, guard: dict | None = None, extra_lines: list[str] | None = None,
                  exempt_body: str | None = None) -> list[str]:
    """Return every forbidden item found in the package (empty list = clean).

    guard        one record of data/leakage_guard/guard_<dataset>.jsonl: `bug_ids` (word-boundary match,
                 any length), `code_lines` (lines only in the fixed method, substring match), `paths`.
    extra_lines  focal-body lines (added by the runner except in ablation A5a).
    exempt_body  ablation A5a only (D-72): B's verbatim focal body, removed from the text the `code_lines` are
                 matched against -- an F-only line can be a substring of a B line. Bug ids, paths, extra lines
                 and generic patterns are still matched against the whole package.
    Generic patterns (any Defects4J bug id, buggy/fixed checkout names) are always applied.
    """
    guard = guard or {}
    hits = []
    for bid in guard.get("bug_ids", []):
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(bid)}(?![0-9])", package_text):
            hits.append(bid)
    low = package_text.lower()
    low_code = package_text.replace(exempt_body, "\n").lower() if exempt_body else low
    for s in guard.get("code_lines", []):
        s = (s or "").strip()
        if len(s) >= 6 and s.lower() in low_code:
            hits.append(s)
    for s in list(guard.get("paths", [])) + list(extra_lines or []):
        s = (s or "").strip()
        if len(s) >= 6 and s.lower() in low:
            hits.append(s)
    for pat in GENERIC_PATTERNS:
        hits += re.findall(pat, package_text)
    return hits


def cited_ids_valid(cited: list[str], package: Package) -> tuple[list[str], list[str]]:
    present = set(package.ids)
    return [c for c in cited if c in present], [c for c in cited if c not in present]
