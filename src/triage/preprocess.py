"""Preprocessing rules of Phase 2 Table 7. Stdlib only (also used on the WSL execution side)."""
from __future__ import annotations

import re
from typing import Iterable

from . import config

FRAMEWORK_PREFIXES = (
    "org.junit.", "junit.", "sun.reflect.", "jdk.internal.", "java.lang.reflect.", "java.lang.Thread",
    "org.apache.tools.ant.", "org.hamcrest.", "org.mockito.internal.", "net.bytebuddy.", "TestRunner",
    "triage.runner.",
)
_HASH = re.compile(r"@[0-9a-f]{6,8}\b")
_ABS_PATH = re.compile(r"(?:/[\w.\-]+){2,}/?|[A-Za-z]:\\(?:[\w.\- ]+\\)*[\w.\- ]*")
_TIMESTAMP = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b")
_TMP = re.compile(r"\b(?:tmp|temp)[\w\-]*\d{3,}[\w\-]*", re.I)
_FRAME = re.compile(r"^\s*at\s+([\w$.<>]+)\(([^)]*)\)")
_CAUSED = re.compile(r"^\s*Caused by:\s*(.*)")


def scrub(text: str) -> str:
    text = _TIMESTAMP.sub("<TIMESTAMP>", text)
    text = _HASH.sub("@<HASH>", text)
    text = _TMP.sub("<TMPDIR>", text)
    text = _ABS_PATH.sub(lambda m: "<PATH>" if m.group(0).count("/") > 2 or "\\" in m.group(0) else m.group(0), text)
    return text


def truncate_message(msg: str, limit: int = config.MAX_MESSAGE_CHARS) -> str:
    msg = msg or ""
    return msg if len(msg) <= limit else msg[:limit] + f" …[truncated {len(msg) - limit} chars]"


def _is_project_frame(method: str, project_packages: Iterable[str], test_class: str) -> bool:
    if test_class and method.startswith(test_class):
        return True
    return any(method.startswith(p) for p in project_packages) and not method.startswith(FRAMEWORK_PREFIXES)


def normalise_stack_trace(trace: str, project_packages: Iterable[str], test_class: str,
                          max_frames: int = config.MAX_STACK_FRAMES) -> dict:
    """Return the retained frames plus a rendered, scrubbed trace.

    Keeps: header line, project/test frames (up to `max_frames`), head of every 'Caused by'.
    Collapses: consecutive non-project frames into '[k framework frames omitted]'.
    """
    project_packages = tuple(project_packages)
    lines = (trace or "").splitlines()
    out_lines, frames = [], []
    omitted = 0
    kept = 0

    def flush():
        nonlocal omitted
        if omitted:
            out_lines.append(f"[{omitted} framework frames omitted]")
            omitted = 0

    for i, line in enumerate(lines):
        m = _FRAME.match(line)
        if m:
            method, loc = m.group(1), m.group(2)
            if _is_project_frame(method, project_packages, test_class) and kept < max_frames:
                flush()
                frames.append({"method": method, "location": loc,
                               "in_test": bool(test_class) and method.startswith(test_class)})
                out_lines.append(f"at {method}({loc})")
                kept += 1
            else:
                omitted += 1
            continue
        if re.match(r"^\s*\.\.\. \d+ more", line):
            omitted += int(re.findall(r"\d+", line)[0])
            continue
        c = _CAUSED.match(line)
        if c:
            flush()
            out_lines.append("Caused by: " + truncate_message(scrub(c.group(1))))
            continue
        if i == 0 or line.strip():
            flush()
            out_lines.append(truncate_message(scrub(line.strip())))
    flush()
    return {"frames": frames, "rendered": "\n".join(out_lines)}


def deepest_project_frame(frames: list[dict], focal_class: str) -> str:
    """R0 feature: location of the deepest (top-of-stack) project frame: test | focal | main | none."""
    if not frames:
        return "none"
    top = frames[0]
    if top["in_test"]:
        return "test"
    if focal_class and top["method"].startswith(focal_class + "."):
        return "focal"
    return "main"


def normalise_test_body(src: str) -> str:
    """Comment- and whitespace-insensitive canonical form used for de-duplication hashing."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    src = re.sub(r"\s+", " ", src).strip()
    # the test method name is irrelevant to behaviour
    src = re.sub(r"(void\s+)\w+(\s*\()", r"\1T\2", src, count=1)
    return src


def strip_html(javadoc: str) -> str:
    t = re.sub(r"</?(p|br|ul|ol|li|pre|code|b|i|em|strong|tt|a[^>]*)\s*/?>", " ", javadoc or "", flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\{@(?:code|link|linkplain|literal)\s+([^}]*)\}", r"\1", t)
    t = t.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&nbsp;", " ")
    return re.sub(r"[ \t]+", " ", t).strip()


def approx_tokens(text: str) -> int:
    """Deterministic, conservative token estimate (D-35). Real counts come from the response usage field."""
    return int(len(text) / config.CHARS_PER_TOKEN_ESTIMATE) + 1


def cap_words(text: str, max_words: int = config.MAX_ARGUMENT_WORDS) -> str:
    """First max_words whitespace-separated words (D-35: forwarded debate statements are held to 150 words)."""
    words = text.split()
    return text if len(words) <= max_words else " ".join(words[:max_words]) + " …[truncated]"


def cap_tokens(text: str, max_tokens: int) -> tuple[str, bool]:
    if approx_tokens(text) <= max_tokens:
        return text, False
    keep = int(max_tokens * config.CHARS_PER_TOKEN_ESTIMATE)
    return text[:keep] + " …[truncated]", True
