"""D-12 / D-66: SC-T draws samples independent of SC. The arm name is part of the call tag, so the same package,
sample index and replicate give a different call key and therefore a different sampling seed."""
from triage.llm import request_key

MSG = [{"role": "user", "content": "package text"}]


def _key(arm: str, i: int) -> str:
    return request_key("qwen3.5:9b", MSG, 0.7, 0.95, 512, i, tag=f"{arm}|S1|full")


def test_sc_t_keys_and_seeds_differ_from_sc():
    for i in range(5):
        sc, sct = _key("SC", i), _key("SC-T", i)
        assert sc != sct
        assert int(sc[:8], 16) % 2_147_483_647 != int(sct[:8], 16) % 2_147_483_647
    assert len({_key("SC-T", i) for i in range(5)}) == 5
