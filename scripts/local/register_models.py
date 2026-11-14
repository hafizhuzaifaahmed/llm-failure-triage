"""Fill configs/local_models.json model entries from the live server: manifest digest, quantization, family,
parameter size, and the model's own default sampling parameters for top_k / min_p (recorded explicitly so a
future Ollama default change cannot alter them). Run after a pull, before feasibility. Never run after the freeze.

    python scripts/local/register_models.py qwen3.5:9b gemma4:12b gemma4:26b
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from triage.ollama import LOCAL_MODELS_FILE, OllamaAPI  # noqa: E402

FAMILY = {"gemma4": "gemma", "qwen3.5": "qwen", "qwen2.5-coder": "qwen"}
JUDGES = {"qwen3.5:9b", "qwen3.5:9b-q8_0", "qwen3.5:35b", "gemma4:12b", "gemma4:e4b"}


def main():
    cfg = json.loads(LOCAL_MODELS_FILE.read_text(encoding="utf-8"))
    if cfg.get("frozen"):
        raise SystemExit("configuration is frozen; registration is not allowed")
    api = OllamaAPI()
    tags = api.tags()
    for tag in sys.argv[1:]:
        if tag not in tags:
            raise SystemExit(f"{tag} is not pulled")
        show = api.show(tag)
        params = {}
        for line in (show.get("parameters") or "").splitlines():
            m = re.match(r"\s*(\w+)\s+(.+)", line)
            if m:
                params.setdefault(m.group(1), []).append(m.group(2).strip().strip('"'))
        d = show.get("details") or {}
        entry = cfg["models"].get(tag, {})
        entry.update({
            "family": FAMILY.get(tag.split(":")[0], d.get("family")),
            "digest": tags[tag]["digest"], "size_bytes": tags[tag].get("size"),
            "quantization": d.get("quantization_level"), "parameter_size": d.get("parameter_size"),
            "format": d.get("format"), "ollama_family": d.get("family"), "modelfile_parameters": params,
            "num_ctx": 8192, "think": False, "keep_alive": "30m",
            "top_k": int(params["top_k"][0]) if "top_k" in params else 40,
            "min_p": float(params["min_p"][0]) if "min_p" in params else 0.0,
            "require_gpu_resident": tag in JUDGES,
        })
        for k in ("presence_penalty", "frequency_penalty", "repeat_penalty", "repeat_last_n"):  # D-34
            if k in params:
                entry[k] = float(params[k][0]) if k != "repeat_last_n" else int(params[k][0])
        cfg["models"][tag] = entry
        print(tag, entry["digest"], entry["quantization"], entry["parameter_size"], "top_k", entry["top_k"],
              "min_p", entry["min_p"])
    LOCAL_MODELS_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
