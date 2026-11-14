"""Pull the four E6b candidates in the D-82 order (authors' permission, 3 Nov) and record their digests (no model load).

Starts the frozen-env server if none is up (a pull does not load a model, so no GPU session is involved), pulls each
tag with the frozen Ollama 0.40.13, and writes `results/e6b/pulls.json` with the manifest digest and size reported by
/api/tags. Nothing is run on any study data.

    python scripts/local/pull_e6b_candidates.py
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import ollama_server  # noqa: E402
from triage.io_utils import dump_json  # noqa: E402

ORDER = ["ministral-3:14b-instruct-2512-q4_K_M", "phi4:14b-q4_K_M",
         "mistral-nemo:12b-instruct-2407-q4_K_M", "llama3.1:8b-instruct-q4_K_M"]
EXE = Path.home() / "AppData" / "Local" / "Programs" / "Ollama" / "ollama.exe"
LOGS = ROOT / "logs" / "ollama_pull"
OUT = ROOT / "results" / "e6b" / "pulls.json"


def main():
    if not ollama_server.is_up(ollama_server.DEFAULT_URL):
        ollama_server.start(tag="e6b_pulls")
    LOGS.mkdir(parents=True, exist_ok=True)
    rec = {"order": ORDER, "pulls": []}
    for tag in ORDER:
        t0 = time.time()
        log = LOGS / f"pull_{tag.replace(':', '_')}.log"
        with open(log, "w", encoding="utf-8") as fh:
            r = subprocess.run([str(EXE), "pull", tag], stdout=fh, stderr=subprocess.STDOUT)
        rec["pulls"].append({"tag": tag, "exit": r.returncode, "wall_s": round(time.time() - t0, 1), "log": log.name})
        print(tag, "exit", r.returncode, round(time.time() - t0), "s", flush=True)
    from triage.ollama import OllamaAPI
    tags = OllamaAPI(ollama_server.DEFAULT_URL, timeout_s=30).tags()
    for p in rec["pulls"]:
        t = tags.get(p["tag"], {})
        p.update(digest=t.get("digest"), size_bytes=t.get("size"))
    dump_json(OUT, rec)
    print(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()
