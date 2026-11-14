"""E9 frontier reference judge (D-92, D-96): Claude Sonnet 5.5, J1 + DEB at S1 on D1-test, Message Batches, US$ 8 cap.

    python scripts/frontier/e9.py dryrun    # no network, no key: builds pass 1, prints every check and the worst case
    python scripts/frontier/e9.py run       # loads the key from env/.env (D-97) into this process; canary, then passes
    python scripts/frontier/e9.py status

`run` refuses to start unless ANTHROPIC_API_KEY is set in the environment (its value is never read here, printed or
written; the SDK reads it) and `results/runs_frontier/E9_SONNET55_D1TEST/AUTHORS_KEY_SET` exists (the authors create it
after exporting the key and setting the Console spend limit). The first batch is a 3-request canary; any invalid-request
error stops the run before the real passes. Each pass runs the committed runner over the frontier client, which
answers from the frontier call log or queues the call; the queued calls go out as one batch under the cap, and the
loop repeats until every decision is made (J1: one pass; DEB: one pass per dependent call). logs/STOP is honoured.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from triage import config, frontier, scope  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402
from triage.ollama import LOCAL_SCOPE_FILE  # noqa: E402
from triage.prompts import PromptSet  # noqa: E402

EXP = ROOT / "configs" / "experiments" / "E9_SONNET55_D1TEST.json"
RUN = ROOT / "results" / "runs_frontier" / "E9_SONNET55_D1TEST"
STATE = RUN / "batches.jsonl"
GO = RUN / "AUTHORS_KEY_SET"
CANARY = 3
MAX_PASSES = 12                                       # D-99: room for chunked batches and a resume


def exp():
    return json.loads(EXP.read_text(encoding="utf-8"))


def check_frozen_prompts(e):
    frozen = json.loads((ROOT / "configs" / "local_models.FROZEN.json").read_text(encoding="utf-8"))
    ps = PromptSet.named(e["prompt_set"])
    if ps.set_hash() != frozen["prompt_set"]["set_hash"]:
        raise SystemExit("prompt set does not match the frozen prompt hash; refusing")
    return ps.set_hash()


def one_pass(client, e):
    import run_experiment
    r = run_experiment.execute(e, client, RUN, workers=1)
    decided = sum(1 for _ in read_jsonl(RUN / "decisions.jsonl"))
    return {"pending": len(client.pending), "deferred_tasks": r.deferred, "decisions": decided}


def bound_whole_run(client, pending):
    """Worst-case bound for the whole experiment from pass 1: J1 requests as queued; each DEB instance's five calls bounded
    by its first advocate prompt plus every earlier call's full max_tokens of output (rounds 2 and the adjudicator)."""
    j1 = [r for r in pending if r["role"] == "judge"]
    adv = [r for r in pending if r["role"] != "judge"]
    w = sum(frontier.worst_case_usd(r) for r in j1)
    for r in adv:
        mx = r["max_tokens"]
        base = frontier.worst_case_usd(r)
        grow = lambda k: k * mx * frontier.BATCH_PRICE["input"] / 1e6
        w += 2 * base + 2 * (base + grow(2)) + (base + grow(4))
    return w


def cmd_dryrun(_a):
    e = exp()
    h = check_frozen_prompts(e)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        client = frontier.FrontierClient(log_dir=Path(tmp), scope=scope.load(LOCAL_SCOPE_FILE))
        import run_experiment
        run_dir = Path(tmp) / "run"
        r = run_experiment.execute(e, client, run_dir, workers=1)
        pending = list(client.pending.values())
        sample = [frontier.build_params(p) for p in pending[:2]]
        out = {"what": "E9 dry run: pass 1 built, nothing sent", "label": frontier.LABEL, "prompt_set_hash": h,
               "pass1_pending_requests": len(pending), "pass1_roles": {k: sum(1 for p in pending if p["role"] == k)
                                                                       for k in sorted({p["role"] for p in pending})},
               "pass1_worst_case_usd": sum(frontier.worst_case_usd(p) for p in pending),
               "whole_run_worst_case_bound_usd": bound_whole_run(client, pending), "cap_usd": frontier.CAP_USD,
               "deferred_tasks": r.deferred, "leakage_rejections": sum(1 for _ in read_jsonl(run_dir / "leakage_rejections.jsonl")),
               "example_params_without_messages": [{k: v for k, v in s.items() if k != "messages"} for s in sample],
               "sampling_fields_sent": sorted({k for s in sample for k in s if k in ("temperature", "top_p", "top_k")}),
               "key_in_environment": bool(os.environ.get("ANTHROPIC_API_KEY"))}
    RUN.mkdir(parents=True, exist_ok=True)
    dump_json(RUN / "dryrun.json", out)
    print(json.dumps({k: v for k, v in out.items() if k != "example_params_without_messages"}, indent=1))
    if out["whole_run_worst_case_bound_usd"] > frontier.CAP_USD:
        print("WARNING: the whole-run worst-case bound exceeds the cap; the per-batch guard will stop the run first")


ENV_FILE = ROOT / "env" / ".env"                     # D-97: the authors' key file (git-ignored, never staged)


def load_key():
    """Load the key from the authors' .env into this process only; it is never read, printed or written here."""
    from dotenv import load_dotenv
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE, override=False)


def cmd_run(a):
    load_key()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set (env/.env or the environment); the authors provide it")
    if not GO.exists():
        raise SystemExit(f"{GO} not found: the authors create it after setting the Console spend limit")
    e = exp()
    check_frozen_prompts(e)
    import anthropic
    api = anthropic.Anthropic()                       # the SDK reads the key; it is never read or written here
    client = frontier.FrontierClient(scope=scope.load(LOCAL_SCOPE_FILE))
    RUN.mkdir(parents=True, exist_ok=True)
    for i in range(MAX_PASSES):
        st = one_pass(client, e)
        print(f"pass {i}: {st}", flush=True)
        if not client.pending:
            print("no pending calls: every decision is made")
            break
        if frontier.unfinished_batches(STATE):              # D-99: collect a batch already in flight before sending more
            print(f"resumed: {frontier.resume(client, api, STATE)}", flush=True)
            client = frontier.FrontierClient(scope=scope.load(LOCAL_SCOPE_FILE))
            continue
        canary = not any(r.get("event") == "ended" for r in read_jsonl(STATE))    # the very first batch only
        res = frontier.submit_pending(client, api, STATE, limit=CANARY if canary else None)
        print(f"batch: {res}", flush=True)
        if canary and (res.get("errored") or res.get("invalid_after_failures")):
            raise SystemExit("canary batch had errored requests; stopping before the real passes (see batches.jsonl and "
                             "data/raw/llm_calls_frontier/_failures.jsonl)")
        client = frontier.FrontierClient(scope=scope.load(LOCAL_SCOPE_FILE))   # fresh cache from the log
    print("spent US$", round(client.spend_usd(), 4), "of", frontier.CAP_USD)


def cmd_status(_a):
    client = frontier.FrontierClient()
    rows = list(read_jsonl(STATE))
    print(json.dumps({"batches": [r for r in rows if r.get("event") == "ended"],
                      "decisions": sum(1 for _ in read_jsonl(RUN / "decisions.jsonl")),
                      "logged_calls": sum(1 for _ in read_jsonl(client.log_path)),
                      "spent_usd": client.spend_usd(), "cap_usd": frontier.CAP_USD}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["dryrun", "run", "status"])
    a = ap.parse_args()
    {"dryrun": cmd_dryrun, "run": cmd_run, "status": cmd_status}[a.step](a)


if __name__ == "__main__":
    main()
