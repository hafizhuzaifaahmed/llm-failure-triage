"""D-68 amendment (before Tier 3): a band hit is also fatal when chars / (the model's lowest measured density) >=
num_ctx - num_predict, i.e. when even at the densest packing ever measured for that model the prompt might not have
fitted. The table must hold the lowest measured value per model; an unmeasured model gets the lowest of all."""
import json
import math
from pathlib import Path

import pytest

from triage import ollama
from triage.ollama import MIN_CHARS_PER_TOKEN, min_chars_per_token, truncation_check

ROOT = Path(__file__).resolve().parents[2]
FEAS = ROOT / "results" / "dev" / "feasibility"


def floor3(x: float) -> float:
    return math.floor(x * 1000) / 1000


def test_table_holds_the_lowest_measured_density():
    probe = {m: json.loads((FEAS / f).read_text(encoding="utf-8"))["summary"]["min_chars_per_token"]
             for m, f in [("qwen3.5:9b", "qwen3.5_9b.D35.json"), ("qwen3.5:9b-q8_0", "qwen3.5_9b-q8_0.json"),
                          ("gemma4:12b", "gemma4_12b.json"), ("gemma4:26b", "gemma4_26b.json")]}
    held = {r["model"]: r["min_chars_per_token"] for r in json.loads(
        (ROOT / "results" / "heldout" / "session1_min_density_per_role.json").read_text(encoding="utf-8"))["per_role"]}
    seen = {"qwen3.5:9b": min(probe["qwen3.5:9b"], held["qwen3.5_9b"]), "qwen3.5:9b-q8_0": probe["qwen3.5:9b-q8_0"],
            "gemma4:12b": probe["gemma4:12b"], "gemma4:26b": min(probe["gemma4:26b"], held["gemma4_26b"])}
    assert MIN_CHARS_PER_TOKEN == {m: floor3(v) for m, v in seen.items()}
    assert MIN_CHARS_PER_TOKEN["qwen3.5:9b"] == 2.372 and MIN_CHARS_PER_TOKEN["gemma4:12b"] == 2.314


@pytest.mark.parametrize("model", sorted(MIN_CHARS_PER_TOKEN))
def test_per_model_bound_at_the_band(model):
    d, room = MIN_CHARS_PER_TOKEN[model], 8192 - 512
    edge = math.ceil(d * room)                      # smallest chars with chars / d >= room
    for rep in (4088, 4098, 4160):                  # bottom, Ollama's cut, top of the band
        below, at = edge - 1, edge
        want_below = "fatal" if below / rep > ollama.BAND_FATAL_CHARS_PER_TOKEN else "band_hit_density_normal"
        assert truncation_check(below, rep, 8192, 512, model) == want_below
        assert truncation_check(at, rep, 8192, 512, model) == "fatal"


def test_gemma4_12b_examples():
    # gemma4:12b at 2.314: 17,772 chars could be 7,680 real tokens; the qwen bound (2.372) would have accepted it
    assert truncation_check(17772, 4100, 8192, 512, "gemma4:12b") == "fatal"
    assert truncation_check(17772, 4100, 8192, 512, "qwen3.5:9b") == "band_hit_density_normal"
    assert truncation_check(17770, 4100, 8192, 512, "gemma4:12b") == "band_hit_density_normal"


def test_bound_uses_num_predict():
    # qwen3.5:9b with num_predict 1,024 has 7,168 tokens of room: 2.372 x 7,168 = 17,002.5 chars
    assert truncation_check(17003, 4100, 8192, 1024, "qwen3.5:9b") == "fatal"
    assert truncation_check(17002, 4100, 8192, 1024, "qwen3.5:9b") == "band_hit_density_normal"
    assert truncation_check(17003, 4100, 8192, 512, "qwen3.5:9b") == "band_hit_density_normal"   # 7,680 of room


def test_unmeasured_model_gets_the_lowest_density():
    assert min_chars_per_token("qwen3.5:35b") == min_chars_per_token(None) == 2.314
    assert truncation_check(17772, 4100, 8192, 512, "qwen3.5:35b") == "fatal"
    assert truncation_check(17772, 4100, 8192, 512) == "fatal"


def test_outside_the_band_density_is_not_judged():
    assert truncation_check(30000, 4200, 8192, 512, "gemma4:12b") == "ok"
    assert truncation_check(30000, 4000, 8192, 512, "gemma4:12b") == "ok"
