"""KUU-NG (D-109): a KUU panel with no generator-family judge — M1 (Qwen), E6b (Ministral) and a fourth-family judge.

    python scripts/local/kuung.py begin    # frozen server: session_check --start, then --end; stop it
    python scripts/local/kuung.py select   # fourth-family judge: phi4, then llama3.1 — Step 1 as judge, then dev gates
                                           # G-a and G-b (G-c/G-d reported), exactly the E6b rules (D-82/D-85)
    python scripts/local/kuung.py run      # fresh J1 at S1, replicate 30, on D1-test and D2: M1, E6b, the selected judge
    python scripts/local/kuung.py finish   # stop KUU-NG servers, restart the frozen server, session_check --start

Each member runs on its own profile, port, call log and safety log with the stopping rule armed; a member that ends with
a non-zero exit, a stop or a safety abort halts the run, with no retry. The votes are combined offline by
scripts/analysis/kuung_analysis.py (no call). If no candidate passes, KUU-NG is reported as not run.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "local"))

from triage import expl_profile, ollama_server  # noqa: E402
from triage.io_utils import append_jsonl, dump_json  # noqa: E402
from triage.spec_inference import model_slug  # noqa: E402

import e6b  # noqa: E402  (spec_from_server, py: shared, unchanged)

PROFILE = expl_profile.KUUNG_PROFILE_FILE
SELECTION = ROOT / "results" / "kuung" / "selection.json"
DEV_EXP = ROOT / "configs" / "experiments" / "LOCAL_DEV_KUUNG_CHECK.json"
SESSION_LOG = ROOT / "logs" / "sessions_kuung.jsonl"
MEMBERS = [(f"LOCAL_HO_KUUNG_{ds}_{w}", f) for w, f in (("M1", ROOT / "configs" / "kuu_m1.json"),
                                                      ("E6B", expl_profile.E6B_PROFILE_FILE),
                                                      ("NG", PROFILE)) for ds in ("D1", "D2")]


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def log(event, **kw):
    append_jsonl(SESSION_LOG, {"utc": utc(), "event": event, **kw})


def load():
    return json.loads(PROFILE.read_text(encoding="utf-8"))


def save(p):
    PROFILE.write_text(json.dumps(p, indent=2) + "\n", encoding="utf-8")


def stop_all():
    for f in (ROOT / "configs" / "kuu_m1.json", expl_profile.E6B_PROFILE_FILE, PROFILE):
        p = json.loads(Path(f).read_text(encoding="utf-8"))
        if ollama_server.is_up(p["base_url"]):
            ollama_server.stop(p["base_url"])
    if ollama_server.is_up():
        ollama_server.stop()


def cmd_begin(_a):
    if not ollama_server.is_up():
        ollama_server.start(tag="frozen_before_kuung")
    r1, r2 = e6b.py("scripts/local/session_check.py", "--start"), e6b.py("scripts/local/session_check.py", "--end")
    log("frozen_session_check", start_exit=r1.returncode, end_exit=r2.returncode)
    print(r1.stdout[-500:])
    if r1.returncode != 0:
        raise SystemExit("frozen session_check --start failed; not starting KUU-NG")
    ollama_server.stop()


def try_candidate(tag):
    from triage.ollama import OllamaAPI
    p = load()
    stop_all()
    env = ollama_server.start_profile(expl_profile.load(PROFILE), tag="kuung")   # port-only settings; no model loaded
    log("server_start", env=env, candidate=tag)
    api = OllamaAPI(p["base_url"], timeout_s=p["first_response_timeout_s"])
    p = load()
    p.update(model_tag=tag, model_spec=e6b.spec_from_server(api, tag))
    p["safety"]["max_median_latency_s"] = None
    save(p)
    rec = {"tag": tag, "utc": utc(), "spec": {k: p["model_spec"][k] for k in ("digest", "quantization", "parameter_size", "family", "think")}}
    r = e6b.py("scripts/local/feasibility.py", "--model", tag, "--role", "judge", "--profile", PROFILE, timeout=6 * 3600)
    f = ROOT / p["feasibility_dir"] / f"{model_slug(tag)}.json"
    feas = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    v = feas.get("verdict", {})
    rec.update(step1_exit=r.returncode, step1_passes=bool(v.get("passes")), step1_verdict=v,
               step1_median_wall_s=(feas.get("summary") or {}).get("median_wall_s"), step1_tail=(r.stdout + r.stderr)[-1500:])
    log("step1", tag=tag, passes=rec["step1_passes"], exit=r.returncode)
    if not rec["step1_passes"]:
        return rec
    p = load()
    p["safety"]["max_median_latency_s"] = round(3 * rec["step1_median_wall_s"], 3)      # fixed before any dev call
    save(p)
    r = e6b.py("scripts/run_experiment.py", DEV_EXP, "--workers", "1")
    run = ROOT / "results" / "dev" / f"CHECK_KUUNG_{model_slug(tag)}"
    g = e6b.py("scripts/local/dev_gates.py", "--run", run, "--required", "a,b", "--baselines-from", "results/dev/GATE_M1b",
               "--call-log-dir", p["call_log_dir"])
    gates = json.loads((run / "dev_gates.json").read_text(encoding="utf-8")) if (run / "dev_gates.json").exists() else {}
    rec.update(dev_run_exit=r.returncode, dev_run_tail=(r.stdout + r.stderr)[-1200:], gates_exit=g.returncode,
               G_a=gates.get("G_a"), G_b=gates.get("G_b"), G_c=gates.get("G_c"), G_d=gates.get("G_d"),
               selected=bool(gates.get("G_a")) and bool(gates.get("G_b")))
    if r.returncode != 0 or g.returncode != 0 or not gates:      # D-86: a harness failure is not a candidate failure
        rec.update(selected=False, harness_error=True, gates_tail=(g.stdout + g.stderr)[-1500:])
    log("dev_gates", tag=tag, G_a=rec["G_a"], G_b=rec["G_b"], selected=rec["selected"],
        harness_error=rec.get("harness_error", False))
    return rec


def cmd_select(_a):
    p = load()
    out = json.loads(SELECTION.read_text(encoding="utf-8")) if SELECTION.exists() else {"order": p["candidate_order"], "tried": []}
    if out.get("selected"):
        print("already selected:", out["selected"])
        return
    done = {t["tag"] for t in out["tried"] if not t.get("harness_error")}
    for tag in p["candidate_order"]:
        if tag in done:
            continue
        if expl_profile.STOP_FILE_PATH().exists():
            print("logs/STOP present; stopping before", tag)
            break
        rec = try_candidate(tag)
        out["tried"].append(rec)
        SELECTION.parent.mkdir(parents=True, exist_ok=True)
        dump_json(SELECTION, out)
        print(tag, "step1", rec["step1_passes"], "gates", rec.get("G_a"), rec.get("G_b"), flush=True)
        if rec.get("harness_error"):
            raise SystemExit(f"{tag}: harness error in the dev run or the gate script; selection halted (D-86)")
        if rec.get("selected"):
            out["selected"] = tag
            dump_json(SELECTION, out)
            break
    else:
        out["selected"] = None
        out["note"] = "no candidate passed Step 1 and gates G-a/G-b: KUU-NG reported as not run (D-109)"
        dump_json(SELECTION, out)
    stop_all()
    print(json.dumps({k: v for k, v in out.items() if k != "tried"}, indent=1))


def cmd_run(_a):
    sel = json.loads(SELECTION.read_text(encoding="utf-8")) if SELECTION.exists() else {}
    if not sel.get("selected") or load()["model_tag"] != sel["selected"]:
        raise SystemExit("no selected KUU-NG judge in the profile; run `select` first")
    if ollama_server.is_up():
        raise SystemExit("the frozen server is up; run `begin` first")
    for name, f in MEMBERS:
        status = ROOT / "results" / "runs_local" / name / "run_status.json"
        if expl_profile.STOP_FILE_PATH().exists():
            raise SystemExit(f"logs/STOP present; stopping before {name}")
        p = expl_profile.load(f)
        stop_all()
        env = ollama_server.start_profile(p, tag=f"kuung_{name[-2:].lower()}")
        log("server_start", member=name, model=p["model_tag"], env=env)
        t0 = time.time()
        r = e6b.py("scripts/run_experiment.py", ROOT / "configs" / "experiments" / f"{name}.json", "--workers", "1")
        logf = ROOT / "logs" / "runs" / f"kuung_{name}.log"
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
            raise SystemExit(f"{name} did not complete (exit {r.returncode}, stopped={stopped}); KUU-NG halted, no retry")


def cmd_finish(_a):
    stop_all()
    stop = expl_profile.STOP_FILE_PATH()
    if stop.exists() and stop.read_text(encoding="utf-8").startswith(expl_profile.SAFETY_MARK):
        print("safety stop:", stop.read_text(encoding="utf-8").strip())
        stop.unlink()
    ollama_server.start(tag="frozen_after_kuung")
    r = e6b.py("scripts/local/session_check.py", "--start")
    log("frozen_restarted", session_check_exit=r.returncode)
    print(r.stdout[-600:], f"session_check exit {r.returncode}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["begin", "select", "run", "finish"])
    a = ap.parse_args()
    {"begin": cmd_begin, "select": cmd_select, "run": cmd_run, "finish": cmd_finish}[a.step](a)


if __name__ == "__main__":
    main()
