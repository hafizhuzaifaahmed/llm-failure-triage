"""Step 6 — write the one immutable configuration file for the held-out run (MODEL_SELECTION_PROTOCOL Step 6).

    python scripts/local/freeze.py [--exploratory qwen3.5:35b]

Builds configs/local_models.FROZEN.json from the working config, the live server and the dev evidence: Ollama
version; server environment; for G, M1, M2 (and an included exploratory model): tag, manifest digest, GGUF blob
digests, quantization, family, parameter count, licence hash, chat-template hash, num_ctx, num_predict,
temperature, top_p, top_k / min_p / penalties, seed policy, think, per-role format-schema hashes, keep_alive,
runner and residency evidence; prompt-set hashes; dev-gate outcomes; k_T; sampling (X-07). Refuses if a frozen
file already exists. Prints the file's SHA-256 (record it in DECISIONS.md).
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage import config, hwinfo  # noqa: E402
from triage.io_utils import sha256_text  # noqa: E402
from triage.ollama import (FROZEN_MODELS_FILE, LOCAL_MODELS_FILE, OllamaAPI, model_options,  # noqa: E402
                           schema_for_role)
from triage.prompts import PromptSet  # noqa: E402

MANIFESTS = Path.home() / ".ollama" / "models" / "manifests" / "registry.ollama.ai" / "library"
ROLES_FOR_SCHEMA = ("judge", "adjudicator", "advocate_p_r1", "spec_inferencer")


def manifest(tag: str) -> dict:
    name, t = tag.split(":")
    return json.loads((MANIFESTS / name / t).read_text(encoding="utf-8"))


def model_entry(api, tag: str, spec: dict, role: str) -> dict:
    show = api.show(tag)
    m = manifest(tag)
    info = show.get("model_info") or {}
    return {
        "role": role, "tag": tag, "manifest_digest": spec["digest"],
        "blobs": [{"mediaType": l["mediaType"], "digest": l["digest"], "size": l["size"]} for l in m["layers"]],
        "quantization": spec.get("quantization"), "family": spec.get("family"), "ollama_family": spec.get("ollama_family"),
        "parameter_size": spec.get("parameter_size"), "parameter_count": info.get("general.parameter_count"),
        "licence_sha256": sha256_text(show.get("license") or ""), "chat_template_sha256": sha256_text(show.get("template") or ""),
        "capabilities": show.get("capabilities"),
        "num_ctx": spec["num_ctx"], "num_predict": {"judge_roles": config.MAX_OUTPUT_TOKENS, "generator": 4096},
        "temperature": {"judges": config.TEMPERATURE, "spec_inferencer": config.SPEC_TEMPERATURE,
                        "generator": config.GENERATION_TEMPERATURE},
        "top_p": 1.0, **model_options(spec),
        "seed_policy": "seed = int(request_key[:8], 16) mod 2147483647 (request key = model, messages, temperature, "
                       "top_p, max_tokens, sample_index, tag, routing)",
        "think": spec.get("think", False), "keep_alive": spec.get("keep_alive"),
        "format_schema_sha256": {r: sha256_text(json.dumps(schema_for_role(r), sort_keys=True)) for r in ROLES_FOR_SCHEMA},
        "require_gpu_resident": spec.get("require_gpu_resident", False),
        "modelfile_parameters": spec.get("modelfile_parameters"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exploratory", help="tag of an included exploratory model (D-55)")
    a = ap.parse_args()
    if FROZEN_MODELS_FILE.exists():
        raise SystemExit(f"{FROZEN_MODELS_FILE} already exists; the freeze is immutable")
    work = json.loads(LOCAL_MODELS_FILE.read_text(encoding="utf-8"))
    env = json.loads((config.ROOT / "configs" / "local_server_env.json").read_text(encoding="utf-8"))
    api = OllamaAPI()
    roles = work["roles"]
    models = {role: model_entry(api, tag, work["models"][tag], role) for role, tag in roles.items()}
    if a.exploratory:
        models["EXPLORATORY"] = model_entry(api, a.exploratory, work["models"][a.exploratory], "exploratory (D-55)")
    ps = PromptSet.named("local_m1b")
    dev = lambda p: json.loads((config.ROOT / p).read_text(encoding="utf-8"))
    g1, m2, gsel = dev("results/dev/GATE_M1b/dev_gates.json"), dev("results/dev/CHECK_M2/dev_gates.json"), \
        dev("results/dev/g_selection_gemma4_26b.json")
    keep = ("G_a_valid_rate", "G_a", "G_b_citations", "G_b", "G_c", "G_d", "G_d_detail", "P4")
    frozen = {
        "frozen": True, "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime": {"engine": "ollama", "version": api.version(), "runner": "llamacpp (bundled llama-server) for all three"
                    " models under the frozen env (D-38, D-46)"},
        "server_env": env["env"], "hardware": {**{k: v for k, v in hwinfo.gpu().items() if k in ("name", "mem_total_mib",
                                                                                                 "driver", "cuda")},
                                               "driver": hwinfo.gpu().get("driver"), "ram_total_gib": hwinfo.ram().get("total_gib")},
        "roles": roles, "models": {m["tag"]: {**work["models"][m["tag"]], "digest": m["manifest_digest"]} for m in models.values()},
        "frozen_models": models,
        "prompt_set": {"name": "local_m1b", "set_hash": ps.set_hash(), "hashes": ps.hashes()},
        "decoding": {"package_cap_tokens": config.MAX_PACKAGE_TOKENS, "chars_per_token_estimate": config.CHARS_PER_TOKEN_ESTIMATE,
                     "max_argument_words": config.MAX_ARGUMENT_WORDS, "sc_samples": config.SC_SAMPLES,
                     "deb_calls": config.DEB_CALLS, "replicates": config.REPLICATES, "k_T": g1["P4"]["k_T"]},
        "sampling": {"D1_test": "overall / proportional 1:2, TF stratified by project (X-07, D-53)",
                     "dev_pilot": "within-project 1:2 (selection only)"},
        "dev_evidence": {"G_selection": {k: gsel.get(k) for k in ("C1", "C1_ci95", "C2", "C2_ci95", "P1", "P1_ci95",
                                                                   "C4_uniqueness", "verdict", "selected")},
                         "M1_gate": {k: g1.get(k) for k in keep}, "M2_check": {k: m2.get(k) for k in keep},
                         "note": "DEV PILOT; M1 fails G-d (D-48, D-50, D-52) — reported as a finding (option a)"},
        "residency_check": "session_check.py reads 'offloaded X/Y layers' from the server log for llamacpp-runner models",
    }
    text = json.dumps(frozen, indent=2, sort_keys=True)
    FROZEN_MODELS_FILE.write_text(text, encoding="utf-8")
    print(FROZEN_MODELS_FILE, "sha256", sha256_text(text))


if __name__ == "__main__":
    main()
