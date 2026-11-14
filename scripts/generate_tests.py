"""Stage C4 — generate candidate tests with model G (PAID unless --mock). Windows side.

    python scripts/generate_tests.py --split dev [--limit 5] [--mock]
"""
import argparse

from _common import config, load_contexts, local_model, make_client
from triage.generation import generate
from triage.llm import StopRequested
from triage.io_utils import dump_json
from triage.prompts import PromptSet
from triage.sessions import g_session_end, g_session_start


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--prompt-set", default="v0")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--local", action="store_true", help="use the local Ollama generator (configs/local_models.json)")
    ap.add_argument("--model", help="local model tag to use instead of the G role (for sequential G selection)")
    a = ap.parse_args()
    client, prompts = make_client(a.mock, local=a.local), PromptSet.named(a.prompt_set)
    model_id = (a.model or local_model("G")) if a.local else config.MODELS["G"]["id"]
    ctxs = list(load_contexts(a.split).values())[: a.limit]
    if client.scope is not None:  # paid or local: only the approved split (held-out projects are refused)
        client.scope.check_split(a.split, "(test generation)")
        client.scope.check_items(ctxs, "focal method")
    slug = model_id.replace("/", "__").replace(":", "_")
    out_dir = config.INTERIM / ("candidates_mock" if a.mock else (f"candidates_{slug}" if a.local else "candidates"))
    if a.local:   # D-40: RAM / digest / thinking precondition, checked after G loads; raises if not met
        g_session_start(client.backend.api, model_id, client.backend.spec(model_id))
    n_ok = n_gen = 0
    try:
        for ctx in ctxs:
            for g in range(config.GENERATIONS_PER_FOCAL):
                c = generate(ctx, client, prompts, model_id, g)
                dump_json(out_dir / f"{c['candidate_id']}.json", c)
                n_ok += c["assembled"]
                n_gen += 1
    except StopRequested as e:   # D-58: clean stop; re-running resumes from the call log
        print("STOPPED ON REQUEST (D-58):", e, flush=True)
    if a.local:
        g_session_end(model_id, n_gen)
    print(f"{len(ctxs)} focal methods, {n_ok} assembled test classes -> {out_dir}")


if __name__ == "__main__":
    main()
