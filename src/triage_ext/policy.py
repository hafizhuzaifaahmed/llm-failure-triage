"""Certificate rules that combine probe evidence with a base triage rule (D-134). Pure functions.

A base rule's label is PROGRAM_FAULT (keep) or TEST_FAULT (discard). Probe evidence can only act through two
certificates, each with one meaning:

  CK  certified keep      a regression-consistent flip exists: some small edit of the focal method makes the test pass
                          and breaks no sibling test, so the test's expectation is realisable by a nearby program.
  CD  decoupled discard   no mutant of the focal method changes the failure at all (>= MIN_MUTANTS compiled): the
                          failure does not depend on the method under test.

An instance without a usable ledger (excluded, or too few mutants) falls through to the base rule unchanged.
"""
from __future__ import annotations

PF, TF = "PROGRAM_FAULT", "TEST_FAULT"


def _usable(summary: dict | None) -> bool:
    return bool(summary) and not summary.get("excluded")


def certified_keep(base_label: str, summary: dict | None) -> str:
    if _usable(summary) and summary.get("rcf"):
        return PF
    return base_label


def decoupled_discard(base_label: str, summary: dict | None) -> str:
    if _usable(summary) and summary.get("decoupled"):
        return TF
    return base_label


def combined(base_label: str, summary: dict | None) -> str:
    """CK takes precedence over CD (they cannot both hold: a flip is a coupling)."""
    if _usable(summary) and summary.get("rcf"):
        return PF
    if _usable(summary) and summary.get("decoupled"):
        return TF
    return base_label


RULES = {"CK": certified_keep, "CD": decoupled_discard, "CK+CD": combined}
