"""D1 sampling frame (Phase 2 Section 3.2) and context extraction from B (C3). Runs inside WSL; stdlib only.

The frame of Zhao et al. [12] (318 focal methods / 233 defects) is NOT shipped as a list in their
replication package (commit 751f9f4 = Zenodo v1.0.0); only the procedure is. It is reconstructed
here by re-implementing that procedure (D-03):

  candidates  = functions changed by the fix (buggy_fix_info.json -> fixing_changes[*].changed_functions)
  keep if       the method exists in BOTH the buggy and fixed checkout
                AND it is public or protected (their unify notebook drops private and package-private)
                AND it is invoked by name inside at least one bug-triggering test method on B
  key           bug + method signature (duplicates collapsed)

Then the Phase 2 [DES] steps: cap of 25 focal methods per project (seeded), project-level split
3 dev / 14 test (seeded draw, made before any test is generated).
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Optional

from . import config, javasrc
from .execution import D4J_HOME, checkout_version

FIX_INFO = config.EXTERNAL / "EvalAndMitigate" / "data" / "d4j2_fix_info"
ACCESS = re.compile(r"\b(public|protected)\b")


def active_bugs(project: str) -> list[str]:
    f = D4J_HOME / "framework" / "projects" / project / "active-bugs.csv"
    rows = f.read_text().splitlines()[1:]
    return [r.split(",")[0] for r in rows if r.strip()]


def parse_qualified(q: str) -> dict:
    """'org.x.Foo:bar:[final String s, int n]:Number' -> parts. Inner classes appear as Outer$Inner."""
    cls, rest = q.split(":", 1)
    name, rest = rest.split(":", 1)
    close = rest.rfind("]:")  # array types inside the list contain ']' too, so anchor on the last "]:"
    if close == -1:
        close = rest.rindex("]")
    params = rest[rest.index("[") + 1: close]
    ret = rest[close + 2:]
    cls = cls.replace("\\$", "$")
    parts, depth, cur = [], 0, ""
    for ch in params:  # split on top-level commas only (generic arguments contain commas)
        depth += ch == "<"
        depth -= ch == ">"
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    ptypes = []
    for p in [x.strip() for x in parts if x.strip()]:
        p = re.sub(r"\bfinal\b|@\w+", "", p).strip()
        ptypes.append(p.rsplit(None, 1)[0] if " " in p else p)
    return {"class": cls, "simple_class": cls.split(".")[-1].split("$")[-1], "outer_class": cls.split(".")[-1].split("$")[0],
            "name": name, "param_types": ptypes, "return_type": ret}


def _norm_type(t: str) -> str:
    t = re.sub(r"<.*>", "", t).replace("...", "[]").strip()
    return t.split(".")[-1]


def locate_method(src: str, q: dict) -> Optional[javasrc.Member]:
    try:
        cands = javasrc.find_methods(src, q["simple_class"], q["name"])
    except ValueError:
        return None
    want = [_norm_type(t) for t in q["param_types"]]
    for m in cands:
        try:
            if [_norm_type(t) for t in javasrc.param_types(m)] == want:
                return m
        except ValueError:
            continue
    return None


def invoked_in(test_src: str, test_methods: list[str], method_name: str) -> bool:
    """True if `method_name(` is called as a method (not constructed) in any of the named test methods."""
    try:
        ms = javasrc.members(test_src, javasrc.top_level_class_name(test_src))
    except ValueError:
        return False
    pat = re.compile(rf"(?<![\w$])(?<!new\s){re.escape(method_name)}\s*\(")
    for m in ms:
        if m.kind == "method" and m.name in test_methods:
            body = javasrc.mask(m.text(test_src))
            body = body[body.find("{"):]
            if pat.search(body):
                return True
    return False


def screen_bug(bug_name: str) -> list[dict]:
    """Return one record per candidate focal method of a bug, with the frame decision and its reasons."""
    info = json.loads((FIX_INFO / bug_name / "buggy_fix_info.json").read_text())
    project, bug = info["proj"], str(info["id"])
    props = info["properties"]
    wb = checkout_version(project, bug, "b")
    wf = checkout_version(project, bug, "f")
    triggers: dict[str, list[str]] = {}
    for t in info.get("trigger_tests", []):
        triggers.setdefault(t["test_class"], []).append(t["test_function"])
    test_srcs = {}
    for tc in triggers:
        p = wb / props["test.dir"] / (tc.split("$")[0].replace(".", "/") + ".java")
        if p.exists():
            test_srcs[tc] = p.read_text(errors="replace")
    out, seen = [], set()
    for change in info.get("fixing_changes", []):
        files = list(dict.fromkeys(change.get("changed_class", [])))
        quals = sorted({q for cf in change.get("changed_functions", []) for q in cf["qualified_names"]})
        for qual in quals:
            q = parse_qualified(qual)
            rec = {"bug_name": bug_name, "project": project, "bug": bug, "qualified": qual, "class": q["class"],
                   "method": q["name"], "param_types": q["param_types"]}
            src_b = src_f = None
            for rel in files:
                pb, pf = wb / rel, wf / rel
                if pb.exists() and re.search(rf"\b(class|interface|enum)\s+{re.escape(q['simple_class'])}\b",
                                            pb.read_text(errors="replace")):
                    src_b = pb.read_text(errors="replace")
                    src_f = pf.read_text(errors="replace") if pf.exists() else None
                    rec["file"] = rel
                    break
            mb = locate_method(src_b, q) if src_b else None
            mf = locate_method(src_f, q) if src_f else None
            rec["in_B"], rec["in_F"] = mb is not None, mf is not None
            rec["access_ok"] = bool(mb and ACCESS.search(mb.header.split("(")[0]))
            rec["is_constructor"] = bool(mb and mb.kind == "constructor")
            rec["invoked"] = any(invoked_in(test_srcs[tc], fns, q["name"]) for tc, fns in triggers.items()
                                 if tc in test_srcs)
            rec["signature"] = javasrc.signature_of(mb) if mb else None
            key = (bug_name, rec["signature"] or qual)
            rec["duplicate"] = key in seen
            seen.add(key)
            rec["in_frame"] = rec["in_B"] and rec["in_F"] and rec["access_ok"] and rec["invoked"] and not rec["duplicate"]
            reasons = [k for k, ok in (("absent_in_B", rec["in_B"]), ("absent_in_F", rec["in_F"]),
                                       ("private_or_package", rec["access_ok"]), ("not_invoked", rec["invoked"]),
                                       ("duplicate", not rec["duplicate"])) if not ok]
            rec["exclusion_reasons"] = reasons
            rec["focal_id"] = f"{bug_name}::{q['class']}::{q['name']}({','.join(q['param_types'])})"
            out.append(rec)
    return out


def apply_cap_and_split(frame: list[dict]) -> tuple[list[dict], dict]:
    """25-per-project seeded cap and the 3/14 project split. Both draws use fixed seeds (config)."""
    projects = sorted({r["project"] for r in frame})
    rng_split = random.Random(config.SEED_SPLIT)
    dev = sorted(rng_split.sample(sorted(config.D4J_PROJECTS), config.N_DEV_PROJECTS))
    rng_cap = random.Random(config.SEED_FRAME_CAP)
    sampled = []
    for p in projects:
        rows = sorted([r for r in frame if r["project"] == p], key=lambda r: r["focal_id"])
        if len(rows) > config.MAX_FOCAL_PER_PROJECT:
            rows = sorted(rng_cap.sample(rows, config.MAX_FOCAL_PER_PROJECT), key=lambda r: r["focal_id"])
        for r in rows:
            sampled.append({**r, "split": "dev" if p in dev else "test"})
    return sampled, {"dev_projects": dev, "test_projects": [p for p in config.D4J_PROJECTS if p not in dev],
                     "seed_split": config.SEED_SPLIT, "seed_cap": config.SEED_FRAME_CAP}


# ------------------------------------------------------------------------------------------
# Context extraction from B (C3). The fixed version is used ONLY to compute the patch-line mask
# and the label-side copy of the fixed body (stored outside every judge-visible record).
# ------------------------------------------------------------------------------------------

def patch_lines_in_B(diff: str, rel_path: str) -> set[int]:
    """B-side line numbers touched by the fix in `rel_path` (removed lines, and insertion points)."""
    lines, cur_file, b_line = set(), None, 0
    for ln in diff.splitlines():
        if ln.startswith("--- "):
            cur_file = ln[4:].split("\t")[0]
            cur_file = cur_file[2:] if cur_file.startswith(("a/", "b/")) else cur_file
            continue
        if ln.startswith("+++ "):
            continue
        m = re.match(r"@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@", ln)
        if m:
            b_line = int(m.group(1))
            continue
        if cur_file is None or not cur_file.endswith(rel_path):
            continue
        if ln.startswith("-"):
            lines.add(b_line)
            b_line += 1
        elif ln.startswith("+"):
            lines.add(b_line)
        else:
            b_line += 1
    return lines


def _type_file(src_root: Path, pkg: str, imports: list[str], simple: str) -> Optional[Path]:
    for imp in imports:
        if imp.endswith("." + simple):
            p = src_root / (imp.replace(".", "/") + ".java")
            if p.exists():
                return p
    p = src_root / pkg.replace(".", "/") / f"{simple}.java"
    return p if p.exists() else None


def extract_context(rec: dict, info: dict, b_workdir: Optional[Path] = None, f_workdir: Optional[Path] = None,
                    mask_lines: Optional[dict] = None) -> dict:
    """Judge-visible context pieces for one focal method, all taken from B.

    D1 calls this with the defaults (B and F are the Defects4J checkouts; call-site lines changed by the fix are
    masked). D2 passes b_workdir = the mutant version (F + one mutant), f_workdir = F, and mask_lines = the mutated
    line, so the context is extracted from D2's own B exactly as Phase 2 C3 prescribes.
    """
    project, bug = rec["project"], rec["bug"]
    wb = Path(b_workdir) if b_workdir is not None else checkout_version(project, bug, "b")
    wf = Path(f_workdir) if f_workdir is not None else checkout_version(project, bug, "f")
    props = info["properties"]
    src_root = wb / props["src.dir"]
    src = (wb / rec["file"]).read_text(errors="replace")
    q = parse_qualified(rec["qualified"])
    m = locate_method(src, q)
    cls_members = javasrc.members(src, q["simple_class"])
    public = [x for x in cls_members if x.kind in ("method", "constructor") and ACCESS.search(x.header.split("(")[0])]
    ctors = [javasrc.signature_of(x) + ";" for x in public if x.kind == "constructor"]
    methods = [javasrc.signature_of(x) + ";" for x in public if x.kind == "method" and x.start != m.start]
    pkg = javasrc.package_of(src)
    imports = javasrc.imports_of(src)
    type_sigs = []
    prim = {"int", "long", "short", "byte", "char", "boolean", "float", "double", "void", "String", "Object"}
    for t in dict.fromkeys([_norm_type(t) for t in q["param_types"] + [q["return_type"]]]):
        t = t.replace("[]", "")
        if not t or t in prim or t == q["simple_class"]:
            continue
        tf = _type_file(src_root, pkg, imports, t)
        if tf:
            try:
                tsrc = tf.read_text(errors="replace")
                tm = [javasrc.signature_of(x) + ";" for x in javasrc.members(tsrc, t)
                      if x.kind in ("method", "constructor") and ACCESS.search(x.header.split("(")[0])][:15]
                type_sigs.append(f"{javasrc.class_declaration(tsrc, t)} {{ {' '.join(tm)} }}")
            except ValueError:
                pass
    # call sites of the focal method in main code of B, minus lines changed by the fix
    main_sources = {str(p.relative_to(wb)): p.read_text(errors="replace") for p in sorted(src_root.rglob("*.java"))}
    if mask_lines is None:
        mask_lines = {}
        for ch in info.get("fixing_changes", []):
            for rel in ch.get("changed_class", []):
                mask_lines.setdefault(rel, set()).update(patch_lines_in_B(ch.get("diff", ""), rel))
    sites = []
    for s in javasrc.call_sites(main_sources, q["name"], max_sites=config.MAX_CALL_SITES * 3,
                                context=config.CALL_SITE_CONTEXT_LINES):
        banned = mask_lines.get(s["path"], set())
        if banned & set(s["lines"]):
            keep = [l for l in s["snippet"].split("\n")]
            s["snippet"] = "\n".join(t for ln, t in zip(s["lines"], keep) if ln not in banned)
            s["patch_lines_removed"] = True
        sites.append(s)
        if len(sites) >= config.MAX_CALL_SITES:
            break
    siblings = [{"name": x.name, "javadoc": x.javadoc} for x in cls_members
                if x.kind == "method" and x.start != m.start and ACCESS.search(x.header.split("(")[0])]
    body_b = src[m.start:m.end]
    mf = locate_method((wf / rec["file"]).read_text(errors="replace"), q)
    fixed_body = (wf / rec["file"]).read_text(errors="replace")[mf.start:mf.end] if mf else None
    javadoc_b = m.javadoc
    javadoc_f = mf.javadoc if mf else None
    return {
        "focal_id": rec["focal_id"], "package": pkg, "focal_class": q["class"].replace("$", "."),
        "focal_method_name": q["name"], "class_simple": q["simple_class"], "imports": imports,
        "sig": {"focal_signature": javasrc.signature_of(m), "class_declaration": javasrc.class_declaration(src, q["simple_class"]),
                "constructors": ctors, "methods": methods, "type_signatures": type_sigs},
        "doc": {"method_javadoc": javadoc_b, "class_javadoc": javasrc.class_javadoc(src, q["simple_class"])},
        "javadoc_edited_by_fix": bool(javadoc_f is not None and javadoc_f.strip() != (javadoc_b or "").strip()),
        "call_sites": sites, "siblings": siblings,
        "impl_B": body_b,                 # judge-visible ONLY in ablation A5
        "_label_side": {"fixed_body": fixed_body},  # never copied into instance records
        "fields": [javasrc.signature_of(x) for x in cls_members if x.kind == "field"][:40],
    }
