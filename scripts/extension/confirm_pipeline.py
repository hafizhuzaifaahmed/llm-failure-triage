"""CFP confirmation pipeline after generation (D-142). Each real step checks its own preconditions and refuses
otherwise; the validate-* commands reproduce the original study's stored data and never touch confirmation data.

Real steps (in order; none may run before generation has passed the readiness gate):
    execute  --tranche T [--workers 6]   WSL: compile and run every generated test on B and F
    label    --tranche T                 labels, instances, guard, exclusions, all-instance sample (written once)
    vote-configs                         writes the six vote experiment configs and the M3 profile copy (no call)
    vote     --tranche F1|F2 --model M1|M2|M3   one fresh J1 call per instance at S1 (labels must be committed)
    concat                               read-only concatenation of F1, F2 and CTRL for the frozen analysis

Validation on the original study's stored data (no model call, no confirmation data):
    validate-labels      rebuild labels/instances/guard/exclusions of D1 from the stored execution records
    validate-execution   WSL: re-execute the stored D1 test classes and compare every label   [--bugs N]
    validate-votes       replay E8's three vote runs from the committed call logs through the vote driver
    validate-concat      split the pilot into three parts by bug, concatenate, re-run the frozen analysis
"""
import argparse
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import confirm_lib as L  # noqa: E402

ROOT = L.ROOT
VALID = ROOT / "results" / "extension" / "validation"


def _gate():
    return L.load_module("confirm_gate", ROOT / "scripts" / "extension" / "confirm_gate.py")


def _require(checks: list[str]):
    """Run named checks of the readiness gate; exit with every failure listed."""
    g = _gate()
    fns = {"registration": g.check_registration, "desktop": g.check_no_desktop_server,
           "server": g.check_frozen_server, "hashes": g.check_manifest_and_hashes,
           "frozen": g.check_nothing_frozen_changed}
    bad = []
    for c in checks:
        ok, why = fns[c]()
        if not ok:
            bad.append(f"{c}: {why}")
    if bad:
        sys.exit("REFUSED (D-142):\n  " + "\n  ".join(bad))


def _write_report(name: str, rep: dict) -> Path:
    VALID.mkdir(parents=True, exist_ok=True)
    p = VALID / f"{name}.json"
    p.write_text(json.dumps(rep, indent=1, sort_keys=True), encoding="utf-8", newline="\n")
    return p


# ---------------------------------------------------------------------------------------------------------------
# real steps
# ---------------------------------------------------------------------------------------------------------------
def cmd_execute(a):
    _require(["registration", "hashes", "frozen"])
    p = L.paths(a.tranche)
    if not any(p["candidates"].glob("*.json")):
        sys.exit(f"no generated candidates in {p['candidates']}")
    groups = L.group_candidates(p["candidates"], p["executions"])
    L.check_execution_scope(a.tranche, groups)
    print(L.execute(p["candidates"], p["executions"], a.workers))


def cmd_label(a):
    _require(["registration", "hashes", "frozen"])
    print(json.dumps(L.label_tranche(a.tranche), indent=1))
    print("Commit the labels now (sealing): the vote driver refuses until they are committed.")


def cmd_vote_configs(_a):
    for f in L.write_vote_configs():
        print(f.relative_to(ROOT))
    print(L.CONF_E6B_PROFILE.relative_to(ROOT))


def cmd_vote(a):
    if a.tranche not in L.JUDGED:
        sys.exit("only F1 and F2 are judged (registration, data collection step 6)")
    checks = ["registration", "desktop", "hashes", "frozen"] + (["server"] if a.model != "M3" else [])
    _require(checks)
    p = L.paths(a.tranche)
    for k in ("labels", "instances", "guard"):
        if not p[k].exists() or not L.is_committed(p[k]):
            sys.exit(f"{p[k].name} is missing or not committed: labels must be sealed before any judge reads an instance")
    name = L.vote_run_name(a.tranche, a.model)
    exp = json.loads((L.EXP_DIR / f"{name}.json").read_text(encoding="utf-8"))
    profile = None
    if a.model == "M3":
        from triage import expl_profile
        profile = expl_profile.load(L.CONF_E6B_PROFILE)          # the study's own profile checks (ports, log dirs)
        sel = json.loads(expl_profile.resolve(profile["selection_gated"]["selection_file"]).read_text()).get("selected")
        if sel != profile["model_tag"]:
            sys.exit(f"{profile['model_tag']} is not the selected third-family judge ({sel})")
    client = L.vote_client(a.model, p["vote_calls"] / a.model, profile=profile)
    L.run_vote(exp, client, p["votes"] / name, workers=1)


def cmd_concat(_a):
    _require(["registration", "hashes", "frozen"])
    frame = {r["focal_id"]: r["tranche"] for r in L.read_jsonl(L.FRAME_FILE)}
    parts = []
    for tr in L.TRANCHES:
        p = L.paths(tr)
        ledger = ROOT / "results" / "extension" / "probes" / L.runs()["runs"]["probes"][tr] / "ledger.jsonl"
        votes = {m: p["votes"] / L.vote_run_name(tr, m) / "decisions.jsonl" for m in L.VOTE_MODELS} if tr in L.JUDGED else {}
        missing = [str(x) for x in [ledger, p["instances"], p["labels"], *votes.values()] if not Path(x).exists()]
        if missing:
            sys.exit(f"{tr}: missing inputs {missing}")
        parts.append({"tranche": tr, "ledger": ledger, "instances": p["instances"], "labels": p["labels"], "votes": votes})
    out_ledger = ROOT / "results" / "extension" / "probes" / L.CONCAT_RUN
    print(json.dumps(L.concatenate(parts, out_ledger, L.BASE / "ALL", frame)["counts"], indent=1))


# ---------------------------------------------------------------------------------------------------------------
# validation on stored data
# ---------------------------------------------------------------------------------------------------------------
STUDY = {"labels": ROOT / "data" / "ground_truth_store" / "labels_D1.jsonl",
         "instances": ROOT / "data" / "processed" / "instances_D1.jsonl",
         "guard": ROOT / "data" / "leakage_guard" / "guard_D1.jsonl",
         "exclusions": ROOT / "data" / "processed" / "exclusions_D1.jsonl"}
D1_CANDS = ROOT / "data" / "interim" / "candidates_gemma4_26b"
D1_EXECS = ROOT / "data" / "raw" / "executions_gemma4_26b"


def _study_contexts():
    return {c["focal_id"]: c for c in (json.loads(p.read_text(encoding="utf-8"))
                                       for p in sorted((ROOT / "data" / "interim" / "context").glob("*.json")))}


def _study_fixed():
    return {r["focal_id"]: r.get("fixed_body")
            for r in L.read_jsonl(ROOT / "data" / "ground_truth_store" / "fixed_bodies.jsonl")}


def _compare_files(built: dict[str, Path]) -> dict:
    out = {}
    for k, ref in STUDY.items():
        a, b = L.raw_lines(built[k]), L.raw_lines(ref)
        ja = {json.loads(x).get("instance_id") or i: json.loads(x) for i, x in enumerate(a)}
        jb = {json.loads(x).get("instance_id") or i: json.loads(x) for i, x in enumerate(b)}
        diff = [i for i in set(ja) | set(jb) if ja.get(i) != jb.get(i)]
        out[k] = {"records_built": len(a), "records_study": len(b), "lines_identical": a == b,
                  "records_identical": not diff, "records_differing": len(diff), "examples": sorted(map(str, diff))[:5]}
    return out


def cmd_validate_labels(_a):
    out_dir = VALID / "labels_D1"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    t0 = time.time()
    counts = L.build_dataset("D1", D1_EXECS, D1_CANDS, _study_contexts(), _study_fixed(), out_dir)
    built = {"labels": out_dir / "labels_D1.jsonl", "instances": out_dir / "instances_D1.jsonl",
             "guard": out_dir / "guard_D1.jsonl", "exclusions": out_dir / "exclusions_D1.jsonl"}
    rep = {"what": "dataset.build through the confirmation driver on the study's stored D1 execution records",
           "counts": counts, "seconds": round(time.time() - t0, 1), "comparison": _compare_files(built)}
    rep["exact"] = all(v["records_identical"] for v in rep["comparison"].values())
    print(json.dumps(rep, indent=1))
    _write_report("validate_labels_D1", rep)
    shutil.rmtree(out_dir)                         # the comparison is the result; the copies are not kept


def cmd_validate_execution(a):
    """Re-executes stored D1 test classes (CPU only, WSL) and compares labels method by method."""
    from triage import labeling
    out = VALID / "exec_D1" / "executions"
    bugs = None
    if a.bugs:
        names = sorted({json.loads(p.read_text())["focal_id"].split("::")[0] for p in D1_CANDS.glob("*.json")})
        bugs = set(names[:: max(1, len(names) // a.bugs)][: a.bugs])
    run = L.execute(D1_CANDS, out, a.workers, bugs=bugs)
    rows, mism = 0, []
    cmp_comp = 0
    for p in sorted(out.glob("*.json")):
        new = json.loads(p.read_text())
        old = json.loads((D1_EXECS / p.name).read_text())
        comp_same = {k: v for k, v in new["compilation"].items()} == {k: v for k, v in old["compilation"].items()}
        cmp_comp += int(comp_same)
        om = {m["method"]: labeling.label(m)["label"] for m in old["methods"]}
        for m in new["methods"]:
            rows += 1
            ln = labeling.label(m)["label"]
            if om.get(m["method"]) != ln:
                mism.append({"candidate_id": new["candidate_id"], "method": m["method"], "stored": om.get(m["method"]),
                             "reexecuted": ln})
        missing = set(om) - {m["method"] for m in new["methods"]}
        for name in missing:
            mism.append({"candidate_id": new["candidate_id"], "method": name, "stored": om[name], "reexecuted": None})
    n_records = len(list(out.glob("*.json")))
    rep = {"what": "re-execution of the study's stored D1 test classes through the confirmation execution driver",
           "run": run, "records_compared": n_records, "compilation_identical": cmp_comp,
           "methods_compared": rows, "label_mismatches": len(mism), "mismatches": mism[:50],
           "exact": not mism and cmp_comp == n_records, "bugs_subset": sorted(bugs) if bugs else "all"}
    print(json.dumps({k: v for k, v in rep.items() if k != "mismatches"}, indent=1))
    _write_report("validate_execution_D1" + (f"_{a.bugs}bugs" if a.bugs else ""), rep)


def _decisions_equal(a: dict, b: dict) -> bool:
    def norm(d):
        d = json.loads(json.dumps(d))
        (d.get("cost") or {}).pop("cached_calls", None)
        d.pop("utc", None)
        return d
    return norm(a) == norm(b)


def cmd_validate_votes(_a):
    from triage import expl_profile
    from triage.ollama import LOCAL_CALL_LOG_DIR
    e6b = json.loads(L.E6B_PROFILE.read_text(encoding="utf-8"))
    plan = [("M1", "LOCAL_HO_E8_VOTE_M1", LOCAL_CALL_LOG_DIR / "qwen3.5_9b.jsonl", None),
            ("M2", "LOCAL_HO_E8_VOTE_M2", LOCAL_CALL_LOG_DIR / "gemma4_12b.jsonl", None),
            ("M3", "LOCAL_HO_E8_VOTE_E6B", expl_profile.resolve(e6b["call_log_dir"]) / "ministral-3_14b-instruct-2512-q4_K_M.jsonl",
             e6b["model_tag"])]
    rep = {"what": "E8 votes (replicate 10) replayed from the committed call logs through the confirmation vote "
                   "driver: same config builder, client construction and run_experiment.execute; a backend that "
                   "cannot make a call", "models": {}}
    tmp = Path(tempfile.mkdtemp(prefix="cfp_vote_replay_"))
    try:
        for model, name, log, tag in plan:
            log_dir = tmp / f"log_{model}"
            log_dir.mkdir()
            shutil.copy2(log, log_dir / log.name)              # a copy: the study's call log is never opened for writing
            exp = L.vote_config(name, "D1", ROOT / "data" / "processed" / "instances_D1.jsonl",
                                ROOT / "data" / "processed" / "sample_D1_test.json", STUDY["guard"], model, 10,
                                model_tag=tag)
            client = L.vote_client(model, log_dir, replay=True, profile=e6b if model == "M3" else None)
            run_dir = tmp / f"run_{model}"
            t0 = time.time()
            err = None
            try:
                L.run_vote(exp, client, run_dir, workers=1)
            except BaseException as e:                          # a missing log entry must show up, not crash the report
                err = f"{type(e).__name__}: {str(e)[:300]}"
            new = {d["instance_id"]: d for d in L.read_jsonl(run_dir / "decisions.jsonl")} if (run_dir / "decisions.jsonl").exists() else {}
            old = {d["instance_id"]: d for d in L.read_jsonl(ROOT / "results" / "runs_local" / name / "decisions.jsonl")
                   if d["replicate"] == 10 and d["arm"] == "J1" and d.get("level") == "S1"}
            diff = [i for i in set(old) | set(new) if not (i in old and i in new and _decisions_equal(old[i], new[i]))]
            rep["models"][model] = {"run": name, "decisions_committed": len(old), "decisions_replayed": len(new),
                                    "identical": len(old) - len([i for i in diff if i in old]),
                                    "differing_or_missing": len(diff), "examples": sorted(diff)[:5], "error": err,
                                    "seconds": round(time.time() - t0, 1),
                                    "label_raw_agreement": sum(1 for i in old if i in new and old[i]["label_raw"] == new[i]["label_raw"])}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    rep["exact"] = all(m["differing_or_missing"] == 0 and not m["error"] for m in rep["models"].values())
    print(json.dumps(rep, indent=1))
    _write_report("validate_votes_E8", rep)


def cmd_validate_concat(_a):
    import subprocess
    lab = {l["instance_id"]: l for l in L.read_jsonl(STUDY["labels"]) if l["split"] == "test"}
    inst_lines = [l for l in L.raw_lines(STUDY["instances"]) if json.loads(l)["split"] == "test"]
    led_lines = L.raw_lines(ROOT / "results" / "extension" / "probes" / "CFP_D1_TEST" / "ledger.jsonl")
    bugs = sorted({l["bug_name"] for l in lab.values()})
    part_of = {b: ("P1", "P2", "P3")[k % 3] for k, b in enumerate(bugs)}
    bug_of = {json.loads(l)["instance_id"]: json.loads(l)["bug_name"] for l in inst_lines}
    vote_runs = {"M1": "LOCAL_HO_E8_VOTE_M1", "M2": "LOCAL_HO_E8_VOTE_M2", "M3": "LOCAL_HO_E8_VOTE_E6B"}
    tmp = Path(tempfile.mkdtemp(prefix="cfp_concat_"))
    run = "VALID_CONCAT_PILOT"
    ledger_dir = ROOT / "results" / "extension" / "probes" / run
    if ledger_dir.exists():
        shutil.rmtree(ledger_dir)
    try:
        parts = []
        for part in ("P1", "P2", "P3"):
            d = tmp / part
            d.mkdir()
            sel = lambda lines: [l for l in lines if part_of[bug_of[json.loads(l)["instance_id"]]] == part]  # noqa: E731
            files = {"ledger": sel(led_lines), "instances": sel(inst_lines),
                     "labels": sel([l for l in L.raw_lines(STUDY["labels"]) if json.loads(l)["split"] == "test"])}
            rec = {"tranche": part}
            for k, lines in files.items():
                (d / f"{k}.jsonl").write_bytes(b"".join(x + b"\n" for x in lines))
                rec[k] = d / f"{k}.jsonl"
            rec["votes"] = {}
            for m, r in vote_runs.items():
                lines = [l for l in L.raw_lines(ROOT / "results" / "runs_local" / r / "decisions.jsonl")
                         if json.loads(l)["instance_id"] in bug_of and part_of[bug_of[json.loads(l)["instance_id"]]] == part]
                (d / f"votes_{m}.jsonl").write_bytes(b"".join(x + b"\n" for x in lines))
                rec["votes"][m] = d / f"votes_{m}.jsonl"
            parts.append(rec)
        man = L.concatenate(parts, ledger_dir, tmp / "ALL", frame=None, replicate=10)
        out = tmp / "analysis.json"
        cmd = [sys.executable, str(ROOT / "scripts" / "extension" / "confirm_analysis.py"), "--run", run,
               "--instances", str(tmp / "ALL" / "instances.jsonl"), "--labels", str(tmp / "ALL" / "labels.jsonl"),
               "--votes", *[f"{m}={tmp / 'ALL' / 'votes' / m}" for m in vote_runs], "--replicate", "10",
               "--dry-run", "--out", str(out)]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        new = json.loads(out.read_text(encoding="utf-8")) if out.exists() else None
        ref = json.loads((ROOT / "results" / "extension" / "dryrun" / "confirm_analysis_dryrun_on_pilot.json").read_text(encoding="utf-8"))
        if new is not None:
            new.pop("run", None)
        ref.pop("run", None)
        diffs = [k for k in set(ref) | set(new or {}) if (new or {}).get(k) != ref.get(k)]
        rep = {"what": "pilot split into three parts by bug, concatenated by the confirmation driver, analysed by the "
                       "frozen confirm_analysis.py; compared with the committed analysis dry run on the unsplit pilot",
               "parts": man["counts"], "outputs": {k: v["records"] for k, v in man["outputs"].items()},
               "analysis_exit": r.returncode, "analysis_stderr": r.stderr[-500:], "differing_sections": diffs,
               "exact": r.returncode == 0 and not diffs}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(ledger_dir, ignore_errors=True)
    print(json.dumps(rep, indent=1))
    _write_report("validate_concat_pilot", rep)


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("execute", "label"):
        s = sub.add_parser(name)
        s.add_argument("--tranche", required=True, choices=list(L.TRANCHES))
        if name == "execute":
            s.add_argument("--workers", type=int, default=6)
    sub.add_parser("vote-configs")
    s = sub.add_parser("vote")
    s.add_argument("--tranche", required=True, choices=list(L.JUDGED))
    s.add_argument("--model", required=True, choices=list(L.VOTE_MODELS))
    sub.add_parser("concat")
    sub.add_parser("validate-labels")
    s = sub.add_parser("validate-execution")
    s.add_argument("--workers", type=int, default=6)
    s.add_argument("--bugs", type=int, default=0, help="spread sample of N bugs (0 = all D1 bugs)")
    sub.add_parser("validate-votes")
    sub.add_parser("validate-concat")
    a = ap.parse_args(argv)
    {"execute": cmd_execute, "label": cmd_label, "vote-configs": cmd_vote_configs, "vote": cmd_vote,
     "concat": cmd_concat, "validate-labels": cmd_validate_labels, "validate-execution": cmd_validate_execution,
     "validate-votes": cmd_validate_votes, "validate-concat": cmd_validate_concat}[a.cmd](a)


if __name__ == "__main__":
    main()
