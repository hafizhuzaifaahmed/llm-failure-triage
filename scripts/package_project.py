"""Build the shareable project ZIP with a SHA-256 manifest.

    python scripts/package_project.py

Excluded: the cloned public replication package (re-clone at commit 751f9f4, see REPRODUCIBILITY_GUIDE.md),
caches, LaTeX intermediates, mock/synthetic smoke outputs (results/smoke/, reproducible with smoke_test.py),
any active configs/budget.json, and the deliverables folder itself.
"""
import hashlib
import json
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "deliverables"
EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", ".git"}
EXCLUDE_PREFIXES = ["data/external/EvalAndMitigate/", "results/smoke/", "deliverables/"]
EXCLUDE_FILES = {"configs/budget.json"}
EXCLUDE_SUFFIXES = {".aux", ".fls", ".fdb_latexmk", ".blg", ".out", ".synctex.gz", ".pyc"}


def included(rel: str, p: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in p.parts):
        return False
    if any(rel.startswith(x) for x in EXCLUDE_PREFIXES) or rel in EXCLUDE_FILES:
        return False
    if p.suffix in EXCLUDE_SUFFIXES or (rel.startswith("paper/") and p.suffix == ".log"):
        return False
    return True


def main():
    OUT_DIR.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M")
    zpath = OUT_DIR / f"Phase3_4_FailureTriage_{stamp}.zip"
    manifest = []
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(ROOT.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(ROOT).as_posix()
            if not included(rel, p):
                continue
            data = p.read_bytes()
            z.writestr(f"Phase3_4_FailureTriage/{rel}", data)
            manifest.append({"path": rel, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        note = ("data/external/EvalAndMitigate is not included (public, 137 MB). Re-create with:\n"
                "git clone https://github.com/drixs2050/EvalAndMitigate.git data/external/EvalAndMitigate\n"
                "git -C data/external/EvalAndMitigate checkout 751f9f4153fce0d55c111602a27e19009dec0721\n")
        z.writestr("Phase3_4_FailureTriage/data/external/README_EXTERNAL.txt", note)
        z.writestr("Phase3_4_FailureTriage/PACKAGE_MANIFEST.json", json.dumps(manifest, indent=1))
    total = sum(m["bytes"] for m in manifest)
    print(f"{zpath}\n{len(manifest)} files, {total / 1e6:.1f} MB uncompressed, {zpath.stat().st_size / 1e6:.1f} MB zipped")


if __name__ == "__main__":
    main()
