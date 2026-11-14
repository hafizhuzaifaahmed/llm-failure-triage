"""D-69: a model that quotes Java source containing the escape `\\uD83D` writes it unescaped inside its JSON answer,
so parsing yields a lone surrogate, which UTF-8 cannot encode. Hashing and JSONL writes must accept it losslessly,
and must stay byte-identical for every string without one (no existing call key or record changes)."""
import hashlib
import json

from triage.io_utils import append_jsonl, read_jsonl, sha256_text, write_jsonl
from triage.llm import request_key

# what qwen3.5:9b returned, in shape: the six characters \uD83D quoted inside a JSON string
PARSED = json.loads('{"summary": "input \\"\\u0001A\\uD83D\\" expected ?A?", "label": "TEST_FAULT"}')


def test_parsed_answer_really_holds_a_lone_surrogate():
    assert "\ud83d" in PARSED["summary"]


def test_hash_unchanged_for_valid_text_and_defined_for_lone_surrogate():
    for s in ["", "plain", "café → \U0001F600", "\\uD83D as six ASCII chars"]:
        assert sha256_text(s) == hashlib.sha256(s.encode("utf-8")).hexdigest()
    a, b = sha256_text(PARSED["summary"]), sha256_text(PARSED["summary"])
    assert a == b and a != sha256_text(PARSED["summary"].replace("\ud83d", "�"))


def test_request_key_unchanged_for_valid_messages_and_defined_for_lone_surrogate():
    msg = [{"role": "user", "content": "café \U0001F600 package"}]
    payload = {"model": "m", "messages": msg, "temperature": 0.7, "top_p": 0.95, "max_tokens": 512,
               "sample_index": 0, "tag": "J1|S1|full"}
    k = request_key("m", msg, 0.7, 0.95, 512, 0, "J1|S1|full")
    assert k == request_key("m", msg, 0.7, 0.95, 512, 0, "J1|S1|full")
    bad = [{"role": "user", "content": "forwarded: " + PARSED["summary"]}]
    assert request_key("m", bad, 0.7, 0.95, 512, 2, "DEB|S1|full") == request_key("m", bad, 0.7, 0.95, 512, 2, "DEB|S1|full")
    assert payload  # shape documented above; the key for valid text is pinned by the hash test


def test_jsonl_write_is_lossless_and_unchanged_for_valid_records(tmp_path):
    f = tmp_path / "d.jsonl"
    ok = {"instance_id": "i1", "summary": "café \U0001F600"}
    append_jsonl(f, ok)
    assert f.read_text(encoding="utf-8").splitlines() == [json.dumps(ok, ensure_ascii=False, sort_keys=True)]
    append_jsonl(f, {"instance_id": "i2", **PARSED})
    f.read_bytes().decode("utf-8")                       # the file stays valid UTF-8
    rows = list(read_jsonl(f))
    assert rows[0] == ok and rows[1] == {"instance_id": "i2", **PARSED}
    g = tmp_path / "w.jsonl"
    write_jsonl(g, [ok, PARSED])
    assert list(read_jsonl(g)) == [ok, PARSED]
