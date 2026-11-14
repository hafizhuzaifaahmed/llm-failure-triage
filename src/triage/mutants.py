"""D2 seeded faults (Phase 2 Section 3.2, Table 4). Runs inside WSL; stdlib only.

For each held-out (test-split) focal method:
  1. copy the compiled FIXED checkout F to a scratch dir and run Major through `defects4j mutation` with the
     eight approved operators (AOR LOR SOR COR ROR ORU LVR STD), instrumenting only the focal class.
     Pass 1 uses a single trigger test to obtain mutants.log quickly.
  2. keep mutants whose enclosing method (Major's `Class@method(params)`) is the focal method.
  3. pass 2 runs the relevant developer tests with every other mutant excluded (-e) -> kill.csv.
     A mutant counts as killed only if its status is FAIL or EXC (TIME is treated as not killed, so a
     timeout can never stand in for an observable fault).
  4. choose up to MAX_MUTANTS_PER_FOCAL killed mutants with a seeded RNG.
  5. materialise each as source: Major logs the character offset of the mutated expression, so the
     replacement is exact; the result must compile and at least one relevant developer test must fail on it.
B for D2 = F + one mutant; F is unchanged.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from . import config
from .execution import ENV, WORK, d4j, prepare_version

KILLED = ("FAIL", "EXC")
VERIFY_TIMEOUT_S = 900   # wall clock for `defects4j test -r` on one materialised mutant
_LOG = re.compile(r"^(\d+):(\w+):([^:]*):([^:]*):(.+?)@([^:(]+)\(([^)]*)\):(\d+):(\d+):(.*) \|==> (.*)$")


def parse_mutants_log(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        m = _LOG.match(line)
        if not m:
            continue
        out.append({"id": int(m.group(1)), "operator": m.group(2), "from": m.group(3), "to": m.group(4),
                    "class": m.group(5), "method": m.group(6),
                    "params": [p.strip() for p in m.group(7).split(",") if p.strip()],
                    "line": int(m.group(8)), "offset": int(m.group(9)), "original": m.group(10),
                    "mutated": m.group(11)})
    return out


def _simple(t: str) -> str:
    return re.sub(r"<.*>", "", t).replace("...", "[]").split(".")[-1].strip()


def in_focal(mut: dict, focal_class: str, method: str, param_types: list[str]) -> bool:
    cls = mut["class"].replace("$", ".")
    if cls != focal_class.replace("$", ".") or mut["method"] != method:
        return False
    return [_simple(p) for p in mut["params"]] == [_simple(p) for p in param_types]


def parse_kill_csv(text: str) -> dict[int, str]:
    out = {}
    for line in text.splitlines()[1:]:
        if "," in line:
            i, s = line.split(",", 1)
            out[int(i)] = s.strip()
    return out


def materialise(src: str, mut: dict, window: int = 2000) -> Optional[str]:
    """Apply one Major mutant to source text. None if it cannot be placed unambiguously.

    Major's logged offset points at the expression's key token (e.g. the `==` of `a == b`, the `(` of a call),
    not at the expression's start. The rule is therefore: find every whitespace-insensitive occurrence of the
    logged original fragment near the offset and accept it only if exactly one occurrence spans the offset.
    """
    orig, new, off = mut["original"], mut["mutated"], mut["offset"]
    if new == "<NO-OP>":
        new = ";" if orig.rstrip().endswith((";", "}")) else ""
    pat = re.compile(r"\s*".join(re.escape(tok) for tok in orig.split()))
    lo = max(0, off - window)
    spans = [m for m in pat.finditer(src, lo, min(len(src), off + window)) if m.start() <= off < max(m.end(), m.start() + 1)]
    if len(spans) != 1:
        return None
    m = spans[0]
    return src[:m.start()] + new + src[m.end():]


def read_src(path: Path) -> tuple[str, str]:
    """Read source without newline translation (Major's offsets count CR characters). UTF-8 if the file is
    valid UTF-8, otherwise Latin-1, which round-trips every byte unchanged."""
    raw = Path(path).read_bytes()
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        return raw.decode("latin-1"), "latin-1"


def write_src(path: Path, text: str, encoding: str) -> None:
    Path(path).write_bytes(text.encode(encoding))


def _write(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n")
    return path


def seeded_order(focal_id: str, ids: list[int]) -> list[int]:
    """Deterministic random permutation of the killed mutant ids (candidates are tried in this order)."""
    seed = int(hashlib.sha256(f"{config.SEED_MUTANTS}|{focal_id}".encode()).hexdigest()[:12], 16)
    ids = sorted(ids)
    random.Random(seed).shuffle(ids)
    return ids


def build_for_focal(rec: dict, ctx: dict, info: dict) -> dict:
    """rec: frame record; ctx: B-side context (for focal class / file); info: buggy_fix_info.json."""
    project, bug = rec["project"], rec["bug"]
    meta_f = prepare_version(project, bug, "f")
    fdir = Path(meta_f["workdir"])
    tag = hashlib.sha256(rec["focal_id"].encode()).hexdigest()[:10]
    scratch = WORK / f"{project}_{bug}" / f"mut_{tag}"
    if scratch.exists():
        shutil.rmtree(scratch)
    shutil.copytree(fdir, scratch, symlinks=True)
    outer = rec["class"].split("$")[0]
    cls_file = _write(scratch / ".triage_classes.txt", [outer])
    ops_file = _write(scratch / ".triage_ops.txt", config.MUTATION_OPERATORS)
    trig = [t.strip() for t in re.split(r"[\n;,]", meta_f.get("tests.trigger", "")) if t.strip()]
    result = {"focal_id": rec["focal_id"], "project": project, "bug": bug, "status": None}
    try:
        d4j("mutation", "-w", str(scratch), "-i", str(cls_file), "-m", str(ops_file), "-t", trig[0], timeout=3600)
    except Exception as e:
        log = scratch / "mutants.log"
        if "Cannot mutate project" in str(e) and (not log.exists() or not log.read_text().strip()):
            # Defects4J treats "0 mutants generated" as a failure; none of the 8 operators applies to the class
            return {**result, "status": "NO_CLASS_MUTANTS", "n_mutants_class": 0}
        return {**result, "status": "MUTATION_FAILED", "error": str(e)[-500:]}
    muts = parse_mutants_log((scratch / "mutants.log").read_text(errors="replace"))
    focal = [m for m in muts if in_focal(m, rec["class"], rec["method"], rec["param_types"])]
    result.update(n_mutants_class=len(muts), n_mutants_focal=len(focal),
                  focal_by_operator={op: sum(m["operator"] == op for m in focal) for op in config.MUTATION_OPERATORS})
    if not focal:
        return {**result, "status": "NO_FOCAL_MUTANTS"}
    focal_ids = {m["id"] for m in focal}
    excl = _write(scratch / ".triage_exclude.txt", [str(m["id"]) for m in muts if m["id"] not in focal_ids])
    try:
        d4j("mutation", "-w", str(scratch), "-i", str(cls_file), "-m", str(ops_file), "-e", str(excl), timeout=7200)
    except Exception as e:
        return {**result, "status": "ANALYSIS_FAILED", "error": str(e)[-500:]}
    kill = parse_kill_csv((scratch / "kill.csv").read_text())
    killed = [m["id"] for m in focal if kill.get(m["id"]) in KILLED]
    result["kill_status_counts"] = {s: sum(kill.get(m["id"]) == s for m in focal) for s in ("FAIL", "EXC", "TIME", "LIVE", "UNCOV")}
    result["n_killed"] = len(killed)
    if not killed:
        return {**result, "status": "NONE_KILLED"}
    src_rel = rec["file"]
    f_src, enc = read_src(fdir / src_rel)
    result["placeable_focal"] = sum(materialise(f_src, m) is not None for m in focal)
    result["placeable_killed"] = sum(materialise(f_src, by) is not None for by in focal if by["id"] in set(killed))
    chosen, attempts = [], []
    by_id = {m["id"]: m for m in focal}
    # try mutants in seeded order until MAX_MUTANTS_PER_FOCAL are materialised and verified
    order = seeded_order(rec["focal_id"], killed)
    for mid in order:
        if len(chosen) >= config.MAX_MUTANTS_PER_FOCAL:
            break
        m = by_id[mid]
        new_src = materialise(f_src, m)
        att = {"mutant_id": mid, "operator": m["operator"], "line": m["line"], "original": m["original"],
               "mutated": m["mutated"], "kill_status": kill.get(mid)}
        if new_src is None:
            attempts.append({**att, "verdict": "NOT_PLACEABLE"})
            continue
        vdir = WORK / f"{project}_{bug}" / f"m{mid}"
        if vdir.exists():
            shutil.rmtree(vdir)
        shutil.copytree(fdir, vdir, symlinks=True)
        write_src(vdir / src_rel, new_src, enc)
        try:
            d4j("compile", "-w", str(vdir))
        except Exception:
            attempts.append({**att, "verdict": "DOES_NOT_COMPILE"})
            shutil.rmtree(vdir, ignore_errors=True)
            continue
        try:
            p = subprocess.run(["defects4j", "test", "-r", "-w", str(vdir)], env=ENV, capture_output=True, text=True,
                               timeout=VERIFY_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            # a mutant can make a developer test loop; that is not a verified observable failure
            attempts.append({**att, "verdict": "VERIFY_TIMEOUT"})
            subprocess.run(["pkill", "-f", str(vdir)], capture_output=True)
            shutil.rmtree(vdir, ignore_errors=True)
            continue
        n_fail = int(re.search(r"Failing tests:\s*(\d+)", p.stdout).group(1)) if "Failing tests" in p.stdout else -1
        if n_fail <= 0:
            attempts.append({**att, "verdict": "NOT_KILLED_ON_SOURCE", "failing_tests": n_fail})
            shutil.rmtree(vdir, ignore_errors=True)
            continue
        props = {k: d4j("export", "-p", k, "-w", str(vdir)).strip() for k in ("cp.test", "dir.src.classes", "dir.src.tests")}
        meta = {"project": project, "bug": bug, "version": f"m{mid}", "workdir": str(vdir), "mutant_of": "f", **props}
        (vdir.parent / f"meta_m{mid}.json").write_text(json.dumps(meta, indent=2))
        diff = {"file": src_rel, "offset": m["offset"], "original": m["original"], "mutated": m["mutated"]}
        from .frame import locate_method, parse_qualified
        fm = locate_method(new_src, parse_qualified(rec["qualified"]))
        body = new_src[fm.start:fm.end] if fm else None
        chosen.append({**att, "verdict": "VERIFIED", "failing_dev_tests": n_fail, "workdir": str(vdir), "diff": diff,
                       "mutated_focal_body": body,
                       "mutated_source_sha256": hashlib.sha256(new_src.encode()).hexdigest()})
        attempts.append(chosen[-1])
    shutil.rmtree(scratch, ignore_errors=True)
    return {**result, "status": "OK" if chosen else "NONE_VERIFIED", "chosen": chosen, "attempts": attempts}
