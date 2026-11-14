"""KUU confirmatory run on D2 (D-95): fresh J1 calls from M1, M2 and the E6b judge, one model on one server at a time.

    python scripts/local/kuu.py begin    # frozen server: session_check --start, then --end; stop it
    python scripts/local/kuu.py run      # M1 (kuu_m1), M2 (kuu_m2), E6b (e6b): own server each, stopping rule armed
    python scripts/local/kuu.py finish   # stop any KUU server, restart the frozen server, session_check --start

Every member runs through the unchanged J1 arm at replicate index 20 (no committed run uses it), with its own profile,
port, call log, session log and safety log. A member that ends with a non-zero exit, a stop or a safety abort halts
the run; nothing is retried. The votes are combined offline by scripts/analysis/kuu_analysis.py (no call).
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import expl_profile, ollama_server  # noqa: E402
from triage.io_utils import append_jsonl  # noqa: E402

MEMBERS = (("LOCAL_HO_KUU_D2_M1", ROOT / "configs" / "kuu_m1.json"),
           ("LOCAL_HO_KUU_D2_M2", ROOT / "configs" / "kuu_m2.json"),
           ("LOCAL_HO_KUU_D2_E6B", expl_profile.E6B_PROFILE_FILE))
SESSION_LOG = ROOT / "logs" / "sessions_kuu.jsonl"


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def log(event, **kw):
    append_jsonl(SESSION_LOG, {"utc": utc(), "event": event, **kw})


def py(*args):
    return subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def stop_all_profile_servers():
    for _, f in MEMBERS:
        p = expl_profile.load(f)
        if ollama_server.is_up(p["base_url"]):
            ollama_server.stop(p["base_url"])


def cmd_begin(_a):
    if not ollama_server.is_up():
        ollama_server.start(tag="frozen_before_kuu")
    r1, r2 = py("scripts/local/session_check.py", "--start"), py("scripts/local/session_check.py", "--end")
    log("frozen_session_check", start_exit=r1.returncode, end_exit=r2.returncode)
    print(r1.stdout[-500:])
    if r1.returncode != 0:
        raise SystemExit("frozen session_check --start failed; not starting KUU")
    ollama_server.stop()


def cmd_run(_a):
    if ollama_server.is_up():
        raise SystemExit("the frozen server is up; run `begin` first")
    for name, f in MEMBERS:
        run_dir = ROOT / "results" / "runs_local" / name
        status = run_dir / "run_status.json"
        if expl_profile.STOP_FILE_PATH().exists():
            raise SystemExit(f"logs/STOP present; stopping before {name}")
        p = expl_profile.load(f)
        stop_all_profile_servers()
        env = ollama_server.start_profile(p, tag=f"kuu_{name[-2:].lower()}")
        log("server_start", member=name, model=p["model_tag"], env=env)
        t0 = time.time()
        r = py("scripts/run_experiment.py", ROOT / "configs" / "experiments" / f"{name}.json", "--workers", "1")
        logf = ROOT / "logs" / "runs" / f"kuu_{name}.log"
        logf.parent.mkdir(parents=True, exist_ok=True)
        with open(logf, "a", encoding="utf-8") as fh:
            fh.write(f"=== {utc()} ===\n{r.stdout}\n{r.stderr}\nexit {r.returncode}\n")
        stopped = "STOPPED ON REQUEST" in r.stdout or "STOPPING RUN" in r.stdout
        ollama_server.stop(p["base_url"])
        decisions = json.loads(status.read_text(encoding="utf-8")).get("decisions") if status.exists() else None
        log("member_end", member=name, exit=r.returncode, stopped=stopped, wall_s=round(time.time() - t0, 1),
            decisions=decisions)
        print(name, "exit", r.returncode, "decisions", decisions, round(time.time() - t0), "s", flush=True)
        if r.returncode != 0 or stopped:
            raise SystemExit(f"{name} did not complete (exit {r.returncode}, stopped={stopped}); KUU halted, no retry")


def cmd_finish(_a):
    stop_all_profile_servers()
    stop = expl_profile.STOP_FILE_PATH()
    if stop.exists() and stop.read_text(encoding="utf-8").startswith(expl_profile.SAFETY_MARK):
        print("safety stop:", stop.read_text(encoding="utf-8").strip())
        stop.unlink()
    ollama_server.start(tag="frozen_after_kuu")
    r = py("scripts/local/session_check.py", "--start")
    log("frozen_restarted", session_check_exit=r.returncode)
    print(r.stdout[-600:], f"session_check exit {r.returncode}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["begin", "run", "finish"])
    a = ap.parse_args()
    {"begin": cmd_begin, "run": cmd_run, "finish": cmd_finish}[a.step](a)


if __name__ == "__main__":
    main()
