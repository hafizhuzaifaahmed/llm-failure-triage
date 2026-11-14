"""Freeze manifest for the CFP confirmation (D-138).

    python scripts/extension/freeze_cfp.py --write     # once; refuses to overwrite an existing manifest
    python scripts/extension/freeze_cfp.py --check     # exit 1 and list every difference

The manifest (configs/extension/cfp_frozen.json) records a content hash of every file that determines a confirmation
result, and every engine parameter. Hash = sha256 of the file's bytes with CRLF normalised to LF, so that a checkout
with different line endings still verifies.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config  # noqa: E402
from triage_ext import ledger, mutate, policy, probe  # noqa: E402

MANIFEST = ROOT / "configs" / "extension" / "cfp_frozen.json"
FILES = ["src/triage_ext/mutate.py", "src/triage_ext/probe.py", "src/triage_ext/ledger.py", "src/triage_ext/policy.py",
         "scripts/extension/run_probes_tranche.py", "scripts/extension/confirm_analysis.py",
         "scripts/extension/build_confirm_frames.py", "configs/extension/confirm_frame.jsonl"]


def content_hash(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def parameters() -> dict:
    return {"max_mutants_per_focal": mutate.MAX_MUTANTS, "callee_depth": probe.CALLEE_DEPTH,
            "probe_timeout_s": probe.PROBE_TIMEOUT_S, "baseline_timeout_s": 30, "max_siblings": probe.MAX_SIBLINGS,
            "min_compiled_mutants_for_decoupling": ledger.MIN_MUTANTS, "parallel_jvms": 12,
            "operators": {"ROR": mutate.ROR, "AOR": mutate.AOR, "COR": mutate.COR,
                          "LVR": "0->1, 1->0, n->{n+1,n-1}, true<->false", "NEG": "if (c) -> if (!(c))",
                          "STD": "delete one statement that is not a control transfer"},
            "source_levels_tried": list(probe.SOURCE_LEVELS), "decision_rules": sorted(policy.RULES),
            "bootstrap": {"resamples": config.BOOTSTRAP_RESAMPLES, "seed": config.SEED_BOOTSTRAP}}


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    current = {"files": {f: content_hash(f) for f in FILES}, "parameters": parameters()}
    if a.write:
        if MANIFEST.exists():
            sys.exit(f"{MANIFEST} exists; a frozen configuration is not rewritten")
        frozen = json.loads((ROOT / "configs" / "local_models.FROZEN.json").read_text(encoding="utf-8"))
        gen = frozen["models"][frozen["roles"]["G"]]
        doc = {"decision": "D-138", "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "engine_identical_to_commit": "eb2d231 (the engine that produced CFP_D1_TEST)",
               "hash_method": "sha256 of file bytes with CRLF normalised to LF", **current,
               "generator": {"model": frozen["roles"]["G"], "digest": gen["digest"], "quantization": gen["quantization"],
                             "parameter_size": gen["parameter_size"], "num_ctx": gen["num_ctx"], "top_k": gen["top_k"],
                             "temperature": config.GENERATION_TEMPERATURE, "top_p": 1.0, "max_output_tokens": 4096,
                             "think": gen["think"], "prompt_set": frozen["prompt_set"]["name"],
                             "generator_prompt_sha256": frozen["prompt_set"]["hashes"]["generator"],
                             "runtime": frozen["runtime"], "server_env": frozen["server_env"]}}
        MANIFEST.write_text(json.dumps(doc, indent=1, sort_keys=True), encoding="utf-8", newline="\n")
        print("written", MANIFEST)
        return
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    bad = [f"file changed: {f}" for f, h in doc["files"].items() if current["files"].get(f) != h]
    bad += [f"parameter changed: {k}" for k, v in doc["parameters"].items() if current["parameters"].get(k) != v]
    if bad:
        print("\n".join(bad))
        sys.exit(1)
    print("frozen configuration verified:", len(doc["files"]), "files,", len(doc["parameters"]), "parameters")


if __name__ == "__main__":
    main()
