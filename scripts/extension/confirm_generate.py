"""Generate tests for one confirmation tranche (D-140). Windows side. REFUSES TO RUN unless the readiness gate passes.

    python scripts/extension/confirm_generate.py --tranche F1

Uses the study's own generation code (`triage.generation.generate`), the frozen generator and prompt, and the
study's local client, but writes to the tranche's own directories so that no earlier record is touched:

    data/extension/confirm/<tranche>/llm_calls/     call log (the client resumes from it)
    data/extension/confirm/<tranche>/candidates/    one file per generated test class

`--mock` exercises the driver with the study's mock responder and writes under results/smoke/ only; it makes no
model call, skips the gate, and its output is never research data.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "extension"))

BASE = ROOT / "data" / "extension" / "confirm"
RUNS = ROOT / "configs" / "extension" / "confirm_runs.json"


def load_contexts(tranche: str) -> list[dict]:
    ctxs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((BASE / tranche / "context").glob("*.json"))]
    return sorted(ctxs, key=lambda c: c["focal_id"])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tranche", required=True, choices=["F1", "F2", "CTRL"])
    ap.add_argument("--limit", type=int, help="first N methods only (mock smoke test)")
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args(argv)
    runs = json.loads(RUNS.read_text(encoding="utf-8"))
    tag = runs["datasets"][a.tranche]

    if not a.mock:
        import confirm_gate
        rep = confirm_gate.evaluate()
        if not rep["ready"]:
            for c in rep["checks"]:
                print(f"[{'PASS' if c['ok'] else 'FAIL'}] {c['check']}: {c['detail']}")
            sys.exit("NOT READY: generation is refused (D-140)")
    if a.limit and not a.mock:
        sys.exit("--limit is for the mock smoke test only; a tranche is generated whole")

    from _common import local_model
    from triage import config
    from triage.generation import generate
    from triage.io_utils import dump_json
    from triage.llm import LLMClient, StopRequested
    from triage.prompts import PromptSet

    ctxs = load_contexts(a.tranche)[: a.limit]
    prompts = PromptSet.named(runs["prompt_set"])
    if a.mock:
        from triage.llm import MockBackend
        from triage.mock_responder import responder
        client = LLMClient(MockBackend(responder), log_dir=ROOT / "results" / "smoke" / "confirm_mock" / "llm_calls")
        model_id, out_dir = "mock", ROOT / "results" / "smoke" / "confirm_mock" / a.tranche / "candidates"
    else:
        from triage.ollama import OllamaBackend
        from triage.sessions import g_session_end, g_session_start
        client = LLMClient(OllamaBackend(), log_dir=BASE / a.tranche / "llm_calls")
        model_id, out_dir = local_model("G"), BASE / a.tranche / "candidates"
        client.scope.check_dataset(tag, "(confirmation generation)")
        client.scope.check_split("test", "(confirmation generation)")
        client.scope.check_items(ctxs, "focal method")
        g_session_start(client.backend.api, model_id, client.backend.spec(model_id), log=BASE / "sessions.jsonl")
    assert config.GENERATION_TEMPERATURE == 0.7
    n_ok = n_gen = 0
    try:
        for ctx in ctxs:
            for g in range(int(ctx["generations"])):
                c = generate(ctx, client, prompts, model_id, g)
                dump_json(out_dir / f"{c['candidate_id']}.json", {**c, "tranche": a.tranche, "dataset": tag})
                n_ok += c["assembled"]
                n_gen += 1
    except StopRequested as e:                      # clean stop; re-running resumes from the tranche's call log
        print("STOPPED ON REQUEST:", e, flush=True)
    if not a.mock:
        g_session_end(model_id, n_gen, log=BASE / "sessions.jsonl")
    print(f"{a.tranche} ({tag}): {len(ctxs)} focal methods, {n_gen} generations, {n_ok} assembled test classes -> {out_dir}")


if __name__ == "__main__":
    main()
