"""The two human audits of Phase 2, as blinded sheets plus scoring.

Label audit (Section 3.4): both authors independently inspect a stratified random sample of 100 labelled
development instances (50 PF, 50 TF) and decide whether the failure on B is attributable to the fault.
Spec leakage audit (Section 3.6.1): both authors classify a stratified sample of 60 inferred specifications
against the fix as STATES_FIXED / STATES_BUGGY / SILENT.

Blinding: rater sheets never show the automatic label or the outcome on F (label audit), and never show
the instance's label (spec audit). The answer key is written to the ground-truth store, separately.
Each rater gets an identical copy with rows in the same random order; raters must not confer.
"""
from __future__ import annotations

import csv
import random
from collections import Counter
from pathlib import Path

from . import config, stats

LABEL_CHOICES = ("ATTRIBUTABLE_TO_FAULT", "NOT_ATTRIBUTABLE", "UNSURE")
SPEC_CHOICES = ("STATES_FIXED", "STATES_BUGGY", "SILENT")


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def stratified(rows: list[dict], key, quotas: dict, seed: int) -> list[dict]:
    rng = random.Random(seed)
    out = []
    for stratum, n in quotas.items():
        pool = sorted([r for r in rows if key(r) == stratum], key=lambda r: r["instance_id"] if "instance_id" in r else r["focal_id"])
        out += rng.sample(pool, min(n, len(pool)))
    rng.shuffle(out)
    return out


def make_label_audit(labels: list[dict], instances: dict, fix_diffs: dict, out_dir: Path,
                     n_pf: int = 50, n_tf: int = 50, seed: int = 20261013) -> dict:
    """labels: label-store rows (dev split). instances: instance_id -> instance record. fix_diffs: bug -> diff."""
    dev = [l for l in labels if l["split"] == "dev" and l["label"] in ("PF", "TF")]
    sample = stratified(dev, lambda r: r["label"], {"PF": n_pf, "TF": n_tf}, seed)
    sheet, key = [], []
    for k, l in enumerate(sample, 1):
        inst = instances[l["instance_id"]]
        f = inst["failure"]
        aid = f"LA{k:03d}"
        sheet.append({
            "audit_id": aid, "project": l["project"], "focal_method": inst["focal_class"] + "." + inst["focal_method_name"],
            "test_method": inst["test"]["method_source"],
            "failure_on_buggy_version": f"{f['outcome_type']} {f.get('exception_class') or ''}: {f.get('message') or ''}"
                                        f"\nline: {f.get('failing_test_line_text')}\n{f.get('rendered_trace', '')}",
            "fix_patch": fix_diffs.get(l["bug_name"], "(patch unavailable)"),
            "decision": "", "notes": "",
        })
        key.append({"audit_id": aid, "instance_id": l["instance_id"], "auto_label": l["label"]})
    for rater in ("A", "B"):
        _write_csv(out_dir / f"label_audit_rater_{rater}.csv", sheet)
    _write_csv(config.GT_STORE / "audit" / "label_audit_key.csv", key)
    return {"n": len(sample), "by_label": dict(Counter(k["auto_label"] for k in key)),
            "requested": {"PF": n_pf, "TF": n_tf}}


def make_spec_audit(specs: list[dict], contexts: dict, fix_diffs: dict, out_dir: Path, n: int = 60,
                    seed: int = 20261014) -> dict:
    """specs: valid S2 records (test split). Stratified by project, proportional with >= 1 per project."""
    valid = [s for s in specs if s.get("valid") and contexts.get(s["focal_id"], {}).get("split") == "test"]
    by_proj = Counter(contexts[s["focal_id"]]["project"] for s in valid)
    total = sum(by_proj.values())
    quotas = {}
    if total:  # largest-remainder allocation, at least one per project, summing to min(n, total)
        target = min(n, total)
        share = {p: target * c / total for p, c in by_proj.items()}
        quotas = {p: max(1, min(by_proj[p], int(share[p]))) for p in by_proj}
        for p in sorted(by_proj, key=lambda p: share[p] - int(share[p]), reverse=True) * 2:
            if sum(quotas.values()) >= target:
                break
            if quotas[p] < by_proj[p]:
                quotas[p] += 1
        while sum(quotas.values()) > target:
            quotas[max(quotas, key=quotas.get)] -= 1
    sample = stratified(valid, lambda s: contexts[s["focal_id"]]["project"], quotas, seed)
    sheet = []
    for k, s in enumerate(sample, 1):
        c = contexts[s["focal_id"]]
        spec = "\n".join(f"{kk}: {vv}" for kk, vv in s["spec"].items())
        sheet.append({"audit_id": f"SA{k:03d}", "project": c["project"],
                      "focal_signature": c["sig"]["focal_signature"], "inferred_specification": spec,
                      "fix_patch": fix_diffs.get(c["bug_name"], "(patch unavailable)"),
                      "classification": "", "notes": ""})
    for rater in ("A", "B"):
        _write_csv(out_dir / f"spec_audit_rater_{rater}.csv", sheet)
    _write_csv(config.GT_STORE / "audit" / "spec_audit_key.csv",
               [{"audit_id": r["audit_id"], "focal_id": s["focal_id"]} for r, s in zip(sheet, sample)])
    return {"n": len(sample), "quotas": quotas}


def score_label_audit(sheet_a: Path, sheet_b: Path, key: Path) -> dict:
    a = {r["audit_id"]: r["decision"].strip().upper() for r in _read_csv(sheet_a)}
    b = {r["audit_id"]: r["decision"].strip().upper() for r in _read_csv(sheet_b)}
    k = {r["audit_id"]: r["auto_label"] for r in _read_csv(key)}
    ids = sorted(k)
    blanks = [i for i in ids if a.get(i) not in LABEL_CHOICES or b.get(i) not in LABEL_CHOICES]
    if blanks:
        return {"status": "incomplete", "missing_or_invalid": blanks}
    to_label = {"ATTRIBUTABLE_TO_FAULT": "PF", "NOT_ATTRIBUTABLE": "TF"}
    kappa = stats.cohen_kappa([a[i] for i in ids], [b[i] for i in ids])
    agree = {}
    for name, r in (("rater_A", a), ("rater_B", b)):
        decided = [i for i in ids if r[i] != "UNSURE"]
        agree[name] = {"agreement_with_auto_label": sum(to_label[r[i]] == k[i] for i in decided) / len(decided)
                       if decided else float("nan"), "unsure": len(ids) - len(decided)}
    disagreements = [i for i in ids if a[i] != b[i]]
    return {"status": "scored", "n": len(ids), "cohen_kappa_raters": kappa, **agree,
            "rater_disagreements": disagreements}


def score_spec_audit(sheet_a: Path, sheet_b: Path) -> dict:
    a = {r["audit_id"]: r["classification"].strip().upper() for r in _read_csv(sheet_a)}
    b = {r["audit_id"]: r["classification"].strip().upper() for r in _read_csv(sheet_b)}
    ids = sorted(a)
    blanks = [i for i in ids if a[i] not in SPEC_CHOICES or b.get(i) not in SPEC_CHOICES]
    if blanks:
        return {"status": "incomplete", "missing_or_invalid": blanks}
    return {"status": "scored", "n": len(ids), "cohen_kappa_raters": stats.cohen_kappa([a[i] for i in ids], [b[i] for i in ids]),
            "proportions_rater_A": {c: sum(a[i] == c for i in ids) / len(ids) for c in SPEC_CHOICES},
            "proportions_rater_B": {c: sum(b[i] == c for i in ids) / len(ids) for c in SPEC_CHOICES}}
