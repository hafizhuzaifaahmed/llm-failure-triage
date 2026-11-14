"""D2 helpers: Major log parsing, focal filtering and exact materialisation (offsets as Major logs them)."""
from triage import mutants

LOG = ("57:ROR:==(java.lang.Object,java.lang.Object):FALSE(java.lang.Object,java.lang.Object):"
       "org.apache.commons.lang3.math.NumberUtils@createNumber(java.lang.String):451:30:str == null |==> false\n"
       "58:COR:<METHOD_INVOCATION(boolean)>:FALSE:org.apache.commons.lang3.math.NumberUtils@createNumber(java.lang.String)"
       ":454:91:StringUtils.isBlank(str) |==> false\n"
       "60:LVR:0:POS:org.apache.commons.lang3.math.NumberUtils@isDigits(java.lang.String):459:0:0 |==> 1\n")
SRC = ("public Number createNumber(final String str) {\n"   # 'str == null' starts at 26; '==' at 30
       "    if (str == null) { return null; }\n"
       "    if (StringUtils.isBlank(str)) { throw new X(); }\n"
       "    int a = 0; int b = 0;\n}")


def test_parse_and_focal_filter():
    ms = mutants.parse_mutants_log(LOG)
    assert [m["id"] for m in ms] == [57, 58, 60] and ms[0]["params"] == ["java.lang.String"]
    f = [m for m in ms if mutants.in_focal(m, "org.apache.commons.lang3.math.NumberUtils", "createNumber", ["String"])]
    assert [m["id"] for m in f] == [57, 58]


def test_materialise_uses_span_containing_offset():
    ms = {m["id"]: m for m in mutants.parse_mutants_log(LOG)}
    off_eq = SRC.index("==")
    out = mutants.materialise(SRC, {**ms[57], "offset": off_eq})
    assert "if (false)" in out and out.count("str == null") == 0
    off_paren = SRC.index("(str))")
    out = mutants.materialise(SRC, {**ms[58], "offset": off_paren})
    assert "if (false)" in out and "isBlank" not in out


def test_materialise_refuses_ambiguous_or_missing():
    m = {"original": "0", "mutated": "1", "offset": SRC.index("a = 0") + 4}
    out = mutants.materialise(SRC, m)
    assert "int a = 1; int b = 0;" in out                      # the 0 under the offset, not the other one
    assert mutants.materialise(SRC, {"original": "zzz", "mutated": "y", "offset": 5}) is None


def test_crlf_sources_keep_major_offsets_and_bytes(tmp_path):
    crlf = SRC.replace("\n", "\r\n")
    p = tmp_path / "Foo.java"
    p.write_bytes(crlf.encode("utf-8"))
    text, enc = mutants.read_src(p)
    assert text == crlf and enc == "utf-8"                      # no newline translation
    off = crlf.index("==")                                       # offset as Major counts it (CR included)
    out = mutants.materialise(text, {"original": "str == null", "mutated": "false", "offset": off})
    mutants.write_src(p, out, enc)
    assert p.read_bytes().count(b"\r\n") == crlf.count("\r\n") and b"if (false)" in p.read_bytes()
    p.write_bytes("caf\xe9 = 1;".encode("latin-1"))
    assert mutants.read_src(p)[1] == "latin-1"


def test_seeded_order_is_a_deterministic_permutation():
    a = mutants.seeded_order("f1", [5, 1, 9, 3])
    assert sorted(a) == [1, 3, 5, 9] and a == mutants.seeded_order("f1", [3, 9, 1, 5])
    assert a != sorted(a) or mutants.seeded_order("f2", [5, 1, 9, 3]) != a
