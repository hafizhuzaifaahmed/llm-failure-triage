"""Generation contexts and dataset manifest for the CFP confirmation (D-140). WSL entry point.

    wsl -d Ubuntu-22.04 -- bash scripts/wsl/run.sh scripts/extension/confirm_contexts.py [--workers 6]

No model call and no test run. For every row of configs/extension/confirm_frame.jsonl the study's own
`frame.extract_context` builds the buggy-side context. Everything is written under data/extension/confirm/<tranche>/,
never into the study's stores:

    context/<sha16(focal_id)>.json     generation input (buggy side only), with split "test" and the tranche
    label_side/fixed_bodies.jsonl      the fixed body, for labelling and the leakage guard only

configs/extension/confirm_dataset_manifest.json records, per tranche, the methods with a context, those without and
why, and the sha256 of each method's generation prompt (generation index 0), so the inputs to generation are fixed
before any call. The frame file is read, never edited.
"""
import argparse
import hashlib
import json
import sys
import time
import traceback
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import frame  # noqa: E402
from triage.generation import generation_prompt  # noqa: E402
from triage.io_utils import sha256_text  # noqa: E402
from triage.prompts import PromptSet  # noqa: E402

BASE = ROOT / "data" / "extension" / "confirm"
MANIFEST = ROOT / "configs" / "extension" / "confirm_dataset_manifest.json"
TAGS = {"F1": "D1C_F1", "F2": "D1C_F2", "CTRL": "D1C_CTRL"}
PROMPT_SET = "local_m1b"


def read_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _context(rec):
    try:
        info = json.loads((frame.FIX_INFO / rec["bug_name"] / "buggy_fix_info.json").read_text())
        return rec, frame.extract_context(rec, info), None
    except Exception as e:                                  # reported in the manifest, never guessed around
        return rec, None, f"{type(e).__name__}: {e} | {traceback.format_exc()[-300:]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    rows = read_jsonl(ROOT / "configs" / "extension" / "confirm_frame.jsonl")
    prompts = PromptSet.named(PROMPT_SET)
    per = defaultdict(lambda: {"dataset_tag": None, "frame_methods": 0, "contexts": 0, "missing": [], "prompt_sha256": {}})
    for r in rows:
        per[r["tranche"]]["frame_methods"] += 1
        per[r["tranche"]]["dataset_tag"] = TAGS[r["tranche"]]
    label_side = defaultdict(list)
    t0 = time.time()
    with ProcessPoolExecutor(a.workers) as ex:
        for n, f in enumerate(as_completed([ex.submit(_context, r) for r in rows]), 1):
            rec, ctx, err = f.result()
            tr = rec["tranche"]
            if err:
                per[tr]["missing"].append({"focal_id": rec["focal_id"], "error": err.split(" | ")[0][:200]})
                continue
            ls = ctx.pop("_label_side")
            label_side[tr].append({"focal_id": rec["focal_id"], **ls})
            ctx = {**ctx, "split": "test", "project": rec["project"], "bug_name": rec["bug_name"], "tranche": tr,
                   "dataset": TAGS[tr], "generations": rec["generations"]}
            d = BASE / tr / "context"
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{sha256_text(rec['focal_id'])[:16]}.json").write_text(
                json.dumps(ctx, indent=1, sort_keys=True), encoding="utf-8", newline="\n")
            per[tr]["contexts"] += 1
            per[tr]["prompt_sha256"][rec["focal_id"]] = hashlib.sha256(
                generation_prompt(ctx, prompts, 0).encode("utf-8")).hexdigest()
            if n % 100 == 0:
                print(f"  {n}/{len(rows)}  {time.time() - t0:.0f}s", flush=True)
    for tr, recs in label_side.items():
        d = BASE / tr / "label_side"
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "fixed_bodies.jsonl", "w", encoding="utf-8", newline="\n") as f:
            for r in sorted(recs, key=lambda r: r["focal_id"]):
                f.write(json.dumps(r, sort_keys=True) + "\n")
    out = {"decision": "D-140", "prompt_set": PROMPT_SET, "generator_prompt_sha256": prompts.hashes()["generator"]
           if hasattr(prompts, "hashes") else None, "tranches": {}}
    for tr in ("F1", "F2", "CTRL"):
        p = per[tr]
        ids = sorted(p["prompt_sha256"])
        digest = hashlib.sha256("\n".join(f"{i}\t{p['prompt_sha256'][i]}" for i in ids).encode()).hexdigest()
        bugs = {i.split("::")[0] for i in ids}
        gens = {r["focal_id"]: r["generations"] for r in rows if r["tranche"] == tr}
        out["tranches"][tr] = {"dataset_tag": p["dataset_tag"], "frame_methods": p["frame_methods"],
                               "contexts": p["contexts"], "bugs_with_context": len(bugs),
                               "generation_calls": sum(gens[i] for i in ids),
                               "missing": sorted(p["missing"], key=lambda m: m["focal_id"]),
                               "missing_reasons": dict(Counter(m["error"].split(":")[0] for m in p["missing"])),
                               "prompts_digest": digest, "prompt_sha256": {i: p["prompt_sha256"][i] for i in ids}}
    out["generation_calls_total"] = sum(t["generation_calls"] for t in out["tranches"].values())
    MANIFEST.write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8", newline="\n")
    print(json.dumps({tr: {k: v for k, v in t.items() if k not in ("prompt_sha256", "missing")}
                      for tr, t in out["tranches"].items()}, indent=1))
    print("total generation calls", out["generation_calls_total"], f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
