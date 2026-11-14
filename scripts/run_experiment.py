"""Run one experiment configuration (configs/experiments/*.json). PAID unless --mock.

    python scripts/run_experiment.py configs/experiments/PILOT_dev.json [--workers 16] [--max-tasks N] [--mock]

Every evidence package is checked against data/leakage_guard/guard_<dataset>.jsonl before any model call.
A real (non-mock) run refuses to start if that file is missing or does not cover every instance.
"""
import argparse
import json
import sys
from pathlib import Path

from _common import config, make_client
from triage.io_utils import dump_json, read_jsonl
from triage.prompts import PromptSet
from triage.runner import Runner, load_specs
from triage.spec_inference import SPEC_CACHE, model_slug


def _p(x) -> Path:
    x = Path(x)
    return x if x.is_absolute() else config.ROOT / x


def load_guard(path: Path) -> dict:
    return {r["instance_id"]: r for r in read_jsonl(path)}


def execute(exp: dict, client, run_dir: Path, workers: int = 16, max_tasks: int | None = None,
            require_guard: bool = True) -> Runner:
    """The live entry point used by main() and by tests."""
    local = exp.get("backend") == "ollama"
    if local:
        from triage.ollama import load_local_models
        roles = load_local_models()["roles"]
        model_id = exp.get("model_tag") or roles.get(exp["model"], exp["model"])   # model_tag: D-55 exploratory
        spec_model_id = roles["M1"]
    else:
        model_id = config.MODELS[exp["model"]]["id"] if exp["model"] in config.MODELS else exp["model"]
        spec_model_id = config.MODELS["M1"]["id"]
    ds, split = exp["dataset"], exp["split"]
    inst_file = _p(exp.get("instances_file", config.PROCESSED / f"instances_{ds}.jsonl"))
    sample_file = _p(exp.get("sample_file", config.PROCESSED / f"sample_{ds}_{split}.json"))
    guard_file = _p(exp.get("guard_file", config.LEAKAGE_GUARD / f"guard_{ds}.jsonl"))
    keep = set(json.loads(sample_file.read_text())["instance_ids"])
    instances = [i for i in read_jsonl(inst_file) if i["instance_id"] in keep]
    wrong_split = [i["instance_id"] for i in instances if i.get("split") != split]
    if wrong_split:
        raise SystemExit(f"{len(wrong_split)} sampled instances are not in split {split!r}; refusing to run")
    if getattr(client, "scope", None) is not None:   # paid or local run: approved scope only
        client.scope.check_experiment(exp["name"])
        client.scope.check_dataset(ds, f"(experiment {exp['name']})")
        client.scope.check_split(split, f"(experiment {exp['name']})")
        client.scope.check_items(instances, "instance")
    guard = load_guard(guard_file) if guard_file.exists() else {}
    missing = [i["instance_id"] for i in instances if i["instance_id"] not in guard]
    if require_guard and (not guard_file.exists() or missing):
        raise SystemExit(f"leakage guard {guard_file} missing or incomplete ({len(missing)} instances uncovered)")
    if local and exp.get("requires_ram_precondition") and hasattr(client.backend, "spec"):
        from triage.sessions import g_session_start      # D-40 / D-55: >= 4 GiB available after the model loads
        kw = {"log": _p(exp["session_log"])} if exp.get("session_log") else {}   # D-76: the 35b logs to its own file
        if exp.get("ram_gate_min_gib") is not None:                                 # D-78: 35b only
            kw["min_available_gib"] = exp["ram_gate_min_gib"]
        g_session_start(client.backend.api, model_id, client.backend.spec(model_id), **kw)
    spec_model = model_slug(spec_model_id)  # M2 reuses M1's specification (Sec. 3.6.1)
    specs = load_specs(_p(exp.get("specs_file", SPEC_CACHE / f"S2__{spec_model}.jsonl")))
    specs_p = load_specs(_p(exp.get("specs_prime_file", SPEC_CACHE / f"S2prime__{spec_model}.jsonl")))
    prompts = PromptSet.named(exp["prompt_set"])
    for c in exp["conditions"]:
        if c.get("arm") == "SC-T" and not isinstance(c.get("k"), int):
            raise SystemExit("SC-T k must be set from pilot gate P4 before running (see EXPERIMENT_STATUS.md)")
    frozen_sha = None
    if local:
        from triage.io_utils import sha256_text
        from triage.ollama import FROZEN_MODELS_FILE
        if FROZEN_MODELS_FILE.exists():
            frozen = json.loads(FROZEN_MODELS_FILE.read_text(encoding="utf-8"))
            frozen_sha = sha256_text(FROZEN_MODELS_FILE.read_text(encoding="utf-8"))
            if split != "dev" and prompts.set_hash() != frozen["prompt_set"]["set_hash"]:
                raise SystemExit(f"prompt set {exp['prompt_set']} does not match the frozen prompt hash; refusing")
        elif split != "dev":
            raise SystemExit("held-out local runs require configs/local_models.FROZEN.json (Step 6)")
    dump_json(run_dir / "experiment.json", {**exp, "model_id": model_id, "prompt_set_hash": prompts.set_hash(),
                                            "frozen_config_sha256": frozen_sha,
                                            "prompt_hashes": prompts.hashes(), "n_instances": len(instances),
                                            "guard_file": str(guard_file), "guard_entries": len(guard)})
    r = Runner(run_dir, client, prompts, model_id, specs, specs_p, workers=workers, forbidden=guard,
               require_guard=require_guard)
    r.run(instances, exp["conditions"], exp.get("replicates", config.REPLICATES), max_tasks)
    return r


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("experiment")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--max-tasks", type=int)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--replay", action="store_true", help="recompute decisions from the call log only (no key, no calls)")
    ap.add_argument("--prompt-set", help="fills the <set> placeholder of a prompt-development config")
    ap.add_argument("--only-arm", help="run one arm's conditions only (D-67: the 35b runs J1, then DEB, then SC)")
    a = ap.parse_args(argv)
    exp = json.loads(Path(a.experiment).read_text())
    if a.prompt_set:
        exp = {k: (v.replace("<set>", a.prompt_set) if isinstance(v, str) else v) for k, v in exp.items()}
    if "<set>" in json.dumps(exp):
        raise SystemExit("this config has a <set> placeholder: pass --prompt-set")
    if a.only_arm:
        exp = {**exp, "conditions": [c for c in exp["conditions"] if c["arm"] == a.only_arm]}
        if not exp["conditions"]:
            raise SystemExit(f"no condition with arm {a.only_arm!r} in {a.experiment}")
    base = config.ROOT / "results" / "smoke" if a.mock else (config.RESULTS / "replay" if a.replay else config.RESULTS / "runs")
    local = exp.get("backend") == "ollama" and not a.mock
    if local and not a.replay:
        base = config.RESULTS / "dev" if exp.get("split") == "dev" else config.RESULTS / "runs_local"
    from triage import expl_profile
    profile = expl_profile.for_experiment(exp["name"]) if local and not a.replay else None   # D-67
    if profile is not None and exp.get("model_tag") == "{profile}":   # D-85: the E6b candidate under test
        if not profile.get("model_tag") or not profile.get("model_spec"):
            raise SystemExit(f"{exp['name']}: profile has no registered candidate (run scripts/local/e6b.py register)")
        gate = profile.get("selection_gated", {})                  # D-87: held-out only for the selected candidate
        if exp["name"] in gate.get("experiments", []):
            sel_f = expl_profile.resolve(gate["selection_file"])
            sel = json.loads(sel_f.read_text(encoding="utf-8")).get("selected") if sel_f.exists() else None
            if sel != profile["model_tag"]:
                raise SystemExit(f"{exp['name']}: {profile['model_tag']} is not the selected candidate ({sel}); refusing")
        exp = {**exp, "model_tag": profile["model_tag"],
               "run_label": exp.get("run_label", exp["name"]).replace("{model}", model_slug(profile["model_tag"]))}
    run_dir = base / exp.get("run_label", exp["name"])   # run_label: folder per round; name: scope-checked
    if profile is not None:
        exp = {**exp, "session_log": profile["session_log"], "ram_gate_min_gib": profile["safety"]["min_available_gib"],
               "label": profile["label"], "differences_from_M1": profile["differences_from_M1"],
               "decisions": profile.get("decisions", ["D-55", "D-67", "D-76", "D-78"])}
    if profile is not None and expl_profile.past_deadline(profile):
        raise SystemExit(f"{exp['name']}: past its compute deadline {profile['deadline_local']} (D-67 time box)")
    execute(exp, make_client(a.mock, a.replay, local=local, profile=profile), run_dir, a.workers, a.max_tasks)


if __name__ == "__main__":
    sys.exit(main())
