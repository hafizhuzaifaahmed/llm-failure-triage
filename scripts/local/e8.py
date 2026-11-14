"""E8 three-family vote (D-82, D-83, D-90): fresh J1-prompt calls batched by model, one model loaded at a time.

    python scripts/local/e8.py frozen     # frozen server: session_check --start; M1 batch, then M2 batch; --end
    python scripts/local/e8.py e6b        # stop frozen; E6b server: E6b batch (selection-gated); stop; restart frozen, --start

Every call goes through the unchanged J1 arm at replicate indices no committed run used (10-12), so the call key, and
with it the seed, is new; nothing is reused from the committed J1 replicates. The E6b batch runs under the E6b profile
with its stopping rule armed. Votes are formed offline by scripts/analysis/e8_analysis.py (no call).
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "local"))

import e6b  # noqa: E402
from triage import expl_profile, ollama_server  # noqa: E402

EXP = ROOT / "configs" / "experiments"
FROZEN_BATCHES = ("LOCAL_HO_E8_VOTE_M1", "LOCAL_HO_E8_VOTE_M2")
E6B_BATCH = "LOCAL_HO_E8_VOTE_E6B"


def run(name: str) -> int:
    t0 = time.time()
    r = e6b.py("scripts/run_experiment.py", EXP / f"{name}.json", "--workers", "1")
    logf = ROOT / "logs" / "runs" / f"e8_{name}.log"
    logf.parent.mkdir(parents=True, exist_ok=True)
    with open(logf, "a", encoding="utf-8") as f:
        f.write(f"=== {e6b.utc()} ===\n{r.stdout}\n{r.stderr}\nexit {r.returncode}\n")
    stopped = "STOPPED ON REQUEST" in r.stdout
    print(name, "exit", r.returncode, round(time.time() - t0), "s", "stopped" if stopped else "", flush=True)
    return 1 if stopped else r.returncode


def cmd_frozen(_a):
    if not ollama_server.is_up():
        ollama_server.start(tag="frozen_e8")
    r = e6b.py("scripts/local/session_check.py", "--start")
    print(r.stdout[-400:])
    if r.returncode != 0:
        raise SystemExit("frozen session_check --start failed; not running E8")
    try:
        for name in FROZEN_BATCHES:
            if expl_profile.STOP_FILE_PATH().exists() or run(name) != 0:
                raise SystemExit(f"{name} did not complete; E8 stopped")
    finally:
        print(e6b.py("scripts/local/session_check.py", "--end").stdout[-300:])


def cmd_e6b(_a):
    p = e6b.load()
    e6b.ensure_server(p)                         # stops the frozen server first
    try:
        rc = run(E6B_BATCH)
    finally:
        ollama_server.stop(p["base_url"])
        e6b.log(p, "server_stop", after=E6B_BATCH)
        stop = expl_profile.STOP_FILE_PATH()
        if stop.exists() and stop.read_text(encoding="utf-8").startswith(expl_profile.SAFETY_MARK):
            print("safety stop:", stop.read_text(encoding="utf-8").strip())
            stop.unlink()
        ollama_server.start(tag="frozen_after_e8")
        r = e6b.py("scripts/local/session_check.py", "--start")
        print(r.stdout[-400:], f"session_check exit {r.returncode}")
    if rc != 0:
        raise SystemExit(f"{E6B_BATCH} did not complete")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["frozen", "e6b"])
    a = ap.parse_args()
    {"frozen": cmd_frozen, "e6b": cmd_e6b}[a.step](a)


if __name__ == "__main__":
    main()
