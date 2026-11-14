"""Freeze manifest for whole-method dependence probes (WDP; D-147).

    python scripts/extension/freeze_wdp.py            # once; refuses to overwrite an existing manifest
    python scripts/extension/freeze_wdp.py --refreeze D-148   # replace it under a recorded decision
    python scripts/extension/freeze_wdp.py --check    # exit 1 and list every difference

Writes configs/extension/wdp_frozen.json: the sha256 (file bytes with CRLF normalised to LF) of the WDP code files,
of TECHNICAL_METHOD_SPEC.md and of OPUS_EXECUTION_BRIEF.md, the engine parameters and a UTC time. The manifest is an
internal Git freeze; it is not an external preregistration.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

MANIFEST = ROOT / "configs" / "extension" / "wdp_frozen.json"
FILES = ["src/triage_dep/__init__.py", "src/triage_dep/interventions.py", "src/triage_dep/screen.py",
         "src/triage_dep/wdp.py", "src/triage_dep/levels.py",
         "scripts/extension/run_wdp_tranche.py", "scripts/extension/wdp_analysis.py",
         "scripts/extension/wdp_report.py", "scripts/extension/freeze_wdp.py",
         "docs/research_extension/TECHNICAL_METHOD_SPEC.md", "docs/research_extension/OPUS_EXECUTION_BRIEF.md"]


def content_hash(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def parameters() -> dict:
    from triage_dep import interventions, wdp
    from triage_ext import probe
    return {"variant_table_sha256": interventions.variant_table_sha256(), "x_throw_body": interventions.X_THROW_BODY,
            "max_variants": interventions.MAX_VARIANTS, "baseline_timeout_s": wdp.BASELINE_TIMEOUT_S,
            "variant_timeout_s": wdp.VARIANT_TIMEOUT_S, "marker_env": wdp.MARKER_ENV,
            "source_levels_tried": list(probe.SOURCE_LEVELS), "bootstrap_resamples": 10_000,
            "bootstrap_seed": 20261113}


def current() -> dict:
    return {"files": {f: content_hash(f) for f in FILES}, "parameters": parameters()}


def manifest_sha256() -> str:
    return hashlib.sha256(MANIFEST.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def check() -> list[str]:
    """Every difference between the working tree and configs/extension/wdp_frozen.json; empty means verified.

    The one implementation of the frozen-file check: `--check` prints it and the run driver imports it."""
    if not MANIFEST.exists():
        return [f"manifest missing: {MANIFEST}"]
    try:
        doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cur = current()
    except Exception as e:                                    # unreadable manifest or a missing hashed file
        return [f"check could not run: {e!r}"]
    bad = [f"file changed: {f}" for f, h in doc.get("files", {}).items() if cur["files"].get(f) != h]
    bad += [f"file not in manifest: {f}" for f in FILES if f not in doc.get("files", {})]
    bad += [f"parameter changed: {k}" for k, v in doc.get("parameters", {}).items() if cur["parameters"].get(k) != v]
    bad += [f"parameter not in manifest: {k}" for k in cur["parameters"] if k not in doc.get("parameters", {})]
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--refreeze", metavar="DECISION", help="replace an existing manifest under a recorded decision")
    a = ap.parse_args()
    if not a.check:
        previous = None
        if MANIFEST.exists():
            if not a.refreeze:
                sys.exit(f"{MANIFEST} exists; a frozen configuration is not rewritten (use --refreeze <decision>)")
            old = json.loads(MANIFEST.read_text(encoding="utf-8"))
            previous = {"decision": old.get("decision"), "frozen_utc": old.get("frozen_utc"),
                        "manifest_sha256": manifest_sha256()}
        doc = {"decision": a.refreeze or "D-147", "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "status": "exploratory; protocol frozen internally in Git before the run; not externally "
                         "preregistered; designed after the confirmation outcomes were known",
               "hash_method": "sha256 of file bytes with CRLF normalised to LF", **current()}
        if previous:
            doc["supersedes"] = previous
        MANIFEST.write_text(json.dumps(doc, indent=1, sort_keys=True), encoding="utf-8", newline="\n")
        print("written", MANIFEST)
        return
    bad = check()
    if bad:
        print("\n".join(bad))
        sys.exit(1)
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    print("frozen WDP configuration verified:", len(doc["files"]), "files,", len(doc["parameters"]), "parameters;",
          "manifest sha256", manifest_sha256())


if __name__ == "__main__":
    main()
