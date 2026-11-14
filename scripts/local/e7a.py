"""E7a second generator (D-82, D-91, D-100): selection on dev by D-22, then the test corpus, then judging by M1.

    python scripts/local/e7a.py begin    # frozen server: session_check --start/--end; stop it
    python scripts/local/e7a.py select   # per candidate in order: register, Step 1 (generator probes), dev generation,
                                         # CPU execution in the frozen WSL distro, select_g.py (D-22/D-22a); stop at a pass
    python scripts/local/e7a.py test     # the selected generator: test generation, execution, build_dataset D1G2
    python scripts/local/e7a.py judge    # frozen server: M1 judges the D1G2 test sample (LOCAL_HO_E7A_M1)
    python scripts/local/e7a.py finish   # stop the E7a server, restart the frozen server, session_check --start

Generation uses the frozen generator prompt set v0 (the one G used, verified byte-identical on G's logged prompts), the
frozen context (num_ctx 8,192, num_predict 4,096; D-91) and G's generation decoding, three generations per focal
method, through the profile's own server and call log with the stopping rule armed. Execution reuses
scripts/run_execution.py unchanged in the frozen distro; labelling, de-duplication and sampling reuse
scripts/build_dataset.py unchanged (D-53 proportional reading for test) under the dataset name D1G2. The selection
record is results/e7a/selection.json.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "local"))

import e6b  # noqa: E402
from triage import config, expl_profile, ollama_server  # noqa: E402
from triage.io_utils import append_jsonl, dump_json  # noqa: E402
from triage.spec_inference import model_slug  # noqa: E402

PROFILE = expl_profile.E7A_PROFILE_FILE
SELECTION = ROOT / "results" / "e7a" / "selection.json"
DATASET = "D1G2"
PROMPT_SET = "v0"
WSL = ["wsl", "-d", "Ubuntu-22.04", "--", "bash", "scripts/wsl/run.sh"]


def load():
    return json.loads(PROFILE.read_text(encoding="utf-8"))


def save(p):
    PROFILE.write_text(json.dumps(p, indent=2) + "\n", encoding="utf-8")


def log(p, event, **kw):
    append_jsonl(expl_profile.resolve(p["session_log"]), {"utc": e6b.utc(), "event": event, **kw})


def dirs(tag):
    s = model_slug(tag)
    return config.INTERIM / f"candidates_{s}", config.RAW / f"executions_{s}"


def ensure_server(p):
    if ollama_server.is_up(ollama_server.DEFAULT_URL):
        ollama_server.stop()
    if not ollama_server.is_up(p["base_url"]):
        log(p, "server_start", env=ollama_server.start_profile(p, tag="e7a"))


def generate(split: str) -> dict:
    """Three generations per focal method of the split with the profile's generator (idempotent per candidate)."""
    from _common import load_contexts, make_client
    from triage.generation import generate as gen_one
    from triage.prompts import PromptSet
    p = load()
    ensure_server(p)
    client, prompts = make_client(local=True, profile=p), PromptSet.named(PROMPT_SET)
    cdir, _ = dirs(p["model_tag"])
    cdir.mkdir(parents=True, exist_ok=True)
    ctxs = list(load_contexts(split).values())
    client.scope.check_split(split, "(E7a generation)")         # as generate_tests.py: approved splits and items only
    client.scope.check_items(ctxs, "focal method")
    n = ok = 0
    for ctx in ctxs:
        for g in range(config.GENERATIONS_PER_FOCAL):
            if expl_profile.STOP_FILE_PATH().exists():
                raise SystemExit("logs/STOP present; generation stopped")
            c = gen_one(ctx, client, prompts, p["model_tag"], g)
            dump_json(cdir / f"{c['candidate_id']}.json", c)
            n += 1
            ok += bool(c["assembled"])
    log(p, "generated", split=split, candidates=n, assembled=ok)
    return {"candidates": n, "assembled": ok}


def execute(tag: str) -> int:
    cdir, edir = dirs(tag)
    rel = lambda q: str(q.relative_to(ROOT)).replace("\\", "/")
    r = subprocess.run(WSL + ["scripts/run_execution.py", "--candidates", rel(cdir), "--out", rel(edir), "--workers", "6"],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    logf = ROOT / "logs" / "runs" / f"exec_e7a_{model_slug(tag)}.log"
    logf.parent.mkdir(parents=True, exist_ok=True)
    with open(logf, "a", encoding="utf-8") as fh:
        fh.write(f"=== {e6b.utc()} ===\n{r.stdout}\n{r.stderr}\nexit {r.returncode}\n")
    return r.returncode


def cmd_begin(_a):
    p = load()
    if not ollama_server.is_up():
        ollama_server.start(tag="frozen_before_e7a")
    r1, r2 = e6b.py("scripts/local/session_check.py", "--start"), e6b.py("scripts/local/session_check.py", "--end")
    log(p, "frozen_session_check", start_exit=r1.returncode, end_exit=r2.returncode)
    print(r1.stdout[-500:])
    if r1.returncode != 0:
        raise SystemExit("frozen session_check --start failed; not starting E7a")
    ollama_server.stop()


def cmd_select(_a):
    from triage.ollama import OllamaAPI
    out = json.loads(SELECTION.read_text(encoding="utf-8")) if SELECTION.exists() else {"order": load()["candidate_order"],
                                                                                        "tried": []}
    if out.get("selected"):
        print("already selected:", out["selected"])
        return
    done = {t["tag"] for t in out["tried"]}
    for tag in load()["candidate_order"]:
        if tag in done:
            continue
        p = load()
        ensure_server(p)
        spec = e6b.spec_from_server(OllamaAPI(p["base_url"], timeout_s=p["first_response_timeout_s"]), tag)
        spec["require_gpu_resident"] = False           # generator role: partial offload allowed (Step 1, D-39/D-40)
        p.update(model_tag=tag, model_spec=spec)
        p["safety"]["max_median_latency_s"] = None
        save(p)
        rec = {"tag": tag, "utc": e6b.utc(), "digest": spec["digest"]}
        r = e6b.py("scripts/local/feasibility.py", "--model", tag, "--role", "generator", "--profile", PROFILE, timeout=6 * 3600)
        f = ROOT / "results" / "dev" / "feasibility" / f"{model_slug(tag)}.json"
        feas = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        v = feas.get("verdict", {})
        rec.update(step1_exit=r.returncode, step1_verdict=v, step1_median_wall_s=(feas.get("summary") or {}).get("median_wall_s"),
                   step1_g_feasible=bool(v.get("context_length_8192") and v.get("thinking_off_empty_all")))
        log(p, "step1", tag=tag, g_feasible=rec["step1_g_feasible"], exit=r.returncode)
        if rec["step1_g_feasible"] and rec["step1_median_wall_s"]:
            p = load()
            p["safety"]["max_median_latency_s"] = round(3 * rec["step1_median_wall_s"], 3)   # before any dev generation
            save(p)
            rec["dev_generation"] = generate("dev")
            ollama_server.stop(p["base_url"])
            rec["dev_execution_exit"] = execute(tag)
            g = e6b.py("scripts/local/select_g.py", "--model", tag)
            sel = ROOT / "results" / "dev" / f"g_selection_{model_slug(tag)}.json"
            res = json.loads(sel.read_text(encoding="utf-8")) if sel.exists() else {}
            rec.update(select_g_exit=g.returncode, verdict=res.get("verdict"), C1=res.get("C1"), C2=res.get("C2"),
                       P1=res.get("P1"), selected=bool(res.get("selected")))
        else:
            rec["selected"] = False
        out["tried"].append(rec)
        dump_json(SELECTION, out)
        print(tag, json.dumps({k: rec.get(k) for k in ("step1_g_feasible", "C1", "C2", "P1", "selected")}), flush=True)
        if rec.get("selected"):
            out["selected"] = tag
            dump_json(SELECTION, out)
            return
    out["selected"] = None
    out["note"] = "no candidate passed D-22/D-22a on dev: E7a reported as not run"
    dump_json(SELECTION, out)


def cmd_test(_a):
    sel = json.loads(SELECTION.read_text(encoding="utf-8"))
    p = load()
    if not sel.get("selected") or p["model_tag"] != sel["selected"]:
        raise SystemExit("no selected E7a generator in the profile; run `select` first")
    t0 = time.time()
    res = generate("test")
    ollama_server.stop(p["base_url"])
    rc = execute(p["model_tag"])
    cdir, edir = dirs(p["model_tag"])
    b = e6b.py("scripts/build_dataset.py", "--dataset", DATASET, "--candidates", cdir, "--executions", edir)
    log(p, "test_built", generation=res, execution_exit=rc, build_exit=b.returncode, wall_s=round(time.time() - t0, 1))
    print(res, "execution", rc, "build", b.returncode, b.stdout[-800:], b.stderr[-800:])


def cmd_judge(_a):
    if not ollama_server.is_up():
        ollama_server.start(tag="frozen_e7a_judge")
    r = e6b.py("scripts/local/session_check.py", "--start")
    if r.returncode != 0:
        raise SystemExit("frozen session_check --start failed")
    j = e6b.py("scripts/run_experiment.py", ROOT / "configs" / "experiments" / "LOCAL_HO_E7A_M1.json", "--workers", "1")
    print(j.stdout[-1500:], j.stderr[-800:], "exit", j.returncode)
    print(e6b.py("scripts/local/session_check.py", "--end").stdout[-300:])


def cmd_finish(_a):
    p = load()
    ollama_server.stop(p["base_url"])
    stop = expl_profile.STOP_FILE_PATH()
    if stop.exists() and stop.read_text(encoding="utf-8").startswith(expl_profile.SAFETY_MARK):
        stop.unlink()
    if not ollama_server.is_up():
        ollama_server.start(tag="frozen_after_e7a")
    print(e6b.py("scripts/local/session_check.py", "--start").stdout[-500:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["begin", "select", "test", "judge", "finish"])
    a = ap.parse_args()
    {"begin": cmd_begin, "select": cmd_select, "test": cmd_test, "judge": cmd_judge, "finish": cmd_finish}[a.step](a)


if __name__ == "__main__":
    main()
