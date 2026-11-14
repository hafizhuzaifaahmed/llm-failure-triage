"""Dependence levels and certificates (WDP spec version 4, sections 2.3 to 2.5). Pure functions.

`level(wdp_record, first_order_summary)` applies the table of section 2.4, first matching row wins, and returns
(level, nd_reason) with nd_reason None unless the level is ND. The record is the engine's ledger record (None when
there is no record); the first-order summary is the `summary` of the registered engine's ledger record for the same
test (None when there is none).

Validity comes first: a missing record is ND `excluded:no_record` and a malformed one (the nine rules of section
2.3, in order) is ND `malformed:<code>`, whatever the first-order ledger says. FS needs a present, valid record and
a first-order `coupled` that is exactly true; U, RI and WS need a first-order summary that is SILENT. Every
level-deciding comparison is exact. The function never raises.
"""
from __future__ import annotations

from .interventions import X_THROW_ID

FS, WS, RI, U, ND = "FS", "WS", "RI", "U", "ND"
LEVELS = (FS, ND, WS, RI, U)
SAME, CHANGED, ERR, NA = "SAME", "CHANGED", "ERR", "NA"
FO_CHANGED, FO_SILENT, FO_UNUSABLE = "CHANGED", "SILENT", "UNUSABLE"
KNOWN_CLASSES = ("SAME", "SHIFT", "FLIP", "ERR")
X_RET_IDS = ("X-RET-1", "X-RET-2")
ND_REASONS = ("x_throw_err", "x_throw_na", "x_ret_err", "no_x_ret", "throw_swallowed", "swallow_risk",
              "first_order_unusable")
MALFORMED = ("malformed:bad_shape", "malformed:unknown_class", "malformed:uncompiled_with_class",
             "malformed:variant_ids", "malformed:compiled_not_run", "malformed:entered_missing",
             "malformed:surfaced_missing", "malformed:marker_inconsistent", "malformed:swallow_risk_missing",
             "malformed:unclassifiable")
NO_RECORD = "excluded:no_record"
PF, TF = "PROGRAM_FAULT", "TEST_FAULT"


def _is_str(x) -> bool:
    return isinstance(x, str)


def _variants(rec) -> list:
    """The record's variants when they are a list of objects; otherwise an empty list (helpers never raise)."""
    if not isinstance(rec, dict):
        return []
    vs = rec.get("variants")
    if not isinstance(vs, list):
        return []
    return [v for v in vs if isinstance(v, dict)]


def outcome_class(cls) -> str:
    """Ledger class of one variant run -> SAME / CHANGED / ERR (spec 2.2); None (not run) -> NA."""
    if cls is None:
        return NA
    if cls == "SHIFT" or cls == "FLIP":
        return CHANGED
    if cls == "SAME":
        return SAME
    if cls == "ERR":
        return ERR
    return "UNKNOWN"


def _excluded(rec) -> bool:
    return isinstance(rec, dict) and _is_str(rec.get("excluded")) and rec.get("excluded") != ""


def _x_throw_variant(rec):
    return next((v for v in _variants(rec) if v.get("id") == X_THROW_ID), None)


def x_throw(rec) -> str:
    """x_throw of a record (spec 2.3): NA when excluded, absent or not compiled."""
    if not isinstance(rec, dict) or _excluded(rec):
        return NA
    v = _x_throw_variant(rec)
    if v is None or v.get("compiled") is not True:
        return NA
    return outcome_class(v.get("class"))


def x_ret(rec) -> list[str]:
    """Classes of the compiled X-RET variants (uncompiled variants never contribute a class)."""
    if not isinstance(rec, dict) or _excluded(rec):
        return []
    return [outcome_class(v.get("class")) for v in _variants(rec)
            if v.get("id") != X_THROW_ID and v.get("compiled") is True]


def fo_state(first_order_summary) -> str:
    """Spec 2.3: CHANGED if `coupled` is exactly true; SILENT if present, not excluded and `coupled` exactly
    false; UNUSABLE otherwise."""
    s = first_order_summary
    if not isinstance(s, dict):
        return FO_UNUSABLE
    if s.get("coupled") is True:
        return FO_CHANGED
    if s.get("excluded") is None and s.get("coupled") is False:
        return FO_SILENT
    return FO_UNUSABLE


def fo_changed(first_order_summary) -> bool:
    return fo_state(first_order_summary) == FO_CHANGED


def malformed(rec) -> str | None:
    """Record validity (spec 2.3): the code of the first rule that holds, or None for a valid record."""
    # 1. bad_shape (every record)
    if not isinstance(rec, dict):
        return "malformed:bad_shape"
    ex = rec.get("excluded")
    if not (ex is None or (_is_str(ex) and ex != "")):
        return "malformed:bad_shape"
    vs = rec.get("variants")
    if not isinstance(vs, list) or any(not isinstance(v, dict) for v in vs):
        return "malformed:bad_shape"
    if any(not _is_str(v.get("id")) or not isinstance(v.get("compiled"), bool) for v in vs):
        return "malformed:bad_shape"
    # 2. unknown_class (every variant, compiled or not; every record)
    if any(v.get("class") is not None and v.get("class") not in KNOWN_CLASSES for v in vs):
        return "malformed:unknown_class"
    # 3. uncompiled_with_class (every record)
    if any(v.get("compiled") is False and v.get("class") is not None for v in vs):
        return "malformed:uncompiled_with_class"
    if ex is not None:                       # rules 4 to 9 apply to non-excluded records only
        return None
    # 4. variant_ids
    ids = [v.get("id") for v in vs]
    others = [i for i in ids if i != X_THROW_ID]
    if ids.count(X_THROW_ID) != 1 or len(others) > 2 or len(set(others)) != len(others) \
            or any(i not in X_RET_IDS for i in others):
        return "malformed:variant_ids"
    # 5. compiled_not_run
    if any(v.get("compiled") is True and v.get("class") is None for v in vs):
        return "malformed:compiled_not_run"
    xt_has_class = next(v for v in vs if v.get("id") == X_THROW_ID).get("class") is not None
    # 6. entered_missing
    if xt_has_class and not isinstance(rec.get("entered"), bool):
        return "malformed:entered_missing"
    # 7. surfaced_missing
    if xt_has_class and not isinstance(rec.get("surfaced"), bool):
        return "malformed:surfaced_missing"
    # 8. marker_inconsistent
    if rec.get("surfaced") is True and rec.get("entered") is not True:
        return "malformed:marker_inconsistent"
    # 9. swallow_risk_missing
    if not isinstance(rec.get("swallow_risk"), bool):
        return "malformed:swallow_risk_missing"
    return None


def level(wdp_record, first_order_summary) -> tuple[str, str | None]:
    try:
        return _level(wdp_record, first_order_summary)
    except Exception:                                                      # never raises; fails closed
        return ND, "malformed:unclassifiable"


def _level(rec, s) -> tuple[str, str | None]:
    if rec is None:                                                        # 1
        return ND, NO_RECORD
    bad = malformed(rec)                                                   # 2
    if bad is not None:
        return ND, bad
    fo = fo_state(s)
    if fo == FO_CHANGED:                                                   # 3
        return FS, None
    if rec.get("excluded") is not None:                                    # 4
        return ND, f"excluded:{rec['excluded']}"
    if fo != FO_SILENT:                                                    # 5
        return ND, "first_order_unusable"
    xt = x_throw(rec)
    if xt == ERR or xt == NA:                                              # 6
        return ND, "x_throw_err" if xt == ERR else "x_throw_na"
    xr = x_ret(rec)
    if ERR in xr:                                                          # 7
        return ND, "x_ret_err"
    if CHANGED in xr:                                                      # 8
        return WS, None
    if xt == CHANGED:
        return (RI, None) if len(xr) > 0 else (ND, "no_x_ret")             # 9, 10
    entered, swallow = rec.get("entered"), rec.get("swallow_risk")
    if xt == SAME and entered is True:                                     # 11
        return ND, "throw_swallowed"
    if xt == SAME and swallow is True:                                     # 12
        return ND, "swallow_risk"
    if xt == SAME and entered is False and swallow is False and all(c == SAME for c in xr):   # 13
        return U, None
    return ND, "malformed:unclassifiable"                                  # 14


def cd_u(base: str, lvl: str) -> str:
    """CD-U (primary): discard at level U, otherwise the base rule's label."""
    return TF if lvl == U else base


def cd_ur(base: str, lvl: str) -> str:
    """CD-UR (secondary, riskier): discard at level U or RI, otherwise the base rule's label."""
    return TF if lvl in (U, RI) else base
