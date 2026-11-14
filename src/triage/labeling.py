"""Ground-truth labeller (Phase 2 Section 3.4, Table 6). Never imports or calls any LLM module.

sigma(t, V) = (outcome type, exception class, test line at which the failure surfaced).
An outcome on a version is deterministic iff all runs on that version share the same sigma.
Messages are excluded from sigma because they may legitimately differ between B and F.

Precedence of the rules (D-06):
  NC  >  TIMEOUT  >  ENV  >  FLAKY  >  PASS / MISGUIDED / PF / TF / AMB
"""
from __future__ import annotations

from typing import Optional

PF, TF, AMB = "PF", "TF", "AMB"
EXCLUDED = ("NC", "TIMEOUT", "ENV", "FLAKY", "PASS", "MISGUIDED")
ALL_LABELS = (PF, TF, AMB) + EXCLUDED
FAIL_OUTCOMES = ("assertion_failure", "exception")


def sigma(run: dict) -> tuple:
    if run["outcome"] == "pass":
        return ("pass", None, None)
    return (run["outcome"], run.get("exception") or None, run.get("failing_test_line"))


def _deterministic(runs: list[dict]) -> Optional[tuple]:
    sigs = {sigma(r) for r in runs}
    return sigs.pop() if len(sigs) == 1 else None


def label(method_rec: dict) -> dict:
    """method_rec: one entry of execution.execute_candidate()['methods']."""
    if not method_rec.get("compile_b") or not method_rec.get("compile_f"):
        return {"label": "NC", "reason": "does not compile on both versions"}
    rb, rf = method_rec["runs_b"], method_rec["runs_f"]
    outs = [r["outcome"] for r in rb + rf]
    if "timeout" in outs:
        return {"label": "TIMEOUT", "reason": "a run exceeded the per-test timeout"}
    if "harness_error" in outs:
        return {"label": "ENV", "reason": "harness/environment error persisted after re-run"}
    sb, sf = _deterministic(rb), _deterministic(rf)
    if sb is None or sf is None:
        return {"label": "FLAKY", "reason": f"non-deterministic on {'B' if sb is None else 'F'}",
                "sigma_B": None if sb is None else list(sb), "sigma_F": None if sf is None else list(sf)}
    b_fail, f_fail = sb[0] in FAIL_OUTCOMES, sf[0] in FAIL_OUTCOMES
    out = {"sigma_B": list(sb), "sigma_F": list(sf)}
    if not b_fail and not f_fail:
        return {"label": "PASS", "reason": "passes on B and F", **out}
    if not b_fail and f_fail:
        return {"label": "MISGUIDED", "reason": "passes on B, fails on F (asserts the buggy behaviour)", **out}
    if b_fail and not f_fail:
        return {"label": PF, "reason": "fails deterministically on B, passes deterministically on F", **out}
    if sb == sf:
        return {"label": TF, "reason": "fails on B and F with identical failure signatures", **out}
    return {"label": AMB, "reason": "fails on B and F with different failure signatures", **out}


def is_triage_instance(lab: str) -> bool:
    """Instances that enter the judging pipeline: every deterministic failure on B (PF, TF, AMB).
    AMB instances are judged so the sensitivity analysis can rescore them, but are excluded from the
    primary analysis."""
    return lab in (PF, TF, AMB)
