"""S2 specifications (and S2' for ablation A5b): one M1 call per focal method (PAID unless --mock).

    python scripts/infer_specs.py --split test [--prime]
"""
import argparse

from _common import config, load_contexts, local_model, make_client
from triage.llm import StopRequested
from triage.prompts import PromptSet
from triage.spec_inference import infer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"])
    ap.add_argument("--prime", action="store_true", help="also infer S2' from the buggy body (A5b)")
    ap.add_argument("--prompt-set", default="v0")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--local", action="store_true", help="use the local M1 (configs/local_models.json)")
    a = ap.parse_args()
    client, prompts = make_client(a.mock, local=a.local), PromptSet.named(a.prompt_set)
    m1 = local_model("M1") if a.local else config.MODELS["M1"]["id"]
    ctxs = list(load_contexts(a.split).values())
    if client.scope is not None:  # paid or local: approved split only; --split is mandatory
        client.scope.check_split(a.split, "(spec inference)")
        client.scope.check_items(ctxs, "focal method")
        if a.prime and client.scope.name in ("dev_pilot", "local_dev_selection"):
            raise SystemExit("S2' specifications (ablation A5b) are not part of the approved dev pilot")
    ok = n = 0
    try:
        for ctx in ctxs:
            r = infer(ctx, client, prompts, m1)
            ok += r["valid"]
            n += 1
            if a.prime:
                infer(ctx, client, prompts, m1, with_body=True)
    except StopRequested as e:   # D-58: clean stop; re-running resumes from the call log
        print("STOPPED ON REQUEST (D-58):", e, flush=True)
    print(f"{ok}/{n} valid specifications")


if __name__ == "__main__":
    main()
