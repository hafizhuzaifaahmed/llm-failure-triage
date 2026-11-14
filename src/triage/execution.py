"""Dual execution of generated tests on buggy (B) and fixed (F) versions — Phase 2 C2, C5-C7.

Runs inside WSL (Linux, Java 11, Defects4J 3.0.1). Stdlib only.

* Each Defects4J version is checked out and compiled once, into a native-filesystem work dir.
* A generated test class is compiled against BOTH versions; methods that fail to compile are pruned
  method-by-method for at most three passes (D-05). A method that compiles on only one version is NC.
* Every surviving method is run RUNS_PER_VERSION times per version, each in a fresh JVM, with a hard
  wall-clock timeout of TEST_TIMEOUT_S; a harness error is re-run once (ENV_RERUNS) before it counts.
* Locale/time zone follow Defects4J (TZ=America/Los_Angeles, en_US).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from . import config, javasrc
from .io_utils import sha256_text

D4J_HOME = Path(os.environ.get("D4J_HOME", Path.home() / "experiment" / "defects4j"))
PERL5LIB = os.environ.get("TRIAGE_PERL5LIB", str(Path.home() / "experiment" / "perl5" / "lib" / "perl5"))
WORK = Path(os.environ.get("TRIAGE_WORK", Path.home() / "triage_work"))
RUNNER_SRC = config.ROOT / "src" / "java"
RUNNER_BIN = WORK / "_runner"
JUNIT_JAR = D4J_HOME / "framework" / "projects" / "lib" / "junit-4.12-hamcrest-1.3.jar"

ENV = {
    **os.environ,
    "PATH": f"{D4J_HOME / 'framework' / 'bin'}:/usr/bin:/bin",
    "PERL5LIB": PERL5LIB,
    "TZ": "America/Los_Angeles",
    "LANG": "en_US.UTF-8",
    "LC_ALL": "C.UTF-8",
}
JVM_FLAGS = ["-Duser.language=en", "-Duser.country=US", "-Duser.timezone=America/Los_Angeles",
             "-Dfile.encoding=UTF-8", "-Xmx1g", "-XX:+UseSerialGC", "-XX:TieredStopAtLevel=1"]


def d4j(*args: str, cwd: Optional[Path] = None, timeout: int = 1800) -> str:
    p = subprocess.run(["defects4j", *args], cwd=cwd, env=ENV, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(f"defects4j {' '.join(args)} failed: {p.stderr[-2000:]}")
    return p.stdout


def ensure_runner() -> Path:
    marker = RUNNER_BIN / "triage" / "runner" / "SingleTestRunner.class"
    src = RUNNER_SRC / "triage" / "runner" / "SingleTestRunner.java"
    if not marker.exists() or marker.stat().st_mtime < src.stat().st_mtime:   # rebuild a stale runner (D-43)
        RUNNER_BIN.mkdir(parents=True, exist_ok=True)
        subprocess.run(["javac", "-source", "8", "-target", "8", "-nowarn", "-cp", str(JUNIT_JAR),
                        "-d", str(RUNNER_BIN), str(src)], check=True, capture_output=True, env=ENV)
    return RUNNER_BIN


def checkout_version(project: str, bug: str, version: str) -> Path:
    """Source checkout only (no compile). Idempotent via a marker file."""
    wd = WORK / f"{project}_{bug}" / version
    marker = wd.parent / f".checkout_{version}"
    if marker.exists():
        return wd
    if wd.exists():
        shutil.rmtree(wd)
    # a fresh checkout is uncompiled: any cached compile metadata for this version is now stale
    (wd.parent / f"meta_{version}.json").unlink(missing_ok=True)
    wd.parent.mkdir(parents=True, exist_ok=True)
    d4j("checkout", "-p", project, "-v", f"{bug}{version}", "-w", str(wd))
    marker.write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    return wd


def prepare_version(project: str, bug: str, version: str) -> dict:
    """Checkout + compile one version ('b' or 'f'); cache paths and classpath. Idempotent."""
    wd = WORK / f"{project}_{bug}" / version
    meta_path = wd.parent / f"meta_{version}.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        if (wd / meta["dir.bin.classes"]).is_dir():
            return meta
        meta_path.unlink()  # metadata claims a compiled version whose classes are gone: rebuild it
    checkout_version(project, bug, version)
    d4j("compile", "-w", str(wd))
    props = {k: d4j("export", "-p", k, "-w", str(wd)).strip()
             for k in ("cp.test", "dir.src.classes", "dir.src.tests", "dir.bin.classes", "dir.bin.tests",
                       "classes.modified", "tests.trigger")}
    meta = {"project": project, "bug": bug, "version": version, "workdir": str(wd), **props}
    meta_path.write_text(json.dumps(meta, indent=2))
    return meta


# ------------------------------------------------------------------------------------------
# compilation
# ------------------------------------------------------------------------------------------

_ERR = re.compile(r"^(.*?\.java):(\d+): error: (.*)$", re.M)


def _javac(src_text: str, pkg: str, cls: str, meta: dict, out_dir: Path) -> list[tuple[int, str]]:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    src_dir = out_dir / "src" / pkg.replace(".", "/")
    src_dir.mkdir(parents=True, exist_ok=True)
    f = src_dir / f"{cls}.java"
    f.write_text(src_text, encoding="utf-8")
    cp = f"{meta['cp.test']}:{JUNIT_JAR}"
    p = subprocess.run(["javac", "-nowarn", "-encoding", "UTF-8", "-Xmaxerrs", "1000", "-cp", cp,
                        "-d", str(out_dir / "classes"), str(f)], capture_output=True, text=True, env=ENV,
                       cwd=meta["workdir"], timeout=300)
    if p.returncode == 0:
        return []
    errs = [(int(m.group(2)), m.group(3)) for m in _ERR.finditer(p.stderr) if m.group(1).endswith(f"{cls}.java")]
    return errs or [(0, p.stderr[-500:])]


def compile_on_both(src_text: str, pkg: str, cls: str, meta_b: dict, meta_f: dict, out_root: Path) -> dict:
    """Prune non-compiling @Test methods (<= MAX_COMPILE_PRUNE_PASSES passes) until the class compiles on B and F.

    Returns {'source': final source, 'compiled': [...], 'nc_both': [...], 'nc_one_version': [...],
             'class_error': str|None, 'passes': n}.
    """
    try:
        all_tests = [m.name for m in javasrc.test_methods(src_text)]
    except ValueError as e:   # D-65: braces do not balance (truncated model output); javac cannot accept it either
        return {"source": src_text, "compiled": [], "nc_both": [], "nc_one_version": [],
                "class_error": f"unparseable class: {e}", "passes": 0}
    failed_on = {"b": set(), "f": set()}
    cur = src_text
    for p in range(config.MAX_COMPILE_PRUNE_PASSES + 1):
        errs = {"b": _javac(cur, pkg, cls, meta_b, out_root / "b"), "f": _javac(cur, pkg, cls, meta_f, out_root / "f")}
        if not errs["b"] and not errs["f"]:
            break
        if p == config.MAX_COMPILE_PRUNE_PASSES:
            return {"source": cur, "compiled": [], "nc_both": all_tests, "nc_one_version": [],
                    "class_error": "still not compiling after max prune passes", "passes": p}
        remove = set()
        for v in ("b", "f"):
            for line, msg in errs[v]:
                m = javasrc.member_at_line(cur, line) if line else None
                if m is None or not javasrc.is_test_method(m):
                    return {"source": cur, "compiled": [], "nc_both": all_tests, "nc_one_version": [],
                            "class_error": f"[{v}] line {line}: {msg}", "passes": p}
                failed_on[v].add(m.name)
                remove.add(m.name)
        cur = javasrc.remove_members(cur, remove)
        if not javasrc.test_methods(cur):
            break
    compiled = [m.name for m in javasrc.test_methods(cur)]
    one = sorted(failed_on["b"] ^ failed_on["f"])
    both = sorted(failed_on["b"] & failed_on["f"])
    return {"source": cur, "compiled": compiled, "nc_both": both, "nc_one_version": one,
            "class_error": None, "passes": p}


# ------------------------------------------------------------------------------------------
# execution
# ------------------------------------------------------------------------------------------

def _unesc(s: str) -> str:
    return re.sub(r"\\(\\|n|r)", lambda m: {"\\": "\\", "n": "\n", "r": "\r"}[m.group(1)], s)


def run_once(fqcn: str, method: str, test_classes: Path, meta: dict) -> dict:
    cp = f"{test_classes}:{ensure_runner()}:{meta['cp.test']}:{JUNIT_JAR}"
    t0 = time.time()
    try:
        p = subprocess.run(["java", *JVM_FLAGS, "-cp", cp, "triage.runner.SingleTestRunner", fqcn, method],
                           capture_output=True, text=True, env=ENV, cwd=meta["workdir"],
                           timeout=config.TEST_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return {"outcome": "timeout", "exception": "", "message": "", "trace": "", "duration_s": config.TEST_TIMEOUT_S}
    dur = round(time.time() - t0, 3)
    m = re.search(r"<<<TRIAGE-RESULT>>>\n(.*?)\n<<<END-TRIAGE-RESULT>>>", p.stdout, re.S)
    if not m:
        return {"outcome": "harness_error", "exception": "", "message": f"no result block; rc={p.returncode}",
                "trace": p.stderr[-2000:], "duration_s": dur}
    rec = {}
    for line in m.group(1).split("\n"):
        k, _, v = line.partition("=")
        rec[k] = _unesc(v)
    rec["duration_s"] = dur
    return rec


def failing_test_line(trace: str, fqcn: str) -> Optional[int]:
    simple = fqcn.rsplit(".", 1)[-1]
    for m in re.finditer(rf"at {re.escape(fqcn)}\.[\w$<>]+\({re.escape(simple)}\.java:(\d+)\)", trace or ""):
        return int(m.group(1))
    return None


def run_method(fqcn: str, method: str, test_classes: Path, meta: dict) -> list[dict]:
    runs = []
    for _ in range(config.RUNS_PER_VERSION):
        r = run_once(fqcn, method, test_classes, meta)
        if r["outcome"] == "harness_error":
            for _ in range(config.ENV_RERUNS):
                r2 = run_once(fqcn, method, test_classes, meta)
                r2["rerun_of_harness_error"] = True
                r = r2
                if r["outcome"] != "harness_error":
                    break
        r["failing_test_line"] = failing_test_line(r.get("trace", ""), fqcn)
        runs.append(r)
    return runs


def execute_candidate(cand: dict, meta_b: dict, meta_f: dict) -> dict:
    """cand: {'candidate_id','package','class_name','source'} for one generated test class.

    Each surviving @Test method is compiled ALONE in its own class copy, so a sibling test can never
    influence it (fixtures and helpers are kept). Returns the raw execution record (immutable once stored).
    """
    pkg, cls = cand["package"], cand["class_name"]
    out_root = WORK / "_exec" / cand["candidate_id"]
    comp = compile_on_both(cand["source"], pkg, cls, meta_b, meta_f, out_root / "all")
    methods = []
    for name in comp["compiled"]:
        single = javasrc.keep_only_test(comp["source"], name)
        mdir = out_root / name
        eb = _javac(single, pkg, cls, meta_b, mdir / "b")
        ef = _javac(single, pkg, cls, meta_f, mdir / "f")
        rec = {"method": name, "source_class": single, "compile_b": not eb, "compile_f": not ef}
        if eb or ef:
            rec["compile_errors"] = {"b": eb[:3], "f": ef[:3]}
            methods.append(rec)
            continue
        fq = f"{pkg}.{cls}" if pkg else cls
        rec["runs_b"] = run_method(fq, name, mdir / "b" / "classes", meta_b)
        rec["runs_f"] = run_method(fq, name, mdir / "f" / "classes", meta_f)
        methods.append(rec)
    shutil.rmtree(out_root, ignore_errors=True)
    return {"candidate_id": cand["candidate_id"], "source_sha256": sha256_text(cand["source"]),
            "compilation": {k: v for k, v in comp.items() if k != "source"}, "methods": methods,
            "env": {"tz": ENV["TZ"], "jvm_flags": JVM_FLAGS, "timeout_s": config.TEST_TIMEOUT_S,
                    "runs_per_version": config.RUNS_PER_VERSION}}


# ------------------------------------------------------------------------------------------
# coverage of the focal method by passing generated tests (G-selection criterion 3; reported)
# ------------------------------------------------------------------------------------------

def parse_cobertura(xml_text: str, class_name: str, line_lo: int, line_hi: int) -> dict:
    """Line and branch coverage of lines line_lo..line_hi of `class_name` in a Cobertura coverage.xml."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_text)
    lines = {}
    for c in root.iter("class"):
        if c.get("name") != class_name:
            continue
        for ln in c.iter("line"):
            n = int(ln.get("number"))
            if line_lo <= n <= line_hi:
                hits = int(ln.get("hits", "0"))
                cov, tot = 0, 0
                if ln.get("branch") == "true":
                    m = re.search(r"\((\d+)/(\d+)\)", ln.get("condition-coverage", ""))
                    if m:
                        cov, tot = int(m.group(1)), int(m.group(2))
                prev = lines.get(n, (0, 0, 0))
                lines[n] = (max(prev[0], hits), max(prev[1], cov), max(prev[2], tot))
    lt = len(lines)
    lc = sum(1 for h, _, _ in lines.values() if h > 0)
    bt = sum(t for _, _, t in lines.values())
    bc = sum(c for _, c, _ in lines.values())
    return {"lines_total": lt, "lines_covered": lc, "line_rate": lc / lt if lt else None,
            "branches_total": bt, "branches_covered": bc, "branch_rate": bc / bt if bt else None}


def focal_coverage(meta_f: dict, test_source: str, pkg: str, cls: str, focal_class: str,
                   focal_file_rel: str, line_lo: int, line_hi: int, tag: str) -> dict:
    """Run `defects4j coverage` on a scratch copy of F for ONE generated test class, passed as an external test
    suite archive (`-s`, so no developer-written test runs) with the focal class instrumented explicitly (`-i`).
    `-t` cannot be used: it takes a single Class::method."""
    base = WORK / "_cov" / tag
    if base.exists():
        shutil.rmtree(base)
    scratch, suite = base / "f", base / "suite"
    shutil.copytree(meta_f["workdir"], scratch, symlinks=True)
    (suite / pkg.replace(".", "/")).mkdir(parents=True, exist_ok=True)
    (suite / pkg.replace(".", "/") / f"{cls}.java").write_text(test_source, encoding="utf-8")
    archive = base / "gen-suite.tar.bz2"
    subprocess.run(["tar", "-cjf", str(archive), "-C", str(suite), "."], check=True, capture_output=True)
    inst = base / "instrument.txt"
    inst.write_text(focal_class + chr(10), encoding="utf-8")
    try:
        d4j("coverage", "-w", str(scratch), "-s", str(archive), "-i", str(inst), timeout=1800)
        xml_text = (scratch / "coverage.xml").read_text(encoding="utf-8", errors="replace")
        return {"status": "ok", **parse_cobertura(xml_text, focal_class, line_lo, line_hi)}
    except Exception as e:
        return {"status": "failed", "error": str(e)[-300:]}
    finally:
        shutil.rmtree(base, ignore_errors=True)
