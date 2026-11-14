"""Whole-method dependence probe engine (WDP spec version 2, section 3). Runs inside WSL; stdlib only.

For one focal method of a buggy checkout the engine compiles at most three whole-body replacements of that method
(X-THROW with an entry marker, and the X-RET bodies of its declared return type) into overlay class directories;
for each failing test of the method it runs the test on the identity overlay and on every variant overlay and
records what changed. The checkout is never modified: overlays and marker files live under the engine's scratch
directory and are removed per method.

Prediction-time boundary. The engine reads the buggy checkout through the registered engine's three whitelisted
metadata keys (`triage_ext.probe.load_meta`), the failing test's source and its stored buggy-version run. It has no
code path to the other version, to labels, to developer tests or to judge decisions;
`tests/extension/test_wdp.py` scans this file to keep it that way.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from triage.execution import ENV, JUNIT_JAR, JVM_FLAGS, _javac, _unesc, ensure_runner, failing_test_line
from triage_ext.ledger import classify, message_digest, signature
from triage_ext.probe import SCRATCH, SOURCE_LEVELS, compile_overlay, load_meta, locate, read_source

from . import interventions, screen

BASELINE_TIMEOUT_S = 30
VARIANT_TIMEOUT_S = 10
WDP_SCRATCH = SCRATCH / "wdp"
MARKER_ENV = "WDP_MARKER"


def run_test_env(fqcn: str, method: str, cp_front: str, meta: dict, timeout: int = VARIANT_TIMEOUT_S,
                 extra_env: dict | None = None) -> dict:
    """A copy of `triage_ext.probe.run_test` that differs only in merging `extra_env` into the environment."""
    cp = f"{cp_front}:{ensure_runner()}:{meta['cp.test']}:{JUNIT_JAR}"
    env = {**ENV, **(extra_env or {})}
    t0 = time.time()
    try:
        p = subprocess.run(["java", *JVM_FLAGS, "-cp", cp, "triage.runner.SingleTestRunner", fqcn, method],
                           capture_output=True, text=True, env=env, cwd=meta["workdir"], timeout=timeout)
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


def surfaced(run: dict) -> bool:
    """The X-THROW run's recorded exception is the probe's own Error (spec 2.3, consistency check only)."""
    return run.get("exception") == "java.lang.Error" and "__WDP__" in (run.get("message") or "")


class WdpProbe:
    """Variant overlays of one focal method, shared by every failing test of that method."""

    def __init__(self, focal_id: str, bug_name: str, rel_file: str, impl: str, meta: dict | None = None):
        self.focal_id, self.bug_name = focal_id, bug_name
        self.meta = meta if meta is not None else load_meta(bug_name)    # an injected meta: toy fixture only
        self.rel = rel_file[len(self.meta["dir.src.classes"]):].lstrip("/") if rel_file.startswith(
            self.meta["dir.src.classes"]) else rel_file
        self.dir = WDP_SCRATCH / hashlib.sha1(focal_id.encode()).hexdigest()[:16]
        self.exclusion = None
        self.level = None
        self.return_type = None
        self.variants: list[dict] = []          # {id, body, body_sha, compiled}
        self.overlays: dict[str, Path] = {}
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
        for level in SOURCE_LEVELS:
            if compile_overlay(self.src, self.enc, self.rel, self.meta, self.dir / "identity", level):
                self.level = level
                break
        else:
            self.exclusion = "focal_recompile_failed"
            return
        self.identity = self.dir / "identity" / "classes"
        self.return_type = interventions.return_type(self.method_text)
        self.variants = [{**v, "body_sha": interventions.body_sha(v["body"]), "compiled": False}
                         for v in interventions.variants(self.method_text)]

        def build(v: dict):
            out = self.dir / "v" / v["id"]
            text = self.src[:span[0]] + interventions.apply(self.method_text, v["body"]) + self.src[span[1]:]
            return v["id"], (out / "classes") if compile_overlay(text, self.enc, self.rel, self.meta, out,
                                                                 self.level) else None
        with ThreadPoolExecutor(len(self.variants)) as ex:
            for vid, classes in ex.map(build, self.variants):
                if classes is not None:
                    self.overlays[vid] = classes
        for v in self.variants:
            v["compiled"] = v["id"] in self.overlays

    # ---- one failing test -------------------------------------------------------------------------------------
    def probe(self, inst: dict, test_src: str, pkg: str, cls: str, stored_run: dict) -> dict:
        t0 = time.time()
        rec = {"instance_id": inst["instance_id"], "focal_id": self.focal_id, "method": inst["method"],
               "return_type": self.return_type, "source_level": self.level,
               "swallow_risk": screen.swallow_risk(test_src),                 # computed even if the test is excluded
               "entered": None, "surfaced": None,
               "variants": [{"id": v["id"], "body_sha": v["body_sha"], "compiled": v["compiled"], "class": None,
                             "outcome": None, "exception": None, "failing_test_line": None, "message_digest": None}
                            for v in self.variants],
               "baseline": None}
        if self.exclusion:
            return self._done(rec, self.exclusion, t0)
        tdir = self.dir / "t" / inst["instance_id"]
        if _javac(test_src, pkg, cls, self.meta, tdir):
            return self._done(rec, "test_compile_failed", t0)
        tcls = tdir / "classes"
        fqcn = f"{pkg}.{cls}" if pkg else cls
        base = run_test_env(fqcn, inst["method"], f"{self.identity}:{tcls}", self.meta, timeout=BASELINE_TIMEOUT_S)
        rec["baseline"] = {"outcome": base.get("outcome"), "exception": base.get("exception"),
                           "failing_test_line": base.get("failing_test_line"),
                           "message_digest": message_digest(base.get("message"))}
        if signature(base) != signature(stored_run) or base.get("outcome") == "pass":
            shutil.rmtree(tdir, ignore_errors=True)
            return self._done(rec, "baseline_not_reproduced", t0)

        def marker(vid: str, n: int) -> Path:
            p = tdir / f"marker_{vid}_{n}"
            if p.exists():
                raise RuntimeError(f"marker path exists before the run: {p}")
            return p

        def one(vid: str):
            front = f"{self.overlays[vid]}:{tcls}"
            is_throw = vid == interventions.X_THROW_ID
            m1 = marker(vid, 1) if is_throw else None
            run = run_test_env(fqcn, inst["method"], front, self.meta, VARIANT_TIMEOUT_S,
                               {MARKER_ENV: str(m1)} if is_throw else None)
            entered = m1.exists() if is_throw else None
            rerun = None
            if run.get("outcome") == "pass":
                m2 = marker(vid, 2) if is_throw else None
                rerun = run_test_env(fqcn, inst["method"], front, self.meta, VARIANT_TIMEOUT_S,
                                     {MARKER_ENV: str(m2)} if is_throw else None)
            return vid, run, rerun, entered

        compiled = [v["id"] for v in self.variants if v["compiled"]]
        with ThreadPoolExecutor(max(1, len(compiled))) as ex:
            results = {vid: (run, rerun, entered) for vid, run, rerun, entered in ex.map(one, compiled)}
        for v in rec["variants"]:
            if v["id"] not in results:
                continue
            run, rerun, entered = results[v["id"]]
            v.update({"class": classify(base, run, rerun), "outcome": run.get("outcome"),
                      "exception": run.get("exception"), "failing_test_line": run.get("failing_test_line"),
                      "message_digest": message_digest(run.get("message"))})
            if v["id"] == interventions.X_THROW_ID:
                rec["entered"] = bool(entered)
                rec["surfaced"] = surfaced(run)
        shutil.rmtree(tdir, ignore_errors=True)
        return self._done(rec, None, t0)

    @staticmethod
    def _done(rec: dict, exclusion: str | None, t0: float) -> dict:
        rec["excluded"] = exclusion
        rec["seconds"] = round(time.time() - t0, 2)
        return rec

    def cleanup(self):
        shutil.rmtree(self.dir, ignore_errors=True)
