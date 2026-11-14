"""Revision-pass local runs (D-123 to D-127) on a dedicated Ollama server (port 11441) with the D-109 stopping rule.

    python scripts/local/revision_runs.py begin           # frozen server: session_check --start, --end; stop it
    python scripts/local/revision_runs.py run NAME [...]  # configs/revision/NAME.json, one model at a time
    python scripts/local/revision_runs.py finish          # stop the revision server, restart the frozen one, check

Each run takes its member's existing profile (spec, digest, latency limit unchanged), moves it to port 11441 and the
revision log directories, and runs the stock Runner with the frozen prompts and the leakage guard. A client wrapper may
change only what the run config names (temperature, output-token cap; `think`/`num_ctx` for D-126); every change is
written into the run's experiment.json. A run that ends with an error, a stop or a safety abort halts the sequence,
with no retry and no setting change.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "local"))

from triage import config, expl_profile, ollama_server  # noqa: E402
from triage.io_utils import append_jsonl, dump_json, read_jsonl, sha256_text  # noqa: E402

PORT = "127.0.0.1:11441"
CFG_DIR = ROOT / "configs" / "revision"
RUN_DIR = ROOT / "results" / "revision" / "runs"
SESSION_LOG = ROOT / "logs" / "sessions_revision.jsonl"
MEMBERS = {"M1": ROOT / "configs" / "kuu_m1.json", "M2": ROOT / "configs" / "kuu_m2.json",
           "E6B": ROOT / "configs" / "e6b.json", "NG": ROOT / "configs" / "kuung.json"}
REVISION = {"server_env_overrides": {"OLLAMA_HOST": PORT}, "base_url": f"http://{PORT}",
            "server_log_dir": "logs/ollama_server_revision", "call_log_dir": "data/raw/llm_calls_local_revision",
            "session_log": "logs/sessions_revision.jsonl", "safety_events": "results/revision/safety_events.jsonl",
            "deadline_local": "2026-11-12T23:59:00"}


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def log(event, **kw):
    append_jsonl(SESSION_LOG, {"utc": utc(), "event": event, **kw})


def profile_for(run: dict) -> dict:
    """The member's committed profile, moved to the revision server and logs; spec patched only as the run names."""
    base = expl_profile.load(MEMBERS[run["member"]])          # validates the committed profile unchanged
    p = {**base, **REVISION, "safety": dict(base["safety"])}
    p["model_spec"] = {**base["model_spec"], **run.get("spec_patch", {})}
    if run.get("max_median_latency_s") is not None:
        p["safety"]["max_median_latency_s"] = run["max_median_latency_s"]
    p["safety"]["decision"] = "D-123 (the D-109 stopping rule)"
    return p


class Wrapped:
    """Passes every call to the LLMClient, setting only the named options (D-123)."""

    def __init__(self, client, temperature=None, max_tokens=None):
        self.client, self.temperature, self.max_tokens = client, temperature, max_tokens

    def __getattr__(self, name):
        return getattr(self.client, name)

    def complete(self, **kw):
        if self.temperature is not None:
            kw["temperature"] = self.temperature
        if self.max_tokens is not None:
            kw["max_tokens"] = self.max_tokens
        return self.client.complete(**kw)


def py(*args, timeout=None):
    import subprocess
    return subprocess.run([sys.executable, *map(str, args)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)


def stop_revision():
    if ollama_server.is_up(REVISION["base_url"]):
        ollama_server.stop(REVISION["base_url"])


def cmd_begin(_a):
    if not ollama_server.is_up():
        ollama_server.start(tag="frozen_before_revision")
    r1, r2 = py("scripts/local/session_check.py", "--start"), py("scripts/local/session_check.py", "--end")
    log("frozen_session_check", start_exit=r1.returncode, end_exit=r2.returncode)
    print(r1.stdout[-400:])
    if r1.returncode != 0:
        raise SystemExit("frozen session_check --start failed; not starting the revision runs")
    ollama_server.stop()


def run_one(name: str):
    from triage.llm import LLMClient
    from triage.ollama import FROZEN_MODELS_FILE, OllamaAPI
    from triage.prompts import PromptSet
    from triage.runner import Runner, load_specs
    from triage.scope import require
    from triage.sessions import g_session_start
    from triage.spec_inference import SPEC_CACHE, model_slug
    run = json.loads((CFG_DIR / f"{name}.json").read_text(encoding="utf-8"))
    p = profile_for(run)
    if expl_profile.past_deadline(p):
        raise SystemExit(f"{name}: past the compute deadline {p['deadline_local']}")
    if expl_profile.STOP_FILE_PATH().exists():
        raise SystemExit(f"logs/STOP present; not starting {name}")
    scope = require(ROOT / "configs" / "local_scope.json")
    scope.check_experiment(name)
    scope.check_model(p["model_tag"], {"digest": p["model_spec"]["digest"]}, local=True)
    samp = json.loads((ROOT / run["sample_file"]).read_text(encoding="utf-8"))
    keep = set(samp["instance_ids"])
    instances = [i for i in read_jsonl(config.PROCESSED / f"instances_{run['dataset']}.jsonl") if i["instance_id"] in keep]
    if len(instances) != len(keep) or any(i.get("split") != run["split"] for i in instances):
        raise SystemExit(f"{name}: sample and instances disagree or a split differs; refusing")
    guard = {r["instance_id"]: r for r in read_jsonl(config.LEAKAGE_GUARD / f"guard_{run['dataset']}.jsonl")}
    if any(i["instance_id"] not in guard for i in instances):
        raise SystemExit(f"{name}: leakage guard incomplete; refusing")
    prompts = PromptSet.named(run["prompt_set"])
    frozen_txt = FROZEN_MODELS_FILE.read_text(encoding="utf-8")
    if run["split"] != "dev" and prompts.set_hash() != json.loads(frozen_txt)["prompt_set"]["set_hash"]:
        raise SystemExit("prompt set does not match the frozen prompt hash; refusing")
    stop_revision()
    if ollama_server.is_up():
        raise SystemExit("the frozen server is up on 11434; run `begin` first")
    env = ollama_server.start_profile(p, tag=f"revision_{name.lower()}")
    log("server_start", run=name, model=p["model_tag"], spec_patch=run.get("spec_patch", {}), env=env)
    api = OllamaAPI(p["base_url"], timeout_s=p["first_response_timeout_s"])
    for _ in range(60):
        if ollama_server.is_up(p["base_url"]):
            break
        time.sleep(1)
    client = LLMClient(expl_profile.safe_backend(p, api=api), log_dir=expl_profile.resolve(p["call_log_dir"]))
    pre_spec = {**p["model_spec"], "think": False if p["model_spec"].get("think") else p["model_spec"].get("think")}
    g_session_start(api, p["model_tag"], pre_spec, log=SESSION_LOG, min_available_gib=p["safety"]["min_available_gib"])
    wrapped = Wrapped(client, run.get("temperature"), run.get("max_tokens"))
    spec_model = model_slug(json.loads(frozen_txt)["roles"]["M1"])
    out = RUN_DIR / name
    out.mkdir(parents=True, exist_ok=True)
    dump_json(out / "experiment.json", {**run, "model_id": p["model_tag"], "model_spec": p["model_spec"],
                                        "safety": p["safety"], "server": PORT, "call_log_dir": p["call_log_dir"],
                                        "prompt_set_hash": prompts.set_hash(), "prompt_hashes": prompts.hashes(),
                                        "frozen_config_sha256": sha256_text(frozen_txt), "n_instances": len(instances),
                                        "client_overrides": {"temperature": run.get("temperature"),
                                                             "max_tokens": run.get("max_tokens")},
                                        "started_utc": utc()})
    r = Runner(out, wrapped, prompts, p["model_tag"], load_specs(SPEC_CACHE / f"S2__{spec_model}.jsonl"),
               load_specs(SPEC_CACHE / f"S2prime__{spec_model}.jsonl"), workers=1, forbidden=guard, require_guard=True)
    t0 = time.time()
    r.run(instances, run["conditions"], 1)
    stopped = expl_profile.STOP_FILE_PATH().exists()
    ollama_server.stop(p["base_url"])
    status = json.loads((out / "run_status.json").read_text(encoding="utf-8")) if (out / "run_status.json").exists() else {}
    errors = len(list(read_jsonl(out / "errors.jsonl"))) if (out / "errors.jsonl").exists() else 0
    log("run_end", run=name, wall_s=round(time.time() - t0, 1), decisions=status.get("decisions"), errors=errors,
        stopped=stopped)
    print(name, "decisions", status.get("decisions"), "errors", errors, "stopped", stopped, round(time.time() - t0), "s",
          flush=True)
    if stopped or errors:
        raise SystemExit(f"{name} did not complete cleanly (errors {errors}, stopped {stopped}); halted, no retry")


def cmd_run(a):
    for name in a.names:
        run_one(name)


def cmd_finish(_a):
    stop_revision()
    stop = expl_profile.STOP_FILE_PATH()
    if stop.exists() and stop.read_text(encoding="utf-8").startswith(expl_profile.SAFETY_MARK):
        print("safety stop:", stop.read_text(encoding="utf-8").strip())
    ollama_server.start(tag="frozen_after_revision")
    r = py("scripts/local/session_check.py", "--start")
    log("frozen_restarted", session_check_exit=r.returncode)
    print(r.stdout[-500:], f"session_check exit {r.returncode}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="step", required=True)
    sub.add_parser("begin")
    rp = sub.add_parser("run")
    rp.add_argument("names", nargs="+")
    sub.add_parser("finish")
    a = ap.parse_args()
    {"begin": cmd_begin, "run": cmd_run, "finish": cmd_finish}[a.step](a)


if __name__ == "__main__":
    main()
