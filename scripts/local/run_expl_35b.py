"""D-67 exploratory qwen3.5:35b, end to end, under the authors' time box (D-76).

    python scripts/local/run_expl_35b.py feasibility   # stop the frozen server, start the 35b server, synthetic probes
    python scripts/local/run_expl_35b.py run           # J1 for all instances, then DEB, then SC, until done or deadline
    python scripts/local/run_expl_35b.py finish        # stop the 35b server, restart the frozen server, session_check

Feasibility: a crash (load failure, server exit, any probe error) or a request with no response within
`first_response_timeout_s` (15 min) drops the 35b with no further change -- no retry, no other setting.
Run: the D-78 safety rule (scripts' backend wrapper) aborts on RAM < 0.5 GiB at a 25-call check, a median latency of the
last 50 calls > 10 s, or a server crash/hang; the 4 GiB session gate is waived for this run only (D-78).
Deadline: a watchdog creates logs/STOP at `deadline_local`; the runner then starts no new call and exits cleanly.
Every step appends to the profile's own session log; outcomes go to results/expl_35b/outcome.json.
"""
import argparse
import json
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import expl_profile, ollama_server  # noqa: E402
from triage.io_utils import append_jsonl, dump_json, read_jsonl  # noqa: E402
from triage.llm import STOP_FILE  # noqa: E402

EXP = ROOT / "configs" / "experiments" / "EXPL_35B_D1TEST.json"
OUTCOME = ROOT / "results" / "expl_35b" / "outcome.json"
DEADLINE_MARK = "D-67/D-76 deadline"
TOOL_MARKS = (DEADLINE_MARK, expl_profile.SAFETY_MARK)


def labels(p) -> dict:
    """Every 35b output says what it is and how it differs from M1 (D-78)."""
    return {"label": p["label"], "model": p["model_tag"], "differences_from_M1": p["differences_from_M1"],
            "decisions": ["D-55", "D-67", "D-76", "D-77", "D-78"], "safety_rule": p["safety"]}


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def log(p, event, **kw):
    append_jsonl(expl_profile.resolve(p["session_log"]), {"utc": utc(), "event": event, **kw})


def outcome() -> dict:
    return json.loads(OUTCOME.read_text(encoding="utf-8")) if OUTCOME.exists() else {}


def save(**kw):
    o = {**outcome(), **kw}
    dump_json(OUTCOME, o)
    return o


def py(*args, timeout=None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def server_info(p) -> dict:
    from triage.ollama import OllamaAPI
    api = OllamaAPI(p["base_url"], timeout_s=30)
    try:
        return {"version": api.version(), "digest": api.tags().get(p["model_tag"], {}).get("digest"),
                "ps": {k: {x: v.get(x) for x in ("size", "size_vram", "context_length")} for k, v in api.ps().items()}}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"[:300]}


def cmd_feasibility(p):
    if expl_profile.past_deadline(p):
        raise SystemExit("past the D-67 deadline; not starting")
    save(**labels(p))
    ollama_server.stop()
    env = ollama_server.start_profile(p, tag="expl35b")
    log(p, "server_start", env=env, **server_info(p))
    t0 = time.time()
    try:
        # a hang inside one request is bounded by first_response_timeout_s; the whole probe set by a generous cap
        r = py("scripts/local/feasibility.py", "--model", p["model_tag"], "--role", "judge",
               "--profile", "configs/expl_35b.json", timeout=6 * 3600)
        crashed, tail = r.returncode != 0, (r.stdout[-1500:] + "\n" + r.stderr[-2500:])
    except subprocess.TimeoutExpired as e:
        crashed, tail = True, f"feasibility exceeded 6 h: {e}"
    up = ollama_server.is_up(p["base_url"])
    info = server_info(p)
    rec = {"feasibility_utc": utc(), "feasibility_wall_s": round(time.time() - t0, 1), "server_up_after": up,
           "feasibility_ok": (not crashed) and up, "feasibility_tail": tail}
    if not rec["feasibility_ok"]:
        rec.update(dropped=True, reason="feasibility crash or hang (D-67: dropped with no further change)")
    save(**rec)
    log(p, "feasibility", ok=rec["feasibility_ok"], wall_s=rec["feasibility_wall_s"], **info)
    print(json.dumps({k: v for k, v in rec.items() if k != "feasibility_tail"}, indent=1))
    print(tail[-1200:])


def watchdog(p, stop_evt: threading.Event, now=datetime.now, poll_s: float = 30.0):
    """Create logs/STOP at the deadline (D-76 time box). Returns True if it fired."""
    while not stop_evt.is_set():
        if expl_profile.past_deadline(p, now()):
            if not STOP_FILE.exists():
                STOP_FILE.parent.mkdir(parents=True, exist_ok=True)
                STOP_FILE.write_text(f"{DEADLINE_MARK} {p['deadline_local']} reached at {utc()}\n", encoding="utf-8")
            return True
        stop_evt.wait(poll_s)
    return False


def decisions_by_arm() -> dict:
    run = ROOT / "results" / "runs_local" / "EXPL_35B_D1TEST" / "decisions.jsonl"
    out = {}
    for d in read_jsonl(run):
        out[d["arm"]] = out.get(d["arm"], 0) + 1
    return out


def cmd_run(p):
    if not outcome().get("feasibility_ok"):
        raise SystemExit("feasibility has not passed (or the 35b was dropped); not running")
    if not ollama_server.is_up(p["base_url"]):
        raise SystemExit(f"the exploratory server is not up at {p['base_url']}")
    save(**labels(p))
    evt = threading.Event()
    fired = {"v": False}
    th = threading.Thread(target=lambda: fired.__setitem__("v", watchdog(p, evt)), daemon=True)
    th.start()
    passes = outcome().get("passes", {})
    log(p, "run_start", **server_info(p))
    for arm in p["arm_passes"]:
        if STOP_FILE.exists() or expl_profile.past_deadline(p):
            break
        t0 = time.time()
        r = py("scripts/run_experiment.py", EXP, "--only-arm", arm, "--workers", "1")
        logf = ROOT / "logs" / "runs" / f"expl35b_{arm}.log"
        logf.parent.mkdir(parents=True, exist_ok=True)
        with open(logf, "a", encoding="utf-8") as f:
            f.write(f"=== {utc()} ===\n{r.stdout}\n{r.stderr}\nexit {r.returncode}\n")
        passes[arm] = {"exit": r.returncode, "wall_s": round(time.time() - t0, 1), "end_utc": utc(),
                       "stopped": "STOPPED ON REQUEST" in r.stdout}
        save(passes=passes, decisions_by_arm=decisions_by_arm())
        log(p, "pass_end", arm=arm, **passes[arm])
        if r.returncode != 0 or passes[arm]["stopped"]:
            break
    evt.set()
    th.join(timeout=5)
    o = save(passes=passes, decisions_by_arm=decisions_by_arm(), deadline_fired=fired["v"] or STOP_FILE.exists()
             and STOP_FILE.read_text(encoding="utf-8").startswith(DEADLINE_MARK), run_end_utc=utc(),
             stop_reason=STOP_FILE.read_text(encoding="utf-8").strip() if STOP_FILE.exists() else None,
             safety_aborted=STOP_FILE.exists() and STOP_FILE.read_text(encoding="utf-8").startswith(expl_profile.SAFETY_MARK))
    print(json.dumps(o.get("passes"), indent=1), o.get("decisions_by_arm"))


E6A_PLAN = {1: (("DEB", None), ("SC", 95)), 2: (("SC", None),)}     # D-82/D-88: (arm, max new decisions)
E6A_CALL_CAP = 870                                                   # per server start; the D-78 slowdown came at 871


def call_log_lines(p) -> int:
    d = expl_profile.resolve(p["call_log_dir"])
    return sum(sum(1 for _ in open(f, encoding="utf-8")) for f in d.glob("*.jsonl") if not f.name.startswith("_"))


def cmd_e6a(p, session: int):
    """E6a (D-82, D-88): complete the 35b in two server starts, each below 871 calls; exploratory, as the 35b."""
    if not outcome().get("feasibility_ok"):
        raise SystemExit("feasibility has not passed; not running")
    if expl_profile.past_deadline(p):
        raise SystemExit("past the D-67 deadline; not starting")
    done = outcome().get("e6a", {})
    if str(session) in done:
        raise SystemExit(f"E6a session {session} already recorded")
    if session == 2 and "1" not in done:
        raise SystemExit("E6a session 1 has not run")
    if ollama_server.is_up(ollama_server.DEFAULT_URL):
        r = py("scripts/local/session_check.py", "--end")
        log(p, "frozen_session_end", exit=r.returncode)
        ollama_server.stop()
    if ollama_server.is_up(p["base_url"]):
        ollama_server.stop(p["base_url"])            # a fresh start for every session (D-82)
    env = ollama_server.start_profile(p, tag=f"expl35b_e6a_s{session}")
    log(p, "e6a_server_start", session=session, env=env, **server_info(p))
    evt = threading.Event()
    th = threading.Thread(target=lambda: watchdog(p, evt), daemon=True)
    th.start()
    n0, rec = call_log_lines(p), {"start_utc": utc(), "passes": {}}
    for arm, cap in E6A_PLAN[session]:
        if STOP_FILE.exists() or expl_profile.past_deadline(p):
            break
        t0 = time.time()
        r = py("scripts/run_experiment.py", EXP, "--only-arm", arm, "--workers", "1",
               *(["--max-tasks", cap] if cap else []))
        logf = ROOT / "logs" / "runs" / f"e6a_s{session}_{arm}.log"
        logf.parent.mkdir(parents=True, exist_ok=True)
        with open(logf, "a", encoding="utf-8") as f:
            f.write(f"=== {utc()} ===\n{r.stdout}\n{r.stderr}\nexit {r.returncode}\n")
        rec["passes"][arm] = {"exit": r.returncode, "wall_s": round(time.time() - t0, 1), "max_tasks": cap,
                              "stopped": "STOPPED ON REQUEST" in r.stdout, "end_utc": utc()}
        log(p, "e6a_pass_end", session=session, arm=arm, **rec["passes"][arm])
        if r.returncode != 0 or rec["passes"][arm]["stopped"]:
            break
    evt.set()
    th.join(timeout=5)
    ollama_server.stop(p["base_url"])
    log(p, "e6a_server_stop", session=session)
    rec.update(end_utc=utc(), calls=call_log_lines(p) - n0, call_cap=E6A_CALL_CAP,
               stop_reason=STOP_FILE.read_text(encoding="utf-8").strip() if STOP_FILE.exists() else None)
    rec["within_cap"] = rec["calls"] <= E6A_CALL_CAP
    save(e6a={**done, str(session): rec}, decisions_by_arm=decisions_by_arm())
    print(json.dumps(rec, indent=1), decisions_by_arm())


def cmd_finish(p):
    ollama_server.stop(p["base_url"])
    log(p, "server_stop")
    if STOP_FILE.exists() and STOP_FILE.read_text(encoding="utf-8").startswith(TOOL_MARKS):
        STOP_FILE.unlink()          # created by the time box or the D-78 safety rule, not by the authors
    ollama_server.start(tag="frozen_after_35b")
    r = py("scripts/local/session_check.py", "--start")
    save(frozen_restart_utc=utc(), session_check_exit=r.returncode, session_check_tail=r.stdout[-1500:] + r.stderr[-800:])
    log(p, "frozen_restarted", session_check_exit=r.returncode)
    print(r.stdout[-1500:], r.stderr[-800:], f"session_check exit {r.returncode}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["feasibility", "run", "e6a", "finish"])
    ap.add_argument("--session", type=int, choices=[1, 2], help="e6a: which of the two server starts (D-88)")
    a = ap.parse_args()
    p = expl_profile.load()
    if a.step == "e6a":
        return cmd_e6a(p, a.session)
    {"feasibility": cmd_feasibility, "run": cmd_run, "finish": cmd_finish}[a.step](p)


if __name__ == "__main__":
    main()
