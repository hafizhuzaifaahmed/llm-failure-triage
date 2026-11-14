"""D-26 — after the freeze, copy every blob of the frozen models to archive/model_blobs/ and verify SHA-256.

    python scripts/local/archive_blobs.py

Ollama names each blob by the SHA-256 of its content, so each copy is re-hashed and must equal its name. Writes
archive/model_blobs/MANIFEST.json and configs/model_blob_manifest.json (tracked; archive/ itself is git-ignored).
Refuses if free disk would drop below 20 GB.
"""
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage.ollama import FROZEN_MODELS_FILE  # noqa: E402

BLOBS = Path.home() / ".ollama" / "models" / "blobs"
OUT = config.ROOT / "archive" / "model_blobs"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    frozen = json.loads(FROZEN_MODELS_FILE.read_text(encoding="utf-8"))
    need = {}
    for role, m in frozen["frozen_models"].items():
        for b in m["blobs"]:
            need.setdefault(b["digest"], {"size": b["size"], "mediaType": b["mediaType"], "models": []})["models"].append(m["tag"])
    total = sum(v["size"] for v in need.values())
    free = shutil.disk_usage(config.ROOT).free
    if free - total < 20e9:
        raise SystemExit(f"not enough disk: need {total / 1e9:.1f} GB, free {free / 1e9:.1f} GB (keep >= 20 GB)")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for digest, v in sorted(need.items()):
        src = BLOBS / digest.replace(":", "-")
        dst = OUT / digest.replace(":", "-")
        if not dst.exists() or dst.stat().st_size != v["size"]:
            shutil.copyfile(src, dst)
        got = "sha256:" + sha256_file(dst)
        rows.append({"digest": digest, "verified": got == digest, "size": v["size"], "mediaType": v["mediaType"],
                     "models": v["models"]})
        print(digest[:19], v["size"], "ok" if got == digest else "MISMATCH", flush=True)
    man = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "frozen_file": str(FROZEN_MODELS_FILE.name),
           "total_bytes": total, "all_verified": all(r["verified"] for r in rows), "blobs": rows}
    (OUT / "MANIFEST.json").write_text(json.dumps(man, indent=2), encoding="utf-8")
    (config.ROOT / "configs" / "model_blob_manifest.json").write_text(json.dumps(man, indent=2), encoding="utf-8")
    print("all verified:", man["all_verified"], f"{total / 1e9:.1f} GB")


if __name__ == "__main__":
    main()
