"""D-84: seal the blind LLM rater's CSVs. Checks shape only (row counts, ids, vocabulary) and never prints a decision.

    python scripts/audit/seal_llm_rater.py --rater-dir C:/llm_rater_C --run-dir C:/llm_rater_C_run --sealed-dir C:/llm_rater_C_sealed

Copies the two filled CSVs and the session result into the sealed directory (outside git), writes
docs/audits/kit/LLM_RATER_SEAL.json with their SHA-256 and the run's metadata, and exits non-zero if the shape is wrong.
The CSVs are unsealed only after both human CSVs are committed (`--verify` re-checks the hashes at that point).
"""
import argparse
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "docs" / "audits" / "kit"
SEAL = KIT / "LLM_RATER_SEAL.json"
FILES = ("label_audit_rater_C.csv", "calibration_rater_C.csv")
VOCAB, CONF = {"PF", "TF", "AMB"}, {"1", "2", "3"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def shape(filled: Path, template: Path) -> dict:
    t = list(csv.DictReader(template.open(encoding="utf-8", newline="")))
    f = list(csv.DictReader(filled.open(encoding="utf-8-sig", newline="")))
    id_col = "audit_id" if "audit_id" in t[0] else "item"
    fixed = [c for c in t[0] if c not in ("decision", "confidence", "notes")]
    return {"rows": len(f), "rows_expected": len(t),
            "columns_unchanged": list(f[0].keys()) == list(t[0].keys()) if f else False,
            "fixed_columns_unchanged": [{c: r[c] for c in fixed} for r in f] == [{c: r[c] for c in fixed} for r in t],
            "ids_unique": len({r[id_col] for r in f}) == len(f),
            "decisions_in_vocabulary": sum(r["decision"].strip() in VOCAB for r in f),
            "confidence_valid": sum(r["confidence"].strip() in CONF for r in f)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rater-dir", type=Path)
    ap.add_argument("--run-dir", type=Path)
    ap.add_argument("--sealed-dir", type=Path)
    ap.add_argument("--verify", action="store_true", help="re-check the sealed files against the committed hashes")
    a = ap.parse_args()
    if a.verify:
        seal = json.loads(SEAL.read_text(encoding="utf-8"))
        ok = all(sha(Path(seal["sealed_dir"]) / n) == seal["sha256"][n] for n in FILES)
        print("sealed hashes match" if ok else "HASH MISMATCH")
        sys.exit(0 if ok else 1)
    checks = {n: shape(a.rater_dir / n, KIT / n) for n in FILES}
    ok = all(c["rows"] == c["rows_expected"] and c["columns_unchanged"] and c["fixed_columns_unchanged"] and c["ids_unique"]
             and c["decisions_in_vocabulary"] == c["rows"] and c["confidence_valid"] == c["rows"] for c in checks.values())
    print(json.dumps(checks, indent=1))
    if not ok:
        sys.exit("shape check failed; nothing sealed")
    a.sealed_dir.mkdir(parents=True, exist_ok=True)
    for n in FILES:
        shutil.copy2(a.rater_dir / n, a.sealed_dir / n)
    shutil.copy2(a.run_dir / "result.json", a.sealed_dir / "session_result.json")
    res = json.loads((a.run_dir / "result.json").read_text(encoding="utf-8"))
    prompt = (KIT / "llm_rater" / "PROMPT.txt").read_text(encoding="utf-8")
    seal = {
        "decision": "D-84",
        "rater": "C (LLM)",
        "sha256": {n: sha(a.sealed_dir / n) for n in FILES},
        "session_result_sha256": sha(a.sealed_dir / "session_result.json"),
        "sealed_dir": str(a.sealed_dir),
        "unseal_rule": "opened only after both human rater CSVs (A, B) are committed",
        "model_ids": sorted((res.get("modelUsage") or {}).keys()),
        "start_utc": (a.run_dir / "start_utc.txt").read_text().strip(),
        "end_utc": (a.run_dir / "end_utc.txt").read_text().strip(),
        "num_turns": res.get("num_turns"),
        "duration_ms": res.get("duration_ms"),
        "is_error": res.get("is_error"),
        "final_reply": (res.get("result") or "").strip()[:20],
        "permission_denials": len(res.get("permission_denials") or []),
        "client": "Claude Code CLI 2.1.317, headless (-p), claude.ai subscription login, no API key",
        "flags": ["--model claude-opus-5-5", "--permission-mode dontAsk", "--settings docs/audits/kit/llm_rater/settings.json",
                  "--setting-sources project", "--strict-mcp-config", "--mcp-config {\"mcpServers\":{}}",
                  "--no-session-persistence", "--output-format json",
                  "minimal environment (env -i: PATH, SYSTEMROOT, user-profile and temp variables only)"],
        "prompt_file": "docs/audits/kit/llm_rater/PROMPT.txt",
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "inputs_sha256": {n: sha(KIT / n) for n in ("packets_rater_C.pdf", "LABEL_AUDIT_RUBRIC.md", *FILES)}
        | {"INSTRUCTIONS.md": sha(KIT / "llm_rater" / "INSTRUCTIONS.md")},
        "isolation_probe": "docs/audits/kit/llm_rater/isolation_probe_result.json",
        "shape_checks": checks,
    }
    SEAL.write_text(json.dumps(seal, indent=2) + "\n", encoding="utf-8")
    print("sealed:", json.dumps(seal["sha256"], indent=1))


if __name__ == "__main__":
    main()
