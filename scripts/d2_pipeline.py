"""D2 (seeded faults, E5-R1) pipeline: contexts -> generation -> S2 specs -> execution -> dataset.

    WSL:     bash scripts/wsl/run.sh scripts/d2_pipeline.py contexts [--workers 4]
    Windows: python scripts/d2_pipeline.py generate --local
    Windows: python scripts/d2_pipeline.py specs --local
    WSL:     bash scripts/wsl/run.sh scripts/d2_pipeline.py execute [--workers 6]
    Windows: python scripts/d2_pipeline.py dataset [--cap N]

Every stage is idempotent and refuses unless the active scope lists dataset D2 and the test split (D-62: added only
after Tier 2 and after the D2 code hash is recorded). Stages that load G or M1 honour the stop file (D-58);
WSL stages start no new bug job once the stop file exists. Never run generation concurrently with a WSL stage.
"""
import argparse
import json
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from triage import config, d2, scope  # noqa: E402
from triage.io_utils import append_jsonl, dump_json, read_jsonl, write_immutable  # noqa: E402
from triage.llm import STOP_FILE, StopRequested  # noqa: E402

G_SLUG = "gemma4_26b"
CANDIDATES = config.INTERIM / f"candidates_{G_SLUG}_D2"
EXECUTIONS = config.RAW / f"executions_{G_SLUG}_D2"


def _scope_or_exit(what: str):
    sc = scope.load(scope.LOCAL_SCOPE_FILE)
    if sc is None:
        raise SystemExit("no configs/local_scope.json: D2 runs only under the local held-out scope")
    sc.check_dataset("D2", f"({what})")
    sc.check_split("test", f"({what})")
    return sc


def _units():
    return d2.verified_mutants(read_jsonl(d2.MUTANTS_FILE))


def _stop_futures(futs):
    if STOP_FILE.exists():
        print("STOPPED ON REQUEST (D-58): stop file present; finishing running bug jobs", flush=True)
        for f in futs:
            f.cancel()


def cmd_contexts(a):
    _scope_or_exit("D2 contexts")
    frame_recs = {r["focal_id"]: r for r in read_jsonl(config.PROCESSED / "frame_d1.jsonl")}
    have = set(d2.load_contexts())
    by_bug = defaultdict(list)
    for r, m in _units():
        by_bug[(r["project"], r["bug"])].append((r, m))
    scope.check_focal_ids_local([d2.d2_focal_id(r["focal_id"], m["mutant_id"]) for us in by_bug.values() for r, m in us],
                                "D2 contexts")
    d2.CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"{sum(map(len, by_bug.values()))} units over {len(by_bug)} bugs ({len(have)} contexts exist)", flush=True)
    from triage import frame
    with ProcessPoolExecutor(a.workers) as ex:
        futs = []
        for (p, b), us in sorted(by_bug.items()):
            info = json.loads((frame.FIX_INFO / f"{p}_{b}" / "buggy_fix_info.json").read_text())
            futs.append(ex.submit(d2.contexts_for_bug, p, b, us, frame_recs, info, have))
        for i, f in enumerate(as_completed(futs), 1):
            if f.cancelled():
                continue
            for did, ctx, fixed, err in f.result():
                if err:
                    append_jsonl(config.INTERIM / "context_D2_errors.jsonl", {"focal_id": did, "error": err[:800]})
                    continue
                d2.context_file(did).write_text(json.dumps(ctx, indent=1, sort_keys=True), encoding="utf-8")
                append_jsonl(d2.FIXED_BODIES, {"focal_id": did, "fixed_body": fixed})
            print(f"  bugs {i}/{len(futs)}", flush=True)
            _stop_futures(futs)


def _client_and_contexts(a, what):
    from _common import make_client
    from triage.prompts import PromptSet
    client = make_client(local=a.local)
    ctxs = list(d2.load_contexts().values())
    if client.scope is None:
        raise SystemExit(f"{what} needs the local scope (--local)")
    client.scope.check_dataset("D2", f"({what})")
    client.scope.check_split("test", f"({what})")
    client.scope.check_items(ctxs, "D2 unit")
    return client, PromptSet.named(a.prompt_set), ctxs


def cmd_generate(a):
    from _common import local_model
    from triage.sessions import g_session_end, g_session_start
    client, prompts, ctxs = _client_and_contexts(a, "D2 generation")
    model_id = local_model("G")
    CANDIDATES.mkdir(parents=True, exist_ok=True)
    g_session_start(client.backend.api, model_id, client.backend.spec(model_id))
    n = n_ok = 0
    try:
        n, n_ok = d2.generate_units(ctxs[: a.limit], client, prompts, model_id, CANDIDATES)
    except StopRequested as e:
        print("STOPPED ON REQUEST (D-58):", e, flush=True)
    g_session_end(model_id, n)
    print(f"{len(ctxs)} D2 units, {n_ok}/{n} assembled -> {CANDIDATES}")


def cmd_specs(a):
    from _common import local_model
    from triage.spec_inference import infer
    client, prompts, ctxs = _client_and_contexts(a, "D2 S2 specs")
    m1 = local_model("M1")
    ok = n = 0
    try:
        for ctx in ctxs:
            ok += infer(ctx, client, prompts, m1)["valid"]
            n += 1
    except StopRequested as e:
        print("STOPPED ON REQUEST (D-58):", e, flush=True)
    print(f"{ok}/{n} valid D2 specifications")


def cmd_execute(a):
    _scope_or_exit("D2 execution")
    mutant_of = {d2.d2_focal_id(r["focal_id"], m["mutant_id"]): m for r, m in _units()}
    groups = defaultdict(lambda: defaultdict(list))
    for p in sorted(CANDIDATES.glob("*.json")):
        c = json.loads(p.read_text())
        if not c.get("assembled") or (EXECUTIONS / f"{c['candidate_id']}.json").exists():
            continue
        proj, bug = c["focal_id"].split("::")[0].rsplit("_", 1)
        groups[(proj, bug)][c["focal_id"]].append(c)
    scope.check_focal_ids_local([fid for g in groups.values() for fid in g], "D2 execution")
    from triage import execution
    execution.ensure_runner()
    EXECUTIONS.mkdir(parents=True, exist_ok=True)
    print(f"{sum(len(cs) for g in groups.values() for cs in g.values())} candidates over {len(groups)} bugs", flush=True)
    with ProcessPoolExecutor(a.workers) as ex:
        futs = [ex.submit(d2.execute_bug, p, b, dict(g), mutant_of) for (p, b), g in sorted(groups.items())]
        for i, f in enumerate(as_completed(futs), 1):
            if f.cancelled():
                continue
            for cid, rec, err in f.result():
                if err:
                    append_jsonl(EXECUTIONS.parent / "execution_errors_D2.jsonl", {"candidate_id": cid, "error": err})
                else:
                    write_immutable(EXECUTIONS / f"{cid}.json", json.dumps(rec, indent=1, sort_keys=True))
            print(f"  bugs {i}/{len(futs)}", flush=True)
            _stop_futures(futs)


def cmd_dataset(a):
    from triage import dataset
    _scope_or_exit("D2 dataset build")
    cands = {json.loads(p.read_text())["candidate_id"]: json.loads(p.read_text()) for p in CANDIDATES.glob("*.json")}
    execs = [json.loads(p.read_text()) for p in sorted(EXECUTIONS.glob("*.json"))]
    scope.check_focal_ids_local([e["focal_id"] for e in execs], "D2 dataset build")
    ctxs = d2.load_contexts()
    fixed = {r["focal_id"]: r.get("fixed_body") for r in read_jsonl(d2.FIXED_BODIES)}
    counts = dataset.build("D2", execs, cands, ctxs, fixed)
    samp = dataset.sample("D2", "test", mode="proportional", cap=a.cap)
    counts["sample"] = {"n": len(samp["instance_ids"]), "mode": samp["mode"], "cap": a.cap, "capped": samp["capped"],
                        "per_project": samp["per_project"]}
    counts["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    dump_json(config.PROCESSED / "dataset_summary_D2.json", counts)
    print(json.dumps({k: counts[k] for k in ("labels", "exclusions", "executed_methods")}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("contexts", "execute"):
        s = sub.add_parser(name)
        s.add_argument("--workers", type=int, default=4 if name == "contexts" else 6)
    for name in ("generate", "specs"):
        s = sub.add_parser(name)
        s.add_argument("--local", action="store_true", required=True)
        s.add_argument("--prompt-set", default="local_m1b")
        s.add_argument("--limit", type=int)
    s = sub.add_parser("dataset")
    s.add_argument("--cap", type=int, help="judged-set cap (decided by the authors before any D2 outcome exists)")
    a = ap.parse_args()
    {"contexts": cmd_contexts, "generate": cmd_generate, "specs": cmd_specs, "execute": cmd_execute,
     "dataset": cmd_dataset}[a.cmd](a)


if __name__ == "__main__":
    main()
