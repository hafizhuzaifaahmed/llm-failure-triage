"""Readiness gate for the CFP confirmation (D-140). Generation may start only when every check passes.

    python scripts/extension/confirm_gate.py            # full report, exit 1 unless ready
    python scripts/extension/confirm_gate.py --offline  # skip the two server checks (for preparation and tests)

The five preconditions set by the authors on 2026-11-11:
  1. the OSF registration is deposited and recorded (configs/extension/osf_registration.json), and the registered
     text is byte-for-byte the text in this repository;
  2. the default desktop Ollama server is not running;
  3. the frozen study server answers with the frozen Ollama version and the frozen generator digest;
  4. the dataset manifest and the configuration hashes validate;
  5. no frozen experimental component has changed since the pilot.
The generation driver calls `evaluate()` and refuses to run unless `ready` is true. There is no override flag.
"""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

EXT = ROOT / "configs" / "extension"
REGISTRATION = EXT / "osf_registration.json"
PREREG = ROOT / "docs" / "research_extension" / "OSF_PREREGISTRATION_CFP.md"
MANIFEST = EXT / "confirm_dataset_manifest.json"
FROZEN_MODELS = ROOT / "configs" / "local_models.FROZEN.json"
BASE = ROOT / "data" / "extension" / "confirm"
# paths that must be identical to `master` (the state the study and the pilot were run on)
IMMUTABLE = ["paper", "prompts", "configs/local_models.FROZEN.json", "data/processed", "data/ground_truth_store",
             "data/interim", "data/raw", "results/runs_local", "results/runs_frontier", "results/heldout",
             "results/revision", "docs/paper", "src/triage", "src/java"]
ENGINE_COMMIT = "eb2d231"


def content_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _freeze():
    spec = importlib.util.spec_from_file_location("freeze_cfp", ROOT / "scripts" / "extension" / "freeze_cfp.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout.strip()


def check_registration() -> tuple[bool, str]:
    if not REGISTRATION.exists():
        return False, "no OSF registration recorded (configs/extension/osf_registration.json is absent)"
    r = json.loads(REGISTRATION.read_text(encoding="utf-8"))
    missing = [k for k in ("osf_id", "url", "registered_utc", "registration_doc_sha256", "recorded_in_decision") if not r.get(k)]
    if missing:
        return False, f"registration record incomplete: {missing}"
    if r["registration_doc_sha256"] != content_hash(PREREG):
        return False, "the registered text differs from docs/research_extension/OSF_PREREGISTRATION_CFP.md"
    return True, f"registered {r['osf_id']} at {r['registered_utc']}"


def check_no_desktop_server() -> tuple[bool, str]:
    try:
        out = subprocess.run(["tasklist"], capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL).stdout.lower()
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, f"cannot list processes: {e}"
    if "ollama app.exe" in out:
        return False, "the default desktop Ollama app is running (ollama app.exe)"
    return True, "no desktop Ollama app process"


def check_frozen_server() -> tuple[bool, str]:
    from triage.ollama import OllamaAPI
    cfg = json.loads(FROZEN_MODELS.read_text(encoding="utf-8"))
    g = cfg["roles"]["G"]
    try:
        api = OllamaAPI(timeout_s=10)
        ver, live = api.version(), (api.tags().get(g) or {}).get("digest", "")
    except Exception as e:
        return False, f"the study server does not answer on 127.0.0.1:11434: {type(e).__name__}"
    if ver != cfg["runtime"]["version"]:
        return False, f"Ollama version {ver} != frozen {cfg['runtime']['version']}"
    want = cfg["models"][g]["digest"]
    if not live or not (live.startswith(want) or want.startswith(live)):
        return False, f"generator digest {live[:16]} != frozen {want[:16]}"
    return True, f"Ollama {ver}, {g} digest {want[:12]} (run scripts/local/session_check.py --start as well)"


def check_manifest_and_hashes() -> tuple[bool, str]:
    fz = _freeze()
    doc = json.loads(fz.MANIFEST.read_text(encoding="utf-8"))
    bad = [f for f, h in doc["files"].items() if fz.content_hash(f) != h]
    if bad or fz.parameters() != doc["parameters"]:
        return False, f"freeze manifest mismatch: {bad or 'parameters'}"
    if not MANIFEST.exists():
        return False, "dataset manifest missing"
    from triage.generation import generation_prompt
    from triage.io_utils import sha256_text
    from triage.prompts import PromptSet
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    prompts = PromptSet.named(man["prompt_set"])
    frozen = json.loads(FROZEN_MODELS.read_text(encoding="utf-8"))
    if prompts.hashes()["generator"] != frozen["prompt_set"]["hashes"]["generator"]:
        return False, "generator prompt differs from the frozen prompt set"
    n = 0
    for tr, t in man["tranches"].items():
        if t["missing"]:
            return False, f"{tr}: {len(t['missing'])} frame rows have no context"
        for fid, h in t["prompt_sha256"].items():
            p = BASE / tr / "context" / f"{sha256_text(fid)[:16]}.json"
            if not p.exists():
                return False, f"{tr}: context file missing for {fid}"
            ctx = json.loads(p.read_text(encoding="utf-8"))
            if hashlib.sha256(generation_prompt(ctx, prompts, 0).encode("utf-8")).hexdigest() != h:
                return False, f"{tr}: generation input changed for {fid}"
            n += 1
    return True, f"freeze manifest verified; {n} generation inputs match the dataset manifest"


def check_nothing_frozen_changed() -> tuple[bool, str]:
    changed = [l for l in _git("diff", "--name-only", "master", "--", *IMMUTABLE).splitlines() if l]
    if changed:
        return False, f"files differ from master under immutable paths: {changed[:5]}"
    eng = [l for l in _git("diff", "--name-only", ENGINE_COMMIT, "--", "src/triage_ext").splitlines() if l]
    if eng:
        return False, f"engine differs from the pilot ({ENGINE_COMMIT}): {eng}"
    old = json.loads(subprocess.run(["git", "show", "master:configs/local_scope.json"], cwd=ROOT, capture_output=True,
                                    text=True, encoding="utf-8", stdin=subprocess.DEVNULL).stdout)
    new = json.loads((ROOT / "configs" / "local_scope.json").read_text(encoding="utf-8"))
    for k in ("allowed_splits", "allowed_models"):
        if new[k] != old[k]:
            return False, f"the scope lock's {k} changed"
    for k in ("allowed_datasets", "allowed_experiments"):
        if new[k][: len(old[k])] != old[k]:
            return False, f"the scope lock lost or reordered entries in {k}"
    return True, f"immutable paths identical to master; engine identical to {ENGINE_COMMIT}; scope lock only gained entries"


def evaluate(offline: bool = False) -> dict:
    checks = [("1 OSF registration recorded and identical to the repository text", check_registration),
              ("2 default desktop Ollama server stopped", check_no_desktop_server),
              ("3 frozen study server and generator digest verified", check_frozen_server),
              ("4 dataset manifest and configuration hashes validated", check_manifest_and_hashes),
              ("5 no frozen experimental component changed", check_nothing_frozen_changed)]
    out = {"checks": [], "offline": offline}
    for name, fn in checks:
        if offline and name[0] in "23":
            out["checks"].append({"check": name, "ok": None, "detail": "skipped (offline)"})
            continue
        ok, detail = fn()
        out["checks"].append({"check": name, "ok": ok, "detail": detail})
    out["ready"] = (not offline) and all(c["ok"] for c in out["checks"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    rep = evaluate(a.offline)
    for c in rep["checks"]:
        mark = {True: "PASS", False: "FAIL", None: "SKIP"}[c["ok"]]
        print(f"[{mark}] {c['check']}: {c['detail']}")
    print("READY TO GENERATE" if rep["ready"] else "NOT READY: generation is refused")
    sys.exit(0 if rep["ready"] else 1)


if __name__ == "__main__":
    main()
