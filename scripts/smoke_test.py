"""End-to-end plumbing check with SYNTHETIC instances and the MOCK backend. Zero cost, zero research value.

    python scripts/smoke_test.py && python scripts/analyze.py --smoke

Everything is written under results/smoke/. Figures carry a 'SMOKE TEST — MOCK DATA' watermark.
"""
import json
import random
import shutil
import sys

import run_experiment
from _common import config, make_client
from triage import dataset
from triage.io_utils import dump_json, write_jsonl

BASE = config.ROOT / "results" / "smoke"


def synth(n=90, seed=7):
    rng = random.Random(seed)
    insts, labels, weights, jd = [], [], {}, []
    for i in range(n):
        proj = f"Proj{i % 6}"
        bug = f"{proj}_{i % 15}"
        lab = "PF" if rng.random() < 0.34 else ("TF" if rng.random() < 0.95 else "AMB")
        assertion = rng.random() < 0.6
        iid = f"syn{i:03d}"
        has_doc = rng.random() < 0.7
        insts.append({
            "instance_id": iid, "focal_id": f"{bug}::f", "project": proj, "bug_name": bug, "split": "test",
            "focal_class": "org.syn.Foo", "focal_method_name": "bar",
            "test": {"method_source": f"@Test\npublic void t{i}() {{\n  assertEquals({i}, new Foo().bar({i}));\n}}",
                     "imports": ["org.junit.Test"], "fixtures": ""},
            "failure": {"outcome_type": "assertion_failure" if assertion else "exception",
                        "exception_class": "java.lang.AssertionError" if assertion else "java.lang.IllegalStateException",
                        "message": f"expected:<{i}> but was:<{i + 1}>", "failing_test_line": 3,
                        "failing_test_line_text": f"assertEquals({i}, new Foo().bar({i}));",
                        "frames": [] if assertion else [{"method": "org.syn.Foo.bar", "location": "Foo.java:10", "in_test": False}]},
            "sig": {"focal_signature": "public int bar(int x)", "class_declaration": "public class Foo",
                    "constructors": ["public Foo()"], "methods": [], "type_signatures": []},
            "doc": {"method_javadoc": "/** Returns x. */" if has_doc else "", "class_javadoc": ""},
            "impl": "public int bar(int x) {\n    return x + 1; // synthetic body line long enough\n}",
            "covariates": {"javadoc_present": has_doc},
        })
        labels.append({"instance_id": iid, "label": lab, "project": proj, "bug_name": bug, "split": "test"})
        if lab == "TF":
            weights[iid] = 3.0
        if has_doc:
            jd.append(iid)
    return insts, labels, weights, jd


def main():
    if BASE.exists():
        shutil.rmtree(BASE)
    insts, labels, weights, jd = synth()
    write_jsonl(BASE / "synthetic_labels.jsonl", labels)
    dump_json(BASE / "synthetic_sample.json", {"tf_weights": weights, "javadoc_ids": jd,
                                               "note": "SYNTHETIC — pipeline validation only"})
    # one planted leak: its failure message names the bug id, so the guard must block it before any call
    leaky = json.loads(json.dumps(insts[0]))
    leaky["instance_id"] = "syn_leak"
    leaky["failure"]["message"] = f"regression from {leaky['bug_name']}"
    insts.append(leaky)
    labels.append({**labels[0], "instance_id": "syn_leak"})
    write_jsonl(BASE / "synthetic_labels.jsonl", labels)
    inp = BASE / "inputs"
    write_jsonl(inp / "instances.jsonl", insts)
    (inp / "sample.json").write_text(json.dumps({"instance_ids": [i["instance_id"] for i in insts]}))
    write_jsonl(inp / "guard.jsonl", [dataset.guard_record(i["instance_id"], i["bug_name"], None, i["impl"]) for i in insts])
    spec = {k: "synthetic" for k in ("purpose", "preconditions", "postconditions", "exceptions", "edge_cases")}
    write_jsonl(inp / "specs.jsonl", [{"focal_id": f, "spec": spec, "valid": True} for f in {i["focal_id"] for i in insts}])
    conds = [{"arm": "DA"}, {"arm": "KA"}, {"arm": "R0"},
             {"arm": "J1", "levels": ["S0", "S1", "S2"]}, {"arm": "SC", "levels": ["S0", "S1", "S2"]},
             {"arm": "DEB", "levels": ["S0", "S1", "S2"]}, {"arm": "SC-T", "levels": ["S1"], "k": 7},
             {"arm": "A1", "levels": ["S1"], "replicates": 1}, {"arm": "A2", "levels": ["S1"], "replicates": 1},
             {"arm": "J1", "levels": ["S1"], "variant": "noF", "replicates": 1},
             {"arm": "DEB", "levels": ["S1"], "variant": "impl", "replicates": 1},
             {"arm": "J1", "levels": ["S2"], "variant": "specprime", "replicates": 1}]
    exp = {"name": "SMOKE_synthetic", "dataset": "SYN", "split": "test", "model": "mock-model", "prompt_set": "v0",
           "replicates": 3, "conditions": conds, "instances_file": str(inp / "instances.jsonl"),
           "sample_file": str(inp / "sample.json"), "guard_file": str(inp / "guard.jsonl"),
           "specs_file": str(inp / "specs.jsonl"), "specs_prime_file": str(inp / "specs.jsonl")}
    run_dir = BASE / "SMOKE_synthetic"
    run_experiment.execute(exp, make_client(mock=True), run_dir, workers=8)   # the live entry point
    count = lambda f: sum(1 for _ in open(run_dir / f)) if (run_dir / f).exists() else 0
    n_dec, n_err, n_rej = count("decisions.jsonl"), count("errors.jsonl"), count("leakage_rejections.jsonl")
    leaked_ids = {json.loads(l)["instance_id"] for l in open(run_dir / "leakage_rejections.jsonl")} if n_rej else set()
    # The criterion is what was SENT: the planted string must appear in no prompt. (The A4 'noF' variant of the
    # leaky instance is legitimately judged: removing [F] removes the leak, so its package is clean.)
    planted = leaky["failure"]["message"]
    sent = [json.loads(l)["messages"][0]["content"] for f in (BASE / "llm_calls").glob("*.jsonl")
            if not f.name.startswith("_") for l in open(f, encoding="utf-8")]
    leaks_sent = sum(planted in p for p in sent)
    judged_leaky = sorted({(json.loads(l)["arm"], json.loads(l)["level"], json.loads(l)["variant"])
                           for l in open(run_dir / "decisions.jsonl")
                           if json.loads(l)["instance_id"] == "syn_leak" and json.loads(l)["arm"] not in ("DA", "KA", "R0")})
    print(f"decisions={n_dec} errors={n_err} leakage_rejections={n_rej} rejected_ids={sorted(leaked_ids)} "
          f"prompts_sent={len(sent)} prompts_containing_planted_leak={leaks_sent} leaky_instance_judged_in={judged_leaky}")
    if n_err:
        print(open(run_dir / "errors.jsonl").read()[:2000])
    sys.exit(1 if n_err or leaks_sent or leaked_ids != {"syn_leak"} else 0)


if __name__ == "__main__":
    main()
