"""Counterfactual program probe engine (D-134). Runs inside WSL next to the Defects4J checkouts; stdlib only.

For one focal method of a buggy checkout the engine compiles first-order mutants of that method into overlay class
directories; for each failing test of that method it runs the test against every overlay and records what changed.
The checkout itself is never modified: mutants live under the scratch directory and reach the JVM only through the
front of the classpath.

Prediction-time boundary. The engine reads the buggy checkout through three whitelisted metadata keys, the failing
test's source and its stored buggy-version runs. It has no code path to the other version, to labels or to developer
tests; `tests/extension/test_boundary.py` scans this file to keep it that way.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from triage import javasrc
from triage.execution import ENV, JUNIT_JAR, JVM_FLAGS, WORK, _javac, _unesc, ensure_runner, failing_test_line

from . import ledger, mutate

META_KEYS = ("workdir", "cp.test", "dir.src.classes")     # the only checkout metadata the engine may read
PROBE_TIMEOUT_S = 10
MAX_SIBLINGS = 30
WORKERS = int(os.environ.get("PROBE_WORKERS", "12"))
SCRATCH = WORK / "_probe"
SOURCE_LEVELS = (None, "8", "7", "6")                      # tried in order until the unmutated class compiles
CALLEE_DEPTH = 2                                           # same-class callees of the focal method, transitively
_KEYWORDS = {"if", "for", "while", "switch", "catch", "return", "new", "super", "this", "synchronized", "assert"}


def callee_regions(src: str, focal_class: str, focal_span: tuple[int, int], depth: int = CALLEE_DEPTH) -> list[dict]:
    """Bodies of same-class methods the focal method calls by simple name, transitively to `depth` (D-135).

    Purely syntactic: a name followed by '(' that matches a method declared in the focal class. Overloads are all
    included. Returns [{name, start, end, tier}] in source order, never overlapping the focal method.
    """
    simple = re.split(r"[.$]", focal_class)[-1]
    try:
        mem = [m for m in javasrc.members(src, simple) if m.kind in ("method", "constructor") and "{" in m.text(src)]
    except (ValueError, IndexError):
        return []
    by_name: dict[str, list] = {}
    for m in mem:
        by_name.setdefault(m.name, []).append(m)

    def calls(text: str) -> set[str]:
        toks = [t for t in mutate.tokenize(text) if t.kind not in ("ws", "comment")]
        return {t.text for k, t in enumerate(toks[:-1]) if t.kind == "id" and toks[k + 1].text == "("
                and t.text not in _KEYWORDS and t.text in by_name}

    chosen: dict[int, dict] = {}
    frontier = calls(src[focal_span[0]:focal_span[1]])
    for tier in range(1, depth + 1):
        nxt: set[str] = set()
        for name in sorted(frontier):
            for m in by_name[name]:
                if m.start in chosen or not (m.end <= focal_span[0] or m.start >= focal_span[1]):
                    continue
                chosen[m.start] = {"name": m.name, "start": m.start, "end": m.end, "tier": tier}
                nxt |= calls(m.text(src))
        frontier = nxt
    return [chosen[k] for k in sorted(chosen)]


def load_meta(bug_name: str) -> dict:
    project, bug = bug_name.rsplit("_", 1)
    raw = json.loads((WORK / f"{project}_{bug}" / "meta_b.json").read_text())
    meta = {k: raw[k] for k in META_KEYS}
    if not meta["workdir"].rstrip("/").endswith("/b"):
        raise RuntimeError(f"not a buggy checkout: {meta['workdir']}")
    return meta


def read_source(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    for enc in ("utf-8", "iso-8859-1"):
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"cannot decode {path}")


def locate(src: str, impl: str) -> tuple[int, int] | None:
    """Offsets of the focal method text in the class source; None unless it occurs exactly once."""
    for cand in (impl, impl.replace("\r\n", "\n"), impl.replace("\n", "\r\n")):
        if cand and src.count(cand) == 1:
            s = src.index(cand)
            return s, s + len(cand)
    return None


def compile_overlay(src_text: str, enc: str, rel_file: str, meta: dict, out_dir: Path, level: str | None) -> bool:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    f = out_dir / "src" / rel_file
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(src_text.encode(enc))
    (out_dir / "classes").mkdir(parents=True, exist_ok=True)
    cmd = ["javac", "-nowarn", "-proc:none", "-encoding", enc, "-cp", meta["cp.test"], "-d", str(out_dir / "classes")]
    if level:
        cmd += ["-source", level, "-target", level]
    try:
        p = subprocess.run(cmd + [str(f)], capture_output=True, text=True, env=ENV, cwd=meta["workdir"], timeout=300)
    except subprocess.TimeoutExpired:
        return False
    return p.returncode == 0


def run_test(fqcn: str, method: str, cp_front: str, meta: dict, timeout: int = PROBE_TIMEOUT_S) -> dict:
    """One fresh-JVM run of one test method with `cp_front` ahead of the checkout's classpath."""
    cp = f"{cp_front}:{ensure_runner()}:{meta['cp.test']}:{JUNIT_JAR}"
    t0 = time.time()
    try:
        p = subprocess.run(["java", *JVM_FLAGS, "-cp", cp, "triage.runner.SingleTestRunner", fqcn, method],
                           capture_output=True, text=True, env=ENV, cwd=meta["workdir"], timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"outcome": "timeout", "exception": "", "message": "", "duration_s": timeout, "failing_test_line": None}
    m = re.search(r"<<<TRIAGE-RESULT>>>\n(.*?)\n<<<END-TRIAGE-RESULT>>>", p.stdout, re.S)
    if not m:
        return {"outcome": "harness_error", "exception": "", "message": f"no result block; rc={p.returncode}",
                "duration_s": round(time.time() - t0, 3), "failing_test_line": None}
    rec = {}
    for line in m.group(1).split("\n"):
        k, _, v = line.partition("=")
        rec[k] = _unesc(v)
    rec["failing_test_line"] = failing_test_line(rec.pop("trace", ""), fqcn)
    rec["duration_s"] = round(time.time() - t0, 3)
    return rec


class FocalProbe:
    """Mutant overlays of one focal method, shared by every failing test of that method."""

    def __init__(self, focal_id: str, bug_name: str, rel_file: str, impl: str, focal_class: str = ""):
        self.focal_id, self.bug_name = focal_id, bug_name
        self.meta = load_meta(bug_name)
        self.rel = rel_file[len(self.meta["dir.src.classes"]):].lstrip("/") if rel_file.startswith(
            self.meta["dir.src.classes"]) else rel_file
        self.dir = SCRATCH / hashlib.sha1(focal_id.encode()).hexdigest()[:16]
        self.exclusion = None
        self.overlays: dict[str, Path] = {}
        self.mutants: list[dict] = []          # file-level edits: mid, tier, region, start, end, replacement, m
        self.n_generated = 0
        self.n_generated_callee = 0
        self._siblings_ready: dict[int, Path | None] = {}
        src_path = Path(self.meta["workdir"]) / rel_file
        if not src_path.exists():
            self.exclusion = "focal_not_located"
            return
        self.src, self.enc = read_source(src_path)
        span = locate(self.src, impl)
        if span is None:
            self.exclusion = "focal_not_located"
            return
        self.span = span
        self.method_text = self.src[span[0]:span[1]]
        self.level = None
        for level in SOURCE_LEVELS:
            if compile_overlay(self.src, self.enc, self.rel, self.meta, self.dir / "identity", level):
                self.level = level
                break
        else:
            self.exclusion = "focal_recompile_failed"
            return
        self.identity = self.dir / "identity" / "classes"
        focal, self.n_generated = mutate.sample_mutants(self.method_text, focal_id)
        self.mutants = [self._edit(m, 0, "<focal>", span[0]) for m in focal]
        room = mutate.MAX_MUTANTS - len(self.mutants)
        pool = []
        for k, reg in enumerate(callee_regions(self.src, focal_class, span)):
            for m in mutate.all_mutants(self.src[reg["start"]:reg["end"]]):
                pool.append(self._edit(m, reg["tier"], reg["name"], reg["start"], prefix=f"c{k}:"))
        self.n_generated_callee = len(pool)
        if room > 0 and pool:
            if len(pool) > room:                 # focal-method mutants first; the rest by a seeded sample
                rng = random.Random(int(hashlib.sha256((focal_id + "|callees").encode()).hexdigest()[:16], 16))
                pool = [pool[i] for i in sorted(rng.sample(range(len(pool)), room))]
            self.mutants += pool

        def build(e: dict):
            out = self.dir / "m" / re.sub(r"[^\w]", "_", e["mid"])
            text = self.src[:e["start"]] + e["replacement"] + self.src[e["end"]:]
            return e["mid"], (out / "classes") if compile_overlay(text, self.enc, self.rel, self.meta, out, self.level) else None
        with ThreadPoolExecutor(WORKERS) as ex:
            for mid, classes in ex.map(build, self.mutants):
                if classes is not None:
                    self.overlays[mid] = classes

    @staticmethod
    def _edit(m: mutate.Mutant, tier: int, region: str, offset: int, prefix: str = "") -> dict:
        return {"mid": prefix + m.mid, "tier": tier, "region": region, "start": offset + m.start,
                "end": offset + m.end, "replacement": m.replacement, "m": m}

    # ---- one failing test -------------------------------------------------------------------------------------
    def probe(self, inst: dict, test_src: str, pkg: str, cls: str, stored_run: dict, siblings: list[dict]) -> dict:
        t0 = time.time()
        rec = {"instance_id": inst["instance_id"], "focal_id": self.focal_id, "method": inst["method"],
               "n_generated": self.n_generated, "n_generated_callee": self.n_generated_callee,
               "n_sampled": len(self.mutants), "n_compiled": len(self.overlays),
               "source_level": getattr(self, "level", None), "mutants": []}
        if self.exclusion:
            return self._done(rec, self.exclusion, t0)
        tdir = self.dir / "t" / inst["instance_id"]
        if _javac(test_src, pkg, cls, self.meta, tdir):
            return self._done(rec, "test_compile_failed", t0)
        tcls = tdir / "classes"
        fqcn = f"{pkg}.{cls}" if pkg else cls
        base = run_test(fqcn, inst["method"], f"{self.identity}:{tcls}", self.meta, timeout=30)
        rec["baseline"] = {"outcome": base.get("outcome"), "exception": base.get("exception"),
                           "failing_test_line": base.get("failing_test_line"),
                           "message_digest": ledger.message_digest(base.get("message"))}
        if ledger.signature(base) != ledger.signature(stored_run) or base.get("outcome") == "pass":
            return self._done(rec, "baseline_not_reproduced", t0)
        by_mid = {e["mid"]: e for e in self.mutants}

        def one(mid: str):
            front = f"{self.overlays[mid]}:{tcls}"
            run = run_test(fqcn, inst["method"], front, self.meta)
            rerun = run_test(fqcn, inst["method"], front, self.meta) if run.get("outcome") == "pass" else None
            e = by_mid[mid]
            m = e["m"]
            return {"mid": mid, "tier": e["tier"], "region": e["region"], "operator": m.operator, "line": m.line,
                    "original": m.original[:80],
                    "replacement": m.replacement[:80], "class": ledger.classify(base, run, rerun),
                    "outcome": run.get("outcome"), "exception": run.get("exception"),
                    "failing_test_line": run.get("failing_test_line"),
                    "message_digest": ledger.message_digest(run.get("message"))}
        with ThreadPoolExecutor(WORKERS) as ex:
            rec["mutants"] = list(ex.map(one, sorted(self.overlays)))
        flips = [m for m in rec["mutants"] if m["class"] == ledger.FLIP]
        if flips:
            chosen = self._choose_siblings(siblings, inst["instance_id"])
            for m in flips:
                results = self._run_siblings(chosen, self.overlays[m["mid"]])
                m["siblings_run"] = len(results)
                m["siblings_failed"] = sum(1 for r in results if r != "pass")
                m["rc"] = m["siblings_failed"] == 0
                m["rc_vacuous"] = len(results) == 0
        shutil.rmtree(tdir, ignore_errors=True)
        return self._done(rec, None, t0)

    def _done(self, rec: dict, exclusion: str | None, t0: float) -> dict:
        rec["excluded"] = exclusion
        rec["summary"] = {"excluded": exclusion} if exclusion else {**ledger.summarise(rec["mutants"]), "excluded": None}
        if not exclusion:                      # sensitivity view: mutants of the focal method body only (D-134 scope)
            rec["summary_focal_only"] = ledger.summarise([m for m in rec["mutants"] if m.get("tier") == 0])
        rec["seconds"] = round(time.time() - t0, 2)
        return rec

    def _choose_siblings(self, siblings: list[dict], instance_id: str) -> list[dict]:
        if len(siblings) <= MAX_SIBLINGS:
            return siblings
        rng = random.Random(int(hashlib.sha256((self.focal_id + "|siblings").encode()).hexdigest()[:16], 16))
        return [siblings[i] for i in sorted(rng.sample(range(len(siblings)), MAX_SIBLINGS))]

    def _run_siblings(self, chosen: list[dict], overlay: Path) -> list[str]:
        def one(k_s):
            k, s = k_s
            if k not in self._siblings_ready:
                sdir = self.dir / "s" / str(k)
                ok = not _javac(s["source_class"], s["package"], s["class_name"], self.meta, sdir)
                self._siblings_ready[k] = (sdir / "classes") if ok else None
            scls = self._siblings_ready[k]
            if scls is None:
                return None                   # a sibling that does not compile alone is not evidence either way
            fq = f"{s['package']}.{s['class_name']}" if s["package"] else s["class_name"]
            return run_test(fq, s["method"], f"{overlay}:{scls}", self.meta).get("outcome")
        with ThreadPoolExecutor(WORKERS) as ex:
            return [r for r in ex.map(one, list(enumerate(chosen))) if r is not None]

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)
