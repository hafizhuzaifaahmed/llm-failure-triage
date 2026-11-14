"""GPU non-determinism study (MODEL_SELECTION_PROTOCOL "GPU non-determinism plan"). Dev split only.

    python scripts/local/nondeterminism.py --prompt-set <frozen dev set> [--n 50]

50 dev pilot instances (seeded choice), J1 at S1 with M1: each prompt is sent twice with the SAME seed at T = 0
(pure runtime non-determinism) and twice with the same seed at T = 0.7 (runtime + sampling with a fixed seed).
Packages are built and leakage-checked exactly as in study runs. Calls go to the raw API (measurement, not study
decisions). Writes results/dev/nondeterminism.json with label-flip and identical-text rates.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage.context_builder import build_package, leakage_check  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402
from triage.ollama import OllamaAPI, load_local_models, model_options, schema_for_role  # noqa: E402
from triage.prompts import PromptSet  # noqa: E402
from triage.schema import parse_output  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt-set", required=True)
    ap.add_argument("--n", type=int, default=50)
    a = ap.parse_args()
    cfg = load_local_models()
    m1 = cfg["roles"]["M1"]
    spec = cfg["models"][m1]
    sample = json.loads((config.PROCESSED / "sample_D1_dev_pilot.json").read_text())["instance_ids"]
    insts = {i["instance_id"]: i for i in read_jsonl(config.PROCESSED / "instances_D1.jsonl") if i["split"] == "dev"}
    guard = {g["instance_id"]: g for g in read_jsonl(config.LEAKAGE_GUARD / "guard_D1.jsonl")}
    ids = sorted(i for i in sample if i in insts)
    random.Random(20261102).shuffle(ids)
    ids = ids[: a.n]
    prompts = PromptSet.named(a.prompt_set)
    api = OllamaAPI()
    rows = []
    for k, iid in enumerate(ids):
        inst = insts[iid]
        pkg = build_package(inst, "S1")
        body = inst["impl"][inst["impl"].find("{") + 1:]
        hits = leakage_check(pkg.text, guard.get(iid), [l.strip() for l in body.split("\n") if len(l.strip()) >= 25])
        if hits:
            rows.append({"instance_id": iid, "skipped": "leakage", "hits": hits[:3]})
            continue
        text = prompts.render("judge", package=pkg.text)
        row = {"instance_id": iid}
        for temp in (0.0, 0.7):
            outs = []
            for _ in range(2):
                o = api.chat({"model": m1, "messages": [{"role": "user", "content": text}], "stream": False,
                              "think": False, "format": schema_for_role("judge"), "keep_alive": "30m",
                              "options": {"num_ctx": spec["num_ctx"], "num_predict": config.MAX_OUTPUT_TOKENS,
                                          "temperature": temp, "top_p": 1.0, "seed": 5000 + k,
                                          **model_options(spec)}})
                c = (o.get("message") or {}).get("content") or ""
                p = parse_output(c, "judge")
                outs.append((c, p.data.get("label") if p.ok else "INVALID"))
            row[f"T{temp}"] = {"identical_text": outs[0][0] == outs[1][0], "label_flip": outs[0][1] != outs[1][1],
                               "labels": [outs[0][1], outs[1][1]]}
        rows.append(row)
        print(iid, row.get("T0.0"), row.get("T0.7"), flush=True)
    done = [r for r in rows if "skipped" not in r]
    res = {"model": m1, "digest": spec.get("digest"), "prompt_set": a.prompt_set, "n": len(done),
           "skipped": len(rows) - len(done), "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for t in ("T0.0", "T0.7"):
        res[t] = {"label_flip_rate": sum(r[t]["label_flip"] for r in done) / len(done) if done else None,
                  "identical_text_rate": sum(r[t]["identical_text"] for r in done) / len(done) if done else None}
    res["rows"] = rows
    dump_json(config.ROOT / "results" / "dev" / "nondeterminism.json", res)
    print(json.dumps({k: res[k] for k in ("n", "T0.0", "T0.7")}, indent=1))


if __name__ == "__main__":
    main()
