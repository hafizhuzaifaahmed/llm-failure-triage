"""Evidence ledger for counterfactual program probes (D-134). Pure functions; no I/O beyond what callers pass in.

One ledger record per failing instance. Everything in it is derived from executions on the buggy version, so the
record is prediction-time evidence: it may be shown to a judge or used by a policy.
"""
from __future__ import annotations

import hashlib
import re

FLIP, SHIFT, SAME, ERR = "FLIP", "SHIFT", "SAME", "ERR"
MIN_MUTANTS = 10          # fewer compiled mutants than this: the decoupling flag is undefined
EXCLUSIONS = ("focal_not_located", "focal_recompile_failed", "test_compile_failed", "baseline_not_reproduced")

_HEX = re.compile(r"@[0-9a-f]{4,}")


def norm_message(msg: str) -> str:
    """Message with object hash codes removed, so two runs of one behaviour compare equal."""
    return _HEX.sub("@H", (msg or "").strip())[:2000]


def signature(run: dict) -> tuple:
    """(outcome type, exception class, failing test line): the study's failure signature (paper Section 3.3)."""
    return (run.get("outcome"), run.get("exception") or None, run.get("failing_test_line"))


def classify(baseline: dict, run: dict, rerun: dict | None = None) -> str:
    """Class of one mutant run against the baseline failure on the unmutated buggy version."""
    out = run.get("outcome")
    if out in ("timeout", "harness_error", None):
        return ERR
    if out == "pass":
        if rerun is None or rerun.get("outcome") != "pass":
            return ERR                      # a pass that does not repeat is not counted as a flip
        return FLIP
    if signature(run) != signature(baseline) or norm_message(run.get("message")) != norm_message(baseline.get("message")):
        return SHIFT
    return SAME


def summarise(mutants: list[dict]) -> dict:
    """Counts and the two flags the policy uses. `mutants` are ledger entries with `class` and, for flips, `rc`."""
    n = {k: sum(1 for m in mutants if m["class"] == k) for k in (FLIP, SHIFT, SAME, ERR)}
    compiled = len(mutants)
    scored = compiled - n[ERR]
    rcf = sum(1 for m in mutants if m["class"] == FLIP and m.get("rc") is True)
    return {
        "n_compiled": compiled, "n_flip": n[FLIP], "n_shift": n[SHIFT], "n_same": n[SAME], "n_err": n[ERR],
        "n_rcf": rcf,
        "flip": n[FLIP] > 0,
        "rcf": rcf > 0,                                           # certified-keep evidence
        "flip_without_rcf": n[FLIP] > 0 and rcf == 0,
        "coupled": (n[FLIP] + n[SHIFT]) > 0,
        "decoupled": compiled >= MIN_MUTANTS and (n[FLIP] + n[SHIFT]) == 0,   # decoupled-discard evidence
        "flip_fraction": n[FLIP] / scored if scored else None,
        "coupled_fraction": (n[FLIP] + n[SHIFT]) / scored if scored else None,
    }


def message_digest(msg: str) -> str:
    return hashlib.sha1(norm_message(msg).encode("utf-8", "replace")).hexdigest()[:12]
