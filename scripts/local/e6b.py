"""E6b third-family judge (D-82, D-85): selection in the pre-registered order, then the D1-test run.

    python scripts/local/e6b.py begin      # frozen server: session_check --start, then --end; stop it (GPU session start)
    python scripts/local/e6b.py select     # for each candidate in order: register -> Step 1 -> dev gates; stop at the first pass
    python scripts/local/e6b.py heldout    # the selected judge: J1, then SC, then DEB at S1 on D1-test, 1 replicate
    python scripts/local/e6b.py finish     # stop the E6b server, restart the frozen server, session_check --start

Rules (fixed in D-82/D-85 before any load): a candidate is selected when its Step 1 judge verdict passes
(MODEL_SELECTION_PROTOCOL: 8,192 context, fully GPU-resident, free VRAM >= 0.5 GiB, thinking empty, >= 98% valid,
probes fit) AND dev gates G-a and G-b pass (G-c/G-d reported). The latency limit of the stopping rule is written into
the profile from the candidate's own Step 1 median before any dev or test call. If no candidate passes, E6b is reported
as not run. Every step appends to the profile's session log; the selection record is results/e6b/selection.json.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import expl_profile, ollama_server  # noqa: E402
from triage.io_utils import append_jsonl, dump_json  # noqa: E402
from triage.spec_inference import model_slug  # noqa: E402

PROFILE = expl_profile.E6B_PROFILE_FILE
SELECTION = ROOT / "results" / "e6b" / "selection.json"
DEV_EXP = ROOT / "configs" / "experiments" / "LOCAL_DEV_E6B_CHECK.json"
HO_EXP = ROOT / "configs" / "experiments" / "LOCAL_HO_E6B_D1TEST.json"
SAMPLING_KEYS = ("presence_penalty", "frequency_penalty", "repeat_penalty", "repeat_last_n")


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load():
    return json.loads(PROFILE.read_text(encoding="utf-8"))


def save(p):
    PROFILE.write_text(json.dumps(p, indent=2) + "\n", encoding="utf-8")


def log(p, event, **kw):
    append_jsonl(expl_profile.resolve(p["session_log"]), {"utc": utc(), "event": event, **kw})


def py(*args, timeout=None):
    return subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)


def spec_from_server(api, tag: str) -> dict:
    """The register_models rule (D-34), written into the profile instead of a model config: digest, quantisation,
    family, the Modelfile's own sampling defaults sent explicitly; D-85: think = None when the model has no thinking
    channel (the field is then not sent), False otherwise."""
    tags = api.tags()
    if tag not in tags:
        raise SystemExit(f"{tag} is not pulled")
    show = api.show(tag)
    params = {}
    for line in (show.get("parameters") or "").splitlines():
        m = re.match(r"\s*(\w+)\s+(.+)", line)
        if m:
            params.setdefault(m.group(1), []).append(m.group(2).strip().strip('"'))
    d = show.get("details") or {}
    caps = show.get("capabilities") or []
    spec = {"family": d.get("family"), "digest": tags[tag]["digest"], "size_bytes": tags[tag].get("size"),
            "quantization": d.get("quantization_level"), "parameter_size": d.get("parameter_size"), "format": d.get("format"),
            "ollama_family": d.get("family"), "capabilities": caps, "modelfile_parameters": params, "num_ctx": 8192,
            "think": False if "thinking" in caps else None, "keep_alive": "30m",
            "top_k": int(params["top_k"][0]) if "top_k" in params else 40,
            "min_p": float(params["min_p"][0]) if "min_p" in params else 0.0, "require_gpu_resident": True}
    for k in SAMPLING_KEYS:
        if k in params:
            spec[k] = float(params[k][0]) if k != "repeat_last_n" else int(params[k][0])
    return spec


def cmd_begin(_a):
    p = load()
    if not ollama_server.is_up():
        ollama_server.start(tag="frozen_before_e6b")
    r1 = py("scripts/local/session_check.py", "--start")
    r2 = py("scripts/local/session_check.py", "--end")
    log(p, "frozen_session_check", start_exit=r1.returncode, end_exit=r2.returncode)
    print(r1.stdout[-600:], r2.stdout[-300:])
    if r1.returncode != 0:
        raise SystemExit("frozen session_check --start failed; not starting E6b")
    ollama_server.stop()


def ensure_server(p):
    if ollama_server.is_up(ollama_server.DEFAULT_URL):
        ollama_server.stop()
    if not ollama_server.is_up(p["base_url"]):
        env = ollama_server.start_profile(p, tag="e6b")
        log(p, "server_start", env=env)


def try_candidate(tag: str, prior: dict | None = None) -> dict:
    """`prior`: an earlier record of this tag that stopped on a harness error (D-86). Its Step 1 result and the
    latency limit derived from it are kept, not re-measured; the dev run resumes (idempotent) and the gates are rerun."""
    from triage.ollama import OllamaAPI
    p = load()
    ensure_server(p)
    api = OllamaAPI(p["base_url"], timeout_s=p["first_response_timeout_s"])
    p.update(model_tag=tag, model_spec=spec_from_server(api, tag))
    p["safety"]["max_median_latency_s"] = None
    save(p)
    rec = {"tag": tag, "utc": utc(), "spec": {k: p["model_spec"][k] for k in ("digest", "quantization", "parameter_size", "family", "think")}}
    if prior and prior.get("step1_passes") and prior["spec"]["digest"] == rec["spec"]["digest"]:
        rec.update({k: prior[k] for k in prior if k.startswith("step1_")}, resumed_after_harness_error=prior.get("harness_error"))
        log(p, "step1_reused", tag=tag, median_wall_s=rec["step1_median_wall_s"])
    else:
        r = py("scripts/local/feasibility.py", "--model", tag, "--role", "judge", "--profile", PROFILE, timeout=6 * 3600)
        f = expl_profile.resolve(p["feasibility_dir"]) / f"{model_slug(tag)}.json"
        feas = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        v = feas.get("verdict", {})
        rec.update(step1_exit=r.returncode, step1_passes=bool(v.get("passes")), step1_verdict=v,
                   step1_median_wall_s=(feas.get("summary") or {}).get("median_wall_s"), step1_tail=(r.stdout + r.stderr)[-1500:])
        log(p, "step1", tag=tag, passes=rec["step1_passes"], exit=r.returncode)
    if not rec["step1_passes"]:
        return rec
    p = load()
    p["safety"]["max_median_latency_s"] = round(3 * rec["step1_median_wall_s"], 3)      # fixed before any dev call
    save(p)
    r = py("scripts/run_experiment.py", DEV_EXP, "--workers", "1")
    run = ROOT / "results" / "dev" / f"CHECK_E6B_{model_slug(tag)}"
    g = py("scripts/local/dev_gates.py", "--run", run, "--required", "a,b", "--baselines-from", "results/dev/GATE_M1b",
           "--call-log-dir", p["call_log_dir"])
    gates = json.loads((run / "dev_gates.json").read_text(encoding="utf-8")) if (run / "dev_gates.json").exists() else {}
    rec.update(dev_run_exit=r.returncode, dev_run_tail=(r.stdout + r.stderr)[-1200:], gates_exit=g.returncode,
               G_a=gates.get("G_a"), G_b=gates.get("G_b"), G_c=gates.get("G_c"), G_d=gates.get("G_d"),
               selected=bool(gates.get("G_a")) and bool(gates.get("G_b")))
    if r.returncode != 0 or g.returncode != 0 or not gates:      # D-86: a harness failure is not a candidate failure
        rec.update(selected=False, harness_error=True, gates_tail=(g.stdout + g.stderr)[-1500:])
    log(p, "dev_gates", tag=tag, G_a=rec["G_a"], G_b=rec["G_b"], selected=rec["selected"],
        harness_error=rec.get("harness_error", False))
    return rec


def cmd_select(_a):
    p = load()
    out = json.loads(SELECTION.read_text(encoding="utf-8")) if SELECTION.exists() else {"order": p["candidate_order"], "tried": []}
    if out.get("selected"):
        print("already selected:", out["selected"])
        return
    last = {t["tag"]: t for t in out["tried"]}
    done = {tag for tag, t in last.items() if not t.get("harness_error")}
    for tag in p["candidate_order"]:
        if tag in done:
            continue
        if expl_profile.STOP_FILE_PATH().exists():
            print("logs/STOP present; stopping before", tag)
            break
        rec = try_candidate(tag, prior=last.get(tag))
        out["tried"].append(rec)
        dump_json(SELECTION, out)
        print(tag, "step1", rec["step1_passes"], "gates", rec.get("G_a"), rec.get("G_b"), flush=True)
        if rec.get("harness_error"):
            raise SystemExit(f"{tag}: harness error in the dev run or the gate script; selection halted (D-86), "
                             "fix and rerun `select` to resume this candidate")
        if rec.get("selected"):
            out["selected"] = tag
            dump_json(SELECTION, out)
            break
    else:
        out["selected"] = None
        out["note"] = "no candidate passed Step 1 and gates G-a/G-b: E6b reported as not run (D-82)"
        dump_json(SELECTION, out)
    print(json.dumps({k: v for k, v in out.items() if k != "tried"}, indent=1))


def cmd_heldout(_a):
    sel = json.loads(SELECTION.read_text(encoding="utf-8"))
    p = load()
    if not sel.get("selected") or p["model_tag"] != sel["selected"]:
        raise SystemExit("no selected E6b judge in the profile; run `select` first")
    if not p["safety"].get("max_median_latency_s"):
        raise SystemExit("latency limit not set from Step 1; refusing")
    ensure_server(p)
    for arm in p["arm_passes"]:
        if expl_profile.STOP_FILE_PATH().exists():
            break
        t0 = time.time()
        r = py("scripts/run_experiment.py", HO_EXP, "--only-arm", arm, "--workers", "1")
        logf = ROOT / "logs" / "runs" / f"e6b_{arm}.log"
        logf.parent.mkdir(parents=True, exist_ok=True)
        with open(logf, "a", encoding="utf-8") as fh:
            fh.write(f"=== {utc()} ===\n{r.stdout}\n{r.stderr}\nexit {r.returncode}\n")
        log(p, "pass_end", arm=arm, exit=r.returncode, wall_s=round(time.time() - t0, 1),
            stopped="STOPPED ON REQUEST" in r.stdout)
        print(arm, "exit", r.returncode, round(time.time() - t0), "s", flush=True)
        if r.returncode != 0 or "STOPPED ON REQUEST" in r.stdout:
            break


def cmd_finish(_a):
    p = load()
    ollama_server.stop(p["base_url"])
    log(p, "server_stop")
    stop = expl_profile.STOP_FILE_PATH()
    if stop.exists() and stop.read_text(encoding="utf-8").startswith(expl_profile.SAFETY_MARK):
        stop.unlink()
    ollama_server.start(tag="frozen_after_e6b")
    r = py("scripts/local/session_check.py", "--start")
    log(p, "frozen_restarted", session_check_exit=r.returncode)
    print(r.stdout[-800:], f"session_check exit {r.returncode}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["begin", "select", "heldout", "finish"])
    a = ap.parse_args()
    {"begin": cmd_begin, "select": cmd_select, "heldout": cmd_heldout, "finish": cmd_finish}[a.step](a)


if __name__ == "__main__":
    main()
