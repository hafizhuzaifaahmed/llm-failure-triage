"""D-68 amendment re-scan: every logged local call, judged by the D-68 rule as adopted (4.5 chars/token) and by the
amended rule (also fatal when chars / the model's lowest measured density >= num_ctx - num_predict). Reads metadata
only (model, max_tokens, prompt chars, reported prompt tokens, num_ctx) -- never prompts, responses or verdicts.

    python scripts/local/d68_rescan_per_model.py   -> results/heldout/d68_rescan_per_model.json
"""
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config, ollama  # noqa: E402
from triage.io_utils import dump_json, read_jsonl  # noqa: E402


def as_adopted(chars, rep, num_ctx, max_tokens):
    """D-68 before the amendment (4.5 chars/token only)."""
    if rep <= 0:
        return "fatal" if chars > 0 else "ok"
    if rep >= num_ctx - max_tokens:
        return "fatal"
    lo, hi = num_ctx // 2 + ollama.TRUNCATION_BAND[0], num_ctx // 2 + ollama.TRUNCATION_BAND[1]
    if lo <= rep <= hi:
        return "fatal" if chars / rep > ollama.BAND_FATAL_CHARS_PER_TOKEN else "band_hit_density_normal"
    return "ok"


def main():
    out = {"fields_read": ["model_requested", "role", "tag", "max_tokens", "local.prompt_chars",
                           "local.prompt_eval_count", "local.options.num_ctx"],
           "min_chars_per_token": ollama.MIN_CHARS_PER_TOKEN, "by_log": {}, "changed": [], "band_hits": []}
    for f in sorted(ollama.LOCAL_CALL_LOG_DIR.glob("*.jsonl")):
        if f.name.startswith("_"):
            continue
        tally = Counter()
        for r in read_jsonl(f):
            loc = r.get("local") or {}
            if not loc:
                continue
            chars, rep = int(loc.get("prompt_chars") or 0), int(loc.get("prompt_eval_count") or 0)
            num_ctx = int((loc.get("options") or {}).get("num_ctx", config.MAX_INPUT_TOKENS))
            model = r.get("model_requested")
            old = as_adopted(chars, rep, num_ctx, r["max_tokens"])
            new = ollama.truncation_check(chars, rep, num_ctx, r["max_tokens"], model)
            tally[f"{old}->{new}"] += 1
            row = {"log": f.name, "key": r["key"][:12], "model": model, "role": r.get("role"), "tag": r.get("tag"),
                   "max_tokens": r["max_tokens"], "prompt_chars": chars, "prompt_eval_count": rep,
                   "chars_per_token": round(chars / rep, 3) if rep else None,
                   "per_model_bound_chars": round(ollama.min_chars_per_token(model) * (num_ctx - r["max_tokens"]), 1),
                   "adopted": old, "amended": new}
            if old != new:
                out["changed"].append(row)
            if "band_hit_density_normal" in (old, new):
                out["band_hits"].append(row)
        out["by_log"][f.name] = dict(tally)
    out["calls_scanned"] = sum(sum(t.values()) for t in out["by_log"].values())
    out["newly_fatal"] = sum(1 for c in out["changed"] if c["amended"] == "fatal")
    out["newly_accepted"] = sum(1 for c in out["changed"] if c["amended"] != "fatal")
    if out["band_hits"]:
        out["smallest_margin_chars"] = min(b["per_model_bound_chars"] - b["prompt_chars"] for b in out["band_hits"])
    dump_json(ROOT / "results" / "heldout" / "d68_rescan_per_model.json", out)
    print(f"scanned {out['calls_scanned']} | newly fatal {out['newly_fatal']} | newly accepted {out['newly_accepted']} "
          f"| band hits {len(out['band_hits'])} | smallest margin {out.get('smallest_margin_chars')} chars")
    for k, v in out["by_log"].items():
        print(f"  {k:28s} {v}")


if __name__ == "__main__":
    main()
