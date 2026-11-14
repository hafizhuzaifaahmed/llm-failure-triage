"""E9b memorisation check (D-104): Claude Sonnet 5.5, J1 + DEB at S1, one replicate each, on the scored D2 instances.

    python scripts/frontier/e9b.py dryrun    # no network, no key: builds pass 1, prints every check and the worst case
    python scripts/frontier/e9b.py run       # loads the key from env/.env into this process; canary, then passes
    python scripts/frontier/e9b.py status

Same client, request settings, batching, canary, resume and logging as E9 (DEB requests go first, D-105) (scripts/frontier/e9.py, src/triage/frontier.py),
with three differences fixed in D-104: the experiment and run folder, a call log of its own
(data/raw/llm_calls_frontier_e9b/) so the cap counts E9b's spend only and no E9 answer can be replayed, and the cap,
US$ 11.00. Cap layers: (1) each batch's worst case plus the spend so far must fit under US$ 11.00 before it is created;
(2) the spend is recomputed from logged usage before every batch; (3) the authors' US$ 12 Console limit.

`run` refuses to start unless ANTHROPIC_API_KEY is set (loaded from env/.env into this process; its value is never read
here, printed or written) and results/runs_frontier/E9B_SONNET55_D2/AUTHORS_KEY_SET exists (the authors create it after
putting the new key in env/.env and setting the Console limit). logs/STOP is honoured.
"""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "frontier"))

from triage import frontier, scope  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402
from triage.ollama import LOCAL_SCOPE_FILE  # noqa: E402

import e9  # noqa: E402  (check_frozen_prompts, bound_whole_run, load_key: shared, unchanged)

EXP = ROOT / "configs" / "experiments" / "E9B_SONNET55_D2.json"
RUN = ROOT / "results" / "runs_frontier" / "E9B_SONNET55_D2"
STATE = RUN / "batches.jsonl"
GO = RUN / "AUTHORS_KEY_SET"
LOG_DIR = ROOT / "data" / "raw" / "llm_calls_frontier_e9b"
CAP_USD = 11.00                                       # D-104, under the authors' US$ 12 Console limit
CANARY = 3
MAX_PASSES = 12


def exp():
    return json.loads(EXP.read_text(encoding="utf-8"))


def new_client(log_dir=None):
    return frontier.FrontierClient(log_dir=log_dir or LOG_DIR, scope=scope.load(LOCAL_SCOPE_FILE))


def one_pass(client, e):
    import run_experiment
    r = run_experiment.execute(e, client, RUN, workers=1)
    decided = sum(1 for _ in read_jsonl(RUN / "decisions.jsonl"))
    return {"pending": len(client.pending), "deferred_tasks": r.deferred, "decisions": decided}


def cmd_dryrun(_a):
    e = exp()
    h = e9.check_frozen_prompts(e)
    with tempfile.TemporaryDirectory() as tmp:
        client = new_client(Path(tmp) / "log")
        import run_experiment
        run_dir = Path(tmp) / "run"
        r = run_experiment.execute(e, client, run_dir, workers=1)
        pending = list(client.pending.values())
        sample = [frontier.build_params(p) for p in pending[:2]]
        out = {"what": "E9b dry run: pass 1 built, nothing sent", "label": frontier.LABEL, "prompt_set_hash": h,
               "sample_n": json.loads((ROOT / e["sample_file"]).read_text(encoding="utf-8"))["n"],
               "pass1_pending_requests": len(pending),
               "pass1_roles": {k: sum(1 for p in pending if p["role"] == k) for k in sorted({p["role"] for p in pending})},
               "pass1_worst_case_usd": sum(frontier.worst_case_usd(p) for p in pending),
               "whole_run_worst_case_bound_usd": e9.bound_whole_run(client, pending), "cap_usd": CAP_USD,
               "spent_so_far_on_own_log_usd": new_client().spend_usd(),
               "deferred_tasks": r.deferred,
               "leakage_rejections": sum(1 for _ in read_jsonl(run_dir / "leakage_rejections.jsonl")),
               "example_params_without_messages": [{k: v for k, v in s.items() if k != "messages"} for s in sample],
               "sampling_fields_sent": sorted({k for s in sample for k in s if k in ("temperature", "top_p", "top_k")}),
               "key_in_environment": bool(os.environ.get("ANTHROPIC_API_KEY"))}
    RUN.mkdir(parents=True, exist_ok=True)
    dump_json(RUN / "dryrun.json", out)
    print(json.dumps({k: v for k, v in out.items() if k != "example_params_without_messages"}, indent=1))
    if out["whole_run_worst_case_bound_usd"] > CAP_USD:
        print("NOTE: the whole-run worst-case bound exceeds the cap; the per-batch guard chunks or stops the run first")


def cmd_run(_a):
    e9.load_key()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set (env/.env or the environment); the authors provide it")
    if not GO.exists():
        raise SystemExit(f"{GO} not found: the authors create it after setting the Console spend limit")
    e = exp()
    e9.check_frozen_prompts(e)
    import anthropic
    api = anthropic.Anthropic()                       # the SDK reads the key; it is never read or written here
    client = new_client()
    RUN.mkdir(parents=True, exist_ok=True)
    for i in range(MAX_PASSES):
        st = one_pass(client, e)
        print(f"pass {i}: {st}", flush=True)
        if not client.pending:
            print("no pending calls: every decision is made")
            break
        if frontier.unfinished_batches(STATE):
            print(f"resumed: {frontier.resume(client, api, STATE)}", flush=True)
            client = new_client()
            continue
        canary = not any(r.get("event") == "ended" for r in read_jsonl(STATE))
        # D-105: DEB first. The cascade needs Sonnet DEB, so J1 requests are held back while any DEB request is queued;
        # if the cap stops the run, it stops with DEB complete and J1 (secondary) short.
        deb = {k: v for k, v in client.pending.items() if v["role"] != "judge"}
        if deb:
            client.pending = deb
        res = frontier.submit_pending(client, api, STATE, cap=CAP_USD, limit=CANARY if canary else None)
        print(f"batch: {res}", flush=True)
        if canary and (res.get("errored") or res.get("invalid_after_failures")):
            raise SystemExit("canary batch had errored requests; stopping before the real passes")
        client = new_client()
    print("spent US$", round(client.spend_usd(), 4), "of", CAP_USD)


def cmd_status(_a):
    client = new_client()
    rows = list(read_jsonl(STATE))
    print(json.dumps({"batches": [r for r in rows if r.get("event") == "ended"],
                      "decisions": sum(1 for _ in read_jsonl(RUN / "decisions.jsonl")),
                      "logged_calls": sum(1 for _ in read_jsonl(client.log_path)),
                      "spent_usd": client.spend_usd(), "cap_usd": CAP_USD}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["dryrun", "run", "status"])
    a = ap.parse_args()
    {"dryrun": cmd_dryrun, "run": cmd_run, "status": cmd_status}[a.step](a)


if __name__ == "__main__":
    main()
