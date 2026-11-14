"""Reverse a unified diff into a standard one (D-82 protocol note): the replication package stores each fix as
fixed -> buggy; the audit packets show it buggy -> fixed.

The result is an ordinary unified diff: `diff --git a/P b/P`, `index <buggy>..<fixed>`, `--- a/P`, `+++ b/P`, hunk
headers `@@ -<buggy range> +<fixed range> @@`, and inside every change block all "-" (buggy) lines come before all
"+" (fixed) lines, as `git diff` writes them. A "\\ No newline at end of file" marker stays with the line it follows.
"""
import re

HUNK = re.compile(r"^@@ -(\d+(?:,\d+)?) \+(\d+(?:,\d+)?) @@(.*)$")
NOEOL = "\\ No newline at end of file"


def _flush(block, out):
    """block: list of (sign, [lines]) with sign '+'/'-' as in the SOURCE; emit reversed, '-' group first."""
    minus = [grp for sign, grp in block if sign == "+"]   # source '+' = buggy  -> output '-'
    plus = [grp for sign, grp in block if sign == "-"]    # source '-' = fixed  -> output '+'
    for grp in minus:
        out.append("-" + grp[0][1:])
        out.extend(grp[1:])
    for grp in plus:
        out.append("+" + grp[0][1:])
        out.extend(grp[1:])
    block.clear()


def reverse_unified_diff(diff: str) -> str:
    out, block = [], []
    in_hunk = False
    for ln in diff.splitlines():
        if ln.startswith("diff --git ") or ln.startswith("index ") or ln.startswith("--- ") or ln.startswith("+++ "):
            _flush(block, out)
            in_hunk = False
            if ln.startswith("index "):
                m = re.match(r"^index ([0-9a-f]+)\.\.([0-9a-f]+)(.*)$", ln)
                out.append(f"index {m.group(2)}..{m.group(1)}{m.group(3)}" if m else ln)
            elif ln.startswith("--- "):
                out.append("--- " + _ab(ln[4:], "a/"))
            elif ln.startswith("+++ "):
                out.append("+++ " + _ab(ln[4:], "b/"))
            else:
                out.append(ln)
            continue
        m = HUNK.match(ln)
        if m:
            _flush(block, out)
            in_hunk = True
            out.append(f"@@ -{m.group(2)} +{m.group(1)} @@{m.group(3)}")
            continue
        if in_hunk and ln and ln[0] in "+-":
            block.append((ln[0], [ln]))
            continue
        if in_hunk and ln == NOEOL and block:
            block[-1][1].append(ln)
            continue
        _flush(block, out)
        out.append(ln)
    _flush(block, out)
    # keep "--- a/" before "+++ b/" (they are already in that order in the source)
    return "\n".join(out)


def _ab(path: str, prefix: str) -> str:
    if path == "/dev/null":
        return path
    for p in ("a/", "b/"):
        if path.startswith(p):
            return prefix + path[2:]
    return prefix + path


def sides(diff: str) -> tuple[list[str], list[str]]:
    """The old and new side of every hunk, concatenated (for checking a reversal)."""
    old, new, in_hunk = [], [], False
    for ln in diff.splitlines():
        if HUNK.match(ln):
            in_hunk = True
            continue
        if ln.startswith(("diff --git ", "index ", "--- ", "+++ ")):
            in_hunk = False
            continue
        if not in_hunk or ln == NOEOL:
            continue
        if ln.startswith("-"):
            old.append(ln[1:])
        elif ln.startswith("+"):
            new.append(ln[1:])
        else:
            old.append(ln[1:] if ln.startswith(" ") else ln)
            new.append(ln[1:] if ln.startswith(" ") else ln)
    return old, new
