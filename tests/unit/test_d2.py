"""D2 pipeline (D-62): ids, mutant selection, context extraction from D2's own B, the held-out/dataset lock, G
generation against the fake Ollama server, stop handling, and dataset build/labels/guard. Synthetic fixtures only:
no Defects4J, no real model, no held-out D2 outcome."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from triage import config, d2, dataset, llm, ollama, scope  # noqa: E402
from triage.io_utils import read_jsonl  # noqa: E402
from triage.llm import LLMClient, StopRequested  # noqa: E402
from triage.ollama import OllamaAPI, OllamaBackend  # noqa: E402
from triage.prompts import PromptSet  # noqa: E402
from triage.scope import ScopeViolation  # noqa: E402
from test_ollama_local import CFG, STATE, TAG, server  # noqa: E402,F401  (fake Ollama server fixture)

BASE = "Lang_1::p.Calc::add(int,int)"
F_SRC = """package p;

public class Calc {
    /** Adds two numbers. */
    public int add(int first, int second) {
        int result = first + second;
        return result;
    }

    public int twice(int x) {
        return add(x, x);
    }
}
"""
B_SRC = F_SRC.replace("int result = first + second;", "int result = first - second;")
MUT_LINE = 6


def _tree(root: Path, src: str) -> Path:
    f = root / "src" / "p" / "Calc.java"
    f.parent.mkdir(parents=True)
    f.write_bytes(src.encode("utf-8"))        # exact bytes: Major offsets and source hashes count every character
    return root


def _rec(split="test"):
    return {"focal_id": BASE, "project": "Lang", "bug": "1", "bug_name": "Lang_1", "split": split,
            "file": "src/p/Calc.java", "qualified": "p.Calc:add:[int first, int second]:int"}


def _mut(body):
    return {"mutant_id": 7, "operator": "AOR", "line": MUT_LINE, "verdict": "VERIFIED", "mutated_focal_body": body,
            "diff": {"file": "src/p/Calc.java", "offset": 0, "original": "first + second", "mutated": "first - second"}}


INFO = {"properties": {"src.dir": "src"}, "fixing_changes": []}


def _mutated_body():
    start = B_SRC.index("public int add")
    end = B_SRC.index("}", B_SRC.index("return result;")) + 1
    return B_SRC[start:end]


# ---------------------------------------------------------------- ids and selection
def test_ids_round_trip_and_refuse_double_suffix():
    did = d2.d2_focal_id(BASE, 7)
    assert did == BASE + "#m7" and d2.base_focal_id(did) == BASE and d2.mutant_id_of(did) == 7
    assert d2.base_focal_id(BASE) == BASE and d2.mutant_id_of(BASE) is None
    with pytest.raises(ValueError):
        d2.d2_focal_id(did, 8)


def test_only_verified_mutants_of_ok_methods_in_fixed_order():
    recs = [{"focal_id": "B::x", "status": "OK", "chosen": [{"mutant_id": 9, "verdict": "VERIFIED"},
                                                            {"mutant_id": 3, "verdict": "VERIFIED"}]},
            {"focal_id": "A::y", "status": "OK", "chosen": [{"mutant_id": 5, "verdict": "NOT_PLACEABLE"}]},
            {"focal_id": "C::z", "status": "NONE_KILLED"}]
    got = [(r["focal_id"], m["mutant_id"]) for r, m in d2.verified_mutants(recs)]
    assert got == [("B::x", 3), ("B::x", 9)]


def test_same_body_tolerates_newlines_and_latin1_decoding():
    assert d2.same_body("a\nb", "a\r\nb")
    latin = "x = \"café\";"                       # read_src's Latin-1 view of a non-UTF-8 file
    as_read = latin.encode("latin-1").decode("utf-8", errors="replace")
    assert d2.same_body(as_read, latin) and not d2.same_body("other", latin)


# ---------------------------------------------------------------- context from D2's own B
def test_context_is_extracted_from_the_mutant_version(tmp_path):
    b = _tree(tmp_path / "b", B_SRC)
    f = _tree(tmp_path / "f", F_SRC)
    ctx, fixed = d2.context_for_mutant(_rec(), INFO, _mut(_mutated_body()), b, f)
    assert ctx["focal_id"] == BASE + "#m7" and ctx["base_focal_id"] == BASE and ctx["dataset"] == "D2"
    assert ctx["split"] == "test" and ctx["bug_name"] == "Lang_1" and ctx["mutant_id"] == 7
    assert "first - second" in ctx["impl_B"] and "first + second" not in ctx["impl_B"]
    assert "first + second" in fixed and "_label_side" not in ctx
    assert ctx["doc"]["method_javadoc"] and "Adds two numbers" in ctx["doc"]["method_javadoc"]


def test_context_refuses_dev_methods_and_inconsistent_mutants(tmp_path):
    b = _tree(tmp_path / "b", B_SRC)
    f = _tree(tmp_path / "f", F_SRC)
    with pytest.raises(ValueError):
        d2.context_for_mutant(_rec(split="dev"), INFO, _mut(_mutated_body()), b, f)
    with pytest.raises(d2.D2Inconsistent):
        d2.context_for_mutant(_rec(), INFO, _mut("public int add(int a, int b) { return 0; }"), b, f)


# ---------------------------------------------------------------- held-out lock and dataset gate
def _scope_file(tmp_path, datasets=None, splits=("dev", "test")):
    body = {"scope": "t", "allowed_splits": list(splits), "allowed_experiments": ["X"], "allowed_models": ["m"]}
    if datasets is not None:
        body["allowed_datasets"] = datasets
    p = tmp_path / "scope.json"
    p.write_text(json.dumps(body))
    return p


def _context_dir(tmp_path, monkeypatch, split="test"):
    (tmp_path / "interim" / "context").mkdir(parents=True)
    (tmp_path / "interim" / "context" / "a.json").write_text(json.dumps({"focal_id": BASE, "split": split}))
    monkeypatch.setattr(config, "INTERIM", tmp_path / "interim")


def test_d2_ids_are_refused_until_d2_is_an_allowed_dataset(tmp_path, monkeypatch):
    _context_dir(tmp_path, monkeypatch)
    did = BASE + "#m7"
    with pytest.raises(ScopeViolation):
        scope.check_focal_ids_local([did], "t", _scope_file(tmp_path, ["D1"]))
    with pytest.raises(ScopeViolation):                       # absent field = D1 only
        scope.check_focal_ids_local([did], "t", _scope_file(tmp_path))
    assert scope.check_focal_ids_local([did, BASE], "t", _scope_file(tmp_path, ["D1", "D2"])) == 2
    with pytest.raises(ScopeViolation):                       # base method's split still governs
        scope.check_focal_ids_local([did], "t", _scope_file(tmp_path, ["D1", "D2"], splits=("dev",)))
    sc = scope.load(_scope_file(tmp_path, ["D1"]))
    with pytest.raises(ScopeViolation):
        sc.check_dataset("D2")
    with pytest.raises(ScopeViolation):
        sc.check_dataset("D3")
    sc.check_dataset("D1")


# ---------------------------------------------------------------- generation (fake Ollama server)
def _gen_ctx(mid):
    return {"focal_id": f"{BASE}#m{mid}", "split": "test", "package": "p", "focal_class": "p.Calc",
            "class_simple": "Calc", "focal_method_name": "add", "imports": [],
            "impl_B": _mutated_body().replace("first - second", f"first - second * {mid}"),
            "sig": {"focal_signature": "public int add(int first, int second)", "constructors": [],
                    "methods": ["public int twice(int x);"]}}


@pytest.fixture()
def fake_g(tmp_path, monkeypatch, server):  # noqa: F811
    STATE.reset()
    STATE.content = "```java\npublic class X {\n  @Test public void t() { assertEquals(2, new Calc().add(1, 1)); }\n}\n```"
    sc = tmp_path / "local_scope.json"
    sc.write_text(json.dumps({"scope": "t", "allowed_splits": ["test"], "allowed_experiments": ["X"],
                              "allowed_models": [TAG]}))
    monkeypatch.setattr(ollama, "LOCAL_SCOPE_FILE", sc)
    monkeypatch.setattr(llm, "STOP_FILE", tmp_path / "STOP")

    def make():
        return LLMClient(OllamaBackend(CFG, api=OllamaAPI(server), telemetry=False), log_dir=tmp_path / "calls",
                         sleep=lambda s: None)
    return make, tmp_path


def test_generation_per_unit_is_distinct_and_resumable(fake_g):
    make, tmp = fake_g
    out = tmp / "cands"
    out.mkdir()
    n, ok = d2.generate_units([_gen_ctx(7), _gen_ctx(8)], make(), PromptSet.named("local_m1b"), TAG, out)
    assert (n, ok) == (2 * config.GENERATIONS_PER_FOCAL, 2 * config.GENERATIONS_PER_FOCAL)
    cands = [json.loads(p.read_text()) for p in out.glob("*.json")]
    assert len({c["candidate_id"] for c in cands}) == 6 and {c["dataset"] for c in cands} == {"D2"}
    assert {c["focal_id"] for c in cands} == {BASE + "#m7", BASE + "#m8"}
    sent = len(STATE.requests)
    d2.generate_units([_gen_ctx(7), _gen_ctx(8)], make(), PromptSet.named("local_m1b"), TAG, out)
    assert len(STATE.requests) == sent                         # resumed from the call log, no new call


def test_generation_refuses_d1_contexts_and_stops_on_request(fake_g):
    make, tmp = fake_g
    with pytest.raises(ValueError):
        d2.generate_units([{**_gen_ctx(7), "focal_id": BASE}], make(), PromptSet.named("local_m1b"), TAG, tmp)
    (tmp / "STOP").write_text("")
    with pytest.raises(StopRequested):
        d2.generate_units([_gen_ctx(9)], make(), PromptSet.named("local_m1b"), TAG, tmp)
    assert STATE.requests == []


# ---------------------------------------------------------------- dataset build, labels, guard
TEST_CLASS = """package p;

import static org.junit.Assert.*;
import org.junit.*;

public class Calc_add_TriageGen0Test {
    @Test
    public void addsOneAndOne() {
        assertEquals(2, new Calc().add(1, 1));
    }
}
"""


def _runs(outcome, exc="", line=None):
    return [{"outcome": outcome, "exception": exc, "failing_test_line": line, "message": "expected:<2> but was:<0>"
             if outcome != "pass" else "", "trace": ""} for _ in range(3)]


def test_dataset_build_labels_d2_and_guards_the_original_line(tmp_path, monkeypatch):
    for k in ("GT_STORE", "LEAKAGE_GUARD", "PROCESSED"):
        (tmp_path / k).mkdir()
        monkeypatch.setattr(config, k, tmp_path / k)
    b = _tree(tmp_path / "b", B_SRC)
    f = _tree(tmp_path / "f", F_SRC)
    ctx, fixed = d2.context_for_mutant(_rec(), INFO, _mut(_mutated_body()), b, f)
    cand = {"candidate_id": "c1", "focal_id": ctx["focal_id"], "generation": 0, "package": "p",
            "class_name": "Calc_add_TriageGen0Test", "source": TEST_CLASS}
    ex = {"candidate_id": "c1", "focal_id": ctx["focal_id"],
          "compilation": {"compiled": ["addsOneAndOne"], "nc_both": [], "nc_one_version": [], "class_error": None},
          "methods": [{"method": "addsOneAndOne", "source_class": TEST_CLASS, "compile_b": True, "compile_f": True,
                       "runs_b": _runs("assertion_failure", "java.lang.AssertionError", 9), "runs_f": _runs("pass")}]}
    counts = dataset.build("D2", [ex], {"c1": cand}, {ctx["focal_id"]: ctx}, {ctx["focal_id"]: fixed})
    assert counts["labels"] == {"PF": 1}
    lab = list(read_jsonl(tmp_path / "GT_STORE" / "labels_D2.jsonl"))[0]
    inst = list(read_jsonl(tmp_path / "PROCESSED" / "instances_D2.jsonl"))[0]
    guard = list(read_jsonl(tmp_path / "LEAKAGE_GUARD" / "guard_D2.jsonl"))[0]
    assert lab["dataset"] == inst["dataset"] == "D2" and inst["focal_id"] == BASE + "#m7"
    assert "label" not in inst and "first - second" in inst["impl"]
    assert "int result = first + second;" in guard["code_lines"] and "Lang_1" in guard["bug_ids"]


# ---------------------------------------------------------------- WSL-side stages with Defects4J faked
@pytest.fixture()
def fake_d4j(tmp_path, monkeypatch):
    from triage import execution
    calls = []

    def d4j(*args, **kw):
        calls.append(args)
        return "/fake/cp" if args[0] == "export" else ""
    monkeypatch.setattr(execution, "WORK", tmp_path / "work")
    monkeypatch.setattr(execution, "d4j", d4j)
    fdir = _tree(tmp_path / "work" / "Lang_1" / "f", F_SRC)
    return {"workdir": str(fdir)}, calls, tmp_path


def _verified(f_src=F_SRC):
    import hashlib
    from triage.mutants import materialise
    off = f_src.index("+ second")
    diff = {"file": "src/p/Calc.java", "offset": off, "original": "first + second", "mutated": "first - second"}
    new = materialise(f_src, diff)
    return {"mutant_id": 7, "operator": "AOR", "line": MUT_LINE, "diff": diff,
            "mutated_source_sha256": hashlib.sha256(new.encode()).hexdigest()}


def test_mutant_version_is_built_then_reused_and_always_compiled(fake_d4j):
    meta_f, calls, tmp = fake_d4j
    mut = _verified()
    meta = d2.prepare_mutant_version("Lang", "1", mut, meta_f)
    vfile = Path(meta["workdir"]) / "src" / "p" / "Calc.java"
    assert "first - second" in vfile.read_text() and meta["version"] == "m7" and meta["cp.test"] == "/fake/cp"
    assert (tmp / "work" / "Lang_1" / "meta_m7.json").exists()
    vfile.with_name("Marker.txt").write_text("kept")            # a reused tree is not re-copied
    d2.prepare_mutant_version("Lang", "1", mut, meta_f)
    assert vfile.with_name("Marker.txt").exists()
    assert sum(1 for c in calls if c[0] == "compile") == 2


def test_mutant_version_rebuilt_when_tampered_and_refused_when_unreproducible(fake_d4j):
    meta_f, _, tmp = fake_d4j
    mut = _verified()
    meta = d2.prepare_mutant_version("Lang", "1", mut, meta_f)
    vfile = Path(meta["workdir"]) / "src" / "p" / "Calc.java"
    vfile.write_text("tampered")
    d2.prepare_mutant_version("Lang", "1", mut, meta_f)
    assert "first - second" in vfile.read_text()
    with pytest.raises(d2.D2Inconsistent):
        d2.prepare_mutant_version("Lang", "1", {**mut, "mutated_source_sha256": "0" * 64}, meta_f)


def test_execute_bug_runs_each_unit_against_its_own_mutant_version(fake_d4j, monkeypatch):
    from triage import execution
    meta_f, _, tmp = fake_d4j
    monkeypatch.setattr(execution, "prepare_version", lambda p, b, v: meta_f)
    seen = []

    def fake_exec(c, mb, mf):
        seen.append((c["candidate_id"], mb["version"], mf["workdir"]))
        if c["candidate_id"] == "bad":
            raise RuntimeError("boom")
        return {"candidate_id": c["candidate_id"], "methods": []}
    monkeypatch.setattr(execution, "execute_candidate", fake_exec)
    did = BASE + "#m7"
    out = d2.execute_bug("Lang", "1", {did: [{"candidate_id": "c1", "focal_id": did},
                                              {"candidate_id": "bad", "focal_id": did}]}, {did: _verified()})
    assert [(c, v) for c, v, _ in seen] == [("c1", "m7"), ("bad", "m7")] and seen[0][2] == meta_f["workdir"]
    ok = [r for _, r, e in out if r]
    assert ok[0]["dataset"] == "D2" and ok[0]["mutant_version"] == "m7" and ok[0]["focal_id"] == did
    assert [e for _, r, e in out if e and "boom" in e]
