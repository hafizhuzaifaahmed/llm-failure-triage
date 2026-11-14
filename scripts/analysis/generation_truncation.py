"""Generation-truncation check (D-91; zero model calls): how many of G's 702 D1 generations were lost to length.

For every generation record (data/interim/candidates_gemma4_26b) the matching generator call in the frozen call log
(same key) is read and three length signals are taken, fixed in D-91 before this script was run:
  (1) output cap:   done_reason/finish_reason == "length", or eval_count >= num_predict
  (2) context:      prompt_eval_count + eval_count >= num_ctx, or the committed input truncation rule says "fatal"
  (3) cut-off code: the Java code in the reply has unbalanced braces (strings, chars and comments skipped) or an
                    unclosed ``` fence
Each signal is reported alone and as a union, crossed with NC_CLASS (the whole class did not compile,
data/processed/exclusions_D1.jsonl) and with the number of tests the generation yielded.

Decision rule (D-91, fixed before computing): a larger generation context for E7a is justified iff the union marks at
least 5% of the 702 generations; otherwise E7a keeps the frozen num_ctx 8192 / num_predict 4096. E7a itself still
needs its own approval either way.

    python scripts/analysis/generation_truncation.py   -> results/heldout/generation_truncation.json
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage.io_utils import dump_json, read_jsonl  # noqa: E402
from triage.ollama import truncation_check  # noqa: E402

CANDS = ROOT / "data" / "interim" / "candidates_gemma4_26b"
CALLS = ROOT / "data" / "raw" / "llm_calls_local" / "gemma4_26b.jsonl"
EXCL = ROOT / "data" / "processed" / "exclusions_D1.jsonl"
OUT = ROOT / "results" / "heldout" / "generation_truncation.json"
THRESHOLD = 0.05


def code_of(text: str) -> tuple[str, bool]:
    """The Java code of a reply and whether a ``` fence was left open."""
    fences = [m.start() for m in re.finditer(r"```", text)]
    if not fences:
        return text, False
    unclosed = len(fences) % 2 == 1
    parts = re.split(r"```[a-zA-Z]*\n?", text)
    code = "\n".join(parts[1::2]) if len(parts) > 1 else text
    return code, unclosed


def brace_balance(code: str) -> int:
    """{ minus } outside string/char literals and comments."""
    depth, i, n = 0, 0, len(code)
    while i < n:
        c = code[i]
        if code.startswith("//", i):
            j = code.find("\n", i)
            i = n if j < 0 else j
        elif code.startswith("/*", i):
            j = code.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif c in "\"'":
            if code.startswith('"""', i):
                j = code.find('"""', i + 3)
                i = n if j < 0 else j + 3
                continue
            j = i + 1
            while j < n and code[j] != c and code[j] != "\n":
                j += 2 if code[j] == "\\" else 1
            i = j + 1
        else:
            depth += (c == "{") - (c == "}")
            i += 1
    return depth


def main():
    calls = {}
    for d in read_jsonl(CALLS):
        if d.get("role") == "generator":
            calls[d["key"]] = d                      # last record for a key wins (a retry supersedes)
    nc_class = {e["candidate_id"] for e in read_jsonl(EXCL) if e.get("category") == "NC_CLASS"}
    rows, missing = [], []
    for p in sorted(CANDS.glob("*.json")):
        c = json.loads(p.read_text(encoding="utf-8"))
        d = calls.get(c["call_key"])
        if d is None:
            missing.append(c["candidate_id"])
            continue
        loc = d.get("local") or {}
        opt = loc.get("options") or {}
        num_ctx, num_predict = int(opt.get("num_ctx", 8192)), int(opt.get("num_predict", d.get("max_tokens") or 4096))
        pe, ev = int(loc.get("prompt_eval_count") or 0), int(loc.get("eval_count") or d.get("output_tokens") or 0)
        code, unclosed = code_of(d.get("text") or "")
        bal = brace_balance(code)
        s1 = (loc.get("done_reason") or d.get("finish_reason")) == "length" or ev >= num_predict
        s2 = pe + ev >= num_ctx or truncation_check(int(loc.get("prompt_chars") or 0), pe, num_ctx, num_predict,
                                                    d.get("model_requested")) == "fatal"
        s3 = bal != 0 or unclosed
        rows.append({"candidate_id": c["candidate_id"], "focal_id": c["focal_id"], "generation": c["generation"],
                     "n_tests": int(c["n_tests"]), "assembled": bool(c.get("assembled")),
                     "nc_class": c["candidate_id"] in nc_class, "prompt_tokens": pe, "output_tokens": ev,
                     "num_ctx": num_ctx, "num_predict": num_predict, "brace_balance": bal, "unclosed_fence": unclosed,
                     "s1_output_cap": s1, "s2_context": s2, "s3_cut_off_code": s3, "any": s1 or s2 or s3})
    n = len(rows)
    count = lambda f: sum(1 for r in rows if f(r))
    union = count(lambda r: r["any"])
    out = {"what": "generation-truncation check (D-91, zero calls)", "generator": "gemma4:26b (G, frozen)",
           "generations": n, "missing_call_records": missing,
           "settings": dict(Counter(f"num_ctx {r['num_ctx']} / num_predict {r['num_predict']}" for r in rows).most_common()),
           "signals": {"s1_output_cap": count(lambda r: r["s1_output_cap"]),
                       "s2_context": count(lambda r: r["s2_context"]),
                       "s3_cut_off_code": count(lambda r: r["s3_cut_off_code"]), "union": union},
           "union_share": union / n if n else None,
           "nc_class": {"total": count(lambda r: r["nc_class"]),
                        "with_a_length_signal": count(lambda r: r["nc_class"] and r["any"])},
           "not_assembled": count(lambda r: not r["assembled"]),
           "tests_in_flagged_generations": sum(r["n_tests"] for r in rows if r["any"]),
           "flagged_with_zero_tests": count(lambda r: r["any"] and r["n_tests"] == 0),
           "output_tokens": {"max": max(r["output_tokens"] for r in rows), "p99": sorted(r["output_tokens"] for r in rows)[int(0.99 * (n - 1))],
                             "median": sorted(r["output_tokens"] for r in rows)[n // 2]},
           "max_prompt_plus_output": max(r["prompt_tokens"] + r["output_tokens"] for r in rows),
           "rule": f"larger E7a generation context justified iff union_share >= {THRESHOLD} (D-91)",
           "larger_context_justified": bool(n and union / n >= THRESHOLD),
           "flagged": [r for r in rows if r["any"]]}
    dump_json(OUT, out)
    print(json.dumps({k: v for k, v in out.items() if k != "flagged"}, indent=1))


if __name__ == "__main__":
    main()
