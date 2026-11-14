"""Shared code for the CFP confirmation pipeline after generation (D-142): execution, labelling, judge votes and the
read-only concatenation of the tranches. Every step reuses the study's own modules unchanged:

  execution   scripts/run_execution._bug_job -> triage.execution.execute_candidate   (WSL side)
  labelling   triage.dataset.build -> triage.labeling.label                          (writes redirected per tranche)
  votes       scripts/run_experiment.execute -> triage.runner.Runner -> J1 arm         (tranche-local call logs)

Nothing here is in the CFP freeze manifest and nothing here edits a study file. The library never starts a model
call by itself; the CLI in confirm_pipeline.py decides when a step may run.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "src", ROOT / "scripts", ROOT / "scripts" / "extension"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from triage import config  # noqa: E402

RUNS_FILE = ROOT / "configs" / "extension" / "confirm_runs.json"
FRAME_FILE = ROOT / "configs" / "extension" / "confirm_frame.jsonl"
BASE = ROOT / "data" / "extension" / "confirm"
EXP_DIR = ROOT / "configs" / "extension" / "experiments"
E6B_PROFILE = ROOT / "configs" / "e6b.json"
CONF_E6B_PROFILE = ROOT / "configs" / "extension" / "conf_e6b_profile.json"
TRANCHES = ("F1", "F2", "CTRL")
JUDGED = ("F1", "F2")                                  # the control group is not judged (registration, step 6)
VOTE_MODELS = ("M1", "M2", "M3")
VOTE_REPLICATE = 80                                    # no committed decision uses 80 (used: 0-2, 10-12, 20-74)
CONCAT_RUN = "CFP_CONF_ALL"


# ---------------------------------------------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------------------------------------------
def runs() -> dict:
    return json.loads(RUNS_FILE.read_text(encoding="utf-8"))


def read_jsonl(p: Path) -> list[dict]:
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def raw_lines(p: Path) -> list[bytes]:
    """Non-empty lines of a JSONL file as bytes, line ending removed (so CRLF and LF sources concatenate alike)."""
    return [l.rstrip(b"\r") for l in p.read_bytes().split(b"\n") if l.strip()]


def rel_path(p) -> str:
    """Repository-relative path when inside the repository, absolute otherwise."""
    q = Path(p).resolve()
    try:
        return q.relative_to(ROOT).as_posix()
    except ValueError:
        return q.as_posix()


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tranche_dir(tr: str) -> Path:
    return BASE / tr


def paths(tr: str) -> dict:
    d = tranche_dir(tr)
    tag = runs()["datasets"][tr]
    return {"dir": d, "tag": tag, "context": d / "context", "candidates": d / "candidates",
            "executions": d / "executions", "label_side": d / "label_side" / "fixed_bodies.jsonl",
            "labels": d / f"labels_{tag}.jsonl", "instances": d / f"instances_{tag}.jsonl",
            "guard": d / f"guard_{tag}.jsonl", "exclusions": d / f"exclusions_{tag}.jsonl",
            "sample": d / f"sample_{tag}_all.json", "summary": d / f"dataset_summary_{tag}.json",
            "votes": d / "votes", "vote_calls": d / "llm_calls_votes"}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, mod)
    spec.loader.exec_module(mod)
    return mod


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          stdin=subprocess.DEVNULL).stdout.strip()


def is_committed(p: Path) -> bool:
    """True when the file is tracked and identical to HEAD (used to check that labels are sealed)."""
    try:
        rel = Path(p).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return False                                   # outside the repository: cannot be committed
    return bool(git("ls-files", "--", rel)) and not git("status", "--porcelain", "--", rel)


def contexts(tr: str) -> dict[str, dict]:
    return {c["focal_id"]: c for c in (json.loads(p.read_text(encoding="utf-8"))
                                       for p in sorted(paths(tr)["context"].glob("*.json")))}


# ---------------------------------------------------------------------------------------------------------------
# 1. execution (WSL)
# ---------------------------------------------------------------------------------------------------------------
def group_candidates(cand_dir: Path, out_dir: Path) -> dict[tuple, list]:
    """Assembled candidates not yet executed, grouped by bug, exactly as scripts/run_execution.py groups them."""
    groups = defaultdict(list)
    for p in sorted(cand_dir.glob("*.json")):
        c = json.loads(p.read_text())
        if not c.get("assembled") or (out_dir / f"{c['candidate_id']}.json").exists():
            continue
        proj, bug = c["focal_id"].split("::")[0].rsplit("_", 1)
        groups[(proj, bug)].append(c)
    return groups


def check_execution_scope(tr: str, groups: dict) -> None:
    """The study's execution lock reads only the study's contexts, so the tranche gets the same check here:
    dataset tag and split approved, and every candidate's focal method belongs to this tranche."""
    from triage import scope
    sc = scope.load(scope.LOCAL_SCOPE_FILE)
    if sc is None:
        raise SystemExit("no local scope file: refusing to execute")
    sc.check_dataset(paths(tr)["tag"], "(confirmation execution)")
    sc.check_split("test", "(confirmation execution)")
    known = set(contexts(tr))
    alien = [c["focal_id"] for cs in groups.values() for c in cs if c["focal_id"] not in known]
    if alien:
        raise SystemExit(f"{len(alien)} candidates are not methods of tranche {tr}: {alien[:3]}")


def execute(cand_dir: Path, out_dir: Path, workers: int = 6, bugs: set | None = None) -> dict:
    """Compile and run every assembled candidate on B and F with the study's _bug_job; immutable records."""
    from concurrent.futures import ProcessPoolExecutor, as_completed

    from triage import execution
    from triage.io_utils import append_jsonl, write_immutable
    from triage.llm import STOP_FILE
    rx = load_module("run_execution", ROOT / "scripts" / "run_execution.py")
    out_dir.mkdir(parents=True, exist_ok=True)
    groups = group_candidates(cand_dir, out_dir)
    if bugs is not None:
        groups = {k: v for k, v in groups.items() if f"{k[0]}_{k[1]}" in bugs}
    execution.ensure_runner()
    n_ok = n_err = 0
    print(f"{sum(map(len, groups.values()))} candidates over {len(groups)} bugs -> {out_dir}", flush=True)
    with ProcessPoolExecutor(workers) as ex:
        futs = [ex.submit(rx._bug_job, p, b, cs) for (p, b), cs in sorted(groups.items())]
        for i, f in enumerate(as_completed(futs), 1):
            if f.cancelled():
                continue
            for cid, rec, err in f.result():
                if err:
                    append_jsonl(out_dir.parent / f"{out_dir.name}_errors.jsonl", {"candidate_id": cid, "error": err})
                    n_err += 1
                else:
                    write_immutable(out_dir / f"{cid}.json", json.dumps(rec, indent=1, sort_keys=True))
                    n_ok += 1
            if i % 10 == 0 or i == len(futs):
                print(f"  bugs {i}/{len(futs)}", flush=True)
            if STOP_FILE.exists():
                print("STOPPED ON REQUEST: stop file present; finishing running bug jobs", flush=True)
                for f2 in futs:
                    f2.cancel()
    return {"bugs": len(groups), "records": n_ok, "errors": n_err}


# ---------------------------------------------------------------------------------------------------------------
# 2. labelling and dataset build (redirected writes)
# ---------------------------------------------------------------------------------------------------------------
@contextlib.contextmanager
def redirected_stores(out_dir: Path):
    """dataset.build writes through config.GT_STORE, config.LEAKAGE_GUARD and config.PROCESSED; point all three at
    one tranche directory for the duration, then restore them."""
    saved = (config.GT_STORE, config.LEAKAGE_GUARD, config.PROCESSED)
    out_dir.mkdir(parents=True, exist_ok=True)
    config.GT_STORE = config.LEAKAGE_GUARD = config.PROCESSED = out_dir
    try:
        yield out_dir
    finally:
        config.GT_STORE, config.LEAKAGE_GUARD, config.PROCESSED = saved


def build_dataset(dataset: str, exec_dir: Path, cand_dir: Path, ctxs: dict[str, dict], fixed: dict[str, str],
                  out_dir: Path) -> dict:
    """The study's dataset.build on one set of execution records, with the study's input ordering
    (scripts/build_dataset.py: executions in sorted path order). Writes labels_, guard_, instances_ and
    exclusions_<dataset>.jsonl into out_dir and returns the counts."""
    from triage import dataset as ds
    cands = {}
    for p in cand_dir.glob("*.json"):
        c = json.loads(p.read_text())
        cands[c["candidate_id"]] = c
    execs = [json.loads(p.read_text()) for p in sorted(exec_dir.glob("*.json"))]
    with redirected_stores(out_dir):
        return ds.build(dataset, execs, cands, ctxs, fixed)


NEAR_LIMIT_S = 20.0          # descriptive only: two thirds of the study's 30 s wall-clock limit (D-142)


def near_time_limit(exec_dir: Path) -> dict:
    """Methods with any run of NEAR_LIMIT_S seconds or more, by label. Their label can depend on machine load (a run
    near the limit may finish or time out); the D1 re-execution showed this for one dev-split method. Reported,
    never used to change a label."""
    from triage import labeling
    out = Counter()
    for f in sorted(exec_dir.glob("*.json")):
        for m in json.loads(f.read_text())["methods"]:
            d = [float(r.get("duration_s") or 0) for r in (m.get("runs_b") or []) + (m.get("runs_f") or [])]
            if d and max(d) >= NEAR_LIMIT_S:
                out[labeling.label(m)["label"]] += 1
    return {"threshold_s": NEAR_LIMIT_S, "methods_by_label": dict(out)}


def label_tranche(tr: str) -> dict:
    p = paths(tr)
    for k in ("labels", "instances", "guard", "exclusions"):
        if p[k].exists():
            raise SystemExit(f"{p[k]} exists: labels are written once and never rebuilt (sealing)")
    if not any(p["executions"].glob("*.json")):
        raise SystemExit(f"no execution records in {p['executions']}")
    ctxs = contexts(tr)
    fixed = {r["focal_id"]: r.get("fixed_body") for r in read_jsonl(p["label_side"])}
    counts = build_dataset(p["tag"], p["executions"], p["candidates"], ctxs, fixed, p["dir"])
    ids = [r["instance_id"] for r in read_jsonl(p["instances"])]
    p["sample"].write_text(json.dumps({"dataset": p["tag"], "split": "test", "mode": "all_instances",
                                       "instance_ids": ids, "note": "every triage instance; no label is read"},
                                      indent=1), encoding="utf-8", newline="\n")
    counts["instances"] = len(ids)
    counts["near_time_limit"] = near_time_limit(p["executions"])
    p["summary"].write_text(json.dumps(counts, indent=1, sort_keys=True), encoding="utf-8", newline="\n")
    return counts


# ---------------------------------------------------------------------------------------------------------------
# 3. three-judge votes
# ---------------------------------------------------------------------------------------------------------------
def vote_run_name(tr: str, model: str) -> str:
    return runs()["runs"]["votes"][tr][model]


def vote_config(name: str, dataset: str, instances: Path, sample: Path, guard: Path, model: str, replicate: int,
                session_log: Path | None = None, model_tag: str | None = None) -> dict:
    """An experiment configuration in the study's format: the unchanged J1 arm at S1, frozen prompts, one call per
    instance at one replicate index. M1 and M2 go through the frozen roles; M3 names its model tag."""
    rel = lambda q: Path(q).resolve().relative_to(ROOT).as_posix()       # noqa: E731
    exp = {"name": name, "description": "CFP confirmation vote (D-142): one fresh J1 call per instance at S1, frozen "
                                        "local_m1b prompts and decoding, replicate index used by no committed run.",
           "dataset": dataset, "split": "test", "prompt_set": "local_m1b", "backend": "ollama",
           "instances_file": rel(instances), "sample_file": rel(sample), "guard_file": rel(guard),
           "replicates": 1, "conditions": [{"arm": "J1", "levels": ["S1"], "replicate_indices": [replicate]}],
           "run_label": name}
    if model in ("M1", "M2"):
        exp["model"] = model
    else:
        exp["model_tag"] = model_tag
    if session_log is not None:
        exp.update({"requires_ram_precondition": True, "session_log": rel(session_log)})
    return exp


def conf_e6b_profile() -> dict:
    """A copy of the study's third-family profile (configs/e6b.json is not edited) serving only the confirmation
    vote runs, with its call, session and safety logs under the confirmation tree."""
    p = json.loads(E6B_PROFILE.read_text(encoding="utf-8"))
    q = copy.deepcopy(p)
    q["_status"] = ("D-142: copy of configs/e6b.json for the CFP confirmation votes only; model, digest, server "
                    "settings, safety rule and selection are unchanged; only the experiments served and the log "
                    "locations differ. The deadline field is not used by the confirmation driver.")
    q["experiments"] = [vote_run_name(tr, "M3") for tr in JUDGED]
    q["call_log_dir"] = "data/extension/confirm/llm_calls_votes_e6b"
    q["session_log"] = "data/extension/confirm/sessions_e6b.jsonl"
    q["safety_events"] = "data/extension/confirm/safety_events_e6b.jsonl"
    q["selection_gated"] = {**p["selection_gated"], "experiments": list(q["experiments"])}
    return q


def write_vote_configs() -> list[Path]:
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    prof = conf_e6b_profile()
    CONF_E6B_PROFILE.write_text(json.dumps(prof, indent=1), encoding="utf-8", newline="\n")
    out = []
    for tr in JUDGED:
        p = paths(tr)
        for m in VOTE_MODELS:
            name = vote_run_name(tr, m)
            log = p["dir"] / ("sessions_votes.jsonl" if m != "M3" else "sessions_votes_e6b.jsonl")
            exp = vote_config(name, p["tag"], p["instances"], p["sample"], p["guard"], m, VOTE_REPLICATE,
                              session_log=log, model_tag=prof["model_tag"] if m == "M3" else None)
            f = EXP_DIR / f"{name}.json"
            f.write_text(json.dumps(exp, indent=1), encoding="utf-8", newline="\n")
            out.append(f)
    return out


def vote_client(model: str, log_dir: Path, replay: bool = False, profile: dict | None = None):
    """LLMClient for a vote run. replay=True gives a backend with identical routing whose call() always raises, so a
    request missing from the log can never reach a server."""
    from triage import expl_profile
    from triage.llm import LLMClient, NotInLog
    from triage.ollama import OllamaBackend
    cfg = expl_profile.models_cfg(profile) if model == "M3" else None
    if replay:
        class ReplayOllama(OllamaBackend):
            def call(self, model_id, *a, **kw):
                raise NotInLog(f"{model_id}: request not in the call log (replay)")

            def check_digest(self, model_id):
                return None
        b = ReplayOllama(cfg, telemetry=False, verify_digests=False)
        b.api = None
        return LLMClient(b, log_dir=log_dir)
    if model == "M3":
        return LLMClient(expl_profile.safe_backend(profile), log_dir=expl_profile.resolve(profile["call_log_dir"]))
    return LLMClient(OllamaBackend(), log_dir=log_dir)


def run_vote(exp: dict, client, run_dir: Path, workers: int = 1):
    rexp = load_module("run_experiment", ROOT / "scripts" / "run_experiment.py")
    return rexp.execute(exp, client, run_dir, workers=workers)


# ---------------------------------------------------------------------------------------------------------------
# 4. read-only concatenation
# ---------------------------------------------------------------------------------------------------------------
def concatenate(parts: list[dict], out_ledger_dir: Path, out_data_dir: Path, frame: dict[str, str] | None,
                vote_models: tuple = VOTE_MODELS, replicate: int | None = VOTE_REPLICATE) -> dict:
    """parts: [{"tranche", "ledger", "instances", "labels", "votes": {model: decisions.jsonl} or {}}], in order.

    Writes ledger.jsonl, instances.jsonl, labels.jsonl and votes/<model>/decisions.jsonl by copying source lines
    byte for byte (line endings normalised to LF), refuses to overwrite, and refuses on any duplicate instance id,
    any ledger or label record without an instance, or any instance whose focal method belongs to another tranche.
    A manifest records the sha256 of every source and output and the per-tranche counts."""
    outs = {"ledger": out_ledger_dir / "ledger.jsonl", "instances": out_data_dir / "instances.jsonl",
            "labels": out_data_dir / "labels.jsonl"}
    for m in vote_models:
        outs[f"votes_{m}"] = out_data_dir / "votes" / m / "decisions.jsonl"
    existing = [str(p) for p in outs.values() if p.exists()]
    if existing:
        raise SystemExit(f"refusing to overwrite: {existing}")
    seen: dict[str, str] = {}
    buf = defaultdict(list)
    manifest = {"decision": "D-142", "vote_replicate": replicate, "sources": [], "counts": {}}
    for part in parts:
        tr = part["tranche"]
        inst_lines = raw_lines(Path(part["instances"]))
        inst = [json.loads(l) for l in inst_lines]
        ids = [r["instance_id"] for r in inst]
        dup = [i for i in ids if i in seen] + [i for i, n in Counter(ids).items() if n > 1]
        if dup:
            raise SystemExit(f"duplicate instance ids across or within tranches: {sorted(set(dup))[:5]}")
        seen.update({i: tr for i in ids})
        if frame is not None:
            wrong = [r["focal_id"] for r in inst if frame.get(r["focal_id"]) != tr]
            if wrong:
                raise SystemExit(f"{len(wrong)} instances of {tr} have focal methods of another tranche: {wrong[:3]}")
        own = set(ids)
        counts = {"instances": len(ids)}
        for key in ("ledger", "labels"):
            lines = raw_lines(Path(part[key]))
            orphan = [json.loads(l)["instance_id"] for l in lines if json.loads(l)["instance_id"] not in own]
            if orphan:
                raise SystemExit(f"{tr} {key}: {len(orphan)} records have no instance in the tranche: {orphan[:3]}")
            buf[key] += lines
            counts[key] = len(lines)
        buf["instances"] += inst_lines
        for m in vote_models:
            src = (part.get("votes") or {}).get(m)
            if not src:
                continue
            lines = [l for l in raw_lines(Path(src))
                     if replicate is None or json.loads(l).get("replicate") == replicate]
            orphan = [json.loads(l)["instance_id"] for l in lines if json.loads(l)["instance_id"] not in own]
            if orphan:
                raise SystemExit(f"{tr} votes {m}: {len(orphan)} decisions have no instance: {orphan[:3]}")
            buf[f"votes_{m}"] += lines
            counts[f"votes_{m}"] = len(lines)
        manifest["counts"][tr] = counts
        for key, src in [("ledger", part["ledger"]), ("instances", part["instances"]), ("labels", part["labels"])] + \
                [(f"votes_{m}", s) for m, s in (part.get("votes") or {}).items()]:
            manifest["sources"].append({"tranche": tr, "kind": key, "path": rel_path(src),
                                        "sha256": sha256_file(Path(src))})
    manifest["outputs"] = {}
    for key, p in outs.items():
        if key.startswith("votes_") and not buf[key]:
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"".join(l + b"\n" for l in buf[key]))
        manifest["outputs"][key] = {"path": rel_path(p), "records": len(buf[key]),
                                    "sha256": sha256_file(p)}
    (out_data_dir / "concat_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8", newline="\n")
    return manifest
